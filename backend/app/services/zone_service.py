"""Zone-based violation rules: stop-line / red-light and illegal-parking.

These require per-camera calibration (where is the stop line? where is the
restricted zone?) which a single still image can't infer on its own — a
real deployment would pull this from a one-time camera-setup step, and
signal state from a live signal-controller feed. Here both are supplied
by the operator at request time (see api/routes/detect.py), and the
detection logic itself — geometric crossing/overlap against detected
vehicle boxes — is real.
"""

VEHICLE_CATEGORIES = {"Two-Wheeler", "Car", "Bus", "Truck"}
STOP_LINE_BAND_PX = 28


def line_y_px(y_percent: float, height: int) -> int:
    return int(height * max(0.0, min(100.0, y_percent)) / 100)


def zone_rect_px(top: float, bottom: float, left: float, right: float, width: int, height: int):
    x1 = int(width * max(0.0, min(100.0, left)) / 100)
    x2 = int(width * max(0.0, min(100.0, right)) / 100)
    y1 = int(height * max(0.0, min(100.0, top)) / 100)
    y2 = int(height * max(0.0, min(100.0, bottom)) / 100)
    return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))


def _overlap_ratio(box, rect) -> float:
    bx1, by1, bx2, by2 = box
    rx1, ry1, rx2, ry2 = rect
    ix1, iy1 = max(bx1, rx1), max(by1, ry1)
    ix2, iy2 = min(bx2, rx2), min(by2, ry2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    inter = (ix2 - ix1) * (iy2 - iy1)
    box_area = (bx2 - bx1) * (by2 - by1)
    return inter / box_area if box_area else 0.0


def detect_signal_violations(vehicle_detections, line_y: int, signal_state: str) -> list[dict]:
    """A vehicle whose front edge sits within STOP_LINE_BAND_PX of the line
    is a Stop-Line Violation (stopped/positioned past the marked line).
    A vehicle fully past the line while signal_state == 'red' is a
    Red-Light Violation (proceeded through on red)."""
    hits = []
    for det in vehicle_detections:
        if det["category"] not in VEHICLE_CATEGORIES:
            continue
        x1, y1, x2, y2 = det["box"]

        if y1 <= line_y <= y2 or (line_y - STOP_LINE_BAND_PX <= y2 <= line_y + STOP_LINE_BAND_PX):
            hits.append({"violation_type": "Stop-Line Violation", "confidence": det["confidence"], "box": det["box"]})
        elif y2 > line_y + STOP_LINE_BAND_PX and signal_state == "red":
            hits.append({"violation_type": "Red-Light Violation", "confidence": det["confidence"], "box": det["box"]})

    return hits


def detect_illegal_parking(vehicle_detections, zone_rect, min_overlap: float = 0.45) -> list[dict]:
    hits = []
    for det in vehicle_detections:
        if det["category"] not in VEHICLE_CATEGORIES:
            continue
        if _overlap_ratio(det["box"], zone_rect) >= min_overlap:
            hits.append({"violation_type": "Illegal Parking", "confidence": det["confidence"], "box": det["box"]})
    return hits
