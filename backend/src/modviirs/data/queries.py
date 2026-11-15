"""
queries.py — funciones de consulta por AOI para el backend Flask.

Adaptado de harmonize_firms.py y aoi_queries.py (NASA2026/Data/armonizacion/).
No importa harmonize_firms; todas las constantes y helpers están inlineadas aquí.
La ruta a los parquet es relativa a este archivo (backend/data/).
"""
import datetime as dt
import math
from pathlib import Path

import polars as pl

# backend/src/modviirs/data/queries.py  →  parents[3] = backend/
_DATA_DIR = Path(__file__).resolve().parents[3] / "data"

# --- constantes (de harmonize_firms.py) ---
GRID_DEG = 0.1
PERSIST_GRID_DEG = 0.01
CONF_KEEP = ["nominal", "high"]
FRP_COMPARABLE_MW = 15.0
BASELINE_MODIS = (2001, 2024)
BASELINE_VIIRS = (2012, 2024)
EXCLUDE_YM = {
    ("MODIS", 2022, 4),
    ("VIIRS", 2022, 7),
    ("VIIRS", 2022, 8),
}
SOURCES_VIIRS_NRT = ["VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"]
API_MAX_DAYS = 5


# --- helpers (de harmonize_firms.py) ---

def _collect(lf):
    """Colecta LazyFrame en streaming; compatible con polars <2.0 y >=2.0."""
    try:
        return lf.collect(engine="streaming")
    except TypeError:
        try:
            return lf.collect(streaming=True)
        except Exception:
            return lf.collect()


def _drop_gap_months(df):
    """Excluye meses con huecos de datos conocidos (sesgan la climatología)."""
    if not EXCLUDE_YM:
        return df
    keys = [f"{s}-{y}-{m}" for (s, y, m) in EXCLUDE_YM]
    k = (
        pl.col("sensor_group")
        + "-"
        + pl.col("year").cast(pl.Utf8)
        + "-"
        + pl.col("month").cast(pl.Utf8)
    )
    return df.with_columns(k.alias("_k")).filter(~pl.col("_k").is_in(keys)).drop("_k")


# --- consulta por AOI (de harmonize_firms.py) ---

def aoi_cell_range(lat_min, lat_max, lon_min, lon_max):
    """Índices de celda del AOI con la misma fórmula que el pipeline (floor(valor/GRID_DEG)).
    int() truncaría hacia 0 y fallaría con coordenadas negativas (México, Brasil, Australia…)
    """
    def f(v):
        return int(math.floor(v / GRID_DEG))

    return f(lat_min), f(lat_max), f(lon_min), f(lon_max)


def aoi_calendar(lat_min, lat_max, lon_min, lon_max, sensor_group, baseline=None):
    """Serie mensual del AOI + anomalía contra su propia historia, con ceros explícitos.
    Meses válidos = meses con datos del sensor (cualquier país) en activity_grid.
    Un mes válido sin fuego en el AOI vale 0.
    Los meses de hueco conocido (EXCLUDE_YM) salen con valid=False, z/pctl nulos.
    Columnas: year, month, afd, valid, mean, std, p50, n_base, z, pctl.
    """
    g = pl.read_parquet(_DATA_DIR / "activity_grid.parquet")
    cyl, cyh, cxl, cxh = aoi_cell_range(lat_min, lat_max, lon_min, lon_max)
    gs = g.filter(pl.col("sensor_group") == sensor_group)
    present = (
        gs.select(["year", "month"])
        .unique()
        .with_columns(
            pl.struct(["year", "month"])
            .map_elements(
                lambda r: (sensor_group, r["year"], r["month"]) not in EXCLUDE_YM,
                return_dtype=pl.Boolean,
            )
            .alias("valid")
        )
    )
    sub = gs.filter(
        pl.col("cy").is_between(cyl, cyh) & pl.col("cx").is_between(cxl, cxh)
    )
    sums = sub.group_by(["year", "month"]).agg(
        pl.col("active_fire_days").sum().alias("afd")
    )
    ser = (
        present.join(sums, on=["year", "month"], how="left")
        .with_columns(pl.col("afd").fill_null(0))
        .sort(["year", "month"])
    )
    lo, hi = baseline or (BASELINE_VIIRS if sensor_group == "VIIRS" else BASELINE_MODIS)
    base = ser.filter(pl.col("valid") & pl.col("year").is_between(lo, hi))
    clim = base.group_by("month").agg(
        [
            pl.col("afd").mean().alias("mean"),
            pl.col("afd").std().alias("std"),
            pl.col("afd").median().alias("p50"),
            pl.len().alias("n_base"),
        ]
    )
    bv = base.select(["month", pl.col("afd").alias("_b")])
    pct = (
        ser.join(bv, on="month")
        .group_by(["year", "month"])
        .agg((pl.col("_b") <= pl.col("afd")).mean().alias("pctl"))
    )
    out = (
        ser.join(clim, on="month", how="left")
        .join(pct, on=["year", "month"], how="left")
        .with_columns(
            [
                pl.when(pl.col("valid") & (pl.col("std") > 0))
                .then((pl.col("afd") - pl.col("mean")) / pl.col("std"))
                .otherwise(None)
                .alias("z"),
                pl.when(pl.col("valid")).then(pl.col("pctl")).otherwise(None).alias("pctl"),
            ]
        )
        .sort(["year", "month"])
    )
    return out


