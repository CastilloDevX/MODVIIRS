import { es } from 'react-day-picker/locale'
import { Calendar } from '@/components/ui/calendar'
import { MAX_DATE, MAX_MONTH, MIN_DATE, MIN_MONTH } from './dates'
import { PHASES, type PhaseId } from './hotspots'

type Props = {
  start: Date
  end: Date
  onChange: (start: Date, end: Date) => void
  /** Days of the range grouped by hotspot intensity phase; each one is painted in its colour. */
  phaseDays?: Record<PhaseId, Date[]> | null
}

export function RangeCalendar({ start, end, onChange, phaseDays }: Props) {
  return (
    <>
      <Calendar mode="range" locale={es} weekStartsOn={1} captionLayout="dropdown" startMonth={MIN_MONTH} endMonth={MAX_MONTH} disabled={{ before: MIN_DATE, after: MAX_DATE }} selected={{ from: start, to: end }} defaultMonth={start}
        modifiers={phaseDays ?? undefined} modifiersClassNames={{ yellow: 'day-yellow', orange: 'day-orange', red: 'day-red' }}
        className="range-calendar" onSelect={r => { if (r?.from) onChange(r.from, r.to ?? r.from) }} />
      {phaseDays && (
        <ul className="day-legend" aria-label="Color de cada día según sus hotspots">
          {PHASES.map(ph => <li key={ph.id}><span style={{ background: ph.color }} />{ph.label}</li>)}
          <li className="day-legend-note">Intensidad del día frente al día pico de la región (escala log).</li>
        </ul>
      )}
    </>
  )
}
