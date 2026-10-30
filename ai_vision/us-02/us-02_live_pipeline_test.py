import cv2
import os
import sys
import time
import numpy as np


# ============================================================
# 1. ADD US-01 TO PYTHON PATH
# ============================================================

US01_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "us-01")
)

sys.path.append(US01_PATH)


# ============================================================
# 2. IMPORT US-01 COMPONENTS
# ============================================================

from camera_source import (
    open_camera,
    read_frame,
    release_camera
)

from frame_buffer import LatestFrameBuffer


# ============================================================
# 3. IMPORT FACE ALIGNMENT
# ============================================================

from face_alignment import align_face

# Run from this folder so relative model/image paths work from anywhere
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# ============================================================
# 4. MODEL PATHS
# ============================================================

YUNET_MODEL = (
    "models/yunet/"
    "face_detection_yunet_2023mar.onnx"
)

SFACE_MODEL = (
    "models/sface/"
    "face_recognition_sface_2021dec.onnx"
)


# ============================================================
# 5. YuNet SETTINGS
# ============================================================

CONFIDENCE_THRESHOLD = 0.6
NMS_THRESHOLD = 0.3
TOP_K = 5000


# ============================================================
# 6. MAIN
# ============================================================

def main():

    print("=" * 60)
    print("US-02 FINAL LIVE PIPELINE")
    print("=" * 60)

    # --------------------------------------------------------
    # Check models
    # --------------------------------------------------------

    if not os.path.exists(YUNET_MODEL):

        print("ERROR: YuNet model not found.")
        print(YUNET_MODEL)

        return

    if not os.path.exists(SFACE_MODEL):

        print("ERROR: SFace model not found.")
        print(SFACE_MODEL)

        return

    print("YuNet model found.")
    print("SFace model found.")

    # --------------------------------------------------------
    # Open camera using US-01
    # --------------------------------------------------------

    camera = open_camera()

    if camera is None:

        print("ERROR: Could not open camera.")

        return

    print("Camera connected.")

    # --------------------------------------------------------
    # Create US-01 latest frame buffer
    # --------------------------------------------------------

    buffer = LatestFrameBuffer()

    print("Latest-frame buffer created.")

    # --------------------------------------------------------
    # Initialize models later after frame size is known
    # --------------------------------------------------------

    detector = None
    recognizer = None

    frame_count = 0

    try:

        while True:

            # =================================================
            # STEP 1
            # Get frame from US-01 camera
            # =================================================

            frame = read_frame(camera)

            if frame is None:

                print("ERROR: Could not read frame.")

                break

            frame_count += 1

            # =================================================
            # STEP 2
            # Put newest frame into buffer
            # =================================================

            buffer.update(frame)

            # =================================================
            # STEP 3
            # Get latest frame
            # =================================================

            latest_frame = buffer.get()

            if latest_frame is None:

                continue

            # =================================================
            # STEP 4
            # Initialize YuNet
            # =================================================

            if detector is None:

                height, width = latest_frame.shape[:2]

                detector = cv2.FaceDetectorYN.create(
                    YUNET_MODEL,
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

            # =================================================
            # STEP 5
            # Initialize SFace
            # =================================================

            if recognizer is None:

                recognizer = cv2.FaceRecognizerSF.create(
                    SFACE_MODEL,
                    ""
                )

                print("SFace initialized.")

            # =================================================
            # STEP 6
            # YuNet face detection
            # =================================================

            detection_start = time.perf_counter()

            _, faces = detector.detect(latest_frame)

            detection_time = (
                time.perf_counter()
                - detection_start
            ) * 1000

            # =================================================
            # STEP 7
            # Process detected faces
            # =================================================

            face_count = 0

            if faces is not None:

                face_count = len(faces)

                for index, face in enumerate(faces):

                    # ------------------------------------------------
                    # Bounding box
                    # ------------------------------------------------

                    x = int(face[0])
                    y = int(face[1])
                    w = int(face[2])
                    h = int(face[3])

                    confidence = float(face[14])

                    # ------------------------------------------------
                    # Extract YuNet's 5 landmarks
                    # ------------------------------------------------

                    landmarks = (
                        face[4:14]
                        .reshape(5, 2)
                    )

                    # ------------------------------------------------
                    # Face alignment
                    # ------------------------------------------------

                    alignment_start = (
                        time.perf_counter()
                    )

                    aligned_face = align_face(
                        latest_frame,
                        landmarks
                    )

                    alignment_time = (
                        time.perf_counter()
                        - alignment_start
                    ) * 1000

                    # ------------------------------------------------
                    # Check alignment
                    # ------------------------------------------------

                    if aligned_face is None:

                        continue

                    # ------------------------------------------------
                    # SFace embedding
                    # ------------------------------------------------

                    embedding_start = (
                        time.perf_counter()
                    )

                    feature = recognizer.feature(
                        aligned_face
                    )

                    embedding_time = (
                        time.perf_counter()
                        - embedding_start
                    ) * 1000

                    # ------------------------------------------------
                    # Check embedding
                    # ------------------------------------------------

                    if feature is None:

                        continue

                    # ------------------------------------------------
                    # Embedding information
                    # ------------------------------------------------

                    embedding_shape = feature.shape

                    embedding_norm = float(
                        np.linalg.norm(feature)
                    )

                    # ------------------------------------------------
                    # Draw bounding box
                    # ------------------------------------------------

                    cv2.rectangle(
                        latest_frame,
                        (x, y),
                        (x + w, y + h),
                        (0, 255, 0),
                        2
                    )

                    # ------------------------------------------------
                    # Draw 5 landmarks
                    # ------------------------------------------------

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

                    # ------------------------------------------------
                    # Face label
                    # ------------------------------------------------

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

                    # ------------------------------------------------
                    # Display embedding information
                    # ------------------------------------------------

                    info_y = y + h + 20

                    if info_y < latest_frame.shape[0] - 10:

                        cv2.putText(
                            latest_frame,
                            "SFace: 128-D",
                            (x, info_y),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.45,
                            (255, 255, 255),
                            1
                        )

                    # ------------------------------------------------
                    # Print embedding information periodically
                    # ------------------------------------------------

                    if frame_count % 30 == 0:

                        print(
                            f"Face {index + 1} | "
                            f"Confidence: {confidence:.3f} | "
                            f"Alignment: "
                            f"{alignment_time:.2f} ms | "
                            f"SFace: "
                            f"{embedding_time:.2f} ms | "
                            f"Embedding: "
                            f"{embedding_shape} | "
                            f"Norm: "
                            f"{embedding_norm:.3f}"
                        )

            # =================================================
            # STEP 8
            # Display pipeline information
            # =================================================

            cv2.putText(
                latest_frame,
                "US-01 + US-02",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0),
                2
            )

            cv2.putText(
                latest_frame,
                f"Faces: {face_count}",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            cv2.putText(
                latest_frame,
                f"YuNet: {detection_time:.2f} ms",
                (20, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )

            cv2.putText(
                latest_frame,
                "SFace: ACTIVE",
                (20, 130),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )

            # =================================================
            # STEP 9
            # Show live camera feed
            # =================================================

            cv2.imshow(
                "US-02 Final Live Pipeline",
                latest_frame
            )

            # =================================================
            # STEP 10
            # Quit with Q
            # =================================================

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):

                break

    finally:

        # ----------------------------------------------------
        # Release US-01 camera
        # ----------------------------------------------------

        release_camera(camera)

        cv2.destroyAllWindows()

        print()
        print("=" * 60)
        print("US-02 pipeline stopped.")
        print("=" * 60)


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":

    main()