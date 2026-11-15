# =========================================================
# harmonize_firms.py  —  Armonizacion MODIS-VIIRS FIRMS
# Lee los parquet crudos por pais/anio y genera el dataset
# armonizado de dos capas (puntos + actividad) + validacion.
# Documentacion de las salidas: armonizacion/README.md (ya no se regenera desde aqui).
# =========================================================
import math
import os
from pathlib import Path
import polars as pl

# ---------------- ETAPA 0: CONFIG ----------------
# El script vive en Data/armonizacion/ y se ubica por __file__ (sin rutas absolutas):
# lee de ../parquet y escribe en su propia carpeta. Overridable con FIRMS_RAW / FIRMS_OUT.
HERE     = Path(__file__).resolve().parent                       # .../Data/armonizacion
RAW_ROOT = Path(os.environ.get("FIRMS_RAW", HERE.parent / "parquet"))
OUT      = Path(os.environ.get("FIRMS_OUT", HERE))
OUT.mkdir(parents=True, exist_ok=True)

SMOKE        = os.environ.get("FIRMS_SMOKE", "0") == "1"   # "1" = solo SMOKE_FILTER
SMOKE_FILTER = os.environ.get("FIRMS_SMOKE_COUNTRY", "Mexico")

GRID_DEG           = 0.1       # rejilla de la capa de actividad
PERSIST_GRID_DEG   = 0.01      # rejilla fina para fuentes persistentes
PERSIST_MIN_MONTHS = 60        # celda 0.01 con fuego en >=60 meses distintos -> persistente
OVERLAP            = (2012, 2024)   # solape MODIS/VIIRS (2025 fuera por deriva de Aqua)
BASELINE_MODIS     = (2001, 2024)   # climatologia MODIS
BASELINE_VIIRS     = (2012, 2024)   # climatologia VIIRS
CONF_KEEP          = ["nominal", "high"]   # regla n+h; se descarta 'low'
FRP_COMPARABLE_MW  = 15.0      # umbral del toggle "comparable entre sensores"

# Insight EDA: excluir meses con huecos de datos al CALIBRAR (sesgan las razones).
# (sensor_group, year, month). Verificados en el EDA; amplia la lista si detectas mas.
EXCLUDE_YM = {
    ("MODIS", 2022, 4),   # hueco Aqua abr-2022 (~16 dias)
    ("VIIRS", 2022, 7),   # hueco S-NPP jul-2022
    ("VIIRS", 2022, 8),   # hueco S-NPP ago-2022
}

INSTRUMENTS = {
    "modis":       {"glob": "modis",       "res_m": 1000, "group": "MODIS"},
    "viirs-snpp":  {"glob": "viirs-snpp",  "res_m": 375,  "group": "VIIRS"},
    "viirs-jpss1": {"glob": "viirs-jpss1", "res_m": 375,  "group": "VIIRS"},
}
# satellite (en los datos) -> plataforma legible
PLATFORM = {"Terra": "Terra", "Aqua": "Aqua", "N": "Suomi-NPP", "N20": "NOAA-20", "N21": "NOAA-21"}

RE_YEAR    = r"[\\/](\d{4})[\\/]"
RE_COUNTRY = r"[\\/]\d{4}[\\/]([^\\/]+)\.parquet$"

def _drop_gap_months(df):
    """Insight EDA: fuera los meses con huecos de datos al calibrar/climatologia."""
    if not EXCLUDE_YM:
        return df
    keys = [f"{s}-{y}-{m}" for (s, y, m) in EXCLUDE_YM]
    k = (pl.col("sensor_group") + "-" + pl.col("year").cast(pl.Utf8) + "-" + pl.col("month").cast(pl.Utf8))
    return df.with_columns(k.alias("_k")).filter(~pl.col("_k").is_in(keys)).drop("_k")

def _collect(lf):
    """Colecta en streaming, compatible con polars <2.0 y >=2.0."""
    try:
        return lf.collect(engine="streaming")
    except TypeError:
        try:
            return lf.collect(streaming=True)
        except Exception:
            return lf.collect()

