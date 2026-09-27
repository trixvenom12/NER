# Comprehensive Code & Architecture Explanation
## PS SIH26002: AI-Based Smart Logistics and Accessibility Intelligence Platform for North Eastern Region (NER)
### Developed by Team Git Pirates

---

## 1. System Overview & Architectural Paradigm

The NER Logistics Intelligence Platform is designed to solve critical supply chain vulnerabilities along the primary lifeline corridor of Northeast India: **National Highway 6 (NH-6)**, spanning roughly **350 km** from **Guwahati (Assam) through Shillong and Jowai (Meghalaya) to Silchar (Barak Valley, Assam)**.

The core paradigm of this system is:
> **"A road graph whose edge weights move dynamically with the weather, terrain slope, geological susceptibility, and satellite precursors."**

Rather than relying on generic shortest-distance algorithms or opaque black-box deep learning, the platform employs an **explainable, dual-layer architecture**:
1. **Transparent Physical Index (Layer A)**: A citable multi-factor weighted hazard model based on India Meteorological Department (IMD) rainfall thresholds and Geological Survey of India (GSI) slope mechanics.
2. **Learned Correction (Layer B)**: A machine learning model trained on 5 years of historical blockades that nudges the transparent score by at most $\pm 15$ points.
3. **Hazard-Aware Dijkstra Routing**: Uses a single risk parameter $\alpha$ to produce three distinct route profiles (`fastest`, `balanced`, `safest`) with non-linear (squared) risk penalties.
4. **Offline-First PWA**: Guarantees that truckers and disaster authorities can plan routes, view advisories, and file incident/SOS reports in deep mountain shadow zones with zero network connectivity.

---

## 2. NER — Full Tech Stack & Architectural Specification

### 1. Frontend
- **React.js** — Web application and dashboards
- **MapLibre GL JS** — Interactive maps, routes and hazard layers
- **Tailwind CSS** — UI styling and responsive design

### 2. Backend
- **Python** — Core backend, data processing and ML
- **FastAPI** — REST APIs and communication between frontend, ML, GIS and database

### 3. AI / Machine Learning
- **Scikit-learn** — Machine-learning pipeline and risk analysis
- **XGBoost** — Risk-model adjustment/prediction
- **Transparent Risk Index** — Combines rainfall, slope, susceptibility, historical incidents and driver reports

### 4. GIS & Routing
- **OpenStreetMap (OSM)** — Road-network data
- **OSMnx** — Extracts and builds the road graph
- **NetworkX** — Graph-based route optimization
- **PostGIS** — Spatial/geographic database operations
- **PostgreSQL** — Main database
- **pysheds** — Terrain and hydrological analysis

### 5. Terrain & Environmental Data
- **SRTM DEM** — Elevation and slope
- **Sentinel-1 SAR** — Satellite/environmental monitoring
- **GSI / Bhuvan** — Landslide susceptibility data
- **IMD / Open-Meteo** — Rainfall and weather data
- **CWC** — Flood/water-level information
- **Historical incident data** — Previous landslides, floods and blockades
- **Driver reports** — Real-time ground-level road information

### 6. Routing Engine

The system supports:

- **Fastest Route** — Minimum travel time
- **Balanced Route** — Time + risk
- **Safest Route** — Minimum risk
- **Blocked-road exclusion** — Confirmed blocked/high-risk segments are avoided

```text
Road Network
     ↓
Risk Score per Segment
     ↓
Risk-Weighted Graph
     ↓
NetworkX Routing
     ↓
Fastest / Balanced / Safest
```

### 7. Offline-First / PWA

- **Progressive Web App (PWA)** — Application that can operate with poor connectivity
- **Service Workers** — Cache application resources
- **IndexedDB** — Store corridor maps, routes, risk data and pending reports locally
- **Background Sync API** — Synchronize reports/SOS when connectivity returns
- **Offline Outbox** — Queues driver reports and SOS requests

