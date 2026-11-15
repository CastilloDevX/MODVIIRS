"""Servicio de prediccion: actualizacion por lotes (NRT) y lectura rapida del cache.

Flujo de `actualizar()` (CLI: `flask --app wsgi prediction-update`, tarda ~1-2 min):
  1. FIRMS Area API, VIIRS NOAA-20: SP (ene-2026 .. fin de SP) + NRT (hasta hoy), peninsula.
  2. Reglas de la armonizacion de Alexis: confianza n+h, sin fuentes persistentes
     (persistent_mask), sin duplicados.
  3. Dias-con-fuego por celda 0.1 deg y semana -> suma por zona 0.5 deg.
  4. NASA POWER diario 2026 (65 puntos, uno por zona).
  5. BurnModel: entrena con 2002-2025 (segundos) y predice:
       - todas las semanas 2026 ya observadas (H=1, fuera de muestra) -> validacion "en vivo" 2026
       - semana en curso (H=1) y semana proxima (H=2)
  6. Guarda data/prediccion/cache/prediccion_actual.json (lo leen los endpoints en milisegundos).
"""

from __future__ import annotations

import json
import logging
import math
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from modviirs.clients.firms_client import FIRMSClient
from modviirs.clients.power_client import PowerClient
from modviirs.models.burn_model import TAM_ZONA, BurnModel

log = logging.getLogger(__name__)

BBOX = (-92.5, 17.8, -86.7, 21.7)  # W, S, E, N
S, W, TAM_CELDA = 17.8, -92.5, 0.1
FUENTE_SP, FUENTE_NRT = "VIIRS_NOAA20_SP", "VIIRS_NOAA20_NRT"
INICIO_VIVO = date(2026, 1, 1)
NIVELES = [(0.30, "alto"), (0.10, "moderado"), (0.0, "bajo")]
AVISO = (
    "Probabilidad de actividad ANOMALA de puntos de calor (dias-con-fuego por encima del p90 "
    "historico de la zona en esas fechas). Un punto de calor no es un incendio."
)


def data_dir(config) -> Path:
    default = Path(__file__).resolve().parents[3] / "data"
    return Path(config.get("DATA_PATH") or default)


def cache_dir(config) -> Path:
    p = data_dir(config) / "prediccion" / "cache"
    p.mkdir(parents=True, exist_ok=True)
    return p


# ----------------------------------------------------------------- procesamiento de detecciones
def normalizar(det: pd.DataFrame, mascara: pd.DataFrame) -> pd.DataFrame:
    """Reglas de Alexis para VIIRS: confianza n/h, NOAA-20, sin persistentes, sin duplicados."""
    if det.empty:
        return det
    d = det.copy()
    d = d[d.confidence.astype(str).str.lower().str[0].isin(["n", "h"])]
    d = d[d.satellite.astype(str).isin(["N20", "NOAA-20", "J1"])]
    d = d.drop_duplicates(["latitude", "longitude", "acq_date", "acq_time"])
    d["py"] = np.floor(d.latitude / 0.01).astype("int64")
    d["px"] = np.floor(d.longitude / 0.01).astype("int64")
    d = d.merge(mascara[["py", "px"]].assign(_p=True), on=["py", "px"], how="left")
    return d[d._p.isna()].drop(columns=["_p"])


