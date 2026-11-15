> Snapshot histórico (14-nov-2026, noche), conservado como contexto. La documentación vigente del repo es `../README.md`, `GUIA_DATASETS.md` e `IMPLEMENTACION_API.md`; si algo difiere, mandan esos documentos y el código. Los `claude/*.md` citados abajo son notas externas al repo.

# Resumen de estado para relevo de sesión — 14-nov-2026

[ARMONIZACIÓN][DATOS][BACKEND/FRONTEND] Resume lo decidido, lo verificado, lo construido y lo pendiente hasta el 14-nov-2026 (noche). Está pensado para que otra sesión relea la estructura del proyecto y escriba documentación. Convención: ✅ verificado · 🔶 inferido/propuesto · ❓ por verificar. Los detalles viven en los docs del proyecto (sección 6).

## 1. Objetivo y alcance actual
NASA Space Apps, track "Burning Activity Calendar": app web que armoniza hotspots MODIS (1 km, 2000–hoy) y VIIRS (375 m, 2012–hoy) de FIRMS en una serie consistente. El usuario elige un AOI y fechas y obtiene calendario de actividad, comparación contra la historia, mapa de puntos y descarga CSV. Hackathon: valor de demo > perfección.

**Alcance de la API en este momento:** `/calendar` (serie mensual del AOI con anomalía) y `/medians` (12 medianas mensuales históricas del AOI). El mes en curso, el timeline diario y la comparación "mes a la fecha" están en pausa. Un compañero construye un predictor aparte.

## 2. Decisiones tomadas
1. **Método D + G.** No se armoniza el *número* de fuegos; se armoniza la *señal de anomalía*: métrica = **días-con-fuego por celda de 0.1° y mes**, y anomalía (z/percentil) contra la climatología del propio sensor. (`armonizacion_resumen_decision.md`, `investigacion_armonizacion.md`)
2. **Dos capas:** puntos (`hotspots_harmonized`, esquema único, sin fusionar 1 km con 375 m) y actividad (`activity_grid`, celda×mes×sensor×país).
3. **Filtros:** `confidence` nominal + high (se descarta low); fuentes persistentes por recurrencia de celda 0.01° (≥60 meses distintos), no por `type`.
4. **La anomalía de un AOI se calcula a nivel AOI** (sumar celdas, luego estadística sobre esa serie); nunca promediando z de celdas.
5. **Comparación con medianas: VIIRS contra VIIRS** (baseline 2012–2024). MODIS solo para el histórico largo.
6. **Ceros explícitos:** un mes válido sin fuego vale 0; un mes sin datos del sensor es "sin datos".
7. El mes en curso, cuando se retome, se tratará con datos mensuales (proyección del total parcial, marcada como estimación) y no con datos diarios. 🔶 propuesto, el usuario no confirmó la opción.

## 3. Hallazgos verificados
**Productos FIRMS** (fuentes en `notas_fuentes_datos_firms.md` y `descarga_por_pais_firms.md`) ✅
- Cobertura: MODIS 1-nov-2000; S-NPP 20-ene-2012; NOAA-20 1-abr-2018; NOAA-21 17-ene-2024.
- Archivo por país (sin llave) cubre hasta 2025; **2026 no está publicado**, debe venir de la Area API.
- Area API: requiere MAP_KEY, 1–5 días por consulta, 5 000 transacciones por 10 min; fuentes `VIIRS_NOAA20_NRT/SP`, `VIIRS_NOAA21_NRT/SP`, etc.
- NRT es preliminar y no trae `type`; la FAQ recomienda SP para tendencias.
- S-NPP dejó de publicarse el 2-nov-2026; NOAA-20/21 son su reemplazo directo.
- Carpeta de NOAA-20 en el archivo por país: `viirs-jpss1`.

**EDA de 6 países** (`eda_seis_paises_resultados.md`) ✅: la razón de conteos Aqua/S-NPP es 0.11–0.21 (estable pero específica por país); la de FRP es 0.57–0.76; S-NPP ≈ NOAA-20 (razón 1.01); huecos de datos sesgan las razones y se excluyen al calibrar.

**Literatura** (`investigacion_armonizacion.md`) ✅: la armonización por anomalía/percentil es práctica operativa (GFED5NRT, EFFIS/GWIS); no se encontró una serie de *conteos* ya armonizada publicada; una referencia (Franquesa 2025) descarta la normalización por cuantiles para armonizar.

**Pruebas de esta sesión (solo con muestras de México y Brasil, escasas)** ✅
- Spearman MODIS↔VIIRS en el solape de la muestra = 0.978; factores por país en muestra: afd ≈ 2.4–2.6, conteo ≈ 3.8–3.9, FRP ≈ 0.84–0.87.
- `satellite` en la muestra: `Terra`, `Aqua`, `N` (S-NPP), `N20`. `N21` sin confirmar. NOAA-20 empieza el 2018-04-01 en la muestra.
- Se encontraron y corrigieron dos errores: (a) la climatología y `aoi_calendar` no incluían ceros, lo que inflaba medias; (b) `aoi_calendar` usaba `int()` para ubicar celdas, que falla con coordenadas negativas (ahora `floor`).
- Verificado contra cálculo manual: climatología (300 celdas, 0 fallos), `aoi_monthly_medians` (12 meses, 0 fallos), `aoi_daily` y `aoi_mtd_compare`.

