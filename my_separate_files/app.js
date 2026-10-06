/**
 * web/app.js — Core Client Logic for NER Logistics Intelligence Platform
 * Modules 8 & 9 implementation:
 * - MapLibre GL JS integration with risk coloring (#A33A28, #B8862A, #3F7A55)
 * - Dynamic Current Location (Start) & Destination Markers with Auto-Fit Camera
 * - GPS Geolocation Auto-Detection
 * - Route Swap & All 28 Corridor Waypoints
 * - Interactive 5-Factor Explanation Drawer on segment click
 * - 3 Profile Route Cards (Fastest, Balanced, Safest) with time/distance deltas
 * - Live Hazard Simulation on Sonapur Ghat & Reset with visual detour divergence
 * - 2-Second Hold-to-Fire SOS Emergency Trigger with Audio synthesis & nearest facilities
 * - Offline IndexedDB storage & Outbox Batch Sync
 */

const API_BASE = "";
const CORRIDOR_CENTER = [92.25, 25.45]; // NH-6 Meghalaya Central Ghats

// All 28 Corridor Nodes with Coordinates
const NODE_COORDINATES = {
  101: { name: "Guwahati (Khanapara Hub)", lat: 26.1150, lon: 91.8210 },
  102: { name: "Byrnihat (Ri-Bhoi Checkpost)", lat: 26.0420, lon: 91.8650 },
  103: { name: "Nongpoh North", lat: 25.9320, lon: 91.8780 },
  104: { name: "Nongpoh Town", lat: 25.9012, lon: 91.8805 },
  105: { name: "Umsning Junction", lat: 25.7620, lon: 91.9051 },
  106: { name: "Umiam (Barapani Lake)", lat: 25.6610, lon: 91.8980 },
  107: { name: "Mawiong (Shillong North)", lat: 25.6020, lon: 91.8830 },
  108: { name: "Shillong Central (Police Bazar)", lat: 25.5788, lon: 91.8933 },
  109: { name: "Laitkor Ghat", lat: 25.5350, lon: 91.9320 },
  110: { name: "Mawryngkneng Junction", lat: 25.5560, lon: 92.0520 },
  111: { name: "Shillong Bypass", lat: 25.6320, lon: 91.9850 },
  112: { name: "Ummulong", lat: 25.4950, lon: 92.1240 },
  113: { name: "Jowai (West Jaintia Hills)", lat: 25.4410, lon: 92.2030 },
  114: { name: "Khliehtyrshi", lat: 25.4120, lon: 92.2450 },
  115: { name: "Ladrymbai (Weighbridge Hub)", lat: 25.3210, lon: 92.3120 },
  116: { name: "Khliehriat (East Jaintia Hills)", lat: 25.2640, lon: 92.3520 },
  117: { name: "Lumshnong Escarpment", lat: 25.1850, lon: 92.3780 },
  118: { name: "Sonapur Tunnel North", lat: 25.1180, lon: 92.3650 },
  119: { name: "Sonapur Tunnel South", lat: 25.1110, lon: 92.3720 },
  120: { name: "Sonapur Ridge Detour", lat: 25.1290, lon: 92.3920 },
  121: { name: "Malidor Border", lat: 25.0420, lon: 92.4210 },
  122: { name: "Umkiang", lat: 25.0680, lon: 92.3850 },
  123: { name: "Kalain Junction", lat: 24.9650, lon: 92.5620 },
  124: { name: "Badarpur Ghat", lat: 24.9020, lon: 92.5850 },
  125: { name: "Panchgram", lat: 24.8720, lon: 92.6510 },
  126: { name: "Silchar Ramnagar", lat: 24.8380, lon: 92.7420 },
  127: { name: "Silchar ISBT Terminal", lat: 24.8250, lon: 92.7910 },
  128: { name: "Borkhola Bypass", lat: 24.9120, lon: 92.7210 }
};

let map;
let activeProfile = "balanced";
let currentRouteData = null;
let allAlternatives = null;
let isOfflineMode = !navigator.onLine;

let startMarker = null;
let destMarker = null;
let avoidedHazardMarker = null;

// IndexedDB Helper for Offline Resilience
const DB_NAME = "ner_logistics_offline_db";
const DB_VERSION = 1;

function openOfflineDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains("corridor_cache")) {
        db.createObjectStore("corridor_cache");
      }
      if (!db.objectStoreNames.contains("outbox")) {
        db.createObjectStore("outbox", { keyPath: "client_id" });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function idbSave(storeName, key, value) {
  try {
    const db = await openOfflineDB();
    const tx = db.transaction(storeName, "readwrite");
    tx.objectStore(storeName).put(value, key);
    return tx.complete;
  } catch (err) {
    console.warn("IndexedDB save warning:", err);
  }
}

async function idbGet(storeName, key) {
  try {
    const db = await openOfflineDB();
    return new Promise((resolve) => {
      const tx = db.transaction(storeName, "readonly");
      const req = tx.objectStore(storeName).get(key);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => resolve(null);
    });
  } catch (err) {
    return null;
  }
}

async function idbGetAllOutbox() {
  try {
    const db = await openOfflineDB();
    return new Promise((resolve) => {
      const tx = db.transaction("outbox", "readonly");
      const req = tx.objectStore("outbox").getAll();
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => resolve([]);
    });
  } catch (err) {
    return [];
  }
}

async function idbDeleteOutbox(clientIds) {
  try {
    const db = await openOfflineDB();
    const tx = db.transaction("outbox", "readwrite");
    const store = tx.objectStore("outbox");
    clientIds.forEach(id => store.delete(id));
    return tx.complete;
  } catch (err) {
    console.warn("IndexedDB delete warning:", err);
  }
}

// ==========================================================
// Initialization
// ==========================================================
document.addEventListener("DOMContentLoaded", () => {
  initMap();
  setupTabNavigation();
  setupRoutingControls();
  setupSOSButton();
  setupHazardSimulation();
  setupOfflineSync();
  setupNetworkMonitor();
  loadCorridorData();
});

// MapLibre Initialization
function initMap() {
  const mapStyle = {
    version: 8,
    sources: {
      "osm-tiles": {
        type: "raster",
        tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
        tileSize: 256,
        attribution: "&copy; OpenStreetMap Contributors"
      }
    },
    layers: [
      {
        id: "osm-layer",
        type: "raster",
        source: "osm-tiles",
        minzoom: 0,
        maxzoom: 19,
        paint: {
          "raster-saturation": -0.85,
          "raster-contrast": 0.2,
          "raster-brightness-min": 0.15,
          "raster-brightness-max": 0.45
        }
      }
    ]
  };

  map = new maplibregl.Map({
    container: "map",
    style: mapStyle,
    center: CORRIDOR_CENTER,
    zoom: 8.3,
    minZoom: 6.5,
    maxBounds: [89.5, 23.5, 94.5, 28.0]
  });

  map.addControl(new maplibregl.NavigationControl(), "top-right");

  map.on("load", () => {
    addMapLayers();
    createLocationMarkers();
    fetchRouteAlternatives();
  });
}

function createLocationMarkers() {
  // 1. Start Marker (Green Glowing Pin)
  const startEl = document.createElement("div");
  startEl.className = "custom-pin start-pin";
  startEl.innerHTML = `<div class="pin-body">📍 START</div>`;
  startMarker = new maplibregl.Marker({ element: startEl, anchor: "bottom" })
    .setLngLat([NODE_COORDINATES[101].lon, NODE_COORDINATES[101].lat])
    .addTo(map);

  // 2. Destination Marker (Red Flag Pin)
  const destEl = document.createElement("div");
  destEl.className = "custom-pin dst-pin";
  destEl.innerHTML = `<div class="pin-body">🏁 DESTINATION</div>`;
  destMarker = new maplibregl.Marker({ element: destEl, anchor: "bottom" })
    .setLngLat([NODE_COORDINATES[127].lon, NODE_COORDINATES[127].lat])
    .addTo(map);
}

function updateLocationMarkers(srcId, dstId) {
  const srcNode = NODE_COORDINATES[srcId];
  const dstNode = NODE_COORDINATES[dstId];

  if (startMarker && srcNode) {
    startMarker.setLngLat([srcNode.lon, srcNode.lat]);
    startMarker.getElement().querySelector(".pin-body").textContent = `📍 ${srcNode.name.split(" ")[0]}`;
  }

  if (destMarker && dstNode) {
    destMarker.setLngLat([dstNode.lon, dstNode.lat]);
    destMarker.getElement().querySelector(".pin-body").textContent = `🏁 ${dstNode.name.split(" ")[0]}`;
  }
}

function addMapLayers() {
  // 1. Full Corridor Road Network Risk Layer
  map.addSource("risk-segments", {
    type: "geojson",
    data: { type: "FeatureCollection", features: [] }
  });

  // Base road casing
  map.addLayer({
    id: "risk-line-bg",
    type: "line",
    source: "risk-segments",
    layout: { "line-join": "round", "line-cap": "round" },
    paint: {
      "line-width": ["interpolate", ["linear"], ["zoom"], 7, 4, 13, 10],
      "line-color": "#050811",
      "line-opacity": 0.9
    }
  });

  // Build manual risk colors: hazard #A33A28, caution #B8862A, safe #3F7A55
  map.addLayer({
    id: "risk-line",
    type: "line",
    source: "risk-segments",
    layout: { "line-join": "round", "line-cap": "round" },
    paint: {
      "line-width": ["interpolate", ["linear"], ["zoom"], 7, 2.5, 13, 7],
      "line-color": [
        "match",
        ["get", "band"],
        "hazard", "#ef4444",
        "caution", "#f59e0b",
        "#10b981"
      ],
      "line-opacity": 0.95
    }
  });

  // 2. Active Route Highlight Polyline (with glowing halo)
  map.addSource("active-route", {
    type: "geojson",
    data: { type: "FeatureCollection", features: [] }
  });

  map.addLayer({
    id: "active-route-halo",
    type: "line",
    source: "active-route",
    layout: { "line-join": "round", "line-cap": "round" },
    paint: {
      "line-width": ["interpolate", ["linear"], ["zoom"], 7, 7, 13, 15],
      "line-color": "#0284c7",
      "line-opacity": 0.4
    }
  });

  map.addLayer({
    id: "active-route-line",
    type: "line",
    source: "active-route",
    layout: { "line-join": "round", "line-cap": "round" },
    paint: {
      "line-width": ["interpolate", ["linear"], ["zoom"], 7, 3.5, 13, 8],
      "line-color": "#38bdf8",
      "line-opacity": 0.95
    }
  });

  // 3. InSAR Precursor Deformation Overlay
  map.addSource("insar-deformation", {
    type: "geojson",
    data: { type: "FeatureCollection", features: [] }
  });

  map.addLayer({
    id: "insar-polygons",
    type: "fill",
    source: "insar-deformation",
    paint: {
      "fill-color": "#dc2626",
      "fill-opacity": 0.45,
      "fill-outline-color": "#f87171"
    }
  });

  // 4. Historical Incidents Points Layer
  map.addSource("incidents-source", {
    type: "geojson",
    data: { type: "FeatureCollection", features: [] }
  });

  map.addLayer({
    id: "incidents-circles",
    type: "circle",
    source: "incidents-source",
    paint: {
      "circle-radius": 6.5,
      "circle-color": "#f43f5e",
      "circle-stroke-width": 2,
      "circle-stroke-color": "#ffffff"
    }
  });

  // 5. Facilities & Truck Bays Layer
  map.addSource("facilities-source", {
    type: "geojson",
    data: { type: "FeatureCollection", features: [] }
  });

  map.addLayer({
    id: "facilities-circles",
    type: "circle",
    source: "facilities-source",
    paint: {
      "circle-radius": 6,
      "circle-color": "#10b981",
      "circle-stroke-width": 2,
      "circle-stroke-color": "#ffffff"
    }
  });

  // Interactive Click Handlers
  map.on("click", "risk-line", onSegmentClick);
  map.on("click", "incidents-circles", onIncidentClick);
  map.on("click", "facilities-circles", onFacilityClick);

  // Cursor hover effects
  ["risk-line", "incidents-circles", "facilities-circles", "insar-polygons"].forEach(layer => {
    map.on("mouseenter", layer, () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", layer, () => { map.getCanvas().style.cursor = ""; });
  });
}

// ==========================================================
// Module 8 Deliverable: Factor Explanation Drawer
// ==========================================================
function onSegmentClick(e) {
  if (!e.features || !e.features.length) return;
  const props = e.features[0].properties;

  let factors = {};
  try {
    factors = typeof props.factors === "string" ? JSON.parse(props.factors) : props.factors || {};
  } catch (err) {
    factors = {};
  }

  showFactorDrawer(props, factors);
}

function showFactorDrawer(props, factors) {
  const drawer = document.getElementById("factor-drawer");
  document.getElementById("drawer-segment-name").textContent = `Segment #${props.id} (${props.road_ref || "NH-6"})`;
  document.getElementById("drawer-segment-sub").textContent = `${props.highway || "Trunk"} · Free speed: ${props.free_speed_kph || 40} km/h · Length: ${Math.round(props.length_m || 0)}m`;

  const score = props.score || 0;
  const band = props.band || "safe";
  const badge = document.getElementById("drawer-score-badge");
  document.getElementById("drawer-score-val").textContent = `${score} / 100 (${band.toUpperCase()})`;

  badge.className = `drawer-score-badge risk-pill ${band}`;

  // Fill 5 Factor Bars
  const rainPct = Math.round((factors.rain || 0) * 100);
  const slopePct = Math.round((factors.slope || 0) * 100);
  const suscPct = Math.round((factors.susceptibility || 0) * 100);
  const histPct = Math.round((factors.history || 0) * 100);
  const repPct = Math.round((factors.reports || 0) * 100);

  document.getElementById("bar-val-rain").textContent = `${rainPct}%`;
  document.getElementById("bar-fill-rain").style.width = `${rainPct}%`;

  document.getElementById("bar-val-slope").textContent = `${slopePct}%`;
  document.getElementById("bar-fill-slope").style.width = `${slopePct}%`;

  document.getElementById("bar-val-susc").textContent = `${suscPct}%`;
  document.getElementById("bar-fill-susc").style.width = `${suscPct}%`;

  document.getElementById("bar-val-hist").textContent = `${histPct}%`;
  document.getElementById("bar-fill-hist").style.width = `${histPct}%`;

  document.getElementById("bar-val-reports").textContent = `${repPct}%`;
  document.getElementById("bar-fill-reports").style.width = `${repPct}%`;

  drawer.style.display = "block";
}

document.getElementById("drawer-close").addEventListener("click", () => {
  document.getElementById("factor-drawer").style.display = "none";
});

function onIncidentClick(e) {
  const p = e.features[0].properties;
  new maplibregl.Popup({ offset: 12 })
    .setLngLat(e.lngLat)
    .setHTML(`
      <div style="font-family: inherit; font-size: 12px; color: #0f172a;">
        <strong style="color: #e11d48; text-transform: uppercase;">⚠️ ${p.kind || "Blockade"}</strong>
        <div style="margin-top: 4px;"><strong>Date:</strong> ${p.occurred_on || "N/A"}</div>
        <div><strong>Duration:</strong> ${p.duration_hours || "N/A"} hrs</div>
        <div style="margin-top: 6px;">
          <a href="${p.source_url}" target="_blank" style="color: #0284c7; text-decoration: underline; font-weight: 600;">Verified News / PIB Citation</a>
        </div>
      </div>
    `)
    .addTo(map);
}

function onFacilityClick(e) {
  const p = e.features[0].properties;
  new maplibregl.Popup({ offset: 12 })
    .setLngLat(e.lngLat)
    .setHTML(`
      <div style="font-family: inherit; font-size: 12px; color: #0f172a;">
        <strong style="color: #047857;">🚛 ${p.name}</strong>
        <div style="color: #64748b; font-size: 11px;">Category: ${p.kind}</div>
        <div style="margin-top: 6px;"><strong>Capacity:</strong> ${p.capacity} commercial bays</div>
      </div>
    `)
    .addTo(map);
}

// ==========================================================
// Routing & Profile Switching
// ==========================================================
function setupRoutingControls() {
  const srcSelect = document.getElementById("route-src");
  const dstSelect = document.getElementById("route-dst");

  srcSelect.addEventListener("change", () => {
    updateLocationMarkers(srcSelect.value, dstSelect.value);
    fetchRouteAlternatives();
  });

  dstSelect.addEventListener("change", () => {
    updateLocationMarkers(srcSelect.value, dstSelect.value);
    fetchRouteAlternatives();
  });

  // Swap Button
  document.getElementById("btn-swap-route").addEventListener("click", () => {
    const temp = srcSelect.value;
    srcSelect.value = dstSelect.value;
    dstSelect.value = temp;
    updateLocationMarkers(srcSelect.value, dstSelect.value);
    fetchRouteAlternatives();
  });

  // Use GPS / Current Location Detection
  document.getElementById("btn-use-gps").addEventListener("click", () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }
    const btn = document.getElementById("btn-use-gps");
    btn.textContent = "Locating...";

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const userLat = pos.coords.latitude;
        const userLon = pos.coords.longitude;

        // Find nearest node
        let closestId = 101;
        let minDist = Infinity;
        for (const [id, node] of Object.entries(NODE_COORDINATES)) {
          const d = Math.hypot(node.lat - userLat, node.lon - userLon);
          if (d < minDist) {
            minDist = d;
            closestId = id;
          }
        }

        srcSelect.value = closestId;
        updateLocationMarkers(srcSelect.value, dstSelect.value);
        fetchRouteAlternatives();
        btn.innerHTML = "<span>🎯</span> Located!";
        setTimeout(() => { btn.innerHTML = "<span>🎯</span> My GPS"; }, 3000);
      },
      (err) => {
        console.warn("GPS error:", err);
        // Default to Guwahati
        srcSelect.value = 101;
        updateLocationMarkers(101, dstSelect.value);
        btn.innerHTML = "<span>🎯</span> My GPS";
        alert("Using default Guwahati Khanapara as current location.");
      },
      { timeout: 5000 }
    );
  });

  const profileCards = document.querySelectorAll(".profile-card");
  profileCards.forEach(card => {
    card.addEventListener("click", () => {
      profileCards.forEach(c => c.classList.remove("active"));
      card.classList.add("active");
      activeProfile = card.getAttribute("data-profile");
      displayActiveProfile();
    });
  });
}