```text
Internet Available
       ↓
Download Corridor Data
       ↓
IndexedDB
       ↓
Network Lost
       ↓
Continue Using Cached Data
       ↓
Network Returns
       ↓
Background Sync
       ↓
FastAPI
       ↓
Database
```

### 8. APIs / Services

- `/route` — Route calculation
- `/risk` — Road-risk information
- `/facilities` — Truck bays, food, fuel and medical facilities
- `/reports` — Driver road-condition reports
- `/sos` — Emergency SOS
- `/analytics` — Historical data and heatmaps
- `/sync` — Offline-data synchronization

### 9. Database

**PostgreSQL + PostGIS**

Stores:

- Road network
- Geographic coordinates
- Hazard zones
- Risk scores
- Historical incidents
- Driver reports
- Truck/facility information
- Offline synchronization data

### 10. Deployment

- **Docker**
- **Docker Compose**
- **Cloud VM deployment**

Container structure:

```text
Docker Compose
│
├── React + MapLibre
├── FastAPI
├── ML/Risk Engine
├── PostgreSQL
└── PostGIS
```

### Complete Architecture

```text
IMD / Open-Meteo ─┐
SRTM ─────────────┤
Sentinel-1 ───────┤
CWC ──────────────┤
GSI/Bhuvan ───────┤
OSM ──────────────┤
Historical Data ──┤
Driver Reports ───┘
        ↓
PostgreSQL + PostGIS
        ↓
┌─────────────────────────┐
│ GIS / Terrain Processing│
│ OSMnx + pysheds         │
└────────────┬────────────┘
             ↓
┌─────────────────────────┐
│ Risk Engine             │
│ Risk Index + XGBoost    │
└────────────┬────────────┘
             ↓
┌─────────────────────────┐
│ Routing Engine          │
│ NetworkX                │
│ Fastest / Balanced /    │
│ Safest                  │
└────────────┬────────────┘
             ↓
          FastAPI
             ↓
┌─────────────────────────┐
│ React + MapLibre GL JS  │
└────────────┬────────────┘
             ↓
┌─────────────────────────┐
│ Offline PWA             │
│ Service Worker          │
│ IndexedDB               │
│ Background Sync         │
└─────────────────────────┘
```

The prototype manual specifically describes this architecture around **OSM/OSMnx/NetworkX routing, PostGIS, the transparent risk index + XGBoost adjustment, FastAPI, React/MapLibre, and the offline PWA stack**.

---

## 3. File & Directory Structure

