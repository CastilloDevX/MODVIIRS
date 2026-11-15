import { useState } from 'react'
import { Calendar } from '@/components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { MAX_DATE, MAX_MONTH, MIN_DATE, MIN_MONTH, formatShort } from './dates'

type Props = { label: string; value: Date; onChange: (d: Date) => void; min?: Date; max?: Date }

export function DateField({ label, value, onChange, min, max }: Props) {
  const [open, setOpen] = useState(false)
  return (
    <div className="date-col">
      <span className="label">{label}</span>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger className="date-field" aria-label={`${label}: ${formatShort(value)}`}>{formatShort(value)}</PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar mode="single" weekStartsOn={1} captionLayout="dropdown" startMonth={MIN_MONTH} endMonth={MAX_MONTH} required selected={value} defaultMonth={value}
            disabled={[{ before: min && min > MIN_DATE ? min : MIN_DATE }, { after: max && max < MAX_DATE ? max : MAX_DATE }]}
            onSelect={d => { if (d) { onChange(d); setOpen(false) } }} />
        </PopoverContent>
      </Popover>
    </div>
  )
}
