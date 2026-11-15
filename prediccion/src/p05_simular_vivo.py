"""p05 - Prueba del flujo EN VIVO del backend sin internet (para la VM de desarrollo).

Simula 2026 con los datos NOAA-20 de 2025 del parquet de Alexis desplazados +364 dias (mismo dia de
la semana) y el clima POWER de 2025 igual. Solo prueba que el flujo funciona, NO mide habilidad.
Uso: PYTHONPATH=backend/src python prediccion/src/p05_simular_vivo.py
"""
import json
from datetime import date

import pandas as pd

import config as C
from modviirs import create_app
from modviirs.services import prediction_service as svc

p = pd.read_parquet(C.PUNTOS)
p = p[(p.satellite == "N20") & (p.acq_date_d >= pd.Timestamp("2025-01-01").date())].copy()
f = pd.to_datetime(p.acq_date_d) + pd.Timedelta(days=364)
det = pd.DataFrame({"latitude": p.latitude, "longitude": p.longitude,
                    "acq_date": f.dt.strftime("%Y-%m-%d"), "acq_time": "0000", "satellite": "N20",
                    "confidence": p.conf_class.str[0]})
det = det[pd.to_datetime(det.acq_date) <= "2026-11-15"]
pw = pd.read_parquet(C.POWER)
pw = pw[pw.fecha >= "2025-01-01"].copy()
pw["fecha"] = pw.fecha + pd.Timedelta(days=364)

app = create_app({"TESTING": True})
res = svc.actualizar(app.config, hoy=date(2026, 11, 15), detecciones=det, power=pw)
CACHE = svc.cache_dir(app.config) / "prediccion_actual.json"
print(json.dumps(res, indent=1, default=str))
c = app.test_client()
for url in ["/api/v1/predictions", "/api/v1/predictions/weeks", "/api/v1/predictions/week/2024-04-22",
            "/api/v1/predictions/week/2026-04-20", "/api/v1/predictions/validation"]:
    r = c.get(url)
    j = r.get_json()
    print(url, r.status_code, {k: (v if not isinstance(v, (list, dict)) or k == "resumen" else type(v).__name__)
                               for k, v in (j.items() if isinstance(j, dict) else [])})

# no dejar datos simulados como prediccion vigente
CACHE.replace(CACHE.with_name("prediccion_actual_SIMULADO.json"))
print("cache simulado renombrado a prediccion_actual_SIMULADO.json")
