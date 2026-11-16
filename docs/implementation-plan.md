# Verdant Implementation Plan

**Source of truth:** `docs/design-system.md` + `VERDANT — MASTER PRODUCT DESIGN & IMPLEMENTATION CONTRACT`

## Execution rule (non-negotiable)

1. Inspect repository → create docs/design-system.md → create docs/implementation-plan.md.
2. Implement design system + application shell. Verify visual result before proceeding with all pages.
3. Implement per phased order. Do not attempt entire application in one pass.
4. Maintain a checklist of completed requirements; test each major workflow.

---

## Phase 1 — Repository inspection (complete)

- Existing custom-auth FastAPI + Next.js app inspected.
- Must be adapted to: botanical design tokens, Supabase Auth (mandatory), new routes, PWA, dark mode, responsive, i18n en/hi/kn.
- Database: PostgreSQL running in Docker (`infosys-postgres` on port 5432).

---

## Phase 2 — Design system

Tasks:
- [ ] Rewrite `frontend/app/globals.css` with Verdant light/dark CSS variables.
- [ ] Update `frontend/tailwind.config.js` with Verdant colour palette, spacing, radius, fonts.
- [ ] Load fonts: Manrope/Inter (en), Noto Sans Devanagari (hi), Noto Sans Kannada (kn), Noto Sans Tamil (prepared).
- [ ] Build UI primitives: Button, Input, Label, Select, Card, Separator, Textarea, Badge, Progress, Checkbox, Switch, Dialog, Toast.
- [ ] Build layout: AppSidebar (248px / 76px collapsed), MobileNavigation (bottom bar + More sheet), TopBar, PageContainer.
- [ ] Build data presentation: MetricDisplay, FieldCard, MoistureIndicator, StatusLabel, SensorFreshnessIndicator, WeatherSummary, AlertItem, ActivityTimeline.
- [ ] Build data entry: FormSection, FormField, FieldSelector, SensorSelector, DateTimeInput, ValidationMessage, SubmitButton.
- [ ] Build tables: DataTable, TableToolbar, TablePagination, ExportAction.
- [ ] Build visualization: MoistureHistoryChart, ForecastSummary.
- [ ] Build feedback: EmptyState, ErrorState, LoadingState, ConfirmationDialog.
- [ ] Verify visual result (light + dark + mobile + desktop) before Phase 3.

---

## Phase 3 — Backend foundation (Supabase Auth)

Tasks:
- [ ] Update `requirements.txt`: add `supabase-py`, `python-jose[cryptography]`, `httpx`, `bcrypt`; keep FastAPI/SQLAlchemy/Alembic.
- [ ] Add `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` to `.env.example`.
- [ ] SQLAlchemy models: `profiles` (id UUID references auth.users.id, full_name, email, preferred_language, theme_preference, created_at, updated_at); `fields`, `sensors`, `sensor_readings` (add `source`, `idempotency_key`, `validation_status`), `weather_records`, `alerts`.
- [ ] Alembic migrations: profiles table + add source/idempotency/validation_status to readings + alerts table + update existing tables.
- [ ] Security: `verify_supabase_jwt(token)` — verify signature via Supabase JWKS, validate iss/exp/aud, extract `sub` (Supabase user ID).
- [ ] Auth dependency: `get_current_user` — resolve Supabase user ID → profile row → enforce ownership.
- [ ] Remove custom password hashing/login (Supabase Auth is the identity provider).
- [ ] Centralized error handling: 401 / 403 / 404 / 422 / 500 schemas.
- [ ] OpenAPI docs at `/docs`.

---

## Phase 4 — Core application (in exact order)

1. [ ] Login (`/login`) — Verdant branding, email/password, show/hide, forgot password, Google sign-in, registration link, loading/validation/error states.
2. [ ] Registration (`/register`) — full name, email, password, confirm password, Google option, terms/privacy, email verification.
3. [ ] Forgot password (`/forgot-password`) and Reset password (`/reset-password`).
4. [ ] Dashboard shell (`/dashboard`) — greeting, farm overview metrics, field conditions, weather summary, alerts, recent activity, empty state.
5. [ ] Field registration (`/fields/new`) — field identification, agricultural info, sensor configuration.
6. [ ] Field directory (`/fields`) — search, filters, grid/list toggle, field cards, list view, actions (view/edit/delete + confirmation).
7. [ ] Field details (`/fields/[id]`) — field identity, current conditions, moisture history chart, sensor history, weather, activity.
8. [ ] Field edit (`/fields/[id]/edit`).
9. [ ] Sensor data ingestion (`/readings`) — record reading form + reading history table + filters + CSV export.
10. [ ] Weather (`/weather`) — location selection, current weather, 5-day forecast, API handling, honest fallback.
11. [ ] Alerts — low/high moisture, stale sensor, missing reading, expected rainfall; resolve action.
12. [ ] Settings (`/settings`) — profile, language, appearance, units, regional, notifications, account/password, logout.

