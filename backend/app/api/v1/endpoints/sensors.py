from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from uuid import UUID

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.base import Profile, SensorReading
from app.crud import (
    create_reading,
    get_readings,
    get_latest_reading_for_field,
    get_sensor_for_field,
    get_field_by_id,
)
from app.schemas import SensorReadingCreate, SensorReadingOut

router = APIRouter()


@router.post("/", response_model=SensorReadingOut, status_code=status.HTTP_201_CREATED)
def submit_reading(
    reading_in: SensorReadingCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    # field must belong to user
    field = get_field_by_id(db, reading_in.field_id, current_user.id)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    # if sensor_id provided, verify it belongs to the field
    if reading_in.sensor_id is not None:
        sensor = get_sensor_for_field(db, reading_in.field_id, reading_in.sensor_id)
        if not sensor:
            raise HTTPException(
                status_code=400,
                detail="Sensor ID does not belong to the selected field",
            )

    # Manual entries through this endpoint are always labelled manual. A
    # separate ingestion path would be required to claim an IoT source.
    reading_in.source = "manual"

    # normalize recorded_at to UTC
    recorded_at = reading_in.recorded_at or datetime.now(timezone.utc)
    if recorded_at.tzinfo is None:
        recorded_at = recorded_at.replace(tzinfo=timezone.utc)
    if recorded_at > datetime.now(timezone.utc) + timedelta(minutes=10):
        raise HTTPException(
            status_code=400,
            detail="Recorded time is in the future. Check the date and time.",
        )
    reading_in.recorded_at = recorded_at

    if reading_in.idempotency_key:
        existing = (
            db.query(SensorReading)
            .filter(
                SensorReading.idempotency_key == reading_in.idempotency_key,
                SensorReading.field_id == reading_in.field_id,
            )
            .first()
        )
        if existing:
            response.status_code = status.HTTP_200_OK
            return existing

    try:
        reading = create_reading(db, reading_in)
    except IntegrityError:
        db.rollback()
        if reading_in.idempotency_key:
            existing = (
                db.query(SensorReading)
                .filter(SensorReading.idempotency_key == reading_in.idempotency_key)
                .first()
            )
            if existing:
                response.status_code = status.HTTP_200_OK
                return existing
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This reading was already recorded.",
        )
    return reading


@router.get("/", response_model=List[SensorReadingOut])
def list_readings(
    field_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    return get_readings(
        db,
        field_id=field_id,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )


@router.get("/latest/{field_id}", response_model=Optional[SensorReadingOut])
def latest_reading(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    field = get_field_by_id(db, field_id, current_user.id)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return get_latest_reading_for_field(db, field_id)
