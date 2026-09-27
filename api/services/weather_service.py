"""
api/services/weather_service.py — Corridor Weather Ingestion & Cache
Module 1 implementation:
- Samples corridor weather every ~10-15 km from Open-Meteo
- Ingests into weather_obs table
- Guaranteed offline fallback to cached observations (zero third-party sync calls in request handlers)
"""

import httpx
import json
import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Any
from api.database import get_connection

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Corridor observation sample coordinates (10 km spacing)
SAMPLE_POINTS = [
    (1, 26.1150, 91.8210, "Guwahati_Khanapara"),
    (2, 26.0420, 91.8650, "Byrnihat_Entry"),
    (3, 25.9320, 91.8780, "Nongpoh_North"),
    (4, 25.8640, 91.8840, "Nongpoh_South"),
    (5, 25.7620, 91.9051, "Umsning_Ghat"),
    (6, 25.6610, 91.8980, "Umiam_Barapani"),
    (7, 25.6020, 91.9540, "Shillong_Bypass"),
    (8, 25.5560, 92.0520, "Mawryngkneng"),
    (9, 25.4950, 92.1240, "Ummulong_Ridge"),
    (10, 25.4410, 92.2030, "Jowai_Bypass"),
    (11, 25.3210, 92.3120, "Ladrymbai_Mining_Belt"),
    (12, 25.2640, 92.3520, "Khliehriat_Central"),
    (13, 25.1850, 92.3780, "Lumshnong_Ghat"),
    (14, 25.1142, 92.3685, "Sonapur_Tunnel_Zone"),
    (15, 25.0420, 92.4210, "Malidor_Border_Ghat"),
    (16, 24.9650, 92.5620, "Kalain_Valley_Entry"),
    (17, 24.9020, 92.5850, "Badarpur_Ghat_Floodplain"),
    (18, 24.8720, 92.6510, "Panchgram_Paper_Mill_Stretch"),
    (19, 24.8380, 92.7420, "Silchar_Ramnagar_Approach"),
    (20, 24.8250, 92.7910, "Silchar_ISBT_Hub")
]

async def fetch_corridor_weather_live() -> List[Dict[str, Any]]:
    """
    Asynchronous weather pull covering the whole corridor in a single Open-Meteo call.
    Accepts comma-separated latitude and longitude lists.
    """
    params = {
        "latitude": ",".join(str(p[1]) for p in SAMPLE_POINTS),
        "longitude": ",".join(str(p[2]) for p in SAMPLE_POINTS),
        "hourly": "precipitation,visibility",
        "past_days": 1,
        "forecast_days": 1,
        "timezone": "Asia/Kolkata"
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(OPEN_METEO_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            
            # Format results
            results = []
            now_iso = datetime.now(timezone.utc).isoformat()
            
            # Single point returns dict, multiple points returns list
            responses = data if isinstance(data, list) else [data]
            for idx, pt in enumerate(SAMPLE_POINTS):
                pt_data = responses[idx] if idx < len(responses) else {}
                hourly = pt_data.get("hourly", {})
                precip = hourly.get("precipitation", [0.0])
                vis = hourly.get("visibility", [10000.0])
                
                # Latest and 24h sum
                current_rain = float(precip[-1]) if precip else 0.0
                rain_24h = float(sum(precip[-24:])) if len(precip) >= 24 else float(sum(precip))
                vis_m = float(vis[-1]) if vis else 10000.0
                
                results.append({
                    "point_id": pt[0],
                    "ts": now_iso,
                    "rain_mm": round(current_rain, 1),
                    "rain_24h_mm": round(rain_24h, 1),
                    "visibility_m": round(vis_m, 1),
                    "lat": pt[1],
                    "lon": pt[2]
                })
            
            # Update database
            _save_weather_to_db(results)
            return results
    except Exception as e:
        print(f"[WARN] Live weather fetch failed (likely offline): {e}. Using cached weather observations.")
        return get_cached_weather()

def _save_weather_to_db(obs_list: List[Dict[str, Any]]):
    """Save freshly ingested weather observations to local database."""
    conn = get_connection()
    cur = conn.cursor()
    for o in obs_list:
        cur.execute("""
        INSERT INTO weather_obs (point_id, ts, rain_mm, rain_24h_mm, visibility_m, lat, lon)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (
            o["point_id"],
            o["ts"],
            o["rain_mm"],
            o["rain_24h_mm"],
            o["visibility_m"],
            o["lat"],
            o["lon"]
        ))
    conn.commit()
    conn.close()

def get_cached_weather() -> List[Dict[str, Any]]:
    """Retrieve the latest weather observation for each point from local DB."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT point_id, ts, rain_mm, rain_24h_mm, visibility_m, lat, lon
    FROM weather_obs
    WHERE id IN (
        SELECT MAX(id) FROM weather_obs GROUP BY point_id
    );
    """)
    rows = cur.fetchall()
    conn.close()
    
    return [
        {
            "point_id": r["point_id"],
            "ts": r["ts"],
            "rain_mm": r["rain_mm"],
            "rain_24h_mm": r["rain_24h_mm"],
            "visibility_m": r["visibility_m"],
            "lat": r["lat"],
            "lon": r["lon"]
        }
        for r in rows
    ]
