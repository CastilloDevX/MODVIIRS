def get_predictions(lat_min: float, lat_max: float, lon_min: float, lon_max: float):
    """Return burn activity prediction for the given AOI.

    Delegates to BurnModel.predict.
    Returns a dict with at minimum: prediction, confidence interval,
    baseline used, and sensor_group.
    """
    raise NotImplementedError
