"""
US-10: Detection evidence capture.

For a confirmed match, saves:
  - the FULL camera frame with the matched person highlighted (scene context:
    surroundings, nearby people, direction of movement)
  - the aligned face crop (for side-by-side checking with the reference)
  - one JSON line in detections.jsonl with all detection details

The returned record is exactly what is handed to Member 3.
"""

import json
import os
import threading
from datetime import datetime

import cv2


AI_VISION_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_EVIDENCE_DIR = os.path.join(AI_VISION_DIR, "data", "evidence")


class EvidenceCapture:

    def __init__(self, evidence_dir=DEFAULT_EVIDENCE_DIR):
        self.evidence_dir = os.path.abspath(evidence_dir)
        self.log_path = os.path.join(evidence_dir, "detections.jsonl")
        self.lock = threading.Lock()
        os.makedirs(evidence_dir, exist_ok=True)

    def capture(self, frame, aligned_face, details):
        """
        frame:        original (un-annotated) camera frame
        aligned_face: 112x112 aligned face or None
        details:      dict with person_id, name, confidence, camera_id,
                      track_id, location (US-09) ...

        Returns the stored detection record.
        """
        now = datetime.now()
        day_dir = os.path.join(self.evidence_dir, now.strftime("%Y-%m-%d"))
        os.makedirs(day_dir, exist_ok=True)

        safe_person = "".join(c for c in details["person_id"] if c.isalnum() or c in "-_")
        stem = f"{now.strftime('%H%M%S_%f')}_{safe_person}_{details.get('camera_id', 'CAM')}"

        scene = frame.copy()
        x, y, w, h = details["location"]["bbox"]
        label = f"{details['name']} ({details['confidence_percent']}%)"

        cv2.rectangle(scene, (x, y), (x + w, y + h), (0, 0, 255), 3)
        cv2.putText(scene, label, (x, max(25, y - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(scene, f"{details.get('camera_id', '')}  {now:%Y-%m-%d %H:%M:%S}",
                    (10, scene.shape[0] - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        scene_path = os.path.join(day_dir, stem + "_scene.jpg")
        cv2.imwrite(scene_path, scene)

        face_path = None
        if aligned_face is not None:
            face_path = os.path.join(day_dir, stem + "_face.jpg")
            cv2.imwrite(face_path, aligned_face)

        record = {
            **details,
            "match": True,
            "timestamp": now.isoformat(timespec="seconds"),
            "scene_image": scene_path,
            "face_image": face_path,
        }

        with self.lock:
            with open(self.log_path, "a", encoding="utf-8") as log:
                log.write(json.dumps(record) + "\n")

        return record