# --- consultas de aoi_queries.py (OUT → _DATA_DIR) ---

def aoi_monthly_medians(lat_min, lat_max, lon_min, lon_max, sensor_group="VIIRS", baseline=None):
    """12 filas (una por mes del año) con la distribución histórica del AOI.
    Para cada mes: suma active_fire_days de las celdas del AOI en cada año del baseline
    (ceros incluidos; meses de hueco excluidos) y resume ese conjunto de años.
    Columnas: month, median, p25, p75, mean, std, min, max, n_years, baseline_corto.
    """
    lo, hi = baseline or (BASELINE_VIIRS if sensor_group == "VIIRS" else BASELINE_MODIS)
    cal = aoi_calendar(lat_min, lat_max, lon_min, lon_max, sensor_group, baseline=(lo, hi))
    b = cal.filter(pl.col("valid") & pl.col("year").is_between(lo, hi))
    a = pl.col("afd").cast(pl.Float64)
    return (
        b.group_by("month")
        .agg(
            [
                a.median().alias("median"),
                a.quantile(0.25, "linear").alias("p25"),
                a.quantile(0.75, "linear").alias("p75"),
                a.mean().alias("mean"),
                a.std().alias("std"),
                a.min().alias("min"),
                a.max().alias("max"),
                pl.len().alias("n_years"),
            ]
        )
        .with_columns((pl.col("n_years") < 8).alias("baseline_corto"))
        .sort("month")
    )


def aoi_daily(bbox_latlon, start, end, sensor_group="VIIRS"):
    """Serie diaria del AOI entre start y end.
    bbox_latlon=(lat_min, lat_max, lon_min, lon_max).
    Columnas: date, cells_active, n_hotspots, frp_sum.
    """
    cyl, cyh, cxl, cxh = aoi_cell_range(*bbox_latlon)
    d = pl.scan_parquet(_DATA_DIR / "activity_daily.parquet").filter(
        (pl.col("sensor_group") == sensor_group)
        & pl.col("cy").is_between(cyl, cyh)
        & pl.col("cx").is_between(cxl, cxh)
        & pl.col("acq_date_d").is_between(start, end)
    )
    cells = (
        d.select(["cy", "cx", "acq_date_d"])
        .unique()
        .group_by("acq_date_d")
        .agg(pl.len().alias("cells_active"))
    )
    tot = d.group_by("acq_date_d").agg(
        [pl.col("n_hotspots").sum(), pl.col("frp_sum").sum()]
    )
    return _collect(
        cells.join(tot, on="acq_date_d").sort("acq_date_d")
    ).rename({"acq_date_d": "date"})


