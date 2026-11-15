# Armonización MODIS–VIIRS: qué se va a hacer y por qué (resumen y defensa) — 14-nov-2026

[ARMONIZACIÓN][PITCH] Documento de decisión. El detalle metodológico y el ranking están en `investigacion_armonizacion.md` (notas del proyecto, fuera del repo); el pipeline técnico en `../README.md`.

## Qué se va a hacer (en una frase)
Convertir los CSV crudos de hotspots de FIRMS (MODIS 2000–hoy + los tres VIIRS) en **un dataset armonizado de dos capas**: una **capa de puntos** (todas las detecciones con un esquema único, para el mapa y la descarga CSV) y una **capa de actividad** (los mismos focos contados por celda de rejilla y mes, expresados como **anomalía respecto a lo normal de cada zona**, para el calendario y los modelos).

## La decisión
- **Métrica primaria = días-con-fuego por celda** (nº de días del mes con ≥1 detección), no el conteo bruto de hotspots.
- **Armonización del calendario = anomalía normalizada por sensor** (percentil / z-score contra la climatología del propio sensor): método **D + G** del ranking.
- **Capa de magnitud opcional = factor por país/bioma** (método A) para quien quiera ver "unidades VIIRS-equivalentes", con el **umbral FRP ~13–20 MW** (método B) como validación cruzada.
- **Capa de puntos = esquema unificado + regla de `confidence` n+h + filtro de fuentes persistentes + marca de sensor**; no se fusionan las geometrías 1 km y 375 m.

## Por qué (el fundamento)
MODIS (1 km) y VIIRS (375 m) **no son intercambiables**: VIIRS detecta 5–9× más hotspots porque resuelve fuegos pequeños y fríos que MODIS no ve. Pegar los conteos crudos haría que 2012 (entrada de VIIRS) pareciera una explosión de fuego 5–9× que es puro artefacto del sensor. Dos hechos del EDA deciden el método:

1. **La diferencia vive en los fuegos pequeños.** La razón de *conteos* Aqua/S-NPP es 0.11–0.21, pero la de *FRP* (energía) es 0.57–0.76 (mucho más cerca de 1). El conteo crudo es la peor variable para armonizar; las variables robustas (días-con-fuego, FRP) son estables entre sensores.
2. **El objetivo es anomalía, no magnitud absoluta.** "¿Este mes está inusualmente alto para esta zona?" se responde comparando cada sensor contra *su propio* normal. Eso **cancela el salto 5–9× por construcción**, sin inventar un factor de conversión imposible de validar antes de 2012 (donde solo hay MODIS).

Por eso la armonización "fuerte" vive en la capa de actividad (D agrega y borra el sobre-conteo de 375 m; G borra el salto de magnitud), y los puntos se quedan a nivel de detección con esquema común: fusionar 1 km con 375 m sería deshonesto.

## Cómo empata con el proyecto general
El reto tiene dos partes y esta decisión sirve a ambas:
- **Parte 1 (armonización, "el sensor de origen deja de importar"):** se cumple literalmente en la capa de actividad — el calendario lee anomalía, no número crudo, así que 2000–hoy se ve en una sola escala sin salto en 2012.
- **Parte 2 (app web):** encaja directo con tu frontend. Selección de AOI → la capa de actividad (precalculada) alimenta el **calendario** y la **comparación mes actual (API NRT) vs mediana histórica (SP)**; la capa de puntos alimenta el **mapa de hotspots** y la **descarga CSV**. Y como subproducto, ambas capas sirven para **entrenar modelos** (actividad/anomalía por zona; eventos a nivel de punto).

## Por qué es defendible
- **Precedente operativo:** reportar la actividad como z-score/percentil contra una climatología es exactamente lo que hacen **GFED5NRT** (NASA/VU, Chen et al. 2026) y **EFFIS/GWIS** (Copernicus). No es un invento del equipo.
- **Figura que gana el pitch:** en el solape 2012–2024, la anomalía mensual de un AOI calculada por separado con MODIS y con VIIRS **coincide** (correlación de rangos alta, sesgo ≈ 0) aunque los conteos crudos difieran 5–9×. Un solo gráfico justifica unir las series.
- **Control positivo:** S-NPP ≈ NOAA-20 (razón 1.01 en el EDA); el método debe dar ≈identidad entre los gemelos → prueba de que no mete artefactos.
- **Rigor visible:** se distingue "sin datos" de "cero fuego" (huecos marcados), se filtran fuentes persistentes (gas flares, industria) con un criterio común a ambos sensores, y el mes actual (NRT) se marca como preliminar.
- **Honestidad sobre el alcance:** la literatura **no publica una serie de conteos ya armonizada** (se verificó); el enfoque es una contribución genuina, y se nombra su simplificación (los conteos dependen de detectabilidad; FRP y burned area son físicamente más conservadores).

## La frase para los jueces
> "No armonizamos el *número* de fuegos, que depende del sensor; armonizamos la *señal de anomalía*, que es lo que importa para detectar meses y años excepcionales — el mismo espacio que usan GFED5NRT y EFFIS."
