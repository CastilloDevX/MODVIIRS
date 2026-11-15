import { useState } from 'react'
import { Link } from 'react-router-dom'
import logo from '../../assets/logo.png'
import { Button, buttonVariants } from '@/components/ui/button'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { COUNTRY_SELECTION, type Country } from './countries'
import { DateField } from './DateField'
import { BASEMAPS } from './layers'
import { MapView, type ViewMode } from './MapView'
import { RangeCalendar } from './RangeCalendar'
import type { Bbox } from './region'
import { Timeline } from './Timeline'
import { PHASES, countPhases, type PhaseId } from './hotspots'
import { AnalysisPanel } from './AnalysisPanel'
import { dayPhases, denseSeries } from './stats'
import { STEP_UNITS, addDays, diffDays, isoDate, snapToStops, stepEnd, stepStops, type StepUnit } from './dates'
import { getPointsCsvUrl } from '../../lib/api'
import { useFiresCalendar } from '../../lib/hooks/useFiresCalendar'
import { useFiresMedians } from '../../lib/hooks/useFiresMedians'
import { useFiresPoints } from '../../lib/hooks/useFiresPoints'
import { useFiresTimeline } from '../../lib/hooks/useFiresTimeline'
import type { SensorGroup } from '../../lib/types'
import './map.css'

const fmt = (v: number, pos: string, neg: string) => `${Math.abs(v).toFixed(2)}° ${v >= 0 ? pos : neg}`
const BASEMAP = BASEMAPS[0].id

