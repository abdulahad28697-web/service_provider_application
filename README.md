# ServiceHub AI

ServiceHub AI is a full-stack service-provider and booking platform that
connects customers with verified service providers. It supports customer
bookings, provider management, messaging, reviews, notifications, payments,
AI assistance, and admin management.

## Features

### Customer Features

- User registration and login (JWT)
- Profile management
- Address management
- Browse, search and filter services
- Provider public profiles
- Favorite providers
- Booking creation with availability and time-slot selection
- Booking history, cancellation and rescheduling
- Customer ↔ provider messaging
- Notifications
- Payment checkout (Cash, JazzCash, Easypaisa)
- Reviews and ratings
- AI service assistant

### Provider Features

- Provider onboarding and verification
- Provider profile management
- Service creation and management (auto-generated unique slugs)
- Provider availability / schedule management
- Booking request management (accept / reject / complete)
- Customer messaging
- Notifications
- Payment-status tracking
- Cash-payment confirmation
- Earnings and revenue dashboard
- Portfolio management
- Reviews and ratings

### Admin Features

- Admin authentication
- Admin dashboard
- Provider verification and application management
- Booking, review and payment management
- Active/deactivated user statistics
- Audit logs

## Technology Stack

### Frontend

- React 19
- Vite 8
- React Router 7
- Axios
- Lucide React

### Backend

- FastAPI 0.141 (Python 3.13)
- SQLAlchemy 2.0 (async)
- PostgreSQL via asyncpg
- Redis (pub/sub notifications)
- Pydantic v2 / pydantic-settings
- PyJWT for JWT tokens
- bcrypt for password hashing
- WebSockets for real-time messaging

### Infrastructure

- Docker / Docker Compose
- PostgreSQL 16
- Redis 7

## Project Structure

```text
service-provider-team/
├── backend/
│   ├── app/
│   │   ├── api/v1/        # HTTP endpoints (routers)
│   │   ├── common/        # Cross-cutting helpers (utils, responses, pagination)
│   │   ├── core/          # Config, security, exceptions, dependencies
│   │   ├── database/      # Engine, session, base
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── repositories/  # Data-access layer
│   │   ├── schemas/       # Pydantic request/response models
│   │   ├── services/      # Business logic
│   │   └── uploads/       # Local upload handling
│   ├── tests/             # Pytest suite (unit tests)
│   ├── main.py            # FastAPI app factory + middleware
│   ├── seed.py            # Realistic sample-data seeder
│   ├── Dockerfile
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
└── README.md
```

## Quick Start (Docker)

The full stack runs with a single command:

```bash
docker compose up --build
```

This starts four containers:

| Service  | Port | Description                                 |
|----------|------|---------------------------------------------|
| frontend | 3000 | React UI served via Nginx                   |
| backend  | 8000 | FastAPI app + Swagger UI at `/docs`         |
| db       | 5432 | PostgreSQL 16                               |
| redis    | 6379 | Redis 7                                     |

Once the stack is healthy, seed sample data:

```bash
docker compose exec backend python seed.py
```

All seeded accounts share the password **`Password123`**. See
`backend/seed.py` for the full list of accounts (admin, providers,
customers).

You can also run the backend test suite inside Docker (no Postgres
required — tests use an in-memory SQLite database):

```bash
docker compose run --rm test
```

## Quick Start (Local Development)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # PowerShell:  .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Point at your local Postgres + Redis (or use the Docker defaults below):
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/servicehub
export REDIS_URL=redis://localhost:6379/0
export SECRET_KEY=dev-secret-change-me
export CORS_ORIGINS='["http://localhost:5173"]'
export DEBUG=true

uvicorn main:app --reload --port 8000
```

API docs: <http://localhost:8000/docs>

### Frontend

```bash
cd frontend
npm install
npm run dev
```

UI: <http://localhost:5173>

### Run tests

```bash
cd backend
pytest -v
```

The test suite uses SQLite + an in-memory async engine, so it requires
no external services.

## Environment Variables

All backend settings are loaded from environment variables (or a `.env`
file at the backend root). See `backend/app/core/config.py` for the full
list. The most important are:

| Variable             | Description                                                  | Default                                                                                |
|----------------------|--------------------------------------------------------------|----------------------------------------------------------------------------------------|
| `PROJECT_NAME`       | Service name shown in OpenAPI                                | `ServiceHub AI`                                                                        |
| `PROJECT_VERSION`    | Service version                                              | `0.1.0`                                                                                |
| `API_V1_PREFIX`      | API root prefix                                              | `/api/v1`                                                                              |
| `DEBUG`              | Enables dev shortcuts (rate limit skip, default secret OK)   | `False`                                                                                |
| `SECRET_KEY`         | JWT signing key (**required to change in production**)       | `change-me-in-production` (rejected unless `DEBUG=true`)                               |
| `ALGORITHM`          | JWT algorithm                                                | `HS256`                                                                                |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT lifetime in minutes                                | `1440` (24h)                                                                           |
| `DATABASE_URL`       | SQLAlchemy async URL                                         | `postgresql+asyncpg://postgres:postgres@db:5432/servicehub`                            |
| `REDIS_URL`          | Redis connection URL                                         | `redis://redis:6379/0`                                                                 |
| `ENABLE_REDIS`       | Toggle Redis-backed pub/sub for notifications                | `True`                                                                                 |
| `NOTIFICATION_CHANNEL` | Redis pub/sub channel for notifications                     | `servicehub:notifications`                                                             |
| `CORS_ORIGINS`       | Comma-separated list of allowed origins (JSON list in Docker) | `["http://localhost:3000","http://localhost:5173"]` (must not be `*` in production)   |
| `DEFAULT_PAGE_SIZE`  | Default pagination size                                      | `20`                                                                                   |
| `MAX_PAGE_SIZE`      | Maximum pagination size                                      | `100`                                                                                  |

