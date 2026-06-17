CATEGORY_MAP = {
    "motorcycle": "Two-Wheeler",
    "bicycle": "Two-Wheeler",
    "car": "Car",
    "bus": "Bus",
    "truck": "Truck",
    "person": "Pedestrian / Rider",
}

VEHICLE_MIN_CONFIDENCE = 0.35
MERGE_CATEGORIES = {"Two-Wheeler", "Car", "Bus", "Truck"}


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


def _close(a, b, gap_ratio: float = 0.12) -> bool:
    """True if two boxes overlap at all, or sit close enough together that
    they're almost certainly the same physical vehicle split into two
    detections by occlusion (e.g. a rider's body covering the middle of a
    scooter)."""
    if _iou(a, b) > 0:
        return True
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    gap_x = max(bx1 - ax2, ax1 - bx2, 0)
    gap_y = max(by1 - ay2, ay1 - by2, 0)
    scale = max(ax2 - ax1, ay2 - ay1, bx2 - bx1, by2 - by1)
    return gap_x < scale * gap_ratio and gap_y < scale * gap_ratio


def _merge_category(dets: list[dict]) -> list[dict]:
    """Union overlapping/adjacent same-category boxes into one detection,
    keeping the highest confidence. Prevents one physical vehicle that got
    split into two overlapping boxes (common with partial occlusion) from
    being counted, and acted on, twice."""
    merged: list[dict] = []
    used = [False] * len(dets)

    for i, det in enumerate(dets):
        if used[i]:
            continue
        group = [det]
        used[i] = True
        changed = True
        while changed:
            changed = False
            for j, other in enumerate(dets):
                if used[j]:
                    continue
                if any(_close(g["box"], other["box"]) for g in group):
                    group.append(other)
                    used[j] = True
                    changed = True

        x1 = min(g["box"][0] for g in group)
        y1 = min(g["box"][1] for g in group)
        x2 = max(g["box"][2] for g in group)
        y2 = max(g["box"][3] for g in group)
        best = max(group, key=lambda g: g["confidence"])
        merged.append({**best, "box": [x1, y1, x2, y2]})

    return merged


def classify_frame(model, results) -> dict:
    """Classify every detection from the stock COCO model into the road-user
    categories the problem statement asks for (vehicles, riders, pedestrians),
    with per-detection confidence scores. Same-category vehicle boxes that
    overlap or sit immediately adjacent are merged first (see _merge_category)
    so a single partially-occluded vehicle isn't double-counted.
    """
    by_category: dict[str, list[dict]] = {}

    for box in results[0].boxes:
        class_id = int(box.cls)
        class_name = model.names[class_id]
        confidence = float(box.conf)

        if confidence < VEHICLE_MIN_CONFIDENCE:
            continue

        category = CATEGORY_MAP.get(class_name)
        if category is None:
            continue

        xyxy = [round(float(v), 1) for v in box.xyxy[0]]
        by_category.setdefault(category, []).append(
            {"category": category, "class_name": class_name, "confidence": round(confidence, 4), "box": xyxy}
        )

    detections = []
    counts: dict = {}
    for category, dets in by_category.items():
        merged = _merge_category(dets) if category in MERGE_CATEGORIES else dets
        detections.extend(merged)
        counts[category] = len(merged)

    vehicles_detected = sum(v for k, v in counts.items() if k != "Pedestrian / Rider")

    return {
        "detections": detections,
        "counts": counts,
        "total_road_users": len(detections),
        "vehicles_detected": vehicles_detected,
    }
