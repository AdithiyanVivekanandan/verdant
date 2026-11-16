from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.base import Profile
from app.crud import (
    get_fields_by_user,
    get_field_by_id,
    create_field,
    update_field,
    delete_field,
    get_sensor_for_field,
    create_sensor,
    get_sensors_for_field,
)
from app.schemas import (
    FieldCreate, FieldUpdate, FieldOut, SensorCreate, SensorOut,
)

router = APIRouter()


@router.post("/", response_model=FieldOut, status_code=status.HTTP_201_CREATED)
def create_field_endpoint(
    field_in: FieldCreate,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    field = create_field(db, field_in, current_user.id)
    return field


@router.get("/", response_model=List[FieldOut])
def list_fields(
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    return get_fields_by_user(db, current_user.id)


@router.get("/{field_id}", response_model=FieldOut)
def get_field(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    field = get_field_by_id(db, field_id, current_user.id)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return field


@router.put("/{field_id}", response_model=FieldOut)
def update_field_endpoint(
    field_id: int,
    field_in: FieldUpdate,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    field = get_field_by_id(db, field_id, current_user.id)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return update_field(db, field, field_in)


@router.delete("/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_field_endpoint(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    field = get_field_by_id(db, field_id, current_user.id)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    delete_field(db, field)
    return None


@router.get("/{field_id}/sensors", response_model=List[SensorOut])
def list_sensors(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    field = get_field_by_id(db, field_id, current_user.id)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    return get_sensors_for_field(db, field_id)


@router.post("/{field_id}/sensors", response_model=SensorOut, status_code=status.HTTP_201_CREATED)
def add_sensor(
    field_id: int,
    sensor_in: SensorCreate,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    field = get_field_by_id(db, field_id, current_user.id)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    existing = next(
        (s for s in get_sensors_for_field(db, field_id)
         if s.sensor_identifier == sensor_in.sensor_identifier),
        None,
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This sensor is already attached to the field.",
        )
    try:
        return create_sensor(db, field_id, sensor_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This sensor is already attached to the field.",
        )
