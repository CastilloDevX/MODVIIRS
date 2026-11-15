> Nota: este documento se escribió dentro del proyecto de trabajo (Claude Project). Las referencias a `notas_fuentes_datos_firms.md`, `investigacion_armonizacion.md`, `descarga_por_pais_firms.md` y `eda_seis_paises_resultados.md` apuntan a notas externas al repo; lo que sí está en el repo es `../README.md`, `GUIA_DATASETS.md`, `IMPLEMENTACION_API.md`, `ARMONIZACION_DECISION.md` y los notebooks de `analisis/`.

# Guía de datasets: estructura, uso y casos de uso — actualizada 14-nov-2026

[DATOS][ARMONIZACIÓN][BACKEND/FRONTEND] Vistazo rápido a las tablas que existen en `Data\`, qué contiene cada una, cómo consultarla y para qué caso de uso del demo sirve. Contexto metodológico en `ARMONIZACION_DECISION.md`; pasos de ejecución en `../README.md`; plan para construir la API en `IMPLEMENTACION_API.md`.

**Estado de cada elemento** (según lo verificado en esta sesión):
- ✅ Probado con muestras (México + Brasil): `activity_grid`, `hotspots_harmonized`, `scaling_factors`, `persistent_mask`, `gaps`, `validation_report`.
- ✅ Corregido con ceros y verificado contra cálculo de fuerza bruta (300 celdas, 0 fallos): `cell_climatology` (nueva versión) y `aoi_calendar()`.
- ✅ Probado con muestra (resultado idéntico a fuerza bruta): `activity_daily`, `aoi_daily()`, `normalize_nrt()`, `aoi_mtd_compare()`.
- 🟡 Escrito, sin validar el empalme con datos completos: `training_dataset`.
- ⬜ Pendiente: variante NOAA-20 solo, línea base común, 2026 desde la API, `normalize_nrt` contra una respuesta real de la API.

## 1. Mapa general

```
Data/
├─ csv/ , parquet/{modis,viirs-snpp,viirs-jpss1}/{año}/{País}.parquet   ← crudos FIRMS (6 países, archivo hasta 2025)
├─ analisis/02_eda/                                                      ← tablas AGREGADAS del EDA (solo diagnóstico)
└─ armonizacion/
   ├─ harmonize_firms.py            genera las tablas de abajo (y define aoi_calendar)
   ├─ aoi_queries.py                funciones por AOI para el backend + build-daily + rebuild-climatology
   ├─ build_training_dataset.py     genera training_dataset.*
   ├─ hotspots_harmonized.parquet   CAPA DE PUNTOS
   ├─ activity_grid.parquet         CAPA DE ACTIVIDAD (celda×mes×sensor×país)
   ├─ activity_daily.parquet        celda×día×sensor×país (timeline diario y acumulado del mes)
   ├─ cell_climatology.parquet      línea base por celda, CON ceros
   ├─ scaling_factors.parquet       factores VIIRS/MODIS por país
   ├─ persistent_mask.parquet       celdas 0.01° de fuentes persistentes
   ├─ gaps.csv                      huecos de sensor
   ├─ validation_report.csv         evidencia MODIS vs VIIRS en el solape
   └─ training_dataset.parquet/.csv serie continua para modelos
