"""
StreamingTranscriber for real-time music transcription from piano key detections.

This module processes detection events and maintains active notes to transcribe
music in real-time. It includes a background transcription loop that analyzes
note patterns and generates transcribed music events.
"""

import asyncio
from collections import deque, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from app.utils.logger import get_logger

from music21 import stream, note, meter, tempo

logger = get_logger(__name__)

@dataclass
class NoteEvent:
    note_name: str
    key_number: int
    camera_id: str
    start_time: datetime
    end_time: Optional[datetime] = None

    def duration_seconds(self):
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

class StreamingTranscriber:
    def __init__(self, buffer_seconds: float = 4.0, bpm: int = 120):
        self.buffer_seconds = buffer_seconds
        self.bpm = bpm
        self.detections: deque = deque()  # stores (timestamp, note_name, key_number, camera_id)
        self.active_notes: Dict[str, NoteEvent] = {}  # note_name -> NoteEvent
        self.completed_notes: List[NoteEvent] = []

    def ingest_detection(self, note_name: str, key_number: int, camera_id: str, timestamp: datetime):
        self.detections.append((timestamp, note_name, key_number, camera_id))
        self._prune_old_detections(timestamp)
        self._update_active_notes(timestamp)

    def _prune_old_detections(self, now: datetime):
        cutoff = now - timedelta(seconds=self.buffer_seconds)
        while self.detections and self.detections[0][0] < cutoff:
            self.detections.popleft()

    def _update_active_notes(self, now: datetime):
        # Count how many times each note appears in current buffer
        recent_notes = defaultdict(int)
        for _, note_name, _, _ in self.detections:
            recent_notes[note_name] += 1

        # Start new notes
        for _, note_name, key_number, camera_id in self.detections:
            if note_name not in self.active_notes:
                self.active_notes[note_name] = NoteEvent(
                    note_name=note_name,
                    key_number=key_number,
                    camera_id=camera_id,
                    start_time=now
                )

        # Finalize notes no longer detected
        to_finalize = []
        logger.info(f"Active notes: {self.active_notes}")
        logger.info(f"Recent notes: {recent_notes}")
        logger.info(f"Completed notes: {self.completed_notes}")
        for note_name in list(self.active_notes.keys()):
            if recent_notes[note_name] == 0:
                # If note hasn't appeared in recent buffer, finalize it
                self.active_notes[note_name].end_time = now
                self.completed_notes.append(self.active_notes[note_name])
                to_finalize.append(note_name)

        for name in to_finalize:
            del self.active_notes[name]

    def quantize_duration(self, duration_sec: float) -> float:
        beat_sec = 60 / self.bpm
        durations = [4, 2, 1, 0.5, 0.25]  # whole to 16th notes
        for d in durations:
            if abs(duration_sec - d * beat_sec) < 0.2 * beat_sec:
                return d
        return 0.25  # default to 16th

    def generate_musicxml(self) -> Optional[str]:
        if not self.completed_notes:
            logger.info("No completed notes to generate musicxml")
            return None

        s = stream.Score()
        treble = stream.Part()
        bass = stream.Part()

        treble.append(meter.TimeSignature('4/4'))
        bass.append(meter.TimeSignature('4/4'))
        treble.append(tempo.MetronomeMark(number=self.bpm))
        bass.append(tempo.MetronomeMark(number=self.bpm))

        for evt in self.completed_notes:
            duration = evt.duration_seconds()
            if duration is not None:
                dur = self.quantize_duration(duration)
                n = note.Note(evt.note_name)
                n.quarterLength = dur
                if evt.key_number < 60:
                    bass.append(n)
                else:
                    treble.append(n)

        s.insert(0, treble)
        s.insert(0, bass)
        return s.write('musicxml')  # returns filepath or str if buffer

    def reset(self):
        self.completed_notes.clear()


# Global instance for integration
_transcriber_instance: Optional[StreamingTranscriber] = None


def get_transcriber() -> StreamingTranscriber:
    """Get the global StreamingTranscriber instance."""
    global _transcriber_instance
    if _transcriber_instance is None:
        _transcriber_instance = StreamingTranscriber()
    return _transcriber_instance


# Example of background usage in FastAPI
async def background_transcription_loop(transcriber: StreamingTranscriber):
    logger.info("Starting background transcription loop")
    while True:
        await asyncio.sleep(1.0)
        xml = transcriber.generate_musicxml()
        if xml:
            # Import here to avoid circular imports
            from app.utils.signals import music_transcribed
            
            # Emit the music_transcribed signal
            try:
                transcription_data = {
                    'musicxml': xml,
                    'completed_notes': [
                        {
                            'note_name': evt.note_name,
                            'key_number': evt.key_number,
                            'camera_id': evt.camera_id,
                            'start_time': evt.start_time.isoformat(),
                            'end_time': evt.end_time.isoformat() if evt.end_time else None,
                            'duration': evt.duration_seconds()
                        }
                        for evt in transcriber.completed_notes
                    ],
                    'active_notes_count': len(transcriber.active_notes),
                    'timestamp': datetime.utcnow().isoformat()
                }

                logger.info(f"Emitting music_transcribed signal: {transcription_data}")
                
                music_transcribed.send(
                    transcriber,
                    transcription_data=transcription_data,
                    notes_count=len(transcriber.completed_notes)
                )
            except Exception as e:
                # Log error but don't break the loop
                print(f"Error emitting music_transcribed signal: {e}")
            
            transcriber.reset()
        else:
            logger.info("No musicxml generated")