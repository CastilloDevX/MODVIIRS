import { useEffect, useRef, useState, type ReactNode } from 'react'

type Props = { children: ReactNode; className?: string }

/** One entrance per section; content stays visible when motion is reduced or unsupported. */
export function Reveal({ children, className = '' }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const element = ref.current
    if (!element) return

    const motion = window.matchMedia('(prefers-reduced-motion: reduce)')
    if (motion.matches || !('IntersectionObserver' in window)) return

    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setVisible(true)
        observer.disconnect()
      }
    }, { threshold: 0.08 })

    element.dataset.animate = 'true'
    observer.observe(element)
    const onPreferenceChange = () => {
      if (motion.matches) {
        setVisible(true)
        observer.disconnect()
      }
    }
    motion.addEventListener('change', onPreferenceChange)
    return () => {
      observer.disconnect()
      motion.removeEventListener('change', onPreferenceChange)
    }
  }, [])

  return (
    <div ref={ref} className={`landing-reveal ${className}`} data-visible={visible}>
      {children}
    </div>
  )
}
