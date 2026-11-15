import json

import pytest

from modviirs import create_app
from modviirs.services import prediction_service as svc


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(svc, "cache_dir", lambda cfg: tmp_path)
    return create_app({"TESTING": True}).test_client(), tmp_path


def test_predictions_without_cache_returns_503(client):
    c, _ = client
    r = c.get("/api/v1/predictions")
    assert r.status_code == 503
    assert r.is_json


def test_validation_and_history(client):
    c, _ = client
    v = c.get("/api/v1/predictions/validation")
    assert v.status_code == 200 and "resumen_h1" in v.json
    w = c.get("/api/v1/predictions/weeks")
    assert w.status_code == 200 and "2024-04-22" in w.json["historico"]
    g = c.get("/api/v1/predictions/week/2024-04-22?lat_min=18&lat_max=20&lon_min=-90&lon_max=-88")
    assert g.status_code == 200 and g.json["type"] == "FeatureCollection"
    assert 0 < len(g.json["features"]) < 65
    assert c.get("/api/v1/predictions/week/1999-01-04").status_code == 404


def test_predictions_from_cache(client):
    c, tmp = client
    fila = {
        "zona_id": 0,
        "prob": 0.42,
        "nivel": "alto",
        "base": 0.1,
        "p50": 1,
        "p90": 5,
        "valor": None,
        "anomalia": None,
    }
    cache = {
        "generado_utc": "x",
        "datos_hasta": "2026-11-15",
        "fuentes": {},
        "aviso": "",
        "semana_en_curso": {"semana": "2026-11-09", "horizonte_semanas": 1},
        "semana_proxima": {"semana": "2026-11-16", "horizonte_semanas": 2},
        "temporada_2026": {},
        "semanas": {"2026-11-09": [fila], "2026-11-16": [fila]},
    }
    (tmp / "prediccion_actual.json").write_text(json.dumps(cache))
    r = c.get("/api/v1/predictions")
    assert r.status_code == 200
    assert r.json["semana_en_curso"]["features"][0]["properties"]["prob"] == 0.42
    assert r.json["semana_proxima"]["resumen"]["zonas_alto"] == 1


def test_semanas_objetivo():
    from datetime import date

    completa, t1, t2 = svc.semanas_objetivo(date(2026, 11, 15), date(2026, 11, 15))
    assert (str(completa), str(t1), str(t2)) == ("2026-11-02", "2026-11-09", "2026-11-16")
