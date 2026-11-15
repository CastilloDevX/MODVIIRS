"""
build_training_dataset.py  --  dataset de entrenamiento independiente del sensor.

Entrada : activity_grid.parquet + scaling_factors.parquet (salidas de harmonize_firms.py)
Salida  : training_dataset.parquet  y  training_dataset.csv  (en esta misma carpeta)

Una fila por celda 0.1 x mes (x pais), con CEROS EXPLICITOS y una sola serie continua:
  - 2001-2011 (o desde que haya datos): MODIS
  - 2012-01 en adelante               : VIIRS
Targets:
  afd_z           (RECOMENDADO) anomalia estandarizada vs la climatologia del PROPIO sensor -> comparable entre sensores
  afd_anom        afd - media climatologica del propio sensor (en dias-con-fuego)
  afd_viirs_equiv dias-con-fuego en "unidades VIIRS" (MODIS * factor por pais, tope 31) -> aproximado
  afd             dias-con-fuego crudo (NO comparable entre sensores)

Parametros (constantes al inicio del script): MIN_ACTIVE_MONTHS, COUNTRIES, WRITE_CSV, MIN_YEARS_Z.
"""
import sys
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
OUT = HERE   # entrada y salida: esta misma carpeta

MIN_ACTIVE_MONTHS = 6      # solo celdas con >= N meses con fuego en toda la serie
COUNTRIES = []             # p. ej. ["Mexico", "Brazil"]; vacio = todos
WRITE_CSV = True           # False = no escribir el CSV

BASELINE = {"MODIS": (2001, 2024), "VIIRS": (2012, 2024)}   # igual que harmonize_firms.py
SWITCH = (2012, 1)                                          # desde aqui la serie unificada usa VIIRS
MIN_YEARS_Z = 8   # minimo de anios de baseline para confiar en z
EXCLUDE_YM = {("MODIS", 2022, 4), ("VIIRS", 2022, 7), ("VIIRS", 2022, 8)}  # meses con hueco (igual que harmonize)


