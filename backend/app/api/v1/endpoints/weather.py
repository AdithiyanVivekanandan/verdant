from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from uuid import UUID
import httpx

from app.core.database import get_db
from app.api.deps import get_current_user
from app.core.config import settings
from app.models.base import Profile, Field, WeatherRecord
from app.crud import get_field_by_id

router = APIRouter()


def classify_condition(code: int) -> str:
    if 200 <= code < 300:
        return "Thunderstorm"
    if 300 <= code < 400:
        return "Drizzle"
    if 500 <= code < 600:
        return "Rain"
    if 600 <= code < 700:
        return "Snow"
    if 700 <= code < 800:
        return "Atmosphere"
    if code == 800:
        return "Clear"
    if 801 <= code < 805:
        return "Clouds"
    return "Clear"


async def fetch_openweather(lat: float, lon: float) -> Optional[dict]:
    if not settings.OPENWEATHERMAP_API_KEY:
        return None
    url = f"{settings.OPENWEATHERMAP_BASE_URL}/weather"
    params = {"lat": lat, "lon": lon, "appid": settings.OPENWEATHERMAP_API_KEY, "units": "metric"}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            return None
        return resp.json()


async def fetch_forecast_openweather(lat: float, lon: float) -> Optional[dict]:
    if not settings.OPENWEATHERMAP_API_KEY:
        return None
    url = f"{settings.OPENWEATHERMAP_BASE_URL}/forecast"
    params = {"lat": lat, "lon": lon, "appid": settings.OPENWEATHERMAP_API_KEY, "units": "metric"}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            return None
        return resp.json()


def _latest_live_weather(db: Session, field_id: int, max_age_hours: int = 24):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    return (
        db.query(WeatherRecord)
        .filter(
            WeatherRecord.field_id == field_id,
            WeatherRecord.provider == "openweathermap",
            WeatherRecord.recorded_at >= cutoff,
        )
        .order_by(WeatherRecord.recorded_at.desc())
        .first()
    )


@router.get("/current/{field_id}")
async def current_weather(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    field = get_field_by_id(db, field_id, current_user.id)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    if not field.latitude or not field.longitude:
        return {
            "field_id": field.id,
            "available": False,
            "source": "unavailable",
            "reason": "no_location",
            "message": "Add latitude and longitude to this field to fetch live weather.",
            "recorded_at": None,
        }

    data = None
    try:
        data = await fetch_openweather(field.latitude, field.longitude)
    except Exception:
        data = None

    if data:
        main = data.get("main", {})
        weather = (data.get("weather") or [{}])[0]
        wind = data.get("wind", {})
        temperature = round(float(main.get("temp", 0.0)), 1)
        conditions = classify_condition(int(weather.get("id", 800)))
        humidity = round(float(main.get("humidity", 0.0)), 1)
        rainfall = round(float((data.get("rain") or {}).get("1h", 0.0)), 1)
        rainfall_probability = round(float(data.get("pop", 0.0) * 100), 1)
        wind_speed = round(float(wind.get("speed", 0.0)), 1)
        recorded_at = datetime.now(timezone.utc)

        record = WeatherRecord(
            field_id=field.id,
            provider="openweathermap",
            temperature=temperature,
            humidity=humidity,
            rainfall_probability=rainfall_probability,
            rainfall=rainfall,
            wind_speed=wind_speed,
            recorded_at=recorded_at,
        )
        db.add(record)
        db.commit()

        return {
            "field_id": field.id,
            "available": True,
            "source": "openweathermap",
            "reason": "live",
            "temperature": temperature,
            "conditions": conditions,
            "humidity": humidity,
            "rainfall_probability": rainfall_probability,
            "rainfall": rainfall,
            "wind_speed": wind_speed,
            "recorded_at": recorded_at,
            "cached": False,
        }

    cached = _latest_live_weather(db, field.id, max_age_hours=24)
    if cached:
        return {
            "field_id": field.id,
            "available": True,
            "source": "openweathermap",
            "reason": "cached",
            "temperature": cached.temperature,
            "conditions": None,
            "humidity": cached.humidity,
            "rainfall_probability": cached.rainfall_probability or 0,
            "rainfall": cached.rainfall or 0,
            "wind_speed": cached.wind_speed,
            "recorded_at": cached.recorded_at,
            "cached": True,
        }

    return {
        "field_id": field.id,
        "available": False,
        "source": "unavailable",
        "reason": "provider_unavailable",
        "message": "Live weather is unavailable. No measurements are shown rather than estimated values.",
        "recorded_at": None,
    }


@router.get("/forecast/{field_id}")
async def forecast_weather(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: Profile = Depends(get_current_user),
):
    field = get_field_by_id(db, field_id, current_user.id)
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    if not field.latitude or not field.longitude:
        return {
            "field_id": field.id,
            "available": False,
            "source": "unavailable",
            "reason": "no_location",
            "message": "Add latitude and longitude to this field to fetch a forecast.",
            "forecast": [],
        }

    data = None
    try:
        data = await fetch_forecast_openweather(field.latitude, field.longitude)
    except Exception:
        data = None

    if not data:
        return {
            "field_id": field.id,
            "available": False,
            "source": "unavailable",
            "reason": "provider_unavailable",
            "message": "Live forecast is unavailable. No forecast values are invented.",
            "forecast": [],
        }

    forecast = []
    seen_dates = set()
    for entry in data.get("list", []):
        dt = datetime.fromtimestamp(entry["dt"], tz=timezone.utc)
        date_str = dt.strftime("%Y-%m-%d")
        if date_str in seen_dates:
            continue
        seen_dates.add(date_str)
        if len(forecast) >= 5:
            break
        main = entry.get("main", {})
        weather = (entry.get("weather") or [{}])[0]
        wind = entry.get("wind", {})
        forecast.append({
            "date": date_str,
            "temperature": round(float(main.get("temp", 0.0)), 1),
            "min_temperature": round(float(main.get("temp_min", 0.0)), 1),
            "max_temperature": round(float(main.get("temp_max", 0.0)), 1),
            "conditions": classify_condition(int(weather.get("id", 800))),
            "humidity": round(float(main.get("humidity", 0.0)), 1),
            "rainfall_probability": round(float(entry.get("pop", 0.0) * 100), 1),
            "wind_speed": round(float(wind.get("speed", 0.0)), 1),
        })

    return {
        "field_id": field.id,
        "available": True,
        "source": "openweathermap",
        "reason": "live",
        "forecast": forecast,
    }