# ---------------- ETAPA 1: INGESTA + ESQUEMA UNIFICADO ----------------
def _files(inst_key):
    base = RAW_ROOT / INSTRUMENTS[inst_key]["glob"]
    fs = [str(p) for p in base.glob("**/*.parquet")]
    if SMOKE:
        fs = [f for f in fs if SMOKE_FILTER.lower() in Path(f).name.lower()]
    return fs

def load_instrument(inst_key):
    spec = INSTRUMENTS[inst_key]
    files = _files(inst_key)
    if not files:
        print(f"  [aviso] sin parquet para {inst_key}")
        return None
    lf = pl.scan_parquet(files, include_file_paths="src_path")
    bright = "bright_ti4" if spec["group"] == "VIIRS" else "brightness"

    if spec["group"] == "MODIS":
        confnum = pl.col("confidence").cast(pl.Float64, strict=False)
        conf_class = (pl.when(confnum >= 80).then(pl.lit("high"))
                        .when(confnum >= 30).then(pl.lit("nominal"))
                        .otherwise(pl.lit("low")))
    else:
        c = pl.col("confidence").cast(pl.Utf8).str.to_lowercase()
        conf_class = (pl.when(c == "h").then(pl.lit("high"))
                        .when(c == "n").then(pl.lit("nominal"))
                        .otherwise(pl.lit("low")))

    lf = lf.with_columns([
        pl.lit(spec["group"]).alias("sensor_group"),
        pl.lit(spec["res_m"]).alias("res_m"),
        pl.col("src_path").str.extract(RE_YEAR, 1).cast(pl.Int32).alias("year"),
        pl.col("src_path").str.extract(RE_COUNTRY, 1).alias("country"),
        pl.col(bright).cast(pl.Float64).alias("bright_main"),
        conf_class.alias("conf_class"),
        pl.col("acq_date").cast(pl.Date).alias("acq_date_d"),
        pl.col("frp").cast(pl.Float64, strict=False).alias("frp"),
        pl.col("satellite").cast(pl.Utf8).alias("satellite"),
        pl.col("version").cast(pl.Utf8, strict=False).alias("version"),
        pl.col("type").cast(pl.Int16, strict=False).alias("type"),
    ]).with_columns([
        pl.col("acq_date_d").dt.month().alias("month"),
        (pl.col("latitude").cast(pl.Float64) / GRID_DEG).floor().cast(pl.Int32).alias("cy"),
        (pl.col("longitude").cast(pl.Float64) / GRID_DEG).floor().cast(pl.Int32).alias("cx"),
        (pl.col("latitude").cast(pl.Float64) / PERSIST_GRID_DEG).floor().cast(pl.Int64).alias("py"),
        (pl.col("longitude").cast(pl.Float64) / PERSIST_GRID_DEG).floor().cast(pl.Int64).alias("px"),
    ])
    return lf.select([
        "latitude", "longitude", "acq_date_d", "year", "month", "country",
        "sensor_group", "satellite", "res_m", "conf_class", "frp", "daynight",
        "bright_main", "version", "type", "cy", "cx", "py", "px",
    ])

def load_all():
    lfs = [load_instrument(k) for k in INSTRUMENTS]
    lfs = [x for x in lfs if x is not None]
    if not lfs:
        raise SystemExit(f"No se encontraron parquet bajo {RAW_ROOT}")
    return pl.concat(lfs, how="vertical_relaxed")

# ---------------- ETAPA 2: FUENTES PERSISTENTES + HUECOS ----------------
def build_persistent_mask(lf_all):
    mask = (lf_all
            .with_columns((pl.col("year") * 12 + pl.col("month")).alias("ym"))
            .group_by(["py", "px"])
            .agg(pl.col("ym").n_unique().alias("n_months"))
            .filter(pl.col("n_months") >= PERSIST_MIN_MONTHS)
            .with_columns(pl.lit(True).alias("is_persistent"))
            .select(["py", "px", "is_persistent"]))
    mask = _collect(mask)
    mask.write_parquet(OUT / "persistent_mask.parquet")
    print(f"  celdas persistentes 0.01: {mask.height:,}")

