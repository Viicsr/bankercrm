# BankCRM API

REST API for banking CRM built with FastAPI, SQLAlchemy 2.0, and PostgreSQL.

## Tech Stack

- FastAPI — async REST framework
- SQLAlchemy 2.0 — async ORM
- Alembic — database migrations
- PostgreSQL — production database
- Pydantic v2 — data validation
- PyJWT + passlib[bcrypt] — JWT authentication and password hashing
- Docker — database container
- pytest — testing
- asgi-correlation-id — X-Request-ID propagation across request lifecycle

## Architecture

```
┌──────────────────────────────────────────────────┐
│                   FastAPI App                    │
│                                                  │
│  ┌─────────────────────────────────────────────┐ │
│  │              Middleware Stack               │ │
│  │  CorrelationId · RequestLogging · Security  │ │
│  └─────────────────────┬───────────────────────┘ │
│                        │                         │
│  ┌──────────┐  ┌───────▼──────┐                  │
│  │  Router  │→ │   Service    │                  │
│  │ (HTTP)   │  │ (Business)   │                  │
│  └──────────┘  └──────┬───────┘                  │
│                       │                          │
│  ┌────────────────────▼──────────────────────┐   │
│  │             Security Layer                │   │
│  │      JWT decode · RBAC · bcrypt           │   │
│  └────────────────────┬──────────────────────┘   │
│                       │                          │
│               ┌───────▼───────┐                  │
│               │  SQLAlchemy   │                  │
│               │    (ORM)      │                  │
│               └───────┬───────┘                  │
└───────────────────────┼──────────────────────────┘
                        │
                ┌───────▼───────┐
                │  PostgreSQL   │
                │   (Docker)    │
                └───────────────┘
```

Cada capa tiene una única responsabilidad:
- **Router** — recibe HTTP, valida parámetros, delega al service. Sin try/except ni lógica de error
- **Service** — lógica de negocio pura. Lanza excepciones de dominio, sin dependencias de FastAPI
- **Middleware** — cross-cutting concerns: request ID, timing, security headers, logging
- **Exception Handlers** — único punto de traducción de excepciones de dominio a respuestas HTTP
- **Security** — JWT stateless, hashing bcrypt, dependencias de autenticación y RBAC
- **ORM** — modelos SQLAlchemy, queries async, relaciones

## Project Structure

```
bankercrm/
├── app/
│   ├── core/
│   │   ├── config.py           # Settings con pydantic-settings (12-Factor) + ALLOWED_ORIGINS
│   │   ├── database.py         # Async engine + connection pool + get_db
│   │   ├── exceptions.py       # Jerarquía de excepciones de dominio (AppBaseException → NotFoundError, ConflictError, ForbiddenError, UnauthorizedError...)
│   │   ├── error_handlers.py   # Handlers globales: app_exception_handler, validation_exception_handler, unhandled_exception_handler
│   │   ├── logging_config.py   # JSONFormatter + setup_logging() — JSON en producción, texto legible en desarrollo
│   │   └── security.py         # hash_password, verify_password, create/decode JWT
│   ├── middleware/
│   │   ├── request_id.py       # RequestLoggingMiddleware — logging estructurado por request con correlation ID, X-Process-Time
│   │   └── security.py         # SecurityHeadersMiddleware — X-Content-Type-Options, X-Frame-Options, Referrer-Policy, HSTS
│   ├── models/
│   │   ├── client.py           # ORM Client con relationship a accounts
│   │   ├── account.py          # ORM Account con FK a clients + AccountType Enum
│   │   └── user.py             # ORM User con UserRole Enum (admin, analyst, read_only)
│   ├── schemas/
│   │   ├── client.py           # ClientCreate / ClientUpdate / ClientResponse / ClientWithAccountsResponse
│   │   ├── account.py          # AccountCreate / AccountUpdate / AccountResponse
│   │   ├── auth.py             # UserRegister / UserResponse / TokenResponse / RefreshRequest
│   │   ├── common.py           # PaginatedResponse[T] — genérico reutilizable
│   │   └── errors.py           # ErrorResponse, FieldError — schema estándar RFC 7807
│   ├── services/
│   │   ├── client_service.py   # CRUD + paginación
│   │   ├── account_service.py  # CRUD + validación de cliente activo
│   │   └── user_service.py     # Registro, autenticación, búsqueda por email/id
│   ├── api/
│   │   └── v1/
│   │       ├── deps.py         # get_current_user + require_roles (RBAC factory)
│   │       └── routers/
│   │           ├── clients.py  # Endpoints de clientes (protegidos por rol)
│   │           ├── accounts.py # Endpoints de cuentas (protegidos por rol)
│   │           └── auth.py     # register / login / refresh
│   └── main.py                 # Entrypoint + lifespan + exception handlers + middleware stack
├── alembic/                    # Migraciones versionadas
├── bruno/                      # Colección Bruno — requests organizadas por recurso
│   ├── auth/
│   │   ├── register admin.yml
│   │   ├── refresh.yml
│   │   └── login.yml
│   ├── clients/
│   │   ├── create client.yml
│   │   ├── list clients.yml
│   │   ├── get client.yml
│   │   ├── get client not found.yml
│   │   └── update client.yml
│   │   ├── get client account.yml
│   │   └── create account.yml
│   ├── health/
│   │   └── health check.yml
│   └── bruno.json              # Configuración de la colección
├── tests/
│   ├── conftest.py             # Fixtures: setup_db + client + user fixtures (SQLite async)
│   ├── test_health.py
│   ├── test_clients.py
│   ├── test_accounts.py
│   ├── test_auth.py
│   ├── test_errors.py          # Formato estándar de errores (404, 409, 422, 401, 403)
│   └── test_middleware.py      # Request ID, process time, security headers
├── .env.example
├── requirements.txt
└── docker-compose.yml
```

