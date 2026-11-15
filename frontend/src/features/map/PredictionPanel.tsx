import { Button } from '@/components/ui/button'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { LEVELS, pct, type CurrentForecast, type ZoneCollection } from './predictions'
import type { ForecastView } from './usePrediction'

type Props = {
  view: ForecastView
  onViewChange: (v: ForecastView) => void
  live: CurrentForecast | null
  shown: ZoneCollection | null
  monday: string
  loading: boolean
  onFocus: () => void
}

export function PredictionPanel({ view, onViewChange, live, shown, monday, loading, onFocus }: Props) {
  const r = shown?.resumen
  const label = view === 'timeline' ? `Week of ${monday}` : shown ? `Week of ${shown.semana}` : ''
  return (
    <section className="field pred-panel" aria-label="Hotspot anomaly forecast">
      <h2 className="label">Anomaly forecast · Yucatán</h2>
      <ToggleGroup variant="outline" className="w-full pred-toggle" value={[view]} aria-label="Forecast view"
        onValueChange={v => { if (v[0]) onViewChange(v[0] as ForecastView) }}>
        <ToggleGroupItem value="timeline" className="flex-1">Timeline</ToggleGroupItem>
        <ToggleGroupItem value="current" className="flex-1" disabled={!live}>This wk</ToggleGroupItem>
        <ToggleGroupItem value="next" className="flex-1" disabled={!live}>Next wk</ToggleGroupItem>
        <ToggleGroupItem value="off" className="flex-1">Off</ToggleGroupItem>
      </ToggleGroup>
      {view !== 'off' && (
        <div className="pred-info">
          <div>{label}{shown?.horizonte_semanas ? ` · ${shown.horizonte_semanas}-week lead` : ''}</div>
          {loading && view === 'timeline' ? <div>Loading…</div>
            : r ? <div>Max probability <b>{pct(r.prob_max)}</b> · {r.zonas_alto} high-risk zone{r.zonas_alto === 1 ? '' : 's'}</div>
            : <div>No forecast for this week (model covers 2015–2025 and live 2026).</div>}
          {live && <div className="pred-muted">Live data until {live.datos_hasta} (FIRMS VIIRS NOAA-20 + NASA POWER)</div>}
        </div>
      )}
      <div className="pred-legend">
        {LEVELS.map(l => <span key={l.label}><i style={{ background: l.color }} />{l.label}</span>)}
        <span><i className="pred-anom" />observed anomaly</span>
      </div>
      <Button variant="outline" size="sm" onClick={onFocus}>Zoom to Yucatán</Button>
      <p className="pred-muted">Probability that a 55 km zone has unusually high fire activity (above its own historical p90). A hotspot is not a wildfire.</p>
    </section>
  )
}
