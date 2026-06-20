import threading

import cv2
import numpy as np
from ultralytics import YOLO

from app.core.config import PLATE_MODEL_PATH

MIN_ASPECT = 1.8
MAX_ASPECT = 6.0
MIN_AREA_RATIO = 0.001
MAX_AREA_RATIO = 0.08
PLATE_MODEL_MIN_CONFIDENCE = 0.35

_lock = threading.Lock()
_plate_model = None


def get_plate_model() -> YOLO:
    global _plate_model
    if _plate_model is None:
        with _lock:
            if _plate_model is None:
                _plate_model = YOLO(PLATE_MODEL_PATH)
    return _plate_model


def detect_plate_boxes(image_bgr: np.ndarray) -> list[tuple[float, list[int]]]:
    """Real trained plate detector (models/plate-best.pt). Returns
    (confidence, [x1,y1,x2,y2]) pairs sorted by confidence, highest first."""
    model = get_plate_model()
    results = model(image_bgr, verbose=False)

    boxes = []
    for box in results[0].boxes:
        confidence = float(box.conf)
        if confidence < PLATE_MODEL_MIN_CONFIDENCE:
            continue
        xyxy = [int(v) for v in box.xyxy[0]]
        boxes.append((confidence, xyxy))

    boxes.sort(key=lambda b: b[0], reverse=True)
    return boxes


def locate_plate_candidates(image_bgr: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Fallback classical-CV plate-region localization (no trained model
    needed): find rectangular, high-edge-density regions with a plausible
    plate aspect ratio in the lower half of the frame. Used only if the
    trained detector finds nothing — keeps the pipeline working even on
    plates the model wasn't trained to see."""
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


BRIGHT_THRESHOLD = 205


def locate_bright_plate_candidates(image_bgr: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Second classical fallback: find bright (white/light-colored) plausible
    plate-aspect rectangles in the lower half of the frame. Indian plates are
    characteristically white or yellow backgrounds with dark text — a
    brightness threshold is a different, complementary signal from the
    edge-density one above, and catches real plates the edge-contour method
    fragments into illegible slivers (verified directly: recovered an exact
    plate read on a photo where the edge-based method found nothing usable,
    with no false positives introduced on any other test photo)."""
    h, w = image_bgr.shape[:2]
    lower = image_bgr[int(h * 0.35):, :]
    offset_y = int(h * 0.35)

    gray = cv2.cvtColor(lower, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, BRIGHT_THRESHOLD, 255, cv2.THRESH_BINARY)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, np.ones((3, 5), np.uint8))

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    frame_area = h * w
    candidates = []

    for contour in contours:
        x, y, cw, ch = cv2.boundingRect(contour)
        if ch == 0:
            continue
        aspect = cw / ch
        area_ratio = (cw * ch) / frame_area

        if MIN_ASPECT <= aspect <= MAX_ASPECT and 0.0008 <= area_ratio <= MAX_AREA_RATIO:
            score = area_ratio * (1.0 / (1.0 + abs(aspect - 3.2)))
            candidates.append((score, (x, y + offset_y, x + cw, y + offset_y + ch)))

    candidates.sort(key=lambda c: c[0], reverse=True)
    return [box for _, box in candidates[:8]]
