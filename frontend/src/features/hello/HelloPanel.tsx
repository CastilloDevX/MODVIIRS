import { useEffect, useState } from 'react'
import { getHello } from '../../lib/api'

type State = { status: 'loading' } | { status: 'success'; message: string } | { status: 'error'; message: string }

export function HelloPanel() {
  const [attempt, setAttempt] = useState(0)
  const [state, setState] = useState<State>({ status: 'loading' })

  useEffect(() => {
    const controller = new AbortController()
    let timedOut = false
    const timeout = window.setTimeout(() => {
      timedOut = true
      controller.abort()
    }, 10000)
    getHello(controller.signal)
      .then(({ message }) => setState({ status: 'success', message }))
      .catch((error: unknown) => {
        if (controller.signal.aborted && !timedOut) return
        setState({ status: 'error', message: timedOut ? 'La API tardó demasiado en responder.' : error instanceof Error ? error.message : 'No se pudo conectar con la API.' })
      })
      .finally(() => window.clearTimeout(timeout))
    return () => { window.clearTimeout(timeout); controller.abort() }
  }, [attempt])

  return (
    <section className="panel" aria-labelledby="response-title">
      <div className="panel-heading"><h2 id="response-title">Respuesta del servidor</h2><span className={`status ${state.status}`}>{state.status === 'success' ? 'Conectado' : state.status === 'error' ? 'Sin conexión' : 'Conectando'}</span></div>
      <div className="response" role="status" aria-live="polite" aria-atomic="true">
        {state.status === 'loading' ? <p>Consultando el servidor…</p> : state.status === 'error' ? <><h3>No pudimos conectar</h3><p>{state.message}</p></> : <><span className="response-label">MENSAJE RECIBIDO</span><h3>{state.message}</h3><p>El frontend y el backend se están comunicando.</p></>}
      </div>
      <div className="panel-actions"><span>Servicio de bienvenida</span><button disabled={state.status === 'loading'} onClick={() => { setState({ status: 'loading' }); setAttempt(value => value + 1) }}>{state.status === 'loading' ? 'Consultando…' : state.status === 'error' ? 'Reintentar' : 'Volver a consultar'}<span aria-hidden="true"> ↗</span></button></div>
    </section>
  )
}
