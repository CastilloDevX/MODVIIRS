import { useState } from 'react'
import { Link } from 'react-router-dom'
import logo from '../../assets/logo.png'
import { Input } from '@/components/ui/input'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { DateField } from './DateField'
import { BASEMAPS } from './layers'
import { Button } from '@/components/ui/button'
import { COUNTRY_SELECTION, type Country } from './countries'
import type { Bbox } from './region'
import { MapView, type ViewMode } from './MapView'
import { PredictionPanel } from './PredictionPanel'
import { usePrediction, type ForecastView } from './usePrediction'
import { RangeCalendar } from './RangeCalendar'
import { Timeline } from './Timeline'
import { addDays, diffDays, snapOffset } from './dates'
import './map.css'

const fmt = (v: number, pos: string, neg: string) => `${Math.abs(v).toFixed(2)}° ${v >= 0 ? pos : neg}`

export function MapPage() {
  const [range, setRange] = useState({ start: new Date(2026, 9, 10), end: new Date(2026, 9, 17) })
  const [offset, setOffset] = useState(0)
  const [stepDays, setStepDays] = useState(1)
  const [basemap, setBasemap] = useState(BASEMAPS[0].id)
  const [country, setCountry] = useState<Country | null>(null)
  const [picking, setPicking] = useState(false)
  const [region, setRegion] = useState<Bbox | null>(null)
  const [mode, setMode] = useState<ViewMode>('3d')
  const days = diffDays(range.start, range.end)
  const [forecastView, setForecastView] = useState<ForecastView>('timeline')
  const [focus, setFocus] = useState(0)
  const forecast = usePrediction(addDays(range.start, offset), forecastView)

  const changeRange = (start: Date, end: Date) => { setRange({ start, end }); setOffset(0); setStepDays(s => Math.min(s, Math.max(diffDays(start, end), 1))) }
  const changeStep = (n: number) => { setStepDays(n); setOffset(o => snapOffset(o, n, days)) }

  const togglePicking = () => {
    if (picking) { setPicking(false); return }
    setRegion(null)
    setPicking(true)
    document.querySelector('.stage')?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="map-page">
      <aside className="sidebar">
        <Link to="/" aria-label="MODVIIRS: ir a la landing"><img className="logo" src={logo} alt="MODVIIRS" /></Link>
        <h2 className="label">Calendar</h2>
        <RangeCalendar start={range.start} end={range.end} onChange={changeRange} />
        <div className="dates">
          <DateField label="Start date" value={range.start} max={range.end} onChange={d => changeRange(d, range.end)} />
          <DateField label="Final date" value={range.end} min={range.start} onChange={d => changeRange(range.start, d)} />
        </div>
        <div className="field">
          <label className="label" htmlFor="step-days">Steps (days)</label>
          <Input id="step-days" type="number" inputMode="numeric" min={1} max={Math.max(days, 1)} value={stepDays}
            onChange={e => { const n = Math.floor(Number(e.target.value)); if (n >= 1) changeStep(Math.min(n, Math.max(days, 1))) }} />
        </div>
        {COUNTRY_SELECTION && <div className="field">
          <h2 className="label">Country</h2>
          <div className="country-field">
            <span>{country ? country.name : 'Click a country on the map'}</span>
            {country && <button type="button" aria-label="Quitar selección de país" onClick={() => setCountry(null)}>×</button>}
          </div>
        </div>}
        <div className="field">
          <h2 className="label">Region</h2>
          <Button type="button" variant="outline" className="region-button" aria-pressed={picking} onClick={togglePicking}>{picking ? 'Cancel' : 'Select'}</Button>
          {picking && <p className="hint">Click (or tap) the first corner, then the opposite one. Drag to move the map. Esc cancels.</p>}
          {region && !picking && (
            <div className="country-field">
              <span>{fmt(region.north, 'N', 'S')} · {fmt(region.south, 'N', 'S')}<br />{fmt(region.west, 'E', 'W')} · {fmt(region.east, 'E', 'W')}</span>
              <button type="button" aria-label="Quitar región" onClick={() => setRegion(null)}>×</button>
            </div>
          )}
        </div>
        <div className="field">
          <h2 className="label">Imagery</h2>
          <ToggleGroup variant="outline" className="w-full" value={[basemap]} aria-label="Imagenología"
            onValueChange={v => { if (v[0]) setBasemap(v[0]) }}>
            {BASEMAPS.map(b => <ToggleGroupItem key={b.id} value={b.id} className="flex-1">{b.label}</ToggleGroupItem>)}
          </ToggleGroup>
        </div>
        <PredictionPanel view={forecastView} onViewChange={setForecastView} live={forecast.live} shown={forecast.shown}
          monday={forecast.monday} loading={forecast.loading} onFocus={() => setFocus(f => f + 1)} />
      </aside>
      <main className="stage">
        <MapView basemap={basemap} mode={mode} onModeChange={setMode} selected={country?.id ?? null} onSelect={setCountry}
          picking={picking} onPickingChange={setPicking} region={region} onRegionChange={setRegion}
          prediction={forecast.shown} focusPeninsula={focus} />
        <Timeline start={range.start} end={range.end} offset={offset} stepDays={stepDays} onOffsetChange={setOffset} />
      </main>
    </div>
  )
}
