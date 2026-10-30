import threading
import time


class LatestFrameBuffer:
    def __init__(self):
        self.latest_frame = None
        self.lock = threading.Lock()

    def update(self, frame):
        """
        Replace the old frame with the newest frame.
        """
        with self.lock:
            self.latest_frame = frame

    def get(self):
        """
        Return the latest available frame.
        """
        with self.lock:
            return self.latest_frame


# Test the buffer
if __name__ == "__main__":
    buffer = LatestFrameBuffer()

    for frame_number in range(1, 6):
        buffer.update(frame_number)

        print("Camera produced:", frame_number)
        print("Buffer contains:", buffer.get())

        time.sleep(0.5)
        