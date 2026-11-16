"""Inference: turn a field's history into an irrigation requirement.

The inference path is:

1. build the feature context for the field at the latest reading,
2. predict the soil moisture at the 24 h horizon with the promoted model, or
   with the transparent baseline when no usable model exists,
3. combine the predicted moisture with the soil water balance to obtain the
   irrigation depth and the water volume.

The result always states which source produced it and how confident it is.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.baselines.baselines import LinearTrendBaseline, PersistenceBaseline
from app.ml.features.engineering import (
    HORIZON_HOURS,
    FeatureContext,
    build_context,
)
from app.ml.models.registry import ModelArtifact, load_selected_artifact
from app.models.base import Field, SensorReading, WeatherRecord
from app.models.irrigation import IrrigationEvent
from app.services.agronomy import (
    WaterBalanceResult,
    compute_water_balance,
    effective_rainfall_mm,
    hargreaves_et0,
    scs_effective_rainfall,
)


@dataclass
class PredictionOutcome:
    """The outcome of one prediction for one field."""

    field_id: int
    predicted_at: datetime
    target_time: Optional[datetime]
    current_moisture: Optional[float]
    predicted_moisture: Optional[float]
    moisture_trend_pp_per_day: Optional[float]
    model_name: str
    model_version: Optional[str]
    model_status: str
    confidence: float
    uncertainty: Optional[float]
    provisional: bool
    requirement: Optional[WaterBalanceResult]
    reason: str
    data_freshness: str
    input_refs: dict[str, Any] = dataclass_field(default_factory=dict)
    limitations: list[str] = dataclass_field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_id": self.field_id,
            "predicted_at": self.predicted_at.isoformat(),
            "target_time": self.target_time.isoformat() if self.target_time else None,
            "current_moisture": self.current_moisture,
            "predicted_moisture": self.predicted_moisture,
            "moisture_trend_pp_per_day": self.moisture_trend_pp_per_day,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "model_status": self.model_status,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "provisional": self.provisional,
            "requirement": self.requirement.to_dict() if self.requirement else None,
            "reason": self.reason,
            "data_freshness": self.data_freshness,
            "input_refs": self.input_refs,
            "limitations": self.limitations,
        }


def _load_field_data(db: Session, field: Field) -> tuple[list[Any], list[Any], list[Any]]:
    readings = (
        db.execute(
            select(SensorReading)
            .where(SensorReading.field_id == field.id)
            .order_by(SensorReading.recorded_at)
        )
        .scalars()
        .all()
    )
    weather = (
        db.execute(
            select(WeatherRecord)
            .where(WeatherRecord.field_id == field.id)
            .order_by(WeatherRecord.recorded_at)
        )
        .scalars()
        .all()
    )
    events = (
        db.execute(
            select(IrrigationEvent)
            .where(IrrigationEvent.field_id == field.id)
            .order_by(IrrigationEvent.start_time)
        )
        .scalars()
        .all()
    )
    return list(readings), list(weather), list(events)


def _estimate_et0(
    field: Field,
    weather: list[Any],
    now: datetime,
) -> tuple[Optional[float], Optional[str]]:
    """Reference evapotranspiration from recorded weather only.

    Uses the Hargreaves equation with the temperature range observed for the
    field. Returns ``(et0, source)``; ``et0`` is ``None`` when the recorded
    weather does not contain a usable temperature range or the field has no
    coordinates.
    """
    if field.latitude is None:
        return None, None

    recent = [
        w
        for w in weather
        if getattr(w, "recorded_at", None) is not None
        and (now - w.recorded_at).total_seconds() <= 3 * 86400
    ]
    if len(recent) < 2:
        return None, None

    temps = [float(w.temperature) for w in recent if w.temperature is not None]
    if len(temps) < 2:
        return None, None

    t_min = min(temps)
    t_max = max(temps)
    et0 = hargreaves_et0(t_min, t_max, field.latitude, now.date())
    if et0 is None:
        return None, None
    return et0, "hargreaves_from_recorded_temperature_range"


def _freshness_of(latest: Optional[Any], now: datetime, uses_sensor: bool) -> tuple[str, Optional[float]]:
    if latest is None or getattr(latest, "recorded_at", None) is None:
        return "missing", None
    age_hours = (now - latest.recorded_at).total_seconds() / 3600.0
    if uses_sensor:
        if age_hours <= 2:
            return "fresh", age_hours
        if age_hours <= 24:
            return "delayed", age_hours
        return "stale", age_hours
    if age_hours <= 24:
        return "fresh", age_hours
    if age_hours <= 72:
        return "delayed", age_hours
    return "stale", age_hours


def predict_field(
    db: Session,
    field: Field,
    *,
    now: Optional[datetime] = None,
    artifact: Optional[ModelArtifact] = None,
    target_moisture: Optional[float] = None,
) -> PredictionOutcome:
    """Produce an irrigation requirement prediction for one field."""
    now = now or datetime.now(timezone.utc)
    readings, weather, events = _load_field_data(db, field)

    limitations: list[str] = []
    latest = readings[-1] if readings else None
    uses_sensor = bool(latest and (latest.sensor_id is not None or latest.source == "iot_sensor"))
    freshness, age_hours = _freshness_of(latest, now, uses_sensor)

    if latest is None:
        return PredictionOutcome(
            field_id=field.id,
            predicted_at=now,
            target_time=None,
            current_moisture=None,
            predicted_moisture=None,
            moisture_trend_pp_per_day=None,
            model_name="none",
            model_version=None,
            model_status="no_data",
            confidence=0.0,
            uncertainty=None,
            provisional=True,
            requirement=None,
            reason="No soil moisture reading exists for this field, so no requirement can be estimated.",
            data_freshness="missing",
            input_refs={"reading_count": 0},
            limitations=["A requirement cannot be estimated without a soil moisture reading."],
        )

    feature_time = latest.recorded_at
    context = build_context(
        at_time=feature_time,
        readings=readings,
        weather=weather,
        irrigation_events=events,
        crop_type=field.crop_type,
        soil_type=field.soil_type,
        growth_stage=field.growth_stage,
        area_acres=field.area_acres,
        sowing_date=field.sowing_date,
    )

    predicted_moisture: Optional[float]
    trend: Optional[float]
    model_name: str
    model_version: Optional[str]
    model_status: str
    provisional = True
    uncertainty: Optional[float] = None
    confidence = 0.4
    used_artifact = artifact if artifact is not None else load_selected_artifact()

    if used_artifact is not None:
        try:
            row = used_artifact.imputer.transform(context.values)
            predicted_moisture = float(used_artifact.model.predict(np.asarray([row], dtype=float))[0])
            model_name = used_artifact.metadata.model_name
            model_version = used_artifact.metadata.model_version
            requirements = used_artifact.metadata.minimum_production_requirements or {}
            if requirements.get("meets_requirements"):
                model_status = "validated"
                provisional = False
                confidence = 0.65
            else:
                model_status = "provisional"
                confidence = 0.45
            interval = (used_artifact.metadata.metrics or {}).get("residual_interval")
            if interval:
                uncertainty = float(interval[0])
        except Exception as exc:  # pragma: no cover - defensive
            used_artifact = None
            predicted_moisture = None
            limitations.append(f"The trained model could not be used ({exc}); the baseline was used instead.")
    else:
        predicted_moisture = None
        model_name = "baseline"
        model_version = None
        model_status = "baseline_only"

    if predicted_moisture is None:
        persistence = PersistenceBaseline().predict_one(context)
        trend_baseline = LinearTrendBaseline(horizon_hours=HORIZON_HOURS).predict_one(context)
        predicted_moisture = trend_baseline if trend_baseline is not None else persistence
        if predicted_moisture is None:
            predicted_moisture = float(context.values.get("current_moisture") or 0.0)
        model_name = "baseline:linear_trend" if trend_baseline is not None else "baseline:persistence"
        model_version = None
        model_status = "baseline_only"
        provisional = True
        confidence = 0.35
        limitations.append(
            "No promoted model artifact is available for this deployment; the transparent "
            "baseline (recent moisture trend) produced this estimate."
        )

    delta = predicted_moisture - float(context.values.get("current_moisture") or predicted_moisture)
    trend = round(delta / (HORIZON_HOURS / 24.0), 3)

    # --- water balance ----------------------------------------------------
    et0, et0_source = _estimate_et0(field, weather, now)
    if et0 is None:
        limitations.append(
            "No reference evapotranspiration could be estimated from the recorded weather for this field."
        )

    rainfall_window = [
        w.rainfall
        for w in weather
        if getattr(w, "recorded_at", None) is not None
        and (now - w.recorded_at).total_seconds() <= 3 * 86400
    ]
    rainfall_events = rainfall_window if rainfall_window else None

    requirement = compute_water_balance(
        current_moisture=predicted_moisture,
        crop_type=field.crop_type,
        soil_type=field.soil_type,
        growth_stage=field.growth_stage,
        area_acres=field.area_acres,
        latitude=field.latitude,
        et0_mm=et0,
        et0_source=et0_source,
        rainfall_events=rainfall_events,
        horizon_days=1.0,
        target_moisture=target_moisture,
    )

    if freshness == "stale":
        confidence = min(confidence, 0.25)
        limitations.append(
            "The latest reading is stale, so the requirement is uncertain and must be confirmed in the field."
        )
    elif freshness == "missing":
        confidence = min(confidence, 0.2)

    reason = _build_reason(
        field=field,
        current_moisture=context.values.get("current_moisture"),
        predicted_moisture=predicted_moisture,
        trend=trend,
        requirement=requirement,
        freshness=freshness,
        age_hours=age_hours,
    )

    return PredictionOutcome(
        field_id=field.id,
        predicted_at=now,
        target_time=feature_time + timedelta(hours=HORIZON_HOURS),
        current_moisture=context.values.get("current_moisture"),
        predicted_moisture=round(predicted_moisture, 2),
        moisture_trend_pp_per_day=trend,
        model_name=model_name,
        model_version=model_version,
        model_status=model_status,
        confidence=round(confidence, 2),
        uncertainty=round(uncertainty, 2) if uncertainty is not None else None,
        provisional=provisional,
        requirement=requirement,
        reason=reason,
        data_freshness=freshness,
        input_refs={
            "latest_reading_id": getattr(latest, "id", None),
            "latest_recorded_at": feature_time.isoformat() if feature_time else None,
            "reading_count": len(readings),
            "weather_record_count": len(weather),
            "irrigation_event_count": len(events),
            "age_hours": round(age_hours, 2) if age_hours is not None else None,
            "horizon_hours": HORIZON_HOURS,
        },
        limitations=limitations,
    )


def _build_reason(
    *,
    field: Field,
    current_moisture: Optional[float],
    predicted_moisture: Optional[float],
    trend: Optional[float],
    requirement: WaterBalanceResult,
    freshness: str,
    age_hours: Optional[float],
) -> str:
    parts: list[str] = []
    if current_moisture is not None:
        parts.append(f"Latest measured moisture is {current_moisture:.1f}%.")
    if predicted_moisture is not None:
        parts.append(
            f"The predicted moisture in 24 hours is {predicted_moisture:.1f}%"
            + (f" ({trend:+.1f} points per day)." if trend is not None else ".")
        )
    depth = requirement.net_requirement_mm
    if depth is not None and depth > 0:
        parts.append(f"The soil water balance gives a net requirement of {depth:.1f} mm.")
        if requirement.gross_volume_litres:
            parts.append(f"That is about {requirement.gross_volume_litres:,.0f} litres for this field.")
    elif depth is not None:
        parts.append("The soil water balance does not indicate a water deficit right now.")
    if freshness in ("stale", "missing"):
        parts.append(
            "The underlying measurement is not current, so this recommendation is uncertain "
            "and should be confirmed in the field."
        )
    elif age_hours is not None:
        parts.append(f"The reading is {age_hours:.1f} hours old.")
    parts.append(
        f"Crop {field.crop_type} at the {field.growth_stage} stage in {field.soil_type}."
    )
    return " ".join(parts)
