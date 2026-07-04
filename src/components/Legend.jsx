import useClimateStore from '../store/useClimateStore'

const GLASS = {
  background: 'rgba(10, 10, 20, 0.72)',
  backdropFilter: 'blur(12px)',
  WebkitBackdropFilter: 'blur(12px)',
  border: '1px solid rgba(255, 255, 255, 0.08)',
  borderRadius: 10,
}

const GRADIENT = 'linear-gradient(to bottom, #4EB3D3 0%, #A8D96B 25%, #F0C040 50%, #E07020 75%, #B01020 100%)'

// Matches the MapLibre CMIP6_COLOR_EXPR stops (hot at top, cold at bottom)
const CMIP6_GRADIENT = 'linear-gradient(to bottom, #a50026 0%, #d73027 15%, #f46d43 30%, #fdae61 45%, #fee090 60%, #abd9e9 75%, #74add1 88%, #4575b4 100%)'

const LAYER_META = {
  vulnerability: {
    label:  'Vulnerability',
    top:    'Low exposure',
    bottom: 'High exposure',
  },
  readiness: {
    label:  'Readiness',
    top:    'Highly ready',
    bottom: 'Not ready',
  },
  ndGain: {
    label:  'Adaptive Capacity',
    top:    'High capacity',
    bottom: 'Low capacity',
  },
}

function activeMeta(activeLayers) {
  const { readiness, vulnerability } = activeLayers
  if (readiness && vulnerability) return LAYER_META.ndGain
  if (vulnerability)              return LAYER_META.vulnerability
  if (readiness)                  return LAYER_META.readiness
  return null
}

export default function Legend() {
  const activeLayers = useClimateStore((s) => s.activeLayers)
  const meta = activeMeta(activeLayers)

  return (
    <div style={{
      position: 'fixed',
      bottom: 24,
      left: 20,
      zIndex: 100,
      display: 'flex',
      flexDirection: 'column',
      gap: 8,
      userSelect: 'none',
    }}>

      {/* CMIP6 temperature anomaly legend — shown when grid layer is on */}
      {activeLayers.cmip6Grid && (
        <div style={{
          ...GLASS,
          padding: '12px 14px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 6,
        }}>
          <div style={{
            fontSize: 10,
            color: 'rgba(255,255,255,0.4)',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            marginBottom: 2,
          }}>
            Temp anomaly (vs 1990)
          </div>

          <div style={{ display: 'flex', gap: 8, alignItems: 'stretch' }}>
            <div style={{ width: 10, height: 90, borderRadius: 5, background: CMIP6_GRADIENT, flexShrink: 0 }} />
            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: 90 }}>
              <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.55)', whiteSpace: 'nowrap' }}>5°C+</span>
              <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.35)', whiteSpace: 'nowrap' }}>2.5°C</span>
              <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.55)', whiteSpace: 'nowrap' }}>0°C</span>
            </div>
          </div>
        </div>
      )}

      {/* ND-GAIN legend — shown when readiness or vulnerability layer is on */}
      {meta && (
        <div style={{
          ...GLASS,
          padding: '12px 14px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 6,
        }}>
          <div style={{
            fontSize: 10,
            color: 'rgba(255,255,255,0.4)',
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            marginBottom: 2,
            transition: 'opacity 0.2s',
          }}>
            {meta.label}
          </div>

          <div style={{ display: 'flex', gap: 8, alignItems: 'stretch' }}>
            <div style={{
              width: 10,
              height: 120,
              borderRadius: 5,
              background: GRADIENT,
              flexShrink: 0,
            }} />
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              height: 120,
            }}>
              <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.55)', whiteSpace: 'nowrap' }}>
                {meta.top}
              </span>
              <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.35)', whiteSpace: 'nowrap' }}>
                50
              </span>
              <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.55)', whiteSpace: 'nowrap' }}>
                {meta.bottom}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
