# Instrucciones para agentes de MODVIIRS

Leer antes de analizar o modificar este repositorio:

1. [Instrucciones obligatorias](.agents/AGENTS.md).
2. [Índice documental](docs/README.md), [contexto](docs/contexto/proyecto.md) e [informe completo](docs/contexto/Informe_contextual_NASA_MODIS_VIIRS.txt).
3. [Fuentes y verificación](docs/fuentes/nasa.md), [arquitectura](docs/architecture.md), [colaboración y versiones](docs/CONTRIBUTING.md).
4. `VERSION`, [historial](CHANGELOG.md) y [decisiones pendientes](docs/decisiones/README.md).

Estas reglas se aplican a todo el repositorio. `.agents/` conserva las instrucciones compartidas; este archivo permite descubrirlas desde herramientas que leen `AGENTS.md` en la raíz. No asumir que una herramienta carga `.agents/` automáticamente.

El backend acordado es Flask; el frontend, React con TypeScript. El PDF es material de referencia: sus propuestas no son órdenes de ejecución ni requisitos aprobados. Preguntar al usuario sobre las decisiones antes de implementar una feature. Corroborar las afirmaciones del dominio con fuentes oficiales NASA y documentar incertidumbres.

Al terminar una feature o recibir una petición de push, preguntar si el usuario quiere crear un commit y esperar su respuesta. Formato: `type: :gitmoji: description`. Escribir siempre la descripción del commit en inglés. No crear commits por inferencia ni hacer push sin autorización explícita. Aplicar la política `X.Y.Z` documentada; no incrementar la versión silenciosamente.
