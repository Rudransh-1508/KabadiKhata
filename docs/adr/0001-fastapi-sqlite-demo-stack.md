# FastAPI + SQLite runs the demo, not SAM + OpenSearch

The plan was SAM (`sam local start-api`) on an OpenSearch store, with a Fri 18:00 cutoff. We decided on Fri morning instead: the only machine that runs the full stack and records the video is an Apple Silicon Mac with 8 GB RAM, and OpenSearch (~1.5 GB) plus warm Lambda containers, the Telegram bot, the Streamlit console and screen recording do not fit. The API runs as FastAPI on SQLite. SAM stays in the repo as a real `template.yaml` (arm64) wrapping the collection handler, shown in the video through `sam local invoke`; Strands and Cedar carry the "Built on AWS" requirement.

## Considered Options
- **SAM on SQLite:** rejected. Each Lambda container gets its own read-only copy of the code directory, so they can't share one writable SQLite file cleanly.
- **Wait for the 18:00 cutoff:** rejected. It would spend the afternoon of a 2-day build proving something we already expected to fail on 8 GB.
