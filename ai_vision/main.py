"""
AI Vision & Recognition module - full live pipeline (US-01 .. US-12).

    Camera (webcam / phone stream / video file)
      -> US-01 latest-frame buffer (camera thread)
      -> US-02 YuNet detection
      -> US-03 face tracking (track IDs)
      -> US-04 quality check + selective recognition
      -> US-02 alignment + SFace embedding
      -> US-06 compare with US-05 reference embeddings
      -> US-07 threshold decision
      -> US-08 multi-frame verification per track
      -> US-09 localisation  -> US-10 evidence capture
      -> US-11 on_match(result)  ==> Member 3 (alerts / dashboard)
      -> US-12 history: us-12/detection_history.py

Run:
    python main.py                                   # laptop webcam
    python main.py --source http://192.168.1.5:8080/video --camera-id CAM02
    python main.py --source clip.mp4 --no-display

Register people first:
    python us-05/reference_store.py add MP001 "Rahul Kumar" rahul.jpg

Member 3 integration:
    from main import AIVisionPipeline
    AIVisionPipeline(source=0, on_match=my_alert_function).run()
"""

import argparse
import os
import sys
import threading
import time

import cv2

AI_VISION_DIR = os.path.dirname(os.path.abspath(__file__))
for story in ("us-01", "us-02", "us-03", "us-04", "us-05", "us-06",
              "us-07", "us-08", "us-09", "us-10"):
    sys.path.append(os.path.join(AI_VISION_DIR, story))

from camera_source import open_camera, parse_source, read_frame, release_camera
from frame_buffer import LatestFrameBuffer
from face_engine import FaceEngine
from face_tracker import FaceTracker
from face_quality import check_face_quality
from selective_recognition import SelectiveRecognition
from reference_store import ReferenceStore, DEFAULT_STORE
from face_matcher import compare
from match_decision import SFACE_COSINE_THRESHOLD, confidence_percent, decide
from match_verifier import MatchVerifier
from face_localization import locate_face
from evidence_capture import EvidenceCapture, DEFAULT_EVIDENCE_DIR


GREEN = (0, 200, 0)
ORANGE = (0, 165, 255)
RED = (0, 0, 255)
WHITE = (255, 255, 255)


def print_match(result):
    """Default US-11 notification: console. Member 3 replaces this with real alerts."""
    print()
    print("=" * 50)
    print("  MATCH FOUND")
    print(f"  Name       : {result['name']} ({result['person_id']})")
    print(f"  Confidence : {result['confidence_percent']}%  (cosine {result['confidence']:.3f})")
    print(f"  Time       : {result['timestamp']}")
    print(f"  Camera     : {result['camera_id']}  zone: {result['location']['zone']}")
    print(f"  Scene      : {result['scene_image']}")
    print("=" * 50)


