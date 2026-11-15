import { es } from 'react-day-picker/locale'
import { Calendar } from '@/components/ui/calendar'
import { MAX_MONTH, MIN_DATE, MIN_MONTH } from './dates'

type Props = { start: Date; end: Date; onChange: (start: Date, end: Date) => void }

export function RangeCalendar({ start, end, onChange }: Props) {
  return (
    <Calendar mode="range" locale={es} weekStartsOn={1} captionLayout="dropdown" startMonth={MIN_MONTH} endMonth={MAX_MONTH} disabled={{ before: MIN_DATE }} selected={{ from: start, to: end }} defaultMonth={start}
      className="range-calendar" onSelect={r => { if (r?.from) onChange(r.from, r.to ?? r.from) }} />
  )
}
