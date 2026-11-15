from flask import Blueprint, jsonify

predictions = Blueprint("predictions", __name__)


@predictions.get("/predictions")
def get_predictions():
    """GET /api/v1/predictions

    Query params: lat_min, lat_max, lon_min, lon_max
    Returns: prediction, confidence interval, baseline, sensor_group
    """
    return jsonify(status="not_implemented"), 501
