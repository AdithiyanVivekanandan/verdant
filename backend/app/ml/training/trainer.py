"""Model training and evaluation.

The trainer is deliberately conservative:

* The split is **time aware**: samples are ordered by feature timestamp and
  split chronologically (train -> validation -> test). Random shuffling is
  never used, so future observations can never leak into training.
* A transparent baseline (persistence / linear trend) is evaluated on the
  same split. A tree model is only promoted when it beats the baseline.
* The data set size, feature list, periods, metrics and limitations are
  written into the artifact metadata.
* When the data set is too small for production use, the artifact is still
  stored, but the metadata records that the requirements are not met and
  inference reports predictions as provisional.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np

from app.ml.baselines.baselines import PersistenceBaseline, LinearTrendBaseline
from app.ml.evaluation.metrics import evaluate, prediction_interval
from app.ml.features.engineering import (
    CATEGORICAL_FEATURES,
    HORIZON_HOURS,
    NUMERIC_FEATURES,
    FeatureContext,
    feature_names,
)
from app.ml.models.registry import ModelArtifact, ModelMetadata, save_artifact
from app.ml.preprocessing.imputer import MedianImputer
from app.ml.training.dataset import DatasetBundle


def _context_from_sample(sample: Any) -> FeatureContext:
    """Rebuild a FeatureContext-like object from a stored sample row."""
    context = FeatureContext()
    context.values = dict(sample.features)
    context.categoricals = {}
    context.meta = {"field_id": sample.field_id}
    return context


def chronological_split(
    samples: list[Any],
    *,
    validation_ratio: float = 0.2,
    test_ratio: float = 0.2,
) -> tuple[list[Any], list[Any], list[Any]]:
    """Split samples by time into train, validation and test sets."""
    ordered = sorted(samples, key=lambda s: (s.feature_time, s.field_id))
    total = len(ordered)
    if total == 0:
        return [], [], []
    test_size = max(1, int(round(total * test_ratio))) if total >= 5 else 0
    val_size = max(1, int(round(total * validation_ratio))) if total - test_size >= 3 else 0
    if total - test_size - val_size < 1:
        val_size = 0
    train = ordered[: total - test_size - val_size]
    validation = ordered[total - test_size - val_size : total - test_size]
    test = ordered[total - test_size :] if test_size else []
    return train, validation, test


def _fit_estimator(name: str, seed: int):
    if name == "random_forest":
        from sklearn.ensemble import RandomForestRegressor

        # n_jobs=1 keeps the fit bit-for-bit reproducible: parallel tree
        # building introduces floating point differences that change the
        # reported metrics between runs.
        return RandomForestRegressor(
            n_estimators=300,
            max_depth=8,
            min_samples_leaf=3,
            max_features="sqrt",
            random_state=seed,
            n_jobs=1,
        )
    if name == "gradient_boosting":
        from sklearn.ensemble import GradientBoostingRegressor

        return GradientBoostingRegressor(
            n_estimators=200,
            max_depth=3,
            learning_rate=0.05,
            loss="squared_error",
            random_state=seed,
        )
    raise ValueError(f"Unknown model: {name}")


def evaluate_candidates(
    train: list[Any],
    validation: list[Any],
    test: list[Any],
    *,
    seed: int = 42,
) -> dict[str, Any]:
    """Fit candidate models and compare them with the baselines."""
    results: dict[str, Any] = {"candidates": {}, "baseline": {}}

    if not train:
        return results

    imputer = MedianImputer().fit([s.features for s in train])
    x_train = np.asarray(imputer.transform_many([s.features for s in train]), dtype=float)
    y_train = np.asarray([s.target for s in train], dtype=float)

    def _score(predictor, samples: list[Any]) -> Optional[dict[str, Any]]:
        if not samples:
            return None
        x = np.asarray(imputer.transform_many([s.features for s in samples]), dtype=float)
        y = np.asarray([s.target for s in samples], dtype=float)
        predictions = np.asarray(predictor.predict(x), dtype=float)
        return evaluate(y, predictions, groups=[s.crop_type for s in samples])

    def _score_baseline(baseline: Any, samples: list[Any]) -> Optional[dict[str, Any]]:
        """Score a baseline on raw feature contexts (no imputation needed)."""
        if not samples:
            return None
        y = np.asarray([s.target for s in samples], dtype=float)
        predictions = np.asarray(
            baseline.predict([_context_from_sample(s) for s in samples]), dtype=float
        )
        return evaluate(y, predictions, groups=[s.crop_type for s in samples])

    # --- baselines ----------------------------------------------------------
    baselines = {
        "persistence": PersistenceBaseline(),
        "linear_trend": LinearTrendBaseline(horizon_hours=HORIZON_HOURS),
    }
    for baseline_name, baseline in baselines.items():
        results["baseline"][baseline_name] = {
            "train": _score_baseline(baseline, train),
            "validation": _score_baseline(baseline, validation),
            "test": _score_baseline(baseline, test),
        }

    # --- candidate tree models ---------------------------------------------
    for candidate in ("random_forest", "gradient_boosting"):
        try:
            estimator = _fit_estimator(candidate, seed)
            estimator.fit(x_train, y_train)
        except Exception as exc:  # pragma: no cover - depends on optional deps
            results["candidates"][candidate] = {"error": str(exc)}
            continue

        train_preds = estimator.predict(x_train)
        train_eval = evaluate(y_train, train_preds, groups=[s.crop_type for s in train])
        residuals = (y_train - np.asarray(train_preds, dtype=float)).tolist()

        candidate_result: dict[str, Any] = {
            "train": train_eval,
            "validation": _score(estimator, validation),
            "test": _score(estimator, test),
            "residual_interval": prediction_interval(residuals),
        }
        results["candidates"][candidate] = candidate_result
        results.setdefault("_fitted", {})[candidate] = (estimator, residuals)

    return results


def choose_model(results: dict[str, Any]) -> tuple[Optional[str], str]:
    """Pick the promoted model.

    A candidate is only promoted when it beats the persistence baseline on
    the validation split. Otherwise the baseline stays in charge and the
    reason is recorded.
    """
    candidates = results.get("candidates", {})
    baseline_mae = None
    baseline = results.get("baseline", {}).get("persistence", {})
    for split in ("validation", "test"):
        metrics = baseline.get(split)
        if metrics and metrics.get("mae") is not None:
            baseline_mae = metrics["mae"]
            break

    best_name = None
    best_mae = None
    for name, result in candidates.items():
        if result.get("error"):
            continue
        validation = result.get("validation")
        if not validation or validation.get("mae") is None:
            continue
        if best_mae is None or validation["mae"] < best_mae:
            best_mae = validation["mae"]
            best_name = name

    if best_name is None:
        return None, "No candidate model could be fitted on the available data."
    if baseline_mae is None:
        return best_name, "Promoted as the best available model; no baseline comparison was possible."
    if best_mae < baseline_mae:
        return (
            best_name,
            f"Validation MAE {best_mae:.2f} is lower than the persistence baseline MAE {baseline_mae:.2f}.",
        )
    return (
        None,
        f"No candidate beat the persistence baseline (baseline MAE {baseline_mae:.2f}, best candidate MAE {best_mae:.2f}).",
    )


def train_model(
    bundle: DatasetBundle,
    *,
    model_name: str = "soil_moisture_horizon",
    model_version: Optional[str] = None,
    seed: int = 42,
    save: bool = True,
) -> Optional[ModelArtifact]:
    """Train, evaluate and store the model artifact.

    The artifact is always stored so the evaluation is auditable, but it is
    marked ``selected`` only when it actually beats the transparent
    baseline. Otherwise inference keeps using the baseline.
    """
    train, validation, test = chronological_split(bundle.samples)
    if not train:
        return None

    results = evaluate_candidates(train, validation, test, seed=seed)
    selected_name, reason = choose_model(results)

    fitted = results.get("_fitted", {})
    candidate_name = selected_name
    if candidate_name is None:
        # Keep the best candidate for the record, but do not promote it.
        best_mae = None
        for name, result in results.get("candidates", {}).items():
            if result.get("error") or name not in fitted:
                continue
            validation_metrics = result.get("validation") or {}
            if validation_metrics.get("mae") is None:
                continue
            if best_mae is None or validation_metrics["mae"] < best_mae:
                best_mae = validation_metrics["mae"]
                candidate_name = name
    if candidate_name is None or candidate_name not in fitted:
        return None
    estimator, residuals = fitted[candidate_name]

    imputer = MedianImputer().fit([s.features for s in train])
    version = model_version or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    requirements = bundle.requirement_report()
    limitations = list(bundle.limitations)
    if not requirements["meets_requirements"]:
        limitations.append(
            "The available data set is below the production requirement "
            f"({requirements['actual_training_samples']} samples over "
            f"{requirements['actual_span_days']} days and {requirements['actual_fields']} fields). "
            "Predictions from this artifact are provisional."
        )
    if bundle.missing_feature_counts:
        missing_desc = ", ".join(
            f"{key} ({count})" for key, count in sorted(bundle.missing_feature_counts.items())
        )
        limitations.append(f"Features with missing values, imputed with the training median: {missing_desc}.")
    if selected_name is None:
        limitations.append(
            "No trained model beat the transparent baseline on the validation split, so the "
            "baseline remains the active predictor."
        )

    metadata = ModelMetadata(
        model_name=model_name,
        model_version=version,
        trained_at=datetime.now(timezone.utc).isoformat(),
        target="soil_moisture_percentage",
        horizon_hours=HORIZON_HOURS,
        training_samples=len(train),
        validation_samples=len(validation),
        training_period_start=train[0].feature_time.isoformat() if train else None,
        training_period_end=train[-1].feature_time.isoformat() if train else None,
        validation_period_start=validation[0].feature_time.isoformat() if validation else None,
        validation_period_end=validation[-1].feature_time.isoformat() if validation else None,
        fields_in_training=sorted({str(s.field_id) for s in train}),
        features=feature_names(),
        metrics=results["candidates"].get(candidate_name, {}),
        baseline_metrics=results.get("baseline", {}),
        comparison={
            "candidates": {
                name: {
                    "validation_mae": (result.get("validation") or {}).get("mae"),
                    "test_mae": (result.get("test") or {}).get("mae"),
                }
                for name, result in results.get("candidates", {}).items()
            },
            "baseline_validation_mae": (
                (results.get("baseline", {}).get("persistence", {}).get("validation") or {}).get("mae")
            ),
            "selected": selected_name,
            "reason": reason,
        },
        imputation_medians=imputer.to_dict(),
        data_limitations=limitations,
        minimum_production_requirements=requirements,
        selected=selected_name is not None,
        selection_reason=reason,
        hyperparameters={"seed": seed, "horizon_hours": HORIZON_HOURS, "candidate": candidate_name},
    )

    artifact = ModelArtifact(model=estimator, metadata=metadata, imputer=imputer)
    if save:
        save_artifact(artifact)
    return artifact


def feature_importance(artifact: ModelArtifact) -> dict[str, float]:
    """Top feature importances, when the estimator exposes them."""
    estimator = artifact.model
    importances = getattr(estimator, "feature_importances_", None)
    if importances is None:
        return {}
    names = list(artifact.imputer.medians.keys())
    pairs = sorted(zip(names, [float(v) for v in importances]), key=lambda item: item[1], reverse=True)
    return {name: round(value, 6) for name, value in pairs[:15]}