def actividad_por_zona(d: pd.DataFrame) -> pd.DataFrame:
    """Dias-con-fuego por celda 0.1 deg y semana (lunes), sumado por zona 0.5 deg."""
    if d.empty:
        return pd.DataFrame(columns=["zona_id", "semana", "valor"])
    d = d.copy()
    d["fecha"] = pd.to_datetime(d.acq_date)
    fila = np.floor((d.latitude - S) / TAM_CELDA + 1e-9).astype(int)
    col = np.floor((d.longitude - W) / TAM_CELDA + 1e-9).astype(int)
    d = d[(fila >= 0) & (fila < 39) & (col >= 0) & (col < 58)]
    fila, col = fila[d.index], col[d.index]
    d["cell_id"] = fila * 100 + col
    d["zona_id"] = (fila // 5) * 100 + col // 5
    d["semana"] = d.fecha - pd.to_timedelta(d.fecha.dt.weekday, unit="D")
    celda = d.groupby(["zona_id", "cell_id", "semana"]).fecha.nunique()
    celda = celda.rename("valor").reset_index()
    return celda.groupby(["zona_id", "semana"]).valor.sum().astype(float).reset_index()


# ----------------------------------------------------------------- descargas con cache
def descargar_firms(cfg, hoy: date) -> pd.DataFrame:
    client = FIRMSClient(cfg.get("FIRMS_MAP_KEY", ""))
    ruta = cache_dir(cfg) / "firms_noaa20_2026.parquet"
    disp = client.availability().set_index("data_id")
    fin_sp = min(disp.loc[FUENTE_SP, "max_date"].date(), hoy)
    viejo = pd.read_parquet(ruta) if ruta.exists() else pd.DataFrame()
    if len(viejo):
        # se conserva lo descargado; los ultimos 10 dias se vuelven a pedir (NRT se corrige)
        corte = min(pd.to_datetime(viejo.acq_date).max().date() - timedelta(days=10), hoy)
        viejo = viejo[pd.to_datetime(viejo.acq_date).dt.date < corte]
        desde = corte
    else:
        desde = INICIO_VIVO
    partes = [viejo]
    if desde <= fin_sp:
        partes.append(client.fetch_range(FUENTE_SP, BBOX, desde, fin_sp).assign(fuente="SP"))
        desde = fin_sp + timedelta(days=1)
    if desde <= hoy:
        partes.append(client.fetch_range(FUENTE_NRT, BBOX, desde, hoy).assign(fuente="NRT"))
    det = pd.concat([p for p in partes if len(p)], ignore_index=True)
    # SP trae version "2" y NRT "2.0NRT": todo texto para que el parquet acepte la mezcla
    texto = ["acq_date", "acq_time", "version", "confidence", "satellite", "instrument", "daynight"]
    for c in texto:
        if c in det:
            det[c] = det[c].astype(str)
    det.to_parquet(ruta, index=False)
    return det


def descargar_power(cfg, zonas: pd.DataFrame, hoy: date) -> pd.DataFrame:
    ruta = cache_dir(cfg) / "power_2026.parquet"
    viejo = pd.read_parquet(ruta) if ruta.exists() else pd.DataFrame()
    desde = INICIO_VIVO
    if len(viejo):
        desde = max(
            INICIO_VIVO, viejo.dropna(subset=["PRECTOTCORR"]).fecha.max().date() - timedelta(days=5)
        )
        viejo = viejo[viejo.fecha.dt.date < desde]
    client, partes = PowerClient(), [viejo]
    for z in zonas.itertuples():
        lat, lon = 18.0 + 0.5 * z.zf, -92.25 + 0.5 * z.zc  # mismo punto POWER que al entrenar
        try:
            partes.append(client.daily_point(lat, lon, desde, hoy))
        except Exception as e:  # noqa: BLE001 - un punto caido no detiene la actualizacion
            log.warning("POWER %s,%s fallo: %s", lat, lon, e)
    pw = pd.concat([p for p in partes if len(p)], ignore_index=True)
    pw.to_parquet(ruta, index=False)
    return pw


# ----------------------------------------------------------------- actualizacion completa
def semanas_objetivo(ultimo_dato: date, hoy: date):
    """Ultima semana completa observada y semanas a predecir (en curso H=1, proxima H=2)."""
    ultimo_completo = min(ultimo_dato, hoy - timedelta(days=1))
    lunes = ultimo_completo - timedelta(days=ultimo_completo.weekday())
    completa = lunes if ultimo_completo.weekday() == 6 else lunes - timedelta(days=7)
    return completa, completa + timedelta(days=7), completa + timedelta(days=14)


def nivel(p: float) -> str:
    return next(n for u, n in NIVELES if p >= u)


def actualizar(
    cfg,
    hoy: date | None = None,
    detecciones: pd.DataFrame | None = None,
    power: pd.DataFrame | None = None,
) -> dict:
    """Corre todo el flujo y escribe el cache (`detecciones`/`power` permiten simular)."""
    from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

    hoy = hoy or datetime.now(timezone.utc).date()  # noqa: UP017
    ddir = data_dir(cfg)
    modelo = BurnModel(ddir)
    det = detecciones if detecciones is not None else descargar_firms(cfg, hoy)
    mascara = pd.read_parquet(ddir / "persistent_mask.parquet")
    d = normalizar(det, mascara)
    act = actividad_por_zona(d)
    pw = power if power is not None else descargar_power(cfg, modelo.zonas_df, hoy)

    ultimo = pd.to_datetime(det.acq_date).max().date()
    completa, t1, t2 = semanas_objetivo(ultimo, hoy)
    obs = pd.date_range("2026-01-05", completa, freq="W-MON")
    sem = pd.DataFrame({"semana": list(obs) + [pd.Timestamp(t1), pd.Timestamp(t2)]})
    sem["era"], sem["valido"] = "VIIRS", True
    sem["observado"] = sem.semana <= pd.Timestamp(completa)
    act = act[act.semana <= pd.Timestamp(completa)]

    modelo.entrenar(horizontes=(1, 2))
    pred = modelo.predecir(act, sem, pw, {1: list(obs) + [pd.Timestamp(t1)], 2: [pd.Timestamp(t2)]})

    # validacion "en vivo" 2026: semanas observadas, predichas sin haberlas visto
    v = pred[(pred.horizonte == 1) & pred.anomalia.notna()]
    temporada = {
        "semanas_evaluadas": int(v.semana.nunique()),
        "zona_semanas": int(len(v)),
        "anomalias_observadas": int(v.anomalia.sum()),
    }
    if v.anomalia.nunique() == 2:
        base = v.freq_hist.fillna(v.anomalia.mean())
        temporada.update(
            {
                "auc": round(float(roc_auc_score(v.anomalia, v.prob)), 3),
                "auc_base": round(float(roc_auc_score(v.anomalia, base)), 3),
                "ap": round(float(average_precision_score(v.anomalia, v.prob)), 3),
                "ap_base": round(float(average_precision_score(v.anomalia, base)), 3),
                "brier": round(float(brier_score_loss(v.anomalia, v.prob)), 4),
                "brier_base": round(float(brier_score_loss(v.anomalia, base)), 4),
            }
        )

    def g(x):
        return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), 3)

    def fila(r):
        return {
            "zona_id": int(r.zona_id),
            "prob": g(r.prob),
            "nivel": nivel(r.prob),
            "base": g(r.freq_hist),
            "p50": g(r.p50),
            "p90": g(r.p90),
            "valor": g(r.valor),
            "anomalia": None if pd.isna(r.anomalia) else int(r.anomalia),
        }

    semanas = {
        str(s.date()): [fila(r) for r in g.itertuples()]
        for s, g in pred[pred.horizonte == 1].groupby("semana")
    }
    semanas[str(t2)] = [fila(r) for r in pred[pred.horizonte == 2].itertuples()]
    salida = {
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),  # noqa: UP017
        "datos_hasta": str(ultimo),
        "ultima_semana_observada": str(completa),
        "semana_en_curso": {"semana": str(t1), "horizonte_semanas": 1},
        "semana_proxima": {"semana": str(t2), "horizonte_semanas": 2},
        "fuentes": {
            "hotspots": f"NASA FIRMS {FUENTE_SP} + {FUENTE_NRT}",
            "clima": "NASA POWER (diario)",
            "armonizacion": "reglas de Alexis (n+h, mascara persistentes)",
        },
        "aviso": AVISO,
        "temporada_2026": temporada,
        "semanas": semanas,
    }
    (cache_dir(cfg) / "prediccion_actual.json").write_text(json.dumps(salida, ensure_ascii=False))
    _leer_json.cache_clear()
    log.info("Prediccion actualizada: en curso %s, proxima %s", t1, t2)
    return {
        k: salida[k]
        for k in [
            "generado_utc",
            "datos_hasta",
            "semana_en_curso",
            "semana_proxima",
            "temporada_2026",
        ]
    }


