"""Model artifact registry.

Model artifacts are stored on disk under ``backend/app/ml/artifacts`` (or the
directory configured with ``ML_ARTIFACT_DIR``). Each artifact has:

* a versioned directory ``<model_name>/<version>/``
* ``model.pkl``      – the fitted estimator
* ``metadata.json``  – training data size, features, training/validation
  periods, metrics, limitations and the feature order.

The registry never invents an artifact: when no artifact is present the
inference layer falls back to the transparent baseline and reports the
prediction as provisional.
"""

from __future__ import annotations

import json
import os
import pickle
import shutil
from dataclasses import asdict, dataclass, field as dataclass_field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

DEFAULT_ARTIFACT_ROOT = Path(__file__).resolve().parents[1] / "artifacts"


def artifact_root() -> Path:
    configured = os.environ.get("ML_ARTIFACT_DIR")
    root = Path(configured).expanduser() if configured else DEFAULT_ARTIFACT_ROOT
    root.mkdir(parents=True, exist_ok=True)
    return root


@dataclass
class ModelMetadata:
    """Everything needed to describe and audit a trained model."""

    model_name: str
    model_version: str
    trained_at: str
    target: str
    horizon_hours: int
    training_samples: int
    validation_samples: int
    training_period_start: Optional[str]
    training_period_end: Optional[str]
    validation_period_start: Optional[str]
    validation_period_end: Optional[str]
    fields_in_training: list[str] = dataclass_field(default_factory=list)
    features: list[str] = dataclass_field(default_factory=list)
    metrics: dict[str, Any] = dataclass_field(default_factory=dict)
    baseline_metrics: dict[str, Any] = dataclass_field(default_factory=dict)
    comparison: dict[str, Any] = dataclass_field(default_factory=dict)
    imputation_medians: dict[str, float] = dataclass_field(default_factory=dict)
    data_limitations: list[str] = dataclass_field(default_factory=list)
    minimum_production_requirements: dict[str, Any] = dataclass_field(default_factory=dict)
    selected: bool = False
    selection_reason: str = ""
    hyperparameters: dict[str, Any] = dataclass_field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelMetadata":
        known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**known)


@dataclass
class ModelArtifact:
    """A fitted estimator together with its metadata."""

    model: Any
    metadata: ModelMetadata
    imputer: Any

    def predict(self, rows: list[list[float]]) -> list[float]:
        return [float(value) for value in self.model.predict(rows)]


def save_artifact(artifact: ModelArtifact) -> Path:
    """Write an artifact to the registry and return its directory."""
    meta = artifact.metadata
    target_dir = artifact_root() / meta.model_name / meta.model_version
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    with (target_dir / "model.pkl").open("wb") as handle:
        pickle.dump(artifact.model, handle)
    with (target_dir / "metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(meta.to_dict(), handle, indent=2, sort_keys=True)
    with (target_dir / "imputer.json").open("w", encoding="utf-8") as handle:
        json.dump(artifact.imputer.to_dict(), handle, indent=2, sort_keys=True)
    return target_dir


def list_versions(model_name: Optional[str] = None) -> list[dict[str, Any]]:
    """List stored model versions, newest first."""
    root = artifact_root()
    entries: list[dict[str, Any]] = []
    names = [model_name] if model_name else [p.name for p in root.iterdir() if p.is_dir()]
    for name in names:
        if not name:
            continue
        model_dir = root / name
        if not model_dir.is_dir():
            continue
        for version_dir in model_dir.iterdir():
            metadata_file = version_dir / "metadata.json"
            if not version_dir.is_dir() or not metadata_file.exists():
                continue
            with metadata_file.open(encoding="utf-8") as handle:
                metadata = json.load(handle)
            entries.append(
                {
                    "model_name": metadata.get("model_name"),
                    "model_version": metadata.get("model_version"),
                    "trained_at": metadata.get("trained_at"),
                    "training_samples": metadata.get("training_samples"),
                    "metrics": metadata.get("metrics"),
                    "selected": metadata.get("selected"),
                    "path": str(version_dir),
                }
            )
    entries.sort(key=lambda item: item.get("trained_at") or "", reverse=True)
    return entries


def load_artifact(model_name: str, model_version: str) -> Optional[ModelArtifact]:
    """Load one artifact; returns ``None`` when it does not exist."""
    from app.ml.preprocessing.imputer import MedianImputer

    version_dir = artifact_root() / model_name / model_version
    metadata_file = version_dir / "metadata.json"
    model_file = version_dir / "model.pkl"
    imputer_file = version_dir / "imputer.json"
    if not (metadata_file.exists() and model_file.exists() and imputer_file.exists()):
        return None

    with metadata_file.open(encoding="utf-8") as handle:
        metadata = ModelMetadata.from_dict(json.load(handle))
    with model_file.open("rb") as handle:
        model = pickle.load(handle)
    with imputer_file.open(encoding="utf-8") as handle:
        imputer = MedianImputer.from_dict(json.load(handle))
    return ModelArtifact(model=model, metadata=metadata, imputer=imputer)


def load_selected_artifact(model_name: Optional[str] = None) -> Optional[ModelArtifact]:
    """Load the most recent artifact that was selected as the active model.

    Only artifacts explicitly marked ``selected`` are returned. An artifact
    that failed to beat the transparent baseline is stored for auditing but
    is never used for inference.
    """
    for entry in list_versions(model_name):
        if not entry.get("selected"):
            continue
        artifact = load_artifact(entry["model_name"], entry["model_version"])
        if artifact is not None:
            return artifact
    return None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
