import cv2
import time

from camera_source import open_camera, read_frame, release_camera


def process_camera_stream():
    camera = open_camera()

    previous_time = time.time()
    frame_count = 0
    fps = 0

    while True:
        frame = read_frame(camera)

        if frame is None:
            print("Could not read frame")
            break

        frame_count += 1

        # Calculate FPS every second
        current_time = time.time()
        elapsed_time = current_time - previous_time

        if elapsed_time >= 1.0:
            fps = frame_count / elapsed_time
            frame_count = 0
            previous_time = current_time

        # Get frame dimensions
        height, width = frame.shape[:2]

        # Display information on the frame
        cv2.putText(
            frame,
            "Camera: CONNECTED",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Resolution: {width} x {height}",
            (20, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"Camera FPS: {fps:.1f}",
            (20, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        cv2.imshow("Live Camera Feed", frame)

        # Press Q to stop
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    release_camera(camera)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    process_camera_stream()