def main():
    act = pl.read_parquet(OUT / "activity_grid.parquet")
    sf = pl.read_parquet(OUT / "scaling_factors.parquet").select(
        "country", pl.col("factor_afd_viirs_over_modis").alias("f_afd"))
    if COUNTRIES:
        act = act.filter(pl.col("country").is_in(COUNTRIES))
    print(f"activity_grid: {act.height:,} filas")

    # 1) celdas candidatas (union de sensores) con suficiente actividad
    cells = (act.group_by(["cy", "cx", "country", "sensor_group"]).agg(pl.len().alias("n"))
                .group_by(["cy", "cx", "country"]).agg(pl.col("n").max().alias("n_active_months"))
                .filter(pl.col("n_active_months") >= MIN_ACTIVE_MONTHS)
                .with_columns((pl.col("cy").cast(pl.Float64) * 0.1).alias("cell_lat"),
                              (pl.col("cx").cast(pl.Float64) * 0.1).alias("cell_lon")))
    print(f"celdas con >= {MIN_ACTIVE_MONTHS} meses con fuego: {cells.height:,}")

    # 2) calendario mensual valido por pais y sensor: SOLO meses que existen en los datos
    #    (si falta un archivo/mes, no se fabrican ceros) y sin meses de hueco conocidos
    months = (act.select(["country", "sensor_group", "year", "month"]).unique()
                 .filter(~pl.struct(["sensor_group", "year", "month"]).map_elements(
                     lambda r: (r["sensor_group"], r["year"], r["month"]) in EXCLUDE_YM,
                     return_dtype=pl.Boolean)))

    # 3) rejilla completa con ceros explicitos
    full = (cells.join(months, on="country", how="inner")
                 .join(act.select(["cy", "cx", "country", "sensor_group", "year", "month",
                                   "active_fire_days", "count", "frp_sum"]),
                       on=["cy", "cx", "country", "sensor_group", "year", "month"], how="left")
                 .with_columns(pl.col("active_fire_days").fill_null(0).alias("afd"),
                               pl.col("count").fill_null(0).alias("n_hotspots"),
                               pl.col("frp_sum").fill_null(0.0).alias("frp_sum"))
                 .drop(["active_fire_days", "count"]))

    # 4) climatologia correcta (con ceros) por celda, mes y sensor
    base = pl.concat([
        full.filter((pl.col("sensor_group") == g) & pl.col("year").is_between(lo, hi))
        for g, (lo, hi) in BASELINE.items()])
    clim = (base.group_by(["cy", "cx", "country", "sensor_group", "month"])
                .agg([pl.col("afd").mean().alias("afd_mean"),
                      pl.col("afd").std().alias("afd_std"),
                      pl.len().alias("n_years")]))
    full = full.join(clim, on=["cy", "cx", "country", "sensor_group", "month"], how="left")
    ok = (pl.col("n_years") >= MIN_YEARS_Z) & (pl.col("afd_std") > 0)
    full = (full.with_columns([
                pl.when(ok).then((pl.col("afd") - pl.col("afd_mean")) / pl.col("afd_std")).otherwise(None).alias("afd_z"),
                (pl.col("afd") - pl.col("afd_mean")).alias("afd_anom")])
                .join(sf, on="country", how="left")
                .with_columns(pl.when(pl.col("sensor_group") == "MODIS")
                                .then((pl.col("afd") * pl.col("f_afd")).clip(upper_bound=31))
                                .otherwise(pl.col("afd").cast(pl.Float64)).alias("afd_viirs_equiv")))

    # 5) diagnostico de empalme en el solape (ambos sensores, 2012-2024)
    ov = full.filter(pl.col("year").is_between(2012, 2024))
    a = ov.filter(pl.col("sensor_group") == "MODIS").select(["cy", "cx", "country", "year", "month", pl.col("afd_z").alias("z_m")])
    b = ov.filter(pl.col("sensor_group") == "VIIRS").select(["cy", "cx", "country", "year", "month", pl.col("afd_z").alias("z_v")])
    j = a.join(b, on=["cy", "cx", "country", "year", "month"]).drop_nulls()
    if j.height:
        print(f"[solape 2012-2024] celdas-mes comparables: {j.height:,} | "
              f"corr(z_MODIS, z_VIIRS)={j.select(pl.corr('z_m', 'z_v')).item():.3f} | "
              f"corr Spearman={j.select(pl.corr('z_m', 'z_v', method='spearman')).item():.3f} | "
              f"media z: MODIS={j['z_m'].mean():.3f} VIIRS={j['z_v'].mean():.3f}")

    # 6) serie unificada: MODIS antes de SWITCH, VIIRS desde SWITCH
    ym = pl.col("year") * 100 + pl.col("month")
    use_viirs = ym >= SWITCH[0] * 100 + SWITCH[1]
    uni = (full.filter(pl.when(use_viirs).then(pl.col("sensor_group") == "VIIRS")
                         .otherwise(pl.col("sensor_group") == "MODIS"))
               .with_columns(pl.date(pl.col("year"), pl.col("month"), 1).alias("date"))
               .select(["date", "year", "month", "country", "cy", "cx", "cell_lat", "cell_lon",
                        "sensor_group", "afd", "afd_z", "afd_anom", "afd_viirs_equiv",
                        "afd_mean", "afd_std", "n_hotspots", "frp_sum"])
               .sort(["country", "cy", "cx", "date"]))

    uni.write_parquet(OUT / "training_dataset.parquet")
    print(f"-> training_dataset.parquet ({uni.height:,} filas, "
          f"{uni['date'].min()} a {uni['date'].max()}, z nulos: {uni['afd_z'].null_count() / uni.height:.1%})")
    if WRITE_CSV:
        uni.write_csv(OUT / "training_dataset.csv")
        print(f"-> training_dataset.csv ({(OUT / 'training_dataset.csv').stat().st_size / 1e6:,.0f} MB)")


if __name__ == "__main__":
    main()
