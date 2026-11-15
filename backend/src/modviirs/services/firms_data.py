from __future__ import annotations

import csv
import io
import math
from collections import Counter
from datetime import date, timedelta

from modviirs.services.firms_client import SOURCES, FirmsInvalidResponseError

REQUIRED_COLUMNS = {"latitude", "longitude", "acq_date", "acq_time"}
NUMERIC_COLUMNS = {
    "bright_ti4",
    "bright_ti5",
    "bright_t31",
    "brightness",
    "frp",
    "scan",
    "track",
}


def _number(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError
    return result


def _properties(row: dict[str, str | None], source: str) -> dict:
    properties = {}
    for name, value in row.items():
        if value is None:
            continue
        value = value.strip()
        if name in {"latitude", "longitude"}:
            properties[name] = _number(value)
        elif name in NUMERIC_COLUMNS and value:
            try:
                number = _number(value)
                properties[name] = int(number) if number.is_integer() else number
            except ValueError:
                properties[name] = value
        else:
            properties[name] = value
    properties["source"] = source
    return properties


def parse_hotspots_csv(
    payload: bytes,
    source: str,
    bbox: tuple[float, float, float, float],
    start_date: date,
    end_date: date,
) -> tuple[list[dict], int, dict[str, int]]:
    sample = payload[:1024].lstrip().lower()
    if sample.startswith((b"<html", b"<!doctype", b"<head", b"<body")):
        raise FirmsInvalidResponseError("NASA FIRMS devolvió contenido HTML en lugar de CSV.")
    try:
        text = payload.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        if not reader.fieldnames:
            raise FirmsInvalidResponseError("NASA FIRMS devolvió un CSV sin encabezado.")
        headers = [header.strip().lower() for header in reader.fieldnames]
        if len(headers) != len(set(headers)) or not REQUIRED_COLUMNS.issubset(headers):
            raise FirmsInvalidResponseError("NASA FIRMS devolvió un esquema CSV inválido.")
        reader.fieldnames = headers

        features = []
        rejections: Counter[str] = Counter()
        west, south, east, north = bbox
        for row in reader:
            if None in row:
                rejections["malformed_row"] += 1
                continue
            try:
                latitude = _number(row.get("latitude") or "")
                longitude = _number(row.get("longitude") or "")
                acquired_value = row.get("acq_date") or ""
                acquired = date.fromisoformat(acquired_value)
                if acquired.isoformat() != acquired_value:
                    raise ValueError
            except (ValueError, TypeError):
                rejections["invalid_required_value"] += 1
                continue

            if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
                rejections["invalid_coordinates"] += 1
                continue
            if not start_date <= acquired <= end_date:
                rejections["outside_date_range"] += 1
                continue
            if not west <= longitude <= east or not south <= latitude <= north:
                rejections["outside_bbox"] += 1
                continue

            try:
                properties = _properties(row, source)
            except ValueError:
                rejections["invalid_required_value"] += 1
                continue
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [longitude, latitude]},
                    "properties": properties,
                }
            )
    except UnicodeDecodeError:
        raise FirmsInvalidResponseError(
            "NASA FIRMS devolvió una codificación CSV inválida."
        ) from None
    except csv.Error:
        raise FirmsInvalidResponseError("NASA FIRMS devolvió un CSV malformado.") from None

    return features, sum(rejections.values()), dict(sorted(rejections.items()))


def query_hotspots(client, source: str, bbox: tuple, start_date: date, end_date: date) -> dict:
    features = []
    total_rejected = 0
    rejection_reasons: Counter[str] = Counter()
    cursor = start_date
    bbox_text = ",".join(str(coordinate) for coordinate in bbox)
    while cursor <= end_date:
        days = min(5, (end_date - cursor).days + 1)
        payload = client.fetch_area_csv(source, bbox_text, days, cursor.isoformat())
        batch, rejected, reasons = parse_hotspots_csv(
            payload,
            source,
            bbox,
            cursor,
            cursor + timedelta(days=days - 1),
        )
        features.extend(batch)
        total_rejected += rejected
        rejection_reasons.update(reasons)
        cursor += timedelta(days=days)

    return {
        "features": features,
        "count": len(features),
        "records_rejected": total_rejected,
        "rejection_reasons": dict(sorted(rejection_reasons.items())),
        "bbox": bbox_text,
    }


def source_details(source: str) -> dict:
    return {"code": source, **SOURCES[source]}
