> Nota: este documento se escribió dentro del proyecto de trabajo (Claude Project). Las referencias a `notas_fuentes_datos_firms.md`, `investigacion_armonizacion.md`, `descarga_por_pais_firms.md` y `eda_seis_paises_resultados.md` apuntan a notas externas al repo; lo que sí está en el repo es `../README.md`, `GUIA_DATASETS.md`, `IMPLEMENTACION_API.md`, `ARMONIZACION_DECISION.md` y los notebooks de `analisis/`.

# Implementación de la API y funciones del backend — plan iterativo (14-nov-2026)

[BACKEND/FRONTEND][ANALÍTICA][DATOS] Qué usar y qué hacer para construir cada función del producto, en el orden en que conviene implementarlas. Cada iteración es independiente y tiene criterio de aceptación. Guía de datasets: `GUIA_DATASETS.md`. Decisión metodológica: `ARMONIZACION_DECISION.md`.

**Convenciones de este documento:** ✅ verificado (fuente o prueba en esta sesión) · 🔶 inferido/propuesto · ❓ por verificar.

## 0. Principios que no se negocian
1. **Comparación VIIRS contra VIIRS** para el mes actual: historia = `sensor_group == "VIIRS"` (baseline 2012–2024); datos nuevos = solo fuentes VIIRS de la Area API. MODIS vive en el calendario histórico, nunca contra el mes actual.
2. **Métrica = celda-días con fuego** en rejilla 0.1° (pares celda–día con ≥1 hotspot). Sumada en un mes = `active_fire_days`.
3. **La anomalía se calcula a nivel AOI** (sumar celdas, luego z/percentil contra la historia del AOI). Nunca promediar z de celdas.
4. **Ceros explícitos:** un mes válido sin fuego vale 0; un mes sin datos del sensor es "sin datos" (`valid=False`), no cero. ✅ implementado en `aoi_calendar`.
5. **El mes en curso es preliminar** (NRT) y se marca así en la respuesta.
6. **El AOI se ajusta a celdas de 0.1°** (celdas con índice dentro del bbox). Un polígono se aproxima por su bbox o por las celdas cuyo centro cae dentro; debe decirse en la UI. 🔶

## 1. Stack y estructura sugerida 🔶
Propuesta, ajustable a lo que ya tengas: servicio Python (FastAPI) que importa `aoi_queries.py` directamente; los parquet viven en disco junto al servicio y no hay base de datos.

| Necesidad | Opción recomendada | Alternativa | Trade-off |
|---|---|---|---|
| Calendario, mes a la fecha, timeline diario | polars sobre parquet (`aoi_queries.py`, ya implementado) | DuckDB | polars: cero código nuevo. DuckDB: mejor si crece el volumen |
| Puntos del mapa y CSV | DuckDB sobre `hotspots_harmonized.parquet` | polars lazy | DuckDB: SQL simple y exportación CSV directa; polars: una dependencia menos |
| Mes actual | llamada a la Area API desde el backend | snapshot precalculado del AOI | API: dato vivo; snapshot: respaldo para la demo si la API falla (ya decidido en `notas_fuentes_datos_firms.md`) |

Reglas de seguridad ✅: el MAP_KEY vive solo en el backend (variable de entorno); el frontend nunca lo ve.

## 2. Orden de implementación

### I0 — Preparar datos (una vez, en tu máquina)
1. Confirmar que el run de `harmonize_firms.py` terminó (salidas en `Data/armonizacion/`: ver `../README.md`).
2. `python aoi_queries.py rebuild-climatology` (climatología corregida con ceros y con `country` en la clave).
3. `python aoi_queries.py build-daily` (crea `activity_daily.parquet`). **Opcional por ahora:** solo lo necesitan el timeline diario (I3) y la comparación del mes a la fecha (I4), ambos en pausa.
4. `python build_training_dataset.py` y revisar la línea `[solape 2012-2024]`.
**Aceptación:** existe `cell_climatology.parquet` con columnas `n_years` y `n_years_fire`. `/calendar` y `/medians` solo necesitan `activity_grid.parquet`.

### I1 — `GET /calendar` (calendario mensual)
- **Entrada:** `bbox` (lat_min, lat_max, lon_min, lon_max), `sensor_group` (default `VIIRS`; `MODIS` para el histórico largo), rango de fechas opcional, `baseline` opcional.
- **Implementación:** `aoi_calendar(...)`. Devuelve `year, month, afd, valid, mean, std, p50, n_base, z, pctl`.
- **Qué hace el frontend:** colorear por `z` o `pctl` con rampa accesible; `valid=False` se pinta como "sin datos"; `n_base < 8` se marca como línea base corta. 🔶
- **Aceptación:** (a) la suma de `afd` de un mes coincide con sumar `active_fire_days` de las celdas del AOI en `activity_grid`; (b) un AOI sin fuego devuelve ceros, no filas faltantes; (c) un AOI en coordenadas negativas (México, Brasil) incluye las celdas de borde.

