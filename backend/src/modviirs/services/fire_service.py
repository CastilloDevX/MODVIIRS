import datetime as dt

import polars as pl

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
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
    start: dt.date,
    end: dt.date,
    **filters,
):
    bbox = (lat_min, lat_max, lon_min, lon_max)
    df, truncated = Q.aoi_points(bbox, start, end, **filters)
    records = df.with_columns(
        pl.col("acq_date_d").dt.to_string("%Y-%m-%d")
    ).to_dicts()
    return records, truncated


def get_current(lat_min: float, lat_max: float, lon_min: float, lon_max: float):
    raise NotImplementedError
