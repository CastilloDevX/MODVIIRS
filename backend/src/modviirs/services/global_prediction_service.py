"""Prediccion para los 6 paises de la armonizacion de Alexis (zonas de 1 grado).

Fuente: data/prediccion/pred_global.parquet y validacion_global.json, generados por
prediccion/src/p06_global_actividad.py + p07_global_modelo.py (walk-forward 2023-2025, H1/H2,
VIIRS armonizado multiplataforma, eras S-NPP / S-NPP+NOAA-20, clima NASA POWER por zona:
AUC 0.839 vs 0.833 sin clima, mejor en 18/18 pares pais-anio, Wilcoxon p=0.0002).
La peninsula de Yucatan conserva su modelo propio (0.5 deg, clima NASA POWER, en vivo 2026).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from modviirs.services import prediction_service as pen

TAM = 1.0
NOMBRES = {
    "Mexico": "México",
    "Brazil": "Brasil",
    "Russian_Federation": "Rusia",
    "Australia": "Australia",
    "Angola": "Angola",
    "Democratic_Republic_of_the_Congo": "RD del Congo",
}
AVISO = (
    "Probabilidad de actividad ANOMALA de puntos de calor por zona de 1 grado (~110 km): "
    "dias-con-fuego por encima del p90 historico de la zona en esas fechas. Variables: "
    "historia de la zona y clima NASA POWER. Prediccion walk-forward (cada anio con un "
    "modelo entrenado solo con anios previos). "
    "Un punto de calor no es un incendio."
)


def _ruta(cfg, nombre) -> Path:
    return pen.data_dir(cfg) / "prediccion" / nombre


@lru_cache(maxsize=2)
def _leer(ruta: str, mtime: float) -> pd.DataFrame:
    return pd.read_parquet(ruta)


def disponible(cfg) -> bool:
    return _ruta(cfg, "pred_global.parquet").exists()


def tabla(cfg) -> pd.DataFrame:
    r = _ruta(cfg, "pred_global.parquet")
    return _leer(str(r), r.stat().st_mtime)


def _filtrar(t: pd.DataFrame, bbox) -> pd.DataFrame:
    if bbox is None:
        return t
    la0, la1, lo0, lo1 = bbox
    return t[(t.lat0 < la1) & (t.lat0 + TAM > la0) & (t.lon0 < lo1) & (t.lon0 + TAM > lo0)]


def paises(cfg) -> list[dict]:
    t = tabla(cfg)
    val = pen._json(_ruta(cfg, "validacion_global.json")) or {}
    met = {m["pais"]: m for m in val.get("por_pais", [])}
    z = t.drop_duplicates(["pais", "zona_id"])
    out = []
    for p, g in z.groupby("pais"):
        m = met.get(p, {})
        out.append(
            {
                "pais": p,
                "nombre": NOMBRES.get(p, p),
                "zonas": int(len(g)),
                "bbox": {
                    "west": int(g.lon0.min()),
                    "south": int(g.lat0.min()),
                    "east": int(g.lon0.max()) + 1,
                    "north": int(g.lat0.max()) + 1,
                },
                "auc": m.get("auc"),
                "auc_base": m.get("auc_base"),
                "ap": m.get("ap"),
                "ap_base": m.get("ap_base"),
            }
        )
    sem = t.semana
    return {
        "paises": out,
        "semanas": {"desde": str(sem.min().date()), "hasta": str(sem.max().date())},
        "aviso": AVISO,
    }


def get_week(cfg, semana: str, bbox=None, horizonte: int = 1):
    t = tabla(cfg)
    g = _filtrar(t[(t.semana == pd.Timestamp(semana)) & (t.horizonte == horizonte)], bbox)
    if g.empty:
        return None

    def num(v, d=1):
        return None if pd.isna(v) else round(float(v), d)

    feats = []
    for r in g.itertuples():
        lat, lon = float(r.lat0), float(r.lon0)
        ring = [[lon, lat], [lon + TAM, lat], [lon + TAM, lat + TAM], [lon, lat + TAM], [lon, lat]]
        props = {
            "zona_id": int(r.zona_id),
            "pais": r.pais,
            "prob": round(float(r.prob), 3),
            "nivel": pen.nivel(r.prob),
            "base": num(r.freq_hist, 3),
            "p50": num(r.p50),
            "p90": num(r.p90),
            "valor": num(r.valor),
            "anomalia": None if pd.isna(r.anomalia) else int(r.anomalia),
        }
        feats.append(
            {
                "type": "Feature",
                "id": int(r.zona_id),
                "properties": props,
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            }
        )
    probs = g.prob
    return {
        "type": "FeatureCollection",
        "features": feats,
        "resumen": {
            "zonas": len(feats),
            "prob_max": round(float(probs.max()), 3),
            "zonas_alto": int((probs >= pen.NIVELES[0][0]).sum()),
            "esperadas": round(float(probs.sum()), 2),
        },
        "semana": semana,
        "horizonte_semanas": horizonte,
        "fuente": "historico_walk_forward",
        "escala": "global_1deg",
        "aviso": AVISO,
    }


def get_series(cfg, bbox=None, start: str = "2023-01-02", end: str | None = None) -> dict:
    t = tabla(cfg)
    t = _filtrar(t[t.horizonte == 1], bbox)
    t = t[t.semana >= pd.Timestamp(start)]
    if end:
        t = t[t.semana <= pd.Timestamp(end)]
    num = ["prob", "valor", "p50", "p90", "anomalia"]
    t = t.assign(**{c: t[c].astype("float64") for c in num})
    t = t.assign(alto=t.prob >= pen.NIVELES[0][0])
    g = t.groupby("semana")
    s = pd.DataFrame(
        {
            "zonas": g.zona_id.size(),
            "prob_max": g.prob.max().round(3),
            "prob_media": g.prob.mean().round(3),
            "esperadas": g.prob.sum().round(2),
            "zonas_alto": g.alto.sum(),
            "valor": g.valor.sum(min_count=1).round(1),
            "p50": g.p50.sum(min_count=1).round(1),
            "p90": g.p90.sum(min_count=1).round(1),
            "anomalias": g.anomalia.sum(min_count=1),
        }
    ).reset_index()
    s.insert(1, "fuente", "historico")
    s["semana"] = s.semana.dt.strftime("%Y-%m-%d")
    s = s.astype(object).where(s.notna(), None)
    ps = sorted(t.pais.unique().tolist())
    return {
        "escala": "global_1deg",
        "tam_zona_grados": TAM,
        "paises": [NOMBRES.get(p, p) for p in ps],
        "zonas": sorted(int(z) for z in t.zona_id.unique()),
        "data": s.to_dict(orient="records"),
        "aviso": AVISO,
    }


def usa_peninsula(bbox) -> bool:
    """True si >= 50 % del bbox cae dentro de la peninsula (modelo 0.5 deg con clima, en vivo)."""
    if bbox is None:
        return True
    la0, la1, lo0, lo1 = bbox
    w, s, e, n = pen.BBOX
    inter = max(0.0, min(la1, n) - max(la0, s)) * max(0.0, min(lo1, e) - max(lo0, w))
    area = max(1e-9, (la1 - la0) * (lo1 - lo0))
    return inter / area >= 0.5
