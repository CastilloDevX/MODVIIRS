import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'

const MapPage = lazy(() => import('./features/map/MapPage').then(module => ({ default: module.MapPage })))
const LandingPage = lazy(() => import('./features/landing/LandingPage').then(module => ({ default: module.LandingPage })))

export default function App() {
  return (
    <Suspense fallback={<p role="status" style={{ padding: 24 }}>Loading…</p>}>
      <Routes>
        <Route path="/" element={<MapPage />} />
        <Route path="/landing" element={<LandingPage />} />
        <Route path="/map" element={<MapPage />} />
        <Route path="*" element={<h1 className="title">404</h1>} />
      </Routes>
    </Suspense>
  )
}
