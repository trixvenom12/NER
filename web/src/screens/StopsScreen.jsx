import React, { useState, useEffect } from 'react';
import { useMapContext } from '../utils/MapContext.jsx';
import { fetchFacilities } from '../utils/api.js';

export default function StopsScreen() {
  const { setFacilities: setCtxFacilities, setFlyTo } = useMapContext();
  const [facilities, setFacilities] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const data = await fetchFacilities();
        if (data) {
          setFacilities(data);
          setCtxFacilities(data);
        }
      } catch (err) {
        console.error('Failed to load facilities:', err);
      } finally {
        setLoading(false);
      }
    })();
  }, [setCtxFacilities]);

  const handleFacilityClick = (fac) => {
    setFlyTo({ lat: fac.lat, lon: fac.lon, zoom: 13 });
  };

  const kindIcons = {
    truck_bay: '🅿️',
    fuel: '⛽',
    medical: '🏥',
    food: '🍛',
    weighbridge: '⚖️',
    emergency_shelter: '🏠',
  };

  return (
    <div className="tab-content active" style={{ display: 'block' }}>
      <div className="section-heading">
        <span>NH-6 Highway Facilities & Bays</span>
        <span style={{ fontSize: '10.5px', color: 'var(--text-dim)' }}>
          {loading ? 'Loading...' : `${facilities.length} facilities`}
        </span>
      </div>

      <div id="facilities-list-container">
        {facilities.map((fac) => {
          const avail = fac.availability;
          const occPercent = avail ? avail.occupancy_pct : 0;
          const icon = kindIcons[fac.kind] || '📍';

          return (
            <div key={fac.id} className="facility-card" onClick={() => handleFacilityClick(fac)}>
              <div className="facility-header">
                <span className="facility-name">{icon} {fac.name}</span>
                <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--accent-cyan)', textTransform: 'uppercase' }}>
                  {fac.kind.replace('_', ' ')}
                </span>
              </div>

              {avail && (
                <>
                  <div className="bay-occupancy-bar">
                    <div
                      className="bay-occupancy-fill"
                      style={{
                        width: `${occPercent}%`,
                        background: occPercent > 85 ? '#ef4444' : occPercent > 60 ? '#f59e0b' : 'var(--accent-emerald)',
                      }}
                    />
                  </div>
                  <div className="occupancy-meta">
                    <span>{avail.occupied_bays} / {avail.total_capacity} bays • {avail.status}</span>
                    <span>{occPercent}% full</span>
                  </div>
                  <div style={{ fontSize: '10px', color: 'var(--text-dim)', marginTop: '4px' }}>
                    {avail.diurnal_phase} • Confidence: {avail.prediction_confidence}
                  </div>
                </>
              )}

              {!avail && (
                <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '6px' }}>
                  Capacity: {fac.capacity || 'N/A'}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
