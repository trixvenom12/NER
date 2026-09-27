import React, { useState, useEffect, useCallback } from 'react';
import { useMapContext } from '../utils/MapContext.jsx';
import { fetchRouteAlternatives } from '../utils/api.js';

const LOCATIONS = [
  { id: 101, label: 'Guwahati (Khanapara / Beltola Hub)' },
  { id: 106, label: 'Umiam (Barapani Lake)' },
  { id: 108, label: 'Shillong (Central GS Road)' },
  { id: 113, label: 'Jowai (Bypass Junction)' },
  { id: 116, label: 'Khliehriat (East Jaintia Hills)' },
  { id: 127, label: 'Silchar (ISBT / Ramnagar Terminal)' },
];

function getBandClass(score) {
  if (score >= 62) return 'hazard';
  if (score >= 34) return 'caution';
  return 'safe';
}

export default function RouteScreen() {
  const { setRouteGeoJSON, activeProfile, setActiveProfile, routeAlternatives, setRouteAlternatives } = useMapContext();
  const [src, setSrc] = useState(101);
  const [dst, setDst] = useState(127);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadRoutes = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRouteAlternatives(src, dst);
      if (data) {
        setRouteAlternatives(data);
        // Set active route geometry on map
        const active = data.routes?.[activeProfile];
        if (active?.geometry) {
          setRouteGeoJSON(active.geometry);
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [src, dst, activeProfile, setRouteAlternatives, setRouteGeoJSON]);

  // Load on mount and when origin/destination changes
  useEffect(() => { loadRoutes(); }, [src, dst]);

  // When profile changes, update the map geometry
  useEffect(() => {
    if (routeAlternatives?.routes?.[activeProfile]?.geometry) {
      setRouteGeoJSON(routeAlternatives.routes[activeProfile].geometry);
    }
  }, [activeProfile, routeAlternatives, setRouteGeoJSON]);

  const routes = routeAlternatives?.routes || {};
  const activeRoute = routes[activeProfile];

  return (
    <div className="tab-content active" style={{ display: 'block' }}>
      {/* Origin / Destination Selector */}
      <div className="route-selector-card">
        <div className="field-group">
          <label>Origin</label>
          <select className="select-input" value={src} onChange={e => setSrc(Number(e.target.value))}>
            {LOCATIONS.map(loc => <option key={loc.id} value={loc.id}>{loc.label}</option>)}
          </select>
        </div>
        <div className="field-group">
          <label>Destination</label>
          <select className="select-input" value={dst} onChange={e => setDst(Number(e.target.value))}>
            {LOCATIONS.map(loc => <option key={loc.id} value={loc.id}>{loc.label}</option>)}
          </select>
        </div>
      </div>

      {loading && <div style={{ textAlign: 'center', padding: '20px', color: 'var(--accent-cyan)' }}>Computing routes...</div>}
      {error && <div style={{ textAlign: 'center', padding: '12px', color: '#f87171', fontSize: '12px' }}>⚠ {error}</div>}

      {/* 3 Profile Cards */}
      {!loading && routes.fastest && (
        <div className="profile-cards-grid">
          {['fastest', 'balanced', 'safest'].map(profile => {
            const r = routes[profile];
            if (!r || !r.path_found) return null;
            const delta = r.delta_vs_fastest;
            return (
              <div
                key={profile}
                className={`profile-card ${activeProfile === profile ? 'active' : ''}`}
                onClick={() => setActiveProfile(profile)}
              >
                <div className="profile-name">{profile}</div>
                <div className="profile-time">{Math.round(r.duration_min)}m</div>
                <div className={`profile-delta ${profile === 'fastest' ? 'best' : delta?.duration_min > 10 ? 'extra' : ''}`}>
                  {profile === 'fastest' ? 'Base Time' : `+${Math.round(delta?.duration_min || 0)} min`}
                </div>
                <span className={`risk-pill ${getBandClass(r.mean_risk)}`}>
                  Risk {Math.round(r.mean_risk)}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* Active Route Stats */}
      {activeRoute && activeRoute.path_found && (
        <>
          <div className="route-metrics-bar">
            <div className="metric-item">
              <div className="metric-val">{activeRoute.distance_km} km</div>
              <div className="metric-lbl">Distance</div>
            </div>
            <div className="metric-item">
              <div className="metric-val">{Math.round(activeRoute.duration_min)} min</div>
              <div className="metric-lbl">Duration</div>
            </div>
            <div className="metric-item">
              <div className="metric-val">{activeRoute.mean_risk}</div>
              <div className="metric-lbl">Mean Hazard</div>
            </div>
            <div className="metric-item">
              <div className="metric-val">{activeRoute.max_risk}</div>
              <div className="metric-lbl">Max Hazard</div>
            </div>
          </div>

          {/* Driver Advisories */}
          {activeRoute.advisories && activeRoute.advisories.length > 0 && (
            <>
              <div className="section-heading">
                <span>Driver Advisories & Hazards</span>
                <span style={{ fontSize: '11px', color: 'var(--accent-cyan)' }}>{activeRoute.advisories.length} alerts</span>
              </div>
              <div className="advisories-list">
                {activeRoute.advisories.map((adv, i) => (
                  <div key={i} className={`advisory-card ${adv.level}`}>
                    <div className="advisory-header">
                      <span>KM {adv.at_km}</span>
                      <span style={{ textTransform: 'uppercase' }}>{adv.level}</span>
                    </div>
                    <div>{adv.text}</div>
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
