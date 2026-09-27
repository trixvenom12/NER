"""
api/services/precursor_engine.py — InSAR Deformation & Rainfall Anomaly Detector
Module 6 implementation:
- Pre-computed Sentinel-1 surface deformation data over high-risk ghat sectors
- Time-series anomaly detector over displacement plus 72-hour antecedent rainfall
- Rolling z-score formulation with "watch" vs "high" hazard alert classification
"""

import json
import os
import numpy as np
from typing import List, Dict, Any, Union, Sequence

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PRECURSOR_DATA_PATH = os.path.join(_PROJECT_ROOT, "data", "precursor_deformation.geojson")

def rolling_z(series: Union[List[float], np.ndarray, Sequence[float]], window: int = 5) -> np.ndarray:
    """
    Computes rolling z-score across displacement time-series.
    z = (s - mu) / sd
    Captures accelerating ground creep velocity anomalies.
    """
    s = np.asarray(series, dtype=float)
    # Use window appropriate for short or long series
    win = min(window, len(s))
    if win < 2:
        return np.zeros_like(s)

    mu = np.convolve(s, np.ones(win) / win, mode="same")
    var = np.convolve((s - mu)**2, np.ones(win) / win, mode="same")
    sd = np.sqrt(np.maximum(var, 0.0)) + 1e-6
    return (s - mu) / sd

def detect_precursor_alerts(
    displacement_series: List[float],
    rain_72h_series: List[float],
    z_thresh: float = 1.8,
    rain_thresh: float = 80.0
) -> List[Dict[str, Any]]:
    """
    Detects slope failure precursor alerts:
    - Triggered when displacement anomaly z > z_thresh
    - Classified as 'high' alert when paired with heavy antecedent rain (> 80 mm)
    - Classified as 'watch' alert when rain is below saturation threshold
    """
    if not displacement_series or len(displacement_series) != len(rain_72h_series):
        return []

    # Displacements are typically negative (subsidence/descent), take absolute magnitude
    disp_mag = np.abs(np.array(displacement_series))
    z = rolling_z(disp_mag, window=5)

    alerts = []
    for i in range(len(z)):
        if z[i] > z_thresh:
            level = "high" if rain_72h_series[i] > rain_thresh else "watch"
            alerts.append({
                "time_step_index": int(i),
                "z_score": round(float(z[i]), 2),
                "displacement_mm": round(float(displacement_series[i]), 2),
                "rain_72h_mm": round(float(rain_72h_series[i]), 1),
                "level": level,
                "advisory": (
                    "CRITICAL: Satellite InSAR deformation anomaly detected coinciding with heavy antecedent rain. "
                    "Imminent slope failure likely within 12-24 hours."
                    if level == "high" else
                    "WATCH: Accelerating ground displacement detected via InSAR. Monitor slope drainage."
                )
            })

    return alerts

class PrecursorService:
    def __init__(self, geojson_path: str = PRECURSOR_DATA_PATH):
        self.geojson_path = geojson_path
        self._data = None
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.geojson_path):
            with open(self.geojson_path, "r") as f:
                self._data = json.load(f)
        else:
            self._data = {"type": "FeatureCollection", "features": []}

    def get_deformation_geojson(self) -> Dict[str, Any]:
        return self._data or {"type": "FeatureCollection", "features": []}

    def get_all_alerts(self) -> List[Dict[str, Any]]:
        results = []
        features = self._data.get("features", []) if self._data else []

        for feat in features:
            props = feat.get("properties", {})
            site_id = props.get("site_id", "Unknown")
            name = props.get("location_name", "Unknown")
            disp = props.get("recent_displacement_mm", [])
            rain = props.get("rain_72h_history_mm", [])

            alerts = detect_precursor_alerts(disp, rain)
            if alerts:
                latest_alert = alerts[-1]  # Most recent detection
                results.append({
                    "site_id": site_id,
                    "location_name": name,
                    "displacement_rate_mm_yr": props.get("displacement_mm_per_year"),
                    "latest_alert": latest_alert,
                    "all_triggers": alerts
                })

        return results

precursor_service = PrecursorService()
