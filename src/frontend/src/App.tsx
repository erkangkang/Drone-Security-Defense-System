import { Routes, Route, Navigate } from 'react-router-dom'
import { MainLayout } from './components/layout/MainLayout'
import { Dashboard } from './pages/Dashboard'
import { Screen } from './pages/Screen'
import { MapPage } from './pages/Map'
import { Alerts } from './pages/Alerts'
import { Threats } from './pages/Threats'
import { Detectors } from './pages/Detectors'
import { Statistics } from './pages/Statistics'
import { Settings } from './pages/Settings'

function App() {
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/screen" element={<Screen />} />
        <Route path="/map" element={<MapPage />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/threats" element={<Threats />} />
        <Route path="/detectors" element={<Detectors />} />
        <Route path="/statistics" element={<Statistics />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </MainLayout>
  )
}

export default App
