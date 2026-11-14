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
