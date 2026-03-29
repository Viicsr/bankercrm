# BankCRM API

REST API for banking CRM built with FastAPI, SQLAlchemy 2.0, and PostgreSQL.

## Tech Stack

- FastAPI — async REST framework
- SQLAlchemy 2.0 — async ORM
- Alembic — database migrations
- PostgreSQL — production database
- Pydantic v2 — data validation
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
- **ORM** — modelos SQLAlchemy, queries async, relaciones

## Project Structure

```
bankercrm/
├── app/
│   ├── core/
│   │   ├── config.py           # Settings con pydantic-settings (12-Factor)
│   │   ├── database.py         # Async engine + connection pool + get_db
│   │   └── exceptions.py       # Excepciones de dominio (NotFoundError, AlreadyExistsError)
│   ├── models/
│   │   ├── client.py           # ORM Client con relationship a accounts
│   │   └── account.py          # ORM Account con FK a clients + AccountType Enum
│   ├── schemas/
│   │   ├── client.py           # ClientCreate / ClientUpdate / ClientResponse / ClientWithAccountsResponse
│   │   ├── account.py          # AccountCreate / AccountUpdate / AccountResponse
│   │   └── common.py           # PaginatedResponse[T] — genérico reutilizable
│   ├── services/
│   │   ├── client_service.py   # CRUD + paginación
│   │   └── account_service.py  # CRUD + validación de cliente activo
│   ├── api/
│   │   └── v1/
│   │       └── routers/
│   │           ├── clients.py  # Endpoints de clientes
│   │           └── accounts.py # Endpoints de cuentas
│   └── main.py                 # Entrypoint + lifespan
├── alembic/                    # Migraciones versionadas
├── tests/
│   ├── conftest.py             # Fixtures: setup_db + client (SQLite async)
│   ├── test_health.py
│   ├── test_client.py
│   └── test_acounts.py
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

## API Endpoints

### Health

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |

### Clients

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/clients` | Create a new client |
| `GET` | `/api/v1/clients` | List clients (paginated) |
| `GET` | `/api/v1/clients/{id}` | Get client by ID |
| `PATCH` | `/api/v1/clients/{id}` | Partial update of a client |
| `GET` | `/api/v1/clients/{id}/accounts` | Get client with all their accounts |

### Accounts

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/accounts?client_id={id}` | Create account for a client |
| `GET` | `/api/v1/accounts/{id}` | Get account by ID |

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

Tests use SQLite — no Docker required.

Expected output:
```
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
tests/test_health.py::test_health_check PASSED

14 passed in 0.45s
```

## Design Decisions (ADR)

### ADR-001: selectinload over joinedload for one-to-many relationships

`selectinload` emits a separate `SELECT ... WHERE id IN (...)` query instead of a JOIN. For one-to-many collections this avoids row duplication — a client with 5 accounts would appear 5 times in a JOIN result. `selectinload` keeps the result set clean at the cost of one additional roundtrip, which is acceptable in an async context.

### ADR-002: Offset pagination over cursor-based in phase 1

Offset/limit pagination is simpler to implement and sufficient for the current data volume. The service layer is isolated enough that migrating to cursor-based pagination later only requires changing `list_clients` in `ClientService` and updating the response schema — no router changes needed.

### ADR-003: Domain exceptions over generic ValueError

`NotFoundError` and `AlreadyExistsError` inherit from a common `AppError` base class. This allows routers to catch specific exception types instead of inspecting error message strings. In a future iteration, a global exception handler (`@app.exception_handler(AppError)`) will replace the per-router `try/except` blocks entirely.

## Daily Startup

```bash
docker start bankercrm-db
cd ~/Projects/bankercrm
source .venv/bin/activate
uvicorn app.main:app --reload
```
```