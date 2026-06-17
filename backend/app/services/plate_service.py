import cv2
import numpy as np

MIN_ASPECT = 1.8
MAX_ASPECT = 6.0
MIN_AREA_RATIO = 0.001
MAX_AREA_RATIO = 0.08


def locate_plate_candidates(image_bgr: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Classical CV plate-region localization: find rectangular,
    high-edge-density regions with a plausible plate aspect ratio in the
    lower half of the frame (where plates sit on two-wheelers/cars).

    This replaces a blind fixed-percentage crop with an actual detected
    bounding box — no trained plate detector required. Returns candidate
    boxes ordered by how plate-like they look (most likely first).
    """
    h, w = image_bgr.shape[:2]
    lower = image_bgr[int(h * 0.35):, :]
    offset_y = int(h * 0.35)

    gray = cv2.cvtColor(lower, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    edges = cv2.Canny(gray, 30, 200)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((3, 9), np.uint8))

    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    frame_area = h * w
    candidates = []

    for contour in contours:
        x, y, cw, ch = cv2.boundingRect(contour)
        if ch == 0:
            continue
        aspect = cw / ch
        area_ratio = (cw * ch) / frame_area

        if MIN_ASPECT <= aspect <= MAX_ASPECT and MIN_AREA_RATIO <= area_ratio <= MAX_AREA_RATIO:
            score = area_ratio * (1.0 / (1.0 + abs(aspect - 3.2)))
            candidates.append((score, (x, y + offset_y, x + cw, y + offset_y + ch)))

    candidates.sort(key=lambda c: c[0], reverse=True)
    return [box for _, box in candidates[:5]]
