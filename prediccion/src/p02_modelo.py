"""p02 - Modelo de anomalias semanales por zona sobre la armonizacion de Alexis.

"El sistema anticipa con X% de probabilidad un comportamiento anomalo de puntos de calor
 en la semana T en la zona Z."

Uso:  python prediccion/src/p02_modelo.py [clima|sinclima] [horizonte_semanas]
      (por defecto: clima 1)

- Anomalia (Z,T): dias-con-fuego de la zona > max(p90, 3), con p90 calculado SOLO con anios
  anteriores de la MISMA era (Aqua vs Aqua, S-NPP vs S-NPP) -> la normalizacion por era de Alexis.
- Variables: solo informacion hasta T-H. Rezagos que crucen el cambio de era o caigan en huecos -> NaN.
  Rezagos en dos escalas: crudos y relativos al umbral de su era (lag/max(p90,3)), para que el modelo
  no confunda la escala MODIS con la VIIRS (no se usa la era como variable).
- Modelo: HistGradientBoostingClassifier. Validacion walk-forward: para cada anio Y entrena con < Y.
- Linea base: frecuencia historica de anomalias (misma zona, semana del anio y era).
Salidas: data/processed/pred_<tag>.parquet, outputs/metricas_<tag>.csv, outputs/calibracion_<tag>.csv,
         outputs/figures/modelo_<tag>.png
"""
import sys
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import config as C
from anomalias import cargar_matriz, percentiles_historicos, anomalias, frecuencia_historica

MODO = sys.argv[1] if len(sys.argv) > 1 else "clima"
H = int(sys.argv[2]) if len(sys.argv) > 2 else 1
TAG = f"{MODO}_h{H}"

Z, sem, zonas = cargar_matriz()
P50, P90, NA = percentiles_historicos(Z, sem, por_era=True)
A = anomalias(Z, P90)
FR = frecuencia_historica(A, sem, por_era=True)
nW, nZ = Z.shape
era = sem.era.to_numpy()


def lag(X, k):
    """Valor de X en T-(k+H-1); NaN si cruza el cambio de era."""
    k = k + H - 1
    o = np.full_like(X, np.nan, dtype=float)
    o[k:] = X[:-k]
    cruza = np.r_[np.ones(k, bool), era[k:] != era[:-k]]
    o[cruza] = np.nan
    return o


