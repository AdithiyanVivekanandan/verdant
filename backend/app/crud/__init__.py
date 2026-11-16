from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple
from uuid import UUID

from app.models.base import Profile, Field, Sensor, SensorReading, WeatherRecord, Alert
from app.schemas import FieldCreate, FieldUpdate, SensorCreate, SensorReadingCreate
from app.services.irrigation import field_state, thresholds_for


# ---- Auth ----
def get_profile_by_supabase_user_id(db: Session, supabase_user_id: UUID) -> Optional[Profile]:
    return db.query(Profile).filter(Profile.supabase_user_id == supabase_user_id).first()


def create_profile(
    db: Session,
    supabase_user_id: UUID,
    full_name: str,
    email: str,
    language: str = "en",
) -> Profile:
    profile = Profile(
        supabase_user_id=supabase_user_id,
        full_name=full_name,
        email=email,
        preferred_language=language,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


# ---- Fields ----
def get_fields_by_user(db: Session, user_id: UUID) -> List[Field]:
    return (
        db.query(Field)
        .filter(Field.user_id == user_id)
        .order_by(Field.created_at.desc())
        .all()
    )


def get_field_by_id(db: Session, field_id: int, user_id: UUID) -> Optional[Field]:
    return db.query(Field).filter(Field.id == field_id, Field.user_id == user_id).first()


def create_field(db: Session, field_in: FieldCreate, user_id: UUID) -> Field:
    data = field_in.model_dump()
    field = Field(user_id=user_id, **data)
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


def update_field(db: Session, field: Field, field_in: FieldUpdate) -> Field:
    update_data = field_in.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(field, k, v)
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


def delete_field(db: Session, field: Field) -> None:
    db.delete(field)
    db.commit()


# ---- Sensors ----
def get_sensor_by_identifier(db: Session, sensor_identifier: str) -> Optional[Sensor]:
    return db.query(Sensor).filter(Sensor.sensor_identifier == sensor_identifier).first()


def get_sensor_by_id(db: Session, sensor_id: int) -> Optional[Sensor]:
    return db.query(Sensor).filter(Sensor.id == sensor_id).first()


def create_sensor(db: Session, field_id: int, sensor_in: SensorCreate) -> Sensor:
    # Ensure uniqueness within field
    existing = (
        db.query(Sensor)
        .filter(Sensor.field_id == field_id, Sensor.sensor_identifier == sensor_in.sensor_identifier)
        .first()
    )
    if existing:
        return existing
    sensor = Sensor(field_id=field_id, **sensor_in.model_dump())
    db.add(sensor)
    db.commit()
    db.refresh(sensor)
    return sensor


def get_sensors_for_field(db: Session, field_id: int) -> List[Sensor]:
    return db.query(Sensor).filter(Sensor.field_id == field_id).all()


def get_sensor_for_field(db: Session, field_id: int, sensor_id: int) -> Optional[Sensor]:
    return db.query(Sensor).filter(Sensor.id == sensor_id, Sensor.field_id == field_id).first()


# ---- Sensor Readings ----
def create_reading(db: Session, reading_in: SensorReadingCreate) -> SensorReading:
    reading = SensorReading(
        field_id=reading_in.field_id,
        sensor_id=reading_in.sensor_id,
        growth_stage=reading_in.crop_growth_stage,
        moisture_percentage=reading_in.moisture_percentage,
        soil_temperature=reading_in.soil_temperature,
        source=reading_in.source or "manual",
        idempotency_key=reading_in.idempotency_key,
        recorded_at=reading_in.recorded_at or datetime.now(timezone.utc),
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


def get_readings(
    db: Session,
    field_id: Optional[int] = None,
    user_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[SensorReading]:
    query = db.query(SensorReading)
    if field_id is not None:
        query = query.filter(SensorReading.field_id == field_id)
    if start_date is not None:
        query = query.filter(SensorReading.recorded_at >= start_date)
    if end_date is not None:
        query = query.filter(SensorReading.recorded_at <= end_date)
    # scope to user if requested
    if user_id is not None:
        query = query.join(Field).filter(Field.user_id == user_id)
    return query.order_by(desc(SensorReading.recorded_at)).offset(offset).limit(limit).all()


def get_latest_reading_for_field(db: Session, field_id: int) -> Optional[SensorReading]:
    return (
        db.query(SensorReading)
        .filter(SensorReading.field_id == field_id)
        .order_by(desc(SensorReading.recorded_at))
        .first()
    )


def get_readings_count(db: Session, user_id: UUID) -> int:
    return db.query(SensorReading).join(Field).filter(Field.user_id == user_id).count()


# ---- Dashboard ----
def _uses_sensor(reading: Optional[SensorReading]) -> bool:
    return bool(reading and (reading.sensor_id is not None or reading.source == "iot_sensor"))


def _legacy_condition(status: str, reason: str) -> str:
    if status in ("no_data", "sensor_unavailable"):
        return "unknown"
    if reason == "below_band":
        return "low"
    if reason == "above_band":
        return "high"
    if status == "healthy":
        return "healthy"
    return "moderate"


def moisture_condition(moisture: Optional[float]) -> str:
    """Legacy generic condition retained for older API callers."""
    if moisture is None:
        return "unknown"
    if moisture < 30:
        return "low"
    if moisture < 45:
        return "moderate"
    if moisture <= 75:
        return "healthy"
    return "high"


def get_field_moisture_summaries(db: Session, user_id: UUID) -> List[dict]:
    fields = db.query(Field).filter(Field.user_id == user_id).order_by(Field.field_name).all()
    now = datetime.now(timezone.utc)
    results = []
    for f in fields:
        sensors = get_sensors_for_field(db, f.id)
        latest = get_latest_reading_for_field(db, f.id)
        moisture = latest.moisture_percentage if latest else None
        state = field_state(
            moisture=moisture,
            recorded_at=latest.recorded_at if latest else None,
            has_sensor=bool(sensors),
            uses_sensor=_uses_sensor(latest),
            crop_type=f.crop_type,
            soil_type=f.soil_type,
            now=now,
        )
        sensor = latest.sensor if latest and latest.sensor_id else (sensors[0] if sensors else None)
        results.append({
            "id": f.id,
            "field_name": f.field_name,
            "crop_type": f.crop_type,
            "area_acres": f.area_acres,
            "latest_moisture": moisture,
            "moisture_condition": _legacy_condition(state["status"], state["reason"]),
            "last_updated": latest.recorded_at if latest else None,
            "has_sensor": bool(sensors),
            "sensor_identifier": sensor.sensor_identifier if sensor else None,
            "sensor_id": sensor.id if sensor else None,
            "source": latest.source if latest else None,
            "validation_status": latest.validation_status if latest else None,
            "ingested_at": latest.ingested_at if latest else None,
            "freshness": state["freshness"],
            "age_hours": state["age_hours"],
            "status": state["status"],
            "status_reason": state["reason"],
            "requires_attention": state["requires_attention"],
            "threshold_low": state["low"],
            "threshold_high": state["high"],
            "crop_band": state["crop_band"],
            "soil_adjusted": state["soil_adjusted"],
        })
    return results


def get_dashboard_summary(db: Session, user_id: UUID) -> dict:
    summaries = get_field_moisture_summaries(db, user_id)
    moistures = [s["latest_moisture"] for s in summaries if s["latest_moisture"] is not None]
    updates = [s["last_updated"] for s in summaries if s["last_updated"] is not None]
    status_counts: dict[str, int] = {}
    for s in summaries:
        status_counts[s["status"]] = status_counts.get(s["status"], 0) + 1

    return {
        "total_fields": len(summaries),
        "average_moisture": round(sum(moistures) / len(moistures), 2) if moistures else 0.0,
        "fields_requiring_attention": sum(1 for s in summaries if s["requires_attention"]),
        "fields_with_no_data": sum(
            1 for s in summaries if s["status"] in ("no_data", "sensor_unavailable")
        ),
        "latest_sensor_update": max(updates) if updates else None,
        "status_counts": status_counts,
    }


def get_alerts(db: Session, user_id: UUID) -> List[dict]:
    alerts = []
    severity_rank = {"critical": 0, "warning": 1, "info": 2}

    for s in get_field_moisture_summaries(db, user_id):
        field_name = s["field_name"]
        moisture = s["latest_moisture"]
        low = s["threshold_low"]
        high = s["threshold_high"]
        age = s["age_hours"]

        if s["status"] == "stale":
            alerts.append({
                "field_id": s["id"],
                "field_name": field_name,
                "type": "stale_sensor",
                "message": (
                    f"The latest reading for {field_name} is {age:.0f} hours old. "
                    "Verdant is not using it for a moisture decision."
                ),
                "severity": "warning",
                "moisture": moisture,
                "reason": "stale_reading",
                "action": "Check the sensor power and connection, or record a current manual reading.",
                "freshness": s["freshness"],
                "last_updated": s["last_updated"],
                "threshold_low": low,
                "threshold_high": high,
            })
            continue

        if s["status"] in ("no_data", "sensor_unavailable"):
            if s["has_sensor"]:
                alerts.append({
                    "field_id": s["id"],
                    "field_name": field_name,
                    "type": "missing_sensor",
                    "message": (
                        f"{field_name} has a sensor but no readings yet. "
                        "Moisture is unknown, not zero."
                    ),
                    "severity": "warning",
                    "moisture": None,
                    "reason": "sensor_no_readings",
                    "action": "Check the sensor or record a manual reading.",
                    "freshness": "missing",
                    "last_updated": None,
                    "threshold_low": low,
                    "threshold_high": high,
                })
            else:
                alerts.append({
                    "field_id": s["id"],
                    "field_name": field_name,
                    "type": "missing_sensor",
                    "message": (
                        f"No reading has been recorded for {field_name}. "
                        "Moisture is unknown, not zero."
                    ),
                    "severity": "info",
                    "moisture": None,
                    "reason": "no_readings",
                    "action": "Record a manual reading or add a sensor.",
                    "freshness": "missing",
                    "last_updated": None,
                    "threshold_low": low,
                    "threshold_high": high,
                })
            continue

        if s["status"] in ("critical", "needs_review"):
            below = s["status_reason"] == "below_band"
            critical = s["status"] == "critical"
            band = f"{low:.0f}–{high:.0f}%"
            if below:
                message = (
                    f"Soil moisture is {moisture:.1f}% in {field_name}; the lower "
                    f"band for {s['crop_type']} in this soil is {low:.0f}%."
                )
                action = (
                    "Irrigate today and record a new reading afterwards."
                    if critical
                    else "Plan irrigation soon and check the field in person."
                )
                alert_type = "low_moisture"
            else:
                message = (
                    f"Soil moisture is {moisture:.1f}% in {field_name}; the upper "
                    f"band for {s['crop_type']} in this soil is {high:.0f}%."
                )
                action = (
                    "Hold irrigation and check drainage if the reading stays high."
                    if critical
                    else "Do not irrigate now; check again tomorrow."
                )
                alert_type = "high_moisture"
            alerts.append({
                "field_id": s["id"],
                "field_name": field_name,
                "type": alert_type,
                "message": message,
                "severity": "critical" if critical else "warning",
                "moisture": moisture,
                "reason": s["status_reason"],
                "action": action,
                "freshness": s["freshness"],
                "last_updated": s["last_updated"],
                "threshold_low": low,
                "threshold_high": high,
            })

    alerts.sort(key=lambda a: (severity_rank.get(a["severity"], 9), a["field_name"]))
    return alerts
