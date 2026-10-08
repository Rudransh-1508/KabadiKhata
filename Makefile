export PYTHONPATH := src

.PHONY: install test api seed demo

install:
	uv sync --extra dev

test:
	MOCK_LLM=1 uv run pytest -q

api:
	uv run uvicorn api.app:app --port 3000 --reload

# Rebuilds data/kk.db from data/synth/world.json (P1 generates it)
seed:
	uv run python -m ledger.seed

# Seeds, then starts every process in the Procfile in one terminal
demo: seed
	uv run honcho start