# ----------------------------------------------------------------- lectura (endpoints)
@lru_cache(maxsize=8)
def _leer_json(ruta: str, mtime: float):
    return json.loads(Path(ruta).read_text())


def _json(ruta: Path):
    return _leer_json(str(ruta), ruta.stat().st_mtime) if ruta.exists() else None


@lru_cache(maxsize=4)
def _historico(ruta: str, mtime: float) -> pd.DataFrame:
    return pd.read_parquet(ruta)


@lru_cache(maxsize=2)
def _zonas(ruta: str) -> dict:
    z = pd.read_parquet(ruta)
    return {int(r.zona_id): (float(r.lat_min), float(r.lon_min)) for r in z.itertuples()}


def _feature(zid, props, zonas):
    lat, lon = zonas[zid]
    ring = [
        [lon, lat],
        [lon + TAM_ZONA, lat],
        [lon + TAM_ZONA, lat + TAM_ZONA],
        [lon, lat + TAM_ZONA],
        [lon, lat],
    ]
    return {
        "type": "Feature",
        "id": zid,
        "properties": props,
        "geometry": {"type": "Polygon", "coordinates": [ring]},
    }


def _en_bbox(zid, zonas, bbox):
    if bbox is None:
        return True
    lat, lon = zonas[zid]
    la0, la1, lo0, lo1 = bbox
    return lat < la1 and lat + TAM_ZONA > la0 and lon < lo1 and lon + TAM_ZONA > lo0


