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

    @app.errorhandler(500)
    def handle_internal_error(_error):
        return jsonify(error="Internal Server Error", message="Error interno del servidor."), 500

    return app
