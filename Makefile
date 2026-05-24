# Developer shortcuts for installing, seeding, testing, and running the app.
# Author: Sarala Biswal

.PHONY: install seed dev-api dev-ui test lint docker-up demo clean

install:
	uv sync --extra dev
	cd ui && npm install

seed:
	uv run python -m seed_data.generator

dev-api:
	uv run uvicorn api.main:app --reload --port 9100

dev-ui:
	cd ui && npm run dev

test:
	uv run pytest -q --cov --cov-fail-under=80

lint:
	uv run ruff check .
	uv run mypy api tracking quality costs drift

docker-up:
	docker compose up --build

demo: seed
	@echo "Start the API with: make dev-api"
	@echo "Start the UI with:  make dev-ui"
	@echo "Dashboard URL:     http://localhost:5173"

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -f observability.db
