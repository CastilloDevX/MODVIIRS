# Frontend MODVIIRS

React, TypeScript y Vite. Consultar el [README principal](../README.md) para iniciar ambos sistemas, verificar cambios y desplegar.

- `npm ci`: instalar dependencias fijadas.
- `npm run dev`: desarrollo en el puerto 5173, con proxy a Flask.
- `npm run lint`: análisis estático.
- `npm run build`: comprobar tipos y compilar a `dist/`.
- `npm run preview`: inspeccionar la compilación; necesita un backend accesible y un proxy `/api` externo o una URL de API configurada durante el build.

## Landing

La presentación del proyecto está en `/landing`, en inglés; sus botones abren `/map`. Usa el icono de `public/icon.png`, Orbitron para la marca y Prompt para las secciones. Los textos, referencias oficiales y metadatos de las capturas se editan en `src/features/landing/content.ts`; la composición vive en `LandingPage.tsx` y los estilos están acotados a `landing.css`. Se establece el idioma y la descripción del documento al entrar y se restauran al salir.

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

Las cuatro capturas de `public/images/features/` proceden del visualizador actualizado, con una región de Yucatán y el rango del 1 al 30 de abril de 2024. Muestran el mapa con filtros de intensidad, un paso semanal, la curva de actividad al pasar el cursor por la timeline y el panel histórico con sus gráficas. Son capturas nativas de Chromium a 1600 × 1000, obtenidas mediante los controles reales de la aplicación y sin datos simulados.

La evidencia de región, fechas, escalas, versión del código y respuestas HTTP está en [capturas-landing.json](../docs/decisiones/capturas-landing.json). La serie diaria del análisis usa VIIRS; los puntos del mapa y las estadísticas del paso incluyen ambos sensores. Al renovar las imágenes, esperar a que terminen de cargar datos, capas y animaciones; actualizar sus dimensiones, texto alternativo y pie en `content.ts`.

### Predicción y fuentes

La quinta captura, `public/images/features/pronostico.jpg` (1600 × 1200), muestra la pestaña Pronóstico del sistema con México y la semana del 22 de abril de 2024. Se identifica como reproducción histórica; las imágenes conservan los rótulos de la interfaz fotografiada. El texto de la landing describe anomalías semanales, máximo de probabilidad por zona, zonas esperadas y contraste con observaciones, sin anunciar exactitud del modelo.

Las referencias enlazan el portal FIRMS indicado por el usuario, atributos y guías de MODIS/VIIRS con sus versiones, archivo, API, formación, POWER y GIBS. La consulta y sus límites están en [fuentes NASA](../docs/fuentes/nasa.md#referencias-y-sección-predictiva-de-la-landing--15-de-noviembre-de-2026). Las fuentes oficiales documentan los datos; el método del equipo no se presenta como validado por NASA.

### MagicBento

Desde armonización se usa el motor de MagicBento aportado por el usuario, conservando el fondo Particles en la portada. `components/MagicBento.jsx` y su CSS contienen la adaptación; `MagicBento.d.ts` aporta tipos y `LandingBento.tsx` configura tarjetas de contenido propio con altura automática, columnas adaptables de al menos 300 px, brillo coral y movimiento reducido. Las ilustraciones de ejemplo y sus dependencias Hugeicons se omiten; no se añade ningún paquete.

`LandingCapture.tsx` conserva el texto alternativo, las dimensiones y la ampliación de las cinco capturas. Los enlaces a fuentes siguen siendo enlaces semánticos dentro de tarjetas estáticas. Cambiar la preferencia de movimiento durante la sesión reinicia los efectos con la configuración correspondiente; no se recortan descripciones para encajar en una altura fija.
