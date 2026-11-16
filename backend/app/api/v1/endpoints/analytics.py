"""Water usage analytics endpoints.

All totals are built from **measured** irrigation events only. Schedules and
predictions are reported separately as planned volume.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.ml.pipelines.irrigation_pipeline import schedule_to_dict
from app.models.base import Field, Profile, SensorReading
from app.models.irrigation import IrrigationEvent, IrrigationSchedule
from app.schemas.irrigation import DashboardAnalyticsResponse, WaterUsageResponse
from app.services.analytics import (
    period_totals,
    previous_period_comparison,
    resolve_timezone,
    water_usage,
)
from app.services.irrigation import field_state

router = APIRouter()

#: A sensor that reported within this window counts as "reporting recently".
RECENT_SENSOR_HOURS = 6


def _parse_datetime(value: Optional[str], field: str) -> Optional[datetime]:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field} must be an ISO-8601 timestamp",
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@router.get("/water-usage", response_model=WaterUsageResponse)
def get_water_usage(
    field_id: Optional[int] = Query(default=None, gt=0),
    start: Optional[str] = Query(default=None),
    end: Optional[str] = Query(default=None),
    tz: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Measured water usage with field, crop and period breakdowns."""
    zone = resolve_timezone(tz)
    summary = water_usage(
        db,
        current_user.id,
        field_id=field_id,
        start=_parse_datetime(start, "start"),
        end=_parse_datetime(end, "end"),
        tz=zone,
    )
    return WaterUsageResponse(**summary.to_dict())


