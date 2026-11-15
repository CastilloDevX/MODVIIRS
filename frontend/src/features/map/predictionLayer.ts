/**
 * Ready-to-use MapLibre layer for the forecast (0.5° zones coloured by probability).
 * Usage inside MapView:  map.on('load', () => addPredictionLayers(map))
 *                        setPredictionData(map, zoneCollection | null)
 *                        map.fitBounds(PENINSULA)
 */
import * as maplibregl from 'maplibre-gl'
import { LEVELS, pct, type ZoneCollection, type ZoneProps } from './predictions'

const EMPTY_FC = { type: 'FeatureCollection', features: [] } as const
type GeoData = Parameters<maplibregl.GeoJSONSource['setData']>[0]

export function addPredictionLayers(map: maplibregl.Map, opts: { popup?: boolean } = { popup: true }) {
  if (map.getSource('pred')) return
  map.addSource('pred', { type: 'geojson', data: EMPTY_FC as unknown as GeoData })
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
  if (!opts.popup) return
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
}

export function setPredictionData(map: maplibregl.Map, data: ZoneCollection | null) {
  ;(map.getSource('pred') as maplibregl.GeoJSONSource | undefined)?.setData((data ?? EMPTY_FC) as unknown as GeoData)
}

export function setPredictionVisible(map: maplibregl.Map, visible: boolean) {
  for (const id of ['pred-fill', 'pred-line']) if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', visible ? 'visible' : 'none')
}
