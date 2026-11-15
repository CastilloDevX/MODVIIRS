import type { CSSProperties, MouseEvent, ReactElement, ReactNode } from 'react'

export type MagicBentoItem = {
  id: string
  title?: string
  description?: string
  label?: string
  icon?: ReactNode
  visual?: ReactNode
  content?: ReactNode
  image?: string
  href?: string
  target?: string
  rel?: string
  colSpan?: number
  rowSpan?: number
  onClick?: (event: MouseEvent<HTMLElement>) => void
}

export type MagicBentoProps = {
  items: MagicBentoItem[]
  columns?: number
  rowHeight?: number
  gap?: number
  radius?: number
  theme?: 'dark' | 'light'
  glowColor?: string
  textAutoHide?: boolean
  enableBorderGlow?: boolean
  enableSpotlight?: boolean
  spotlightRadius?: number
  enableStars?: boolean
  particleCount?: number
  enableTilt?: boolean
  enableMagnetism?: boolean
  clickEffect?: boolean
  intro?: boolean
  disableAnimations?: boolean
  onItemClick?: (item: MagicBentoItem, index: number) => void
  className?: string
  style?: CSSProperties
}

export default function MagicBento(props: MagicBentoProps): ReactElement