GAPS = [
    ("VIIRS", "Suomi-NPP", "2026-05-01", "2026-07-27", "anomalias S-NPP 2026 (GPS/spacecraft)"),
    ("VIIRS", "Suomi-NPP", "2026-11-02", "2099-01-01", "cese definitivo S-NPP"),
    ("MODIS", "Aqua",      "2024-03-22", "2024-03-25", "perdida estacion Svalbard"),
    ("MODIS", "Terra",     "2026-03-26", "2026-03-27", "standby Terra"),
]
def write_gaps():
    pl.DataFrame(GAPS, schema=["sensor_group", "platform", "start", "end", "cause"],
                 orient="row").write_csv(OUT / "gaps.csv")

# ---------------- ETAPA 3: CAPA DE PUNTOS ----------------
def build_points(lf_all):
    lf = (lf_all
          .filter(pl.col("conf_class").is_in(CONF_KEEP))
          .join(pl.scan_parquet(OUT / "persistent_mask.parquet"), on=["py", "px"], how="left")
          .with_columns([
              pl.col("is_persistent").fill_null(False),
              (pl.col("frp") >= FRP_COMPARABLE_MW).alias("frp_comparable"),
          ])
          .select(["latitude", "longitude", "acq_date_d", "year", "month", "country",
                   "sensor_group", "satellite", "res_m", "conf_class", "frp", "daynight",
                   "bright_main", "version", "type", "is_persistent", "frp_comparable",
                   "cy", "cx"]))
    lf.sink_parquet(OUT / "hotspots_harmonized.parquet")
    print("  -> hotspots_harmonized.parquet")

# ---------------- ETAPA 4: CAPA DE ACTIVIDAD ----------------
def build_activity_grid():
    pts = pl.scan_parquet(OUT / "hotspots_harmonized.parquet").filter(~pl.col("is_persistent"))
    grid = (pts
            .group_by(["cy", "cx", "year", "month", "sensor_group", "country"])
            .agg([
                pl.len().alias("count"),
                pl.col("acq_date_d").n_unique().alias("active_fire_days"),
                pl.col("frp").sum().alias("frp_sum"),
                pl.col("frp").mean().alias("frp_mean"),
            ])
            .with_columns([
                (pl.col("cy") * GRID_DEG).alias("cell_lat"),
                (pl.col("cx") * GRID_DEG).alias("cell_lon"),
            ]))
    grid = _collect(grid)
    grid.write_parquet(OUT / "activity_grid.parquet")
    print(f"  -> activity_grid.parquet  ({grid.height:,} filas)")
    return grid

# ---------------- ETAPA 5: FACTORES (A) + CLIMATOLOGIA POR CELDA ----------------
def build_scaling_factors(grid):
    # Insight EDA: ratio estable pero DISTINTO por pais -> factores por pais, no global.
    # Insight EDA: excluir meses con huecos al calibrar.
    lo, hi = OVERLAP
    ov = _drop_gap_months(grid.filter(pl.col("year").is_between(lo, hi)))
    tot = (ov.group_by(["country", "sensor_group"])
             .agg([pl.col("active_fire_days").sum().alias("afd"),
                   pl.col("count").sum().alias("cnt"),
                   pl.col("frp_sum").sum().alias("frp")]))
    m = (tot.filter(pl.col("sensor_group") == "MODIS")
            .select(["country", pl.col("afd").alias("afd_m"),
                     pl.col("cnt").alias("cnt_m"), pl.col("frp").alias("frp_m")]))
    v = (tot.filter(pl.col("sensor_group") == "VIIRS")
            .select(["country", pl.col("afd").alias("afd_v"),
                     pl.col("cnt").alias("cnt_v"), pl.col("frp").alias("frp_v")]))
    # factor de magnitud por pais = VIIRS / MODIS (expresa MODIS en "unidades VIIRS")
    fac = (m.join(v, on="country", how="inner")
             .with_columns([
                 (pl.col("afd_v") / pl.col("afd_m")).alias("factor_afd_viirs_over_modis"),
                 (pl.col("cnt_v") / pl.col("cnt_m")).alias("factor_cnt_viirs_over_modis"),
                 (pl.col("frp_v") / pl.col("frp_m")).alias("factor_frp_viirs_over_modis"),
             ]).sort("country"))
    fac.write_parquet(OUT / "scaling_factors.parquet")
    print("  factores por pais (solape, sin meses con huecos):"); print(fac)

