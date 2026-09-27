-- ==========================================================
-- SIH26002 NER Logistics Intelligence Platform
-- Supabase / PostgreSQL 16 Schema with PostGIS & RLS
-- ==========================================================

-- Enable PostGIS for geospatial analysis if needed
CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. Segment Table: One row per directed road segment
CREATE TABLE IF NOT EXISTS segment (
    id BIGSERIAL PRIMARY KEY,
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

-- 2. Rolling Weather Observations: Sampled along corridor
CREATE TABLE IF NOT EXISTS weather_obs (
    id BIGSERIAL PRIMARY KEY,
    point_id INTEGER,
    ts TIMESTAMPTZ NOT NULL,
    rain_mm REAL DEFAULT 0.0,
    rain_24h_mm REAL DEFAULT 0.0,
    visibility_m REAL DEFAULT 10000.0,
    lat REAL NOT NULL,
    lon REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_weather_obs_ts ON weather_obs(ts);

-- 3. Historical Incidents: Credibility layer from PIB & regional archives
CREATE TABLE IF NOT EXISTS incident (
    id BIGSERIAL PRIMARY KEY,
    occurred_on DATE,
    kind TEXT, -- landslide | flood | blockade | waterlogging
    duration_hours REAL DEFAULT 0.0,
    source_url TEXT,
    lat REAL NOT NULL,
    lon REAL NOT NULL
);

-- 4. Segment Risk: Written by the risk engine, read by the router
CREATE TABLE IF NOT EXISTS segment_risk (
    segment_id BIGINT NOT NULL REFERENCES segment(id) ON DELETE CASCADE,
    computed_at TIMESTAMPTZ NOT NULL,
    score REAL NOT NULL, -- 0..100
    band TEXT NOT NULL,  -- safe | caution | hazard
    factors JSONB NOT NULL,
    PRIMARY KEY (segment_id, computed_at)
);

CREATE INDEX IF NOT EXISTS idx_segment_risk_band ON segment_risk(band);

-- 5. Facilities: Truck bays, fuel, food, medical, weighbridges
CREATE TABLE IF NOT EXISTS facility (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL, -- truck_bay | fuel | food | medical | toilet
    capacity INTEGER DEFAULT 50,
    attrs JSONB NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_facility_kind ON facility(kind);

-- 6. Driver Reports: Ground truth reports & emergency SOS
CREATE TABLE IF NOT EXISTS report (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    device_id TEXT NOT NULL,
    kind TEXT NOT NULL, -- blocked | slide | water | sos
    note TEXT,
    confirmed_count INTEGER DEFAULT 0,
    lat REAL NOT NULL,
    lon REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_report_created_at ON report(created_at);

-- ==========================================================
-- Supabase Row Level Security (RLS) Policies
-- ==========================================================
ALTER TABLE segment ENABLE ROW LEVEL SECURITY;
ALTER TABLE weather_obs ENABLE ROW LEVEL SECURITY;
ALTER TABLE incident ENABLE ROW LEVEL SECURITY;
ALTER TABLE segment_risk ENABLE ROW LEVEL SECURITY;
ALTER TABLE facility ENABLE ROW LEVEL SECURITY;
ALTER TABLE report ENABLE ROW LEVEL SECURITY;

-- Allow public read access to road network and static/operational data
CREATE POLICY "Public read on segment" ON segment FOR SELECT USING (true);
CREATE POLICY "Public read on weather_obs" ON weather_obs FOR SELECT USING (true);
CREATE POLICY "Public read on incident" ON incident FOR SELECT USING (true);
CREATE POLICY "Public read on segment_risk" ON segment_risk FOR SELECT USING (true);
CREATE POLICY "Public read on facility" ON facility FOR SELECT USING (true);
CREATE POLICY "Public read on report" ON report FOR SELECT USING (true);

-- Allow public/anonymous submission of driver reports & SOS
CREATE POLICY "Public insert on report" ON report FOR INSERT WITH CHECK (true);

-- Allow backend service role full access
CREATE POLICY "Service full access on segment" ON segment FOR ALL TO service_role USING (true);
CREATE POLICY "Service full access on weather_obs" ON weather_obs FOR ALL TO service_role USING (true);
CREATE POLICY "Service full access on incident" ON incident FOR ALL TO service_role USING (true);
CREATE POLICY "Service full access on segment_risk" ON segment_risk FOR ALL TO service_role USING (true);
CREATE POLICY "Service full access on facility" ON facility FOR ALL TO service_role USING (true);
CREATE POLICY "Service full access on report" ON report FOR ALL TO service_role USING (true);
