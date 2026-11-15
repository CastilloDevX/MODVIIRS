#!/usr/bin/env python3
"""Resume los zips FIRMS (sin extraer) en tablas pequeñas para decidir regiones de interés.

Uso (desde Data/): python analisis/01_paises/summarize_firms.py [DATA_DIR] [--workers N]
Lee   <DATA_DIR>/raw/<inst>/<inst>_<año>_all_countries.zip   (zips all_countries; ya NO se conservan en disco:
      este script es historico y documenta como se generaron las tablas; para regenerarlas hay que volver a bajar los zips)
Crea  analisis/01_paises/tablas/summary_country_month.csv.gz   (instrument,country,year_month,n,n_day,frp_sum)
      analisis/01_paises/tablas/summary_grid1deg_year.csv.gz   (instrument,year,lat_cell,lon_cell,n,frp_sum)
lat_cell/lon_cell = esquina suroeste de la celda de 1 grado (floor).
"""
import argparse, glob, os, sys, zipfile
from multiprocessing import Pool
import numpy as np
import pandas as pd

COLS = ["latitude", "longitude", "acq_date", "frp", "daynight"]


def work(zpath):
    inst = os.path.basename(os.path.dirname(zpath))
    year = int(os.path.basename(zpath).split("_")[1])
    cm, gr = [], []
    with zipfile.ZipFile(zpath) as z:
        for m in z.namelist():
            if not m.endswith(".csv"):
                continue
            country = os.path.basename(m)[:-4].split(f"_{year}_", 1)[1]
            with z.open(m) as f:
                df = pd.read_csv(f, usecols=COLS, dtype={"daynight": "string"})
            if df.empty:
                continue
            df["frp"] = pd.to_numeric(df["frp"], errors="coerce")
            df["ym"] = df["acq_date"].str[:7]
            df["is_day"] = (df["daynight"] == "D").astype("int32")
            g = df.groupby("ym").agg(n=("frp", "size"), n_day=("is_day", "sum"), frp_sum=("frp", "sum")).reset_index()
            g.insert(0, "country", country); g.insert(0, "instrument", inst)
            cm.append(g)
            df["lat_cell"] = np.floor(df["latitude"]).astype("int16")
            df["lon_cell"] = np.floor(df["longitude"]).astype("int16")
            h = df.groupby(["lat_cell", "lon_cell"]).agg(n=("frp", "size"), frp_sum=("frp", "sum")).reset_index()
            h.insert(0, "year", year); h.insert(0, "instrument", inst)
            gr.append(h)
    return inst, year, (pd.concat(cm) if cm else None), (pd.concat(gr) if gr else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir", nargs="?", default=None, help="carpeta Data (default: dos niveles sobre este script)")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    a.data_dir = a.data_dir or os.path.abspath(os.path.join(here, "..", ".."))
    zips = sorted(glob.glob(os.path.join(a.data_dir, "raw", "*", "*_all_countries.zip")))
    if not zips:
        sys.exit("no hay zips en raw/")
    cm, gr = [], []
    with Pool(a.workers) as p:
        for inst, year, c, g in p.imap_unordered(work, zips):
            print("ok", inst, year, flush=True)
            if c is not None: cm.append(c)
            if g is not None: gr.append(g)
    out = os.path.join(here, "tablas"); os.makedirs(out, exist_ok=True)
    cm = pd.concat(cm).rename(columns={"ym": "year_month"})
    # un país puede aparecer en el mismo mes desde varios CSV del mismo instrumento? (no esperado) -> consolidar
    cm = cm.groupby(["instrument", "country", "year_month"], as_index=False).sum()
    gr = pd.concat(gr).groupby(["instrument", "year", "lat_cell", "lon_cell"], as_index=False).sum()
    cm.round({"frp_sum": 1}).to_csv(os.path.join(out, "summary_country_month.csv.gz"), index=False)
    gr.round({"frp_sum": 1}).to_csv(os.path.join(out, "summary_grid1deg_year.csv.gz"), index=False)
    print("country-month rows:", len(cm), "| grid rows:", len(gr))


if __name__ == "__main__":
    main()
