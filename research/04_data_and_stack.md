# 04 - Data sources and Build It stack (checked 2026-10-08)
Legend: VERIFIED = I hit it from this machine today. DOCS = from docs/search only. UNVERIFIED = not confirmed. Raw responses are in research/raw/04/.

## Part A - Data sources

### Air
| Source | Gives | Delhi coverage | Auth | Status / sample | Gotchas |
|---|---|---|---|---|---|
| Open-Meteo Air Quality | CAMS model PM2.5, PM10, NO2, O3, SO2, CO, dust, US/EU AQI; hourly, past_days + forecast | Gridded (~11 km), any lat/lon | None | VERIFIED. `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=28.61&longitude=77.21&current=pm2_5,pm10,us_aqi&timezone=Asia/Kolkata` returned PM2.5 60.1 at 2026-10-08 00:30. past_days works | Model, not station readings. Free for non-commercial use, ~10k calls/day |
| WAQI / aqicn | Station AQI + pollutants (CPCB/DPCC stations relayed) | Many Delhi stations | Free token, instant signup (aqicn.org/data-platform/token) | PARTIAL. `api.waqi.info/feed/delhi/?token=demo` returns 200 but the demo token resolved to Shanghai. `search/?keyword=Delhi&token=demo` returned other-city/stale rows. Delhi station data NOT verified | Attribution required. Use `feed/geo:28.6;77.2/` or `map/bounds` with a real token |
| OpenAQ v3 | Aggregated station measurements | Delhi has many stations | API key (free, signup at explore.openaq.org) | Endpoint alive: `api.openaq.org/v3/locations?coordinates=28.61,77.21&radius=25000` gives 401 without `X-API-Key`. Data not fetched | v1/v2 retired; v3 only. Rate-limited per key |
| NASA FIRMS | Active fire hotspots (VIIRS/MODIS), stubble burning | Bounding box Punjab/Haryana/Delhi | Free MAP_KEY (email based) | Endpoint alive; DEMO_KEY returned "Invalid MAP_KEY". Pattern: `https://firms.modaps.eosdis.nasa.gov/api/area/csv/<KEY>/VIIRS_SNPP_NRT/70,26,80,32/1` | Max 10 days per call. Key page: firms.modaps.eosdis.nasa.gov/api/map_key. Key speed UNVERIFIED |
| CPCB / data.gov.in realtime AQI | Official hourly station AQI | Delhi ~40 stations | data.gov.in API key | UNVERIFIED. data.gov.in homepage 200, but my API calls timed out. airquality.cpcb.gov.in/AQI_India/ gave 404; app.cpcbccr.com redirects (308) | Flaky; cache a snapshot for the demo |
| DPCC / SAFAR | Official Delhi / IITM data | Delhi | No public API found | UNVERIFIED. Skip | Scraping only |
| IQAir | City/station AQI | Delhi | Key | 403 without key | Free tier tight; skip |
| Google Air Quality API | 500 m AQI, heatmap tiles | Delhi | Google Cloud key + billing | Endpoint alive (needs key) | Billing needed, so avoid |
| Sentinel-5P | NO2/CO columns | Delhi | Copernicus account | DOCS only; heavy for 2 days | Skip |

### Heat and Water
| Source | Gives | Auth | Status / sample | Gotchas |
|---|---|---|---|---|
| Open-Meteo forecast | temp, apparent temp, humidity, precip, UV, forecast | None | VERIFIED `api.open-meteo.com/v1/forecast?latitude=28.61&longitude=77.21&current=temperature_2m,apparent_temperature&daily=temperature_2m_max,precipitation_sum&timezone=Asia/Kolkata` gave 24.6 C, feels 28.0 | ~10k calls/day free |
| Open-Meteo historical (ERA5) | Daily/hourly archive, heatwave baselines | None | VERIFIED `archive-api.open-meteo.com/v1/archive?latitude=28.61&longitude=77.21&start_date=2024-05-01&end_date=2024-05-03&daily=temperature_2m_max` gave 32.7, 35.0, 38.1 | ~9 km grid |
| Open-Meteo Flood (GloFAS) | River discharge forecast | None | VERIFIED `flood-api.open-meteo.com/v1/flood?latitude=28.66&longitude=77.23&daily=river_discharge` gave ~4.35 m3/s (coarse grid) | Trend only; not a gauge level |
| IMD | Warnings, nowcasts | No open API found | mausam.imd.gov.in returns 200 (site only). UNVERIFIED for API | Scraping/PDF |
| India-WRIS (CGWB) | Groundwater levels | Portal | indiawris.gov.in 200; no open API verified | Likely manual CSV |
| Delhi waterlogging hotspots | Lists in PDFs/news | n/a | No dataset found. Option: hand-curate hotspots or use OSM underpasses via Overpass | Do not claim an official dataset |
| DJB tanker/leak, Bhuvan | - | - | UNVERIFIED; no open API found | Synthetic/crowd data |

