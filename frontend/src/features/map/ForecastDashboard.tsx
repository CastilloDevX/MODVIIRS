import { useEffect, useMemo, useState } from 'react'
import { Card, Kpi } from './charts'
import type { Bbox } from './region'
import {
  getCurrentForecast, getForecastSeries, getForecastValidation, getGlobalCountries, mondayOf,
  type CountryInfo, type CurrentForecast, type ForecastSeries, type SeriesRow,
} from './predictions'
import './forecast.css'

/**
 * Pronóstico de actividad ANÓMALA de puntos de calor para la región seleccionada (rama `predictivo`),
 * con las mismas tarjetas, KPIs y gráficos que la vista HISTÓRICO.
 *
 * Datos (backend Flask, docs/API_PREDICCIONES.md):
 *   GET /api/predictions/series      serie semanal; el backend elige el modelo: Península de Yucatán
 *                                    (0.5°, clima NASA POWER, en vivo 2026) o 6 países (1°, 2023–2025)
 *   GET /api/predictions             semana en curso y próxima (solo península, en vivo)
 *   GET /api/predictions/validation  y /api/predictions/global/countries  → precisión comprobada
 */
type Props = { region: Bbox | null; date: Date }
type Validation = { auc: number; base: number; ap: number; apBase: number; auc2: number; ap2: number; auc26?: number; base26?: number; calibration: { prob: number; observed: number; n: number }[] }

const ALERTS = [
  { min: 0.5, key: 'CRÍTICO', color: '#ff4d4f' },
  { min: 0.3, key: 'ELEVADO', color: '#ff8a3d' },
  { min: 0.1, key: 'VIGILANCIA', color: '#f5c542' },
  { min: 0, key: 'NORMAL', color: '#3ccf8e' },
]
const alertOf = (p: number | null | undefined) => (p == null ? null : ALERTS.find(a => p >= a.min) ?? ALERTS[3])

/**
 * How far ahead the model stays useful. Walk-forward validation 2015–2025 (era VIIRS), prediccion/README.md.
 * The live service publishes 1 and 2 weeks ahead; 4 weeks is validated offline only.
 */
const HORIZONS = [
  { weeks: 1, auc: 0.847, ap: 0.272, verdict: 'Confiable', color: '#3ccf8e' },
  { weeks: 2, auc: 0.81, ap: 0.191, verdict: 'Confiable', color: '#3ccf8e' },
  { weeks: 4, auc: 0.776, ap: 0.143, verdict: 'Orientativo', color: '#f5c542' },
]
const BASE = { auc: 0.582, ap: 0.071 }

const fmtWeek = (iso?: string) =>
  iso ? new Date(`${iso}T12:00:00`).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' }) : '—'
const WEEKS_BEFORE = 104, WEEKS_AFTER = 26 // ventana de las gráficas alrededor de la semana elegida

