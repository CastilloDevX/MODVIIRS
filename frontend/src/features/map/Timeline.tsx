import { useRef, useState } from 'react'
import { addDays, diffDays, formatLong, formatShort, snapOffset } from './dates'

type Props = {
  start: Date
  end: Date
  offset: number
  stepDays: number
  onOffsetChange: (offset: number) => void
}

const MAX_TICKS = 400

export function Timeline({ start, end, offset, stepDays, onOffsetChange }: Props) {
  const trackRef = useRef<HTMLDivElement>(null)
  const dragging = useRef(false)
  const [grabbing, setGrabbing] = useState(false)
  const days = diffDays(start, end)
  const pct = (i: number) => (days === 0 ? 0 : (i / days) * 100)
  const tickStride = Math.max(1, Math.ceil((days + 1) / MAX_TICKS))
  const labelStride = Math.max(stepDays, Math.ceil(days / 10 / stepDays) * stepDays)
  const current = addDays(start, offset)

  const fromPointer = (clientX: number) => {
    const rect = trackRef.current!.getBoundingClientRect()
    const frac = Math.min(Math.max((clientX - rect.left) / rect.width, 0), 1)
    onOffsetChange(snapOffset(frac * days, stepDays, days))
  }

  const onKeyDown = (e: React.KeyboardEvent) => {
    const moves: Record<string, number> = { ArrowRight: offset + stepDays, ArrowUp: offset + stepDays, ArrowLeft: offset - stepDays, ArrowDown: offset - stepDays, Home: 0, End: days }
    if (!(e.key in moves)) return
    e.preventDefault()
    onOffsetChange(snapOffset(moves[e.key], stepDays, days))
  }

  const ticks: number[] = []
  for (let i = 0; i <= days; i += tickStride) ticks.push(i)
  if (ticks[ticks.length - 1] !== days) ticks.push(days)

  return (
    <footer className="timeline">
      <div className="timeline-body">
        <div ref={trackRef} className={`track${grabbing ? ' dragging' : ''}`} role="slider" tabIndex={0} aria-label="Línea de tiempo"
          aria-valuemin={0} aria-valuemax={days} aria-valuenow={offset} aria-valuetext={formatLong(current)}
          onKeyDown={onKeyDown}
          onPointerDown={e => { dragging.current = true; setGrabbing(true); e.currentTarget.setPointerCapture(e.pointerId); fromPointer(e.clientX) }}
          onPointerMove={e => { if (dragging.current) fromPointer(e.clientX) }}
          onPointerUp={() => { dragging.current = false; setGrabbing(false) }} onPointerCancel={() => { dragging.current = false; setGrabbing(false) }}>
          {ticks.map(i => (
            <span key={i} className={`tick${i % stepDays === 0 || i === days ? ' step' : ''}`} style={{ left: `${pct(i)}%` }} />
          ))}
          <span className="thumb" style={{ left: `${pct(offset)}%` }}><span className="bubble">{formatShort(current)}</span></span>
        </div>
        <div className="day-labels" aria-hidden="true">
          {ticks.filter(i => i % labelStride === 0 || i === days).map(i => (
            <span key={i} style={{ left: `${pct(i)}%` }}>{addDays(start, i).getDate()}</span>
          ))}
        </div>
      </div>
    </footer>
  )
}
