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

## Project Structure
bankercrm/
├── app/
│   ├── core/
│   │   ├── config.py         # Settings with pydantic-settings (12-Factor)
│   │   └── database.py       # Async engine + connection pool + get_db
│   ├── models/
│   │   └── client.py         # SQLAlchemy ORM models
│   ├── schemas/
│   │   └── client.py         # Pydantic schemas (input/output)
│   ├── services/
│   │   └── client_service.py # Business logic layer
│   ├── api/
│   │   └── v1/
│   │       └── routers/
│   │           └── clients.py # HTTP endpoints
│   └── main.py               # App entrypoint + lifespan
├── alembic/                  # Database migrations
├── tests/                    # pytest test suite
├── .env.example              # Environment variables template
├── requirements.txt
└── docker-compose.yml

## Getting Started

### Prerequisites

- Python 3.12
- Docker Desktop

### 1. Clone the repository

git clone https://github.com/vicsr/bankercrm.git
cd bankercrm

### 2. Create and activate virtual environment

python3.12 -m venv .venv
source .venv/bin/activate

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

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/clients` | Create a new client |
| `GET` | `/api/v1/clients/{id}` | Get client by ID |

## Running Tests

```bash
pytest tests/ -v
```

Tests use SQLite in-memory database — no Docker required.

Expected output:
```
tests/test_client.py::test_create_client PASSED
tests/test_client.py::test_create_client_duplicate_email PASSED
tests/test_client.py::test_get_client PASSED
tests/test_client.py::test_get_client_not_found PASSED
tests/test_health.py::test_health_check PASSED

5 passed in 0.12s
```

## Daily Startup

```bash
docker start bankercrm-db
cd ~/Projects/bankercrm
source .venv/bin/activate
uvicorn app.main:app --reload
```
```