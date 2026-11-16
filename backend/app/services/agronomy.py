"""Agronomic parameters and the soil-water-balance calculations.

Everything in this module is **configurable and documented**. The values are
general reference figures (FAO-56 style crop coefficients, textbook soil
water constants, the Hargreaves evapotranspiration equation and the USDA-SCS
effective-rainfall approximation). They are *not* calibrated to a local
extension service, so every number produced here is reported with its
assumptions and a confidence flag.

Design rules enforced here:

* A missing input is never silently replaced with zero. ``None`` propagates
  and the caller must label the result as unavailable or partial.
* Water volume is only produced when depth and area are both known.
* Application efficiency is only applied when the farmer supplied it.
* Irrigation duration is only produced when an application rate is known.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field as dataclass_field
from datetime import date, datetime, timezone
from typing import Any, Iterable, Optional

# --------------------------------------------------------------------------
# Unit conversions
# --------------------------------------------------------------------------

ACRE_TO_HECTARE = 0.40468564224
#: 1 mm of water over 1 hectare = 10 000 litres.
LITRES_PER_MM_PER_HECTARE = 10_000.0
LITRES_PER_KILOLITRE = 1000.0

#: Reference evapotranspiration conversion from MJ m-2 day-1 to mm day-1.
MJ_TO_MM_EVAPORATION = 0.408


def acres_to_hectares(acres: Optional[float]) -> Optional[float]:
    """Convert acres to hectares. ``None`` stays ``None``."""
    if acres is None:
        return None
    return float(acres) * ACRE_TO_HECTARE


def depth_mm_to_litres(depth_mm: Optional[float], area_ha: Optional[float]) -> Optional[float]:
    """Water volume (litres) = depth (mm) x area (ha) x 10 000.

    Returns ``None`` when either input is unknown: a volume is never guessed.
    """
    if depth_mm is None or area_ha is None:
        return None
    return float(depth_mm) * float(area_ha) * LITRES_PER_MM_PER_HECTARE


def litres_to_depth_mm(litres: Optional[float], area_ha: Optional[float]) -> Optional[float]:
    """Inverse of :func:`depth_mm_to_litres`."""
    if litres is None or area_ha is None or area_ha <= 0:
        return None
    return float(litres) / (float(area_ha) * LITRES_PER_MM_PER_HECTARE)


def litres_per_acre(litres: Optional[float], area_acres: Optional[float]) -> Optional[float]:
    """Water use per acre. Returns ``None`` when the area is unknown."""
    if litres is None or area_acres is None or area_acres <= 0:
        return None
    return float(litres) / float(area_acres)


def litres_to_kilolitres(litres: Optional[float]) -> Optional[float]:
    if litres is None:
        return None
    return float(litres) / LITRES_PER_KILOLITRE


# --------------------------------------------------------------------------
# Crop parameters
# --------------------------------------------------------------------------

#: Growth stages recognised by the platform, mapped to the FAO-56 style
#: growth-stage groups used for the crop coefficient.
STAGE_GROUPS: dict[str, str] = {
    "seedling": "initial",
    "emergence": "initial",
    "establishment": "initial",
    "vegetative": "development",
    "vegetative growth": "development",
    "development": "development",
    "flowering": "mid",
    "flowering and fruiting": "mid",
    "fruiting": "mid",
    "tillering": "mid",
    "maturity": "late",
    "late": "late",
    "ripening": "late",
    "harvest": "late",
}


@dataclass(frozen=True)
class CropParameters:
    """Reference parameters for one crop."""

    name: str
    #: Crop coefficient (Kc) per FAO-56 stage group: initial, development, mid, late.
    kc: dict[str, float]
    #: Maximum rooting depth in metres at full growth.
    max_root_depth_m: float
    #: Typical daily water use in mm day-1 during the peak (mid) stage.
    peak_daily_mm: float
    source: str = "FAO-56 (Allen et al., 1998) general values, not locally calibrated"
    notes: str = ""


CROP_PARAMETERS: dict[str, CropParameters] = {
    "rice": CropParameters(
        name="Rice",
        kc={"initial": 1.05, "development": 1.20, "mid": 1.20, "late": 0.90},
        max_root_depth_m=0.5,
        peak_daily_mm=6.0,
        notes="Rice is normally kept in a wet or saturated soil; deficit scheduling is not usual.",
    ),
    "wheat": CropParameters(
        name="Wheat",
        kc={"initial": 0.40, "development": 0.80, "mid": 1.15, "late": 0.35},
        max_root_depth_m=1.2,
        peak_daily_mm=5.0,
    ),
    "maize": CropParameters(
        name="Maize",
        kc={"initial": 0.35, "development": 0.70, "mid": 1.20, "late": 0.60},
        max_root_depth_m=1.3,
        peak_daily_mm=6.0,
    ),
    "cotton": CropParameters(
        name="Cotton",
        kc={"initial": 0.35, "development": 0.75, "mid": 1.15, "late": 0.70},
        max_root_depth_m=1.2,
        peak_daily_mm=6.0,
    ),
    "sugarcane": CropParameters(
        name="Sugarcane",
        kc={"initial": 0.40, "development": 0.90, "mid": 1.20, "late": 0.70},
        max_root_depth_m=1.8,
        peak_daily_mm=7.0,
    ),
    "tomato": CropParameters(
        name="Tomato",
        kc={"initial": 0.60, "development": 0.85, "mid": 1.15, "late": 0.80},
        max_root_depth_m=0.9,
        peak_daily_mm=5.0,
    ),
    "ragi": CropParameters(
        name="Ragi",
        kc={"initial": 0.35, "development": 0.70, "mid": 1.05, "late": 0.50},
        max_root_depth_m=1.0,
        peak_daily_mm=4.0,
        notes="Ragi (finger millet) is commonly grown under rainfed conditions.",
    ),
}

DEFAULT_CROP_PARAMETERS = CropParameters(
    name="Unspecified crop",
    kc={"initial": 0.40, "development": 0.80, "mid": 1.10, "late": 0.60},
    max_root_depth_m=1.0,
    peak_daily_mm=5.0,
    notes="No reviewed parameter set for this crop; a generic set is used and flagged.",
)


def crop_parameters(crop_type: Optional[str]) -> tuple[CropParameters, bool]:
    """Return ``(parameters, is_crop_specific)`` for a crop name."""
    if not crop_type:
        return DEFAULT_CROP_PARAMETERS, False
    params = CROP_PARAMETERS.get(str(crop_type).strip().lower())
    if params is None:
        return DEFAULT_CROP_PARAMETERS, False
    return params, True


# --------------------------------------------------------------------------
# Soil parameters
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class SoilParameters:
    """Soil water constants expressed as volumetric water content (%).

    ``field_capacity`` and ``wilting_point`` are percentages of volumetric
    soil water content, matching the unit used by the soil moisture sensors
    in this system. ``available_water_fraction`` is the plant-available
    fraction of the total porosity range.
    """

    name: str
    field_capacity: float
    wilting_point: float
    #: Rooting depth in metres at which the soil is wettable in this soil.
    max_effective_depth_m: float
    #: Infiltration rate in mm hour-1, used for rainfall effectiveness notes.
    infiltration_mm_h: float
    source: str = "Textbook soil water constants, indicative only"
    notes: str = ""


SOIL_PARAMETERS: dict[str, SoilParameters] = {
    "sandy soil": SoilParameters("Sandy soil", 18.0, 6.0, 0.6, 25.0, notes="Low water holding, drains fast."),
    "red soil": SoilParameters("Red soil", 30.0, 12.0, 1.0, 12.0),
    "loamy soil": SoilParameters("Loamy soil", 33.0, 13.0, 1.2, 10.0),
    "black soil": SoilParameters("Black soil", 39.0, 18.0, 1.2, 6.0, notes="Heavy clay; slow infiltration."),
    "clay soil": SoilParameters("Clay soil", 40.0, 17.0, 1.0, 5.0),
}

DEFAULT_SOIL_PARAMETERS = SoilParameters("Unspecified soil", 32.0, 12.0, 1.0, 10.0)


def soil_parameters(soil_type: Optional[str]) -> tuple[SoilParameters, bool]:
    if not soil_type:
        return DEFAULT_SOIL_PARAMETERS, False
    params = SOIL_PARAMETERS.get(str(soil_type).strip().lower())
    if params is None:
        return DEFAULT_SOIL_PARAMETERS, False
    return params, True


def stage_group(growth_stage: Optional[str]) -> str:
    """Map a free-text growth stage to an FAO-56 stage group."""
    if not growth_stage:
        return "mid"
    return STAGE_GROUPS.get(str(growth_stage).strip().lower(), "mid")


def root_depth_m(crop: CropParameters, growth_stage: Optional[str]) -> float:
    """Effective rooting depth for the current stage.

    The root system is assumed to reach a fraction of the maximum depth that
    depends on the growth stage.
    """
    group = stage_group(growth_stage)
    fraction = {"initial": 0.25, "development": 0.60, "mid": 0.90, "late": 1.00}[group]
    return max(0.15, crop.max_root_depth_m * fraction)


def crop_coefficient(crop: CropParameters, growth_stage: Optional[str]) -> float:
    return crop.kc[stage_group(growth_stage)]


# --------------------------------------------------------------------------
# Reference evapotranspiration (Hargreaves)
# --------------------------------------------------------------------------

def extraterrestrial_radiation_mj(lat_deg: float, day: date) -> float:
    """FAO-56 equation 21: extraterrestrial radiation Ra (MJ m-2 day-1)."""
    phi = math.radians(float(lat_deg))
    dr = 1 + 0.033 * math.cos(2 * math.pi * day.timetuple().tm_yday / 365)
    delta = 0.409 * math.sin(2 * math.pi * day.timetuple().tm_yday / 365 - 1.39)
    try:
        omega_s = math.acos(max(-1.0, min(1.0, -math.tan(phi) * math.tan(delta))))
    except ValueError:  # pragma: no cover - guarded by clamping above
        omega_s = 0.0
    gsc = 0.0820
    ra = (24 * 60 / math.pi) * gsc * dr * (
        omega_s * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(omega_s)
    )
    return max(0.0, ra)


def hargreaves_et0(
    t_min_c: Optional[float],
    t_max_c: Optional[float],
    lat_deg: Optional[float],
    day: Optional[date] = None,
) -> Optional[float]:
    """Reference evapotranspiration ET0 (mm day-1) via Hargreaves-Samani.

    Returns ``None`` when any required input is missing: ET0 is never
    estimated from an invented temperature range.
    """
    if t_min_c is None or t_max_c is None or lat_deg is None:
        return None
    if t_max_c < t_min_c:
        t_min_c, t_max_c = t_max_c, t_min_c
    day = day or datetime.now(timezone.utc).date()
    ra = extraterrestrial_radiation_mj(float(lat_deg), day)
    if ra <= 0:
        return None
    t_mean = (float(t_min_c) + float(t_max_c)) / 2.0
    dtr = float(t_max_c) - float(t_min_c)
    et0 = 0.0023 * ra * (t_mean + 17.8) * math.sqrt(dtr)
    return max(0.0, et0)


# --------------------------------------------------------------------------
# Effective rainfall
# --------------------------------------------------------------------------

def scs_effective_rainfall(rainfall_mm: float) -> float:
    """USDA-SCS effective rainfall for a single event (mm).

    Pe = P(125 - 0.2 P) / 125 for P <= 250 mm, else 125 mm.
    """
    p = float(rainfall_mm)
    if p <= 0:
        return 0.0
    if p > 250:
        return 125.0
    return max(0.0, p * (125.0 - 0.2 * p) / 125.0)


def effective_rainfall_mm(rainfall_events: Iterable[Optional[float]]) -> Optional[float]:
    """Effective rainfall over a window.

    ``None`` is returned when *no* event carries a measurement, because
    "no observation" and "zero rain" are different facts. A list containing
    only ``None`` values therefore yields ``None``.
    """
    total = 0.0
    observed = False
    for value in rainfall_events:
        if value is None:
            continue
        observed = True
        total += scs_effective_rainfall(float(value))
    if not observed:
        return None
    return total


# --------------------------------------------------------------------------
# Soil water balance
# --------------------------------------------------------------------------

@dataclass
class WaterBalanceResult:
    """Result of the irrigation requirement calculation.

    Every numeric field is optional and ``None`` means "not computable from
    the available inputs" — never "zero".
    """

    current_moisture: Optional[float] = None
    field_capacity: Optional[float] = None
    wilting_point: Optional[float] = None
    root_depth_mm: Optional[float] = None
    root_depth_m: Optional[float] = None
    kc: Optional[float] = None
    et0_mm: Optional[float] = None
    et0_source: Optional[str] = None
    crop_water_use_mm: Optional[float] = None
    depletion_mm: Optional[float] = None
    effective_rainfall_mm: Optional[float] = None
    net_requirement_mm: Optional[float] = None
    gross_requirement_mm: Optional[float] = None
    application_efficiency: Optional[float] = None
    area_ha: Optional[float] = None
    net_volume_litres: Optional[float] = None
    gross_volume_litres: Optional[float] = None
    assumptions: list[str] = dataclass_field(default_factory=list)
    missing_inputs: list[str] = dataclass_field(default_factory=list)
    confidence: str = "low"
    calculation_version: str = "soil-water-balance/1.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_moisture": self.current_moisture,
            "field_capacity": self.field_capacity,
            "wilting_point": self.wilting_point,
            "root_depth_mm": self.root_depth_mm,
            "root_depth_m": self.root_depth_m,
            "kc": self.kc,
            "et0_mm": self.et0_mm,
            "et0_source": self.et0_source,
            "crop_water_use_mm": self.crop_water_use_mm,
            "depletion_mm": self.depletion_mm,
            "effective_rainfall_mm": self.effective_rainfall_mm,
            "net_requirement_mm": self.net_requirement_mm,
            "gross_requirement_mm": self.gross_requirement_mm,
            "application_efficiency": self.application_efficiency,
            "area_ha": self.area_ha,
            "net_volume_litres": self.net_volume_litres,
            "gross_volume_litres": self.gross_volume_litres,
            "assumptions": list(self.assumptions),
            "missing_inputs": list(self.missing_inputs),
            "confidence": self.confidence,
            "calculation_version": self.calculation_version,
        }


def compute_water_balance(
    *,
    current_moisture: Optional[float],
    crop_type: Optional[str],
    soil_type: Optional[str],
    growth_stage: Optional[str],
    area_acres: Optional[float],
    latitude: Optional[float] = None,
    et0_mm: Optional[float] = None,
    et0_source: Optional[str] = None,
    rainfall_events: Optional[Iterable[Optional[float]]] = None,
    horizon_days: float = 1.0,
    application_efficiency: Optional[float] = None,
    target_moisture: Optional[float] = None,
) -> WaterBalanceResult:
    """Compute the irrigation requirement for one field.

    The balance is:

        requirement = depletion_to_target + crop_water_use - effective_rainfall

    where ``depletion_to_target`` uses the plant-available water between the
    current moisture and the target moisture, ``crop_water_use`` is
    ``Kc * ET0 * horizon`` and ``effective_rainfall`` is the USDA-SCS
    effective rainfall over the same window.

    Missing values never become zero: the affected term is omitted from the
    balance, the missing input is recorded, and the confidence drops.
    """
    crop, crop_known = crop_parameters(crop_type)
    soil, soil_known = soil_parameters(soil_type)

    result = WaterBalanceResult()
    result.assumptions.append(
        f"Soil moisture readings are treated as volumetric water content (%): "
        f"field capacity {soil.field_capacity:.1f}%, wilting point {soil.wilting_point:.1f}% "
        f"for {soil.name.lower()}."
    )
    if not crop_known:
        result.assumptions.append(
            "No reviewed crop parameter set for this crop; a generic parameter set is used."
        )
    if not soil_known:
        result.assumptions.append(
            "No reviewed soil parameter set for this soil; a generic parameter set is used."
        )

    result.field_capacity = soil.field_capacity
    result.wilting_point = soil.wilting_point
    result.area_ha = acres_to_hectares(area_acres)

    kc = crop_coefficient(crop, growth_stage)
    result.kc = kc
    root_m = root_depth_m(crop, growth_stage)
    result.root_depth_m = round(root_m, 3)
    result.root_depth_mm = root_m * 1000.0

    # --- crop water use ---------------------------------------------------
    if et0_mm is not None:
        result.et0_mm = round(float(et0_mm), 3)
        result.et0_source = et0_source or "measured"
        result.crop_water_use_mm = round(kc * float(et0_mm) * horizon_days, 2)
    else:
        result.missing_inputs.append("reference_evapotranspiration")
        result.assumptions.append(
            "No reference evapotranspiration is available, so crop water use is excluded "
            "from the balance and the estimate reflects the depletion only."
        )

    # --- effective rainfall ----------------------------------------------
    if rainfall_events is None:
        result.missing_inputs.append("rainfall_observations")
        result.assumptions.append(
            "No rainfall observations are available for the window, so no rainfall credit is applied."
        )
    else:
        effective = effective_rainfall_mm(rainfall_events)
        if effective is None:
            result.missing_inputs.append("rainfall_observations")
            result.assumptions.append(
                "Rainfall records exist but none carry a measured amount, so no rainfall credit is applied."
            )
        else:
            result.effective_rainfall_mm = round(effective, 2)

    # --- depletion to the target moisture --------------------------------
    if current_moisture is None:
        result.missing_inputs.append("current_soil_moisture")
        result.confidence = "low"
        return result

    result.current_moisture = float(current_moisture)
    target = target_moisture
    if target is None:
        target = soil.field_capacity
        result.assumptions.append(
            "Target is the soil field capacity, i.e. the wettest moisture the soil holds "
            "against gravity."
        )
    depletion = max(0.0, (float(target) - float(current_moisture)) / 100.0 * result.root_depth_mm)
    result.depletion_mm = round(depletion, 2)

    requirement = depletion
    if result.crop_water_use_mm is not None:
        requirement += result.crop_water_use_mm
    if result.effective_rainfall_mm is not None:
        requirement -= result.effective_rainfall_mm
    requirement = max(0.0, requirement)
    result.net_requirement_mm = round(requirement, 2)

    # --- gross requirement (efficiency) ----------------------------------
    if application_efficiency is not None and 0 < application_efficiency <= 1:
        result.application_efficiency = float(application_efficiency)
        result.gross_requirement_mm = round(requirement / float(application_efficiency), 2)
        result.assumptions.append(
            f"Application efficiency of {application_efficiency:.0%} (supplied by the farmer) "
            "converts the net requirement into the gross depth to apply."
        )
    else:
        result.gross_requirement_mm = result.net_requirement_mm
        result.assumptions.append(
            "No application efficiency is recorded for this field, so the gross requirement "
            "equals the net requirement and the applied volume may need to be higher in practice."
        )

    result.net_volume_litres = depth_mm_to_litres(result.net_requirement_mm, result.area_ha)
    result.gross_volume_litres = depth_mm_to_litres(result.gross_requirement_mm, result.area_ha)

    # --- sanity flags -------------------------------------------------------
    sanity_failed = False
    if result.gross_requirement_mm is not None and result.gross_requirement_mm > 100:
        result.assumptions.append(
            "The computed refill depth is larger than 100 mm. Verify the sensor calibration "
            "and the root depth assumption before applying this volume."
        )
        sanity_failed = True
    if result.current_moisture is not None and result.current_moisture < result.wilting_point:
        result.assumptions.append(
            "The moisture reading is below the wilting point for this soil, which usually "
            "points to a sensor problem rather than a real reading."
        )
        sanity_failed = True

    # --- confidence --------------------------------------------------------
    complete = (
        result.crop_water_use_mm is not None
        and result.effective_rainfall_mm is not None
        and crop_known
        and soil_known
    )
    if sanity_failed:
        result.confidence = "low"
    elif complete:
        result.confidence = "medium"
    else:
        result.confidence = "low"
    return result


def duration_minutes_for_volume(
    volume_litres: Optional[float],
    application_rate_litres_per_hour: Optional[float],
) -> Optional[float]:
    """Irrigation duration in minutes for a known volume and application rate.

    Returns ``None`` when the application rate is unknown: a duration is
    never invented from a volume.
    """
    if volume_litres is None or not application_rate_litres_per_hour:
        return None
    if application_rate_litres_per_hour <= 0:
        return None
    return round(float(volume_litres) / float(application_rate_litres_per_hour) * 60.0, 1)
