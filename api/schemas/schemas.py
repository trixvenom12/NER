"""
api/schemas/schemas.py — Pydantic v2 Models for Requests and Responses
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class RouteRequest(BaseModel):
    src_node_id: int = Field(default=101, description="Origin Node ID (e.g. 101 Guwahati)")
    dst_node_id: int = Field(default=127, description="Destination Node ID (e.g. 127 Silchar)")
    profile: str = Field(default="balanced", description="fastest | balanced | safest")

class DeltaInfo(BaseModel):
    distance_km: float
    duration_min: float

class SegmentDetail(BaseModel):
    id: int
    u: int
    v: int
    road_ref: str
    highway: str
    length_m: float
    free_speed_kph: int
    score: float
    band: str
    factors: Dict[str, Any]

class AdvisoryItem(BaseModel):
    at_km: float
    level: str
    text: str
    dominant_factor: Optional[str] = None
    facility_id: Optional[int] = None
    segment_id: Optional[int] = None

class RouteResponse(BaseModel):
    profile: str
    path_found: bool
    distance_km: float
    duration_min: float
    delta_vs_fastest: DeltaInfo
    max_risk: float
    mean_risk: float
    node_ids: List[int]
    geometry: Dict[str, Any]
    segments: List[SegmentDetail]
    advisories: List[AdvisoryItem]

class RouteAlternativesResponse(BaseModel):
    src: int
    dst: int
    routes: Dict[str, Any]

class ReportCreate(BaseModel):
    device_id: str = Field(default="dev-trucker-01")
    kind: str = Field(..., description="blocked | slide | water | sos")
    note: Optional[str] = None
    lat: float
    lon: float

class SOSRequest(BaseModel):
    device_id: str
    lat: float
    lon: float
    note: Optional[str] = "EMERGENCY: Driver activated 2-second hold SOS distress signal"
    last_known_route: Optional[List[int]] = None

class SyncBatchItem(BaseModel):
    client_id: str
    kind: str
    lat: float
    lon: float
    created_at: str
    note: Optional[str] = None

class SyncBatchRequest(BaseModel):
    device_id: str
    items: List[SyncBatchItem]

class SyncBatchResponseItem(BaseModel):
    client_id: str
    status: str
    server_id: int

class SyncBatchResponse(BaseModel):
    results: List[SyncBatchResponseItem]

class RiskSimulationRequest(BaseModel):
    target_location: str = Field(default="Sonapur_Tunnel_Zone", description="Sonapur_Tunnel_Zone | Lumshnong_Ghat | Umiam_Barapani")
    rain_24h_mm: float = Field(default=165.0, description="Simulated 24h rainfall in mm")
    report_blockade: bool = Field(default=False, description="Set confirmed road blockade (r >= 0.92)")
