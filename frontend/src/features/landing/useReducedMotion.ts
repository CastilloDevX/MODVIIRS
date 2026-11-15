import { useSyncExternalStore } from 'react'

const query = '(prefers-reduced-motion: reduce)'
const getPreference = () => window.matchMedia(query).matches
const getServerPreference = () => true

function subscribe(onChange: () => void) {
  const media = window.matchMedia(query)
  media.addEventListener('change', onChange)
  return () => media.removeEventListener('change', onChange)
}

export function useReducedMotion() {
  return useSyncExternalStore(subscribe, getPreference, getServerPreference)
}
