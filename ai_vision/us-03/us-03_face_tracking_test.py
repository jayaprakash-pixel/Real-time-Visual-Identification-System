import sys
import os
import cv2

# ---------------------------------------------------------
# PATH SETUP
# ---------------------------------------------------------

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

US01_PATH = os.path.join(CURRENT_DIR, "..", "us-01")
US02_PATH = os.path.join(CURRENT_DIR, "..", "us-02")

sys.path.append(US01_PATH)
sys.path.append(US02_PATH)

# US-01
from camera_source import open_camera, read_frame, release_camera
from frame_buffer import LatestFrameBuffer

# US-03
from face_tracker import FaceTracker


# ---------------------------------------------------------
# YUNET MODEL
# ---------------------------------------------------------

YUNET_MODEL = os.path.join(
    US02_PATH,
    "models",
    "yunet",
    "face_detection_yunet_2023mar.onnx"
)


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print("=" * 60)
    print("US-03 FACE TRACKING TEST")
    print("=" * 60)

    # -----------------------------------------------------
    # Check model
    # -----------------------------------------------------

    if not os.path.exists(YUNET_MODEL):
        print("YuNet model not found:")
        print(YUNET_MODEL)
        return

    print("YuNet model found.")

    # -----------------------------------------------------
    # Open camera
    # -----------------------------------------------------

    camera = open_camera()

    if camera is None:
        print("Failed to open camera.")
        return

    print("Camera connected.")

    # -----------------------------------------------------
    # Create latest-frame buffer
    # -----------------------------------------------------

    buffer = LatestFrameBuffer()

    print("Latest-frame buffer created.")

    # -----------------------------------------------------
    # Initialize YuNet
    # -----------------------------------------------------

    detector = cv2.FaceDetectorYN.create(
        YUNET_MODEL,
        "",
        (640, 480),
        0.6,
        0.3,
        5000
    )

    print("YuNet initialized: 640 x 480")

    # -----------------------------------------------------
    # Initialize tracker
    # -----------------------------------------------------

    tracker = FaceTracker(
        max_distance=80,
        max_missed_frames=10
    )

    print("Face tracker initialized.")
    print()
    print("Press 'q' to stop.")
    print("-" * 60)

    # -----------------------------------------------------
    # Main loop
    # -----------------------------------------------------

    while True:

        # Get camera frame
        frame = read_frame(camera)

        if frame is None:
            continue

        # Update latest-frame buffer
        buffer.update(frame)

        # Get latest frame
        latest_frame = buffer.get()

        if latest_frame is None:
            continue

        # -------------------------------------------------
        # Prepare frame for YuNet
        # -------------------------------------------------

        height, width = latest_frame.shape[:2]

        detector.setInputSize((width, height))

        # -------------------------------------------------
        # Detect faces
        # -------------------------------------------------

        _, faces = detector.detect(latest_frame)

        detections = []

        if faces is not None:

            for face in faces:

                x = int(face[0])
                y = int(face[1])
                w = int(face[2])
                h = int(face[3])

                detections.append((x, y, w, h))

        # -------------------------------------------------
        # Update tracker
        # -------------------------------------------------

        tracks = tracker.update(detections)

        # -------------------------------------------------
        # Draw tracking results
        # -------------------------------------------------

        for track in tracks:

            track_id = track["track_id"]
            x, y, w, h = track["bbox"]

            # Bounding box
            cv2.rectangle(
                latest_frame,
                (x, y),
                (x + w, y + h),
                (0, 255, 0),
                2
            )

            # Track ID
            label = f"Track ID: {track_id}"

            cv2.putText(
                latest_frame,
                label,
                (x, max(y - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

        # -------------------------------------------------
        # Display information
        # -------------------------------------------------

        cv2.putText(
            latest_frame,
            f"Faces: {len(tracks)}",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        cv2.putText(
            latest_frame,
            "US-03 Face Tracking",
            (20, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        # -------------------------------------------------
        # Show frame
        # -------------------------------------------------

        cv2.imshow("US-03 Face Tracking", latest_frame)

        # -------------------------------------------------
        # Quit
        # -------------------------------------------------

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

    # -----------------------------------------------------
    # Cleanup
    # -----------------------------------------------------

    release_camera(camera)
    cv2.destroyAllWindows()

    print()
    print("US-03 tracking test stopped.")
    print("=" * 60)


if __name__ == "__main__":
    main()