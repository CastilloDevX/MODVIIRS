import threading

import click
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from modviirs.api import api


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_prefixed_env(prefix="MODVIIRS")
    if test_config is not None:
        app.config.update(test_config)
    app.register_blueprint(api, url_prefix="/api")

    try:
        from flasgger import Swagger

        Swagger(
            app,
            config={
                "headers": [],
                "specs": [
                    {
                        "endpoint": "apispec",
                        "route": "/apispec.json",
                        "rule_filter": lambda rule: rule.rule.startswith("/api/"),
                        "model_filter": lambda tag: True,
                    }
                ],
                "static_url_path": "/flasgger_static",
                "swagger_ui": True,
                "specs_route": "/apidocs",
            },
            template={
                "info": {
                    "title": "MODVIIRS API",
                    "description": "Hotspot fire activity from MODIS/VIIRS sensors.",
                    "version": "1.0.0",
                },
                "basePath": "/",
            },
        )
    except ImportError:
        pass

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        response = error.get_response()
        response.data = app.json.dumps({"error": error.name, "message": error.description})
        response.content_type = "application/json"
        return response

    @app.cli.command("prediction-update")
    def prediction_update():
        """Descarga FIRMS NRT + NASA POWER, entrena y actualiza la prediccion (~1-2 min)."""
        from modviirs.services import prediction_service

        click.echo(prediction_service.actualizar(app.config))

    @app.cli.command("prediction-snapshot")
    @click.option(
        "--out", default=None, help="Carpeta destino (default: frontend/public/prediccion)"
    )
    def prediction_snapshot(out):
        """Copia estatica de las predicciones para el frontend (respaldo si la API no responde)."""
        from modviirs.services import prediction_service

        click.echo(prediction_service.snapshot(app.config, out))

    horas = float(app.config.get("PREDICTION_REFRESH_HOURS") or 0)
    if horas > 0 and not app.config.get("TESTING"):
        _iniciar_refresco(app, horas)

    @app.errorhandler(500)
    def handle_internal_error(_error):
        return jsonify(error="Internal Server Error", message="Error interno del servidor."), 500

    return app


def _iniciar_refresco(app: Flask, horas: float) -> None:
    """Actualiza la prediccion en segundo plano cada `horas` (usar con 1 solo proceso/worker)."""
    from modviirs.services import prediction_service

    def ciclo():
        try:
            with app.app_context():
                prediction_service.actualizar(app.config)
        except Exception:  # noqa: BLE001 - se conserva la ultima prediccion buena
            app.logger.exception("Fallo la actualizacion de la prediccion")
        t = threading.Timer(horas * 3600, ciclo)
        t.daemon = True
        t.start()

    t = threading.Timer(5, ciclo)
    t.daemon = True
    t.start()