```

Grano común: rejilla **0.1°** (índices enteros `cy = floor(lat/0.1)`, `cx = floor(lon/0.1)`), paso mensual (diario en `activity_daily`). `sensor_group`: `MODIS` (Terra+Aqua, 1 km) o `VIIRS` (S-NPP + NOAA-20 + NOAA-21, 375 m). Filtros: `confidence` nominal+high (se descarta low).

## 2. Tablas y estructura

### hotspots_harmonized.parquet — capa de puntos
Una fila por detección. `latitude, longitude, acq_date_d (Date), year, month, country, sensor_group, satellite, res_m (1000/375), conf_class (nominal/high), frp (MW), daynight (D/N), bright_main (K), version, type (0–3), is_persistent (bool), frp_comparable (frp ≥ 15 MW), cy, cx`.
Valores de `satellite` vistos en la muestra: `Terra`, `Aqua`, `N` (S-NPP), `N20`. `N21` sin confirmar. Es esquema común, no fusión: el origen siempre se conserva.

### activity_grid.parquet — capa de actividad
Una fila por celda × mes × sensor_group × país **solo si hubo fuego** (no hay ceros explícitos). `cy, cx, cell_lat, cell_lon, year, month, sensor_group, country, active_fire_days` (0–31), `count`, `frp_sum`, `frp_mean`. Sin fuentes persistentes.

### activity_daily.parquet — celda × día (nueva)
`cy, cx, acq_date_d, sensor_group, country, n_hotspots, frp_sum`; sin fuentes persistentes. Se genera con `python aoi_queries.py build-daily`. Métrica derivada: **celda-días con fuego** (pares celda–día con ≥1 hotspot); sumada en un mes equivale a `active_fire_days`.

### cell_climatology.parquet — línea base por celda (corregida)
Clave `cy, cx, country, month, sensor_group` (**ahora incluye `country`**); `afd_mean, afd_std, afd_p50, afd_p90` (percentiles con interpolación lineal), `n_years` (años válidos del baseline), `n_years_fire` (años con fuego). Baseline: MODIS 2001–2024, VIIRS 2012–2024. Los meses válidos sin fuego cuentan como 0. Los meses de hueco conocido (`EXCLUDE_YM`) no entran. Para recalcular sin repetir el pipeline: `python aoi_queries.py rebuild-climatology`.

### scaling_factors.parquet
Por país: `factor_afd_viirs_over_modis`, `factor_cnt_…`, `factor_frp_…` (VIIRS/MODIS en el solape 2012–2024). En muestras: afd ≈ 2.4–2.6, conteo ≈ 3.8–3.9, FRP ≈ 0.84–0.87.

### persistent_mask.parquet · gaps.csv · validation_report.csv
`persistent_mask`: `py, px` (celdas 0.01° con fuego en ≥60 meses distintos). `gaps.csv`: `sensor_group, platform, start, end, cause` ("sin datos" ≠ "cero"); es informativo (para la UI y `/meta/gaps`): el código **no** lo lee. Lo que decide `valid=False` y la exclusión de la climatología es `EXCLUDE_YM` en `harmonize_firms.py` (Aqua abr-2022, S-NPP jul/ago-2022) más la ausencia de datos del sensor ese mes. `validation_report.csv`: `year, month, MODIS, VIIRS`.

### training_dataset.parquet / .csv
Una fila por celda × mes, con ceros explícitos, serie única (MODIS hasta 2011, VIIRS desde 2012-01). `date, year, month, country, cy, cx, cell_lat, cell_lon, sensor_group (metadato), afd, afd_z (target recomendado), afd_anom, afd_viirs_equiv, afd_mean, afd_std, n_hotspots, frp_sum`. `afd_z` nulo si hay <8 años de baseline (configurable con `MIN_YEARS_Z` en el script) o std = 0.

## 3. Funciones de consulta (`aoi_queries.py` y `harmonize_firms.py`)

| Función | Entrada → salida | Fuente |
|---|---|---|
| `aoi_calendar(lat_min, lat_max, lon_min, lon_max, sensor_group)` | serie mensual: `year, month, afd, valid, mean, std, p50, n_base, z, pctl` (con ceros; meses de hueco con `valid=False`) | `activity_grid` |
| `aoi_monthly_medians(lat_min, lat_max, lon_min, lon_max, sensor_group)` | 12 filas: `month, median, p25, p75, mean, std, min, max, n_years, baseline_corto` (ceros incluidos) | `activity_grid` |
| `aoi_daily(bbox_latlon, start, end, sensor_group)` (opcional, en pausa) | `date, cells_active, n_hotspots, frp_sum` | `activity_daily` |
| `aoi_mtd_baseline(bbox_latlon, month, day)` | celda-días del tramo día 1…`day` del mes, por año del baseline VIIRS | `activity_daily` |
| `aoi_mtd_compare(bbox_latlon, nrt_norm, as_of)` | mes actual vs mediana/percentiles históricos del mismo tramo | NRT normalizado + `activity_daily` |
| `nrt_request_plan(bbox, start, end)` | requests a la Area API (solo VIIRS, ventanas ≤5 días), sin MAP_KEY | — |
| `normalize_nrt(raw)` | CSV crudo de la API → esquema armonizado | `persistent_mask` |
| `aoi_cell_range(...)` | índices de celda del AOI con `floor` (no `int`, que falla con coordenadas negativas) | — |

## 4. Casos de uso del demo

| Necesito… | Usar | Nota |
|---|---|---|
| Calendario mensual de un AOI, coloreado por anomalía | `aoi_calendar` | z a nivel AOI, nunca promediando z de celdas |
| Mes actual (NRT) vs mediana histórica | `nrt_request_plan` → API → `normalize_nrt` → `aoi_mtd_compare` | VIIRS contra VIIRS; el mes en curso es preliminar |
| Puntos en el mapa de un día o rango | `hotspots_harmonized` | Filtrar por bbox y `acq_date_d`; tope de puntos por zoom |
| Interruptores del mapa | `hotspots_harmonized` | `frp_comparable`, `is_persistent`, `sensor_group`/`satellite` |
| Descarga CSV de hotspots | `hotspots_harmonized` | Misma consulta del mapa, exportada completa |
| Timeline mensual (2000–hoy) | `aoi_calendar` | Una sola escala vía z/percentil |
| Timeline diario | `aoi_daily` | Celdas activas y FRP; una línea por `sensor_group`; sin z diario |
| Entrenar/predecir anomalía | `training_dataset` (`afd_z`) | Partición temporal; no usar `sensor_group` como feature |
| Evidencia para jueces | `validation_report.csv` + diagnóstico `[solape 2012-2024]` | Pendiente de correr completo |
| "Sin datos" vs "cero" | `valid` en `aoi_calendar` (fuente de verdad); `gaps.csv` solo como leyenda | Pintar distinto |

## 5. Ejemplos mínimos

```python
import datetime as dt, polars as pl
import aoi_queries as Q

