# Verdant — Smart Irrigation Platform

**Working name:** Verdant
**Product:** Smart Irrigation System for Predictive Water Management and Crop Optimization
**Primary user:** Farmers in India
**Design:** Botanical / Earth / Instrument — calm, professional, trustworthy, minimal

## Product Vision

A farmer-facing smart irrigation platform that helps farmers understand their fields, monitor soil moisture, view weather conditions, and record sensor readings.

Built for farmers, not enterprise analysts. Minimal interface, complete functionality, real backend.

## Tech Stack

**Frontend**
- Next.js 14 (App Router), TypeScript, Tailwind CSS
- Custom Verdant UI primitives (Button, Input, Label, Select, Card, Badge, Progress, Switch, Dialog, Toast)
- Lucide React icons, Recharts charts, `i18next` + `react-i18next`
- Responsive, mobile-first, PWA-ready, dark mode support
- i18n: English, Hindi, Kannada (Tamil fonts prepared)

**Backend**
- Python, FastAPI, Pydantic, SQLAlchemy, Alembic
- Supabase Auth (identity provider), JWT verification via JWKS
- PostgreSQL

**Integrations**
- OpenWeatherMap (optional, via `OPENWEATHERMAP_API_KEY`); falls back to labeled demo weather
- Architected for future Sarvam AI integration (translation + voice) — not integrated in v1

## Repository Layout

```
infosys/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── endpoints/
│   │   │           ├── auth.py        (Supabase JWT verification, /auth/me)
│   │   │           ├── fields.py
│   │   │           ├── sensors.py
│   │   │           ├── weather.py
│   │   │           └── dashboard.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── security.py          (Supabase JWT verify)
│   │   ├── crud/
│   │   │   └── __init__.py
│   │   ├── models/
│   │   │   └── base.py              (Profile, Field, Sensor, SensorReading, WeatherRecord, Alert)
│   │   ├── schemas/
│   │   │   └── __init__.py
│   │   └── main.py
│   ├── alembic/
│   │   └── versions/
│   │       ├── 0001_initial_schema.py
│   │       ├── 0002_seed_demo.py
│   │       └── 0003_supabase_auth.py
│   ├── .env
│   ├── .env.example
│   ├── requirements.txt
│   └── seed.py
├── frontend/
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── (app)/
│   │   │   ├── layout.tsx
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── fields/
│   │   │   │   ├── register/page.tsx
│   │   │   │   └── [id]/page.tsx
│   │   │   ├── sensors/page.tsx
│   │   │   ├── weather/page.tsx
│   │   │   └── settings/page.tsx
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── ui/                      (Button, Input, Label, Select, Card, Badge, Progress, Switch, Dialog, Toast, Separator, Textarea)
│   │   ├── layout/                  (sidebar, top-bar, mobile-navigation, page-container)
│   │   └── dashboard/               (moisture-chart, time-filter)
│   ├── lib/
│   │   ├── supabase/client.ts
│   │   ├── i18n.ts
│   │   ├── translations/            (en.ts, hi.ts, kn.ts)
│   │   ├── api.ts
│   │   └── utils.ts
│   ├── middleware.ts
│   ├── public/
│   │   ├── manifest.json
│   │   ├── sw.js
│   │   └── icons/
│   ├── next.config.js
│   ├── tailwind.config.js
│   └── package.json
├── docs/
│   ├── design-system.md
│   └── implementation-plan.md
└── README.md
```

## Database Schema

Tables: `profiles`, `fields`, `sensors`, `sensor_readings`, `weather_records`, `alerts`, `irrigation_events`, `irrigation_schedules`, `irrigation_predictions`, `field_irrigation_settings`, `farmer_irrigation_preferences`

