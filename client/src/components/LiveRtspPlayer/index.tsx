import React, { useEffect, useRef } from 'react';
import Hls from 'hls.js';

/**
 * Props:
 *   src = full HLS URL, e.g. "http://host.docker.internal:8888/edge-right/index.m3u8"
 *   autoPlay = start immediately (default true)
 *   muted = start muted (Chrome blocks autoplay w/ sound)
 */
export function LiveRtspPlayer({
  src,
  autoPlay = true,
  muted = true,
}: {
  src: string;
  autoPlay?: boolean;
  muted?: boolean;
}) {
  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    if (!src) return;

    const video = videoRef.current!;
    let hls: Hls | undefined;

    // Safari (and iOS) can play HLS directly
    if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = src;
    } else if (Hls.isSupported()) {
      hls = new Hls({ enableWorker: true });
      hls.loadSource(src);
      hls.attachMedia(video);
    } else {
      console.error('This browser cannot play HLS or MediaSource');
    }

    return () => hls?.destroy();
  }, [src]);

  return (
    <video
      ref={videoRef}
      controls
      playsInline
      autoPlay={autoPlay}
      muted={muted}
      style={{ width: '100%', height: 'auto', background: '#000' }}
    />
  );
}