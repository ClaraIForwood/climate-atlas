import useClimateStore from '../store/useClimateStore'
import { formatYear } from '../utils/formatters'

const MIN_YEAR = 2024
const MAX_YEAR = 2080
const TICKS = [2030, 2040, 2050, 2060, 2070, 2080]

export default function YearSlider() {
  const activeYear = useClimateStore((s) => s.activeYear)
  const setActiveYear = useClimateStore((s) => s.setActiveYear)

  const pct = ((activeYear - MIN_YEAR) / (MAX_YEAR - MIN_YEAR)) * 100

  return (
    <div style={{ width: '100%' }}>
      {/* Year label */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 }}>
        <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
          Year
        </span>
        <span style={{
          fontSize: 26,
          fontWeight: 700,
          color: '#4EB3D3',
          letterSpacing: '-0.02em',
          lineHeight: 1,
          fontVariantNumeric: 'tabular-nums',
        }}>
          {formatYear(activeYear)}
        </span>
      </div>

      {/* Slider track with gradient fill */}
      <div style={{ position: 'relative', paddingBottom: 18 }}>
        <div style={{
          position: 'absolute',
          top: 8,
          left: 0,
          width: `${pct}%`,
          height: 4,
          borderRadius: 2,
          background: 'linear-gradient(90deg, #B01020, #E07020, #F0C040, #A8D96B, #4EB3D3)',
          backgroundSize: `${100 / (pct / 100 || 0.01)}% 100%`,
          backgroundPosition: '0 0',
          pointerEvents: 'none',
          zIndex: 1,
        }} />
        <input
          type="range"
          min={MIN_YEAR}
          max={MAX_YEAR}
          step={1}
          value={activeYear}
          onChange={(e) => setActiveYear(Number(e.target.value))}
          style={{ width: '100%', position: 'relative', zIndex: 2 }}
          aria-label="Projection year"
        />

        {/* Tick marks */}
        <div style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          display: 'flex',
          justifyContent: 'space-between',
          pointerEvents: 'none',
        }}>
          {TICKS.map((yr) => {
            const pos = ((yr - MIN_YEAR) / (MAX_YEAR - MIN_YEAR)) * 100
            return (
              <div
                key={yr}
                style={{
                  position: 'absolute',
                  left: `${pos}%`,
                  transform: 'translateX(-50%)',
                  fontSize: 9,
                  color: 'rgba(255,255,255,0.35)',
                  letterSpacing: '0.04em',
                  fontVariantNumeric: 'tabular-nums',
                }}
              >
                {yr}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
