# API de predicciones — guía para el frontend

> **Qué predice:** la probabilidad (0–1) de que una **zona de 0.5° (~55 km)** de la Península de Yucatán tenga actividad **anómala** de puntos de calor en una semana: días con fuego por encima del **p90 histórico de esa zona en esas fechas**. *Un punto de calor no es un incendio.*
> Método y validación: `prediccion/README.md`. Swagger: **http://127.0.0.1:5000/apidocs** (tag *Predictions*).

## Endpoints (base `VITE_API_BASE_URL` = `/api`)
Todos aceptan un `bbox` opcional: `lat_min, lat_max, lon_min, lon_max` (mismo formato que `/fires/*`).

| Endpoint | Para qué usarlo | Respuesta |
|---|---|---|
| `GET /predictions` | Mapa "en vivo" | `{generado_utc, datos_hasta, aviso, fuentes, semana_en_curso, semana_proxima}`. Cada semana es un **GeoJSON FeatureCollection** + `resumen` + `semana` + `horizonte_semanas` (1 o 2) |
| `GET /predictions/week/YYYY-MM-DD` | Mapa de una semana (lunes) de la línea del tiempo, 2008–2026 | FeatureCollection + `resumen {zonas, prob_max, zonas_alto}` + `fuente` (`historico_walk_forward` / `vivo`) |
| `GET /predictions/weeks` | Saber qué semanas existen | `{historico: [...], vivo_2026: [...]}` |
| `GET /predictions/series?bbox&start&end` | **Dashboard del área seleccionada**: serie semanal | `{zonas: [ids], data: [{semana, fuente, zonas, prob_max, prob_media, zonas_alto, valor, p90, anomalias}]}` |
| `GET /predictions/validation` | Panel "¿qué tan confiable es?" | `resumen_h1/h2`, `metricas_por_anio`, `calibracion`, `wilcoxon_clima`, `falsas_anomalias`, `temporada_2026_vivo` |

**Propiedades de cada zona (feature):**

| Campo | Significado |
|---|---|
| `zona_id` | Id de la zona. `lat_min = 17.8 + floor(id/100)*0.5`, `lon_min = -92.5 + (id%100)*0.5` |
| `prob` | Probabilidad de anomalía (0–1) |
| `nivel` | `bajo` (<10 %), `moderado` (10–30 %) o `alto` (≥30 %) |
| `base` | Frecuencia histórica de anomalías: lo que diría "la climatología". Útil para mostrar "modelo vs. normal" |
| `p50`, `p90` | Días con fuego típicos y "altos" para esa zona y fechas |
| `valor` | Días con fuego observados (`null` si la semana aún no se observa) |
| `anomalia` | 1/0 si se observó anomalía (`null` si aún no) |

## Qué ya está listo en el frontend (sin conectar a `MapView`)
- `features/map/predictions.ts`: tipos (`ZoneCollection`, `CurrentForecast`, `ForecastSeries`…) y funciones `getCurrentForecast(signal, bbox?)`, `getWeekForecast(week, signal, bbox?)`, `getForecastSeries(bbox, signal, start?, end?)`, `getForecastValidation(signal)`, `mondayOf(date)`, `LEVELS` (colores) y `PENINSULA` (bounds). Si la API no responde, `getCurrent/getWeek` leen el respaldo estático de `public/prediccion/`.
- `features/map/predictionLayer.ts`: `addPredictionLayers(map)`, `setPredictionData(map, data)` y `setPredictionVisible(map, bool)`. Capa de relleno por probabilidad, borde blanco en las anomalías observadas y popup.
- `features/map/usePrediction.ts` + `PredictionPanel.tsx`: hook y panel de ejemplo (Timeline / This wk / Next wk / Off, leyenda).

**Conectar la capa en `MapView` (3 líneas):**
```ts
import { addPredictionLayers, setPredictionData } from './predictionLayer'
map.on('load', () => { /* … */ addPredictionLayers(map, { popup: !picking }) })
useEffect(() => { if (mapRef.current?.isStyleLoaded()) setPredictionData(mapRef.current, prediction) }, [prediction])
```

## Ideas de dashboard al seleccionar una región (`region: Bbox`)
1. **KPIs:** probabilidad máxima de la semana en curso y de la próxima (`getCurrentForecast(signal, region)` → `semana_en_curso.resumen.prob_max`), y número de zonas en riesgo alto.
2. **Serie temporal** (`getForecastSeries(region, signal, '2024-01-01')`): línea de `prob_max` con marcas donde `anomalias > 0`, y barras de `valor` contra la línea `p90`. Muestra cómo el modelo anticipa la temporada (marzo–mayo).
3. **"Modelo vs. normal":** `prob_media` contra el promedio de `base`.
4. **Confiabilidad** (`/predictions/validation`): AUC 0.85 contra 0.59 de la climatología; temporada 2026 en vivo con AUC 0.86 contra 0.61; tabla de calibración ("cuando dice 40 %, ocurre ~36 %").
5. **Etiquetas honestas:** "Hotspot ≠ incendio" y "Probabilidades altas (>50 %) son optimistas: mostrarlas como *riesgo alto*".

