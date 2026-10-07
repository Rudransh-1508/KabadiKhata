# Winning projects from hackathons on environment themes (research for Environmental Hacks, Oct 8-11 2026)

Compiled 2026-10-08. Verification tags: [V] = placement confirmed on an official/primary or institutional page I fetched; [S] = from a search-result snippet or secondary news only; [U] = unverified/self-claimed.

Limits of this research: Devpost returns HTTP 403 to automated fetches, so no Devpost winner galleries were read (only search snippets). LinkedIn was not accessed. GitHub repo search for "winner" + environment keywords returned very little. Google Solution Challenge Indian Top-10 lists could not be found. So the environment-track entries are weighted to Indian institutional press, government-run hackathons and AWS/WRI/IIT events. The most important finding is the full First Commit (Bharat Builds event 1) winner list with READMEs.

---

## 1. Synthesis

### 1a. What Bharat Builds Tour / First Commit judges actually rewarded (event 1, Sept 17-20 2026, Bangalore + online; 13,660+ registrants per a runner-up README)
Source: https://www.wemakedevs.org/aws/first-commit/projects (fetched). Event 2 (ours, Environmental Hacks) is Oct 8-11 with in-person build day Oct 10 in Delhi; First Commit was open-ended, ours is themed. Same five criteria: Idea & Impact, Built on AWS, Design & Usability, Execution, 3-min demo video.

Prize structure: Ship It (1st, Rs 2L + $3k credits; deployed live on AWS, architecture part of score), Build It (2nd, Rs 1.5L + $2k; local open-source AWS stack, no AWS account needed), Best UI (3rd, Rs 1L + $1k), 4 runner-ups ($1k each). Note: placement order = prize track, and "Build It" (local stack) took 2nd, so local-only is viable but live-deployed won 1st. A side prize exists for blog posts on AWS Builder Center (Best Blog).

Winners (all read from READMEs, see section 3 for details):
- 1st Ship It: Suraksha (agentic companion for aging parent). Hardware (Galaxy Watch) + voice (Transcribe/Polly, Hindi/Hinglish) + Bedrock Nova agents + Cedar consent policy enforced before every tool call + Step Functions escalation chain + DynamoDB memory + EventBridge proactive checks. Emotional, human story, "quiet by design", real AWS architecture diagram, build story doc.
- 2nd Build It: Beacon Night Shift (voice on-call agent). Solo builder. Strands agent + Step Functions DryRun->Approve->Execute->Verify, transcript as safety artifact, runs locally with `make local` in 2 minutes without AWS account (moto), CI badge, tests, 3-min demo cut, AWS Builder Center blog, Apache-2.0. Pure "engineering rigor + safety/approval gate" pitch.
- 3rd Best UI: CampusEvac (two-player browser fire evacuation drill: evacuee first-person, warden overhead; realtime sync; replayable audit). Winner on UI/novelty, not backend depth. Directly safety-adjacent (schools/campuses).
- Runner-ups: Magpie (finance workspace), FreshTrace (food spoilage / cold chain, ESP32 hardware + AWS IoT-style dashboard, S3-hosted), Expressive captions (voice agent video editing), Factcade (small-factory ops copilot, Strands + Nova Pro, deterministic loss maths + AI explains + owner approves).

Patterns visible in the First Commit winners (n=8, small sample, inference):
1. All top finalists used AWS agentic/AI stack in a real way (Bedrock Nova, Strands, Step Functions, Cedar, EventBridge, DynamoDB) and drew architecture diagrams. Cedar is explicitly in the judges' toolbox and the 1st-place winner used it for consent.
2. "Human in the loop / consent / approval" is a recurring design stance (Suraksha consent + ask-her-first; Beacon approve_fix checked against transcript; Factcade owner approves). Deterministic code decides actions, LLM explains/judges. Two READMEs state this rule verbatim ("AI never computes money", "the model decides language, code decides actions", "no silent LLM fallbacks").
3. Concrete named persona and quantified moment (Amma 72 in Bengaluru; 3 AM page; rupees lost per hour).
4. Hardware or physical-world element appeared in 2 of 8 (watch, ESP32) but wasn't required; 3 of the winners had polished live URLs plus a YouTube demo.
5. Solo and 3-4 person teams both won. Students from various colleges.
6. Real working demos with simulated history clearly labelled (Suraksha: "today is live", earlier history simulated and labelled).
7. Nobody won with a plain dashboard.

