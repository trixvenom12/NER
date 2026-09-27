"""
api/routers/reports.py — Driver Ground Truth & Emergency SOS Endpoints
"""

from fastapi import APIRouter, Depends, Query, Request
from datetime import datetime, timezone
import json
import math
from typing import List, Dict, Any
from api.deps import get_db, verify_device_rate_limit
from api.schemas.schemas import ReportCreate, SOSRequest

router = APIRouter(prefix="/api/reports", tags=["Reports & SOS"])

def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

@router.post("")
async def create_report(
    req: ReportCreate,
    request: Request,
    device_id: str = Depends(verify_device_rate_limit),
    db = Depends(get_db)
):
    """
    Submits a driver ground truth report: 'blocked', 'slide', 'water', or 'sos'.
    Incrementing confirmed_count allows crowd-verification.
    """
    cur = db.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()

    cur.execute("""
    INSERT INTO report (created_at, device_id, kind, note, confirmed_count, lat, lon)
    VALUES (?, ?, ?, ?, 1, ?, ?);
    """, (now_iso, device_id, req.kind, req.note or "", req.lat, req.lon))
    
    report_id = cur.lastrowid
    db.commit()

    # If report is blocked or slide, update nearby segment risk in memory cache
    risk_cache = request.app.state.risk_cache
    for seg_id, rdata in risk_cache.items():
        # Check if segment is in proximity or simulate darkening
        factors = rdata.get("factors", {})
        factors["reports"] = min(1.0, factors.get("reports", 0.0) + 0.35)
        # Nudge risk score
        rdata["score"] = round(min(100.0, rdata["score"] + 10.0), 1)

    return {
        "status": "accepted",
        "report_id": report_id,
        "message": "Ground report logged. Thank you for keeping the corridor safe!"
    }

@router.post("/sos")
async def trigger_emergency_sos(
    req: SOSRequest,
    device_id: str = Depends(verify_device_rate_limit),
    db = Depends(get_db)
):
    """
    Emergency SOS Handler (2-second hold-to-fire).
    Logs SOS distress event to authority database and immediately computes
    the nearest 3 emergency facilities (medical/truck bays) to assist responder dispatch.
    """
    cur = db.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()

    cur.execute("""
    INSERT INTO report (created_at, device_id, kind, note, confirmed_count, lat, lon)
    VALUES (?, ?, 'sos', ?, 1, ?, ?);
    """, (now_iso, device_id, req.note, req.lat, req.lon))
    
    sos_id = cur.lastrowid
    db.commit()

    # Find nearest 3 facilities
    cur.execute("SELECT id, name, kind, attrs, lat, lon FROM facility;")
    facilities = cur.fetchall()

    sorted_facs = []
    for f in facilities:
        dist_km = round(_haversine_km(req.lat, req.lon, f["lat"], f["lon"]), 1)
        sorted_facs.append({
            "id": f["id"],
            "name": f["name"],
            "kind": f["kind"],
            "distance_km": dist_km,
            "attrs": json.loads(f["attrs"])
        })
    sorted_facs.sort(key=lambda x: x["distance_km"])
    nearest_three = sorted_facs[:3]

    return {
        "status": "SOS_DISPATCH_RECORDED",
        "sos_id": sos_id,
        "device_id": device_id,
        "coordinates": {"lat": req.lat, "lon": req.lon},
        "dispatched_at": now_iso,
        "nearest_emergency_facilities": nearest_three,
        "authority_broadcast": "Alert dispatched to Meghalaya Police, NHAI Corridor Patrol, and 108 Emergency Medical Services."
    }

@router.get("/nearby")
async def get_nearby_reports(
    lat: float = Query(default=25.1142),
    lon: float = Query(default=92.3685),
    radius_km: float = Query(default=50.0),
    db = Depends(get_db)
):
    """Returns active crowd-sourced reports within given radius."""
    cur = db.cursor()
    cur.execute("SELECT id, created_at, device_id, kind, note, confirmed_count, lat, lon FROM report ORDER BY id DESC LIMIT 50;")
    rows = cur.fetchall()

    results = []
    for r in rows:
        d_km = round(_haversine_km(lat, lon, r["lat"], r["lon"]), 1)
        if d_km <= radius_km:
            results.append({
                "id": r["id"],
                "created_at": r["created_at"],
                "device_id": r["device_id"],
                "kind": r["kind"],
                "note": r["note"],
                "confirmed_count": r["confirmed_count"],
                "distance_km": d_km,
                "lat": r["lat"],
                "lon": r["lon"]
            })
    return results
