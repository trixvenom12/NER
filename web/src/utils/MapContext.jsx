/**
 * web/src/utils/MapContext.jsx — Shared state between sidebar screens and MapLibre
 * Screens push data (route geometry, layer toggles, etc.) → Map reads and renders.
 */

import React, { createContext, useContext, useState, useCallback } from 'react';

const MapContext = createContext(null);

export function MapProvider({ children }) {
  // Active route GeoJSON geometry (LineString from routing API)
  const [routeGeoJSON, setRouteGeoJSON] = useState(null);

  // Risk segments GeoJSON FeatureCollection
  const [riskSegments, setRiskSegments] = useState(null);

  // Facilities list
  const [facilities, setFacilities] = useState([]);

  // Currently selected route profile
  const [activeProfile, setActiveProfile] = useState('balanced');

  // Route alternatives data (all 3 profiles)
  const [routeAlternatives, setRouteAlternatives] = useState(null);

  // Layer visibility toggles
  const [layerToggles, setLayerToggles] = useState({
    riskSegments: true,
    incidents: true,
    insar: true,
    heatmap: false,
    facilities: true,
    route: true,
  });

  // Fly-to target for map animation
  const [flyTo, setFlyTo] = useState(null);

  const toggleLayer = useCallback((layerName) => {
    setLayerToggles(prev => ({ ...prev, [layerName]: !prev[layerName] }));
  }, []);

  const value = {
    routeGeoJSON, setRouteGeoJSON,
    riskSegments, setRiskSegments,
    facilities, setFacilities,
    activeProfile, setActiveProfile,
    routeAlternatives, setRouteAlternatives,
    layerToggles, toggleLayer, setLayerToggles,
    flyTo, setFlyTo,
  };

  return <MapContext.Provider value={value}>{children}</MapContext.Provider>;
}

export function useMapContext() {
  const ctx = useContext(MapContext);
  if (!ctx) throw new Error('useMapContext must be used within MapProvider');
  return ctx;
}