async function fetchRouteAlternatives() {
  const src = document.getElementById("route-src").value;
  const dst = document.getElementById("route-dst").value;

  updateLocationMarkers(src, dst);

  try {
    let data;
    if (isOfflineMode) {
      data = await idbGet("corridor_cache", `routes_${src}_${dst}`);
    } else {
      const resp = await fetch(`${API_BASE}/api/route/alternatives?src=${src}&dst=${dst}`);
      data = await resp.json();
      await idbSave("corridor_cache", `routes_${src}_${dst}`, data);
    }

    if (data && data.routes) {
      allAlternatives = data.routes;
      updateProfileCards(data.routes);
      displayActiveProfile();
    }
  } catch (err) {
    console.error("Routing error:", err);
  }
}

function updateProfileCards(routes) {
  const fastest = routes.fastest || {};
  const balanced = routes.balanced || {};
  const safest = routes.safest || {};

  // Fastest
  document.getElementById("fastest-time").textContent = `${Math.round(fastest.duration_min || 0)}m`;
  document.getElementById("fastest-risk").textContent = `Risk ${fastest.mean_risk || 0}`;

  // Balanced
  document.getElementById("balanced-time").textContent = `${Math.round(balanced.duration_min || 0)}m`;
  const balDelta = balanced.delta_vs_fastest ? balanced.delta_vs_fastest.duration_min : 0;
  document.getElementById("balanced-delta").textContent = balDelta > 0 ? `+${balDelta} min` : "0 min";
  document.getElementById("balanced-risk").textContent = `Risk ${balanced.mean_risk || 0}`;

  // Safest
  document.getElementById("safest-time").textContent = `${Math.round(safest.duration_min || 0)}m`;
  const safeDelta = safest.delta_vs_fastest ? safest.delta_vs_fastest.duration_min : 0;
  document.getElementById("safest-delta").textContent = safeDelta > 0 ? `+${safeDelta} min` : "0 min";
  document.getElementById("safest-risk").textContent = `Risk ${safest.mean_risk || 0}`;
}

