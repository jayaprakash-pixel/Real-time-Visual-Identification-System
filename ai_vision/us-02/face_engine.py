import os

import cv2
import numpy as np

from face_alignment import align_face

# Hide OpenCV 5 dnn "Targets are not supported by the new graph engine" warnings.
cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

YUNET_MODEL = os.path.join(MODELS_DIR, "yunet", "face_detection_yunet_2023mar.onnx")
SFACE_MODEL = os.path.join(MODELS_DIR, "sface", "face_recognition_sface_2021dec.onnx")


class FaceEngine:
    """
    US-02: YuNet detection -> 5 landmarks -> alignment -> SFace embedding.

    Shared by the live pipeline (US-01..US-10) and reference enrolment (US-05),
    so reference and live embeddings are always produced the same way.
    """

    def __init__(self, confidence_threshold=0.6, nms_threshold=0.3, top_k=5000):
        for path in (YUNET_MODEL, SFACE_MODEL):
            if not os.path.exists(path):
                raise FileNotFoundError(f"Model not found: {path}")

        self.detector = cv2.FaceDetectorYN.create(
            YUNET_MODEL, "", (320, 320),
            confidence_threshold, nms_threshold, top_k
        )
        self.recognizer = cv2.FaceRecognizerSF.create(SFACE_MODEL, "")

    def detect(self, frame):
        """
        Returns a list of faces:
            {"bbox": (x, y, w, h), "landmarks": 5x2 array, "score": float}
        """
        height, width = frame.shape[:2]
        self.detector.setInputSize((width, height))

        _, faces = self.detector.detect(frame)

        if faces is None:
            return []

        return [
            {
                "bbox": tuple(int(v) for v in face[:4]),
                "landmarks": face[4:14].reshape(5, 2),
                "score": float(face[14]),
            }
            for face in faces
        ]

    def align(self, frame, face):
        return align_face(frame, face["landmarks"])

    def embed_aligned(self, aligned_face):
        """
        128-D SFace embedding, L2-normalised so that a dot product
        between two embeddings equals their cosine similarity.
        """
        feature = self.recognizer.feature(aligned_face).flatten()
        norm = np.linalg.norm(feature)

        if norm == 0:
            return None

        return (feature / norm).astype(np.float32)

    def embed(self, frame, face):
        aligned = self.align(frame, face)

        if aligned is None:
            return None

        return self.embed_aligned(aligned)
