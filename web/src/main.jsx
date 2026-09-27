import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { MapProvider } from './utils/MapContext.jsx'
import App from './App.jsx'
import './index.css'
import 'maplibre-gl/dist/maplibre-gl.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <MapProvider>
        <App />
      </MapProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