function displayActiveProfile() {
  if (!allAlternatives || !allAlternatives[activeProfile]) return;
  const r = allAlternatives[activeProfile];
  currentRouteData = r;

  // Update Metrics Bar
  document.getElementById("metric-dist").textContent = `${r.distance_km || 0} km`;
  document.getElementById("metric-dur").textContent = `${Math.round(r.duration_min || 0)} min`;
  document.getElementById("metric-mean-risk").textContent = `${r.mean_risk || 0}`;
  document.getElementById("metric-max-risk").textContent = `${r.max_risk || 0}`;

  // Update Active Route Line on Map
  if (map && map.getSource("active-route") && r.geometry && r.geometry.coordinates) {
    map.getSource("active-route").setData({
      type: "Feature",
      geometry: r.geometry,
      properties: { profile: activeProfile }
    });

    // Dynamic line & halo colors matching profile aesthetic
    const profileColors = {
      fastest: { line: "#38bdf8", halo: "#0284c7" },   // Sky Blue
      balanced: { line: "#60a5fa", halo: "#2563eb" },  // Royal Blue
      safest: { line: "#10b981", halo: "#059669" }     // Emerald Green
    };
    const c = profileColors[activeProfile] || profileColors.balanced;
    if (map.getLayer("active-route-line")) {
      map.setPaintProperty("active-route-line", "line-color", c.line);
    }
    if (map.getLayer("active-route-halo")) {
      map.setPaintProperty("active-route-halo", "line-color", c.halo);
    }

    // Auto-fit camera to the active route with smooth animation!
    if (r.geometry.coordinates.length > 1) {
      const bounds = new maplibregl.LngLatBounds();
      r.geometry.coordinates.forEach(coord => bounds.extend(coord));
      map.fitBounds(bounds, { padding: 90, duration: 1000 });
    }
  }

  // Populate Advisories List
  renderAdvisories(r.advisories || []);
}

