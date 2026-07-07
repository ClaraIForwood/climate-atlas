import useClimateStore from '../store/useClimateStore'

const GLASS = {
  background: 'rgba(10, 10, 20, 0.72)',
  backdropFilter: 'blur(12px)',
  WebkitBackdropFilter: 'blur(12px)',
  border: '1px solid rgba(255, 255, 255, 0.08)',
  borderRadius: 10,
}

const GRADIENT = 'linear-gradient(to bottom, #4EB3D3 0%, #A8D96B 25%, #F0C040 50%, #E07020 75%, #B01020 100%)'

// Matches MapCanvas's CMIP6_COLOR_EXPR stops exactly (hot at top, cold at bottom),
// proportionally positioned across the [-1.0, 10.0] range.
const CMIP6_GRADIENT = 'linear-gradient(to bottom, #67001f 0%, #7a0021 14%, #920024 32%, #a50026 45%, #d73027 55%, #f46d43 64%, #fdae61 68%, #fee090 73%, #abd9e9 77%, #74add1 82%, #4575b4 91%, #313695 100%)'

// Matches MapCanvas's PRECIP_COLOR_EXPR stops (wetter/green at top, drier/brown at bottom)
const PRECIP_GRADIENT = 'linear-gradient(to bottom, #01665e 0%, #35978f 14%, #80cdc1 29%, #c7eae5 43%, #f5f5f5 57%, #dfc27d 71%, #bf812d 86%, #8c510a 100%)'

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
            <div style={{ position: 'relative', width: 10, height: 90, borderRadius: 5, background: CMIP6_GRADIENT, flexShrink: 0 }}>
              <span style={{
                position: 'absolute', right: '100%', marginRight: 4, top: '91%',
                transform: 'translateY(-50%)', fontSize: 8, color: 'rgba(255,255,255,0.35)', whiteSpace: 'nowrap',
              }}>0°C</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: 90 }}>
              <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.55)', whiteSpace: 'nowrap' }}>10°C+</span>
              <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.55)', whiteSpace: 'nowrap' }}>-1°C</span>
            </div>
          </div>

          <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.3)', textAlign: 'center', lineHeight: 1.4, maxWidth: 150, marginTop: 2 }}>
            Negative = single-run cooling vs 1990 baseline, not measurement error.
          </div>
        </div>
      )}

      {/* Precipitation change legend — shown when precip grid layer is on */}
      {activeLayers.precipGrid && (
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
            Precip change (vs 1990)
          </div>

          <div style={{ display: 'flex', gap: 8, alignItems: 'stretch' }}>
            <div style={{ position: 'relative', width: 10, height: 90, borderRadius: 5, background: PRECIP_GRADIENT, flexShrink: 0 }}>
              <span style={{
                position: 'absolute', right: '100%', marginRight: 4, top: '66.7%',
                transform: 'translateY(-50%)', fontSize: 8, color: 'rgba(255,255,255,0.35)', whiteSpace: 'nowrap',
              }}>0%</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: 90 }}>
              <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.55)', whiteSpace: 'nowrap' }}>+100%+</span>
              <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.55)', whiteSpace: 'nowrap' }}>-50%</span>
            </div>
          </div>

          <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.3)', textAlign: 'center', lineHeight: 1.4, maxWidth: 150, marginTop: 2 }}>
            Single-model (MRI-ESM2-0) estimate. Precipitation shows wider inter-model disagreement than temperature across CMIP6 generally.
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

      {/* Persistent model-attribution caption — always visible, regardless of active layer */}
      <div style={{ ...GLASS, padding: '8px 12px' }}>
        <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.35)', lineHeight: 1.4 }}>
          Data: MRI-ESM2-0 (one of ~30 CMIP6 models).
        </div>
      </div>
    </div>
  )
}
