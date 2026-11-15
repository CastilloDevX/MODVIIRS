export type SensorGroup = 'VIIRS' | 'MODIS'

export type FirePoint = {
  latitude: number
  longitude: number
  acq_date_d: string
  frp: number
  conf_class: 'nominal' | 'high'
  daynight: 'D' | 'N'
  is_persistent: boolean
  frp_comparable: boolean
  bright_main: number
  satellite: string
  sensor_group: SensorGroup
  year: number
  month: number
  res_m: number
  version: string
}

export type PointsResponse = {
  count: number
  truncated: boolean
  data: FirePoint[]
}

export type TimelineRow = {
  date: string
  cells_active: number
  n_hotspots: number
  frp_sum: number
}

export type TimelineResponse = {
  sensor_group: SensorGroup
  start: string
  end: string
  data: TimelineRow[]
}

export type MedianRow = {
  month: number
  median: number
  p25: number
  p75: number
  mean: number
  std: number
  min: number
  max: number
  n_years: number
  baseline_corto: boolean
}

export type MediansResponse = {
  sensor_group: SensorGroup
  data: MedianRow[]
}

export type CalendarRow = {
  year: number
  month: number
  afd: number
  valid: boolean
  mean: number
  std: number
  p50: number
  n_base: number
  z: number | null
  pctl: number | null
}

export type CalendarResponse = {
  sensor_group: SensorGroup
  data: CalendarRow[]
}

export type PointFilters = {
  frp_comparable?: boolean
  exclude_persistent?: boolean
  satellite?: string
}
