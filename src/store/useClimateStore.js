import { create } from 'zustand'

const useClimateStore = create((set) => ({
  activeYear: 2024,
  activeLayers: {
    readiness: false,
    vulnerability: false,
    cmip6Grid: false,
  },

  setActiveYear: (year) => set({ activeYear: year }),

  toggleLayer: (layer) =>
    set((state) => ({
      activeLayers: { ...state.activeLayers, [layer]: !state.activeLayers[layer] },
    })),
}))

export default useClimateStore
