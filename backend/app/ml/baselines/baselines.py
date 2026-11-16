"""Transparent baselines.

These are the reference points every trained model has to beat. They are
intentionally simple and explainable:

* ``persistence``    – the moisture reading stays as it is.
* ``linear_trend``   – the recent rate of change continues for the horizon.
* ``field_mean``     – the field's historical mean moisture.

They are also the fallback used for inference when no promoted model exists.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

from app.ml.features.engineering import FeatureContext


class PersistenceBaseline:
    """Predict the current moisture at the target horizon."""

    name = "persistence"

    def predict(self, contexts: Sequence[FeatureContext]) -> list[float]:
        predictions = []
        for context in contexts:
            value = context.values.get("current_moisture")
            predictions.append(float(value) if value is not None else float("nan"))
        return predictions

    def predict_one(self, context: FeatureContext) -> Optional[float]:
        value = context.values.get("current_moisture")
        return float(value) if value is not None else None


class LinearTrendBaseline:
    """Extrapolate the recent moisture trend over the horizon."""

    name = "linear_trend"

    def __init__(self, horizon_hours: int = 24):
        self.horizon_hours = horizon_hours

    def predict(self, contexts: Sequence[FeatureContext]) -> list[float]:
        return [self._predict_one(context) for context in contexts]

    def _predict_one(self, context: FeatureContext) -> float:
        current = context.values.get("current_moisture")
        if current is None:
            return float("nan")
        delta_6 = context.values.get("moisture_delta_6h")
        delta_12 = context.values.get("moisture_delta_12h")
        delta_24 = context.values.get("moisture_delta_24h")
        deltas = [d for d in (delta_6, delta_12, delta_24) if d is not None]
        if not deltas:
            return float(current)
        average_delta = sum(deltas) / len(deltas)
        # Average deltas cover 6/12/24 h; normalise to a per-hour rate.
        hours_covered = sum(
            h for h, d in ((6, delta_6), (12, delta_12), (24, delta_24)) if d is not None
        ) / max(1, len(deltas))
        rate_per_hour = average_delta / max(1.0, hours_covered)
        return float(current) + rate_per_hour * self.horizon_hours

    def predict_one(self, context: FeatureContext) -> Optional[float]:
        value = self._predict_one(context)
        return None if value != value else value


class FieldMeanBaseline:
    """Predict the historical mean moisture of the field."""

    name = "field_mean"

    def __init__(self, field_means: Optional[dict[int, float]] = None):
        self.field_means = field_means or {}

    def predict(self, contexts: Sequence[FeatureContext]) -> list[float]:
        predictions = []
        for context in contexts:
            mean = self.field_means.get(context.meta.get("field_id", -1))
            current = context.values.get("current_moisture")
            value = mean if mean is not None else current
            predictions.append(float(value) if value is not None else float("nan"))
        return predictions

    def predict_one(self, context: FeatureContext) -> Optional[float]:
        mean = self.field_means.get(context.meta.get("field_id", -1))
        if mean is not None:
            return float(mean)
        current = context.values.get("current_moisture")
        return float(current) if current is not None else None


def default_baselines(horizon_hours: int = 24) -> list[Any]:
    return [PersistenceBaseline(), LinearTrendBaseline(horizon_hours=horizon_hours)]
