import cv2
import time
import os
import sys 

US01_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "us-01"))
sys.path.append(US01_PATH)

# US-01 components
from camera_source import open_camera, read_frame, release_camera
from frame_buffer import LatestFrameBuffer

# Run from this folder so relative model/image paths work from anywhere
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# --------------------------------------------------
# YuNet configuration
# --------------------------------------------------

MODEL_PATH = "models/yunet/face_detection_yunet_2023mar.onnx"

CONFIDENCE_THRESHOLD = 0.6
NMS_THRESHOLD = 0.3
TOP_K = 5000


def main():

    print("Starting US-01 + US-02 integration test...")

    # --------------------------------------------------
    # Check YuNet model
    # --------------------------------------------------

    if not os.path.exists(MODEL_PATH):
        print("ERROR: YuNet model not found.")
        return

    # --------------------------------------------------
    # Create camera
    # --------------------------------------------------

    camera = open_camera()

    if camera is None:
        print("ERROR: Could not open camera.")
        return

    print("Camera connected.")

    # --------------------------------------------------
    # Create low-latency buffer
    # --------------------------------------------------

    buffer = LatestFrameBuffer()

    print("Low-latency buffer created.")

    # --------------------------------------------------
    # Variables
    # --------------------------------------------------

    detector = None

    frame_count = 0

    previous_time = time.perf_counter()

    display_fps = 0.0

    try:

        while True:

            # --------------------------------------------------
            # 1. Get frame from US-01 camera source
            # --------------------------------------------------

            frame = read_frame(camera)

            if frame is None:
                print("ERROR: Could not read camera frame.")
                break

            frame_count += 1

            # --------------------------------------------------
            # 2. Put frame into US-01 low-latency buffer
            # --------------------------------------------------

            buffer.update(frame)

            # --------------------------------------------------
            # 3. Get ONLY the latest frame
            # --------------------------------------------------

            latest_frame = buffer.get()


            if latest_frame is None:
                continue

            # --------------------------------------------------
            # 4. Create YuNet detector once
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
                    f"YuNet initialized "
                    f"for {width} x {height}"
                )

            # --------------------------------------------------
            # 5. Run YuNet on latest frame
            # --------------------------------------------------

            start_time = time.perf_counter()

            _, faces = detector.detect(latest_frame)

            end_time = time.perf_counter()

            inference_time = (end_time - start_time) * 1000

            # --------------------------------------------------
            # 6. Draw detected faces
            # --------------------------------------------------

            face_count = 0

            if faces is not None:

                face_count = len(faces)

                for index, face in enumerate(faces):

                    x = int(face[0])
                    y = int(face[1])
                    w = int(face[2])
                    h = int(face[3])

                    confidence = float(face[14])

                    # Bounding box
                    cv2.rectangle(
                        latest_frame,
                        (x, y),
                        (x + w, y + h),
                        (0, 255, 0),
                        2
                    )

                    # Face label
                    label = (
                        f"Face {index + 1}: "
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

            # --------------------------------------------------
            # 7. Calculate display FPS
            # --------------------------------------------------

            current_time = time.perf_counter()

            elapsed = current_time - previous_time

            if elapsed >= 1.0:

                display_fps = frame_count / elapsed

                frame_count = 0

                previous_time = current_time

            # --------------------------------------------------
            # 8. Display system information
            # --------------------------------------------------

            cv2.putText(
                latest_frame,
                "US-01 + US-02",
                (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            cv2.putText(
                latest_frame,
                f"Faces: {face_count}",
                (20, 65),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            cv2.putText(
                latest_frame,
                f"YuNet: {inference_time:.2f} ms",
                (20, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )

            cv2.putText(
                latest_frame,
                f"Display FPS: {display_fps:.1f}",
                (20, 135),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )

            # --------------------------------------------------
            # 9. Show frame
            # --------------------------------------------------

            cv2.imshow(
                "YuNet + Low Latency Camera",
                latest_frame
            )

            # --------------------------------------------------
            # 10. Press Q to stop
            # --------------------------------------------------

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:

        release_camera(camera)

        cv2.destroyAllWindows()

        print("\nIntegration test stopped.")


if __name__ == "__main__":
    main()