## Getting Started

### Prerequisites

- Python 3.12
- Docker Desktop
- Bruno (optional, for API testing)

### 1. Clone the repository

```bash
git clone https://github.com/vicsr/bankercrm.git
cd bankercrm
```

### 2. Create and activate virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your values
```

Generate a secure SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Start PostgreSQL with Docker

```bash
docker run --name bankercrm-db \
  -e POSTGRES_USER=vicsr \
  -e POSTGRES_PASSWORD=bankercrm123 \
  -e POSTGRES_DB=bankercrm \
  -p 5432:5432 \
  -d postgres:16
```

### 6. Run database migrations

```bash
alembic upgrade head
```

### 7. Start the server

```bash
uvicorn app.main:app --reload
```

API available at: `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `APP_ENV` | Environment name — controls log format and HSTS | `development` |
| `APP_NAME` | Application name — included in every log entry | `BankCRM` |
| `APP_VERSION` | Application version | `0.1.0` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@localhost:5432/db` |
| `SECRET_KEY` | JWT signing key (generate with secrets.token_hex(32)) | `a3f9...` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `7` |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origins | `http://localhost:3000,http://localhost:5173` |

## Authentication

The API uses JWT Bearer tokens. Authentication is stateless — the server issues signed tokens and verifies them mathematically on each request without storing sessions.

### Auth Flow

```
1. POST /api/v1/auth/register    → create user account
2. POST /api/v1/auth/login       → obtain access_token + refresh_token
3. Include token in every request: Authorization: Bearer <access_token>
4. POST /api/v1/auth/refresh     → renew access_token using refresh_token
```

### Token Types

| Token | TTL | Purpose |
|---|---|---|
| `access_token` | 30 min | Authenticate requests to protected endpoints |
| `refresh_token` | 7 days | Obtain a new access_token without re-login |

The refresh endpoint rotates the refresh token on every use — the previous token is invalidated when a new one is issued.

### Roles

| Role | Permissions |
|---|---|
| `admin` | Full read + write access |
| `analyst` | Read + create (no modify/delete) |
| `read_only` | Read only |

### Permission Matrix

| Endpoint | admin | analyst | read_only |
|---|---|---|---|
| `POST /clients`               | ✅ | ✅ | ❌ |
| `GET /clients`                | ✅ | ✅ | ✅ |
| `GET /clients/{id}`           | ✅ | ✅ | ✅ |
| `PATCH /clients/{id}`         | ✅ | ✅ | ❌ |
| `GET /clients/{id}/accounts`  | ✅ | ✅ | ✅ |
| `POST /accounts`              | ✅ | ✅ | ❌ |
| `GET /accounts/{id}`          | ✅ | ✅ | ✅ |

