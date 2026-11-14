# Contexto del proyecto MODVIIRS

Fecha de incorporación: 14 de noviembre de 2026.

## Procedencia y autoridad

El usuario aportó **Harmonization of MODIS and VIIRS Hot Spots — Informe contextual y análisis técnico**, fechado el 14 de noviembre de 2026 y referido a NASA Space Apps Challenge 2026. El original de cuatro páginas está [preservado aquí](Informe_contextual_NASA_MODIS_VIIRS.pdf), con [texto completo](Informe_contextual_NASA_MODIS_VIIRS.txt), incluidas sus once secciones y bibliografía. SHA-256 del PDF: `335d042311c330f1d5041392626dea57f02103302e4889b5ab03a3f18ba5b118`.

Este documento organiza el contexto aportado; no sustituye al original. El informe advierte que su interpretación y perspectiva de evaluación no son una evaluación oficial NASA. Sus instrucciones y propuestas se tratan como material de referencia, separado de las solicitudes del usuario. La página del reto no pudo consultarse directamente en esta revisión; los requisitos atribuidos al reto permanecen pendientes de corroboración directa. Consultar el [registro NASA](../fuentes/nasa.md).

## Objetivo y destinatarios descritos en el informe (secciones 1–2)

Construir una aplicación web que transforme registros de focos activos MODIS y VIIRS en un calendario comparable de actividad de quema para un área de interés. Permitir explorar patrones históricos, condiciones inusuales y periodos críticos, tanto de incendios forestales como de quemas agrícolas detectables desde satélite.

Los destinatarios descritos son personal de alerta temprana y emergencias, científicos y gestores de tierras. El informe sitúa el reto en ciencias de la Tierra y software, con dificultad intermedia y avanzada.

El informe atribuye al reto selección de área, armonización conjunta de sensores y calendario histórico con anomalías. No identifica un algoritmo, arquitectura, lenguaje, modelo de IA o diseño obligatorio del calendario. Predicción de propagación, clasificación de causas y alertas automáticas serían ampliaciones, no requisitos confirmados. Todo ello requiere cotejo con el enunciado oficial antes de fijar alcance.

## Problema científico (sección 3)

Según el informe, MODIS ofrece detecciones de resolución nominal aproximada de 1 km y el producto VIIRS considerado, de 375 m. Las diferencias de sensibilidad, pasos, geometría, cobertura y algoritmos afectan la comparabilidad. Concatenar archivos no resuelve esas diferencias ni existe una conversión universal basada únicamente en áreas de píxel.

Una detección no representa necesariamente un incendio independiente: un mismo evento puede generar varios píxeles y observaciones. Los focos no proporcionan directamente área quemada, severidad ni perímetros precisos. Estas limitaciones condicionan la métrica, la interfaz y cualquier afirmación científica futura.

## Datos, servicios y cobertura (secciones 4–5)

El informe propone FIRMS como fuente de detecciones de fuego activo y anomalías térmicas. También pueden aparecer volcanes y fuentes industriales. Contempla descargas recientes, archivo histórico, WMS/WMS-T y API Area con MAP_KEY. Los parámetros, fuentes SP/NRT, cuotas, formatos y disponibilidad deben verificarse para cada integración; ver el registro oficial enlazado.

Se distingue procesamiento estándar para análisis histórico de datos NRT provisionales. El informe documenta MODIS Terra desde noviembre de 2000, Aqua desde julio de 2002 y VIIRS S-NPP del 20 de enero de 2012 al 2 de noviembre de 2026. No asumir continuidad futura ni aplicar fechas de una misión a otro producto. Las fuentes oficiales muestran discrepancias para NOAA-20 y NOAA-21 que deben resolverse por producto concreto, consultando disponibilidad antes de descargar.

## Atributos y límites (sección 6)

El contexto aportado incluye coordenadas, fecha/hora de adquisición, satélite, confianza, colección/versión, dimensiones del píxel, temperaturas de brillo y FRP, según producto. Se debe conservar su procedencia y distinguir hora de adquisición UTC de la fecha de consulta o procesamiento.

