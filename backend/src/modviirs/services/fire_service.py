def get_calendar(lat_min: float, lat_max: float, lon_min: float, lon_max: float, sensor_group: str):
    """Monthly fire activity series with anomaly for an AOI.

    Delegates to queries.aoi_calendar.
    Returns a list of dicts: year, month, afd, valid, mean, std, p50, n_base, z, pctl.
    """
    raise NotImplementedError


def get_medians(lat_min: float, lat_max: float, lon_min: float, lon_max: float, sensor_group: str):
    """Historical monthly medians (12 rows) for an AOI.

    Delegates to queries.aoi_monthly_medians.
    Returns a list of dicts: month, median, p25, p75, mean, std, min, max, n_years, baseline_corto.
    """
    raise NotImplementedError


def get_points(
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
    start: str,
    end: str,
    **filters,
):
    """Individual fire detections within an AOI and date range.

    Optional filter kwargs: frp_comparable, exclude_persistent, sensor_group, satellite.
    Returns a list of dicts from hotspots_harmonized.parquet.
    If result exceeds the point cap, returns cell-aggregated data instead.
    """
    raise NotImplementedError


def get_timeline(
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
    start: str,
    end: str,
    sensor_group: str,
):
    """Daily fire activity timeline for an AOI.

    Delegates to queries.aoi_daily.
    Returns a list of dicts: date, cells_active, n_hotspots, frp_sum.
    """
    raise NotImplementedError


def get_current(lat_min: float, lat_max: float, lon_min: float, lon_max: float):
    """Month-to-date fire activity vs historical baseline (NRT data).

    Fetches NRT data via FIRMSClient, normalizes it, then delegates to
    queries.aoi_mtd_compare. Returns a dict matching the /fires/current schema
    defined in IMPLEMENTACION_API.md (I4).
    """
    raise NotImplementedError
