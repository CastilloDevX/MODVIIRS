import type { FirePoint, TimelineRow } from '../../lib/types'
import { addDays, diffDays } from './dates'
import { phaseOf, type PhaseId } from './hotspots'

/** The API sends ISO dates ("2012-12-01") or HTTP dates ("Sat, 01 Dec 2012 00:00:00 GMT"); both mean a calendar day in UTC. */
const parseDay = (s: string) => {
  const iso = /^(\d{4})-(\d{2})-(\d{2})/.exec(s)
  if (iso) return new Date(+iso[1], +iso[2] - 1, +iso[3])
  const d = new Date(s)
  return new Date(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate())
}

/** One value per day of the range (0 where the API returned no row). */
export function denseSeries(rows: TimelineRow[] | undefined, start: Date, days: number, key: 'n_hotspots' | 'frp_sum' | 'cells_active'): number[] {
  const out = new Array<number>(days + 1).fill(0)
  for (const r of rows ?? []) {
    const i = diffDays(start, parseDay(r.date))
    if (i >= 0 && i <= days) out[i] = r[key]
  }
  return out
}

export type RangeStats = { total: number; activeDays: number; days: number; peak: number; peakDate: Date; perDay: number; frpSum: number; maxCells: number }

export function rangeStats(rows: TimelineRow[] | undefined, start: Date, days: number): RangeStats {
  const hot = denseSeries(rows, start, days, 'n_hotspots')
  const frp = denseSeries(rows, start, days, 'frp_sum')
  const cells = denseSeries(rows, start, days, 'cells_active')
  const total = hot.reduce((a, b) => a + b, 0)
  const peakIdx = hot.reduce((best, v, i) => (v > hot[best] ? i : best), 0)
  return {
    total, days: days + 1, activeDays: hot.filter(v => v > 0).length, peak: hot[peakIdx], peakDate: addDays(start, peakIdx),
    perDay: total / (days + 1), frpSum: frp.reduce((a, b) => a + b, 0), maxCells: Math.max(0, ...cells),
  }
}

const quantile = (sorted: number[], q: number) => (sorted.length ? sorted[Math.min(sorted.length - 1, Math.floor(q * sorted.length))] : 0)

export const FRP_BINS = [0, 1, 2, 5, 10, 20, 50, 100, 200, 500]

export type PointStats = {
  n: number; frpMean: number; frpMedian: number; frpP90: number; frpMax: number; frpSum: number
  highPct: number; nightPct: number; persistentPct: number; comparablePct: number
  day: number; night: number; high: number; nominal: number
  satellites: { label: string; value: number }[]
  histogram: number[]
}

export function pointStats(points: FirePoint[]): PointStats {
  const n = points.length
  const frp = points.map(p => p.frp).sort((a, b) => a - b)
  const sum = frp.reduce((a, b) => a + b, 0)
  const night = points.filter(p => p.daynight === 'N').length
  const high = points.filter(p => p.conf_class === 'high').length
  const sats = new Map<string, number>()
  const histogram = new Array<number>(FRP_BINS.length).fill(0)
  for (const p of points) {
    sats.set(p.satellite, (sats.get(p.satellite) ?? 0) + 1)
    let b = 0
    while (b + 1 < FRP_BINS.length && p.frp >= FRP_BINS[b + 1]) b++
    histogram[b]++
  }
  const pct = (k: number) => (n ? (100 * k) / n : 0)
  return {
    n, frpSum: sum, frpMean: n ? sum / n : 0, frpMedian: quantile(frp, 0.5), frpP90: quantile(frp, 0.9), frpMax: frp[n - 1] ?? 0,
    highPct: pct(high), nightPct: pct(night), persistentPct: pct(points.filter(p => p.is_persistent).length),
    comparablePct: pct(points.filter(p => p.frp_comparable).length),
    day: n - night, night, high, nominal: n - high,
    satellites: [...sats].map(([label, value]) => ({ label, value })).sort((a, b) => b.value - a.value),
    histogram,
  }
}

/** Approximate area of a lat/lon box in km². */
export const boxAreaKm2 = (b: { south: number; north: number; west: number; east: number }) =>
  Math.abs(b.north - b.south) * 111.32 * Math.abs(b.east - b.west) * 111.32 * Math.cos((((b.north + b.south) / 2) * Math.PI) / 180)

/** Reduces a long series to at most `n` columns keeping the maximum of each bucket, so peaks survive. */
export function downsample(values: number[], n: number): number[] {
  if (values.length <= n) return values
  const out: number[] = []
  const size = values.length / n
  for (let i = 0; i < n; i++) out.push(Math.max(...values.slice(Math.floor(i * size), Math.max(Math.floor((i + 1) * size), Math.floor(i * size) + 1))))
  return out
}


/**
 * Phase of each day with hotspots, from its hotspot count on a log scale relative to the peak day
 * of the region (0..1: up to 0.4 yellow, up to 0.7 orange, above that red). Days without hotspots are left out.
 */
export function dayPhases(hotspotsPerDay: number[], start: Date): Record<PhaseId, Date[]> {
  const out: Record<PhaseId, Date[]> = { yellow: [], orange: [], red: [] }
  const max = Math.max(0, ...hotspotsPerDay)
  if (max === 0) return out
  hotspotsPerDay.forEach((n, i) => {
    if (n > 0) out[phaseOf(Math.log10(1 + n) / Math.log10(1 + max))].push(addDays(start, i))
  })
  return out
}
