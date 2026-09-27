"""
api/routers/facilities.py — Truck Bay & Highway Facilities Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
import json
from typing import List, Dict, Any, Optional
from api.deps import get_db
from api.services.occupancy_service import predict_truck_bay_availability

router = APIRouter(prefix="/api/facilities", tags=["Facilities"])

@router.get("")
async def list_facilities(kind: Optional[str] = None, db = Depends(get_db)):
    """
    Returns list of verified highway facilities along NH-6.
    Includes Ri-Bhoi truck bays, fuel stations, weighbridges, and medical refuges.
    """
    cur = db.cursor()
    if kind:
        cur.execute("SELECT id, name, kind, capacity, attrs, lat, lon FROM facility WHERE kind = ?;", (kind,))
    else:
        cur.execute("SELECT id, name, kind, capacity, attrs, lat, lon FROM facility;")
    
    rows = cur.fetchall()
    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "name": r["name"],
            "kind": r["kind"],
            "capacity": r["capacity"],
            "attrs": json.loads(r["attrs"]) if isinstance(r["attrs"], str) else (r["attrs"] or {}),
            "lat": r["lat"],
            "lon": r["lon"],
            "availability": predict_truck_bay_availability(r["id"], r["capacity"]) if r["kind"] == "truck_bay" else None
        })
    return results

@router.get("/{facility_id}/availability")
async def get_facility_availability(facility_id: int, db = Depends(get_db)):
    """
    Simulates diurnal occupancy for a specific truck bay.
    Returns: occupied vs available bays, percentage, confidence rating, and timestamp.
    """
    cur = db.cursor()
    cur.execute("SELECT id, name, kind, capacity FROM facility WHERE id = ?;", (facility_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Facility not found")

    capacity = row["capacity"] or 50
    return predict_truck_bay_availability(facility_id, capacity)
