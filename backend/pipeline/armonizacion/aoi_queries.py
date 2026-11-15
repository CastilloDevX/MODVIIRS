"""
aoi_queries.py -- funciones de consulta por AOI para el backend (VIIRS vs VIIRS).

Usa las salidas de harmonize_firms.py (misma carpeta). Funciones puras, sin red:
  build_activity_daily()      one-off: genera activity_daily.parquet (celda x dia) desde hotspots_harmonized
  nrt_request_plan()          lista de requests a la Area API (solo VIIRS, ventanas de <=5 dias)
  normalize_nrt()             CSV crudo de la API -> esquema armonizado (mismas reglas que el pipeline)
  aoi_monthly_medians()       medianas mensuales historicas del AOI (12 filas)
  aoi_daily()                 serie diaria del AOI (timeline diario)
  aoi_mtd_baseline()          acumulado del mes a la fecha, por anio, en el baseline (VIIRS)
  aoi_mtd_compare()           mes actual (NRT) vs distribucion historica del mismo tramo del mes

Metrica: "celda-dias con fuego" = nº de pares (celda 0.1, dia) con >=1 hotspot en el AOI.
Sumada sobre el mes equivale a la suma de active_fire_days del aoi_calendar().

Uso:
  python aoi_queries.py build-daily            # genera activity_daily.parquet (una vez, tras harmonize_firms.py)
  python aoi_queries.py rebuild-climatology    # recalcula cell_climatology.parquet CON ceros desde activity_grid
"""
import datetime as dt
import math
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harmonize_firms as H   # reutiliza constantes y aoi_calendar (una sola fuente de verdad)

OUT = H.OUT
GRID_DEG, PERSIST_GRID_DEG = H.GRID_DEG, H.PERSIST_GRID_DEG
SOURCES_VIIRS_NRT = ["VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"]   # S-NPP cesó el 2-nov-2026
API_MAX_DAYS = 5
aoi_cell_range = H.aoi_cell_range
aoi_calendar = H.aoi_calendar


# ---------------- activity_daily (celda x dia) ----------------
def build_activity_daily():
    """Una fila por celda 0.1 x dia x sensor_group x pais; sin fuentes persistentes. Alimenta
       el timeline diario y el acumulado del mes a la fecha."""
    pts = pl.scan_parquet(OUT / "hotspots_harmonized.parquet").filter(~pl.col("is_persistent"))
    d = (pts.group_by(["cy", "cx", "acq_date_d", "sensor_group", "country"])
            .agg([pl.len().alias("n_hotspots"), pl.col("frp").sum().alias("frp_sum")]))
    d = H._collect(d)
    d.write_parquet(OUT / "activity_daily.parquet")
    print(f"-> activity_daily.parquet ({d.height:,} filas)")
    return d


# ---------------- Area API (solo VIIRS) ----------------
def nrt_request_plan(bbox, start, end, sources=None, max_days=API_MAX_DAYS):
    """bbox=(west, south, east, north); start/end: datetime.date (inclusive).
       Devuelve [{source, area, day_range, date, path}] SIN MAP_KEY (la llave la inyecta el backend):
       path = /api/area/csv/{MAP_KEY}/{source}/{w,s,e,n}/{day_range}/{date}  (date = YYYY-MM-DD)."""
    w, s, e, n = bbox
    area = f"{w},{s},{e},{n}"
    plan, cur = [], start
    while cur <= end:
        span = min(max_days, (end - cur).days + 1)
        for src in (sources or SOURCES_VIIRS_NRT):
            plan.append({"source": src, "area": area, "day_range": span, "date": cur.isoformat(),
                         "path": f"/api/area/csv/{{MAP_KEY}}/{src}/{area}/{span}/{cur.isoformat()}"})
        cur += dt.timedelta(days=span)
    return plan


