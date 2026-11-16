"""Irrigation intelligence endpoints.

All routes require an authenticated farmer and enforce ownership on the
farmer's own fields. A user-supplied farmer id is never trusted: the
ownership check always uses the authenticated profile.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.ml.inference.predictor import predict_field
from app.ml.models.registry import list_versions, load_selected_artifact
from app.ml.pipelines.irrigation_pipeline import (
    complete_schedule,
    generate_daily_schedule,
    get_field_settings,
    get_preferences,
    persist_prediction,
    schedule_to_dict,
)
from app.models.base import Field, Profile
from app.models.irrigation import (
    FarmerIrrigationPreference,
    FieldIrrigationSettings,
    IrrigationEvent,
    IrrigationPrediction,
    IrrigationSchedule,
)
from app.schemas.irrigation import (
    FarmerPreferenceIn,
    FarmerPreferenceOut,
    FieldIrrigationSettingsIn,
    FieldIrrigationSettingsOut,
    IrrigationEventCreate,
    IrrigationEventList,
    IrrigationEventOut,
    IrrigationScheduleOut,
    PredictionHistoryOut,
    PredictionResponse,
    ScheduleComplete,
    ScheduleSkip,
    ScheduleUpdate,
    TodayScheduleResponse,
)
from app.services.analytics import resolve_timezone
from app.services.irrigation import thresholds_for

router = APIRouter()

DECISION_SUPPORT_NOTICE = (
    "This schedule is decision support. Verdant does not control irrigation equipment; "
    "you decide whether and when to irrigate."
)


def _owned_field(db: Session, field_id: int, profile: Profile) -> Field:
    field = (
        db.execute(
            select(Field).where(Field.id == field_id, Field.user_id == profile.id)
        )
        .scalars()
        .first()
    )
    if field is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Field not found")
    return field


def _owned_schedule(db: Session, schedule_id: int, profile: Profile) -> IrrigationSchedule:
    row = (
        db.execute(
            select(IrrigationSchedule).where(
                IrrigationSchedule.id == schedule_id,
                IrrigationSchedule.user_id == profile.id,
            )
        )
        .scalars()
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Schedule entry not found"
        )
    return row


def _event_out(event: IrrigationEvent) -> IrrigationEventOut:
    return IrrigationEventOut(
        id=event.id,
        field_id=event.field_id,
        field_name=event.field.field_name if event.field else None,
        start_time=event.start_time,
        end_time=event.end_time,
        duration_minutes=event.duration_minutes,
        water_volume_litres=event.water_volume_litres,
        volume_measured=event.water_volume_litres is not None,
        application_method=event.application_method,
        water_source=event.water_source,
        recorded_by=event.recorded_by,
        notes=event.notes,
        created_at=event.created_at,
    )


# --------------------------------------------------------------------------
# Predictions
# --------------------------------------------------------------------------

@router.get("/predictions/{field_id}", response_model=PredictionResponse)
def get_field_prediction(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Explainable irrigation requirement prediction for one field."""
    field = _owned_field(db, field_id, current_user)
    outcome = predict_field(db, field)
    thresholds = thresholds_for(field.crop_type, field.soil_type)

    prediction = persist_prediction(db, field, outcome, user_id=current_user.id)

    requirement = outcome.requirement
    net_depth = requirement.net_requirement_mm if requirement else None
    volume = requirement.gross_volume_litres if requirement else None

    recommended_date = None
    if net_depth is not None and net_depth > 0:
        recommended_date = outcome.predicted_at.date().isoformat()

    return PredictionResponse(
        field_id=field.id,
        field_name=field.field_name,
        predicted_at=outcome.predicted_at,
        target_time=outcome.target_time,
        current_moisture=outcome.current_moisture,
        predicted_moisture=outcome.predicted_moisture,
        moisture_trend_pp_per_day=outcome.moisture_trend_pp_per_day,
        irrigation_requirement_mm=net_depth,
        estimated_volume_litres=volume,
        recommended_date=recommended_date,
        model_name=outcome.model_name,
        model_version=outcome.model_version,
        model_status=outcome.model_status,
        confidence=outcome.confidence,
        uncertainty=outcome.uncertainty,
        provisional=outcome.provisional,
        reason=outcome.reason,
        data_freshness=outcome.data_freshness,
        calculation_version=requirement.calculation_version if requirement else None,
        requirement=requirement.to_dict() if requirement else None,
        input_refs=outcome.input_refs,
        limitations=outcome.limitations,
        prediction_id=prediction.id if prediction else None,
    )


