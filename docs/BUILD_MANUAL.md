# Build Manual for the NER Hazard-Aware Logistics Prototype
**SIH26002 · Transportation & Logistics · Team Git Pirates**

## Executive Summary
A working demo that a judge can drive with their own hands in eight minutes. Not a product. Nine modules, in build order, with the parts that are safe to fake marked clearly.
- **9** modules
- **3** services in compose
- **1** corridor for the demo (NH-6 Guwahati → Shillong → Silchar, ~350 km)
- **0** live SAR processing

The whole product in one picture: **A road graph whose edge weights move with the weather.**

---

## Module Breakdown

### MOD 0: Scope, and the things you must refuse to build
- **Hazard-aware routing**: Build fully (interactive core demo).
- **Risk scoring + alerts**: Build fully (feeds routing; explains itself on screen).
- **Offline PWA**: Build fully (huge differentiator for NER; demo by turning off wifi).
- **Trucker services + SOS**: Build thin (real map layer + working SOS payload; bay availability from seeded data).
- **Analytics for planning**: Build thin (one heatmap + one chart from historical table).
- **InSAR landslide precursors**: Pre-compute, don't run live (Sentinel-1 interferometry is a multi-week pipeline).
- **Cut list**: User accounts & JWT auth (use fake header-based driver ID), payments, native Android app, real-time GPS fleet tracking, admin CRUD screens, chatbot, Kubernetes, complex multilingual UI beyond a simple toggle.
- **Pin the geography**: NH-6 Guwahati → Shillong → Silchar (~350 km), bounding box `(N 26.60, S 24.70, E 93.30, W 90.90)`.

### MOD 1: Data Acquisition
- **Static sources**:
  - Road network: OSM corridor extract for bbox.
  - Elevation/slope: SRTM 30m / DEM slope calculation for segments.
  - Landslide susceptibility: GSI / Bhuvan NRSC landslide inventory layers.
  - Rainfall climatology: Open-Meteo ERA5 archive.
  - Historical blockades: Hand-compiled CSV from news + PIB releases (date, lat, lon, type, road_ref, duration_hours, source_url).
  - Truck bays / facilities: OSM tags + NH-6 bays GeoJSON.
- **Live sources & fetch discipline**:
  - Open-Meteo API hourly forecast/archive sampled every ~10 km.
  - Cached in database; API handlers never make synchronous external calls.

### MOD 2: Database Schema
- Six tables:
  1. `segment`
  2. `weather_obs`
  3. `incident`
  4. `segment_risk`
  5. `facility`
  6. `report`

### MOD 3: Building the Road Graph
- Routable NetworkX graph where edges carry terrain attributes (`mean_slope_deg`, `length_m`, `speed_kph`, `susceptibility`).
- Loaded into memory at FastAPI startup in the lifespan handler.

### MOD 4: Risk Scoring Engine
- **Layer A (Transparent Hazard Index)**:
  - $Factors = \text{rain}(0.34) + \text{slope}(0.22) + \text{susceptibility}(0.18) + \text{history}(0.16) + \text{reports}(0.10)$
  - IMD heavy rainfall threshold: 10–120 mm/24h.
  - Himalayan slope threshold: 8°–35°.
  - Bands: Safe (<34), Caution (34–61), Hazard (>=62).
- **Layer B (Learned Adjustment)**:
  - Incident-trained classifier adjustment nudging transparent score by at most $\pm 15$ points.
- Background recompute loop writing updated `segment_risk` records.

### MOD 5: Hazard-Aware Routing
- Profiles: `fastest` ($\alpha = 0.0$), `balanced` ($\alpha = 1.2$), `safest` ($\alpha = 4.0$).
- Cost function: $w = base\_min \times (1 + \alpha \times r^2)$. Hard exclude if $r \ge 0.92$.
- Response contains full explanation: deltas, geometry, segment factors, and deterministic advisories.

### MOD 6: Landslide Precursors
- Pre-computed Sentinel-1 deformation raster/polygon overlay (`displacement_mm_per_year`).
- Time-series anomaly detector (rolling z-score over displacement + 72h antecedent rainfall).

### MOD 7: FastAPI Backend
- Lifespan pattern loading graph and model into memory.
- 12 Endpoints covering routing, risk, facilities, reports, analytics, and offline batch sync.

### MOD 8: Web Client
- 4 Screens: Route Planning, Corridor Risk Monitor, Truck Bays & Stops, Driver Reports & SOS.
- Interactive 5-factor breakdown panel when tapping hazardous segments.

### MOD 9: Offline PWA, SOS, and Truck Bays
- Service worker precaching and IndexedDB offline bundle.
- 2-second hold-to-fire SOS with sound tone and visible queue confirmation.
- Diurnal truck bay availability simulation.