### I1b — `GET /medians` (primer entregable al seleccionar un AOI) ✅ implementado
- **Entrada:** `bbox` (lat_min, lat_max, lon_min, lon_max), `sensor_group` (default `VIIRS`), `baseline` opcional (default 2012–2024 para VIIRS).
- **Implementación:** `aoi_monthly_medians(...)` en `aoi_queries.py`. Devuelve 12 filas, una por mes del año: `month, median, p25, p75, mean, std, min, max, n_years, baseline_corto`.
- **Cómo se calcula:** para cada mes (p. ej. todos los noviembres 2012–2024) se suma `active_fire_days` de las celdas del AOI en cada año, con ceros incluidos y sin meses de hueco; la mediana y los cuartiles se calculan sobre esos años. `baseline_corto = true` si hay menos de 8 años.
- **Aceptación:** verificado ✅ contra cálculo de fuerza bruta (12 meses, 0 fallos, en muestra); un AOI sin fuego devuelve medianas 0.
- **Alcance actual:** solo este endpoint y `/calendar`. La comparación del mes en curso (I4) y el timeline diario (I3) quedan en pausa; el mes en curso, cuando se retome, se resolverá con datos mensuales (proyección del total parcial) y no con datos diarios.

### I2 — `GET /points` y `GET /points.csv` (mapa y descarga)
- **Entrada:** `bbox`, `start`, `end`, filtros opcionales `frp_comparable`, `exclude_persistent`, `sensor_group`, `satellite`.
- **Implementación:** consulta DuckDB (o polars lazy) sobre `hotspots_harmonized.parquet` filtrando `latitude`, `longitude`, `acq_date_d` y los interruptores. El CSV exporta todas las columnas del esquema.
- **Mapa:** si el resultado excede un tope (p. ej. 50 000 puntos), devolver agregación por celda 0.1° (de `activity_daily`) y dejar los puntos para zoom cercano; el CSV siempre es completo. 🔶
- **Aceptación:** el conteo del CSV coincide con el del mapa sin tope; `is_persistent=True` desaparece cuando el interruptor está activo.

### I3 — `GET /timeline/daily`
- **Implementación:** `aoi_daily(bbox_latlon, start, end, sensor_group)` → `date, cells_active, n_hotspots, frp_sum`.
- **Reglas:** una línea por `sensor_group`; no se calcula z diario (demasiado ruidoso); usar `cells_active` y `frp_sum` como series principales.
- **Aceptación:** `sum(cells_active)` de un mes = `afd` de ese mes en `/calendar` (misma métrica).

### I4 — `GET /current-vs-median` (el flujo crítico del demo)
Pasos exactos que debe ejecutar el backend:

1. **Definir `as_of`:** última fecha completa = ayer UTC. 🔶 (NRT tiene latencia de hasta ~3 h ✅ según la FAQ de FIRMS, por eso no se usa el día en curso). Se compara el mes de `as_of`, del día 1 a `as_of.day`.
2. **Plan de requests:** `nrt_request_plan(bbox_lonlat, primer_día_del_mes, as_of)` → una request por fuente y ventana de ≤5 días. Fuentes: `VIIRS_NOAA20_NRT` y `VIIRS_NOAA21_NRT`. S-NPP no se pide porque dejó de publicarse el 2-nov-2026 ✅. Formato de ruta ✅: `/api/area/csv/{MAP_KEY}/{SOURCE}/{w,s,e,n}/{1-5}/{fecha}`. ❓ Confirmar con la primera llamada real el formato exacto de `{fecha}` (el plan usa `YYYY-MM-DD`).
3. **Ejecutar con cuidado:** límite de 5 000 transacciones por 10 min por llave ✅. Reintentos con espera, caché por (AOI, `as_of`) de unos minutos, y respaldo con snapshot si falla. Las respuestas de error de la API pueden venir como texto, no como CSV: validar columnas antes de parsear. 🔶
4. **Normalizar:** `normalize_nrt(df)` aplica las mismas reglas del pipeline: quita duplicados, `confidence` l/n/h → low/nominal/high y descarta low, calcula `cy, cx` con `floor(valor/0.1)`, marca `is_persistent` con `persistent_mask.parquet`, calcula `frp_comparable`, `sensor_group="VIIRS"`. NRT no trae `type` ✅, por eso el pipeline no depende de `type`.
5. **Comparar:** `aoi_mtd_compare(bbox_latlon, nrt_norm, as_of)`: cuenta celda-días del mes actual en el AOI y los compara con la distribución de los **mismos días del mes** en cada año válido del baseline VIIRS (2012–2024). Así se evita comparar un mes incompleto contra meses completos.
6. **Responder:**
```json
{"as_of": "2026-11-13", "month": 11, "days_covered": 13, "afd_mtd": 43,
 "median": 55.0, "p25": 40.0, "p75": 70.0, "min": 18, "max": 120, "ratio_to_median": 0.78,
 "pctl": 0.31, "z": -0.45, "n_years_baseline": 13, "status": "ok",
 "preliminary": true, "baseline": "VIIRS 2012-2024", "sources": ["VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"]}
```
`status` puede ser `ok`, `baseline_corto` (<8 años) o `sin_baseline`. Estructura probada ✅ con muestra (resultado idéntico a cálculo de fuerza bruta).
- **Aceptación:** con un mes pasado descargado de la API y `as_of` dentro de ese mes, `afd_mtd` coincide con lo que da el histórico para ese mismo tramo (prueba de consistencia NRT vs archivo). ❓ Aún no probado con la API real.

