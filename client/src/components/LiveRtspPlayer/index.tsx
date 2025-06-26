import { useEffect, useRef } from 'react';
import Hls from 'hls.js';
import PredictionsOverlay from '../PredictionsOverlay';

interface Props {
  cameraId: string;
  hlsUrl: string;
  wsUrl: string;
}

export function LiveRtspPlayer({ cameraId, hlsUrl, wsUrl }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    let hls: Hls | undefined;

    const safePlay = () =>
      video
        .play()
        .catch((err) => {
          // AbortError is expected when the component unmounts
          if (err.name !== 'AbortError') console.error(err);
        });

    // Common helper – wait until we *really* can play
    const onCanPlayOnce = () => {
      video.removeEventListener('canplay', onCanPlayOnce);
      safePlay();
    };

    if (Hls.isSupported()) {
      hls = new Hls({ enableWorker: true });

      hls.on(Hls.Events.ERROR, (event, data) => {
        if (data.fatal) {
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              console.error('Fatal network error encountered, trying to recover...', data);
              hls?.startLoad();
              break;
            case Hls.ErrorTypes.MEDIA_ERROR:
              console.error('Fatal media error encountered, trying to recover...', data);
              hls?.recoverMediaError();
              break;
            default:
              console.error('Unrecoverable fatal error, destroying HLS instance.', data);
              hls?.destroy();
              break;
          }
        }
      });

      hls.attachMedia(video);

      hls.on(Hls.Events.MEDIA_ATTACHED, () => {
        hls!.loadSource(hlsUrl);
      });

      // Attach canplay listener *before* we begin loading
      video.addEventListener('canplay', onCanPlayOnce);
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      // Safari / iOS
      video.src = hlsUrl;
      video.addEventListener('canplay', onCanPlayOnce);
    } else {
      console.error('HLS not supported in this browser');
    }

    return () => {
      hls?.destroy();
      video.pause();
      video.removeEventListener('canplay', onCanPlayOnce);
    };
  }, [hlsUrl]);

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <video
        ref={videoRef}
        muted
        playsInline
        controls
        style={{ width: '100%', height: 'auto', background: '#000' }}
      />
      <PredictionsOverlay cameraId={cameraId} wsUrl={wsUrl} />
    </div>
  );
}