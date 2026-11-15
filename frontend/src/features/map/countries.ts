import type { Feature, FeatureCollection, MultiPolygon, Polygon, Position } from 'geojson'

export type Country = { id: string; name: string }
export type CountryFeature = Feature<Polygon | MultiPolygon, Country>

/** Country picking is parked for now (region picking uses the map clicks); flip to bring it back. */
export const COUNTRY_SELECTION = false
export const COUNTRIES_URL = '/data/countries.geojson'
export const EMPTY: FeatureCollection = { type: 'FeatureCollection', features: [] }

const LAT = 85.0511
/** Rectangle covering the world with a vertex every 10 degrees, so it follows the curvature of the globe. */
export function worldRing(): Position[] {
  const ring: Position[] = []
  for (let x = -180; x < 180; x += 10) ring.push([x, -LAT])
  for (let y = -LAT; y < LAT; y += 10) ring.push([180, y])
  for (let x = 180; x > -180; x -= 10) ring.push([x, LAT])
  for (let y = LAT; y > -LAT; y -= 10) ring.push([-180, y])
  ring.push(ring[0])
  return ring
}

/** The whole world minus the country: the shape that is dimmed. Enclaves and lakes inside the country stay dimmed too. */
export function dimmedWorld(country: CountryFeature): Feature<MultiPolygon> {
  const polygons = country.geometry.type === 'Polygon' ? [country.geometry.coordinates] : country.geometry.coordinates
  const outers = polygons.map(p => p[0])
  const inners = polygons.flatMap(p => p.slice(1))
  return { type: 'Feature', properties: {}, geometry: { type: 'MultiPolygon', coordinates: [[worldRing(), ...outers], ...inners.map(r => [r])] } }
}
