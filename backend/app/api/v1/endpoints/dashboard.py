from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone, timedelta
from uuid import UUID

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.base import Profile, Field, SensorReading, WeatherRecord
from app.crud import (
    get_dashboard_summary,
    get_field_moisture_summaries,
    get_alerts,
    moisture_condition,
    get_field_by_id,
    get_latest_reading_for_field,
)

router = APIRouter()


@router.get("/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    return get_dashboard_summary(db, current_user.id)


@router.get("/fields")
def dashboard_fields(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    return get_field_moisture_summaries(db, current_user.id)


@router.get("/alerts")
def dashboard_alerts(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    return get_alerts(db, current_user.id)


@router.get("/latest/{field_id}")
def latest_sensor(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    field = get_field_by_id(db, field_id, current_user.id)
    if not field:
        return {"error": "Field not found"}
    r = get_latest_reading_for_field(db, field_id)
    if not r:
        return {
            "field_id": field.id,
            "field_name": field.field_name,
            "moisture": None,
            "soil_temperature": None,
            "recorded_at": None,
            "moisture_condition": "unknown",
        }
    return {
        "field_id": field.id,
        "field_name": field.field_name,
        "moisture": r.moisture_percentage,
        "soil_temperature": r.soil_temperature,
        "growth_stage": r.growth_stage,
        "recorded_at": r.recorded_at,
        "ingested_at": r.ingested_at,
        "moisture_condition": moisture_condition(r.moisture_percentage),
    }
