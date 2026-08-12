.PHONY: dev db migrate import test lint typecheck check hooks

dev:
	docker compose up --build

db:
	docker compose up -d db

migrate:
	cd backend && uv run alembic upgrade head

import:
	cd backend && uv run python -m app.importers.catalogue ../data/catalogue.csv

test:
	cd backend && uv run pytest
	cd frontend && npm test -- --run --passWithNoTests

lint:
	cd backend && uv run ruff check .
	cd frontend && npm run lint

typecheck:
	cd backend && uv run ty check

check: lint typecheck test

hooks:
	cd backend && uv run prek install --prepare-hooks
