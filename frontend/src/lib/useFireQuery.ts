import { useEffect, useState } from 'react'

export type QueryState<T> = { data: T | null; loading: boolean; error: string | null }

/**
 * Generic fire data fetching hook with AbortController cleanup.
 * Pass `null` as fetcher to disable (e.g. when required params are missing).
 * deps should list all values captured by the fetcher closure.
 */
export function useFireQuery<T>(
  fetcher: ((signal: AbortSignal) => Promise<T>) | null,
  deps: ReadonlyArray<unknown>,
): QueryState<T> {
  const [state, setState] = useState<QueryState<T>>({ data: null, loading: false, error: null })

  // oxlint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!fetcher) {
      // oxlint-disable-next-line react-hooks/exhaustive-deps
      setState({ data: null, loading: false, error: null })
      return
    }
    const controller = new AbortController()
    setState(prev => ({ ...prev, loading: true, error: null }))
    fetcher(controller.signal).then(
      data => setState({ data, loading: false, error: null }),
      (err: unknown) => {
        if (err instanceof Error && err.name === 'AbortError') return
        setState({ data: null, loading: false, error: err instanceof Error ? err.message : 'Unknown error' })
      },
    )
    return () => controller.abort()
    // oxlint-disable-next-line react-hooks/exhaustive-deps
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps) // deps vary per call site — this hook is intentionally generic

  return state
}
