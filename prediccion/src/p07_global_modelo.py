"""Modelo de anomalias para los 6 paises (zonas de 1 grado, sin clima) + walk-forward.

Misma definicion que la peninsula (backend/src/modviirs/models/burn_model.py):
anomalia = actividad > max(p90, 3), p90 de la misma zona, woy +-2, anios previos, misma era.
Eras VIIRS de la armonizacion de Alexis (sensor_group VIIRS, multiplataforma):
  era 0: 2012-01-20 .. 2018-03-31 (solo S-NPP)   era 1: 2018-04-01 .. (S-NPP + NOAA-20)
Sin clima POWER (inviable para ~3k zonas en el tiempo del hackaton; el modelo sin clima
de la peninsula tiene AUC 0.841 vs 0.853 con clima).
Salidas en backend/data/prediccion/:
  pred_global.parquet     pais, zona_id, lat0, lon0, semana, horizonte, valor, p50, p90,
                          anomalia, freq_hist, prob
  validacion_global.json  metricas por pais y anio (AUC, AP, Brier vs linea base freq_hist)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "backend/src"))
from modviirs.models.burn_model import (  # noqa: E402
    FEATS_CLIMA, PARAMS, columnas, matriz, preparar_semanas, tabla,
)
import os  # noqa: E402

ZS = RAIZ / "prediccion/data/global_zs.parquet"
OUT = RAIZ / "backend/data/prediccion"
MIN_TOTAL = 20          # dias-fuego minimos en 2012-2025 para modelar una zona
ANIOS_TEST = [2023, 2024, 2025]
INICIO, FIN = pd.Timestamp("2012-01-20"), pd.Timestamp("2025-12-31")
CAMBIO_ERA = pd.Timestamp("2018-04-01")

# CLIMA=1 -> variante con NASA POWER por zona (prediccion/data/power_global.parquet, p08)
CLIMA = os.environ.get("CLIMA") == "1"
SUF = "_clima" if CLIMA else ""
TMP = RAIZ / f"prediccion/data/global_tmp{SUF}"
TMP.mkdir(exist_ok=True)
FEATS = columnas(False) + ["pais_c"] + (FEATS_CLIMA if CLIMA else [])


def clima_zonas(zonas):
    """POWER diario por zona -> valor al lunes con los dias ANTERIORES (como burn_model)."""
    pw = pd.read_parquet(RAIZ / "prediccion/data/power_global.parquet",
                         filters=[("zona_id", "in", [int(z) for z in zonas])])
    out = []
    for zid, s in pw.sort_values("fecha").groupby("zona_id"):
        s = s.drop_duplicates("fecha").set_index("fecha").asfreq("D").ffill()
        c = pd.DataFrame({
            "lluvia_30d": s.PRECTOTCORR.rolling(30).sum(),
            "lluvia_90d": s.PRECTOTCORR.rolling(90).sum(),
            "dias_sin_lluvia": s.PRECTOTCORR.lt(1).groupby(s.PRECTOTCORR.ge(1).cumsum()).cumsum(),
            "hr_7d": s.RH2M.rolling(7).mean(),
            "tmax_7d": s.T2M_MAX.rolling(7).mean(),
            "viento_7d": s.WS10M.rolling(7).mean(),
        }).shift(1)
        c = c[c.index.weekday == 0].rename_axis("semana").reset_index()
        woy = np.minimum((c.semana.dt.dayofyear - 1) // 7 + 1, 52)
        c["lluvia_90d_anom"] = c.lluvia_90d - c.groupby(woy).lluvia_90d.transform(
            lambda x: x.shift(1).expanding().mean())
        c["zona_id"] = zid
        out.append(c)
    if not out:
        return pd.DataFrame(columns=["semana", "zona_id", *FEATS_CLIMA])
    return pd.concat(out, ignore_index=True)
PAISES = ["Angola", "Australia", "Brazil", "Democratic_Republic_of_the_Congo", "Mexico",
          "Russian_Federation"]


def semanas():
    lunes = pd.date_range(INICIO - pd.Timedelta(days=INICIO.weekday()), FIN, freq="W-MON")
    sem = pd.DataFrame({"semana": lunes})
    sem["era"] = (sem.semana + pd.Timedelta(days=6) >= CAMBIO_ERA).astype(int)
    # semanas incompletas (inicio/fin de datos, cambio de era) -> no validas
    fin_sem = sem.semana + pd.Timedelta(days=6)
    sem["valido"] = (sem.semana >= INICIO) & (fin_sem <= FIN)
    sem.loc[(sem.semana < CAMBIO_ERA) & (fin_sem >= CAMBIO_ERA), "valido"] = False
    return preparar_semanas(sem)


def etapa_tabla(pais, parte=None, n_partes=2, solo_clima=False):
    """Tabla de variables (H1 y H2) de un pais -> global_tmp/tabla_<pais>[_<parte>].parquet
    Paises muy grandes (Rusia) se parten por longitud en n_partes (limite de tiempo por paso);
    la senal regional se calcula entonces por cada parte."""
    i = PAISES.index(pais)
    sem = semanas()
    g = pd.read_parquet(ZS, filters=[("pais", "=", pais)])
    tot = g.groupby("zona_id").valor.sum()
    zonas = np.sort(tot[tot >= MIN_TOTAL].index.to_numpy())
    if parte is not None:  # zona_id = (lat+90)*1000 + (lon+180): partir por longitud
        lon = zonas % 1000
        corte = np.quantile(lon, np.linspace(0, 1, n_partes + 1))
        sel = (lon >= corte[parte]) & ((lon < corte[parte + 1]) | (parte == n_partes - 1))
        zonas = zonas[sel]
    geo = g.drop_duplicates("zona_id").set_index("zona_id").loc[zonas, ["lat0", "lon0"]]
    z = matriz(g[g.zona_id.isin(zonas)], sem, zonas)
    suf = "" if parte is None else f"_{parte}"
    cache = TMP / f"clima_{pais}{suf}.parquet"
    if solo_clima:  # etapa previa para paises grandes (limite de tiempo por paso)
        clima_zonas(zonas).to_parquet(cache, index=False)
        print("clima", pais, parte, len(zonas))
        return
    cl = None
    if CLIMA:
        cl = pd.read_parquet(cache) if cache.exists() else clima_zonas(zonas)
    out = []
    for h in (1, 2):
        t = tabla(z, sem, zonas, None, h)
        t["zf"] = np.tile(geo.lat0.to_numpy(), len(sem))
        t["zc"] = np.tile(geo.lon0.to_numpy(), len(sem))
        t["pais"], t["pais_c"], t["horizonte"] = pais, i, h
        t = t[sem.valido.repeat(len(zonas)).to_numpy()]
        if cl is not None:  # clima conocido en T-h
            c = cl.assign(semana=cl.semana + pd.Timedelta(weeks=h - 1))
            t = t.merge(c, on=["semana", "zona_id"], how="left")
        num = t.select_dtypes("float64").columns
        t[num] = t[num].astype("float32")
        out.append(t)
    pd.concat(out).to_parquet(TMP / f"tabla_{pais}{suf}.parquet", index=False)
    print(pais, len(zonas), "zonas")


def leer(h, cols=None, filtro=None):
    f = [("horizonte", "=", h)] + (filtro or [])
    return pd.concat([pd.read_parquet(p, columns=cols, filters=f)
                      for p in sorted(TMP.glob("tabla_*.parquet"))], ignore_index=True)


def etapa_fit(h, y):
    tr = leer(h, FEATS + ["anomalia"], [("anio", "<", y)])
    tr = tr[tr.anomalia.notna()]
    m = HistGradientBoostingClassifier(**PARAMS).fit(tr[FEATS], tr.anomalia.astype(int))
    te = leer(h, filtro=[("anio", "=", y)])
    te["prob"] = m.predict_proba(te[FEATS])[:, 1]
    te["lat0"], te["lon0"] = te.zf.astype("int16"), te.zc.astype("int16")
    cols = ["pais", "zona_id", "lat0", "lon0", "semana", "horizonte", "valor", "p50", "p90",
            "anomalia", "freq_hist", "prob"]
    te[cols].to_parquet(TMP / f"pred_h{h}_{y}.parquet", index=False)
    print("h", h, "anio", y, "train", len(tr), "test", len(te))


def etapa_final():
    P = pd.concat([pd.read_parquet(f) for f in sorted(TMP.glob("pred_h*_*.parquet"))],
                  ignore_index=True)
    P.to_parquet(OUT / f"pred_global{SUF}.parquet", index=False)
    met = []
    e1 = P[(P.horizonte == 1) & P.anomalia.notna()]
    for (pais, y), e in e1.groupby(["pais", e1.semana.dt.year]):
        yv, p, b = e.anomalia.astype(int), e.prob, e.freq_hist.fillna(0)
        if yv.nunique() < 2:
            continue
        met.append(dict(pais=pais, anio=int(y), n=len(e), anomalias=int(yv.sum()),
                        auc=roc_auc_score(yv, p), ap=average_precision_score(yv, p),
                        brier=brier_score_loss(yv, p), auc_base=roc_auc_score(yv, b),
                        ap_base=average_precision_score(yv, b),
                        brier_base=brier_score_loss(yv, b)))
    M = pd.DataFrame(met)
    agg = M.groupby("pais")[["auc", "ap", "brier", "auc_base", "ap_base", "brier_base"]].mean()
    res = {"descripcion": "Walk-forward H1 por pais (entrena con anios < anio de prueba). "
           "Zonas de 1 grado, VIIRS armonizado (Alexis)"
           + (", con clima NASA POWER." if CLIMA else ", sin clima."),
           "anios_prueba": ANIOS_TEST,
           "por_pais_anio": M.round(4).to_dict("records"),
           "por_pais": agg.round(4).reset_index().to_dict("records")}
    res["clima_nasa_power"] = CLIMA
    (OUT / f"validacion_global{SUF}.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(agg.round(3))
    print("OK", len(P))


if __name__ == "__main__":
    # uso: [clima <pais> [parte]] | tabla <pais> [parte] | fit <h> <anio> | final
    a = sys.argv[1:]
    if a[0] == "clima":
        etapa_tabla(a[1], int(a[2]) if len(a) > 2 else None, solo_clima=True)
    elif a[0] == "tabla":
        etapa_tabla(a[1], int(a[2]) if len(a) > 2 else None)
    elif a[0] == "fit":
        etapa_fit(int(a[1]), int(a[2]))
    else:
        etapa_final()
