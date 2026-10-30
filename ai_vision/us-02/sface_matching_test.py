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
# Test images
# --------------------------------------------------

IMAGE_1 = "image_01.jpg"
IMAGE_2 = "image_03.jpg"

# Later, we will test:
#
# IMAGE_1 = "person1_a.jpg"
# IMAGE_2 = "person2.jpg"


# --------------------------------------------------
# YuNet settings
# --------------------------------------------------

CONFIDENCE_THRESHOLD = 0.6
NMS_THRESHOLD = 0.3
TOP_K = 5000


# --------------------------------------------------
# Load models
# --------------------------------------------------

def load_models():

    print("Loading YuNet...")

    detector = cv2.FaceDetectorYN.create(
        YUNET_MODEL,
        "",
        (320, 320),
        CONFIDENCE_THRESHOLD,
        NMS_THRESHOLD,
        TOP_K
    )

    print("YuNet loaded.")

    print("Loading SFace...")

    recognizer = cv2.FaceRecognizerSF.create(
        SFACE_MODEL,
        ""
    )

    print("SFace loaded.")

    return detector, recognizer


# --------------------------------------------------
# Generate embedding from an image
# --------------------------------------------------

def get_embedding(image_path, detector, recognizer):

    print()
    print("----------------------------------------")
    print("Processing:", image_path)
    print("----------------------------------------")

    # --------------------------------------------------
    # Read image
    # --------------------------------------------------

    image = cv2.imread(image_path)

    if image is None:

        print("ERROR: Could not read image.")
        return None

    height, width = image.shape[:2]

    print(
        f"Image size: "
        f"{width} x {height}"
    )

    # --------------------------------------------------
    # Update YuNet input size
    # --------------------------------------------------

    detector.setInputSize(
        (width, height)
    )

    # --------------------------------------------------
    # Detect face
    # --------------------------------------------------

    _, faces = detector.detect(image)

    if faces is None or len(faces) == 0:

        print("ERROR: No face detected.")
        return None

    print(
        f"Faces detected: "
        f"{len(faces)}"
    )

    # --------------------------------------------------
    # Select the largest face
    #
    # For this test we assume the main
    # person is the largest face.
    # --------------------------------------------------

    largest_face = max(
        faces,
        key=lambda face: face[2] * face[3]
    )

    confidence = float(
        largest_face[14]
    )

    print(
        f"Selected face confidence: "
        f"{confidence:.4f}"
    )

    # --------------------------------------------------
    # Align face using SFace's
    # official alignment
    # --------------------------------------------------

    aligned_face = recognizer.alignCrop(
        image,
        largest_face
    )

    if aligned_face is None:

        print("ERROR: Face alignment failed.")
        return None

    print(
        "Face aligned:",
        aligned_face.shape[1],
        "x",
        aligned_face.shape[0]
    )

    # --------------------------------------------------
    # Generate embedding
    # --------------------------------------------------

    start = cv2.getTickCount()

    feature = recognizer.feature(
        aligned_face
    )

    end = cv2.getTickCount()

    inference_time = (
        (end - start)
        / cv2.getTickFrequency()
    ) * 1000

    if feature is None:

        print(
            "ERROR: Could not generate embedding."
        )

        return None

    print(
        f"Embedding inference time: "
        f"{inference_time:.2f} ms"
    )

    print(
        "Embedding shape:",
        feature.shape
    )

    return feature


# --------------------------------------------------
# Calculate cosine similarity
# --------------------------------------------------

def cosine_similarity(embedding1, embedding2):

    vector1 = embedding1.flatten()
    vector2 = embedding2.flatten()

    numerator = np.dot(
        vector1,
        vector2
    )

    denominator = (
        np.linalg.norm(vector1)
        *
        np.linalg.norm(vector2)
    )

    if denominator == 0:

        return 0.0

    similarity = numerator / denominator

    return float(similarity)


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    print("========================================")
    print("SFace Face Matching Test")
    print("========================================")

    # --------------------------------------------------
    # Check models
    # --------------------------------------------------

    if not os.path.exists(YUNET_MODEL):

        print("ERROR: YuNet model not found.")
        print(YUNET_MODEL)
        return

    if not os.path.exists(SFACE_MODEL):

        print("ERROR: SFace model not found.")
        print(SFACE_MODEL)
        return

    # --------------------------------------------------
    # Check images
    # --------------------------------------------------

    if not os.path.exists(IMAGE_1):

        print("ERROR: Image 1 not found.")
        print(IMAGE_1)
        return

    if not os.path.exists(IMAGE_2):

        print("ERROR: Image 2 not found.")
        print(IMAGE_2)
        return

    # --------------------------------------------------
    # Load models
    # --------------------------------------------------

    detector, recognizer = load_models()

    # --------------------------------------------------
    # Generate embedding 1
    # --------------------------------------------------

    embedding1 = get_embedding(
        IMAGE_1,
        detector,
        recognizer
    )

    if embedding1 is None:
        return

    # --------------------------------------------------
    # Generate embedding 2
    # --------------------------------------------------

    embedding2 = get_embedding(
        IMAGE_2,
        detector,
        recognizer
    )

    if embedding2 is None:
        return

    # --------------------------------------------------
    # Compare embeddings
    # --------------------------------------------------

    print()
    print("========================================")
    print("Comparing Faces")
    print("========================================")

    similarity = cosine_similarity(
        embedding1,
        embedding2
    )

    print(
        f"Cosine similarity: "
        f"{similarity:.4f}"
    )

    # --------------------------------------------------
    # IMPORTANT:
    # Do NOT use a final threshold yet.
    # --------------------------------------------------

    print()
    print(
        "No match threshold is being applied yet."
    )

    print(
        "We first need to collect similarity"
    )

    print(
        "scores from multiple same-person and"
    )

    print(
        "different-person image pairs."
    )

    print()
    print("Test completed.")


# --------------------------------------------------
# Program entry point
# --------------------------------------------------

if __name__ == "__main__":
    main()