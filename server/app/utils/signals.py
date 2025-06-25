"""
Signal definitions for the detection system.

This module defines all the signals (events) that can be emitted and subscribed to
in the detection system using blinker.
"""
from blinker import signal

# Detection events
detection_made = signal('detection.made')  # Emitted for any detection
high_confidence_detection_made = signal('detection.high_confidence')  # Emitted only for high confidence detections
snapshot_made = signal('snapshot.made')  # Emitted for any snapshot
notes_detected = signal('notes.detected')  # Emitted when musical notes are detected
musical_events_created = signal('music.events_created') # Emitted when musical events are created from detections