"""Actividad semanal por zona de 1 grado para los 6 paises de la armonizacion de Alexis.

Fuente: backend/data/activity_daily.parquet (celdas 0.1 deg x dia, sin fuentes persistentes),
solo sensor_group == VIIRS. Dia-con-fuego = fila con n_hotspots > 0. Zona = floor(lat), floor(lon).
Salida: prediccion/data/global_zs.parquet  (pais, zona_id, lat0, lon0, semana, valor)
"""
from pathlib import Path
import sys
import pandas as pd
import pyarrow.parquet as pq
import pyarrow.compute as pc

RAIZ = Path(__file__).resolve().parents[2]
SRC = RAIZ / "backend/data/activity_daily.parquet"
OUT = RAIZ / "prediccion/data/global_zs.parquet"

PAISES = ["Mexico", "Brazil", "Russian_Federation", "Australia", "Angola",
          "Democratic_Republic_of_the_Congo"]

partes = []
for p in PAISES:
    t = pq.read_table(SRC, columns=["cy", "cx", "acq_date_d", "n_hotspots"],
                      filters=[("sensor_group", "=", "VIIRS"), ("country", "=", p)])
    t = t.filter(pc.greater(t["n_hotspots"], 0))
    d = t.select(["cy", "cx", "acq_date_d"]).to_pandas()
    d["lat0"] = (d.cy // 10).astype("int16")
    d["lon0"] = (d.cx // 10).astype("int16")
    f = pd.to_datetime(d.acq_date_d)
    d["semana"] = f - pd.to_timedelta(f.dt.weekday, unit="D")
    g = d.groupby(["lat0", "lon0", "semana"]).size().rename("valor").reset_index()
    g["pais"] = p
    print(p, len(d), "dias-celda ->", g[["lat0", "lon0"]].drop_duplicates().shape[0], "zonas",
          f.min().date(), f.max().date(), flush=True)
    partes.append(g)
    del t, d, f
zs = pd.concat(partes, ignore_index=True)
zs["zona_id"] = (zs.lat0.astype(int) + 90) * 1000 + (zs.lon0.astype(int) + 180)
zs.to_parquet(OUT, index=False)
print("OK", OUT, len(zs))
