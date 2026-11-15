from __future__ import annotations

from datetime import date
from math import isfinite

from flask import Blueprint, abort, current_app, jsonify, request

from modviirs.services.firms_client import (
    SOURCES,
    FirmsClient,
    FirmsInvalidResponseError,
    FirmsNotConfiguredError,
    FirmsRateLimitError,
    FirmsTimeoutError,
    FirmsUpstreamError,
)
from modviirs.services.firms_data import query_hotspots, source_details

firms = Blueprint("firms", __name__)


def _iso_date(value: str, name: str) -> date:
    if len(value) != 10 or value[4] != "-" or value[7] != "-":
        abort(400, description=f"{name} debe usar el formato YYYY-MM-DD.")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        abort(400, description=f"{name} no es una fecha válida.")
    if parsed.isoformat() != value:
        abort(400, description=f"{name} debe usar el formato YYYY-MM-DD.")
    return parsed


def _query_filters() -> tuple[str, tuple[float, float, float, float], date, date]:
    source = request.args.get("source", "")
    if source not in SOURCES:
        abort(400, description="source debe ser uno de los productos FIRMS admitidos.")

    bbox_value = request.args.get("bbox", "")
    try:
        bbox = tuple(float(part) for part in bbox_value.split(","))
        if len(bbox) != 4 or not all(isfinite(value) for value in bbox):
            raise ValueError
        west, south, east, north = bbox
        if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
            raise ValueError
    except ValueError:
        abort(400, description="bbox debe ser w,s,e,n válido en coordenadas geográficas WGS84.")

    start_value = request.args.get("start_date", "")
    end_value = request.args.get("end_date", "")
    if not start_value or not end_value:
        abort(400, description="start_date y end_date son obligatorios.")
    start = _iso_date(start_value, "start_date")
    end = _iso_date(end_value, "end_date")
    if start > end:
        abort(400, description="start_date debe ser anterior o igual a end_date.")
    if (end - start).days + 1 > 31:
        abort(400, description="El intervalo máximo es de 31 días inclusivos.")
    return source, bbox, start, end


def _client() -> FirmsClient:
    map_key = current_app.config.get("FIRMS_MAP_KEY")
    if not map_key or not str(map_key).strip():
        raise FirmsNotConfiguredError("La clave de NASA FIRMS no está configurada.")
    factory = current_app.config.get("FIRMS_CLIENT_FACTORY", FirmsClient)
    return factory(map_key)


def _query_data():
    source, bbox, start, end = _query_filters()
    result = query_hotspots(_client(), source, bbox, start, end)
    return source, bbox, start, end, result


def _provider_error(error):
    if isinstance(error, FirmsTimeoutError):
        status, name = 504, "Gateway Timeout"
    elif isinstance(error, FirmsNotConfiguredError | FirmsRateLimitError):
        status, name = 503, "Service Unavailable"
    elif isinstance(error, FirmsInvalidResponseError | FirmsUpstreamError):
        status, name = 502, "Bad Gateway"
    else:
        raise error
    return jsonify(error=name, message=str(error)), status


@firms.get("/firms/sources")
def get_sources():
    return jsonify(
        sources=[source_details(source) for source in SOURCES],
    )


@firms.get("/firms/hotspots")
def get_hotspots():
    try:
        source, bbox, start, end, result = _query_data()
    except (
        FirmsInvalidResponseError,
        FirmsNotConfiguredError,
        FirmsRateLimitError,
        FirmsTimeoutError,
        FirmsUpstreamError,
    ) as error:
        return _provider_error(error)

    details = source_details(source)
    return jsonify(
        type="FeatureCollection",
        features=result["features"],
        metadata={
            "source": source,
            "sensor": details["sensor"],
            "platform": details["platform"],
            "processing_type": details["processing_type"],
            "bbox": result["bbox"],
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "date_basis": "UTC",
            "count": result["count"],
            "truncated": False,
            "records_rejected": result["records_rejected"],
            "rejection_reasons": result["rejection_reasons"],
        },
    )


@firms.get("/firms/summary")
def get_summary():
    try:
        source, _bbox, start, end, result = _query_data()
    except (
        FirmsInvalidResponseError,
        FirmsNotConfiguredError,
        FirmsRateLimitError,
        FirmsTimeoutError,
        FirmsUpstreamError,
    ) as error:
        return _provider_error(error)

    counts = {}
    for feature in result["features"]:
        acquired = feature["properties"]["acq_date"]
        counts[acquired] = counts.get(acquired, 0) + 1
    details = source_details(source)
    return jsonify(
        total_detections=result["count"],
        counts_by_date=[{"date": day, "count": count} for day, count in sorted(counts.items())],
        source=source,
        sensor=details["sensor"],
        platform=details["platform"],
        processing_type=details["processing_type"],
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        date_basis="UTC",
        metric="reported_detections",
        note="Conteos de detecciones reportadas; no equivalen a incendios individuales.",
        records_rejected=result["records_rejected"],
        rejection_reasons=result["rejection_reasons"],
    )
