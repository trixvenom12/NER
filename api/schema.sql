-- ==========================================================
-- SIH26002 NER Logistics Intelligence Platform - Database Schema
-- Compatible with PostgreSQL 16 + PostGIS 3.4 and SQLite
-- ==========================================================

-- Segment Table: one row per directed road segment
CREATE TABLE IF NOT EXISTS segment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    osm_way_id BIGINT,
    u_node BIGINT NOT NULL,
    v_node BIGINT NOT NULL,
    road_ref TEXT DEFAULT 'NH-6',
    highway TEXT DEFAULT 'trunk',
    length_m DOUBLE PRECISION NOT NULL,
    free_speed_kph SMALLINT NOT NULL DEFAULT 40,
    mean_slope_deg REAL DEFAULT 0.0,
    susceptibility REAL DEFAULT 0.0,
    geom_geojson TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_segment_u_node ON segment(u_node);
CREATE INDEX IF NOT EXISTS idx_segment_v_node ON segment(v_node);

-- Rolling Weather Observations: sampled along corridor
CREATE TABLE IF NOT EXISTS weather_obs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    point_id INTEGER,
    ts TIMESTAMP NOT NULL,
    rain_mm REAL DEFAULT 0.0,
    rain_24h_mm REAL DEFAULT 0.0,
    visibility_m REAL DEFAULT 10000.0,
    lat REAL NOT NULL,
    lon REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_weather_obs_ts ON weather_obs(ts);

-- Hand-compiled History: Credibility layer from PIB & regional archives
CREATE TABLE IF NOT EXISTS incident (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_on DATE,
    kind TEXT, -- landslide | flood | blockade | waterlogging
    duration_hours REAL DEFAULT 0.0,
    source_url TEXT,
    lat REAL NOT NULL,
    lon REAL NOT NULL
);

-- Segment Risk: Written by the risk engine, read by the router
CREATE TABLE IF NOT EXISTS segment_risk (
    segment_id BIGINT NOT NULL,
    computed_at TIMESTAMP NOT NULL,
    score REAL NOT NULL, -- 0..100
    band TEXT NOT NULL,  -- safe | caution | hazard
    factors TEXT NOT NULL, -- JSON string holding every input
    PRIMARY KEY (segment_id, computed_at),
    FOREIGN KEY (segment_id) REFERENCES segment(id)
);

CREATE INDEX IF NOT EXISTS idx_segment_risk_band ON segment_risk(band);

-- Truck bays, fuel, food, medical, weighbridges
CREATE TABLE IF NOT EXISTS facility (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    kind TEXT NOT NULL, -- truck_bay | fuel | food | medical | toilet
    capacity INTEGER DEFAULT 50,
    attrs TEXT NOT NULL, -- JSON string
    lat REAL NOT NULL,
    lon REAL NOT NULL
);

-- Driver-submitted Ground Truth + Emergency SOS
CREATE TABLE IF NOT EXISTS report (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    device_id TEXT NOT NULL,
    kind TEXT NOT NULL, -- blocked | slide | water | sos
    note TEXT,
    confirmed_count INTEGER DEFAULT 0,
    lat REAL NOT NULL,
    lon REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_report_created_at ON report(created_at);
