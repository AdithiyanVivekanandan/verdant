"""Feature engineering for the irrigation moisture-horizon model.

The model predicts **soil moisture at a fixed horizon (24 h)** for a field.
The irrigation *requirement* is then derived from that prediction with the
soil water balance in :mod:`app.services.agronomy`. This split is
deliberate: the measured dataset contains soil moisture observations, not
historical irrigation decisions, so a requirement model could only be
trained on invented labels.

Every feature is computed from data that is **strictly earlier** than the
prediction timestamp. Missing observations are represented as ``None`` and
imputed later from training statistics; they are never replaced by zero.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field as dataclass_field
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Optional, Sequence

#: Prediction horizon used for training and inference.
HORIZON_HOURS = 24

#: Tolerated slack when matching a future observation to the horizon.
HORIZON_TOLERANCE_HOURS = 12

#: Categorical vocabularies (fixed so training and inference agree).
CROP_VOCAB = ("rice", "wheat", "maize", "cotton", "sugarcane", "tomato", "ragi", "other")
SOIL_VOCAB = ("sandy soil", "red soil", "loamy soil", "black soil", "clay soil", "other")
STAGE_VOCAB = (
    "seedling",
    "vegetative",
    "flowering",
    "maturity",
    "other",
)

NUMERIC_FEATURES = (
    "current_moisture",
    "moisture_lag_6h",
    "moisture_lag_12h",
    "moisture_lag_24h",
    "moisture_delta_6h",
    "moisture_delta_12h",
    "moisture_delta_24h",
    "moisture_std_24h",
    "moisture_min_24h",
    "moisture_max_24h",
    "reading_count_24h",
    "soil_temperature",
    "temperature",
    "humidity",
    "wind_speed",
    "rainfall_24h",
    "rainfall_72h",
    "rainfall_probability",
    "forecast_rainfall_mm",
    "hours_since_last_reading",
    "hours_since_last_irrigation",
    "irrigation_litres_7d",
    "area_acres",
    "crop_age_days",
    "hour_sin",
    "hour_cos",
    "doy_sin",
    "doy_cos",
)

CATEGORICAL_FEATURES = ("crop_type", "soil_type", "growth_stage")


def feature_names() -> list[str]:
    """Flat, ordered feature names used by the model."""
    names = list(NUMERIC_FEATURES)
    for feature in CATEGORICAL_FEATURES:
        names.extend(f"{feature}={value}" for value in _vocab_for(feature))
    return names


def _vocab_for(feature: str) -> Sequence[str]:
    if feature == "crop_type":
        return CROP_VOCAB
    if feature == "soil_type":
        return SOIL_VOCAB
    return STAGE_VOCAB


def as_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _safe(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _nearest_at_or_before(
    readings: Sequence[Any],
    moment: datetime,
) -> Optional[Any]:
    """Latest reading recorded at or before ``moment``."""
    best = None
    best_time = None
    for reading in readings:
        recorded = as_utc(getattr(reading, "recorded_at", None))
        if recorded is None or recorded > moment:
            continue
        if best_time is None or recorded > best_time:
            best, best_time = reading, recorded
    return best


def _readings_between(
    readings: Sequence[Any],
    start: datetime,
    end: datetime,
) -> list[Any]:
    out = []
    for reading in readings:
        recorded = as_utc(getattr(reading, "recorded_at", None))
        if recorded is None or recorded < start or recorded > end:
            continue
        out.append(reading)
    return out


def _mean(values: Iterable[Optional[float]]) -> Optional[float]:
    numbers = [v for v in values if v is not None]
    if not numbers:
        return None
    return sum(numbers) / len(numbers)


def _std(values: Iterable[Optional[float]]) -> Optional[float]:
    numbers = [v for v in values if v is not None]
    if len(numbers) < 2:
        return None
    mean = sum(numbers) / len(numbers)
    return math.sqrt(sum((n - mean) ** 2 for n in numbers) / (len(numbers) - 1))


def _rainfall_sum(
    weather: Sequence[Any],
    start: datetime,
    end: datetime,
) -> Optional[float]:
    """Sum measured rainfall in a window.

    ``None`` when no observation in the window carries a measured amount —
    "not observed" is different from "no rain".
    """
    total = 0.0
    observed = False
    for record in weather:
        recorded = as_utc(getattr(record, "recorded_at", None))
        if recorded is None or recorded < start or recorded > end:
            continue
        amount = _safe(getattr(record, "rainfall", None))
        if amount is None:
            continue
        observed = True
        total += amount
    if not observed:
        return None
    return total


def _latest_weather(weather: Sequence[Any], moment: datetime) -> Optional[Any]:
    best = None
    best_time = None
    for record in weather:
        recorded = as_utc(getattr(record, "recorded_at", None))
        if recorded is None or recorded > moment:
            continue
        if best_time is None or recorded > best_time:
            best, best_time = record, recorded
    return best


def _next_weather(weather: Sequence[Any], moment: datetime) -> Optional[Any]:
    """Nearest forecast record published after ``moment``."""
    best = None
    best_time = None
    for record in weather:
        recorded = as_utc(getattr(record, "recorded_at", None))
        if recorded is None or recorded < moment:
            continue
        if best_time is None or recorded < best_time:
            best, best_time = record, recorded
    return best


def _normalise_crop(value: Optional[str]) -> str:
    text = (value or "").strip().lower()
    return text if text in CROP_VOCAB else "other"


def _normalise_soil(value: Optional[str]) -> str:
    text = (value or "").strip().lower()
    return text if text in SOIL_VOCAB else "other"


def _normalise_stage(value: Optional[str]) -> str:
    text = (value or "").strip().lower()
    return text if text in STAGE_VOCAB else "other"


@dataclass
class FeatureContext:
    """Raw (un-imputed) feature values for one field at one moment."""

    values: dict[str, Optional[float]] = dataclass_field(default_factory=dict)
    categoricals: dict[str, str] = dataclass_field(default_factory=dict)
    meta: dict[str, Any] = dataclass_field(default_factory=dict)


def build_context(
    *,
    at_time: datetime,
    readings: Sequence[Any],
    weather: Sequence[Any],
    irrigation_events: Sequence[Any],
    crop_type: Optional[str],
    soil_type: Optional[str],
    growth_stage: Optional[str],
    area_acres: Optional[float],
    sowing_date: Optional[datetime] = None,
) -> FeatureContext:
    """Build the raw feature context for a field at ``at_time``.

    Only information available at or before ``at_time`` is used.
    """
    at_time = as_utc(at_time) or datetime.now(timezone.utc)
    context = FeatureContext()
    values: dict[str, Optional[float]] = {name: None for name in NUMERIC_FEATURES}
    meta: dict[str, Any] = {}

    ordered_readings = sorted(
        (r for r in readings if as_utc(getattr(r, "recorded_at", None)) is not None),
        key=lambda r: as_utc(r.recorded_at),
    )

    current = _nearest_at_or_before(ordered_readings, at_time)
    current_time = as_utc(current.recorded_at) if current else None
    current_moisture = _safe(getattr(current, "moisture_percentage", None)) if current else None
    values["current_moisture"] = current_moisture
    values["soil_temperature"] = _safe(getattr(current, "soil_temperature", None)) if current else None

    if current_time is not None:
        values["hours_since_last_reading"] = round((at_time - current_time).total_seconds() / 3600.0, 3)
    else:
        meta["no_reading_at_prediction_time"] = True

    # --- moisture lags and window statistics ------------------------------
    lags: dict[int, Optional[float]] = {}
    for hours in (6, 12, 24):
        moment = at_time - timedelta(hours=hours)
        reading = _nearest_at_or_before(ordered_readings, moment)
        lag_value = _safe(getattr(reading, "moisture_percentage", None)) if reading else None
        lags[hours] = lag_value
        values[f"moisture_lag_{hours}h"] = lag_value
        if current_moisture is not None and lag_value is not None:
            values[f"moisture_delta_{hours}h"] = round(current_moisture - lag_value, 3)
        else:
            values[f"moisture_delta_{hours}h"] = None

    window = _readings_between(ordered_readings, at_time - timedelta(hours=24), at_time)
    window_values = [_safe(getattr(r, "moisture_percentage", None)) for r in window]
    values["moisture_std_24h"] = _std(window_values)
    present = [v for v in window_values if v is not None]
    values["moisture_min_24h"] = min(present) if present else None
    values["moisture_max_24h"] = max(present) if present else None
    values["reading_count_24h"] = float(len(present))

    # --- weather ------------------------------------------------------------
    latest_weather = _latest_weather(weather, at_time)
    if latest_weather is not None:
        values["temperature"] = _safe(getattr(latest_weather, "temperature", None))
        values["humidity"] = _safe(getattr(latest_weather, "humidity", None))
        values["wind_speed"] = _safe(getattr(latest_weather, "wind_speed", None))
        values["rainfall_probability"] = _safe(getattr(latest_weather, "rainfall_probability", None))
        meta["weather_recorded_at"] = as_utc(getattr(latest_weather, "recorded_at", None))
        meta["weather_provider"] = getattr(latest_weather, "provider", None)
    else:
        meta["no_weather_before_prediction_time"] = True

    values["rainfall_24h"] = _rainfall_sum(weather, at_time - timedelta(hours=24), at_time)
    values["rainfall_72h"] = _rainfall_sum(weather, at_time - timedelta(hours=72), at_time)

    forecast = _next_weather(weather, at_time)
    if forecast is not None:
        values["forecast_rainfall_mm"] = _safe(getattr(forecast, "rainfall", None))
        meta["forecast_rainfall_probability"] = _safe(getattr(forecast, "rainfall_probability", None))
    else:
        values["forecast_rainfall_mm"] = None

    # --- irrigation history -------------------------------------------------
    past_events = []
    for event in irrigation_events:
        start = as_utc(getattr(event, "start_time", None))
        if start is None or start > at_time:
            continue
        past_events.append((start, event))
    past_events.sort(key=lambda item: item[0])

    if past_events:
        last_start = past_events[-1][0]
        values["hours_since_last_irrigation"] = round((at_time - last_start).total_seconds() / 3600.0, 3)
        recent = [
            _safe(getattr(event, "water_volume_litres", None))
            for start, event in past_events
            if start >= at_time - timedelta(days=7)
        ]
        measured = [v for v in recent if v is not None]
        values["irrigation_litres_7d"] = sum(measured) if measured else None
    else:
        values["hours_since_last_irrigation"] = None
        values["irrigation_litres_7d"] = None

    # --- static / temporal --------------------------------------------------
    values["area_acres"] = _safe(area_acres)
    sowing = as_utc(sowing_date)
    if sowing is not None:
        values["crop_age_days"] = round((at_time - sowing).total_seconds() / 86400.0, 2)

    hour = at_time.hour + at_time.minute / 60.0
    values["hour_sin"] = round(math.sin(2 * math.pi * hour / 24.0), 6)
    values["hour_cos"] = round(math.cos(2 * math.pi * hour / 24.0), 6)
    doy = at_time.timetuple().tm_yday
    values["doy_sin"] = round(math.sin(2 * math.pi * doy / 365.25), 6)
    values["doy_cos"] = round(math.cos(2 * math.pi * doy / 365.25), 6)

    context.values = values
    context.categoricals = {
        "crop_type": _normalise_crop(crop_type),
        "soil_type": _normalise_soil(soil_type),
        "growth_stage": _normalise_stage(growth_stage),
    }
    context.meta = meta
    return context


def vectorise(context: FeatureContext) -> dict[str, Optional[float]]:
    """Flatten a context into the ordered feature vector."""
    vector: dict[str, Optional[float]] = {name: context.values.get(name) for name in NUMERIC_FEATURES}
    for feature in CATEGORICAL_FEATURES:
        value = context.categoricals.get(feature, "other")
        for candidate in _vocab_for(feature):
            vector[f"{feature}={candidate}"] = 1.0 if candidate == value else 0.0
    return vector


@dataclass
class TrainingSample:
    """One supervised training row."""

    field_id: int
    feature_time: datetime
    target_time: datetime
    features: dict[str, Optional[float]]
    target: float
    crop_type: Optional[str]
    field_name: Optional[str] = None


def find_horizon_target(
    readings: Sequence[Any],
    at_time: datetime,
    horizon_hours: int = HORIZON_HOURS,
    tolerance_hours: int = HORIZON_TOLERANCE_HOURS,
) -> Optional[tuple[datetime, float]]:
    """Find the observation that represents the value at ``at_time + horizon``.

    The first reading at or after the horizon and within the tolerance
    window is used. No interpolation is performed.
    """
    at_time = as_utc(at_time)
    if at_time is None:
        return None
    low = at_time + timedelta(hours=horizon_hours)
    high = at_time + timedelta(hours=horizon_hours + tolerance_hours)
    candidates = []
    for reading in readings:
        recorded = as_utc(getattr(reading, "recorded_at", None))
        if recorded is None or recorded < low or recorded > high:
            continue
        moisture = _safe(getattr(reading, "moisture_percentage", None))
        if moisture is None:
            continue
        candidates.append((recorded, moisture))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[0]


def build_training_samples(
    *,
    field_id: int,
    field_name: Optional[str],
    crop_type: Optional[str],
    soil_type: Optional[str],
    growth_stage: Optional[str],
    area_acres: Optional[float],
    sowing_date: Optional[datetime],
    readings: Sequence[Any],
    weather: Sequence[Any],
    irrigation_events: Sequence[Any],
    horizon_hours: int = HORIZON_HOURS,
) -> list[TrainingSample]:
    """Build supervised samples for one field.

    A sample is created for every reading that has a matching observation at
    the horizon. The last readings of a series usually have no target and are
    therefore not samples.
    """
    samples: list[TrainingSample] = []
    for reading in readings:
        recorded = as_utc(getattr(reading, "recorded_at", None))
        if recorded is None:
            continue
        target = find_horizon_target(readings, recorded, horizon_hours=horizon_hours)
        if target is None:
            continue
        target_time, target_value = target
        context = build_context(
            at_time=recorded,
            readings=readings,
            weather=weather,
            irrigation_events=irrigation_events,
            crop_type=crop_type,
            soil_type=soil_type,
            growth_stage=growth_stage,
            area_acres=area_acres,
            sowing_date=sowing_date,
        )
        samples.append(
            TrainingSample(
                field_id=field_id,
                feature_time=recorded,
                target_time=target_time,
                features=vectorise(context),
                target=target_value,
                crop_type=crop_type,
                field_name=field_name,
            )
        )
    return samples
