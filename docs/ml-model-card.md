# Verdant Irrigation Model Card

**Model family:** soil-moisture horizon regression (24 h ahead)
**Owner:** Verdant ML engineering
**Last trained:** see `backend/app/ml/artifacts/soil_moisture_horizon/*/metadata.json`

---

## 1. What the model does

The model predicts the **volumetric soil moisture percentage a field will
have in 24 hours**. The irrigation *requirement* is then derived from that
prediction with the soil water balance in `app/services/agronomy.py`.

This split is deliberate. The recorded data set contains soil moisture
observations, weather observations and (from now on) irrigation events. It
does **not** contain historical irrigation *decisions*, so a model of the
"requirement" itself could only be trained on invented labels. Predicting
the observable quantity and deriving the agronomic quantity keeps every
number traceable to a measurement.

The end-to-end chain is:

```
sensor readings ─┐
weather records ─┼─► feature context ─► model / baseline ─► predicted moisture (24 h)
irrigation events┘                                                          │
                                                                            ▼
                          soil water balance (depletion + crop water use − effective rainfall)
                                                                            │
                                                                            ▼
                                       irrigation depth (mm) ─► volume (litres) ─► schedule
```

## 2. Training data

Built by `app/ml/training/dataset.py` from the live PostgreSQL database:

| Source | Used for |
|---|---|
| `sensor_readings` | target (soil moisture at +24 h) and moisture history features |
| `weather_records` | rainfall, temperature, humidity, wind, ET0 estimate |
| `irrigation_events` | hours since last irrigation, 7-day litres applied |
| `fields` | crop, soil, growth stage, area |

### Current data set (live development database)

| Fact | Value |
|---|---|
| Supervised samples | 78 |
| Fields contributing samples | 4 (field 1: 24, field 2: 24, field 3: 24, field 6: 6) |
| Fields present but too thin | 6 (fields 4, 5, 8, 9, 10) |
| Time span | 6.75 days (2026-11-09 → 2026-11-16) |
| Production requirement | ≥ 200 samples, ≥ 3 fields, ≥ 21 days |
| **Meets the production requirement** | **No** |

### Minimum data requirements for production

| Requirement | Threshold | Current |
|---|---|---|
| Training samples | 200 | 78 |
| Fields | 3 | 3 |
| Time span (days) | 21 | 6.75 |

Until all three are met, every prediction is reported as **provisional**
(`prediction.provisional = true`, `prediction.status = "provisional"`).

## 3. Features

30 numeric features plus 19 one-hot category indicators
(`app/ml/features/engineering.py`). Every feature is computed from data
**strictly earlier** than the prediction timestamp.

**Moisture** — current value, lags at 6/12/24 h, deltas at 6/12/24 h,
standard deviation, min and max over the last 24 h, reading count,
hours since the last reading.

**Weather** — latest temperature, humidity, wind speed, rainfall
probability; measured rainfall over 24 h and 72 h; forecast rainfall.

**Soil and crop** — soil temperature, crop type, soil type, growth stage,
field area, days since sowing.

**Irrigation history** — hours since the last irrigation event, litres
applied in the last 7 days.

**Temporal** — hour of day (sin/cos), day of year (sin/cos).

**Missing data** is represented as `None` and imputed with the **training
median** (`app/ml/preprocessing/imputer.py`). It is never replaced with
zero. The imputer statistics are stored inside the model artifact, so
training and inference apply exactly the same transformation.

## 4. Model strategy

### Baselines (the reference every model has to beat)

| Baseline | Description |
|---|---|
| `persistence` | the moisture reading stays as it is |
| `linear_trend` | the recent rate of change continues over the horizon |
| `field_mean` | the field's historical mean moisture |

### Candidates

| Model | Configuration |
|---|---|
| Random Forest Regressor | 300 trees, max depth 8, min samples per leaf 3 |
| Gradient Boosting Regressor | 200 stages, depth 3, learning rate 0.05 |

A deeper sequence model (LSTM) was **not** used: with 78 samples over
6.75 days there is no sequential depth to learn from, and an LSTM would be a
model chosen for sophistication rather than for the data.

### Time-aware validation

Samples are ordered by feature timestamp and split chronologically into
train → validation → test (70 / 15 / 15). Random shuffling is never used,
so a future observation can never leak into training. Fields appear in
more than one split, so the reported error also reflects generalisation
across fields within the same farm.

## 5. Evaluation results

Measured on the time-aware split of the live development data set.

### Candidate models

