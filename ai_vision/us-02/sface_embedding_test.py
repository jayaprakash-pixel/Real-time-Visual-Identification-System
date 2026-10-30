import cv2
import os
import numpy as np

# Run from this folder so relative model/image paths work from anywhere
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# --------------------------------------------------
# Model paths
# --------------------------------------------------

YUNET_MODEL = (
    "models/yunet/"
    "face_detection_yunet_2023mar.onnx"
)

SFACE_MODEL = (
    "models/sface/"
    "face_recognition_sface_2021dec.onnx"
)

# --------------------------------------------------
# Test image
# --------------------------------------------------

IMAGE_PATH = "test.jpg"

# --------------------------------------------------
# YuNet settings
# --------------------------------------------------

CONFIDENCE_THRESHOLD = 0.6
NMS_THRESHOLD = 0.3
TOP_K = 5000


def main():

    print("Starting SFace embedding test...")

    # --------------------------------------------------
    # Check files
    # --------------------------------------------------

    if not os.path.exists(YUNET_MODEL):

        print("ERROR: YuNet model not found.")
        print(YUNET_MODEL)

        return

    if not os.path.exists(SFACE_MODEL):

        print("ERROR: SFace model not found.")
        print(SFACE_MODEL)

        return

    if not os.path.exists(IMAGE_PATH):

        print("ERROR: Test image not found.")
        print(IMAGE_PATH)

        return

    print("All required files found.")

    # --------------------------------------------------
    # Load image
    # --------------------------------------------------

    image = cv2.imread(IMAGE_PATH)

    if image is None:

        print("ERROR: Could not read image.")

        return

    height, width = image.shape[:2]

    print(f"Image size: {width} x {height}")

    # --------------------------------------------------
    # Create YuNet detector
    # --------------------------------------------------

    print("Loading YuNet...")

    detector = cv2.FaceDetectorYN.create(
        YUNET_MODEL,
        "",
        (width, height),
        CONFIDENCE_THRESHOLD,
        NMS_THRESHOLD,
        TOP_K
    )

    print("YuNet loaded.")

    # --------------------------------------------------
    # Detect face
    # --------------------------------------------------

    print("Detecting face...")

    _, faces = detector.detect(image)

    if faces is None or len(faces) == 0:

        print("ERROR: No face detected.")

        return

    print(f"Faces detected: {len(faces)}")

    # --------------------------------------------------
    # Load SFace
    # --------------------------------------------------

    print("Loading SFace...")

    recognizer = cv2.FaceRecognizerSF.create(
        SFACE_MODEL,
        ""
    )

    print("SFace loaded.")

    # --------------------------------------------------
    # Process each detected face
    # --------------------------------------------------

    for index, face in enumerate(faces):

        print()
        print("----------------------------------------")
        print(f"Processing Face {index + 1}")
        print("----------------------------------------")

        # --------------------------------------------------
        # Face information
        # --------------------------------------------------

        x = int(face[0])
        y = int(face[1])
        w = int(face[2])
        h = int(face[3])

        confidence = float(face[14])

        print(
            f"Bounding box: "
            f"x={x}, y={y}, "
            f"width={w}, height={h}"
        )

        print(f"YuNet confidence: {confidence:.4f}")

        # --------------------------------------------------
        # SFace official alignment
        #
        # YuNet face contains:
        #
        # [0:4]   -> bounding box
        # [4:14]  -> 5 landmarks
        # [14]    -> confidence
        # --------------------------------------------------

        start_alignment = cv2.getTickCount()

        aligned_face = recognizer.alignCrop(
            image,
            face
        )

        end_alignment = cv2.getTickCount()

        alignment_time = (
            (end_alignment - start_alignment)
            / cv2.getTickFrequency()
        ) * 1000

        print(
            f"Alignment time: "
            f"{alignment_time:.2f} ms"
        )

        if aligned_face is None:

            print("ERROR: Face alignment failed.")

            continue

        print(
            "Aligned face size:",
            aligned_face.shape[1],
            "x",
            aligned_face.shape[0]
        )

        # --------------------------------------------------
        # Generate SFace embedding
        # --------------------------------------------------

        start_embedding = cv2.getTickCount()

        feature = recognizer.feature(
            aligned_face
        )

        end_embedding = cv2.getTickCount()

        embedding_time = (
            (end_embedding - start_embedding)
            / cv2.getTickFrequency()
        ) * 1000

        # --------------------------------------------------
        # Validate embedding
        # --------------------------------------------------

        if feature is None:

            print("ERROR: SFace failed to generate embedding.")

            continue

        print(
            f"Embedding inference time: "
            f"{embedding_time:.2f} ms"
        )

        print(
            "Embedding shape:",
            feature.shape
        )

        print(
            "Embedding data type:",
            feature.dtype
        )

        # --------------------------------------------------
        # Print first few values
        # --------------------------------------------------

        print("First 10 embedding values:")

        print(feature[0][:10])

        # --------------------------------------------------
        # Calculate vector norm
        # --------------------------------------------------

        norm = np.linalg.norm(feature)

        print(
            f"Embedding L2 norm: "
            f"{norm:.6f}"
        )

        # --------------------------------------------------
        # Display aligned face
        # --------------------------------------------------

        cv2.imshow(
            f"SFace Aligned Face {index + 1}",
            aligned_face
        )

    # --------------------------------------------------
    # Display original image
    # --------------------------------------------------

    cv2.imshow(
        "Original Image",
        image
    )

    print()
    print("----------------------------------------")
    print("Embedding test completed.")
    print("Press any key to close.")
    print("----------------------------------------")

    cv2.waitKey(0)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()