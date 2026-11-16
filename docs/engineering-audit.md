# VERDANT — Engineering Audit and Architecture Review

**Repository:** `/home/r1phun73r/Documents/College-year-3/internship/infosys`
**Product:** Verdant — Smart Irrigation Management Platform
**Audit type:** Architecture, security, and code review (audit-only; no changes made)
**Status:** Complete

---

## 1. Executive summary

Verdant is a farmer-facing smart irrigation platform with a Next.js 14 App Router frontend and a FastAPI/SQLAlchemy/Alembic backend backed by PostgreSQL and Supabase Auth. The application implements the core domain (fields, sensors, soil-moisture readings, weather, dashboard, alerts) and enforces ownership at the application layer via Supabase-verified JWTs.

Overall impression: the codebase is coherent, follows a clean layered structure (routers → CRUD → models → schemas), validates input with Pydantic, and ties Supabase Auth into every data endpoint. The domain model matches the README and the alerts/weather/dashboard features are implemented rather than stubbed.

However, the audit identified a **confirmed P0 secret exposure** (real Supabase and OpenWeatherMap credentials committed in `backend/.env` with no `.gitignore`), several **P1 authentication/authorization reliability gaps** (new users can be locked out because profile creation is not guaranteed; CORS is misconfigured with `allow_origins=["*"]` + `allow_credentials=True`; no database Row Level Security), and a **complete absence of automated tests**. Notable architectural risks include N+1 queries in dashboard/alerts, duplicated moisture-threshold business rules between backend and frontend, and async endpoints blocking the event loop with synchronous SQLAlchemy.

No fixes were implemented during this audit, per the operating rules.

---

## 2. Actual technology stack and dependency versions

Verified against installed package metadata in `backend/venv/lib/python3.14/site-packages` and `frontend/package.json`.

### Backend (`backend/`)
| Component | Version (installed) | Source |
|---|---|---|
| Python | 3.14 (venv) | `venv` |
| FastAPI | 0.115.0 | `requirements.txt` + dist-info |
| Uvicorn | 0.32.1 | `requirements.txt` + dist-info |
| Starlette | 0.38.6 | transitive (dist-info) |
| Pydantic | 2.14.3 | `requirements.txt` + dist-info |
| pydantic-settings | 2.15.0 | `requirements.txt` (`>=2.4,<3.0`) + dist-info |
| SQLAlchemy | 2.1.8 | `requirements.txt` + dist-info |
| Alembic | 1.20.1 | `requirements.txt` + dist-info |
| psycopg2-binary | 2.9.13 | `requirements.txt` + dist-info |
| python-jose[cryptography] | 3.3.0 | `requirements.txt` + dist-info |
| httpx | 0.28.0 | `requirements.txt` + dist-info |
| python-multipart | 0.0.9 | `requirements.txt` + dist-info |
| python-dotenv | 1.0.1 | `requirements.txt` + dist-info |
| python-dateutil | 2.9.0.post0 | `requirements.txt` + dist-info |
| bcrypt | 4.2.0 | `requirements.txt` (declared, unused in code) |

### Frontend (`frontend/`)
| Component | Version | Source |
|---|---|---|
| Next.js | 14.2.15 | `package.json` |
| React | ^18.3.1 | `package.json` |
| TypeScript | ^5 | `package.json` (dev) |
| Tailwind CSS | ^3.4.11 | `package.json` (dev) |
| @supabase/ssr | ^0.12.7 | `package.json` |
| @supabase/supabase-js | ^2.119.0 | `package.json` |
| i18next / react-i18next | ^23.15.1 / ^14.1.2 | `package.json` |
| recharts | ^2.12.7 | `package.json` |
| lucide-react | ^0.454.0 | `package.json` |
| eslint | ^8 | `package.json` (dev) |

### Infrastructure
- PostgreSQL database: `irrigation` (localhost:5432 per README)
- Identity provider: Supabase Auth (JWKS-based RS256 verification in backend)
- Optional: OpenWeatherMap API (demo fallback when key absent)
- Migrations: Alembic, 3 revisions (`0001`, `0002`, `0003`)

### Local agent skills present (guidance only, not applied)
- `.opencode/skills/fastapi-alembic-migrations`
- `.opencode/skills/fastapi-testing`
- `frontend/.agents/skills/fastapi`, `frontend/.agents/skills/supabase`, `frontend/.agents/skills/supabase-postgres-best-practices`, `frontend/.agents/skills/playwright`

---

## 3. Current architecture overview

### Backend (`backend/app/`)
```
main.py                          # FastAPI app, CORS, /health, mounts /api/v1
  core/
    config.py                    # pydantic-settings Settings (loads backend/.env)
    database.py                  # sync create_engine, sessionmaker, get_db() generator
    security.py                  # Supabase JWKS fetch + RS256 JWT verify (iss/aud/exp)
  api/
    deps.py                      # get_db(), get_current_user() (JWT -> profile)
    v1/
      api.py                     # mounts auth/fields/sensors/weather/dashboard routers
      endpoints/
        auth.py                  # GET/PATCH /auth/me, POST /auth/profile, POST /auth/logout
        fields.py                # CRUD for fields + sensors (owner-scoped)
        sensors.py               # POST/GET readings, latest reading
        weather.py               # current + 5-day forecast (OpenWeatherMap or demo)
        dashboard.py             # summary, per-field moisture, alerts, latest sensor
  models/
    base.py                      # Profile, Field, Sensor, SensorReading, WeatherRecord, Alert
  schemas/
    __init__.py                  # Pydantic v2 request/response schemas
  crud/
    __init__.py                  # SQLAlchemy 1.x-style query API + domain helpers
```

- **Auth model:** Supabase is the identity provider. The frontend signs users in/up client-side (`signInWithPassword`, `signUp`, `signInWithOAuth`), then sends the Supabase access token as `Authorization: Bearer <token>`. The backend verifies the RS256 signature against Supabase JWKS (`security.py:verify_supabase_jwt`), validates `iss`, `aud`, `exp`, extracts `sub`, resolves it to a `profiles` row, and enforces `user_id` ownership on every field/reading/weather endpoint.
- **Session:** stateless JWT; `/auth/logout` is a no-op (client discards token).
- **Database access:** synchronous SQLAlchemy `Session` per request via `Depends(get_db)`; no async session, no explicit transaction blocks (rely on autocommit=False default commit per CRUD call).
- **Migrations:** Alembic with `target_metadata = Base.metadata`; `compare_type=True`; `sqlalchemy.url` overridden from `settings.DATABASE_URL`. Three revisions; `0002` seeds demo data inside a migration; `0003` adds the `alerts` table, an idempotency-key index, and a late FK from `fields.user_id` to `profiles`.

