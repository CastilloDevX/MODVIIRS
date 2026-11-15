from flask import Blueprint, jsonify

hello = Blueprint("hello", __name__)


@hello.get("/hello")
def get_hello():
    """
    Simple greeting.
    ---
    tags:
      - Health
    responses:
      200:
        description: Hello message.
        schema:
          type: object
          properties:
            message:
              type: string
              example: Hello World
    """
    return jsonify(message="Hello World")


@hello.get("/health")
def get_health():
    """
    Health check.
    ---
    tags:
      - Health
    responses:
      200:
        description: Service is running.
        schema:
          type: object
          properties:
            status:
              type: string
              example: ok
    """
    return jsonify(status="ok")
