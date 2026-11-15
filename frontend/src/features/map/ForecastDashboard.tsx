import { useEffect, useMemo, useState } from 'react'
import { Calendar } from '@/components/ui/calendar'
import { Card, Kpi } from './charts'
import { addDays, diffDays, isoDate } from './dates'
import type { Bbox } from './region'
import {
  getForecastReliability, getForecastSeries, getForecastValidation, getGlobalCountries,
  type CountryInfo, type ForecastSeries, type ReliabilityWeek, type SeriesRow,
} from './predictions'
import './forecast.css'

/**
 * PREDICTIONS view: how reliable the forecast is for the days after the established date (the final date of the range).
 * Only future days are shown: the forecast starts one week after the established date and covers 2 weeks,
 * the range in which the model is promising.
 *
 * Reliability of a day = validated accuracy (walk-forward AUC) of the model in that time of the year, lowered by the
 * distance to the established date (weeks ahead). Source: walk-forward validation 2015–2025 (prediccion/README.md).
 */
type Props = { region: Bbox | null; anchor: Date }
type Picked = { from: Date; to: Date; ref: string }
type Validation = { years: { year: number; auc: number; base: number }[]; calibration: { prob: number; observed: number; n: number }[] }

/** Walk-forward validation (era VIIRS 2015–2025). 3 weeks is interpolated between the 2- and 4-week results. */
const HORIZONS = [
  { weeks: 1, auc: 0.847, ap: 0.272 },
  { weeks: 2, auc: 0.81, ap: 0.191 },
  { weeks: 3, auc: 0.79, ap: 0.167 },
  { weeks: 4, auc: 0.776, ap: 0.143 },
]
const START_AFTER_DAYS = 7 // the forecast starts one week after the established date
const WINDOW_DAYS = 14 // and covers 2 weeks

/** Level of a reliability value: > 75 % very reliable, > 50 % medium, otherwise no colour. */
const levelOf = (v: number) => (v > 0.75 ? 'high' : v > 0.5 ? 'medium' : null)
const LEVELS = {
  high: { label: 'VERY RELIABLE', color: '#00e676', text: 'You can rely on this forecast.' },
  medium: { label: 'MEDIUM RELIABILITY', color: '#ffc400', text: 'Use it as a hint, not as a certainty.' },
}
/** ISO week (1–52) and ISO year of a date; week 53 counts as 52, like the backend. */
function isoWeekOf(d: Date) {
  const t = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()))
  t.setUTCDate(t.getUTCDate() - ((t.getUTCDay() + 6) % 7) + 3)
  const year = t.getUTCFullYear()
  const jan4 = new Date(Date.UTC(year, 0, 4))
  const week = 1 + Math.round(((t.getTime() - jan4.getTime()) / 86_400_000 - 3 + ((jan4.getUTCDay() + 6) % 7)) / 7)
  return { year, week: Math.min(week, 52) }
}
const fmtDay = (d: Date) => d.toLocaleDateString('en-US', { day: 'numeric', month: 'long', year: 'numeric' })

/** Validated accuracy of the model for a day that is `daysAhead` days after the data cut-off. */
const accuracyAhead = (daysAhead: number) => {
  const weeks = Math.min(Math.max(Math.ceil(daysAhead / 7), 1), HORIZONS.length)
  return HORIZONS[weeks - 1].auc
}

