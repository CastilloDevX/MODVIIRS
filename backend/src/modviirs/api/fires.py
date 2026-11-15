import datetime as dt
import os
import tempfile

from flask import Blueprint, jsonify, request, send_file

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
        description: Monthly fire counts per year with anomaly statistics against the historical baseline.
        schema:
          type: object
          properties:
            sensor_group:
              type: string
              example: VIIRS
            data:
              type: array
              items:
                type: object
                properties:
                  year:
                    type: integer
                    description: "Observation year."
                    example: 2024
                  month:
                    type: integer
                    description: "Observation month (1–12)."
                    example: 6
                  afd:
                    type: integer
                    description: "Active Fire Days: number of cell-days with at least one hotspot detection in the AOI. Range: ≥ 0."
                    example: 143729
                  valid:
                    type: boolean
                    description: "False for known data-gap months (e.g. VIIRS 2022-07/08). Skip these cells in visualizations."
                  mean:
                    type: number
                    description: "Historical mean of afd for this month across baseline years. Range: ≥ 0."
                  std:
                    type: number
                    description: "Historical standard deviation of afd for this month. Range: ≥ 0. Use as error band width."
                  p50:
                    type: number
                    description: "Historical median of afd for this month. Range: ≥ 0. More robust than mean for skewed distributions."
                  n_base:
                    type: integer
                    description: "Number of years in the climatological baseline (typically 12–13). Lower values reduce reliability."
                  z:
                    type: number
                    description: "Z-score: (afd − mean) / std. Null when valid=false or std=0. Typical range: −3 to +3. RECOMMENDED FOR DIVERGING COLOR RAMP — negative (blue) = below average, positive (red) = above average, zero = climatological normal."
                    example: -1.06
                  pctl:
                    type: number
                    description: "Percentile rank of afd within baseline years for the same month. Range: 0–1 (null when valid=false). RECOMMENDED FOR SEQUENTIAL COLOR RAMP — 0 = lowest on record, 1 = highest on record."
                    example: 0.23
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
        description: "12 rows (one per calendar month) summarizing the historical distribution of fire activity. Use to build a seasonality reference chart: median as the center line, p25/p75 as the IQR band, min/max as the full range."
        schema:
          type: object
          properties:
            sensor_group:
              type: string
              example: VIIRS
            data:
              type: array
              items:
                type: object
                properties:
                  month:
                    type: integer
                    description: "Calendar month (1–12)."
                    example: 6
                  median:
                    type: number
                    description: "Historical median of monthly afd across baseline years. Use as the center reference line in seasonality charts."
                  p25:
                    type: number
                    description: "25th percentile of monthly afd. Use as the lower bound of the IQR band."
                  p75:
                    type: number
                    description: "75th percentile of monthly afd. Use as the upper bound of the IQR band."
                  mean:
                    type: number
                    description: "Historical mean of monthly afd."
                  std:
                    type: number
                    description: "Standard deviation of monthly afd. Use as error bar half-width."
                  min:
                    type: number
                    description: "Lowest monthly afd ever recorded in the baseline. Use as the absolute floor of the range band."
                  max:
                    type: number
                    description: "Highest monthly afd ever recorded in the baseline. Use as the absolute ceiling of the range band."
                  n_years:
                    type: integer
                    description: "Number of valid years in the baseline for this month."
                  baseline_corto:
                    type: boolean
                    description: "True when n_years < 8. Show a visual warning — statistics are less reliable."
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
        description: "Day-by-day fire activity series. Each row is one day with three complementary intensity signals: spatial spread (cells_active), detection count (n_hotspots), and radiative energy (frp_sum)."
        schema:
          type: object
          properties:
            sensor_group:
              type: string
              example: VIIRS
            start:
              type: string
              example: "2024-01-01"
            end:
              type: string
              example: "2024-03-31"
            data:
              type: array
              items:
                type: object
                properties:
                  date:
                    type: string
                    description: "Acquisition date (YYYY-MM-DD). Use as x-axis."
                    example: "2024-06-15"
                  cells_active:
                    type: integer
                    description: "Number of distinct 0.1° grid cells with fire activity. Reflects spatial spread. Range: ≥ 0."
                  n_hotspots:
                    type: integer
                    description: "Total raw hotspot detections (satellite passes × fires). Higher than cells_active when multiple satellites overpass the same cell. Range: ≥ 0."
                  frp_sum:
                    type: number
                    description: "Sum of Fire Radiative Power (MW) for all hotspots that day. Best proxy for total fire energy. Range: ≥ 0 MW. RECOMMENDED FOR LINE CHART COLOR/FILL INTENSITY."
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
        description: "Individual hotspot detections. Each row is one satellite observation of a fire. Cap: 50 000 records (check truncated flag). For the full dataset use /fires/points.csv."
        schema:
          type: object
          properties:
            count:
              type: integer
              description: "Number of records returned (≤ 50 000)."
            truncated:
              type: boolean
              description: "True when the result was cut at 50 000 rows. Use /fires/points.csv to get the full dataset."
            data:
              type: array
              items:
                type: object
                properties:
                  latitude:
                    type: number
                    description: "Hotspot latitude (−90 to 90). Use as map Y coordinate."
                  longitude:
                    type: number
                    description: "Hotspot longitude (−180 to 180). Use as map X coordinate."
                  acq_date_d:
                    type: string
                    description: "Acquisition date (YYYY-MM-DD). Use for temporal filtering or animation."
                    example: "2024-06-15"
                  frp:
                    type: number
                    description: "Fire Radiative Power in MW. Range: ≥ 0. RECOMMENDED FOR POINT COLOR RAMP — higher values = more intense fire. Suggested scale: 0–500 MW with logarithmic normalization."
                  conf_class:
                    type: string
                    description: "Detection confidence class. Values: 'nominal' | 'high'. Low-confidence detections are pre-filtered out. Use for point opacity or size (high = larger/more opaque)."
                    example: nominal
                  daynight:
                    type: string
                    description: "Whether the detection was during day or night. Values: 'D' | 'N'. Use for icon variant."
                    example: D
                  is_persistent:
                    type: boolean
                    description: "True for hotspots at known persistent industrial or volcanic sources (oil flares, volcanoes, etc.). Use a distinct shape or color to differentiate from active wildfires."
                  frp_comparable:
                    type: boolean
                    description: "True when FRP ≥ 15 MW, the threshold where MODIS and VIIRS FRP values are comparable. Use to filter when comparing sensors."
                  bright_main:
                    type: number
                    description: "Brightness temperature of the main channel (Kelvin). Secondary intensity signal; prefer frp for color ramps."
                  satellite:
                    type: string
                    description: "Satellite identifier. VIIRS examples: 'N20' (NOAA-20), 'N21' (NOAA-21). MODIS examples: 'Terra', 'Aqua'."
                    example: N20
                  sensor_group:
                    type: string
                    description: "Sensor family. Values: 'VIIRS' | 'MODIS'."
                    example: VIIRS
                  year:
                    type: integer
                  month:
                    type: integer
                  res_m:
                    type: integer
                    description: "Sensor spatial resolution in metres. VIIRS: 375 m, MODIS: 1000 m."
                  version:
                    type: string
                    description: "FIRMS data collection version."
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
    The sensor_group column (MODIS/VIIRS) is not included.
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
    # The sensor family column (MODIS/VIIRS) is dropped from the export. The file is
    # streamed to disk, not built in memory: a wide area can have millions of rows.
    lf = Q.aoi_points_lazy(bbox, start, end, **filters).drop("sensor_group")
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    try:
        lf.sink_csv(path)
    except Exception:
        os.remove(path)
        raise
    response = send_file(
        path, mimetype="text/csv", as_attachment=True, download_name="hotspots.csv"
    )
    response.call_on_close(lambda: os.path.exists(path) and os.remove(path))
    return response


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
