import { useEffect, useState } from "react";
import type { Detection, WebsocketConnectionInit } from '../types'

enum RealTimeMessage {
  ConnectionMade = 'connection_made',
  DetectionMade = 'detection_made',
  MusicTranscribed = 'music_transcribed',
}

interface ActiveNote {
  note_name: string;
  key_number: number;
  start_time: string;
  confidence: number;
  camera_id: string;
  detection_count: number;
  duration: number;
}

interface TranscribedNote {
  note_name: string;
  key_number: number;
  start_time: string;
  end_time: string | null;
  duration: number | null;
  confidence: number;
  camera_id: string;
}

interface TranscriptionData {
  transcribed_notes: TranscribedNote[];
  active_notes_count: number;
  timestamp: string;
  stats: {
    total_detections: number;
    total_notes: number;
    active_count: number;
    transcribed_count: number;
    last_update: string;
    running: boolean;
  };
}

export const useRealTime = (url: string) => {
  const [isLoading, setIsLoading] = useState(true);
  const [relativePositions, setRelativePositions] = useState<{[cameraId: string]: Detection[]}>({});
  const [activeNotes, setActiveNotes] = useState<ActiveNote[]>([]);
  const [recentTranscriptions, setRecentTranscriptions] = useState<TranscribedNote[]>([]);
  const [transcriptionStats, setTranscriptionStats] = useState<TranscriptionData['stats'] | null>(null);

  useEffect(() => {
    const socket = new WebSocket(url);

    socket.onopen = () => console.log('WebSocket connected');
    socket.onclose = () => console.log('WebSocket disconnected');
    socket.onerror = (err) => console.error('WebSocket error:', err);

    socket.onmessage = (event) => {
      const response = JSON.parse(event.data);
      const { message, data } = response;

      if (message === RealTimeMessage.ConnectionMade) {
        const initData = data as WebsocketConnectionInit & {
          active_notes: ActiveNote[];
          transcriber_stats: TranscriptionData['stats'];
          recent_transcriptions: TranscribedNote[];
        };
        setRelativePositions(initData.relative_positions);
        setActiveNotes(initData.active_notes || []);
        setTranscriptionStats(initData.transcriber_stats || null);
        setRecentTranscriptions(initData.recent_transcriptions || []);
        setIsLoading(false);
      } else if (message === RealTimeMessage.DetectionMade) {
        console.log('DetectionMade', data);
      } else if (message === RealTimeMessage.MusicTranscribed) {
        console.log('MusicTranscribed', data);
        
        const transcriptionData: TranscriptionData = data.transcription;
        
        // Update recent transcriptions with new notes
        if (transcriptionData.transcribed_notes && transcriptionData.transcribed_notes.length > 0) {
          setRecentTranscriptions((prev: TranscribedNote[]) => [
            ...prev,
            ...transcriptionData.transcribed_notes
          ].slice(-100)); // Keep only the last 100 transcriptions
        }
        
        // Update stats
        if (transcriptionData.stats) {
          setTranscriptionStats(transcriptionData.stats);
        }
        
        // Note: Active notes are updated in real-time through the transcriber
        // We could fetch them if needed, but they're more efficiently updated server-side
      }
    };

    return () => {
      socket.close();
    };
  }, [url]);

  return { 
    isLoading, 
    relativePositions,
    activeNotes,
    recentTranscriptions,
    transcriptionStats
  };
};