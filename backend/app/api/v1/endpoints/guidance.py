from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.base import Profile, Field, WeatherRecord
from app.crud import (
    get_field_by_id,
    get_fields_by_user,
    get_latest_reading_for_field,
    get_sensors_for_field,
)
from app.services.irrigation import build_guidance

router = APIRouter()


def _live_weather(db: Session, field_id: int):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=6)
    return (
        db.query(WeatherRecord)
        .filter(
            WeatherRecord.field_id == field_id,
            WeatherRecord.provider == "openweathermap",
            WeatherRecord.recorded_at >= cutoff,
        )
        .order_by(WeatherRecord.recorded_at.desc())
        .first()
    )


def _guidance_for(db: Session, field: Field) -> dict:
    return build_guidance(
        field=field,
        latest=get_latest_reading_for_field(db, field.id),
        sensors=get_sensors_for_field(db, field.id),
        live_weather=_live_weather(db, field.id),
    )


@router.get("/")
def list_guidance(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    return [_guidance_for(db, f) for f in get_fields_by_user(db, current_user.id)]


@router.get("/{field_id}")
def field_guidance(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    field = get_field_by_id(db, field_id, current_user.id)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return _guidance_for(db, field)