### Production validation

`Settings` will refuse to start if both of these are true:

- `DEBUG` is `false` (the default)
- `SECRET_KEY` is still the placeholder `change-me-in-production`

…and will also reject `CORS_ORIGINS` containing `*` when not in debug mode.

## Middleware & Security

`backend/main.py` installs three middlewares on every request:

1. **`SecurityHeadersMiddleware`** — adds `X-Content-Type-Options`,
   `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`, plus
   `Strict-Transport-Security` and `Content-Security-Policy` once
   `DEBUG` is off.
2. **`RateLimitMiddleware`** — 120 requests/minute per client IP, skipped
   for `/`, `/health` and `/media/*`, and disabled entirely in debug.
   Excess requests return `429 Too Many Requests` with a `Retry-After`
   header.
3. **`CORSMiddleware`** — origin list driven by `CORS_ORIGINS`.

All errors thrown by the application flow through
`app.core.exceptions.register_exception_handlers` and are returned in a
uniform envelope:

```json
{
  "success": false,
  "message": "Service not found.",
  "data": null
}
```

## Architecture

The backend follows a clean layered pattern:

```
API routers (app/api/v1)
   ↓
Services (app/services)   ← business rules, transactions
   ↓
Repositories (app/repositories)   ← data access only
   ↓
Models (app/models)   ← SQLAlchemy ORM
```

Cross-cutting helpers live in `app/common`:

- `app/common/utils.py` — `slugify`, `generate_unique_slug`,
  `generate_public_id`, `utc_now`, `coerce_bool`
- `app/common/responses.py` — `success_response` / `error_response`
- `app/common/pagination.py` — `PageParams` and `Page`
- `app/common/constants.py` — enums (`BookingStatus`, `UserRole`, …)

### Service slug generation

Services try the **bare** slug first; only when that collides do we
fall back to `base-slug` + provider id + counter. This keeps URLs clean
when no collision exists. The logic lives in
`app.common.utils.generate_unique_slug` and is exercised by unit tests.

### Soft-delete with booking conflict

Deleting a service (marking `is_active = false`) is rejected with
`ConflictError` if the service has any booking in `PENDING`, `ACCEPTED`,
or `COMPLETED` status.

## API Surface

All endpoints are mounted under `/api/v1`. Highlights:

| Group       | Prefix                  | Notes                                                    |
|-------------|-------------------------|----------------------------------------------------------|
| Auth        | `/auth`                 | register, login, change-password, forgot/reset-password  |
| Users       | `/users`                | profile, addresses, favorites                            |
| Providers   | `/providers`            | profiles, search, application, verification              |
| Services    | `/services`             | CRUD, search, filter, pagination                         |
| Categories  | `/categories`           | list, CRUD                                               |
| Bookings    | `/bookings`             | book, accept/reject/complete/cancel/reschedule, payments |
| Reviews     | `/reviews`              | per booking                                              |
| Messaging   | `/messages`, `/ws/chat` | REST + WebSocket chat                                    |
| Schedule    | `/providers/me/schedule`| provider availability                                    |
| Notifications | `/notifications`      | list, mark read                                          |
| Dashboard   | `/dashboard`            | customer / provider / admin summaries                    |
| Admin       | `/admin`                | admin-only operations                                    |
| AI          | `/ai`                   | assistant endpoints                                      |
| Health      | `/` and `/api/v1/health`| root and health checks                                   |

Interactive docs are auto-generated at `/docs` (Swagger UI) and
`/redoc`.

## Testing

```bash
cd backend
pytest -v                # full suite (84 tests)
pytest tests/unit/test_utils.py   # utility-focused subset
```

The test suite uses:

- `pytest-asyncio` for async test support
- An in-memory SQLite database (`sqlite+aiosqlite://`) for fast, isolated runs
- `tests/factories.py` for shared test data builders

Recent additions:

- `tests/unit/test_security.py` — production config validation
- `tests/unit/test_utils.py` — `slugify`, `generate_unique_slug`,
  `generate_public_id`, `coerce_bool`

## Seed Data

`backend/seed.py` populates a fresh database with realistic sample data:

- 1 admin
- 8 providers (each with schedule, portfolio image, 1–3 services)
- 5 customers
- 8 categories
- 8 bookings across all statuses
- Reviews for completed bookings
- A few favorite-provider links

Re-runnable: it skips rows that already exist. Pass `--clear` to wipe
all tables first:

```bash
docker compose exec backend python seed.py --clear
```

## Troubleshooting

- **`SECRET_KEY must be changed from the default value in production`**
  — you started the app with `DEBUG=false` (default) and forgot to set
  `SECRET_KEY`. Set a strong random value (e.g. `openssl rand -hex 32`).
- **`CORS_ORIGINS cannot contain '*'`** — same idea for production CORS;
  list explicit origins.
- **Frontend can't reach the API** — verify the `CORS_ORIGINS` list
  includes the frontend origin (e.g. `http://localhost:5173` for `vite`,
  `http://localhost:3000` for Docker).
- **Tests are slow / hang** — make sure no other Postgres or Redis
  process is occupying the test ports. The tests do not require them.
- **Rate limit `429` in dev** — set `DEBUG=true` to bypass the limiter.