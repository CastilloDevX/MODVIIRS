from flask import Blueprint, jsonify

fires = Blueprint("fires", __name__)


@fires.get("/fires/calendar")
def get_calendar():
    """GET /api/v1/fires/calendar

    Query params: lat_min, lat_max, lon_min, lon_max, sensor_group (default: VIIRS)
    Returns: year, month, afd, valid, mean, std, p50, n_base, z, pctl
    """
    return jsonify(status="not_implemented"), 501


@fires.get("/fires/medians")
def get_medians():
    """GET /api/v1/fires/medians

    Query params: lat_min, lat_max, lon_min, lon_max, sensor_group (default: VIIRS)
    Returns: month, median, p25, p75, mean, std, min, max, n_years, baseline_corto
    """
    return jsonify(status="not_implemented"), 501


@fires.get("/fires/points")
def get_points():
    """GET /api/v1/fires/points

    Query params: lat_min, lat_max, lon_min, lon_max, start, end
    Optional: frp_comparable, exclude_persistent, sensor_group, satellite
    Returns GeoJSON points or cell-aggregated data if above the point cap.
    """
    return jsonify(status="not_implemented"), 501


@fires.get("/fires/points.csv")
def get_points_csv():
    """GET /api/v1/fires/points.csv

    Same params as /fires/points. Streams full results as a CSV file download.
    """
    return jsonify(status="not_implemented"), 501


@fires.get("/fires/timeline")
def get_timeline():
    """GET /api/v1/fires/timeline

    Query params: lat_min, lat_max, lon_min, lon_max, start, end,
                  sensor_group (default: VIIRS)
    Returns: date, cells_active, n_hotspots, frp_sum
    """
    return jsonify(status="not_implemented"), 501


@fires.get("/fires/current")
def get_current():
    """GET /api/v1/fires/current

    Month-to-date fire activity vs historical baseline using NRT data.
    Query params: lat_min, lat_max, lon_min, lon_max
    Returns: as_of, afd_mtd, median, z, pctl, preliminary, sources
    """
    return jsonify(status="not_implemented"), 501
