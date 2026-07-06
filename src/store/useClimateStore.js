import { create } from 'zustand'

const useClimateStore = create((set) => ({
  activeYear: 2024,
  activeLayers: {
    readiness: false,
    vulnerability: false,
    cmip6Grid: false,
    precipGrid: false,
  },
  infoPanelOpen: false,

  setActiveYear: (year) => set({ activeYear: year }),

  toggleLayer: (layer) =>
    set((state) => ({
      activeLayers: { ...state.activeLayers, [layer]: !state.activeLayers[layer] },
    })),

  toggleInfoPanel: () => set((state) => ({ infoPanelOpen: !state.infoPanelOpen })),
  closeInfoPanel: () => set({ infoPanelOpen: false }),
}))

export default useClimateStore
