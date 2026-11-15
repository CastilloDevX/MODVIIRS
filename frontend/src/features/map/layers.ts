export type Basemap = { id: string; label: string; layer: string; format: 'jpeg' | 'png'; maxzoom: number; maxMapZoom: number; time?: string }

// maxMapZoom: deepest MapLibre zoom that still shows real detail (above it tiles are only enlarged); 256 px tiles are 1:1 at zoom = tile level - 1.
// Only the daylight Earth dataset is used.
// Every layer comes from NASA GIBS (Global Imagery Browse Services, NASA ESDIS), WMTS GoogleMapsCompatible.
export const BASEMAPS: Basemap[] = [
  { id: 'clear', label: 'Sin nubes', layer: 'BlueMarble_ShadedRelief_Bathymetry', format: 'jpeg', maxzoom: 8, maxMapZoom: 12 },
]

const GIBS = 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best'
export const gibsTiles = (layer: string, level: number, format: string, time?: string) =>
  [`${GIBS}/${layer}/default/${time ? `${time}/` : ''}GoogleMapsCompatible_Level${level}/{z}/{y}/{x}.${format}`]

/** Landsat 30 m cloud-free composite (year 2000), shown over the "clear" basemap when zoomed in. Level 12 is the finest NASA GIBS offers. */
export const LANDSAT = { id: 'landsat', layer: 'Landsat_WELD_CorrectedReflectance_TrueColor_Global_Annual', level: 12, time: '2000-12-01', showFor: 'clear' }

/** Coastlines, borders and place names (NASA GIBS reference layers). They are drawn from tiles of level 9, so they fade out when zoomed in past it. */
export const OVERLAYS = [
  { id: 'features', layer: 'Reference_Features', level: 9 },
  { id: 'labels', layer: 'Reference_Labels', level: 9 },
] as const
