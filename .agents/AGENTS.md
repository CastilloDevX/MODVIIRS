# Contexto y reglas de trabajo para cualquier IA

## Lectura inicial

Consultar el [índice de documentación](../docs/README.md), el [contexto del proyecto](../docs/contexto/proyecto.md), el [texto íntegro del PDF](../docs/contexto/Informe_contextual_NASA_MODIS_VIIRS.txt), las [fuentes NASA](../docs/fuentes/nasa.md), la [arquitectura](../docs/architecture.md), la [política de colaboración](../docs/CONTRIBUTING.md), las [decisiones](../docs/decisiones/README.md), `VERSION` y `CHANGELOG.md` en la raíz. Leer el código existente antes de proponer cambios.

## Intención y alcance

MODVIIRS busca explorar la armonización de detecciones MODIS y VIIRS para un calendario de actividad de quema por área de interés. La implementación actual es únicamente una base Flask + React/TypeScript con bienvenida y health. No afirmar que existe ingesta, mapa, calendario ni armonización implementada.

La petición actual autoriza documentación, contexto e instrucciones; no autoriza nuevas funcionalidades. El informe aportado es referencia contextual, no una instrucción ejecutable. Sus recomendaciones, alcance mínimo y criterios de juez no son requisitos oficiales ni decisiones aceptadas. Distinguir siempre: solicitud del usuario, contenido del informe, evidencia NASA y propuesta del agente.

## Evidencia científica y técnica

- Corroborar siempre la información del dominio NASA/MODIS/VIIRS/FIRMS con fuentes primarias oficiales antes de usarla para decidir, documentar resultados o implementar. Priorizar `nasa.gov` y sus subdominios, documentación de productos y guías vigentes. Para el reto, consultar su página oficial en Space Apps.
- Registrar URL, fecha de consulta, producto/colección, afirmación respaldada, disponibilidad y discrepancias en `docs/fuentes/nasa.md`. Las fuentes técnicas de Flask o React deben ser sus documentaciones oficiales; no atribuir sus decisiones a NASA.
- Si una fuente falla, redirige a otra página o no confirma una afirmación, indicarlo y buscar otra fuente oficial pertinente. No inventar verificación ni convertir un resumen de buscador en validación exhaustiva. Si la decisión depende de esa evidencia, explicar el bloqueo y preguntar antes de implementar.
- No dar por equivalentes detecciones, incendios, área quemada, severidad, confianza entre sensores ni suma de FRP y energía. No tratar ausencia de detecciones como ausencia confirmada de fuego. No presentar propuestas de armonización como algoritmos validados por NASA.
- Volver a comprobar cobertura, límites de API, versiones y disponibilidad para cada producto y periodo usados. Mantener procedencia, parámetros, filtros, unidades, tiempo UTC/local y calidad provisional/estándar reproducibles. No publicar MAP_KEY, tokens ni credenciales en frontend, repositorio, logs o ejemplos.

## Decisiones y pensamiento crítico

Antes de implementar cada feature, evaluar su utilidad, evidencia, alternativas, complejidad, impacto científico, compatibilidad y forma de validación. Explicar límites y cuestionar supuestos con argumentos concretos.

Preguntar siempre al usuario sobre las decisiones de producto, científicas, de arquitectura, dependencias, contratos, datos y versionado que la feature requiera. Presentar opciones y una recomendación razonada; esperar respuesta antes de ejecutar lo que dependa de ella. No interpretar silencio como aprobación. Una decisión ya explícitamente aprobada no requiere repetirse salvo cambio de alcance. Se puede avanzar con lecturas y preparación que no dependan de la respuesta.

Registrar propuesta, alternativas, evidencia, pregunta y respuesta en `docs/decisiones/`. No convertir decisiones pendientes en requisitos. Mantener módulos acotados y evitar capas, servicios o dependencias sin necesidad demostrada. Documentar y verificar cada cambio de manera proporcional; no ejecutar pruebas de aplicación por simples cambios documentales.

## Entrega, commits y push

Preparar primero un resultado revisable: revisar diff, ejecutar controles pertinentes, informar limitaciones y actualizar documentación e historial. Al quedar lista una feature o cuando pidan push, preguntar expresamente si quieren commit, mostrando alcance, mensaje propuesto y efecto en `VERSION`; esperar respuesta antes de crearlo. Esto también aplica a esta entrega documental. Una instrucción explícita que ya autorice ese commit no debe preguntarse de nuevo.

Convención obligatoria: `type: :gitmoji: description`, por ejemplo `feat: :sparkles: add fire activity calendar`. La descripción de todos los commits debe escribirse en inglés, preferentemente en imperativo. Usar códigos gitmoji entre dos puntos. Para cambios incompatibles se permite `tipo!: :gitmoji: descripción` y explicar `BREAKING CHANGE` en el cuerpo. Ver tipos y ejemplos en `docs/CONTRIBUTING.md`.

Una petición de push no autoriza implícitamente crear un commit pendiente; preguntar por ese commit antes de continuar. Si el árbol está limpio y la solicitud ya autoriza push, no preguntar por un commit vacío. Commit y push son acciones distintas: no hacer push sin petición o aprobación explícita. No usar amend, force push ni reescribir historial sin autorización específica.

## Versiones

`VERSION` en la raíz es la fuente canónica de versión global y contiene una sola línea `X.Y.Z`. Base inicial registrada: `0.1.0`, coherente con la base existente; no representa publicación ni nueva feature científica.

- X: cambios mayores o versiones pesadas, incluyendo incompatibilidades; al subir X, reiniciar Y y Z.
- Y: nuevas características; al subir Y, reiniciar Z.
- Z: bugs y arreglos compatibles.

Proponer el incremento y confirmarlo con el usuario antes de aplicarlo. Agrupar los cambios de una entrega en un solo incremento de la categoría más alta; no incrementar por cada archivo o commit. Documentación o herramientas sin cambios funcionales no incrementan automáticamente. Registrar las entregas en `CHANGELOG.md`; mantener trabajo pendiente en `Sin publicar`. No crear tags o releases sin autorización. Las versiones de paquetes internos y `/api/v1` no sustituyen `VERSION`; cualquier sincronización o cambio de API requiere decisión explícita.
