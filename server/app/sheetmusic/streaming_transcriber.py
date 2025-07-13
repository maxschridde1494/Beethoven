"""
StreamingTranscriber for real-time music transcription from piano key detections.

This module processes detection events and maintains active notes to transcribe
music in real-time. It includes a background transcription loop that analyzes
note patterns and generates transcribed music events.
"""

import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from collections import defaultdict

from app.utils.logger import get_logger
from app.utils.signals import detection_made

logger = get_logger(__name__)


@dataclass
class ActiveNote:
    """Represents a currently active (pressed) note."""
    note_name: str
    key_number: int
    start_time: datetime
    confidence: float
    camera_id: str
    detection_count: int = 1
    last_seen: datetime = field(default_factory=datetime.now)


@dataclass
class TranscribedNote:
    """Represents a transcribed note with timing information."""
    note_name: str
    key_number: int
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None  # in seconds
    confidence: float = 0.0
    camera_id: str = ""


class StreamingTranscriber:
    """Real-time music transcriber that processes piano key detections."""
    
    def __init__(self, 
                 note_timeout: float = 2.0,
                 min_confidence: float = 0.5,
                 transcription_interval: float = 0.5):
        """
        Initialize the StreamingTranscriber.
        
        Args:
            note_timeout: Time in seconds after which a note is considered released
            min_confidence: Minimum confidence threshold for valid notes
            transcription_interval: Interval in seconds for background transcription loop
        """
        self.note_timeout = note_timeout
        self.min_confidence = min_confidence
        self.transcription_interval = transcription_interval
        
        # Active notes tracking
        self.active_notes: Dict[str, ActiveNote] = {}  # key: note_name
        self.lock = threading.Lock()
        
        # Transcription history
        self.transcribed_notes: List[TranscribedNote] = []
        self.note_history: List[ActiveNote] = []
        
        # Background loop control
        self.running = False
        self.background_thread: Optional[threading.Thread] = None
        
        # Statistics
        self.stats = {
            'total_detections': 0,
            'total_notes': 0,
            'active_count': 0,
            'last_update': datetime.now()
        }
        
    def start(self):
        """Start the background transcription loop."""
        if self.running:
            logger.warning("StreamingTranscriber already running")
            return
            
        self.running = True
        self.background_thread = threading.Thread(
            target=self.background_transcription_loop,
            daemon=True
        )
        self.background_thread.start()
        logger.info("StreamingTranscriber started")
        
    def stop(self):
        """Stop the background transcription loop."""
        self.running = False
        if self.background_thread and self.background_thread.is_alive():
            self.background_thread.join(timeout=5.0)
        logger.info("StreamingTranscriber stopped")
        
    def process_detections(self, detections: List[dict]) -> Dict[str, Any]:
        """
        Process a list of detection events and update active notes.
        
        Args:
            detections: List of detection dictionaries from detection_made signal
            
        Returns:
            Dictionary with processing results and statistics
        """
        if not detections:
            return self.get_stats()
            
        current_time = datetime.now()
        processed_count = 0
        new_notes = []
        updated_notes = []
        
        with self.lock:
            for detection in detections:
                try:
                    # Extract note information
                    note_name = detection.get('note_name')
                    key_number = detection.get('key_number')
                    confidence = detection.get('confidence', 0.0)
                    camera_id = detection.get('camera_id', '')
                    
                    # Skip if invalid note or low confidence
                    if not note_name or not key_number or confidence < self.min_confidence:
                        continue
                        
                    # Update or create active note
                    if note_name in self.active_notes:
                        # Update existing note
                        active_note = self.active_notes[note_name]
                        active_note.detection_count += 1
                        active_note.last_seen = current_time
                        active_note.confidence = max(active_note.confidence, confidence)
                        updated_notes.append(note_name)
                    else:
                        # Create new active note
                        active_note = ActiveNote(
                            note_name=note_name,
                            key_number=key_number,
                            start_time=current_time,
                            confidence=confidence,
                            camera_id=camera_id,
                            last_seen=current_time
                        )
                        self.active_notes[note_name] = active_note
                        new_notes.append(note_name)
                        logger.debug(f"New active note: {note_name} (key {key_number})")
                        
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"Error processing detection: {e}")
                    continue
                    
            # Update statistics
            self.stats['total_detections'] += len(detections)
            self.stats['active_count'] = len(self.active_notes)
            self.stats['last_update'] = current_time
            
        logger.debug(f"Processed {processed_count} detections, "
                    f"{len(new_notes)} new notes, {len(updated_notes)} updated notes")
                    
        return {
            'processed_count': processed_count,
            'new_notes': new_notes,
            'updated_notes': updated_notes,
            'active_notes_count': len(self.active_notes),
            'stats': self.stats
        }
        
    def background_transcription_loop(self):
        """
        Background loop that processes note timeouts and generates transcription events.
        
        This runs continuously and:
        - Removes notes that haven't been seen recently (note timeout)
        - Generates transcribed notes for completed note events
        - Analyzes patterns for music transcription
        """
        logger.info("Background transcription loop started")
        
        while self.running:
            try:
                current_time = datetime.now()
                timeout_threshold = current_time - timedelta(seconds=self.note_timeout)
                
                # Process note timeouts and generate transcribed notes
                transcribed_this_cycle = []
                
                with self.lock:
                    expired_notes = []
                    
                    # Find expired notes
                    for note_name, active_note in self.active_notes.items():
                        if active_note.last_seen < timeout_threshold:
                            expired_notes.append(note_name)
                            
                    # Process expired notes
                    for note_name in expired_notes:
                        active_note = self.active_notes.pop(note_name)
                        
                        # Create transcribed note
                        transcribed_note = TranscribedNote(
                            note_name=active_note.note_name,
                            key_number=active_note.key_number,
                            start_time=active_note.start_time,
                            end_time=active_note.last_seen,
                            duration=(active_note.last_seen - active_note.start_time).total_seconds(),
                            confidence=active_note.confidence,
                            camera_id=active_note.camera_id
                        )
                        
                        self.transcribed_notes.append(transcribed_note)
                        self.note_history.append(active_note)
                        transcribed_this_cycle.append(transcribed_note)
                        
                        logger.debug(f"Transcribed note: {note_name} "
                                   f"(duration: {transcribed_note.duration:.2f}s)")
                        
                    # Update stats
                    self.stats['total_notes'] += len(transcribed_this_cycle)
                    self.stats['active_count'] = len(self.active_notes)
                    
                # Emit transcription events if we have new transcribed notes
                if transcribed_this_cycle:
                    # Import here to avoid circular imports
                    from app.utils.signals import music_transcribed
                    
                    # Prepare transcription data
                    transcription_data = {
                        'transcribed_notes': [
                            {
                                'note_name': note.note_name,
                                'key_number': note.key_number,
                                'start_time': note.start_time.isoformat(),
                                'end_time': note.end_time.isoformat() if note.end_time else None,
                                'duration': note.duration,
                                'confidence': note.confidence,
                                'camera_id': note.camera_id
                            }
                            for note in transcribed_this_cycle
                        ],
                        'active_notes_count': len(self.active_notes),
                        'timestamp': current_time.isoformat(),
                        'stats': self.stats.copy()
                    }
                    
                    # Emit the music_transcribed signal
                    try:
                        # Since signals are synchronous, we need to handle this carefully
                        # For now, we'll use a simple approach
                        music_transcribed.send(
                            self,
                            transcription_data=transcription_data,
                            notes_count=len(transcribed_this_cycle)
                        )
                        logger.debug(f"Emitted music_transcribed signal with {len(transcribed_this_cycle)} notes")
                    except Exception as e:
                        logger.error(f"Error emitting music_transcribed signal: {e}")
                        
            except Exception as e:
                logger.error(f"Error in background transcription loop: {e}")
                
            # Wait before next cycle
            time.sleep(self.transcription_interval)
            
        logger.info("Background transcription loop stopped")
        
    def get_active_notes(self) -> List[dict]:
        """Get current active notes."""
        with self.lock:
            return [
                {
                    'note_name': note.note_name,
                    'key_number': note.key_number,
                    'start_time': note.start_time.isoformat(),
                    'confidence': note.confidence,
                    'camera_id': note.camera_id,
                    'detection_count': note.detection_count,
                    'duration': (datetime.now() - note.start_time).total_seconds()
                }
                for note in self.active_notes.values()
            ]
            
    def get_recent_transcriptions(self, limit: int = 50) -> List[dict]:
        """Get recent transcribed notes."""
        with self.lock:
            recent_notes = self.transcribed_notes[-limit:] if limit else self.transcribed_notes
            return [
                {
                    'note_name': note.note_name,
                    'key_number': note.key_number,
                    'start_time': note.start_time.isoformat(),
                    'end_time': note.end_time.isoformat() if note.end_time else None,
                    'duration': note.duration,
                    'confidence': note.confidence,
                    'camera_id': note.camera_id
                }
                for note in recent_notes
            ]
            
    def get_stats(self) -> Dict[str, Any]:
        """Get transcriber statistics."""
        with self.lock:
            return {
                'total_detections': self.stats['total_detections'],
                'total_notes': self.stats['total_notes'],
                'active_count': self.stats['active_count'],
                'transcribed_count': len(self.transcribed_notes),
                'last_update': self.stats['last_update'].isoformat(),
                'running': self.running
            }
            
    def clear_history(self):
        """Clear transcription history (useful for testing or reset)."""
        with self.lock:
            self.transcribed_notes.clear()
            self.note_history.clear()
            self.stats['total_notes'] = 0
            logger.info("Transcription history cleared")


# Global instance
_transcriber_instance: Optional[StreamingTranscriber] = None


def get_transcriber() -> StreamingTranscriber:
    """Get the global StreamingTranscriber instance."""
    global _transcriber_instance
    if _transcriber_instance is None:
        _transcriber_instance = StreamingTranscriber()
    return _transcriber_instance


def start_transcriber():
    """Start the global transcriber."""
    transcriber = get_transcriber()
    if not transcriber.running:
        transcriber.start()


def stop_transcriber():
    """Stop the global transcriber."""
    global _transcriber_instance
    if _transcriber_instance and _transcriber_instance.running:
        _transcriber_instance.stop()