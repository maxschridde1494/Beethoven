import { useEffect, useState } from "react";
import type { Detection, Snapshot, WebsocketConnectionInit } from '../types'

export enum RealTimeMessage {
  DetectionMade = 'detection_made',
  HighConfidenceDetectionMade = 'high_confidence_detection_made',
  SnapshotMade = 'snapshot_made',
  ConnectionMade = 'connection_made'
}

interface RealTimeUpdate {
  timestamp: string;
  status: string;
  message: RealTimeMessage;
  data?: Detection | Snapshot | WebsocketConnectionInit;
}

interface RealTimeState {
  last10Detections: Detection[]
  last5Snapshots: string[]
  highConfidenceDetection?: Detection
  isLoading: boolean
}

export function useRealTime(uri: string): RealTimeState {
  const [last10Detections, setLast10Detections] = useState<Detection[]>([])
  const [last5Snapshots, setLast5Snapshots] = useState<string[]>([])
  const [highConfidenceDetection, setHighConfidenceDetection] = useState<Detection>()
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const ws = new WebSocket(uri);

    ws.onmessage = (ev) => {
      const realTimeUpdate = JSON.parse(ev.data) as RealTimeUpdate
      const { data, message } = realTimeUpdate
      if (!data) return

      switch (message) {
        case RealTimeMessage.ConnectionMade:
          const initData = data as WebsocketConnectionInit
          setLast10Detections(initData.last_10_detections)
          setLast5Snapshots(initData.last_5_snapshots)
          setIsLoading(false)
          break
        case RealTimeMessage.DetectionMade:
          setLast10Detections(prev => [(data as Detection), ...prev].slice(0, 10))
          break
        case RealTimeMessage.HighConfidenceDetectionMade:
          setHighConfidenceDetection(data as Detection)
          break
        case RealTimeMessage.SnapshotMade:
          setLast5Snapshots(prev => [(data as Snapshot).asset_path, ...prev].slice(0, 5))
          break
      }
    }

    return () => ws.close();
  }, [uri]);

  return {
    last10Detections,
    last5Snapshots,
    highConfidenceDetection,
    isLoading
  }
}