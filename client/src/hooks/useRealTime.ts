import { useEffect, useState } from "react";
import type { Detection, Snapshot, WebsocketConnectionInit } from '../types'

enum RealTimeMessage {
  ConnectionMade = 'connection_made',
  DetectionMade = 'detection_made',
  // HighConfidenceDetectionMade = 'high_confidence_detection_made',
  // SnapshotMade = 'snapshot_made'
}

export const useRealTime = (url: string) => {
  const [last10Detections, setLast10Detections] = useState<Detection[]>([]);
  // const [last5Snapshots, setLast5Snapshots] = useState<Snapshot[]>([]);
  // const [highConfidenceDetection, setHighConfidenceDetection] = useState<Detection | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [initialPredictions, setInitialPredictions] = useState<{[cameraId: string]: Detection[]}>({});

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
        // setLast10Detections(initData.last_10_detections);
        // setLast5Snapshots(initData.last_5_snapshots);
        setInitialPredictions(initData.initial_predictions);
        setIsLoading(false);
      // } else if (message === RealTimeMessage.HighConfidenceDetectionMade) {
        // setHighConfidenceDetection(data as Detection);
      } else if (message === RealTimeMessage.DetectionMade) {
        console.log('DetectionMade', data);
        // setLast10Detections(prev => [data as Detection, ...prev.slice(0, 9)]);
      // } else if (message === RealTimeMessage.SnapshotMade) {
        // setLast5Snapshots(prev => [(data as {asset_path: string}).asset_path, ...prev.slice(0, 4)]);
      }
    };

    return () => {
      socket.close();
    };
  }, [url]);

  return { 
    last10Detections, 
    // last5Snapshots, 
    // highConfidenceDetection, 
    isLoading, 
    initialPredictions 
  };
};