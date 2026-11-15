from __future__ import annotations

from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener

BASE_URL = "https://firms.modaps.eosdis.nasa.gov"
REQUEST_TIMEOUT_SECONDS = 30

SOURCES = {
    "MODIS_SP": {
        "sensor": "MODIS",
        "platform": "Terra/Aqua",
        "processing_type": "standard",
    },
    "MODIS_NRT": {
        "sensor": "MODIS",
        "platform": "Terra/Aqua",
        "processing_type": "near-real-time",
    },
    "VIIRS_SNPP_SP": {
        "sensor": "VIIRS",
        "platform": "Suomi-NPP",
        "processing_type": "standard",
    },
    "VIIRS_SNPP_NRT": {
        "sensor": "VIIRS",
        "platform": "Suomi-NPP",
        "processing_type": "near-real-time",
    },
    "VIIRS_NOAA20_SP": {
        "sensor": "VIIRS",
        "platform": "NOAA-20",
        "processing_type": "standard",
    },
    "VIIRS_NOAA20_NRT": {
        "sensor": "VIIRS",
        "platform": "NOAA-20",
        "processing_type": "near-real-time",
    },
    "VIIRS_NOAA21_SP": {
        "sensor": "VIIRS",
        "platform": "NOAA-21",
        "processing_type": "standard",
    },
    "VIIRS_NOAA21_NRT": {
        "sensor": "VIIRS",
        "platform": "NOAA-21",
        "processing_type": "near-real-time",
    },
}


class FirmsClientError(Exception):
    """Error sanitizado de configuración o comunicación con FIRMS."""


class FirmsNotConfiguredError(FirmsClientError):
    pass


class FirmsTimeoutError(FirmsClientError):
    pass


class FirmsRateLimitError(FirmsClientError):
    pass


class FirmsUpstreamError(FirmsClientError):
    pass


class FirmsInvalidResponseError(FirmsClientError):
    pass


class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class FirmsClient:
    def __init__(self, map_key: str | None, timeout: float = REQUEST_TIMEOUT_SECONDS, opener=None):
        self._map_key = map_key.strip() if map_key and map_key.strip() else None
        self.timeout = timeout
        self._opener = opener or build_opener(_RejectRedirects()).open

    def fetch_area_csv(self, source: str, bbox: str, days: int, start_date: str) -> bytes:
        if not self._map_key:
            raise FirmsNotConfiguredError("La clave de NASA FIRMS no está configurada.")
        if source not in SOURCES or not 1 <= days <= 5:
            raise ValueError("Fuente o duración de consulta FIRMS inválida.")

        url = (
            f"{BASE_URL}/api/area/csv/{quote(self._map_key, safe='')}/"
            f"{source}/{bbox}/{days}/{start_date}"
        )
        request = Request(url, headers={"Accept": "text/csv", "User-Agent": "MODVIIRS/1.0"})
        try:
            response = self._opener(request, timeout=self.timeout)
        except HTTPError as error:
            status = error.code
            error.close()
            if status == 429:
                raise FirmsRateLimitError(
                    "NASA FIRMS informó que se alcanzó el límite de consultas."
                ) from None
            if status in (401, 403):
                raise FirmsNotConfiguredError(
                    "NASA FIRMS rechazó la credencial configurada."
                ) from None
            raise FirmsUpstreamError("NASA FIRMS respondió con un error HTTP.") from None
        except TimeoutError:
            raise FirmsTimeoutError(
                "La consulta a NASA FIRMS excedió el tiempo de espera."
            ) from None
        except URLError as error:
            if isinstance(error.reason, TimeoutError):
                raise FirmsTimeoutError(
                    "La consulta a NASA FIRMS excedió el tiempo de espera."
                ) from None
            raise FirmsUpstreamError("No se pudo establecer conexión con NASA FIRMS.") from None
        except (OSError, HTTPException):
            raise FirmsUpstreamError("No se pudo establecer conexión con NASA FIRMS.") from None

        try:
            status = response.getcode()
            if status is None or status < 200 or status >= 300:
                if status == 429:
                    raise FirmsRateLimitError(
                        "NASA FIRMS informó que se alcanzó el límite de consultas."
                    )
                raise FirmsUpstreamError("NASA FIRMS respondió con un estado HTTP inesperado.")
            try:
                return response.read()
            except TimeoutError:
                raise FirmsTimeoutError(
                    "La descarga de NASA FIRMS excedió el tiempo de espera."
                ) from None
            except HTTPException:
                raise FirmsUpstreamError("La respuesta de NASA FIRMS se interrumpió.") from None
            except OSError:
                raise FirmsUpstreamError("No se pudo leer la respuesta de NASA FIRMS.") from None
        finally:
            try:
                response.close()
            except OSError:
                pass
