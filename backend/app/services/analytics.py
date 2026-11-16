"""Water usage analytics.

Rules enforced here:

* Only **measured** irrigation events count as water used. A missing
  ``water_volume_litres`` stays missing and is counted separately as
  "events without a measurement".
* Predictions and schedules never count as consumption. Planned volume is
  reported next to actual volume, not merged with it.
* Duration is never converted into a volume unless a calibrated application
  rate exists.
* Aggregations are timezone aware: day, week and month boundaries are
  computed in the requested timezone (default: Asia/Kolkata for Verdant).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Iterable, Optional
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import Field, Profile
from app.models.irrigation import IrrigationEvent, IrrigationSchedule

DEFAULT_TIMEZONE = "Asia/Kolkata"
LITRES_PER_M3 = 1000.0
ACRE = 4046.8564224  # m2


def resolve_timezone(name: Optional[str]) -> ZoneInfo:
    if not name:
        return ZoneInfo(DEFAULT_TIMEZONE)
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo(DEFAULT_TIMEZONE)


def _tz(value: datetime, tz: ZoneInfo) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(tz)


def _day_start(day: date, tz: ZoneInfo) -> datetime:
    return datetime.combine(day, time.min, tzinfo=tz)


def _bucket_key(moment: datetime, tz: ZoneInfo, granularity: str) -> str:
    local = _tz(moment, tz)
    if granularity == "day":
        return local.date().isoformat()
    if granularity == "week":
        iso = local.date().isocalendar()
        monday = local.date() - timedelta(days=local.date().weekday())
        return monday.isoformat()
    if granularity == "month":
        return local.strftime("%Y-%m")
    return local.date().isoformat()


@dataclass
class WaterUsageSummary:
    """Aggregated measured water use for a farmer."""

    total_litres: float
    measured_event_count: int
    unmeasured_event_count: int
    events_without_measurement: list[dict[str, Any]]
    period_start: Optional[str]
    period_end: Optional[str]
    by_field: list[dict[str, Any]]
    by_crop: list[dict[str, Any]]
    by_day: list[dict[str, Any]]
    daily_series: list[dict[str, Any]]
    weekly_series: list[dict[str, Any]]
    monthly_series: list[dict[str, Any]]
    average_per_event_litres: Optional[float]
    average_per_event_days: Optional[float]
    irrigation_frequency_per_week: Optional[float]
    litres_per_acre: Optional[float]
    planned_vs_actual: list[dict[str, Any]]
    estimated_vs_actual: list[dict[str, Any]]
    data_notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_litres": self.total_litres,
            "measured_event_count": self.measured_event_count,
            "unmeasured_event_count": self.unmeasured_event_count,
            "events_without_measurement": self.events_without_measurement,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "by_field": self.by_field,
            "by_crop": self.by_crop,
            "by_day": self.by_day,
            "daily_series": self.daily_series,
            "weekly_series": self.weekly_series,
            "monthly_series": self.monthly_series,
            "average_per_event_litres": self.average_per_event_litres,
            "average_per_event_days": self.average_per_event_days,
            "irrigation_frequency_per_week": self.irrigation_frequency_per_week,
            "litres_per_acre": self.litres_per_acre,
            "planned_vs_actual": self.planned_vs_actual,
            "estimated_vs_actual": self.estimated_vs_actual,
            "data_notes": self.data_notes,
        }


def load_events(
    db: Session,
    user_id: Any,
    *,
    field_id: Optional[int] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> list[IrrigationEvent]:
    query = db.execute(
        select(IrrigationEvent).where(IrrigationEvent.user_id == user_id)
    ).scalars().all()
    events = list(query)
    if field_id is not None:
        events = [e for e in events if e.field_id == field_id]
    if start is not None:
        events = [e for e in events if e.start_time >= start]
    if end is not None:
        events = [e for e in events if e.start_time <= end]
    events.sort(key=lambda e: e.start_time)
    return events


def _series(
    events: Iterable[IrrigationEvent],
    tz: ZoneInfo,
    granularity: str,
) -> list[dict[str, Any]]:
    buckets: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    for event in events:
        if event.water_volume_litres is None:
            continue
        key = _bucket_key(event.start_time, tz, granularity)
        buckets[key] += float(event.water_volume_litres)
        counts[key] += 1
    return [
        {"bucket": key, "litres": round(buckets[key], 1), "events": counts[key]}
        for key in sorted(buckets.keys())
    ]


def water_usage(
    db: Session,
    user_id: Any,
    *,
    field_id: Optional[int] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    timezone_name: Optional[str] = None,
    tz: Optional[ZoneInfo] = None,
) -> WaterUsageSummary:
    """Compute the water usage analytics for a farmer."""
    tz = tz or resolve_timezone(timezone_name)
    events = load_events(db, user_id, field_id=field_id, start=start, end=end)

    fields = {
        f.id: f
        for f in db.execute(select(Field).where(Field.user_id == user_id)).scalars().all()
    }

    total = 0.0
    measured = 0
    unmeasured = 0
    missing_measurements: list[dict[str, Any]] = []
    per_field: dict[int, dict[str, Any]] = {}
    per_crop: dict[str, dict[str, Any]] = {}

    for event in events:
        field = fields.get(event.field_id)
        volume = event.water_volume_litres
        if volume is None:
            unmeasured += 1
            missing_measurements.append(
                {
                    "event_id": event.id,
                    "field_id": event.field_id,
                    "field_name": field.field_name if field else None,
                    "start_time": event.start_time.isoformat(),
                    "duration_minutes": event.duration_minutes,
                }
            )
            continue

        measured += 1
        total += float(volume)

        field_entry = per_field.setdefault(
            event.field_id,
            {
                "field_id": event.field_id,
                "field_name": field.field_name if field else None,
                "crop_type": field.crop_type if field else None,
                "area_acres": field.area_acres if field else None,
                "total_litres": 0.0,
                "events": 0,
            },
        )
        field_entry["total_litres"] += float(volume)
        field_entry["events"] += 1

        if field is not None:
            crop_entry = per_crop.setdefault(
                field.crop_type,
                {"crop_type": field.crop_type, "total_litres": 0.0, "events": 0, "fields": set()},
            )
            crop_entry["total_litres"] += float(volume)
            crop_entry["events"] += 1
            crop_entry["fields"].add(field.id)

    by_field = []
    for entry in per_field.values():
        area = entry.get("area_acres")
        entry["total_litres"] = round(entry["total_litres"], 1)
        entry["litres_per_acre"] = (
            round(entry["total_litres"] / float(area), 1) if area else None
        )
        entry["average_per_event_litres"] = (
            round(entry["total_litres"] / entry["events"], 1) if entry["events"] else None
        )
        by_field.append(entry)
    by_field.sort(key=lambda item: item["total_litres"], reverse=True)

    by_crop = []
    for entry in per_crop.values():
        entry["total_litres"] = round(entry["total_litres"], 1)
        entry["fields"] = sorted(entry["fields"])
        entry["average_per_event_litres"] = (
            round(entry["total_litres"] / entry["events"], 1) if entry["events"] else None
        )
        by_crop.append(entry)
    by_crop.sort(key=lambda item: item["total_litres"], reverse=True)

    total_area = sum(float(f.area_acres) for f in fields.values())
    litres_per_acre = round(total / total_area, 1) if total_area > 0 else None

    average_per_event = round(total / measured, 1) if measured else None

    # Average interval between irrigation events per field.
    intervals: list[float] = []
    by_field_events: dict[int, list[datetime]] = defaultdict(list)
    for event in events:
        by_field_events[event.field_id].append(event.start_time)
    for times in by_field_events.values():
        times.sort()
        for previous, current in zip(times, times[1:]):
            intervals.append((current - previous).total_seconds() / 86400.0)
    average_days = round(sum(intervals) / len(intervals), 2) if intervals else None
    frequency_per_week = (
        round(7.0 / average_days, 2) if average_days and average_days > 0 else None
    )

    by_day: dict[str, dict[str, Any]] = {}
    for event in events:
        if event.water_volume_litres is None:
            continue
        key = _bucket_key(event.start_time, tz, "day")
        entry = by_day.setdefault(key, {"date": key, "total_litres": 0.0, "events": 0})
        entry["total_litres"] += float(event.water_volume_litres)
        entry["events"] += 1
    for entry in by_day.values():
        entry["total_litres"] = round(entry["total_litres"], 1)

    planned_vs_actual = _planned_vs_actual(db, user_id, tz, field_id=field_id)
    estimated_vs_actual = _estimated_vs_actual(db, user_id, events)

    notes: list[str] = []
    if unmeasured:
        notes.append(
            f"{unmeasured} irrigation event(s) have no measured volume and are excluded from every total."
        )
    if not measured:
        notes.append(
            "No measured irrigation volume is recorded yet, so the totals are empty rather than estimated."
        )

    return WaterUsageSummary(
        total_litres=round(total, 1),
        measured_event_count=measured,
        unmeasured_event_count=unmeasured,
        events_without_measurement=missing_measurements,
        period_start=start.isoformat() if start else None,
        period_end=end.isoformat() if end else None,
        by_field=by_field,
        by_crop=by_crop,
        by_day=sorted(by_day.values(), key=lambda item: item["date"]),
        daily_series=_series(events, tz, "day"),
        weekly_series=_series(events, tz, "week"),
        monthly_series=_series(events, tz, "month"),
        average_per_event_litres=average_per_event,
        average_per_event_days=average_days,
        irrigation_frequency_per_week=frequency_per_week,
        litres_per_acre=litres_per_acre,
        planned_vs_actual=planned_vs_actual,
        estimated_vs_actual=estimated_vs_actual,
        data_notes=notes,
    )


def _planned_vs_actual(
    db: Session,
    user_id: Any,
    tz: ZoneInfo,
    *,
    field_id: Optional[int] = None,
) -> list[dict[str, Any]]:
    """Planned (scheduled) volume against the actual measured volume."""
    schedules = (
        db.execute(
            select(IrrigationSchedule).where(IrrigationSchedule.user_id == user_id)
        )
        .scalars()
        .all()
    )
    planned: dict[str, float] = defaultdict(float)
    actual: dict[str, float] = defaultdict(float)

    for schedule in schedules:
        if field_id is not None and schedule.field_id != field_id:
            continue
        key = _bucket_key(
            datetime.combine(schedule.scheduled_date, time.min, tzinfo=timezone.utc), tz, "day"
        )
        if schedule.estimated_volume_litres:
            planned[key] += float(schedule.estimated_volume_litres)
        if schedule.actual_volume_litres:
            actual[key] += float(schedule.actual_volume_litres)

    keys = sorted(set(planned.keys()) | set(actual.keys()))
    return [
        {
            "date": key,
            "planned_litres": round(planned.get(key, 0.0), 1),
            "actual_litres": round(actual.get(key, 0.0), 1),
        }
        for key in keys
    ]


def _estimated_vs_actual(
    db: Session,
    user_id: Any,
    events: list[IrrigationEvent],
) -> list[dict[str, Any]]:
    """Compare the estimate that produced a schedule with what was applied."""
    rows = (
        db.execute(
            select(IrrigationSchedule).where(
                IrrigationSchedule.user_id == user_id,
                IrrigationSchedule.status == "completed",
            )
        )
        .scalars()
        .all()
    )
    events_by_field: dict[int, list[IrrigationEvent]] = defaultdict(list)
    for event in events:
        events_by_field[event.field_id].append(event)

    results = []
    for row in rows:
        estimated = row.estimated_volume_litres
        actual = row.actual_volume_litres
        if estimated is None and actual is None:
            continue
        difference = None
        difference_ratio = None
        if estimated is not None and actual is not None and estimated > 0:
            difference = round(actual - estimated, 1)
            difference_ratio = round((actual - estimated) / estimated * 100.0, 1)
        results.append(
            {
                "schedule_id": row.id,
                "field_id": row.field_id,
                "field_name": row.field.field_name if row.field else None,
                "scheduled_date": row.scheduled_date.isoformat() if row.scheduled_date else None,
                "estimated_litres": estimated,
                "actual_litres": actual,
                "difference_litres": difference,
                "difference_percent": difference_ratio,
            }
        )
    return results


def period_totals(
    db: Session,
    user_id: Any,
    *,
    tz: ZoneInfo,
) -> dict[str, Any]:
    """Today / this week / this month measured usage."""
    now = datetime.now(timezone.utc).astimezone(tz)
    today = now.date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    events = load_events(db, user_id)

    def _sum_between(start_date: date, end_date: date) -> tuple[float, int]:
        total = 0.0
        count = 0
        for event in events:
            if event.water_volume_litres is None:
                continue
            local = _tz(event.start_time, tz)
            if start_date <= local.date() <= end_date:
                total += float(event.water_volume_litres)
                count += 1
        return round(total, 1), count

    today_litres, today_events = _sum_between(today, today)
    week_litres, week_events = _sum_between(week_start, today)
    month_litres, month_events = _sum_between(month_start, today)

    return {
        "today": {"litres": today_litres, "events": today_events},
        "this_week": {"litres": week_litres, "events": week_events},
        "this_month": {"litres": month_litres, "events": month_events},
        "timezone": str(tz),
        "week_start": week_start.isoformat(),
        "month_start": month_start.isoformat(),
    }


def previous_period_comparison(
    db: Session,
    user_id: Any,
    *,
    tz: ZoneInfo,
    days: int = 7,
) -> dict[str, Any]:
    """Compare the current window with the preceding window of the same length."""
    now = datetime.now(timezone.utc).astimezone(tz)
    today = now.date()
    current_start = today - timedelta(days=days - 1)
    previous_start = current_start - timedelta(days=days)
    previous_end = current_start - timedelta(days=1)

    events = load_events(db, user_id)

    def _sum(start_date: date, end_date: date) -> float:
        total = 0.0
        for event in events:
            if event.water_volume_litres is None:
                continue
            local = _tz(event.start_time, tz)
            if start_date <= local.date() <= end_date:
                total += float(event.water_volume_litres)
        return round(total, 1)

    current = _sum(current_start, today)
    previous = _sum(previous_start, previous_end)
    change = None
    change_percent = None
    if previous > 0:
        change = round(current - previous, 1)
        change_percent = round((current - previous) / previous * 100.0, 1)
    return {
        "days": days,
        "current_start": current_start.isoformat(),
        "current_end": today.isoformat(),
        "previous_start": previous_start.isoformat(),
        "previous_end": previous_end.isoformat(),
        "current_litres": current,
        "previous_litres": previous,
        "change_litres": change,
        "change_percent": change_percent,
    }
