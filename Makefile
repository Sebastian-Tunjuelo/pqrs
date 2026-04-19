SHELL := /bin/bash

PYTHON ?= python3

.PHONY: up down seed test lint pull-model demo demo-full

up:
	docker compose up -d

down:
	docker compose down

pull-model:
	bash scripts/pull-ollama-model.sh

seed:
	@echo "Dim secretaría / territorio: data/seed/*.sql + migraciones warehouse (Alembic)."
	@echo "Banco Q&A: pip install -e ./contexts/banco_qa && desde la raíz del repo:"
	@echo "  DATABASE_URL=postgresql://pqrs:pqrs@localhost:5433/pqrs?sslmode=disable python -m banco_qa seed"

test:
	@echo "E2E API: levante pqrs-api (por defecto http://127.0.0.1:8080; use E2E_API_URL si cambia)."
	@$(PYTHON) -m pip install -q -e ./e2e
	@$(PYTHON) -m pytest ./e2e/tests -q -m e2e

lint:
	@bash scripts/lint.sh

demo: up
	@echo "=== Demo: 200 PQRS sintéticas (Postgres migrado + dim_secretaria + dim_territorio) ==="
	@$(PYTHON) -c "import psycopg" 2>/dev/null || $(PYTHON) -m pip install -q -r scripts/requirements-demo.txt
	@DATABASE_URL=$${DATABASE_URL:-postgresql://pqrs:pqrs@localhost:5433/pqrs?sslmode=disable} $(PYTHON) scripts/demo_seed_pqrs.py --purge

demo-full: demo pull-model
	@echo "Demo listo; modelo Ollama descargado si pull-model tuvo éxito."