export function ForecastDashboard({ region, date }: Props) {
  const [live, setLive] = useState<CurrentForecast | null>(null)
  const [series, setSeries] = useState<{ key: string; data: ForecastSeries | null } | null>(null)
  const [val, setVal] = useState<Validation | null>(null)
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
      const h1 = v.resumen_h1 as { auc: number; auc_base: number; ap: number; ap_base: number } | undefined
      const h2 = v.resumen_h2 as { auc: number; ap: number } | undefined
      const t = v.temporada_2026_vivo as { auc?: number; auc_base?: number } | undefined
      const cal = (v.calibracion as { prob_media: number; observado: number; n: number }[] | undefined) ?? []
      if (h1 && h2) setVal({ auc: h1.auc, base: h1.auc_base, ap: h1.ap, apBase: h1.ap_base, auc2: h2.auc, ap2: h2.ap, auc26: t?.auc, base26: t?.auc_base, calibration: cal.map(c => ({ prob: c.prob_media, observed: c.observado, n: c.n })) })
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
  const nearest = sel && sel.semana !== wanted ? (sel.semana > wanted ? 'primera semana con pronóstico' : 'última semana con pronóstico') : null

  const from = Math.max(0, idx - WEEKS_BEFORE)
  const chartRows = useMemo(() => rows.slice(from, idx + WEEKS_AFTER + 1), [rows, from, idx])
  const chartHi = idx - from

  const yearPeak = useMemo(() => {
    if (!sel) return null
    const y = sel.semana.slice(0, 4)
    return rows.filter(r => r.semana.startsWith(y) && r.esperadas !== null)
      .reduce<SeriesRow | null>((m, r) => (m === null || (r.esperadas ?? 0) > (m.esperadas ?? 0) ? r : m), null)
  }, [rows, sel])

  const auc = useMemo(() => {
    if (!loaded) return null
    if (isLive && val) return val.auc26 !== undefined ? { v: val.auc26, base: val.base26 ?? 0.5, scope: 'temporada 2026 en vivo' } : { v: val.auc, base: val.base, scope: 'validado 2015–2025' }
    const cs = countries.filter(c => loaded.paises.includes(c.nombre) && c.auc !== null)
    if (!cs.length) return null
    const w = cs.reduce((a, c) => a + c.zonas, 0)
    const avg = (f: (c: CountryInfo) => number) => cs.reduce((a, c) => a + f(c) * c.zonas, 0) / w
    return { v: avg(c => c.auc ?? 0), base: avg(c => c.auc_base ?? 0.5), scope: 'repetición 2023–2025' }
  }, [loaded, isLive, val, countries])

  if (!region) return null

  const peak = sel?.prob_max ?? null
  const alert = alertOf(peak)
  const ratio = sel && sel.valor !== null && sel.p50 ? sel.valor / sel.p50 : null
  let card = 1 // entrance stagger, after the tabs

  if (loaded === undefined) return <Card index={card++} title="Pronóstico"><div className="skeleton" aria-busy="true">Analizando la región…</div></Card>
  if (loaded === null) return <Card index={card++} title="Pronóstico"><p className="card-error">No disponible: el motor de pronóstico no responde (levanta el backend en el puerto 5000).</p></Card>
  if (zones === 0 || !sel) {
    return (
      <Card index={card++} title="Pronóstico" note="Cobertura: Península de Yucatán (en vivo, zonas de 0.5°) y México, Brasil, Rusia, Australia, Angola y RD del Congo (zonas de 1°, 2023–2025).">
        <p className="card-error">Esta región está fuera del área monitoreada. Selecciona una región dentro de la cobertura.</p>
      </Card>
    )
  }

  return (
    <>
      <p className="sensor-note">
        {isLive ? '● EN VIVO · zonas de ~55 km · NASA FIRMS (VIIRS NOAA-20) + clima NASA POWER' : 'REPLAY 2023–2025 · zonas de ~110 km · NASA FIRMS VIIRS armonizado + clima NASA POWER'} · {zones} zonas · {loaded.paises.join(' · ')}
      </p>

      <Card index={card++} title={`Pronóstico · semana del ${fmtWeek(sel.semana)}`}
        note={`${nearest ? `Es la ${nearest}. ` : ''}Anomalía = una zona con más días-fuego que su percentil 90 histórico para esa época. Un punto de calor no es un incendio.`}>
        <div className="kpis">
          <Kpi label="Riesgo pico" value={peak === null ? null : peak * 100} decimals={0} unit=" %" color={alert?.color} />
          <Kpi label="Nivel" text={alert?.key ?? '—'} color={alert?.color} />
          <Kpi label="Zonas vigiladas" value={zones} />
          <Kpi label="Zonas esperadas anómalas" value={sel.esperadas} decimals={1} />
          <Kpi label="Zonas que lo fueron" value={sel.anomalias} text="sin observar" />
          <Kpi label="Actividad vs típica" value={ratio} decimals={1} unit=" ×" />
        </div>
      </Card>

      <Card index={card++} title="Perspectiva" note="En vivo el servicio publica la semana en curso (1 semana de anticipación) y la próxima (2 semanas).">
        <div className="kpis">
          {isLive && live ? <>
            <Outlook title="Esta semana" week={live.semana_en_curso.semana} p={live.semana_en_curso.resumen.prob_max} high={live.semana_en_curso.resumen.zonas_alto} />
            <Outlook title="Próxima semana" week={live.semana_proxima.semana} p={live.semana_proxima.resumen.prob_max} high={live.semana_proxima.resumen.zonas_alto} />
          </> : <Outlook title={following ? 'Semana siguiente' : 'Semana anterior'} week={(following ?? rows[idx - 1])?.semana} p={(following ?? rows[idx - 1])?.prob_max ?? null} />}
          <Outlook title={`Pico de ${sel.semana.slice(0, 4)}`} week={yearPeak?.semana} p={yearPeak?.prob_max ?? null} />
        </div>
      </Card>

      <Card index={card++} title="Actividad de fuego vs. rango normal">
        <ActivityChart rows={chartRows} hi={chartHi} />
        <div className="fd-legend">
          <span><i className="fd-k-bar" />días-fuego detectados por satélite</span>
          <span><i className="fd-k-band" />rango normal (típico → máximo estacional)</span>
        </div>
      </Card>

      <Card index={card++} title="Pronóstico vs. realidad">
        <ForecastChart rows={chartRows} hi={chartHi} />
        <div className="fd-legend">
          <span><i className="fd-k-exp" />zonas pronosticadas como anómalas</span>
          <span><i className="fd-k-obs" />zonas que fueron anómalas</span>
        </div>
      </Card>

      <Card index={card++} title="¿Hasta cuándo es confiable?"
        note="AUC: probabilidad de que el modelo ponga una zona que sí fue anómala por encima de una que no (0.5 = azar). AP: precisión media frente a la de la línea base. El servicio en vivo publica hasta 2 semanas; 4 semanas se validó solo fuera de línea.">
        <div className="kpis">
          <Kpi label="Confiable hasta" text="2 semanas" color="#3ccf8e" />
          <Kpi label="AUC a 1 sem." value={HORIZONS[0].auc} decimals={2} />
          <Kpi label="AUC a 2 sem." value={HORIZONS[1].auc} decimals={2} />
          {auc && <Kpi label={`AUC ${auc.scope}`} value={auc.v} decimals={2} unit={` vs ${auc.base.toFixed(2)}`} />}
          <Kpi label="AP a 1 sem." value={HORIZONS[0].ap / BASE.ap} decimals={1} unit=" × base" />
          <Kpi label="AP a 4 sem." value={HORIZONS[2].ap / BASE.ap} decimals={1} unit=" × base" />
        </div>
        <HorizonChart />
        <div className="fd-legend">
          {HORIZONS.map(h => <span key={h.weeks}><i style={{ background: h.color }} />{h.weeks} sem.: {h.verdict}</span>)}
          <span><i className="fd-k-base" />línea base (promedios históricos)</span>
        </div>
      </Card>

      {val && val.calibration.length > 0 && (
        <Card index={card++} title="Calibración: lo que dice vs. lo que ocurre" note="Cada par de barras: probabilidad media pronosticada (naranja) frente a la frecuencia observada (blanca). Buena hasta ~40 %; por encima de 70 % el modelo es optimista (muestra pequeña): léelo como «riesgo alto».">
          <CalibrationChart bins={val.calibration} />
        </Card>
      )}

      <p className="panel-foot">Predice actividad anómala de puntos de calor, no la ubicación de incendios forestales. Solo usa el clima pasado (sin pronóstico meteorológico).</p>
    </>
  )
}

