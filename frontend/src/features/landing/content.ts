// Landing page copy: edit here without changing the page layout.
export const landingSections = [
  { id: 'harmonization', label: 'Harmonization', number: '01' },
  { id: 'visualizer', label: 'Visualizer', number: '02' },
  { id: 'prediction', label: 'Prediction', number: '03' },
  { id: 'bibliography', label: 'Bibliography', number: '04' },
] as const

// Summary of the project's harmonization report; provenance and limits in docs/fuentes/nasa.md.
export const harmonizationSteps = [
  {
    number: '00',
    title: 'Scoping the data',
    description: 'Brazil, DR Congo, Angola, Australia and Russia were selected for their high number of detections. Mexico was added as a contrast case.',
  },
  {
    number: '01',
    title: 'Exploratory data analysis',
    description: 'Counts, fire radiative power (FRP) and overpass times were compared over the 2012–2024 overlap to identify differences between sensors, persistent sources and data gaps.',
  },
  {
    number: '02',
    title: 'Choosing the harmonization strategy',
    description: 'A common 0.1° grid records days with detections per cell and month. Activity is expressed as anomalies and percentiles against each sensor\'s own history.',
  },
  {
    number: '03',
    title: 'Results',
    description: 'Two layers were produced for 2000–2025: individual detections and monthly gridded activity. Adjusting for changes in the satellite constellation is still pending.',
  },
] as const

type VisualizerFeature = {
  title: string
  description: string
  screenshot?: { src: string; alt: string; caption: string; width: number; height: number }
}

export const visualizerFeatures: readonly VisualizerFeature[] = [
  {
    title: 'Interactive map',
    description: 'Explore detections in 3D or 2D and select the region you want to look at.',
    screenshot: {
      src: '/images/features/mapa-interactivo.jpg',
      alt: 'MODVIIRS visualizer with a map, a selected region and detections from April 2024.',
      caption: 'A region, its detections and the map context.',
      width: 1440,
      height: 960,
    },
  },
  {
    title: 'Harmonized data timeline',
    description: 'Move through the selected period by days or intervals and watch how the detections on the map change.',
    screenshot: {
      src: '/images/features/linea-de-tiempo.jpg',
      alt: 'MODVIIRS timeline control with one day selected within the April 2024 range.',
      caption: 'Move through the dates with the cursor or the keyboard.',
      width: 1160,
      height: 270,
    },
  },
  {
    title: 'Timeline peak analysis',
    description: 'Spot the most active days in the selected range and read the peak alongside the daily evolution of detections.',
  },
  {
    title: 'Analysis module with charts',
    description: 'See radiative power (FRP) distributions, per-satellite data, an anomaly calendar and seasonality in a single panel.',
  },
]

export const predictionTopics = ['Model description', 'Training and evaluation', 'Results and limitations']
export const bibliographyTopics = ['Reference 01', 'Reference 02', 'Reference 03']
