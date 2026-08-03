# ServiceHub AI — Service Provider Application

An AI-based service provider & booking platform. Customers browse services,
book providers at a time slot, and providers manage their catalog, weekly
availability, and the booking lifecycle. It also includes **authentication,
admin management (provider verification + audit logs), customer reviews, an
admin dashboard, and an AI assistant** (chatbot, recommendations, market trends,
provider search). The backend is a FastAPI + SQLAlchemy application organised as
a clean **layered architecture**.

> Repository root contains the backend (`backend/`) and a placeholder for the
> frontend (`frontend/`). This document focuses on the backend.

---

## Table of contents

- [Tech stack](#tech-stack)
- [Architecture](#architecture)
- [Directory layout](#directory-layout)
- [Getting started](#getting-started)
  - [Run with Docker](#run-with-docker)
  - [Run locally](#run-locally)
- [Running the tests](#running-the-tests)
- [API conventions](#api-conventions)
  - [Response envelope](#response-envelope)
  - [Pagination](#pagination)
  - [Errors](#errors)
  - [Authentication & roles](#authentication--roles)

---

## Tech stack

| Concern       | Technology                                        |
| ------------- | ------------------------------------------------- |
| Web framework | FastAPI + Uvicorn                                 |
| ORM           | SQLAlchemy 2.0 (async)                            |
| Database      | PostgreSQL (asyncpg) — SQLite (aiosqlite) in tests|
| Messaging     | Redis (optional, best-effort event publishing)    |
| Validation    | Pydantic v2 / pydantic-settings                   |
| Security      | PyJWT + bcrypt                                    |
| Tests         | pytest + pytest-asyncio + httpx                   |

---

## Architecture

The backend follows a strict, horizontally-layered layout. **Dependencies flow
one way**: `api → services → repositories → models`. A layer never reaches into
a sibling layer or skips one.

| Layer         | Responsibility                                                                 |
| ------------- | ------------------------------------------------------------------------------ |
| `app/api/v1/` | HTTP routers (controllers). Parse/validate input, call services, shape responses. No business logic. |
| `app/services/` | Business logic & rules (uniqueness, state machine, availability, ownership). Each service is a class bound to a session. |
| `app/repositories/` | Data-access. One class per aggregate; only talks to the DB and returns ORM objects. No business rules. |
| `app/models/` | SQLAlchemy ORM models (one file per entity). |
| `app/schemas/` | Pydantic request/response models (one file per domain). |
| `app/core/`   | Cross-cutting concerns: config, security, exceptions, auth dependencies, permission guards. |
| `app/database/` | Declarative `Base`, engine/session factory, request-scoped session dependency. |
| `app/common/` | Shared constants (enums), pagination, response envelopes, small utilities. |

This separation keeps each layer thin and independently testable: business
rules are unit-tested through services, and the data layer through repositories,
without standing up HTTP or a real database.

### Request flow

```
HTTP request
   │
   ▼
api/v1/<router> ─── validates input (Pydantic schema)
   │
   ▼
services/<service> ─── applies business rules, orchestrates repositories
   │
   ▼
repositories/<repository> ─── runs queries against the database
   │
   ▼
models / database
```

---

## Directory layout

```
backend/
├── main.py                     # FastAPI app factory + lifespan
├── requirements.txt
├── Dockerfile
├── pytest.ini
├── .env.example                # copy to .env to configure
├── app/
│   ├── api/v1/                 # routers: auth, admin, categories, services,
│   │                           #   bookings, reviews, dashboard, ai + aggregator
│   ├── core/                   # config, security, exceptions, dependencies, permissions
│   ├── database/               # base, engine/session, request-scoped session
│   ├── common/                 # constants, pagination, responses, utils
│   ├── models/                 # user, provider, category, service, booking, schedule, review, admin_log
│   ├── schemas/                # auth, admin, category, service, booking, schedule, review, dashboard, ai
│   ├── repositories/           # base + per-aggregate data access + service filters
│   └── services/               # auth, admin, provider, category, service, booking,
│                               #   scheduling, review, dashboard, ai
└── tests/
    ├── conftest.py             # shared fixtures (in-memory SQLite)
    ├── factories.py            # record builders
    └── unit/                   # service-layer, repository-layer & security tests
```

---

## Getting started

### Run with Docker

The `docker-compose.yml` stacks PostgreSQL + Redis + the backend.

```bash
# From the repository root
docker compose up --build
```

The API is then available at <http://localhost:8000>, with interactive docs at
<http://localhost:8000/docs>.

### Run locally

Requires Python 3.11+ and (optionally) PostgreSQL/Redis for full functionality.

```bash
cd backend

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # adjust credentials as needed
uvicorn main:app --reload
```

> Tests use an in-memory SQLite database and run **without** PostgreSQL or
> Redis, so you only need Python + the requirements to run them.

---

## Running the tests

The suite exercises the service layer, repository layer, and security
primitives against an in-memory SQLite database. No external services needed.

```bash
cd backend
python -m pytest              # or: pytest -v
```

### Running the tests in Docker

A dedicated `test` service builds the backend image and runs the suite in an
isolated container (again, no Postgres/Redis required):

```bash
# From the repository root
docker compose build backend
docker compose run --rm test
```

---

## API conventions

### Response envelope

Every endpoint returns a uniform JSON envelope so consumers rely on a single
contract:

```json
{
  "success": true,
  "message": "Services fetched.",
  "data": { ... }
}
```

`data` holds the payload for successful responses; it may be a single object or
a page.

### Pagination

List endpoints accept `page` (1-based) and `page_size` (capped by
`MAX_PAGE_SIZE`). Responses use a standard page shape:

```json
{
  "items": [ ... ],
  "total": 37,
  "page": 1,
  "page_size": 20,
  "pages": 2
}
```

### Errors

Domain errors are raised as typed exceptions (e.g. `NotFoundError`,
`ConflictError`, `ForbiddenError`) in the service layer and mapped centrally to
HTTP status codes. Validation errors from FastAPI are also normalised. Error
bodies are:

```json
{
  "success": false,
  "code": "not_found",
  "message": "Service not found.",
  "details": null,
  "status_code": 404
}
```

| Exception            | HTTP status | `code`        |
| -------------------- | ----------- | ------------- |
| `BadRequestError`    | 400         | `bad_request` |
| `UnauthorizedError`  | 401         | `unauthorized`|
| `ForbiddenError`     | 403         | `forbidden`   |
| `NotFoundError`      | 404         | `not_found`   |
| `ConflictError`      | 409         | `conflict`    |
| Validation error     | 422         | `validation_error` |

### Authentication & roles

Create an account at `POST /api/v1/auth/register` and obtain a bearer token at
`POST /api/v1/auth/login`. Send it as `Authorization: Bearer <token>`. Role
guards restrict access:

- `require_customer` — customers & admins
- `require_provider` — providers & admins
- `require_admin` — admins only

The booking routes additionally enforce ownership/participation (a provider may
only act on their own bookings; customers may only view/cancel their own).

### Feature endpoints

| Area | Endpoints |
| --- | --- |
| Auth | `POST /auth/register`, `POST /auth/login` |
| Admin | `POST /admin/providers/onboard`, `GET /admin/users`, `GET /admin/providers`, `PUT /admin/providers/{id}/verify`, `GET /admin/audit-logs` |
| Reviews | `POST /reviews`, `GET /reviews` |
| Dashboard | `POST /dashboard` |
| AI assistant | `POST /ai/chatbot`, `POST /ai/recommend`, `GET /ai/trends`, `GET /ai/search` |

