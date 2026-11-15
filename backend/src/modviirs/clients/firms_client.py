import io
from datetime import date, timedelta

import pandas as pd
import requests


class FIRMSClient:
    """HTTP client for the NASA FIRMS Area API.

    MAP_KEY is read from Flask config (env var MODVIIRS_FIRMS_MAP_KEY).
    Rate limit: 5 000 transactions per 10 min per key.
    S-NPP ceased publishing on 2026-11-02; use NOAA-20 and NOAA-21 only for 2026.
    """

    BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
    AVAILABILITY_URL = "https://firms.modaps.eosdis.nasa.gov/api/data_availability/csv"

    def __init__(self, map_key: str, timeout: int = 60) -> None:
        if not map_key:
            raise ValueError("Falta MODVIIRS_FIRMS_MAP_KEY.")
        self._map_key = map_key
        self._timeout = timeout

    def fetch_area(self, source: str, bbox_lonlat: tuple, day_range: int, date: str) -> str:
        """Fetch fire detections from the FIRMS Area API.

        Args:
            source: FIRMS source identifier, e.g. "VIIRS_NOAA20_NRT".
            bbox_lonlat: (west, south, east, north) in decimal degrees.
            day_range: Number of days to retrieve (1–5).
            date: Start date in YYYY-MM-DD format (the API returns [date, date + day_range - 1]).

        Returns:
            Raw CSV text from the API response.
        """
        area = ",".join(str(v) for v in bbox_lonlat)
        url = f"{self.BASE_URL}/{self._map_key}/{source}/{area}/{int(day_range)}/{date}"
        r = requests.get(url, timeout=self._timeout)
        r.raise_for_status()
        text = r.text
        if not text.startswith("latitude"):
            raise ValueError(f"Respuesta inesperada de FIRMS ({source} {date}): {text[:120]}")
        return text

    def fetch_range(self, source: str, bbox_lonlat: tuple, start: date, end: date) -> pd.DataFrame:
        """Descarga [start, end] en ventanas de 5 dias y devuelve un DataFrame."""
        partes, d = [], start
        while d <= end:
            n = min(5, (end - d).days + 1)
            txt = self.fetch_area(source, bbox_lonlat, n, d.isoformat())
            df = pd.read_csv(io.StringIO(txt), dtype={"acq_time": str, "confidence": str})
            if len(df):
                partes.append(df)
            d += timedelta(days=n)
        return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()

    def availability(self) -> pd.DataFrame:
        r = requests.get(f"{self.AVAILABILITY_URL}/{self._map_key}/all", timeout=self._timeout)
        r.raise_for_status()
        return pd.read_csv(io.StringIO(r.text), parse_dates=["min_date", "max_date"])