### Example

```bash
# Register a user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@bank.com", "password": "Admin1234!", "role": "admin"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin@bank.com&password=Admin1234!"

# Use the token
curl http://localhost:8000/api/v1/clients \
  -H "Authorization: Bearer <access_token>"
```

## Error Handling

All errors follow a consistent RFC 7807-inspired format:

```json
{
  "error": "NotFoundError",
  "detail": "Client '99999' not found",
  "path": "/api/v1/clients/99999",
  "request_id": "a1b2c3d4-..."
}
```

| Field | Description |
|---|---|
| `error` | Exception class name — machine-readable |
| `detail` | Human-readable description of this specific occurrence |
| `path` | Endpoint that generated the error |
| `request_id` | Correlation ID — use this when reporting issues |

Validation errors (422) additionally include an `errors` array:

```json
{
  "error": "ValidationError",
  "detail": "Request validation failed",
  "errors": [
    {"field": "body -> email", "message": "value is not a valid email address"}
  ],
  "path": "/api/v1/clients",
  "request_id": "a1b2c3d4-..."
}
```

### Error Hierarchy

```
AppBaseException
├── NotFoundError       → 404
├── ConflictError       → 409
├── ForbiddenError      → 403
├── UnauthorizedError   → 401
└── ValidationError     → 422
```

Services throw domain exceptions. A single global handler in `app/core/error_handlers.py` converts them to HTTP responses — routers contain no error handling logic.

## Logging

Logging behavior is controlled by `APP_ENV`:

| Environment | Format | Use case |
|---|---|---|
| `development` | Human-readable (`HH:MM:SS \| LEVEL \| module \| message`) | Local development — easy to read in terminal |
| `staging` / `production` | JSON (one log entry per line) | Machine-parseable, ready for Datadog / CloudWatch / Grafana Loki |

Every log entry in production JSON format includes:

```json
{
  "timestamp": "2026-04-28T17:00:01.234Z",
  "level": "INFO",
  "logger": "app.middleware.request_id",
  "message": "HTTP Request",
  "service": "BankCRM",
  "environment": "production",
  "request_id": "a1b2c3d4-e5f6-...",
  "method": "GET",
  "path": "/api/v1/clients/1",
  "status_code": 200,
  "duration_ms": 12.43
}
```

The `request_id` field appears on every log line generated during a request — filter by it to see the complete trace of any single request.

**What never appears in logs:** passwords, JWT tokens, full card numbers, DNI/NIE, complete email addresses in production (PII under GDPR).

To test JSON format locally:

```bash
APP_ENV=production uvicorn app.main:app --reload
```

## Middleware

Every request passes through the following middleware stack in order:

| Order | Middleware | Header added | Purpose |
|---|---|---|---|
| 1st | `CorrelationIdMiddleware` | `X-Request-ID` | Assigns a unique UUID per request; accepts client-provided ID if present |
| 2nd | `RequestLoggingMiddleware` | `X-Process-Time` | Structured log per request with method, path, status, duration, and request_id |
| 3rd | `SecurityHeadersMiddleware` | Multiple | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` |
| 4th | `CORSMiddleware` | `Access-Control-*` | Restricts cross-origin requests to `ALLOWED_ORIGINS` |

> Middlewares execute in reverse registration order — `CorrelationIdMiddleware` runs first so the ID is available to all subsequent layers.

```bash
# Verify headers are present
curl -I http://localhost:8000/health
# X-Request-ID: a1b2c3d4-e5f6-...
# X-Process-Time: 3.21ms
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
```

## Bruno API Client

The repository includes a [Bruno](https://www.usebruno.com/) collection in the `bruno/` directory. Bruno is an open-source API client (like Postman/Insomnia) that stores collections as plain files versioned alongside the code.

### Setup

1. Install Bruno from [usebruno.com](https://www.usebruno.com/)
2. Open Bruno → **Open Collection** → select the `bruno/` folder
3. Set the `base_url` environment variable to `http://localhost:8000`

### Workflow

```
1. Run health/health check → verify the app is running and DB is connected
2. Run auth/login → copy access_token and refresh_token from the response
3. Set {{token}} and {{refresh_token}} as environment variables in Bruno
4. When the access_token expires (30 min), run auth/refresh instead of logging in again
5. For requests targeting a specific resource, set {{client_id}} in the environment
```