```
c:/Google Antigravity Files/SIH 2026 Project/
├── AGENTS.md                  # Authoritative rules, constraints, and tech stack
├── SCOPE.md                   # Module 0 contract: 3 deep pillars, 3 thin surfaces, cut list
├── CODE_EXPLANATION.md        # Comprehensive technical documentation (this file)
├── data/
│   ├── schema.sql             # SQL DDL for PostgreSQL 16 + PostGIS 3.4 & SQLite
│   ├── ner_logistics.db       # Local high-speed SQLite database with 6 core tables
│   ├── incidents.csv          # Real, cited historical blockades on NH-6 (2021-2026)
│   ├── facilities.geojson     # Highway truck bays, fuel stops, weighbridges, and refuges
│   ├── weather_seed.json      # 10km sampled rainfall and visibility observations
│   ├── segments_seed.json     # Road segments database seed
│   ├── precursor_deformation.geojson # Pre-computed Sentinel-1 InSAR surface deformation
│   └── graph/
│       └── ner_drive.graphml  # Serialized NetworkX GraphML road network
├── build/
│   ├── build_graph.py         # Constructs road network, calculates slopes, exports GraphML
│   └── seed_data.py           # Offline database seeder running in < 2 seconds
├── models/
│   └── risk_model.joblib      # Serialized scikit-learn risk adjustment model
├── api/
│   ├── main.py                # FastAPI app with lifespan loader and static file mount
│   ├── database.py            # SQLite / PostgreSQL connection and table initializer
│   ├── deps.py                # Dependency providers (graph handle, risk cache, rate limiter)
│   ├── schemas/
│   │   └── schemas.py         # Pydantic v2 request and response data models
│   ├── services/
│   │   ├── risk_engine.py      # Dual-layer hazard index and ML adjustment engine
│   │   ├── routing_engine.py   # Hazard-aware routing with alpha profiles and squared penalties
│   │   ├── advisories.py       # Deterministic template-based driver warning generator
│   │   ├── precursor_engine.py # InSAR rolling z-score anomaly detector
│   │   ├── weather_service.py  # Open-Meteo corridor weather ingestion with offline cache
│   │   └── occupancy_service.py# Diurnal truck bay occupancy prediction model
│   └── routers/
│       ├── routes.py          # POST /api/route, GET /api/route/alternatives, POST /api/route/simulate-hazard
│       ├── risk.py            # GET /api/risk/segments, GET /api/risk/heatmap
│       ├── facilities.py      # GET /api/facilities, GET /api/facilities/{id}/availability
│       ├── reports.py         # POST /api/reports, POST /api/reports/sos, GET /api/reports/nearby
│       ├── analytics.py       # GET /api/analytics/hotspots, GET /api/analytics/seasonal
│       ├── sync.py            # POST /api/sync/batch (idempotent offline queue drain)
│       └── precursor.py       # GET /api/precursor/alerts, GET /api/precursor/deformation
├── web/
│   ├── index.html             # Responsive HTML5 UI with MapLibre GL map and 4 tabs
│   ├── style.css              # Dark slate glassmorphism design tokens & micro-animations
│   ├── app.js                 # MapLibre controller, 2s hold SOS, factor drawer, IndexedDB sync
│   ├── sw.js                  # PWA service worker with app shell precaching
│   └── manifest.json          # PWA web manifest
└── tests/
    └── test_all_modules.py    # Complete automated verification suite
```

---

## 3. Detailed Function & Feature Documentation

### 3.1 Database & Schema (`api/database.py`, `data/schema.sql`)

The database strictly implements the 6 core tables specified in the Build Manual:

1. **`segment`**:
   - `id` (INTEGER PRIMARY KEY): Unique identifier for directed road segments.
   - `osm_way_id` (BIGINT): Corresponding OpenStreetMap way identifier.
   - `u_node`, `v_node` (BIGINT): Origin and destination graph node IDs.
   - `road_ref` (TEXT): Highway designation (e.g. `'NH-6'`, `'Shillong-Bypass'`).
   - `highway` (TEXT): Road classification (`'trunk'`, `'primary'`, `'secondary'`).
   - `length_m` (REAL): Segment distance in meters.
   - `free_speed_kph` (INTEGER): Default uninhibited speed limit (30-60 km/h).
   - `mean_slope_deg` (REAL): Average gradient in degrees calculated from elevation topography.
   - `susceptibility` (REAL): Baseline GSI geological hazard rating [0.0..1.0].
   - `geom_geojson` (TEXT): GeoJSON LineString geometry string.

2. **`weather_obs`**:
   - Stores rolling hourly weather records sampled every ~10-15 km along NH-6.
   - Fields: `point_id`, `ts`, `rain_mm`, `rain_24h_mm`, `visibility_m`, `lat`, `lon`.

3. **`incident`**:
   - The credibility layer: Hand-compiled records from official PIB and regional news archives for NH-6 (2021-2026).
   - Fields: `occurred_on`, `kind` (`landslide`, `flood`, `blockade`, `waterlogging`), `duration_hours`, `source_url`, `lat`, `lon`.

4. **`segment_risk`**:
   - Written by the Risk Engine and read by the Routing Engine.
   - Fields: `segment_id`, `computed_at`, `score` (0..100), `band` (`safe`, `caution`, `hazard`), `factors` (JSON blob containing normalized breakdown).

