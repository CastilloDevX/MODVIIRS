import datetime as dt

from flask import Blueprint, jsonify, request

from modviirs.services import fire_service

fires = Blueprint("fires", __name__)


def _parse_bbox():
    """Extract and validate lat_min/max, lon_min/max from query string.
    Returns (lat_min, lat_max, lon_min, lon_max) or raises ValueError.
    """
    return (
        float(request.args["lat_min"]),
        float(request.args["lat_max"]),
        float(request.args["lon_min"]),
        float(request.args["lon_max"]),
    )


@fires.get("/fires/calendar")
def get_calendar():
    try:
        lat_min, lat_max, lon_min, lon_max = _parse_bbox()
    except (KeyError, ValueError):
        return jsonify(error="lat_min, lat_max, lon_min, lon_max are required floats"), 400
    sensor_group = request.args.get("sensor_group", "VIIRS")
    data = fire_service.get_calendar(lat_min, lat_max, lon_min, lon_max, sensor_group)
    return jsonify(sensor_group=sensor_group, data=data)


@fires.get("/fires/medians")
def get_medians():
    try:
        lat_min, lat_max, lon_min, lon_max = _parse_bbox()
    except (KeyError, ValueError):
        return jsonify(error="lat_min, lat_max, lon_min, lon_max are required floats"), 400
    sensor_group = request.args.get("sensor_group", "VIIRS")
    data = fire_service.get_medians(lat_min, lat_max, lon_min, lon_max, sensor_group)
    return jsonify(sensor_group=sensor_group, data=data)


@fires.get("/fires/timeline")
def get_timeline():
    try:
        lat_min, lat_max, lon_min, lon_max = _parse_bbox()
    except (KeyError, ValueError):
        return jsonify(error="lat_min, lat_max, lon_min, lon_max are required floats"), 400
    try:
        start = dt.date.fromisoformat(request.args["start"])
        end = dt.date.fromisoformat(request.args["end"])
    except (KeyError, ValueError):
        return jsonify(error="start and end are required as YYYY-MM-DD"), 400
    sensor_group = request.args.get("sensor_group", "VIIRS")
    data = fire_service.get_timeline(lat_min, lat_max, lon_min, lon_max, start, end, sensor_group)
    return jsonify(
        sensor_group=sensor_group, start=start.isoformat(), end=end.isoformat(), data=data
    )


@fires.get("/fires/points")
def get_points():
    return jsonify(status="not_implemented"), 501


@fires.get("/fires/points.csv")
def get_points_csv():
    return jsonify(status="not_implemented"), 501


@fires.get("/fires/current")
def get_current():
    return jsonify(status="not_implemented"), 501
