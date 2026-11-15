# Features

## Done

**Monthly fire activity history for an area of interest**
Given a bounding box, returns the complete monthly time series of fire activity across all available years (MODIS from 2001, VIIRS from 2012). Each month includes the raw activity value, its z-score and percentile relative to the historical baseline for that same calendar month, and a flag for known sensor gap months. Useful for plotting multi-year fire calendars and detecting anomalous seasons.
`GET /api/v1/fires/calendar`

**Typical fire seasonality for an area of interest**
Given a bounding box, returns the historical fire distribution summarized by calendar month (12 rows). For each month: median, interquartile range, mean, standard deviation, min and max across baseline years. Useful for showing what a "normal" fire year looks like and how the current year compares at a glance.
`GET /api/v1/fires/medians`

**Day-by-day fire activity between two dates**
Given a bounding box and a date range, returns the daily count of active fire cells, total hotspot detections, and total FRP sum. Useful for visualizing fire pulses and comparing specific fire events across days within a season or period.
`GET /api/v1/fires/timeline`

---

## Pending

**Current month fire activity vs historical baseline (NRT)**
Given a bounding box, fetches real-time VIIRS fire detections from the NASA FIRMS Area API for the ongoing month and compares them against the historical VIIRS baseline for the same day-range. Returns the month-to-date fire count alongside baseline statistics (median, percentiles, z-score) so the user can assess whether the current fire season is anomalous. Requires `MODVIIRS_FIRMS_MAP_KEY`.
`GET /api/v1/fires/current`

**Individual fire detections for an area and time window**
Given a bounding box and a date range, returns the raw fire detection records (location, date, FRP, confidence, satellite) from the harmonized point dataset. Also available as a CSV download. Requires `hotspots_harmonized.parquet` (not in repo — regenerate with the pipeline).
`GET /api/v1/fires/points` · `GET /api/v1/fires/points.csv`

**Burn activity anomaly prediction for an area of interest**
Given a bounding box, runs a trained model to predict whether fire activity in that area is expected to be anomalous based on historical patterns. Returns a prediction score, confidence interval, and the baseline used. Model not yet implemented.
`GET /api/v1/predictions`
