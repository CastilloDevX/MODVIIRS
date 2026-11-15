import { useFireQuery, type QueryState } from '../useFireQuery'
import { getFiresCalendar } from '../api'
import type { Bbox } from '../../features/map/region'
import type { SensorGroup, CalendarResponse } from '../types'

export function useFiresCalendar(
  bbox: Bbox | null,
  sensorGroup: SensorGroup,
): QueryState<CalendarResponse> {
  return useFireQuery(
    bbox !== null ? (signal) => getFiresCalendar(bbox, sensorGroup, signal) : null,
    [bbox, sensorGroup],
  )
}
