from flask import Blueprint, abort, current_app, jsonify, request

from modviirs.services import prediction_service as svc

predictions = Blueprint("predictions", __name__)


def _bbox():
    keys = ["lat_min", "lat_max", "lon_min", "lon_max"]
    if not all(k in request.args for k in keys):
        return None
    try:
        return tuple(float(request.args[k]) for k in keys)
    except ValueError:
        abort(400, description="lat_min, lat_max, lon_min y lon_max deben ser numeros.")


@predictions.get("/predictions")
def get_predictions():
    """GET /api/v1/predictions[?lat_min&lat_max&lon_min&lon_max]

    Prediccion vigente (cache de la ultima actualizacion NRT): `semana_en_curso` (1 semana de
    anticipacion) y `semana_proxima` (2 semanas). Cada una es un GeoJSON de zonas 0.5 deg con
    prob (0-1), nivel, base (frecuencia historica), p50/p90, valor y anomalia observada.
    """
    data = svc.get_predictions(current_app.config, _bbox())
    if data is None:
        abort(
            503,
            description="Sin prediccion vigente: ejecutar `flask --app wsgi prediction-update`.",
        )
    return jsonify(data)


@predictions.get("/predictions/weeks")
def get_weeks():
    """GET /api/v1/predictions/weeks -> semanas disponibles (historico 2015-2025 y vivo 2026)."""
    return jsonify(svc.list_weeks(current_app.config))


@predictions.get("/predictions/week/<semana>")
def get_week(semana: str):
    """GET /api/v1/predictions/week/YYYY-MM-DD (lunes) -> GeoJSON de esa semana."""
    data = svc.get_week(current_app.config, semana, _bbox())
    if data is None:
        abort(404, description=f"No hay prediccion para la semana {semana}.")
    return jsonify(data)


@predictions.get("/predictions/validation")
def get_validation():
    """GET /api/v1/predictions/validation -> metricas walk-forward, calibracion y temporada 2026."""
    return jsonify(svc.get_validation(current_app.config))
