from datetime import date, timedelta

import pytest

from modviirs import create_app
from modviirs.services.firms_client import (
    SOURCES,
    FirmsClient,
    FirmsInvalidResponseError,
    FirmsNotConfiguredError,
    FirmsRateLimitError,
    FirmsTimeoutError,
    FirmsUpstreamError,
)

HEADERS = "latitude,longitude,acq_date,acq_time,satellite,instrument,confidence,frp,type"
BBOX = "-90.5,20.5,-89.0,21.5"
START = "2026-10-10"
END = "2026-10-17"
SECRET = "test-secret-never-return-this"


class StubClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def fetch_area_csv(self, source, bbox, days, start_date):
        self.calls.append((source, bbox, days, start_date))
        return self.responses.pop(0)


def csv_row(
    acquired,
    latitude="20.9",
    longitude="-89.6",
    extra='N,VIIRS,n,12.5,"vegetation, low confidence"',
):
    return f"{latitude},{longitude},{acquired},1530,{extra}\n".encode()


def request_url(path="hotspots", params=None):
    query = {
        "source": "VIIRS_SNPP_SP",
        "bbox": BBOX,
        "start_date": START,
        "end_date": END,
    }
    if params:
        query.update(params)
    encoded = "&".join(f"{key}={value}" for key, value in query.items())
    return f"/api/v1/firms/{path}?{encoded}"


def app_with_client(client, map_key=SECRET):
    return create_app(
        {
            "TESTING": True,
            "FIRMS_MAP_KEY": map_key,
            "FIRMS_CLIENT_FACTORY": lambda _key: client,
        }
    )


def test_sources_catalogue_has_eight_products_without_availability_dates():
    response = create_app({"TESTING": True}).test_client().get("/api/v1/firms/sources")

    assert response.status_code == 200
    assert len(response.json["sources"]) == 8
    assert {item["code"] for item in response.json["sources"]} == set(SOURCES)
    assert all(
        {"sensor", "platform", "processing_type"} <= item.keys()
        for item in response.json["sources"]
    )
    assert not any("date" in key for item in response.json["sources"] for key in item)


@pytest.mark.parametrize(
    ("source", "row", "instrument", "satellite"),
    [
        ("MODIS_SP", "20.9,-89.6,2026-10-10,1530,Terra,MODIS,82,12.5,0", "MODIS", "Terra"),
        (
            "VIIRS_SNPP_SP",
            '20.9,-89.6,2026-10-10,1530,N,VIIRS,n,12.5,"vegetation, low confidence"',
            "VIIRS",
            "N",
        ),
    ],
)
def test_hotspots_transform_csv_to_geojson_and_preserve_attributes(
    source, row, instrument, satellite
):
    client = StubClient([(HEADERS + "\n" + row + "\n").encode()])
    response = (
        app_with_client(client)
        .test_client()
        .get(request_url(params={"source": source, "start_date": START, "end_date": START}))
    )

    assert response.status_code == 200
    feature = response.json["features"][0]
    assert response.json["type"] == "FeatureCollection"
    assert feature["geometry"]["coordinates"] == [-89.6, 20.9]
    assert feature["properties"]["source"] == source
    assert feature["properties"]["instrument"] == instrument
    assert feature["properties"]["satellite"] == satellite
    assert feature["properties"]["acq_date"] == START
    assert feature["properties"]["acq_time"] == "1530"
    assert feature["properties"]["frp"] == 12.5
    if source.startswith("VIIRS"):
        assert feature["properties"]["type"] == "vegetation, low confidence"


