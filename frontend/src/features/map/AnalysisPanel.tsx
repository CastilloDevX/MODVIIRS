import { useMemo, useState, type ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import type { QueryState } from '../../lib/useFireQuery'
import type { CalendarResponse, MediansResponse, PointsResponse, TimelineResponse } from '../../lib/types'
import { AreaChart, BandChart, BarList, Card, Donut, Heatmap, Histogram, Kpi } from './charts'
import { addDays, formatLong } from './dates'
import { ForecastDashboard } from './ForecastDashboard'
import type { Bbox } from './region'
import { boxAreaKm2, denseSeries, pointStats, rangeStats } from './stats'
import './analysis.css'

type Props = {
  region: Bbox
  start: Date
  end: Date
  days: number
  timeline: QueryState<TimelineResponse>
  calendar: QueryState<CalendarResponse>
  medians: QueryState<MediansResponse>
  points: PointsResponse | null
  windowStart: string
  windowEnd: string
  stepFrom: number
  stepTo: number
  onClose: () => void
}

function Async<T>({ state, children }: { state: QueryState<T>; children: (data: T) => ReactNode }) {
  if (state.error) return <p className="card-error">Unavailable: {state.error}</p>
  if (!state.data) return <div className="skeleton" aria-busy="true">Loading…</div>
  return <>{children(state.data)}</>
}

export function AnalysisPanel({ region, start, end, days, timeline, calendar, medians, points, windowStart, windowEnd, stepFrom, stepTo, onClose }: Props) {
  const rows = timeline.data?.data
  const range = useMemo(() => (rows ? rangeStats(rows, start, days) : null), [rows, start, days])
  const hot = useMemo(() => denseSeries(rows, start, days, 'n_hotspots'), [rows, start, days])
  const frp = useMemo(() => denseSeries(rows, start, days, 'frp_sum'), [rows, start, days])
  const ps = useMemo(() => (points ? pointStats(points.data) : null), [points])
  const [view, setView] = useState<'historico' | 'pronostico'>('historico')
  const dateAt = (i: number) => formatLong(addDays(start, i))
  const labels: [string, string] = [formatLong(start), formatLong(end)]
  let card = 0

  return (
    <aside className="analysis-panel" aria-label="Analysis results">
      <header>
        <div>
          <h2>Analysis</h2>
          <p>{Math.abs(region.north - region.south).toFixed(2)}° × {Math.abs(region.east - region.west).toFixed(2)}° · ≈ {Math.round(boxAreaKm2(region)).toLocaleString('en')} km²</p>
        </div>
        <Button type="button" variant="ghost" size="sm" onClick={onClose} aria-label="Hide the analysis panel">Hide ›</Button>
      </header>

      <div className="analysis-tabs" role="group" aria-label="Panel view">
        <button type="button" aria-pressed={view === 'historico'} onClick={() => setView('historico')}>HISTORY</button>
        <button type="button" className="is-forecast" aria-pressed={view === 'pronostico'} onClick={() => setView('pronostico')}>PREDICTIONS ✦</button>
      </div>

      {/* Modelo predictivo (rama predictivo): semana del cursor del timeline */}
      {view === 'pronostico' && <ForecastDashboard region={region} anchor={end} />}

      {view === 'historico' && <>

      <p className="sensor-note">Sensor: VIIRS 375 m (daily series, calendar and seasonality)</p>

      <Card index={card++} title={`Range summary · ${labels[0]} → ${labels[1]}`}>
        <Async state={timeline}>{() => range && (
          <div className="kpis">
            <Kpi label="Hotspots" value={range.total} />
            <Kpi label="Fire days" value={range.activeDays} unit={` / ${range.days}`} />
            <Kpi label="Peak day" value={range.peak} unit={` · ${formatLong(range.peakDate)}`} />
            <Kpi label="Daily mean" value={range.perDay} decimals={1} unit=" /day" />
            <Kpi label="FRP total" value={range.frpSum} unit=" MW" />
            <Kpi label="Max active cells" value={range.maxCells} unit=" /day" />
          </div>
        )}</Async>
      </Card>

      <Card index={card++} title="Hotspots per day" note="The polygon shows daily hotspots; the peak is marked. The light band is the step selected on the timeline.">
        <Async state={timeline}>{() => <AreaChart values={hot} labels={labels} dateAt={dateAt} color="#ff8f00" unit="hotspots" highlight={[stepFrom, stepTo]} />}</Async>
      </Card>

      <Card index={card++} title="Total FRP per day (MW)" note="Sum of the radiative power of all detections of the day. It adds satellite passes, so it can repeat the same fire; it is not emitted energy.">
        <Async state={timeline}>{() => <AreaChart values={frp} labels={labels} dateAt={dateAt} color="#e53935" unit="MW" highlight={[stepFrom, stepTo]} />}</Async>
      </Card>

      <Card index={card++} title={`Current step · ${windowStart}${windowEnd !== windowStart ? ` → ${windowEnd}` : ''}`}
        note={points?.truncated ? 'Result limited to 50,000 detections: the statistics use that sample.' : 'Statistics of all detections in the step (both sensors).'}>
        {!ps ? <div className="skeleton" aria-busy="true">Loading…</div> : (
          <div className="kpis">
            <Kpi label="Detections" value={ps.n} />
            <Kpi label="FRP mean" value={ps.frpMean} decimals={1} unit=" MW" />
            <Kpi label="FRP median" value={ps.frpMedian} decimals={1} unit=" MW" />
            <Kpi label="FRP P90" value={ps.frpP90} decimals={1} unit=" MW" />
            <Kpi label="FRP max" value={ps.frpMax} decimals={1} unit=" MW" />
            <Kpi label="FRP sum" value={ps.frpSum} unit=" MW" />
            <Kpi label="High confidence" value={ps.highPct} decimals={1} unit=" %" />
            <Kpi label="Persistent" value={ps.persistentPct} decimals={1} unit=" %" />
            <Kpi label="FRP ≥ 15 MW" value={ps.comparablePct} decimals={1} unit=" %" />
          </div>
        )}
      </Card>

      <Card index={card++} title="FRP distribution (MW, current step)" note="Log-spaced ranges: almost all fires are small; the tail on the right is the intense events.">
        {ps ? <Histogram counts={ps.histogram} /> : <div className="skeleton" aria-busy="true">Loading…</div>}
      </Card>

      <Card index={card++} title="Day / night and confidence (current step)">
        {ps ? (
          <div className="duo">
            <Donut parts={[{ label: 'Day', value: ps.day, color: '#ffd600' }, { label: 'Night', value: ps.night, color: '#5c6bc0' }]} />
            <Donut parts={[{ label: 'High', value: ps.high, color: '#e53935' }, { label: 'Nominal', value: ps.nominal, color: '#ff8f00' }]} />
          </div>
        ) : <div className="skeleton" aria-busy="true">Loading…</div>}
      </Card>

      <Card index={card++} title="Satellites (current step)">
        {ps ? <BarList items={ps.satellites} /> : <div className="skeleton" aria-busy="true">Loading…</div>}
      </Card>

      <Card index={card++} title="Anomaly calendar (monthly)" note="Colour = z-score of the month's fire-days against the same month in the baseline (blue: below normal, red: above). Grey: month without sensor data. Hover to see AFD, z and percentile.">
        <Async state={calendar}>{d => <Heatmap rows={d.data} />}</Async>
      </Card>

      <Card index={card++} title="Typical seasonality" note="Median (line), interquartile range (strong band), minimum–maximum (faint band) and mean (dots) of fire-days per month in the baseline.">
        <Async state={medians}>{d => <BandChart rows={d.data} />}</Async>
      </Card>

      <p className="panel-foot">Calendar and seasonality metric: fire-days per 0.1° cell, not a hotspot count. Zero detections does not confirm there was no fire (clouds, smoke, sensor gaps).</p>
      </>}
    </aside>
  )
}
