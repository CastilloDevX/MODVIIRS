import type { LandingScreenshot } from './content'

export function LandingCapture({ screenshot, title }: { screenshot: LandingScreenshot; title: string }) {
  return (
    <figure className="landing-feature-capture">
      <a href={screenshot.src} target="_blank" rel="noopener noreferrer" aria-label={`Enlarge screenshot: ${title} (opens in a new tab)`}>
        <img
          src={screenshot.src}
          alt={screenshot.alt}
          width={screenshot.width}
          height={screenshot.height}
          loading="lazy"
          decoding="async"
        />
      </a>
      <figcaption>{screenshot.caption}</figcaption>
    </figure>
  )
}
