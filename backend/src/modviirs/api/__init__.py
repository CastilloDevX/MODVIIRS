from flask import Blueprint

from modviirs.api.fires import fires
from modviirs.api.hello import hello
from modviirs.api.predictions import predictions

api = Blueprint("api_v1", __name__)
api.register_blueprint(hello)
api.register_blueprint(fires)
api.register_blueprint(predictions)
