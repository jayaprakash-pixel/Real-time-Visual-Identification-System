"""
US-12: Detection history and reporting.

Reads the evidence log written by US-10 and lets you search it.

    python detection_history.py                      # all detections
    python detection_history.py --person MP001
    python detection_history.py --camera CAM01 --date 2026-10-06
"""

import argparse
import json
import os
import sys

AI_VISION_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(AI_VISION_DIR, "us-10"))

from evidence_capture import DEFAULT_EVIDENCE_DIR


def load_detections(evidence_dir=DEFAULT_EVIDENCE_DIR, person=None, camera=None, date=None):
    log_path = os.path.join(evidence_dir, "detections.jsonl")

    if not os.path.exists(log_path):
        return []

    records = []

    with open(log_path, encoding="utf-8") as log:
        for line in log:
            if not line.strip():
                continue

            record = json.loads(line)

            if person and person.lower() not in (record["person_id"].lower(), record["name"].lower()):
                continue
            if camera and record.get("camera_id") != camera:
                continue
            if date and not record["timestamp"].startswith(date):
                continue

            records.append(record)

    return records


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Review previous detections")
    parser.add_argument("--person", help="person ID or name")
    parser.add_argument("--camera", help="camera ID, e.g. CAM01")
    parser.add_argument("--date", help="YYYY-MM-DD")
    args = parser.parse_args()

    records = load_detections(person=args.person, camera=args.camera, date=args.date)

    print(f"{len(records)} detection(s)")
    print(f"{'Time':<20} {'ID':<8} {'Name':<20} {'Conf':>6}  {'Camera':<8} {'Zone':<14} Scene")

    for r in records:
        print(f"{r['timestamp']:<20} {r['person_id']:<8} {r['name'][:20]:<20} "
              f"{r['confidence_percent']:>5}%  {r.get('camera_id', ''):<8} "
              f"{r['location']['zone']:<14} {r['scene_image']}")
