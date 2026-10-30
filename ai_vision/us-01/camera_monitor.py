import cv2
import threading
import time

from camera_source import open_camera, read_frame, release_camera
from frame_buffer import LatestFrameBuffer


def camera_thread(camera, buffer, stop_event):
    """
    Continuously captures frames from the camera
    and places the latest frame into the buffer.
    """

    frame_number = 0

    while not stop_event.is_set():

        frame = read_frame(camera)

        if frame is None:
            print("Could not read frame")
            stop_event.set()
            break

        frame_number += 1

        capture_time = time.perf_counter()

        buffer.update(
            (frame_number, frame, capture_time)
        )


def main():

    # --------------------------------
    # Camera and buffer initialization
    # --------------------------------

    camera = open_camera()

    buffer = LatestFrameBuffer()

    stop_event = threading.Event()

    # --------------------------------
    # Camera thread
    # --------------------------------

    camera_worker = threading.Thread(
        target=camera_thread,
        args=(camera, buffer, stop_event)
    )

    camera_worker.start()

    # --------------------------------
    # FPS variables
    # --------------------------------

    previous_time = time.perf_counter()
    frame_count = 0
    fps = 0

    try:

        while True:

            # Get latest frame from buffer
            data = buffer.get()

            if data is None:
                time.sleep(0.01)
                continue

            frame_number, frame, capture_time = data

            # Draw on a copy: the buffer's frame is shared with other threads
            frame = frame.copy()

            # --------------------------------
            # FPS calculation
            # --------------------------------

            frame_count += 1

            current_time = time.perf_counter()

            elapsed_time = current_time - previous_time

            if elapsed_time >= 1.0:

                fps = frame_count / elapsed_time

                frame_count = 0
                previous_time = current_time

            # --------------------------------
            # Frame information
            # --------------------------------

            height, width = frame.shape[:2]

            # Calculate frame age
            frame_age = (
                current_time - capture_time
            ) * 1000

            # --------------------------------
            # Monitoring information
            # --------------------------------

            cv2.putText(
                frame,
                "LIVE CAMERA MONITOR",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                "Camera: CONNECTED",
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"Resolution: {width} x {height}",
                (20, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Display FPS: {fps:.1f}",
                (20, 130),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Latest Frame: {frame_number}",
                (20, 160),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Frame Age: {frame_age:.1f} ms",
                (20, 190),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                "Status: STREAMING",
                (20, 220),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2
            )

            # --------------------------------
            # Display live feed
            # --------------------------------

            cv2.imshow(
                "Missing Person Detection - Monitor",
                frame
            )

            # Press Q to stop
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:

        # Stop camera thread
        stop_event.set()

        camera_worker.join()

        # Release resources
        release_camera(camera)

        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()