def test_periods_are_inclusive_and_split_into_maximum_five_day_calls():
    starts = [date(2026, 10, 10), date(2026, 10, 15), date(2026, 10, 20)]
    payloads = [
        (HEADERS + "\n" + csv_row((start + timedelta(days=days - 1)).isoformat()).decode()).encode()
        for start, days in zip(starts, (5, 5, 1), strict=True)
    ]
    client = StubClient(payloads)
    response = (
        app_with_client(client)
        .test_client()
        .get(request_url(params={"start_date": "2026-10-10", "end_date": "2026-10-20"}))
    )

    assert response.status_code == 200
    assert [call[2:] for call in client.calls] == [
        (5, "2026-10-10"),
        (5, "2026-10-15"),
        (1, "2026-10-20"),
    ]
    assert [feature["properties"]["acq_date"] for feature in response.json["features"]] == [
        "2026-10-14",
        "2026-10-19",
        "2026-10-20",
    ]
    assert response.json["metadata"]["end_date"] == "2026-10-20"
    assert response.json["metadata"]["date_basis"] == "UTC"
    assert response.json["metadata"]["truncated"] is False


def test_maximum_31_day_period_is_allowed_and_uses_seven_chunks():
    empty_csv = (HEADERS + "\n").encode()
    client = StubClient([empty_csv] * 7)
    response = (
        app_with_client(client)
        .test_client()
        .get(request_url(params={"start_date": "2026-10-01", "end_date": "2026-10-31"}))
    )

    assert response.status_code == 200
    assert [call[2] for call in client.calls] == [5, 5, 5, 5, 5, 5, 1]
    assert client.calls[-1][3] == "2026-10-31"
    assert response.json["metadata"]["count"] == 0


@pytest.mark.parametrize(
    "params",
    [
        {"source": "NOT_A_SOURCE"},
        {"bbox": "-90,20,-91,21"},
        {"bbox": "-181,20,-90,21"},
        {"bbox": "-90,91,-89,92"},
        {"bbox": "-90,nan,-89,21"},
        {"bbox": "-90,20,-89"},
        {"start_date": "20261010"},
        {"start_date": "2026-02-30"},
        {"end_date": "2026-10-09"},
        {"end_date": "2026-11-10"},
    ],
)
def test_invalid_filters_return_400_without_calling_provider(params):
    client = StubClient([])
    response = app_with_client(client).test_client().get(request_url(params=params))

    assert response.status_code == 400
    assert response.is_json
    assert client.calls == []


def test_missing_filters_return_400():
    response = create_app({"TESTING": True}).test_client().get("/api/v1/firms/hotspots")
    assert response.status_code == 400


def test_valid_empty_csv_returns_empty_collection():
    client = StubClient([(HEADERS + "\n").encode()])
    response = app_with_client(client).test_client().get(request_url(params={"end_date": START}))

    assert response.status_code == 200
    assert response.json["features"] == []
    assert response.json["metadata"]["count"] == 0
    assert response.json["metadata"]["records_rejected"] == 0


def test_invalid_rows_are_counted_and_explained_in_metadata():
    rows = [
        csv_row(START).decode(),
        csv_row(START, latitude="91").decode(),
        csv_row("2026-10-18").decode(),
        csv_row(START, longitude="-88").decode(),
        "not,a,complete,row\n",
        csv_row(START).decode().rstrip() + ",extra\n",
    ]
    client = StubClient([(HEADERS + "\n" + "".join(rows)).encode()])
    response = app_with_client(client).test_client().get(request_url(params={"end_date": START}))

    assert response.status_code == 200
    assert response.json["metadata"]["count"] == 1
    assert response.json["metadata"]["records_rejected"] == 5
    assert response.json["metadata"]["rejection_reasons"] == {
        "invalid_coordinates": 1,
        "invalid_required_value": 1,
        "malformed_row": 1,
        "outside_bbox": 1,
        "outside_date_range": 1,
    }


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (b"<html>unauthorized</html>", "HTML"),
        (b"latitude,longitude\n1,2\n", "esquema"),
        (b'latitude,longitude,acq_date,acq_time\n"unfinished', "malformado"),
        (b"\xff,longitude,acq_date,acq_time\n", "codificación"),
    ],
)
def test_invalid_csv_is_reported_as_bad_gateway(payload, message):
    client = StubClient([payload])
    response = app_with_client(client).test_client().get(request_url())

    assert response.status_code == 502
    assert message in response.json["message"]