**Riesgos de este flujo 🔶 (hipótesis a validar, no hechos):**
- **NRT vs SP:** NRT es preliminar, con geolocalización que puede degradarse y sin el filtro de calidad de SP ✅ (FIRMS FAQ). Validar comparando un mes reciente en NRT y en SP.
- **Composición de plataformas:** el baseline VIIRS contiene S-NPP (2012–2024) y NOAA-20 (2018–2024); el mes actual usa NOAA-20 + NOAA-21. Como la métrica es días-con-fuego (robusta a la cantidad de pasadas), el efecto debería ser pequeño; se valida con el solape.
- **Valor de `satellite` de NOAA-21** ❓ en las respuestas de la API: confirmarlo, solo se usa como metadato.
- **Tamaño del AOI:** ❓ no se verificó un límite de área de la Area API; para AOI muy grandes conviene partir por mosaicos.

### I5 — 2026 desde la API (calendario hasta "hoy")
El archivo por país llega hasta 2025 y **2026 no está publicado** ✅ (`notas_fuentes_datos_firms.md`). El calendario 2000–hoy necesita los meses de 2026 desde la Area API.
- **Opciones:** (1) construir los meses cerrados de 2026 una sola vez con `*_SP` si ya existe, si no `*_NRT`, y guardarlos como una tabla más con `version` marcada; (2) consultar la API en cada petición (lento y gasta cuota). Recomendada: opción 1, con tarea periódica que agrega cada mes cerrado. 🔶
- ❓ Verificar con el endpoint `/api/data_availability/` hasta qué fecha hay SP por fuente.
- **Aceptación:** `/calendar` muestra los meses de 2026 con `version` visible y `preliminary` cuando venga de NRT.

### I6 — `GET /meta/gaps`
Devolver `gaps.csv` para pintar "sin datos" en calendario y timeline. Ya listados: pérdida de Svalbard de Aqua (marzo 2024), standby de Terra (marzo 2026), anomalías de S-NPP 2026 y su cese definitivo ✅ según las fuentes de `notas_fuentes_datos_firms.md`. ❓ Confirmar si el hueco de S-NPP de mayo–julio 2026 existe en FIRMS (Copernicus lo reporta para sus productos).

### I7 — Evidencia para jueces
Script (no endpoint) que, para 2–3 AOI, grafica 2012–2024: conteos crudos MODIS vs VIIRS (separados 5–9×) arriba y `z` de ambos abajo (superpuestos), más la línea `[solape 2012-2024]` de `build_training_dataset.py`. Es lo que justifica la armonización.

## 3. Pruebas mínimas por función
- **Contra fuerza bruta:** recalcular a mano desde `activity_grid`/`activity_daily` en 2–3 AOI y comparar. Ya hecho en muestra para climatología (300 celdas), `aoi_mtd_compare` y `aoi_daily`.
- **Coordenadas negativas:** AOI en México (lon negativa) y Brasil/Australia (lat negativa).
- **AOI vacío:** debe devolver ceros y `status` coherente, nunca error.
- **Mes de hueco** (p. ej. abr-2022 MODIS): `valid=False`, `z` nulo.

## 4. Decisiones abiertas (tuyas)
1. **Línea base común 2012–2024** para MODIS y VIIRS en el calendario largo (recomendada; evita un escalón en 2012 si hay tendencia).
2. **Predictor con NOAA-20 solo:** requiere variante desde `hotspots_harmonized` y bajar el mínimo de años del z.
3. **Cómo tratar AOI que cruzan fronteras:** las sumas entre países asumen que no hay hotspots duplicados entre archivos de países vecinos ❓ sin verificar.
4. **Tope de puntos del mapa** y estrategia de agregación al alejar el zoom.