5. **`facility`**:
   - Highway freight infrastructure: Ri-Bhoi truck bays, Byrnihat parking, Nongpoh oasis, Mawryngkneng terminal, Jowai bypass bay, Ladrymbai weighbridge, Sonapur emergency shelter, Silchar ISBT.
   - Fields: `id`, `name`, `kind`, `capacity`, `attrs` (JSON), `lat`, `lon`.

6. **`report`**:
   - Driver crowdsourced reports and emergency SOS distress calls.
   - Fields: `id`, `created_at`, `device_id`, `kind`, `note`, `confirmed_count`, `lat`, `lon`.

#### Functions in `api/database.py`:
- `get_connection()`: Opens SQLite connection with thread-safety and row factory enabled.
- `init_db()`: Executes SQL DDL to create all 6 tables and indexes if not already present.

---

### 3.2 Graph Construction & Road Geometry (`build/build_graph.py`)

#### Purpose:
Generates the routable graph representation of the NH-6 corridor connecting Guwahati, Shillong, Jowai, Khliehriat, Sonapur, and Silchar, including the **Shillong Bypass** and the **Sonapur Mountain Ridge Detour**.

#### Functions in `build/build_graph.py`:
- `haversine_m(lat1, lon1, lat2, lon2) -> float`:
  - **Inputs**: Coordinates of two geographic points in decimal degrees.
  - **Logic**: Uses the spherical Haversine formula with Earth's radius $R = 6,371,000$ meters.
  - **Returns**: Great-circle distance in meters.
- `build_graph() -> nx.MultiDiGraph`:
  - **Logic**:
    1. Iterates over 28 defined corridor waypoints (nodes) with elevation profiles.
    2. Builds bidirectional road segments, applying a 1.18 winding factor for mountain curves.
    3. Calculates terrain slope: $\theta = \arctan(\Delta Z / \Delta S)$.
    4. Calibrates ghat sections to citable slope literature: Sonapur Tunnel cutting ($\ge 31.5^\circ$), escarpment ridges ($\ge 24.0^\circ$).
    5. Serializes to `data/graph/ner_drive.graphml` and dumps `data/segments_seed.json`.

---

### 3.3 Risk Scoring Engine (`api/services/risk_engine.py`)

#### Dual-Layer Mathematical Formulation:

#### Layer A — Transparent Hazard Index:
$$\text{RawScore} = \sum_{k} W_k \times F_k$$
Where the weights $W$ are:
- **Rainfall Past 24h ($W_{rain} = 0.34$)**: Normalized between $10\text{ mm}$ (light) and $120\text{ mm}$ (IMD heavy rainfall warning boundary).
- **Slope Gradient ($W_{slope} = 0.22$)**: Normalized between $8^\circ$ (gentle) and $35^\circ$ (Himalayan foothills angle-of-repose shear boundary).
- **Geological Susceptibility ($W_{susc} = 0.18$)**: Lithological shear vulnerability [0.0..1.0] from GSI / Bhuvan landslide inventory.
- **Historical Recurrence ($W_{history} = 0.16$)**: Normalized incident count within 2 km radius [0..6].
- **Crowd Ground Truth ($W_{reports} = 0.10$)**: Normalized verified driver reports within last 4 hours [0..3].

**Official Risk Bands:**
- $\text{Score} < 34.0 \implies \mathbf{Safe}$ (`#3F7A55`, Green)
- $34.0 \le \text{Score} < 62.0 \implies \mathbf{Caution}$ (`#B8862A`, Amber)
- $\text{Score} \ge 62.0 \implies \mathbf{Hazard}$ (`#A33A28`, Red)

#### Layer B — Learned ML Adjustment:
A gradient-boosted classifier (`GradientBoostingClassifier`) trained on historical incident features, month, and 72-hour antecedent rainfall nudges the transparent score by at most $\pm 15$ points:
$$\text{Score}_{\text{final}} = \text{clamp}\left(0.0, 100.0, \text{Score}_{\text{base}} + (P_{\text{model}} - 0.5) \times 30.0\right)$$
*Why this design?* If the ML model fails or receives zero data, it outputs $P=0.5$, which makes the adjustment $0.0$, guaranteeing the demo can never break.

