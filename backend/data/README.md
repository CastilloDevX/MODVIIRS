# Dataset armonizado MODIS–VIIRS

Salida de `harmonize_firms.py` (+ `aoi_queries.py` y `build_training_dataset.py`) a partir de `../parquet/{instrumento}/{año}/{País}.parquet`.
Dos capas + metadatos. Método **D** (rejilla 0.1° + días-con-fuego) + **G** (anomalía por sensor). Decisión y defensa: `docs/ARMONIZACION_DECISION.md`.

> **Estado de validación:** las pruebas con datos reales se hicieron solo con muestras escasas (México y Brasil). El diagnóstico decisivo
> (`[solape 2012-2024]` de `build_training_dataset.py` con los 6 países completos) está pendiente; no se debe afirmar que la armonización está *validada*.
> Las medianas y anomalías son de **días-con-fuego**, no de conteos de hotspots.

## Archivos y esquema

| Archivo | Qué es | Columnas | ¿En el repo? |
|---|---|---|---|
| `hotspots_harmonized.parquet` | **Capa de puntos**: una fila por detección, esquema único (no fusiona 1 km con 375 m). Mapa, descarga CSV y modelos a nivel de evento | `latitude, longitude, acq_date_d, year, month, country, sensor_group, satellite, res_m, conf_class, frp, daynight, bright_main, version, type, is_persistent, frp_comparable, cy, cx` | No (~2.9 GB) |
| `activity_grid.parquet` | **Capa de actividad**: celda 0.1° × mes × sensor × país, solo donde hubo fuego (sin ceros explícitos), sin fuentes persistentes. Fuente de `/calendar` y `/medians`. **Métrica primaria: `active_fire_days`** | `cy, cx, year, month, sensor_group, country, count, active_fire_days, frp_sum, frp_mean, cell_lat, cell_lon` | No (~233 MB) |
| `activity_daily.parquet` | Celda × día × sensor × país (timeline diario y mes a la fecha). Se genera con `python aoi_queries.py build-daily` | `cy, cx, acq_date_d, sensor_group, country, n_hotspots, frp_sum` | No (se genera) |
| `cell_climatology.parquet` | Línea base por celda/mes/sensor/país **con ceros** (baseline MODIS 2001–2024, VIIRS 2012–2024). Para colorear celdas | `cy, cx, country, month, sensor_group, afd_mean, afd_std, afd_p50, afd_p90, n_years, n_years_fire` | Sí |
| `scaling_factors.parquet` | Factor de magnitud VIIRS/MODIS **por país** en el solape 2012–2024 (método A, opcional) | `country, afd_m, cnt_m, frp_m, afd_v, cnt_v, frp_v, factor_afd_viirs_over_modis, factor_cnt_viirs_over_modis, factor_frp_viirs_over_modis` | Sí |
| `persistent_mask.parquet` | Celdas 0.01° de fuentes persistentes (toggle "excluir persistentes") | `py, px, is_persistent` | Sí |
| `gaps.csv` | Huecos conocidos de sensor, **informativo** (leyenda de UI). El código no lo lee | `sensor_group, platform, start, end, cause` | Sí |
| `validation_report.csv` | Suma mensual de `active_fire_days` MODIS vs VIIRS en el solape (evidencia para jueces) | `year, month, MODIS, VIIRS` | Sí |
| `training_dataset.parquet/.csv` | Serie continua celda×mes con ceros (MODIS hasta 2011, VIIRS desde 2012-01) | ver `docs/GUIA_DATASETS.md` | No (se genera) |

Índices de celda: `cy = floor(lat / 0.1)`, `cx = floor(lon / 0.1)` (floor, no `int()`: falla con coordenadas negativas). `py, px` igual con 0.01°.
`sensor_group`: `MODIS` (Terra+Aqua, 1 km) o `VIIRS` (S-NPP + NOAA-20 + NOAA-21, 375 m).

## Reglas aplicadas (están en el código)

- `confidence`: se conservan `nominal` y `high`; se descarta `low`. MODIS numérico: ≥ 80 high, ≥ 30 nominal, < 30 low. VIIRS: `h`/`n`/`l`.
- Fuentes persistentes: celda 0.01° con fuego en ≥ 60 meses distintos (`PERSIST_MIN_MONTHS`), sobre todos los sensores. Se marcan en la capa de puntos (`is_persistent`) y se excluyen de `activity_grid`/`activity_daily`.
- `frp_comparable`: `frp >= 15 MW` (`FRP_COMPARABLE_MW`).
- Meses con hueco que se excluyen al calibrar y de la climatología (`EXCLUDE_YM`): MODIS abr-2022, VIIRS jul-2022 y ago-2022. En `aoi_calendar` salen con `valid=False`.
  Un mes válido sin fuego vale 0; un mes sin datos del sensor es "sin datos" (no cero).
- Anomalía por AOI: sumar las celdas del AOI por mes y comparar contra la historia del propio AOI (`aoi_calendar()`); **nunca** promediar z de celdas.
  El AOI se aproxima por su bbox ajustado a celdas de 0.1° (debe indicarse en la UI).
- Comparación del mes en curso: VIIRS contra VIIRS (2012–2024).

## Cómo regenerar (desde cualquier directorio; rutas relativas al propio script)

```
python armonizacion/harmonize_firms.py                  # desde Data/; lee ../parquet y escribe aquí
python armonizacion/aoi_queries.py rebuild-climatology  # recalcula cell_climatology desde activity_grid
python armonizacion/aoi_queries.py build-daily          # activity_daily.parquet
python armonizacion/build_training_dataset.py           # training_dataset.* + diagnóstico de empalme
```
Prueba rápida con un país: `FIRMS_SMOKE=1` (PowerShell: `$env:FIRMS_SMOKE="1"`; opcional `FIRMS_SMOKE_COUNTRY=Mexico`).
`FIRMS_RAW` cambia la carpeta de entrada y `FIRMS_OUT` la de salida (también la usan `aoi_queries.py` y `build_training_dataset.py`).
Dependencias: `pip install -r ../requirements.txt` (el pipeline solo usa polars y pyarrow).

## Uso desde el backend

```python
import sys; sys.path.insert(0, "Data/armonizacion")      # o instalar/copiar el módulo
import aoi_queries as Q
Q.aoi_calendar(19.0, 20.0, -100.0, -99.0, "VIIRS")        # year, month, afd, valid, mean, std, p50, n_base, z, pctl
Q.aoi_monthly_medians(19.0, 20.0, -100.0, -99.0)          # 12 filas: month, median, p25, p75, mean, std, min, max, n_years, baseline_corto
```
`/calendar` y `/medians` solo necesitan `activity_grid.parquet`. Funciones, endpoints y plan de implementación: `docs/IMPLEMENTACION_API.md`; tablas y casos de uso: `docs/GUIA_DATASETS.md`.
