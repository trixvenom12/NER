"""
api/routers/routes.py — Route Planning & Hazard Simulation Endpoints
POST /api/route         — Compute single route with specified profile
GET  /api/route/alternatives — Compute all 3 route profiles
POST /api/route/simulate-hazard — Inject simulated rainfall for demo
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from typing import Dict, Any, List

from api.deps import get_graph, get_risk_cache, get_db
from api.schemas.schemas import RouteRequest, RiskSimulationRequest
from api.services.routing_engine import route_single, route_all_alternatives

router = APIRouter(prefix="/api/route", tags=["Routing"])


def _load_facilities_list(db) -> List[Dict[str, Any]]:
    """Load facility list for advisory generation."""
    import json
    cur = db.cursor()
    cur.execute("SELECT id, name, kind, capacity, attrs, lat, lon FROM facility;")
    rows = cur.fetchall()
    results = []
    for r in rows:
        attrs = r["attrs"]
        if isinstance(attrs, str):
            attrs = json.loads(attrs)
        results.append({
            "id": r["id"],
            "name": r["name"],
            "kind": r["kind"],
            "capacity": r["capacity"],
            "attrs": attrs,
            "lat": r["lat"],
            "lon": r["lon"],
        })
    return results


@router.post("")
async def compute_route(
    req: RouteRequest,
    request: Request,
    db=Depends(get_db),
):
    """Compute a single hazard-aware route with the given profile."""
    G = request.app.state.graph
    if not G:
        raise HTTPException(status_code=503, detail="Road graph not loaded. Run: python build/build_graph.py")

    risk_cache = request.app.state.risk_cache
    facilities = _load_facilities_list(db)

    result = route_single(G, req.src_node_id, req.dst_node_id, req.profile, risk_cache, facilities)
    return result


@router.get("/alternatives")
async def get_all_alternatives(
    request: Request,
    src: int = 101,
    dst: int = 127,
    db=Depends(get_db),
):
    """Compute fastest, balanced, and safest routes with explicit deltas."""
    G = request.app.state.graph
    if not G:
        raise HTTPException(status_code=503, detail="Road graph not loaded. Run: python build/build_graph.py")

    risk_cache = request.app.state.risk_cache
    facilities = _load_facilities_list(db)

    return route_all_alternatives(G, src, dst, risk_cache, facilities)


@router.post("/simulate-hazard")
async def simulate_hazard(
    req: RiskSimulationRequest,
    request: Request,
    db=Depends(get_db),
):
    """
    The 8-minute demo trigger: Injects simulated weather into the risk cache
    to demonstrate live route diversion away from hazard zones.
    """
    import json

    risk_cache = request.app.state.risk_cache
    cur = db.cursor()

    # Map location names to segment node ranges
    LOCATION_SEGMENTS = {
        "Sonapur_Tunnel_Zone": ["NH-6-Sonapur-Tunnel", "Sonapur"],
        "Lumshnong_Ghat": ["Lumshnong"],
        "Umiam_Barapani": ["Umiam", "Barapani"],
    }

    target_refs = LOCATION_SEGMENTS.get(req.target_location, ["Sonapur"])

    # Find matching segments
    cur.execute("SELECT id, road_ref, mean_slope_deg, susceptibility FROM segment;")
    segments = cur.fetchall()

    affected_ids = []
    for seg in segments:
        road_ref = seg["road_ref"] or ""
        if any(ref.lower() in road_ref.lower() for ref in target_refs):
            affected_ids.append(seg["id"])

            # Recompute with injected rainfall
            rain_factor = min(1.0, max(0.0, (req.rain_24h_mm - 10.0) / 110.0))
            slope_factor = min(1.0, max(0.0, (seg["mean_slope_deg"] - 8.0) / 27.0))
            susc = seg["susceptibility"] or 0.0

            new_score = round((rain_factor * 0.34 + slope_factor * 0.22 + susc * 0.18 + 0.8 * 0.16 + 0.5 * 0.10) * 100.0, 1)

            if req.report_blockade:
                new_score = 95.0  # Hard blockade

            band = "hazard" if new_score >= 62.0 else "caution" if new_score >= 34.0 else "safe"

            risk_cache[seg["id"]] = {
                "score": new_score,
                "band": band,
                "factors": {
                    "rain": round(rain_factor, 3),
                    "slope": round(slope_factor, 3),
                    "susceptibility": round(susc, 3),
                    "history": 0.8,
                    "reports": 0.5,
                    "simulated": True,
                },
            }

    # Re-route with updated risks
    G = request.app.state.graph
    facilities = _load_facilities_list(db)

    alternatives = None
    if G:
        alternatives = route_all_alternatives(G, 101, 127, risk_cache, facilities)

    return {
        "status": "simulation_applied",
        "target": req.target_location,
        "rain_24h_mm": req.rain_24h_mm,
        "blockade_set": req.report_blockade,
        "affected_segment_count": len(affected_ids),
        "updated_routes": alternatives,
    }
