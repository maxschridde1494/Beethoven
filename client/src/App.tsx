import './App.css'
import { LiveRtspPlayer } from './components/LiveRtspPlayer'
import { useRealTime } from './hooks/useRealTime';
import InitialPredictions from './components/InitialPredictions';
import type { Prediction } from './types';

function App() {
  const { initialPredictions } = useRealTime('ws://localhost:8000/ws');

  if (Object.keys(initialPredictions).length === 0) {
    return <div>Loading...</div>;
  }
  
  return (
    <div>
      <h1>Beethoven</h1>
      <div>
        <InitialPredictions predictions={initialPredictions as unknown as { [key: string]: Prediction[] }} />
      </div>
      <div style={{ display: 'flex', flexDirection: 'row', gap: '10px' }}>
        <LiveRtspPlayer
          cameraId="middle-left"
          hlsUrl="http://localhost:8888/middle-left/index.m3u8"
          wsUrl="ws://localhost:8000/ws/predictions"
        />
        <LiveRtspPlayer
          cameraId="edge-left"
          hlsUrl="http://localhost:8888/edge-left/index.m3u8"
          wsUrl="ws://localhost:8000/ws/predictions"
        />
      </div>
    </div>
  )
}

export default App
