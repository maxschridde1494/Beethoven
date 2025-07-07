export interface Detection {
  id?: number;
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
  key_number?: number;
  note_name?: string;
}
export interface WebsocketConnectionInit {
  relative_positions: {[cameraId: string]: Detection[]};
}