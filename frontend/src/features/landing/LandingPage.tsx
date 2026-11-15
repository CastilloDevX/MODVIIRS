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

function MapLink({ className = '', children = 'Open the visualizer' }) {
  return (
    <Link to="/" className={`landing-map-link ${className}`}>
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
          <span className="landing-pending"><span aria-hidden="true">— </span>To be completed</span>
        </li>
      ))}
    </ul>
  )
}

export function LandingPage() {
  return (
    <div className="landing-page">
      <a href="#content" className="landing-skip-link">Skip to content</a>

      <header className="landing-header">
        <a href="#top" className="landing-small-brand" aria-label="MODVIIRS, top of the page">
          <img src="/icon.png" alt="" width="25" height="25" />
          <span>MODVIIRS</span>
        </a>
        <nav aria-label="Project sections" className="landing-nav">
          {landingSections.map(section => <a key={section.id} href={`#${section.id}`}>{section.label}</a>)}
        </nav>
        <MapLink className="landing-map-link-small">Explore the map</MapLink>
      </header>

      <main id="content">
        <section id="top" className="landing-hero" aria-labelledby="landing-title">
          <ParticleBackground />
          <div className="landing-hero-content">
            <h1 id="landing-title" className="landing-wordmark landing-enter landing-enter-2">
              <img src="/icon.png" alt="" width="88" height="88" fetchPriority="high" />
              <span>MODVIIRS</span>
            </h1>
            <p className="landing-intro landing-enter landing-enter-3">
              From data to perspective.
              <span>Explore the project, its process and the visualizer.</span>
            </p>
            <MapLink className="landing-map-link-primary landing-enter landing-enter-4">Start exploring</MapLink>
          </div>
          <div className="landing-hero-bottom landing-enter landing-enter-4">
            <a href="#harmonization" className="landing-scroll-link"><ArrowDown size={16} aria-hidden="true" />Discover the project</a>
            <span className="landing-hero-caption">MODIS <span aria-hidden="true">/</span> VIIRS</span>
          </div>
        </section>

        <div className="landing-content">
          <section id="harmonization" className="landing-section" aria-labelledby="harmonization-title">
            <Reveal>
              <div className="landing-section-heading">
                <p className="landing-section-index"><span>01</span>THE PROCESS</p>
                <div>
                  <h2 id="harmonization-title">Harmonization<span>.</span></h2>
                  <p className="landing-section-description">A walk from the selection of the data to the results.</p>
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

          <section id="visualizer" className="landing-section" aria-labelledby="visualizer-title">
            <Reveal>
              <div className="landing-section-heading">
                <p className="landing-section-index"><span>02</span>THE EXPLORATION</p>
                <div>
                  <h2 id="visualizer-title">Visualizer features<span>.</span></h2>
                  <p className="landing-section-description">Explore the map, move through time and read the analysis.</p>
                  <Link to="/" className="landing-text-link">Go to the visualizer<ArrowRight size={18} aria-hidden="true" /></Link>
                </div>
              </div>
            </Reveal>
            <VisualizerFeatures />
          </section>

          <section id="prediction" className="landing-section landing-section-split" aria-labelledby="prediction-title">
            <Reveal>
              <p className="landing-section-index"><span>03</span>THE PREDICTION</p>
              <h2 id="prediction-title">Prediction<br />model<span>.</span></h2>
              <p className="landing-section-description">This section will bring together the description of the model, its evaluation and its limits.</p>
            </Reveal>
            <Reveal className="landing-topics-wrap"><PendingTopics topics={predictionTopics} /></Reveal>
          </section>

          <section id="bibliography" className="landing-section landing-section-split" aria-labelledby="bibliography-title">
            <Reveal>
              <p className="landing-section-index"><span>04</span>THE REFERENCES</p>
              <h2 id="bibliography-title">Bibliography<span>.</span></h2>
              <p className="landing-section-description">Sources and readings that will accompany the development of the project.</p>
            </Reveal>
            <Reveal className="landing-topics-wrap"><PendingTopics topics={bibliographyTopics} /></Reveal>
          </section>

          <Reveal>
            <div className="landing-closing">
              <p>The next perspective<br />starts on the map.</p>
            </div>
          </Reveal>
        </div>
      </main>

      <LandingFooter />
    </div>
  )
}
