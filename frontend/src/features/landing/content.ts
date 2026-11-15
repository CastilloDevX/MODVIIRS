// Textos de la landing: editar aquí sin cambiar la composición de la página.
export const landingSections = [
  { id: 'armonizacion', label: 'Armonización', number: '01' },
  { id: 'visualizador', label: 'Visualizador', number: '02' },
  { id: 'prediccion', label: 'Predicción', number: '03' },
  { id: 'bibliografia', label: 'Bibliografía', number: '04' },
] as const

// Síntesis del informe de armonización del proyecto; procedencia y límites en docs/fuentes/nasa.md.
export const harmonizationSteps = [
  {
    number: '00',
    title: 'Acotar los datos',
    description: 'Se seleccionaron Brasil, RD del Congo, Angola, Australia y Rusia por su elevado número de detecciones. México se añadió como caso de contraste.',
  },
  {
    number: '01',
    title: 'Análisis exploratorio de datos',
    description: 'Se compararon conteos, potencia radiativa (FRP) y horarios de paso en el solapamiento 2012–2024 para identificar diferencias entre sensores, fuentes persistentes y huecos de datos.',
  },
  {
    number: '02',
    title: 'Elegir la estrategia de armonización',
    description: 'Una rejilla común de 0.1° registra días con detecciones por celda y mes. La actividad se expresa como anomalías y percentiles respecto a la historia de cada sensor.',
  },
  {
    number: '03',
    title: 'Resultados',
    description: 'Se generaron dos capas para 2000–2025: detecciones individuales y actividad mensual en rejilla. El ajuste por cambios en la constelación de satélites sigue pendiente.',
  },
] as const

type VisualizerFeature = {
  title: string
  description: string
  screenshot?: { src: string; alt: string; caption: string; width: number; height: number }
}

export const visualizerFeatures: readonly VisualizerFeature[] = [
  {
    title: 'Mapa interactivo',
    description: 'Explora las detecciones en 3D o 2D, cambia la imagen de fondo y selecciona la región que quieres consultar.',
    screenshot: {
      src: '/images/features/mapa-interactivo.jpg',
      alt: 'Visualizador MODVIIRS con mapa, región seleccionada y detecciones de abril de 2024.',
      caption: 'Una región, sus detecciones y el contexto del mapa.',
      width: 1440,
      height: 960,
    },
  },
  {
    title: 'Timeline de datos armonizados',
    description: 'Recorre el periodo seleccionado por días o intervalos y observa cómo cambian las detecciones que aparecen en el mapa.',
    screenshot: {
      src: '/images/features/linea-de-tiempo.jpg',
      alt: 'Control temporal de MODVIIRS con un día seleccionado dentro del rango de abril de 2024.',
      caption: 'Desplázate por las fechas con el cursor o el teclado.',
      width: 1160,
      height: 270,
    },
  },
  {
    title: 'Análisis de picos de la timeline',
    description: 'Identifica los días de mayor actividad en el rango seleccionado y consulta el pico junto a la evolución diaria de las detecciones.',
  },
  {
    title: 'Módulo de análisis con gráficas',
    description: 'Consulta distribuciones de potencia radiativa (FRP), datos por satélite, un calendario de anomalías y la estacionalidad en un mismo panel.',
  },
]

export const predictionTopics = ['Descripción del modelo', 'Entrenamiento y evaluación', 'Resultados y limitaciones']
export const bibliographyTopics = ['Referencia 01', 'Referencia 02', 'Referencia 03']
