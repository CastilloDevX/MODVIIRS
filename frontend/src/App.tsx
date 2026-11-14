import { HelloPanel } from './features/hello/HelloPanel'
import './App.css'

export default function App() {
  return (
    <div className="shell">
      <header><a className="brand" href="/">MODVIIRS<span>Workspace</span></a><span className="environment">Desarrollo</span></header>
      <main>
        <p className="eyebrow">CONEXIÓN CON LA API</p>
        <h1>Un comienzo conectado.</h1>
        <p className="intro">Tu espacio de trabajo con React y Flask.</p>
        <HelloPanel />
      </main>
      <footer>MODVIIRS <span>Base del proyecto · v0.1.0</span></footer>
    </div>
  )
}
