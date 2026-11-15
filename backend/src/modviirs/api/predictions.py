"""Endpoints del modelo predictivo (rama `predictivo`). Contrato: docs/API_PREDICCIONES.md."""

from flask import Blueprint, abort, current_app, jsonify, request

from modviirs.services import global_prediction_service as glob
from modviirs.services import prediction_service as svc

predictions = Blueprint("predictions", __name__)

BBOX = """
      - {name: lat_min, in: query, type: number, required: false}
      - {name: lat_max, in: query, type: number, required: false}
      - {name: lon_min, in: query, type: number, required: false}
      - {name: lon_max, in: query, type: number, required: false}"""

DOC_ACTUAL = f"""
    Live forecast of anomalous hotspot activity (current and next week).
    ---
    tags: [Predictions]
    description: >
      Probability that each 0.5 deg zone (~55 km) of the Yucatan Peninsula has ANOMALOUS fire
      activity (fire-days above its own historical p90 for those dates), computed by
      `flask prediction-update` from FIRMS VIIRS NOAA-20 (SP+NRT) and NASA POWER.
      `semana_en_curso` = 1-week lead, `semana_proxima` = 2-week lead. Each is a GeoJSON
      FeatureCollection. Zone properties: zona_id, prob (0-1), nivel (bajo <0.10,
      moderado 0.10-0.30, alto >=0.30), base (historical anomaly frequency = baseline),
      p50/p90 (usual/high fire-days), valor (observed fire-days or null), anomalia (0/1/null).
      Optional bbox keeps only the zones that intersect it.
    parameters:{BBOX}
    responses:
      200: {{description: "generado_utc, datos_hasta, aviso, semana_en_curso, semana_proxima"}}
      503: {{description: "No live forecast yet: run flask --app wsgi prediction-update"}}
    """

DOC_SEMANA = f"""
    Forecast for one week as GeoJSON (map layer).
    ---
    tags: [Predictions]
    description: >
      `semana` = Monday (YYYY-MM-DD). Historical weeks are out-of-sample walk-forward
      predictions (each year predicted by a model trained only on previous years); 2026 weeks
      come from the live run. Same zone properties as /predictions.
    parameters:
      - {{name: semana, in: path, type: string, required: true}}{BBOX}
    responses:
      200: {{description: "FeatureCollection + resumen (zonas, prob_max, zonas_alto) + fuente"}}
      404: {{description: "No forecast for that week"}}
    """

DOC_SERIE = f"""
    Weekly forecast time series for an area of interest (dashboard).
    ---
    tags: [Predictions]
    description: >
      Aggregates the zones that intersect the bbox week by week. `escala=auto` (default) uses
      the Yucatan Peninsula model (0.5 deg zones, NASA POWER climate, walk-forward 2015-2025 +
      live 2026) when >= 50 % of the bbox lies in the peninsula, otherwise the 6-country model
      (Mexico, Brazil, Russia, Australia, Angola, DR Congo; 1 deg zones, walk-forward
      2023-2025). Without bbox = whole peninsula. `esperadas` = expected number of anomalous
      zones (sum of probabilities), compare it with `anomalias` (observed).
    parameters:{BBOX}
      - {{name: escala, in: query, type: string, required: false, enum: [auto, peninsula, global]}}
      - {{name: start, in: query, type: string, required: false, description: "Monday"}}
      - {{name: end, in: query, type: string, required: false}}
    responses:
      200:
        description: >
          escala, tam_zona_grados, paises, zonas (ids) and data: [{{semana, fuente, zonas,
          prob_max, prob_media, esperadas, zonas_alto, valor, p50, p90, anomalias}}].
          valor/p50/p90 = summed fire-days; anomalias = zones with observed anomaly (null if
          not observed yet).
    """


def _doc(texto: str):
    def deco(f):
        f.__doc__ = texto
        return f

    return deco


def _bbox():
    keys = ["lat_min", "lat_max", "lon_min", "lon_max"]
    if not all(k in request.args for k in keys):
        return None
    try:
        return tuple(float(request.args[k]) for k in keys)
    except ValueError:
        abort(400, description="lat_min, lat_max, lon_min y lon_max deben ser numeros.")


