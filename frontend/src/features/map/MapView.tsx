import { useEffect, useRef } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { COUNTRIES_URL, COUNTRY_SELECTION, EMPTY, dimmedWorld, type Country, type CountryFeature } from './countries'
import { BASEMAPS, LANDSAT, OVERLAYS, gibsTiles } from './layers'
import { bboxOf, dimOutside, outlineOf, type Bbox, type LngLat } from './region'
import type { FirePoint } from '../../lib/types'

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
  basemap: string; mode: ViewMode; onModeChange: (m: ViewMode) => void
  selected: string | null; onSelect: (c: Country | null) => void
  picking: boolean; onPickingChange: (p: boolean) => void
  region: Bbox | null; onRegionChange: (r: Bbox | null) => void
  points: FirePoint[] | null; truncated: boolean
}

/** While picking the planet is dark; the box between the first corner and the pointer stays lit. */
function showRegion(map: maplibregl.Map, box: Bbox | null, dark: boolean) {
  ;(map.getSource('region-dim') as maplibregl.GeoJSONSource | undefined)?.setData(dark ? dimOutside(box) : EMPTY)
  ;(map.getSource('region-outline') as maplibregl.GeoJSONSource | undefined)?.setData(box ? outlineOf(box) : EMPTY)
}

const validPoint = (p: LngLat) => Number.isFinite(p.lng) && Number.isFinite(p.lat)

/** Dims everything except the selected country and outlines it. */
function showSelection(map: maplibregl.Map, countries: CountryFeature[], id: string | null) {
  const country = id ? countries.find(c => c.properties.id === id) : undefined
  ;(map.getSource('dim') as maplibregl.GeoJSONSource | undefined)?.setData(country ? dimmedWorld(country) : EMPTY)
  ;(map.getSource('outline') as maplibregl.GeoJSONSource | undefined)?.setData(country ?? EMPTY)
}