#### Functions in `api/services/risk_engine.py`:
- `norm(x, lo, hi) -> float`: Clamps and scales input to range $[0.0, 1.0]$.
- `score_segment_transparent(seg, wx_rain_24h, hist_count, active_reports) -> tuple[float, dict]`: Computes Layer A score and returns factor breakdown.
- `get_band(score) -> str`: Maps score to `'safe'`, `'caution'`, or `'hazard'`.
- `RiskEngine._load_or_train_model()`: Loads `models/risk_model.joblib` or trains a new model with cross-validation reporting AUC.
- `RiskEngine.score(...) -> tuple[float, str, dict]`: Full dual-layer evaluation returning final score, band, and transparent factors object.

---

### 3.4 Hazard-Aware Routing Engine (`api/services/routing_engine.py`)

#### Mathematical Routing Model:
The system maps "safest / balanced / fastest" to a single risk aversion parameter $\alpha$:
- **Fastest**: $\alpha = 0.0$ (Travel time minimization only)
- **Balanced**: $\alpha = 1.2$ (Standard commercial transit balance)
- **Safest**: $\alpha = 4.0$ (Strict hazard aversion for hazardous materials/tankers)

#### Edge Cost Function:
$$\text{BaseMinutes} = \frac{\text{Length (m)}}{1000 \times \max(\text{Speed (km/h)}, 5)} \times 60$$
$$r = \frac{\text{RiskScore}}{100.0}$$
$$\text{Weight} = \begin{cases} 
\text{None} & \text{if } r \ge 0.92 \quad \text{(Hard exclusion: road blocked)} \\
\text{BaseMinutes} \times (1 + \alpha \times r^2) & \text{otherwise}
\end{cases}$$

*Why squared risk?* Squaring $r$ ensures mildly damp roads ($r = 0.2 \implies r^2 = 0.04$) are barely penalized, while dangerous ghat sectors ($r = 0.8 \implies r^2 = 0.64$) receive heavy penalties that force diversions.

#### Functions in `api/services/routing_engine.py`:
- `edge_cost(alpha, risk_by_seg) -> weight_function`: Returns closure suitable for `networkx.shortest_path`. Returns `None` for blocked segments so NetworkX removes the edge without mutating the graph.
- `_get_best_edge(G, u, v, w_fn)`: Correctly extracts edge attribute dictionary whether graph is `DiGraph` or `MultiDiGraph`.
- `route_single(G, src, dst, profile, risk_by_seg, facilities) -> dict`: Computes shortest path via Dijkstra, calculates total distance, driving time, mean hazard, maximum peak hazard, extracts LineString coordinates, and generates driver advisories.
- `route_all_alternatives(G, src, dst, risk_by_seg, facilities) -> dict`: Concurrently evaluates fastest, balanced, and safest profiles, computing explicit time and distance deltas (e.g. $+18\text{ min}$ for safer route).

---

### 3.5 Deterministic Driver Advisories (`api/services/advisories.py`)

#### Purpose:
Generates citable, human-readable warnings for drivers along their planned route without invoking heavy LLMs.

#### Functions in `api/services/advisories.py`:
- `generate_advisories(segments, cumulative_kms, facilities) -> list[dict]`:
  1. Inspects segments with score $\ge 34.0$ (`caution` or `hazard`).
  2. Identifies the dominant factor contributing to risk (Rain, Slope, Susceptibility, History, or Crowd Report).
  3. Formats deterministic advisory templates with precise chainage km.
  4. Identifies highway truck bays and emergency medical havens within $5\text{ km}$ of the route.
  5. De-duplicates repeated warnings within $15\text{ km}$.

---

### 3.6 InSAR Satellite Precursor Engine (`api/services/precursor_engine.py`)

