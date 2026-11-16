"""Pydantic schemas for the irrigation intelligence API."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, Optional

from pydantic import BaseModel, Field as PField, field_validator, model_validator


# --------------------------------------------------------------------------
# Irrigation events
# --------------------------------------------------------------------------

class IrrigationEventCreate(BaseModel):
    field_id: int = PField(..., gt=0)
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[float] = PField(default=None, ge=0, le=24 * 60 * 30)
    water_volume_litres: Optional[float] = PField(default=None, ge=0)
    application_method: Optional[str] = PField(default=None, max_length=50)
    water_source: Optional[str] = PField(default=None, max_length=50)
    notes: Optional[str] = PField(default=None, max_length=2000)

    @model_validator(mode="after")
    def _check_window(self) -> "IrrigationEventCreate":
        if self.end_time is not None:
            if self.end_time.tzinfo is None:
                self.end_time = self.end_time.replace(tzinfo=self.start_time.tzinfo)
            if self.end_time < self.start_time:
                raise ValueError("end_time must not be before start_time")
        if self.duration_minutes is None and self.end_time is not None:
            delta = (self.end_time - self.start_time).total_seconds() / 60.0
            self.duration_minutes = round(delta, 1)
        return self


class IrrigationEventOut(BaseModel):
    id: int
    field_id: int
    field_name: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    water_volume_litres: Optional[float] = None
    volume_measured: bool = False
    application_method: Optional[str] = None
    water_source: Optional[str] = None
    recorded_by: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class IrrigationEventList(BaseModel):
    items: list[IrrigationEventOut]
    total: int
    limit: int
    offset: int


# --------------------------------------------------------------------------
# Schedules
# --------------------------------------------------------------------------

class IrrigationScheduleOut(BaseModel):
    id: int
    field_id: int
    field_name: Optional[str] = None
    scheduled_date: str
    recommended_start_time: Optional[str] = None
    recommended_window_end: Optional[str] = None
    estimated_volume_litres: Optional[float] = None
    estimated_duration_minutes: Optional[float] = None
    estimated_depth_mm: Optional[float] = None
    priority: str
    reason: Optional[str] = None
    reason_code: Optional[str] = None
    model_version: Optional[str] = None
    confidence: Optional[float] = None
    uncertainty_litres: Optional[float] = None
    status: str
    actual_volume_litres: Optional[float] = None
    actual_duration_minutes: Optional[float] = None
    completed_at: Optional[str] = None
    created_at: Optional[str] = None
    prediction_id: Optional[int] = None
    is_decision_support: bool = True


class ScheduleUpdate(BaseModel):
    recommended_start_time: Optional[time] = None
    recommended_window_end: Optional[time] = None
    estimated_volume_litres: Optional[float] = PField(default=None, ge=0)
    estimated_duration_minutes: Optional[float] = PField(default=None, ge=0)
    priority: Optional[str] = None
    notes: Optional[str] = PField(default=None, max_length=2000)

    @field_validator("priority")
    @classmethod
    def _validate_priority(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        allowed = {"low", "medium", "high", "critical", "uncertain"}
        if value not in allowed:
            raise ValueError(f"priority must be one of {sorted(allowed)}")
        return value


class ScheduleComplete(BaseModel):
    actual_volume_litres: Optional[float] = PField(default=None, ge=0)
    actual_duration_minutes: Optional[float] = PField(default=None, ge=0)
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    notes: Optional[str] = PField(default=None, max_length=2000)
    application_method: Optional[str] = PField(default=None, max_length=50)
    water_source: Optional[str] = PField(default=None, max_length=50)


class ScheduleSkip(BaseModel):
    reason: Optional[str] = PField(default=None, max_length=500)


class TodayScheduleResponse(BaseModel):
    date: str
    timezone: str
    entries: list[IrrigationScheduleOut]
    total_estimated_litres: float
    decision_support_notice: str
    generated_at: datetime


# --------------------------------------------------------------------------
# Predictions
# --------------------------------------------------------------------------

class PredictionResponse(BaseModel):
    field_id: int
    field_name: Optional[str] = None
    predicted_at: datetime
    target_time: Optional[datetime] = None
    current_moisture: Optional[float] = None
    predicted_moisture: Optional[float] = None
    moisture_trend_pp_per_day: Optional[float] = None
    irrigation_requirement_mm: Optional[float] = None
    estimated_volume_litres: Optional[float] = None
    estimated_volume_unit: str = "litres"
    recommended_date: Optional[str] = None
    model_name: str
    model_version: Optional[str] = None
    model_status: str
    confidence: float
    uncertainty: Optional[float] = None
    provisional: bool
    reason: str
    data_freshness: str
    calculation_version: Optional[str] = None
    requirement: Optional[dict[str, Any]] = None
    input_refs: Optional[dict[str, Any]] = None
    limitations: list[str] = PField(default_factory=list)
    prediction_id: Optional[int] = None


class PredictionHistoryOut(BaseModel):
    id: int
    field_id: int
    predicted_at: datetime
    target_time: Optional[datetime] = None
    current_moisture: Optional[float] = None
    predicted_moisture: Optional[float] = None
    irrigation_requirement_mm: Optional[float] = None
    estimated_volume_litres: Optional[float] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    confidence: Optional[float] = None
    status: str
    data_freshness: Optional[str] = None

    model_config = {"from_attributes": True}


# --------------------------------------------------------------------------
# Settings and preferences
# --------------------------------------------------------------------------

class FieldIrrigationSettingsIn(BaseModel):
    application_method: Optional[str] = PField(default=None, max_length=50)
    application_rate_litres_per_hour: Optional[float] = PField(default=None, gt=0)
    application_efficiency: Optional[float] = PField(default=None, gt=0, le=1)
    water_source: Optional[str] = PField(default=None, max_length=50)
    notes: Optional[str] = PField(default=None, max_length=2000)


class FieldIrrigationSettingsOut(BaseModel):
    field_id: int
    application_method: Optional[str] = None
    application_rate_litres_per_hour: Optional[float] = None
    application_efficiency: Optional[float] = None
    water_source: Optional[str] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class FarmerPreferenceIn(BaseModel):
    preferred_start_time: Optional[time] = None
    preferred_end_time: Optional[time] = None
    max_daily_volume_litres: Optional[float] = PField(default=None, ge=0)
    irrigation_days: Optional[str] = PField(default=None, max_length=100)
    notes: Optional[str] = PField(default=None, max_length=2000)


class FarmerPreferenceOut(BaseModel):
    preferred_start_time: Optional[time] = None
    preferred_end_time: Optional[time] = None
    max_daily_volume_litres: Optional[float] = None
    irrigation_days: str = "all"
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


# --------------------------------------------------------------------------
# Analytics
# --------------------------------------------------------------------------

class WaterUsageResponse(BaseModel):
    total_litres: float
    measured_event_count: int
    unmeasured_event_count: int
    events_without_measurement: list[dict[str, Any]]
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    by_field: list[dict[str, Any]]
    by_crop: list[dict[str, Any]]
    by_day: list[dict[str, Any]]
    daily_series: list[dict[str, Any]]
    weekly_series: list[dict[str, Any]]
    monthly_series: list[dict[str, Any]]
    average_per_event_litres: Optional[float] = None
    average_per_event_days: Optional[float] = None
    irrigation_frequency_per_week: Optional[float] = None
    litres_per_acre: Optional[float] = None
    planned_vs_actual: list[dict[str, Any]]
    estimated_vs_actual: list[dict[str, Any]]
    data_notes: list[str]


class DashboardAnalyticsResponse(BaseModel):
    total_fields: int
    fields_healthy: int
    fields_requiring_attention: int
    fields_without_data: int
    sensors_reporting_recently: int
    water_usage_today_litres: float
    water_usage_this_week_litres: float
    water_usage_this_month_litres: float
    scheduled_volume_today_litres: float
    scheduled_fields_today: int
    fields_needing_irrigation_today: int
    moisture_status_distribution: list[dict[str, Any]]
    crop_water_usage: list[dict[str, Any]]
    field_water_usage: list[dict[str, Any]] = PField(default_factory=list)
    fields_needing_updated_measurements: list[dict[str, Any]]
    recent_irrigation_events: list[dict[str, Any]]
    daily_water_series: list[dict[str, Any]]
    weekly_water_series: list[dict[str, Any]]
    monthly_water_series: list[dict[str, Any]]
    planned_vs_actual: list[dict[str, Any]]
    data_notes: list[str]
    timezone: str
    generated_at: datetime


class ModelStatusResponse(BaseModel):
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    status: str
    trained_at: Optional[str] = None
    training_samples: Optional[int] = None
    validation_samples: Optional[int] = None
    training_period_start: Optional[str] = None
    training_period_end: Optional[str] = None
    validation_period_start: Optional[str] = None
    validation_period_end: Optional[str] = None
    features: list[str] = PField(default_factory=list)
    metrics: dict[str, Any] = PField(default_factory=dict)
    baseline_metrics: dict[str, Any] = PField(default_factory=dict)
    comparison: dict[str, Any] = PField(default_factory=dict)
    data_limitations: list[str] = PField(default_factory=list)
    minimum_production_requirements: dict[str, Any] = PField(default_factory=dict)
    active_predictor: str = "baseline"
    provisional: bool = True
    note: str = ""
    available_versions: list[dict[str, Any]] = PField(default_factory=list)
