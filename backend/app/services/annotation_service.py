import cv2
import numpy as np

COLOR_VIOLATION = (68, 68, 239)   # BGR red
COLOR_COMPLIANT = (94, 197, 34)   # BGR green
COLOR_RIDER = (248, 191, 56)      # BGR blue/amber mix
COLOR_PLATE = (240, 176, 0)       # BGR cyan-ish
COLOR_VEHICLE = (180, 180, 180)
COLOR_ZONE = (0, 140, 255)        # BGR orange
COLOR_LINE = (255, 255, 255)


def _draw_box(img, box, color, label):
    x1, y1, x2, y2 = [int(v) for v in box]
    cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
    if label:
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        cv2.rectangle(img, (x1, max(0, y1 - th - 8)), (x1 + tw + 6, y1), color, -1)
        cv2.putText(img, label, (x1 + 3, max(12, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (15, 15, 15), 2, cv2.LINE_AA)


def draw_annotations(
    image_bgr: np.ndarray,
    helmet_boxes: list[dict],
    triple_riding_hits: list[dict],
    vehicle_detections: list[dict],
    plate_box: list[int] | None,
    signal_hits: list[dict] | None = None,
    parking_hits: list[dict] | None = None,
    stop_line_y: int | None = None,
    parking_zone: tuple[int, int, int, int] | None = None,
) -> np.ndarray:
    """Draw all detected entities on a copy of the original image:
    vehicle/road-user boxes (faint), triple-riding motorcycle boxes,
    helmet violations, the localized plate region, and any calibrated
    stop-line / no-parking-zone guides plus the violations they produced.
    """
    out = image_bgr.copy()
    h, w = out.shape[:2]

    if parking_zone:
        x1, y1, x2, y2 = parking_zone
        overlay = out.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), COLOR_ZONE, -1)
        out = cv2.addWeighted(overlay, 0.18, out, 0.82, 0)
        cv2.rectangle(out, (x1, y1), (x2, y2), COLOR_ZONE, 2)
        cv2.putText(out, "No-Parking Zone", (x1 + 6, y1 + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, COLOR_ZONE, 2, cv2.LINE_AA)

    if stop_line_y is not None:
        cv2.line(out, (0, stop_line_y), (w, stop_line_y), COLOR_LINE, 2, cv2.LINE_AA)
        cv2.putText(out, "Stop Line", (8, max(18, stop_line_y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, COLOR_LINE, 2, cv2.LINE_AA)

    for det in vehicle_detections:
        _draw_box(out, det["box"], COLOR_VEHICLE, det["category"])

    for hit in triple_riding_hits:
        _draw_box(out, hit["box"], COLOR_RIDER, f"Triple Riding ({hit['rider_count']} riders)")

    for hit in (signal_hits or []):
        _draw_box(out, hit["box"], COLOR_VIOLATION, hit["violation_type"])

    for hit in (parking_hits or []):
        _draw_box(out, hit["box"], COLOR_VIOLATION, "Illegal Parking")

    for box_info in helmet_boxes:
        color = COLOR_VIOLATION if box_info["is_violation"] else COLOR_COMPLIANT
        label = f"{box_info['class_name']} {box_info['confidence']*100:.0f}%"
        _draw_box(out, box_info["box"], color, label)

    if plate_box:
        _draw_box(out, plate_box, COLOR_PLATE, "Plate")

    return out
