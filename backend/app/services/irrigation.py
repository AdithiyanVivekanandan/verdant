"""Rule-based irrigation guidance.

The guidance is deliberately transparent: it uses a published crop/soil moisture
band, the latest reading, and only live weather records. It never invents
measurements and it never claims to be a validated predictive model.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional


CROP_BANDS: dict[str, tuple[float, float, str]] = {
    "Rice": (35.0, 75.0, "Rice is commonly kept in a wetter band."),
    "Wheat": (30.0, 65.0, "Wheat commonly uses a moderate band."),
    "Maize": (30.0, 70.0, "Maize commonly uses a moderate band."),
    "Cotton": (25.0, 65.0, "Cotton commonly tolerates a wider band."),
    "Sugarcane": (40.0, 80.0, "Sugarcane commonly uses a wetter band."),
    "Tomato": (40.0, 70.0, "Tomato commonly uses a moderate band."),
    "Ragi": (25.0, 60.0, "Ragi commonly tolerates a drier band."),
}

# Positive adjustments raise the target band for fast-draining soils.
SOIL_ADJUSTMENTS: dict[str, float] = {
    "Sandy soil": 5.0,
    "Red soil": 0.0,
    "Loamy soil": 0.0,
    "Black soil": -5.0,
    "Clay soil": -5.0,
}

DEFAULT_BAND = (30.0, 70.0, "No crop-specific band is available; a general band is used.")


def _as_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def thresholds_for(crop_type: str, soil_type: str) -> dict[str, Any]:
    low, high, note = CROP_BANDS.get(crop_type, DEFAULT_BAND)
    adjustment = SOIL_ADJUSTMENTS.get(soil_type, 0.0)
    low = max(5.0, min(90.0, low + adjustment))
    high = max(low + 5.0, min(95.0, high + adjustment))
    return {
        "low": round(low, 1),
        "high": round(high, 1),
        "crop_band": crop_type in CROP_BANDS,
        "soil_adjusted": adjustment != 0.0,
        "note": note,
    }


def reading_freshness(
    recorded_at: Optional[datetime],
    uses_sensor: bool,
    now: Optional[datetime] = None,
) -> tuple[str, Optional[float]]:
    """Return (fresh|delayed|stale|missing, age_hours).

    Sensor readings are expected frequently, so they go stale faster than
    manual readings. The thresholds are stated in the product docs.
    """
    recorded = _as_utc(recorded_at)
    if recorded is None:
        return "missing", None
    now = now or datetime.now(timezone.utc)
    age_hours = max(0.0, (now - recorded).total_seconds() / 3600.0)
    if uses_sensor:
        if age_hours <= 2:
            return "fresh", round(age_hours, 2)
        if age_hours <= 24:
            return "delayed", round(age_hours, 2)
        return "stale", round(age_hours, 2)
    if age_hours <= 24:
        return "fresh", round(age_hours, 2)
    if age_hours <= 72:
        return "delayed", round(age_hours, 2)
    return "stale", round(age_hours, 2)


def moisture_state(moisture: float, thresholds: dict[str, Any]) -> tuple[str, str]:
    low = thresholds["low"]
    high = thresholds["high"]
    if moisture < low:
        if moisture <= low - 5:
            return "critical", "below_band"
        return "needs_review", "below_band"
    if moisture > high:
        if moisture >= high + 10:
            return "critical", "above_band"
        return "needs_review", "above_band"
    return "healthy", "within_band"


def field_state(
    *,
    moisture: Optional[float],
    recorded_at: Optional[datetime],
    has_sensor: bool,
    uses_sensor: bool,
    crop_type: str,
    soil_type: str,
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    thresholds = thresholds_for(crop_type, soil_type)
    freshness, age_hours = reading_freshness(recorded_at, uses_sensor, now)

    if moisture is None:
        return {
            "status": "sensor_unavailable" if has_sensor else "no_data",
            "reason": "sensor_no_readings" if has_sensor else "no_readings",
            "freshness": "missing",
            "age_hours": None,
            "requires_attention": True,
            **thresholds,
        }

    if freshness == "stale":
        status, reason = "stale", "stale_reading"
    else:
        status, reason = moisture_state(float(moisture), thresholds)

    return {
        "status": status,
        "reason": reason,
        "freshness": freshness,
        "age_hours": age_hours,
        "requires_attention": status in {"critical", "needs_review", "stale"},
        **thresholds,
    }


def build_guidance(
    *,
    field: Any,
    latest: Any,
    sensors: list[Any],
    live_weather: Optional[Any],
    now: Optional[datetime] = None,
) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    has_sensor = bool(sensors)
    sensor_identifiers = [s.sensor_identifier for s in sensors]
    thresholds = thresholds_for(field.crop_type, field.soil_type)

    moisture = float(latest.moisture_percentage) if latest else None
    recorded_at = _as_utc(latest.recorded_at) if latest else None
    uses_sensor = bool(latest and (latest.sensor_id is not None or latest.source == "iot_sensor"))
    state = field_state(
        moisture=moisture,
        recorded_at=recorded_at,
        has_sensor=has_sensor,
        uses_sensor=uses_sensor,
        crop_type=field.crop_type,
        soil_type=field.soil_type,
        now=now,
    )
    age_hours = state["age_hours"]

    weather_input = None
    rain_expected = False
    if live_weather is not None:
        weather_age = (now - _as_utc(live_weather.recorded_at)).total_seconds() / 3600.0
        if weather_age <= 6:
            probability = float(live_weather.rainfall_probability or 0)
            rain_expected = probability >= 60
            weather_input = {
                "temperature": live_weather.temperature,
                "rainfall_probability": probability,
                "rainfall_mm": live_weather.rainfall or 0,
                "recorded_at": live_weather.recorded_at.isoformat(),
                "provider": live_weather.provider,
                "rain_expected": rain_expected,
            }

    recommendation = "no_irrigation"
    urgency = "routine"
    headline = "No irrigation needed now"
    explanation = "The latest soil moisture is inside the crop and soil band for this field."
    actions = ["Check the field again tomorrow or after a change in weather."]
    confidence = "high"

    if latest is None:
        recommendation = "record_reading"
        urgency = "action"
        headline = "Not enough current information"
        explanation = (
            "No reading has been recorded for this field yet, so Verdant cannot "
            "judge the soil moisture."
        )
        actions = [
            "Record a manual reading or connect a sensor.",
            "Walk the field and check soil at a few places before irrigating.",
        ]
        confidence = "low"
    elif state["status"] == "stale":
        recommendation = "check_sensor"
        urgency = "action"
        headline = "Reading is out of date"
        explanation = (
            f"The latest reading is {age_hours:.0f} hours old. Verdant will not "
            "base an irrigation decision on stale data."
        )
        actions = [
            "Check that the sensor is powered and reporting.",
            "Record a current manual reading if the sensor is unavailable.",
        ]
        confidence = "low"
    elif state["reason"] == "below_band":
        if rain_expected:
            recommendation = "rain_expected"
            urgency = "watch"
            headline = "Rain is likely; check before irrigating"
            explanation = (
                f"Soil moisture ({moisture:.1f}%) is below the lower band "
                f"({thresholds['low']:.1f}%), but live weather reports a "
                f"{weather_input['rainfall_probability']:.0f}% chance of rain."
            )
            actions = [
                "Check the field and the sky before starting irrigation.",
                "If the rain does not arrive, irrigate and record the action.",
            ]
            confidence = "medium"
        elif state["status"] == "critical":
            recommendation = "irrigate_now"
            urgency = "today"
            headline = "Irrigate this field today"
            explanation = (
                f"Soil moisture ({moisture:.1f}%) is more than 5 points below "
                f"the lower band ({thresholds['low']:.1f}%) for "
                f"{field.crop_type} in {field.soil_type}."
            )
            actions = [
                "Irrigate today, following your normal local practice.",
                "Record a new reading after irrigation to confirm the change.",
            ]
            confidence = "high"
        else:
            recommendation = "irrigate_soon"
            urgency = "soon"
            headline = "Plan irrigation soon"
            explanation = (
                f"Soil moisture ({moisture:.1f}%) is below the lower band "
                f"({thresholds['low']:.1f}%) for {field.crop_type} in "
                f"{field.soil_type}."
            )
            actions = [
                "Plan irrigation before the next dry spell.",
                "Check the field in person before applying water.",
            ]
            confidence = "high" if uses_sensor else "medium"
    elif state["reason"] == "above_band":
        recommendation = "hold_irrigation"
        urgency = "watch"
        headline = "Hold irrigation; the soil is wetter than the band"
        explanation = (
            f"Soil moisture ({moisture:.1f}%) is above the upper band "
            f"({thresholds['high']:.1f}%). Extra water may be lost or waterlog "
            f"the crop."
        )
        actions = [
            "Do not irrigate now.",
            "Check drainage if the reading stays high for more than a day.",
        ]
        confidence = "high" if uses_sensor else "medium"
    elif rain_expected:
        recommendation = "no_irrigation"
        urgency = "routine"
        headline = "No irrigation needed; rain is likely"
        explanation = (
            f"Moisture is inside the band ({thresholds['low']:.1f}–"
            f"{thresholds['high']:.1f}%) and live weather reports a "
            f"{weather_input['rainfall_probability']:.0f}% chance of rain."
        )
        actions = ["Recheck after the forecast rain has passed."]
        confidence = "medium"

    if not thresholds["crop_band"]:
        confidence = "low" if confidence == "high" else confidence

    limitations = [
        "This is a rule-based guide using one soil-moisture reading, not a validated prediction.",
        "Moisture bands are general crop/soil guidance; local variety, slope, and irrigation method can change the right band.",
        "A sensor measures at one point. Check the field in person before a major irrigation decision.",
    ]
    if not thresholds["crop_band"]:
        limitations.append("No reviewed crop-specific band is stored for this crop; a general band was used.")
    if weather_input is None:
        limitations.append("No recent live weather record was available, so rainfall was not considered.")
    if sensor_identifiers:
        limitations.append(f"Sensor(s) on this field: {', '.join(sensor_identifiers)}.")

    return {
        "field_id": field.id,
        "field_name": field.field_name,
        "generated_at": now.isoformat(),
        "recommendation": recommendation,
        "urgency": urgency,
        "headline": headline,
        "explanation": explanation,
        "actions": actions,
        "confidence": confidence,
        "status": state["status"],
        "reason": state["reason"],
        "thresholds": {
            "low": thresholds["low"],
            "high": thresholds["high"],
            "crop_specific": thresholds["crop_band"],
            "soil_adjusted": thresholds["soil_adjusted"],
        },
        "inputs": {
            "moisture_percentage": moisture,
            "recorded_at": recorded_at.isoformat() if recorded_at else None,
            "freshness": state["freshness"],
            "age_hours": age_hours,
            "source": latest.source if latest else None,
            "sensor_identifier": latest.sensor_identifier if latest else None,
            "has_sensor": has_sensor,
            "sensor_identifiers": sensor_identifiers,
            "crop_type": field.crop_type,
            "soil_type": field.soil_type,
            "growth_stage": field.growth_stage,
            "weather": weather_input,
        },
        "limitations": limitations,
        "review_required": True,
        "review_note": (
            "Agronomic guidance is written and reviewed in English. Other "
            "languages show this English text with a review notice until a "
            "knowledgeable reviewer approves the translation."
        ),
    }
