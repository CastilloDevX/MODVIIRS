# Frontend MODVIIRS

React, TypeScript y Vite. Consultar el [README principal](../README.md) para iniciar ambos sistemas, verificar cambios y desplegar.

- `npm ci`: instalar dependencias fijadas.
- `npm run dev`: desarrollo en el puerto 5173, con proxy a Flask.
- `npm run lint`: análisis estático.
- `npm run build`: comprobar tipos y compilar a `dist/`.
- `npm run preview`: inspeccionar la compilación; necesita un backend accesible y un proxy `/api` externo o una URL de API configurada durante el build.

## Landing

La presentación del proyecto está en `/landing`; sus botones abren `/map`. Usa el icono de `public/icon.png`, Orbitron para la marca y Prompt para las secciones. Los textos provisionales y las listas se editan en `src/features/landing/content.ts`; la composición vive en `LandingPage.tsx` y los estilos están acotados a `landing.css`.

La página tiene animaciones de entrada y de aparición al desplazarse, con soporte de `prefers-reduced-motion`. El visualizador se carga al navegar a su ruta, para que la landing no descargue el mapa al abrirse.

### Fondo de partículas

La portada usa [Particles de React Bits](https://reactbits.dev/backgrounds/particles), obtenido con el comando solicitado desde el registro público:

```bash
npx shadcn@latest add @react-bits/Particles-JS-CSS
```

Los parámetros se encuentran en `src/features/landing/ParticleBackground.tsx`: 200 partículas blancas con parallax, brillo, parpadeo y expansión al hacer clic. El componente JavaScript está en `src/components/Particles.jsx`, con su CSS y una declaración TypeScript adyacente. La única adaptación de su lógica mueve la actualización de la referencia de configuración a un efecto de React.

El fondo puede pausarse y se mantiene estático al solicitar movimiento reducido. Si WebGL 2 no está disponible, el fondo CSS y el contenido siguen visibles. No requiere paquetes adicionales, licencia privada ni backend para abrir `/landing`.

Ver [decisión y alcance](../docs/decisiones/0001-landing.md).

### Features y capturas

`VisualizerFeatures.tsx` muestra las cuatro funcionalidades descritas en `content.ts`. El campo opcional `screenshot` permite añadir o actualizar una imagen, sus dimensiones, texto alternativo y pie. Las imágenes se cargan de forma diferida y pueden abrirse a tamaño completo.

Las capturas de mapa y control temporal se guardan en `public/images/features/`; proceden de la aplicación local con datos reales, seleccionando una región de Yucatán en abril de 2024. El control temporal de esta versión recorre fechas y actualiza las detecciones del mapa; la captura no representa una gráfica de actividad. La evidencia de los controles utilizados y respuestas HTTP está en [capturas-landing.json](../docs/decisiones/capturas-landing.json).

El análisis de picos y el panel con gráficas se revisaron en `origin/main` después de actualizar las referencias remotas con `git fetch`; no se hizo pull ni merge. Por indicación del usuario, esas dos features llevan texto sin captura hasta que solicite agregarlas. Para añadirlas después, tomar imágenes de la versión actualizada de la aplicación y completar `screenshot` en sus entradas; no usar ilustraciones de ejemplo como capturas del sistema.