export function MapPage() {
  const [range, setRange] = useState({ start: new Date(2012, 11, 1), end: new Date(2025, 11, 31) })
  const [offset, setOffset] = useState(0)
  const [stepUnit, setStepUnit] = useState<StepUnit>('month')
  const [country, setCountry] = useState<Country | null>(null)
  const [picking, setPicking] = useState(false)
  const [region, setRegion] = useState<Bbox | null>(null)
  const [phases, setPhases] = useState<PhaseId[]>(['yellow', 'orange', 'red'])
  const [sensor, setSensor] = useState<SensorGroup>('VIIRS')
  const [panelOpen, setPanelOpen] = useState(true)
  const [mode, setMode] = useState<ViewMode>('3d')
  const days = diffDays(range.start, range.end)
  const stops = stepStops(range.start, range.end, stepUnit, 1)

  // Hotspots of the step the timeline cursor is on.
  const windowStart = isoDate(addDays(range.start, offset))
  const windowEnd = isoDate(addDays(range.start, stepEnd(offset, stops, days)))
  const { data: pointsResponse, loading, error } = useFiresPoints(region, windowStart, windowEnd, {})

  const timeline = useFiresTimeline(region, isoDate(range.start), isoDate(range.end), sensor)
  const calendar = useFiresCalendar(region, sensor)
  const medians = useFiresMedians(region, sensor)
  const timelineRows = timeline.data?.data
  const hoverSeries = timelineRows ? denseSeries(timelineRows, range.start, days, 'n_hotspots') : null
  const phaseDays = hoverSeries ? dayPhases(hoverSeries, range.start) : null
  const counts = countPhases(region ? pointsResponse?.data ?? null : null)

  const changeRange = (start: Date, end: Date) => { setRange({ start, end }); setOffset(0) }
  const changeStepUnit = (unit: StepUnit) => {
    setStepUnit(unit)
    setOffset(o => snapToStops(o, stepStops(range.start, range.end, unit, 1), days))
  }

  const togglePicking = () => {
    if (picking) { setPicking(false); return }
    setRegion(null)
    setPicking(true)
    document.querySelector('.stage')?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="map-page">
      <aside className="sidebar">
        <Link to="/" aria-label="MODVIIRS"><img className="logo" src={logo} alt="MODVIIRS" /></Link>
        <div className="field">
          <h2 className="label">Region</h2>
          <Button type="button" variant="outline" className="region-button" aria-pressed={picking} onClick={togglePicking}>{picking ? 'Cancel' : 'Select'}</Button>
          {picking && <p className="hint">Click (or tap) the first corner, then the opposite one. Drag to move the map. Esc cancels.</p>}
          {!region && !picking && <p className="hint">Select a region to load the calendar and the hotspots.</p>}
          {region && !picking && (
            <div className="country-field">
              <span>{fmt(region.north, 'N', 'S')} · {fmt(region.south, 'N', 'S')}<br />{fmt(region.west, 'E', 'W')} · {fmt(region.east, 'E', 'W')}</span>
              <button type="button" aria-label="Quitar región" onClick={() => setRegion(null)}>×</button>
            </div>
          )}
        </div>
        {region && !picking && (
          <>
            <h2 className="label">Calendar</h2>
            <RangeCalendar start={range.start} end={range.end} onChange={changeRange} phaseDays={phaseDays} />
            <div className="dates">
              <DateField label="Start date" value={range.start} max={range.end} onChange={d => changeRange(d, range.end)} />
              <DateField label="Final date" value={range.end} min={range.start} onChange={d => changeRange(range.start, d)} />
            </div>
            <a className={`${buttonVariants({ variant: 'outline' })} export-button`} href={getPointsCsvUrl(region, isoDate(range.start), isoDate(range.end), {})} download="hotspots.csv">
              Export CSV
            </a>
            <p className="hint">
              {loading ? 'Loading hotspots…' : error ? `Could not load hotspots: ${error}` : pointsResponse ? `${pointsResponse.count.toLocaleString('en')} hotspots · ${windowStart}${windowEnd !== windowStart ? ` → ${windowEnd}` : ''}` : ''}
            </p>
          </>
        )}
        {COUNTRY_SELECTION && <div className="field">
          <h2 className="label">Country</h2>
          <div className="country-field">
            <span>{country ? country.name : 'Click a country on the map'}</span>
            {country && <button type="button" aria-label="Quitar selección de país" onClick={() => setCountry(null)}>×</button>}
          </div>
        </div>}
      </aside>
      <main className="stage">
        <MapView basemap={BASEMAP} mode={mode} onModeChange={setMode} selected={country?.id ?? null} onSelect={setCountry}
          picking={picking} onPickingChange={setPicking} region={region} onRegionChange={setRegion}
          points={region ? pointsResponse?.data ?? null : null} truncated={region ? pointsResponse?.truncated ?? false : false}
          visiblePhases={phases}
          panel={region && !picking ? (panelOpen ? (
            <AnalysisPanel key={`${region.west},${region.south},${region.east},${region.north}`} region={region} start={range.start} end={range.end} days={days} sensor={sensor} onSensorChange={setSensor}
              timeline={timeline} calendar={calendar} medians={medians} points={pointsResponse}
              windowStart={windowStart} windowEnd={windowEnd} stepFrom={offset} stepTo={stepEnd(offset, stops, days)} onClose={() => setPanelOpen(false)} />
          ) : <button type="button" className="panel-tab" onClick={() => setPanelOpen(true)}>ANÁLISIS</button>) : null}
          filters={region && !picking ? (
            <>
              <h2 className="label">Hotspots · intensidad (0 – 1)</h2>
              <ToggleGroup multiple orientation="vertical" variant="outline" value={phases} aria-label="Fases de intensidad de los hotspots"
                onValueChange={v => setPhases(v as PhaseId[])}>
                {PHASES.map(ph => (
                  <ToggleGroupItem key={ph.id} value={ph.id} className="phase-item">
                    <span className="phase-dot" style={{ background: ph.color }} />
                    <span>{ph.label}</span>
                    <span className="phase-range">{ph.range}</span>
                    <span className="phase-count">{counts[ph.id].toLocaleString('en')}</span>
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
            </>
          ) : null}
          controls={region && !picking ? (
            <div className="control-group scale-group">
              <ToggleGroup variant="outline" value={[stepUnit]} aria-label="Escala de los pasos"
                onValueChange={v => { if (v[0]) changeStepUnit(v[0] as StepUnit) }}>
                {STEP_UNITS.map(u => <ToggleGroupItem key={u.id} value={u.id}>{u.label}</ToggleGroupItem>)}
              </ToggleGroup>
              <span className="caption">Escala de los pasos de la línea de tiempo</span>
            </div>
          ) : null} />
        {region && !picking && <Timeline start={range.start} end={range.end} offset={offset} stops={stops} series={hoverSeries} onOffsetChange={setOffset} />}
      </main>
    </div>
  )
}
