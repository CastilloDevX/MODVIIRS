const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '/api/v1').replace(/\/$/, '')

export type HealthResponse = { status: 'ok' }

export type ApiErrorKind = 'network' | 'http' | 'invalid-response' | 'cancelled'

export class ApiError extends Error {
  constructor(
    readonly kind: ApiErrorKind,
    message: string,
    readonly statusCode?: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === 'AbortError'
}

export async function getHello(signal: AbortSignal): Promise<{ message: string }> {
  const response = await fetch(`${API_BASE_URL}/hello`, { signal })
  if (!response.ok) throw new Error(`La API respondió con el estado ${response.status}.`)
  const data: unknown = await response.json()
  if (typeof data !== 'object' || data === null || !('message' in data) || typeof data.message !== 'string') {
    throw new Error('La API devolvió una respuesta inesperada.')
  }
  return { message: data.message }
}

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}/health`, { signal })
  } catch (error) {
    if (signal?.aborted || isAbortError(error)) {
      throw new ApiError('cancelled', 'La solicitud de salud fue cancelada.')
    }
    throw new ApiError('network', 'No se pudo conectar con el backend.')
  }

  if (!response.ok) {
    throw new ApiError('http', `La API respondió con el estado ${response.status}.`, response.status)
  }

  let data: unknown
  try {
    data = await response.json()
  } catch (error) {
    if (signal?.aborted || isAbortError(error)) {
      throw new ApiError('cancelled', 'La solicitud de salud fue cancelada.')
    }
    throw new ApiError('invalid-response', 'La API no devolvió JSON válido.')
  }

  if (typeof data !== 'object' || data === null || !('status' in data) || data.status !== 'ok') {
    throw new ApiError('invalid-response', 'La API devolvió un estado inesperado.')
  }

  return { status: 'ok' }
}
