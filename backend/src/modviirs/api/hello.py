from flask import Blueprint, jsonify

hello = Blueprint("hello", __name__)


@hello.get("/hello")
def get_hello():
    return jsonify(message="Hello World")


@hello.get("/health")
def get_health():
    return jsonify(status="ok")