#### Purpose:
Pre-computes Sentinel-1 DInSAR surface deformation rates (mm/year) over critical escarpments (Sonapur Tunnel, Kseh Bilat) and runs a real-time time-series anomaly detector.

#### Mathematical Anomaly Formulation:
Rolling z-score across ground displacement magnitude:
$$\mu = \frac{1}{W} \sum_{j=0}^{W-1} s_{i-j}, \quad \sigma = \sqrt{\frac{1}{W} \sum_{j=0}^{W-1} (s_{i-j} - \mu)^2} + \epsilon$$
$$z = \frac{s_i - \mu}{\sigma}$$
- If $z > 1.8$ and $\text{Rain}_{72h} > 80\text{ mm} \implies \mathbf{HIGH\ ALERT}$ (Imminent slope failure)
- If $z > 1.8$ and $\text{Rain}_{72h} \le 80\text{ mm} \implies \mathbf{WATCH\ ALERT}$ (Accelerating creep)

#### Functions in `api/services/precursor_engine.py`:
- `rolling_z(series, window) -> np.ndarray`: Computes moving window z-score with numerical stability $\epsilon = 10^{-6}$.
- `detect_precursor_alerts(disp, rain) -> list[dict]`: Returns time-stamped alerts with z-score and recommended action.
- `PrecursorService.get_deformation_geojson()`: Returns Sentinel-1 polygon overlay for MapLibre rendering.
- `PrecursorService.get_all_alerts()`: Scans all monitored slope sites and returns active alerts.

---

### 3.7 Diurnal Truck Bay Occupancy Model (`api/services/occupancy_service.py`)

#### Purpose:
Simulates realistic commercial vehicle parking occupancy along NH-6 without inventing fake live sensor numbers.

#### Mathematical Formulation:
Uses a diurnal circadian wave reflecting long-haul trucking rest rhythms on the Guwahati-Silchar route:
$$\text{Wave} = 0.60 + 0.28 \times \sin\left(\text{radians}\left((\text{Hour}_{\text{IST}} - 18) \times 15\right)\right)$$
- **Peak Rest (01:00 - 04:00 IST)**: $\sim 85-95\%$ capacity utilized.
- **Midday Departure (08:00 - 11:00 IST)**: $\sim 30-45\%$ capacity utilized.
- **Afternoon Rest (13:00 - 15:00 IST)**: $\sim 60-70\%$ capacity utilized.

#### Functions:
- `predict_truck_bay_availability(facility_id, total_capacity, current_hour) -> dict`: Returns occupied bays, available bays, percentage, diurnal phase, calculation timestamp, and confidence rating (`HIGH` during daytime, `MEDIUM` during shift changes).

---

### 3.8 Idempotent Offline Sync (`api/routers/sync.py`)

#### Purpose:
Implements the offline queue drain endpoint (`POST /api/sync/batch`).

#### Logic:
- Accepts a batch of client-generated UUID items:
  `{"device_id": "tr-4471", "items": [{"client_id": "uuid-...", "kind": "blocked", "lat": 25.11, "lon": 92.36, ...}]}`
- Maintains an in-memory set `PROCESSED_CLIENT_IDS`. If an item was already saved, it safely returns status `"accepted"` without duplicate database insertion (strict idempotence).
- Immediately darkens affected road segments in the live risk cache so the reroute updates in real time.

---

### 3.9 Interactive Web UI & PWA Client (`web/`)

#### 1. Header & Connectivity (`web/index.html`, `web/app.js`):
- Dynamic connectivity chip switching between `Online (Live Feed)` and `Offline (Airplane Mode)`.
- `Cache Corridor` button: Stores road graph, facilities, and all route combinations in IndexedDB for offline access.
- Language switcher: Supports English, Hindi, and Assamese.

