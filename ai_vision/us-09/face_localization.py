"""
US-09: Missing-person localisation.

Converts a face bounding box into a position the operator can understand:
pixel bbox, centre point, normalised centre (0..1, independent of camera
resolution) and a 3x3 zone such as "top-left" or "middle-center".
"""


def locate_face(bbox, frame_shape):
    x, y, w, h = bbox
    frame_height, frame_width = frame_shape[:2]

    center_x = x + w / 2
    center_y = y + h / 2

    norm_x = min(max(center_x / frame_width, 0.0), 1.0)
    norm_y = min(max(center_y / frame_height, 0.0), 1.0)

    rows = ("top", "middle", "bottom")
    cols = ("left", "center", "right")
    zone = f"{rows[min(int(norm_y * 3), 2)]}-{cols[min(int(norm_x * 3), 2)]}"

    return {
        "bbox": [int(x), int(y), int(w), int(h)],
        "center": [int(center_x), int(center_y)],
        "center_normalized": [round(norm_x, 3), round(norm_y, 3)],
        "zone": zone,
        "frame_size": [int(frame_width), int(frame_height)],
    }


if __name__ == "__main__":
    assert locate_face((0, 0, 60, 60), (480, 640))["zone"] == "top-left"
    assert locate_face((290, 210, 60, 60), (480, 640))["zone"] == "middle-center"
    assert locate_face((600, 440, 40, 40), (480, 640))["zone"] == "bottom-right"
    print("US-09 localization: all checks passed")
