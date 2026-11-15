import pytest

from modviirs import create_app


@pytest.fixture
def client():
    return create_app({"TESTING": True}).test_client()


def test_hello(client):
    response = client.get("/api/hello")
    assert response.status_code == 200
    assert response.is_json
    assert response.json == {"message": "Hello World"}


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_versioned_health_alias(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_harmonized_data_unavailable_returns_explicit_service_error(client):
    response = client.get("/api/v1/fires/calendar?lat_min=18&lat_max=19&lon_min=-91&lon_max=-90")
    assert response.status_code == 503
    assert response.json["error"] == "Data Unavailable"
    assert "Git LFS" in response.json["message"]


def test_missing_route_returns_json(client):
    response = client.get("/api/missing")
    assert response.status_code == 404
    assert response.json["error"] == "Not Found"


def test_method_not_allowed_preserves_allow_header(client):
    response = client.post("/api/hello")
    assert response.status_code == 405
    assert "GET" in response.headers["Allow"]
    assert response.is_json


def test_factory_isolates_configuration():
    first = create_app({"TESTING": True, "CUSTOM_VALUE": "first"})
    second = create_app({"TESTING": True})
    assert first.config["CUSTOM_VALUE"] == "first"
    assert "CUSTOM_VALUE" not in second.config
