import cv2
import os

# Run from this folder so relative model/image paths work from anywhere
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# --------------------------------------------------
# SFace model path
# --------------------------------------------------

MODEL_PATH = (
    "models/sface/"
    "face_recognition_sface_2021dec.onnx"
)


def main():

    print("Starting SFace model test...")

    # --------------------------------------------------
    # Check whether model exists
    # --------------------------------------------------

    if not os.path.exists(MODEL_PATH):

        print("ERROR: SFace model not found.")
        print("Expected path:")
        print(MODEL_PATH)

        return

    print("SFace model found.")
    print("Model path:", MODEL_PATH)

    # --------------------------------------------------
    # OpenCV information
    # --------------------------------------------------

    print("OpenCV version:", cv2.__version__)

    # --------------------------------------------------
    # Check FaceRecognizerSF
    # --------------------------------------------------

    if not hasattr(cv2, "FaceRecognizerSF"):

        print("ERROR: FaceRecognizerSF is not available.")

        return

    print("FaceRecognizerSF available: True")

    # --------------------------------------------------
    # Load SFace
    # --------------------------------------------------

    print("Loading SFace model...")

    recognizer = cv2.FaceRecognizerSF.create(
        MODEL_PATH,
        ""
    )

    print("SFace model loaded successfully!")


if __name__ == "__main__":
    main()