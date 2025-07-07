import { useEffect, useState } from "react";
import type { Detection, WebsocketConnectionInit } from '../types'

enum RealTimeMessage {
  ConnectionMade = 'connection_made',
  DetectionMade = 'detection_made',
}

export const useRealTime = (url: string) => {
  const [isLoading, setIsLoading] = useState(true);
  const [relativePositions, setRelativePositions] = useState<{[cameraId: string]: Detection[]}>({});

  useEffect(() => {
    const socket = new WebSocket(url);

    socket.onopen = () => console.log('WebSocket connected');
    socket.onclose = () => console.log('WebSocket disconnected');
    socket.onerror = (err) => console.error('WebSocket error:', err);

    socket.onmessage = (event) => {
      const response = JSON.parse(event.data);
      const { message, data } = response;

      if (message === RealTimeMessage.ConnectionMade) {
        const initData = data as WebsocketConnectionInit;
        setRelativePositions(initData.relative_positions);
        setIsLoading(false);
      } else if (message === RealTimeMessage.DetectionMade) {
        console.log('DetectionMade', data);
      }
    };

    return () => {
      socket.close();
    };
  }, [url]);

  return { 
    isLoading, 
    relativePositions 
  };
};