# Instrucciones para agentes — backend Flask

## Qué es este backend

API Flask (`/api/v1`) que expone el calendario de actividad de quema MODIS/VIIRS para un
área de interés (AOI). Lee archivos Parquet en disco y, para datos del mes en curso, consulta
la NASA FIRMS Area API. No tiene base de datos propia.

## Estructura de paquete

```
src/modviirs/
├── __init__.py          # create_app — application factory
├── api/
│   ├── __init__.py      # registra Blueprints bajo /api/v1
│   ├── fires.py         # /fires/calendar, /medians, /points, /timeline, /current
│   └── predictions.py   # /predictions
├── services/
│   └── fire_service.py  # lógica de negocio; delega a queries y clients
├── data/
│   └── queries.py       # capa de datos — aoi_queries.py vive aquí
├── clients/
│   └── firms_client.py  # FIRMSClient — llama a la FIRMS Area API
└── models/
    └── burn_model.py    # BurnModel — predictor de anomalía
```

Cadena de importación: `api → services → data/queries + clients → models`.
Las rutas solo llaman a `fire_service`; `fire_service` llama a `queries` o `FIRMSClient`.
No importar `queries` directamente desde `api/`.

## Variables de entorno

| Variable | Uso |
|---|---|
| `MODVIIRS_FIRMS_MAP_KEY` | MAP_KEY para la FIRMS Area API; solo vive en el backend |
| `MODVIIRS_DATA_PATH` | Ruta al directorio con los archivos Parquet (default: `data/`) |

Flask las carga automáticamente con `app.config.from_prefixed_env(prefix="MODVIIRS")`.
**El MAP_KEY nunca debe aparecer en respuestas, logs ni llegar al frontend.**

## Ejecutar localmente

```bash
pip install -e ".[dev]"   # instalar
pytest                     # tests
ruff check src/            # linter
flask --app wsgi run --debug                       # servidor
gunicorn wsgi:app                                  # producción
```