def _valid_years(sensor_group, month, lo, hi):
    g = pl.scan_parquet(_DATA_DIR / "activity_grid.parquet").filter(
        (pl.col("sensor_group") == sensor_group)
        & (pl.col("month") == month)
        & pl.col("year").is_between(lo, hi)
    ).select("year").unique()
    ys = sorted(_collect(g)["year"].to_list())
    return [y for y in ys if (sensor_group, y, month) not in EXCLUDE_YM]


def aoi_mtd_baseline(bbox_latlon, month, day, sensor_group="VIIRS", baseline=None):
    """Celda-días con fuego del AOI en el tramo [día 1 .. día day] del month, por año."""
    lo, hi = baseline or (BASELINE_VIIRS if sensor_group == "VIIRS" else BASELINE_MODIS)
    cyl, cyh, cxl, cxh = aoi_cell_range(*bbox_latlon)
    years = _valid_years(sensor_group, month, lo, hi)
    d = (
        pl.scan_parquet(_DATA_DIR / "activity_daily.parquet")
        .filter(
            (pl.col("sensor_group") == sensor_group)
            & pl.col("cy").is_between(cyl, cyh)
            & pl.col("cx").is_between(cxl, cxh)
            & (pl.col("acq_date_d").dt.month() == month)
            & (pl.col("acq_date_d").dt.day() <= day)
            & pl.col("acq_date_d").dt.year().is_in(years)
        )
        .select(["cy", "cx", "acq_date_d"])
        .unique()
        .group_by(pl.col("acq_date_d").dt.year().alias("year"))
        .agg(pl.len().alias("afd_mtd"))
    )
    got = _collect(d)
    full = pl.DataFrame({"year": years}, schema={"year": pl.Int32})
    return (
        full.join(got.with_columns(pl.col("year").cast(pl.Int32)), on="year", how="left")
        .with_columns(pl.col("afd_mtd").fill_null(0))
        .sort("year")
    )


def aoi_mtd_compare(bbox_latlon, nrt_norm: pl.DataFrame, as_of=None, baseline=None):
    """Compara el mes en curso (NRT normalizado, VIIRS) contra la historia VIIRS del mismo tramo."""
    as_of = as_of or (dt.datetime.now(dt.UTC).date() - dt.timedelta(days=1))
    cyl, cyh, cxl, cxh = aoi_cell_range(*bbox_latlon)
    cur = (
        nrt_norm.filter(
            (pl.col("sensor_group") == "VIIRS")
            & ~pl.col("is_persistent")
            & pl.col("cy").is_between(cyl, cyh)
            & pl.col("cx").is_between(cxl, cxh)
            & (pl.col("acq_date_d").dt.year() == as_of.year)
            & (pl.col("acq_date_d").dt.month() == as_of.month)
            & (pl.col("acq_date_d").dt.day() <= as_of.day)
        )
        .select(["cy", "cx", "acq_date_d"])
        .unique()
        .height
    )
    base = aoi_mtd_baseline(bbox_latlon, as_of.month, as_of.day, "VIIRS", baseline)
    v = base["afd_mtd"].cast(pl.Float64)
    n = base.height
    bl = baseline or BASELINE_VIIRS
    res = {
        "as_of": as_of.isoformat(),
        "month": as_of.month,
        "days_covered": as_of.day,
        "afd_mtd": cur,
        "n_years_baseline": n,
        "preliminary": True,
        "baseline": f"VIIRS {bl[0]}-{bl[1]}",
        "sources": SOURCES_VIIRS_NRT,
    }
    if n == 0:
        return {**res, "status": "sin_baseline"}
    std = v.std() if n > 1 else None
    med = v.median()
    res.update(
        {
            "status": "ok" if n >= 8 else "baseline_corto",
            "median": med,
            "p25": v.quantile(0.25, "linear"),
            "p75": v.quantile(0.75, "linear"),
            "min": v.min(),
            "max": v.max(),
            "mean": v.mean(),
            "std": std,
            "ratio_to_median": (cur / med) if med and med > 0 else None,
            "pctl": float((v <= cur).sum()) / n,
            "z": ((cur - v.mean()) / std) if std and std > 0 else None,
        }
    )
    return res


