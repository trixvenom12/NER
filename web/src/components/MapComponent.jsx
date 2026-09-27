import React, { useEffect, useRef } from 'react';
import * as maplibregl from 'maplibre-gl';
import { useMapContext } from '../utils/MapContext.jsx';
import { fetchRiskSegments, fetchFacilities, fetchRiskHeatmap, fetchDeformationLayer } from '../utils/api.js';

// Risk band color mapping (from Build Manual)
const BAND_COLORS = {
  safe: '#3F7A55',
  caution: '#B8862A',
  hazard: '#A33A28',
};

export default function MapComponent() {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const {
    routeGeoJSON,
    riskSegments, setRiskSegments,
    facilities, setFacilities,
    layerToggles,
    flyTo,
  } = useMapContext();

  // ─── Initialize Map ──────────────────────────────────────────────
  useEffect(() => {
    if (map.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: [91.88, 25.57],
      zoom: 8,
      pitch: 40,
      bearing: -17.6,
      antialias: true,
    });

    map.current.addControl(new maplibregl.NavigationControl(), 'top-right');
    map.current.addControl(new maplibregl.ScaleControl(), 'bottom-right');

    map.current.on('load', async () => {
      // Add empty sources that we'll populate reactively
      map.current.addSource('risk-segments', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      });

      map.current.addSource('active-route', {
        type: 'geojson',
        data: { type: 'Feature', geometry: { type: 'LineString', coordinates: [] }, properties: {} },
      });

      map.current.addSource('facilities-points', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      });

      map.current.addSource('heatmap-points', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      });

      map.current.addSource('insar-deformation', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      });

      // ─── Risk Segments Layer (color-coded road lines) ────────────
      map.current.addLayer({
        id: 'risk-segments-line',
        type: 'line',
        source: 'risk-segments',
        paint: {
          'line-color': [
            'match', ['get', 'band'],
            'hazard', BAND_COLORS.hazard,
            'caution', BAND_COLORS.caution,
            'safe', BAND_COLORS.safe,
            '#666',
          ],
          'line-width': 4,
          'line-opacity': 0.85,
        },
      });

      // ─── Active Route Layer (highlighted on top) ─────────────────
      map.current.addLayer({
        id: 'active-route-outline',
        type: 'line',
        source: 'active-route',
        paint: {
          'line-color': '#000',
          'line-width': 8,
          'line-opacity': 0.4,
        },
      });

      map.current.addLayer({
        id: 'active-route-line',
        type: 'line',
        source: 'active-route',
        paint: {
          'line-color': '#38bdf8',
          'line-width': 4,
          'line-opacity': 0.95,
        },
      });

      // ─── Facilities Layer ────────────────────────────────────────
      map.current.addLayer({
        id: 'facilities-circles',
        type: 'circle',
        source: 'facilities-points',
        paint: {
          'circle-radius': 6,
          'circle-color': '#10b981',
          'circle-stroke-width': 2,
          'circle-stroke-color': '#fff',
          'circle-opacity': 0.9,
        },
      });

      // ─── Heatmap Layer ───────────────────────────────────────────
      map.current.addLayer({
        id: 'risk-heatmap',
        type: 'heatmap',
        source: 'heatmap-points',
        paint: {
          'heatmap-weight': ['get', 'weight'],
          'heatmap-intensity': 1.2,
          'heatmap-radius': 30,
          'heatmap-color': [
            'interpolate', ['linear'], ['heatmap-density'],
            0, 'rgba(0,0,0,0)',
            0.2, '#10b981',
            0.5, '#f59e0b',
            0.8, '#ef4444',
            1, '#7f1d1d',
          ],
          'heatmap-opacity': 0.7,
        },
        layout: { visibility: 'none' },
      });

      // ─── InSAR Deformation Layer ─────────────────────────────────
      map.current.addLayer({
        id: 'insar-fill',
        type: 'fill',
        source: 'insar-deformation',
        paint: {
          'fill-color': '#8b5cf6',
          'fill-opacity': 0.25,
        },
        layout: { visibility: 'none' },
      });

      map.current.addLayer({
        id: 'insar-outline',
        type: 'line',
        source: 'insar-deformation',
        paint: {
          'line-color': '#a78bfa',
          'line-width': 2,
          'line-dasharray': [2, 2],
        },
        layout: { visibility: 'none' },
      });

      // ─── Click handler: Factor Explanation Popup ──────────────────
      map.current.on('click', 'risk-segments-line', (e) => {
        const feature = e.features[0];
        if (!feature) return;
        const p = feature.properties;
        const factors = typeof p.factors === 'string' ? JSON.parse(p.factors) : p.factors;

        const bandColor = BAND_COLORS[p.band] || '#666';
        const factorBars = ['rain', 'slope', 'susceptibility', 'history', 'reports']
          .map(key => {
            const val = factors[key] || 0;
            const pct = Math.round(val * 100);
            return `<div style="margin:3px 0"><div style="display:flex;justify-content:space-between;font-size:10px;color:#94a3b8"><span>${key}</span><span>${pct}%</span></div><div style="height:5px;background:#1e293b;border-radius:3px;overflow:hidden"><div style="height:100%;width:${pct}%;background:${bandColor};border-radius:3px"></div></div></div>`;
          })
          .join('');

        new maplibregl.Popup({ maxWidth: '300px' })
          .setLngLat(e.lngLat)
          .setHTML(`
            <div style="font-family:Outfit,sans-serif;padding:4px">
              <div style="font-weight:800;font-size:13px;margin-bottom:4px">${p.road_ref || 'NH-6'} — Segment ${p.id}</div>
              <div style="display:inline-block;padding:2px 8px;border-radius:999px;font-size:10px;font-weight:700;color:#fff;background:${bandColor};margin-bottom:8px">${p.band?.toUpperCase()} (${p.score})</div>
              <div style="font-size:11px;color:#94a3b8;margin-bottom:6px">${p.length_m}m • ${p.free_speed_kph} km/h • Slope ${p.mean_slope_deg}°</div>
              ${factorBars}
            </div>
          `)
          .addTo(map.current);
      });

      map.current.on('mouseenter', 'risk-segments-line', () => {
        map.current.getCanvas().style.cursor = 'pointer';
      });
      map.current.on('mouseleave', 'risk-segments-line', () => {
        map.current.getCanvas().style.cursor = '';
      });

      // ─── Facility popup ──────────────────────────────────────────
      map.current.on('click', 'facilities-circles', (e) => {
        const p = e.features[0]?.properties;
        if (!p) return;
        new maplibregl.Popup()
          .setLngLat(e.lngLat)
          .setHTML(`
            <div style="font-family:Outfit,sans-serif;padding:4px">
              <div style="font-weight:700;font-size:13px">${p.name}</div>
              <div style="font-size:11px;color:#94a3b8">${p.kind?.replace('_', ' ')} • Capacity: ${p.capacity}</div>
            </div>
          `)
          .addTo(map.current);
      });

      // ─── Initial data load ────────────────────────────────────────
      try {
        const [segs, facs, heatData, insarData] = await Promise.all([
          fetchRiskSegments(),
          fetchFacilities(),
          fetchRiskHeatmap(),
          fetchDeformationLayer(),
        ]);

        if (segs) {
          setRiskSegments(segs);
          map.current.getSource('risk-segments')?.setData(segs);
        }

        if (facs) {
          setFacilities(facs);
          const facGeoJSON = {
            type: 'FeatureCollection',
            features: facs.map(f => ({
              type: 'Feature',
              geometry: { type: 'Point', coordinates: [f.lon, f.lat] },
              properties: { name: f.name, kind: f.kind, capacity: f.capacity },
            })),
          };
          map.current.getSource('facilities-points')?.setData(facGeoJSON);
        }

        if (heatData) {
          map.current.getSource('heatmap-points')?.setData(heatData);
        }

        if (insarData) {
          map.current.getSource('insar-deformation')?.setData(insarData);
        }
      } catch (err) {
        console.error('Failed to load initial map data:', err);
      }
    });
  }, [setRiskSegments, setFacilities]);

  // ─── Update risk segments on map when context changes ────────────
  useEffect(() => {
    if (!map.current || !riskSegments) return;
    const src = map.current.getSource('risk-segments');
    if (src) src.setData(riskSegments);
  }, [riskSegments]);

  // ─── Update active route geometry ────────────────────────────────
  useEffect(() => {
    if (!map.current) return;
    const src = map.current.getSource('active-route');
    if (!src) return;

    if (routeGeoJSON && routeGeoJSON.coordinates && routeGeoJSON.coordinates.length > 1) {
      src.setData({
        type: 'Feature',
        geometry: routeGeoJSON,
        properties: {},
      });
    } else {
      src.setData({ type: 'Feature', geometry: { type: 'LineString', coordinates: [] }, properties: {} });
    }
  }, [routeGeoJSON]);

  // ─── Layer visibility toggles ────────────────────────────────────
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;

    const setVis = (layerId, visible) => {
      if (map.current.getLayer(layerId)) {
        map.current.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none');
      }
    };

    setVis('risk-segments-line', layerToggles.riskSegments);
    setVis('active-route-line', layerToggles.route);
    setVis('active-route-outline', layerToggles.route);
    setVis('facilities-circles', layerToggles.facilities);
    setVis('risk-heatmap', layerToggles.heatmap);
    setVis('insar-fill', layerToggles.insar);
    setVis('insar-outline', layerToggles.insar);
  }, [layerToggles]);

  // ─── Fly-to animation ───────────────────────────────────────────
  useEffect(() => {
    if (!map.current || !flyTo) return;
    map.current.flyTo({
      center: [flyTo.lon, flyTo.lat],
      zoom: flyTo.zoom || 13,
      duration: 1500,
    });
  }, [flyTo]);

  return (
    <div className="map-wrap" style={{ position: 'absolute', inset: 0 }}>
      <div ref={mapContainer} style={{ position: 'absolute', inset: 0 }} />
    </div>
  );
}
