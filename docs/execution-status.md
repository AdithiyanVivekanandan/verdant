# Execution Status

Updated: 2026-11-16

## Scope of this session

Implementation of the **Verdant ML irrigation intelligence layer**: data
foundation, ML pipeline, irrigation requirement and volume estimation,
daily scheduling, water usage analytics, the redesigned dashboard, the field
intelligence view, the API surface and the tests.

## Completed work

### Data foundation (backend)

- New Alembic migration `0004_irrigation_intelligence.py` (additive only —
  no existing table was modified or dropped).
- New tables: `irrigation_events`, `irrigation_schedules`,
  `irrigation_predictions`, `field_irrigation_settings`,
  `farmer_irrigation_preferences`.
- Additive nullable columns on `weather_records`: `temperature_min`,
  `temperature_max`, `et0_mm`.
- Foreign keys with `ON DELETE CASCADE` (schedule → prediction uses
  `SET NULL`), unique constraint `uq_irrigation_schedule_field_date` for
  duplicate prevention, check constraints on volume, duration, time window
  and confidence, and indexes on every ownership and time column.
- Removed a duplicated index declaration on `sensor_readings.recorded_at`
  that would have failed on a fresh `create_all`.

### Agronomy and calculation layer (`app/services/agronomy.py`)

- Unit conversions: acres → hectares, depth (mm) → litres
  (1 mm over 1 ha = 10 000 L), litres → depth, litres per acre,
  litres → kilolitres.
- Crop parameters (FAO-56 style crop coefficients, maximum rooting depth,
  peak daily use) for Rice, Wheat, Maize, Cotton, Sugarcane, Tomato, Ragi,
  with an explicit generic fallback that is flagged.
- Soil parameters (field capacity, wilting point, effective depth,
  infiltration rate) for the five soils used in Verdant.
- Hargreaves-Samani reference evapotranspiration with a correctly computed
  extraterrestrial radiation term; returns `None` when an input is missing.
- USDA-SCS effective rainfall; distinguishes "no rain" from "no
  observation".
- Soil water balance: `requirement = depletion to target + crop water use
  − effective rainfall`, with an optional efficiency conversion to the gross
  depth. Missing inputs are recorded, never zero-filled.
- Sanity checks: a refill depth above 100 mm or a reading below the
  wilting point lowers the confidence and states the reason.

### ML pipeline (`app/ml/`)

```
app/ml/
├── features/engineering.py     30 numeric + 19 one-hot features
├── preprocessing/imputer.py     training-median imputation
├── baselines/baselines.py       persistence, linear trend
├── training/dataset.py          data set builder + requirement report
├── training/trainer.py          time-aware split, evaluation, promotion
├── evaluation/metrics.py        MAE, RMSE, R², bias, per-group errors
├── inference/predictor.py       prediction + water balance + explanation
├── models/registry.py           versioned artifact store
└── pipelines/irrigation_pipeline.py  schedule generation, completion
```

- The model predicts **soil moisture at a 24 h horizon**; the irrigation
  requirement is derived from that prediction with the water balance. This
  avoids training on invented requirement labels.
- Time-aware split (70/15/15 by feature timestamp). Random shuffling is
  never used.
- A trained model is only promoted when it beats the persistence baseline
  on the validation split.
- Reproducible: fixed seed, `n_jobs=1` so the fit is bit-for-bit
  repeatable, artifact metadata records data facts, periods, metrics,
  limitations and the production requirement.
- Graceful degradation: no artifact → transparent baseline; no reading →
  no prediction at all; failing model → caught and the baseline takes over.

### Scheduling

- One schedule row per field per day, enforced by a unique constraint and
  reused on regeneration.
- Priority derived from the crop/soil band, the predicted moisture and the
  data freshness: `low | medium | high | critical | uncertain`.
- A stale or missing reading produces an `uncertain` entry with **no
  volume** — no recommendation is made from outdated data.
- Every entry carries a written reason, a reason code, the confidence, the
  model version and the decision-support notice.
- Farmer availability windows and a daily cap are honoured through
  `farmer_irrigation_preferences`.
- Accept, edit, skip and complete are implemented. Completion writes a
  measured `irrigation_event` and keeps the original estimate for the
  planned-vs-actual comparison.

### Water usage analytics (`app/services/analytics.py`)

- Only **measured** events count as water used. Events without a measured
  volume are counted separately and excluded from every total.
- Predictions and schedules are never counted as consumption.
- Daily, weekly and monthly aggregations; per-field and per-crop
  breakdowns; litres per acre; average per event; irrigation frequency;
  planned against actual; estimate against actual; previous-period against
  current-period comparison.
- All day boundaries are computed in the requested timezone
  (default `Asia/Kolkata`).

### API (`/api/v1`)

New routers `irrigation`, `analytics` and `ml`:

