# Environmental Hacks: Shortlist and Recommendation

Synthesised on 8 Oct 2026 from four research reports in this folder:
`01_problem_statements.md`, `02_winning_projects.md`, `03_delhi_pain_points.md`, `04_data_and_stack.md`.

Constraints: we build locally (Build It, with AWS open-source tools). The team is 4 people, strong in ML and backend and weak in frontend. We have 2 days. The focus is Delhi.

---

## What these judges reward
Evidence comes from the winners of First Commit (event 1 of the same tour), checked at wemakedevs.org/aws/first-commit/projects.
- **1st, Suraksha.** An agent with Cedar consent policies checked before every tool call, a human escalation step and Hindi voice.
- **2nd, Beacon Night Shift.** Built locally with a Strands agent and no AWS account. It had tests, a 3-minute demo and a Builder Center blog.
- **The pattern:** code decides and a human approves, while the LLM explains. The AWS architecture is central to the project. One named persona, one polished flow, and a prediction that leads to a concrete action.

Overused ideas to avoid: a plain AQI dashboard, a smart dustbin that classifies trash, a carbon tracker, a flood-risk map, a chatbot over a PDF.

---

## The four candidates

### A. Saans: a bad-air-day agent for Delhi schools (Air)  **RECOMMENDED**
**Problem.** GRAP measures are triggered by Delhi's city-wide average AQI. Two-thirds of Delhi has no reliable AQI reading: only 34.5% of the city's area is within 2 km of a monitor, and 22 of the 25 stations surveyed break siting norms (Newslaundry, 1 Dec 2025; CAG, Mar 2025). Schools have no per-school rule for outdoor PE, assembly or sports days. October is when it hits:
- The revised GRAP came into force on 29 Sep 2026.
- Stubble burning started around 5 Oct 2026.

**Validation.**
- The track text names "school safety on bad days".
- SIH 2026 **#26082** (MoES) asks for a 72-hour AQI forecast for Delhi NCR that accounts for stubble burning and winter inversion.
- SIH 2024 **#1616** (DPCC): fixed monitoring stations do not represent where people actually are.

**What it does**
1. **ML.** A per-school 72-hour PM2.5 forecast. Inputs:
   - Open-Meteo air-quality model data (no key needed)
   - the nearest station readings (WAQI or OpenAQ)
   - NASA FIRMS stubble fires upwind of Delhi
   - wind and boundary-layer weather
2. **Strands agent.** Turns the forecast into a plan for the day, such as "move assembly indoors", "cancel outdoor PE 2–4 pm", "reschedule Thursday's sports day" or "hybrid recommended".
3. **Cedar policy.** The agent can only recommend. The principal approves. Nobody can override a closure that GRAP mandates. Every decision is logged for audit.
4. **Parent notice.** Sent in Hindi and English through a Telegram bot or a WhatsApp-style message.

**AWS shown in the demo.** Strands, Cedar, SAM CLI local (the forecast Lambda and the notification API), and OpenSearch (station time series, nearest-school geo queries, and a Dashboards map).

**Risks.** This is likely the most crowded idea in the Air track, because it is Delhi in October and the track text names it. We beat that crowding with the per-school forecast and the approval-governed agent; "another AQI dashboard" would not.

### B. Kabadiwala Connect: scrap valuation and recycler matching (Waste and Energy)
**Problem.** The informal sector handles about 95% of e-waste (DEF report, Feb 2026). Seelampur is the hub. A DPCC inspection found widespread non-compliance among authorised EPR outlets.

**Validation.** SIH 2026 **#26229** (Ministry of Mines) is this exact problem statement. It asks for a low-literacy, offline-tolerant app with photo classification, price discovery and recycler matching. The track text names "informal recyclers".

**What it does.** A collector photographs scrap. The ML model identifies the material or e-waste type and estimates its value. The app matches the nearest authorised recycler (CPCB list plus OSM) and offers a Hindi voice flow.

**Risks.** The photo classification can look like the overused "trash classifier". The win depends on the persona and the usability for low-literacy users.

