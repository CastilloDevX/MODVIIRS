"""BurnModel: probabilidad de actividad ANOMALA de puntos de calor por zona y semana.

"El sistema anticipa con X % de probabilidad un comportamiento anomalo de puntos de calor
 en la semana T en la zona Z."  (Peninsula de Yucatan, zonas de 0.5 deg ~55 km)

Metodo (validado en la rama `predictivo`, ver prediccion/README.md):
- Actividad = dias-con-fuego por celda 0.1 deg y semana (metrica de la armonizacion de
  Alexis), sumada por zona (5x5 celdas). Una sola plataforma a la vez: Aqua (era MODIS) y
  S-NPP -> NOAA-20 (era VIIRS).
- Anomalia (Z,T) = actividad > max(p90, 3), con p90 de la misma zona, semanas del anio +-2,
  SOLO anios anteriores y SOLO la misma era (normalizacion por era = metodo G de Alexis).
- Variables con informacion hasta T-H: rezagos crudos y relativos al umbral de su era,
  anomalias
  previas, p50/p90 esperados, frecuencia historica (= linea base), senal regional y
  clima NASA POWER.
- HistGradientBoostingClassifier (se entrena en segundos, por eso no se serializa: evita
  incompatibilidades de version de scikit-learn entre maquinas).
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

# semanas sin historia dan "Mean of empty slice" en nanmean: es esperado (resultado NaN)
warnings.filterwarnings("ignore", message="Mean of empty slice", category=RuntimeWarning)
warnings.filterwarnings("ignore", message="All-NaN slice", category=RuntimeWarning)

S, W = 17.8, -92.5
TAM_ZONA = 0.5
VENT, MIN_ANIOS, UMBRAL_MIN = 2, 3, 3
PARAMS = dict(
    max_iter=200, learning_rate=0.05, max_leaf_nodes=15, l2_regularization=1.0, random_state=0
)
FEATS_CLIMA = [
    "lluvia_30d",
    "lluvia_90d",
    "lluvia_90d_anom",
    "dias_sin_lluvia",
    "hr_7d",
    "tmax_7d",
    "viento_7d",
]


def _woy(fechas: pd.Series) -> np.ndarray:
    return np.minimum((fechas.dt.dayofyear.to_numpy() - 1) // 7 + 1, 52)


def preparar_semanas(sem: pd.DataFrame) -> pd.DataFrame:
    """sem: semana, era, valido, [observado]. Agrega anio y woy."""
    sem = sem.sort_values("semana").reset_index(drop=True).copy()
    if "observado" not in sem:
        sem["observado"] = sem.valido
    sem["anio"] = sem.semana.dt.year
    sem["woy"] = _woy(sem.semana)
    return sem


def matriz(zs: pd.DataFrame, sem: pd.DataFrame, zonas: np.ndarray) -> np.ndarray:
    """Z[semana, zona] = dias-con-fuego; 0 si se observo sin fuego; NaN si no se observo."""
    z = (
        zs.groupby(["semana", "zona_id"])
        .valor.sum()
        .unstack()
        .reindex(index=sem.semana, columns=zonas)
        .fillna(0)
        .to_numpy(dtype=float)
    )
    z[~(sem.valido & sem.observado).to_numpy()] = np.nan
    return z


def percentiles(z: np.ndarray, sem: pd.DataFrame):
    anio, woy = sem.anio.to_numpy(), sem.woy.to_numpy()
    era, val = sem.era.to_numpy(), sem.valido.to_numpy()
    p50 = np.full_like(z, np.nan)
    p90 = np.full_like(z, np.nan)
    for (y, k, e), idx in sem[sem.valido].groupby(["anio", "woy", "era"]).groups.items():
        dist = np.abs(woy - k)
        dist = np.minimum(dist, 52 - dist)
        h = val & (anio < y) & (dist <= VENT) & (era == e)
        if len(np.unique(anio[h])) < MIN_ANIOS:
            continue
        with np.errstate(all="ignore"):
            p50[idx] = np.nanpercentile(z[h], 50, axis=0)
            p90[idx] = np.nanpercentile(z[h], 90, axis=0)
    return p50, p90


def anomalias(z: np.ndarray, p90: np.ndarray) -> np.ndarray:
    a = (z > np.maximum(p90, UMBRAL_MIN)).astype(float)
    a[np.isnan(p90) | np.isnan(z)] = np.nan
    return a


def frecuencia(a: np.ndarray, sem: pd.DataFrame) -> np.ndarray:
    anio, woy, era = sem.anio.to_numpy(), sem.woy.to_numpy(), sem.era.to_numpy()
    fr = np.full_like(a, np.nan)
    for (y, k, e), idx in sem[sem.valido].groupby(["anio", "woy", "era"]).groups.items():
        h = (anio < y) & (woy == k) & (era == e)
        if h.sum():
            with np.errstate(all="ignore"):
                fr[idx] = np.nanmean(a[h], axis=0)
    return fr


def clima_semanal(power: pd.DataFrame) -> pd.DataFrame:
    """Diario NASA POWER (fecha, lat, lon, PRECTOTCORR, RH2M, T2M_MAX, WS10M) -> valor al LUNES
    de cada semana calculado con los dias ANTERIORES. Columnas: semana, zf, zc, FEATS_CLIMA."""
    pw = power.sort_values("fecha").copy()
    pw["zf"] = np.clip(np.round((pw.lat - 18.0) / 0.5), 0, 7).astype(int)
    pw["zc"] = np.clip(np.round((pw.lon + 92.25) / 0.5), 0, 11).astype(int)
    out = []
    for (zf, zc), s in pw.groupby(["zf", "zc"]):
        s = s.drop_duplicates("fecha").set_index("fecha").asfreq("D").ffill()
        c = pd.DataFrame(
            {
                "lluvia_30d": s.PRECTOTCORR.rolling(30).sum(),
                "lluvia_90d": s.PRECTOTCORR.rolling(90).sum(),
                "dias_sin_lluvia": s.PRECTOTCORR.lt(1)
                .groupby(s.PRECTOTCORR.ge(1).cumsum())
                .cumsum(),
                "hr_7d": s.RH2M.rolling(7).mean(),
                "tmax_7d": s.T2M_MAX.rolling(7).mean(),
                "viento_7d": s.WS10M.rolling(7).mean(),
            }
        ).shift(1)
        c = c[c.index.weekday == 0]
        c["zf"], c["zc"] = zf, zc
        out.append(c.rename_axis("semana").reset_index())
    cl = pd.concat(out)
    cl["woy"] = _woy(cl.semana)
    cl = cl.sort_values("semana")
    cl["lluvia_90d_anom"] = cl.lluvia_90d - cl.groupby(["zf", "zc", "woy"]).lluvia_90d.transform(
        lambda x: x.shift(1).expanding().mean()
    )
    return cl.drop(columns="woy")


def tabla(z, sem, zonas, clima: pd.DataFrame | None, h: int) -> pd.DataFrame:
    """Tabla zona x semana con etiqueta y variables (solo informacion hasta T-h)."""
    p50, p90 = percentiles(z, sem)
    a = anomalias(z, p90)
    fr = frecuencia(a, sem)
    n_w, n_z = z.shape
    era = sem.era.to_numpy()

    def lag(x, k):
        k = k + h - 1
        o = np.full_like(x, np.nan, dtype=float)
        o[k:] = x[:-k]
        o[np.r_[np.ones(k, bool), era[k:] != era[:-k]]] = np.nan
        return o

    umb = np.maximum(p90, UMBRAL_MIN)
    with np.errstate(all="ignore"):
        rel = z / umb
        reg = np.nansum(z, axis=1, keepdims=True) / np.nansum(umb, axis=1, keepdims=True)
        frac = np.nanmean(a, axis=1, keepdims=True)
    reg[np.isnan(p90).all(axis=1) | np.isnan(z).all(axis=1)] = np.nan

    def rep(v):
        return np.repeat(v, n_z, axis=1)

    feat = {
        "lag1": lag(z, 1),
        "lag2": lag(z, 2),
        "lag3": lag(z, 3),
        "lag4": lag(z, 4),
        "rel1": lag(rel, 1),
        "rel2": lag(rel, 2),
        "rel3": lag(rel, 3),
        "rel4": lag(rel, 4),
        "rel52": lag(rel, 52 - h + 1),
        "anom_lag1": lag(a, 1),
        "anom_lag2": lag(a, 2),
        "p50_T": p50,
        "p90_T": p90,
        "freq_hist": fr,
        "region_rel_lag1": lag(rep(reg), 1),
        "region_anom_lag1": lag(rep(frac), 1),
    }
    d = pd.DataFrame(
        {
            "zona_id": np.tile(zonas, n_w),
            "semana": np.repeat(sem.semana.to_numpy(), n_z),
            "anio": np.repeat(sem.anio.to_numpy(), n_z),
            "woy": np.repeat(sem.woy.to_numpy(), n_z),
            "mes": np.repeat(sem.semana.dt.month.to_numpy(), n_z),
            "era": np.repeat(era, n_z),
            "zf": np.tile(zonas // 100, n_w),
            "zc": np.tile(zonas % 100, n_w),
            "valor": z.ravel(),
            "p50": p50.ravel(),
            "p90": p90.ravel(),
            "anomalia": a.ravel(),
        }
    )
    for k, x in feat.items():
        d[k] = x.ravel()
    if clima is not None:
        c = clima.copy()
        c["semana"] = c.semana + pd.Timedelta(weeks=h - 1)  # clima conocido en T-h
        d = d.merge(c, on=["semana", "zf", "zc"], how="left")
    return d


def columnas(con_clima: bool) -> list[str]:
    base = [
        "woy",
        "mes",
        "zf",
        "zc",
        "lag1",
        "lag2",
        "lag3",
        "lag4",
        "rel1",
        "rel2",
        "rel3",
        "rel4",
        "rel52",
        "anom_lag1",
        "anom_lag2",
        "p50_T",
        "p90_T",
        "freq_hist",
        "region_rel_lag1",
        "region_anom_lag1",
    ]
    return base + (FEATS_CLIMA if con_clima else [])


class BurnModel:
    """Entrena con la historia armonizada (2002-2025) y predice semanas nuevas (NRT)."""

    def __init__(self, data_dir: Path | str) -> None:
        d = Path(data_dir) / "prediccion"
        self.zs_hist = pd.read_parquet(d / "zonas_semana_hist.parquet")
        self.sem_hist = pd.read_parquet(d / "semanas_hist.parquet")
        self.zonas_df = pd.read_parquet(d / "zonas.parquet")
        self.power_hist = pd.read_parquet(d / "power_daily.parquet")
        self.zonas = np.sort(self.zonas_df.zona_id.to_numpy())
        self.modelos: dict[int, HistGradientBoostingClassifier] = {}

    def _combinar(self, zs_nuevas, sem_nuevas, power_nuevo):
        zs = pd.concat([self.zs_hist, zs_nuevas], ignore_index=True)
        sem = pd.concat(
            [self.sem_hist.assign(observado=self.sem_hist.valido), sem_nuevas], ignore_index=True
        )
        sem = preparar_semanas(sem.drop_duplicates("semana", keep="last"))
        power = (
            pd.concat([self.power_hist, power_nuevo], ignore_index=True)
            if power_nuevo is not None and len(power_nuevo)
            else self.power_hist
        )
        return zs, sem, clima_semanal(power)

    def entrenar(self, horizontes=(1, 2)) -> None:
        sem = preparar_semanas(self.sem_hist)
        z = matriz(self.zs_hist, sem, self.zonas)
        clima = clima_semanal(self.power_hist)
        for h in horizontes:
            t = tabla(z, sem, self.zonas, clima, h)
            t = t[t.anomalia.notna()]
            self.modelos[h] = HistGradientBoostingClassifier(**PARAMS).fit(
                t[columnas(True)], t.anomalia.astype(int)
            )

    def predecir(
        self,
        zs_nuevas: pd.DataFrame,
        sem_nuevas: pd.DataFrame,
        power_nuevo: pd.DataFrame | None,
        objetivos: dict[int, list],
    ) -> pd.DataFrame:
        """objetivos: {horizonte: [semanas (Timestamp lunes) a predecir con ese horizonte]}."""
        zs, sem, clima = self._combinar(zs_nuevas, sem_nuevas, power_nuevo)
        z = matriz(zs, sem, self.zonas)
        salida = []
        for h, semanas in objetivos.items():
            if not semanas:
                continue
            t = tabla(z, sem, self.zonas, clima, h)
            t = t[t.semana.isin(pd.to_datetime(semanas))].copy()
            t["prob"] = self.modelos[h].predict_proba(t[columnas(True)])[:, 1]
            t["horizonte"] = h
            salida.append(
                t[
                    [
                        "zona_id",
                        "semana",
                        "horizonte",
                        "valor",
                        "p50",
                        "p90",
                        "anomalia",
                        "freq_hist",
                        "prob",
                    ]
                ]
            )
        return pd.concat(salida, ignore_index=True)

    def predict(self, lat_min, lat_max, lon_min, lon_max):  # compatibilidad con el stub original
        raise NotImplementedError("Usar prediction_service.get_predictions (lee el cache).")
