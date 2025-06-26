import './App.css'
import LiveRtspPlayer from './components/LiveRtspPlayer'
import { useRealTime } from './hooks/useRealTime';
import InitialPredictions from './components/InitialPredictions';
import type { Prediction } from './types';

function App() {
  const { initialPredictions } = useRealTime('ws://localhost:8000/ws');
  
  return (
    <div>
      <h1>Beethoven</h1>
      <div>
        <InitialPredictions predictions={initialPredictions as unknown as { [key: string]: Prediction[] }} />
      </div>
      <div className="card">
        <LiveRtspPlayer
          cameraId="edge-right"
          hlsUrl="http://localhost:8888/edge-right/index.m3u8"
          wsUrl="ws://localhost:8000/ws/predictions"
        />
      </div>
    </div>
  )
}

export default App