def _coleccion(filas, zonas, bbox, extra):
    feats = [_feature(f["zona_id"], f, zonas) for f in filas if _en_bbox(f["zona_id"], zonas, bbox)]
    probs = [f["properties"]["prob"] for f in feats if f["properties"].get("prob") is not None]
    resumen = {
        "zonas": len(feats),
        "prob_max": max(probs) if probs else None,
        "zonas_alto": sum(1 for f in feats if f["properties"].get("nivel") == "alto"),
    }
    return {"type": "FeatureCollection", "features": feats, "resumen": resumen, **extra}


def get_predictions(cfg, bbox=None):
    """Prediccion vigente: semana en curso (H=1) y proxima (H=2)."""
    actual = _json(cache_dir(cfg) / "prediccion_actual.json")
    if actual is None:
        return None
    zonas = _zonas(str(data_dir(cfg) / "prediccion" / "zonas.parquet"))
    meta = {k: actual[k] for k in ["generado_utc", "datos_hasta", "fuentes", "aviso"]}
    out = {**meta}
    for clave in ["semana_en_curso", "semana_proxima"]:
        s = actual[clave]["semana"]
        extra = {"semana": s, "horizonte_semanas": actual[clave]["horizonte_semanas"]}
        out[clave] = _coleccion(actual["semanas"].get(s, []), zonas, bbox, extra)
    return out


def list_weeks(cfg):
    h = _historico(
        str(data_dir(cfg) / "prediccion" / "pred_historico.parquet"),
        (data_dir(cfg) / "prediccion" / "pred_historico.parquet").stat().st_mtime,
    )
    hist = sorted({str(s.date()) for s in h.semana})
    actual = _json(cache_dir(cfg) / "prediccion_actual.json")
    vivo = sorted(actual["semanas"]) if actual else []
    return {"historico": hist, "vivo_2026": vivo}


def get_week(cfg, semana: str, bbox=None):
    zonas = _zonas(str(data_dir(cfg) / "prediccion" / "zonas.parquet"))
    actual = _json(cache_dir(cfg) / "prediccion_actual.json")
    if actual and semana in actual["semanas"]:
        extra = {"semana": semana, "fuente": "vivo"}
        return _coleccion(actual["semanas"][semana], zonas, bbox, extra)
    ruta = data_dir(cfg) / "prediccion" / "pred_historico.parquet"
    h = _historico(str(ruta), ruta.stat().st_mtime)
    g = h[h.semana == pd.Timestamp(semana)]
    if g.empty:
        return None
    filas = [
        {
            "zona_id": int(r.zona_id),
            "prob": round(float(r.prob), 3),
            "nivel": nivel(r.prob),
            "base": None if pd.isna(r.base) else round(float(r.base), 3),
            "p50": None if pd.isna(r.p50) else round(float(r.p50), 1),
            "p90": None if pd.isna(r.p90) else round(float(r.p90), 1),
            "valor": None if pd.isna(r.valor) else round(float(r.valor), 1),
            "anomalia": None if pd.isna(r.anomalia) else int(r.anomalia),
        }
        for r in g.itertuples()
    ]
    return _coleccion(filas, zonas, bbox, {"semana": semana, "fuente": "historico_walk_forward"})