### Waste and Energy
| Source | Gives | Auth | Status / sample | Gotchas |
|---|---|---|---|---|
| PVGIS (EU JRC) | PV yield per kWp, works for India (ERA5 DB) | None | VERIFIED `re.jrc.ec.europa.eu/api/v5_3/PVcalc?lat=28.61&lon=77.21&peakpower=1&loss=14&outputformat=json` returned 5.2 KB JSON, radiation_db PVGIS-ERA5 | Best solar source. Add `optimalangles=1` |
| NREL PVWatts v8 | PV yield | DEMO_KEY | Call timed out; UNVERIFIED. India coverage uncertain | Use PVGIS |
| Global Solar Atlas | GHI/PVOUT maps | Site only | Site 200; no API tested | Use PVGIS |
| PM Surya Ghar | Subsidy rules | - | Not verified today (my recollection: Rs 30k/kW to 2 kW, +18k for 3rd kW, cap 78k) | Verify before use |
| OpenStreetMap / Overpass | EV chargers, recycling, waste, bus stops, underpasses | None | VERIFIED. `overpass-api.de/api/interpreter` POST returns 200 only with a User-Agent (plain curl got 406). Query `nwr["amenity"="charging_station"](28.4,76.8,28.9,77.4)` | Cache results before demo |
| Delhi Open Transit Data (otd.delhi.gov.in) | Static GTFS, GTFS-realtime, DMRC static | Realtime key by registration (speed UNVERIFIED) | Site 200; pages `/data/static`, `/data/staticDMRC`, `/data/realtime`, `/documentation`. Feeds not downloaded | IIIT-Delhi run; realtime is risky |
| Open Charge Map | EV chargers | Key | 403 without key | OSM instead |
| MCD waste, CPCB e-waste recyclers, data.gov.in waste | Ward waste, recyclers | data.gov.in key | UNVERIFIED (data.gov.in API timed out) | Hand-build a small CSV |

### Best 3 per track
- Air: Open-Meteo AQ (no key, verified), NASA FIRMS (free key), WAQI or OpenAQ v3 (free key).
- Heat and Water: Open-Meteo forecast + ERA5 (no key, verified), Open-Meteo Flood (no key, verified), OSM Overpass (no key).
- Waste and Energy: PVGIS (no key, verified), OSM Overpass (no key, verified with UA), Delhi OTD static GTFS (site alive, feed untested).

## Part B - Build It stack

Docker: `docker --version` = Docker 27.2.0 installed. WSL default distro is docker-desktop (WSL2). Daemon running state not checked.

### 1. Strands Agents SDK
- Python `strands-agents` 1.58.1 (GitHub release 2026-10-06; PyPI confirmed), Python >=3.10. TypeScript SDK v1.3.0 (2026-05-21). `strands-agents-tools` 0.8.9 (2026-09-15).
- PyPI extras confirm providers: anthropic, openai, gemini, litellm, ollama, mistral, llamaapi, sagemaker, writer, a2a, otel, cedar. Strands site states Ollama, OpenAI, Anthropic, Gemini, LiteLLM, MCP integration, and multi-agent via graph, swarm and agents-as-tools.
- README now promotes a new `strands-harness` package; the classic `strands-agents` still ships.
- Default provider is Bedrock (needs AWS), so pass an explicit model. Code below is from the documented API and NOT executed here:
```python
# pip install "strands-agents[openai]" strands-agents-tools   # or [ollama] [anthropic] [gemini]
from strands import Agent, tool
from strands.models.openai import OpenAIModel  # or strands.models.ollama.OllamaModel(host=..., model_id="llama3.1")
@tool
def get_aqi(lat: float, lon: float) -> dict: ...
agent = Agent(model=OpenAIModel(client_args={"api_key": "..."}, model_id="gpt-4o-mini"), tools=[get_aqi])
agent("Is it safe for kids to play outside in Dwarka?")
```

