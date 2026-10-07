# Delhi / NCR pain points — news + X research (written 2026-10-08)

Method note: news came from WebSearch snippets plus 3 page fetches. Search snippets sometimes mix years, so any figure not tied to a date below should be re-verified before it goes on a slide. For example, the "GRAP II since Oct 19" line in one result is from 2025, not 2026. Raw X data: `research/raw/03_x/*.json` (9 searches, about 490 tweets; analysis scripts live outside that folder). The X "top" results are noisy, with many viral off-topic tweets. The Delhi-specific ones are quoted below.

## Top 10 unsolved Delhi pain points (ranked)

| # | Pain point | Track | Who suffers | Evidence | Gap a software tool could fill | Oct 2026 timeliness |
|---|---|---|---|---|---|---|
| 1 | Two-thirds of Delhi has no reliable AQI reading; official monitors are badly sited and have data outages at peak times. People get one city-wide number, not their street's exposure. | Air | 21.8M residents, schools, outdoor workers | Strong (Newslaundry 1 Dec 2025, CAG Mar 2025) | ML hyperlocal AQI estimate (fuse CPCB/DPCC, satellite, weather, fires, traffic) with a personal exposure score and sensor-trust flags | Very high. GRAP revised 29 Sep 2026; smog season starts now |
| 2 | Schools and parents have no clear rule for outdoor play or hybrid classes on bad-air days. GRAP triggers on the city-wide average, and the October outdoor window is already squeezed (heat, rain, exams). | Air | Children, school admins | Medium (X: @sbgreen17 21 Sep 2026; GRAP hybrid-school rules reported 30 Sep 2026) | Per-school forecast and advisory (outdoor/indoor/mask), parent alerts, a school-level GRAP compliance checklist | Very high |
| 3 | Outdoor and informal workers have no enforceable heat protection. The Heat Action Plan names them but gives them no right to stop work, and heat deaths are undercounted. | Heat | Construction workers, vendors, delivery riders | Strong (The Leaflet HAP audit, May-Jul 2026: 70 workers, 17 sites; "92% of construction sites in heat zones"; heatwaves not notified under the DM Act as of 4 Aug 2026) | Heat-risk map by ward and site, shift-timing advisories, cooling-point finder, incident logging | Low for October (off-season), but good for a "design for next summer" pitch |
| 4 | Waterlogging is hotspot-fixated. Minto Bridge was fixed and heavily publicised, while other areas flood (Sadar Bazaar, Subroto Park, Connaught Place outer circle, IGI airport on 4 Sep 2026). Political fights and misinformation filled the gap. | Water | Commuters, low-lying colonies, underpass users | Strong (record 112.1 mm in 24 hrs on 1-2 Sep 2026, highest Sept day in 12 years; ANI posts, 8.7k-like thread on airport FIRs against 63 handles) | Flood-risk prediction per street (rain nowcast plus drain/topography data), citizen-reported waterlogging verified with imagery, a route-avoidance tool | Medium (monsoon withdrawing; a prototype can be demoed on the Sept data) |
| 5 | DJB supply is unreliable: a 25.8% potable-water shortfall, 51-53% non-revenue water, no flow meters. Residents depend on tankers whose schedules and fixed points are not transparent. | Water | About 20M residents, south Delhi and Vasant Vihar colonies, unauthorised colonies | Strong (CAG Report 3 of 2025, tabled 23 Mar 2026; X: tanker complaints Apr-May 2026, "short of 90 MGD", "tanker arrangements inadequate") | Complaint triage plus leak/outage detection (NLP on DJB/X complaints, clustering by area), tanker demand forecasting, public supply-gap dashboard | Medium-high. Yamuna ammonia alerts recur in the Oct-Nov season |
| 6 | Landfill and legacy waste: the Okhla (Jul 2026) and Bhalswa (Dec 2026) targets look hard to meet; Ghazipur has about 69 lakh MT left (28 Jun 2026) and is due Dec 2027. Fires and smoke continue. | Waste, Air | Neighbours of the sites, informal pickers | Medium-strong (Delhi government Air Pollution Mitigation Plan 2026 timelines; NGT proceedings Apr 2026) | Dashboard tracking promised vs actual bio-mining progress; satellite fire/heat anomaly detection at landfills | High. Winter smoke, and the Bhalswa deadline in December |
| 7 | Source segregation and bulk-generator compliance: MCD segregation is about 59% and only 63% of that is processed. 3,059 bulk generators were identified and 1,449 registered. 500+ dhalaos were still operating in Feb 2026. New SWM Rules 2026 (four-bin, digital tracking) start 1 Apr. | Waste | Waste pickers, residents, RWAs | Medium (snippet data, not re-verified; X: school-adjacent garbage spot, 4.7k likes, 22 Aug 2026) | RWA/bulk-generator compliance app with photo checks, a waste-classifier model, pickup routing, a pickers' marketplace | Medium |
| 8 | Informal recyclers: informal actors handle about 95% of e-waste. Seelampur dismantling is done without protection. A DPCC inspection of 83 authorised EPR outlets found widespread non-compliance. Authorised recyclers hold less than 10% of capacity. | Waste | Seelampur workers, kabadiwalas | Medium (DEF report Feb 2026, news reports) | Digital take-back and traceability platform linking households, kabadiwalas and authorised recyclers, with ML identification of items and value | Medium. Diwali electronics buying is coming |
| 9 | Rooftop solar in Delhi is stuck. The CM said in Sept 2026 that the scheme "was not gaining sufficient momentum in Delhi". Only about 10,000 buildings had solar. A zero-cost 3 kW scheme for about 2.3 lakh homes was approved on 1 Sep 2026 (target Mar 2027), and the registration portal launched in Sept. | Energy | Residents of flats and RWAs, DISCOM consumers | Strong (ANI 1 Sep 2026, India Plus 3 Sep 2026, Pioneer/KNN reports) | Roof-suitability scoring from satellite imagery, savings calculator, vendor matching and shared-roof RWA aggregation | Very high. The portal is brand new and demand is unserved |
| 10 | Bus reliability and last mile: drivers skip stops (route 356 STL, 13.8k likes, 9 Jun 2026), a contract-driver strike (15-16 Sep 2026) forced DMRC to scale up, and overcrowding. Fleet goals are 5,000+ e-buses now and 14,000 by 2029. | Energy / Transport | Commuters, women, students | Medium-strong (X; DMRC statement 16 Sep 2026) | Crowd-sourced bus reliability and missed-stop tracker, last-mile feeder planner, e-bus charging/demand analytics | Medium |

