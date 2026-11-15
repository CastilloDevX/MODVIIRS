import { useFireQuery, type QueryState } from '../useFireQuery'
import { getFiresPoints } from '../api'
import type { Bbox } from '../../features/map/region'
import type { PointFilters, PointsResponse } from '../types'

export function useFiresPoints(
  bbox: Bbox | null,
  start: string,
  end: string,
  filters: PointFilters,
): QueryState<PointsResponse> {
  const { frp_comparable, exclude_persistent, satellite } = filters
  return useFireQuery(
    bbox !== null ? (signal) => getFiresPoints(bbox, start, end, filters, signal) : null,
    [bbox, start, end, frp_comparable, exclude_persistent, satellite],
  )
}
