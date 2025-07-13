import { useEffect, useState } from "react";
import type { Detection, WebsocketConnectionInit } from '../types'

enum RealTimeMessage {
  ConnectionMade = 'connection_made',
  DetectionMade = 'detection_made',
  MusicTranscribed = 'music_transcribed',
  SheetUpdate = 'sheet_update',
}

interface ActiveNote {
  note_name: string;
  key_number: number;
  camera_id: string;
  start_time: string;
  duration: number;
}

interface CompletedNote {
  note_name: string;
  key_number: number;
  camera_id: string;
  start_time: string;
  end_time: string | null;
  duration: number | null;
}

interface TranscriptionData {
  musicxml?: string;
  completed_notes: CompletedNote[];
  active_notes_count: number;
  timestamp: string;
}

interface TranscriberStats {
  active_count: number;
  completed_count: number;
  buffer_seconds: number;
  bpm: number;
}

export const useRealTime = (url: string) => {
  const [isLoading, setIsLoading] = useState(true);
  const [relativePositions, setRelativePositions] = useState<{[cameraId: string]: Detection[]}>({});
  const [activeNotes, setActiveNotes] = useState<ActiveNote[]>([]);
  const [recentTranscriptions, setRecentTranscriptions] = useState<CompletedNote[]>([]);
  const [transcriptionStats, setTranscriptionStats] = useState<TranscriberStats | null>(null);
  const [musicXML, setMusicXML] = useState<string | null>(null);

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
          transcriber_stats: TranscriberStats;
          recent_transcriptions: CompletedNote[];
        };
        setRelativePositions(initData.relative_positions);
        setActiveNotes(initData.active_notes || []);
        setTranscriptionStats(initData.transcriber_stats || null);
        setRecentTranscriptions(initData.recent_transcriptions || []);
        setIsLoading(false);
      } else if (message === RealTimeMessage.DetectionMade) {
        // console.log('DetectionMade', data);
      } else if (message === RealTimeMessage.MusicTranscribed) {
        // console.log('MusicTranscribed', data);
        
        const transcriptionData: TranscriptionData = data.transcription;
        
        // Update recent transcriptions with new completed notes
        if (transcriptionData.completed_notes && transcriptionData.completed_notes.length > 0) {
          setRecentTranscriptions((prev: CompletedNote[]) => [
            ...prev,
            ...transcriptionData.completed_notes
          ].slice(-100)); // Keep only the last 100 transcriptions
        }
        
        // Update music XML if available
        if (transcriptionData.musicxml) {
          setMusicXML(transcriptionData.musicxml);
        }
      } else if (message === RealTimeMessage.SheetUpdate) {
        console.log('SheetUpdate', data);
        
        // Update music XML from sheet update
        if (data.xml) {
          setMusicXML(data.xml);
        }
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
    transcriptionStats,
    musicXML
  };
};