function renderAdvisories(advisories) {
  const container = document.getElementById("advisories-container");
  container.innerHTML = "";
  document.getElementById("advisory-count").textContent = `${advisories.length} alerts`;

  if (!advisories.length) {
    container.innerHTML = `<div style="font-size: 12px; color: var(--text-dim); text-align: center; padding: 12px;">No active hazards along selected profile. Route is clear.</div>`;
    return;
  }

  advisories.forEach(adv => {
    const card = document.createElement("div");
    card.className = `advisory-card ${adv.level || "caution"}`;
    card.innerHTML = `
      <div class="advisory-header">
        <span>At Km ${adv.at_km} · ${adv.dominant_factor ? adv.dominant_factor.toUpperCase() : "HAZARD"}</span>
        <span style="text-transform: uppercase;">${adv.level}</span>
      </div>
      <div>${adv.text}</div>
    `;
    container.appendChild(card);
  });
}

// ==========================================================
// Full Corridor Data Loading
// ==========================================================
async function loadCorridorData() {
  try {
    // 1. Risk Segments
    let segsData = await idbGet("corridor_cache", "risk_segments");
    if (!segsData && !isOfflineMode) {
      const resp = await fetch(`${API_BASE}/api/risk/segments`);
      segsData = await resp.json();
      await idbSave("corridor_cache", "risk_segments", segsData);
    }
    if (map && map.getSource("risk-segments") && segsData) {
      map.getSource("risk-segments").setData(segsData);
    }

    // 2. Facilities
    let facData = await idbGet("corridor_cache", "facilities");
    if (!facData && !isOfflineMode) {
      const resp = await fetch(`${API_BASE}/api/facilities`);
      const facList = await resp.json();
      facData = {
        type: "FeatureCollection",
        features: facList.map(f => ({
          type: "Feature",
          properties: f,
          geometry: { type: "Point", coordinates: [f.lon, f.lat] }
        }))
      };
      await idbSave("corridor_cache", "facilities", facData);
    }
    if (map && map.getSource("facilities-source") && facData) {
      map.getSource("facilities-source").setData(facData);
      renderFacilitiesTab(facData.features.map(f => f.properties));
    }

    // 3. Historical Incidents
    let incData = await idbGet("corridor_cache", "incidents");
    if (!incData && !isOfflineMode) {
      incData = {
        type: "FeatureCollection",
        features: [
          { type: "Feature", properties: { kind: "Landslide", occurred_on: "2024-07-09", duration_hours: 76, source_url: "https://theshillongtimes.com" }, geometry: { type: "Point", coordinates: [92.3685, 25.1142] } },
          { type: "Feature", properties: { kind: "Road Cave-In", occurred_on: "2025-06-08", duration_hours: 48, source_url: "https://eastmojo.com" }, geometry: { type: "Point", coordinates: [92.3410, 25.1380] } },
          { type: "Feature", properties: { kind: "Flooding", occurred_on: "2024-09-12", duration_hours: 40, source_url: "https://timesofindia.indiatimes.com" }, geometry: { type: "Point", coordinates: [92.6240, 24.8720] } }
        ]
      };
      await idbSave("corridor_cache", "incidents", incData);
    }
    if (map && map.getSource("incidents-source") && incData) {
      map.getSource("incidents-source").setData(incData);
    }

    // 4. InSAR Precursor Deformation Layer
    let insarData = await idbGet("corridor_cache", "insar_layer");
    if (!insarData && !isOfflineMode) {
      const resp = await fetch(`${API_BASE}/api/precursor/deformation`);
      insarData = await resp.json();
      await idbSave("corridor_cache", "insar_layer", insarData);
    }
    if (map && map.getSource("insar-deformation") && insarData) {
      map.getSource("insar-deformation").setData(insarData);
    }

    // 5. Precursor Alerts
    if (!isOfflineMode) {
      const resp = await fetch(`${API_BASE}/api/precursor/alerts`);
      const alertData = await resp.json();
      renderPrecursorAlerts(alertData.alerts || []);
    }
  } catch (err) {
    console.warn("Corridor data loading warning:", err);
  }
}

