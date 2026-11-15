import { useFireQuery, type QueryState } from '../useFireQuery'
import { getFiresTimeline } from '../api'
import type { Bbox } from '../../features/map/region'
import type { SensorGroup, TimelineResponse } from '../types'

export function useFiresTimeline(
  bbox: Bbox | null,
  start: string,
  end: string,
  sensorGroup: SensorGroup,
): QueryState<TimelineResponse> {
  return useFireQuery(
    bbox !== null ? (signal) => getFiresTimeline(bbox, start, end, sensorGroup, signal) : null,
    [bbox, start, end, sensorGroup],
  )
}