function Outlook({ title, week, p, high }: { title: string; week?: string; p: number | null; high?: number }) {
  const a = alertOf(p)
  return (
    <div className="kpi">
      <span className="kpi-label">{title}</span>
      <span className="kpi-value" style={{ color: a?.color }}>{p === null ? '—' : `${Math.round(p * 100)} %`}</span>
      <span className="kpi-label">{a?.key ?? ''} · {fmtWeek(week)}{high !== undefined ? ` · ${high} zonas altas` : ''}</span>
    </div>
  )
}

const W = 320, H = 120, PAD = { l: 8, r: 8, t: 8, b: 16 }

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
    {[0, 0.5, 1].map(t => <line key={t} x1={PAD.l} x2={W - PAD.r} y1={s.y(s.max * t)} y2={s.y(s.max * t)} className="grid" />)}
    {s.years.map(t => <text key={t.y} x={s.x(t.i) + 2} y={H - 3} className="axis">{t.y}</text>)}
    {hi >= 0 && <line x1={s.x(hi)} x2={s.x(hi)} y1={PAD.t} y2={PAD.t + s.ih} className="cursor" />}
  </>
}

function ActivityChart({ rows, hi }: { rows: SeriesRow[]; hi: number }) {
  const s = useScale(rows, r => Math.max(r.valor ?? 0, r.p90 ?? 0))
  const band = rows.map((r, i) => (r.p90 === null ? null : `${s.x(i).toFixed(1)},${s.y(r.p90).toFixed(1)}`)).filter(Boolean)
  const low = rows.map((r, i) => (r.p50 === null ? null : `${s.x(i).toFixed(1)},${s.y(r.p50).toFixed(1)}`)).filter(Boolean).reverse()
  return (
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Actividad semanal de fuego frente a su rango normal">
      <Axis s={s} hi={hi} />
      <polygon className="fd-band area-fill" points={[...band, ...low].join(' ')} />
      {rows.map((r, i) => {
        const over = r.valor !== null && r.p90 !== null && r.valor > r.p90
        return (
          <rect key={r.semana} className="bar-up" style={{ animationDelay: `${Math.min(i, 60) * 8}ms` }} x={s.x(i) - s.bw / 2} width={s.bw} y={s.y(r.valor ?? 0)} height={Math.max(0, s.y(0) - s.y(r.valor ?? 0))}
            fill={over ? '#ff8f00' : '#ffd600'} opacity={i === hi ? 1 : over ? 0.95 : 0.6}>
            <title>{`${fmtWeek(r.semana)}: ${r.valor ?? '—'} días-fuego · típico ${r.p50 ?? '—'} · máximo estacional ${r.p90 ?? '—'}`}</title>
          </rect>
        )
      })}
    </svg>
  )
}