Honorable mentions: stubble-fire politics (Punjab fires have begun; CAQM flying squads in 34 districts until 30 Nov), and the Delhi Clean Air Action 2026 (10 interventions).

## A. Details by track

### Air
- **What is happening.** CAQM issued a revised GRAP on 29 Sep 2026. X posts of 30 Sep 2026 report 50% work-from-home and hybrid schools at higher stages (secondary reports; check the CAQM order). Delhi had its lowest September AQI in 5 years (monthly 102, per an X post of 1 Oct 2026), so the winter spike may land harder. Stubble burning started in Punjab around 5 Oct 2026 (ANI Tarn Taran video, 2.7k likes). CAQM has deployed flying squads (18 in Punjab, 16 in Haryana). The Delhi Clean Air Action 2026 has 10 interventions (CM, 29 Sep 2026).
- **Government already does.** GRAP stages, flying squads, cloud seeding. The 2025 trials with IIT Kanpur cost Rs 3.2 crore for five trials (Rs 64 lakh per run), and AQI was still poor the next day (275 on 29 Oct 2025). Also 46 CAAQMS after six new stations (Feb 2026 report).
- **Gap.**
  - Coverage: Newslaundry, 1 Dec 2025 — 38 stations (before the six new ones), only 34.5% of the area within 2 km of a station, 22 of 25 surveyed stations violate siting norms, and about 52 stations are needed. CAG (Mar-Apr 2025): the AQI is "unreliable" and none of the 24 DPCC stations measure lead.
  - Under-monitored zones: Bawana, Chhattarpur, the Yamuna floodplain.
  - School guidance is generic.
