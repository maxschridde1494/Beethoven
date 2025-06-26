import React, { useEffect, useRef } from 'react';
import Hls from 'hls.js';
import PredictionsOverlay from '../PredictionsOverlay';

interface LiveRtspPlayerProps {
  cameraId: string;
  hlsUrl: string;
  wsUrl: string;
}

const LiveRtspPlayer: React.FC<LiveRtspPlayerProps> = ({ cameraId, hlsUrl, wsUrl }) => {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    let hls: Hls;

    if (Hls.isSupported()) {
      hls = new Hls();
      hls.loadSource(hlsUrl);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.play();
      });
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = hlsUrl;
      video.addEventListener('loadedmetadata', () => {
        video.play();
      });
    }

    return () => {
      if (hls) {
        hls.destroy();
      }
    };
  }, [hlsUrl]);

  return (
    <div style={{ position: 'relative', width: '100%', height: 'auto' }}>
        <video ref={videoRef} controls autoPlay muted style={{ width: '100%', height: 'auto' }} />
        <PredictionsOverlay cameraId={cameraId} wsUrl={wsUrl} />
    </div>
  );
};

export default LiveRtspPlayer;