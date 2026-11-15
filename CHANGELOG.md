# Historial de cambios

La versión global vive en [VERSION](VERSION). Seguir la [política de versionado y commits](docs/CONTRIBUTING.md). Las entradas sin publicar no implican una release, tag, commit ni push realizados.

## Sin publicar

### Frontend

- La sección de features de `/landing` presenta mapa interactivo, timeline de datos armonizados, análisis de picos y módulo de gráficas. Se añadieron capturas reales del mapa y del control temporal con datos de abril de 2024; las capturas de picos y gráficas se aplazan por indicación del usuario. No se incorporan los cambios remotos del visualizador ni se modifica su lógica.
- Footer adaptable de la landing con MODVIIRS y marca Orbitron, equipo Astra 11 y NASA, renderizado desde el componente `LandingFooter`. Se reutilizan los logos editados de `frontend/public/images/`, con NASA transparente y Astra 11 recortado.
- Ruta `/landing` con logo, marca Orbitron y secciones Prompt de armonización, visualizador, predicción y bibliografía. Incluye enlaces a `/map`, contenido provisional centralizado y animaciones de entrada que respetan movimiento reducido. Fondo `@react-bits/Particles-JS-CSS` con los parámetros del usuario, control de pausa y tipos para TypeScript; no añade paquetes npm. La carga de la landing está separada de la del mapa.
- Los cuatro pasos de armonización de la landing resumen el informe aportado «Armonización MODIS–VIIRS: método, pipeline y uso de los datos»: seis países de estudio, análisis del solapamiento, rejilla de 0.1° con anomalías por sensor y dos capas de salida. Se conserva la advertencia sobre el ajuste pendiente por cambios de constelación. Solo cambia contenido editorial, sin incremento de `VERSION`.
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