| Model | Validation MAE | Validation RMSE | Validation R² | Test MAE | Test RMSE | Test R² |
|---|---|---|---|---|---|---|
| Random Forest | 3.70 | 4.75 | 0.907 | 3.57 | 5.00 | 0.892 |
| Gradient Boosting | 4.55 | 5.58 | 0.872 | 4.41 | 5.50 | 0.869 |

### Baselines (same split)

| Baseline | Validation MAE | Test MAE |
|---|---|---|
| persistence | 3.89 | 3.92 |
| linear_trend | 7.54 | 9.71 |

### Selection outcome

The **Random Forest was promoted**: its validation MAE (3.70) is lower
than the persistence baseline MAE (3.89), so it is the active predictor.

It is still reported as **provisional**, because the data set does not meet
the production requirement. `GET /api/v1/ml/models/status` returns
`status: "provisional"`, `active_predictor: "soil_moisture_horizon"`,
`provisional: true`, and every prediction carries
`prediction.provisional = true` and `prediction.model_status =
"provisional"`.

The improvement over the baseline is real but small (a 5 % MAE reduction on
16 validation samples). It is not evidence of a validated model.

### Reproducibility

The training fit uses `random_state=42` and `n_jobs=1`, so repeated runs
produce bit-for-bit identical metrics. The seed is recorded in the artifact
metadata.

### Error by crop

Reported per crop in `metadata.json` under `metrics.by_group`. With 78
samples spread over three crops, each group has too few samples for the
per-crop error to be treated as a reliable estimate; it is published as a
diagnostic, not as a validated result.

## 6. Uncertainty and confidence

* The prediction interval half-width comes from the **training residuals**
  of the fitted model (1.96 × residual standard deviation).
* When the trained model is active but the data set is below the
  production requirement, the confidence is capped at 0.45 and the
  prediction is marked provisional.
* When only the baseline is available, the confidence is fixed at 0.35.
* A stale reading caps the confidence at 0.25, a missing reading at 0.20.
* Confidence is reduced to `low` when the computed refill depth exceeds
  100 mm or the reading sits below the wilting point.

## 7. Known limitations

1. **The data set is far below the production requirement.** 78 samples
   over 6.75 days cannot support a validated model.
2. **No irrigation history.** `hours_since_last_irrigation` and
   `irrigation_litres_7d` are missing for every sample, so the model has
   never seen a post-irrigation recovery.
3. **Weather coverage is partial.** 39 of 78 samples have no weather
   observation within the preceding window, so the weather features are
   imputed.
4. **The three contributing fields have very different crops** (rice,
   tomato, ragi), so the model sees a small, heterogeneous sample.
5. **The soil moisture sensor measures at one point per field.** Field
   heterogeneity (slope, texture, irrigation method) is not represented.
6. **The agronomic parameters are reference values**, not locally
   calibrated. See `app/services/agronomy.py` for the sources.
7. **The 24 h horizon is fixed.** A model for a 3-day forecast or a
   different irrigation interval would need its own training set.

## 8. Reproducing the training

```bash
cd backend
pip install -r requirements.txt
PYTHONPATH=. python -m scripts.train_irrigation_model --dry-run   # evaluate only
PYTHONPATH=. python -m scripts.train_irrigation_model             # train and store
```

The script prints the data set facts, the candidate comparison, the
selection decision, the feature importance and every recorded limitation,
then writes the artifact:

```
backend/app/ml/artifacts/soil_moisture_horizon/<version>/
├── model.pkl        # the fitted estimator
├── metadata.json    # data facts, metrics, limitations, requirements
└── imputer.json     # the training medians used for imputation
```

Training is deterministic: the seed is fixed at 42 and recorded in the
metadata.

## 9. Graceful degradation

* No artifact → the transparent baseline (recent moisture trend) is used
  and the prediction is marked provisional.
* An artifact that never beat the baseline on the validation split is
  stored for auditing but is **not** used for inference.
* No reading → no prediction is produced at all; the API returns an
  explicit "no data" outcome rather than a number.
* A stale reading → the recommendation is marked uncertain and no volume
  is proposed.
* A failing model at inference time → the exception is caught, the
  limitation is recorded and the baseline takes over.

## 10. What would make this model production ready

1. Keep every field on a regular reading cadence for at least 21 days.
2. Reach 200 supervised samples across at least 3 fields.
3. Record irrigation events with a measured volume, so the irrigation
   history features carry real signal.
4. Configure a weather provider for every field so the weather features
   are observed rather than imputed.
5. Re-run the training script and confirm that the selected model beats
   the persistence baseline on the validation split **and** that the
   production requirement is met.