@predictions.get("/predictions")
@_doc(DOC_ACTUAL)
def get_predictions():
    data = svc.get_predictions(current_app.config, _bbox())
    if data is None:
        abort(
            503,
            description="Sin prediccion vigente: ejecutar `flask --app wsgi prediction-update`.",
        )
    return jsonify(data)


@predictions.get("/predictions/weeks")
def get_weeks():
    """
    Weeks (Mondays) with a forecast available.
    ---
    tags: [Predictions]
    responses:
      200: {description: "historico (walk-forward 2008-2025) and vivo_2026: lists of YYYY-MM-DD"}
    """
    return jsonify(svc.list_weeks(current_app.config))


@predictions.get("/predictions/week/<semana>")
@_doc(DOC_SEMANA)
def get_week(semana: str):
    data = svc.get_week(current_app.config, semana, _bbox())
    if data is None:
        abort(404, description=f"No hay prediccion para la semana {semana}.")
    return jsonify(data)


@predictions.get("/predictions/series")
@_doc(DOC_SERIE)
def get_series():
    bbox, escala = _bbox(), request.args.get("escala", "auto")
    start, end = request.args.get("start"), request.args.get("end")
    usar_global = glob.disponible(current_app.config) and (
        escala == "global" or (escala == "auto" and not glob.usa_peninsula(bbox))
    )
    if usar_global:
        return jsonify(glob.get_series(current_app.config, bbox, start or "2023-01-02", end))
    return jsonify(svc.get_series(current_app.config, bbox, start or "2015-01-05", end))


def _global_o_503():
    if not glob.disponible(current_app.config):
        abort(503, description="Falta data/prediccion/pred_global.parquet (correr p06 + p07).")


@predictions.get("/predictions/global/countries")
def get_global_countries():
    """
    Countries covered by the 6-country model (Alexis' harmonized VIIRS data).
    ---
    tags: [Predictions]
    description: >
      Mexico, Brazil, Russia, Australia, Angola and DR Congo with 1 deg zones (~110 km).
      Per country: zones, bbox {west, south, east, north} and walk-forward H1 metrics
      (AUC / average precision vs the climatology baseline).
    responses:
      200: {description: "paises, semanas {desde, hasta}, aviso"}
    """
    _global_o_503()
    return jsonify(glob.paises(current_app.config))


@predictions.get("/predictions/global/week/<semana>")
def get_global_week(semana: str):
    """
    6-country forecast for one week as GeoJSON (1 deg zones, map layer).
    ---
    tags: [Predictions]
    parameters:
      - {name: semana, in: path, type: string, required: true, description: "Monday"}
      - {name: horizonte, in: query, type: integer, required: false, enum: [1, 2]}
      - {name: lat_min, in: query, type: number, required: false}
      - {name: lat_max, in: query, type: number, required: false}
      - {name: lon_min, in: query, type: number, required: false}
      - {name: lon_max, in: query, type: number, required: false}
    responses:
      200: {description: "FeatureCollection (props: zona_id, pais, prob, nivel, base, p50, p90,
        valor, anomalia) + resumen {zonas, prob_max, zonas_alto, esperadas}"}
      404: {description: "No forecast for that week (available 2023-2025)"}
    """
    _global_o_503()
    data = glob.get_week(current_app.config, semana, _bbox(), int(request.args.get("horizonte", 1)))
    if data is None:
        abort(404, description=f"No hay prediccion global para la semana {semana}.")
    return jsonify(data)


@predictions.get("/predictions/global/validation")
def get_global_validation():
    """
    Walk-forward metrics of the 6-country model, per country and year.
    ---
    tags: [Predictions]
    responses:
      200: {description: "por_pais, por_pais_anio (auc, ap, brier and their *_base)"}
    """
    _global_o_503()
    from modviirs.services.prediction_service import _json, data_dir

    return jsonify(_json(data_dir(current_app.config) / "prediccion" / "validacion_global.json"))


@predictions.get("/predictions/validation")
def get_validation():
    """
    How reliable the forecast is (metrics for the dashboard).
    ---
    tags: [Predictions]
    description: >
      Walk-forward metrics 2015-2025 (AUC, average precision, Brier vs climatology baseline),
      per-year metrics, calibration (predicted vs observed frequency), Wilcoxon test for the
      NASA POWER climate variables, false-anomaly rates without harmonization and the live
      2026 season evaluation.
    responses:
      200: {description: "Validation summary"}
    """
    return jsonify(svc.get_validation(current_app.config))
