# Developer & Agent Guidelines — Team Git Pirates

## Project: SIH26002 NER Logistics Intelligence Platform

This document governs all architectural and implementation decisions for the repository.

### Core Architecture & Tech Stack

1. **Backend**:
   - Python 3.12+ with FastAPI and Uvicorn.
   - NetworkX for in-memory graph operations and Dijkstra routing.
   - Pydantic v2 for request/response schemas.
   - Scikit-learn / XGBoost for learned hazard adjustment.
   - APScheduler for background weather and risk recomputation loops.
   - SQLite with spatial support (and PostgreSQL 16 + PostGIS 3.4 compatibility via SQL DDL).

2. **Frontend**:
   - Modern HTML5, Vanilla CSS design tokens (dark slate #0f172a theme, glassmorphism), ES6 JavaScript.
   - MapLibre GL JS for vector map rendering and risk coloring.
   - Progressive Web App (PWA) with Service Worker and IndexedDB outbox storage.

3. **Data Provenance & Integrity**:
   - Real, hand-compiled incidents from official PIB and regional news archives for NH-6 (2021–2026).
   - Real geographic coordinates for the corridor from Guwahati (Beltola) to Silchar via Shillong and Jowai.
   - Weather ingested from Open-Meteo with local caching so the system works with zero external network connectivity.
   - InSAR deformation pre-computed offline from Sentinel-1 radar interferometry scenes.

### Non-Negotiable Rules

1. **No Third-Party Synchronous API Calls**:
   API request handlers must never block on external web calls. All weather and map data is served from local cache or the database.
2. **Deterministic Advisories**:
   Advisories must be generated from deterministic templates keyed on dominant risk factors to guarantee instant generation, offline capability, and multilingual support.
3. **Squared Risk Term in Cost Function**:
   Edge penalty uses $w = base \times (1 + \alpha \times r^2)$. This ensures mildly damp roads are not unnecessarily diverted while steep hazard ghats are strictly routed around.
4. **Hard Blockade Exclusion**:
   Confirmed blockades ($r \ge 0.92$) return `None` from the NetworkX weight function, excluding the edge without modifying the underlying graph structure.
5. **Offline-First Resilience**:
   The entire corridor experience must work in Airplane Mode once downloaded. Outbox incident reports must queue locally and drain idempotently upon reconnection.