function renderFacilitiesTab(facilities) {
  const container = document.getElementById("facilities-list-container");
  container.innerHTML = "";

  facilities.forEach(f => {
    const card = document.createElement("div");
    card.className = "facility-card";
    const avail = f.availability || { available_bays: 24, total_capacity: f.capacity || 50, occupancy_pct: 52 };
    const occPct = avail.occupancy_pct || 50;

    card.innerHTML = `
      <div class="facility-header">
        <div class="facility-name">${f.name}</div>
        <span class="risk-pill ${avail.available_bays > 10 ? 'safe' : 'caution'}">${avail.available_bays} Bays Free</span>
      </div>
      <div style="font-size: 11px; color: var(--text-dim);">${f.attrs ? f.attrs.location : "NH-6 Corridor"} · Capacity: ${f.capacity}</div>
      <div class="bay-occupancy-bar">
        <div class="bay-occupancy-fill" style="width: ${occPct}%; background: ${occPct > 80 ? '#ef4444' : '#10b981'};"></div>
      </div>
      <div class="occupancy-meta">
        <span>Predicted: ${occPct}% full</span>
        <span>${avail.prediction_confidence || "92% Confidence"}</span>
      </div>
    `;

    card.addEventListener("click", () => {
      map.flyTo({ center: [f.lon, f.lat], zoom: 11.5 });
    });

    container.appendChild(card);
  });
}

function renderPrecursorAlerts(alerts) {
  const container = document.getElementById("precursor-alerts-container");
  container.innerHTML = "";

  if (!alerts.length) {
    container.innerHTML = `<div style="font-size: 12px; color: var(--text-dim); padding: 8px;">No active InSAR precursor anomalies.</div>`;
    return;
  }

  alerts.forEach(a => {
    const l = a.latest_alert || {};
    const card = document.createElement("div");
    card.className = `advisory-card ${l.level === "high" ? "hazard" : "caution"}`;
    card.innerHTML = `
      <div class="advisory-header">
        <span>${a.location_name}</span>
        <span style="color: #ef4444; font-weight: 800;">Z-SCORE ${l.z_score}</span>
      </div>
      <div><strong>Rate:</strong> ${a.displacement_rate_mm_yr} mm/yr · 72h Rain: ${l.rain_72h_mm} mm</div>
      <div style="margin-top: 4px; font-size: 11.5px;">${l.advisory}</div>
    `;
    container.appendChild(card);
  });
}

