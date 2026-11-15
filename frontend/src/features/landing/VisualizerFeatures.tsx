import { visualizerFeatures } from './content'
import { LandingBento } from './LandingBento'
import { LandingCapture } from './LandingCapture'

export function VisualizerFeatures() {
  return (
    <LandingBento className="landing-features" items={visualizerFeatures.map((feature, index) => ({
      id: feature.title,
      content: (
        <article className="landing-feature">
          <span className="landing-feature-number" aria-hidden="true">{String(index + 1).padStart(2, '0')}</span>
          <h3>{feature.title}</h3>
          <p>{feature.description}</p>
          <LandingCapture screenshot={feature.screenshot} title={feature.title} />
        </article>
      ),
    }))} />
  )
}
