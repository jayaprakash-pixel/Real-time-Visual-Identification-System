import cv2
import os
import sys
import numpy as np

# --------------------------------------------------
# Add US-01 folder to Python path
# --------------------------------------------------

US01_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "us-01")
)

sys.path.append(US01_PATH)


# --------------------------------------------------
# Import US-01 components
# --------------------------------------------------

from camera_source import open_camera, read_frame, release_camera
from frame_buffer import LatestFrameBuffer


# --------------------------------------------------
# Import our alignment module
# --------------------------------------------------

from face_alignment import align_face

# Run from this folder so relative model/image paths work from anywhere
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# --------------------------------------------------
# YuNet model
# --------------------------------------------------

MODEL_PATH = "models/yunet/face_detection_yunet_2023mar.onnx"

CONFIDENCE_THRESHOLD = 0.6
NMS_THRESHOLD = 0.3
TOP_K = 5000


def main():

    print("Starting YuNet + Face Alignment test...")

    # --------------------------------------------------
    # Check model
    # --------------------------------------------------

    if not os.path.exists(MODEL_PATH):
        print("ERROR: YuNet model not found.")
        return

    # --------------------------------------------------
    # Open camera
    # --------------------------------------------------

    camera = open_camera()

    if camera is None:
        print("ERROR: Could not open camera.")
        return

    print("Camera connected.")

    # --------------------------------------------------
    # Create latest-frame buffer
    # --------------------------------------------------

    buffer = LatestFrameBuffer()

    print("Low-latency buffer created.")

    detector = None

    try:

        while True:

            # --------------------------------------------------
            # 1. Get frame from camera
            # --------------------------------------------------

            frame = read_frame(camera)

            if frame is None:
                print("ERROR: Could not read frame.")
                break

            # --------------------------------------------------
            # 2. Put newest frame into buffer
            # --------------------------------------------------

            buffer.update(frame)

            # --------------------------------------------------
            # 3. Get latest frame
            # --------------------------------------------------

            latest_frame = buffer.get()

            if latest_frame is None:
                continue

            # --------------------------------------------------
            # 4. Initialize YuNet
            # --------------------------------------------------

            if detector is None:

                height, width = latest_frame.shape[:2]

                detector = cv2.FaceDetectorYN.create(
                    MODEL_PATH,
                    "",
                    (width, height),
                    CONFIDENCE_THRESHOLD,
                    NMS_THRESHOLD,
                    TOP_K
                )

                print(
                    f"YuNet initialized: "
                    f"{width} x {height}"
                )

            # --------------------------------------------------
            # 5. Detect faces
            # --------------------------------------------------

            _, faces = detector.detect(latest_frame)

            # --------------------------------------------------
            # 6. Process every detected face
            # --------------------------------------------------

            if faces is not None:

                for index, face in enumerate(faces):

                    # ------------------------------------------
                    # Bounding box
                    # ------------------------------------------

                    x = int(face[0])
                    y = int(face[1])
                    w = int(face[2])
                    h = int(face[3])

                    confidence = float(face[14])

                    # ------------------------------------------
                    # Extract YuNet's 5 landmarks
                    # ------------------------------------------

                    landmarks = face[4:14].reshape(5, 2)

                    # ------------------------------------------
                    # Align face
                    # ------------------------------------------

                    aligned_face = align_face(
                        latest_frame,
                        landmarks
                    )

                    # ------------------------------------------
                    # Draw bounding box
                    # ------------------------------------------

                    cv2.rectangle(
                        latest_frame,
                        (x, y),
                        (x + w, y + h),
                        (0, 255, 0),
                        2
                    )

                    # ------------------------------------------
                    # Draw landmarks
                    # ------------------------------------------

                    for point in landmarks:

                        px = int(point[0])
                        py = int(point[1])

                        cv2.circle(
                            latest_frame,
                            (px, py),
                            3,
                            (0, 0, 255),
                            -1
                        )

                    # ------------------------------------------
                    # Face label
                    # ------------------------------------------

                    label = (
                        f"Face {index + 1} "
                        f"{confidence:.2f}"
                    )

                    cv2.putText(
                        latest_frame,
                        label,
                        (x, max(25, y - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (0, 255, 0),
                        2
                    )

                    # ------------------------------------------
                    # Show aligned face
                    # ------------------------------------------

                    if aligned_face is not None:

                        window_name = (
                            f"Aligned Face {index + 1}"
                        )

                        cv2.imshow(
                            window_name,
                            aligned_face
                        )

            # --------------------------------------------------
            # Show original camera feed
            # --------------------------------------------------

            cv2.imshow(
                "YuNet + Face Alignment",
                latest_frame
            )

            # --------------------------------------------------
            # Press Q to quit
            # --------------------------------------------------

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

    finally:

        release_camera(camera)

        cv2.destroyAllWindows()

        print("Test stopped.")


if __name__ == "__main__":
    main()