def _q_with_zeros(q):
    """Cuantil (interp. lineal) de una serie de N anios donde solo se guardan los k valores >0.
       Los (N-k) anios sin fila son ceros reales (mes con datos y sin fuego)."""
    n = pl.col("n_years").cast(pl.Int64)
    z = n - pl.col("_k").cast(pl.Int64)                       # ceros implicitos
    pos = (n - 1).cast(pl.Float64) * q
    lo, hi, fr = pos.floor().cast(pl.Int64), pos.ceil().cast(pl.Int64), pos - pos.floor()
    def at(i):
        return (pl.when(i < z).then(pl.lit(0.0))
                  .otherwise(pl.col("_v").list.get(i - z, null_on_oob=True).cast(pl.Float64)))
    return at(lo) * (1 - fr) + at(hi) * fr

def build_cell_climatology(grid):
    """Climatologia por celda/mes/sensor/pais CON ceros: un mes valido sin fila = 0 dias-con-fuego.
       n_years = anios validos del baseline (con datos del sensor ese mes); n_years_fire = anios con fuego."""
    grid = _drop_gap_months(grid)   # insight EDA: no sesgar la climatologia con meses de hueco
    parts = []
    for group, (lo, hi) in (("MODIS", BASELINE_MODIS), ("VIIRS", BASELINE_VIIRS)):
        b = grid.filter((pl.col("sensor_group") == group) & pl.col("year").is_between(lo, hi))
        if b.height == 0:
            continue
        nyears = (b.select(["country", "month", "year"]).unique()
                    .group_by(["country", "month"]).agg(pl.len().alias("n_years")))
        c = (b.group_by(["cy", "cx", "country", "month"])
              .agg([pl.col("active_fire_days").cast(pl.Float64).sum().alias("_s"),
                    (pl.col("active_fire_days").cast(pl.Float64) ** 2).sum().alias("_s2"),
                    pl.len().alias("_k"),
                    pl.col("active_fire_days").sort().alias("_v")])
              .join(nyears, on=["country", "month"]))
        N = pl.col("n_years").cast(pl.Float64)
        c = c.with_columns([
            (pl.col("_s") / N).alias("afd_mean"),
            pl.when(N > 1).then(((pl.col("_s2") - pl.col("_s") ** 2 / N) / (N - 1)).clip(lower_bound=0).sqrt())
              .otherwise(None).alias("afd_std"),
            _q_with_zeros(0.5).alias("afd_p50"),
            _q_with_zeros(0.9).alias("afd_p90"),
            pl.col("_k").alias("n_years_fire"),
            pl.lit(group).alias("sensor_group")])
        parts.append(c.select(["cy", "cx", "country", "month", "sensor_group",
                               "afd_mean", "afd_std", "afd_p50", "afd_p90", "n_years", "n_years_fire"]))
    out = pl.concat(parts)
    out.write_parquet(OUT / "cell_climatology.parquet")
    print(f"  -> cell_climatology.parquet ({out.height:,} filas, con ceros)")

# ---------------- CONSULTA POR AOI (ejemplo para el frontend) ----------------
def aoi_cell_range(lat_min, lat_max, lon_min, lon_max):
    """Indices de celda del AOI con la MISMA formula que el pipeline (floor(valor/GRID_DEG)).
       (int() truncaria hacia 0 y fallaria con coordenadas negativas: Mexico, Brasil, Australia...)"""
    f = lambda v: int(math.floor(v / GRID_DEG))
    return f(lat_min), f(lat_max), f(lon_min), f(lon_max)

