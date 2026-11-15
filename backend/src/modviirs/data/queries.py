# Paste the contents of aoi_queries.py here.
#
# Functions expected by fire_service:
#   aoi_calendar, aoi_monthly_medians, aoi_daily,
#   aoi_mtd_compare, normalize_nrt, nrt_request_plan
#
# Key conventions (from IMPLEMENTACION_API.md):
#   - Grid index: math.floor(value / 0.1)  — NOT int(), breaks on negative coords
#   - Anomaly at AOI level: sum cells → z/percentile, never average per-cell z
#   - sensor_group "VIIRS" uses baseline 2012–2024; "MODIS" for long history
#   - valid=False means sensor gap (not zero fire); valid month with no fire → afd=0
#   - Parquet files are read from the path set in current_app.config["MODVIIRS_DATA_PATH"]


def aoi_calendar(lat_min, lat_max, lon_min, lon_max, sensor_group):
    """Monthly fire activity series with anomaly stats for an AOI.

    Returns columns: year, month, afd, valid, mean, std, p50, n_base, z, pctl
    """
    raise NotImplementedError


def aoi_monthly_medians(lat_min, lat_max, lon_min, lon_max, sensor_group):
    """12-row historical distribution (one per calendar month) for an AOI.

    Returns columns: month, median, p25, p75, mean, std, min, max, n_years, baseline_corto
    """
    raise NotImplementedError


def aoi_daily(bbox_latlon, start, end, sensor_group):
    """Daily fire activity timeline for an AOI.

    Returns columns: date, cells_active, n_hotspots, frp_sum
    sum(cells_active) over a month must equal afd from aoi_calendar for that month.
    """
    raise NotImplementedError


def aoi_mtd_compare(bbox_latlon, nrt_norm, as_of):
    """Compare month-to-date NRT data against the historical baseline.

    Compares the same day-range within each baseline year (not full months).
    Returns a dict matching the /fires/current response schema.
    """
    raise NotImplementedError


def normalize_nrt(raw_df):
    """Apply pipeline harmonization rules to raw Area API CSV data.

    Applies: confidence l/n/h → low/nominal/high (drops low), deduplication,
    grid indices via floor(), persistent source marking, frp_comparable flag.
    NRT data does not include the 'type' column — do not depend on it.
    """
    raise NotImplementedError


def nrt_request_plan(bbox_lonlat, start, as_of):
    """Generate the list of Area API requests needed to cover a date range.

    Each window is ≤5 days (API limit). Sources: VIIRS_NOAA20_NRT, VIIRS_NOAA21_NRT.
    Returns a list of dicts with keys: source, bbox, day_range, date.
    """
    raise NotImplementedError
