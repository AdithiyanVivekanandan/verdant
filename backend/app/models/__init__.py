from app.core.database import Base  # noqa: F401
from app.models.base import Profile, Field, Sensor, SensorReading, WeatherRecord, Alert  # noqa: F401
from app.models.irrigation import (  # noqa: F401
    IrrigationEvent,
    IrrigationSchedule,
    IrrigationPrediction,
    FieldIrrigationSettings,
    FarmerIrrigationPreference,
)