### Frontend (`frontend/app/`)
```
layout.tsx                       # root: I18nProvider + SessionProvider + SW registration
middleware.ts                    # Next.js middleware: Supabase server client, route guards
  (auth)/                        # login, register, forgot-password, reset-password, callback(route)
  (app)/                         # dashboard, fields, fields/[id], sensors, weather, settings
components/
  ui/                            # custom primitives (Button, Input, Label, Select, Card, ...)
  layout/                        # sidebar, top-bar, mobile-nav, page-container, protected-layout
  auth/session-provider.tsx      # ensures profile exists on init / SIGNED_IN
  dashboard/moisture-chart.tsx   # Recharts line chart
lib/
  api.ts                         # fetch wrapper attaching Supabase access token
  supabase/client.ts             # browser Supabase client (no-op if env missing)
  i18n.ts + translations/        # i18next: en, hi, kn
```

- **Route protection:** `middleware.ts` checks `supabase.auth.getUser()` on every request; unauthenticated users are redirected to `/auth/login`; authenticated users are redirected away from `/auth/*`. `protected-layout.tsx` exists but appears unused by current routes.
- **API client:** `lib/api.ts` attaches `Authorization: Bearer <access_token>` and `Accept-Language` from i18n; throws on non-OK with `err.status` and `err.body`.
- **PWA:** `public/manifest.json` (standalone, SVG icons), `public/sw.js` (precache shell), registered in `layout.tsx`.
- **i18n:** en/hi/kn, persisted in `localStorage`, `fallbackLng: "en"`.
- **Moisture thresholds:** duplicated in `frontend/lib/utils.ts` (`moistureConditionLabel`: <30 low, <45 moderate, <=75 healthy, else high) and mirrored in backend `crud.moisture_condition`.

### Mermaid architecture diagram (supported by actual implementation)

```mermaid
flowchart TD
    subgraph Browser["Browser (Next.js 14 App Router)"]
        UI[UI components / pages]
        APIClient[lib/api.ts - fetch + Bearer token]
        SBClient[Supabase browser client @supabase/ssr]
        Middleware[Next.js middleware - session guard]
        SW[Service worker / manifest - PWA]
    end

    subgraph Supabase["Supabase (Identity Provider)"]
        Auth[auth.signInWithPassword / signUp / signInWithOAuth]
        JWKS[.well-known/jwks.json - RS256 public keys]
    end

    subgraph Backend["Backend (FastAPI 0.115.0)"]
        CORS[CORS middleware]
        Router[APIRouter /api/v1]
        Deps[get_current_user - JWT verify + profile resolve]
        AuthE[auth endpoints: /me, /profile, /logout]
        FieldsE[fields endpoints]
        SensorsE[sensors/readings endpoints]
        WeatherE[weather endpoints]
        DashE[dashboard endpoints]
        CRUD[crud/__init__.py - SQLAlchemy Session]
        Models[models/base.py - SQLAlchemy models]
    end

    subgraph DB[(PostgreSQL - irrigation)]
        P[profiles]
        F[fields]
        S[sensors]
        R[sensor_readings]
        W[weather_records]
        A[alerts]
    end

    subgraph Ext["External services"]
        OWM[OpenWeatherMap API - optional]
    end

    UI <-> APIClient
    APIClient -->|Authorization: Bearer JWT| CORS
    CORS --> Router
    Router --> Deps
    Deps -.->|verify signature, iss, aud, exp| JWKS
    Deps --> Models
    Router --> AuthE & FieldsE & SensorsE & WeatherE & DashE
    AuthE & FieldsE & SensorsE & WeatherE & DashE --> CRUD
    CRUD --> Models
    Models --> DB
    WeatherE -.->|HTTP| OWM
    SBClient <-> Auth
    Middleware -.->|getUser| SBClient
```

Note: the diagram reflects actual code paths. RLS policies are **not** present in the database (see finding DB-03), so enforcement is application-layer only.

---

## 4. Backend findings

### BE-01 — P0 — Committed secrets in `backend/.env`
- **Location:** `backend/.env` (also mirrored in `README.md` documentation listing)
- **Evidence:** The file contains real, non-placeholder values for `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, and `OPENWEATHERMAP_API_KEY`. There is no project-level `.gitignore` to exclude `.env`.
- **Problem:** If this tree is copied, archived, or pushed to a remote, the Supabase service-role key and JWT secret are exposed. The service-role key bypasses RLS and can alter any data; the JWT secret could be used to forge tokens (though the backend verifies via JWKS, not the secret, the secret is still a Supabase platform secret).
- **Correction:** Remove `.env` from the repository, add `.env` to `.gitignore`, rotate all exposed credentials, and inject secrets via environment / secret manager at runtime. Replace `backend/.env` values with placeholders only.
- **Risks:** Rotating the Supabase keys requires updating the Supabase project configuration and any deployed frontend/backend env. Frontend `NEXT_PUBLIC_*` values are intended to be public (anon key), but the service-role key and JWT secret must never be committed.
- **Verification:** Confirm `backend/.env` no longer contains real values; confirm `.gitignore` excludes `.env`; confirm `git status`/`find` shows no other `.env` files with real secrets.

### BE-02 — P1 — New authenticated users can be locked out of all data endpoints
- **Location:** `backend/app/api/deps.py:22-56` (`get_current_user`); `backend/app/api/v1/endpoints/auth.py:37-75` (`ensure_profile`); `frontend/components/auth/session-provider.tsx:21-28`
- **Evidence:** `get_current_user` raises HTTP 401 "Profile not found for authenticated user" when no `profiles` row exists for the Supabase `sub`. Profiles are only created via `POST /auth/profile` (`ensure_profile`), which the frontend calls opportunistically in `SessionProvider` and **swallows all errors** (`catch {}`). If registration does not auto-sign-in, or `/auth/profile` fails, the user has a valid Supabase session but receives 401 on every data endpoint indefinitely.
- **Problem:** A valid user cannot access fields/readings/dashboard until a profile row is created, and failures in profile creation are silently ignored. This breaks the "register → dashboard" workflow.
- **Correction:** Make profile creation guaranteed and explicit: on `SIGNED_IN`, ensure a profile exists (create from verified JWT claims if missing), return an error to the UI if it fails instead of swallowing it, and consider auto-creating the profile via a database trigger or Supabase auth hook on user creation.
- **Risks:** Changing auth flow affects login/register UX; must ensure existing users with profiles are unaffected.
- **Verification:** Register a new user via Supabase, do not call `/auth/profile`, then call `GET /api/v1/fields/` — expect 401 today; after fix, expect success. Check that `ensure_profile` errors surface to the UI.

### BE-03 — P1 — CORS misconfiguration (`allow_origins=["*"]` with `allow_credentials=True`)
- **Location:** `backend/app/main.py:9-15`
- **Evidence:** `CORSMiddleware` is configured with `allow_origins=["*"]` and `allow_credentials=True`. With `*` and credentials, browsers will not send cookies/Authorization headers cross-origin (the combination is invalid per the fetch spec), so the setting is either ineffective or insecure depending on client behavior.
- **Problem:** Either cross-origin authenticated requests from the frontend fail (credentials not sent), or the API is open to any origin. The frontend runs on `localhost:3000`; the backend on `localhost:8000`, so a specific origin should be listed.
- **Correction:** Set `allow_origins` to the explicit frontend origin(s) (e.g. `https://<frontend>`, `http://localhost:3000`) with `allow_credentials=True`, or drop credentials if not needed. Use environment variable `CORS_ORIGINS`.
- **Risks:** Changing CORS may break local development if origin list is incomplete.
- **Verification:** Attempt a cross-origin `fetch` with `Authorization` header and `credentials: "include"` from `http://localhost:3000` to `http://localhost:8000`; confirm the response echoes the specific origin and allows credentials.

