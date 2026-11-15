import { useState } from 'react'
import { Link } from 'react-router-dom'
import logo from '../../assets/logo.png'
import { Input } from '@/components/ui/input'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { DateField } from './DateField'
import { BASEMAPS } from './layers'
import { MapView, type ViewMode } from './MapView'
import { RangeCalendar } from './RangeCalendar'
import { Timeline } from './Timeline'
import { diffDays, snapOffset } from './dates'
import './map.css'

export function MapPage() {
  const [range, setRange] = useState({ start: new Date(2026, 9, 10), end: new Date(2026, 9, 17) })
  const [offset, setOffset] = useState(0)
  const [stepDays, setStepDays] = useState(1)
  const [basemap, setBasemap] = useState(BASEMAPS[0].id)
  const [mode, setMode] = useState<ViewMode>('3d')
  const days = diffDays(range.start, range.end)

  const changeRange = (start: Date, end: Date) => { setRange({ start, end }); setOffset(0); setStepDays(s => Math.min(s, Math.max(diffDays(start, end), 1))) }
  const changeStep = (n: number) => { setStepDays(n); setOffset(o => snapOffset(o, n, days)) }

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
        <div className="field">
          <h2 className="label">Imagery</h2>
          <ToggleGroup variant="outline" className="w-full" value={[basemap]} aria-label="Imagenología"
            onValueChange={v => { if (v[0]) setBasemap(v[0]) }}>
            {BASEMAPS.map(b => <ToggleGroupItem key={b.id} value={b.id} className="flex-1">{b.label}</ToggleGroupItem>)}
          </ToggleGroup>
        </div>
      </aside>
      <main className="stage">
        <MapView basemap={basemap} mode={mode} onModeChange={setMode} />
        <Timeline start={range.start} end={range.end} offset={offset} stepDays={stepDays} onOffsetChange={setOffset} />
      </main>
    </div>
  )
}