- **Sources.** [Newslaundry, 1 Dec 2025](https://www.newslaundry.com/2025/12/01/two-thirds-of-delhi-does-not-have-reliable-air-quality-data), [Newslaundry on CAG, 1 Apr 2025](https://www.newslaundry.com/2025/04/01/delhi-air-quality-data-unreliable-cag-report-confirms-newslaundry-probe), [Superkalam on 6 new stations, 10 Feb 2026](https://superkalam.com/current-affairs/10-02-2026/with-6-more-aqi-monitoring-stations-delhi-tops-all-cities-but-experts-wary-pg4-f34e6557-7f64-4956-b7fd-afb2a19cdfc9), [Outlook Business on cloud seeding](https://www.outlookbusiness.com/news/delhi-cloud-seeding-diwali-air-pollution). Stubble 2025 data: Punjab 4,062 fire events vs 6,266 in 2024 over 15 Sep-9 Nov (a 35% fall) and Haryana 333 vs 959, so the fall is a trend a model could use.

### Heat
- **What is happening.** The 2026 Heat Wave Action Plan covers 339 centres in 13 districts and over 30 hospitals with cool rooms (CM statement, 26 Apr 2026, [IANS](https://ianslive.in/heat-wave-action-plan-implemented-at-ground-level-across-delhi-cm-rekha-gupta--20260426142725)). Delhi Congress alleged that temperatures crossed 46 C and promised water ATMs, cooling points and revised work hours were not visible on the ground.
- **Gap.** [The Leaflet audit](https://theleaflet.in/governance-and-policy/auditing-delhis-heat-action-plan-a-ground-study-part-i) (May-Jul 2026):
  - The HAP 2026 text was not accessible.
  - Cooling zones were found only by ground canvassing.
  - Deaths are inconsistently counted across agencies.
  - Heatwaves are not notified as a disaster under the DM Act as of 4 Aug 2026.
  - There is no mechanism for workers to stop work.
- **X.** Top Delhi tweet, @IsmatAraa (3.8k likes, 17 May 2026), contrasts 18 C mall air-conditioning with vendors in 45 C and asks for outdoor cooling in public areas.

### Water and floods
- **Waterlogging.**
  - Rain: Delhi got 112.1 mm in 24 hrs on 1-2 Sep 2026, the highest September day in at least 12 years.
  - Airport: on 4 Sep 2026 the IGI airport was waterlogged. The operator filed an FIR against 63 handles for posts on it. 
  - Minto Bridge (now Shivaji Bridge): the PWD says the 2.5 km pipeline and extra drain worked. Kejriwal said the focus on Minto Bridge ignores flooding elsewhere (Pioneer, Telangana Today; July-Aug 2026).
  - Pre-monsoon: 200 teams deployed (Outlook).
  - Other flooded spots: Sadar Bazaar, Subroto Park (X, 4 Sep 2026), outer-circle Connaught Place.
  - Not found: casualty counts for 2026 (drowning or electrocution). I did not locate 2026 figures.
- **Supply.**
  - South Delhi (Green Park, Hauz Khas, Dakshinpuri, Gulmohar Park, South Ex) had irregular, low-pressure or contaminated supply in summer 2026 ([Sunday Guardian](https://sundayguardianlive.com/news/south-delhi-faces-worsening-water-crisis-210593/amp/)). DJB targeted 1,002 MGD with 6,290 tubewells and a 1916 helpline.
  - CAG (tabled 23 Mar 2026, audit period 2017-18 to 2021-22): potable shortfall 25.79%, NRW 51-53% (Rs 4,988 crore revenue loss), transmission losses up from 16% to 21%, no flow meters, 4 zones under 20 gallons per capita per day ([Pioneer](https://www.dailypioneer.com/news/20-million-lives-at-risk-cag-delivers-damning-verdict-on-delhis-worsening-water-crisis)). Note the audit period is old.
  - Groundwater: extraction about 101% of annual availability overall (snippet; undated). Yamuna ammonia often above 2.5 ppm against a 0.5 ppm limit, cutting Wazirabad and Chandrawal output by up to 50%. Verify dates.

### Waste
- **Landfills.** Okhla was targeted for Jul 2026, Bhalswa for Dec 2026, Ghazipur for Dec 2027. As of 28 Jun 2026, 67.57 lakh MT had been bio-mined at Ghazipur and about 69 lakh MT remained. In April 2026 the NGT gave MCD 4 weeks to examine a time-bound plan ([Punjab Kesari](https://english.punjabkesari.com/india/ngt-directs-mcd-to-submit-time-bound-plan-for-ghazipur-landfill/)). Fires are recurring (NGT suo motu). Claims of success on X (e.g. a post thanking the CM for clearing the "Kude ka pahad") are political and unverified.
- **Segregation.** MCD segregation is about 59% (63% of it processed). Targets are 85% by Feb 2026 and 90% by Aug 2026. 3,059 bulk generators identified, 1,449 registered on the 311 app. 5,756 registered waste pickers. 500+ dhalaos still active (Feb 2026). SWM Rules 2026 introduce four-bin segregation and digital tracking ([IMPRI](https://www.impriindia.com/insights/policy-update/solid-waste-management-rules-2026-examining-indias-implementation-readiness/)). These numbers come from search snippets and are not date-verified, so re-check them.
- **E-waste.** Informal sector handles about 95% (DEF report, Feb 2026; [PDF](https://www.defindia.org/wp-content/uploads/2026/02/Connecting-the-Unconnected-Inside-the-Invisible-E-waste-Economy-of-Delhi’s-Seelampur.pdf)). The Delhi government has planned three e-waste parks.

### Energy and transport
- **Solar.** The central subsidy is Rs 78,000 and Delhi adds Rs 30,000 (Rs 1.08 lakh total). On 1 Sep 2026 the Cabinet approved a zero-upfront scheme for 3 kW systems for households using up to 400 units per month (about 2.3 lakh homes, target Mar 2027, 500 MW). The portal launched in Sept. The CM admitted the scheme lacked momentum in Delhi. Vendor meets were held on 21 Sep 2026. Nationally 50 lakh households were covered and the pace is about 16,000 installs a day (Jul 2026).
- **EV and buses.** EV Policy 2.0 (effective 1 Jul 2026, valid to Mar 2030) covers e-buses (DTC and DIMTS to buy only electric), a 95% EV target, a CNG autorickshaw phase-out proposal and scrappage-linked incentives. Rs 300 crore was cleared for e-bus charging at 7 depots (22 Sep 2026). DTC runs 5,000+ e-buses.
- **Gap.** Reliability, missed stops, crowding, contract-driver labour issues, and first/last-mile access.

## B. X analysis

Scraper worked (logged in). The nine searches ran headless, 80 tweets max each, "top" mode:

| Query | Tweets | Date range of results |
|---|---|---|
| aqi_school | 3 | 21-30 Sep 2026 |
| aqi2 (AQI min_faves:30) | 21 | 15 Sep-7 Oct 2026 |
| waterlog | 80 | 8 Jul-29 Sep 2026 |
| tanker | 80 | 31 Mar-7 Oct 2026 |
| heat | 80 | 14 Apr-28 Jun 2026 |
| stubble | 80 | 28 Sep-7 Oct 2026 |
| garbage | 80 | 13 Mar-7 Oct 2026 |
| djb | 33 | mostly 2026 (one from 2018) |
| solar | 80 | 12 Jan-7 Oct 2026 |
| bus | 55 | 3 Jun-7 Oct 2026 |

I ran 9 searches, the first of which returned only 3 tweets. The result sets are noisy: viral tweets unrelated to Delhi (for example the Modi and ANI posts that matched on "water", and IAS and relationship posts in the tanker query) dominate by likes, so engagement-weighted ranking is not reliable here.

**Recurring themes**
1. Political blame dominates. The tweets about waterlogging, garbage, stubble, tankers and water were mostly AAP vs BJP, so there is little neutral signal. Many tags go to the CM (@gupta_rekha, @CMODelhi), @praveshwahi, and @MCD_Delhi.
2. Tagged authorities, by query. DJB complaints: @DelhiJalBoard (17), @CMODelhi (13), @gupta_rekha (13), @p_sahibsingh (10; the PWD/water minister), @MCD_Delhi (6), @ltgovdelhi (6). Garbage: @gupta_rekha (33), @CMODelhi (30), @praveshwahi (22), @MCD_Delhi (14). Heat: @IMD-type and national accounts (@ndmaindia, @moesgoi, @skymetweather). Buses: @dtchq_delhi (8), @delhipolice, @dtc_union. CAQM and DPCC were barely tagged, so the air complaints go through the CM and Grok instead.
3. DJB complaints are individual, repeated and unresolved: "no water for 5 days in Vasant Vihar" (@bainjal, 22 May 2026), "hazardous water supply for more than 2 months" in Mukherjee Nagar (@Swekshadaan, 8 Aug 2026, 4 likes), a damaged pipeline in Tara Nagar/Kakrola (@TNWA_DF, 19 Jul 2026). Engagement on these is tiny (single digits), which shows a real complaint-routing gap: people post but nobody aggregates.
4. Asks: outdoor cooling in public places, water ATMs and tankers, proper dhalao removal and garbage collection near schools, a stubble solution, reliable DTC stops.

**Representative tweets** (all Delhi-relevant, dates are 2026)
- Bus, 13.8k likes, 499k views, 9 Jun: "An empty DTC bus at 9 PM. Not because there are no passengers—hundreds were waiting at bus stops... The driver simply wouldn't stop. Route 356STL Dwarka Cluster Depot..." (@bhaumikgowande) https://x.com/bhaumikgowande/status/2064421650159047139
- Heat, 3.8k likes, 17 May: "Malls in Delhi have AC blasting at 18°C. The street vendor outside, selling water bottles, sits in 45°C..." (@IsmatAraa) https://x.com/IsmatAraa/status/2055879521388408941
- Garbage near schools, 4.7k likes, 22 Aug: social audit of two MCD schools and one government school; a big garbage spot outside a Delhi government school (@SauravDassss) https://x.com/SauravDassss/status/2091107737698734327
- Waterlogging, 7.6k likes, 4 Sep: waterlogging at IGI airport (@ANI) https://x.com/ANI/status/2095829442639892677
- Misinformation angle, 8.7k likes, 9 Sep: airport operator FIR against 63 social media handles over posts on airport flooding (@erbmjha) https://x.com/erbmjha/status/2097656271294107985
- Stubble, 4.9k likes, 5 Oct: "Stubble burning has already started in Punjab and will continue for the next few months. Then Diwali will be blamed..." (@Mrsinha) https://x.com/Mrsinha/status/2107134791544139780
- AQI sentiment, 1.4k likes, 26 Sep: "gonna enjoy... this delhi mausam for next 30-35 days before smoke engulfs us and we hit 600 on aqi charts" (@_Lazy_being) https://x.com/_Lazy_being/status/2103908672393101581
- Tanker, 149 likes, 28 May: "Delhi is facing a severe water crisis! The city is short of more than 90 million gallons of water every day... tanker arrangements are totally inadequate. Many fixed tanker points..." (@iamrakeshbansal) https://x.com/iamrakeshbansal/status/2059828880069034478
- Bus strike, 1.3k likes, 16 Sep: DTC private contract drivers on a second day of strike (@zoo_bear) https://x.com/zoo_bear/status/2100215916189372841
- Solar, 482 likes, 1 Sep: CM says the scheme "was not gaining sufficient momentum in Delhi" (@ANI) https://x.com/ANI/status/2094753973995786633

**Takeaways for building**
- Grievance data on X is sparse and tiny per issue, but it is real and unaggregated (water, garbage). An ML pipeline that scrapes and geocodes complaints, tags the right authority, and shows repeat offenders has a clear niche.
- Public attention to air quality spikes right now (stubble just started), and the CM launched Delhi Clean Air Action 2026, so air plus schools is the most timely story.
- Solar has fresh policy news (the 1 Sep decision and the Sept portal), which makes it a pitch with a concrete "why now".

## Caveats
- Several figures come from search snippets and could not be date-verified: segregation and bulk-generator counts, groundwater extraction, and the Yamuna ammonia alert (the "until November 1" line may be from a past year).
- The audit period in the CAG report is 2017-22, though it was tabled in Mar 2026.
- I did not find 2026 numbers on waterlogging casualties, 2026 heat deaths, 2026 stubble fire counts, or school closures. Check live sources (CPCB, CAQM, SAFAR) before quoting.
