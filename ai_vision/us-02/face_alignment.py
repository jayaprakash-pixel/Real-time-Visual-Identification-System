import cv2
import numpy as np


# Standard landmark positions for a 112 x 112 aligned face.
# These are TARGET positions, not landmarks detected from the camera.
REFERENCE_POINTS = np.array(
    [
        [38.2946, 51.6963],  # Left eye
        [73.5318, 51.5014],  # Right eye
        [56.0252, 71.7366],  # Nose
        [41.5493, 92.3655],  # Left mouth corner
        [70.7299, 92.2041],  # Right mouth corner
    ],
    dtype=np.float32
)


def align_face(frame, landmarks, output_size=(112, 112)):
    """
    Align a face using the five landmarks detected by YuNet.

    Parameters:
        frame:
            Original camera frame.

        landmarks:
            Five facial landmarks obtained from YuNet.

        output_size:
            Size of the aligned face.

    Returns:
        aligned_face:
            112 x 112 aligned face image.
            Returns None if alignment fails.
    """

    # Make sure landmarks are in the correct NumPy format
    landmarks = np.asarray(landmarks, dtype=np.float32)

    # We expect exactly 5 points:
    # left eye, right eye, nose, left mouth, right mouth
    if landmarks.shape != (5, 2):
        print("Invalid landmark shape:", landmarks.shape)
        return None

    # Calculate transformation from:
    #
    # YuNet detected landmarks
    #          ↓
    # standard reference positions
    #
    transform_matrix, _ = cv2.estimateAffinePartial2D(
        landmarks,
        REFERENCE_POINTS
    )

    # Alignment failed
    if transform_matrix is None:
        return None

    # Apply the transformation
    aligned_face = cv2.warpAffine(
        frame,
        transform_matrix,
        output_size
    )

    return aligned_face