### BE-04 — P2 — No global exception handler / inconsistent error responses
- **Location:** `backend/app/main.py` (no exception handlers); endpoints raise ad-hoc `HTTPException`
- **Evidence:** `main.py` only adds CORS and includes the router. Unhandled exceptions (e.g. SQLAlchemy `IntegrityError` on duplicate `idempotency_key`, database connection failure) propagate as FastAPI/Starlette default 500 responses, potentially exposing internal detail. Error bodies are not standardized (some endpoints return `{"error": ...}` with HTTP 200 — see BE-08).
- **Problem:** Clients cannot rely on a consistent error schema; 500s may leak stack traces or SQL detail in production.
- **Correction:** Add `@app.exception_handler` for `RequestValidationError` (422), `SQLAlchemyError` (500), and a generic 500 handler returning a standardized `{detail, code, status}` JSON body; ensure no exception detail is returned in `APP_ENV=production`.
- **Risks:** Must not change existing 401/404/400 status codes that clients depend on.
- **Verification:** Trigger a duplicate `idempotency_key` submission and confirm a consistent JSON error instead of a raw 500/HTML.

### BE-05 — P2 — No rate limiting
- **Location:** `backend/app/main.py`; no rate-limit middleware or dependency
- **Evidence:** No middleware or dependency limits request frequency on `/auth/*`, `/sensors/`, or any endpoint.
- **Problem:** Unauthenticated/authed clients can brute-force or flood reading submission, weather fetches (OpenWeatherMap calls), and login-adjacent flows.
- **Correction:** Add rate limiting (e.g. `slowapi` or a Redis-backed middleware) keyed by IP/user for auth and write endpoints; add OpenWeatherMap call throttling.
- **Risks:** Introducing a new dependency and state store; verify compatibility with FastAPI 0.115.0 / Starlette 0.38.6.
- **Verification:** Send repeated requests to a single endpoint and confirm 429 responses after the threshold.

---

## 5. Frontend findings

### FE-01 — P2 — `SessionProvider` swallows profile-creation errors
- **Location:** `frontend/components/auth/session-provider.tsx:24-28`
- **Evidence:** `ensureProfile()` calls `api.post("/api/v1/auth/profile")` inside an empty `catch {}`. Any failure (network, 401, 500) is silent; the user sees no error and subsequent API calls fail with 401.
- **Correction:** Surface profile-creation errors to the user (toast/error state) and retry; do not swallow.
- **Verification:** Block the backend `/auth/profile` endpoint and observe login behavior; confirm an error is shown instead of a silent failure.

### FE-02 — P2 — Duplicated moisture-threshold business rule (backend vs frontend)
- **Location:** `frontend/lib/utils.ts:48-57` (`moistureConditionLabel`) and `backend/app/crud/__init__.py:160-169` (`moisture_condition`)
- **Evidence:** Both define identical thresholds (<30 low, <45 moderate, <=75 healthy, >75 high). The design-system doc labels them "configurable, not hardcoded," but they are hardcoded in two codebases with no shared source of truth.
- **Correction:** Centralize thresholds (e.g. backend config + exposed via dashboard metadata, or a shared constant), and keep frontend in sync with the backend's interpretation.
- **Risks:** Changing thresholds requires coordinated frontend/backend release.
- **Verification:** Compare `moisture_condition` output and `moistureConditionLabel` output across boundary values 29/30/44/45/75/76.

### FE-03 — P2 — Field detail page mutates nothing but buttons are non-functional placeholders
- **Location:** `frontend/app/fields/[id]/page.tsx:88-89`
- **Evidence:** Edit and Delete buttons have `onClick={() => {}}`; no edit field route (`/fields/[id]/edit`) exists despite being in `implementation-plan.md`.
- **Correction:** Wire up edit/delete or remove the buttons; add the edit route if intended.
- **Verification:** Click Edit/Delete on a field detail page; confirm no action occurs today.

### FE-04 — P2 — Settings form submits fields not part of the backend update contract
- **Location:** `frontend/app/settings/page.tsx:44-48`
- **Evidence:** The form sends `email` in the PATCH body, but `ProfileUpdate` schema (`backend/app/schemas/__init__.py:22-25`) only allows `full_name`, `preferred_language`, `theme_preference`. Pydantic will ignore extra fields by default but this is a contract mismatch; the email shown cannot be changed via this endpoint (email is tied to Supabase).
- **Correction:** Remove `email` from the submit payload or mark it read-only; update backend if email changes should be supported via Supabase.
- **Verification:** Submit the settings form with a changed email and confirm the backend ignores/rejects it appropriately.

### FE-05 — P3 — PWA icons are SVG placeholders
- **Location:** `frontend/public/icons/icon-192.svg`, `icon-512.svg`; `manifest.json` declares `image/svg+xml`
- **Evidence:** README "Known Limitations" states icons are SVG placeholders and should be PNG for production; some OS app stores/install prompts require PNG.
- **Correction:** Replace SVG icons with PNG assets and update manifest `type`.
- **Verification:** Check manifest renders icons; test "Add to Home Screen" on a device.