| Method | Path |
|---|---|
| GET | `/api/v1/irrigation/predictions/{field_id}` |
| GET | `/api/v1/irrigation/predictions/{field_id}/history` |
| GET | `/api/v1/irrigation/schedule/today` |
| GET | `/api/v1/irrigation/schedule` |
| POST | `/api/v1/irrigation/schedule/{id}/accept` |
| PATCH | `/api/v1/irrigation/schedule/{id}` |
| POST | `/api/v1/irrigation/schedule/{id}/complete` |
| POST | `/api/v1/irrigation/schedule/{id}/skip` |
| POST | `/api/v1/irrigation/events` |
| GET | `/api/v1/irrigation/events` |
| GET/PUT | `/api/v1/irrigation/fields/{field_id}/settings` |
| GET/PUT | `/api/v1/irrigation/preferences` |
| GET | `/api/v1/analytics/water-usage` |
| GET | `/api/v1/analytics/water-usage/fields` |
| GET | `/api/v1/analytics/water-usage/trends` |
| GET | `/api/v1/analytics/dashboard` |
| GET | `/api/v1/analytics/schedule-preview` |
| GET | `/api/v1/ml/models/status` |
| POST | `/api/v1/ml/models/train` |

Ownership is always resolved from the authenticated profile; a
user-supplied farmer id is never trusted. Cross-account access returns
404. Validation, pagination and consistent schemas are applied.

### Frontend

- **Dashboard** rebuilt into six sections: overview metrics, today's
  irrigation schedule with actions, interactive soil moisture trends,
  water consumption charts, weather impact, crop and field insights, plus a
  panel that states which predictor produced the numbers.
- New components: `components/analytics/water-charts.tsx`,
  `irrigation-schedule-list.tsx`, `moisture-trend-panel.tsx`,
  `weather-impact-panel.tsx`, `components/fields/field-intelligence-panel.tsx`.
- **Reports** page (`/reports`) — water usage reports with core metrics,
  consumption series, comparisons and planned-vs-actual.
- **Guidance** page (`/guidance`) — today's schedule grouped into needs
  irrigation / can wait / uncertain, plus the per-field guidance list.
- **Field details** (`/fields/[id]`) — new "Field intelligence" section
  with the requirement and how it was calculated, the schedule for the
  field, water used by the field, the prediction history and the optional
  application settings.
- Translation keys added for `en`, `hi`, `kn` and `ta`.
- Fixed a pre-existing defect: the design tokens are raw `R G B` channels,
  so `fill="var(--primary)"` was invalid CSS and every chart series
  rendered black. All chart colours now use `rgb(var(--token))`.

## Data set and model status (live development database)

| Fact | Value |
|---|---|
| Supervised training samples | 78 |
| Fields contributing samples | 4 (24 / 24 / 24 / 6) |
| Time span | 6.75 days |
| Production requirement | ≥ 200 samples, ≥ 3 fields, ≥ 21 days |
| Meets the requirement | **No** |

Measured on the time-aware split:

| Model | Validation MAE | Validation RMSE | Validation R² | Test MAE | Test RMSE | Test R² |
|---|---|---|---|---|---|---|
| Random Forest (**promoted**) | 3.70 | 4.75 | 0.907 | 3.57 | 5.00 | 0.892 |
| Gradient Boosting | 4.55 | 5.58 | 0.872 | 4.41 | 5.50 | 0.869 |
| persistence baseline | 3.89 | — | — | 3.92 | — | — |
| linear trend baseline | 7.54 | — | — | 9.71 | — | — |

The Random Forest is the active predictor but every prediction is reported
as **provisional**, because the data set is below the production
requirement. Full detail: `docs/ml-model-card.md`.

## Verification executed

| Check | Result |
|---|---|
| `pytest tests/` (backend) | **70 passed** |
| `alembic upgrade head` | applied on PostgreSQL 18, additive only |
| `npx tsc --noEmit` | passed |
| `npx next lint` (new + touched files) | no warnings, no errors |
| `npm run build` | passed, 19 routes |
| Playwright dashboard / reports / guidance / field detail | no console errors, no page errors, no failed requests, no raw i18n keys, no horizontal overflow at 1440 px or 390 px |
| Playwright interactive flow | accept → record actual (2 500 L, 45 min) → the measured volume appears in the analytics as 2.5 kL, with the event and the planned-vs-actual row written to PostgreSQL |
| Playwright Hindi render | all new labels localised, no raw keys |

## Known limitations (honest)

1. **The model is provisional.** 78 samples over 6.75 days is below the
   production requirement. The improvement over the persistence baseline is
   a 5 % MAE reduction on 16 validation samples and is not evidence of a
   validated model.
2. **No irrigation history in the training data.** The irrigation features
   are missing for every training sample.
3. **Weather coverage is partial.** 39 of 78 samples have no weather
   observation in the preceding window.
4. **The agronomic parameters are reference values** (FAO-56 style), not
   locally calibrated. Every assumption is stated in the response.
5. **ET0 is only estimated** when a field has coordinates and a recorded
   temperature range; otherwise the requirement reflects the depletion
   only and the missing input is named.
6. **No application efficiency or rate is known** for the seeded fields,
   so no duration is proposed for them.
7. **The guidance and explanation text is English** in every language, the
   existing Verdant convention. Only the interface labels are translated.
8. **Water usage charts are empty** until the farmer records irrigation
   events with a measured volume. The empty state says so explicitly.

## Remaining work

- None blocking for the stated objectives. Optional follow-ups:
  - Seed a longer, more realistic reading history to move the model past
    the production requirement.
  - Add the farmer availability window and the daily cap to the Settings
    page (the API already supports both).
  - Add a CSV export of the irrigation event log to the Reports page.