export function ForecastDashboard({ region, anchor }: Props) {
  const [series, setSeries] = useState<{ key: string; data: ForecastSeries | null } | null>(null)
  const [val, setVal] = useState<Validation | null>(null)
  const [countries, setCountries] = useState<CountryInfo[]>([])
  const [season, setSeason] = useState<{ key: string; weeks: ReliabilityWeek[] } | null>(null)
  const [picked, setPicked] = useState<Picked | null>(null)
  const [second, setSecond] = useState(false)
  const key = region ? `${region.west},${region.south},${region.east},${region.north}` : ''

  useEffect(() => {
    if (!region) return
    const ctrl = new AbortController()
    getForecastSeries(region, ctrl.signal)
      .then(data => setSeries({ key, data }))
      .catch(e => { if ((e as Error).name !== 'AbortError') setSeries({ key, data: null }) })
    getForecastReliability(region, ctrl.signal).then(r => setSeason({ key, weeks: r.por_semana })).catch(() => {})
    return () => ctrl.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])

  useEffect(() => {
    const ctrl = new AbortController()
    getForecastValidation(ctrl.signal).then(v => {
      const cal = (v.calibracion as { prob_media: number; observado: number; n: number }[] | undefined) ?? []
      const years = ((v.metricas_por_anio as { anio: number; era: string; auc: number; auc_base: number }[] | undefined) ?? [])
        .filter(y => y.era.startsWith('VIIRS')).map(y => ({ year: y.anio, auc: y.auc, base: y.auc_base }))
      setVal({ years, calibration: cal.map(c => ({ prob: c.prob_media, observed: c.observado, n: c.n })) })
    }).catch(() => {})
    getGlobalCountries(ctrl.signal).then(c => setCountries(c.paises)).catch(() => {})
    return () => ctrl.abort()
  }, [])

  const loaded = series?.key === key ? series.data : undefined
  const isLive = loaded?.escala === 'peninsula_0.5deg'
  const zones = loaded?.zonas.length ?? 0

  // The window of future days: starts one week after the established date and lasts 2 weeks.
  const windowStart = addDays(anchor, START_AFTER_DAYS)
  const windowEnd = addDays(windowStart, WINDOW_DAYS - 1)
  const anchorKey = isoDate(anchor)
  const range = picked && picked.ref === anchorKey ? picked : { from: windowStart, to: windowEnd }

  // Accuracy of the model that covers this region, relative to the Yucatán model the horizons were measured on.
  const scale = useMemo(() => {
    if (!loaded || isLive) return 1
    const cs = countries.filter(c => loaded.paises.includes(c.nombre) && c.auc !== null)
    if (!cs.length) return 1
    const avg = cs.reduce((a, c) => a + (c.auc ?? 0), 0) / cs.length
    return Math.min(1, avg / HORIZONS[0].auc)
  }, [loaded, isLive, countries])

  // Accuracy by time of the year (Yucatán model); the other model has no seasonal breakdown.
  const seasonal = useMemo(() => {
    const m = new Map<number, number>()
    if (isLive && season?.key === key) for (const w of season.weeks) if (w.auc !== null) m.set(w.semana, w.auc)
    return m
  }, [isLive, season, key])

  /** Reliability of a day: seasonal accuracy lowered by the distance to the established date. */
  const reliabilityAt = (day: Date) => {
    const ahead = diffDays(anchor, day)
    const seasonAuc = seasonal.get(isoWeekOf(day).week)
    return seasonAuc !== undefined ? seasonAuc * (accuracyAhead(ahead) / HORIZONS[0].auc) : accuracyAhead(ahead) * scale
  }
  const reliabilityOn = (day: Date) => {
    const ahead = diffDays(anchor, day)
    return ahead >= START_AFTER_DAYS + 1 && ahead <= START_AFTER_DAYS + WINDOW_DAYS ? reliabilityAt(day) : null
  }

  const levelDays = useMemo(() => {
    const out = { high: [] as Date[], medium: [] as Date[] }
    for (let i = 0; i < WINDOW_DAYS; i++) {
      const d = addDays(windowStart, i)
      const lvl = levelOf(reliabilityAt(d))
      if (lvl) out[lvl].push(d)
    }
    return out
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [windowStart, scale, seasonal, anchorKey])

  const picks = useMemo(() => {
    const vals: number[] = []
    for (let d = range.from, n = 0; d <= range.to && n < 60; d = addDays(d, 1), n++) {
      const v = reliabilityOn(d)
      if (v !== null) vals.push(v)
    }
    return { avg: vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null, days: vals.length }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [range.from, range.to, anchorKey, scale])

  // Same weeks of the year in every past year: what the model forecast vs what happened (anomalous zones).
  const compare = useMemo(() => {
    const rows: SeriesRow[] = loaded?.data ?? []
    const weeks = new Set<number>()
    for (let d = range.from, n = 0; d <= range.to && n < 60; d = addDays(d, 1), n++) weeks.add(isoWeekOf(d).week)
    const byYear = new Map<number, { f: number; o: number }>()
    for (const r of rows) {
      if (r.esperadas === null || r.anomalias === null) continue
      const iso = isoWeekOf(new Date(`${r.semana}T12:00:00`))
      if (!weeks.has(iso.week)) continue
      const e = byYear.get(iso.year) ?? { f: 0, o: 0 }
      e.f += r.esperadas
      e.o += r.anomalias
      byYear.set(iso.year, e)
    }
    const years = [...byYear.keys()].sort()
    const total = years.reduce((a, y) => a + (byYear.get(y)?.o ?? 0), 0)
    const items = years.map(y => {
      const e = byYear.get(y)!
      // baseline = the average of the other years for the same weeks ("what a normal year looks like")
      const base = years.length > 1 ? (total - e.o) / (years.length - 1) : e.o
      return { year: y, forecast: e.f, observed: e.o, modelError: Math.abs(e.f - e.o), baselineError: Math.abs(base - e.o) }
    })
    const mean = (f: (i: (typeof items)[number]) => number) => (items.length ? items.reduce((a, i) => a + f(i), 0) / items.length : 0)
    return { items, modelMae: mean(i => i.modelError), baseMae: mean(i => i.baselineError) }
  }, [loaded, range.from, range.to])

  if (!region) return null
  let card = 1 // entrance stagger, after the tabs

  if (loaded === undefined) return <Card index={card++} title="Predictions"><div className="skeleton" aria-busy="true">Analysing the region…</div></Card>
  if (loaded === null) return <Card index={card++} title="Predictions"><p className="card-error">Unavailable: the forecast engine is not responding (start the backend on port 5000).</p></Card>
  if (zones === 0) {
    return (
      <Card index={card++} title="Predictions" note="Coverage: Yucatán Peninsula (live, 0.5° zones) and Mexico, Brazil, Russia, Australia, Angola and DR Congo (1° zones).">
        <p className="card-error">This region is outside the monitored area. Select a region inside the coverage.</p>
      </Card>
    )
  }

  const level = picks.avg === null ? null : levelOf(picks.avg)
  const info = level ? LEVELS[level] : null
  const same = range.from.getTime() === range.to.getTime()

  return (
    <>
      <Card index={card++} title="How reliable is the forecast?">
        <div className="rel">
          <div className="rel-result" style={{ ['--lvl' as string]: info?.color ?? '#6b6b6b' }}>
            <span className="rel-dates">{fmtDay(range.from)}{same ? '' : ` → ${fmtDay(range.to)}`}</span>
            {picks.avg === null ? (
              <span className="rel-none">No forecast for these dates.</span>
            ) : (
              <>
                <span className="rel-pct">{Math.round(picks.avg * 100)}<small>%</small></span>
                <span className="rel-badge">{info ? info.label : 'LOW RELIABILITY'}</span>
                <span className="rel-text">{info ? info.text : 'Below 50 %: this forecast is not recommended.'}{!same && ` Average of ${picks.days} forecast days.`}</span>
              </>
            )}
          </div>

          <Calendar mode="range" weekStartsOn={1} startMonth={windowStart} endMonth={windowEnd}
            selected={{ from: range.from, to: range.to }} defaultMonth={windowStart}
            disabled={{ before: windowStart, after: windowEnd }}
            modifiers={levelDays} modifiersClassNames={{ high: 'rel-high', medium: 'rel-medium' }}
            className="rel-calendar"
            onDayClick={day => {
              // first tap: one day; second tap: the end of a period (in any order)
              if (!second) { setPicked({ from: day, to: day, ref: anchorKey }); setSecond(true) }
              else { setPicked(day < range.from ? { from: day, to: range.from, ref: anchorKey } : { from: range.from, to: day, ref: anchorKey }); setSecond(false) }
            }} />

          <ul className="rel-legend" aria-label="Meaning of the colours">
            <li><span style={{ background: '#00e676' }} /><b>Green</b> very reliable (over 75 %)</li>
            <li><span style={{ background: '#ffc400' }} /><b>Yellow</b> medium reliability (over 50 %)</li>
            <li><span style={{ background: 'transparent', border: '1px solid #777' }} /><b>No colour</b> low reliability or no forecast</li>
          </ul>
        </div>
      </Card>

      {seasonal.size > 0 && (
        <Card index={card++} title="Reliability through the year" note="Accuracy of the forecast for each week of the year. Green: over 75 %. Yellow: over 50 %. The marked band is the period you selected; this is why some dates are yellow and others green.">
          <SeasonChart seasonal={seasonal} weeks={[...new Set([range.from, range.to].map(d => isoWeekOf(d).week))]} />
        </Card>
      )}

      {compare.items.length > 0 && (
        <>
          <Card index={card++} title="Forecast vs. reality" note="Anomalous zones in these same weeks of the year, one pair of bars per past year. The closer the orange bar is to the white one, the better the forecast.">
            <PairChart items={compare.items.map(i => ({ label: String(i.year), a: i.forecast, b: i.observed }))} aColor="#ff8f00" bColor="#ffffff" unit="zones" />
            <div className="fd-legend"><span><i style={{ background: '#ff8f00' }} />forecast</span><span><i style={{ background: '#fff' }} />what happened</span></div>
          </Card>

          <Card index={card++} title="Forecast error" note="How far off each estimate was in those weeks. Baseline = guessing a normal year (the average of the other years). Lower is better.">
            <div className="kpis strong">
              <Kpi label="Model error" value={compare.modelMae} decimals={1} unit=" zones" color="#00e676" />
              <Kpi label="Baseline error" value={compare.baseMae} decimals={1} unit=" zones" />
              <Kpi label="Error reduced by" value={compare.baseMae > 0 ? Math.max(0, (1 - compare.modelMae / compare.baseMae) * 100) : null} decimals={0} unit=" %" color="#00e676" />
            </div>
            <PairChart items={compare.items.map(i => ({ label: String(i.year), a: i.modelError, b: i.baselineError }))} aColor="#00e676" bColor="#8a8a8a" unit="zones" />
            <div className="fd-legend"><span><i style={{ background: '#00e676' }} />model error</span><span><i style={{ background: '#8a8a8a' }} />baseline error</span></div>
          </Card>
        </>
      )}

      {val && val.years.length > 0 && (
        <Card index={card++} title="Why it can be trusted" note="Accuracy of the model (green) against simply using historical averages (grey), year by year. The model stays well above the baseline in every year.">
          <SkillChart years={val.years} />
          <div className="fd-legend"><span><i style={{ background: '#00e676' }} />model accuracy</span><span><i className="fd-k-base" />baseline accuracy</span></div>
        </Card>
      )}

      {val && val.calibration.length > 0 && (
        <Card index={card++} title="What it says vs. what happens" note="Average forecast probability (orange) against the frequency actually observed (white). Good up to ~40 %; above 70 % the model is optimistic (small sample): read it as “high risk”.">
          <CalibrationChart bins={val.calibration} />
        </Card>
      )}

      <p className="panel-foot">Reliability is the validated accuracy of the model at each distance: how often, out of 100, it ranks a zone with unusual activity above a normal one. It forecasts anomalous hotspot activity, not the location of wildfires.</p>
    </>
  )
}

const W = 320

const AXIS_H = 120, PAD = { l: 28, r: 6, t: 8, b: 16 }

/** Pairs of bars per label (e.g. forecast vs reality per year). */
function PairChart({ items, aColor, bColor, unit }: { items: { label: string; a: number; b: number }[]; aColor: string; bColor: string; unit: string }) {
  const max = Math.max(1, ...items.map(i => Math.max(i.a, i.b)))
  const bw = (W - PAD.l - PAD.r) / items.length
  const y = (v: number) => PAD.t + (1 - v / max) * (AXIS_H - PAD.t - PAD.b)
  return (
    <svg viewBox={`0 0 ${W} ${AXIS_H}`} role="img" aria-label="Comparison by year">
      {[0, 0.5, 1].map(t => <g key={t}><line x1={PAD.l} x2={W - PAD.r} y1={y(max * t)} y2={y(max * t)} className="grid" /><text x={PAD.l - 4} y={y(max * t) + 3} className="axis" textAnchor="end">{Math.round(max * t)}</text></g>)}
      {items.map((it, i) => (
        <g key={it.label}>
          <rect className="bar-up" style={{ animationDelay: `${i * 50}ms` }} x={PAD.l + i * bw + bw * 0.08} width={bw * 0.4} y={y(it.a)} height={y(0) - y(it.a)} rx="2" fill={aColor}><title>{`${it.label}: ${it.a.toFixed(1)} ${unit}`}</title></rect>
          <rect className="bar-up" style={{ animationDelay: `${i * 50 + 25}ms` }} x={PAD.l + i * bw + bw * 0.52} width={bw * 0.4} y={y(it.b)} height={y(0) - y(it.b)} rx="2" fill={bColor}><title>{`${it.label}: ${it.b.toFixed(1)} ${unit}`}</title></rect>
          <text x={PAD.l + i * bw + bw / 2} y={AXIS_H - 3} className="axis" textAnchor="middle">{it.label.slice(2)}</text>
        </g>
      ))}
    </svg>
  )
}

/** Model accuracy vs baseline accuracy, year by year. */
function SkillChart({ years }: { years: { year: number; auc: number; base: number }[] }) {
  const x = (i: number) => PAD.l + (years.length <= 1 ? 0 : (i / (years.length - 1)) * (W - PAD.l - PAD.r))
  const y = (v: number) => PAD.t + (1 - (v - 0.5) / 0.5) * (AXIS_H - PAD.t - PAD.b)
  const model = years.map((p, i) => `${x(i).toFixed(1)},${y(p.auc).toFixed(1)}`)
  const base = years.map((p, i) => `${x(i).toFixed(1)},${y(p.base).toFixed(1)}`)
  return (
    <svg viewBox={`0 0 ${W} ${AXIS_H}`} role="img" aria-label="Model accuracy vs baseline by year">
      {[0.5, 0.75, 1].map(t => <g key={t}><line x1={PAD.l} x2={W - PAD.r} y1={y(t)} y2={y(t)} className="grid" /><text x={PAD.l - 4} y={y(t) + 3} className="axis" textAnchor="end">{Math.round(t * 100)}%</text></g>)}
      <polygon className="area-fill" points={[...model, ...[...base].reverse()].join(' ')} fill="#00e676" opacity=".16" />
      <polyline className="draw" pathLength={1} points={base.join(' ')} fill="none" stroke="#9a9a9a" strokeWidth="1.5" strokeDasharray="1" />
      <polyline className="draw" pathLength={1} points={model.join(' ')} fill="none" stroke="#00e676" strokeWidth="2" />
      {years.map((p, i) => <circle key={p.year} className="pop" cx={x(i)} cy={y(p.auc)} r="2.6" fill="#00e676"><title>{`${p.year}: model ${Math.round(p.auc * 100)} % · baseline ${Math.round(p.base * 100)} %`}</title></circle>)}
      {years.map((p, i) => <text key={p.year} x={x(i)} y={AXIS_H - 3} className="axis" textAnchor="middle">{String(p.year).slice(2)}</text>)}
    </svg>
  )
}

/** Accuracy for each week of the year with the 75 % / 50 % reliability lines and the selected weeks highlighted. */
function SeasonChart({ seasonal, weeks }: { seasonal: Map<number, number>; weeks: number[] }) {
  const x = (w: number) => PAD.l + ((w - 1) / 51) * (W - PAD.l - PAD.r)
  const y = (v: number) => PAD.t + (1 - (v - 0.5) / 0.5) * (AXIS_H - PAD.t - PAD.b)
  const pts = [...seasonal].sort((a, b) => a[0] - b[0])
  const line = pts.map(([w, v]) => `${x(w).toFixed(1)},${y(v).toFixed(1)}`).join(' ')
  const lo = Math.min(...weeks), hi = Math.max(...weeks)
  return (
    <svg viewBox={`0 0 ${W} ${AXIS_H}`} role="img" aria-label="Reliability by week of the year">
      {[0.5, 0.75, 1].map(t => <g key={t}><line x1={PAD.l} x2={W - PAD.r} y1={y(t)} y2={y(t)} className="grid" /><text x={PAD.l - 4} y={y(t) + 3} className="axis" textAnchor="end">{Math.round(t * 100)}%</text></g>)}
      <rect x={PAD.l} width={W - PAD.l - PAD.r} y={y(0.75)} height={y(0.5) - y(0.75)} fill="#ffc400" opacity=".1" />
      <rect x={PAD.l} width={W - PAD.l - PAD.r} y={y(1)} height={y(0.75) - y(1)} fill="#00e676" opacity=".07" />
      <rect className="step-band" x={x(lo) - 3} width={Math.max(6, x(hi) - x(lo) + 6)} y={PAD.t} height={AXIS_H - PAD.t - PAD.b} />
      <polyline className="draw" pathLength={1} points={line} fill="none" stroke="#fff" strokeWidth="1.8" />
      {pts.map(([w, v]) => <circle key={w} cx={x(w)} cy={y(v)} r="1.8" fill={levelOf(v) === 'high' ? '#00e676' : '#ffc400'}><title>{`Week ${w}: ${Math.round(v * 100)} %`}</title></circle>)}
      {['Jan', 'Apr', 'Jul', 'Oct'].map((m, i) => <text key={m} x={x(1 + i * 13)} y={AXIS_H - 3} className="axis">{m}</text>)}
    </svg>
  )
}

function CalibrationChart({ bins }: { bins: { prob: number; observed: number; n: number }[] }) {
  const h = 110, padL = 26, padB = 16, padT = 8
  const max = Math.max(0.1, ...bins.map(b => Math.max(b.prob, b.observed)))
  const bw = (W - padL - 6) / bins.length
  const y = (v: number) => padT + (1 - v / max) * (h - padT - padB)
  return (
    <svg viewBox={`0 0 ${W} ${h}`} role="img" aria-label="Forecast vs. observed probability">
      {[0, 0.5, 1].map(t => <g key={t}><line x1={padL} x2={W - 6} y1={y(max * t)} y2={y(max * t)} className="grid" /><text x={padL - 4} y={y(max * t) + 3} className="axis" textAnchor="end">{Math.round(max * t * 100)}%</text></g>)}
      {bins.map((b, i) => (
        <g key={i}>
          <rect className="bar-up" style={{ animationDelay: `${i * 60}ms` }} x={padL + i * bw + bw * 0.1} width={bw * 0.38} y={y(b.prob)} height={y(0) - y(b.prob)} rx="2" fill="#ff8f00"><title>{`forecast ${(b.prob * 100).toFixed(1)} % · n = ${b.n.toLocaleString('en')}`}</title></rect>
          <rect className="bar-up" style={{ animationDelay: `${i * 60 + 30}ms` }} x={padL + i * bw + bw * 0.5} width={bw * 0.38} y={y(b.observed)} height={y(0) - y(b.observed)} rx="2" fill="#fff"><title>{`observed ${(b.observed * 100).toFixed(1)} %`}</title></rect>
          <text x={padL + i * bw + bw / 2} y={h - 3} className="axis" textAnchor="middle">{Math.round(b.prob * 100)}%</text>
        </g>
      ))}
    </svg>
  )
}
