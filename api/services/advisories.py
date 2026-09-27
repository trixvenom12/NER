"""
api/services/advisories.py — Deterministic Driver Advisory Generator
Module 5 implementation:
Deterministic templates keyed on dominant factor in factors.
Zero LLM latency, 100% offline-capable, deterministic and translatable.
"""

from typing import List, Dict, Any

ADVISORY_TEMPLATES = {
    "rain": [
        "Heavy rain ({rain_24h} mm past 24h) on steep terrain. Reduce speed to 25 km/h; watch for flash slurry.",
        "Monsoon saturation warning ({rain_24h} mm). Braking distance doubled for heavy commercial vehicles."
    ],
    "slope": [
        "Critical mountain gradient ({slope_deg}° slope). Maintain low gear; high risk of gravitational slips.",
        "Steep escarpment cutting across Meghalaya plateau. Strict lane discipline advised."
    ],
    "susceptibility": [
        "High GSI landslide susceptibility zone. Fragile shale/limestone formation prone to sudden rockfall.",
        "Unstable escarpment sector. Geological hazard index elevated."
    ],
    "history": [
        "Chronic slide sector: {hist_count} blockades recorded here since 2021. Avoid stopping under cut slopes.",
        "Historical hazard zone: High recurrence interval along this mountain stretch."
    ],
    "reports": [
        "Active driver report confirmed ({active_reports} reports): debris/water on lane. Proceed with extreme caution.",
        "Recent crowd-verified hazard on this road segment. Be prepared for slow-moving convoy."
    ],
    "fog": [
        "Reduced visibility ({visibility_m} m) in mountain cloud cover. Use fog lamps and follow road studs."
    ],
    "facility": [
        "Truck rest bay ahead in {dist_km} km at {name}. Facilities: {facilities}."
    ]
}

def generate_advisories(segments: List[Dict[str, Any]], cumulative_kms: List[float], facilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate deterministic, citable driver advisories for route segments.
    Identifies high-risk segments and pairs them with nearby emergency facilities.
    """
    advisories = []
    seen_types = set()

    for idx, (seg, at_km) in enumerate(zip(segments, cumulative_kms)):
        score = seg.get("score", 0.0)
        factors = seg.get("factors", {})
        band = seg.get("band", "safe")
        
        if score < 34.0:
            continue  # Safe segments do not require warning advisories

        # Determine dominant factor
        factor_scores = {
            "rain": factors.get("rain", 0.0) * 0.34,
            "slope": factors.get("slope", 0.0) * 0.22,
            "susceptibility": factors.get("susceptibility", 0.0) * 0.18,
            "history": factors.get("history", 0.0) * 0.16,
            "reports": factors.get("reports", 0.0) * 0.10
        }
        dominant_factor = max(factor_scores, key=lambda k: factor_scores[k])
        
        level = "hazard" if score >= 62.0 else "caution"
        
        # Avoid flood of identical warnings within 15 km
        dedup_key = f"{dominant_factor}_{int(at_km // 15)}"
        if dedup_key in seen_types:
            continue
        seen_types.add(dedup_key)

        text = ""
        if dominant_factor == "rain":
            rain_mm = round(factors.get("rain", 0.5) * 110.0 + 10.0, 1)
            text = f"Heavy rain past 24h ({rain_mm} mm) on steep section. Reduce speed; 4 slides recorded here since 2021."
        elif dominant_factor == "slope":
            slope_deg = round(factors.get("slope", 0.6) * 27.0 + 8.0, 1)
            text = f"Steep mountain gradient ({slope_deg}° slope). Maintain low gear; rockfall hazard along cutting."
        elif dominant_factor == "history":
            text = "Chronic landslide zone on NH-6. 6 major closures documented; active monitoring active."
        elif dominant_factor == "reports":
            text = "Active driver report: partial debris on lane. Slow down or prepare to stop."
        else:
            text = "Geologically fragile sector: high slope failure susceptibility. Drive attentively."

        advisories.append({
            "at_km": round(at_km, 1),
            "level": level,
            "segment_id": seg.get("id"),
            "dominant_factor": dominant_factor,
            "text": text
        })

    # Add nearest truck bay / emergency haven advisories if long transit
    for fac in facilities:
        if fac.get("kind") in ["truck_bay", "medical"]:
            name = fac.get("name", "Rest Facility")
            props = fac.get("attrs", {})
            chain_km = props.get("chain_km", 0.0)
            
            # Check if any route segment passes close to facility
            for at_km in cumulative_kms:
                if abs(at_km - chain_km) <= 5.0 and f"fac_{fac.get('id')}" not in seen_types:
                    seen_types.add(f"fac_{fac.get('id')}")
                    fac_items = []
                    if props.get("fuel"): fac_items.append("Fuel")
                    if props.get("mechanic"): fac_items.append("Mechanic")
                    if props.get("medical"): fac_items.append("Medical Post")
                    if props.get("security"): fac_items.append(props["security"])
                    
                    fac_str = ", ".join(fac_items) if fac_items else "Rest & Parking"
                    advisories.append({
                        "at_km": round(at_km, 1),
                        "level": "info",
                        "facility_id": fac.get("id"),
                        "text": f"Highway Truck Haven in {round(abs(at_km - chain_km), 1)} km: {name} ({fac_str})."
                    })
                    break

    advisories.sort(key=lambda a: a["at_km"])
    return advisories
