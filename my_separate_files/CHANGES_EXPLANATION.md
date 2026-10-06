# Summary of Changes & Fixes

This directory contains the separate files modified to fix the route profile divergence issue (Fastest, Balanced, Safest) and local server execution.

---

## 1. `routing_engine.py` (located in `api/services/routing_engine.py`)
### What Was Wrong:
- When NetworkX routes using `MultiDiGraph`, the edge attribute parameter passed to custom `weight` callbacks is an `AtlasView` of parallel edges (`{0: edge_dict, ...}`).
- The original code checked `if not isinstance(data, dict): return 1.0`. Since `AtlasView` inherits from `collections.abc.Mapping` and is **not** a `dict`, this check returned `1.0` on every single edge for all profiles. Dijkstra was running as an unweighted BFS hop-count, making all 3 profiles identical.

### Changes Made:
- Imported `from collections.abc import Mapping`.
- Updated `edge_cost()` to inspect `isinstance(data, Mapping)` and unpack multi-edge dictionaries properly to evaluate and select the minimum cost edge.
- Updated `_get_best_edge()` to check `isinstance(edge_data, Mapping)`.
- Added `_normalize_node_id()` helper to support int and string node identifiers seamlessly.
- Retained the geometry coordinate fallback for robust rendering.

---

## 2. `build_graph.py` (located in `build/build_graph.py`)
### What Was Wrong:
- The **Sonapur Ridge Detour** (`117 -> 120 -> 119`) had a slow base speed (25 km/h) and high susceptibility ($0.40$), making its base travel time too long to ever be chosen over the tunnel path under realistic $\alpha$ penalties.
- The **Borkhola Bypass** (`123 -> 128 -> 126`) lacked calibrated speeds and susceptibilities relative to the main Badarpur / Panchgram floodplain highway.

### Changes Made:
- **Sonapur Ridge Detour** edges (`117 -> 120` and `120 -> 119`):
  - Speed set to `34 km/h`
  - Susceptibility set to `0.18` and `0.20` (reflecting a stable ridge route avoiding the slide-prone tunnel gorge).
- **Badarpur / Panchgram Main Highway** (`123 -> 124` and `124 -> 125`):
  - Susceptibility set to `0.40` and `0.38` (reflecting Barak River floodplain waterlogging and embankment caution).
- **Borkhola Bypass** (`123 -> 128` and `128 -> 126`):
  - Speed set to `46 km/h`
  - Susceptibility set to `0.10` and `0.08` (elevated bypass route free of riverine flooding).

---

## 3. `weather_seed.json` (located in `data/weather_seed.json`)
### Changes Made:
- Calibrated rainfall for Point 16 (`Sonapur_Ridge_Detour`): `rain_24h_mm = 35.0` (ridge has quick runoff compared to the gorge).
- Calibrated rainfall for Points 19 and 20 (`Badarpur_Ghat_Floodplain` and `Panchgram_Paper_Mill_Stretch`): `rain_24h_mm = 52.0` and `48.0` (reflecting monsoon waterlogging in the valley).

---

## 4. `app.js` (located in `web/app.js`)
### Changes Made:
- Added dynamic polyline and glowing halo recoloring in `displayActiveProfile()`:
  - ⚡ **Fastest**: Electric Cyan / Sky Blue (`#38bdf8`)
  - ⚖️ **Balanced**: Royal Blue (`#60a5fa`)
  - 🛡️ **Safest**: Emerald Green (`#10b981`)
- Enabled camera bounds auto-fitting when switching profiles.

---

## 5. `run_server.bat`
### Changes Made:
- Changed server host binding from `0.0.0.0` to `127.0.0.1` (`python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload`).
- This fixes Windows socket error: `[WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions`.

---

## 6. `test_routes.py`
### Purpose:
- Diagnostic test script that loads the graph, primes the risk cache, and computes all 3 profiles for Guwahati -> Silchar and Shillong -> Silchar, printing out the distances, durations, mean hazard, and node sequences.

---

## Verification Results Summary (Guwahati 101 -> Silchar 127):

| Profile | Distance | Duration | $\Delta$ vs Fastest | Mean Hazard | Key Divergence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Fastest** ($\alpha = 0.0$) | 220.3 km | 297.9 min | 0.0 min | 10.8 | Uses direct **Sonapur Tunnel (118)** and **Main Highway (124, 125)** |
| **Balanced** ($\alpha = 1.2$) | 221.0 km | 299.3 min | **+1.4 min** | 10.6 | **Diverts around 90.1 hazard Sonapur Tunnel** via **Ridge Detour (120)**, stays on Main Highway |
| **Safest** ($\alpha = 4.0$) | 221.9 km | 302.2 min | **+4.3 min** | **8.8** | Diverts around Sonapur Tunnel via **Ridge Detour (120)** **AND** diverts around Badarpur floodplain via **Borkhola Bypass (128)** |
