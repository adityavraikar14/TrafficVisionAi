CATEGORY_MAP = {
    "motorcycle": "Two-Wheeler",
    "bicycle": "Two-Wheeler",
    "car": "Car",
    "bus": "Bus",
    "truck": "Truck",
    "person": "_person",  # refined into Rider / Pedestrian below
}

VEHICLE_MIN_CONFIDENCE = 0.35
MERGE_CATEGORIES = {"Two-Wheeler", "Car", "Bus", "Truck"}
RIDER_CONTAINMENT_THRESHOLD = 0.40
RIDER_EXPAND_RATIO = 0.08

# NOTE on "drivers": for cars/buses/trucks in third-person street-camera
# footage, the driver is almost never a separately visible/detectable
# person (occluded by the cabin/windshield) — so we don't attempt to label
# a "Driver" category here. Auto-labeling anyone near a car as a driver
# would mostly mislabel pedestrians and bystanders. Riders on two-wheelers
# ARE visibly distinguishable from pedestrians, so that split is real.


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


MERGE_MIN_IOU = 0.05


def _close(a, b) -> bool:
    """True only if two boxes genuinely overlap — the signature of one
    physical vehicle split into two detections by occlusion (e.g. a
    rider's body covering the middle of a scooter; the two visible
    fragments still overlap at that point).

    Deliberately does NOT treat "merely nearby" as close: in a dense
    parking row, every distinct vehicle sits close to its neighbor, and
    a proximity-based rule chains them all into one nonsensical mega-box
    (verified directly: this previously merged ~5 separately-parked
    motorcycles into a single fake "vehicle," which then triggered a
    false Triple Riding violation on pedestrians walking past). Requiring
    real overlap avoids that failure mode while still catching the
    one-vehicle-split-by-occlusion case, which does overlap."""
    return _iou(a, b) > MERGE_MIN_IOU


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


def _horizontal_containment(person_box, vehicle_box) -> float:
    px1, _, px2, _ = person_box
    vx1, _, vx2, _ = vehicle_box
    w = vx2 - vx1
    vx1 -= w * RIDER_EXPAND_RATIO
    vx2 += w * RIDER_EXPAND_RATIO
    overlap = max(0.0, min(px2, vx2) - max(px1, vx1))
    person_width = px2 - px1
    return overlap / person_width if person_width else 0.0


def _vertical_overlap(person_box, vehicle_box) -> bool:
    _, py1, _, py2 = person_box
    _, vy1, _, vy2 = vehicle_box
    return py1 <= vy2 and py2 >= vy1


def _refine_person_categories(detections: list[dict]) -> None:
    """Split the generic '_person' detections into Rider (overlapping a
    two-wheeler) vs Pedestrian (everyone else). Mutates in place."""
    two_wheelers = [d for d in detections if d["category"] == "Two-Wheeler"]
    for det in detections:
        if det["category"] != "_person":
            continue
        is_rider = any(
            _vertical_overlap(det["box"], moto["box"])
            and _horizontal_containment(det["box"], moto["box"]) >= RIDER_CONTAINMENT_THRESHOLD
            for moto in two_wheelers
        )
        det["category"] = "Rider" if is_rider else "Pedestrian"


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
    for category, dets in by_category.items():
        merged = _merge_category(dets) if category in MERGE_CATEGORIES else dets
        detections.extend(merged)

    _refine_person_categories(detections)

    counts: dict = {}
    for det in detections:
        counts[det["category"]] = counts.get(det["category"], 0) + 1

    vehicles_detected = sum(v for k, v in counts.items() if k in MERGE_CATEGORIES)

    return {
        "detections": detections,
        "counts": counts,
        "total_road_users": len(detections),
        "vehicles_detected": vehicles_detected,
    }