### 2. LocalStack (important change)
- From 2026-03-23 LocalStack ships ONE unified image requiring a LocalStack account and auth token, including CI (official blog localstack-single-image-next-steps, fetched). A free Hobby plan exists for non-commercial use (token required); students also get access via GitHub Student Developer Pack. docs.localstack.cloud/aws/licensing confirms.
- Hobby services per docs/search: S3, Lambda, DynamoDB, API Gateway, SQS, SNS, ~30 total; excludes Athena, EMR, EKS, RDS, Cognito. EventBridge and Step Functions: UNVERIFIED.
- Option: pin an older pre-March-2026 tag (no token, UNVERIFIED which tags still work).
- Windows: Docker Desktop + WSL2 supported per docs; not run here. Set `LOCALSTACK_AUTH_TOKEN`. Docs do not explicitly address hackathons.

### 3. SAM CLI
- v1.167.0 (2026-10-06). `sam local invoke` / `start-api` need Docker, no AWS account. Works with LocalStack by pointing endpoint URLs at it or via `samlocal`. Not run here. Lowest-risk AWS tool since it needs no token.

### 4. OpenSearch
- Core release line 3.x (GitHub listing showed v3.9.0 on 2026-09-29; treat as latest). Easiest run: official docker compose with opensearch + opensearch-dashboards (set `OPENSEARCH_INITIAL_ADMIN_PASSWORD`, ports 9200/5601). k-NN vectors, geo_point/geo_distance and time-series aggregations are standard features (my knowledge; the docs fetch was too generic to confirm). No token or AWS account needed.

### 5. Cedar
- cedar-policy-cli v4.13.0 (2026-09-15). Python `cedarpy` 4.12.1 on PyPI (2026-09-24); `pip install cedarpy` then `is_authorized`. Strands has a `cedar` extra. JS bindings UNVERIFIED.

### 6. PartyRock
- partyrock.aws returns 200. Free daily usage, no AWS account (Google/Amazon/Apple login), no card (AWS blog via search). No-code browser builder with no stable API found, so it works only as an add-on, not as a backend.

### 7. Finch
- v1.19.0 (2026-09-16). Windows supported: MSI, Windows 10 2004+ amd64, WSL2, `finch vm init`. Docker already present, so Finch is optional (visible `finch run` as a demo touch).

## Recommended architectures (2 days)

**A. Air Guardian (Air), safest.** Strands agent (Ollama or OpenAI/Gemini) with tools for Open-Meteo AQ, FIRMS upwind fires, WAQI. Cedar policy gates advice per persona (child, asthma patient, school admin). Visible AWS: Strands code, `sam local start-api` Lambda wrapping the tools, OpenSearch Dashboards over stored AQI time series. UI: Streamlit or Gradio chat plus folium map. No LocalStack token needed.

**B. Heat/Flood Sentinel (Heat and Water).** Ingest Open-Meteo forecast, ERA5 baseline, GloFAS and OSM underpasses into OpenSearch (geo_distance, k-NN RAG over past events). Strands multi-agent graph (risk analyst, advisory writer). LocalStack Lambda + DynamoDB + S3 store alerts. Demo shows `awslocal` commands and the Dashboards map. UI: Streamlit or a Telegram bot for alerts.

**C. Rooftop and Transit Nudger (Waste and Energy).** Strands agent calls PVGIS for kWp yield plus subsidy math, OSM EV chargers, OTD static GTFS for bus alternatives. LocalStack S3/DynamoDB hold profiles and reports (boto3 `endpoint_url`); SAM local Lambda behind API Gateway exposes the tools. UI: Gradio with a map.

Demo visibility: show `docker ps` with localstack/opensearch, `awslocal dynamodb scan`, `sam local start-api` logs, and Dashboards on screen.

## Unverified / flagged
Real FIRMS/OpenAQ/WAQI keys not obtained; data.gov.in and CPCB endpoints failed from here; PVWatts timed out; OTD feeds not downloaded; no Strands/LocalStack/SAM/OpenSearch code executed; LocalStack Hobby service list (EventBridge, Step Functions) unconfirmed; OpenSearch exact latest version uncertain.