UMB = np.maximum(P90, C.UMBRAL_MIN)
R = Z / UMB                                           # actividad relativa al umbral de su era
reg = np.nansum(Z, axis=1, keepdims=True) / np.nansum(UMB, axis=1, keepdims=True)
reg[np.isnan(P90).all(axis=1)] = np.nan
frac = np.nanmean(A, axis=1, keepdims=True) if True else None
rep = lambda v: np.repeat(v, nZ, axis=1)
feat = {
    "lag1": lag(Z, 1), "lag2": lag(Z, 2), "lag3": lag(Z, 3), "lag4": lag(Z, 4),
    "rel1": lag(R, 1), "rel2": lag(R, 2), "rel3": lag(R, 3), "rel4": lag(R, 4),
    "rel52": lag(R, 52 - H + 1) if H <= 52 else np.full_like(Z, np.nan),
    "anom_lag1": lag(A, 1), "anom_lag2": lag(A, 2),
    "p50_T": P50, "p90_T": P90, "freq_hist": FR,
    "region_rel_lag1": lag(rep(reg), 1),
    "region_anom_lag1": lag(rep(frac), 1),
}
d = pd.DataFrame({
    "zona_id": np.tile(zonas, nW), "semana": np.repeat(sem.semana.to_numpy(), nZ),
    "anio": np.repeat(sem.anio.to_numpy(), nZ), "woy": np.repeat(sem.woy.to_numpy(), nZ),
    "mes": np.repeat(sem.semana.dt.month.to_numpy(), nZ), "era": np.repeat(era, nZ),
    "zf": np.tile(zonas // 100, nW), "zc": np.tile(zonas % 100, nW),
    "valor": Z.ravel(), "p50": P50.ravel(), "p90": P90.ravel(), "anomalia": A.ravel(),
})
for k, X in feat.items():
    d[k] = X.ravel()
FEATS = ["woy", "mes", "zf", "zc"] + list(feat)

if MODO == "clima":
    pw = pd.read_parquet(C.POWER).sort_values("fecha")
    pw["zf"] = np.clip(np.round((pw.lat - 18.0) / 0.5), 0, 7).astype(int)
    pw["zc"] = np.clip(np.round((pw.lon + 92.25) / 0.5), 0, 11).astype(int)
    out = []
    for (zf, zc), s in pw.groupby(["zf", "zc"]):
        s = s.set_index("fecha")
        c = pd.DataFrame({
            "lluvia_30d": s.PRECTOTCORR.rolling(30).sum(),
            "lluvia_90d": s.PRECTOTCORR.rolling(90).sum(),
            "dias_sin_lluvia": s.PRECTOTCORR.lt(1).groupby(s.PRECTOTCORR.ge(1).cumsum()).cumsum(),
            "hr_7d": s.RH2M.rolling(7).mean(), "tmax_7d": s.T2M_MAX.rolling(7).mean(),
            "viento_7d": s.WS10M.rolling(7).mean()}).shift(1)
        c = c[c.index.weekday == 0]
        c["zf"], c["zc"] = zf, zc
        out.append(c.rename_axis("semana").reset_index())
    cl = pd.concat(out)
    cl["woy"] = np.minimum((cl.semana.dt.dayofyear - 1) // 7 + 1, 52)
    cl = cl.sort_values("semana")
    cl["lluvia_90d_anom"] = cl.lluvia_90d - cl.groupby(["zf", "zc", "woy"]).lluvia_90d.transform(
        lambda x: x.shift(1).expanding().mean())
    cl["semana"] = cl.semana + pd.Timedelta(weeks=H - 1)          # clima conocido en T-H
    d = d.merge(cl.drop(columns="woy"), on=["semana", "zf", "zc"], how="left")
    FEATS += ["lluvia_30d", "lluvia_90d", "lluvia_90d_anom", "dias_sin_lluvia", "hr_7d", "tmax_7d", "viento_7d"]

d = d[d.anomalia.notna()].reset_index(drop=True)
d["anomalia"] = d.anomalia.astype(int)
filas, preds = [], []
for Y in sorted(d.anio.unique()):
    tr, te = d[d.anio < Y], d[d.anio == Y].copy()
    if tr.anio.nunique() < 3 or te.anomalia.nunique() < 2:
        continue
    m = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_leaf_nodes=15,
                                       l2_regularization=1.0, random_state=0).fit(tr[FEATS], tr.anomalia)
    te["prob"] = m.predict_proba(te[FEATS])[:, 1]
    te["base"] = te.freq_hist.fillna(tr.anomalia.mean())
    filas.append({"anio": Y, "era": te.era.iat[-1], "n": len(te), "tasa_anom": te.anomalia.mean(),
                  "prob_media": te.prob.mean(),
                  "auc": roc_auc_score(te.anomalia, te.prob), "auc_base": roc_auc_score(te.anomalia, te.base),
                  "ap": average_precision_score(te.anomalia, te.prob),
                  "ap_base": average_precision_score(te.anomalia, te.base),
                  "brier": brier_score_loss(te.anomalia, te.prob),
                  "brier_base": brier_score_loss(te.anomalia, te.base)})
    preds.append(te[["zona_id", "semana", "era", "valor", "p50", "p90", "anomalia", "prob", "base"]])
met = pd.DataFrame(filas)
pr = pd.concat(preds)
met.to_csv(C.OUT / f"metricas_{TAG}.csv", index=False)
pr.to_parquet(C.PROC / f"pred_{TAG}.parquet", index=False)
pr["bin"] = pd.cut(pr.prob, [0, .05, .1, .2, .3, .5, .7, 1], include_lowest=True)
cal = pr.groupby("bin", observed=True).agg(prob_media=("prob", "mean"), observado=("anomalia", "mean"),
                                          n=("anomalia", "size"))
cal.to_csv(C.OUT / f"calibracion_{TAG}.csv")

fig, ax = plt.subplots(1, 3, figsize=(15, 4))
ax[0].plot(met.anio, met.auc, "o-", label="modelo"); ax[0].plot(met.anio, met.auc_base, "s--", label="frecuencia histórica")
ax[0].set_title("AUC por año (fuera de muestra)")
ax[1].plot(met.anio, met.tasa_anom * 100, "o-", color="k", label="observado")
ax[1].plot(met.anio, met.prob_media * 100, "s--", color="tab:red", label="predicho (media)")
ax[1].set_title("% de zona-semanas anómalas")
ax[2].plot([0, 1], [0, 1], ":", color="gray"); ax[2].plot(cal.prob_media, cal.observado, "o-")
ax[2].set_xlabel("probabilidad predicha"); ax[2].set_ylabel("frecuencia observada"); ax[2].set_title("Calibración")
for a in ax[:2]:
    a.axvspan(2011.5, 2014.5, color="gray", alpha=.12); a.legend(fontsize=8); a.grid(alpha=.3)
ax[2].grid(alpha=.3)
fig.suptitle(f"Anomalías semanales por zona – armonización Alexis (por era) – {TAG}  (gris: era VIIRS sin línea base)")
fig.tight_layout(); fig.savefig(C.FIG / f"modelo_{TAG}.png", dpi=140)

v = met[met.era == "VIIRS"]
print(met.round(3).to_string(index=False))
print(f"\nEra VIIRS ({v.anio.min()}-{v.anio.max()}): AUC {v.auc.mean():.3f} (base {v.auc_base.mean():.3f}) | "
      f"AP {v.ap.mean():.3f} (base {v.ap_base.mean():.3f}) | Brier {v.brier.mean():.4f} (base {v.brier_base.mean():.4f})")
print(cal.round(3).to_string())
