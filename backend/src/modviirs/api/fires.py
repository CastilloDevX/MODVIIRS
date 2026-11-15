import datetime as dt
import io

import polars as pl
from flask import Blueprint, Response, jsonify, request

from modviirs.data import queries as Q
from modviirs.services import fire_service

fires = Blueprint("fires", __name__)


def _parse_bbox():
    """Extract and validate lat_min/max, lon_min/max from query string."""
    return (
        float(request.args["lat_min"]),
        float(request.args["lat_max"]),
        float(request.args["lon_min"]),
        float(request.args["lon_max"]),
    )


def _parse_dates():
    """Extract and validate start/end as datetime.date from query string."""
    return (
        dt.date.fromisoformat(request.args["start"]),
        dt.date.fromisoformat(request.args["end"]),
    )


def _parse_point_filters():
    """Extract optional hotspot filters from query string."""
    filters = {}
    if "sensor_group" in request.args:
        filters["sensor_group"] = request.args["sensor_group"]
    if "satellite" in request.args:
        filters["satellite"] = request.args["satellite"]
    if "frp_comparable" in request.args:
        filters["frp_comparable"] = request.args["frp_comparable"].lower() == "true"
    if "exclude_persistent" in request.args:
        filters["exclude_persistent"] = (
            request.args["exclude_persistent"].lower() == "true"
        )
    return filters


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
    try:
        lat_min, lat_max, lon_min, lon_max = _parse_bbox()
    except (KeyError, ValueError):
        return jsonify(error="lat_min, lat_max, lon_min, lon_max are required floats"), 400
    try:
        start, end = _parse_dates()
    except (KeyError, ValueError):
        return jsonify(error="start and end are required as YYYY-MM-DD"), 400
    filters = _parse_point_filters()
    data, truncated = fire_service.get_points(
        lat_min, lat_max, lon_min, lon_max, start, end, **filters
    )
    return jsonify(count=len(data), truncated=truncated, data=data)


@fires.get("/fires/points.csv")
def get_points_csv():
    try:
        lat_min, lat_max, lon_min, lon_max = _parse_bbox()
    except (KeyError, ValueError):
        return jsonify(error="lat_min, lat_max, lon_min, lon_max are required floats"), 400
    try:
        start, end = _parse_dates()
    except (KeyError, ValueError):
        return jsonify(error="start and end are required as YYYY-MM-DD"), 400
    filters = _parse_point_filters()
    bbox = (lat_min, lat_max, lon_min, lon_max)
    df = Q.aoi_points_all(bbox, start, end, **filters)
    buf = io.StringIO()
    df.with_columns(pl.col("acq_date_d").dt.to_string("%Y-%m-%d")).write_csv(buf)
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=hotspots.csv"},
    )


@fires.get("/fires/current")
def get_current():
    return jsonify(status="not_implemented"), 501
