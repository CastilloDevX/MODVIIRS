// Landing copy and verified sources. See docs/fuentes/nasa.md for provenance.
export const landingSections = [
  { id: 'armonizacion', label: 'Harmonization', number: '01' },
  { id: 'visualizador', label: 'Explorer', number: '02' },
  { id: 'prediccion', label: 'Prediction', number: '03' },
  { id: 'bibliografia', label: 'References', number: '04' },
] as const

// Project report summary; this method is not presented as a NASA-validated algorithm.
export const harmonizationSteps = [
  {
    number: '00',
    title: 'Define the study area',
    description: 'Brazil, DR Congo, Angola, Australia and Russia were selected for their high detection counts. Mexico was added as a contrasting case.',
    label: 'SIX COUNTRIES',
  },
  {
    number: '01',
    title: 'Explore the overlap',
    description: 'Detection counts, fire radiative power (FRP) and overpass times were compared over 2012–2024 to identify sensor differences, persistent sources and data gaps.',
    label: 'EXPLORATORY ANALYSIS',
  },
  {
    number: '02',
    title: 'Build a common framework',
    description: 'A shared 0.1° grid records days with detections per cell and month. Activity is expressed as anomalies and percentiles relative to each sensor’s history.',
    label: 'HARMONIZATION STRATEGY',
  },
  {
    number: '03',
    title: 'Connect the results',
    description: 'Two layers cover 2000–2025: individual detections and monthly gridded activity. Adjustment for changes in the satellite constellation remains pending.',
    label: 'POINTS + GRIDDED ACTIVITY',
  },
] as const

export type LandingScreenshot = {
  src: string
  alt: string
  caption: string
  width: number
  height: number
}

type VisualizerFeature = {
  title: string
  description: string
  screenshot: LandingScreenshot
}

export const visualizerFeatures: readonly VisualizerFeature[] = [
  {
    title: 'Interactive map',
    description: 'Explore detections in 3D or 2D, select a region and filter hotspots by intensity.',
    screenshot: {
      src: '/images/features/mapa-interactivo.jpg',
      alt: 'MODVIIRS 2D map with a selected region in Yucatán, intensity filters and detections from April 4, 2024.',
      caption: 'Yucatán region · detections from April 4, 2024.',
      width: 1600,
      height: 1000,
    },
  },
  {
    title: 'Harmonized data timeline',
    description: 'Move through days, weeks, months or years and see how the detections on the map change at each step.',
    screenshot: {
      src: '/images/features/linea-de-tiempo.jpg',
      alt: 'MODVIIRS with the April 2024 calendar, weekly steps and the timeline cursor on April 8.',
      caption: 'Calendar and weekly steps · April 8–14, 2024.',
      width: 1600,
      height: 1000,
    },
  },
  {
    title: 'Activity peaks at a glance',
    description: 'Find the most active days in your selected period. Hover over the timeline to inspect the daily trend and its marked peak.',
    screenshot: {
      src: '/images/features/picos-timeline.jpg',
      alt: 'Daily activity curve above the MODVIIRS timeline, with the VIIRS peak marked on April 26 and a hover reading for April 19, 2024.',
      caption: 'Hover to read each day and locate the activity peak.',
      width: 1600,
      height: 1000,
    },
  },
  {
    title: 'A closer look at the data',
    description: 'Inspect FRP distributions, satellite breakdowns, monthly anomalies and typical seasonality in the analysis panel.',
    screenshot: {
      src: '/images/features/modulo-analisis.jpg',
      alt: 'MODVIIRS historical analysis panel with the April 2024 summary, daily hotspot and FRP charts and statistics for the selected step.',
      caption: 'Period summary and daily hotspot and FRP series.',
      width: 1600,
      height: 1000,
    },
  },
]

export const predictionContent = {
  description: 'Explore weekly hotspot activity anomalies for your selected region. The Forecast tab brings together peak zone risk, expected anomalous zones and charts comparing predictions with observations.',
  method: 'The model combines historical hotspot activity with meteorological variables from NASA POWER.',
  note: 'Peak risk is the highest zone probability in the selected region. This is an experimental anomaly forecast; a hotspot is not an individual wildfire.',
  screenshot: {
    src: '/images/features/pronostico.jpg',
    alt: 'MODVIIRS Forecast tab showing a historical weekly outlook for Mexico, peak zone risk, expected and observed anomalous zones, and comparison charts.',
    caption: 'Forecast tab · historical replay for the week of April 22, 2024.',
    width: 1600,
    height: 1200,
  } satisfies LandingScreenshot,
}

export const primaryReference = {
  title: 'NASA Earthdata · FIRMS',
  href: 'https://www.earthdata.nasa.gov/data/tools/firms',
  description: 'Start with the official FIRMS resource hub, then explore the product guides and services below.',
}

type LandingReference = {
  title: string
  href: string
  description: string
  guide?: { label: string; href: string }
}

export const landingReferences: readonly LandingReference[] = [
  {
    title: 'MODIS active fire data',
    href: 'https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_MODIS_Firehotspots.html',
    description: 'Terra and Aqua detections at nominal 1 km resolution, with confidence, acquisition time and FRP attributes.',
    guide: {
      label: 'Collection 6 user guide · Revision B (PDF)',
      href: 'https://cdn.earthdata.nasa.gov/conduit/upload/10575/MODIS_C6_Fire_User_Guide_B.pdf',
    },
  },
  {
    title: 'VIIRS active fire data',
    href: 'https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html',
    description: 'The 375 m hotspot product: sensor platforms, detection attributes and interpretation.',
    guide: {
      label: 'Collection 2 user guide · v1.2 (PDF)',
      href: 'https://ladsweb.modaps.eosdis.nasa.gov/archive/Document%20Archive/Science%20Data%20Product%20Documentation/VIIRS_C2_AF-375m_User_Guide_1.2.pdf',
    },
  },
  {
    title: 'FIRMS archive downloads',
    href: 'https://firms.modaps.eosdis.nasa.gov/download/',
    description: 'Historical detections, available coverage and standard processing information.',
  },
  {
    title: 'FIRMS Area API',
    href: 'https://firms.modaps.eosdis.nasa.gov/api/area/',
    description: 'Query detections by region, product and date. Includes parameters and access requirements.',
  },
  {
    title: 'Fire Data Academy',
    href: 'https://firms.modaps.eosdis.nasa.gov/academy/',
    description: 'Official Python and notebook tutorials for accessing, filtering and visualizing FIRMS data.',
  },
  {
    title: 'NASA POWER',
    href: 'https://power.larc.nasa.gov/docs/services/api/temporal/daily/',
    description: 'Daily meteorological data services used by the project’s prediction pipeline.',
  },
  {
    title: 'NASA GIBS',
    href: 'https://nasa-gibs.github.io/gibs-api-docs/',
    description: 'Satellite imagery services behind the explorer’s basemap and reference layers.',
  },
]
