"""Funciones compartidas: matriz zona x semana, percentiles historicos por era y anomalias (sin fuga)."""
import numpy as np
import pandas as pd
import config as C


def cargar_matriz():
    """Devuelve (Z, sem, zonas): Z[semana, zona] = dias-con-fuego de la zona (NaN en semanas no validas)."""
    act = pd.read_parquet(C.PROC / "actividad_celda_semana.parquet")
    sem = pd.read_parquet(C.PROC / "semanas.parquet")
    cel = pd.read_parquet(C.PROC / "celdas.parquet")
    act = act.merge(cel[["cell_id", "zona_id"]], on="cell_id")
    zonas = np.sort(cel.zona_id.unique())
    Z = (act.groupby(["semana", "zona_id"]).valor.sum().unstack()
            .reindex(index=sem.semana, columns=zonas).fillna(0).to_numpy(dtype=float))
    Z[~sem.valido.to_numpy()] = np.nan
    sem = sem.copy()
    sem["anio"] = sem.semana.dt.year
    sem["woy"] = np.minimum((sem.semana.dt.dayofyear - 1) // 7 + 1, 52)
    return Z, sem, zonas


def percentiles_historicos(Z, sem, por_era=True):
    """P50/P90 de cada (semana, zona) usando SOLO anios anteriores, semanas del anio +-VENT,
    semanas validas y (si por_era) la MISMA era. Requiere >= MIN_ANIOS anios de historia."""
    anio, woy = sem.anio.to_numpy(), sem.woy.to_numpy()
    era, val = sem.era.to_numpy(), sem.valido.to_numpy()
    P50 = np.full_like(Z, np.nan); P90 = np.full_like(Z, np.nan); NA = np.zeros(len(sem))
    for (y, k, e), idx in sem[val].groupby(["anio", "woy", "era"]).groups.items():
        dist = np.abs(woy - k); dist = np.minimum(dist, 52 - dist)
        h = val & (anio < y) & (dist <= C.VENT_SEMANAS)
        if por_era:
            h &= (era == e)
        n = len(np.unique(anio[h]))
        if n < C.MIN_ANIOS:
            continue
        P50[idx] = np.nanpercentile(Z[h], 50, axis=0)
        P90[idx] = np.nanpercentile(Z[h], 90, axis=0)
        NA[idx] = n
    return P50, P90, NA


def anomalias(Z, P90):
    """1 si la actividad supera max(p90, UMBRAL_MIN); NaN si no hay linea base o la semana no es valida."""
    A = (Z > np.maximum(P90, C.UMBRAL_MIN)).astype(float)
    A[np.isnan(P90) | np.isnan(Z)] = np.nan
    return A


def frecuencia_historica(A, sem, por_era=True):
    """Fraccion de anios anteriores (misma era) con anomalia en la misma zona y semana del anio = LINEA BASE."""
    anio, woy, era = sem.anio.to_numpy(), sem.woy.to_numpy(), sem.era.to_numpy()
    FR = np.full_like(A, np.nan)
    for (y, k, e), idx in sem[sem.valido].groupby(["anio", "woy", "era"]).groups.items():
        h = (anio < y) & (woy == k)
        if por_era:
            h &= (era == e)
        if h.sum():
            with np.errstate(all="ignore"):
                FR[idx] = np.nanmean(A[h], axis=0)
    return FR