### FE-06 — P3 — No TypeScript strictness / `any` usage in pages
- **Location:** `frontend/app/fields/[id]/page.tsx:20-21` (`useState<any>`, `readings: any[]`), `dashboard/page.tsx` interfaces duplicated locally
- **Evidence:** `any` types and locally duplicated API response interfaces drift from backend schemas.
- **Correction:** Enable `strict` in `tsconfig.json`, replace `any` with generated/shared types, derive frontend interfaces from backend schemas.
- **Verification:** Run `tsc --noEmit` / `next lint` and type-check.

---

## 6. Authentication and security findings

### AU-01 — P0 — Committed service-role key and JWT secret
- See **BE-01**. `backend/.env` holds `SUPABASE_SERVICE_ROLE_KEY` and `SUPABASE_JWT_SECRET` with real values. No `.gitignore`. (Values intentionally not reproduced in this report.)

### AU-02 — P1 — No database Row Level Security (RLS)
- **Location:** `backend/alembic/versions/0001_initial_schema.py`, `0003_supabase_auth.py`; database `irrigation`
- **Evidence:** No `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` and no `CREATE POLICY` statements in any migration. All isolation is enforced in application code (`Field.user_id == current_user.id`, etc.).
- **Problem:** If the application layer is bypassed (direct DB access, service-role key, future read replicas), any user can read/write any row. Defense-in-depth is absent.
- **Correction:** Enable RLS on `profiles`, `fields`, `sensors`, `sensor_readings`, `weather_records`, `alerts` and add policies keyed to `auth.uid()` (Supabase) or the application's `supabase_user_id` mapping. Keep application-layer checks as the primary enforcement.
- **Risks:** RLS policies must reference the Supabase `auth.uid()`; since `profiles.supabase_user_id` maps to `auth.users.id`, policies can join on that. Misconfigured policies could lock out legitimate users. Test in a non-production database first.
- **Verification:** Connect as a non-service DB user and attempt `SELECT * FROM fields` belonging to another user; expect RLS to reject.

### AU-03 — P1 — CORS allows all origins with credentials
- See **BE-03**.

### AU-04 — P2 — `verify_supabase_jwt` swallows all exceptions and returns `None`
- **Location:** `backend/app/core/security.py:51-79`
- **Evidence:** The entire `try` block catches `Exception` and returns `None`, so expired, malformed, revoked, and wrong-issuer tokens are indistinguishable; no logging/audit of failed verification.
- **Correction:** Distinguish `ExpiredSignatureError`, `JWTClaimsError`, `JWTError`; log failures (without logging the token); return distinct failure reasons where useful.
- **Verification:** Present an expired token and a tampered token; confirm 401 with appropriate detail (not a generic failure).

### AU-05 — P2 — `/auth/logout` is a client-side no-op
- **Location:** `backend/app/api/v1/endpoints/auth.py:78-81`
- **Evidence:** `logout()` returns `{"detail": "Logged out"}` without invalidating anything (stateless JWT cannot be server-side revoked).
- **Problem:** A stolen access token remains valid until expiry; there is no server-side revocation or token blacklist.
- **Correction:** Document that logout is client-side; consider short access-token lifetimes and/or a token-revocation store if higher assurance is needed.
- **Risks:** Adding revocation requires state (Redis/DB) and lookup on every request.

### AU-06 — P2 — `SUPABASE_JWT_SECRET` configured but unused
- **Location:** `backend/app/core/config.py:9`; `backend/app/core/security.py` uses JWKS
- **Evidence:** `SUPABASE_JWT_SECRET` is loaded but `verify_supabase_jwt` verifies RS256 via JWKS, not the HS256 secret. Presence of the secret suggests uncertainty about the signing algorithm.
- **Correction:** Confirm Supabase RS256 JWKS is the intended mechanism (it is), remove or clearly document that `SUPABASE_JWT_SECRET` is unused, and ensure it never leaks.
- **Verification:** Confirm tokens verify via JWKS and that removing `SUPABASE_JWT_SECRET` does not break auth (it is not referenced in security.py).

### AU-07 — P3 — No security headers / HTTPS enforcement
- **Location:** `backend/app/main.py`
- **Evidence:** No `Strict-Transport-Security`, `X-Content-Type-Options`, `Referrer-Policy`, or `TrustedHostMiddleware`.
- **Correction:** Add security headers middleware and `TrustedHostMiddleware` for allowed hosts.
- **Risks:** Minor; defense-in-depth only.

---

## 7. Database and migration findings

### DB-01 — P2 — Contradictory uniqueness on `sensors.sensor_identifier`
- **Location:** `backend/alembic/versions/0001_initial_schema.py:76` and `:74-76`
- **Evidence:** There is both a global unique index `ix_sensors_sensor_identifier` on `sensor_identifier` alone AND a composite unique constraint `uq_field_sensor_identifier` on `(field_id, sensor_identifier)`. The README says "sensor_identifier (unique per field)," but the global index makes it unique across the entire table, preventing two fields from reusing the same identifier (e.g. "SENSOR-001").
- **Problem:** Schema contradicts the stated business rule; legitimate sensor registrations will fail with a unique-violation.
- **Correction:** Drop the global unique index on `sensor_identifier` and keep only the composite `(field_id, sensor_identifier)` constraint. Add a non-unique index on `sensor_identifier` if lookups by identifier alone are needed.
- **Risks:** Migration must drop/recreate indexes; existing data must not violate the composite constraint.
- **Verification:** Attempt to insert the same `sensor_identifier` on two different fields; should succeed after fix, fail today.

### DB-02 — P2 — N+1 queries in dashboard and alerts
- **Location:** `backend/app/crud/__init__.py:172-197` (`get_dashboard_summary`), `:200-216` (`get_field_moisture_summaries`), `:219-259` (`get_alerts`)
- **Evidence:** Each function loads all fields for the user, then calls `get_latest_reading_for_field(db, f.id)` once per field — one query per field. With N fields, that is N+1 queries.
- **Problem:** Dashboard/alerts response time grows linearly with field count; will be slow for farmers with many fields.
- **Correction:** Replace the per-field loop with a single aggregated query (e.g. `DISTINCT ON (field_id)` over `sensor_readings` ordered by `recorded_at DESC`, joined to `fields`).
- **Risks:** Must preserve `moisture_condition`, stale threshold (48h), and alert semantics exactly.
- **Verification:** Enable SQL logging (`echo=True`) and count queries issued for a user with 5+ fields; expect O(1), not O(N).

