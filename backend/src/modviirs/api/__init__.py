from flask import Blueprint

from modviirs.api.firms import firms
from modviirs.api.hello import hello

api = Blueprint("api_v1", __name__)
api.register_blueprint(hello)
api.register_blueprint(firms)