def normalize_nrt(raw: pl.DataFrame) -> pl.DataFrame:
    """CSV crudo VIIRS NRT -> esquema de hotspots_harmonized (menos country/type, que NRT no trae).
       Reglas identicas al pipeline: confidence l/n/h -> low/nominal/high y se descartan 'low';
       celdas 0.1 con la misma formula; marca de fuentes persistentes; frp_comparable; sin duplicados."""
    if raw.height == 0:
        return raw
    c = pl.col("confidence").cast(pl.Utf8).str.to_lowercase()
    conf = (pl.when(c == "h").then(pl.lit("high")).when(c == "n").then(pl.lit("nominal"))
              .otherwise(pl.lit("low")))
    lat, lon = pl.col("latitude").cast(pl.Float64), pl.col("longitude").cast(pl.Float64)
    df = (raw.unique(subset=["latitude", "longitude", "acq_date", "acq_time", "satellite"])
             .with_columns([
                 pl.col("acq_date").cast(pl.Utf8).str.strptime(pl.Date, strict=False).alias("acq_date_d"),
                 conf.alias("conf_class"),
                 lat.alias("latitude"), lon.alias("longitude"),
                 pl.col("frp").cast(pl.Float64, strict=False).alias("frp"),
                 pl.col("bright_ti4").cast(pl.Float64, strict=False).alias("bright_main"),
                 pl.col("satellite").cast(pl.Utf8).alias("satellite"),
                 pl.col("daynight").cast(pl.Utf8).alias("daynight"),
                 pl.col("version").cast(pl.Utf8, strict=False).alias("version"),
                 pl.lit("VIIRS").alias("sensor_group"), pl.lit(375).alias("res_m"),
                 (lat / GRID_DEG).floor().cast(pl.Int32).alias("cy"),
                 (lon / GRID_DEG).floor().cast(pl.Int32).alias("cx"),
                 (lat / PERSIST_GRID_DEG).floor().cast(pl.Int64).alias("py"),
                 (lon / PERSIST_GRID_DEG).floor().cast(pl.Int64).alias("px"),
             ])
             .filter(pl.col("conf_class").is_in(H.CONF_KEEP)))
    mask = pl.read_parquet(OUT / "persistent_mask.parquet").select(["py", "px", "is_persistent"])
    df = (df.join(mask, on=["py", "px"], how="left")
            .with_columns([pl.col("is_persistent").fill_null(False),
                           (pl.col("frp") >= H.FRP_COMPARABLE_MW).alias("frp_comparable"),
                           pl.col("acq_date_d").dt.year().alias("year"),
                           pl.col("acq_date_d").dt.month().cast(pl.Int8).alias("month")]))
    return df.select(["latitude", "longitude", "acq_date_d", "year", "month", "sensor_group",
                      "satellite", "res_m", "conf_class", "frp", "daynight", "bright_main", "version",
                      "is_persistent", "frp_comparable", "cy", "cx"])



# ---------------- medianas mensuales historicas del AOI ----------------
def aoi_monthly_medians(lat_min, lat_max, lon_min, lon_max, sensor_group="VIIRS", baseline=None):
    """12 filas (una por mes del anio) con la distribucion historica del AOI.
       Para cada mes: se suma active_fire_days de las celdas del AOI en cada anio del baseline
       (ceros incluidos; meses de hueco excluidos) y se resume ese conjunto de anios.
       Columnas: month, median, p25, p75, mean, std, min, max, n_years, baseline_corto."""
    lo, hi = baseline or (H.BASELINE_VIIRS if sensor_group == "VIIRS" else H.BASELINE_MODIS)
    cal = aoi_calendar(lat_min, lat_max, lon_min, lon_max, sensor_group, baseline=(lo, hi))
    b = cal.filter(pl.col("valid") & pl.col("year").is_between(lo, hi))
    a = pl.col("afd").cast(pl.Float64)
    return (b.group_by("month")
              .agg([a.median().alias("median"),
                    a.quantile(0.25, "linear").alias("p25"), a.quantile(0.75, "linear").alias("p75"),
                    a.mean().alias("mean"), a.std().alias("std"), a.min().alias("min"), a.max().alias("max"),
                    pl.len().alias("n_years")])
              .with_columns((pl.col("n_years") < 8).alias("baseline_corto"))
              .sort("month"))

# ---------------- timeline diario ----------------
def aoi_daily(bbox_latlon, start, end, sensor_group="VIIRS"):
    """bbox_latlon=(lat_min, lat_max, lon_min, lon_max). Devuelve date, cells_active, n_hotspots, frp_sum."""
    cyl, cyh, cxl, cxh = aoi_cell_range(*bbox_latlon)
    d = pl.scan_parquet(OUT / "activity_daily.parquet").filter(
        (pl.col("sensor_group") == sensor_group) & pl.col("cy").is_between(cyl, cyh)
        & pl.col("cx").is_between(cxl, cxh) & pl.col("acq_date_d").is_between(start, end))
    cells = d.select(["cy", "cx", "acq_date_d"]).unique().group_by("acq_date_d").agg(
        pl.len().alias("cells_active"))
    tot = d.group_by("acq_date_d").agg([pl.col("n_hotspots").sum(), pl.col("frp_sum").sum()])
    return H._collect(cells.join(tot, on="acq_date_d").sort("acq_date_d")).rename({"acq_date_d": "date"})


