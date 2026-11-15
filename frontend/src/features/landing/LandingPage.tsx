import { useEffect, type ReactNode } from 'react'
import { ArrowDown, ArrowRight, ArrowUpRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import {
  harmonizationSteps,
  landingReferences,
  landingSections,
  predictionContent,
  primaryReference,
} from './content'
import { Reveal } from './Reveal'
import { ParticleBackground } from './ParticleBackground'
import { LandingFooter } from './LandingFooter'
import { LandingBento } from './LandingBento'
import { LandingCapture } from './LandingCapture'
import { VisualizerFeatures } from './VisualizerFeatures'
import './landing.css'

function MapLink({ className = '', children = 'Open explorer' }) {
  return (
    <Link to="/" className={`landing-map-link ${className}`}>
      {children}<ArrowUpRight size={18} aria-hidden="true" />
    </Link>
  )
}

function SourceLink({ href, children, className = '' }: { href: string; children: ReactNode; className?: string }) {
  return (
    <a href={href} className={`landing-source-link ${className}`} target="_blank" rel="noopener noreferrer">
      {children}<ArrowUpRight size={15} aria-hidden="true" />
      <span className="sr-only"> (opens in a new tab)</span>
    </a>
  )
}

export function LandingPage() {
  useEffect(() => {
    const previousLanguage = document.documentElement.lang
    const description = document.querySelector('meta[name="description"]')
    const previousDescription = description?.getAttribute('content')
    document.documentElement.lang = 'en'
    description?.setAttribute('content', 'MODVIIRS — Explore harmonized MODIS and VIIRS hotspot data, activity patterns and weekly anomaly forecasts.')
    return () => {
      document.documentElement.lang = previousLanguage
      if (previousDescription !== null && previousDescription !== undefined) description?.setAttribute('content', previousDescription)
    }
  }, [])

  return (
    <div className="landing-page" lang="en">
      <a href="#contenido" className="landing-skip-link">Skip to content</a>

      <header className="landing-header">
        <a href="#inicio" className="landing-small-brand" aria-label="MODVIIRS, home">
          <img src="/icon.png" alt="" width="25" height="25" />
          <span>MODVIIRS</span>
        </a>
        <nav aria-label="Project sections" className="landing-nav">
          {landingSections.map(section => <a key={section.id} href={`#${section.id}`}>{section.label}</a>)}
        </nav>
        <MapLink className="landing-map-link-small">Explore the map</MapLink>
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
              From data to perspective.
              <span>Discover the process. Explore the patterns.</span>
            </p>
            <MapLink className="landing-map-link-primary landing-enter landing-enter-4">Start exploring</MapLink>
          </div>
          <div className="landing-hero-bottom landing-enter landing-enter-4">
            <a href="#armonizacion" className="landing-scroll-link"><ArrowDown size={16} aria-hidden="true" />Discover the project</a>
            <span className="landing-hero-caption">MODIS <span aria-hidden="true">/</span> VIIRS</span>
          </div>
        </section>

        <div className="landing-content">
          <section id="armonizacion" className="landing-section" aria-labelledby="harmonization-title">
            <Reveal>
              <div className="landing-section-heading">
                <p className="landing-section-index"><span>01</span>THE PROCESS</p>
                <div>
                  <h2 id="harmonization-title">Harmonization<span>.</span></h2>
                  <p className="landing-section-description">From different satellite records to a shared view of activity.</p>
                </div>
              </div>
            </Reveal>
            <LandingBento className="landing-process-grid" items={harmonizationSteps.map(step => ({
              id: step.number,
              content: (
                <article className="landing-process-card">
                  <div className="landing-card-eyebrow"><span>{step.number}</span><span>{step.label}</span></div>
                  <h3>{step.title}</h3>
                  <p>{step.description}</p>
                </article>
              ),
            }))} />
          </section>

          <section id="visualizador" className="landing-section" aria-labelledby="visualizer-title">
            <Reveal>
              <div className="landing-section-heading">
                <p className="landing-section-index"><span>02</span>THE EXPLORER</p>
                <div>
                  <h2 id="visualizer-title">A different perspective<span>.</span></h2>
                  <p className="landing-section-description">Choose a region, move through time and look closer at the data.</p>
                  <Link to="/" className="landing-text-link">Open the explorer<ArrowRight size={18} aria-hidden="true" /></Link>
                </div>
              </div>
            </Reveal>
            <VisualizerFeatures />
          </section>

          <section id="prediccion" className="landing-section" aria-labelledby="prediction-title">
            <LandingBento className="landing-prediction-grid" items={[
              {
                id: 'prediction-overview',
                content: (
                  <article className="landing-prediction-copy">
                    <p className="landing-section-index"><span>03</span>THE OUTLOOK</p>
                    <h2 id="prediction-title">Prediction<br />model<span>.</span></h2>
                    <p className="landing-section-description">{predictionContent.description}</p>
                    <p className="landing-section-description">{predictionContent.method}</p>
                    <p className="landing-prediction-note">{predictionContent.note}</p>
                    <MapLink>Open the explorer</MapLink>
                  </article>
                ),
              },
              {
                id: 'prediction-preview',
                content: <LandingCapture screenshot={predictionContent.screenshot} title="Weekly anomaly forecast" />,
              },
            ]} />
          </section>

          <section id="bibliografia" className="landing-section" aria-labelledby="bibliography-title">
            <Reveal>
              <div className="landing-section-heading">
                <p className="landing-section-index"><span>04</span>THE SOURCES</p>
                <div>
                  <h2 id="bibliography-title">References<span>.</span></h2>
                  <p className="landing-section-description">{primaryReference.description}</p>
                  <SourceLink href={primaryReference.href} className="landing-text-link">{primaryReference.title}</SourceLink>
                </div>
              </div>
            </Reveal>
            <LandingBento className="landing-references" items={landingReferences.map(reference => ({
              id: reference.title,
              content: (
                <article className="landing-reference">
                  <h3><SourceLink href={reference.href}>{reference.title}</SourceLink></h3>
                  <p>{reference.description}</p>
                  {reference.guide && <SourceLink className="landing-guide-link" href={reference.guide.href}>{reference.guide.label}</SourceLink>}
                </article>
              ),
            }))} />
            <p className="landing-attribution">We acknowledge NASA FIRMS / LANCE / ESDIS data, NASA POWER meteorological data and NASA GIBS imagery. The project’s harmonization and prediction methods are developed by the team.</p>
          </section>

          <LandingBento columns={1} className="landing-closing-grid" items={[{
            id: 'start-exploring',
            content: <div className="landing-closing"><p>Your next perspective<br />starts on the map.</p><MapLink>Start exploring</MapLink></div>,
          }]} />
        </div>
      </main>

      <LandingFooter />
    </div>
  )
}