def aoi_calendar(lat_min, lat_max, lon_min, lon_max, sensor_group, baseline=None):
    """Serie mensual del AOI + anomalia contra su PROPIA historia, con ceros explicitos.
       Meses validos = meses con datos del sensor (cualquier pais) en activity_grid. Un mes valido sin
       fuego en el AOI vale 0. Los meses de hueco conocido (EXCLUDE_YM) salen con valid=False,
       z/pctl nulos y no entran a la climatologia.
       Columnas: year, month, afd, valid, mean, std, p50, n_base, z, pctl."""
    g = pl.read_parquet(OUT / "activity_grid.parquet")
    cyl, cyh, cxl, cxh = aoi_cell_range(lat_min, lat_max, lon_min, lon_max)
    gs = g.filter(pl.col("sensor_group") == sensor_group)
    present = (gs.select(["year", "month"]).unique()
                 .with_columns(pl.struct(["year", "month"]).map_elements(
                     lambda r: (sensor_group, r["year"], r["month"]) not in EXCLUDE_YM,
                     return_dtype=pl.Boolean).alias("valid")))
    sub = gs.filter(pl.col("cy").is_between(cyl, cyh) & pl.col("cx").is_between(cxl, cxh))
    sums = sub.group_by(["year", "month"]).agg(pl.col("active_fire_days").sum().alias("afd"))
    ser = (present.join(sums, on=["year", "month"], how="left")
                  .with_columns(pl.col("afd").fill_null(0)).sort(["year", "month"]))
    lo, hi = baseline or (BASELINE_VIIRS if sensor_group == "VIIRS" else BASELINE_MODIS)
    base = ser.filter(pl.col("valid") & pl.col("year").is_between(lo, hi))
    clim = (base.group_by("month").agg([pl.col("afd").mean().alias("mean"),
                                        pl.col("afd").std().alias("std"),
                                        pl.col("afd").median().alias("p50"),
                                        pl.len().alias("n_base")]))
    bv = base.select(["month", pl.col("afd").alias("_b")])
    pct = (ser.join(bv, on="month").group_by(["year", "month"])
              .agg((pl.col("_b") <= pl.col("afd")).mean().alias("pctl")))
    out = (ser.join(clim, on="month", how="left").join(pct, on=["year", "month"], how="left")
              .with_columns([
                  pl.when(pl.col("valid") & (pl.col("std") > 0))
                    .then((pl.col("afd") - pl.col("mean")) / pl.col("std")).otherwise(None).alias("z"),
                  pl.when(pl.col("valid")).then(pl.col("pctl")).otherwise(None).alias("pctl")])
              .sort(["year", "month"]))
    return out

# ---------------- ETAPA 6: VALIDACION ----------------
def validate(grid):
    pts = pl.scan_parquet(OUT / "hotspots_harmonized.parquet")
    twins = (pts.filter(pl.col("sensor_group") == "VIIRS")
                .group_by("satellite").agg(pl.len().alias("n")).collect())
    print("  conteos por plataforma VIIRS (control S-NPP vs NOAA-20):"); print(twins)
    lo, hi = OVERLAP
    series = []
    for grp in ["MODIS", "VIIRS"]:
        s = (grid.filter((pl.col("sensor_group") == grp) & pl.col("year").is_between(lo, hi))
                 .group_by(["year", "month"]).agg(pl.col("active_fire_days").sum().alias(grp))
                 .sort(["year", "month"]))
        series.append(s)
    m = series[0].join(series[1], on=["year", "month"], how="inner")
    if m.height > 2:
        print("  Spearman(MODIS,VIIRS) actividad mensual en solape:",
              round(m.select(pl.corr("MODIS", "VIIRS", method="spearman")).item(), 3))
    m.write_csv(OUT / "validation_report.csv")

# ---------------- MAIN ----------------
if __name__ == "__main__":
    print(f"RAW_ROOT = {RAW_ROOT}\nOUT      = {OUT}\nSMOKE    = {SMOKE}")
    print("1) cargando y unificando parquet...")
    lf_all = load_all()
    print("2) mascara de fuentes persistentes...")
    build_persistent_mask(lf_all); write_gaps()
    print("3) capa de puntos...")
    build_points(lf_all)
    print("4) capa de actividad...")
    grid = build_activity_grid()
    print("5) factores + climatologia...")
    build_scaling_factors(grid); build_cell_climatology(grid)
    print("6) validacion...")
    validate(grid)
    print("LISTO ->", OUT)
