"""
StreamingTranscriber for real-time music transcription from piano key detections.

This module processes detection events and maintains active notes to transcribe
music in real-time. It includes a background transcription loop that analyzes
note patterns and generates transcribed music events.
"""

import asyncio
import threading
import time
from collections import deque, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from app.utils.logger import get_logger

from music21 import stream, note, meter, tempo, converter

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
    def __init__(self, buffer_seconds: float = 4.0, bpm: int = 120, interval: float = 1.0):
        self.buffer_seconds = buffer_seconds
        self.bpm = bpm
        self.detections: deque = deque()  # stores (timestamp, note_name, key_number, camera_id)
        self.active_notes: Dict[str, NoteEvent] = {}  # note_name -> NoteEvent
        self.completed_notes: List[NoteEvent] = []

        self.interval = interval
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def start(self, loop: asyncio.AbstractEventLoop):
        """Start the transcriber thread."""
        if self.running:
            logger.warning("Transcriber already running")
            return
            
        self.loop = loop
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        logger.info("StreamingTranscriber started")

    def stop(self) -> None:
        """Stop the transcriber thread."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
        logger.info("StreamingTranscriber stopped")

    def ingest_detection(self, note_name: str, key_number: int, camera_id: str, timestamp: datetime):
        self.detections.append((timestamp, note_name, key_number, camera_id))
        self._prune_old_detections(timestamp)
        self._update_active_notes(timestamp)

    def _prune_old_detections(self, now: datetime):
        cutoff = now - timedelta(seconds=self.buffer_seconds)
        while self.detections and self.detections[0][0] < cutoff:
            self.detections.popleft()

    def _update_active_notes(self, now: datetime):
        # Start new notes by checking against the current detection buffer
        for ts, note_name, key_number, camera_id in self.detections:
            if note_name not in self.active_notes:
                self.active_notes[note_name] = NoteEvent(
                    note_name=note_name,
                    key_number=key_number,
                    camera_id=camera_id,
                    start_time=ts 
                )
        
        # Finalize notes that have not been seen recently
        to_finalize = []
        timeout = timedelta(seconds=0.2)

        for note_name, note_event in list(self.active_notes.items()):
            last_seen_timestamp = None
            for detection_time, dn, _, _ in reversed(self.detections):
                if dn == note_name:
                    last_seen_timestamp = detection_time
                    break

            # Finalize if timed out or no longer in detections
            if last_seen_timestamp is None or (now - last_seen_timestamp) > timeout:
                note_event.end_time = last_seen_timestamp or now
                self.completed_notes.append(note_event)
                to_finalize.append(note_name)

        for name in to_finalize:
            if name in self.active_notes:
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

        has_notes = False
        for evt in self.completed_notes:
            duration = evt.duration_seconds()
            if duration is not None and duration > 0:
                has_notes = True
                dur = self.quantize_duration(duration)
                n = note.Note(evt.note_name)
                n.quarterLength = dur
                if evt.key_number < 60:
                    bass.append(n)
                else:
                    treble.append(n)

        if not has_notes:
            logger.info("No notes with duration to generate musicxml")
            return None

        s.insert(0, treble)
        s.insert(0, bass)

        # After constructing the music21 Score `s`:
        xml_str = converter.toData(s, fmt='musicxml')
        # If xml_str is bytes, decode it:
        if isinstance(xml_str, bytes):
            xml_str = xml_str.decode('utf-8')
        
        # xml_bytes = converter.freeze(s, fmt='musicxml')
        # return xml_bytes.decode('utf-8')
        return xml_str

    def reset(self):
        self.completed_notes.clear()

    async def _emit_transcription_signal(self, xml: str):
        """Coroutine to emit the music_transcribed signal."""
        # Import here to avoid circular imports
        from app.utils.signals import music_transcribed
        
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
                for evt in self.completed_notes
            ],
            'active_notes_count': len(self.active_notes),
            'timestamp': datetime.utcnow().isoformat()
        }

        logger.info(f"Emitting music_transcribed signal")
        
        await music_transcribed.send_async(
            self,
            transcription_data=transcription_data,
            notes_count=len(self.completed_notes)
        )

    def _loop(self) -> None:
        """Main transcription loop."""
        logger.info("Starting background transcription loop")
        
        while self.running:
            xml = self.generate_musicxml()
            if xml:
                assert self.loop is not None
                coro = self._emit_transcription_signal(xml)
                asyncio.run_coroutine_threadsafe(coro, self.loop)
                self.reset()
            else:
                logger.info("No musicxml generated")

            time.sleep(self.interval)

# Global instance for integration
_transcriber_instance: Optional[StreamingTranscriber] = None


def get_transcriber() -> StreamingTranscriber:
    """Get the global StreamingTranscriber instance."""
    global _transcriber_instance
    if _transcriber_instance is None:
        _transcriber_instance = StreamingTranscriber()
    return _transcriber_instance