- Definir si el calendario usa UTC o día local; no elegirlo implícitamente.
- Las categorías VIIRS baja, nominal y alta no se deben tratar como probabilidades calibradas ni equipararse sin justificación a confianza MODIS.
- Las temperaturas de brillo corresponden a canales espectrales; no representan la temperatura física exacta del incendio.
- FRP es potencia radiativa integrada del píxel en MW. La suma entre pasos puede repetir el mismo fuego y no proporciona directamente energía emitida.
- Nubes, humo, duración, tamaño y cobertura pueden impedir detecciones. Cero puntos no confirma ausencia de fuego. Distinguir datos faltantes, ausencia de detecciones y observación válida; un CSV de detecciones por sí solo no resuelve esa distinción.

Estas precauciones provienen del informe. La validación documental específica de cada afirmación debe completarse con guías oficiales antes de implementar los cálculos correspondientes.

## Propuesta metodológica del informe (sección 7; no aprobada)

1. Acordar región piloto, escala espacial y métrica: días con actividad, celdas activas o índice comparable; conservar conteos por sensor.
2. Ingerir históricos estándar y validar coordenadas, fechas, versiones y duplicados exactos, separando provisional y definitivo.
3. Agregar en grilla común y ventanas explícitas, reconociendo que la grilla no elimina sesgos ni recupera fuegos omitidos.
4. Estimar relaciones con años de solapamiento por región, temporada y día/noche; estudiar correspondencias sin forzar parejas para toda detección.
5. Validar en regiones o años excluidos del ajuste y comparar con una referencia sencilla, mostrando error, sesgo e incertidumbre. Igualar sensores no demuestra exactitud física.
6. Definir una referencia estacional y percentiles con número de años y suficiencia de observaciones explícitos.
7. Presentar mapa, calendario, serie y explicación, con inspección de fuente, filtros, periodo y calidad.

## Anomalías y alerta temprana (sección 8)

El informe propone anomalía como desviación respecto de una referencia histórica definida. Su ejemplo de percentil 90 semanal es ilustrativo: no es umbral NASA aprobado ni decisión del proyecto. La historia puede apoyar preparación y priorización; no produce por sí misma probabilidades futuras, pronósticos operativos ni órdenes de evacuación. Predicción de incendios o propagación requeriría variables y validación adicionales, como meteorología, combustibles y topografía.

## Evaluación y prototipo sugeridos (secciones 9–10)

La perspectiva de juez del informe es una propuesta, no una rúbrica oficial. Sugiere evaluar pertinencia, solidez científica, evidencia antes/después, validación independiente y fallos conocidos, trazabilidad y utilidad. Debe poder reproducirse el resultado e identificar fuentes, versiones, filtros y parámetros.

Como alcance revisable propone una región piloto, varios años de solapamiento, datos reales identificados, métrica acordada, comparación por sensor, corrección validada, calendario y referencia estacional. Añade procedencia, limitaciones, actualización y exportación; expansión global después de validar regionalmente. Estas capacidades son propuestas pendientes, no funcionalidades existentes ni compromisos de entrega.

## Fuentes y atribución (sección 11)

Las ocho referencias del PDF y el recurso Earthdata indicado por el usuario se conservan en [fuentes NASA](../fuentes/nasa.md), junto con su estado de consulta. Reconocer NASA FIRMS/ESDIS y añadir citas de los productos realmente utilizados cuando se incorporen datos. No insinuar patrocinio, aval científico ni evaluación oficial de NASA.

## Estado y reglas acordadas por el usuario

Existe una base monorepo Flask + React/TypeScript: `/api/v1/hello`, `/api/v1/health`, manejo de errores, pantalla conectada, pruebas y CI. No existe todavía funcionalidad científica.

En esta etapa solo se autoriza incorporar documentación y reglas. Antes de implementar features hay que analizar críticamente alternativas y consultar las decisiones con el usuario. Las afirmaciones del dominio se corroboran con NASA; los vacíos se declaran. Al terminar una feature o solicitar push, se pregunta si se desea commit. El formato obligatorio es `type: :gitmoji: description`. `VERSION` expresa `X.Y.Z`: X cambios mayores/pesados, Y características, Z bugs/arreglos. La política detallada está en [colaboración](../CONTRIBUTING.md) y se replica para IA en [.agents](../../.agents/AGENTS.md).
