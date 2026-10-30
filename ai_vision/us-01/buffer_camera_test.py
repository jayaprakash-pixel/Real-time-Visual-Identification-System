import cv2
import threading
import time

from camera_source import open_camera, read_frame, release_camera
from frame_buffer import LatestFrameBuffer


def camera_thread(camera, buffer, stop_event):
    """
    Continuously reads frames from the camera.

    Each frame is given:
    - a frame number
    - the actual frame
    - the capture timestamp

    Only the latest frame is kept in the buffer.
    """

    frame_number = 0

    while not stop_event.is_set():

        frame = read_frame(camera)

        if frame is None:
            print("Could not read frame")
            stop_event.set()
            break

        frame_number += 1

        # Record the exact time when the frame was captured
        capture_time = time.perf_counter()

        # Store frame number, frame and timestamp
        buffer.update(
            (frame_number, frame, capture_time)
        )


def processing_thread(buffer, stop_event):
    """
    Simulates a slower AI processor.

    The processor runs at approximately 10 FPS
    while the camera produces approximately 30 FPS.

    This allows us to observe the behaviour of
    the latest-frame buffer.
    """

    while not stop_event.is_set():

        data = buffer.get()

        if data is None:
            time.sleep(0.01)
            continue

        frame_number, frame, capture_time = data

        # Record the time when processor receives the frame
        process_time = time.perf_counter()

        # Calculate latency
        latency = (process_time - capture_time) * 1000

        print(
            f"Processing frame: {frame_number} | "
            f"Latency: {latency:.2f} ms"
        )

        # Simulate slow AI processing
        time.sleep(0.1)


def main():

    # Open camera
    camera = open_camera()

    # Create latest-frame buffer
    buffer = LatestFrameBuffer()

    # Event used to stop all threads safely
    stop_event = threading.Event()

    # Create camera thread
    camera_worker = threading.Thread(
        target=camera_thread,
        args=(camera, buffer, stop_event)
    )

    # Create processing thread
    processor_worker = threading.Thread(
        target=processing_thread,
        args=(buffer, stop_event)
    )

    # Start both threads
    camera_worker.start()
    processor_worker.start()

    try:

        while True:

            data = buffer.get()

            if data is None:
                time.sleep(0.01)
                continue

            frame_number, frame, capture_time = data

            # Draw on a copy: the buffer's frame is shared with other threads
            frame = frame.copy()

            # Calculate current age of the displayed frame
            current_time = time.perf_counter()

            frame_age = (
                current_time - capture_time
            ) * 1000

            # Display frame number
            cv2.putText(
                frame,
                f"Latest Frame: {frame_number}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            # Display frame age
            cv2.putText(
                frame,
                f"Frame Age: {frame_age:.1f} ms",
                (20, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )

            cv2.imshow(
                "Camera + Low Latency Buffer",
                frame
            )

            # Press Q to stop
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:

        # Tell both threads to stop
        stop_event.set()

        # Wait for threads to finish
        camera_worker.join()
        processor_worker.join()

        # Release camera
        release_camera(camera)

        # Close OpenCV windows
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()