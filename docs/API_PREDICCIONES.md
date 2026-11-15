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
