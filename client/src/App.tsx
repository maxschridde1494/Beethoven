import './App.css'
import ColorKey from './components/ColorKey'
import { LiveRtspPlayer } from './components/LiveRtspPlayer'
import { CLASS_COLORS } from './utils/colorUtils'
import { useRealTime } from './hooks/useRealTime';
import RelativePositions from './components/RelativePositions';
import type { Detection } from './types';

function App() {
  const { relativePositions, isLoading } = useRealTime('ws://localhost:8000/ws');

  // if (isLoading) {
  //   return <div>Loading...</div>;
  // }
  
  return (
    <div>
      <h1 style={{ margin: 0, padding: 0 }}>Beethoven</h1>
      <div style={{ paddingBottom: '10px', width: '20%' }}>
        <RelativePositions positions={relativePositions as unknown as { [key: string]: Detection[] }} />
        <ColorKey colorMap={CLASS_COLORS} />
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
