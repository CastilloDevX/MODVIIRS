import { useEffect, useMemo, useState, type ReactNode } from 'react'
import type { CalendarRow, MedianRow } from '../../lib/types'
import { FRP_BINS, downsample } from './stats'

const W = 320
const nf = (v: number) => (v >= 1000 ? v.toLocaleString('en', { maximumFractionDigits: 0 }) : v.toLocaleString('en', { maximumFractionDigits: 1 }))

/** Number that counts up from 0 whenever its value changes. */
export function CountUp({ value, decimals = 0, suffix = '' }: { value: number; decimals?: number; suffix?: string }) {
  const [shown, setShown] = useState(0)
  useEffect(() => {
    const duration = matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 1100
    let frame = 0
    const t0 = performance.now()
    const tick = (now: number) => {
      const k = duration === 0 ? 1 : Math.min(1, (now - t0) / duration)
      setShown(value * (1 - Math.pow(2, -10 * k)))
      if (k < 1) frame = requestAnimationFrame(tick)
      else setShown(value)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [value])
  const compact = Math.abs(value) >= 1e6
  return <>{compact ? (shown / 1e6).toLocaleString('en', { maximumFractionDigits: 2 }) + ' M' : shown.toLocaleString('en', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}{suffix}</>
}

type AreaProps = { values: number[]; labels: [string, string]; dateAt: (i: number) => string; color: string; unit: string; highlight?: [number, number] }

/** Daily series as a filled polygon with the peak marked; hovering reads any day. */
export function AreaChart({ values, labels, dateAt, color, unit, highlight }: AreaProps) {
  const [hover, setHover] = useState<number | null>(null)
  const H = 110, padL = 34, padB = 16, padT = 8
  const cols = useMemo(() => downsample(values, 300), [values])
  const max = Math.max(1, ...cols)
  const x = (i: number) => padL + (cols.length <= 1 ? 0 : (i / (cols.length - 1)) * (W - padL - 4))
  const y = (v: number) => padT + (1 - v / max) * (H - padT - padB)
  const line = cols.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ')
  const peakIdx = cols.reduce((b, v, i) => (v > cols[b] ? i : b), 0)
  const toDay = (c: number) => Math.round((c / Math.max(1, cols.length - 1)) * (values.length - 1))
  const h = hover === null ? null : Math.min(cols.length - 1, hover)
  return (
    <div className="chart">
      <div className="chart-readout">{h === null ? `Peak: ${nf(values[toDay(peakIdx)] ?? 0)} ${unit} · ${dateAt(toDay(peakIdx))}` : `${dateAt(toDay(h))} · ${nf(values[toDay(h)] ?? 0)} ${unit}`}</div>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Daily series"
        onPointerMove={e => { const r = e.currentTarget.getBoundingClientRect(); const px = ((e.clientX - r.left) / r.width) * W; setHover(Math.max(0, Math.round(((px - padL) / (W - padL - 4)) * (cols.length - 1)))) }}
        onPointerLeave={() => setHover(null)}>
        <defs><linearGradient id={`g-${color.slice(1)}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor={color} stopOpacity=".7" /><stop offset="1" stopColor={color} stopOpacity=".05" /></linearGradient></defs>
        {[0, 0.5, 1].map(t => <g key={t}><line x1={padL} x2={W - 4} y1={y(max * t)} y2={y(max * t)} className="grid" /><text x={padL - 4} y={y(max * t) + 3} className="axis" textAnchor="end">{nf(max * t)}</text></g>)}
        {highlight && <rect className="step-band" x={x(highlight[0] / Math.max(1, values.length - 1) * (cols.length - 1))} width={Math.max(2, x(highlight[1] / Math.max(1, values.length - 1) * (cols.length - 1)) - x(highlight[0] / Math.max(1, values.length - 1) * (cols.length - 1)))} y={padT} height={H - padT - padB} />}
        <path className="area-fill" d={`${line} L${x(cols.length - 1)},${y(0)} L${x(0)},${y(0)} Z`} fill={`url(#g-${color.slice(1)})`} />
        <path className="draw" pathLength={1} d={line} fill="none" stroke={color} strokeWidth="1.6" />
        <circle cx={x(peakIdx)} cy={y(cols[peakIdx])} r="3.5" fill="#fff" stroke={color} strokeWidth="2" className="pop" />
        {h !== null && <g><line x1={x(h)} x2={x(h)} y1={padT} y2={H - padB} className="cursor" /><circle cx={x(h)} cy={y(cols[h])} r="3" fill={color} /></g>}
        <text x={padL} y={H - 3} className="axis">{labels[0]}</text><text x={W - 4} y={H - 3} className="axis" textAnchor="end">{labels[1]}</text>
      </svg>
    </div>
  )
}

const lerp = (a: number, b: number, t: number) => Math.round(a + (b - a) * t)
/** Diverging ramp for z-scores: blue (below normal) – neutral – red (above normal). */
function zColor(z: number) {
  const t = Math.max(-3, Math.min(3, z)) / 3
  const neutral = [58, 58, 62], blue = [59, 130, 246], red = [239, 68, 68]
  const to = t < 0 ? blue : red
  const k = Math.abs(t)
  return `rgb(${lerp(neutral[0], to[0], k)},${lerp(neutral[1], to[1], k)},${lerp(neutral[2], to[2], k)})`
}

const MONTHS = ['E', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']

/** Year × month grid coloured by the anomaly z-score of active-fire days against the same-month baseline. */
export function Heatmap({ rows }: { rows: CalendarRow[] }) {
  const years = [...new Set(rows.map(r => r.year))].sort((a, b) => a - b)
  const byKey = new Map(rows.map(r => [`${r.year}-${r.month}`, r]))
  const padL = 30, cw = (W - padL) / 12, ch = 14
  return (
    <svg viewBox={`0 0 ${W} ${years.length * ch + 16}`} role="img" aria-label="Monthly anomaly calendar">
      {MONTHS.map((m, i) => <text key={i} x={padL + i * cw + cw / 2} y={9} className="axis" textAnchor="middle">{m}</text>)}
      {years.map((yr, yi) => (
        <g key={yr}>
          <text x={padL - 4} y={16 + yi * ch + 10} className="axis" textAnchor="end">{yr}</text>
          {Array.from({ length: 12 }, (_, mi) => {
            const r = byKey.get(`${yr}-${mi + 1}`)
            if (!r) return null
            const fill = !r.valid || r.z === null ? '#2a2a2a' : zColor(r.z)
            return (
              <rect key={mi} className="heat-cell" style={{ animationDelay: `${(yi * 12 + mi) * 6}ms` }} x={padL + mi * cw + 1} y={16 + yi * ch} width={cw - 2} height={ch - 2} rx="2" fill={fill}>
                <title>{`${yr}-${String(mi + 1).padStart(2, '0')} · AFD ${nf(r.afd)}${r.valid ? ` · z ${r.z?.toFixed(2) ?? '—'} · percentile ${r.pctl === null ? '—' : (r.pctl * 100).toFixed(0)}` : ' · month without sensor data'}`}</title>
              </rect>
            )
          })}
        </g>
      ))}
    </svg>
  )
}

/** Typical year: min–max band, interquartile band, median line and mean per calendar month. */
export function BandChart({ rows }: { rows: MedianRow[] }) {
  const H = 120, padL = 34, padB = 16, padT = 8
  const max = Math.max(1, ...rows.map(r => r.max))
  const x = (m: number) => padL + ((m - 0.5) / 12) * (W - padL - 4)
  const y = (v: number) => padT + (1 - v / max) * (H - padT - padB)
  const sorted = [...rows].sort((a, b) => a.month - b.month)
  const band = (lo: (r: MedianRow) => number, hi: (r: MedianRow) => number) =>
    `${sorted.map((r, i) => `${i ? 'L' : 'M'}${x(r.month)},${y(hi(r))}`).join(' ')} ${[...sorted].reverse().map(r => `L${x(r.month)},${y(lo(r))}`).join(' ')} Z`
  return (
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Typical seasonality">
      {[0, 0.5, 1].map(t => <g key={t}><line x1={padL} x2={W - 4} y1={y(max * t)} y2={y(max * t)} className="grid" /><text x={padL - 4} y={y(max * t) + 3} className="axis" textAnchor="end">{nf(max * t)}</text></g>)}
      <path className="area-fill" d={band(r => r.min, r => r.max)} fill="#ff8f00" opacity=".18" />
      <path className="area-fill" d={band(r => r.p25, r => r.p75)} fill="#ff8f00" opacity=".45" />
      <path className="draw" pathLength={1} d={sorted.map((r, i) => `${i ? 'L' : 'M'}${x(r.month)},${y(r.median)}`).join(' ')} fill="none" stroke="#fff" strokeWidth="1.8" />
      {sorted.map(r => <circle key={r.month} cx={x(r.month)} cy={y(r.mean)} r="2.4" fill="#ffd600" className="pop"><title>{`Month ${r.month} · median ${nf(r.median)} · mean ${nf(r.mean)} ± ${nf(r.std)} · P25–P75 ${nf(r.p25)}–${nf(r.p75)} · range ${nf(r.min)}–${nf(r.max)} · ${r.n_years} years${r.baseline_corto ? ' (short baseline)' : ''}`}</title></circle>)}
      {MONTHS.map((m, i) => <text key={i} x={x(i + 1)} y={H - 3} className="axis" textAnchor="middle">{m}</text>)}
    </svg>
  )
}

/** Log-spaced FRP histogram (MW). */
export function Histogram({ counts }: { counts: number[] }) {
  const H = 100, padB = 16, padT = 6
  const max = Math.max(1, ...counts)
  const bw = W / counts.length
  return (
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="FRP distribution">
      {counts.map((c, i) => {
        const h = (c / max) * (H - padB - padT)
        const t = i / (counts.length - 1)
        return (
          <g key={i}>
            <rect className="bar-up" style={{ animationDelay: `${i * 50}ms` }} x={i * bw + 3} width={bw - 6} y={H - padB - h} height={h} rx="2" fill={t < 0.4 ? '#ffd600' : t < 0.7 ? '#ff8f00' : '#e53935'}><title>{`${FRP_BINS[i]}${i < counts.length - 1 ? `–${FRP_BINS[i + 1]}` : '+'} MW · ${nf(c)}`}</title></rect>
            <text x={i * bw + bw / 2} y={H - 4} className="axis" textAnchor="middle">{FRP_BINS[i]}{i === counts.length - 1 ? '+' : ''}</text>
          </g>
        )
      })}
    </svg>
  )
}

export function Donut({ parts }: { parts: { label: string; value: number; color: string }[] }) {
  const total = parts.reduce((a, p) => a + p.value, 0)
  const r = 34, c = 2 * Math.PI * r
  const lens = parts.map(p => (total ? (p.value / total) * c : 0))
  const offsets = lens.map((_, i) => lens.slice(0, i).reduce((a, b) => a + b, 0))
  return (
    <div className="donut">
      <svg viewBox="0 0 100 100" role="img" aria-label={parts.map(p => `${p.label} ${p.value}`).join(', ')}>
        <circle cx="50" cy="50" r={r} fill="none" stroke="#2a2a2a" strokeWidth="14" />
        {total > 0 && parts.map((p, i) => <circle key={p.label} className="donut-seg" cx="50" cy="50" r={r} fill="none" stroke={p.color} strokeWidth="14" strokeDasharray={`${lens[i]} ${c - lens[i]}`} strokeDashoffset={-offsets[i]} transform="rotate(-90 50 50)" />)}
      </svg>
      <ul>{parts.map(p => <li key={p.label}><span className="swatch" style={{ background: p.color }} />{p.label}<b>{total ? ((100 * p.value) / total).toFixed(0) : 0}%</b><i>{nf(p.value)}</i></li>)}</ul>
    </div>
  )
}

export function BarList({ items, color = '#ff8f00' }: { items: { label: string; value: number }[]; color?: string }) {
  const max = Math.max(1, ...items.map(i => i.value))
  return (
    <ul className="barlist">
      {items.map((it, i) => (
        <li key={it.label}>
          <span>{it.label}</span>
          <div><span className="bar-grow" style={{ width: `${(it.value / max) * 100}%`, background: color, animationDelay: `${i * 80}ms` }} /></div>
          <b>{nf(it.value)}</b>
        </li>
      ))}
    </ul>
  )
}

export function Card({ title, note, index, children }: { title: string; note?: string; index: number; children: ReactNode }) {
  return (
    <section className="card" style={{ ['--i' as string]: index }}>
      <h3>{title}</h3>
      {children}
      {note && <p className="card-note">{note}</p>}
    </section>
  )
}

export function Kpi({ label, value, unit, decimals = 0, text, color }: { label: string; value?: number | null; unit?: string; decimals?: number; text?: string; color?: string }) {
  return (
    <div className="kpi">
      <span className="kpi-label">{label}</span>
      <span className="kpi-value" style={color ? { color } : undefined}>
        {value === undefined || value === null ? (text ?? '—') : <CountUp value={value} decimals={decimals} />}{unit && <small>{unit}</small>}
      </span>
    </div>
  )
}
