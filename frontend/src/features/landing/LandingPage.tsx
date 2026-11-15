import { ArrowDown, ArrowRight, ArrowUpRight, Plus } from 'lucide-react'
import { Link } from 'react-router-dom'
import {
  bibliographyTopics,
  harmonizationSteps,
  landingSections,
  predictionTopics,
} from './content'
import { Reveal } from './Reveal'
import { ParticleBackground } from './ParticleBackground'
import { LandingFooter } from './LandingFooter'
import { VisualizerFeatures } from './VisualizerFeatures'
import './landing.css'

function MapLink({ className = '', children = 'Abrir visualizador' }) {
  return (
    <Link to="/map" className={`landing-map-link ${className}`}>
      {children}<ArrowUpRight size={18} aria-hidden="true" />
    </Link>
  )
}

function PendingTopics({ topics }: { topics: readonly string[] }) {
  return (
    <ul className="landing-topics">
      {topics.map(topic => (
        <li key={topic}>
          <span>{topic}</span>
          <span className="landing-pending"><span aria-hidden="true">— </span>Por completar</span>
        </li>
      ))}
    </ul>
  )
}

export function LandingPage() {
  return (
    <div className="landing-page">
      <a href="#contenido" className="landing-skip-link">Saltar al contenido</a>

      <header className="landing-header">
        <a href="#inicio" className="landing-small-brand" aria-label="MODVIIRS, inicio">
          <img src="/icon.png" alt="" width="25" height="25" />
          <span>MODVIIRS</span>
        </a>
        <nav aria-label="Secciones del proyecto" className="landing-nav">
          {landingSections.map(section => <a key={section.id} href={`#${section.id}`}>{section.label}</a>)}
        </nav>
        <MapLink className="landing-map-link-small">Explorar el mapa</MapLink>
      </header>

      <main id="contenido">
        <section id="inicio" className="landing-hero" aria-labelledby="landing-title">
          <ParticleBackground />
          <div className="landing-hero-content">
            <h1 id="landing-title" className="landing-wordmark landing-enter landing-enter-2">
              <img src="/icon.png" alt="" width="88" height="88" fetchPriority="high" />
              <span>MODVIIRS</span>
            </h1>
            <p className="landing-intro landing-enter landing-enter-3">
              Del dato a la perspectiva.
              <span>Explora el proyecto, su proceso y el visualizador.</span>
            </p>
            <MapLink className="landing-map-link-primary landing-enter landing-enter-4">Comenzar a explorar</MapLink>
          </div>
          <div className="landing-hero-bottom landing-enter landing-enter-4">
            <a href="#armonizacion" className="landing-scroll-link"><ArrowDown size={16} aria-hidden="true" />Conoce el proyecto</a>
            <span className="landing-hero-caption">MODIS <span aria-hidden="true">/</span> VIIRS</span>
          </div>
        </section>

        <div className="landing-content">
          <section id="armonizacion" className="landing-section" aria-labelledby="harmonization-title">
            <Reveal>
              <div className="landing-section-heading">
                <p className="landing-section-index"><span>01</span>EL PROCESO</p>
                <div>
                  <h2 id="harmonization-title">Armonización<span>.</span></h2>
                  <p className="landing-section-description">Un recorrido desde la selección de los datos hasta los resultados.</p>
                </div>
              </div>
              <ol className="landing-process" start={0}>
                {harmonizationSteps.map(step => (
                  <li key={step.number}>
                    <span className="landing-step-number" aria-hidden="true">{step.number}</span>
                    <div><h3>{step.title}</h3><p>{step.description}</p></div>
                    <Plus size={18} className="landing-step-mark" aria-hidden="true" />
                  </li>
                ))}
              </ol>
            </Reveal>
          </section>

          <section id="visualizador" className="landing-section" aria-labelledby="visualizer-title">
            <Reveal>
              <div className="landing-section-heading">
                <p className="landing-section-index"><span>02</span>LA EXPLORACIÓN</p>
                <div>
                  <h2 id="visualizer-title">Features del visualizador<span>.</span></h2>
                  <p className="landing-section-description">Explora el mapa, recorre el tiempo y consulta el análisis.</p>
                  <Link to="/map" className="landing-text-link">Ir al visualizador<ArrowRight size={18} aria-hidden="true" /></Link>
                </div>
              </div>
            </Reveal>
            <VisualizerFeatures />
          </section>

          <section id="prediccion" className="landing-section landing-section-split" aria-labelledby="prediction-title">
            <Reveal>
              <p className="landing-section-index"><span>03</span>LA PREDICCIÓN</p>
              <h2 id="prediction-title">Modelo de<br />predicción<span>.</span></h2>
              <p className="landing-section-description">Esta sección reunirá la descripción del modelo, su evaluación y sus límites.</p>
            </Reveal>
            <Reveal className="landing-topics-wrap"><PendingTopics topics={predictionTopics} /></Reveal>
          </section>

          <section id="bibliografia" className="landing-section landing-section-split" aria-labelledby="bibliography-title">
            <Reveal>
              <p className="landing-section-index"><span>04</span>LAS REFERENCIAS</p>
              <h2 id="bibliography-title">Bibliografía<span>.</span></h2>
              <p className="landing-section-description">Fuentes y lecturas que acompañarán el desarrollo del proyecto.</p>
            </Reveal>
            <Reveal className="landing-topics-wrap"><PendingTopics topics={bibliographyTopics} /></Reveal>
          </section>

          <Reveal>
            <div className="landing-closing">
              <p>La siguiente perspectiva<br />empieza en el mapa.</p>
            </div>
          </Reveal>
        </div>
      </main>

      <LandingFooter />
    </div>
  )
}
