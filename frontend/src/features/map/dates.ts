export const DAY_MS = 86_400_000
const MONTHS_ES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
const MONTHS_ABBR = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

export const monthName = (m: number) => MONTHS_ES[m]
export const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate())
export const sameDay = (a: Date, b: Date) => a.getTime() === b.getTime()
export const addDays = (d: Date, n: number) => new Date(d.getFullYear(), d.getMonth(), d.getDate() + n)
export const diffDays = (a: Date, b: Date) => Math.round((b.getTime() - a.getTime()) / DAY_MS)

const pad = (n: number) => String(n).padStart(2, '0')
/** YYYY-MM-DD format for API params. Never use Date.toISOString() — it outputs UTC midnight which shifts the date for users west of UTC. */
export const isoDate = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
/** 10/OCT/26 */
export const formatShort = (d: Date) => `${pad(d.getDate())}/${MONTHS_ABBR[d.getMonth()].toUpperCase()}/${pad(d.getFullYear() % 100)}`
/** 10/Oct/2026 */
export const formatLong = (d: Date) => `${pad(d.getDate())}/${MONTHS_ABBR[d.getMonth()]}/${d.getFullYear()}`

/** 42 days (6 weeks) starting on Monday for the grid of the given month. */
export function monthGrid(year: number, month: number): Date[] {
  const first = new Date(year, month, 1)
  const offset = (first.getDay() + 6) % 7
  return Array.from({ length: 42 }, (_, i) => new Date(year, month, 1 - offset + i))
}

/** Nearest allowed position: a multiple of the step, or the final day. */
export function snapOffset(raw: number, step: number, days: number) {
  const clamped = Math.min(Math.max(raw, 0), days)
  const multiple = Math.round(clamped / step) * step
  return Math.abs(days - clamped) < Math.abs(multiple - clamped) ? days : Math.min(multiple, days)
}


/** NASA imagery used here starts in 2000: earlier dates cannot be selected. */
export const MIN_DATE = new Date(2000, 0, 1)
export const MIN_MONTH = MIN_DATE
export const MAX_MONTH = new Date(new Date().getFullYear(), 11, 31)
