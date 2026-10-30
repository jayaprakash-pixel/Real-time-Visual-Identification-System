import cv2


def parse_source(source):
    """
    Camera source can be:
    - a webcam index:       0, 1, "0"
    - a phone/IP stream:    "http://192.168.1.5:8080/video"
    - a recorded video:     "test_video.mp4"
    """
    if isinstance(source, str) and source.isdigit():
        return int(source)

    return source


def open_camera(camera_index=0):
    camera = cv2.VideoCapture(parse_source(camera_index))

    if not camera.isOpened():
        raise RuntimeError(f"Could not open camera: {camera_index}")

    # Ask the driver to keep only 1 frame internally so we always read
    # the newest frame (ignored by backends that don't support it).
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    return camera


def read_frame(camera):
    success, frame = camera.read()

    if not success:
        return None

    return frame


def release_camera(camera):
    camera.release()


if __name__ == "__main__":
    camera = open_camera()

    while True:
        frame = read_frame(camera)

        if frame is None:
            print("Could not read frame")
            break

        cv2.imshow("Live Camera Feed", frame)

        # Press Q to stop
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    release_camera(camera)
    cv2.destroyAllWindows()
