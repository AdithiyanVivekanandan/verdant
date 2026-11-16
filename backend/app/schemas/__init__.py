from pydantic import BaseModel, EmailStr, Field as PField, validator, root_validator
from datetime import datetime
from typing import Optional, List
from uuid import UUID


# ---- Auth ----
class ProfileOut(BaseModel):
    id: UUID
    supabase_user_id: UUID
    full_name: str
    email: str
    preferred_language: str
    theme_preference: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = PField(default=None, min_length=1, max_length=200)
    preferred_language: Optional[str] = PField(default=None, pattern="^(en|hi|kn|ta)$")
    theme_preference: Optional[str] = PField(default=None, pattern="^(light|dark|system)$")


# ---- Field ----
class FieldBase(BaseModel):
    field_name: str = PField(..., min_length=1, max_length=200)
    farmer_name: str = PField(..., min_length=1, max_length=200)
    location: str = PField(..., min_length=1, max_length=300)
    village: Optional[str] = PField(default=None, max_length=200)
    district: Optional[str] = PField(default=None, max_length=200)
    state: Optional[str] = PField(default=None, max_length=200)
    latitude: Optional[float] = PField(default=None, ge=-90, le=90)
    longitude: Optional[float] = PField(default=None, ge=-180, le=180)
    area_acres: float = PField(..., gt=0, le=10000)
    crop_type: str = PField(..., min_length=1)
    soil_type: str = PField(..., min_length=1)
    growth_stage: str = PField(..., min_length=1)
    sowing_date: Optional[datetime] = None


class FieldCreate(FieldBase):
    pass


class FieldUpdate(BaseModel):
    field_name: Optional[str] = PField(default=None, min_length=1, max_length=200)
    farmer_name: Optional[str] = PField(default=None, min_length=1, max_length=200)
    location: Optional[str] = PField(default=None, min_length=1, max_length=300)
    village: Optional[str] = PField(default=None, max_length=200)
    district: Optional[str] = PField(default=None, max_length=200)
    state: Optional[str] = PField(default=None, max_length=200)
    latitude: Optional[float] = PField(default=None, ge=-90, le=90)
    longitude: Optional[float] = PField(default=None, ge=-180, le=180)
    area_acres: Optional[float] = PField(default=None, gt=0, le=10000)
    crop_type: Optional[str] = PField(default=None, min_length=1)
    soil_type: Optional[str] = PField(default=None, min_length=1)
    growth_stage: Optional[str] = PField(default=None, min_length=1)
    sowing_date: Optional[datetime] = None


class SensorBase(BaseModel):
    sensor_identifier: str = PField(..., min_length=1, max_length=100)
    sensor_type: str = PField(..., min_length=1)
    installation_date: Optional[datetime] = None


class SensorCreate(SensorBase):
    pass


class SensorOut(SensorBase):
    id: int
    field_id: int

    class Config:
        from_attributes = True


class FieldOut(FieldBase):
    id: int
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FieldWithLatest(FieldOut):
    latest_moisture: Optional[float] = None
    latest_recorded_at: Optional[datetime] = None
    moisture_condition: Optional[str] = None

    class Config:
        from_attributes = True


# ---- Sensor Reading ----
class SensorReadingCreate(BaseModel):
    field_id: int = PField(..., gt=0)
    sensor_id: Optional[int] = PField(default=None, gt=0)
    crop_growth_stage: str = PField(..., min_length=1, max_length=100)
    moisture_percentage: float = PField(..., ge=0, le=100)
    soil_temperature: Optional[float] = PField(default=None, ge=-50, le=80)
    recorded_at: Optional[datetime] = None
    source: Optional[str] = PField(default="manual", max_length=50)
    idempotency_key: Optional[str] = PField(default=None, max_length=255)


class SensorReadingOut(BaseModel):
    id: int
    field_id: int
    sensor_id: Optional[int]
    sensor_identifier: Optional[str] = None
    field_name: Optional[str] = None
    growth_stage: str
    moisture_percentage: float
    soil_temperature: Optional[float]
    source: str
    recorded_at: datetime
    ingested_at: datetime
    validation_status: str

    class Config:
        from_attributes = True


# ---- Weather ----
class WeatherOut(BaseModel):
    field_id: int
    temperature: float
    conditions: str
    humidity: float
    rainfall_probability: float
    rainfall: float
    wind_speed: float
    recorded_at: datetime
    source: str  # "openweathermap" or "demo"

    class Config:
        from_attributes = True


class WeatherForecastDay(BaseModel):
    date: str
    temperature: float
    conditions: str
    humidity: float
    rainfall_probability: float
    wind_speed: float


# ---- Dashboard ----
class DashboardSummary(BaseModel):
    total_fields: int
    average_moisture: float
    fields_requiring_attention: int
    latest_sensor_update: Optional[datetime]


class FieldMoistureSummary(BaseModel):
    id: int
    field_name: str
    crop_type: str
    area_acres: float
    latest_moisture: Optional[float]
    moisture_condition: str
    last_updated: Optional[datetime]
    has_sensor: bool = False
    sensor_identifier: Optional[str] = None
    sensor_id: Optional[int] = None
    source: Optional[str] = None
    validation_status: Optional[str] = None
    ingested_at: Optional[datetime] = None
    freshness: str = "missing"
    age_hours: Optional[float] = None
    status: str = "no_data"
    status_reason: str = "no_readings"
    requires_attention: bool = True
    threshold_low: Optional[float] = None
    threshold_high: Optional[float] = None
    crop_band: bool = False
    soil_adjusted: bool = False


class AlertItem(BaseModel):
    field_id: int
    field_name: str
    type: str  # low_moisture, high_moisture, stale_sensor, missing_sensor, expected_rainfall
    message: str
    severity: str  # info, warning, critical
    moisture: Optional[float]
    reason: Optional[str] = None
    action: Optional[str] = None
    freshness: Optional[str] = None
    last_updated: Optional[datetime] = None
    threshold_low: Optional[float] = None
    threshold_high: Optional[float] = None
