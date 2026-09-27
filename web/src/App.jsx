import { Routes, Route, NavLink } from 'react-router-dom';
import { MapPin, Mountain, Truck, AlertTriangle } from 'lucide-react';
import RouteScreen from './screens/RouteScreen';
import CorridorScreen from './screens/CorridorScreen';
import StopsScreen from './screens/StopsScreen';
import SOSScreen from './screens/SOSScreen';
import MapComponent from './components/MapComponent';

export default function App() {
  return (
    <div className="app-container" style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      {/* Left Sidebar (Desktop) / Bottom Nav (Mobile - CSS handles layout) */}
      <aside className="control-sidebar" style={{ width: '440px', display: 'flex', flexDirection: 'column', zIndex: 10 }}>
        
        {/* Header (Simplified) */}
        <header className="app-header" style={{ padding: '16px', borderBottom: '1px solid var(--border-color)' }}>
          <div className="brand-title">NER Logistics Intelligence</div>
        </header>

        {/* Tab Navigation */}
        <nav className="tabs-nav" style={{ display: 'flex', gap: '4px', padding: '8px' }}>
          <NavLink to="/" className={({ isActive }) => `tab-btn ${isActive ? 'active' : ''}`}>
            <MapPin size={16} /> Route
          </NavLink>
          <NavLink to="/corridor" className={({ isActive }) => `tab-btn ${isActive ? 'active' : ''}`}>
            <Mountain size={16} /> Corridor
          </NavLink>
          <NavLink to="/stops" className={({ isActive }) => `tab-btn ${isActive ? 'active' : ''}`}>
            <Truck size={16} /> Stops
          </NavLink>
          <NavLink to="/sos" className={({ isActive }) => `tab-btn ${isActive ? 'active' : ''}`}>
            <AlertTriangle size={16} /> SOS
          </NavLink>
        </nav>

        {/* Screen Content Viewport */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
          <Routes>
            <Route path="/" element={<RouteScreen />} />
            <Route path="/corridor" element={<CorridorScreen />} />
            <Route path="/stops" element={<StopsScreen />} />
            <Route path="/sos" element={<SOSScreen />} />
          </Routes>
        </div>
      </aside>

      {/* Map Viewport */}
      <main className="map-viewport" style={{ flex: 1, position: 'relative' }}>
        <MapComponent />
      </main>
    </div>
  );
}
