"""
build/seed_data.py — Offline Database Seeder
Module 1 & 2 deliverable:
Populates local database with zero network calls from /data:
1. segment table (from data/segments_seed.json)
2. weather_obs table (from data/weather_seed.json)
3. incident table (from data/incidents.csv)
4. facility table (from data/facilities.geojson)
5. segment_risk table (initial risk computed by api/services/risk_engine.py)
"""

import os
import sys
import csv
import json
import sqlite3
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.database import init_db, get_connection
from api.services.risk_engine import risk_engine

def seed_all():
    print("[INFO] Initializing database schema...")
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    # 1. Clear existing data
    for tbl in ["segment_risk", "report", "incident", "weather_obs", "facility", "segment"]:
        cur.execute(f"DELETE FROM {tbl};")
    conn.commit()

    # 2. Seed Segments
    print("[INFO] Seeding segments from data/segments_seed.json...")
    with open("data/segments_seed.json", "r") as f:
        segments = json.load(f)

    for seg in segments:
        cur.execute("""
        INSERT INTO segment (id, osm_way_id, u_node, v_node, road_ref, highway, length_m, free_speed_kph, mean_slope_deg, susceptibility, geom_geojson)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            seg["id"],
            seg["osm_way_id"],
            seg["u_node"],
            seg["v_node"],
            seg["road_ref"],
            seg["highway"],
            seg["length_m"],
            seg["free_speed_kph"],
            seg["mean_slope_deg"],
            seg["susceptibility"],
            json.dumps(seg["geom"])
        ))
    conn.commit()
    print(f"[OK] Seeded {len(segments)} segments.")

    # 3. Seed Weather Observations
    print("[INFO] Seeding weather observations from data/weather_seed.json...")
    with open("data/weather_seed.json", "r") as f:
        weather_list = json.load(f)

    now_iso = datetime.now(timezone.utc).isoformat()
    for w in weather_list:
        cur.execute("""
        INSERT INTO weather_obs (point_id, ts, rain_mm, rain_24h_mm, visibility_m, lat, lon)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (
            w["point_id"],
            now_iso,
            w["rain_mm"],
            w["rain_24h_mm"],
            w["visibility_m"],
            w["lat"],
            w["lon"]
        ))
    conn.commit()
    print(f"[OK] Seeded {len(weather_list)} weather observations.")

    # 4. Seed Historical Incidents
    print("[INFO] Seeding incidents from data/incidents.csv...")
    incident_count = 0
    with open("data/incidents.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute("""
            INSERT INTO incident (occurred_on, kind, duration_hours, source_url, lat, lon)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (
                row["date"],
                row["type"],
                float(row["duration_hours"]),
                row["source_url"],
                float(row["lat"]),
                float(row["lon"])
            ))
            incident_count += 1
    conn.commit()
    print(f"[OK] Seeded {incident_count} historical incidents.")

    # 5. Seed Facilities
    print("[INFO] Seeding facilities from data/facilities.geojson...")
    with open("data/facilities.geojson", "r") as f:
        fac_geo = json.load(f)

    for feat in fac_geo.get("features", []):
        props = feat["properties"]
        geom = feat["geometry"]
        cur.execute("""
        INSERT INTO facility (id, name, kind, capacity, attrs, lat, lon)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (
            props["id"],
            props["name"],
            props["kind"],
            props.get("capacity", 50),
            json.dumps(props.get("attrs", {})),
            geom["coordinates"][1],
            geom["coordinates"][0]
        ))
    conn.commit()
    print(f"[OK] Seeded {len(fac_geo.get('features', []))} highway facilities.")

    # 6. Compute & Seed Initial Segment Risks
    print("[INFO] Computing and seeding initial segment risks via Risk Engine...")
    # Map weather sample points to nearest segment
    weather_by_point = {w["point_id"]: w for w in weather_list}
    
    # Pre-count historical incidents near Sonapur, Umiam, etc.
    cur.execute("SELECT id, lat, lon FROM incident;")
    all_incidents = cur.fetchall()

    for seg in segments:
        seg_geom = seg["geom"]["coordinates"]
        mid_lon = (seg_geom[0][0] + seg_geom[1][0]) / 2.0
        mid_lat = (seg_geom[0][1] + seg_geom[1][1]) / 2.0

        # Find nearest weather observation point
        nearest_wx = min(
            weather_list,
            key=lambda w: (w["lat"] - mid_lat)**2 + (w["lon"] - mid_lon)**2
        )
        wx_rain_24h = nearest_wx["rain_24h_mm"]

        # Count incidents within ~4 km (0.035 deg approx)
        hist_count = sum(
            1 for inc in all_incidents
            if ((inc["lat"] - mid_lat)**2 + (inc["lon"] - mid_lon)**2) < (0.035**2)
        )

        active_reports = 0
        score, band, factors = risk_engine.score(seg, wx_rain_24h, hist_count, active_reports)

        cur.execute("""
        INSERT INTO segment_risk (segment_id, computed_at, score, band, factors)
        VALUES (?, ?, ?, ?, ?);
        """, (
            seg["id"],
            now_iso,
            score,
            band,
            json.dumps(factors)
        ))
    conn.commit()
    print(f"[OK] Computed and seeded risks for {len(segments)} segments.")

    conn.close()
    print("\n[SUCCESS] Entire local database seeded in seconds with zero external network calls!")

if __name__ == "__main__":
    seed_all()
