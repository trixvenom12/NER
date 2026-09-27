"""
api/routers/precursor.py — InSAR Satellite Precursor Layer Endpoints
"""

from fastapi import APIRouter
from typing import Dict, Any, List
from api.services.precursor_engine import precursor_service

router = APIRouter(prefix="/api/precursor", tags=["InSAR Precursors"])

@router.get("/alerts")
async def get_precursor_alerts():
    """
    Returns time-series anomaly detection alerts across pre-computed InSAR deformation sectors.
    Pairs ground displacement velocity anomalies (z-score > 2.0) with 72h antecedent rainfall.
    """
    return {
        "status": "active",
        "methodology": "Sentinel-1 DInSAR 2-pass interferometry + rolling z-score anomaly detector",
        "alerts": precursor_service.get_all_alerts()
    }

@router.get("/deformation")
async def get_deformation_layer():
    """
    Returns Sentinel-1 InSAR surface deformation polygon layer for high-risk slope sections
    (Sonapur Tunnel, Kseh Bilat, Lumshnong).
    """
    return precursor_service.get_deformation_geojson()