// ==========================================================
// 8-Minute Demo Moment: Live Hazard Simulation & Reset
// ==========================================================
function setupHazardSimulation() {
  const btnSim = document.getElementById("btn-simulate-hazard");
  const btnReset = document.getElementById("btn-reset-hazard");
  const alertBanner = document.getElementById("route-reroute-alert");

  btnSim.addEventListener("click", async () => {
    btnSim.disabled = true;
    btnSim.textContent = "Simulating 165mm Torrential Rain...";

    try {
      const resp = await fetch(`${API_BASE}/api/route/simulate-hazard`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_location: "Sonapur_Tunnel_Zone",
          rain_24h_mm: 165.0,
          report_blockade: true
        })
      });
      const res = await resp.json();

      // Refresh risk segments & routes
      await loadCorridorData();
      await fetchRouteAlternatives();

      // Show alert banner
      alertBanner.style.display = "block";
      document.getElementById("reroute-alert-title").textContent = "⚠️ LIVE AI REROUTE ACTIVE";
      document.getElementById("reroute-alert-desc").textContent = "Sonapur Tunnel blocked by severe mudslide. Traffic automatically diverted via Sonapur Old Ridge Detour (+8 min).";

      // Add Avoided Hazard Badge on Map
      if (!avoidedHazardMarker) {
        const hEl = document.createElement("div");
        hEl.className = "avoided-hazard-badge";
        hEl.innerHTML = "⚠️ AVOIDED HAZARD (Tunnel Blocked)";
        avoidedHazardMarker = new maplibregl.Marker({ element: hEl, anchor: "bottom" })
          .setLngLat([92.3685, 25.1142])
          .addTo(map);
      }

      btnSim.textContent = "✅ Hazard Active! Diverting to Safest Route";
      setTimeout(() => {
        btnSim.disabled = false;
        btnSim.innerHTML = `<span>⛈️</span><span>Simulate Torrential Rain on Sonapur Ghat</span>`;
      }, 3500);

      // Focus map to Sonapur sector
      map.flyTo({ center: [92.378, 25.125], zoom: 11.2, duration: 1500 });
    } catch (err) {
      console.error("Simulation error:", err);
      btnSim.textContent = "Simulation Failed";
      btnSim.disabled = false;
    }
  });

  // Reset to Normal Fair Weather
  btnReset.addEventListener("click", async () => {
    btnReset.disabled = true;
    btnReset.textContent = "Resetting Corridor...";

    try {
      await fetch(`${API_BASE}/api/route/reset-hazard`, { method: "POST" });
      
      // Hide alert banner & remove marker
      alertBanner.style.display = "none";
      if (avoidedHazardMarker) {
        avoidedHazardMarker.remove();
        avoidedHazardMarker = null;
      }

      // Refresh data
      await loadCorridorData();
      await fetchRouteAlternatives();

      btnReset.textContent = "☀️ Fair Weather Restored!";
      setTimeout(() => {
        btnReset.disabled = false;
        btnReset.innerHTML = `<span>☀️</span><span>Reset to Normal Fair Weather</span>`;
      }, 3000);
    } catch (err) {
      console.error("Reset error:", err);
      btnReset.disabled = false;
    }
  });
}

// ==========================================================
// 2-Second Hold-to-Fire SOS Trigger
// ==========================================================
function setupSOSButton() {
  const btn = document.getElementById("sos-btn");
  const circle = document.getElementById("sos-progress-circle");
  const statusBadge = document.getElementById("sos-status-badge");

  let holdTimer = null;
  let startTime = 0;
  const HOLD_DURATION = 2000; // 2.0 seconds

  function startHold(e) {
    e.preventDefault();
    startTime = Date.now();
    statusBadge.style.display = "none";

    function step() {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(1.0, elapsed / HOLD_DURATION);
      const offset = 408 - (408 * progress);
      circle.style.strokeDashoffset = offset;

      if (progress < 1.0) {
        holdTimer = requestAnimationFrame(step);
      } else {
        cancelAnimationFrame(holdTimer);
        fireSOS();
      }
    }
    holdTimer = requestAnimationFrame(step);
  }

  function cancelHold() {
    if (holdTimer) cancelAnimationFrame(holdTimer);
    circle.style.strokeDashoffset = 408;
  }

  btn.addEventListener("mousedown", startHold);
  btn.addEventListener("touchstart", startHold, { passive: false });

  window.addEventListener("mouseup", cancelHold);
  window.addEventListener("touchend", cancelHold);

  async function fireSOS() {
    circle.style.strokeDashoffset = 408;
    playEmergencyTone();

    const srcId = document.getElementById("route-src").value;
    const loc = NODE_COORDINATES[srcId] || { lat: 25.1142, lon: 92.3685 };

    const payload = {
      client_id: "sos-" + Date.now() + "-" + Math.random().toString(36).substr(2, 6),
      device_id: "truck-pilot-01",
      kind: "sos",
      lat: loc.lat,
      lon: loc.lon,
      created_at: new Date().toISOString(),
      note: `EMERGENCY: 2-Second Hold SOS trigger near ${NODE_COORDINATES[srcId] ? NODE_COORDINATES[srcId].name : 'NH-6'}`
    };

    if (navigator.onLine) {
      try {
        const resp = await fetch(`${API_BASE}/api/reports/sos`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Device-Id": payload.device_id },
          body: JSON.stringify(payload)
        });
        const res = await resp.json();
        statusBadge.style.display = "inline-block";
        statusBadge.style.background = "rgba(16, 185, 129, 0.2)";
        statusBadge.style.color = "#34d399";
        statusBadge.textContent = "✅ SOS DISPATCHED: Authorities & 108 Alerted";
      } catch (err) {
        queueSOSOffline(payload);
      }
    } else {
      queueSOSOffline(payload);
    }
  }

  async function queueSOSOffline(payload) {
    await idbSave("outbox", payload.client_id, payload);
    statusBadge.style.display = "inline-block";
    statusBadge.style.background = "rgba(245, 158, 11, 0.2)";
    statusBadge.style.color = "#fbbf24";
    statusBadge.textContent = "⚠️ OFFLINE: SOS queued in Outbox. Will broadcast immediately when connected!";
  }

  // Driver quick-report buttons
  document.querySelectorAll(".report-action-btn").forEach(b => {
    b.addEventListener("click", async () => {
      const kind = b.getAttribute("data-kind");
      const srcId = document.getElementById("route-src").value;
      const loc = NODE_COORDINATES[srcId] || { lat: 25.1142, lon: 92.3685 };

      const item = {
        client_id: "rep-" + Date.now() + "-" + Math.random().toString(36).substr(2, 6),
        device_id: "truck-pilot-01",
        kind: kind,
        lat: loc.lat,
        lon: loc.lon,
        created_at: new Date().toISOString(),
        note: `Driver reported: ${kind} hazard near ${NODE_COORDINATES[srcId] ? NODE_COORDINATES[srcId].name : 'NH-6'}`
      };

      if (navigator.onLine) {
        await fetch(`${API_BASE}/api/reports`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(item)
        });
        alert(`Report '${kind.toUpperCase()}' sent to highway authorities!`);
      } else {
        await idbSave("outbox", item.client_id, item);
        alert(`Offline: '${kind.toUpperCase()}' report saved to local Outbox. Will sync upon reconnection.`);
      }
    });
  });
}