cal = Q.aoi_calendar(19.0, 20.0, -100.0, -99.0, "VIIRS")           # calendario con z y percentil
day = Q.aoi_daily((19.0, 20.0, -100.0, -99.0), dt.date(2024, 3, 1), dt.date(2024, 3, 31))

pts = (pl.scan_parquet("hotspots_harmonized.parquet")
         .filter(pl.col("latitude").is_between(19.0, 20.0) & pl.col("longitude").is_between(-100.0, -99.0)
                 & pl.col("acq_date_d").is_between(dt.date(2024, 3, 1), dt.date(2024, 3, 31))
                 & ~pl.col("is_persistent")).collect())
```

## 6. Pendientes y decisiones abiertas
- Correr el run completo y revisar `[solape 2012-2024]` de `build_training_dataset.py`.
- Decidir línea base común 2012–2024 para MODIS y VIIRS (recomendada).
- Ejecutar en tu máquina: `python aoi_queries.py rebuild-climatology` y `python aoi_queries.py build-daily`.
- Predictor con NOAA-20 solo: variante desde `hotspots_harmonized` y mínimo de años del z más bajo (historia ≈ 2018–hoy).
- 2026 no está en el archivo por país: debe venir de la Area API (ver `IMPLEMENTACION_API.md`).
- Verificar si hay hotspots duplicados entre archivos de países vecinos; las sumas por AOI entre países asumen que no.
