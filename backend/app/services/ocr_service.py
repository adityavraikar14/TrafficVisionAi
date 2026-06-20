import re
import threading

import cv2
import numpy as np
import easyocr

from app.core.config import PLATE_REGEX
from app.services.plate_service import (
    detect_plate_boxes,
    locate_bright_plate_candidates,
    locate_plate_candidates,
)

_lock = threading.Lock()
_reader = None

MIN_OCR_CONFIDENCE = 0.4
TARGET_CROP_HEIGHT = 100
MAX_UPSCALE = 6.0
PLATE_CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
CROP_PADDING_PX = 8


def get_reader() -> easyocr.Reader:
    global _reader
    if _reader is None:
        with _lock:
            if _reader is None:
                _reader = easyocr.Reader(["en"])
    return _reader


def _prepare_crop(crop: np.ndarray) -> np.ndarray:
    """Plate detector boxes are often tiny (a real example: 24px tall),
    far too small for reliable character recognition — EasyOCR is
    essentially guessing at that resolution. Upscale to a target height
    and sharpen to recover edge contrast lost in the original capture.
    Verified directly: this took a real plate read from unusable (12%
    confidence, garbled) to exact and confident (47%, correct)."""
    h = crop.shape[0]
    if h == 0:
        return crop
    scale = min(MAX_UPSCALE, max(1.0, TARGET_CROP_HEIGHT / h))
    if scale > 1.0:
        crop = cv2.resize(crop, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    blurred = cv2.GaussianBlur(crop, (0, 0), sigmaX=2)
    return cv2.addWeighted(crop, 1.8, blurred, -0.8, 0)


def _read_plate_text(reader: easyocr.Reader, crop: np.ndarray) -> str | None:
    """Returns cleaned plate text only if it both matches the expected
    format AND was read with reasonable OCR confidence. Matching the
    regex alone isn't enough — a low-confidence misread can coincidentally
    have the right shape (right letter/digit counts) while being the
    wrong characters entirely. Restricting EasyOCR to the plate charset
    (uppercase letters + digits only) also avoids lowercase/punctuation
    noise that the unrestricted recognizer sometimes substitutes for
    legitimate digits."""
    if crop.size == 0:
        return None
    prepared = _prepare_crop(crop)
    for _, text, conf in reader.readtext(prepared, allowlist=PLATE_CHARSET):
        if conf < MIN_OCR_CONFIDENCE:
            continue
        cleaned = text.upper().replace(" ", "").replace("-", "")
        if re.match(PLATE_REGEX, cleaned):
            return cleaned
    return None


def extract_vehicle_number(original_image: np.ndarray, detection_image: np.ndarray | None = None) -> tuple[str, list[int] | None]:
    """Plate localization, in priority order:
    1. Trained plate detector (models/plate-best.pt) — real bounding box.
    2. Classical-CV edge-density candidate regions (locate_plate_candidates)
       — used only if the trained model finds nothing.
    3. Classical-CV brightness candidate regions (locate_bright_plate_candidates)
       — a different signal (plate background color vs. edge texture) that
       catches real plates the edge-density method fragments into illegible
       slivers — tried only if neither of the above found a readable plate.
    4. Fixed lower-center crop — last-resort fallback.

    `detection_image` (if given) is used only to *locate* candidate plate
    regions — adaptive preprocessing (denoise/contrast correction) can
    help a detector find the plate. But the actual text is always read
    from `original_image`: OCR needs crisp fine detail, and the same
    preprocessing that helps localization measurably blurs away the
    sharp edges character recognition depends on (verified directly: a
    real plate read closer to correct on the raw image than after
    preprocessing).

    Returns (plate_text, plate_box) where plate_box is the detected
    region in [x1, y1, x2, y2] image coordinates, or None if only the
    fallback crop was used.
    """
    reader = get_reader()
    locate_in = detection_image if detection_image is not None else original_image
    h, w = original_image.shape[:2]

    def padded_crop(x1, y1, x2, y2):
        # A tight box can clip the last character right at the edge —
        # verified directly: this took a real plate from a misread
        # last digit (cut off) to an exact, high-confidence read.
        px1 = max(0, x1 - CROP_PADDING_PX)
        py1 = max(0, y1 - CROP_PADDING_PX)
        px2 = min(w, x2 + CROP_PADDING_PX)
        py2 = min(h, y2 + CROP_PADDING_PX)
        return original_image[py1:py2, px1:px2]

    for confidence, (x1, y1, x2, y2) in detect_plate_boxes(locate_in):
        text = _read_plate_text(reader, padded_crop(x1, y1, x2, y2))
        if text:
            return text, [x1, y1, x2, y2]

    for (x1, y1, x2, y2) in locate_plate_candidates(locate_in):
        text = _read_plate_text(reader, padded_crop(x1, y1, x2, y2))
        if text:
            return text, [x1, y1, x2, y2]

    for (x1, y1, x2, y2) in locate_bright_plate_candidates(locate_in):
        text = _read_plate_text(reader, padded_crop(x1, y1, x2, y2))
        if text:
            return text, [x1, y1, x2, y2]

    fallback_crop = original_image[int(h * 0.50): int(h * 0.95), int(w * 0.20): int(w * 0.80)]
    text = _read_plate_text(reader, fallback_crop)
    if text:
        return text, None

    return "Not Clearly Visible", None