### DB-03 — P1 — No RLS policies
- See **AU-02**.

### DB-04 — P2 — `alerts` table is unused; alerts computed in-memory
- **Location:** `backend/app/api/v1/endpoints/dashboard.py:38-43`; `backend/app/crud/__init__.py:219-259` (`get_alerts`)
- **Evidence:** The `alerts` table (created in migration `0003`) has columns `message_key`, `trigger_value`, `resolved_at`, but `get_alerts` never inserts, updates, or queries it. Alerts are derived on the fly from the latest reading, and `message` is a hardcoded string, not `message_key`.
- **Problem:** Alerts are not persistent, not resolvable, and not storable; the `alerts` table is dead schema. No "resolve alert" action exists (planned in implementation-plan.md but not implemented).
- **Correction:** Either persist computed alerts to the `alerts` table with `triggered_at`/`resolved_at` and add a resolve endpoint, or remove the table. Align `message_key` usage with the schema.
- **Risks:** Changing alert persistence affects dashboard behavior and any alert history expectations.
- **Verification:** Call `GET /api/v1/dashboard/alerts`, then confirm no rows are written to `alerts` (table remains empty).

### DB-05 — P2 — `SensorReadingOut.growth_stage` required but DB column nullable
- **Location:** `backend/app/schemas/__init__.py:114-127` (`SensorReadingOut.growth_stage: str`); `backend/app/models/base.py:91` (`growth_stage = Column(String, nullable=True)`)
- **Evidence:** Pydantic marks `growth_stage` as required `str`, but the SQLAlchemy column allows `NULL`. A reading with a null `growth_stage` will fail Pydantic serialization with a validation error (500).
- **Correction:** Make `SensorReadingOut.growth_stage: Optional[str] = None` (or backfill a default).
- **Verification:** Insert a reading with null `growth_stage` and call `GET /api/v1/sensors/latest/{id}`; expect 200 today after fix (500 today).

### DB-06 — P2 — `idempotency_key` unique but no conflict handling
- **Location:** `backend/app/crud/__init__.py:107-121` (`create_reading`); model `:96` (`idempotency_key = Column(String, unique=True, ..., nullable=True)`)
- **Evidence:** Duplicate `idempotency_key` submission raises SQLAlchemy `IntegrityError`, which is unhandled → HTTP 500. Nullable unique keys allow multiple NULLs (PostgreSQL behavior), weakening idempotency for unauthenticated/manual submissions.
- **Correction:** Catch `IntegrityError` on `idempotency_key` and return the existing reading or a 409; consider making the key non-nullable for submissions that provide one.
- **Verification:** Submit the same `idempotency_key` twice; expect idempotent 200/201 with the same reading, not a 500.

### DB-07 — P2 — No pagination cap / unbounded `limit`
- **Location:** `backend/app/crud/__init__.py:130` (`get_readings limit: int = 100`); `sensors.py:58`
- **Evidence:** `list_readings` accepts any `limit` with no maximum; a client can request 100,000 rows.
- **Correction:** Enforce `max_limit` (e.g. 1000) and clamp; return total count for pagination UI.
- **Verification:** Request `limit=100000`; confirm clamped response.

### DB-08 — P3 — `updated_at` not updated by database triggers
- **Location:** `backend/app/models/base.py:36,60,75,94,120,136` (`onupdate=...`); migrations use `server_default=sa.text("now()")` only
- **Evidence:** `updated_at` relies on SQLAlchemy ORM `onupdate`; raw SQL or direct DB updates will not refresh it. Migration `0001` lacks `onupdate` triggers.
- **Correction:** Add database triggers or accept ORM-only semantics and document it.
- **Verification:** Update a row via raw SQL and check `updated_at` does not change today.

### DB-09 — P3 — Migration `0002` seeds demo data inside a migration
- **Location:** `backend/alembic/versions/0002_seed_demo.py`
- **Evidence:** Seed data (profiles, fields, sensors, readings, weather) is inserted in an Alembic `upgrade()`; downgrade deletes by email.
- **Problem:** Seed data belongs in a seed script (`seed.py` exists) or separate script, not a schema migration; re-running migrations in production would re-seed or fail.
- **Correction:** Move seed data out of `0002` into `seed.py` (already present) and make `0002` a no-op or remove it.
- **Risks:** Changing migration history requires regenerating or carefully editing revisions.

---

## 8. Smart irrigation domain logic findings

### DO-01 — P2 — Moisture thresholds hardcoded and duplicated
- **Location:** `backend/app/crud/__init__.py:160-169`; `frontend/lib/utils.ts:48-57`
- **Evidence:** Thresholds (<30 low, <45 moderate, <=75 healthy, >75 high) are hardcoded in both backend `moisture_condition` and frontend `moistureConditionLabel`; the design-system says they should be configurable but they are not exposed anywhere.
- **Problem:** No way to adjust thresholds per crop, soil type, or region without code changes; risk of frontend/backend divergence.
- **Correction:** Make thresholds configurable (backend settings or DB table) and expose current thresholds to the frontend.
- **Verification:** Confirm `moisture_condition(29) == "low"` and `moistureConditionLabel(29)` match; test boundary values.

### DO-02 — P2 — Stale-sensor threshold hardcoded at 48 hours
- **Location:** `backend/app/crud/__init__.py:223` (`stale_threshold = now - timedelta(hours=48)`)
- **Evidence:** Design-system defines freshness as Fresh <15min, Delayed 15min-1h, Stale >1h, but the backend uses a hardcoded 48-hour stale threshold in `get_alerts`, contradicting the documented "Stale: more than 1 hour."
- **Problem:** Domain inconsistency between documented freshness model and implemented alert logic.
- **Correction:** Align implementation with the documented freshness model (or document the deviation) and make it configurable.
- **Verification:** Insert a reading 2 hours old; confirm whether a stale alert fires (documented: yes; implemented: no until 48h).

### DO-03 — P2 — `create_sensor` silently deduplicates instead of reporting conflict
- **Location:** `backend/app/crud/__init__.py:82-95` (`create_sensor`)
- **Evidence:** If a sensor with the same `sensor_identifier` already exists on the field, `create_sensor` returns the existing sensor without creating a new one and without signaling that nothing was created.
- **Problem:** Callers cannot distinguish "created" from "already existed"; clients may assume a new sensor was registered.
- **Correction:** Return a flag or raise 409 on conflict; document idempotent behavior.
- **Verification:** Call `POST /fields/{id}/sensors` twice with the same identifier; inspect whether response indicates duplicate.

