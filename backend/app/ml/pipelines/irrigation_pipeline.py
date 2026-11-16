"""End-to-end irrigation intelligence pipeline.

This module glues the pieces together for the API layer:

* build the prediction (model or transparent baseline),
* persist it as an :class:`IrrigationPrediction`,
* derive the daily schedule entries,
* keep measured irrigation events separate from estimates.

It contains no HTTP concerns, so it can be reused by scripts and tests.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ml.inference.predictor import PredictionOutcome, predict_field
from app.models.base import Field, Profile
from app.models.irrigation import (
    FarmerIrrigationPreference,
    FieldIrrigationSettings,
    IrrigationEvent,
    IrrigationPrediction,
    IrrigationSchedule,
)
from app.services.agronomy import duration_minutes_for_volume
from app.services.irrigation import thresholds_for


def _local_now(now: Optional[datetime] = None) -> datetime:
    return now or datetime.now(timezone.utc)


def persist_prediction(
    db: Session,
    field: Field,
    outcome: PredictionOutcome,
    *,
    user_id: Optional[Any] = None,
    min_interval_minutes: int = 30,
) -> Optional[IrrigationPrediction]:
    """Store a prediction outcome for auditing and comparison.

    Repeated calls within ``min_interval_minutes`` reuse the stored record
    instead of writing a new one, so simply opening the field page does not
    flood the prediction history.
    """
    latest = (
        db.execute(
            select(IrrigationPrediction)
            .where(IrrigationPrediction.field_id == field.id)
            .order_by(IrrigationPrediction.predicted_at.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )
    if latest is not None:
        age = outcome.predicted_at - latest.predicted_at
        if age.total_seconds() < min_interval_minutes * 60:
            return latest

    requirement = outcome.requirement
    prediction = IrrigationPrediction(
        user_id=user_id or field.user_id,
        field_id=field.id,
        predicted_at=outcome.predicted_at,
        target_time=outcome.target_time,
        current_moisture=outcome.current_moisture,
        predicted_moisture=outcome.predicted_moisture,
        moisture_trend=outcome.moisture_trend_pp_per_day,
        irrigation_requirement_mm=requirement.net_requirement_mm if requirement else None,
        estimated_volume_litres=requirement.gross_volume_litres if requirement else None,
        model_name=outcome.model_name,
        model_version=outcome.model_version,
        calculation_version=requirement.calculation_version if requirement else None,
        confidence=outcome.confidence,
        uncertainty=outcome.uncertainty,
        status="provisional" if outcome.provisional else "validated",
        data_freshness=outcome.data_freshness,
        reason=outcome.reason,
        input_refs=outcome.input_refs,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def get_field_settings(db: Session, field_id: int) -> Optional[FieldIrrigationSettings]:
    return (
        db.execute(
            select(FieldIrrigationSettings).where(FieldIrrigationSettings.field_id == field_id)
        )
        .scalars()
        .first()
    )


def get_preferences(db: Session, user_id: Any) -> Optional[FarmerIrrigationPreference]:
    return (
        db.execute(
            select(FarmerIrrigationPreference).where(FarmerIrrigationPreference.user_id == user_id)
        )
        .scalars()
        .first()
    )


def build_schedule_entry(
    db: Session,
    field: Field,
    outcome: PredictionOutcome,
    *,
    scheduled_date: date,
    preferences: Optional[FarmerIrrigationPreference] = None,
    settings: Optional[FieldIrrigationSettings] = None,
) -> dict[str, Any]:
    """Turn a prediction into an explainable schedule entry.

    The entry describes *what should happen today* and *why*. It never
    presents itself as an automated controller.
    """
    thresholds = thresholds_for(field.crop_type, field.soil_type)
    requirement = outcome.requirement

    depth = requirement.net_requirement_mm if requirement else None
    volume = requirement.gross_volume_litres if requirement else None

    if outcome.data_freshness in ("stale", "missing"):
        # A depth computed from an outdated reading cannot be presented as a
        # recommendation, so no volume is proposed for the field.
        depth = None
        volume = None

    if settings is not None and settings.application_efficiency:
        efficiency = float(settings.application_efficiency)
        if requirement is not None and requirement.net_requirement_mm is not None:
            gross_depth = requirement.net_requirement_mm / efficiency
            volume = gross_depth * (requirement.area_ha or 0.0) * 10_000.0

    rate = settings.application_rate_litres_per_hour if settings else None
    duration = duration_minutes_for_volume(volume, rate)

    predicted = outcome.predicted_moisture
    below_band = predicted is not None and predicted < thresholds["low"]
    critical = predicted is not None and predicted <= thresholds["low"] - 5

    if outcome.data_freshness in ("stale", "missing"):
        priority = "uncertain"
    elif critical:
        priority = "critical"
    elif predicted is not None and predicted < thresholds["low"] - 3:
        priority = "high"
    elif below_band:
        priority = "medium"
    else:
        priority = "low"

    if priority == "uncertain":
        reason_code = "stale_or_missing_data"
        reason = (
            "The latest soil moisture reading is not current, so no volume is recommended. "
            "Check the field or the sensor before deciding to irrigate."
        )
    elif below_band:
        reason_code = "below_target_band"
        reason = (
            f"Predicted moisture ({predicted:.1f}%) is below the {field.crop_type} band "
            f"({thresholds['low']:.1f}–{thresholds['high']:.1f}%) for {field.soil_type}. "
            f"The soil water balance gives {depth:.1f} mm"
            + (f", about {volume:,.0f} litres." if volume else ".")
        )
    else:
        reason_code = "within_target_band"
        reason = (
            f"Predicted moisture ({predicted:.1f}%) is inside the {field.crop_type} band "
            f"({thresholds['low']:.1f}–{thresholds['high']:.1f}%). "
            "Irrigation is not required today; re-check after the next reading."
        )

    start_time = None
    if preferences is not None and preferences.preferred_start_time:
        start_time = preferences.preferred_start_time
    end_time = None
    if preferences is not None and preferences.preferred_end_time:
        end_time = preferences.preferred_end_time

    confidence = outcome.confidence
    if outcome.provisional:
        confidence = min(confidence, 0.5)

    uncertainty_litres = None
    if volume is not None and outcome.uncertainty is not None:
        uncertainty_litres = round(volume * float(outcome.uncertainty) / 100.0, 1)

    return {
        "field_id": field.id,
        "field_name": field.field_name,
        "crop_type": field.crop_type,
        "area_acres": field.area_acres,
        "scheduled_date": scheduled_date,
        "recommended_start_time": start_time,
        "recommended_window_end": end_time,
        "estimated_volume_litres": round(volume, 1) if volume is not None else None,
        "estimated_duration_minutes": duration,
        "estimated_depth_mm": round(depth, 2) if depth is not None else None,
        "priority": priority,
        "reason": reason,
        "reason_code": reason_code,
        "model_version": outcome.model_version or outcome.model_name,
        "confidence": round(confidence, 2),
        "uncertainty_litres": uncertainty_litres,
        "status": "pending",
        "predicted_moisture": predicted,
        "current_moisture": outcome.current_moisture,
        "data_freshness": outcome.data_freshness,
        "provisional": outcome.provisional,
        "reason_note": (
            "This is decision support, not an automatic irrigation controller. "
            "You decide whether and when to irrigate."
        ),
    }


def generate_daily_schedule(
    db: Session,
    profile: Profile,
    *,
    scheduled_date: Optional[date] = None,
    now: Optional[datetime] = None,
) -> list[dict[str, Any]]:
    """Create (or refresh) today's schedule for one farmer.

    Duplicate prevention: one schedule row per field per date is enforced by
    a unique constraint, and existing rows are reused instead of duplicated.
    """
    now = _local_now(now)
    scheduled_date = scheduled_date or now.date()

    fields = (
        db.execute(select(Field).where(Field.user_id == profile.id).order_by(Field.field_name))
        .scalars()
        .all()
    )
    preferences = get_preferences(db, profile.id)

    existing = {
        row.field_id: row
        for row in db.execute(
            select(IrrigationSchedule).where(
                IrrigationSchedule.user_id == profile.id,
                IrrigationSchedule.scheduled_date == scheduled_date,
            )
        )
        .scalars()
        .all()
    }

    entries: list[dict[str, Any]] = []
    for field in fields:
        outcome = predict_field(db, field, now=now)
        settings = get_field_settings(db, field.id)
        entry = build_schedule_entry(
            db,
            field,
            outcome,
            scheduled_date=scheduled_date,
            preferences=preferences,
            settings=settings,
        )

        row = existing.get(field.id)
        if row is None:
            prediction = persist_prediction(db, field, outcome, user_id=profile.id)
            row = IrrigationSchedule(
                user_id=profile.id,
                field_id=field.id,
                scheduled_date=scheduled_date,
                prediction_id=prediction.id if prediction else None,
            )
            db.add(row)
            try:
                db.flush()
            except IntegrityError:
                db.rollback()
                row = (
                    db.execute(
                        select(IrrigationSchedule).where(
                            IrrigationSchedule.user_id == profile.id,
                            IrrigationSchedule.field_id == field.id,
                            IrrigationSchedule.scheduled_date == scheduled_date,
                        )
                    )
                    .scalars()
                    .first()
                )
        _apply_entry(row, entry)
        db.add(row)
        db.commit()
        db.refresh(row)
        entries.append(schedule_to_dict(row))

    return entries


def _apply_entry(row: IrrigationSchedule, entry: dict[str, Any]) -> None:
    """Write the computed entry onto a schedule row.

    A row the farmer already acted on keeps its status and the actual values;
    the original recommendation is preserved for comparison.
    """
    if row.status in ("accepted", "completed", "skipped", "cancelled") and row.id is not None:
        return
    row.recommended_start_time = entry["recommended_start_time"]
    row.recommended_window_end = entry["recommended_window_end"]
    row.estimated_volume_litres = entry["estimated_volume_litres"]
    row.estimated_duration_minutes = entry["estimated_duration_minutes"]
    row.estimated_depth_mm = entry["estimated_depth_mm"]
    row.priority = entry["priority"]
    row.reason = entry["reason"]
    row.reason_code = entry["reason_code"]
    row.model_version = entry["model_version"]
    row.confidence = entry["confidence"]
    row.uncertainty_litres = entry["uncertainty_litres"]
    row.input_snapshot = {
        "predicted_moisture": entry["predicted_moisture"],
        "current_moisture": entry["current_moisture"],
        "data_freshness": entry["data_freshness"],
        "provisional": entry["provisional"],
    }


def schedule_to_dict(row: IrrigationSchedule) -> dict[str, Any]:
    return {
        "id": row.id,
        "field_id": row.field_id,
        "field_name": row.field.field_name if row.field else None,
        "scheduled_date": row.scheduled_date.isoformat() if row.scheduled_date else None,
        "recommended_start_time": (
            row.recommended_start_time.strftime("%H:%M") if row.recommended_start_time else None
        ),
        "recommended_window_end": (
            row.recommended_window_end.strftime("%H:%M") if row.recommended_window_end else None
        ),
        "estimated_volume_litres": row.estimated_volume_litres,
        "estimated_duration_minutes": row.estimated_duration_minutes,
        "estimated_depth_mm": row.estimated_depth_mm,
        "priority": row.priority,
        "reason": row.reason,
        "reason_code": row.reason_code,
        "model_version": row.model_version,
        "confidence": row.confidence,
        "uncertainty_litres": row.uncertainty_litres,
        "status": row.status,
        "actual_volume_litres": row.actual_volume_litres,
        "actual_duration_minutes": row.actual_duration_minutes,
        "completed_at": row.completed_at.isoformat() if row.completed_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "prediction_id": row.prediction_id,
        "is_decision_support": True,
    }


def complete_schedule(
    db: Session,
    row: IrrigationSchedule,
    *,
    actual_volume_litres: Optional[float],
    actual_duration_minutes: Optional[float],
    actual_start_time: Optional[datetime] = None,
    actual_end_time: Optional[datetime] = None,
    notes: Optional[str] = None,
    application_method: Optional[str] = None,
    water_source: Optional[str] = None,
) -> tuple[IrrigationSchedule, IrrigationEvent]:
    """Complete a schedule entry and record the measured irrigation event."""
    now = datetime.now(timezone.utc)
    start = actual_start_time or now
    end = actual_end_time or (start + timedelta(minutes=actual_duration_minutes or 0))

    event = IrrigationEvent(
        user_id=row.user_id,
        field_id=row.field_id,
        start_time=start,
        end_time=end,
        duration_minutes=actual_duration_minutes,
        water_volume_litres=actual_volume_litres,
        application_method=application_method,
        water_source=water_source,
        recorded_by="manual",
        notes=notes,
    )
    db.add(event)

    row.status = "completed"
    row.completed_at = now
    row.actual_volume_litres = actual_volume_litres
    row.actual_duration_minutes = actual_duration_minutes
    row.actual_start_time = start
    row.actual_end_time = end
    db.add(row)
    db.commit()
    db.refresh(event)
    db.refresh(row)
    return row, event
