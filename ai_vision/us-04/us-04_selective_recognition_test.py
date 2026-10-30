import sys
import os
import cv2
import time

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
US01_PATH = os.path.join(CURRENT_DIR, "..", "us-01")
US02_PATH = os.path.join(CURRENT_DIR, "..", "us-02")
US03_PATH = os.path.join(CURRENT_DIR, "..", "us-03")

sys.path.append(US01_PATH)
sys.path.append(US02_PATH)
sys.path.append(US03_PATH)

from camera_source import open_camera, read_frame, release_camera
from frame_buffer import LatestFrameBuffer
from face_tracker import FaceTracker
from selective_recognition import SelectiveRecognition
from face_alignment import align_face


YUNET_MODEL = os.path.join(
    US02_PATH,
    "models",
    "yunet",
    "face_detection_yunet_2023mar.onnx"
)

SFACE_MODEL = os.path.join(
    US02_PATH,
    "models",
    "sface",
    "face_recognition_sface_2021dec.onnx"
)


print("US-04 FULL INTEGRATION TEST")
print("-" * 40)

# Check models
if not os.path.exists(YUNET_MODEL):
    print("YuNet model not found.")
    exit()

if not os.path.exists(SFACE_MODEL):
    print("SFace model not found.")
    exit()

# Camera
camera = open_camera()

if camera is None:
    print("Camera could not be opened.")
    exit()

buffer = LatestFrameBuffer()
tracker = FaceTracker(max_distance=80, max_missed_frames=10)

# US-04
recognition = SelectiveRecognition(recognition_interval=10)

# YuNet
detector = cv2.FaceDetectorYN.create(
    YUNET_MODEL,
    "",
    (640, 480),
    0.6,
    0.3,
    5000
)

# SFace
recognizer = cv2.FaceRecognizerSF.create(
    SFACE_MODEL,
    ""
)

print("YuNet initialized.")
print("SFace initialized.")
print("Camera connected.")
print("Selective recognition enabled.")
print("-" * 40)

frame_count = 0

try:
    while True:

        # US-01
        frame = read_frame(camera)

        if frame is None:
            continue

        buffer.update(frame)
        latest_frame = buffer.get()

        frame_count += 1

        # US-02
        detector.setInputSize(
            (latest_frame.shape[1], latest_frame.shape[0])
        )

        _, faces = detector.detect(latest_frame)

        detections = []
        landmarks_list = []

        if faces is not None:
            for face in faces:
                x, y, w, h = face[:4].astype(int)
                detections.append((x, y, w, h))
                landmarks_list.append(face[4:14].reshape(5, 2))

        # US-03
        tracks = tracker.update(detections)

        for track in tracks:

            track_id = track["track_id"]
            x, y, w, h = track["bbox"]

            # US-04
            run_recognition = recognition.should_recognize(track_id)

            if run_recognition:

                # Align with YuNet landmarks (same as US-02) instead of
                # resizing a raw crop: SFace expects an aligned 112x112 face.
                face_crop = align_face(
                    latest_frame,
                    landmarks_list[track["detection_index"]]
                )

                if face_crop is not None:

                    start = time.time()

                    embedding = recognizer.feature(face_crop)

                    sface_time = (time.time() - start) * 1000

                    print(
                        f"Frame {frame_count:4} | "
                        f"Track ID {track_id} | "
                        f"SFace RUN | "
                        f"Embedding: {embedding.shape} | "
                        f"Time: {sface_time:.2f} ms"
                    )

            else:
                print(
                    f"Frame {frame_count:4} | "
                    f"Track ID {track_id} | "
                    f"SFace SKIP"
                )

            # Display
            cv2.rectangle(
                latest_frame,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2
            )

            cv2.putText(
                latest_frame,
                f"Track ID: {track_id}",
                (x, max(20, y - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

        cv2.putText(
            latest_frame,
            "US-04 Selective Face Recognition",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

        cv2.imshow("US-04", latest_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    release_camera(camera)
    cv2.destroyAllWindows()

print("-" * 40)
print("US-04 FULL INTEGRATION TEST COMPLETED")