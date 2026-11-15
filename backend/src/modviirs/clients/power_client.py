"""Cliente de NASA POWER (clima diario por punto, sin llave)."""

from datetime import date

import numpy as np
import pandas as pd
import requests

URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMS = "PRECTOTCORR,RH2M,T2M_MAX,WS10M"


class PowerClient:
    def __init__(self, timeout: int = 120) -> None:
        self._timeout = timeout

    def daily_point(self, lat: float, lon: float, start: date, end: date) -> pd.DataFrame:
        q = dict(
            parameters=PARAMS,
            community="AG",
            latitude=round(lat, 3),
            longitude=round(lon, 3),
            start=start.strftime("%Y%m%d"),
            end=end.strftime("%Y%m%d"),
            format="JSON",
        )
        r = requests.get(URL, params=q, timeout=self._timeout)
        r.raise_for_status()
        p = r.json()["properties"]["parameter"]
        d = pd.DataFrame(p)
        d.index = pd.to_datetime(d.index, format="%Y%m%d")
        d = d.replace(-999, np.nan).rename_axis("fecha").reset_index()
        d["lat"], d["lon"] = lat, lon
        return d
