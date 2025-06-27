import './App.css'
import { LiveRtspPlayer } from './components/LiveRtspPlayer'
import { useRealTime } from './hooks/useRealTime';
import InitialPredictions from './components/InitialPredictions';
import type { Detection } from './types';

function App() {
  const { initialPredictions, isLoading } = useRealTime('ws://localhost:8000/ws');

  if (isLoading) {
    return <div>Loading...</div>;
  }
  
  return (
    <div>
      <h1>Beethoven</h1>
      <div>
        <InitialPredictions predictions={initialPredictions as unknown as { [key: string]: Detection[] }} />
      </div>
      <div style={{ display: 'flex', flexDirection: 'row', gap: '10px' }}>
        <LiveRtspPlayer
          cameraId="middle-left"
          hlsUrl="http://localhost:8888/middle-left/index.m3u8"
          wsUrl="ws://localhost:8000/ws"
        />
        <LiveRtspPlayer
          cameraId="edge-left"
          hlsUrl="http://localhost:8888/edge-left/index.m3u8"
          wsUrl="ws://localhost:8000/ws"
        />
      </div>
    </div>
  )
}

export default App