def test_missing_key_returns_503_without_provider_call():
    client = StubClient([])
    response = app_with_client(client, map_key=" ").test_client().get(request_url())

    assert response.status_code == 503
    assert SECRET not in response.get_data(as_text=True)
    assert client.calls == []


def test_flask_prefixed_environment_configures_the_firms_key(monkeypatch):
    monkeypatch.setenv("MODVIIRS_FIRMS_MAP_KEY", SECRET)
    app = create_app({"TESTING": True})

    assert app.config["FIRMS_MAP_KEY"] == SECRET


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (FirmsTimeoutError("timeout"), 504),
        (FirmsRateLimitError("quota"), 503),
        (FirmsNotConfiguredError("bad credential"), 503),
        (FirmsUpstreamError("upstream failed"), 502),
        (FirmsInvalidResponseError("bad csv"), 502),
    ],
)
def test_provider_failures_map_to_json_gateway_errors_without_secret(error, status):
    class ErrorClient:
        def fetch_area_csv(self, *_args):
            raise error

    response = app_with_client(ErrorClient()).test_client().get(request_url())

    assert response.status_code == status
    assert response.is_json
    assert SECRET not in response.get_data(as_text=True)


def test_summary_reuses_query_result_and_counts_observations_by_utc_date():
    payload = (
        HEADERS
        + "\n"
        + csv_row(START).decode()
        + csv_row(START).decode()
        + csv_row("2026-10-11").decode()
    ).encode()
    client = StubClient([payload])
    response = (
        app_with_client(client)
        .test_client()
        .get(request_url(path="summary", params={"end_date": "2026-10-11"}))
    )

    assert response.status_code == 200
    assert response.json["total_detections"] == 3
    assert response.json["counts_by_date"] == [
        {"date": "2026-10-10", "count": 2},
        {"date": "2026-10-11", "count": 1},
    ]
    assert response.json["source"] == "VIIRS_SNPP_SP"
    assert response.json["date_basis"] == "UTC"
    assert response.json["metric"] == "reported_detections"
    assert len(client.calls) == 1


def test_provider_constructs_encoded_secret_url_and_uses_timeout_without_leaking_errors():
    class Response:
        def getcode(self):
            return 200

        def read(self):
            return (HEADERS + "\n").encode()

        def close(self):
            pass

    captured = {}

    def opener(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        return Response()

    client = FirmsClient("key/with space", opener=opener)
    payload = client.fetch_area_csv("VIIRS_SNPP_SP", BBOX, 1, START)

    assert payload.startswith(b"latitude,")
    assert "/key%2Fwith%20space/" in captured["url"]
    assert captured["timeout"] > 0


def test_provider_timeout_and_rate_limit_are_classified_and_sanitized():
    from urllib.error import HTTPError, URLError

    def timeout_opener(*_args, **_kwargs):
        raise URLError(TimeoutError("secret-bearing upstream detail"))

    with pytest.raises(FirmsTimeoutError) as timeout_error:
        FirmsClient(SECRET, opener=timeout_opener).fetch_area_csv("VIIRS_SNPP_SP", BBOX, 1, START)
    assert SECRET not in str(timeout_error.value)

    def quota_opener(request, **_kwargs):
        raise HTTPError(request.full_url, 429, "quota", {}, None)

    with pytest.raises(FirmsRateLimitError) as quota_error:
        FirmsClient(SECRET, opener=quota_opener).fetch_area_csv("VIIRS_SNPP_SP", BBOX, 1, START)
    assert SECRET not in str(quota_error.value)

    def http_error_opener(request, **_kwargs):
        raise HTTPError(request.full_url, 503, "URL contains credentials", {}, None)

    with pytest.raises(FirmsUpstreamError) as http_error:
        FirmsClient(SECRET, opener=http_error_opener).fetch_area_csv(
            "VIIRS_SNPP_SP", BBOX, 1, START
        )
    assert SECRET not in str(http_error.value)