### DO-04 — P2 — Weather fallback behavior is inconsistent
- **Location:** `backend/app/api/v1/endpoints/weather.py:59-119` (`current_weather`)
- **Evidence:** When OpenWeatherMap returns data, a `WeatherRecord` is persisted; when in demo mode (`source="demo"`), nothing is persisted. Demo values are hardcoded (`temperature=28.0`, etc.) and not tied to the field.
- **Problem:** Demo weather is not stored/queryable historically; live weather is. Inconsistent data model.
- **Correction:** Either persist demo records too (marked `provider="demo"`) or clearly separate demo from persisted data in the response schema.
- **Verification:** Call `current_weather` without an OpenWeatherMap key and confirm no row is inserted into `weather_records`.

### DO-05 — P2 — No irrigation-recommendation logic despite being a core domain area
- **Location:** `backend/app/api/v1/endpoints/` (no recommendations endpoint); README/domain lists "Irrigation recommendations"
- **Evidence:** The implementation-plan and README mention irrigation recommendations, but no endpoint, service, or algorithm exists. Alerts are the only recommendation-adjacent output.
- **Problem:** Feature gap relative to documented product scope; do not fabricate an ML model.
- **Correction:** Scope and implement a rule-based recommendation endpoint (e.g. based on moisture threshold + expected rainfall) if required, clearly labeled as rule-based.
- **Verification:** Confirm `GET /api/v1/.../recommendation` returns 404 today.

### DO-06 — P3 — Sensor data model lacks battery/signal/status fields
- **Location:** `backend/app/models/base.py:67-76` (`Sensor`)
- **Evidence:** `Sensor` has `sensor_type` and `installation_date` but no `status` (online/offline), `battery`, or `last_seen`; `stale_sensor` alerts are derived from readings, not sensor health.
- **Problem:** Cannot distinguish "sensor has no readings yet" from "sensor is broken."
- **Correction:** Add `status` and `last_seen` to `Sensor` if sensor health monitoring is required.
- **Verification:** Confirm no `status` column exists today.

---

## 9. Performance and maintainability findings

### PM-01 — P2 — No tests anywhere in the repository
- **Location:** Repository root / `backend` / `frontend` — no `tests/`, `conftest.py`, `pytest.ini`, or frontend test scripts
- **Evidence:** `find` returned zero test files (excluding the `.opencode/skills/fastapi-testing` reference skill, which is guidance, not project tests). `frontend/package.json` scripts are `dev`, `build`, `start`, `lint` only — no `test`.
- **Problem:** No unit, integration, authz, or contract coverage; regressions can only be caught manually.
- **Correction:** Add backend pytest tests (FastAPI `TestClient`/`httpx` with SQLAlchemy session override on a test DB) and frontend tests; do not introduce Docker/testcontainers unless justified.
- **Risks:** Writing tests requires a test database and may need environment setup.
- **Verification:** Run any new test suite; confirm zero tests currently exist.

### PM-02 — P2 — Duplicate layout/field-card logic across frontend pages
- **Location:** `frontend/app/dashboard/page.tsx` (local `FieldCard`, `MetricCard`, `WeatherCard`, `AlertsCard`) and `frontend/app/fields/page.tsx` (local `SkeletonField`, duplicated field-card markup)
- **Evidence:** Field cards, moisture badges, and progress rendering are duplicated inline across pages instead of shared components.
- **Correction:** Extract shared `FieldCard`, `MetricCard`, `MoistureBadge` into `components/`.
- **Verification:** Compare markup in `dashboard/page.tsx` and `fields/page.tsx`; consolidate.

### PM-03 — P2 — `bcrypt` declared but unused
- **Location:** `backend/requirements.txt:13`; no `bcrypt` import in backend code
- **Evidence:** `bcrypt==4.2.0` is pinned but nothing imports it (Supabase handles password hashing).
- **Correction:** Remove `bcrypt` from requirements to reduce supply chain surface.
- **Verification:** `grep -r bcrypt backend/app` returns no matches.

### PM-04 — P2 — Async endpoints use synchronous SQLAlchemy Session
- **Location:** `backend/app/api/v1/endpoints/weather.py:59-178` (`async def` endpoints with sync `db: Session = Depends(get_db)`)
- **Evidence:** `current_weather` and `forecast_weather` are `async def` but perform blocking SQLAlchemy operations on a synchronous session, blocking the event loop during DB writes.
- **Correction:** Make these endpoints `def` (sync) or switch to async SQLAlchemy session + async driver.
- **Verification:** Measure event-loop blocking during a weather write; prefer converting to sync `def`.

### PM-05 — P3 — Unused imports and dead code
- **Location:** `backend/app/api/v1/endpoints/weather.py:11` imports `WeatherRecord` (used), `dashboard.py:9` imports `WeatherRecord` (unused)
- **Evidence:** `dashboard.py` imports `WeatherRecord` but never uses it; `auth.py:5` imports `jwt` (used only for `get_unverified_claims`).
- **Correction:** Remove unused imports.
- **Verification:** Run a linter (ruff/flake8) or `pyflakes`.

### PM-06 — P3 — No API documentation beyond README / inline docstrings
- **Location:** `backend/app/main.py` (FastAPI auto docs at `/docs`); no `docs/api.md`
- **Evidence:** `docs/` contains only `design-system.md` and `implementation-plan.md`; `implementation-plan.md` Phase 7 lists `docs/api.md` as not done.
- **Correction:** Generate/document the OpenAPI contract (`/docs` is available at runtime) and maintain `docs/api.md`.
- **Verification:** Visit `http://localhost:8000/docs`; confirm endpoints are listed.

---

## 10. Testing coverage assessment

| Area | Coverage | Status |
|---|---|---|
| Backend unit tests | None | No `tests/` directory, no `pytest`, no `conftest.py` |
| Backend integration/API tests | None | No FastAPI `TestClient`/`httpx` test suite |
| Auth/authz tests | None | No tests for JWT verification, ownership, RLS |
| DB isolation/migration tests | None | No `alembic` upgrade/downgrade tests |
| Frontend component tests | None | No Jest/React Testing Library/Vitest |
| Frontend integration/E2E | None | No Playwright despite the skill being present |
| Contract tests | None | Frontend interfaces duplicated manually from backend |

Testing tools are not installed for the project (pytest, pytest-asyncio, httpx for testing, playwright are absent as project dev dependencies). The `fastapi-testing` and `playwright` skills exist only under `.opencode/skills/` / `frontend/.agents/skills/` as guidance.

