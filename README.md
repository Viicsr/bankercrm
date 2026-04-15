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

## Architecture

```
┌─────────────────────────────────────────┐
│              FastAPI App                │
│                                         │
│  ┌──────────┐  ┌──────────┐             │
│  │  Router  │→ │ Service  │             │
│  │ (HTTP)   │  │(Business)│             │
│  └──────────┘  └────┬─────┘             │
│                     │                   │
│  ┌──────────────────▼──────────────┐    │
│  │        Security Layer           │    │
│  │  JWT decode · RBAC · bcrypt     │    │
│  └──────────────────┬──────────────┘    │
│                     │                   │
│              ┌──────▼──────┐            │
│              │  SQLAlchemy │            │
│              │    (ORM)    │            │
│              └──────┬──────┘            │
└─────────────────────┼───────────────────┘
                      │
              ┌───────▼───────┐
              │  PostgreSQL   │
              │   (Docker)    │
              └───────────────┘
```

Cada capa tiene una única responsabilidad:
- **Router** — recibe HTTP, valida parámetros, traduce excepciones a códigos HTTP
- **Service** — lógica de negocio pura, sin dependencias de FastAPI
- **Security** — JWT stateless, hashing bcrypt, dependencias de autenticación y RBAC
- **ORM** — modelos SQLAlchemy, queries async, relaciones

## Project Structure

```
bankercrm/
├── app/
│   ├── core/
│   │   ├── config.py           # Settings con pydantic-settings (12-Factor)
│   │   ├── database.py         # Async engine + connection pool + get_db
│   │   ├── exceptions.py       # Excepciones de dominio (NotFoundError, AlreadyExistsError)
│   │   └── security.py         # hash_password, verify_password, create/decode JWT
│   ├── models/
│   │   ├── client.py           # ORM Client con relationship a accounts
│   │   ├── account.py          # ORM Account con FK a clients + AccountType Enum
│   │   └── user.py             # ORM User con UserRole Enum (admin, analyst, read_only)
│   ├── schemas/
│   │   ├── client.py           # ClientCreate / ClientUpdate / ClientResponse / ClientWithAccountsResponse
│   │   ├── account.py          # AccountCreate / AccountUpdate / AccountResponse
│   │   ├── auth.py             # UserRegister / UserResponse / TokenResponse / RefreshRequest
│   │   └── common.py           # PaginatedResponse[T] — genérico reutilizable
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
│   └── main.py                 # Entrypoint + lifespan con graceful shutdown
├── alembic/                    # Migraciones versionadas
├── tests/
│   ├── conftest.py             # Fixtures: setup_db + client + admin_headers (SQLite async)
│   ├── test_health.py
│   ├── test_clients.py
│   ├── test_accounts.py
│   └── test_auth.py
├── .env.example
├── requirements.txt
└── docker-compose.yml
```

## Getting Started

### Prerequisites

- Python 3.12
- Docker Desktop

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
| `APP_ENV` | Environment name | `development` |
| `APP_NAME` | Application name | `BankCRM` |
| `APP_VERSION` | Application version | `0.1.0` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@localhost:5432/db` |
| `SECRET_KEY` | JWT signing key (generate with secrets.token_hex(32)) | `a3f9...` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `7` |

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

27 passed in 7.71s
```

## Design Decisions (ADR)

### ADR-001: selectinload over joinedload for one-to-many relationships

`selectinload` emits a separate `SELECT ... WHERE id IN (...)` query instead of a JOIN. For one-to-many collections this avoids row duplication — a client with 5 accounts would appear 5 times in a JOIN result. `selectinload` keeps the result set clean at the cost of one additional roundtrip, which is acceptable in an async context.

### ADR-002: Offset pagination over cursor-based in phase 1

Offset/limit pagination is simpler to implement and sufficient for the current data volume. The service layer is isolated enough that migrating to cursor-based pagination later only requires changing `list_clients` in `ClientService` and updating the response schema — no router changes needed.

### ADR-003: Domain exceptions over generic ValueError

`NotFoundError` and `AlreadyExistsError` inherit from a common `AppError` base class. This allows routers to catch specific exception types instead of inspecting error message strings. In a future iteration, a global exception handler (`@app.exception_handler(AppError)`) will replace the per-router `try/except` blocks entirely.

### ADR-004: PyJWT over python-jose for JWT handling

`python-jose` has unpatched CVEs since 2023 and is no longer actively maintained. `PyJWT` is the actively maintained alternative with a stable API. All JWT encoding, decoding, and exception handling uses `PyJWT` directly.

### ADR-005: Stateless JWT with per-request DB verification

Access tokens are stateless (no session stored server-side), but `get_current_user` verifies user existence and `is_active` status on every request. This adds one DB query per authenticated request but ensures that deactivated users lose access immediately without waiting for token expiry. Token blacklisting (requiring Redis) is deferred to a future phase.

### ADR-006: Health check with DB timeout and graceful 503

The `/health` endpoint uses `asyncio.wait_for` with a 5-second timeout to detect unresponsive databases. Returns `503` instead of `200` when the DB is unavailable, making it compatible with load balancers and container orchestration health probes that act on HTTP status codes.

## Daily Startup

```bash
docker start bankercrm-db
cd ~/Projects/bankercrm
source .venv/bin/activate
uvicorn app.main:app --reload
```