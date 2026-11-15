import { Route, Routes } from 'react-router-dom'
import { MapPage } from './features/map/MapPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<MapPage />} />
      <Route path="*" element={<h1 className="title">404</h1>} />
    </Routes>
  )
}
