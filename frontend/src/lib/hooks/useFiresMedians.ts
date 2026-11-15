import { useFireQuery, type QueryState } from '../useFireQuery'
import { getFiresMedians } from '../api'
import type { Bbox } from '../../features/map/region'
import type { SensorGroup, MediansResponse } from '../types'

export function useFiresMedians(
  bbox: Bbox | null,
  sensorGroup: SensorGroup,
): QueryState<MediansResponse> {
  return useFireQuery(
    bbox !== null ? (signal) => getFiresMedians(bbox, sensorGroup, signal) : null,
    [bbox, sensorGroup],
  )
}
