class SelectiveRecognition:
    def __init__(self, recognition_interval=10):
        self.recognition_interval = recognition_interval
        self.track_frames = {}

    def should_recognize(self, track_id, interval=None):
        """
        interval: optional override, e.g. a shorter interval while a
        possible match is being verified (US-08) so confirmation is fast.
        """
        interval = interval or self.recognition_interval

        if track_id not in self.track_frames:
            self.track_frames[track_id] = 0
            return True

        self.track_frames[track_id] += 1

        if self.track_frames[track_id] >= interval:
            self.track_frames[track_id] = 0
            return True

        return False

    def remove_track(self, track_id):
        self.track_frames.pop(track_id, None)

    def retain(self, active_track_ids):
        """Forget tracks the tracker has dropped."""
        for track_id in list(self.track_frames):
            if track_id not in active_track_ids:
                self.remove_track(track_id)
