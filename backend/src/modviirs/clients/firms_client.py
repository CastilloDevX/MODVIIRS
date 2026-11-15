class FIRMSClient:
    """HTTP client for the NASA FIRMS Area API.

    MAP_KEY is read from Flask config (env var MODVIIRS_FIRMS_MAP_KEY).
    Used by fire_service.get_current() for NRT data (I4 in IMPLEMENTACION_API.md).

    Rate limit: 5 000 transactions per 10 min per key.
    S-NPP ceased publishing on 2026-11-02; use NOAA-20 and NOAA-21 only for 2026.
    """

    BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

    def __init__(self, map_key: str) -> None:
        self._map_key = map_key

    def fetch_area(self, source: str, bbox_lonlat: tuple, day_range: int, date: str) -> str:
        """Fetch fire detections from the FIRMS Area API.

        Args:
            source: FIRMS source identifier, e.g. "VIIRS_NOAA20_NRT".
            bbox_lonlat: (west, south, east, north) in decimal degrees.
            day_range: Number of days to retrieve (1–5).
            date: End date in YYYY-MM-DD format.

        Returns:
            Raw CSV text from the API response.

        Raises:
            ValueError: If the response does not look like CSV (e.g. error message).
            requests.HTTPError: On non-2xx HTTP status.
        """
        raise NotImplementedError
