# Project Scope & Architecture Contract — SIH26002

**Problem Statement:** PS SIH26002 — AI-Based Smart Logistics and Accessibility Intelligence Platform for North Eastern Region (NER)  
**Team:** Team Git Pirates  
**Corridor Focus:** NH-6 Guwahati → Shillong → Silchar (~350 km)  
**Bounding Box:** `(N 26.60, S 24.70, E 93.30, W 90.90)`  

---

## The Six Solution Pillars & Build Depth

A hackathon prototype that attempts six deep pillars ends up with six broken ones. We build three end to end, wire three as thin but honest surfaces, and clearly demarcate what is shipped vs. what is pre-computed/stubbed.

### Deep Pillars (Built Fully)
1. **Hazard-Aware Routing**:
   - Dynamic road graph whose edge weights adjust in real time according to weather, slope, and hazard scores.
   - 3 Divergent Profiles from a single parameter $\alpha$: Fastest ($\alpha = 0.0$), Balanced ($\alpha = 1.2$), Safest ($\alpha = 4.0$).
   - Hard exclusion for confirmed blockades ($r \ge 0.92$).
   - Full explainability payload with distance/time deltas, segment-level factors, and deterministic advisories.

2. **Risk Scoring Engine & Explainability**:
   - Layer A: Transparent 5-factor hazard index (Rainfall 34%, Slope 22%, Susceptibility 18%, Historical incidents 16%, Active reports 10%).
   - Layer B: Learned adjustment model (gradient-boosted classification nudging base index by at most $\pm 15$ points).
   - Instant visual explanation: Tapping any red/amber segment reveals the exact factor breakdown bars.

3. **Offline Progressive Web App (PWA)**:
   - Full corridor offline cache (road graph, risk snapshot, highway amenities).
   - Client-side route generation when offline.
   - Outbox queue with idempotent sync (`POST /api/sync/batch`) when reconnecting.

### Thin Honest Surfaces (Wired Realistically)
4. **Trucker Services & SOS**:
   - Real map layer with Ri-Bhoi truck bays, fuel stations, weighbridges, and emergency havens along NH-6.
   - 2-second hold-to-fire SOS button with coordinates, device ID, and automatic calculation of nearest 3 emergency facilities.
   - Diurnal truck bay occupancy prediction with visible confidence levels and timestamps.

5. **Analytics for Planning**:
   - Risk density hotspot cluster analysis on Meghalaya ghats.
   - Seasonal/historical blockade frequency chart from the 5-year incident archive.

6. **InSAR Landslide Precursors**:
   - Pre-computed Sentinel-1 surface deformation rate layer (mm/year) over high-risk ghat sections (Sonapur Tunnel, Kseh Bilat).
   - Time-series anomaly detector (rolling z-score over displacement + 72h antecedent rainfall) triggering precursor alerts.

---

## The Cut List (Explicitly Out of Scope)

The following items are intentionally excluded to protect project velocity and demo stability:
- **User accounts & JWT auth**: Replaced by header-based identity (`X-Device-Id`).
- **Payment processing**: Out of scope.
- **Native Android app**: PWA delivers installable mobile experience with service worker cache.
- **Real-time GPS fleet tracking**: Not requested by SIH26002; static simulation is sufficient.
- **Admin CRUD screens**: Data managed through reproducible seed files.
- **Chatbots / LLMs**: Deterministic templates used for rapid, offline-capable driver advisories.
- **Kubernetes / multi-node deployment**: Single containerized / process stack.
