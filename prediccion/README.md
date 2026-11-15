# Modelo predictivo de anomalías de puntos de calor (rama `predictivo`)

> **"El sistema anticipa con X % de probabilidad un comportamiento anómalo de puntos de calor en la semana T en la zona Z."**
> Península de Yucatán · zonas de 0.5° (~55 km) · horizonte de 1 semana (1–4 opcional).

Usa la **armonización de Alexis** (`backend/data/hotspots_harmonized.parquet`): esquema común, confianza nominal+alta y máscara de fuentes persistentes. La anomalía se normaliza **por era**: Aqua se compara contra Aqua y S-NPP contra S-NPP, igual que el método G de Alexis.

## Cómo correrlo
```bash
pip install -r prediccion/requirements.txt
python prediccion/src/p00_extraer_peninsula.py     # extrae México/península del parquet de Alexis (~15 s)
python prediccion/src/p01_actividad_semanal.py     # días-con-fuego semanales por celda, 1 plataforma por era
python prediccion/src/p02_modelo.py clima 1        # modelo + validación walk-forward (~30 s)
python prediccion/src/p03_figura_eras.py           # figura del pitch: falsas anomalías sin armonizar
```
`data/raw/power_daily.parquet` (clima NASA POWER) se descarga con `NASA-challenge/src/00_descarga_power.py` o se comparte por Drive. `data/` no se sube a git.

## Pipeline
| Paso | Qué hace |
|---|---|
| p00 | Del parquet de Alexis (6 países) toma México dentro de −92.5, 17.8, −86.7, 21.7 |
| p01 | Aplica `type == 0` y `is_persistent == False`. Usa **una plataforma por era** (Aqua hasta 2012-01-22, S-NPP desde 2012-01-23; R3 de Alexis). Calcula **días con fuego** por celda de 0.1° y semana (0–7). Marca como no válidas las semanas en huecos de sensor (S-NPP jul–ago 2022) |
| `anomalias.py` | Actividad por zona (5 × 5 celdas). **p90 histórico de la misma zona, semanas del año ±2, solo años anteriores y solo de la misma era** (mínimo 3 años). Anomalía = actividad > max(p90, 3). Línea base = frecuencia histórica de anomalías |
| p02 | Variables hasta T−H: rezagos crudos y relativos al umbral de su era, anomalías previas, p50/p90 esperados, señal regional, frecuencia histórica y clima NASA POWER (lluvia 30/90 d, anomalía de lluvia, días sin lluvia, humedad, temperatura máxima, viento). `HistGradientBoostingClassifier`, con validación walk-forward por año |

## Resultados (fuera de muestra, era VIIRS)
| Horizonte | AUC | AP | Brier | Línea base (AUC / AP / Brier) |
|---|---|---|---|---|
| 1 semana | **0.847** | **0.272** (3.8× la base) | **0.0433** | 0.582 / 0.071 / 0.0664 |
| 2 semanas | 0.810 | 0.191 | 0.0468 | ídem |
| 4 semanas | 0.776 | 0.143 | 0.0493 | ídem |

- Promedio 2015–2025. Para 2018–2025: AUC 0.846 (base 0.601), AP 0.260 (base 0.068).
- El clima de NASA POWER mejora la AP en 14 de 15 años (Wilcoxon p = 0.0026; AUC p = 0.0067).
- Falsas anomalías: con la historia mezclada (sin armonizar), el 18.1 % de las zona-semanas de 2013 y el 16.4 % de las de 2015 salen "anómalas". Normalizando por era, 2015 queda en 8.8 % (`outputs/figures/falsas_anomalias_mezclada_vs_por_era.png`).

## Limitaciones
- 2012–2014 no tienen línea base VIIRS (se requieren 3 años dentro de la era). En 2015–2017 la línea base es corta.
- La calibración es buena hasta ~40 %. En las probabilidades altas (>70 %) el modelo es optimista (n pequeño).
- Predice **actividad anómala de puntos de calor**, no la ubicación de incendios forestales. Contra CONAFOR acierta el cuándo, pero no el dónde.
- Solo usa el clima pasado (sin pronóstico). Los datos SP llegan a dic-2025; para la semana actual hace falta NRT.

## En vivo (backend Flask + frontend)

El modelo vive en `backend/src/modviirs/` siguiendo la arquitectura del repo:

| Archivo | Rol |
|---|---|
| `models/burn_model.py` | `BurnModel`: tabla zona × semana, p90 por era, variables y entrenamiento (segundos; no se serializa) |
| `clients/firms_client.py` | FIRMS Area API (ventanas de 5 días; `data_availability`) |
| `clients/power_client.py` | NASA POWER diario por punto |
| `services/prediction_service.py` | `actualizar()`: FIRMS NOAA-20 2026 (SP + NRT) → reglas de Alexis → días con fuego → POWER → modelo → `data/prediccion/cache/prediccion_actual.json`. También las lecturas para los endpoints y `snapshot()` |
| `api/predictions.py` | Endpoints `/api/v1/predictions…` |

Artefactos (generados por `prediccion/src/p04_exportar_backend.py`): `backend/data/prediccion/` (historia por zona, semanas, zonas, POWER 2002–2025, predicciones walk-forward y `validacion.json`).

**Endpoints**
| Ruta | Devuelve |
|---|---|
| `GET /api/v1/predictions[?lat_min&lat_max&lon_min&lon_max]` | GeoJSON de la semana en curso (H = 1) y la próxima (H = 2), con prob, nivel, base, p50/p90, valor y anomalía |
| `GET /api/v1/predictions/weeks` | Semanas disponibles (histórico walk-forward y vivo 2026) |
| `GET /api/v1/predictions/week/YYYY-MM-DD` | GeoJSON de una semana (lunes) |
| `GET /api/v1/predictions/validation` | Métricas walk-forward, calibración, Wilcoxon, falsas anomalías y temporada 2026 en vivo |

**Correr (PowerShell, desde `backend/`)**
```powershell
py -3.12 -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.lock; pip install --no-deps -e .
$env:MODVIIRS_FIRMS_MAP_KEY = "<tu MAP_KEY>"          # nunca en git ni en el frontend
flask --app wsgi prediction-update                    # ~1–2 min: FIRMS + POWER + entrenamiento
flask --app wsgi prediction-snapshot                  # respaldo estático en frontend/public/prediccion
flask --app wsgi run --debug --port 5000
```
Frontend: `cd frontend; npm ci; npm run dev` → http://localhost:5173/map. Panel "Anomaly forecast": *Timeline* (semana bajo el cursor), *This wk*, *Next wk*.

- **Refresco automático:** `$env:MODVIIRS_PREDICTION_REFRESH_HOURS = 6` lanza un hilo que actualiza cada 6 h. Usar con 1 solo worker; en producción, mejor un cron con `prediction-update`.
- **Respaldo:** si la API no responde, el frontend lee `frontend/public/prediccion/*.json`.
- **Prueba sin internet:** `PYTHONPATH=backend/src python prediccion/src/p05_simular_vivo.py` (simula 2026 con datos de 2025; solo prueba el flujo).
