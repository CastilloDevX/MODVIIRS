# Arquitectura

## Límites

El repositorio comparte documentación y controles, mientras cada aplicación conserva su código, dependencias y ciclo de despliegue. HTTP/JSON es el contrato entre ambas. El frontend no importa código del backend.

Flask sigue el patrón [application factory](https://flask.palletsprojects.com/en/stable/patterns/appfactories/): `create_app` crea instancias aisladas, aplica configuración y registra Blueprints. Los endpoints viven bajo `/api/v1`. React se organiza por funcionalidad; `App` compone la pantalla y `lib/api.ts` encapsula el acceso HTTP. Vite construye los recursos del [frontend](https://vite.dev/guide/).

## Cómo crecer

- Añadir funcionalidades del backend mediante Blueprints, registrados en `api/__init__.py`. Mantener las rutas pequeñas. Cuando aparezcan reglas de negocio, extraerlas a servicios del módulo correspondiente.
- Incorporar persistencia cuando exista una necesidad concreta; aislar el acceso a datos y acompañar cambios del esquema con migraciones. Inicializar futuras extensiones dentro de la fábrica mediante `init_app`.
- Añadir cada funcionalidad de React en `src/features/<nombre>`. Extraer componentes compartidos cuando se reutilicen. Añadir routing y estado global cuando los flujos lo requieran.
- Mantener contratos explícitos y probar respuestas, errores y métodos HTTP. Para una API más amplia, incorporar OpenAPI y generación de tipos para evitar mantener contratos duplicados.
- Mantener compatible `/api/v1`; introducir una versión nueva ante cambios incompatibles. Revisar dependencias y locks periódicamente.

## Alcance inicial

Esta base ofrece comunicación real entre aplicaciones, comprobación de disponibilidad del proceso, errores JSON, configuración externa y CI. No incorpora base de datos, autenticación ni infraestructura de despliegue, porque todavía no hay requisitos que permitan diseñarlos con criterio.

El frontend valida la respuesta de bienvenida en tiempo de ejecución y cancela las peticiones al desmontarse. Las llamadas tienen un límite de diez segundos y se pueden reintentar. El mismo origen evita necesitar CORS durante el desarrollo y en el despliegue recomendado.


## Contexto científico y decisiones futuras

La base técnica no implementa aún ingesta FIRMS, mapas, calendario ni armonización. El [contexto aportado](contexto/proyecto.md) y su PDF completo orientan la investigación; sus propuestas no son requisitos aprobados. Consultar [fuentes NASA](fuentes/nasa.md) y resolver las [decisiones pendientes](decisiones/README.md) con el usuario antes de implementar cada feature.

El historial global usa el archivo raíz [VERSION](../VERSION), con formato `X.Y.Z` y cambios registrados en [CHANGELOG.md](../CHANGELOG.md). X identifica versiones mayores/pesadas, Y nuevas características y Z bugs/arreglos. Este versionado es independiente de `/api/v1`.

La política de decisiones, confirmación de commit/push y mensajes `tipo: :gitmoji: descripción` está en [CONTRIBUTING.md](CONTRIBUTING.md); también se aplica a agentes mediante [AGENTS.md](../AGENTS.md) y [.agents/AGENTS.md](../.agents/AGENTS.md).
