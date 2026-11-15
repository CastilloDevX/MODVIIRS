import { useEffect, useRef } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { BASEMAPS, LANDSAT, OVERLAYS, gibsTiles } from './layers'
import { LEVELS, PENINSULA, pct, type ZoneCollection, type ZoneProps } from './predictions'

const EMPTY = { type: 'FeatureCollection', features: [] } as const
type GeoData = Parameters<maplibregl.GeoJSONSource['setData']>[0]

/** Forecast layer: 0.5° zones coloured by the probability of anomalous hotspot activity. */
function addPredictionLayers(map: maplibregl.Map) {
  map.addSource('pred', { type: 'geojson', data: EMPTY as unknown as GeoData })
  map.addLayer({
    id: 'pred-fill', type: 'fill', source: 'pred',
    paint: {
      'fill-color': ['step', ['coalesce', ['get', 'prob'], 0], LEVELS[0].color, 0.1, LEVELS[1].color, 0.3, LEVELS[2].color, 0.5, LEVELS[3].color],
      'fill-opacity': ['case', ['==', ['get', 'prob'], null], 0.05, 0.5],
    },
  })
  map.addLayer({
    id: 'pred-line', type: 'line', source: 'pred',
    paint: {
      'line-color': ['case', ['==', ['get', 'anomalia'], 1], '#ffffff', 'rgba(0,0,0,0.45)'],
      'line-width': ['case', ['==', ['get', 'anomalia'], 1], 2.2, 0.6],
    },
  })
  map.on('click', 'pred-fill', e => {
    const p = e.features?.[0]?.properties as unknown as ZoneProps | undefined
    if (!p) return
    const anom = p.anomalia === null ? 'not observed yet' : p.anomalia === 1 ? 'YES' : 'no'
    new maplibregl.Popup({ closeButton: true })
      .setLngLat(e.lngLat)
      .setHTML(`<div class="pred-popup"><b>Zone ${p.zona_id}</b><br/>Anomaly probability: <b>${pct(p.prob)}</b> (${p.nivel})`
        + `<br/>Historical frequency: ${pct(p.base)}<br/>Fire-days: ${p.valor ?? '—'} · usual high (p90): ${p.p90 ?? '—'}`
        + `<br/>Observed anomaly: ${anom}</div>`)
      .addTo(map)
  })
  map.on('mouseenter', 'pred-fill', () => { map.getCanvas().style.cursor = 'pointer' })
  map.on('mouseleave', 'pred-fill', () => { map.getCanvas().style.cursor = '' })
}

/** 3D = globe with atmosphere; 2D = flat Mercator map, north up, no tilt. */
function applyMode(map: maplibregl.Map, mode: ViewMode) {
  if (mode === '3d') {
    map.setProjection({ type: 'globe' })
    map.setSky({ 'atmosphere-blend': ['interpolate', ['linear'], ['zoom'], 0, 1, 5, 1, 7, 0] })
    map.setMinZoom(0)
  } else {
    map.setProjection({ type: 'mercator' })
    map.setSky({ 'atmosphere-blend': 0 })
    map.setMinZoom(1)
    map.easeTo({ pitch: 0, bearing: 0, duration: 400 })
  }
}

export type ViewMode = '3d' | '2d'

type Props = {
  basemap: string
  mode: ViewMode
  onModeChange: (m: ViewMode) => void
  prediction?: ZoneCollection | null
  /** Increment to fly to the Yucatán Peninsula. */
  focusPeninsula?: number
}

