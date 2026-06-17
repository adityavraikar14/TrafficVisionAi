import re
import threading

import numpy as np
import easyocr

from app.core.config import PLATE_REGEX
from app.services.plate_service import locate_plate_candidates

_lock = threading.Lock()
_reader = None


def get_reader() -> easyocr.Reader:
    global _reader
    if _reader is None:
        with _lock:
            if _reader is None:
                _reader = easyocr.Reader(["en"])
    return _reader


def _read_plate_text(reader: easyocr.Reader, crop: np.ndarray) -> str | None:
    if crop.size == 0:
        return None
    for _, text, _conf in reader.readtext(crop):
        cleaned = text.upper().replace(" ", "").replace("-", "")
        if re.match(PLATE_REGEX, cleaned):
            return cleaned
    return None


def extract_vehicle_number(image: np.ndarray) -> tuple[str, list[int] | None]:
    """Locate plate-shaped candidate regions via classical CV (see
    plate_service.py) and OCR each in score order. Falls back to a
    fixed lower-center crop if no candidate region produces a valid read.

    Returns (plate_text, plate_box) where plate_box is the detected
    region in [x1, y1, x2, y2] image coordinates, or None if only the
    fallback crop was used.
    """
    reader = get_reader()
    h, w = image.shape[:2]

    for (x1, y1, x2, y2) in locate_plate_candidates(image):
        crop = image[y1:y2, x1:x2]
        text = _read_plate_text(reader, crop)
        if text:
            return text, [x1, y1, x2, y2]

    fallback_crop = image[int(h * 0.50): int(h * 0.95), int(w * 0.20): int(w * 0.80)]
    text = _read_plate_text(reader, fallback_crop)
    if text:
        return text, None

    return "Not Clearly Visible", None
