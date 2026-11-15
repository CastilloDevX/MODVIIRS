import type { Bbox } from '../features/map/region'
import type {
  SensorGroup,
  PointFilters,
  PointsResponse,
  TimelineResponse,
  MediansResponse,
  CalendarResponse,
} from './types'

const _apiBase = import.meta.env.VITE_API_BASE_URL
if (!_apiBase) throw new Error('[api] VITE_API_BASE_URL is not set — copy .env.example to .env and restart Vite.')
const API_BASE_URL = _apiBase.replace(/\/$/, '')

function bboxParams(bbox: Bbox): URLSearchParams {
  const p = new URLSearchParams()
  p.set('lat_min', String(bbox.south))
  p.set('lat_max', String(bbox.north))
  p.set('lon_min', String(bbox.west))
  p.set('lon_max', String(bbox.east))
  return p
}

function applyFilters(p: URLSearchParams, filters: PointFilters) {
  if (filters.frp_comparable !== undefined) p.set('frp_comparable', String(filters.frp_comparable))
  if (filters.exclude_persistent !== undefined) p.set('exclude_persistent', String(filters.exclude_persistent))
  if (filters.satellite !== undefined) p.set('satellite', filters.satellite)
}

function expectArray(data: unknown, endpoint: string): void {
  if (typeof data !== 'object' || data === null || !('data' in data) || !Array.isArray((data as Record<string, unknown>).data)) {
    throw new Error(`Unexpected response from ${endpoint}`)
  }
}

export async function getHello(signal: AbortSignal): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE_URL}/hello`, { signal })
  if (!response.ok) throw new Error(`La API respondió con el estado ${response.status}.`)
  const data: unknown = await response.json()
  if (typeof data !== 'object' || data === null || !('message' in data) || typeof (data as Record<string, unknown>).message !== 'string') {
    throw new Error('La API devolvió una respuesta inesperada.')
  }
  return { message: (data as { message: string }).message }
}

export async function getFiresPoints(
  bbox: Bbox,
  start: string,
  end: string,
  filters: PointFilters,
  signal: AbortSignal,
): Promise<PointsResponse> {
  const p = bboxParams(bbox)
  p.set('start', start)
  p.set('end', end)
  applyFilters(p, filters)
  const response = await fetch(`${API_BASE_URL}/fires/points?${p}`, { signal })
  if (!response.ok) throw new Error(`API error ${response.status}`)
  const data: unknown = await response.json()
  expectArray(data, '/fires/points')
  return data as PointsResponse
}

export async function getFiresTimeline(
  bbox: Bbox,
  start: string,
  end: string,
  sensorGroup: SensorGroup,
  signal: AbortSignal,
): Promise<TimelineResponse> {
  const p = bboxParams(bbox)
  p.set('start', start)
  p.set('end', end)
  p.set('sensor_group', sensorGroup)
  const response = await fetch(`${API_BASE_URL}/fires/timeline?${p}`, { signal })
  if (!response.ok) throw new Error(`API error ${response.status}`)
  const data: unknown = await response.json()
  expectArray(data, '/fires/timeline')
  return data as TimelineResponse
}

export async function getFiresMedians(
  bbox: Bbox,
  sensorGroup: SensorGroup,
  signal: AbortSignal,
): Promise<MediansResponse> {
  const p = bboxParams(bbox)
  p.set('sensor_group', sensorGroup)
  const response = await fetch(`${API_BASE_URL}/fires/medians?${p}`, { signal })
  if (!response.ok) throw new Error(`API error ${response.status}`)
  const data: unknown = await response.json()
  expectArray(data, '/fires/medians')
  return data as MediansResponse
}

export async function getFiresCalendar(
  bbox: Bbox,
  sensorGroup: SensorGroup,
  signal: AbortSignal,
): Promise<CalendarResponse> {
  const p = bboxParams(bbox)
  p.set('sensor_group', sensorGroup)
  const response = await fetch(`${API_BASE_URL}/fires/calendar?${p}`, { signal })
  if (!response.ok) throw new Error(`API error ${response.status}`)
  const data: unknown = await response.json()
  expectArray(data, '/fires/calendar')
  return data as CalendarResponse
}

/** Builds the CSV download URL for direct use in an <a href> — no fetch needed. */
export function getPointsCsvUrl(bbox: Bbox, start: string, end: string, filters: PointFilters): string {
  const p = bboxParams(bbox)
  p.set('start', start)
  p.set('end', end)
  applyFilters(p, filters)
  return `${API_BASE_URL}/fires/points.csv?${p}`
}
