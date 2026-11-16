"""Training data set construction from the live database.

The data set is built from the *existing* Verdant tables only:

* ``sensor_readings``  – soil moisture (the modelling target)
* ``weather_records``  – rainfall and weather context
* ``irrigation_events``– water applied (only present once farmers record it)

Nothing is imputed with zeros and no synthetic rows are created. If the
resulting data set is too small for a model, the trainer reports that and
keeps the transparent baseline active.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import Field, SensorReading, WeatherRecord
from app.models.irrigation import IrrigationEvent
from app.ml.features.engineering import (
    HORIZON_HOURS,
    TrainingSample,
    build_training_samples,
)

#: Minimum requirements before a trained model is considered usable in
#: production. Below these numbers the prediction stays provisional.
MIN_TRAINING_SAMPLES = 200
MIN_FIELDS = 3
MIN_SPAN_DAYS = 21


@dataclass
class DatasetBundle:
    samples: list[TrainingSample]
    field_ids: list[int]
    span_start: Optional[datetime]
    span_end: Optional[datetime]
    reading_counts: dict[int, int]
    missing_feature_counts: dict[str, int]
    limitations: list[str]

    @property
    def sample_count(self) -> int:
        return len(self.samples)

    @property
    def field_count(self) -> int:
        return len(self.field_ids)

    @property
    def span_days(self) -> float:
        if self.span_start is None or self.span_end is None:
            return 0.0
        return (self.span_end - self.span_start).total_seconds() / 86400.0

    def meets_production_requirements(self) -> bool:
        return (
            self.sample_count >= MIN_TRAINING_SAMPLES
            and self.field_count >= MIN_FIELDS
            and self.span_days >= MIN_SPAN_DAYS
        )

    def requirement_report(self) -> dict[str, Any]:
        return {
            "min_training_samples": MIN_TRAINING_SAMPLES,
            "min_fields": MIN_FIELDS,
            "min_span_days": MIN_SPAN_DAYS,
            "actual_training_samples": self.sample_count,
            "actual_fields": self.field_count,
            "actual_span_days": round(self.span_days, 2),
            "meets_requirements": self.meets_production_requirements(),
        }


def build_dataset(
    db: Session,
    *,
    user_id: Optional[Any] = None,
    horizon_hours: int = HORIZON_HOURS,
) -> DatasetBundle:
    """Build the supervised data set from the database."""
    fields = db.execute(select(Field)).scalars().all()
    if user_id is not None:
        fields = [f for f in fields if str(f.user_id) == str(user_id)]
    field_ids = [f.id for f in fields]

    samples: list[TrainingSample] = []
    reading_counts: dict[int, int] = {}
    limitations: list[str] = []

    for field in fields:
        readings = (
            db.execute(
                select(SensorReading)
                .where(SensorReading.field_id == field.id)
                .order_by(SensorReading.recorded_at)
            )
            .scalars()
            .all()
        )
        reading_counts[field.id] = len(readings)
        if len(readings) < 3:
            limitations.append(
                f"Field {field.id} has {len(readings)} reading(s); it contributes no training rows."
            )
            continue

        weather = (
            db.execute(
                select(WeatherRecord)
                .where(WeatherRecord.field_id == field.id)
                .order_by(WeatherRecord.recorded_at)
            )
            .scalars()
            .all()
        )
        events = (
            db.execute(
                select(IrrigationEvent)
                .where(IrrigationEvent.field_id == field.id)
                .order_by(IrrigationEvent.start_time)
            )
            .scalars()
            .all()
        )

        samples.extend(
            build_training_samples(
                field_id=field.id,
                field_name=field.field_name,
                crop_type=field.crop_type,
                soil_type=field.soil_type,
                growth_stage=field.growth_stage,
                area_acres=field.area_acres,
                sowing_date=field.sowing_date,
                readings=readings,
                weather=weather,
                irrigation_events=events,
                horizon_hours=horizon_hours,
            )
        )

    span_start = min((s.feature_time for s in samples), default=None)
    span_end = max((s.target_time for s in samples), default=None)

    missing: dict[str, int] = {}
    if samples:
        for key in samples[0].features.keys():
            count = sum(1 for s in samples if s.features.get(key) is None)
            if count:
                missing[key] = count

    if not samples:
        limitations.append(
            "No field has enough readings to form a 24 h ahead supervised sample."
        )
    else:
        thin = [fid for fid, count in reading_counts.items() if count < 3]
        if thin:
            limitations.append(
                f"Fields {thin} have fewer than 3 readings and could not contribute samples."
            )

    return DatasetBundle(
        samples=samples,
        field_ids=field_ids,
        span_start=span_start,
        span_end=span_end,
        reading_counts=reading_counts,
        missing_feature_counts=missing,
        limitations=limitations,
    )