def normalize_nrt(raw: pl.DataFrame) -> pl.DataFrame:
    """CSV crudo VIIRS NRT → esquema de hotspots_harmonized.
    Reglas idénticas al pipeline: confidence l/n/h → low/nominal/high, se descartan 'low';
    celdas 0.1 con floor(); marca de fuentes persistentes; frp_comparable; sin duplicados.
    """
    if raw.height == 0:
        return raw
    c = pl.col("confidence").cast(pl.Utf8).str.to_lowercase()
    conf = (
        pl.when(c == "h").then(pl.lit("high"))
        .when(c == "n").then(pl.lit("nominal"))
        .otherwise(pl.lit("low"))
    )
    lat = pl.col("latitude").cast(pl.Float64)
    lon = pl.col("longitude").cast(pl.Float64)
    df = (
        raw.unique(subset=["latitude", "longitude", "acq_date", "acq_time", "satellite"])
        .with_columns(
            [
                pl.col("acq_date").cast(pl.Utf8)
                .str.strptime(pl.Date, strict=False).alias("acq_date_d"),
                conf.alias("conf_class"),
                lat.alias("latitude"),
                lon.alias("longitude"),
                pl.col("frp").cast(pl.Float64, strict=False).alias("frp"),
                pl.col("bright_ti4").cast(pl.Float64, strict=False).alias("bright_main"),
                pl.col("satellite").cast(pl.Utf8).alias("satellite"),
                pl.col("daynight").cast(pl.Utf8).alias("daynight"),
                pl.col("version").cast(pl.Utf8, strict=False).alias("version"),
                pl.lit("VIIRS").alias("sensor_group"),
                pl.lit(375).alias("res_m"),
                (lat / GRID_DEG).floor().cast(pl.Int32).alias("cy"),
                (lon / GRID_DEG).floor().cast(pl.Int32).alias("cx"),
                (lat / PERSIST_GRID_DEG).floor().cast(pl.Int64).alias("py"),
                (lon / PERSIST_GRID_DEG).floor().cast(pl.Int64).alias("px"),
            ]
        )
        .filter(pl.col("conf_class").is_in(CONF_KEEP))
    )
    mask = pl.read_parquet(_DATA_DIR / "persistent_mask.parquet").select(
        ["py", "px", "is_persistent"]
    )
    df = (
        df.join(mask, on=["py", "px"], how="left")
        .with_columns(
            [
                pl.col("is_persistent").fill_null(False),
                (pl.col("frp") >= FRP_COMPARABLE_MW).alias("frp_comparable"),
                pl.col("acq_date_d").dt.year().alias("year"),
                pl.col("acq_date_d").dt.month().cast(pl.Int8).alias("month"),
            ]
        )
    )
    return df.select(
        [
            "latitude", "longitude", "acq_date_d", "year", "month", "sensor_group",
            "satellite", "res_m", "conf_class", "frp", "daynight", "bright_main", "version",
            "is_persistent", "frp_comparable", "cy", "cx",
        ]
    )


def nrt_request_plan(bbox, start, end, sources=None, max_days=API_MAX_DAYS):
    """bbox=(west, south, east, north); start/end: datetime.date (inclusive).
    Devuelve [{source, area, day_range, date, path}] sin MAP_KEY.
    """
    w, s, e, n = bbox
    area = f"{w},{s},{e},{n}"
    plan, cur = [], start
    while cur <= end:
        span = min(max_days, (end - cur).days + 1)
        for src in (sources or SOURCES_VIIRS_NRT):
            plan.append(
                {
                    "source": src,
                    "area": area,
                    "day_range": span,
                    "date": cur.isoformat(),
                    "path": f"/api/area/csv/{{MAP_KEY}}/{src}/{area}/{span}/{cur.isoformat()}",
                }
            )
        cur += dt.timedelta(days=span)
    return plan
