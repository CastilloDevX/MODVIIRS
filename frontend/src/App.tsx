import { useEffect, useState } from 'react'
import { Route, Routes } from 'react-router-dom'
import { ApiError, getHealth } from './lib/api'
import { MapPage } from './features/map/MapPage'

type HealthState = 'checking' | 'available' | 'unavailable' | 'unexpected'

function HomePage() {
  const [health, setHealth] = useState<HealthState>('checking')

  useEffect(() => {
    const controller = new AbortController()

    getHealth(controller.signal).then(
      () => setHealth('available'),
      (error: unknown) => {
        if (error instanceof ApiError && error.kind === 'cancelled') return
        setHealth(error instanceof ApiError && error.kind === 'invalid-response' ? 'unexpected' : 'unavailable')
      },
    )

    return () => controller.abort()
  }, [])

  const messages: Record<HealthState, string> = {
    checking: 'Comprobando conexión con el backend…',
    available: 'Backend disponible',
    unavailable: 'Backend no disponible',
    unexpected: 'Respuesta inesperada del backend',
  }

  return (
    <main>
      <h1 className="title">Hola mundo</h1>
      <p role="status" aria-live="polite">{messages[health]}</p>
    </main>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/map" element={<MapPage />} />
      <Route path="*" element={<h1 className="title">404</h1>} />
    </Routes>
  )
}
