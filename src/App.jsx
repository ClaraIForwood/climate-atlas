import MapCanvas from './components/MapCanvas'
import ControlPanel from './components/ControlPanel'
import Legend from './components/Legend'
import InfoPanel from './components/InfoPanel'
import { useUrlState } from './hooks/useUrlState'

export default function App() {
  useUrlState()

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <MapCanvas />
      <ControlPanel />
      <Legend />
      <InfoPanel />
    </div>
  )
}
