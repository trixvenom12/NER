"""
api/routers/risk.py — Risk and Hazard Layer Endpoints
"""

from fastapi import APIRouter, Depends, Query, Request
import json
from typing import Dict, Any
from api.deps import get_risk_cache, get_db

router = APIRouter(prefix="/api/risk", tags=["Risk"])

@router.get("/segments")
async def get_risk_segments(
    request: Request,
    bbox: str = Query(default=None, description="Optional bounding box 'W,S,E,N'"),
    db = Depends(get_db)
):
    """
    Returns GeoJSON FeatureCollection of all corridor segments.
    Each feature carries:
    - band: 'safe' (#3F7A55) | 'caution' (#B8862A) | 'hazard' (#A33A28)
    - score: 0..100
    - factors: verbatim JSON object with 5 factor bars + citations
    """
    risk_cache = request.app.state.risk_cache
    cur = db.cursor()
    cur.execute("SELECT id, road_ref, highway, length_m, free_speed_kph, mean_slope_deg, susceptibility, geom_geojson FROM segment;")
    rows = cur.fetchall()

    features = []
    for r in rows:
        seg_id = r["id"]
        geom = json.loads(r["geom_geojson"])
        risk_info = risk_cache.get(seg_id, {"score": 15.0, "band": "safe", "factors": {}})

        features.append({
            "type": "Feature",
            "properties": {
                "id": seg_id,
                "road_ref": r["road_ref"],
                "highway": r["highway"],
                "length_m": r["length_m"],
                "free_speed_kph": r["free_speed_kph"],
                "mean_slope_deg": r["mean_slope_deg"],
                "susceptibility": r["susceptibility"],
                "score": risk_info.get("score", 15.0),
                "band": risk_info.get("band", "safe"),
                "factors": risk_info.get("factors", {})
            },
            "geometry": geom
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }

@router.get("/heatmap")
async def get_risk_heatmap(
    request: Request,
    db = Depends(get_db)
):
    """
    Returns point features with risk weight for MapLibre GL heatmap layer.
    """
    risk_cache = request.app.state.risk_cache
    cur = db.cursor()
    cur.execute("SELECT id, geom_geojson FROM segment;")
    rows = cur.fetchall()

    features = []
    for r in rows:
        seg_id = r["id"]
        geom = json.loads(r["geom_geojson"])
        coords = geom.get("coordinates", [])
        if coords:
            # Midpoint
            mid_lon = (coords[0][0] + coords[-1][0]) / 2.0
            mid_lat = (coords[0][1] + coords[-1][1]) / 2.0
            score = risk_cache.get(seg_id, {}).get("score", 10.0)

            features.append({
                "type": "Feature",
                "properties": {
                    "segment_id": seg_id,
                    "weight": round(score / 100.0, 2),
                    "score": score
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [mid_lon, mid_lat]
                }
            })

    return {
        "type": "FeatureCollection",
        "features": features
    }
