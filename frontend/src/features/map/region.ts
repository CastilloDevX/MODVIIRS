import type { Feature, LineString, Polygon, Position } from 'geojson'
import { worldRing } from './countries'

export type Bbox = { west: number; south: number; east: number; north: number }
export type LngLat = { lng: number; lat: number }

const MAX_LAT = 85
const clampLat = (v: number) => Math.max(-MAX_LAT, Math.min(MAX_LAT, v))

/** Box spanned by two opposite corners, in whatever order they were clicked. The box does not cross the antimeridian. */
export function bboxOf(a: LngLat, b: LngLat): Bbox {
  return { west: Math.min(a.lng, b.lng), east: Math.max(a.lng, b.lng), south: clampLat(Math.min(a.lat, b.lat)), north: clampLat(Math.max(a.lat, b.lat)) }
}

/** Closed ring with a vertex every 2 degrees at most, so the edges follow the curvature of the globe. */
function ring(b: Bbox): Position[] {
  const out: Position[] = []
  const edge = (from: Position, to: Position) => {
    const n = Math.max(1, Math.ceil(Math.max(Math.abs(to[0] - from[0]), Math.abs(to[1] - from[1])) / 2))
    for (let i = 0; i < n; i++) out.push([from[0] + ((to[0] - from[0]) * i) / n, from[1] + ((to[1] - from[1]) * i) / n])
  }
  const sw: Position = [b.west, b.south], se: Position = [b.east, b.south], ne: Position = [b.east, b.north], nw: Position = [b.west, b.north]
  edge(sw, se); edge(se, ne); edge(ne, nw); edge(nw, sw)
  out.push(out[0])
  return out
}

/** The whole world, or the whole world minus the box: what is dimmed. */
export function dimOutside(b: Bbox | null): Feature<Polygon> {
  return { type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: b ? [worldRing(), ring(b)] : [worldRing()] } }
}

export function outlineOf(b: Bbox): Feature<LineString> {
  return { type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: ring(b) } }
}
