# Historial de cambios

La versión global vive en [VERSION](VERSION). Seguir la [política de versionado y commits](docs/CONTRIBUTING.md). Las entradas sin publicar no implican una release, tag, commit ni push realizados.

## Sin publicar

### Backend

- Nuevo `GET /api/predictions/reliability`: precisión comprobada (AUC walk-forward, era VIIRS) por semana del año para las zonas del área.
- `/api/predictions/validation` y demás JSON de caché ya no devuelven `NaN` (no es JSON válido y el navegador no podía leerlo, por lo que faltaban las gráficas de calibración): se devuelve `null`.
- `queries.py`: si `activity_daily.parquet` / `activity_grid.parquet` son punteros de Git LFS (sin `git lfs pull`), se regeneran desde `hotspots_harmonized.parquet` en `backend/data/.derived/` (ignorado por Git, un parquet por año y sensor, unos 45 s la primera vez). Corrige los errores 500 de `/fires/timeline`, `/calendar` y `/medians`.
- `/fires/points.csv`: se genera en streaming a un archivo temporal (no en memoria) y ya no incluye la columna `sensor_group` (MODIS/VIIRS).
- `/fires/points.csv` ahora se envía en streaming mes a mes (sin archivo temporal): antes fallaba con `Disk quota exceeded` / 500 en regiones grandes y rangos largos.
- `aoi_calendar` ahora lee la actividad de forma perezosa (antes cargaba el parquet entero en memoria).

### Frontend

- La landing (`/landing`) está completamente en inglés (textos, botones, etiquetas accesibles, nombres de sección y ids de anclas) y `<html lang>` pasa a `en`. Las capturas de `public/images/features/` son imágenes de una versión anterior del visualizador y conservan algunas etiquetas en español (meses, días, «Sin nubes/Oscuro»).
- PREDICTIONS: la confiabilidad de cada día ahora depende de la época del año (precisión comprobada por semana del año, ventana de ±2 semanas) y de la distancia a la fecha establecida, por lo que aparecen días amarillos (abril–junio, cuando el modelo es menos preciso). Nuevas gráficas: confiabilidad a lo largo del año, pronóstico vs. realidad por año, error del modelo vs. error de la línea base, precisión del modelo vs. línea base por año y calibración. Se quitó la tarjeta «How far ahead can it be trusted?».
- La página `/` está completamente en inglés (menús, paneles, gráficos, calendarios y etiquetas); la landing no se tocó.
- Pestaña PREDICTIONS (antes FUTURE, antes PRONÓSTICO): solo futuro. El pronóstico empieza una semana después de la fecha establecida (la Final date) y cubre 2 semanas, el rango prometedor. El calendario solo carga esos meses, solo permite elegir fechas (sin selector de mes o año), abre con todo el periodo seleccionado desde el día 1 y muestra la confiabilidad en porcentaje. Se quitó el texto de ayuda bajo el calendario y las tarjetas que mostraban el pasado.
- La ruta `/map` se eliminó: la app vive solo en `/` (y `/landing`); los enlaces de la landing apuntan a `/`.
- PRONÓSTICO: primer widget «¿Qué tan confiable es la predicción?»: calendario con cada día predicho en verde (muy confiable, más de 75 %) o amarillo (a medias, más de 50 %); sin color si es menor o no hay predicción. Un toque elige un día y un segundo toque un periodo; muestra las fechas y el porcentaje de confiabilidad en grande. Confiabilidad = precisión comprobada (AUC) del modelo: por año en la Península de Yucatán, por país en el modelo de 6 países y por horizonte (1 sem. 85 %, 2 sem. 81 %) en las semanas futuras en vivo.
- Vista PRONÓSTICO rediseñada con los mismos patrones del histórico: tarjetas animadas, KPIs, gráficos con la misma paleta y tipografía Prompt. Nuevas tarjetas «¿Hasta cuándo es confiable?» (AUC y AP por horizonte de 1, 2 y 4 semanas frente a la línea base) y «Calibración».
- La sección de features de `/landing` presenta mapa interactivo, timeline de datos armonizados, análisis de picos y módulo de gráficas. Se añadieron capturas reales del mapa y del control temporal con datos de abril de 2024; las capturas de picos y gráficas se aplazan por indicación del usuario.
- Landing completa en inglés, incluidos navegación, textos alternativos, enlaces, metadatos y control de partículas. Se añade MagicBento con iluminación de borde, spotlight, onda de clic y entrada escalonada desde armonización, adaptable y con soporte de movimiento reducido, sin nuevas dependencias npm.
- Predicción de la landing: descripción breve del panel, aclaración de probabilidad máxima por zona y captura real de una reproducción histórica de México (semana del 22 de abril de 2024). Referencias investigadas de NASA Earthdata FIRMS, MODIS/VIIRS y sus guías, archivo, Area API, Fire Data Academy, POWER y GIBS, con reconocimiento de datos e imágenes. Se retiran los textos provisionales de esas secciones.
- La sección de features de `/landing` presenta mapa interactivo, timeline de datos armonizados, análisis de picos y módulo de gráficas. Tras integrar las actualizaciones del visualizador, se renovaron las capturas reales del mapa y de la timeline y se añadieron las de picos y análisis, todas con datos de Yucatán en abril de 2024. Los textos describen los filtros de intensidad y las escalas temporales disponibles; las cuatro imágenes incluyen texto alternativo, dimensiones y pie actualizados.
- Footer adaptable de la landing con MODVIIRS y marca Orbitron, equipo Astra 11 y NASA, renderizado desde el componente `LandingFooter`. Se reutilizan los logos editados de `frontend/public/images/`, con NASA transparente y Astra 11 recortado.
- Ruta `/landing` con logo, marca Orbitron y secciones Prompt de armonización, visualizador, predicción y bibliografía. Incluye enlaces a `/map`, contenido provisional centralizado y animaciones de entrada que respetan movimiento reducido. Fondo `@react-bits/Particles-JS-CSS` con los parámetros del usuario, control de pausa y tipos para TypeScript; no añade paquetes npm. La carga de la landing está separada de la del mapa.
- Los cuatro pasos de armonización de la landing resumen el informe aportado «Armonización MODIS–VIIRS: método, pipeline y uso de los datos»: seis países de estudio, análisis del solapamiento, rejilla de 0.1° con anomalías por sensor y dos capas de salida. Se conserva la advertencia sobre el ajuste pendiente por cambios de constelación. Solo cambia contenido editorial, sin incremento de `VERSION`.
- Panel de análisis: todo en Prompt (se añadió el peso 700, que faltaba) y sensor fijo en VIIRS, sin selector.
- La página principal `/` abre el mapa y se retiró el «Hola mundo». Al integrar los cambios de la landing se conserva `/map` como acceso al mismo visualizador y `/landing` como presentación del proyecto; ambas páginas mantienen la carga diferida.
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