@router.get("/water-usage/fields", response_model=dict)
def get_water_usage_by_field(
    start: Optional[str] = Query(default=None),
    end: Optional[str] = Query(default=None),
    tz: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Per-field water usage, litres per acre and event counts."""
    zone = resolve_timezone(tz)
    summary = water_usage(
        db,
        current_user.id,
        start=_parse_datetime(start, "start"),
        end=_parse_datetime(end, "end"),
        tz=zone,
    )
    return {
        "fields": summary.by_field,
        "total_litres": summary.total_litres,
        "measured_event_count": summary.measured_event_count,
        "unmeasured_event_count": summary.unmeasured_event_count,
        "litres_per_acre": summary.litres_per_acre,
        "timezone": str(zone),
        "data_notes": summary.data_notes,
    }


@router.get("/water-usage/trends", response_model=dict)
def get_water_usage_trends(
    days: int = Query(default=30, ge=1, le=365),
    tz: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Daily, weekly and monthly consumption series plus period comparison."""
    zone = resolve_timezone(tz)
    summary = water_usage(db, current_user.id, tz=zone)
    comparison = previous_period_comparison(db, current_user.id, tz=zone, days=days)
    periods = period_totals(db, current_user.id, tz=zone)
    return {
        "daily": summary.daily_series,
        "weekly": summary.weekly_series,
        "monthly": summary.monthly_series,
        "by_day": summary.by_day,
        "by_crop": summary.by_crop,
        "planned_vs_actual": summary.planned_vs_actual,
        "estimated_vs_actual": summary.estimated_vs_actual,
        "period_comparison": comparison,
        "period_totals": periods,
        "average_per_event_litres": summary.average_per_event_litres,
        "average_per_event_days": summary.average_per_event_days,
        "irrigation_frequency_per_week": summary.irrigation_frequency_per_week,
        "timezone": str(zone),
        "data_notes": summary.data_notes,
    }


@router.get("/dashboard", response_model=DashboardAnalyticsResponse)
def get_dashboard_analytics(
    tz: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Everything the dashboard needs in one consistent response."""
    zone = resolve_timezone(tz)
    now = datetime.now(timezone.utc)
    today = now.astimezone(zone).date()

    fields = (
        db.execute(select(Field).where(Field.user_id == current_user.id).order_by(Field.field_name))
        .scalars()
        .all()
    )

    status_counts: dict[str, int] = {}
    needs_update: list[dict] = []
    healthy = 0
    attention = 0
    without_data = 0
    recent_sensors = 0

    for field in fields:
        latest = (
            db.execute(
                select(SensorReading)
                .where(SensorReading.field_id == field.id)
                .order_by(SensorReading.recorded_at.desc())
                .limit(1)
            )
            .scalars()
            .first()
        )
        sensor_count = len(
            db.execute(
                select(SensorReading.id).where(SensorReading.field_id == field.id).limit(1)
            )
            .scalars()
            .all()
        )
        has_sensor = sensor_count > 0
        uses_sensor = bool(latest and (latest.sensor_id is not None or latest.source == "iot_sensor"))
        state = field_state(
            moisture=latest.moisture_percentage if latest else None,
            recorded_at=latest.recorded_at if latest else None,
            has_sensor=has_sensor,
            uses_sensor=uses_sensor,
            crop_type=field.crop_type,
            soil_type=field.soil_type,
            now=now,
        )
        status_counts[state["status"]] = status_counts.get(state["status"], 0) + 1
        if state["status"] == "healthy":
            healthy += 1
        elif state["status"] in ("no_data", "sensor_unavailable"):
            without_data += 1
            attention += 1
        else:
            attention += 1

        if latest is not None and uses_sensor:
            age_hours = (now - latest.recorded_at).total_seconds() / 3600.0
            if age_hours <= RECENT_SENSOR_HOURS:
                recent_sensors += 1

        if state["freshness"] in ("stale", "missing"):
            needs_update.append(
                {
                    "field_id": field.id,
                    "field_name": field.field_name,
                    "freshness": state["freshness"],
                    "age_hours": state["age_hours"],
                    "last_updated": latest.recorded_at.isoformat() if latest else None,
                    "has_sensor": has_sensor,
                }
            )

    summary = water_usage(db, current_user.id, tz=zone)
    periods = period_totals(db, current_user.id, tz=zone)

    schedules = (
        db.execute(
            select(IrrigationSchedule).where(
                IrrigationSchedule.user_id == current_user.id,
                IrrigationSchedule.scheduled_date == today,
            )
        )
        .scalars()
        .all()
    )
    scheduled_volume = 0.0
    scheduled_fields = 0
    needing_irrigation = 0
    for row in schedules:
        if row.status in ("pending", "accepted"):
            scheduled_fields += 1
            if row.estimated_volume_litres:
                scheduled_volume += float(row.estimated_volume_litres)
        if row.priority in ("high", "critical"):
            needing_irrigation += 1

    recent_events = (
        db.execute(
            select(IrrigationEvent)
            .where(IrrigationEvent.user_id == current_user.id)
            .order_by(IrrigationEvent.start_time.desc())
            .limit(8)
        )
        .scalars()
        .all()
    )

    moisture_distribution = [
        {"status": key, "count": value}
        for key, value in sorted(status_counts.items(), key=lambda item: -item[1])
    ]

    notes = list(summary.data_notes)
    if not summary.measured_event_count:
        notes.append(
            "No measured irrigation volume has been recorded yet, so the water charts are empty."
        )

    return DashboardAnalyticsResponse(
        total_fields=len(fields),
        fields_healthy=healthy,
        fields_requiring_attention=attention,
        fields_without_data=without_data,
        sensors_reporting_recently=recent_sensors,
        water_usage_today_litres=periods["today"]["litres"],
        water_usage_this_week_litres=periods["this_week"]["litres"],
        water_usage_this_month_litres=periods["this_month"]["litres"],
        scheduled_volume_today_litres=round(scheduled_volume, 1),
        scheduled_fields_today=scheduled_fields,
        fields_needing_irrigation_today=needing_irrigation,
        moisture_status_distribution=moisture_distribution,
        crop_water_usage=summary.by_crop,
        field_water_usage=summary.by_field,
        fields_needing_updated_measurements=needs_update,
        recent_irrigation_events=[
            {
                "id": event.id,
                "field_id": event.field_id,
                "field_name": event.field.field_name if event.field else None,
                "start_time": event.start_time.isoformat(),
                "duration_minutes": event.duration_minutes,
                "water_volume_litres": event.water_volume_litres,
                "volume_measured": event.water_volume_litres is not None,
                "application_method": event.application_method,
            }
            for event in recent_events
        ],
        daily_water_series=summary.daily_series,
        weekly_water_series=summary.weekly_series,
        monthly_water_series=summary.monthly_series,
        planned_vs_actual=summary.planned_vs_actual,
        data_notes=notes,
        timezone=str(zone),
        generated_at=now,
    )


@router.get("/schedule-preview", response_model=dict)
def get_schedule_preview(
    tz: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    """Stored schedule rows for a range, without regenerating them."""
    zone = resolve_timezone(tz)
    rows = (
        db.execute(
            select(IrrigationSchedule)
            .where(IrrigationSchedule.user_id == current_user.id)
            .order_by(IrrigationSchedule.scheduled_date.desc())
            .limit(200)
        )
        .scalars()
        .all()
    )
    return {
        "entries": [schedule_to_dict(row) for row in rows],
        "timezone": str(zone),
    }
