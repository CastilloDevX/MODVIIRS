"""p01 - Puntos armonizados (Alexis) -> dias-con-fuego semanales por celda 0.1 deg, una plataforma por era.

Filtros: conf n+h (ya aplicado por Alexis), type == 0, sin fuentes persistentes (is_persistent),
         Aqua en la era MODIS y S-NPP en la era VIIRS (serie homogenea, R3 de Alexis).
Metrica (la de Alexis, a escala semanal): valor = numero de dias distintos de la semana con >= 1 deteccion
         en la celda (0..7). Semana = lunes..domingo (fecha UTC de FIRMS; en Mexico coincide con la local
         para los pasos de ~13:30 y ~01:30).
Salidas (data/processed/):
  actividad_celda_semana.parquet  cell_id, semana, era, valor        (solo celdas con fuego)
  semanas.parquet                 semana, era, valido                 (valido=False en huecos de sensor)
  celdas.parquet                  cell_id, fila, col, lat_min, lon_min, zona_id
"""
import numpy as np
import pandas as pd
import config as C

d = pd.read_parquet(C.PUNTOS, columns=["latitude", "longitude", "acq_date_d", "satellite", "type", "is_persistent"])
n0 = len(d)
d = d[~d.is_persistent]
if C.USAR_FILTRO_TYPE:
    d = d[d["type"] == 0]
d["fecha"] = pd.to_datetime(d.acq_date_d)
partes = []
for era, sat, ini, fin in C.ERAS:
    x = d[(d.satellite == sat) & d.fecha.between(ini, fin)].copy()
    x["era"] = era
    partes.append(x)
d = pd.concat(partes, ignore_index=True)
print(f"detecciones: {n0:,} -> type0 y sin persistentes, 1 plataforma/era: {len(d):,}")

fila = np.floor((d.latitude - C.S) / C.TAM_CELDA + 1e-9).astype(int).clip(0, C.NF - 1)
col = np.floor((d.longitude - C.W) / C.TAM_CELDA + 1e-9).astype(int).clip(0, C.NC - 1)
d["cell_id"] = fila * 100 + col
d["semana"] = d.fecha - pd.to_timedelta(d.fecha.dt.weekday, unit="D")

act = (d.groupby(["cell_id", "semana", "era"]).fecha.nunique().rename("valor").reset_index())
act["valor"] = act.valor.astype(float)
act.to_parquet(C.PROC / "actividad_celda_semana.parquet", index=False)

# semanas, era y validez
sem = pd.DataFrame({"semana": pd.date_range(C.INICIO, "2025-12-29", freq="W-MON")})
sem["era"] = None
for era, _, ini, fin in C.ERAS:
    sem.loc[sem.semana.between(ini, fin), "era"] = era
sem["valido"] = sem.era.notna()
for era, huecos in C.HUECOS.items():
    for ini, fin in huecos:
        fin_sem = sem.semana + pd.Timedelta(days=6)
        sem.loc[(sem.era == era) & (fin_sem >= ini) & (sem.semana <= fin), "valido"] = False
sem.to_parquet(C.PROC / "semanas.parquet", index=False)

cel = pd.DataFrame({"cell_id": np.sort(act.cell_id.unique())})
cel["fila"], cel["col"] = cel.cell_id // 100, cel.cell_id % 100
cel["lat_min"] = (C.S + cel.fila * C.TAM_CELDA).round(4)
cel["lon_min"] = (C.W + cel.col * C.TAM_CELDA).round(4)
cel["zona_id"] = (cel.fila // C.CELDAS_POR_ZONA) * 100 + cel.col // C.CELDAS_POR_ZONA
cel.to_parquet(C.PROC / "celdas.parquet", index=False)

anual = act.assign(anio=act.semana.dt.year).groupby(["anio", "era"]).valor.sum().unstack()
print(f"celdas activas: {len(cel):,} | zonas: {cel.zona_id.nunique()} | semanas no validas: {(~sem.valido).sum()}")
print("dias-con-fuego (celda) por anio y era:\n", anual.round(0).to_string())