@router.get("/predictions/{field_id}/history", response_model=list[PredictionHistoryOut])
def get_prediction_history(
    field_id: int,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    field = _owned_field(db, field_id, current_user)
    rows = (
        db.execute(
            select(IrrigationPrediction)
            .where(IrrigationPrediction.field_id == field.id)
            .order_by(IrrigationPrediction.predicted_at.desc())
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )
    return rows


# --------------------------------------------------------------------------
# Schedule
# --------------------------------------------------------------------------

@router.get("/schedule/today", response_model=TodayScheduleResponse)
def get_today_schedule(
    tz: Optional[str] = Query(default=None, description="IANA timezone name"),
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Generate (or reuse) today's schedule for the signed-in farmer."""
    zone = resolve_timezone(tz)
    today = datetime.now(timezone.utc).astimezone(zone).date()
    entries = generate_daily_schedule(db, current_user, scheduled_date=today)
    total = sum(
        float(entry.get("estimated_volume_litres") or 0.0)
        for entry in entries
        if entry.get("status") in ("pending", "accepted")
    )
    return TodayScheduleResponse(
        date=today.isoformat(),
        timezone=str(zone),
        entries=[IrrigationScheduleOut(**entry) for entry in entries],
        total_estimated_litres=round(total, 1),
        decision_support_notice=DECISION_SUPPORT_NOTICE,
        generated_at=datetime.now(timezone.utc),
    )


@router.get("/schedule", response_model=list[IrrigationScheduleOut])
def list_schedules(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    field_id: Optional[int] = Query(default=None, gt=0),
    schedule_status: Optional[str] = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    query = select(IrrigationSchedule).where(IrrigationSchedule.user_id == current_user.id)
    if start_date is not None:
        query = query.where(IrrigationSchedule.scheduled_date >= start_date)
    if end_date is not None:
        query = query.where(IrrigationSchedule.scheduled_date <= end_date)
    if field_id is not None:
        _owned_field(db, field_id, current_user)
        query = query.where(IrrigationSchedule.field_id == field_id)
    if schedule_status:
        query = query.where(IrrigationSchedule.status == schedule_status)
    rows = (
        db.execute(query.order_by(IrrigationSchedule.scheduled_date.desc()).limit(limit).offset(offset))
        .scalars()
        .all()
    )
    return [IrrigationScheduleOut(**schedule_to_dict(row)) for row in rows]


@router.post("/schedule/{schedule_id}/accept", response_model=IrrigationScheduleOut)
def accept_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Accept a recommendation. Acceptance never starts irrigation."""
    row = _owned_schedule(db, schedule_id, current_user)
    if row.status in ("completed", "skipped", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This schedule entry is already {row.status}.",
        )
    row.status = "accepted"
    db.add(row)
    db.commit()
    db.refresh(row)
    return IrrigationScheduleOut(**schedule_to_dict(row))


@router.post("/schedule/{schedule_id}/skip", response_model=IrrigationScheduleOut)
def skip_schedule(
    schedule_id: int,
    payload: Optional[ScheduleSkip] = None,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Skip a recommendation; the original estimate is preserved."""
    row = _owned_schedule(db, schedule_id, current_user)
    if row.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This schedule entry is already completed.",
        )
    row.status = "skipped"
    if payload and payload.reason:
        note = payload.reason
        row.reason = f"{row.reason} (skipped: {note})" if row.reason else f"Skipped: {note}"
    db.add(row)
    db.commit()
    db.refresh(row)
    return IrrigationScheduleOut(**schedule_to_dict(row))


@router.patch("/schedule/{schedule_id}", response_model=IrrigationScheduleOut)
def update_schedule(
    schedule_id: int,
    payload: ScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Edit a pending recommendation."""
    row = _owned_schedule(db, schedule_id, current_user)
    if row.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A completed schedule entry can no longer be edited.",
        )
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        if key == "notes":
            continue
        setattr(row, key, value)
    if payload.notes:
        existing = row.input_snapshot or {}
        if isinstance(existing, dict):
            existing["farmer_notes"] = payload.notes
            row.input_snapshot = existing
    db.add(row)
    db.commit()
    db.refresh(row)
    return IrrigationScheduleOut(**schedule_to_dict(row))


@router.post("/schedule/{schedule_id}/complete", response_model=IrrigationScheduleOut)
def complete_schedule_entry(
    schedule_id: int,
    payload: ScheduleComplete,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Complete a recommendation and record the measured irrigation event."""
    row = _owned_schedule(db, schedule_id, current_user)
    if row.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This schedule entry is already completed.",
        )
    complete_schedule(
        db,
        row,
        actual_volume_litres=payload.actual_volume_litres,
        actual_duration_minutes=payload.actual_duration_minutes,
        actual_start_time=payload.actual_start_time,
        actual_end_time=payload.actual_end_time,
        notes=payload.notes,
        application_method=payload.application_method,
        water_source=payload.water_source,
    )
    db.refresh(row)
    return IrrigationScheduleOut(**schedule_to_dict(row))


# --------------------------------------------------------------------------
# Events
# --------------------------------------------------------------------------

@router.post("/events", response_model=IrrigationEventOut, status_code=status.HTTP_201_CREATED)
def create_event(
    payload: IrrigationEventCreate,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Record a measured irrigation event."""
    field = _owned_field(db, payload.field_id, current_user)

    start_time = payload.start_time
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    start_time = start_time.astimezone(timezone.utc)

    end_time = payload.end_time
    if end_time is not None:
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)
        end_time = end_time.astimezone(timezone.utc)

    event = IrrigationEvent(
        user_id=current_user.id,
        field_id=field.id,
        start_time=start_time,
        end_time=end_time,
        duration_minutes=payload.duration_minutes,
        water_volume_litres=payload.water_volume_litres,
        application_method=payload.application_method,
        water_source=payload.water_source,
        recorded_by="manual",
        notes=payload.notes,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return _event_out(event)


@router.get("/events", response_model=IrrigationEventList)
def list_events(
    field_id: Optional[int] = Query(default=None, gt=0),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """List measured irrigation events for the signed-in farmer."""
    query = select(IrrigationEvent).where(IrrigationEvent.user_id == current_user.id)
    if field_id is not None:
        _owned_field(db, field_id, current_user)
        query = query.where(IrrigationEvent.field_id == field_id)
    if start_date is not None:
        query = query.where(IrrigationEvent.start_time >= start_date)
    if end_date is not None:
        query = query.where(IrrigationEvent.start_time <= end_date)
    total = len(db.execute(query).scalars().all())
    rows = (
        db.execute(query.order_by(IrrigationEvent.start_time.desc()).limit(limit).offset(offset))
        .scalars()
        .all()
    )
    return IrrigationEventList(
        items=[_event_out(row) for row in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


# --------------------------------------------------------------------------
# Settings and preferences
# --------------------------------------------------------------------------

@router.get("/fields/{field_id}/settings", response_model=FieldIrrigationSettingsOut)
def get_settings(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    field = _owned_field(db, field_id, current_user)
    settings = get_field_settings(db, field.id)
    if settings is None:
        return FieldIrrigationSettingsOut(field_id=field.id)
    return FieldIrrigationSettingsOut(
        field_id=settings.field_id,
        application_method=settings.application_method,
        application_rate_litres_per_hour=settings.application_rate_litres_per_hour,
        application_efficiency=settings.application_efficiency,
        water_source=settings.water_source,
        notes=settings.notes,
    )


@router.put("/fields/{field_id}/settings", response_model=FieldIrrigationSettingsOut)
def put_settings(
    field_id: int,
    payload: FieldIrrigationSettingsIn,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    field = _owned_field(db, field_id, current_user)
    settings = get_field_settings(db, field.id)
    if settings is None:
        settings = FieldIrrigationSettings(field_id=field.id)
        db.add(settings)
    settings.application_method = payload.application_method
    settings.application_rate_litres_per_hour = payload.application_rate_litres_per_hour
    settings.application_efficiency = payload.application_efficiency
    settings.water_source = payload.water_source
    settings.notes = payload.notes
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return FieldIrrigationSettingsOut(
        field_id=settings.field_id,
        application_method=settings.application_method,
        application_rate_litres_per_hour=settings.application_rate_litres_per_hour,
        application_efficiency=settings.application_efficiency,
        water_source=settings.water_source,
        notes=settings.notes,
    )


@router.get("/preferences", response_model=FarmerPreferenceOut)
def get_preference(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    preference = get_preferences(db, current_user.id)
    if preference is None:
        return FarmerPreferenceOut()
    return FarmerPreferenceOut(
        preferred_start_time=preference.preferred_start_time,
        preferred_end_time=preference.preferred_end_time,
        max_daily_volume_litres=preference.max_daily_volume_litres,
        irrigation_days=preference.irrigation_days,
        notes=preference.notes,
    )


@router.put("/preferences", response_model=FarmerPreferenceOut)
def put_preference(
    payload: FarmerPreferenceIn,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    preference = get_preferences(db, current_user.id)
    if preference is None:
        preference = FarmerIrrigationPreference(user_id=current_user.id)
        db.add(preference)
    if payload.preferred_start_time is not None:
        preference.preferred_start_time = payload.preferred_start_time
    if payload.preferred_end_time is not None:
        preference.preferred_end_time = payload.preferred_end_time
    if payload.max_daily_volume_litres is not None:
        preference.max_daily_volume_litres = payload.max_daily_volume_litres
    if payload.irrigation_days is not None:
        preference.irrigation_days = payload.irrigation_days
    if payload.notes is not None:
        preference.notes = payload.notes
    db.add(preference)
    db.commit()
    db.refresh(preference)
    return FarmerPreferenceOut(
        preferred_start_time=preference.preferred_start_time,
        preferred_end_time=preference.preferred_end_time,
        max_daily_volume_litres=preference.max_daily_volume_litres,
        irrigation_days=preference.irrigation_days,
        notes=preference.notes,
    )
