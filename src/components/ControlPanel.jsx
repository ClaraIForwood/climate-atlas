import YearSlider from './YearSlider'
import LayerToggles from './LayerToggles'
import useClimateStore from '../store/useClimateStore'

const GLASS = {
  background: 'rgba(10, 10, 20, 0.72)',
  backdropFilter: 'blur(12px)',
  WebkitBackdropFilter: 'blur(12px)',
  border: '1px solid rgba(255, 255, 255, 0.08)',
  borderRadius: 12,
}

export default function ControlPanel() {
  const toggleInfoPanel = useClimateStore((s) => s.toggleInfoPanel)

  return (
    <div
      style={{
        ...GLASS,
        position: 'fixed',
        top: 20,
        right: 20,
        width: 260,
        padding: '16px 18px',
        zIndex: 100,
        userSelect: 'none',
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
      }}
    >
      {/* Branding */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <div style={{
            fontSize: 13, fontWeight: 700, color: '#fff',
            letterSpacing: '0.06em', textTransform: 'uppercase',
          }}>
            Climate Atlas
          </div>
          <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.35)', marginTop: 2 }}>
            CMIP6 SSP2-4.5 · ND-GAIN
          </div>
        </div>
        <button
          onClick={toggleInfoPanel}
          aria-label="About this data"
          title="About this data / methodology"
          style={{
            width: 20, height: 20, borderRadius: '50%',
            border: '1px solid rgba(255,255,255,0.25)',
            background: 'transparent', color: 'rgba(255,255,255,0.6)',
            fontSize: 11, fontWeight: 700, cursor: 'pointer',
            flexShrink: 0, lineHeight: 1,
          }}
        >i</button>
      </div>

      <div style={{ height: 1, background: 'rgba(255,255,255,0.06)' }} />

      <YearSlider />

      <div style={{ height: 1, background: 'rgba(255,255,255,0.06)' }} />

      <LayerToggles />
    </div>
  )
}