---

## Phase 5 — Polish

Tasks:
- [ ] Complete translations (en/hi/kn) for every interface element.
- [ ] Dark mode on all pages/components.
- [ ] PWA: manifest, icons, service worker, offline indicator, cached data freshness labelling.
- [ ] Responsive refinements (mobile/tablet/desktop/wide).
- [ ] Accessibility: focus rings, contrast, keyboard nav, screen-reader labels, safe areas.
- [ ] Loading, empty, error states everywhere.
- [ ] Structured validation errors.
- [ ] No placeholder buttons; no fake AI recommendations; no fabricated live measurements.

---

## Phase 6 — Testing

Workflows (all must pass):
- [ ] Workflow A — New farmer: register → login → dashboard empty state → register first field → field details.
- [ ] Workflow B — Sensor reading: select field → confirm sensor → enter moisture/temp → submit → backend validation → PostgreSQL persistence → dashboard update → field history.
- [ ] Workflow C — Multilingual: en → hi → kn → navigate → forms → validation messages → reload → persistence.
- [ ] Workflow D — Auth & isolation: two accounts → cross-account access rejected → logout invalidates session.
- [ ] Workflow E — Responsive: mobile/tablet/desktop/wide → no overflow, nav works, forms usable, charts resize, tables adapt, no clipping.
- [ ] Workflow F — Dark mode: all pages → readable text, functional colours, focus indicators, charts.
- [ ] Workflow G — PWA: manifest, install, offline indicator, cached assets, freshness labelling.

Run:
- [ ] Backend tests.
- [ ] Frontend lint.
- [ ] TypeScript type check.
- [ ] Production build (`next build`).
- [ ] Database migration tests.

---

## Phase 7 — Documentation

Create:
- [ ] `README.md` — installation, env vars, database setup, migrations, seed, frontend/backend run instructions.
- [ ] `docs/architecture.md`
- [ ] `docs/api.md`
- [ ] `docs/design-system.md` (done)
- [ ] `docs/data-dictionary.md`
- [ ] `docs/authentication.md` — Supabase setup, Google OAuth, JWT verification in FastAPI, security, troubleshooting.
- [ ] Known limitations.

---

## Acceptance checklist (Definition of Done)

- [ ] Design system implemented (colour, typography, spacing, radius, shadows, breakpoints).
- [ ] Application matches botanical visual identity.
- [ ] All specified pages exist.
- [ ] All navigation works (desktop sidebar + mobile bottom nav).
- [ ] Supabase Auth works (email/password, Google OAuth, password reset, session persistence, logout).
- [ ] Field registration works.
- [ ] Sensor ingestion works (manual form + REST endpoint).
- [ ] PostgreSQL stores real records.
- [ ] Historical readings retrievable.
- [ ] Weather integration works when configured; honest fallback when not.
- [ ] en/hi/kn work; Tamil fonts prepared.
- [ ] Light/dark modes work.
- [ ] Responsive.
- [ ] PWA installable.
- [ ] Data ownership enforced (cross-account rejected).
- [ ] Tests pass.
- [ ] Documentation exists.

---

## Routes

| Route | Page |
|-------|------|
| `/login` | Login |
| `/register` | Registration |
| `/forgot-password` | Forgot password |
| `/reset-password` | Reset password |
| `/dashboard` | Overview / Dashboard |
| `/fields` | My Fields |
| `/fields/new` | Register Field |
| `/fields/[id]` | Field Details |
| `/fields/[id]/edit` | Edit Field |
| `/readings` | Sensor Readings |
| `/weather` | Weather |
| `/settings` | Settings |

## Backend API (`/api/v1`)

Auth: `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`
Fields: `GET /fields`, `POST /fields`, `GET /fields/{id}`, `PATCH /fields/{id}`, `DELETE /fields/{id}`
Sensors: `GET /sensors`, `GET /sensors/{id}`, `POST /sensors`
Readings: `POST /readings`, `GET /readings`, `GET /readings/{id}`, `GET /fields/{id}/readings`, `GET /fields/{id}/readings/latest`
Dashboard: `GET /dashboard/summary`, `GET /dashboard/fields`, `GET /dashboard/alerts`, `GET /dashboard/activity`
Weather: `GET /weather/current`, `GET /weather/forecast`
Alerts: `GET /alerts`, `PATCH /alerts/{id}/resolve`

All field-specific endpoints enforce ownership via Supabase-verified user ID → profile.