**Assessment:** Zero automated test coverage. This is a significant gap given the app handles auth, financial-adjacent (water usage) data, and multi-tenant data isolation.

---

## 11. Prioritized issue register

| ID | Severity | Area | Summary |
|---|---|---|---|
| BE-01 / AU-01 | P0 | Security | Real Supabase service-role key, JWT secret, anon key, OpenWeatherMap key committed in `backend/.env`; no `.gitignore` |
| BE-02 | P1 | Auth | New users can be locked out (profile not guaranteed; `ensure_profile` errors swallowed) |
| AU-02 / DB-03 | P1 | Security/DB | No database Row Level Security; isolation is application-layer only |
| BE-03 / AU-03 | P1 | Security | CORS `allow_origins=["*"]` + `allow_credentials=True` |
| DB-02 | P2 | Performance | N+1 queries in dashboard/alerts/field-moisture |
| BE-04 | P2 | Reliability | No global exception handler; inconsistent 500/error responses |
| FE-01 | P2 | Frontend | Profile-creation errors silently swallowed in `SessionProvider` |
| FE-02 / DO-01 | P2 | Domain | Moisture thresholds hardcoded and duplicated backend/frontend |
| DO-02 | P2 | Domain | Stale-sensor threshold (48h) contradicts documented freshness (>1h) |
| DB-01 | P2 | DB | Contradictory unique constraints on `sensors.sensor_identifier` |
| DB-05 | P2 | DB | `SensorReadingOut.growth_stage` required but DB-nullable |
| DB-06 | P2 | DB | `idempotency_key` duplicate → unhandled 500 |
| BE-05 | P2 | Reliability | No rate limiting |
| AU-04 | P2 | Security | `verify_supabase_jwt` swallows all exceptions |
| PM-01 | P2 | Testing | Zero automated tests |
| PM-02 | P2 | Maintainability | Duplicated UI logic across pages |
| PM-04 | P2 | Performance | Async weather endpoints block on sync DB session |
| DB-04 | P2 | Domain/DB | `alerts` table unused; alerts computed in-memory |
| DO-03 | P2 | Domain | `create_sensor` silently deduplicates |
| FE-03 | P3 | Frontend | Non-functional edit/delete buttons on field detail |
| FE-04 | P3 | Frontend | Settings form submits `email` not in `ProfileUpdate` |
| FE-05 | P3 | PWA | SVG placeholder icons |
| PM-03 | P3 | Dependencies | Unused `bcrypt` in requirements |
| PM-05 | P3 | Maintainability | Unused imports |
| DB-07 | P3 | Performance | Unbounded pagination `limit` |
| DB-08 | P3 | DB | `updated_at` not DB-triggered |
| DB-09 | P3 | Migrations | Demo data seeded inside migration `0002` |
| DO-04 | P3 | Domain | Inconsistent weather persistence (demo vs live) |
| DO-05 | P3 | Domain | Missing irrigation-recommendation feature |
| DO-06 | P3 | Domain | No sensor status/battery fields |
| AU-05 | P3 | Security | `/auth/logout` is client-side no-op (documented limitation) |
| AU-06 | P3 | Security | `SUPABASE_JWT_SECRET` unused |
| AU-07 | P3 | Security | No security headers / trusted hosts |
| PM-06 | P3 | Documentation | No `docs/api.md` |

---

## 12. Recommended implementation roadmap

### Phase 0 — Critical security and data integrity (do first)
1. **BE-01/AU-01:** Remove `backend/.env` real secrets; add `.gitignore`; rotate credentials; replace with placeholders.
2. **AU-02/DB-03:** Enable RLS and add policies on all tables (test on a copy of the DB first).
3. **BE-03/AU-03:** Fix CORS to explicit frontend origins with credentials.
4. **BE-02:** Guarantee profile creation on sign-in; stop swallowing `ensure_profile` errors in frontend (`FE-01`).
5. **AU-04:** Distinguish JWT failure modes and log failures.

Dependencies: Phase 0 requires access to the Supabase project to rotate keys; RLS changes require a non-production database for validation.

### Phase 1 — Authentication and authorization reliability
1. Ensure every authenticated user has a profile before allowing data access (auto-create or clear error).
2. Add standardized global exception handling (`BE-04`).
3. Add rate limiting on auth and write endpoints (`BE-05`).
4. Document that `/auth/logout` is client-side; consider short JWT lifetimes (`AU-05`).
5. Add security headers / `TrustedHostMiddleware` (`AU-07`).

Dependencies: Builds on Phase 0 (CORS, secrets).

### Phase 2 — Backend and database architecture
1. **DB-01:** Fix contradictory `sensors` unique constraints.
2. **DB-02:** Eliminate N+1 with aggregated queries in dashboard/alerts/field summaries.
3. **DB-05:** Make `SensorReadingOut.growth_stage` optional.
4. **DB-06:** Handle `idempotency_key` conflicts idempotently.
5. **DB-07:** Add pagination `max_limit` and total counts.
6. **PM-04:** Convert blocking async weather endpoints to sync (or async SQLAlchemy).
7. **DB-08/DB-09:** Decide on `updated_at` triggers; move seed data out of migration `0002` into `seed.py`.

Dependencies: Database changes should be tested against migration upgrade/downgrade; RLS from Phase 0 must remain intact.

### Phase 3 — Frontend architecture and API integration
1. **FE-02/DO-01:** Centralize moisture thresholds; keep frontend/backend in sync.
2. **FE-03:** Wire up or remove non-functional edit/delete buttons; add `/fields/[id]/edit` route if intended.
3. **FE-04:** Align settings form payload with `ProfileUpdate` (remove `email` or make read-only).
4. **PM-02:** Extract shared `FieldCard`/`MetricCard`/moisture-badge components.
5. **FE-06:** Enable TypeScript strictness; remove `any`; derive types from backend schemas.
6. **FE-05:** Replace SVG PWA icons with PNG.

Dependencies: Depends on backend contract stability from Phase 2.

### Phase 4 — Smart irrigation domain logic and reliability
1. **DO-02:** Align stale-sensor freshness with documented model (or document deviation) and make configurable.
2. **DO-04:** Make weather persistence consistent (persist demo or separate clearly).
3. **DO-05:** Scope and implement rule-based irrigation recommendations (no fabricated ML).
4. **DO-03:** Return explicit created/did-not-exist from sensor creation.
5. **DO-06:** Add `status`/`last_seen` to `Sensor` if sensor health is required.
6. **DB-04:** Persist alerts to the `alerts` table and add a resolve action (or remove the table).

