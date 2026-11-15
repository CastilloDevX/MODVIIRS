import MagicBento, { type MagicBentoItem } from '@/components/MagicBento'
import { useReducedMotion } from './useReducedMotion'

type Props = { items: MagicBentoItem[]; columns?: number; className?: string }

export function LandingBento({ items, columns = 2, className = '' }: Props) {
  const reducedMotion = useReducedMotion()
  return (
    <MagicBento
      key={String(reducedMotion)}
      items={items}
      columns={columns}
      gap={20}
      radius={20}
      glowColor="#ff5149"
      enableBorderGlow={!reducedMotion}
      enableSpotlight={!reducedMotion}
      spotlightRadius={300}
      clickEffect={!reducedMotion}
      textAutoHide={false}
      disableAnimations={reducedMotion}
      className={`landing-bento ${className}`}
      style={{ gridAutoRows: 'minmax(0, auto)' }}
    />
  )
}
