import cv2
import numpy as np

COLOR_VIOLATION = (68, 68, 239)   # BGR red
COLOR_COMPLIANT = (94, 197, 34)   # BGR green
COLOR_RIDER = (248, 191, 56)      # BGR blue/amber mix
COLOR_PLATE = (240, 176, 0)       # BGR cyan-ish
COLOR_VEHICLE = (180, 180, 180)
COLOR_ZONE = (0, 140, 255)        # BGR orange
COLOR_LINE = (255, 255, 255)


def _annotation_scale(h: int, w: int) -> float:
    """Reference sizing is calibrated for ~640px images; scale text/line
    thickness down for smaller frames so labels don't overlap into
    illegible blobs, and up for larger ones so they stay readable."""
    return max(0.35, min(2.0, max(h, w) / 640))


def _rects_overlap(a, b) -> bool:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 <= bx1 or bx2 <= ax1 or ay2 <= by1 or by2 <= ay1)


def _place_label(x1, y1, tw, th, pad, placed):
    """Pick a label rect anchored above (x1, y1) that doesn't collide with
    already-placed labels, trying progressively lower slots first — dense
    scenes with adjacent boxes otherwise stack labels into an illegible blob."""
    step = th + pad
    rect = (x1, max(0, y1 - th - pad), x1 + tw + pad - 2, y1)
    for i in range(6):
        offset = i * step
        cand_y2 = max(th + pad, y1 - offset)
        cand_y1 = cand_y2 - th - pad
        rect = (x1, cand_y1, x1 + tw + pad - 2, cand_y2)
        if not any(_rects_overlap(rect, p) for p in placed):
            break
    placed.append(rect)
    return rect


def _draw_box(img, box, color, label, scale: float = 1.0, placed: list | None = None):
    x1, y1, x2, y2 = [int(v) for v in box]
    line_thickness = max(1, round(2 * scale))
    cv2.rectangle(img, (x1, y1), (x2, y2), color, line_thickness)
    if label:
        font_scale = 0.5 * scale
        text_thickness = max(1, round(2 * scale))
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_thickness)
        pad = max(2, round(8 * scale))
        rx1, ry1, rx2, ry2 = _place_label(x1, y1, tw, th, pad, placed if placed is not None else [])
        cv2.rectangle(img, (rx1, ry1), (rx2, ry2), color, -1)
        cv2.putText(img, label, (rx1 + 3, ry2 - pad // 2), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (15, 15, 15), text_thickness, cv2.LINE_AA)


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
    stunt_hits: list[dict] | None = None,
) -> np.ndarray:
    """Draw all detected entities on a copy of the original image:
    vehicle/road-user boxes (faint), triple-riding motorcycle boxes,
    helmet violations, the localized plate region, and any calibrated
    stop-line / no-parking-zone guides plus the violations they produced.
    """
    out = image_bgr.copy()
    h, w = out.shape[:2]
    scale = _annotation_scale(h, w)
    line_thickness = max(1, round(2 * scale))
    font_scale = 0.55 * scale
    text_thickness = max(1, round(2 * scale))
    placed: list = []

    if parking_zone:
        x1, y1, x2, y2 = parking_zone
        overlay = out.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), COLOR_ZONE, -1)
        out = cv2.addWeighted(overlay, 0.18, out, 0.82, 0)
        cv2.rectangle(out, (x1, y1), (x2, y2), COLOR_ZONE, line_thickness)
        label = "No-Parking Zone"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_thickness)
        pad = max(2, round(8 * scale))
        rx1, ry1, rx2, ry2 = _place_label(x1 + 6, y1 + th + pad, tw, th, pad, placed)
        cv2.putText(out, label, (rx1, ry2 - pad // 2), cv2.FONT_HERSHEY_SIMPLEX, font_scale, COLOR_ZONE, text_thickness, cv2.LINE_AA)

    if stop_line_y is not None:
        cv2.line(out, (0, stop_line_y), (w, stop_line_y), COLOR_LINE, line_thickness, cv2.LINE_AA)
        label = "Stop Line"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_thickness)
        pad = max(2, round(8 * scale))
        rx1, ry1, rx2, ry2 = _place_label(8, max(th + pad, stop_line_y), tw, th, pad, placed)
        cv2.putText(out, label, (rx1, ry2 - pad // 2), cv2.FONT_HERSHEY_SIMPLEX, font_scale, COLOR_LINE, text_thickness, cv2.LINE_AA)

    for det in vehicle_detections:
        _draw_box(out, det["box"], COLOR_VEHICLE, det["category"], scale, placed)

    for hit in triple_riding_hits:
        _draw_box(out, hit["box"], COLOR_RIDER, f"Triple Riding ({hit['rider_count']} riders)", scale, placed)

    for hit in (stunt_hits or []):
        _draw_box(out, hit["box"], COLOR_VIOLATION, f"Stunt Riding {hit['confidence']*100:.0f}%", scale, placed)

    for hit in (signal_hits or []):
        _draw_box(out, hit["box"], COLOR_VIOLATION, hit["violation_type"], scale, placed)

    for hit in (parking_hits or []):
        _draw_box(out, hit["box"], COLOR_VIOLATION, "Illegal Parking", scale, placed)

    for box_info in helmet_boxes:
        color = COLOR_VIOLATION if box_info["is_violation"] else COLOR_COMPLIANT
        label = f"{box_info['class_name']} {box_info['confidence']*100:.0f}%"
        _draw_box(out, box_info["box"], color, label, scale, placed)

    if plate_box:
        _draw_box(out, plate_box, COLOR_PLATE, "Plate", scale, placed)

    return out


def draw_wrong_side_evidence(
    frame_bgr: np.ndarray,
    violation: dict,
    correct_angle_deg: float,
) -> np.ndarray:
    """Evidence frame for a wrong-side violation: the vehicle's box, an
    arrow showing its actual travel path across the tracked frames, and a
    reference arrow in the corner showing the marked correct direction."""
    out = frame_bgr.copy()

    _draw_box(out, violation["box"], COLOR_VIOLATION, f"Wrong-Side Driving ({violation['class_name']})")

    fx, fy = (int(v) for v in violation["first_centroid"])
    lx, ly = (int(v) for v in violation["last_centroid"])
    cv2.arrowedLine(out, (fx, fy), (lx, ly), COLOR_VIOLATION, 3, tipLength=0.25)

    h, w = out.shape[:2]
    origin = (w - 70, 60)
    angle_rad = np.deg2rad(correct_angle_deg)
    end = (int(origin[0] + 45 * np.cos(angle_rad)), int(origin[1] + 45 * np.sin(angle_rad)))
    cv2.arrowedLine(out, origin, end, COLOR_COMPLIANT, 3, tipLength=0.3)
    cv2.putText(out, "Correct Direction", (w - 165, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_COMPLIANT, 2, cv2.LINE_AA)

    return out
