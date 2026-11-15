from flask import Blueprint, jsonify

predictions = Blueprint("predictions", __name__)


@predictions.get("/predictions")
def get_predictions():
    """
    Burn activity anomaly prediction for an area of interest (not yet implemented).
    ---
    tags:
      - Predictions
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
      200:
        description: Prediction, confidence interval, and baseline.
      501:
        description: Not yet implemented.
    """
    return jsonify(status="not_implemented"), 501