export function MapView({ basemap, mode, onModeChange, prediction = null, focusPeninsula = 0 }: Props) {
  const hostRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const current = useRef({ basemap, mode, prediction })
  useEffect(() => { current.current = { basemap, mode, prediction } })

  useEffect(() => {
    const map = new maplibregl.Map({
      container: hostRef.current!,
      style: { version: 8, sources: {}, layers: [{ id: 'bg', type: 'background', paint: { 'background-color': '#000' } }] },
      center: [-75, 10],
      zoom: 1.6,
      maxZoom: BASEMAPS.find(b => b.id === current.current.basemap)!.maxMapZoom,
      cancelPendingTileRequestsWhileZooming: false,
      maxTileCacheSize: 600,
      attributionControl: { compact: true, customAttribution: 'Imagery: NASA GIBS / ESDIS' },
    })
    mapRef.current = map
    map.scrollZoom.setWheelZoomRate(1 / 150)
    map.scrollZoom.setZoomRate(1 / 40)
    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right')

    map.on('load', () => {
      applyMode(map, current.current.mode)
      for (const b of BASEMAPS) {
        map.addSource(b.id, { type: 'raster', tiles: gibsTiles(b.layer, b.maxzoom, b.format, b.time), tileSize: 256, maxzoom: b.maxzoom })
        map.addLayer({ id: b.id, type: 'raster', source: b.id, layout: { visibility: b.id === current.current.basemap ? 'visible' : 'none' } })
      }
      map.addSource(LANDSAT.id, { type: 'raster', tiles: gibsTiles(LANDSAT.layer, LANDSAT.level, 'jpg', LANDSAT.time), tileSize: 256, maxzoom: LANDSAT.level })
      map.addLayer({
        id: LANDSAT.id, type: 'raster', source: LANDSAT.id,
        paint: { 'raster-opacity': ['interpolate', ['linear'], ['zoom'], 4, 0, 6, 1] },
        layout: { visibility: current.current.basemap === LANDSAT.showFor ? 'visible' : 'none' },
      })
      for (const o of OVERLAYS) {
        map.addSource(o.id, { type: 'raster', tiles: gibsTiles(o.layer, o.level, 'png'), tileSize: 256, maxzoom: o.level })
        map.addLayer({ id: o.id, type: 'raster', source: o.id, paint: { 'raster-opacity': ['interpolate', ['linear'], ['zoom'], 8.5, 1, 10, 0] }, maxzoom: 10 })
      }
      addPredictionLayers(map)
      const p = current.current.prediction
      if (p) (map.getSource('pred') as maplibregl.GeoJSONSource).setData(p as unknown as GeoData)
    })
    // GIBS answers 500 for tiles it does not hold (sparse reference layers); not actionable.
    map.on('error', () => {})

    return () => { map.remove(); mapRef.current = null }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map?.isStyleLoaded()) return
    for (const b of BASEMAPS) map.setLayoutProperty(b.id, 'visibility', b.id === basemap ? 'visible' : 'none')
    map.setMaxZoom(BASEMAPS.find(b => b.id === basemap)!.maxMapZoom)
    map.setLayoutProperty(LANDSAT.id, 'visibility', basemap === LANDSAT.showFor ? 'visible' : 'none')
  }, [basemap])

  useEffect(() => {
    const map = mapRef.current
    if (map?.isStyleLoaded()) applyMode(map, mode)
  }, [mode])

  useEffect(() => {
    const src = mapRef.current?.getSource('pred') as maplibregl.GeoJSONSource | undefined
    src?.setData((prediction ?? EMPTY) as unknown as GeoData)
  }, [prediction])

  useEffect(() => {
    if (focusPeninsula > 0) mapRef.current?.fitBounds(PENINSULA, { padding: 60, duration: 1600 })
  }, [focusPeninsula])

  return (
    <div className="map-area">
      <div ref={hostRef} className="map-canvas" role="application" aria-label="Mapa interactivo de la Tierra: arrastra para girar, rueda para acercar" />
      <ToggleGroup variant="outline" className="mode-toggle" value={[mode]} aria-label="Modo de vista"
        onValueChange={v => { if (v[0]) onModeChange(v[0] as ViewMode) }}>
        <ToggleGroupItem value="3d">3D</ToggleGroupItem>
        <ToggleGroupItem value="2d">2D</ToggleGroupItem>
      </ToggleGroup>
    </div>
  )
}
