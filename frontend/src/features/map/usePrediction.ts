import { useEffect, useState } from 'react'
import { getCurrentForecast, getWeekForecast, mondayOf, type CurrentForecast, type ZoneCollection } from './predictions'

export type ForecastView = 'timeline' | 'current' | 'next' | 'off'

/** Loads the forecast to draw: the week under the timeline thumb, or the live current/next week. */
export function usePrediction(date: Date, view: ForecastView) {
  const [live, setLive] = useState<CurrentForecast | null>(null)
  const [loaded, setLoaded] = useState<{ monday: string; data: ZoneCollection | null } | null>(null)
  const monday = mondayOf(date)

  useEffect(() => {
    const ctrl = new AbortController()
    getCurrentForecast(ctrl.signal).then(setLive).catch(() => {})
    return () => ctrl.abort()
  }, [])

  useEffect(() => {
    if (view !== 'timeline') return
    const ctrl = new AbortController()
    getWeekForecast(monday, ctrl.signal)
      .then(data => setLoaded({ monday, data }))
      .catch(() => {
        if (!ctrl.signal.aborted) setLoaded({ monday, data: null })
      })
    return () => ctrl.abort()
  }, [monday, view])

  const shown = view === 'off' ? null
    : view === 'current' ? live?.semana_en_curso ?? null
    : view === 'next' ? live?.semana_proxima ?? null
    : loaded?.monday === monday ? loaded.data : null
  const loading = view === 'timeline' && loaded?.monday !== monday
  return { live, shown, monday, loading }
}