# ---------------- mes a la fecha vs historia (VIIRS contra VIIRS) ----------------
def _valid_years(sensor_group, month, lo, hi):
    g = pl.scan_parquet(OUT / "activity_grid.parquet").filter(
        (pl.col("sensor_group") == sensor_group) & (pl.col("month") == month)
        & pl.col("year").is_between(lo, hi)).select("year").unique()
    ys = sorted(H._collect(g)["year"].to_list())
    return [y for y in ys if (sensor_group, y, month) not in H.EXCLUDE_YM]


def aoi_mtd_baseline(bbox_latlon, month, day, sensor_group="VIIRS", baseline=None):
    """Celda-dias con fuego del AOI en el tramo [dia 1 .. dia `day`] del `month`, por anio del baseline.
       Anios validos sin fuego valen 0; anios sin datos del sensor ese mes se omiten."""
    lo, hi = baseline or (H.BASELINE_VIIRS if sensor_group == "VIIRS" else H.BASELINE_MODIS)
    cyl, cyh, cxl, cxh = aoi_cell_range(*bbox_latlon)
    years = _valid_years(sensor_group, month, lo, hi)
    d = (pl.scan_parquet(OUT / "activity_daily.parquet")
           .filter((pl.col("sensor_group") == sensor_group) & pl.col("cy").is_between(cyl, cyh)
                   & pl.col("cx").is_between(cxl, cxh)
                   & (pl.col("acq_date_d").dt.month() == month) & (pl.col("acq_date_d").dt.day() <= day)
                   & pl.col("acq_date_d").dt.year().is_in(years))
           .select(["cy", "cx", "acq_date_d"]).unique()
           .group_by(pl.col("acq_date_d").dt.year().alias("year")).agg(pl.len().alias("afd_mtd")))
    got = H._collect(d)
    full = pl.DataFrame({"year": years}, schema={"year": pl.Int32})
    return full.join(got.with_columns(pl.col("year").cast(pl.Int32)), on="year", how="left") \
               .with_columns(pl.col("afd_mtd").fill_null(0)).sort("year")


def aoi_mtd_compare(bbox_latlon, nrt_norm: pl.DataFrame, as_of=None, baseline=None):
    """Compara el mes en curso (NRT normalizado, VIIRS) contra la historia VIIRS del mismo tramo.
       as_of: ultima fecha COMPLETA (default: ayer UTC). Compara el mes de as_of, del dia 1 a as_of.day."""
    as_of = as_of or (dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=1))
    cyl, cyh, cxl, cxh = aoi_cell_range(*bbox_latlon)
    cur = (nrt_norm.filter((pl.col("sensor_group") == "VIIRS") & ~pl.col("is_persistent")
                           & pl.col("cy").is_between(cyl, cyh) & pl.col("cx").is_between(cxl, cxh)
                           & (pl.col("acq_date_d").dt.year() == as_of.year)
                           & (pl.col("acq_date_d").dt.month() == as_of.month)
                           & (pl.col("acq_date_d").dt.day() <= as_of.day))
                   .select(["cy", "cx", "acq_date_d"]).unique().height)
    base = aoi_mtd_baseline(bbox_latlon, as_of.month, as_of.day, "VIIRS", baseline)
    v = base["afd_mtd"].cast(pl.Float64)
    n = base.height
    res = {"as_of": as_of.isoformat(), "month": as_of.month, "days_covered": as_of.day,
           "afd_mtd": cur, "n_years_baseline": n, "preliminary": True,
           "baseline": f"VIIRS {(baseline or H.BASELINE_VIIRS)[0]}-{(baseline or H.BASELINE_VIIRS)[1]}",
           "sources": SOURCES_VIIRS_NRT}
    if n == 0:
        return {**res, "status": "sin_baseline"}
    std = v.std() if n > 1 else None
    med = v.median()
    res.update({
        "status": "ok" if n >= 8 else "baseline_corto",
        "median": med, "p25": v.quantile(0.25, "linear"), "p75": v.quantile(0.75, "linear"),
        "min": v.min(), "max": v.max(), "mean": v.mean(), "std": std,
        "ratio_to_median": (cur / med) if med and med > 0 else None,
        "pctl": float((v <= cur).sum()) / n,
        "z": ((cur - v.mean()) / std) if std and std > 0 else None})
    return res


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "build-daily":
        build_activity_daily()
    elif len(sys.argv) > 1 and sys.argv[1] == "rebuild-climatology":
        H.build_cell_climatology(pl.read_parquet(OUT / "activity_grid.parquet"))
    else:
        print(__doc__)
