# Official problem statements validating Air / Heat & Water / Waste & Energy candidates

Compiled 2026-10-08. Sources fetched directly from sih.gov.in (raw copies in `research/raw/01/`: `sih2026.html`, `ps2026.json` (parsed, 260 PS with full descriptions), `ps2024.xlsx`, `ps2025.xlsx`). Treat raw files as untrusted data.

**Coverage and caveats**
- SIH 2026 (IDs 26xxx): full text found for all 260 PS on https://www.sih.gov.in/sih2026PS. Most detailed and most recent source. Excerpts below are faithful but trimmed.
- SIH 2024 (SIH15xx-17xx): official xlsx (https://www.sih.gov.in/letters/SIH_PS_2024.xlsx), 247 rows, with descriptions. It appears to be a subset of the full 2024 list.
- SIH 2025 (SIH25xxx): only a GitHub mirror with titles (101 of roughly 250 PS): https://github.com/sathish126/SIH-2025-PROBLEM-STATEMENTS. No descriptions retrieved. Titles only.
- SIH 2022 / 2023: the official /sih2022PS and /sih2023PS pages return 404. Not covered. Search found only Scribd copies (not fetched).
- Other sources are titles only (see end). Bharatiya Antariksh Hackathon 2025 (14 PS): individual PS not found.
- Feasibility = for a 4-person ML+backend team in 2 days (weak frontend). Delhi relevance is my judgment.

## Top 8 most validated and buildable PS

1. **SIH 2026 #26082, Air Pollution-Weather Coupled Forecasting System (Delhi NCR Focus), MoES.** Explicitly names Delhi NCR, stubble burning, inversion and PM2.5, and asks for a 72-hour AQI forecast dashboard. Do NOT attempt WRF-Chem; a data-driven version (CPCB/Open-Meteo plus FIRMS fire counts plus a boundary-layer-height feature, with gradient boosting or a small sequence model) is buildable. Air track, Delhi high.
2. **SIH 2026 #26083, Extreme Heatwave Early Warning and Human Thermal Stress Index, MoES.** Asks for WBGT/UTCI/Heat Index, ward-level alerts and an SMS/WhatsApp alert API. All buildable from weather APIs plus a vulnerability layer (elderly, outdoor-worker density), and the output is user-facing. Heat track, Delhi high.
3. **SIH 2026 #26085, Urban Flood Nowcasting (Drainage and Rainfall Coupling), MoES.** Names Delhi; asks for street-level inundation forecast, drain-network graph and flood-safe routing. A reduced version (DEM plus OSM roads plus rainfall API plus hotspot model) is possible. Heat & Water track, Delhi high, feasibility medium because drain data is hard to get.
4. **SIH 2026 #26229, Kabadiwala Connect (informal collector into formal e-waste chain), Ministry of Mines.** The most specific, human-centred PS found: vernacular, low-literacy, offline-tolerant app with photo-based material classification, price discovery, recycler matching and traceable handover. ML (image classifier, price estimator) and backend (ledger, matching) fit the team. Waste track, Delhi high, feasibility high; the frontend must be very simple.
5. **SIH 2024 SIH1734, Downscaling of Satellite-based Air Quality Map using AI/ML, ISRO.** Fine-resolution NO2 map from coarse satellite data using Python ML libraries. Pure ML. Air track, Delhi medium, feasibility medium (needs Sentinel-5P/TROPOMI access and gap handling).
6. **SIH 2024 SIH1616, capturing AQI values through mobile and other stations, Delhi Govt (DPCC / Dept of IT).** Real Delhi problem: fixed stations are unrepresentative (industrial or construction proximity). A software reframing (hyperlocal AQI interpolation or low-cost-sensor calibration validated against CPCB stations) is possible. Air track, Delhi high, feasibility medium; PS leans to hardware (drones).
7. **SIH 2026 #26124, AI-Powered Mobile Urban Intelligence Platform Using Public Transport Fleet, BEL.** Bus-camera detection of potholes and waterlogging. A YOLO model on public datasets plus a backend map aggregator is possible. Only loosely tied to the tracks. Delhi medium, feasibility medium.
8. **SIH 2024 SIH1624, AI model for electricity demand and peak projection for Delhi power system, Delhi SLDC/Delhi Transco.** Names Delhi's peaky load and the solar duck curve. Time-series forecasting on public Delhi SLDC data. Energy track. Delhi high, ML feasibility high, but the end user is a utility rather than residents.

Runners-up: SIH 2026 #26255 (Jal Jeevan tap functionality monitoring), #26234 (food-waste redistribution), #26077 (severe-weather nowcasting), SIH 2024 SIH1696 (groundwater level predictor), SIH1695 (DWLR anomaly detection).

---

## Track: AIR

| Source/Year | PS ID | Title | Issuing org | Delhi | Feasibility | Link |
|---|---|---|---|---|---|---|
| SIH 2026 | 26082 | Air Pollution-Weather Coupled Forecasting System (Delhi NCR Focus) | MoES | High | Med (simplified ML version: high) | https://www.sih.gov.in/sih2026PS |
| SIH 2024 | SIH1616 | Technological solutions for capturing AQI values through mobile and other forms of stations | Govt of NCT of Delhi (DPCC / Dept of IT) | High | Med | https://www.sih.gov.in/sih2024PS |
| SIH 2024 | SIH1734 | Downscaling of Satellite based air quality map using AI/ML | ISRO | Med | Med | https://www.sih.gov.in/sih2024PS |
| SIH 2026 | 26162 | AI-Based Detection and Classification of Industrial Fires and Persistent Thermal Sources (NASA FIRMS, OSM, satellite) | NTRO | Low-Med | Med-High (FIRMS is free) | https://www.sih.gov.in/sih2026PS |
| SIH 2026 | 26178 | AI-powered environmental monitoring network (floods, fires, pollution; edge AI) | Qualcomm | Low | Low (hardware) | https://www.sih.gov.in/sih2026PS |
| SIH 2026 | 26181 | AI Personal Health Companion: resilience during heat waves, floods, pollution events | Qualcomm | Med | Low-Med (on-device hardware framing) | https://www.sih.gov.in/sih2026PS |
| SIH 2026 | 26076 | Personalized homepage for the Mausam app (mentions AQI) | MoES | Med | High | https://www.sih.gov.in/sih2026PS |
| Mission LiFE hackathon (DPCC, Delhi; year not stated) | n/a | "Improving Air Quality" (one of 4 themes) | DPCC/RDPC Delhi | High | n/a (title only) | https://dpcc.delhi.gov.in/sites/default/files/inline-files/innovative-hackathon-on-mission-lifepdf-9763157407d692856f122da43216adbc.pdf |
| DPCC Innovation Challenge 2025 | n/a | Reduce PM2.5/PM10 from vehicles (BS-IV or below, BS-VI) and ambient air; Rs 5 lakh shortlisted, Rs 50 lakh final | DPCC | High | Low (mostly hardware) | https://theaarchnews.com/event-calendar/dpcc-innovation-challenge-air-pollution-2025/ (secondary source) |
| DDA Harit Manthan 2026 | n/a | Policy challenge "The Air We Share" (title only) | Delhi Development Authority | High | n/a | https://dda.gov.in/sites/default/files/notice/harit_manthan_2026.pdf |

**Excerpts**

- **26082 (MoES).** Background: "Traditional AQI forecasting models typically treat meteorology and pollution dispersion as separate entities. However, in highly polluted urban landscapes like Delhi NCR, there is a critical, dynamic feedback loop... During peak pollution seasons (such as the winter stubble-burning period), atmospheric inversion layers trap particulate matter close to the ground." Challenge: "build a high-resolution, coupled forecasting system specifically tailored for Delhi NCR that predicts AQI for the next 72 hours." Expected: WRF-Chem or similar coupled framework; two-way feedback between meteorology (temperature, wind, PBL height) and chemistry (PM2.5, PM10, O3, NOx); "a user-friendly, real-time dashboard displaying high-resolution AQI forecasts for Delhi NCR with a 72-hour outlook. Features that explicitly track atmospheric inversion strength and predict how stubble-burning plumes will disperse".
- **SIH1616 (Delhi Govt).** "DPCC is using different stations at fixed sites for measurement of AQI... These fixed stations suffered from various limitations and generally do not give representative values e.g. station located near an industrial area will give higher readings... a temporary construction site/activity near these fixed sites give higher pollution readings due to local reasons. The technological solutions may be required for capturing AQI values through mobile and other forms of stations. Drone would be one of the options..."
- **SIH1734 (ISRO).** "Develop an AI/ML model to generate fine spatial resolution air quality map from coarse resolution satellite data. It should utilise existing python-based ML libraries... validated with unseen independent data. Challenge: large satellite data having gaps under cloudy conditions... Desired Outcome: Fine resolution air quality map of NO2."
- **26162 (NTRO).** "Current satellite-based fire monitoring systems such as NASA FIRMS provide thermal anomaly detections but do not distinguish between industrial fires, gas flares, agricultural b[urning]..." The solution is an AI geospatial system that classifies thermal sources. Useful for separating stubble burning from industrial sources.

## Track: HEAT & WATER

| Source/Year | PS ID | Title | Issuing org | Delhi | Feasibility | Link |
|---|---|---|---|---|---|---|
| SIH 2026 | 26083 | Extreme Heatwave Early Warning and Human Thermal Stress Index | MoES | High | High | https://www.sih.gov.in/sih2026PS |
| SIH 2026 | 26085 | Urban Flood Nowcasting System (Drainage and Rainfall Coupling) | MoES | High (names Delhi) | Med | https://www.sih.gov.in/sih2026PS |
| SIH 2026 | 26071 | AI/ML heavy-rainfall Early Warning and Inundation Prediction (satellite, radar, NWP) | MoES | Med | Med | https://www.sih.gov.in/sih2026PS |
| SIH 2026 | 26077 | AI-Driven Hyper-Local Early Warning System for Severe Weather Nowcasting (2-6 hr) | MoES | Med | Med | https://www.sih.gov.in/sih2026PS |
| SIH 2026 | 26080 | Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts | MoES | Low-Med | Med-High | https://www.sih.gov.in/sih2026PS |
| SIH 2026 | 26068 | WeatherGPT: Conversational AI for weather forecasts, alerts, climate info (multilingual) | MoES | Med | High | https://www.sih.gov.in/sih2026PS |
| SIH 2026 | 26192 | Flash Flood Prediction System for Hilly Regions | MHA | Low | Med | https://www.sih.gov.in/sih2026PS |
| SIH 2026 | 26161 | Dam Break Inundation Modelling Using Hydrodynamic Modelling of any River | NTRO | Low | Med | https://www.sih.gov.in/sih2026PS |
| SIH 2026 | 26255 | AI/ML monitoring of Household Tap Connection functionality (Jal Jeevan Mission), alerts and village feedback | MoJS | Low (rural) | Med-High | https://www.sih.gov.in/sih2026PS |
| SIH 2026 | 26254 | Indigenous Leak Detection Sensor Systems for water supply pipelines | MoJS | Med | Low (hardware) | https://www.sih.gov.in/sih2026PS |
| SIH 2026 | 26240 | AI-Based Spring Revival and Recharge Planning for Tribal Areas | Ministry of Tribal Affairs | Low | Med | https://www.sih.gov.in/sih2026PS |
| SIH 2026 | 26051 | Software model for area-specific shelter thermal comfort (Ladakh focus) | DRDO | Low | Med | https://www.sih.gov.in/sih2026PS |
| SIH 2024 | SIH1619 | Online real-time survey and monitoring of water bodies in Delhi | Govt of NCT of Delhi (Dept of IT) | High | Med-High (satellite water-body mapping) | https://www.sih.gov.in/sih2024PS |
| SIH 2024 | SIH1696 | Software application, Ground Water Level Predictor | Central Ground Water Board | Med | High | https://www.sih.gov.in/sih2024PS |
| SIH 2024 | SIH1695 | Software for analysis of DWLR data, anomaly alarms | CGWB | Low-Med | High | https://www.sih.gov.in/sih2024PS |
| SIH 2024 | SIH1697 | AI chatbot for groundwater information | MoJS | Low-Med | High | https://www.sih.gov.in/sih2024PS |
| SIH 2024 | SIH1692 | Forecasting future water requirements and reservoir storage | DoWR / Central Water Commission | Low | Med | https://www.sih.gov.in/sih2024PS |
| SIH 2024 | SIH1694 | Real-time Ganga river water quality forecasting (AI DSS, satellite, IoT) | NMCG | Low-Med | Med | https://www.sih.gov.in/sih2024PS |
| SIH 2024 | SIH1650 | Early Warning System for Glacial Lake Outburst Floods | DGRE, DRDO | Low | Med | https://www.sih.gov.in/sih2024PS |
| SIH 2025 (title only) | SIH25065 | Application for on-spot assessment of Roof Top Rain Water Harvesting and artificial recharge potential | MoJS | Med-High | High | https://github.com/sathish126/SIH-2025-PROBLEM-STATEMENTS |
| SIH 2025 (title only) | SIH25068 | Real time Groundwater resource evaluation using DWLR data | MoJS | Med | High | same |
| SIH 2025 (title only) | SIH25085 | Non-revenue loss in water supply; water conservation awareness; wastewater reuse | Govt of Kerala | Low-Med | Med | same |
| SIH 2025 (title only) | SIH25001 | Early Warning for Water-Borne Diseases in Rural Northeast India | MDoNER | Low | Med | same |
| DDA Harit Manthan 2026 | n/a | Tech challenge "Making Every Drop Count" (title only) | DDA, Delhi | High | n/a | https://dda.gov.in/sites/default/files/notice/harit_manthan_2026.pdf |
| Mission LiFE hackathon (DPCC) | n/a | "Rejuvenating River Yamuna" (title only) | DPCC/RDPC | High | n/a | link above |

**Excerpts**

- **26083 (MoES).** Background: "traditional meteorological warnings rely almost exclusively on ambient dry-bulb temperature thresholds... standard forecasts ignore the deadly compounding effects of relative humidity, wind speed, and solar radiation... Current public health infrastructure lacks localized, impact-based forecasting that translates raw weather data into actual physiological risk." Challenge: shift from "what the weather will be" to "what the weather will do". Expected: compute a Human Thermal Stress Index (temperature, humidity, wind, radiation) linked to a Mortality Risk Index; WBGT, UTCI or Heat Index; integrate health and demographic data (elderly, outdoor worker density) to predict heat-induced mortality and hospitalisation spikes 3-5 days ahead; "A dynamic GIS-mapped dashboard providing color-coded, hyper-local alerts (Zone/Ward level)... An API capable of pushing automated SMS/WhatsApp regional alerts... heat action plans (opening cooling centers, adjusting power grids, shifting outdoor work hours)."
- **26085 (MoES).** Background: "Urban flooding in major Indian metros like Mumbai, Delhi, and Chennai has become an annual crisis... knowing how much rain will fall does not automatically translate into knowing where the streets will flood... municipal bodies lack real-time, street-level predictive systems." Challenge: "Urban Flood Nowcasting System (0-3 hour lead time) capable of predicting street-level inundation". Expected: fuse rainfall nowcasts with high-resolution DEM and a graph model of the stormwater drains (nodes as manholes or inlets, edges as pipes or canals); a web GIS dashboard with street-by-street water depth in cm; "an API utility that can interface with navigation maps to suggest flood-safe alternative routes for emergency services, public transit, and commuters".
- **26077 (MoES).** "Traditional physics-based NWP models often suffer from computational latency... a real-time, hyper-local early warning system capable of 'nowcasting' severe weather 2 to 6 hours before impact", using a spatiotemporal deep learning architecture for thunderstorms, cloudbursts and flash floods.
- **SIH1696 (CGWB).** "The software application is expected to analyse groundwater levels and factors impacting groundwater level like rainfall, hydrogeology, landuse, population, surface elevation... predict and forecast groundwater levels both in space and time. The application will be accessible to all." About 26,000 wells monitored.
- **SIH1695 (CGWB).** "CGWB will be monitoring 14,000 DWLRs by 2026... Analysing all the 14,000 wells will be an enormous task. Accordingly, a software application is proposed to analyse and flag anomalous data... raise alarms and send messages to the concerned officer and vendors."
- **SIH1619 (Delhi).** "Technological solution for real-time survey and monitoring of water bodies in Delhi is one of the critical areas for rejuvenation of these water bodies." The description is a single line.
- **26255 (MoJS).** "Develop a solution using AI and ML to monitor the functionality of FHTC in real time at both the Gram Panchayat and household levels... provide alerts on water quality issues, allow village members to give feedback through mobile devices, and automatically sync data with IMIS/Sujal Gaon IDs." Rural, not Delhi.

## Track: WASTE & ENERGY

| Source/Year | PS ID | Title | Issuing org | Delhi | Feasibility | Link |
|---|---|---|---|---|---|---|
| SIH 2026 | 26229 | Kabadiwala Connect: Bringing the Informal Collector into the Formal Recycling Chain | Ministry of Mines | High | High | https://www.sih.gov.in/sih2026PS |
| SIH 2026 | 26195 / 26212 | Student Innovation: waste segregation, disposal and sanitization system (software / hardware) | AICTE | Med | Med (vague PS, so the specific problem has to be ours) | https://www.sih.gov.in/sih2026PS |
| SIH 2026 | 26200 / 26217 | Student Innovation: manage and generate renewable/sustainable sources more efficiently | AICTE | Med | Med | https://www.sih.gov.in/sih2026PS |
| SIH 2026 | 26234 | AI Smart Food Waste Reduction and Redistribution Ecosystem for Institutional Kitchens | MoFPI | Med | High | https://www.sih.gov.in/sih2026PS |
| SIH 2026 | 26115 | Smart Mobile Medical-Waste Collection and Segregation System (Autodesk Fusion) | Autodesk | Low-Med | Low (product design) | https://www.sih.gov.in/sih2026PS |
| SIH 2026 | 26259 | Technical Solutions for Multi-Layer Plastic Management at PWMU/MRF level (rural dry waste, low-bandwidth software tools) | MoJS | Low | Med | https://www.sih.gov.in/sih2026PS |
| SIH 2026 | 26124 | AI Mobile Urban Intelligence Platform Using Public Transport Fleet | BEL | Med | Med | https://www.sih.gov.in/sih2026PS |
| SIH 2026 | 26138 | Quantum-Inspired Fuel Consumption Prediction and Green Fleet Optimization | Egreen Quanta | Med | Med | https://www.sih.gov.in/sih2026PS |
| SIH 2026 | 26061 | AI-Driven Smart Energy Management System for Polar Research Stations | MoES | Low | Med | https://www.sih.gov.in/sih2026PS |
| SIH 2024 | SIH1624 | AI model for electricity demand and peak projection for Delhi power system | Delhi SLDC / DTL | High | High (ML); end user is a utility | https://www.sih.gov.in/sih2024PS |
| SIH 2024 | SIH1612 | Automated Bus Scheduling and Route Management for Delhi Transport Corporation | Govt of NCT of Delhi (GGSIPU) | High | Med | https://www.sih.gov.in/sih2024PS |
| SIH 2024 | SIH1724 | Platform for inter-departmental cooperation in Indian cities | MoHUA Smart Cities Mission | Med | Med | https://www.sih.gov.in/sih2024PS |
| SIH 2024 | SIH1525 | Smart Resource Conservation (Energy and Water) in Home Appliances (software variant) | Godrej Appliances | Med | Med | https://www.sih.gov.in/sih2024PS |
| SIH 2024 | SIH1731 | SolarQuest: solar tracker controller (MATLAB/Simulink) | MathWorks | Low | Med (simulation) | https://www.sih.gov.in/sih2024PS |
| SIH 2024 | SIH1575 / SIH1572 / SIH1576 | Waste-to-energy / grid energy storage / carbon capture | Ministry of Power | Low | Low (hardware) | https://www.sih.gov.in/sih2024PS |
| SIH 2024 | SIH1751 / SIH1754 | Swachhta and LiFE dashboard; Digital BRSR platform for India Post | Ministry of Communication | Low | Med | https://www.sih.gov.in/sih2024PS |
| SIH 2025 (title only) | SIH25014 | Waste Segregation Monitoring System for Urban Local Bodies (hardware) | Govt of Punjab | Med | Low-Med | https://github.com/sathish126/SIH-2025-PROBLEM-STATEMENTS |
| SIH 2025 (title only) | SIH25046 | Smart Waste Segregation and Recycling System (hardware) | Govt of Odisha | Low | Low | same |
| SIH 2025 (title only) | SIH25060 | Real life solutions for Waste Management | MoSJE | Med | Med | same |
| SIH 2025 (title only) | SIH25031 | Crowdsourced Civic Issue Reporting and Resolution System | Govt of Jharkhand | Med | High | same |
| SIH 2025 (title only) | SIH25051 / SIH25064 | Renewable energy monitoring for microgrids; RE hosting capacity in distribution feeders | Odisha / Kerala | Low | Low-Med | same |
| Mission LiFE hackathon (DPCC) | n/a | "Strengthening Solid Waste Management Systems" and "Alternatives to Single Use Plastics" (titles only) | DPCC/RDPC Delhi | High | n/a | link above |

**Excerpts**

- **26229 (Ministry of Mines).** Background: "The overwhelming majority of India's end-of-life electronics is collected through informal scrap dealers, waste-pickers, and local aggregators due to their extensive last-mile reach and low collection costs. However, these informal collectors remain largely outside the formal recycling ecosystem. The E-Waste (Management) Rules, 2022 established a formal EPR framework... As a result, material... may undergo unsafe backyard processing such as open-air cable burning, acid leaching of printed circuit boards... The fundamental gap is not only technological but also informational and institutional. Informal collectors may not know the prevailing fair price of materials, which nearby recyclers are authorized, how to complete a compliant material handover". Problem: "Design and develop a vernacular, low-literacy, offline-tolerant mobile platform that enables informal scrap collectors to discover fair prices, connect directly with authorized recyclers, complete a documented and traceable handover... and receive payment. The platform should make the formal recycling channel an economically attractive and convenient option... rather than creating an additional compliance burden." Required parts: photograph, categorise and create digital lots (CRTs, LCD panels, PCBs, cables, batteries, motors, mixed plastics) with an instant value estimate; a price discovery dataset; a transaction and traceability dataset; an authorised recycler dataset with ranking; AI/ML features (material classification, value estimation and more; my extraction cut off the rest).
- **26234 (MoFPI).** Food waste in institutional kitchens: an AI-driven reduction and redistribution ecosystem (background cites the FAO figure that about one-third of food produced is wasted).
- **SIH1624 (Delhi SLDC).** "The load profile of power requirement in NCT of Delhi is highly peculiar... The peak load in Delhi touched 8300 MW this summer while the minimum load during winters goes as low as 2000 MW. The peak... occurs twice i.e. at about 15:30 hrs and again after 23:00 hrs... solar generation... lending a Duck-curve effect... uneven load growth in the city". Asks for an AI-based demand and peak projection model.
- **SIH1612 (DTC).** "DTC relies on manual methods for scheduling and planning... needs an automated software solution capable of handling both linked and unlinked duty scheduling... mapping all existing routes and highlighting overlaps with proposed new routes." An algorithmic and GIS problem.
- **26124 (BEL).** Turn public buses into "mobile urban sensing units": detect road defects, "missing road dividers, missing zebra crossings... waterlogging and other road hazards", and estimate vehicle density.

---

## Other sources checked

- **DPCC "Innovative Hackathon on Mission LiFE"** (Delhi govt PDF): 4 themes (Improving Air Quality; Rejuvenating River Yamuna; Alternatives to Single Use Plastics; Strengthening Solid Waste Management Systems). Titles only. The year is not stated in the PDF.
- **DPCC Innovation Challenge 2025** (air pollution, Rs 50 lakh): reported by a secondary news site; the primary page was not fetched.
- **DDA Harit Manthan 2026** (17-18 Apr 2026, with Udhmodya Foundation): tech PS "Measuring the Health and Performance of Public Green Spaces", "Making Public Green Spaces More Engaging and Accessible", "Making Every Drop Count"; policy PS "From Public Goods to Sustainable Assets", "Unlocking the Potential of Cities' Green Spaces", "The Air We Share". Titles only.
- **Bharatiya Antariksh Hackathon 2025** (ISRO, 14 PS, finale Aug 2025): the list is not on the pages found. NOT retrieved.
- **Not searched or found:** SIH 2022 and 2023 official lists, MoHUA Smart Cities challenges, IUDX, NITI/AIM, Kaggle/AIcrowd, Google/Microsoft India climate challenges. SIH 2023 Scribd copies exist, e.g. https://www.scribd.com/document/673663560/problemStatements (not fetched).

## Observations for track and problem selection

- The strongest official validation is SIH 2026 (current year): MoES issued three Delhi or urban PS (#26082 air, #26083 heat, #26085 flood) that read as near-ready specs with explicit deliverables. They are also large and vague, so the "small problem solved well" angle would be a narrow slice (for example, ward-level heat risk for a set of Delhi wards, or waterlogging hotspots at underpasses).
- #26229 Kabadiwala Connect is the most specific and user-centred PS, with named end users (informal scrap collectors) and a concrete app spec. Delhi has large informal e-waste clusters (for example Seelampur), though that is my background knowledge rather than from the PS.
- Hardware-only PS with strong relevance but not buildable by this team: #26254 leak detection sensors, SIH25014 waste segregation monitoring, DPCC Innovation Challenge (filters and absorbers).
