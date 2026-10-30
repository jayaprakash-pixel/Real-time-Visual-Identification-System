import math


class FaceTracker:
    def __init__(self, max_distance=80, max_missed_frames=10):
        self.next_track_id = 1
        self.tracks = {}

        self.max_distance = max_distance
        self.max_missed_frames = max_missed_frames

    def _get_center(self, bbox):
        x, y, w, h = bbox
        center_x = x + w // 2
        center_y = y + h // 2
        return (center_x, center_y)

    def _calculate_distance(self, point1, point2):
        return math.sqrt(
            (point1[0] - point2[0]) ** 2 +
            (point1[1] - point2[1]) ** 2
        )

    def update(self, detections):
        """
        Update tracker using the faces detected in the current frame.

        detections:
            List of bounding boxes.
            Each bounding box is:
            (x, y, width, height)

        Returns:
            List of dictionaries containing:
            {
                "track_id": int,
                "bbox": tuple,
                "center": tuple,
                "detection_index": int   # position in `detections`
            }
        """

        detection_centers = [
            self._get_center(bbox)
            for bbox in detections
        ]

        # Every (track, detection) pair that is close enough,
        # nearest pairs first. Assigning globally (instead of
        # detection by detection) stops one face "stealing" the
        # track of a neighbouring face that is actually closer to it.
        pairs = sorted(
            (self._calculate_distance(center, track["center"]), track_id, index)
            for track_id, track in self.tracks.items()
            for index, center in enumerate(detection_centers)
        )

        assigned = {}  # detection index -> track id
        matched_tracks = set()

        for distance, track_id, index in pairs:

            if distance > self.max_distance:
                break

            if track_id in matched_tracks or index in assigned:
                continue

            assigned[index] = track_id
            matched_tracks.add(track_id)

        current_tracks = []

        for index, (bbox, center) in enumerate(zip(detections, detection_centers)):

            # No existing track matched -> new track
            if index not in assigned:
                assigned[index] = self.next_track_id
                self.next_track_id += 1

            track_id = assigned[index]

            self.tracks[track_id] = {
                "bbox": bbox,
                "center": center,
                "missed": 0
            }

            current_tracks.append({
                "track_id": track_id,
                "bbox": bbox,
                "center": center,
                "detection_index": index
            })

        # Increase missed count for tracks that were
        # not detected in the current frame.
        seen = set(assigned.values())

        for track_id in list(self.tracks.keys()):

            if track_id not in seen:

                self.tracks[track_id]["missed"] += 1

                if self.tracks[track_id]["missed"] > self.max_missed_frames:
                    del self.tracks[track_id]

        return current_tracks

    def active_ids(self):
        """Track IDs still alive (seen recently). Used to clean up per-track state."""
        return set(self.tracks.keys())


if __name__ == "__main__":
    tracker = FaceTracker(max_distance=80, max_missed_frames=2)

    # Track 1 centre x=100, track 2 centre x=200
    a, b = tracker.update([(75, 100, 50, 50), (175, 100, 50, 50)])
    assert (a["track_id"], b["track_id"]) == (1, 2)

    # Face 1 moves right to x=160, face 2 to x=210. Detection-order greedy
    # gives detection 0 track 2 (40 px < 60 px), then detection 1 is 110 px
    # from track 1 -> wrongly a NEW track. Global nearest-pair keeps 1 and 2.
    a, b = tracker.update([(135, 100, 50, 50), (185, 100, 50, 50)])
    assert (a["track_id"], b["track_id"]) == (1, 2), (a, b)
    assert (a["detection_index"], b["detection_index"]) == (0, 1)

    # Far-away face -> new track; lost tracks expire after max_missed_frames
    (c,) = tracker.update([(500, 400, 50, 50)])
    assert c["track_id"] == 3
    tracker.update([])
    tracker.update([])
    assert tracker.active_ids() == {3}

    print("US-03 face tracker: all checks passed")
