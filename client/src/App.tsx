import './App.css'
import LiveRtspPlayer from './components/LiveRtspPlayer'

function App() {

  return (
    <>
      <h1>Beethoven</h1>
      <div className="card">
        <LiveRtspPlayer
          cameraId="edge-right"
          hlsUrl="http://localhost:8888/edge-right/index.m3u8"
          wsUrl="ws://localhost:8000/ws/predictions"
        />
      </div>
    </>
  )
}

export default App