Dependencies: Requires stable schema from Phase 2.

### Phase 5 — Testing, performance, and technical debt
1. **PM-01:** Add backend pytest suite (FastAPI TestClient/httpx, session override on test DB) covering auth, ownership, CRUD, alerts; add frontend component/integration tests; add E2E for register → field → reading → dashboard workflow.
2. **PM-03:** Remove unused `bcrypt`.
3. **PM-05:** Remove unused imports.
4. **PM-06:** Create `docs/api.md` from `/docs` OpenAPI output.
5. Add migration upgrade/downgrade tests.
6. Performance-test dashboard with many fields after DB-02.

Dependencies: Tests should run against a local test database; no Docker/testcontainers unless there is a clear reason.

---

## 13. Acceptance criteria per phase

**Phase 0 acceptance:**
- `backend/.env` contains no real secret values; `.gitignore` excludes `.env`.
- Rotated Supabase keys are in place and the app still authenticates.
- CORS rejects/echoes only configured origins; credentials work from the frontend origin.
- Every authenticated user has a profile; sign-in failure surfaces an error to the UI.
- RLS enabled; a non-service DB user cannot read another user's rows.

**Phase 1 acceptance:**
- Standardized JSON error responses for 400/401/403/404/422/500; no raw stack traces.
- Rate limiting returns 429 after threshold on auth/write endpoints.
- Logout documented as client-side; JWT lifetimes reviewed.
- Security headers present on responses.

**Phase 2 acceptance:**
- Two fields may share a `sensor_identifier`; composite constraint enforced.
- Dashboard/alerts for a user with N fields issue O(1) queries (verified via SQL log).
- Reading with null `growth_stage` serializes successfully.
- Duplicate `idempotency_key` returns the existing reading (idempotent), not 500.
- Pagination `limit` clamped; total count returned.
- Alembic `upgrade head` and `downgrade` to base are consistent and reversible.

**Phase 3 acceptance:**
- Moisture condition labels match between backend `moisture_condition` and frontend `moistureConditionLabel` at all boundary values.
- Edit/delete on field detail perform an action (or buttons removed).
- Settings PATCH payload matches `ProfileUpdate`; `email` not sent as mutable.
- Shared components used by dashboard and fields pages; no duplicated field-card markup.
- `tsc --noEmit` passes with strict settings; no `any` in page APIs.
- PWA icons are PNG; install prompt works.

**Phase 4 acceptance:**
- Stale-sensor alert threshold matches documented freshness model (or documented deviation).
- Weather persistence consistent across demo and live modes.
- Rule-based irrigation recommendation endpoint exists (if scoped) and is labeled rule-based.
- Sensor creation reports whether a new sensor was created.
- Alerts written to `alerts` table; resolve action works (or table removed with migration).

**Phase 5 acceptance:**
- Backend test suite passes (auth, ownership, CRUD, alerts, migrations).
- Frontend component/integration tests pass; E2E register → field → reading → dashboard passes.
- `bcrypt` removed; unused imports removed.
- `docs/api.md` exists and matches `/docs` OpenAPI output.
- No new P0/P1 findings remain.

---

## What I inspected
- Full backend source: `main.py`, `core/{config,database,security}.py`, `api/{deps,v1/api,v1/endpoints/*.py}`, `models/base.py`, `schemas/__init__.py`, `crud/__init__.py`, all 3 Alembic migrations, `seed.py`, `requirements.txt`, `.env`, `.env.example`, `alembic.ini`.
- Full frontend source: `app/layout.tsx`, `app/{auth,(app),fields,[id],dashboard,readings,weather,settings}/**`, `middleware.ts`, `components/{auth,layout,ui,dashboard}/**`, `lib/{api,supabase/client,i18n,translations,utils}.ts`, `next.config.js`, `tailwind.config.ts`, `postcss.config.js`, `package.json`, `public/{manifest.json,sw.js,icons/*}`.
- Docs: `README.md`, `docs/design-system.md`, `docs/implementation-plan.md`.
- Installed Python package metadata (versions confirmed).
- Empirically verified `pydantic-settings v2.15.0` loads `backend/.env` via `class Config: env_file` (not a defect).

## What I could not verify
- Runtime behavior requiring a live Supabase project and PostgreSQL database (no database was running and no credentials were used to connect); I did not connect to the database or Supabase, per the no-destructive-operations rule.
- Actual JWT verification against a live Supabase JWKS endpoint (network access to Supabase was not tested).
- Frontend build (`next build`) and TypeScript check were not executed.
- Whether the repository will be pushed to a remote (no git repo exists locally).
- Production CORS/origin values (only `localhost:3000`/`8000` are used locally).

## Most critical five findings
1. **P0 — Committed secrets** in `backend/.env` (service-role key, JWT secret, anon key, OpenWeatherMap key) with no `.gitignore`.
2. **P1 — New users can be locked out** — profile creation not guaranteed; `ensure_profile` errors swallowed (`BE-02`, `FE-01`).
3. **P1 — No database Row Level Security** — isolation is application-layer only (`AU-02`/`DB-03`).
4. **P1 — CORS misconfiguration** — `allow_origins=["*"]` + `allow_credentials=True` (`BE-03`).
5. **P2 — Zero automated tests** across backend and frontend (`PM-01`).

## Location of the audit report
`docs/engineering-audit.md` (this file).

## Recommended first implementation phase
**Phase 0 — Critical security and data integrity:** remove/rotate committed secrets, add `.gitignore`, fix CORS, enable RLS, guarantee profile creation and surface errors.

## Tests or checks actually executed and results
- `find` over the repository: confirmed source layout, absence of project `.gitignore`, and absence of any test files (`*.test.*`, `*.spec.*`, `conftest.py`, `pytest.ini`, `pyproject.toml`, frontend test scripts).
- Installed package versions verified against `requirements.txt` (FastAPI 0.115.0, Pydantic 2.14.3, SQLAlchemy 2.1.8, Alembic 1.20.1, etc.).
- `python -c "from app.core.config import settings ..."` confirmed `pydantic-settings v2.15.0` loads `backend/.env` (SUPABASE_URL, SUPABASE_JWT_SECRET, OPENWEATHERMAP_API_KEY all populated), so config loading is not a defect.
- No database connection, no migration `alembic upgrade`, no frontend build, and no network calls to Supabase/OpenWeatherMap were performed (audit-only, non-destructive).