### 1b. Patterns from environment-track winners across other hackathons
- Government/institution-set problem statements reward end-to-end solutions with deployment path: FloodAI 2024 winner predicted flood probability + waterlogging depth + duration (3 outputs, "end-to-end").
- Predict, then tell a specific person what to do: WATCH 2024 1st (heatwave mitigation tool = AI forecast + public health alerts + geofencing); Hydro Harvest AI (location -> roof area -> 30yr rainfall -> tank size report) won Rs 1L from the Jal Shakti Minister.
- Hardware+IoT+app combos dominate SIH waste/water winners (SWACH smart waste hardware 2025; solar IoT segregating bin 2019; underwater floating-waste vehicle 2019; IoT e-waste Technovation 2020).
- Informal-sector/economic-linkage ideas win at design-oriented events (UNLEASH Hack India gold: informal waste pickers -> SHG -> brands/recyclers; EEDO e-waste app connecting producers to authorised recyclers; e-Parali machine rental + stubble collection for farmers).
- Accessible data + clear audience: ASDI hackathon runner-ups used Sentinel-2/Sentinel-5P satellite data with SageMaker, visual tools (waterbody monitoring from India).
- Emergency/disaster information aggregation also wins in government finals (SIH 2024 IIT Bhubaneswar nodal: "Matrix Infinity" real-time disaster information aggregation for NDRF).

### 1c. Overused ideas (judges have seen these a lot)
- Generic AQI dashboard / AQI prediction notebook / "app that shows AQI near you" (also AISEHack 2026 1st was "pollution prediction" - serious forecasting at a national finale, so a plain predictor will not stand out in a student hackathon).
- Smart dustbin with segregation (SIH 2019, 2025, Technovation 2020, SheHacks, RootHacks, TreeHacks MechaSort): image classification of trash plus IoT bin.
- Carbon-footprint tracker; green-points rewards for recycling (ARCH, Sustainable Data Miners at Unitec/AWS).
- Water-quality TDS sensor dashboards; rainfall-based flood predictor with a map.
- "Chatbot over a PDF" wrapper for policy documents (without a workflow/action).