Requests are organized by resource (`auth/`, `clients/`, `accounts/`) and mirror the API endpoint structure exactly.

## API Endpoints

### Health

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | Public | Health check with DB connectivity status |

Returns `200` with `"db": "connected"` when healthy, `503` with `"db": "unreachable"` or `"db": "timeout"` when the database is unavailable.

### Auth

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Public | Create a new user account |
| `POST` | `/api/v1/auth/login` | Public | Obtain access + refresh tokens |
| `POST` | `/api/v1/auth/refresh` | Public | Renew access token |

### Clients

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/clients` | admin, analyst | Create a new client |
| `GET` | `/api/v1/clients` | any role | List clients (paginated) |
| `GET` | `/api/v1/clients/{id}` | any role | Get client by ID |
| `PATCH` | `/api/v1/clients/{id}` | admin, analyst | Partial update of a client |
| `GET` | `/api/v1/clients/{id}/accounts` | any role | Get client with all their accounts |

### Accounts

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/accounts?client_id={id}` | admin, analyst | Create account for a client |
| `GET` | `/api/v1/accounts/{id}` | any role | Get account by ID |

### Pagination

The `GET /api/v1/clients` endpoint supports pagination:

```
GET /api/v1/clients?page=1&size=20&only_active=true
```

Response shape:
```json
{
  "items": [...],
  "total": 50,
  "page": 1,
  "size": 20,
  "pages": 3
}
```

## Running Tests

```bash
pytest tests/ -v
```

Tests use SQLite in-memory — no Docker required.

Expected output:
```
tests/test_auth.py::test_register_user PASSED
tests/test_auth.py::test_register_duplicate_email PASSED
tests/test_auth.py::test_login_success PASSED
tests/test_auth.py::test_login_wrong_password PASSED
tests/test_auth.py::test_login_nonexistent_email PASSED
tests/test_auth.py::test_protected_endpoint_without_token PASSED
tests/test_auth.py::test_protected_endpoint_with_invalid_token PASSED
tests/test_auth.py::test_admin_can_create_client PASSED
tests/test_auth.py::test_readonly_cannot_create_client PASSED
tests/test_auth.py::test_readonly_can_read_clients PASSED
tests/test_auth.py::test_refresh_token PASSED
tests/test_auth.py::test_refresh_with_access_token_fails PASSED
tests/test_accounts.py::test_create_account PASSED
tests/test_acounts.py::test_create_account PASSED
tests/test_acounts.py::test_create_account_negative_balance PASSED
tests/test_acounts.py::test_create_account_duplicate_number PASSED
tests/test_acounts.py::test_create_account_nonexistent_client PASSED
tests/test_acounts.py::test_get_account PASSED
tests/test_acounts.py::test_get_client_with_accounts PASSED
tests/test_acounts.py::test_list_clients_paginated PASSED
tests/test_acounts.py::test_list_clients_page_size_limit PASSED
tests/test_acounts.py::test_update_client PASSED
tests/test_client.py::test_create_client PASSED
tests/test_client.py::test_create_client_duplicate_email PASSED
tests/test_client.py::test_get_client PASSED
tests/test_client.py::test_get_client_not_found PASSED
tests/test_health.py::test_health_check_ok PASSED
tests/test_health.py::test_health_check_db_unreachable PASSED
tests/test_errors.py::test_404_returns_standard_format PASSED
tests/test_errors.py::test_409_on_duplicate_email PASSED
tests/test_errors.py::test_422_validation_error_format PASSED
tests/test_errors.py::test_401_returns_standard_format PASSED
tests/test_errors.py::test_403_returns_standard_format PASSED
tests/test_errors.py::test_invalid_path_returns_404 PASSED
tests/test_middleware.py::test_request_id_header_present PASSED
tests/test_middleware.py::test_process_time_header_present PASSED
tests/test_middleware.py::test_security_headers_present PASSED
tests/test_middleware.py::test_each_request_has_unique_request_id PASSED
tests/test_middleware.py::test_error_response_includes_request_id PASSED

38 passed in X.XXs
```

## CI

