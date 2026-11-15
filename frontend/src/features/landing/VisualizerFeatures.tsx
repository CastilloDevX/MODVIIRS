import { visualizerFeatures } from './content'
import { Reveal } from './Reveal'

export function VisualizerFeatures() {
  return (
    <div className="landing-features">
      {visualizerFeatures.map((feature, index) => (
        <Reveal key={feature.title}>
          <article className="landing-feature">
            <span className="landing-feature-number" aria-hidden="true">{String(index + 1).padStart(2, '0')}</span>
            <h3>{feature.title}</h3>
            <p>{feature.description}</p>
            {feature.screenshot && (
              <figure className="landing-feature-capture">
                <a href={feature.screenshot.src} target="_blank" rel="noreferrer" aria-label={`Ampliar captura: ${feature.title} (abre una pestaña nueva)`}>
                  <img
                    src={feature.screenshot.src}
                    alt={feature.screenshot.alt}
                    width={feature.screenshot.width}
                    height={feature.screenshot.height}
                    loading="lazy"
                    decoding="async"
                  />
                </a>
                <figcaption>{feature.screenshot.caption}</figcaption>
              </figure>
            )}
          </article>
        </Reveal>
      ))}
    </div>
  )
}
