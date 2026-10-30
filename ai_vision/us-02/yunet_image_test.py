import cv2
import os
import time

# Run from this folder so relative model/image paths work from anywhere
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# --------------------------------------------------
# Paths
# --------------------------------------------------

MODEL_PATH = "models/yunet/face_detection_yunet_2023mar.onnx"
IMAGE_PATH = "test.jpg"


# --------------------------------------------------
# Detection settings
# --------------------------------------------------

CONFIDENCE_THRESHOLD = 0.6
NMS_THRESHOLD = 0.3
TOP_K = 5000


def main():

    print("Starting YuNet image detection test...")

    # --------------------------------------------------
    # Check files
    # --------------------------------------------------

    if not os.path.exists(MODEL_PATH):
        print("ERROR: YuNet model not found.")
        return

    if not os.path.exists(IMAGE_PATH):
        print("ERROR: Test image not found.")
        print("Put test.jpg inside the us-02 folder.")
        return

    # --------------------------------------------------
    # Load image
    # --------------------------------------------------

    image = cv2.imread(IMAGE_PATH)

    if image is None:
        print("ERROR: Could not read the image.")
        return

    height, width = image.shape[:2]

    print(f"Image size: {width} x {height}")

    # --------------------------------------------------
    # Create YuNet detector
    # --------------------------------------------------

    detector = cv2.FaceDetectorYN.create(
        MODEL_PATH,
        "",
        (width, height),
        CONFIDENCE_THRESHOLD,
        NMS_THRESHOLD,
        TOP_K
    )

    print("YuNet model loaded.")

    # --------------------------------------------------
    # Run detection
    # --------------------------------------------------

    start_time = time.perf_counter()

    _, faces = detector.detect(image)

    end_time = time.perf_counter()

    inference_time = (end_time - start_time) * 1000

    # --------------------------------------------------
    # Check detections
    # --------------------------------------------------

    if faces is None:
        print("No faces detected.")

        cv2.imshow("YuNet Detection", image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        return

    print(f"Faces detected: {len(faces)}")
    print(f"Inference time: {inference_time:.2f} ms")

    # --------------------------------------------------
    # Draw every detected face
    # --------------------------------------------------

    for index, face in enumerate(faces):

        x = int(face[0])
        y = int(face[1])
        w = int(face[2])
        h = int(face[3])

        confidence = float(face[14])

        print(
            f"Face {index + 1}: "
            f"x={x}, y={y}, "
            f"width={w}, height={h}, "
            f"confidence={confidence:.3f}"
        )

        # Bounding box
        cv2.rectangle(
            image,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

        # Face number + confidence
        label = f"Face {index + 1}: {confidence:.2f}"

        cv2.putText(
            image,
            label,
            (x, max(25, y - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

    # --------------------------------------------------
    # Display information
    # --------------------------------------------------

    cv2.putText(
        image,
        f"Faces: {len(faces)}",
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    cv2.putText(
        image,
        f"Inference: {inference_time:.2f} ms",
        (20, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )

    # --------------------------------------------------
    # Show result
    # --------------------------------------------------

    cv2.imshow("YuNet Face Detection", image)

    print("\nPress any key on the image window to close.")

    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()