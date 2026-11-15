import type { CSSProperties, ReactElement } from 'react'

/** Types for the JavaScript variant installed from @react-bits/Particles-JS-CSS. */
export type ParticlesProps = {
  particleColors?: string[]
  particleCount?: number
  particleSpread?: number
  speed?: number
  particleBaseSize?: number
  glow?: number
  twinkle?: number
  moveParticlesOnHover?: boolean
  hoverEffect?: 'parallax' | 'repel' | 'attract'
  sizeRandomness?: number
  shape?: 'circle' | 'square' | 'ring' | 'sparkle'
  depthOfField?: number
  connections?: boolean
  connectionDistance?: number
  particleHoverFactor?: number
  hoverRadius?: number
  drift?: 'none' | 'up' | 'down' | 'forward'
  driftSpeed?: number
  alphaParticles?: boolean
  disableRotation?: boolean
  cameraDistance?: number
  variation?: number
  opacity?: number
  clickBurst?: boolean
  intro?: boolean
  lightMode?: boolean
  paused?: boolean
  pixelRatio?: number
  className?: string
  style?: CSSProperties
}

export default function Particles(props: ParticlesProps): ReactElement