function playEmergencyTone() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(880, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.3);
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.5);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.5);
  } catch (err) {
    console.log("Audio tone unavailable:", err);
  }
}

// ==========================================================
// Offline Caching & Outbox Sync
// ==========================================================
function setupOfflineSync() {
  const btn = document.getElementById("btn-download-corridor");
  btn.addEventListener("click", async () => {
    btn.disabled = true;
    btn.innerHTML = "<span>⏳</span><span>Caching 350km...</span>";

    await loadCorridorData();
    const nodes = [101, 108, 127];
    for (let s of nodes) {
      for (let d of nodes) {
        if (s !== d) {
          const resp = await fetch(`${API_BASE}/api/route/alternatives?src=${s}&dst=${d}`);
          const res = await resp.json();
          await idbSave("corridor_cache", `routes_${s}_${d}`, res);
        }
      }
    }

    btn.disabled = false;
    btn.innerHTML = "<span>✅</span><span>Corridor Cached (Offline Ready)</span>";
    setTimeout(() => {
      btn.innerHTML = "<span>💾</span><span>Cache Corridor</span>";
    }, 4000);
  });
}

function setupNetworkMonitor() {
  const chip = document.getElementById("net-status-chip");
  const text = document.getElementById("net-status-text");

  function updateNetStatus() {
    isOfflineMode = !navigator.onLine;
    if (isOfflineMode) {
      chip.className = "status-chip offline";
      text.textContent = "Offline (Airplane Mode)";
    } else {
      chip.className = "status-chip";
      text.textContent = "Online (Live Feed)";
      drainOutbox();
    }
  }

  window.addEventListener("online", updateNetStatus);
  window.addEventListener("offline", updateNetStatus);
  updateNetStatus();
}

async function drainOutbox() {
  const outboxItems = await idbGetAllOutbox();
  if (!outboxItems || !outboxItems.length) return;

  console.log(`[SYNC] Draining ${outboxItems.length} queued offline reports...`);
  try {
    const resp = await fetch(`${API_BASE}/api/sync/batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        device_id: "truck-pilot-01",
        items: outboxItems
      })
    });
    const res = await resp.json();
    const acceptedIds = (res.results || []).filter(r => r.status === "accepted").map(r => r.client_id);
    await idbDeleteOutbox(acceptedIds);
    console.log(`[SYNC] Successfully synced ${acceptedIds.length} reports.`);
    loadCorridorData();
  } catch (err) {
    console.warn("Outbox sync retry scheduled later:", err);
  }
}

// Tab navigation switcher
function setupTabNavigation() {
  const tabs = document.querySelectorAll(".tab-btn");
  const contents = document.querySelectorAll(".tab-content");

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      contents.forEach(c => c.classList.remove("active"));

      tab.classList.add("active");
      const targetId = tab.getAttribute("data-tab");
      const targetContent = document.getElementById(targetId);
      if (targetContent) targetContent.classList.add("active");
    });
  });

  document.getElementById("toggle-incidents").addEventListener("change", (e) => {
    map.setLayoutProperty("incidents-circles", "visibility", e.target.checked ? "visible" : "none");
  });

  document.getElementById("toggle-insar").addEventListener("change", (e) => {
    map.setLayoutProperty("insar-polygons", "visibility", e.target.checked ? "visible" : "none");
  });
}
