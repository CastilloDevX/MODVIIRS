# 0001 — Presentación del proyecto en /landing

- Estado: aprobada por solicitud explícita del usuario.
- Fecha: 15 de noviembre de 2026.
- Solicitud y alcance: crear `/landing` con `@react-bits/Particles-JS-CSS`, animación de aparición, `frontend/public/icon.png` junto a la marca Orbitron, botón a `/map` y secciones Prompt. Preparar armonización (pasos 0–3), features del visualizador, modelo de predicción y bibliografía como contenido aún incompleto.
- Problema y criterios: una base editable y adaptable a móvil, sin presentar contenido provisional como resultados o capacidades verificadas. Usar enlaces semánticos, foco visible, movimiento reducido y estilos locales. Separar la carga del mapa para que no condicione la presentación.
- Fuente del componente: [Particles, React Bits](https://reactbits.dev/backgrounds/particles) y su registro público `https://reactbits.dev/r/Particles-JS-CSS.json`, consultados el 15 de noviembre de 2026.
- Alternativas: Horizon Bloom requería acceso al registro privado. El usuario eligió sustituirlo por Particles público; no hace falta una clave privada ni añadir paquetes npm.
- Pregunta resuelta: qué fondo utilizar ante el requisito de licencia de Horizon Bloom.
- Respuesta explícita del usuario: comando `npx shadcn@latest add @react-bits/Particles-JS-CSS`, ejemplo completo de parámetros y «cambiamos el diseño»; reiterado en la solicitud completa de la landing.
- Decisión: usar los parámetros proporcionados (200 partículas blancas, velocidad 0.1, glow 0.5, twinkle 0.3, parallax, clickBurst e intro). Los textos pendientes se marcan «Por completar» y se centralizan en `content.ts`. No se inventan métricas, referencias ni afirmaciones científicas.
- Implementación: registro `@react-bits`, componente JavaScript con tipos adyacentes, configuración en `ParticleBackground.tsx` y actualización de la referencia interna en un efecto de React. Pausa accesible, reacción a cambios de movimiento reducido y fondo CSS si falta WebGL 2. No cambia la API ni la lógica científica.
- VERSION: se conserva `0.2.0`; se propone el incremento Y a `0.3.0`, pendiente de confirmación. Commit y push requieren autorización independiente según las reglas del repositorio.
- Verificación: lint, compilación TypeScript/Vite y navegador en escritorio y móvil: renderizado WebGL, ausencia de desbordamiento horizontal, animaciones, pausa, movimiento reducido, logo, fuentes y navegación a `/map`.

## Ampliación editorial de armonización — 15 de noviembre de 2026

El usuario pidió completar brevemente los cuatro puntos ya existentes a partir del PDF «Armonización MODIS–VIIRS: método, pipeline y uso de los datos». Se aprobaron por esa solicitud los resúmenes de países, EDA, método y salidas, manteniendo el límite del ajuste pendiente por constelación. La procedencia por páginas y el contraste oficial limitado están en [fuentes](../fuentes/nasa.md#síntesis-editorial-de-armonización-para-la-landing--15-de-noviembre-de-2026). No se ejecutan las propuestas del documento ni se modifican las otras secciones. Es un cambio editorial: `VERSION` permanece en `0.2.0`; la propuesta previa de incremento por la landing completa sigue pendiente de respuesta.

## Features y capturas — 15 de noviembre de 2026

- Solicitud: destacar mapa interactivo, timeline de datos armonizados, análisis de picos y módulo de análisis con gráficas; revisar el proyecto y acompañar las funciones con capturas reales.
- Revisión: `MapPage.tsx`, `MapView.tsx`, `Timeline.tsx`, hooks y cliente HTTP, endpoints de datos, documentación del pipeline y referencias de las ramas. Tras `git fetch origin`, `origin/main` incluye `AnalysisPanel.tsx`, `charts.tsx` y una timeline ampliada, ausentes en el checkout local. Se leen con `git show` para verificar las descripciones; no se ejecuta pull, merge ni checkout.
- Aclaración del usuario: «no he hecho un pull de los últimos cambios […] déjalos sin capturas, ya te digo que lo agregues después», en respuesta a la consulta sobre picos y gráficas. Se aplazan las capturas de esas dos funciones y se mantienen sus textos.
- Capturas incluidas: mapa y control de fechas de la aplicación local, mediante interacción con calendarios, región, modos de mapa y teclado. La API consulta `hotspots_harmonized.parquet`; no se sustituyen respuestas ni se fabrican datos o gráficos. El control temporal fotografiado recorre fechas, no muestra una curva de actividad.
- Archivos: `frontend/public/images/features/mapa-interactivo.jpg` y `frontend/public/images/features/linea-de-tiempo.jpg`. La región, fechas, tamaños, commit, atribución de imagen y respuestas de API quedan en [capturas-landing.json](capturas-landing.json).
- Presentación: datos de contenido centralizados, imágenes opcionales, texto alternativo, pies, ampliación de capturas y distribución adaptable. El mapa, los endpoints y las demás secciones de la landing no cambian.
- Versionado: `VERSION` sigue en `0.2.0`, con la entrega de la landing y su commit pendientes de confirmación.