- `profiles`: id (UUID), supabase_user_id (UUID), full_name, email, preferred_language, theme_preference, created_at, updated_at
- `fields`: id, user_id (UUID → profiles), field_name, farmer_name, location, village, district, state, latitude, longitude, area_acres, crop_type, soil_type, growth_stage, sowing_date, created_at, updated_at
- `sensors`: id, field_id, sensor_identifier (unique per field), sensor_type, installation_date, created_at, updated_at
- `sensor_readings`: id, field_id, sensor_id, moisture_percentage (0–100), soil_temperature, growth_stage, source, recorded_at (UTC), ingested_at (UTC), validation_status, idempotency_key
- `weather_records`: id, field_id, provider, temperature, humidity, rainfall_probability, rainfall, wind_speed, temperature_min, temperature_max, et0_mm, forecast_for, retrieved_at, created_at
- `alerts`: id, user_id, field_id, alert_type, severity, message_key, trigger_value, triggered_at, resolved_at, created_at
- `irrigation_events`: id, user_id, field_id, start_time, end_time, duration_minutes, water_volume_litres (NULL = not measured), application_method, water_source, recorded_by, notes, created_at, updated_at
- `irrigation_schedules`: id, user_id, field_id, scheduled_date, recommended_start_time, recommended_window_end, estimated_volume_litres, estimated_duration_minutes, estimated_depth_mm, priority, reason, reason_code, model_version, confidence, uncertainty_litres, status, completed_at, actual_volume_litres, actual_duration_minutes, actual_start_time, actual_end_time, prediction_id, input_snapshot, created_at, updated_at
- `irrigation_predictions`: id, user_id, field_id, predicted_at, target_time, current_moisture, predicted_moisture, moisture_trend, irrigation_requirement_mm, estimated_volume_litres, model_name, model_version, calculation_version, confidence, uncertainty, status, data_freshness, reason, input_refs, created_at
- `field_irrigation_settings`: id, field_id, application_method, application_rate_litres_per_hour, application_efficiency, water_source, notes, updated_at
- `farmer_irrigation_preferences`: id, user_id, preferred_start_time, preferred_end_time, max_daily_volume_litres, irrigation_days, notes, updated_at

Foreign keys cascade on delete (schedule → prediction uses `SET NULL`).
Indexes on `field_id`, `recorded_at`, `email`, `supabase_user_id`, and on
every ownership and time column of the irrigation tables.

The `irrigation_schedules` table has a unique constraint on
`(field_id, scheduled_date)`, which is what prevents a duplicate schedule
for the same field on the same day.

## REST API Endpoints

Base path: `/api/v1`

### Authentication (Supabase Auth is the identity provider)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/me` | Current user profile (requires valid Supabase JWT) |
| PATCH | `/auth/me` | Update profile |
| POST | `/auth/logout` | Logout |

### Fields

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/fields/` | Create a field |
| GET | `/fields/` | List authenticated user's fields |
| GET | `/fields/{id}` | Get a field (owner only) |
| PUT | `/fields/{id}` | Update a field |
| DELETE | `/fields/{id}` | Delete a field |
| GET | `/fields/{id}/sensors` | List sensors for a field |
| POST | `/fields/{id}/sensors` | Add a sensor to a field |

### Sensor Readings

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sensors/` | Submit a sensor reading (validated) |
| GET | `/sensors/` | List readings (filter by field/date, paginated) |
| GET | `/sensors/latest/{id}` | Latest reading for a field |

### Weather

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/weather/current/{id}` | Current weather for a field |
| GET | `/weather/forecast/{id}` | Five-day forecast |

### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/summary` | Totals, avg moisture, attention count, latest update |
| GET | `/dashboard/fields` | Per-field moisture summaries |
| GET | `/dashboard/alerts` | Threshold-based alerts |

