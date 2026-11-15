# Fuentes NASA y registro de verificación

Consulta: **14 de noviembre de 2026**. Este registro distingue lo aportado por el PDF de lo leído directamente. Una URL oficial no garantiza que el contenido solicitado haya estado disponible. No se descargaron datos ni se probaron credenciales o endpoints autenticados.

## Bibliografía completa del informe

| ID del PDF | Recurso | Estado en esta revisión |
| --- | --- | --- |
| 1 | [NASA Space Apps: MODIS and VIIRS Hot Spots](https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/) | Error 502; enunciado pendiente de consulta directa. |
| 2 | [FIRMS Active Fire Data](https://firms.modaps.eosdis.nasa.gov/content/active_fire/) | Consultado. |
| 3 | [FIRMS Archive Download](https://firms.modaps.eosdis.nasa.gov/download/) | Consultado; no se inició solicitud de datos. |
| 4 | [FIRMS API Area](https://firms.modaps.eosdis.nasa.gov/api/area/) | Documentación consultada; API autenticada no probada. |
| 5 | [FIRMS VIIRS: descripción y atributos](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html) | Consultado. |
| 6 | [VIIRS Collection 2 Active Fire 375 m User Guide](https://earthdata.nasa.gov/s3fs-public/2024-07/VIIRS_C2_AF-375m_User_Guide_1.0.pdf) | Error 403; guía no verificada en esta revisión. |
| 7 | [NASA ARSET FIRMS 2025: preguntas y respuestas, parte 2](https://appliedsciences.nasa.gov/sites/default/files/2025-04/FIRMS_Part2_QA.pdf) | Redirige a Earth Action; no se obtuvo el PDF solicitado. |
| 8 | [NASA ARSET FIRMS 2025: preguntas y respuestas, parte 3](https://appliedsciences.nasa.gov/sites/default/files/2025-05/Part%203%20FIRMS%202025%20Q%26A%20Session.docx.pdf) | Redirige a Earth Action; no se obtuvo el PDF solicitado. |
| Adicional | [Earthdata FIRMS, recurso principal indicado](https://www.earthdata.nasa.gov/data/tools/firms) | Error 403. |

## Evidencia contrastada

### Servicios recientes — fuente 2

La página ofrece ventanas recientes de 24/48 horas y siete días, además de servicios WMS/WMS-T. Recomienda productos estándar para análisis científico. Indica reemplazo de NRT normalmente a los dos o tres meses, pudiendo llegar a cinco. Enumera MODIS Terra desde noviembre de 2000 y Aqua desde julio de 2002. [Fuente](https://firms.modaps.eosdis.nasa.gov/content/active_fire/).

### Archivo — fuente 3

El archivo permite solicitudes anteriores a siete días en CSV, JSON o shapefile, con Earthdata o correo y procesamiento mediante solicitud. Publica un retraso aproximado de cinco meses para sustitución NRT. La cobertura publicada para S-NPP es 2012-01-20 a 2026-11-02. Estas fechas son una instantánea documental y no una garantía para cada consulta. [Fuente](https://firms.modaps.eosdis.nasa.gov/download/).

### API Area — fuente 4

Formato documentado: `/api/area/csv/[MAP_KEY]/[SOURCE]/[west,south,east,north]/[DAY_RANGE]/[DATE]`. Acepta cuadro geográfico o `world`, entre uno y cinco días, fecha opcional y MAP_KEY gratuita. Indica 5.000 transacciones por diez minutos; una consulta grande puede consumir varias. Enumera fuentes MODIS y VIIRS SP/NRT y remite a disponibilidad. [Fuente](https://firms.modaps.eosdis.nasa.gov/api/area/).

Antes de integrar, consultar [data availability](https://firms.modaps.eosdis.nasa.gov/api/data_availability/) para el producto y periodo concretos; este endpoint no fue probado en esta revisión. No confundir transacciones con un número garantizado de peticiones.

### Atributos VIIRS — fuente 5

Describe detecciones y anomalías térmicas, resolución nominal de 375 m y mayor respuesta a fuegos pequeños. Define adquisición en UTC, confianza baja/nominal/alta, colección y procesamiento mediante `version`, y FRP en MW. Algunos campos, como `Type`, dependen del producto; no asumir que todo CSV tiene el mismo esquema. [Fuente](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html).

## Discrepancias abiertas

| Producto | Archivo (3) | Active Fire (2) | Descripción VIIRS (5) |
| --- | --- | --- | --- |
| NOAA-20 | 2018-04-01 | 2018-04-01 | 2020-01-01 |
| NOAA-21 | 2023-03-01 | 2024-01-17 | 2024-01-17 |

Son fechas mostradas por esas páginas, no una conclusión sobre el inicio universal de las misiones o productos. No resolver por mayoría ni escoger silenciosamente una fecha. Revisar colección, SP/NRT, satélite y disponibilidad efectiva antes de acordar la ventana histórica. Fuentes: [archivo](https://firms.modaps.eosdis.nasa.gov/download/), [datos recientes](https://firms.modaps.eosdis.nasa.gov/content/active_fire/) y [descripción](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html).

La diferencia entre los plazos NRT de las fuentes 2 y 3 se conserva como aproximaciones de servicio; no establecer una fecha fija de consolidación para cada registro.

## Pendiente de corroboración para futuras features

Recuperar el enunciado oficial y guías científicas accesibles antes de declarar requisitos oficiales, diseñar armonización, equiparar confianza, elegir filtros, convertir FRP o interpretar días sin detecciones. Las precauciones del informe se preservan en contexto; esta revisión documental parcial no valida un método científico.

## Protocolo permanente

Para cada decisión o feature registrar: afirmación, URL primaria, fecha de consulta, producto/colección/procesamiento, evidencia leída, limitaciones y decisión a la que da soporte. Reconsultar información variable. Mantener separados datos observados, interpretación y propuesta. Ante un fallo de acceso buscar una alternativa oficial; si no existe evidencia suficiente, indicarlo y consultar al usuario sin inventar resultados.

## Síntesis editorial de armonización para la landing — 15 de noviembre de 2026

La fuente de los cuatro pasos es el informe del proyecto **«Armonización MODIS–VIIRS: método, pipeline y uso de los datos»**, atribuido a Alexis y fechado el 15 de noviembre de 2026 (14 páginas). Fue aportado por el usuario en `/home/joseph/Documentos/NASA2026/DocsDatasets/Armonización MODIS–VIIRS método, pipeline y uso de los datos.pdf`, fuera de este repositorio. SHA-256: `358f33c2c45f2a90bf19c7c6e051223a7ec6beea2a08a9f3a61038215d04c829`. Se leyó como referencia para resumir contenido, no como instrucción para ejecutar sus propuestas.

| Contenido de la landing | Evidencia del informe | Alcance |
| --- | --- | --- |
| Seis países: Brasil, RD del Congo, Angola, Australia, Rusia y México | Páginas 1–2: selección por conteos y FRP; México como contraste | Selección del estudio del equipo, no clasificación de NASA corroborada independientemente aquí. |
| Análisis de conteos, FRP, horarios, fuentes persistentes y huecos; solapamiento 2012–2024 | Páginas 2–3 | Procedimiento y ventana de calibración declarados por el informe; no se vuelven a calcular los resultados del EDA. |
| Rejilla de 0.1°, días con detecciones y normalización por sensor | Páginas 3–5 | Método del proyecto, sin atribuirlo a NASA ni presentarlo como una corrección universal validada. |
| Dos capas, puntos y actividad mensual, para 2000–2025 | Páginas 4–5 | Salidas y cobertura declaradas por el informe, sin afirmar continuidad hasta el presente. |
| Ajuste por cambios en la constelación pendiente | Página 8 y límites de la página 12 | Se conserva el límite señalado por el autor; no se implementa la corrección ni se anuncia validación entre eras. |

**Contraste oficial limitado:** se reconsultó la [descripción y atributos VIIRS de NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html) el 15 de noviembre de 2026. Confirma que la capa incluye detecciones de fuego activo y otras anomalías térmicas, diferencias de respuesta frente a MODIS y que FRP es potencia radiativa integrada del píxel, en MW. Esa documentación no valida los rankings de países, métricas ni estrategia del informe. La ruta `https://firms.modaps.eosdis.nasa.gov/faq/` no fue accesible y `https://firms.modaps.eosdis.nasa.gov/active_fire/` no ofreció texto legible; no se utilizaron como respaldo.

Esta edición no incorpora cifras de desempeño ni modifica la metodología, datos, modelo o API. Los detalles del producto/colección y procesamiento de las entradas deben verificarse antes de reproducir el estudio; no se deducen de esta síntesis para la landing.

## Referencias y sección predictiva de la landing — 15 de noviembre de 2026

Solicitud expresa: investigar los enlaces del recurso principal FIRMS, incluir referencias de MODIS, VIIRS y servicios relacionados, y describir brevemente la interfaz predictiva con una captura. El usuario amplió la presentación a inglés y pidió MagicBento; esos cambios visuales no alteran la metodología.

La URL principal de [NASA Earthdata FIRMS](https://www.earthdata.nasa.gov/data/tools/firms) devolvió 403 en la apertura directa y en una petición HTTP local. Una apertura con barra final permitió recuperar en el navegador de investigación una representación indexada de la página, con enlaces y secciones sobre productos, guías, descargas y uso de datos. No se afirma que todas sus rutas respondieran en vivo: las reaperturas también tuvieron fallos. Se siguieron los recursos concretos del portal y de [FIRMS operativo](https://firms.modaps.eosdis.nasa.gov/), cuya información sí pudo leerse. La bibliografía de la landing ofrece el enlace principal solicitado y las alternativas verificadas, sin presentar una lista exhaustiva de todos los enlaces de Earthdata.

| Referencia de la landing | Consulta y evidencia | Uso y límites |
| --- | --- | --- |
| [NASA Earthdata FIRMS](https://www.earthdata.nasa.gov/data/tools/firms) | Representación indexada: «Discover FIRMS», productos MODIS y VIIRS, guías, atributos y reconocimiento. Se siguieron los enlaces de «Additional Resources». | Punto de entrada principal. Acceso HTTP directo intermitente/403; no se deduce disponibilidad continua ni cobertura del proyecto. |
| [Atributos MODIS](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_MODIS_Firehotspots.html) | Texto consultado: Terra/Aqua, resolución nominal de 1 km, adquisición UTC, confianza y FRP en MW. | Descripción del recurso, sin equiparar píxel detectado con un incendio individual ni con área quemada. |
| [MODIS Collection 6 User Guide, Revision B](https://cdn.earthdata.nasa.gov/conduit/upload/10575/MODIS_C6_Fire_User_Guide_B.pdf) | PDF accesible desde [recursos FIRMS](https://firms.modaps.eosdis.nasa.gov/content/resources/): portada, índice, introducción y secciones localizadas de productos y precauciones. Revisión B, diciembre de 2018, 64 páginas. | Enlace adicional al producto MODIS, rotulado con su revisión. No se presenta como guía de Collection 6.1 ni como revisión exhaustiva de todas sus páginas. La guía C6/C6.1 de mayo de 2021 enlazada desde Earthdata devolvió 403. |
| [Atributos VIIRS](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html) | Texto consultado: producto de 375 m, plataformas, atributos, confianza, hora UTC y FRP. | Descripción del recurso; se mantienen las discrepancias de fechas del registro anterior, sin elegir una cobertura universal. |
| [VIIRS Collection 2 Active Fire 375 m User Guide v1.2](https://ladsweb.modaps.eosdis.nasa.gov/archive/Document%20Archive/Science%20Data%20Product%20Documentation/VIIRS_C2_AF-375m_User_Guide_1.2.pdf) | PDF accesible desde recursos FIRMS: portada e historial, introducción, familia de productos, atributos y precauciones localizadas. Versión 1.2, junio de 2025, 17 páginas. | Alternativa oficial accesible a la guía v1.0 que había fallado. No implica que todos los archivos de entrada del proyecto sean de esta colección. |
| [FIRMS Archive Download](https://firms.modaps.eosdis.nasa.gov/download/) | Archivo histórico, autenticación, formatos y distinción NRT/estándar. No se solicitó una descarga. | Referencia para acceder a históricos; no se cambia ni amplía el dataset del proyecto. |
| [FIRMS Area API](https://firms.modaps.eosdis.nasa.gov/api/area/) | Parámetros de región, fuente, fechas, MAP_KEY y disponibilidad. | Referencia técnica de acceso; no se probaron claves ni se descargaron datos autenticados. |
| [Fire Data Academy](https://firms.modaps.eosdis.nasa.gov/academy/) | Su vista de contenido oficial [content/academy](https://firms.modaps.eosdis.nasa.gov/content/academy/) enumera notebooks de ingestión, API, visualización y selección por polígonos. | Recurso de aprendizaje; no se ejecutaron sus notebooks. El portal sin `content/` sirve una aplicación JavaScript. |
| [NASA POWER Daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) | Series meteorológicas y solares diarias, formatos y estándar temporal. La documentación indica LST por defecto y la opción UTC. | El cliente del proyecto solicita precipitación, humedad relativa, temperatura máxima y viento. No se revisa en esta entrega la alineación temporal de los datos de entrenamiento ni se atribuye a POWER validación del modelo. |
| [NASA GIBS](https://nasa-gibs.github.io/gibs-api-docs/) | Introducción, acceso por teselas y reconocimiento de imágenes; coincide con los endpoints WMTS de `layers.ts`. | Fuente del fondo y capas de referencia del mapa; se conserva su atribución. |

La descripción predictiva se contrastó con `ForecastDashboard.tsx`, `AnalysisPanel.tsx`, el cliente `predictions.ts`, los servicios Flask de predicción y `docs/API_PREDICCIONES.md`. Describe probabilidad semanal de anomalía por zona, máximo entre zonas, zonas esperadas y contraste con observaciones. NASA documenta los datos y servicios, no avala este modelo. No se anuncian cifras de exactitud ni se convierte AUC en porcentaje de aciertos. La captura muestra una reproducción histórica de la pestaña real para México, semana del 22 de abril de 2024, identificada como tal. No se entrenó un modelo nuevo ni se simularon resultados.