[![CI Pipeline](https://github.com/Viicsr/bankercrm/actions/workflows/ci.yml/badge.svg)](https://github.com/Viicsr/bankercrm/actions/workflows/ci.yml)

## Design Decisions (ADR)

### ADR-001: selectinload over joinedload for one-to-many relationships

`selectinload` emits a separate `SELECT ... WHERE id IN (...)` query instead of a JOIN. For one-to-many collections this avoids row duplication — a client with 5 accounts would appear 5 times in a JOIN result. `selectinload` keeps the result set clean at the cost of one additional roundtrip, which is acceptable in an async context.

### ADR-002: Offset pagination over cursor-based in phase 1

Offset/limit pagination is simpler to implement and sufficient for the current data volume. The service layer is isolated enough that migrating to cursor-based pagination later only requires changing `list_clients` in `ClientService` and updating the response schema — no router changes needed.

### ADR-003: Domain exceptions over generic ValueError

`NotFoundError`, `ConflictError`, and related exceptions inherit from `AppBaseException`. This allows a single global handler (`app_exception_handler`) to convert them to HTTP responses without any `try/except` in the routers. Each exception type carries its own `status_code` and `detail` as class attributes, so the handler never needs to inspect the message string.

### ADR-004: PyJWT over python-jose for JWT handling

`python-jose` has unpatched CVEs since 2023 and is no longer actively maintained. `PyJWT` is the actively maintained alternative with a stable API. All JWT encoding, decoding, and exception handling uses `PyJWT` directly.

### ADR-005: Stateless JWT with per-request DB verification

Access tokens are stateless (no session stored server-side), but `get_current_user` verifies user existence and `is_active` status on every request. This adds one DB query per authenticated request but ensures that deactivated users lose access immediately without waiting for token expiry. Token blacklisting (requiring Redis) is deferred to a future phase.

### ADR-006: Health check with DB timeout and graceful 503

The `/health` endpoint uses `asyncio.wait_for` with a 5-second timeout to detect unresponsive databases. Returns `503` instead of `200` when the DB is unavailable, making it compatible with load balancers and container orchestration health probes that act on HTTP status codes.

### ADR-007: Domain exceptions over HTTPException in services

**Context:** Services need to signal error conditions to callers.
**Decision:** Services throw domain exceptions (`NotFoundError`, `ConflictError`, `ForbiddenError`) that inherit from `AppBaseException`.
**Alternative considered:** Raise `HTTPException` directly from the service.
**Trade-off:** More initial boilerplate, but services are transport-agnostic. If the same service is called from a WebSocket handler, a Celery task, or a CLI command, it does not carry HTTP dependencies. A single global handler is the only place that knows about HTTP.

### ADR-008: Structured JSON logging with readable format in development

**Context:** JSON logs are unreadable during local development.
**Decision:** Human-readable format in `development`, JSON in `staging`/`production`. Controlled by `APP_ENV`.
**Alternative considered:** Always JSON, use `jq` for local readability.
**Trade-off:** Two formatters instead of one, but developer experience is meaningfully better. The 12-factor app principle (Factor XI) requires treating logs as event streams — the format is an implementation detail of the environment.

### ADR-009: Correlation ID in both response header and error body

**Context:** Correlating a client error report with a specific log entry requires a shared identifier.
**Decision:** `X-Request-ID` is added as a response header on every request and included in the `request_id` field of every error response body.
**Alternative considered:** Log-only — keep the ID internal and require timestamp + path to find the log.
**Trade-off:** Minimal — one extra field in error responses. The benefit is that support workflows go from "find the log somehow" to "filter by request_id instantly".

### ADR-010: Bruno over Postman for API client collection

**Context:** The project needs a way to manually test and document API requests that lives alongside the code.
**Decision:** Bruno collections are plain `.bru` files committed to the repository in the `bruno/` directory.
**Alternative considered:** Postman (stores collections in the cloud, requires an account) or Insomnia (similar cloud dependency).
**Trade-off:** Bruno has a smaller ecosystem than Postman, but its file-based storage means the collection is always in sync with the code, works offline, and has no account requirement.

## Daily Startup

```bash
docker start bankercrm-db
cd ~/Projects/bankercrm
source .venv/bin/activate
uvicorn app.main:app --reload
```