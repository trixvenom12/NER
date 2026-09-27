import React, { useState, useRef, useEffect } from 'react';
import { idbPut } from '../utils/db';
import { submitReport, submitSOS, fetchNearbyReports } from '../utils/api.js';

export default function SOSScreen() {
  const [sosStatus, setSosStatus] = useState('');
  const [reportStatus, setReportStatus] = useState('');
  const [nearbyReports, setNearbyReports] = useState([]);
  const [sosResult, setSosResult] = useState(null);
  const [holdProgress, setHoldProgress] = useState(0);
  const sosInterval = useRef(null);
  const sosTimeout = useRef(null);

  // Load nearby reports on mount
  useEffect(() => {
    (async () => {
      try {
        const data = await fetchNearbyReports();
        if (data) setNearbyReports(data);
      } catch (err) {
        console.error('Failed to load nearby reports:', err);
      }
    })();
  }, []);

  const handleReport = async (kind) => {
    setReportStatus('');
    const report = {
      client_id: crypto.randomUUID(),
      kind,
      lat: 25.71,
      lon: 91.88,
      created_at: new Date().toISOString(),
      note: `Driver report: ${kind}`,
    };

    // Try online first
    try {
      const result = await submitReport({ ...report, device_id: 'dev-trucker-01' });
      if (result) {
        setReportStatus(`✅ ${result.message}`);
        // Refresh nearby reports
        const updated = await fetchNearbyReports();
        if (updated) setNearbyReports(updated);
        return;
      }
    } catch {
      // Offline fallback
    }

    // Queue to IndexedDB outbox for offline sync
    await idbPut('outbox', { ...report, status: 'queued' }, report.client_id);
    setReportStatus(`📡 Offline: Report queued in Outbox — will sync when reconnected.`);
  };

  const startSOS = () => {
    setHoldProgress(0);
    setSosStatus('');
    setSosResult(null);

    // Animate progress over 2 seconds
    const startTime = Date.now();
    sosInterval.current = setInterval(() => {
      const elapsed = Date.now() - startTime;
      setHoldProgress(Math.min(100, (elapsed / 2000) * 100));
    }, 50);

    sosTimeout.current = setTimeout(async () => {
      clearInterval(sosInterval.current);
      setHoldProgress(100);

      // Try to play audio tone
      try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        osc.type = 'sine';
        osc.frequency.value = 880;
        osc.connect(ctx.destination);
        osc.start();
        setTimeout(() => osc.stop(), 500);
      } catch {
        // Audio not available
      }

      // Submit SOS
      try {
        const result = await submitSOS({
          device_id: 'dev-trucker-01',
          lat: 25.1142,
          lon: 92.3685,
          note: 'EMERGENCY: Driver activated 2-second hold SOS distress signal',
        });
        if (result) {
          setSosStatus('🚨 SOS DISPATCHED: Authorities & 108 Alerted');
          setSosResult(result);
          return;
        }
      } catch {
        // Offline
      }

      // Offline fallback
      await idbPut('outbox', {
        client_id: crypto.randomUUID(),
        kind: 'sos',
        lat: 25.1142,
        lon: 92.3685,
        created_at: new Date().toISOString(),
        note: 'EMERGENCY SOS',
        status: 'queued',
      }, crypto.randomUUID());
      setSosStatus('📡 OFFLINE: SOS queued in Outbox — will dispatch when reconnected.');
    }, 2000);
  };

  const endSOS = () => {
    if (sosTimeout.current) clearTimeout(sosTimeout.current);
    if (sosInterval.current) clearInterval(sosInterval.current);
    if (holdProgress < 100) {
      setHoldProgress(0);
    }
  };

  const reportKinds = [
    { kind: 'blocked', icon: '🚧', title: 'Road Blocked' },
    { kind: 'slide', icon: '🪨', title: 'Landslide / Mud' },
    { kind: 'water', icon: '🌊', title: 'Waterlogged' },
    { kind: 'breakdown', icon: '⚠️', title: 'Breakdown / Jam' },
  ];

  return (
    <div className="tab-content active" style={{ display: 'block' }}>
      <div className="section-heading">
        <span>Driver Ground Truth Report</span>
      </div>

      <div className="report-grid">
        {reportKinds.map(r => (
          <div key={r.kind} className="report-action-btn" onClick={() => handleReport(r.kind)}>
            <div className="report-btn-icon">{r.icon}</div>
            <div className="report-btn-title">{r.title}</div>
          </div>
        ))}
      </div>

      {reportStatus && (
        <div style={{ fontSize: '12px', padding: '8px 12px', marginBottom: '16px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '8px', color: '#34d399' }}>
          {reportStatus}
        </div>
      )}

      {/* SOS Button */}
      <div className="sos-container">
        <div className="sos-hold-wrapper" style={{ position: 'relative', width: '140px', height: '140px', margin: '0 auto 16px' }}>
          <svg className="sos-ring-svg" viewBox="0 0 140 140" style={{ position: 'absolute', top: 0, left: 0, width: '140px', height: '140px', transform: 'rotate(-90deg)' }}>
            <circle cx="70" cy="70" r="65" fill="none" stroke="#1e293b" strokeWidth="6" />
            <circle
              cx="70" cy="70" r="65" fill="none" stroke="#ef4444" strokeWidth="6"
              strokeDasharray="408"
              strokeDashoffset={408 - (holdProgress / 100) * 408}
              style={{ transition: 'stroke-dashoffset 0.05s linear' }}
            />
          </svg>
          <div
            className="sos-button"
            style={{ position: 'absolute', top: '10px', left: '10px', width: '120px', height: '120px' }}
            onMouseDown={startSOS}
            onMouseUp={endSOS}
            onMouseLeave={endSOS}
            onTouchStart={startSOS}
            onTouchEnd={endSOS}
          >
            SOS
          </div>
        </div>
        <div style={{ fontWeight: 800, fontSize: '15px', marginBottom: '4px', color: '#f87171' }}>
          EMERGENCY DISTRESS BEACON
        </div>
        <div className="sos-hint">
          Press and hold for 2 full seconds to trigger distress beacon to highway emergency services.
        </div>

        {sosStatus && (
          <div style={{ display: 'block', marginTop: '16px', fontWeight: 700, fontSize: '13px', color: sosStatus.includes('DISPATCHED') ? '#f87171' : '#fbbf24' }}>
            {sosStatus}
          </div>
        )}

        {/* Nearest emergency facilities from SOS response */}
        {sosResult?.nearest_emergency_facilities && (
          <div style={{ marginTop: '16px', textAlign: 'left', width: '100%' }}>
            <div style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-dim)', marginBottom: '8px' }}>
              Nearest Emergency Facilities
            </div>
            {sosResult.nearest_emergency_facilities.map((f, i) => (
              <div key={i} style={{ fontSize: '12px', padding: '6px 0', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#fff' }}>{f.name}</span>
                <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{f.distance_km} km</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Nearby Reports */}
      {nearbyReports.length > 0 && (
        <>
          <div className="section-heading" style={{ marginTop: '24px' }}>
            <span>Recent Nearby Reports</span>
            <span style={{ fontSize: '11px', color: 'var(--accent-cyan)' }}>{nearbyReports.length}</span>
          </div>
          <div className="advisories-list">
            {nearbyReports.slice(0, 5).map((r, i) => (
              <div key={i} className={`advisory-card ${r.kind === 'sos' ? 'hazard' : ''}`}>
                <div className="advisory-header">
                  <span style={{ textTransform: 'uppercase' }}>{r.kind}</span>
                  <span>{r.distance_km} km away</span>
                </div>
                <div>{r.note || `${r.kind} report from ${r.device_id}`}</div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