#### 2. Four Core Screens:
- **Tab 1: Route Planning**:
  - Origin and Destination dropdowns.
  - Three Profile Cards (`Fastest`, `Balanced`, `Safest`) with real-time driving time, distance, risk pill, and delta badges.
  - Active route statistics bar (Distance, Duration, Mean Hazard, Max Hazard).
  - Dynamic Driver Advisory cards timeline.
- **Tab 2: Corridor & InSAR Precursors**:
  - Toggle switches for Historical Incidents (2021-2026), InSAR Deformation Layer, and Risk Heatmap.
  - **The 8-Minute Demo Trigger**: *"Simulate Torrential Rain on Sonapur Ghat"* button. Forces a simulated 165 mm downpour onto Sonapur Tunnel, recalculates routes, and demonstrates live divergence before judges!
  - InSAR Precursor alerts list with real-time z-scores.
- **Tab 3: Stops & Truck Bays**:
  - Lists verified facilities along NH-6.
  - Interactive diurnal occupancy bars with available bay counts and confidence ratings.
  - Clicking a facility smoothly pans the map (`flyTo`).
- **Tab 4: SOS & Reports**:
  - Four quick report buttons (`Blocked`, `Landslide`, `Waterlogged`, `Breakdown`).
  - **2-Second Hold-to-Fire SOS**:
    - Animated SVG circular progress ring tracking hold duration.
    - Web Audio API tone synthesis upon firing.
    - Automatic determination of the nearest 3 emergency facilities.
    - Status feedback: *"SOS DISPATCHED: Authorities & 108 Alerted"* (online) vs *"OFFLINE: SOS queued in Outbox"* (offline).

#### 3. Factor Explanation Drawer:
- Clicking any road segment on the MapLibre map opens this sliding drawer.
- Displays the Segment ID, Road Ref, speed, length, and risk band badge.
- Features **5 animated progress bars** representing Rainfall (34%), Slope (22%), Geological Susceptibility (18%), Incident History (16%), and Crowd Ground Truth (10%).
- Includes official citations (IMD, GSI, PIB).

#### 4. Service Worker & IndexedDB Outbox (`web/sw.js`):
- Precaches `index.html`, `style.css`, `app.js`, `manifest.json`.
- Serves cached assets when offline.
- Listens to `window.online` and automatically drains queued outbox reports to `/api/sync/batch`.

---

## 4. How to Run & Verify the Prototype

### 4.1 Seed Database (Zero Network Calls):
```powershell
python build/seed_data.py
```

### 4.2 Run Full Automated Verification Suite:
```powershell
python tests/test_all_modules.py
```

### 4.3 Launch the Web Application:
```powershell
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
- Open **`http://localhost:8000/`** for the full interactive MapLibre Web Client.
- Open **`http://localhost:8000/docs`** for the interactive Swagger OpenAPI documentation.

### 4.4 The Eight-Minute Presentation Walkthrough:
1. **0:00 — Problem & Corridor**: Show the 350 km NH-6 corridor map from Guwahati to Silchar with historical incident pins.
2. **1:00 — Plan Guwahati → Silchar**: Show Fastest vs Safest profile card (+18 min for materially lower risk exposure).
3. **2:30 — Tap the Red Segment**: Open the Factor Explanation Drawer and show the 5 factor bars (Rain, Slope, Susceptibility, History, Reports).
4. **4:00 — Airplane Mode & Outbox Sync**: Turn off Wi-Fi, plan a cached route, hold SOS for 2 seconds (sound tone plays, queues in Outbox), reconnect Wi-Fi, watch it sync and darken the road segment.
5. **6:00 — InSAR Precursors**: Toggle InSAR deformation layer, show Sonapur Tunnel subsidence (-48.5 mm/yr) and z-score alert.
6. **7:00 — Simulate Live Hazard**: Click *"Simulate Torrential Rain on Sonapur Ghat"* and watch the route divert around the tunnel.
7. **7:40 — Close on Scale**: Single corridor hand-verified, same pipeline expandable to all 8 Northeast states, open data throughout.
