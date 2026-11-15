import { Pause, Play } from 'lucide-react'
import { useState, useSyncExternalStore } from 'react'
import Particles, { type ParticlesProps } from '@/components/Particles'

const motionQuery = '(prefers-reduced-motion: reduce)'
const prefersReducedMotion = () => window.matchMedia(motionQuery).matches
const serverMotionPreference = () => true

function subscribeToMotionPreference(onChange: () => void) {
  const media = window.matchMedia(motionQuery)
  media.addEventListener('change', onChange)
  return () => media.removeEventListener('change', onChange)
}

const particleSettings: ParticlesProps = {
  particleColors: ['#ffffff', '#ffffff', '#ffffff'],
  particleCount: 200,
  particleSpread: 10,
  speed: 0.1,
  particleBaseSize: 100,
  glow: 0.5,
  twinkle: 0.3,
  moveParticlesOnHover: true,
  hoverEffect: 'parallax',
  sizeRandomness: 1,
  shape: 'circle',
  depthOfField: 0,
  connections: false,
  connectionDistance: 110,
  particleHoverFactor: 1,
  hoverRadius: 140,
  drift: 'none',
  driftSpeed: 1,
  alphaParticles: false,
  disableRotation: false,
  cameraDistance: 20,
  variation: 0,
  opacity: 1,
  clickBurst: true,
  lightMode: false,
}

export function ParticleBackground() {
  const [paused, setPaused] = useState(false)
  const reducedMotion = useSyncExternalStore(
    subscribeToMotionPreference, prefersReducedMotion, serverMotionPreference,
  )

  return (
    <>
      <div className="landing-hero-background" aria-hidden="true">
        <Particles key={String(reducedMotion)} {...particleSettings} paused={paused || reducedMotion} intro={!reducedMotion} />
      </div>
      {!reducedMotion && (
        <button
          type="button"
          className="landing-motion-toggle"
          aria-label={paused ? 'Resume particle animation' : 'Pause particle animation'}
          onClick={() => setPaused(value => !value)}
        >
          {paused ? <Play size={13} aria-hidden="true" /> : <Pause size={13} aria-hidden="true" />}
          {paused ? 'Resume animation' : 'Pause animation'}
        </button>
      )}
    </>
  )
}