### Irrigation intelligence

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/irrigation/predictions/{field_id}` | Explainable irrigation requirement for a field |
| GET | `/irrigation/predictions/{field_id}/history` | Stored prediction history |
| GET | `/irrigation/schedule/today` | Generate (or reuse) today's schedule |
| GET | `/irrigation/schedule` | List schedules (date/field/status filters) |
| POST | `/irrigation/schedule/{id}/accept` | Accept a recommendation |
| PATCH | `/irrigation/schedule/{id}` | Edit a pending recommendation |
| POST | `/irrigation/schedule/{id}/complete` | Complete it and record the measured event |
| POST | `/irrigation/schedule/{id}/skip` | Skip a recommendation |
| POST | `/irrigation/events` | Record a measured irrigation event |
| GET | `/irrigation/events` | List irrigation events (paginated) |
| GET/PUT | `/irrigation/fields/{field_id}/settings` | Optional application rate, efficiency, method, source |
| GET/PUT | `/irrigation/preferences` | Farmer availability window and daily cap |

### Water analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/water-usage` | Measured water usage with field/crop/period breakdowns |
| GET | `/analytics/water-usage/fields` | Per-field usage and litres per acre |
| GET | `/analytics/water-usage/trends` | Daily/weekly/monthly series and period comparison |
| GET | `/analytics/dashboard` | Everything the dashboard needs in one response |
| GET | `/analytics/schedule-preview` | Stored schedule rows for a range |

### Machine learning

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/ml/models/status` | Active predictor, real metrics, limitations, data requirement |
| POST | `/ml/models/train` | Train from the recorded data and report the outcome |

All field-specific endpoints enforce ownership via Supabase-verified user ID → profile.

## Environment Variables

### Backend (`backend/.env`)

```
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/irrigation
SUPABASE_URL=your-supabase-project-url
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
SUPABASE_JWT_SECRET=
OPENWEATHERMAP_API_KEY=
APP_NAME=Verdant
APP_ENV=development
```

### Frontend (`frontend/.env.local`)

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your-supabase-project-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

## How to Run

### Prerequisites
- Node.js 20+, npm
- Python 3.11+ + venv
- PostgreSQL (running on `localhost:5432`, database `irrigation`, user `postgres`/`postgres`)
- Supabase project (for authentication) — see `docs/authentication.md`

### 1. Database

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/irrigation"
export PYTHONPATH="$(pwd)"
alembic upgrade head
```

### 2. Backend

```bash
cd backend
source venv/bin/activate
export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/irrigation"
export PYTHONPATH="$(pwd)"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Backend health: `http://localhost:8000/health`
API docs: `http://localhost:8000/docs`

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:3000`

### 4. Train the irrigation model (optional)

The prediction pipeline ships with a transparent baseline that works without
a trained model. Training is optional and is repeatable:

```bash
cd backend
source venv/bin/activate
export PYTHONPATH="$(pwd)"
python -m scripts.train_irrigation_model --dry-run   # evaluate only
python -m scripts.train_irrigation_model             # train and store
```

The script prints the data set facts, the candidate comparison against the
baselines, the selection decision, the feature importance and every
recorded limitation. It stores a versioned artifact under
`backend/app/ml/artifacts/`. See `docs/ml-model-card.md`.

### 5. Tests

```bash
cd backend
source venv/bin/activate
export PYTHONPATH="$(pwd)"
pytest tests/            # 70 tests against a temporary PostgreSQL database
```

The test suite creates and drops its own `verdant_test` database, so the
development database is never touched.

```bash
cd frontend
npx tsc --noEmit         # type check
npm run lint             # lint
npm run build            # production build
```

## Demo Account

The database is seeded with a demo farmer profile. Supabase Auth handles authentication — configure your Supabase project credentials in `.env` to enable login/registration.

## Integrations Requiring API Keys

- **Supabase** — Authentication (mandatory). Configure `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`.
- **OpenWeatherMap** (`OPENWEATHERMAP_API_KEY`) — Live weather. Optional; app works in demo weather mode without it.
- **Sarvam AI** — Architected for future translation/voice integration; not connected in v1.

## Known Limitations

- Without Supabase credentials configured, auth is in development mode (accepts any JWT structure).
- Weather falls back to labeled demo data when no OpenWeatherMap key is configured.
- No real IoT/MQTT ingestion yet; sensor readings are entered manually (layer designed for future feeds).
- Predictive irrigation scheduling is a planned future phase (no ML model claims made).
- PWA icons use SVG placeholders; replace with PNG for production.