## 4. Hipótesis por probar ❓🔶
- Que las anomalías MODIS y VIIRS coincidan en 2012–2024 (correlación alta, media de z ≈ 0) y que no haya escalón en 2012: se prueba con la línea `[solape 2012-2024]` de `build_training_dataset.py` sobre datos completos. **No se ha visto.**
- Que usar baselines distintos (MODIS 2001–2024, VIIRS 2012–2024) no genere un escalón; la alternativa recomendada es una línea base común 2012–2024.
- Que NRT y SP den métricas comparables (NOAA-21 en el mes actual vs S-NPP+NOAA-20 en la historia).
- Que no haya hotspots duplicados entre archivos de países vecinos.
- Formato de `{fecha}` de la Area API y valor de `satellite` para NOAA-21: confirmar con una llamada real.

## 5. Estado en disco (carpeta `Data/` del repo)
- Crudos: `csv\`, `parquet\{modis,viirs-snpp,viirs-jpss1}\{año}\{País}.parquet` (6 países: Angola, Australia, Brasil, RD Congo, México, Rusia), `descarga\`, `analisis\`.
- Todo lo armonizado vive en `armonizacion\`:
  - `harmonize_firms.py`: genera `hotspots_harmonized`, `activity_grid`, `cell_climatology`, `scaling_factors`, `persistent_mask`, `gaps.csv`, `validation_report.csv`, README; define `aoi_calendar`.
  - `aoi_queries.py`: `aoi_monthly_medians`, `aoi_daily`, `aoi_mtd_baseline`, `aoi_mtd_compare`, `nrt_request_plan`, `normalize_nrt`; comandos `build-daily` y `rebuild-climatology`.
  - `build_training_dataset.py`: genera `training_dataset.parquet/.csv` (celda×mes con ceros, serie MODIS→VIIRS, target `afd_z`).
  - `docs\`: `GUIA_DATASETS.md`, `IMPLEMENTACION_API.md`, este resumen.
- El usuario corrió `harmonize_firms.py` (generó parquet); **no se ha confirmado el resultado completo del run de los 6 países.** Aún no ha corrido `rebuild-climatology` ni `build_training_dataset.py`.

## 6. Documentos del proyecto (`claude/`)
| Doc | Contenido | Estado |
|---|---|---|
| `investigacion_armonizacion.md` | Métodos A–G, ranking, recomendación D+G, validación | vigente |
| `armonizacion_resumen_decision.md` | Qué/por qué/defensa, frase para jueces | vigente |
| `armonizacion_pipeline.md` | Pasos y script del pipeline | **desactualizado** (ver sección 7) |
| `guia_datasets_armonizados.md` | Estructura y uso de cada tabla y función | vigente |
| `implementacion_api_funciones.md` | Plan iterativo de la API (I0–I7) | vigente |
| `eda_seis_paises_resultados.md`, `descarga_por_pais_firms.md`, `notas_fuentes_datos_firms.md` | EDA, descarga, hechos de FIRMS | vigentes |

El **doc de estado** (https://claude.ai/artifact/4d72MNfTrdYip7AwYqzGHj) se actualizó antes de las correcciones con ceros y del alcance actual de la API; **no refleja** lo de esta sesión.

## 7. Inconsistencias que la documentación debe corregir
1. `armonizacion_pipeline.md` describe un script anterior: lee CSV, escribe en `Data\harmonizado\`, climatología sin ceros y sin `country`, `aoi_calendar` con `int()`. Lo vigente es lo de la sección 5 (`Data\armonizacion\`, entrada en parquet).
2. Esquema de `cell_climatology`: ahora clave `cy, cx, country, month, sensor_group`, con `n_years` y `n_years_fire`.
3. La copia vieja `Data\harmonize_firms.py` (raíz de `Data`) debe borrarla el usuario; no hay shell en su máquina.
4. El doc de estado debe registrar: hallazgo de sesgo por falta de ceros (corregido), alcance actual de la API, decisiones de la sección 2 y los pendientes de la sección 8.

## 8. Pendientes y decisiones abiertas (del usuario)
- Correr en su máquina: `rebuild-climatology`, `build_training_dataset.py`, y compartir la línea `[solape 2012-2024]`.
- Decidir línea base común 2012–2024; decidir si el mes en curso se resuelve con proyección mensual.
- Predictor del compañero: propuesta de NOAA-20 solo (historia ≈ 2018–hoy, mínimo de años del z más bajo); requiere una variante desde `hotspots_harmonized`.
- Traer 2026 desde la Area API (calendario hasta "hoy"); verificar con `/api/data_availability/` hasta cuándo hay SP.
- Backend de puntos y CSV (DuckDB propuesto), con tope de puntos para el mapa.
- Figura de evidencia para jueces (conteos crudos separados vs z coincidiendo).
- Tareas fuera de alcance que siguen sin hacerse: pitch, frontend, rampas de color accesibles.

## 9. Notas para quien escriba la documentación
- No afirmar que la armonización está *validada*: solo hay pruebas en muestra escasa; el diagnóstico decisivo no se ha ejecutado con datos completos.
- Distinguir siempre "esquema común" (capa de puntos) de "armonización de señal" (capa de actividad y anomalía).
- Las medianas y anomalías son de **días-con-fuego**, no de conteos de hotspots.
- El AOI se ajusta a celdas de 0.1° (aproximación por bbox) y esto debe indicarse en la UI.
- Idioma: español, con términos técnicos estándar en inglés (hotspot, FRP, confidence, NRT, SP).
