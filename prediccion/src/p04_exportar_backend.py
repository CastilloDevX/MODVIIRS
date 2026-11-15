"""p04 - Exporta los artefactos que necesita el backend Flask (backend/data/prediccion/).

Uso: python prediccion/src/p04_exportar_backend.py   (despues de p01 y p02 clima 1 / sinclima 1 / clima 2)
"""
import json
import shutil
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
import config as C

DEST = C.RAIZ.parent / "backend" / "data" / "prediccion"
DEST.mkdir(parents=True, exist_ok=True)

act = pd.read_parquet(C.PROC / "actividad_celda_semana.parquet")
cel = pd.read_parquet(C.PROC / "celdas.parquet")
sem = pd.read_parquet(C.PROC / "semanas.parquet")
z = (act.merge(cel[["cell_id", "zona_id"]], on="cell_id").groupby(["zona_id", "semana"]).valor.sum().reset_index())
z.to_parquet(DEST / "zonas_semana_hist.parquet", index=False)
sem.to_parquet(DEST / "semanas_hist.parquet", index=False)
zon = pd.DataFrame({"zona_id": np.sort(cel.zona_id.unique())})
zon["zf"], zon["zc"] = zon.zona_id // 100, zon.zona_id % 100
zon["lat_min"] = (C.S + zon.zf * C.TAM_CELDA * C.CELDAS_POR_ZONA).round(4)
zon["lon_min"] = (C.W + zon.zc * C.TAM_CELDA * C.CELDAS_POR_ZONA).round(4)
zon.to_parquet(DEST / "zonas.parquet", index=False)
shutil.copy(C.POWER, DEST / "power_daily.parquet")
pr = pd.read_parquet(C.PROC / "pred_clima_h1.parquet")
pr.to_parquet(DEST / "pred_historico.parquet", index=False)

met = {t: pd.read_csv(C.OUT / f"metricas_{t}.csv") for t in ["clima_h1", "sinclima_h1", "clima_h2"]}
cal = pd.read_csv(C.OUT / "calibracion_clima_h1.csv")
v = lambda m: m[m.era == "VIIRS"]
a, b = met["sinclima_h1"], met["clima_h1"]
mm = a.merge(b, on="anio", suffixes=("_s", "_c"))
mm = mm[mm.n_c > 1000]
res = lambda m: {k: round(float(v(m)[k].mean()), 4) for k in ["auc", "auc_base", "ap", "ap_base", "brier", "brier_base"]}
val = {
    "descripcion": "Validacion walk-forward (cada anio predicho con un modelo entrenado solo con anios anteriores). "
                   "Anomalia = dias-con-fuego de la zona (0.5 deg) > max(p90 historico de su era, 3).",
    "periodo_resumen": "era VIIRS 2015-2025",
    "resumen_h1": res(met["clima_h1"]), "resumen_h1_sin_clima": res(met["sinclima_h1"]),
    "resumen_h2": res(met["clima_h2"]),
    "wilcoxon_clima": {"anios": int(len(mm)), "anios_mejor": int((mm.ap_c > mm.ap_s).sum()),
                       "p_ap": round(float(wilcoxon(mm.ap_c, mm.ap_s).pvalue), 4)},
    "metricas_por_anio": met["clima_h1"].round(4).to_dict(orient="records"),
    "calibracion": cal.round(4).to_dict(orient="records"),
    "falsas_anomalias": pd.read_csv(C.OUT / "tasa_anomalias_mezclada_vs_por_era.csv", index_col=0)
                           .round(2).reset_index().rename(columns={"index": "anio"}).to_dict(orient="records"),
}
(DEST / "validacion.json").write_text(json.dumps(val, ensure_ascii=False, indent=1, default=lambda x: None))
print("exportado a", DEST, [p.name for p in DEST.iterdir()])
print(json.dumps({k: val[k] for k in ["resumen_h1", "resumen_h1_sin_clima", "resumen_h2", "wilcoxon_clima"]}, indent=1))
