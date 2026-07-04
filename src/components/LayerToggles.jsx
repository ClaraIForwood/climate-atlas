import useClimateStore from '../store/useClimateStore'

function PillToggle({ checked, indeterminate, onChange, label, description, indent }) {
  return (
    <label
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        cursor: 'pointer',
        padding: '4px 0',
        paddingLeft: indent ? 22 : 0,
      }}
      title={description}
    >
      <div
        style={{
          width: 32,
          height: 18,
          borderRadius: 9,
          background: checked
            ? '#4EB3D3'
            : indeterminate
            ? 'rgba(78,179,211,0.35)'
            : 'rgba(255,255,255,0.12)',
          position: 'relative',
          transition: 'background 0.2s ease',
          flexShrink: 0,
          border: '1px solid rgba(255,255,255,0.15)',
        }}
      >
        <div
          style={{
            position: 'absolute',
            top: 2,
            left: checked ? 14 : indeterminate ? 7 : 2,
            width: 12,
            height: 12,
            borderRadius: '50%',
            background: '#fff',
            transition: 'left 0.2s ease',
            boxShadow: '0 1px 3px rgba(0,0,0,0.4)',
          }}
        />
        <input
          type="checkbox"
          checked={checked}
          onChange={onChange}
          style={{ position: 'absolute', opacity: 0, width: 0, height: 0 }}
        />
      </div>
      <span
        style={{
          fontSize: 12,
          color: (checked || indeterminate) ? '#fff' : 'rgba(255,255,255,0.5)',
          fontWeight: (checked || indeterminate) ? 500 : 400,
        }}
      >
        {label}
      </span>
    </label>
  )
}

export default function LayerToggles() {
  const activeLayers     = useClimateStore((s) => s.activeLayers)
  const toggleLayer      = useClimateStore((s) => s.toggleLayer)

  const bothNdGain     = activeLayers.readiness && activeLayers.vulnerability
  const partialNdGain  = activeLayers.readiness !== activeLayers.vulnerability

  function handleNdGain() {
    if (bothNdGain) {
      toggleLayer('readiness')
      toggleLayer('vulnerability')
    } else {
      if (!activeLayers.readiness)     toggleLayer('readiness')
      if (!activeLayers.vulnerability) toggleLayer('vulnerability')
    }
  }

  return (
    <div>
      <div style={{
        fontSize: 10,
        color: 'rgba(255,255,255,0.4)',
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        marginBottom: 8,
      }}>
        Layers
      </div>

      {/* CMIP6 raw temperature grid */}
      <div style={{ marginBottom: 8, marginTop: 4 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <PillToggle
            checked={activeLayers.cmip6Grid}
            onChange={() => toggleLayer('cmip6Grid')}
            label="Raw CMIP6 grid"
          />
          <span
            style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', cursor: 'help', lineHeight: 1 }}
            title="Shows the raw CMIP6 model output — the actual grid cells that city values are extracted from. Each cell is ~125 km × 125 km."
          >?</span>
        </div>
        <div style={{ paddingLeft: 42, marginTop: 2 }}>
          <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.4)', lineHeight: 1.4 }}>
            Temperature anomaly vs 1990 baseline
          </div>
          <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.25)', marginTop: 1 }}>
            MRI-ESM2-0 · SSP2-4.5 · 1.125° grid
          </div>
        </div>
      </div>

      <div style={{ height: 1, background: 'rgba(255,255,255,0.06)', margin: '4px 0' }} />

      {/* ND-GAIN parent */}
      <div style={{ marginTop: 4 }}>
        <PillToggle
          checked={bothNdGain}
          indeterminate={partialNdGain}
          onChange={handleNdGain}
          label="ND-GAIN"
          description="Toggle both ND-GAIN country overlays"
        />

        {/* Divider line connecting parent to children */}
        <div style={{ position: 'relative', marginLeft: 6 }}>
          <div style={{
            position: 'absolute',
            left: 0,
            top: 0,
            bottom: 8,
            width: 1,
            background: 'rgba(255,255,255,0.1)',
          }} />

          <PillToggle
            checked={activeLayers.vulnerability}
            onChange={() => toggleLayer('vulnerability')}
            label="Vulnerability"
            description="Country exposure to climate impacts (ND-GAIN)"
            indent
          />
          <PillToggle
            checked={activeLayers.readiness}
            onChange={() => toggleLayer('readiness')}
            label="Readiness"
            description="Country capacity to adapt to climate change (ND-GAIN)"
            indent
          />
        </div>
      </div>
    </div>
  )
}
