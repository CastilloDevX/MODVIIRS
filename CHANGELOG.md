# Historial de cambios

La versión global vive en [VERSION](VERSION). Seguir la [política de versionado y commits](docs/CONTRIBUTING.md). Las entradas sin publicar no implican una release, tag, commit ni push realizados.

## Sin publicar

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