def get_validation(cfg):
    val = _json(data_dir(cfg) / "prediccion" / "validacion.json") or {}
    actual = _json(cache_dir(cfg) / "prediccion_actual.json")
    if actual:
        val = {
            **val,
            "temporada_2026_vivo": actual.get("temporada_2026"),
            "generado_utc": actual.get("generado_utc"),
        }
    return val


def snapshot(cfg, out: str | None = None) -> str:
    """Escribe current.json y week/<lunes>.json (historico 2015-2025 + vivo 2026)."""
    destino = (
        Path(out)
        if out
        else Path(__file__).resolve().parents[4] / "frontend" / "public" / "prediccion"
    )
    (destino / "week").mkdir(parents=True, exist_ok=True)
    actual = get_predictions(cfg)
    if actual is not None:
        (destino / "current.json").write_text(json.dumps(actual, separators=(",", ":")))
    semanas = list_weeks(cfg)
    todas = [s for s in semanas["historico"] if s >= "2015-01-01"] + semanas["vivo_2026"]
    for s in todas:
        col = get_week(cfg, s)
        if col is not None:
            (destino / "week" / f"{s}.json").write_text(json.dumps(col, separators=(",", ":")))
    return f"{len(todas)} semanas -> {destino}"


def _tabla_larga(cfg) -> pd.DataFrame:
    """Historico walk-forward + vivo 2026 en una sola tabla zona x semana."""
    ruta = data_dir(cfg) / "prediccion" / "pred_historico.parquet"
    h = _historico(str(ruta), ruta.stat().st_mtime)[
        ["zona_id", "semana", "prob", "base", "valor", "p90", "anomalia"]
    ].assign(fuente="historico")
    actual = _json(cache_dir(cfg) / "prediccion_actual.json")
    if actual:
        vivo = pd.DataFrame(
            [
                {"semana": pd.Timestamp(s), **f}
                for s, filas in actual["semanas"].items()
                for f in filas
            ]
        )
        if len(vivo):
            vivo = vivo[["zona_id", "semana", "prob", "base", "valor", "p90", "anomalia"]]
            h = pd.concat([h[~h.semana.isin(vivo.semana)], vivo.assign(fuente="vivo")])
    return h


def get_series(cfg, bbox=None, start: str = "2015-01-05", end: str | None = None) -> dict:
    """Serie semanal agregada de las zonas que tocan el bbox (para un dashboard)."""
    zonas = _zonas(str(data_dir(cfg) / "prediccion" / "zonas.parquet"))
    ids = [z for z in zonas if _en_bbox(z, zonas, bbox)]
    t = _tabla_larga(cfg)
    t = t[t.zona_id.isin(ids) & (t.semana >= pd.Timestamp(start))]
    if end:
        t = t[t.semana <= pd.Timestamp(end)]
    t = t.assign(alto=t.prob >= NIVELES[0][0])
    g = t.groupby("semana")
    s = pd.DataFrame(
        {
            "fuente": g.fuente.last(),
            "zonas": g.zona_id.size(),
            "prob_max": g.prob.max().round(3),
            "prob_media": g.prob.mean().round(3),
            "zonas_alto": g.alto.sum(),
            "valor": g.valor.sum(min_count=1).round(1),
            "p90": g.p90.sum(min_count=1).round(1),
            "anomalias": g.anomalia.sum(min_count=1),
        }
    ).reset_index()
    s["semana"] = s.semana.dt.strftime("%Y-%m-%d")
    s = s.astype(object).where(s.notna(), None)
    return {"zonas": ids, "data": s.to_dict(orient="records")}
