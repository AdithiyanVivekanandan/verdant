from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Boolean,
    Index,
    Text,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Profile(Base):
    """Application-level profile linked to Supabase auth.users.id"""

    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    supabase_user_id = Column(UUID(as_uuid=True), unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    preferred_language = Column(String, default="en", nullable=False)
    theme_preference = Column(String, default="system", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    fields = relationship("Field", back_populates="owner", cascade="all, delete-orphan")


class Field(Base):
    __tablename__ = "fields"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String, nullable=False)
    farmer_name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    village = Column(String, nullable=True)
    district = Column(String, nullable=True)
    state = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    area_acres = Column(Float, nullable=False)
    crop_type = Column(String, nullable=False)
    soil_type = Column(String, nullable=False)
    growth_stage = Column(String, nullable=False)
    sowing_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    owner = relationship("Profile", back_populates="fields")
    readings = relationship("SensorReading", back_populates="field", cascade="all, delete-orphan")
    weather_records = relationship("WeatherRecord", back_populates="field", cascade="all, delete-orphan")
    irrigation_events = relationship(
        "IrrigationEvent", back_populates="field", cascade="all, delete-orphan"
    )
    irrigation_schedules = relationship(
        "IrrigationSchedule", back_populates="field", cascade="all, delete-orphan"
    )
    irrigation_predictions = relationship(
        "IrrigationPrediction", back_populates="field", cascade="all, delete-orphan"
    )
    irrigation_settings = relationship(
        "FieldIrrigationSettings", back_populates="field", cascade="all, delete-orphan", uselist=False
    )


class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True)
    sensor_identifier = Column(String, nullable=False, index=True)
    sensor_type = Column(String, nullable=False)
    installation_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    readings = relationship("SensorReading", back_populates="sensor")

    __table_args__ = (
        UniqueConstraint("field_id", "sensor_identifier", name="uq_field_sensor_identifier"),
    )


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id", ondelete="CASCADE"), nullable=True, index=True)
    moisture_percentage = Column(Float, nullable=False)
    soil_temperature = Column(Float, nullable=True)
    growth_stage = Column(String, nullable=True)
    source = Column(String, default="manual", nullable=False)  # manual, iot_sensor, weather_service, system, demo
    recorded_at = Column(DateTime(timezone=True), nullable=False, index=True)
    ingested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    validation_status = Column(String, default="valid", nullable=False)  # valid, warning, invalid
    idempotency_key = Column(String, unique=True, index=True, nullable=True)

    field = relationship("Field", back_populates="readings")
    sensor = relationship("Sensor", back_populates="readings")

    @property
    def sensor_identifier(self) -> Optional[str]:
        return self.sensor.sensor_identifier if self.sensor else None

    @property
    def field_name(self) -> Optional[str]:
        return self.field.field_name if self.field else None

    __table_args__ = (
        Index("ix_sensor_readings_field_recorded", "field_id", "recorded_at"),
        CheckConstraint("moisture_percentage >= 0 AND moisture_percentage <= 100", name="chk_moisture_range"),
    )


class WeatherRecord(Base):
    __tablename__ = "weather_records"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String, default="demo", nullable=False)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    rainfall_probability = Column(Float, nullable=True)
    rainfall = Column(Float, nullable=True)
    wind_speed = Column(Float, nullable=False)
    # Additive columns used by the irrigation water-balance calculation.
    temperature_min = Column(Float, nullable=True)
    temperature_max = Column(Float, nullable=True)
    et0_mm = Column(Float, nullable=True)
    forecast_for = Column(DateTime(timezone=True), nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    field = relationship("Field", back_populates="weather_records")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"), nullable=True, index=True)
    alert_type = Column(String, nullable=False)  # low_moisture, high_moisture, stale_sensor, missing_sensor, expected_rainfall
    severity = Column(String, nullable=False)  # info, warning, critical
    message_key = Column(String, nullable=False)
    trigger_value = Column(Float, nullable=True)
    triggered_at = Column(DateTime(timezone=True), nullable=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
