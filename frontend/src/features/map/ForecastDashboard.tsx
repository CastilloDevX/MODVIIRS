import { useEffect, useMemo, useState } from 'react'
import type { Bbox } from './region'
import {
  getCurrentForecast, getForecastSeries, getForecastValidation, getGlobalCountries, mondayOf,
  type CountryInfo, type CurrentForecast, type ForecastSeries, type SeriesRow,
} from './predictions'
import './forecast.css'

/**
 * Pronóstico de actividad ANÓMALA de puntos de calor para la región seleccionada (rama `predictivo`).
 *
 * Uso:
 *   <ForecastDashboard region={bbox} date={fechaDelTimeline} embedded />   // dentro de un panel (p. ej. AnalysisPanel)
 *   <ForecastDashboard region={bbox} date={fecha} onClose={...} />         // tarjeta flotante sobre el mapa
 *
 * Datos (backend Flask, docs/API_PREDICCIONES.md):
 *   GET /api/predictions/series      serie semanal; el backend elige el modelo: Península de Yucatán
 *                                    (0.5°, clima NASA POWER, en vivo 2026) o 6 países (1°, 2023–2025)
 *   GET /api/predictions             semana en curso y próxima (solo península, en vivo)
 *   GET /api/predictions/validation  y /api/predictions/global/countries  → precisión comprobada
 */
type Props = { region: Bbox | null; date: Date; onClose?: () => void; embedded?: boolean }
type Trust = { auc: number; base: number; scope: string }

const ALERTS = [
  { min: 0.5, key: 'CRÍTICO', color: '#ff4d4f', phrase: 'un riesgo crítico de actividad anómala de puntos de calor' },
  { min: 0.3, key: 'ELEVADO', color: '#ff8a3d', phrase: 'un riesgo elevado de actividad anómala de puntos de calor' },
  { min: 0.1, key: 'VIGILANCIA', color: '#f5c542', phrase: 'señales tempranas de actividad inusual de puntos de calor' },
  { min: 0, key: 'NORMAL', color: '#3ccf8e', phrase: 'condiciones dentro de su rango estacional habitual' },
]
const alertOf = (p: number | null | undefined) => (p == null ? null : ALERTS.find(a => p >= a.min) ?? ALERTS[3])

const fmtWeek = (iso?: string) =>
  iso ? new Date(`${iso}T12:00:00`).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' }) : '—'
const round1 = (v: number) => (v >= 10 ? Math.round(v).toString() : v.toFixed(1))
const WEEKS_BEFORE = 104, WEEKS_AFTER = 26 // ventana de las gráficas alrededor de la semana elegida

