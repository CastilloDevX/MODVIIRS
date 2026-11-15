import type { FirePoint } from '../../lib/types'

/** FRP (MW) that maps to intensity 1; anything above is clamped. */
export const FRP_MAX = 500

export type PhaseId = 'yellow' | 'orange' | 'red'

/** Intensity runs 0..1: up to 0.4 yellows, up to 0.7 oranges, above that reds. */
export const PHASES: { id: PhaseId; label: string; range: string; from: number; to: number; color: string }[] = [
  { id: 'yellow', label: 'Yellow', range: '0 – 0.4', from: 0, to: 0.4, color: '#ffd600' },
  { id: 'orange', label: 'Orange', range: '0.4 – 0.7', from: 0.4, to: 0.7, color: '#ff8f00' },
  { id: 'red', label: 'Red', range: '0.7 – 1', from: 0.7, to: 1, color: '#e53935' },
]

/** Fire radiative power on a log scale, normalised to 0..1 (FRP is heavy-tailed). */
export const intensityOf = (p: FirePoint) => Math.min(1, Math.log10(1 + Math.max(p.frp, 0)) / Math.log10(1 + FRP_MAX))

export const phaseOf = (intensity: number): PhaseId => (intensity < 0.4 ? 'yellow' : intensity < 0.7 ? 'orange' : 'red')

export function countPhases(points: FirePoint[] | null): Record<PhaseId, number> {
  const counts: Record<PhaseId, number> = { yellow: 0, orange: 0, red: 0 }
  for (const p of points ?? []) counts[phaseOf(intensityOf(p))]++
  return counts
}