class AIVisionPipeline:

    def __init__(self, source=0, camera_id="CAM01", on_match=print_match,
                 threshold=SFACE_COSINE_THRESHOLD, store_path=DEFAULT_STORE,
                 evidence_dir=DEFAULT_EVIDENCE_DIR, recognition_interval=10,
                 alert_cooldown=30.0, on_frame=None):
        self.source = parse_source(source)
        self.camera_id = camera_id
        self.on_match = on_match
        self.threshold = threshold
        self.alert_cooldown = alert_cooldown
        self.on_frame = on_frame    # optional: called with each annotated frame (the server streams it)

        self.engine = FaceEngine()
        self.store = ReferenceStore(store_path, engine=self.engine)
        self.tracker = FaceTracker(max_distance=80, max_missed_frames=10)
        self.selective = SelectiveRecognition(recognition_interval)
        self.verifier = MatchVerifier(min_mean_score=max(threshold, 0.40))
        self.evidence = EvidenceCapture(evidence_dir)

        self.buffer = LatestFrameBuffer()
        self.stop_event = threading.Event()
        self.last_alert = {}        # person_id -> time of last alert
        self.banner = None          # (text, until_time) shown on the preview
        self.last_scores = {}       # track_id -> latest best (person_id, score) for display

        if len(self.store) == 0:
            print("Warning: no missing persons registered (us-05/reference_store.py add ...)")

    # ---------------------------------------------------------
    # US-01: camera thread -> latest-frame buffer
    # ---------------------------------------------------------

    def _camera_loop(self):
        is_file = isinstance(self.source, str) and os.path.isfile(self.source)
        camera = None
        frame_number = 0

        try:
            camera = open_camera(self.source)
            frame_delay = 1.0 / (camera.get(cv2.CAP_PROP_FPS) or 30) if is_file else 0

            while not self.stop_event.is_set():
                frame = read_frame(camera)

                if frame is None:
                    if is_file:
                        break

                    # Phone/CCTV stream dropped: keep trying to reconnect.
                    print("Camera stream lost, reconnecting...")
                    release_camera(camera)
                    time.sleep(2)
                    try:
                        camera = open_camera(self.source)
                    except RuntimeError:
                        pass   # read() on a closed capture returns None -> retry
                    continue

                frame_number += 1
                self.buffer.update((frame_number, frame, time.perf_counter()))

                if frame_delay:
                    time.sleep(frame_delay)   # play files at real speed
        except RuntimeError as error:
            print(error)
        finally:
            if camera is not None:
                release_camera(camera)
            self.camera_done = True

    # ---------------------------------------------------------
    # US-02 .. US-11 on one frame
    # ---------------------------------------------------------

    def process(self, frame):
        """Runs recognition on one frame. Returns list of tracks with display info."""
        faces = self.engine.detect(frame)
        tracks = self.tracker.update([face["bbox"] for face in faces])

        active = self.tracker.active_ids()
        self.selective.retain(active)
        self.verifier.retain(active)
        self.last_scores = {t: s for t, s in self.last_scores.items() if t in active}

        for track in tracks:
            track_id = track["track_id"]
            face = faces[track["detection_index"]]

            aligned = self.engine.align(frame, face)
            if aligned is None:
                continue

            ok, reason = check_face_quality(face, aligned)
            track["quality"] = reason

            if not ok:
                continue

            # Recognise more often while a possible match is being verified.
            interval = 2 if self.verifier.is_pending(track_id) else None

            if not self.selective.should_recognize(track_id, interval):
                continue

            embedding = self.engine.embed_aligned(aligned)
            if embedding is None:
                continue

            ranked = compare(embedding, self.store)
            decision = decide(ranked, self.threshold)
            self.last_scores[track_id] = ranked[0] if ranked else (None, 0.0)

            confirmed = self.verifier.update(track_id, decision)

            if confirmed:
                self._on_confirmed(frame, aligned, track, confirmed)

        return tracks

    def _on_confirmed(self, frame, aligned, track, confirmed):
        person_id = confirmed["person_id"]
        now = time.time()

        # The same person re-appearing as a new track shouldn't spam alerts.
        if now - self.last_alert.get(person_id, 0) < self.alert_cooldown:
            return

        self.last_alert[person_id] = now

        details = {
            "person_id": person_id,
            "name": self.store.name_of(person_id),
            "confidence": round(confirmed["score"], 4),
            "confidence_percent": confidence_percent(confirmed["score"], self.threshold),
            "verified_frames": confirmed["hits"],
            "camera_id": self.camera_id,
            "track_id": track["track_id"],
            "location": locate_face(track["bbox"], frame.shape),     # US-09
        }

        result = self.evidence.capture(frame, aligned, details)      # US-10

        self.banner = (f"MATCH: {details['name']} {details['confidence_percent']}%", now + 5)

        # US-11: hand the result to Member 3. Their errors must not stop detection.
        if self.on_match:
            try:
                self.on_match(result)
            except Exception as error:
                print(f"on_match callback failed: {error}")

    # ---------------------------------------------------------
    # Preview window
    # ---------------------------------------------------------

    def draw(self, frame, tracks, fps, frame_age_ms):
        view = frame.copy()

        for track in tracks:
            x, y, w, h = track["bbox"]
            state, person_id = self.verifier.status(track["track_id"])

            if state == "confirmed":
                color, label = RED, f"#{track['track_id']} {self.store.name_of(person_id)}"
            elif state == "verifying":
                score = self.last_scores.get(track["track_id"], (None, 0))[1]
                color, label = ORANGE, f"#{track['track_id']} verifying {person_id} {score:.2f}"
            else:
                color, label = GREEN, f"#{track['track_id']}"
                best = self.last_scores.get(track["track_id"])
                if best and best[0]:
                    label += f" {best[0]} {best[1]:.2f}"   # best score, below threshold
                if track.get("quality") not in (None, "ok"):
                    label += f" ({track['quality']})"

            cv2.rectangle(view, (x, y), (x + w, y + h), color, 2)
            cv2.putText(view, label, (x, max(20, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

        info = [
            f"{self.camera_id}  FPS {fps:.1f}  frame age {frame_age_ms:.0f} ms",
            f"Faces {len(tracks)}  Registered {len(self.store)}",
        ]
        for i, text in enumerate(info):
            cv2.putText(view, text, (10, 25 + 25 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 2)

        if self.banner and time.time() < self.banner[1]:
            cv2.rectangle(view, (0, view.shape[0] - 45), (view.shape[1], view.shape[0]), RED, -1)
            cv2.putText(view, self.banner[0], (10, view.shape[0] - 14),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, WHITE, 2)

        return view

    # ---------------------------------------------------------
    # Main loop (AI thread = main thread, needed for cv2.imshow)
    # ---------------------------------------------------------

    def run(self, display=True):
        self.camera_done = False
        camera_thread = threading.Thread(target=self._camera_loop, daemon=True)
        camera_thread.start()

        last_frame_number = 0
        processed, fps, fps_start = 0, 0.0, time.perf_counter()

        try:
            while not self.stop_event.is_set():
                data = self.buffer.get()

                # Only process a frame once; wait for a fresh one.
                if data is None or data[0] == last_frame_number:
                    if self.camera_done:
                        break
                    time.sleep(0.003)
                    continue

                frame_number, frame, capture_time = data
                last_frame_number = frame_number

                tracks = self.process(frame)

                processed += 1
                elapsed = time.perf_counter() - fps_start
                if elapsed >= 1.0:
                    fps, processed, fps_start = processed / elapsed, 0, time.perf_counter()

                if display or self.on_frame:
                    age = (time.perf_counter() - capture_time) * 1000
                    view = self.draw(frame, tracks, fps, age)
                    if self.on_frame:
                        self.on_frame(view)
                    if display:
                        cv2.imshow("AI Vision - Missing Person Detection", view)
                        if cv2.waitKey(1) & 0xFF == ord("q"):
                            break
        finally:
            self.stop_event.set()
            camera_thread.join(timeout=5)
            if display:
                cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Vision & Recognition pipeline")
    parser.add_argument("--source", default="0", help="webcam index, stream URL or video file")
    parser.add_argument("--camera-id", default="CAM01")
    parser.add_argument("--threshold", type=float, default=SFACE_COSINE_THRESHOLD)
    parser.add_argument("--refs", default=DEFAULT_STORE, help="reference store (.npz)")
    parser.add_argument("--evidence-dir", default=DEFAULT_EVIDENCE_DIR)
    parser.add_argument("--no-display", action="store_true")
    args = parser.parse_args()

    AIVisionPipeline(
        source=args.source,
        camera_id=args.camera_id,
        threshold=args.threshold,
        store_path=args.refs,
        evidence_dir=args.evidence_dir,
    ).run(display=not args.no_display)
