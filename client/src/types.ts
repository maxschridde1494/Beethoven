export interface Detection {
  id: number;
  detection_id: string;  // UUID
  timestamp: string;     // datetime
  model_id: string;
  camera_id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  confidence: number;
  class_name: string;
  class_id: number;
}

export interface Snapshot {
  asset_path: string;
}

export interface WebsocketConnectionInit {
  last_10_detections: Detection[];
  last_5_snapshots: string[];
}