import cv2
import os

# Run from this folder so relative model/image paths work from anywhere
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("Starting YuNet model test...")

MODEL_PATH = "models/yunet/face_detection_yunet_2023mar.onnx"

print("OpenCV version:", cv2.__version__)
print("FaceDetectorYN available:", hasattr(cv2, "FaceDetectorYN"))

print("Model path:", MODEL_PATH)
print("Model exists:", os.path.exists(MODEL_PATH))

if not os.path.exists(MODEL_PATH):
    print("ERROR: YuNet model not found.")
    exit()

if not hasattr(cv2, "FaceDetectorYN"):
    print("ERROR: FaceDetectorYN is not available in this OpenCV version.")
    exit()

print("Loading YuNet model...")

detector = cv2.FaceDetectorYN.create(
    MODEL_PATH,
    "",
    (640, 480),
    0.6,
    0.3,
    5000
)

print("YuNet model loaded successfully!")