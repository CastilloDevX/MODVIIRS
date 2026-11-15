# Paste predictor code here.
#
# BurnModel wraps the trained model from build_training_dataset.py.
# Input features are built from activity_grid.parquet + cell_climatology.parquet.
# Primary target: afd_z (standardized anomaly, comparable across sensors).


class BurnModel:
    """Burn activity predictor for a given AOI."""

    def predict(self, lat_min: float, lat_max: float, lon_min: float, lon_max: float):
        """Return prediction for the AOI defined by the bounding box.

        Returns a dict with at minimum: prediction, confidence interval,
        baseline used, and sensor_group.
        """
        raise NotImplementedError
