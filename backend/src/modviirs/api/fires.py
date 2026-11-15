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
    """
    Monthly fire activity history for an area of interest.
    ---
    tags:
      - Fires
    parameters:
      - name: lat_min
        in: query
        type: number
        required: true
      - name: lat_max
        in: query
        type: number
        required: true
      - name: lon_min
        in: query
        type: number
        required: true
      - name: lon_max
        in: query
        type: number
        required: true
      - name: sensor_group
        in: query
        type: string
        required: false
        default: VIIRS
        description: "Sensor group (VIIRS or MODIS)."
    responses:
      200:
        description: Monthly fire counts per year.
      400:
        description: Missing or invalid bbox parameters.
    """
    try:
        lat_min, lat_max, lon_min, lon_max = _parse_bbox()
    except (KeyError, ValueError):
        return jsonify(error="lat_min, lat_max, lon_min, lon_max are required floats"), 400
    sensor_group = request.args.get("sensor_group", "VIIRS")
    data = fire_service.get_calendar(lat_min, lat_max, lon_min, lon_max, sensor_group)
    return jsonify(sensor_group=sensor_group, data=data)


@fires.get("/fires/medians")
def get_medians():
    """
    Historical fire seasonality statistics for an area of interest.
    ---
    tags:
      - Fires
    parameters:
      - name: lat_min
        in: query
        type: number
        required: true
      - name: lat_max
        in: query
        type: number
        required: true
      - name: lon_min
        in: query
        type: number
        required: true
      - name: lon_max
        in: query
        type: number
        required: true
      - name: sensor_group
        in: query
        type: string
        required: false
        default: VIIRS
        description: "Sensor group (VIIRS or MODIS)."
    responses:
      200:
        description: Median fire counts by day-of-year.
      400:
        description: Missing or invalid bbox parameters.
    """
    try:
        lat_min, lat_max, lon_min, lon_max = _parse_bbox()
    except (KeyError, ValueError):
        return jsonify(error="lat_min, lat_max, lon_min, lon_max are required floats"), 400
    sensor_group = request.args.get("sensor_group", "VIIRS")
    data = fire_service.get_medians(lat_min, lat_max, lon_min, lon_max, sensor_group)
    return jsonify(sensor_group=sensor_group, data=data)


@fires.get("/fires/timeline")
def get_timeline():
    """
    Day-by-day fire counts for a date range and area of interest.
    ---
    tags:
      - Fires
    parameters:
      - name: lat_min
        in: query
        type: number
        required: true
      - name: lat_max
        in: query
        type: number
        required: true
      - name: lon_min
        in: query
        type: number
        required: true
      - name: lon_max
        in: query
        type: number
        required: true
      - name: start
        in: query
        type: string
        required: true
        description: "Start date (YYYY-MM-DD)."
        example: "2024-01-01"
      - name: end
        in: query
        type: string
        required: true
        description: "End date (YYYY-MM-DD)."
        example: "2024-03-31"
      - name: sensor_group
        in: query
        type: string
        required: false
        default: VIIRS
        description: "Sensor group (VIIRS or MODIS)."
    responses:
      200:
        description: Daily fire counts within the requested date range.
      400:
        description: Missing or invalid parameters.
    """
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
    """
    Individual hotspot fire detections (JSON, capped at 50 000 records).
    ---
    tags:
      - Fires
    parameters:
      - name: lat_min
        in: query
        type: number
        required: true
      - name: lat_max
        in: query
        type: number
        required: true
      - name: lon_min
        in: query
        type: number
        required: true
      - name: lon_max
        in: query
        type: number
        required: true
      - name: start
        in: query
        type: string
        required: true
        description: "Start date (YYYY-MM-DD)."
        example: "2024-01-01"
      - name: end
        in: query
        type: string
        required: true
        description: "End date (YYYY-MM-DD)."
        example: "2024-03-31"
      - name: sensor_group
        in: query
        type: string
        required: false
        default: VIIRS
        description: "Sensor group (VIIRS or MODIS)."
      - name: satellite
        in: query
        type: string
        required: false
        description: "Specific satellite identifier."
      - name: frp_comparable
        in: query
        type: boolean
        required: false
        description: "Filter to FRP-comparable observations only."
      - name: exclude_persistent
        in: query
        type: boolean
        required: false
        description: "Exclude persistent hotspot detections."
    responses:
      200:
        description: Hotspot points with count and truncation flag.
        schema:
          type: object
          properties:
            count:
              type: integer
            truncated:
              type: boolean
            data:
              type: array
              items:
                type: object
      400:
        description: Missing or invalid parameters.
    """
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
    """
    Individual hotspot fire detections as a CSV download (full dataset, no cap).
    ---
    tags:
      - Fires
    produces:
      - text/csv
    parameters:
      - name: lat_min
        in: query
        type: number
        required: true
      - name: lat_max
        in: query
        type: number
        required: true
      - name: lon_min
        in: query
        type: number
        required: true
      - name: lon_max
        in: query
        type: number
        required: true
      - name: start
        in: query
        type: string
        required: true
        description: "Start date (YYYY-MM-DD)."
        example: "2024-01-01"
      - name: end
        in: query
        type: string
        required: true
        description: "End date (YYYY-MM-DD)."
        example: "2024-03-31"
      - name: sensor_group
        in: query
        type: string
        required: false
        default: VIIRS
      - name: satellite
        in: query
        type: string
        required: false
      - name: frp_comparable
        in: query
        type: boolean
        required: false
      - name: exclude_persistent
        in: query
        type: boolean
        required: false
    responses:
      200:
        description: CSV file attachment.
        headers:
          Content-Disposition:
            type: string
            description: "attachment; filename=hotspots.csv"
      400:
        description: Missing or invalid parameters.
    """
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
    """
    Current month near-real-time fire activity (not yet implemented).
    ---
    tags:
      - Fires
    parameters:
      - name: lat_min
        in: query
        type: number
        required: true
      - name: lat_max
        in: query
        type: number
        required: true
      - name: lon_min
        in: query
        type: number
        required: true
      - name: lon_max
        in: query
        type: number
        required: true
    responses:
      501:
        description: Not yet implemented.
    """
    return jsonify(status="not_implemented"), 501
