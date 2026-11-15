"""Descarga clima diario NASA POWER (2011-10-01 .. 2025-12-31) para el centro de cada zona de 1
grado de los 6 paises. CORRER EN TU PC (POWER esta bloqueado desde las VMs):

    python prediccion\\src\\p08_power_global.py          (reanudable: salta zonas ya bajadas)

Orden: zonas con mas actividad primero, asi si se corta, las zonas importantes ya tienen clima.
Salida: prediccion/data/power_global/<zona_id>.parquet  ->  luego  p08 ... unir
"""
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
import requests

RAIZ = Path(__file__).resolve().parents[2]
ZS = RAIZ / "prediccion/data/global_zs.parquet"
DIR = RAIZ / "prediccion/data/power_global"
URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
MIN_TOTAL, HILOS = 20, 6


def bajar(zid, lat, lon):
    out = DIR / f"{zid}.parquet"
    if out.exists():
        return zid, "ya"
    q = dict(parameters="PRECTOTCORR,RH2M,T2M_MAX,WS10M", community="AG", latitude=lat,
             longitude=lon, start="20111001", end="20251231", format="JSON")
    for intento in range(4):
        try:
            r = requests.get(URL, params=q, timeout=180)
            if r.status_code == 429:
                time.sleep(30 * (intento + 1))
                continue
            r.raise_for_status()
            d = pd.DataFrame(r.json()["properties"]["parameter"])
            d.index = pd.to_datetime(d.index, format="%Y%m%d")
            d = d.replace(-999, np.nan).rename_axis("fecha").reset_index()
            d["zona_id"] = zid
            d.to_parquet(out, index=False)
            return zid, "ok"
        except Exception as e:  # noqa: BLE001
            err = e
            time.sleep(5 * (intento + 1))
    return zid, f"ERROR {err}"


def unir():
    fs = sorted(DIR.glob("*.parquet"))
    d = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    d.to_parquet(RAIZ / "prediccion/data/power_global.parquet", index=False)
    print("unido:", len(fs), "zonas,", len(d), "filas")


if __name__ == "__main__":
    if sys.argv[1:] == ["unir"]:
        unir()
        sys.exit()
    DIR.mkdir(parents=True, exist_ok=True)
    g = pd.read_parquet(ZS)
    tot = g.groupby(["zona_id", "lat0", "lon0"]).valor.sum().reset_index()
    tot = tot[tot.valor >= MIN_TOTAL].sort_values("valor", ascending=False)
    print(len(tot), "zonas por descargar (o ya descargadas)", flush=True)
    t0, n = time.time(), 0
    with ThreadPoolExecutor(HILOS) as ex:
        fut = [ex.submit(bajar, int(r.zona_id), r.lat0 + 0.5, r.lon0 + 0.5)
               for r in tot.itertuples()]
        for f in as_completed(fut):
            zid, st = f.result()
            n += 1
            if st.startswith("ERROR") or n % 50 == 0:
                print(f"{n}/{len(tot)}  {time.time() - t0:.0f}s  {zid} {st}", flush=True)
    unir()
