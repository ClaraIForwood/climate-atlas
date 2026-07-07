import useClimateStore from '../store/useClimateStore'

const GLASS = {
  background: 'rgba(10, 10, 20, 0.82)',
  backdropFilter: 'blur(14px)',
  WebkitBackdropFilter: 'blur(14px)',
  border: '1px solid rgba(255, 255, 255, 0.08)',
  borderRadius: 12,
}

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{
        fontSize: 10, color: 'rgba(255,255,255,0.4)',
        letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 6,
      }}>
        {title}
      </div>
      <div style={{ fontSize: 14, color: 'rgba(255,255,255,0.75)', lineHeight: 1.6 }}>
        {children}
      </div>
    </div>
  )
}

export default function InfoPanel() {
  const open = useClimateStore((s) => s.infoPanelOpen)
  const close = useClimateStore((s) => s.closeInfoPanel)

  if (!open) return null

  return (
    <div
      style={{
        ...GLASS,
        position: 'fixed',
        top: 20,
        right: 296,
        width: 360,
        maxWidth: 'calc(100vw - 40px)',
        maxHeight: 'calc(100vh - 40px)',
        overflowY: 'auto',
        zIndex: 100,
        padding: '18px 20px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={{ fontSize: 16, fontWeight: 700, color: '#fff', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
          About this data
        </div>
        <button
          onClick={close}
          aria-label="Close"
          style={{ background: 'transparent', border: 'none', color: 'rgba(255,255,255,0.5)', fontSize: 18, cursor: 'pointer', lineHeight: 1, padding: 0 }}
        >×</button>
      </div>

      <Section title="Single-model limitation">
        <p style={{ margin: '0 0 8px' }}>
          Both the temperature and precipitation grids on this map come from a single CMIP6
          model (MRI-ESM2-0, SSP2-4.5) — one of roughly 30 models in the CMIP6 ensemble.
          Individual models can diverge substantially from the multi-model mean, especially
          for precipitation.
        </p>
        <p style={{ margin: '0 0 8px' }}>
          This single-model limitation applies to all layers on this map. A country-level
          multi-model comparison (World Bank CCKP) is planned as additional context in a
          future update — note that this will provide country-level context, not direct
          city-grid validation.
        </p>
        <p style={{ margin: 0, color: 'rgba(255,255,255,0.55)' }}>
          A concrete example: in this single run, parts of the UK actually show slight
          <em> cooling</em> relative to the 1990–2014 baseline in the 2050s–2070s (rather
          than just muted warming) — a real example of single-run internal variability,
          not a data error.
        </p>
      </Section>

      <Section title="How this compares to the multi-model range">
        <p style={{ margin: 0 }}>
          For context, the IPCC AR6 multi-model ensemble projects <strong>global</strong> warming
          of 2.1–3.5°C by 2081–2100 (vs. 1850–1900) under a comparable medium-emissions scenario
          (SSP2-4.5) — AR6 WGI SPM Table SPM.1. Land regions like Northern Europe are expected to
          warm somewhat faster than this global average, though a verified regional figure has
          not yet been sourced for this panel.
        </p>
      </Section>
    </div>
  )
}