### 1d. Under-served angles for a Delhi 2-day build (inference from gaps in what I found)
- Agentic action layer with consent/approval that uses Cedar + Strands (judges clearly like these): e.g. an agent that detects a bad-air or heat day and executes steps for a school/clinic/RWA (alerts to parents, switches class to indoor, logs decisions), with Cedar policies for who may be notified/overridden, Step Functions escalation, and an audit trail. First Commit's winner pattern (Suraksha) transfers directly.
- School safety on bad AQI days: no winner found that does it; CampusEvac shows safety-drill/gamified training got Best UI at event 1. A "bad-air-day drill/simulation + decision support for school principals" is an open lane.
- Monsoon waterlogging at street level in Delhi (underpasses, Minto Bridge etc.): FloodAI winner outputs (depth, duration) are the benchmark; add citizen reporting + routing for ambulances/commuters + tanker/pump dispatch agent.
- Informal sector linkage for e-waste/waste with WhatsApp/voice-first Hindi interface (UNLEASH, EEDO won on this idea; voice/Hindi was a big part of Suraksha's pitch).
- Heat: cool-roof / heat-risk by ward with health alerts has winners (UNESCO India-Africa 2022 cool roof; WATCH 2024), but nothing found that connects heat risk to worker/vendor schedules or ORS/water-point routing in Delhi.
- Water tanker/leak dispatch for DJB: nothing found among winners; Wave2Web (reservoirs, Bengaluru) and DWLR groundwater (SIH 2024 Jal Shakti, 2nd position) show institutions value predictive water work, but there is no Delhi tanker logistics winner in my results.
- Design guidance: Best UI went to a game/simulation, so even a weak-frontend team should invest in one polished flow and a 3-min video.

---

## 2. Entries by track (environment-related)

### AIR

1. AISEHack 2026 (ANRF with IIT Delhi, IBM, IIIT Hyderabad; final at IIIT Hyderabad; 2,100+ students) - 1st place, theme "Pollution Prediction" [V]
   - Team: Mohammad Saad Nathani, Kartik Soni, Pranav Mundhra, Meet Patel, Anushka Sharma (MPSTME Shirpur, B.Tech AI-ML).
   - Problem/solution: AI-based pollution prediction; method and stack not disclosed on the page.
   - Standout: serious national forecasting hackathon with IBM/IIT Delhi; shows the ML-forecast bar.
   - Link: https://engineering-shirpur.nmims.edu/mpstme-students-win-first-prize-at-aisehack-2026/

2. WATCH 2024 (Weather and Climate Hackathon, KISS Bhubaneswar, Sept 19-21 2024, 16 institutions, BCC/CUNY + US Consulates) - 1st prize, Team Heli-o-sphere (PCCOE Pune) [S: via a team member's LinkedIn profile snippet]
   - Project: AI-based heatwave mitigation tool integrating public health alerts and city-wide geofencing. (Themes were: precision farming, AI/ML for weather/air quality, air quality improvement, heat waves, surprise.)
   - Standout: connects forecast to health alerts + geofenced targeting (action, not dashboard).
   - Links: https://in.linkedin.com/in/suyash16 ; https://news.kiit.ac.in/kiitnews/weather-and-climate-hackathon-concludes-at-kiit/ (not read in full)

3. Celestini Program (Marconi Society), Delhi students - top spot, Air Cognizer [S, older, ~2018-19]
   - Team: Tanmay Srivastava, Kanishk Jeet, Prerna Khanna (Bharati Vidyapeeth College of Engineering, Delhi).
   - Solution: smartphone camera images to estimate AQI in NCR (no sensor needed); won a US award.
   - Link: https://swarajyamag.com/amp/story/insta%2Fneed-of-the-hour-delhi-students-develop-application-that-measures-air-quality-index-win-us-award-for-it ; https://gulfnews.com/world/asia/india/indian-students-develop-app-to-measure-air-quality-1.2298037
   - Note: image-based AQI is now a "seen it" idea.

4. Smart Delhi Ideathon 2025 (GGSIPU, AICTE IDEA Lab; grand finale at Vigyan Bhawan; themes: traffic, waste, air quality, women's safety; prizes Rs 5L/3L/1L) [V event exists; winners not found]
   - Useful as signal of what Delhi organisers consider important. Link: https://usar.acm.org/events/smart-delhi-ideathon

5. Global Challenge Lab 2022 (Imperial College London), 1st of 72 teams - e-Parali [V via University of Toronto news]
   - Team led by Satya Sathwik Juttada (U of Toronto) with international team.
   - Problem: rice straw burning (about 23 Mt emissions/yr). Solution: rental-sharing app for stubble-removal machines for farmers under 5 acres, plus connecting truck drivers who collect stubble for resale to paper/brick/biofuel buyers. Prize GBP 4,000.
   - Standout: marketplace framing around the farmer's economics, not a monitoring dashboard.
   - Link: https://news.engineering.utoronto.ca/app-for-empowering-farmers-in-india-propels-cheme-student-to-first-place-finish-at-international-hackathon/

6. Smart Cities hackathon Panaji, 2020 - winner "the third I" (IIIT Hyderabad), low-cost IoT indoor pollution monitoring [S]
   - Link: https://www.eeas.europa.eu/delegations/india/winner-panaji-masterclass-and-hackathon-smart-solutions-smart-cities-announced_en

7. Nature Hack For Clean Air (Clean Air Asia, HackerEarth, May-Jun 2020, 733 registrations) [U: winners not on fetched page]
   - Link: https://hackerearth.com/challenges/hackathon/nature-hack-for-clean-air/custom-tab/shortlisted-teams

### HEAT & WATER

8. FloodAI Hackathon 2024 (IIT Gandhinagar with IIT Bombay Climate Studies; 160+ applications, 55 selected, 11 teams; Aug 24-25) [S: IITGN news pages blocked to fetch; details from search snippet]
   - 1st (Rs 1L): Team Kappa (Hima Soni, Patel Yash, Manan Suri, Haran Shingala, Pranjal). Flood detection system: probability of flood, forecast of waterlogging depth, and how long it will last; end-to-end, seeking deployment.
   - 2nd (Rs 60k): Team Theta (Raviraj Dave, Mayank Kashyap, Mannat Gayal) - "FloodSense" city-vulnerability dashboard.
   - 3rd (Rs 40k): Team Epsion (Dhruv Sharma, Deep Mathukiya, Harsh Rajput, Prajas Kulkarni).
   - Standout: three concrete outputs (probability, depth, duration) vs generic risk map. A dashboard took 2nd, an end-to-end predictor took 1st.
   - Link: https://news.iitgn.ac.in/iit-gandhinagars-floodai-hackathon-2024-innovating-solutions-for-urban-flooding/

9. Jal Shakti Hackathon 2025 (central, award on World Water Day March 2026, Rs 1L) - Hydro Harvest AI, Shivakumar Induri (JNTU Hyderabad) [V via ETV Bharat]
   - Flow: GPS location -> rooftop area from satellite imagery -> 30 years of rainfall -> report with tank size and pipe diameter. Motivation: urban residents spending up to Rs 10,000 on tankers in summer. Validated against engineering designs in Hyderabad.
   - Standout: very concrete personal output (what tank to buy), solo student, ministerial award.
   - Link: https://www.etvbharat.com/amp/en/technology/rainwater-harvesting-system-with-a-jntu-student-develops-hydro-harvesting-ai-enn26032405752

10. Smart India Hackathon 2024 Software Edition - Team Neural Nex (SRMU Lucknow), 2nd position, Ministry of Jal Shakti problem statement: software for analysing Digital Water Level Recorder (DWLR) groundwater data [S: university news, page later 404; snippet only]
    - Team: Harshita Singh, Shrinjay Shresth, Kaustubh Pandey, Anushka Dixit, Mohd Tabish Khan, Arya Mishra.
    - Link: https://srmu.ac.in/news/team-neural-nex-innovating-water-tech-empowering-the-future1 (404 at fetch; found via search)

11. Wave2Web Hackathon (WRI India, Karnataka State Natural Disaster Monitoring Centre, Central Water Commission, Microsoft, BlackRock; 2,130 registrations) [V]
    - 1st: H2Ox (Oxford interdisciplinary group; focused on end-user applicability and customisation). 2nd: Aqrity (added semi-distributed hydrologic model). 3rd: Poseidon (self-updating model).
    - Task: forecast Bengaluru reservoir levels 1-3 months ahead via dashboards.
    - Standout: judged on end-user usefulness + hydrologic modelling credibility.
    - Link: https://wri-india.org/media/release-wri-india-announces-winners-wave2web-hackathon-aims-develop-predictive-models

12. 2022 Amazon Sustainability Data Initiative (ASDI) Global Hackathon (AWS) [V] - AWS-run, relevant to what AWS sustainability judges reward
    - 1st RAMADDA ASDI (interface to ASDI S3 datasets); 2nd Green Space Suggestion Tool (SageMaker, Sentinel-5P, Docker); 3rd Agri-able; 1st runner-up Waterbody Monitoring (Param Jeet, Jayanth Ajay, India; satellite moisture index, Sentinel-2); 2nd runner-up Indigenous Stewardship & Wildfire Reduction; honorable mention DataPlanet (OpenAQ air quality 3D Earth).
    - Standout: satellite/open datasets on AWS plus a usable tool; AWS-native data stack.
    - Link: https://aws.amazon.com/blogs/publicsector/announcing-winners-2022-amazon-sustainability-data-initiative-asdi-global-hackathon/

13. UNESCO India-Africa Hackathon 2022 - "Unstoppables" (Ashish Papanai, Utkarsha Nehe, Anushka Agarwal + Togo/Mali/Malawi members) won the cooling-rooftops problem statement [S]
    - Solution: PWA that segments rooftops (mean IoU 79.82 on INRIA dataset), computes area and reflectance to estimate electricity savings from cool/white roofs. Awards presented by VP Dhankhar and Education Minister Pradhan.
    - Link: https://cseindia.org/students-create-innovative-apps-at-hackathon-11539

14. SIH 2019 Hardware Edition grand finale [S]: Team Facile Fabricators (1st prize Rs 1L, Smart Cities): unmanned underwater vehicle collecting floating waste with water quality sensors; "Irreplaceable Dream Crushers": low-cost IoT TDS sensing + refiltering plug-and-play for home purifiers. Hyperion101010/monitor-water: water usage tool for Ministry of Water Resources, declared winner of the CGWA category at SIH 2019 finals [S, README-level claim; https://github.com/Hyperion101010/monitor-water].
    - Link: https://news.careers360.com/smart-india-hackathon-2019-hardware-edition-grand-finale-at-iit-delhi

15. SIH 2024 Software Edition, IIT Bhubaneswar nodal centre (Rs 1L each, problem statements from Godrej, NDRF, NCB, NALCO) [V] - winners include "Refrriranger" (sustainability/smart resource conservation, Godrej), and "Matrix Infinity" (Real-time Disaster Information Aggregation Software, NDRF).
    - Link: https://www.iitbbs.ac.in/wp-content/uploads/2025/01/Press-Release-Grand-Finale-of-Smart-India-Hackathon-comes-to-an-end.pdf (local copy: raw/02/sih2024_iitbbs.txt)
    - Other SIH 2024 winners seen: NIT Silchar (oil spill automatic identification), IIIT Nagpur (beach recreation suitability). Link: https://www.newsonair.gov.in/teams-from-across-india-shine-in-smart-india-hackathon-2024-winning-in-various-categories

### WASTE & ENERGY

16. SIH 2025 Grand Finale (LPU, Punjab municipal problem) - Team SWACH (SPCE Mumbai): AI and IoT hardware solution for intelligent waste management for Punjab municipal corporations [S: college PDF/news snippet]
    - Team: Ayushya Maurya, Shravani Kolekar, Vaishnavi Ratnaparkhi, Shah Sachin, Samarth Rasane, Agniva Pal.
    - Link: https://spce.ac.in/Documents/News&Events/SIH winners2026.pdf

17. SIH 2025, KIET Ghaziabad nodal centre, "Clean & Green Technology" theme - Team Si Extractors (Sethu Institute of Technology), "Real-life solutions for Waste Management", Rs 1.5L [V]
    - Link: https://university.careers360.com/articles/kiet-organised-valedictory-ceremony-of-the-grand-finale-of-smart-india-hackathon-2025

18. Technovation Hackathon 2.0 (Sharda University + GNIDA, Jan 25-26 2020, 650+ students) - grand winner (Rs 1L) IEC College of Engineering, Greater Noida: IoT-based e-waste solution; Smart Waste Management category winners MCR (GL Bajaj), Ctr Alt Elite (ABES), Waste Not Want Not (IMSUC) [V]
    - Link: https://www.voicendata.com/technovation-hackathon-2-0-sharda-university-gnida-witness-novel-hacks-smart-governance

19. Technovation Challenge 2018 - Team Cantavits (5 Indian school girls), EEDO app: end-to-end connection between e-waste producers and authorised recyclers; gold medal and $15k [S]
    - Link: https://yourstory.com/2018/09/india-cantavits-technovation-world-challenge

20. UNLEASH Hack India (Bharat) gold winner [S]: platform linking informal waste pickers in Darjeeling (organised into SHGs) directly with brands and recyclers to fix the finance model of plastic waste collection in mountains; removes aggregators.
    - Link: https://unleash.org/?p=6168

21. SIH 2019 [S]: Team Leo Survivors - solar-powered IoT garbage bin segregating biodegradable/non-biodegradable, mini decomposer, app for collection scheduling and dump-yard allocation. Link: https://blog.bitsathy.ac.in/bitians-hit-another-six-bagged-prizes-worth-rs-350000-in-smart-india-hackathon-2019
    SIH 2020 hardware/software qualifier: jcs98/HawkEye - mobile app analysing rooftop solar potential for ISRO, winner of college qualifier round only (weak placement) [U]. https://github.com/jcs98/HawkEye

22. India Solar Hackathon (New Energy Nexus, Devpost, 2016): Rs 3L prizes, Mytrah grand prize Rs 1.5L - winners not read (Devpost blocked) [U]. https://indiasolarhackathon.devpost.com/

### Non-India reference winners (global, mostly snippet-level)
23. Where's My Water! - 1st Place + Most Popular, UF Gator Hackathon: predicts the future of US groundwater using generative AI [S]. https://devpost.com/software/where-s-my-water-apgu2q
24. TreeHacks 2023 Sustainability: MechaSort (waste-sorting robotics for recycling facilities) [S]. https://devpost.com/software/looprrr and gallery link in search; unverified detail.
25. Unitec x AWS generative AI hackathon, 1st: Sustainable Data Miners - carbon footprint tracking for businesses [S]. https://www.unitec.ac.nz/hackathon-winners-using-ai-to-help-businesses-reduce-carbon-footprint/
26. Smaller GitHub-claimed wins (U, README claims): tristanduncombe/arch (ARCH recycling-bin finder, 2024 EAIT Sustainability Hackathon winner); jimmyzhng/BinIt (AI trash sorting, RootHacks); pyxyyy/shehacks (smart bin, SheHacks Boston); primo14/Toast-Dash-Hackathon (B2B organic waste brokerage for fungi recycling, 2025 winner); Talhahax/SolarScan (bill OCR -> solar ROI); Jithin-Jude/KeralaFloodEmergencyServiceSystem (ZealHack'19 winner).

### Bharat Builds Tour: First Commit winners (full list, details)
27. 1st Ship It, Suraksha, team StarBugs [V] - https://www.wemakedevs.org/aws/first-commit/projects ; code https://github.com/harshendram/firstcommit-hack ; live https://suraksha.d2dqtm6sqego9a.amplifyapp.com/ (see 1a).
    Stack: Next.js 15 on Amplify, Cognito, API Gateway, Lambda containers (FastAPI), Bedrock Nova 2 Lite agents + judge, Transcribe/Polly, DynamoDB single-table, EventBridge 1-min worker, Step Functions waitForTaskToken, Cedar ConsentGuard, CDK, Wear OS watch app.
28. 2nd Build It, Beacon Night Shift, solo [V] - https://github.com/Prashant-thakur77/Beacon ; demo https://youtu.be/a3SxZHvIkCo ; blog on AWS Builder Center.
    Stack: CloudWatch -> Lambda (Nova 2 Lite RCA), Strands agent with 7 tools, Transcribe/Polly, Step Functions remediation with dry-run/approval/verify, DynamoDB, S3+CloudFront, moto for local run, Python 3.12, CI.
29. 3rd Best UI, CampusEvac, team 3 BUILDS [V] - https://github.com/AfreenInnovates/campus ; demo https://youtu.be/FhgTfCz0ou8 ; live https://main.d3skpx6qxc85hh.amplifyapp.com/
    Two-player realtime browser fire-evacuation drill; Amplify-hosted; two channels (broadcast-only position, persisted lobby/commands), replay/audit.
30. Runner-up FreshTrace (Powerpuff Girls) - https://github.com/RakshitChaturvedi/FreshTrace (ESP32-S3 MOx gas sensor spoilage/cold chain, S3-hosted dashboard).
31. Runner-up Factcade - https://github.com/Alikhan207/Factcade (Amplify, API GW, Lambda, Bedrock Nova Pro via Strands, DynamoDB, EventBridge; rupees-lost-per-hour cascade, owner approves plan; falls back to rules and says so).
32. Runner-ups Magpie (finance workspace, https://github.com/akkki007/magpie) and Expressive captions (https://github.com/sept1st2c/Daks-caption_VoiceAgent-video-editing).

Also: AI for Bharat Hackathon 2026 (AWS + Hack2Skill + YourStory, about 96,000 registrations, 1,400+ prototypes, Rs 3L per winning team): student-track winners included Bimasathi (IIIT-Delhi team Rayquaza EX, WhatsApp-first multilingual voice insurance-claim assistant) and SocraticDev (Function Override) [S: YourStory article returned 403; details from search snippet]. Shows AWS-backed judges reward WhatsApp/voice/multilingual access-for-communities. https://yourstory.com/2026/06/crop-insurance-conversational-analytics-ai-for-bharat-hackathon

---

## 3. Raw material
READMEs of First Commit winners and the SIH 2024 press release are stored in C:\Users\HP\Desktop\DTU CSE\research\raw\02\ (untrusted data).