## Actualizar los datos
```powershell
cd backend; .venv\Scripts\Activate.ps1
$env:MODVIIRS_FIRMS_MAP_KEY = "<MAP_KEY>"     # nunca en git
flask --app wsgi prediction-update            # FIRMS NOAA-20 2026 + NASA POWER → cache (~1–2 min)
flask --app wsgi prediction-snapshot          # respaldo estático en frontend/public/prediccion
```

---

## Modelo de 6 países (zonas de 1°) — `predictivo`, 15-nov

Cobertura: **México, Brasil, Rusia, Australia, Angola y RD del Congo** (los países de la armonización de Alexis).
Fuente: `backend/data/activity_daily.parquet` (VIIRS armonizado, sin fuentes persistentes), zonas de 1° (~110 km),
eras S-NPP (2012-01 → 2018-03) y S-NPP+NOAA-20 (2018-04 →), **con clima NASA POWER por zona** (AUC 0.839 vs 0.833 sin clima; mejor en 18/18 pares país-año, Wilcoxon p = 0.0002). Predicción walk-forward 2023–2025 (H1 y H2).
La península conserva su modelo propio (0.5°, clima NASA POWER, en vivo 2026).

| Endpoint | Qué devuelve |
|---|---|
| `GET /api/predictions/series?lat_min&lat_max&lon_min&lon_max[&escala=auto\|peninsula\|global]` | Serie semanal. `auto`: península si ≥50 % del bbox cae en ella; si no, modelo de 6 países. Campos nuevos: `escala`, `tam_zona_grados`, `paises`, y por semana `esperadas` (Σ probabilidades = zonas anómalas esperadas) y `p50` (actividad típica). |
| `GET /api/predictions/global/countries` | Países, nº de zonas, bbox `{west,south,east,north}` y AUC/AP vs línea base. |
| `GET /api/predictions/global/week/<lunes>?horizonte=1\|2&bbox` | GeoJSON de zonas de 1° (props: `zona_id, pais, prob, nivel, base, p50, p90, valor, anomalia`) + `resumen {zonas, prob_max, zonas_alto, esperadas}`. |
| `GET /api/predictions/global/validation` | Métricas por país y año. |

Cliente TS: `getGlobalCountries`, `getGlobalWeekForecast` en `frontend/src/features/map/predictions.ts`.

**Cómo leer el dashboard** (`ForecastDashboard.tsx`):
- *Peak zone risk* = probabilidad de la zona más riesgosa de la región (no es "probabilidad de la región"; crece con el tamaño de la región).
- *Zones forecast to break their seasonal record* = Σp (esperadas). *Zones that actually did* = anomalías observadas.
- *Fire activity vs. a typical week* = días-fuego observados / Σp50.
- Banda azul = rango normal (Σp50 → Σp90). Morado = zonas anómalas esperadas; puntos rojos = observadas.
- *Proven accuracy x/10* = AUC×10 (península: temporada en vivo 2026; 6 países: replay 2023–2025, ponderado por zonas).

Regenerar: `python prediccion/src/p06_global_actividad.py`, luego `p07_global_modelo.py tabla <pais> [parte]` por país
(Rusia en partes 0 y 1), `fit <h> <anio>` (h=1: 2023–2025; h=2: 2024–2025) y `final`.
Variante con clima: `python prediccion/src/p08_power_global.py` (en una PC con acceso a NASA POWER) y lo mismo con `CLIMA=1`.

---

## Integración en el panel de Castillo (15-nov, después del merge de `main`)

- `AnalysisPanel.tsx` ahora tiene dos pestañas: **HISTÓRICO** (sus tarjetas, sin cambios) y **PRONÓSTICO ✦**, que monta
  `<ForecastDashboard region={region} date={addDays(start, stepFrom)} embedded />` (semana del cursor del timeline).
- Para moverlo a otro lugar basta con montar el componente donde se quiera:
  - `embedded` → se adapta al ancho del contenedor (panel de 380 px).
  - sin `embedded` + `onClose` → tarjeta flotante sobre el mapa.
- Estilos del pronóstico en `frontend/src/features/map/forecast.css` (importado por el componente; `map.css` queda como en `main`).
- Textos en español. El componente elige solo el modelo según la región (península 0.5° en vivo / 6 países 1° 2023–2025)
  y, si la semana del timeline no tiene pronóstico, usa la más cercana y lo indica.
- Si se quieren usar los números en sus propias tarjetas: `getForecastSeries(region, signal)` devuelve por semana
  `prob_max`, `esperadas`, `anomalias`, `valor`, `p50`, `p90`, `zonas_alto` (ver tabla arriba).
