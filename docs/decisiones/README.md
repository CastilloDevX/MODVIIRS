# Decisiones del proyecto

## Registros

- [0001 — Presentación del proyecto en /landing](0001-landing.md): estructura y fondo Particles aprobados por el usuario.

## Confirmadas por el usuario

- Monorepo sostenible con dos aplicaciones: backend Flask (corrige la preferencia inicial por FastAPI) y frontend React.
- Etapa actual de documentación y contexto, sin nuevas funcionalidades.
- Contrastar información del dominio con fuentes confiables NASA y evaluar críticamente cada feature.
- Preguntar sobre decisiones antes de implementar; consultar por commit al completar una feature o cuando se pida push.
- Mensajes `tipo: :gitmoji: descripción` y versión global `X.Y.Z`: mayores/pesadas, características y arreglos.

## Base técnica existente

React usa TypeScript/Vite; Flask usa fábrica y Blueprints. Existe CI y una API de bienvenida. Son decisiones de la base ya construida, no exigencias científicas NASA. Se conserva `docs/` y se incorpora `.agents/` con un punto de entrada `AGENTS.md`. Se registra `0.1.0` como base documental, sin publicar una release.

## Pendientes antes de las features correspondientes

| Decisión | Qué debe acordarse |
| --- | --- |
| Alcance del reto | Verificar enunciado oficial y seleccionar capacidades de la primera entrega. |
| Región y periodo | Área piloto, años y disponibilidad real por sensor/producto. |
| Métrica | Días activos, celdas o índice; unidad y criterios de interpretación. |
| Tiempo y grilla | UTC/día local, resolución, proyección, ventanas y tratamiento de límites. |
| Calidad | SP/NRT, filtros, versiones, duplicados, fuentes no vegetales y faltantes. |
| Armonización | Método, referencia, solapamiento, validación independiente e incertidumbre. |
| Anomalías | Base estacional, suficiencia de datos, umbrales y presentación. |
| Arquitectura adicional | Persistencia, migraciones, ingesta, tareas, cache, credenciales y proveedor de mapas. |
| Entrega | Criterios de aceptación, incremento de VERSION, commit y destino del push. |

La lista no define un roadmap aprobado. Consultar cada decisión cuando corresponda y no implementar dependencias de una respuesta pendiente.

## Plantilla de registro

Crear `NNNN-titulo.md` cuando haya una decisión concreta:

```markdown
# NNNN — Título

- Estado: propuesta / aprobada / rechazada / sustituida
- Fecha:
- Solicitud y alcance:
- Problema y criterios:
- Fuentes oficiales y fecha de consulta:
- Alternativas, evidencia y limitaciones:
- Recomendación y consecuencias:
- Pregunta al usuario:
- Respuesta explícita y fecha:
- Decisión y efecto en arquitectura, contratos y VERSION:
- Verificación y documentos afectados:
```

Dejar la respuesta vacía mientras no exista confirmación. No registrar una recomendación del agente como aprobación del usuario.
