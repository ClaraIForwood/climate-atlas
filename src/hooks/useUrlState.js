import { useEffect } from 'react'
import useClimateStore from '../store/useClimateStore'

/**
 * Syncs year + layers to URL params on every state change.
 * Reads initial values from URL on mount.
 * Map position (lat/lng/zoom) is handled directly inside MapCanvas.
 */
export function useUrlState() {
  const activeYear = useClimateStore((s) => s.activeYear)
  const activeLayers = useClimateStore((s) => s.activeLayers)
  const setActiveYear = useClimateStore((s) => s.setActiveYear)
  const toggleLayer = useClimateStore((s) => s.toggleLayer)

  // On mount: read URL and hydrate store
  useEffect(() => {
    const p = new URLSearchParams(window.location.search)

    const year = parseInt(p.get('year') ?? '', 10)
    if (!isNaN(year) && year >= 2024 && year <= 2080) {
      setActiveYear(year)
    }

    const layers = (p.get('layers') ?? '').split(',').filter(Boolean)
    const validKeys = ['readiness', 'vulnerability', 'cmip6Grid', 'precipGrid']
    const GRID_KEYS = ['cmip6Grid', 'precipGrid']
    let gridKeyEnabled = null
    layers.forEach((key) => {
      if (!validKeys.includes(key)) return
      if (GRID_KEYS.includes(key)) {
        // Mutual exclusivity: LayerToggles.jsx's handleGridToggle never lets both
        // grid layers be active via the UI — a hand-crafted URL shouldn't be able
        // to either. Whichever grid key appears first in the URL string wins.
        if (gridKeyEnabled) return
        gridKeyEnabled = key
      }
      if (!useClimateStore.getState().activeLayers[key]) {
        toggleLayer(key)
      }
    })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // On state change: push to URL
  useEffect(() => {
    const p = new URLSearchParams(window.location.search)
    p.set('year', activeYear)

    const enabledLayers = Object.entries(activeLayers)
      .filter(([, v]) => v)
      .map(([k]) => k)
    if (enabledLayers.length > 0) {
      p.set('layers', enabledLayers.join(','))
    } else {
      p.delete('layers')
    }

    window.history.replaceState(null, '', `?${p.toString()}`)
  }, [activeYear, activeLayers])
}
