export PYTHONPATH := src

# Settings and keys live in .env (copied from .env.example on first run)
ifneq (,$(wildcard .env))
include .env
export
endif

.PHONY: install test api seed demo tamper sam-invoke up down reindex bot console smoke lambda-deps

install: .env
	uv sync --extra dev --extra product

.env:
	cp .env.example .env
	@echo "Created .env from .env.example (MOCK_LLM=1: no API key needed). Add keys there for the real LLM."

test:
	MOCK_LLM=1 uv run pytest -q

api:
	uv run uvicorn api.app:app --port 3000 --reload

# The bot talks to the real API here (its own default is the mock)
bot:
	KK_USE_MOCK=0 uv run python -m bot.telegram_bot

console:
	KK_USE_MOCK=0 uv run streamlit run console/app.py --server.headless true --server.port 8501

# Rebuilds data/kk.db from data/synth/world.json (P1 generates it)
seed:
	uv run python -m ledger.seed

# OpenSearch for the read-only search copy. Optional: everything else works without it.
up:
	docker compose up -d --wait

down:
	docker compose down

reindex:
	uv run python -m search.reindex

# Seeds, then starts every process in the Procfile in one terminal.
# The leading "-" on up: no Docker means no search copy, not a failed demo.
demo: install
	-$(MAKE) up
	$(MAKE) seed
	uv run honcho start

# Checks every endpoint and the 4 spine beats against a running `make demo`.
# Smoke decides a flag and adds a test kabadiwala, so it re-seeds afterwards to keep the demo pristine.
smoke:
	uv run python scripts/smoke.py; status=$$?; $(MAKE) -s seed > /dev/null; exit $$status

# Video backup for the tamper demo: make tamper COLLECTOR=kw-raju SEQ=0 KG=40
tamper:
	uv run python -m ledger.tamper $(COLLECTOR) $(SEQ) $(KG)

# Lambda dependencies: pinned from uv.lock and cross-installed for Linux arm64 on the host.
# (Downloading them inside the SAM build container took 30+ minutes; Docker's network is ~40x slower here.)
lambda-deps:
	rm -rf .aws-sam-deps && mkdir -p .aws-sam-deps/layer
	uv export --frozen --no-hashes --no-dev --no-emit-project --no-header --quiet > .aws-sam-deps/requirements.txt
	uv pip install --quiet --target .aws-sam-deps/layer/python --python-platform aarch64-manylinux2014 \
		--python-version 3.12 --only-binary :all: -r .aws-sam-deps/requirements.txt

# The "Built on AWS" clip: build the API as an arm64 Lambda and invoke it with a collection event.
# --env-vars pins the Lambda's settings; otherwise sam local copies matching values from .env (exported above).
sam-invoke: lambda-deps
	sam build
	sam local invoke KabadiKhataApi --event events/collection.json --env-vars events/lambda-env.json
	sam local invoke KabadiKhataApi --event events/brand-reads-receipts.json --env-vars events/lambda-env.json

# Runs every attack against the real code and writes docs/redteam_scorecard.md (offline, ~15 s)
.PHONY: redteam
redteam:
	MOCK_LLM=1 uv run python -m agent.redteam --md docs/redteam_scorecard.md

# New web front end on http://localhost:8600 (another port: make web WEB_PORT=8633); needs `make api` running
.PHONY: web
web:
	uv run uvicorn web.server:app --port $(or $(WEB_PORT),8600)
