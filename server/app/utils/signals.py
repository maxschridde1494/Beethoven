"""
Signal definitions for the detection system.

This module defines all the signals (events) that can be emitted and subscribed to
in the detection system using blinker.
"""
from blinker import signal

# Detection events
detection_made = signal('detection.made')
musical_events_created = signal('music.events_created')