function ForecastChart({ rows, hi }: { rows: SeriesRow[]; hi: number }) {
  const s = useScale(rows, r => Math.max(r.esperadas ?? 0, r.anomalias ?? 0))
  const pts = rows.map((r, i) => (r.esperadas === null ? null : `${s.x(i).toFixed(1)},${s.y(r.esperadas).toFixed(1)}`)).filter(Boolean) as string[]
  const area = pts.length ? `${s.x(0).toFixed(1)},${s.y(0)} ${pts.join(' ')} ${s.x(rows.length - 1).toFixed(1)},${s.y(0)}` : ''
  return (
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Zonas anómalas pronosticadas frente a observadas">
      <defs>
        <linearGradient id="fd-exp" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#ff8f00" stopOpacity=".7" /><stop offset="1" stopColor="#ff8f00" stopOpacity=".05" /></linearGradient>
      </defs>
      <Axis s={s} hi={hi} />
      <polygon className="area-fill" points={area} fill="url(#fd-exp)" />
      <polyline className="draw" pathLength={1} points={pts.join(' ')} fill="none" stroke="#ffd54f" strokeWidth="1.6" />
      {rows.map((r, i) => (r.anomalias ?? 0) > 0
        ? <circle key={r.semana} className="pop" cx={s.x(i)} cy={s.y(r.anomalias ?? 0)} r={2.4} fill="#e53935" stroke="#fff" strokeWidth=".6">
            <title>{`${fmtWeek(r.semana)}: pronóstico ≈${r.esperadas ?? '—'} · observado ${r.anomalias}`}</title>
          </circle>
        : null)}
    </svg>
  )
}

