"""Irrigation intelligence data model.

Adds, without modifying existing tables:

* ``irrigation_events``        — recorded water applications (measured).
* ``irrigation_schedules``     — daily, explainable recommendations.
* ``irrigation_predictions``   — stored model/baseline predictions.
* ``field_irrigation_settings``— per-field application parameters (rate,
  efficiency, method, source) used to turn a depth into litres/minutes.
* ``farmer_irrigation_preferences`` — farmer availability windows and caps.

Units are explicit and stored in column names where ambiguity is possible:
``water_volume_litres``, ``estimated_volume_litres``, ``duration_minutes``.
"""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IrrigationEvent(Base):
    """A water application the farmer actually performed.

    ``water_volume_litres`` is a *measured* quantity. It stays NULL when the
    farmer did not measure it; it is never inferred from duration.
    """

    __tablename__ = "irrigation_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True)

    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Float, nullable=True)

    # Measured water volume. NULL means "not measured" — never zero-filled.
    water_volume_litres = Column(Float, nullable=True)

    application_method = Column(String, nullable=True)   # flood, drip, sprinkler, manual_bucket
    water_source = Column(String, nullable=True)          # borewell, canal, tank, rainwater, unknown
    recorded_by = Column(String, default="manual", nullable=False)  # manual | sensor | device
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    field = relationship("Field", back_populates="irrigation_events")
    owner = relationship("Profile")

    __table_args__ = (
        Index("ix_irrigation_events_user_start", "user_id", "start_time"),
        Index("ix_irrigation_events_field_start", "field_id", "start_time"),
        CheckConstraint("water_volume_litres IS NULL OR water_volume_litres >= 0", name="chk_irrigation_event_volume"),
        CheckConstraint("duration_minutes IS NULL OR duration_minutes >= 0", name="chk_irrigation_event_duration"),
        CheckConstraint("end_time IS NULL OR end_time >= start_time", name="chk_irrigation_event_window"),
    )


class IrrigationSchedule(Base):
    """One daily recommendation for one field.

    The original recommendation (``estimated_volume_litres``,
    ``recommended_start_time``, ``model_version``, ``reason``) is preserved
    after completion so planned and actual can be compared.
    """

    __tablename__ = "irrigation_schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True)

    scheduled_date = Column(Date, nullable=False, index=True)
    recommended_start_time = Column(Time, nullable=True)
    recommended_window_end = Column(Time, nullable=True)

    estimated_volume_litres = Column(Float, nullable=True)
    estimated_duration_minutes = Column(Float, nullable=True)
    estimated_depth_mm = Column(Float, nullable=True)

    priority = Column(String, default="medium", nullable=False)  # low | medium | high | critical
    reason = Column(Text, nullable=True)
    reason_code = Column(String, nullable=True)
    model_version = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    uncertainty_litres = Column(Float, nullable=True)

    status = Column(String, default="pending", nullable=False)  # pending|accepted|completed|skipped|cancelled
    completed_at = Column(DateTime(timezone=True), nullable=True)

    actual_volume_litres = Column(Float, nullable=True)
    actual_duration_minutes = Column(Float, nullable=True)
    actual_start_time = Column(DateTime(timezone=True), nullable=True)
    actual_end_time = Column(DateTime(timezone=True), nullable=True)

    prediction_id = Column(Integer, ForeignKey("irrigation_predictions.id", ondelete="SET NULL"), nullable=True)
    input_snapshot = Column(JSONB, nullable=True)  # features/sources used, for audit

    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    field = relationship("Field", back_populates="irrigation_schedules")
    owner = relationship("Profile")
    prediction = relationship("IrrigationPrediction", foreign_keys=[prediction_id])

    __table_args__ = (
        UniqueConstraint("field_id", "scheduled_date", name="uq_irrigation_schedule_field_date"),
        Index("ix_irrigation_schedules_user_date", "user_id", "scheduled_date"),
        CheckConstraint("estimated_volume_litres IS NULL OR estimated_volume_litres >= 0", name="chk_schedule_estimated_volume"),
        CheckConstraint("actual_volume_litres IS NULL OR actual_volume_litres >= 0", name="chk_schedule_actual_volume"),
        CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name="chk_schedule_confidence"),
    )


class IrrigationPrediction(Base):
    """A stored prediction for a field.

    ``status`` distinguishes a provisional estimate (small dataset, baseline
    model) from a production-validated model output.
    """

    __tablename__ = "irrigation_predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True)

    predicted_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False, index=True)
    target_time = Column(DateTime(timezone=True), nullable=True)

    current_moisture = Column(Float, nullable=True)
    predicted_moisture = Column(Float, nullable=True)
    moisture_trend = Column(Float, nullable=True)  # percentage points per day

    irrigation_requirement_mm = Column(Float, nullable=True)
    estimated_volume_litres = Column(Float, nullable=True)

    model_name = Column(String, nullable=True)
    model_version = Column(String, nullable=True)
    calculation_version = Column(String, nullable=True)

    confidence = Column(Float, nullable=True)
    uncertainty = Column(Float, nullable=True)
    status = Column(String, default="provisional", nullable=False)  # provisional | validated | failed
    data_freshness = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    input_refs = Column(JSONB, nullable=True)  # ids/series used to build the prediction

    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    field = relationship("Field", back_populates="irrigation_predictions")
    owner = relationship("Profile")

    __table_args__ = (
        Index("ix_irrigation_predictions_field_predicted", "field_id", "predicted_at"),
        CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name="chk_prediction_confidence"),
    )


class FieldIrrigationSettings(Base):
    """Optional per-field application parameters.

    Every field is nullable on purpose: Verdant only uses these values when
    the farmer supplies them, so no duration or efficiency is ever invented.
    """

    __tablename__ = "field_irrigation_settings"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True)
    application_method = Column(String, nullable=True)
    application_rate_litres_per_hour = Column(Float, nullable=True)
    application_efficiency = Column(Float, nullable=True)  # 0 < e <= 1
    water_source = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    field = relationship("Field", back_populates="irrigation_settings")

    __table_args__ = (
        UniqueConstraint("field_id", name="uq_field_irrigation_settings_field"),
        CheckConstraint(
            "application_efficiency IS NULL OR (application_efficiency > 0 AND application_efficiency <= 1)",
            name="chk_field_irrigation_efficiency",
        ),
        CheckConstraint(
            "application_rate_litres_per_hour IS NULL OR application_rate_litres_per_hour > 0",
            name="chk_field_irrigation_rate",
        ),
    )


class FarmerIrrigationPreference(Base):
    """Farmer availability window and daily cap used by the scheduler."""

    __tablename__ = "farmer_irrigation_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    preferred_start_time = Column(Time, nullable=True)
    preferred_end_time = Column(Time, nullable=True)
    max_daily_volume_litres = Column(Float, nullable=True)
    irrigation_days = Column(String, default="all", nullable=False)  # "all" or comma separated weekday names
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)

    owner = relationship("Profile")

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_farmer_irrigation_preferences_user"),
        CheckConstraint(
            "max_daily_volume_litres IS NULL OR max_daily_volume_litres >= 0",
            name="chk_farmer_irrigation_cap",
        ),
    )
