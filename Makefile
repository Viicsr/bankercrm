.PHONY: help install up down logs shell migrate test lint format build clean export-openapi api-reference

# Variables
COMPOSE = docker compose
COMPOSE_TEST = docker compose -f docker-compose.testing.yml

# Colores para output
GREEN  := \033[0;32m
YELLOW := \033[0;33m
NC     := \033[0m

help: ## Muestra este mensaje de ayuda
	@echo "$(GREEN)BankCRM — Comandos disponibles:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

# === ENTORNO LOCAL ===
install: ## Instala dependencias en el entorno virtual
	pip install -r requirements.txt
# === ENTORNO REMOTO ===
deploy-check: ## Verifica que el deploy de producción responde
	@echo "Checking production health..."
	@curl -sf https://bankercrm-production.up.railway.app/health | python3 -m json.tool
	@echo "Production is up"

# === DOCKER ===
up: ## Levanta la app + BD en Docker (desarrollo)
	$(COMPOSE) up --build -d
	@echo "$(GREEN) App disponible en http://localhost:8000$(NC)"

down: ## Para todos los contenedores
	$(COMPOSE) down

down-v: ## Para contenedores y borra volúmenes (resetea la BD)
	$(COMPOSE) down -v

logs: ## Muestra logs de la app en tiempo real
	$(COMPOSE) logs -f app

shell: ## Abre una shell dentro del contenedor de la app
	$(COMPOSE) exec app bash

rebuild: ## Reconstruye la imagen sin cache
	$(COMPOSE) build --no-cache
	$(COMPOSE) up -d

# === DOCUMENTACIÓN ===
export-openapi: ## Export OpenAPI schema to docs/openapi.json
	mkdir -p docs
	python scripts/export_openapi.py

docs-html: export-openapi ## Genera docs/api-reference.html desde el esquema OpenAPI
	docker run --rm \
		-v "$(CURDIR)/docs:/spec" \
		redocly/cli build-docs /spec/openapi.json -o /spec/api-reference.html
	@echo "$(GREEN) Referencia API generada en docs/api-reference.html$(NC)"
	@open docs/api-reference.html 2>/dev/null || xdg-open docs/api-reference.html 2>/dev/null || true
	
# === BASE DE DATOS ===
migrate: ## Aplica migraciones pendientes (local)
	alembic upgrade head

migrate-docker: ## Aplica migraciones dentro del contenedor
	$(COMPOSE) exec app alembic upgrade head

new-migration: ## Genera nueva migración (uso: make new-migration MSG="descripción")
	alembic revision --autogenerate -m "$(MSG)"

db-shell: ## Abre psql dentro del contenedor de BD
	$(COMPOSE) exec db psql -U vicsr -d bankercrm

# === TESTS ===
test-db-up: ## Levanta solo la BD de tests en Docker
	$(COMPOSE_TEST) up -d db-test
	@echo "$(GREEN)✅ Test DB disponible en localhost:5433$(NC)"

test-db-down: ## Para la BD de tests
	$(COMPOSE_TEST) down

test: ## Ejecuta los tests con cobertura (SQLite local)
	pytest tests/ -v --cov=app --cov-report=term-missing

test-postgres: ## Ejecuta tests contra PostgreSQL real (levanta BD de tests)
	$(MAKE) test-db-up
	sleep 3
	DATABASE_URL=postgresql+asyncpg://vicsr:testpass@localhost:5433/bankercrm_test \
		pytest tests/ -v --cov=app --cov-report=term-missing
	$(MAKE) test-db-down

# === CALIDAD DE CÓDIGO ===
lint: ## Ejecuta el linter ruff
	ruff check .

format: ## Formatea el código con ruff
	ruff format .

lint-fix: ## Corrige automáticamente los problemas de lint
	ruff check . --fix
	ruff format .

# === DOCKER IMAGE ===
build: ## Construye la imagen Docker de producción
	docker build --target runtime -t bankercrm:latest .

clean: ## Limpia contenedores, imágenes y cachés de Docker
	docker system prune -f
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -rf htmlcov/ .coverage coverage.xml