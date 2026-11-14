const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '/api/v1').replace(/\/$/, '')

export async function getHello(signal: AbortSignal): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE_URL}/hello`, { signal })
  if (!response.ok) throw new Error(`La API respondió con el estado ${response.status}.`)
  const data: unknown = await response.json()
  if (typeof data !== 'object' || data === null || !('message' in data) || typeof data.message !== 'string') {
    throw new Error('La API devolvió una respuesta inesperada.')
  }
  return { message: data.message }
}
