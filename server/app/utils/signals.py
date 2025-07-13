"""
Signal definitions for the detection system.

This module defines all the signals (events) that can be emitted and subscribed to
in the detection system using blinker.
"""
from blinker import signal

# Detection events
detection_made = signal('detection.made')

# Music transcription events
music_transcribed = signal('music.transcribed')