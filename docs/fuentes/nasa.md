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
