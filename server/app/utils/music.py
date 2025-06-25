def detections_to_events(detection):
    # events = [(secs, note_number, on_off)]  on_off: 1=on, 0=off

    # TODO: implement this
    events = [(0.00, 60, 1), (0.50, 60, 0), (0.50, 64, 1), (1.00, 64, 0)]
    return events