/** AUC by forecast horizon with the baseline as a reference line. */
function HorizonChart() {
  const h = 96, padL = 24, padB = 16, padT = 8
  const bw = (W - padL - 8) / HORIZONS.length
  const y = (v: number) => padT + (1 - (v - 0.5) / 0.5) * (h - padT - padB)
  return (
    <svg viewBox={`0 0 ${W} ${h}`} role="img" aria-label="AUC por horizonte de pronóstico">
      {[0.5, 0.75, 1].map(t => <g key={t}><line x1={padL} x2={W - 8} y1={y(t)} y2={y(t)} className="grid" /><text x={padL - 4} y={y(t) + 3} className="axis" textAnchor="end">{t.toFixed(2)}</text></g>)}
      {HORIZONS.map((hz, i) => (
        <g key={hz.weeks}>
          <rect className="bar-up" style={{ animationDelay: `${i * 90}ms` }} x={padL + i * bw + bw * 0.2} width={bw * 0.6} y={y(hz.auc)} height={y(0.5) - y(hz.auc)} rx="3" fill={hz.color}>
            <title>{`${hz.weeks} semana(s): AUC ${hz.auc.toFixed(2)} · AP ${hz.ap.toFixed(2)} (base ${BASE.ap.toFixed(2)})`}</title>
          </rect>
          <text x={padL + i * bw + bw / 2} y={y(hz.auc) - 3} className="axis" textAnchor="middle" fill="#fff">{hz.auc.toFixed(2)}</text>
          <text x={padL + i * bw + bw / 2} y={h - 3} className="axis" textAnchor="middle">{hz.weeks} sem.</text>
        </g>
      ))}
      <line x1={padL} x2={W - 8} y1={y(BASE.auc)} y2={y(BASE.auc)} stroke="#9a9a9a" strokeWidth="1.2" strokeDasharray="4 3" />
    </svg>
  )
}

function CalibrationChart({ bins }: { bins: { prob: number; observed: number; n: number }[] }) {
  const h = 110, padL = 26, padB = 16, padT = 8
  const max = Math.max(0.1, ...bins.map(b => Math.max(b.prob, b.observed)))
  const bw = (W - padL - 6) / bins.length
  const y = (v: number) => padT + (1 - v / max) * (h - padT - padB)
  return (
    <svg viewBox={`0 0 ${W} ${h}`} role="img" aria-label="Probabilidad pronosticada frente a observada">
      {[0, 0.5, 1].map(t => <g key={t}><line x1={padL} x2={W - 6} y1={y(max * t)} y2={y(max * t)} className="grid" /><text x={padL - 4} y={y(max * t) + 3} className="axis" textAnchor="end">{Math.round(max * t * 100)}%</text></g>)}
      {bins.map((b, i) => (
        <g key={i}>
          <rect className="bar-up" style={{ animationDelay: `${i * 60}ms` }} x={padL + i * bw + bw * 0.1} width={bw * 0.38} y={y(b.prob)} height={y(0) - y(b.prob)} rx="2" fill="#ff8f00"><title>{`pronosticado ${(b.prob * 100).toFixed(1)} % · n = ${b.n.toLocaleString('en')}`}</title></rect>
          <rect className="bar-up" style={{ animationDelay: `${i * 60 + 30}ms` }} x={padL + i * bw + bw * 0.5} width={bw * 0.38} y={y(b.observed)} height={y(0) - y(b.observed)} rx="2" fill="#fff"><title>{`observado ${(b.observed * 100).toFixed(1)} %`}</title></rect>
          <text x={padL + i * bw + bw / 2} y={h - 3} className="axis" textAnchor="middle">{Math.round(b.prob * 100)}%</text>
        </g>
      ))}
    </svg>
  )
}