### C. Paani Pukar: DJB complaint aggregation and tanker demand (Heat and Water)
**Problem.**
- The CAG report (tabled 23 Mar 2026) found a 25.8% shortfall in potable water and 51–53% of supplied water unbilled (lost to leaks or theft).
- On X, residents post DJB complaints one at a time, again and again, with single-digit likes, and nobody aggregates them.

**What it does.** Complaints come in by Hindi voice or text. NLP classifies each one (no water, dirty water, leak, tanker no-show) and geocodes it to a colony. Complaints are clustered into outage incidents. The system drafts an evidence-backed escalation for each incident and forecasts tanker demand.

**Risks.**
- There is no official data. The demo would use scraped tweets plus synthetic complaints.
- It is less timely in October.
- Problem-statement validation is weaker (SIH #26255 only).

The upside is that no prior winners were found for this idea, so it is the most differentiated.

### D. Rooftop solar for Delhi homes and RWAs (Waste and Energy)
**Problem.** On 1 Sep 2026 the CM said rooftop solar "was not gaining sufficient momentum in Delhi", and only about 10,000 buildings have solar. The same day, the Cabinet approved a zero-upfront 3 kW scheme for about 2.3 lakh homes (target Mar 2027), and the portal launched in Sept 2026. This idea has the best "why now".

**What it does.**
1. The user draws their roof on a map.
2. PVGIS (no key needed) gives the expected yield.
3. The app checks eligibility (up to 400 units a month), shows savings in ₹ and works out a shared-roof plan for an RWA.
4. A Strands agent guides the user through the application checklist.

**Risks.** The ML depth is thin, and it can feel like a calculator. There is no validating problem statement from SIH.

---

## Scores (1–5 per criterion)

| | Idea and Impact | AWS centrality | Usability | Execution risk (5 = safe) | Demo appeal | Team fit (ML+backend) | Timeliness | **Total** |
|---|---|---|---|---|---|---|---|---|
| **A. Saans (schools)** | 5 | 5 | 4 | 4 | 5 | 5 | 5 | **33** |
| B. Kabadiwala Connect | 5 | 4 | 4 | 3 | 4 | 5 | 3 | 28 |
| C. Paani Pukar | 4 | 4 | 4 | 3 | 4 | 4 | 2 | 25 |
| D. Rooftop solar | 4 | 4 | 5 | 5 | 3 | 2 | 5 | 28 |

These scores are my judgement, not measured.

---

## Day 0: do now, whatever we pick
- [ ] **Every member** verifies their student status on AWS Builder Center. This is required to compete.
- [ ] Register free API keys: WAQI token, OpenAQ v3 key, NASA FIRMS MAP_KEY. Each takes a few minutes.
- [ ] Start Docker Desktop and check that `docker ps` works. SAM local and OpenSearch need it.
- [ ] Create the public repo now and have every member commit from day 1. The rules check repo history, so no dumping code at the end.
- [ ] Skip LocalStack unless needed. Since 23 Mar 2026 it needs an account and auth token (free Hobby plan). SAM CLI local needs neither.

## 2-day split for option A (4 people)
| Person | Day 1 | Day 2 |
|---|---|---|
| ML 1 | Data pipeline: Open-Meteo, WAQI/OpenAQ, FIRMS. Load into OpenSearch. | Forecast model: gradient boosting on lagged PM2.5, wind, fire count and hour. Backtest and write it up. |
| ML 2 / backend | Strands agent: tools (get_forecast, get_school, draft_plan, notify), with a Gemini/OpenAI/Ollama model | Cedar policies, approval flow, audit log, Hindi messages |
| Backend | SAM template: forecast Lambda, plan API, notify API. Seed data for about 15 Delhi schools. | Telegram bot, integration, tests |
| Frontend / PM | Streamlit principal console: map, 72-hour chart, approve or reject | Architecture diagram, README, 3-minute demo script and recording, Builder Center blog (top 5 blogs win AirPods) |

**Cut line if behind at the end of day 1:** drop the Telegram bot and FIRMS. Keep the forecast, the agent, the Cedar approval and the Streamlit console.