export function MapView({ basemap, mode, onModeChange, selected, onSelect, picking, onPickingChange, region, onRegionChange, points, truncated }: Props) {
  const hostRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const countriesRef = useRef<CountryFeature[]>([])
  const cornerRef = useRef<LngLat | null>(null)
  const dragStartRef = useRef<{ lngLat: LngLat; x: number; y: number } | null>(null)
  const dragActiveRef = useRef(false)
  const current = useRef({ basemap, mode, selected, onSelect, picking, onPickingChange, onRegionChange })
  useEffect(() => { current.current = { basemap, mode, selected, onSelect, picking, onPickingChange, onRegionChange } })

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
    })
    map.on('load', async () => {
      map.addSource('dim', { type: 'geojson', data: EMPTY })
      map.addSource('outline', { type: 'geojson', data: EMPTY })
      map.addSource('fire-points', { type: 'geojson', data: EMPTY })
      map.addSource('region-dim', { type: 'geojson', data: EMPTY })
      map.addSource('region-outline', { type: 'geojson', data: EMPTY })
      map.addLayer({ id: 'dim', type: 'fill', source: 'dim', paint: { 'fill-color': '#000', 'fill-opacity': 0.7 } })
      map.addLayer({ id: 'outline', type: 'line', source: 'outline', paint: { 'line-color': '#fff', 'line-width': 1.5 } })
      // Fire circles sit above country dim/outline but below region-dim, so they're visible inside the bbox
      map.addLayer({
        id: 'fire-circles', type: 'circle', source: 'fire-points',
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['get', 'frp'], 0, 3, 50, 5, 200, 9, 500, 13],
          'circle-color': ['interpolate', ['linear'], ['get', 'frp'], 0, '#ffe066', 100, '#ff6600', 500, '#8b0000'],
          'circle-opacity': ['case', ['==', ['get', 'conf_class'], 'high'], 1.0, 0.65],
        },
      })
      map.addLayer({
        id: 'fire-circles-persistent', type: 'circle', source: 'fire-points',
        filter: ['==', ['get', 'is_persistent'], true],
        paint: { 'circle-radius': 7, 'circle-color': 'transparent', 'circle-stroke-width': 1.5, 'circle-stroke-color': '#fff' },
      })
      map.addLayer({ id: 'region-dim', type: 'fill', source: 'region-dim', paint: { 'fill-color': '#000', 'fill-opacity': 0.78 } })
      map.addLayer({ id: 'region-outline', type: 'line', source: 'region-outline', paint: { 'line-color': '#fff', 'line-width': 1.5 } })
      if (current.current.picking) showRegion(map, null, true)
      if (!COUNTRY_SELECTION) return
      try {
        const data = await (await fetch(COUNTRIES_URL)).json()
        countriesRef.current = data.features
        map.addSource('countries', { type: 'geojson', data })
        // Almost transparent, but still hit-testable.
        map.addLayer({ id: 'country-hit', type: 'fill', source: 'countries', paint: { 'fill-color': '#000', 'fill-opacity': 0.01 } }, 'region-dim')
        showSelection(map, countriesRef.current, current.current.selected)
      } catch { /* country selection is optional; the map keeps working */ }
    })
    map.on('mousemove', e => {
      if (current.current.picking) return  // handled by picker overlay
      if (!COUNTRY_SELECTION || !map.getLayer('country-hit')) return
      map.getCanvas().style.cursor = map.queryRenderedFeatures(e.point, { layers: ['country-hit'] }).length ? 'pointer' : ''
    })
    map.on('click', e => {
      if (current.current.picking) return  // handled by picker overlay
      if (!COUNTRY_SELECTION || !map.getLayer('country-hit')) return
      const c = current.current
      const props = map.queryRenderedFeatures(e.point, { layers: ['country-hit'] })[0]?.properties as Country | undefined
      c.onSelect(props && props.id !== c.selected ? { id: props.id, name: props.name } : null)
    })
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return
      if (current.current.picking) current.current.onPickingChange(false)
      else if (COUNTRY_SELECTION) current.current.onSelect(null)
    }
    window.addEventListener('keydown', onKey)

    // GIBS answers 500 for tiles it does not hold (sparse reference layers); not actionable.
    map.on('error', () => {})

    return () => { window.removeEventListener('keydown', onKey); map.remove(); mapRef.current = null }
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
    if (map) showSelection(map, countriesRef.current, selected)
  }, [selected])

  useEffect(() => {
    const map = mapRef.current
    cornerRef.current = null
    dragStartRef.current = null
    dragActiveRef.current = false
    if (!map) return
    if (picking) showRegion(map, null, true)
    else showRegion(map, region, region !== null)
  }, [picking, region])

  useEffect(() => {
    const map = mapRef.current
    if (map?.isStyleLoaded()) applyMode(map, mode)
  }, [mode])

  useEffect(() => {
    const map = mapRef.current
    const src = map?.getSource('fire-points') as maplibregl.GeoJSONSource | undefined
    if (!src) return
    src.setData({
      type: 'FeatureCollection',
      features: (points ?? []).map(p => ({
        type: 'Feature' as const,
        geometry: { type: 'Point' as const, coordinates: [p.longitude, p.latitude] },
        properties: { frp: p.frp, conf_class: p.conf_class, is_persistent: p.is_persistent },
      })),
    })
  }, [points])

  return (
    <div className="map-area">
      <div ref={hostRef} className="map-canvas" role="application" aria-label="Mapa interactivo de la Tierra: arrastra para girar, rueda para acercar" />
      {picking && (
        <div
          className="picker-overlay"
          onMouseDown={e => {
            const map = mapRef.current; if (!map) return
            const lngLat = map.unproject([e.nativeEvent.offsetX, e.nativeEvent.offsetY])
            dragStartRef.current = { lngLat: { lng: lngLat.lng, lat: lngLat.lat }, x: e.nativeEvent.offsetX, y: e.nativeEvent.offsetY }
            dragActiveRef.current = false
          }}
          onMouseMove={e => {
            const map = mapRef.current; if (!map) return
            const lngLat = map.unproject([e.nativeEvent.offsetX, e.nativeEvent.offsetY])
            const point = { lng: lngLat.lng, lat: lngLat.lat }
            if (dragStartRef.current && !dragActiveRef.current) {
              const dx = e.nativeEvent.offsetX - dragStartRef.current.x
              const dy = e.nativeEvent.offsetY - dragStartRef.current.y
              if (dx * dx + dy * dy > 25) dragActiveRef.current = true
            }
            if (dragActiveRef.current && dragStartRef.current) { showRegion(map, bboxOf(dragStartRef.current.lngLat, point), true); return }
            if (cornerRef.current && validPoint(point)) showRegion(map, bboxOf(cornerRef.current, point), true)
          }}
          onMouseUp={e => {
            const map = mapRef.current; if (!map || !dragStartRef.current) return
            const lngLat = map.unproject([e.nativeEvent.offsetX, e.nativeEvent.offsetY])
            const point = { lng: lngLat.lng, lat: lngLat.lat }
            if (dragActiveRef.current) {
              const box = bboxOf(dragStartRef.current.lngLat, point)
              dragStartRef.current = null; dragActiveRef.current = false; cornerRef.current = null
              onRegionChange(box); onPickingChange(false)
            } else {
              dragStartRef.current = null
              if (!validPoint(point)) return
              if (!cornerRef.current) { cornerRef.current = point; return }
              const box = bboxOf(cornerRef.current, point)
              cornerRef.current = null; onRegionChange(box); onPickingChange(false)
            }
          }}
        />
      )}
      <ToggleGroup variant="outline" className="mode-toggle" value={[mode]} aria-label="Modo de vista"
        onValueChange={v => { if (v[0]) onModeChange(v[0] as ViewMode) }}>
        <ToggleGroupItem value="3d">3D</ToggleGroupItem>
        <ToggleGroupItem value="2d">2D</ToggleGroupItem>
      </ToggleGroup>
      {truncated && (
        <div className="fire-truncated" role="status">Showing first 50,000 detections · use CSV export for full data</div>
      )}
    </div>
  )
}
