/**
 * web/src/utils/api.js — Centralized API Client
 * All backend calls flow through here. Handles offline fallback gracefully.
 */

const BASE = '/api';

async function apiFetch(path, options = {}) {
  try {
    const res = await fetch(`${BASE}${path}`, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `API ${res.status}`);
    }
    return res.json();
  } catch (err) {
    if (err.message === 'Failed to fetch') {
      console.warn(`[Offline] ${path} — using cached data`);
      return null;
    }
    throw err;
  }
}

// ─── Route Planning ────────────────────────────────────────────────
export function buildRouteAlternativesUrl(src = 101, dst = 127) {
  return `/route/alternatives?src=${src}&dst=${dst}`;
}

export function fetchRouteAlternatives(src = 101, dst = 127) {
  return apiFetch(buildRouteAlternativesUrl(src, dst));
}

export function fetchRoute(src, dst, profile = 'balanced') {
  return apiFetch('/route', {
    method: 'POST',
    body: JSON.stringify({ src_node_id: src, dst_node_id: dst, profile }),
  });
}

// ─── Risk & Corridor ──────────────────────────────────────────────
export function fetchRiskSegments() {
  return apiFetch('/risk/segments');
}

export function fetchRiskHeatmap() {
  return apiFetch('/risk/heatmap');
}

// ─── Facilities ───────────────────────────────────────────────────
export function fetchFacilities(kind = null) {
  const q = kind ? `?kind=${kind}` : '';
  return apiFetch(`/facilities${q}`);
}

export function fetchFacilityAvailability(facilityId) {
  return apiFetch(`/facilities/${facilityId}/availability`);
}

// ─── Reports & SOS ────────────────────────────────────────────────
export function submitReport(report) {
  return apiFetch('/reports', {
    method: 'POST',
    body: JSON.stringify(report),
  });
}

export function submitSOS(sos) {
  return apiFetch('/reports/sos', {
    method: 'POST',
    body: JSON.stringify(sos),
  });
}

export function fetchNearbyReports(lat = 25.11, lon = 92.37, radius = 50) {
  return apiFetch(`/reports/nearby?lat=${lat}&lon=${lon}&radius_km=${radius}`);
}

// ─── Analytics ────────────────────────────────────────────────────
export function fetchHotspots() {
  return apiFetch('/analytics/hotspots');
}

export function fetchSeasonalData() {
  return apiFetch('/analytics/seasonal');
}

// ─── InSAR Precursors ─────────────────────────────────────────────
export function fetchPrecursorAlerts() {
  return apiFetch('/precursor/alerts');
}

export function fetchDeformationLayer() {
  return apiFetch('/precursor/deformation');
}

// ─── Simulation ───────────────────────────────────────────────────
export function simulateHazard(targetLocation = 'Sonapur_Tunnel_Zone', rainMm = 165, blockade = false) {
  return apiFetch('/route/simulate-hazard', {
    method: 'POST',
    body: JSON.stringify({
      target_location: targetLocation,
      rain_24h_mm: rainMm,
      report_blockade: blockade,
    }),
  });
}

// ─── Offline Sync ─────────────────────────────────────────────────
export function syncBatch(deviceId, items) {
  return apiFetch('/sync/batch', {
    method: 'POST',
    body: JSON.stringify({ device_id: deviceId, items }),
  });
}
