export PYTHONPATH := src

# Settings and keys live in .env (copied from .env.example on first run)
ifneq (,$(wildcard .env))
include .env
export
endif

.PHONY: install test api seed demo tamper

install: .env
	uv sync --extra dev

.env:
	cp .env.example .env
	@echo "Created .env from .env.example (MOCK_LLM=1: no API key needed). Add keys there for the real LLM."

test:
	MOCK_LLM=1 uv run pytest -q

api:
	uv run uvicorn api.app:app --port 3000 --reload

# Rebuilds data/kk.db from data/synth/world.json (P1 generates it)
seed:
	uv run python -m ledger.seed

# Seeds, then starts every process in the Procfile in one terminal
demo: install seed
	uv run honcho start

# Video backup for the tamper demo: make tamper COLLECTOR=kw-raju SEQ=0 KG=40
tamper:
	uv run python -m ledger.tamper $(COLLECTOR) $(SEQ) $(KG)
