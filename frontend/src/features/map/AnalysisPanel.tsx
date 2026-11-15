import { useMemo, useState, type ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import type { QueryState } from '../../lib/useFireQuery'
import type { CalendarResponse, MediansResponse, PointsResponse, TimelineResponse } from '../../lib/types'
import { AreaChart, BandChart, BarList, Card, CountUp, Donut, Heatmap, Histogram } from './charts'
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
  if (state.error) return <p className="card-error">No disponible: {state.error}</p>
  if (!state.data) return <div className="skeleton" aria-busy="true">Cargando…</div>
  return <>{children(state.data)}</>
}

function Kpi({ label, value, unit, decimals = 0, text }: { label: string; value?: number; unit?: string; decimals?: number; text?: string }) {
  return (
    <div className="kpi">
      <span className="kpi-label">{label}</span>
      <span className="kpi-value">{value === undefined ? text : <CountUp value={value} decimals={decimals} />}{unit && <small>{unit}</small>}</span>
    </div>
  )
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
    <aside className="analysis-panel" aria-label="Resultados del análisis">
      <header>
        <div>
          <h2>Análisis</h2>
          <p>{Math.abs(region.north - region.south).toFixed(2)}° × {Math.abs(region.east - region.west).toFixed(2)}° · ≈ {Math.round(boxAreaKm2(region)).toLocaleString('en')} km²</p>
        </div>
        <Button type="button" variant="ghost" size="sm" onClick={onClose} aria-label="Ocultar panel de análisis">Ocultar ›</Button>
      </header>

      <div className="analysis-tabs" role="group" aria-label="Vista del panel">
        <button type="button" aria-pressed={view === 'historico'} onClick={() => setView('historico')}>HISTÓRICO</button>
        <button type="button" className="is-forecast" aria-pressed={view === 'pronostico'} onClick={() => setView('pronostico')}>PRONÓSTICO ✦</button>
      </div>

      {/* Modelo predictivo (rama predictivo): semana del cursor del timeline */}
      {view === 'pronostico' && <ForecastDashboard region={region} date={addDays(start, stepFrom)} embedded />}

      {view === 'historico' && <>

      <p className="sensor-note">Sensor: VIIRS 375 m (serie diaria, calendario y estacionalidad)</p>

      <Card index={card++} title={`Resumen del rango · ${labels[0]} → ${labels[1]}`}>
        <Async state={timeline}>{() => range && (
          <div className="kpis">
            <Kpi label="Hotspots" value={range.total} />
            <Kpi label="Días con fuego" value={range.activeDays} unit={` / ${range.days}`} />
            <Kpi label="Día pico" value={range.peak} unit={` · ${formatLong(range.peakDate)}`} />
            <Kpi label="Media diaria" value={range.perDay} decimals={1} unit=" /día" />
            <Kpi label="FRP total" value={range.frpSum} unit=" MW" />
            <Kpi label="Celdas activas máx." value={range.maxCells} unit=" /día" />
          </div>
        )}</Async>
      </Card>

      <Card index={card++} title="Hotspots por día" note="El polígono muestra los hotspots diarios; el pico está marcado. La banda clara es el paso seleccionado en la línea de tiempo.">
        <Async state={timeline}>{() => <AreaChart values={hot} labels={labels} dateAt={dateAt} color="#ff8f00" unit="hotspots" highlight={[stepFrom, stepTo]} />}</Async>
      </Card>

      <Card index={card++} title="FRP total por día (MW)" note="Suma de la potencia radiativa de todas las detecciones del día. Suma de pasadas: puede repetir el mismo fuego; no es energía emitida.">
        <Async state={timeline}>{() => <AreaChart values={frp} labels={labels} dateAt={dateAt} color="#e53935" unit="MW" highlight={[stepFrom, stepTo]} />}</Async>
      </Card>

      <Card index={card++} title={`Paso actual · ${windowStart}${windowEnd !== windowStart ? ` → ${windowEnd}` : ''}`}
        note={points?.truncated ? 'Resultado limitado a 50 000 detecciones: las estadísticas usan esa muestra.' : 'Estadísticas de todas las detecciones del paso (ambos sensores).'}>
        {!ps ? <div className="skeleton" aria-busy="true">Cargando…</div> : (
          <div className="kpis">
            <Kpi label="Detecciones" value={ps.n} />
            <Kpi label="FRP media" value={ps.frpMean} decimals={1} unit=" MW" />
            <Kpi label="FRP mediana" value={ps.frpMedian} decimals={1} unit=" MW" />
            <Kpi label="FRP P90" value={ps.frpP90} decimals={1} unit=" MW" />
            <Kpi label="FRP máx." value={ps.frpMax} decimals={1} unit=" MW" />
            <Kpi label="FRP suma" value={ps.frpSum} unit=" MW" />
            <Kpi label="Confianza alta" value={ps.highPct} decimals={1} unit=" %" />
            <Kpi label="Persistentes" value={ps.persistentPct} decimals={1} unit=" %" />
            <Kpi label="FRP ≥ 15 MW" value={ps.comparablePct} decimals={1} unit=" %" />
          </div>
        )}
      </Card>

      <Card index={card++} title="Distribución de FRP (MW, paso actual)" note="Escala logarítmica por rangos: casi todos los fuegos son pequeños; la cola a la derecha son los eventos intensos.">
        {ps ? <Histogram counts={ps.histogram} /> : <div className="skeleton" aria-busy="true">Cargando…</div>}
      </Card>

      <Card index={card++} title="Día / noche y confianza (paso actual)">
        {ps ? (
          <div className="duo">
            <Donut parts={[{ label: 'Día', value: ps.day, color: '#ffd600' }, { label: 'Noche', value: ps.night, color: '#5c6bc0' }]} />
            <Donut parts={[{ label: 'Alta', value: ps.high, color: '#e53935' }, { label: 'Nominal', value: ps.nominal, color: '#ff8f00' }]} />
          </div>
        ) : <div className="skeleton" aria-busy="true">Cargando…</div>}
      </Card>

      <Card index={card++} title="Satélites (paso actual)">
        {ps ? <BarList items={ps.satellites} /> : <div className="skeleton" aria-busy="true">Cargando…</div>}
      </Card>

      <Card index={card++} title="Calendario de anomalías (mensual)" note="Color = z-score de los días-con-fuego del mes frente al mismo mes en la línea base (azul: menos de lo normal, rojo: más). Gris: mes sin datos del sensor. Pasa el cursor para ver AFD, z y percentil.">
        <Async state={calendar}>{d => <Heatmap rows={d.data} />}</Async>
      </Card>

      <Card index={card++} title="Estacionalidad típica" note="Mediana (línea), rango intercuartil (banda fuerte), mínimo–máximo (banda tenue) y media (puntos) de días-con-fuego por mes de la línea base.">
        <Async state={medians}>{d => <BandChart rows={d.data} />}</Async>
      </Card>

      <p className="panel-foot">Métrica de calendario y estacionalidad: días-con-fuego por celda de 0.1°, no conteo de hotspots. Cero detecciones no confirma ausencia de fuego (nubes, humo, huecos de sensor).</p>
      </>}
    </aside>
  )
}
