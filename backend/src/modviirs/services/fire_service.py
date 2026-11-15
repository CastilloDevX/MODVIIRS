import datetime as dt

from modviirs.data import queries as Q


def get_calendar(lat_min: float, lat_max: float, lon_min: float, lon_max: float, sensor_group: str):
    return Q.aoi_calendar(lat_min, lat_max, lon_min, lon_max, sensor_group).to_dicts()


def get_medians(lat_min: float, lat_max: float, lon_min: float, lon_max: float, sensor_group: str):
    return Q.aoi_monthly_medians(lat_min, lat_max, lon_min, lon_max, sensor_group).to_dicts()


def get_timeline(
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
    start: dt.date,
    end: dt.date,
    sensor_group: str,
):
    return Q.aoi_daily((lat_min, lat_max, lon_min, lon_max), start, end, sensor_group).to_dicts()


def get_points(
    lat_min: float, lat_max: float, lon_min: float, lon_max: float, start, end, **filters
):
    raise NotImplementedError


def get_current(lat_min: float, lat_max: float, lon_min: float, lon_max: float):
    raise NotImplementedError
