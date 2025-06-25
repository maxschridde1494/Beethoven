// import './App.css'

import Score from "./components/Score";
import { LiveRtspPlayer } from "./components/LiveRtspPlayer";

function App() {
  // const { 
  //   last10Detections, 
  //   last5Snapshots, 
  //   highConfidenceDetection,
  //   isLoading 
  // } = useRealTime('ws://localhost:8000/ws')

  return (
    <div style={{ width: "100%" }}>
      <div>
        Project Beethoven
      </div>
      <div style={{ width: "100%", display: "flex" }}>
        <div style={{ width: "50%" }}>
          <LiveRtspPlayer src="http://localhost:8888/edge-left/index.m3u8" />
        </div>
        <div style={{ width: "50%" }}>
          <LiveRtspPlayer src="http://localhost:8888/middle-left/index.m3u8" />
        </div>
      </div>
      <div style={{ width: "100%", display: "flex" }}>
        <div style={{ width: "50%" }}>
          <LiveRtspPlayer src="http://localhost:8888/middle-right/index.m3u8" />
        </div>
        <div style={{ width: "50%" }}>
          <LiveRtspPlayer src="http://localhost:8888/edge-right/index.m3u8" />
        </div>
      </div>
      <Score />
      {/* <ProjectTitle />
      <div className="detection-container">
        {isLoading ? (
          <div className="loading">Connecting to pet detection system...</div>
        ): (
          <>
            <CurrentLocation 
              detection={highConfidenceDetection}
              snapshotPath={last5Snapshots?.[0]}
            />
            <DetectionCarousel snapshots={last5Snapshots} />
            <DetectionLog detections={last10Detections} />
          </>
        )}
      </div> */}
    </div>
  )
}

export default App
