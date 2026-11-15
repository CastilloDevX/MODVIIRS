# Historial de cambios

La versión global vive en [VERSION](VERSION). Seguir la [política de versionado y commits](docs/CONTRIBUTING.md). Las entradas sin publicar no implican una release, tag, commit ni push realizados.

## Sin publicar

### Backend

- `queries.py`: si `activity_daily.parquet` / `activity_grid.parquet` son punteros de Git LFS (sin `git lfs pull`), se regeneran desde `hotspots_harmonized.parquet` en `backend/data/.derived/` (ignorado por Git, un parquet por año y sensor, unos 45 s la primera vez). Corrige los errores 500 de `/fires/timeline`, `/calendar` y `/medians`.
- `/fires/points.csv`: se genera en streaming a un archivo temporal (no en memoria) y ya no incluye la columna `sensor_group` (MODIS/VIIRS).
- `aoi_calendar` ahora lee la actividad de forma perezosa (antes cargaba el parquet entero en memoria).

### Frontend

- La página principal es ahora `/`; la ruta `/map` ya no existe (da 404). Se retiró el «Hola mundo».
- Calendario principal: cada día con hotspots se pinta amarillo, naranja o rojo según su intensidad (conteo diario en escala log frente al día pico de la región; 0–0.4, 0.4–0.7, 0.7–1), con leyenda. Inicio y fin del rango llevan borde blanco.
- Botón blanco «Export CSV» en la barra izquierda: descarga las detecciones de la región para el rango de fechas completo seleccionado.
- `/map`: el botón Region va arriba del todo; calendario, fechas, pasos y línea de tiempo aparecen solo cuando hay una región. Se quitó el selector Imagery (solo el dataset diurno de la Tierra).
- Escala de pasos (Días, Semanas, Meses, Años) junto a los botones 3D/2D; el campo Steps indica cuántas unidades. La línea de tiempo salta entre inicios de paso y los hotspots (`/api/fires/points`) mostrados son los del paso actual.
- Autozoom: al fijar la región la cámara vuela hasta ella y la encuadra. Pulsar Select o borrar la región nunca mueve la cámara.
- Por defecto: rango 1/dic/2012 – 31/dic/2025 y escala de meses; se quitó el campo Steps (cada paso es 1 unidad de la escala).
- Coordenadas (latitud/longitud) del puntero en la esquina inferior derecha del mapa.
- Filtros de hotspots (esquina superior izquierda del mapa): intensidad normalizada 0–1 (FRP en escala logarítmica, tope 500 MW) en tres fases: amarillos 0–0.4, naranjas 0.4–0.7, rojos 0.7–1, con contador y activables por fase.
- Texto bajo los botones 3D/2D y Días/Semanas/Meses/Años explicando su función, con separación visible entre ambos grupos.
- Tipografía: Orbitron solo en el título de página; paneles, títulos y números usan Prompt.
- Panel de análisis a la derecha (aparece con animación al fijar la región; se oculta/reabre): resumen del rango (hotspots, días con fuego, día pico, media diaria, FRP total, celdas activas), series diarias de hotspots y FRP, estadísticas del paso actual (FRP media/mediana/P90/máx./suma, % confianza alta, persistentes, FRP ≥ 15 MW), histograma de FRP, día/noche, confianza, satélites, calendario mensual de anomalías (z-score) y estacionalidad típica. Selector de sensor VIIRS/MODIS para serie, calendario y estacionalidad.
- Línea de tiempo: al pasar el mouse aparece un polígono de hotspots por día a todo lo ancho, con el pico marcado y el día bajo el cursor.
- Fechas seleccionables limitadas a la cobertura del dataset de hotspots: 2000-11-01 a 2025-12-31.
- Selección de región (campo «Region» sobre «Imagery»): el botón Select oscurece el planeta; un clic/toque fija la primera esquina y otro la opuesta. Entre ambos, el rectángulo se ilumina y sigue al cursor; el resto queda oscuro. Mover el mapa con arrastre no cuenta como clic. Esc o Cancel cancelan; × borra la región. Guarda el cuadro como norte/sur/este/oeste (no cruza el antimeridiano); aún no muestra focos.
- Selección de países (polígonos Natural Earth 1:50m, `frontend/public/data/countries.geojson`) queda aparcada tras `COUNTRY_SELECTION = false` en `countries.ts`.

## 0.2.0 — 2026-11-14

### Frontend

- Ruta `/map`: barra lateral con calendario de rango y campos Start/Final date (cada uno abre un calendario emergente), mapa de la Tierra con zoom continuo, panel derecho «Steps» y línea de tiempo arrastrable dividida por días. Es solo interfaz; no hay datos de focos FIRMS.
- Mapa: MapLibre GL con datos solo de NASA GIBS. «Sin nubes»: Blue Marble (nivel 8) y, al acercar, compuesto Landsat WELD 2000 a 30 m (nivel 12, el máximo de GIBS; más allá se amplía). «Oscuro»: VIIRS Black Marble (luces nocturnas 2016). Costas, límites y nombres `Reference_*` (nivel 9) que se desvanecen al acercar. Las capas son estáticas: el mapa no cambia con la fecha seleccionada.
- Calendarios (lateral y de cada fecha) con selectores de mes y año de shadcn; no se puede elegir antes del 1 de enero de 2000.
- Zoom: tope en el último nivel con detalle real (12 en «Sin nubes», 8 en «Oscuro») y rueda más rápida.
- Botones 3D/2D (esquina inferior izquierda del mapa): globo con atmósfera o mapa plano Mercator con norte arriba.
- Línea de tiempo: compacta, sin botón de reproducción; se arrastra (cursor de agarre) o con teclado y salta según los días por paso (campo único, 1 por defecto).
- Todos los controles (calendario, fechas, pasos, imagenología) están en la barra izquierda; no hay panel derecho.
- El logo de `/map` enlaza a `/` (landing).
- shadcn/ui (Tailwind v4, estilo base-nova) con `Calendar`, `Popover`, `ToggleGroup`, `Input`, `Label`, `Button`.
- Ruta `/`: solo «Hola mundo». Se retiró la pantalla de bienvenida conectada a la API (`lib/api.ts` y el backend se conservan).
- Favicon `icon.png`, logo, fuentes Orbitron (títulos) y Prompt (texto) autoalojadas con Fontsource.
- Dependencias nuevas: `react-router-dom`, `maplibre-gl`, `tailwindcss`, shadcn y sus dependencias, `@fontsource/orbitron`, `@fontsource/prompt`.

### Documentación y gobierno del proyecto

- Preservación íntegra del informe contextual MODIS/VIIRS como PDF y texto, con contexto consolidado y bibliografía.
- Registro de contraste con fuentes oficiales NASA, fallos de acceso y discrepancias de cobertura.
- Instrucciones para agentes en `AGENTS.md` y `.agents/`, con análisis crítico, consulta de decisiones y trazabilidad.
- Reglas de autorización para commits/push y mensajes `type: :gitmoji: description`, con descripción en inglés y guía publicada en `.github/CONTRIBUTING.md`.
- Incorporación de `VERSION` con base `0.1.0` y política X/Y/Z; sin incremento funcional ni publicación.

## 0.1.0 — Base existente, sin fecha de publicación registrada

- Monorepo Flask + React/TypeScript/Vite.
- API versionada de bienvenida y health, manejo de errores y frontend conectado.
- Pruebas backend, análisis estático, compilación frontend y configuración CI.

Esta sección describe el punto de partida previo a incorporar el contexto científico; no afirma que las capacidades MODIS/VIIRS estén implementadas ni que se haya publicado esta versión.
