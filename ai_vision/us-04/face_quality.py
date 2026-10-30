import cv2
import numpy as np


# Defaults; tune with real camera footage if needed.
MIN_FACE_SIZE = 40        # px, smaller faces give unreliable embeddings
MIN_SHARPNESS = 15.0      # variance of Laplacian on the aligned 112x112 face
MIN_BRIGHTNESS = 40       # mean grey level of the aligned face
MAX_BRIGHTNESS = 220
MAX_YAW = 0.5             # nose offset from eye midpoint / eye distance (~40 deg turn);
                          # beyond this SFace becomes unreliable even with multi-angle references


def check_face_quality(face, aligned_face):
    """
    Decide whether a face is good enough to run recognition on.

    face:          detection dict from FaceEngine.detect
    aligned_face:  112x112 aligned face

    Returns (ok: bool, reason: str)
    """
    _, _, w, h = face["bbox"]

    if min(w, h) < MIN_FACE_SIZE:
        return False, "too small"

    # Pose: on a frontal face the nose sits between the eyes.
    left_eye, right_eye, nose = face["landmarks"][:3]
    eye_distance = np.linalg.norm(right_eye - left_eye)

    if eye_distance == 0:
        return False, "bad landmarks"

    yaw = abs(nose[0] - (left_eye[0] + right_eye[0]) / 2) / eye_distance

    if yaw > MAX_YAW:
        return False, "side face"

    gray = cv2.cvtColor(aligned_face, cv2.COLOR_BGR2GRAY)

    brightness = gray.mean()

    if brightness < MIN_BRIGHTNESS:
        return False, "too dark"

    if brightness > MAX_BRIGHTNESS:
        return False, "too bright"

    if cv2.Laplacian(gray, cv2.CV_64F).var() < MIN_SHARPNESS:
        return False, "blurry"

    return True, "ok"
