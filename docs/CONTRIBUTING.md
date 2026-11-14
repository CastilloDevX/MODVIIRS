# Colaboración, decisiones y versiones

Esta política reproduce las reglas expresamente solicitadas por el usuario y también rige el trabajo de IA mediante [AGENTS.md](../AGENTS.md) y [.agents/AGENTS.md](../.agents/AGENTS.md).

## Antes de implementar

Leer el [contexto completo](README.md), inspeccionar el código y contrastar información del dominio con [fuentes NASA](fuentes/nasa.md). Evaluar críticamente necesidad, evidencia, alternativas, impacto científico, mantenibilidad, compatibilidad y validación de cada feature.

Preguntar siempre al usuario sobre las decisiones de producto, metodología, arquitectura, datos, dependencias, contratos y versionado antes de implementar lo que dependa de ellas. Exponer opciones y recomendar con razones. Esperar respuesta: silencio no equivale a aprobación. No repetir decisiones ya aprobadas salvo cambios de alcance. Registrar acuerdos en [decisiones](decisiones/README.md). Las recomendaciones del PDF no son órdenes ni requisitos aprobados.

## Entrega y autorización de Git

1. Completar los cambios autorizados y presentar un resultado revisable, con diff, verificaciones, documentación, riesgos y entradas en el historial.
2. Cuando una feature quede lista, preguntar si desean commit, mostrando mensaje, alcance y efecto propuesto en `VERSION`. Aplicar también esta consulta a entregas documentales.
3. Si se solicita push y hay cambios pendientes, preguntar si desean crear el commit antes de continuar. Una solicitud de push no autoriza implícitamente ese commit.
4. Esperar confirmación antes de crear el commit, salvo que el usuario ya lo haya autorizado explícitamente para ese alcance. No mezclar cambios ajenos ni modificar historial sin autorización.
5. Hacer push únicamente con solicitud o autorización explícita. Si ya está autorizado y no hay cambios pendientes, no pedir un commit vacío. Crear tags y releases requiere autorización propia.

## Mensajes de commit

Formato requerido:

```text
type: :gitmoji: description
```

`type` sigue Conventional Commits y `:gitmoji:` es el código del emoji, conservando ambos puntos. La descripción debe estar siempre en inglés y explicar el cambio concreto, preferentemente con un verbo en imperativo (por ejemplo, `add`, `fix` o `document`). Esta regla también se publica en [.github/CONTRIBUTING.md](../.github/CONTRIBUTING.md). No usar el texto literal `convencional-commit` como tipo ni limitar todo a `feat`.

| Tipo | Uso | Ejemplo |
| --- | --- | --- |
| feat | Característica | `feat: :sparkles: add fire activity calendar` |
| fix | Bug o arreglo | `fix: :bug: correct acquisition time conversion` |
| docs | Documentación | `docs: :memo: document NASA context and project guidelines` |
| refactor | Reorganización sin nueva funcionalidad | `refactor: :recycle: extract record validation` |
| test | Pruebas | `test: :white_check_mark: cover API responses` |
| chore | Mantenimiento | `chore: :wrench: update development configuration` |
| ci | Integración continua | `ci: :construction_worker: validate frontend and backend` |

Para cambios incompatibles: `feat!: :boom: change export contract`, con explicación `BREAKING CHANGE` en el cuerpo. El ejemplo de una feature no constituye autorización para construirla.

## VERSION e historial

El archivo raíz [VERSION](../VERSION) es la fuente canónica de versión del proyecto. Contiene exclusivamente `X.Y.Z`, enteros no negativos sin prefijos ni ceros iniciales. La base inicial es `0.1.0`, coherente con la versión del paquete backend existente; registrar esta base no constituye una publicación.

| Componente | Cuándo incrementar | Ejemplo |
| --- | --- | --- |
| X | Versiones pesadas o cambios mayores, incluyendo incompatibilidades | `0.4.2 → 1.0.0` |
| Y | Nuevas características | `0.1.3 → 0.2.0` |
| Z | Bugs o arreglos compatibles | `0.1.0 → 0.1.1` |

Al subir X, reiniciar Y y Z; al subir Y, reiniciar Z. Si una entrega agrupa cambios, usar una vez el incremento de mayor categoría. No incrementar por cada commit ni automáticamente por documentación, pruebas o herramientas sin cambio funcional. Proponer y confirmar con el usuario la clasificación y versión antes de aplicarla, especialmente ante una “versión pesada” ambigua.

[CHANGELOG.md](../CHANGELOG.md) conserva el historial: mantener cambios pendientes en `Sin publicar`; al aprobar una entrega, asignar versión y fecha real, describiendo características, arreglos e incompatibilidades. Actualizar `VERSION` y la entrada de entrega conjuntamente. No inventar versiones previas, fechas de publicación ni tags. El estado inicial se documenta como base, no como release realizada.

Las versiones internas de paquetes no gobiernan el historial global; `/api/v1` versiona el contrato HTTP y no se cambia automáticamente al incrementar `VERSION`. La sincronización de metadatos internos o el cambio de contrato deben acordarse explícitamente.

## Evidencia y comprobaciones

Documentar fuentes, parámetros, unidades, tiempo, calidad y reproducibilidad de resultados científicos. Para código ejecutar pruebas y controles pertinentes al cambio. Para documentación revisar enlaces locales, integridad del PDF, consistencia de reglas y diff; no son necesarias pruebas de aplicación si no cambia código.
