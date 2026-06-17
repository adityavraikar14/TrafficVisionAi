"""Posture analysis using a pretrained COCO-pose model — distinguishes a
seated rider (knees bent, foot tucked near the footrest) from a standing
pedestrian (legs extended), which 2D bounding-box overlap alone cannot do
when a bystander happens to stand close behind a vehicle in-frame.
"""

HIP_IDX = (11, 12)
KNEE_IDX = (13, 14)
ANKLE_IDX = (15, 16)
KP_CONF_MIN = 0.3
SEATED_COMPRESSION_MAX = 0.62  # hip-to-ankle vertical span / bbox height


def _iou(a, b) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    inter = (ix2 - ix1) * (iy2 - iy1)
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    return inter / (area_a + area_b - inter) if (area_a + area_b - inter) else 0.0


def _avg_y(idx_pair, xy, conf):
    ys = [xy[i][1] for i in idx_pair if conf[i] >= KP_CONF_MIN]
    return sum(ys) / len(ys) if ys else None


def get_postures(pose_results) -> list[dict]:
    """One posture entry per detected person: box + 'seated'/'standing'/'unknown'."""
    boxes = pose_results[0].boxes
    keypoints = pose_results[0].keypoints
    if keypoints is None or len(boxes) == 0:
        return []

    xy_all = keypoints.xy.cpu().numpy()
    conf_all = keypoints.conf.cpu().numpy() if keypoints.conf is not None else None

    out = []
    for i in range(len(boxes)):
        box = [float(v) for v in boxes.xyxy[i]]
        xy = xy_all[i]
        conf = conf_all[i] if conf_all is not None else [1.0] * 17

        height = box[3] - box[1]
        hip_y = _avg_y(HIP_IDX, xy, conf)
        ankle_y = _avg_y(ANKLE_IDX, xy, conf)

        if hip_y is None or ankle_y is None or height <= 0:
            out.append({"box": box, "posture": "unknown", "compression_ratio": None})
            continue

        ratio = (ankle_y - hip_y) / height
        posture = "seated" if ratio < SEATED_COMPRESSION_MAX else "standing"
        out.append({"box": box, "posture": posture, "compression_ratio": round(ratio, 3)})

    return out


def match_posture(person_box, postures: list[dict], iou_threshold: float = 0.25) -> dict | None:
    best, best_iou = None, 0.0
    for p in postures:
        iou = _iou(person_box, p["box"])
        if iou > best_iou:
            best_iou, best = iou, p
    return best if best_iou >= iou_threshold else None
