import { useRef, useState } from 'react'
import { addDays, diffDays, formatLong, formatShort, snapToStops } from './dates'
import { downsample } from './stats'

type Props = {
  start: Date
  end: Date
  offset: number
  stops: number[]
  /** Hotspots per day over the whole range (one value per day) for the hover chart. */
  series?: number[] | null
  onOffsetChange: (offset: number) => void
}

const MAX_TICKS = 400

export function Timeline({ start, end, offset, stops, series, onOffsetChange }: Props) {
  const trackRef = useRef<HTMLDivElement>(null)
  const dragging = useRef(false)
  const [grabbing, setGrabbing] = useState(false)
  const [hover, setHover] = useState<number | null>(null)
  const days = diffDays(start, end)
  const pct = (i: number) => (days === 0 ? 0 : (i / days) * 100)
  const stopSet = new Set(stops)
  const labelEvery = Math.max(1, Math.ceil(stops.length / 10))
  const current = addDays(start, offset)

  const dayAt = (clientX: number) => {
    const rect = trackRef.current!.getBoundingClientRect()
    return Math.round(Math.min(Math.max((clientX - rect.left) / rect.width, 0), 1) * days)
  }
  const cols = series && series.length === days + 1 ? downsample(series, 1000) : null
  const max = cols ? Math.max(1, ...cols) : 1
  const peak = series && series.length ? series.reduce((b, v, i) => (v > series[b] ? i : b), 0) : 0
  const cx = (i: number) => (cols && cols.length > 1 ? (i / (cols.length - 1)) * 1000 : 0)
  const cy = (v: number) => 100 - (v / max) * 92
  const path = cols ? cols.map((v, i) => `${i ? 'L' : 'M'}${cx(i).toFixed(1)},${cy(v).toFixed(1)}`).join(' ') : ''

  const fromPointer = (clientX: number) => {
    const rect = trackRef.current!.getBoundingClientRect()
    const frac = Math.min(Math.max((clientX - rect.left) / rect.width, 0), 1)
    onOffsetChange(snapToStops(frac * days, stops, days))
  }

  const onKeyDown = (e: React.KeyboardEvent) => {
    const all = [...new Set([...stops, days])]
    const at = all.indexOf(offset)
    const moves: Record<string, number> = { ArrowRight: all[Math.min(at + 1, all.length - 1)], ArrowUp: all[Math.min(at + 1, all.length - 1)], ArrowLeft: all[Math.max(at - 1, 0)], ArrowDown: all[Math.max(at - 1, 0)], Home: 0, End: days }
    if (!(e.key in moves)) return
    e.preventDefault()
    onOffsetChange(moves[e.key])
  }

  // Every day gets a tick; with very long ranges only the step starts are drawn.
  const ticks: number[] = days + 1 <= MAX_TICKS ? Array.from({ length: days + 1 }, (_, i) => i) : stops.filter((_, k) => k % Math.ceil(stops.length / MAX_TICKS) === 0)
  const label = (i: number) => {
    const d = addDays(start, i)
    if (days <= 31) return String(d.getDate())
    return `${d.getDate()}/${d.getMonth() + 1}${days > 366 ? `/${String(d.getFullYear()).slice(2)}` : ''}`
  }
  const labelled = stops.filter((_, k) => k % labelEvery === 0)

  return (
    <footer className="timeline">
      {cols && (
        <div className={`hover-chart${hover !== null ? ' show' : ''}`} aria-hidden="true">
          <svg viewBox="0 0 1000 100" preserveAspectRatio="none">
            <defs><linearGradient id="hc-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#ff8f00" stopOpacity=".85" /><stop offset="1" stopColor="#ff8f00" stopOpacity=".08" /></linearGradient></defs>
            <path d={`${path} L1000,100 L0,100 Z`} fill="url(#hc-fill)" />
            <path d={path} fill="none" stroke="#ffd54f" strokeWidth="1.5" vectorEffect="non-scaling-stroke" />
          </svg>
          <span className="hc-peak" style={{ left: `${pct(peak)}%`, top: `${cy(series![peak])}%` }}><em>Peak {series![peak].toLocaleString('en')} · {formatShort(addDays(start, peak))}</em></span>
          {hover !== null && (
            <>
              <span className="hc-line" style={{ left: `${pct(hover)}%` }} />
              <span className="hc-dot" style={{ left: `${pct(hover)}%`, top: `${cy(series![hover])}%` }} />
              <span className="hc-tip" style={{ left: `${pct(hover)}%`, transform: `translate(${pct(hover) < 12 ? '0' : pct(hover) > 88 ? '-100%' : '-50%'}, -100%)` }}>{formatShort(addDays(start, hover))} · {series![hover].toLocaleString('en')} hotspots</span>
            </>
          )}
        </div>
      )}
      <div className="timeline-body" onPointerMove={e => setHover(dayAt(e.clientX))} onPointerLeave={() => setHover(null)}>
        <div ref={trackRef} className={`track${grabbing ? ' dragging' : ''}`} role="slider" tabIndex={0} aria-label="Timeline"
          aria-valuemin={0} aria-valuemax={days} aria-valuenow={offset} aria-valuetext={formatLong(current)}
          onKeyDown={onKeyDown}
          onPointerDown={e => { dragging.current = true; setGrabbing(true); e.currentTarget.setPointerCapture(e.pointerId); fromPointer(e.clientX) }}
          onPointerMove={e => { if (dragging.current) fromPointer(e.clientX) }}
          onPointerUp={() => { dragging.current = false; setGrabbing(false) }} onPointerCancel={() => { dragging.current = false; setGrabbing(false) }}>
          {ticks.map(i => (
            <span key={i} className={`tick${stopSet.has(i) || i === days ? ' step' : ''}`} style={{ left: `${pct(i)}%` }} />
          ))}
          <span className="thumb" style={{ left: `${pct(offset)}%` }}><span className="bubble">{formatShort(current)}</span></span>
        </div>
        <div className="day-labels" aria-hidden="true">
          {labelled.map(i => (
            <span key={i} style={{ left: `${pct(i)}%` }}>{label(i)}</span>
          ))}
        </div>
      </div>
    </footer>
  )
}