/** Número animado (cuenta hacia arriba). */
function useCountUp(target: number | null, ms = 900) {
  const [v, setV] = useState(0)
  useEffect(() => {
    if (target === null) return
    let raf = 0
    const t0 = performance.now()
    const tick = (t: number) => {
      const k = Math.min(1, (t - t0) / ms)
      setV(target * (1 - Math.pow(1 - k, 3)))
      if (k < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [target, ms])
  return target === null ? null : v
}

export function ForecastDashboard({ region, date, onClose, embedded = false }: Props) {
  const [live, setLive] = useState<CurrentForecast | null>(null)
  const [series, setSeries] = useState<{ key: string; data: ForecastSeries | null } | null>(null)
  const [valPen, setValPen] = useState<{ auc: number; base: number; auc26?: number; base26?: number } | null>(null)
  const [countries, setCountries] = useState<CountryInfo[]>([])
  const key = region ? `${region.west},${region.south},${region.east},${region.north}` : ''

  useEffect(() => {
    if (!region) return
    const ctrl = new AbortController()
    getCurrentForecast(ctrl.signal, region).then(setLive).catch(() => {})
    getForecastSeries(region, ctrl.signal)
      .then(data => setSeries({ key, data }))
      .catch(e => { if ((e as Error).name !== 'AbortError') setSeries({ key, data: null }) })
    return () => ctrl.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])

  useEffect(() => {
    const ctrl = new AbortController()
    getForecastValidation(ctrl.signal).then(v => {
      const h = v.resumen_h1 as { auc: number; auc_base: number } | undefined
      const t = v.temporada_2026_vivo as { auc?: number; auc_base?: number } | undefined
      if (h) setValPen({ auc: h.auc, base: h.auc_base, auc26: t?.auc, base26: t?.auc_base })
    }).catch(() => {})
    getGlobalCountries(ctrl.signal).then(c => setCountries(c.paises)).catch(() => {})
    return () => ctrl.abort()
  }, [])

  const loaded = series?.key === key ? series.data : undefined
  const rows = useMemo(() => loaded?.data ?? [], [loaded])
  const isLive = loaded?.escala === 'peninsula_0.5deg'
  const zones = loaded?.zonas.length ?? 0

  // semana elegida = semana del timeline; si el modelo no la tiene, la más cercana disponible
  const wanted = mondayOf(date)
  const idx = useMemo(() => {
    if (!rows.length) return -1
    const exact = rows.findIndex(r => r.semana === wanted)
    if (exact >= 0) return exact
    const before = rows.map(r => r.semana <= wanted).lastIndexOf(true)
    return before >= 0 ? before : 0
  }, [rows, wanted])
  const sel: SeriesRow | undefined = rows[idx]
  const following: SeriesRow | undefined = rows[idx + 1]
  const previous: SeriesRow | undefined = rows[idx - 1]
  const side = following ?? previous
  const nearest = sel && sel.semana !== wanted ? (sel.semana > wanted ? 'primera semana con pronóstico' : 'última semana con pronóstico') : null

  const from = Math.max(0, idx - WEEKS_BEFORE)
  const chartRows = useMemo(() => rows.slice(from, idx + WEEKS_AFTER + 1), [rows, from, idx])
  const chartHi = idx - from

  const trust: Trust | null = useMemo(() => {
    if (!loaded) return null
    if (isLive && valPen) {
      return valPen.auc26 !== undefined
        ? { auc: valPen.auc26, base: valPen.base26 ?? 0.5, scope: 'temporada 2026 en vivo, datos que el modelo nunca vio' }
        : { auc: valPen.auc, base: valPen.base, scope: 'validado 2015–2025' }
    }
    const cs = countries.filter(c => loaded.paises.includes(c.nombre) && c.auc !== null)
    if (!cs.length) return null
    const w = cs.reduce((a, c) => a + c.zonas, 0)
    const avg = (f: (c: CountryInfo) => number) => cs.reduce((a, c) => a + f(c) * c.zonas, 0) / w
    return { auc: avg(c => c.auc ?? 0), base: avg(c => c.auc_base ?? 0.5), scope: 'repetición fuera de muestra 2023–2025' }
  }, [loaded, isLive, valPen, countries])

  const yearPeak = useMemo(() => {
    if (!sel) return null
    const y = sel.semana.slice(0, 4)
    return rows.filter(r => r.semana.startsWith(y) && r.esperadas !== null)
      .reduce<SeriesRow | null>((m, r) => (m === null || (r.esperadas ?? 0) > (m.esperadas ?? 0) ? r : m), null)
  }, [rows, sel])

  if (!region) return null

  const peak = sel?.prob_max ?? null
  const alert = alertOf(peak)
  const expected = sel?.esperadas ?? null
  const observed = sel?.anomalias ?? null
  const ratio = sel && sel.valor !== null && sel.p50 ? sel.valor / sel.p50 : null
  const where = loaded?.paises.join(' · ') ?? ''
  const scale = isLive
    ? 'Zonas de ~55 km · NASA FIRMS (VIIRS NOAA-20) + clima NASA POWER · en vivo'
    : 'Zonas de ~110 km · NASA FIRMS VIIRS armonizado + clima NASA POWER'

  return (
    <section className={`fd-panel${embedded ? ' is-embedded' : ''}`} aria-label="Pronóstico de anomalías de puntos de calor">
      <header className="fd-head">
        <div>
          <span className="fd-eyebrow">Inteligencia de alerta temprana</span>
          <h2>Pronóstico de anomalías</h2>
          <p>{loaded === undefined ? 'Analizando la región…' : zones ? `${where} — ${zones} zonas bajo vigilancia` : 'Fuera del área monitoreada'}</p>
        </div>
        <div className="fd-head-right">
          {loaded && zones > 0 && <span className={`fd-badge ${isLive ? 'is-live' : ''}`}>{isLive ? '● EN VIVO' : 'REPLAY 2023–25'}</span>}
          {onClose && <button type="button" aria-label="Cerrar pronóstico" onClick={onClose}>×</button>}
        </div>
      </header>

      {loaded === null && <p className="fd-note">El motor de pronóstico no responde (levanta el backend en el puerto 5000).</p>}
      {loaded && zones === 0 && <p className="fd-note">Cobertura: Península de Yucatán (en vivo, 0.5°) y México, Brasil, Rusia, Australia, Angola y RD del Congo (1°). Selecciona una región ahí.</p>}

      {loaded && zones > 0 && sel && <>
        <div className="fd-hero" style={{ ['--alert' as string]: alert?.color ?? '#888' }}>
          <Gauge value={peak} color={alert?.color ?? '#888'} />
          <div className="fd-hero-stats">
            <span className={`fd-alert ${alert && alert.min >= 0.3 ? 'pulse' : ''}`}>{alert?.key ?? '—'}</span>
            <BigStat value={expected} fmt={round1} unit="" label="zonas que romperían su récord estacional" />
            <BigStat value={observed} fmt={v => Math.round(v).toString()} unit="" label={observed === null ? 'aún sin observar' : 'zonas que realmente lo hicieron'} muted={observed === null} />
            <BigStat value={ratio} fmt={v => v.toFixed(1)} unit="×" label="actividad vs. una semana típica" />
          </div>
        </div>

        <p className="fd-headline">
          Para la semana del <b>{fmtWeek(sel.semana)}</b>{nearest ? ` (${nearest})` : ''}, el modelo detecta <b style={{ color: alert?.color }}>{alert?.phrase}</b> en {zones} zonas monitoreadas
          {expected !== null && <> — se espera que unas <b>{round1(expected)}</b> {expected >= 1.5 ? 'zonas superen' : 'zona supere'} su máximo histórico para esas fechas</>}.
          {observed !== null && <> Contraste con la realidad: <b>{observed}</b> lo hicieron.</>}
        </p>

        <div className="fd-outlook">
          {isLive && live ? <>
            <Mini title="Esta semana" sub={fmtWeek(live.semana_en_curso.semana)} p={live.semana_en_curso.resumen.prob_max} extra={`${live.semana_en_curso.resumen.zonas_alto} zonas de riesgo alto`} />
            <Mini title="Próxima semana" sub={fmtWeek(live.semana_proxima.semana)} p={live.semana_proxima.resumen.prob_max} extra={`${live.semana_proxima.resumen.zonas_alto} zonas de riesgo alto`} />
          </> : (
            <Mini title={following ? 'Semana siguiente' : 'Semana anterior'} sub={fmtWeek(side?.semana)} p={side?.prob_max ?? null} extra={side?.esperadas != null ? `≈${round1(side.esperadas)} zonas esperadas` : '—'} />
          )}
          <Mini title={`Pico de ${sel.semana.slice(0, 4)}`} sub={fmtWeek(yearPeak?.semana)} p={yearPeak?.prob_max ?? null} extra={yearPeak?.esperadas != null ? `≈${round1(yearPeak.esperadas)} zonas esperadas` : '—'} />
        </div>

        <h3 className="fd-h3">Actividad de fuego vs. rango normal</h3>
        <ActivityChart rows={chartRows} hi={chartHi} />
        <div className="fd-legend">
          <span><i className="fd-k-bar" />días-fuego detectados por satélite</span>
          <span><i className="fd-k-band" />rango normal (típico → máximo estacional)</span>
        </div>

        <h3 className="fd-h3">Pronóstico vs. realidad</h3>
        <ForecastChart rows={chartRows} hi={chartHi} />
        <div className="fd-legend">
          <span><i className="fd-k-exp" />zonas pronosticadas como anómalas</span>
          <span><i className="fd-k-obs" />zonas que fueron anómalas</span>
        </div>
      </>}

      {trust && loaded && zones > 0 && (
        <div className="fd-trust">
          <div className="fd-trust-num">{(trust.auc * 10).toFixed(1)}<small>/10</small></div>
          <p>
            <b>Precisión comprobada.</b> En {(trust.auc * 10).toFixed(1)} de cada 10 comparaciones, el modelo coloca una zona que se volvió anómala por encima de una que no —
            vs {(trust.base * 10).toFixed(1)}/10 usando promedios históricos ({trust.scope}).
          </p>
        </div>
      )}
      <p className="fd-note">
        Anomalía = una zona con más días-fuego que su percentil 90 histórico para esa época del año. Un punto de calor no es un incendio. {scale}.
      </p>
    </section>
  )
}

function Gauge({ value, color }: { value: number | null; color: string }) {
  const v = useCountUp(value)
  const r = 52, c = 2 * Math.PI * r, arc = 0.75
  const fill = v === null ? 0 : Math.min(1, v) * arc * c
  return (
    <div className="fd-gauge">
      <svg viewBox="0 0 140 140" aria-hidden>
        <defs>
          <linearGradient id="fd-g" x1="0" x2="1" y1="1" y2="0">
            <stop offset="0" stopColor="#3ccf8e" /><stop offset=".45" stopColor="#f5c542" /><stop offset=".75" stopColor="#ff8a3d" /><stop offset="1" stopColor="#ff4d4f" />
          </linearGradient>
        </defs>
        <circle cx="70" cy="70" r={r} className="fd-gauge-track" strokeDasharray={`${arc * c} ${c}`} transform="rotate(135 70 70)" />
        <circle cx="70" cy="70" r={r} stroke="url(#fd-g)" className="fd-gauge-fill" strokeDasharray={`${fill} ${c}`} transform="rotate(135 70 70)" style={{ filter: `drop-shadow(0 0 6px ${color})` }} />
      </svg>
      <div className="fd-gauge-text">
        <span className="fd-gauge-num" style={{ color }}>{v === null ? '—' : Math.round(v * 100)}<small>%</small></span>
        <span className="fd-gauge-label">riesgo pico</span>
      </div>
    </div>
  )
}

function BigStat({ value, fmt, unit, label, muted }: { value: number | null; fmt: (v: number) => string; unit: string; label: string; muted?: boolean }) {
  const v = useCountUp(value)
  return (
    <div className={`fd-stat ${muted ? 'is-muted' : ''}`}>
      <span className="fd-stat-num">{v === null ? '—' : fmt(v)}{v !== null && unit}</span>
      <span className="fd-stat-label">{label}</span>
    </div>
  )
}

function Mini({ title, sub, p, extra }: { title: string; sub: string; p: number | null; extra: string }) {
  const a = alertOf(p)
  return (
    <div className="fd-mini" style={{ borderColor: a?.color ?? '#333' }}>
      <span className="fd-mini-title">{title}</span>
      <span className="fd-mini-num" style={{ color: a?.color }}>{p === null ? '—' : `${Math.round(p * 100)}%`}</span>
      <span className="fd-mini-sub">{a?.key ?? ''} · {sub}</span>
      <span className="fd-mini-sub">{extra}</span>
    </div>
  )
}

const W = 460, H = 130, PAD = { l: 8, r: 8, t: 8, b: 18 }

function useScale(rows: SeriesRow[], f: (r: SeriesRow) => number) {
  return useMemo(() => {
    const n = rows.length
    const max = Math.max(1, ...rows.map(f))
    const iw = W - PAD.l - PAD.r, ih = H - PAD.t - PAD.b
    const x = (i: number) => PAD.l + (n <= 1 ? 0 : (i / (n - 1)) * iw)
    const y = (v: number) => PAD.t + ih - (Math.min(v, max) / max) * ih
    const bw = Math.max(1, iw / Math.max(n, 1) - 0.6)
    const years = rows.map((r, i) => ({ i, y: r.semana.slice(0, 4), first: i === 0 || r.semana.slice(0, 4) !== rows[i - 1].semana.slice(0, 4) })).filter(t => t.first)
    return { x, y, bw, max, ih, years }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rows])
}

function Axis({ s, hi }: { s: ReturnType<typeof useScale>; hi: number }) {
  return <>
    {s.years.map(t => <text key={t.y} x={s.x(t.i) + 2} y={H - 5} className="fd-axis">{t.y}</text>)}
    {hi >= 0 && <line x1={s.x(hi)} x2={s.x(hi)} y1={PAD.t} y2={PAD.t + s.ih} className="fd-cursor" />}
  </>
}

function ActivityChart({ rows, hi }: { rows: SeriesRow[]; hi: number }) {
  const s = useScale(rows, r => Math.max(r.valor ?? 0, r.p90 ?? 0))
  const band = rows.map((r, i) => (r.p90 === null ? null : `${s.x(i).toFixed(1)},${s.y(r.p90).toFixed(1)}`)).filter(Boolean)
  const low = rows.map((r, i) => (r.p50 === null ? null : `${s.x(i).toFixed(1)},${s.y(r.p50).toFixed(1)}`)).filter(Boolean).reverse()
  return (
    <svg className="fd-chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Actividad semanal de fuego frente a su rango normal">
      <defs>
        <linearGradient id="fd-bar" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#ffb347" /><stop offset="1" stopColor="#ff5e3a" stopOpacity=".55" /></linearGradient>
      </defs>
      <polygon points={[...band, ...low].join(' ')} className="fd-band" />
      {rows.map((r, i) => {
        const over = r.valor !== null && r.p90 !== null && r.valor > r.p90
        return (
          <rect key={r.semana} x={s.x(i) - s.bw / 2} width={s.bw} y={s.y(r.valor ?? 0)} height={Math.max(0, s.y(0) - s.y(r.valor ?? 0))}
            fill="url(#fd-bar)" opacity={i === hi ? 1 : over ? 0.95 : 0.6}>
            <title>{`${fmtWeek(r.semana)}: ${r.valor ?? '—'} días-fuego · típico ${r.p50 ?? '—'} · máximo estacional ${r.p90 ?? '—'}`}</title>
          </rect>
        )
      })}
      <Axis s={s} hi={hi} />
    </svg>
  )
}

function ForecastChart({ rows, hi }: { rows: SeriesRow[]; hi: number }) {
  const s = useScale(rows, r => Math.max(r.esperadas ?? 0, r.anomalias ?? 0))
  const pts = rows.map((r, i) => (r.esperadas === null ? null : `${s.x(i).toFixed(1)},${s.y(r.esperadas).toFixed(1)}`)).filter(Boolean) as string[]
  const area = pts.length ? `${s.x(0).toFixed(1)},${s.y(0)} ${pts.join(' ')} ${s.x(rows.length - 1).toFixed(1)},${s.y(0)}` : ''
  return (
    <svg className="fd-chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Zonas anómalas pronosticadas frente a observadas">
      <defs>
        <linearGradient id="fd-exp" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#8b7bff" stopOpacity=".75" /><stop offset="1" stopColor="#8b7bff" stopOpacity=".05" /></linearGradient>
      </defs>
      <polygon points={area} fill="url(#fd-exp)" />
      <polyline points={pts.join(' ')} className="fd-exp-line" />
      {rows.map((r, i) => (r.anomalias ?? 0) > 0
        ? <circle key={r.semana} cx={s.x(i)} cy={s.y(r.anomalias ?? 0)} r={2.3} className="fd-obs-dot">
            <title>{`${fmtWeek(r.semana)}: pronóstico ≈${r.esperadas ?? '—'} · observado ${r.anomalias}`}</title>
          </circle>
        : null)}
      <Axis s={s} hi={hi} />
    </svg>
  )
}
