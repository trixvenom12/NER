import React, { useState, useEffect } from 'react';
import { useMapContext } from '../utils/MapContext.jsx';
import { fetchPrecursorAlerts, simulateHazard, fetchRiskSegments } from '../utils/api.js';

export default function CorridorScreen() {
  const { layerToggles, toggleLayer, setRiskSegments, setRouteAlternatives, setRouteGeoJSON } = useMapContext();
  const [alerts, setAlerts] = useState([]);
  const [simulating, setSimulating] = useState(false);
  const [simResult, setSimResult] = useState(null);
  const [loadingAlerts, setLoadingAlerts] = useState(true);

  // Load precursor alerts on mount
  useEffect(() => {
    (async () => {
      try {
        const data = await fetchPrecursorAlerts();
        if (data?.alerts) setAlerts(data.alerts);
      } catch (err) {
        console.error('Failed to load precursor alerts:', err);
      } finally {
        setLoadingAlerts(false);
      }
    })();
  }, []);

  // Load risk segments for the map layer
  useEffect(() => {
    (async () => {
      try {
        const data = await fetchRiskSegments();
        if (data) setRiskSegments(data);
      } catch (err) {
        console.error('Failed to load risk segments:', err);
      }
    })();
  }, [setRiskSegments]);

  const handleSimulate = async () => {
    setSimulating(true);
    setSimResult(null);
    try {
      const result = await simulateHazard('Sonapur_Tunnel_Zone', 165, false);
      if (result) {
        setSimResult(result);
        // Update routes with diverted alternatives
        if (result.updated_routes) {
          setRouteAlternatives(result.updated_routes);
          const safest = result.updated_routes.routes?.safest;
          if (safest?.geometry) setRouteGeoJSON(safest.geometry);
        }
        // Refresh risk segments on map
        const updatedSegs = await fetchRiskSegments();
        if (updatedSegs) setRiskSegments(updatedSegs);
      }
    } catch (err) {
      console.error('Simulation failed:', err);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="tab-content active" style={{ display: 'block' }}>
      <div className="corridor-stats-box">
        <div style={{ fontSize: '14px', fontWeight: 800, marginBottom: '8px' }}>NH-6 Corridor Status</div>
        <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px' }}>
          Full 350 km Meghalaya Ghats & Barak Floodplain multi-factor risk assessment.
        </div>

        <div className="toggle-row">
          <span style={{ fontSize: '12.5px' }}>Show Historical Incidents (2021-2026)</span>
          <label className="switch">
            <input type="checkbox" checked={layerToggles.incidents} onChange={() => toggleLayer('incidents')} />
            <span className="slider"></span>
          </label>
        </div>

        <div className="toggle-row">
          <span style={{ fontSize: '12.5px' }}>Sentinel-1 InSAR Deformation Layer</span>
          <label className="switch">
            <input type="checkbox" checked={layerToggles.insar} onChange={() => toggleLayer('insar')} />
            <span className="slider"></span>
          </label>
        </div>

        <div className="toggle-row">
          <span style={{ fontSize: '12.5px' }}>Corridor Risk Heatmap</span>
          <label className="switch">
            <input type="checkbox" checked={layerToggles.heatmap} onChange={() => toggleLayer('heatmap')} />
            <span className="slider"></span>
          </label>
        </div>

        <button className="demo-trigger-btn" onClick={handleSimulate} disabled={simulating}>
          <span>⛈️</span>
          <span>{simulating ? 'Simulating...' : 'Simulate Torrential Rain on Sonapur Ghat'}</span>
        </button>
        <div style={{ fontSize: '10.5px', color: 'var(--text-dim)', textAlign: 'center', marginTop: '6px' }}>
          Triggers live diversion away from Sonapur Tunnel before the judges.
        </div>

        {simResult && (
          <div style={{ marginTop: '12px', padding: '10px', background: 'rgba(163, 58, 40, 0.15)', border: '1px solid rgba(248, 113, 113, 0.3)', borderRadius: '8px', fontSize: '12px' }}>
            <div style={{ fontWeight: 700, color: '#f87171', marginBottom: '4px' }}>⚡ Simulation Applied</div>
            <div style={{ color: 'var(--text-muted)' }}>
              {simResult.affected_segment_count} segments affected with {simResult.rain_24h_mm}mm rainfall.
              Routes recalculated — check Route tab for diversion.
            </div>
          </div>
        )}
      </div>

      {/* InSAR Precursor Alerts */}
      <div className="section-heading">
        <span>Satellite InSAR Precursor Monitor</span>
        <span style={{ fontSize: '11px', color: 'var(--accent-cyan)' }}>{alerts.length} sites</span>
      </div>

      {loadingAlerts && <div style={{ fontSize: '12px', color: 'var(--text-dim)', padding: '12px' }}>Loading alerts...</div>}

      <div className="advisories-list">
        {alerts.map((alert, i) => (
          <div key={i} className={`advisory-card ${alert.latest_alert?.level === 'high' ? 'hazard' : ''}`}>
            <div className="advisory-header">
              <span>{alert.location_name}</span>
              <span style={{ textTransform: 'uppercase', color: alert.latest_alert?.level === 'high' ? '#f87171' : '#facc15' }}>
                {alert.latest_alert?.level} alert
              </span>
            </div>
            <div style={{ fontSize: '12px', marginBottom: '4px' }}>
              Deformation: {alert.displacement_rate_mm_yr} mm/yr | z-score: {alert.latest_alert?.z_score}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
              {alert.latest_alert?.advisory}
            </div>
          </div>
        ))}
        {!loadingAlerts && alerts.length === 0 && (
          <div style={{ fontSize: '12px', color: 'var(--text-dim)', padding: '12px' }}>No active precursor alerts.</div>
        )}
      </div>
    </div>
  );
}
