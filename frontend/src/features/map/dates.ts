export const DAY_MS = 86_400_000
const MONTHS_EN = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
const MONTHS_ABBR = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

export const monthName = (m: number) => MONTHS_EN[m]
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

export type StepUnit = 'day' | 'week' | 'month' | 'year'
export const STEP_UNITS: { id: StepUnit; label: string }[] = [
  { id: 'day', label: 'Days' }, { id: 'week', label: 'Weeks' }, { id: 'month', label: 'Months' }, { id: 'year', label: 'Years' },
]

/** Adds k units to a date; month/year steps keep the day of month, clamped to the shorter month. */
export function addUnits(d: Date, unit: StepUnit, k: number): Date {
  if (unit === 'day') return addDays(d, k)
  if (unit === 'week') return addDays(d, 7 * k)
  const months = unit === 'month' ? k : 12 * k
  const lastDay = new Date(d.getFullYear(), d.getMonth() + months + 1, 0).getDate()
  return new Date(d.getFullYear(), d.getMonth() + months, Math.min(d.getDate(), lastDay))
}

/** Day offsets (from start) where each step begins: 0, n units, 2n units... up to the end date. */
export function stepStops(start: Date, end: Date, unit: StepUnit, n: number): number[] {
  const days = diffDays(start, end)
  const stops: number[] = []
  for (let k = 0; ; k++) {
    const offset = diffDays(start, addUnits(start, unit, k * n))
    if (offset > days) break
    stops.push(offset)
  }
  return stops
}

/** Nearest step start, or the final day. */
export function snapToStops(raw: number, stops: number[], days: number) {
  const clamped = Math.min(Math.max(raw, 0), days)
  return [...stops, days].reduce((best, s) => (Math.abs(s - clamped) < Math.abs(best - clamped) ? s : best), 0)
}

/** Last day offset (inclusive) covered by the step that starts at `offset`. */
export function stepEnd(offset: number, stops: number[], days: number) {
  const next = stops.find(s => s > offset)
  return next === undefined ? days : next - 1
}

/** The hotspot dataset covers 2000-11-01 to 2025-12-31: dates outside cannot be selected. */
export const MIN_DATE = new Date(2000, 10, 1)
export const MAX_DATE = new Date(2025, 11, 31)
export const MIN_MONTH = MIN_DATE
export const MAX_MONTH = MAX_DATE
