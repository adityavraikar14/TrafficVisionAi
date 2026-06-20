"""Wrong-side driving detection via multi-frame vehicle tracking.

Direction of travel cannot be determined from a single image — this is
the one violation type that genuinely needs video. We track each vehicle
across sampled frames (Ultralytics' built-in ByteTrack, no training
needed), compute its net displacement vector, and compare that to an
operator-marked 'correct direction' angle for this camera/road segment.
"""

import math
from collections import defaultdict

VEHICLE_CLASSES = {"car", "motorcycle", "bus", "truck"}
MIN_TRACK_FRAMES = 4
MIN_DISPLACEMENT_PX = 25.0
WRONG_SIDE_ANGLE_THRESHOLD = 120.0  # degrees of deviation from correct direction


def _centroid(box):
    x1, y1, x2, y2 = box
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def build_tracks(model, frame_results: list) -> dict:
    """frame_results: list of (frame_index, ultralytics Results) tuples
    from model.track(). Returns {track_id: [{frame, box, centroid, confidence, class_name}, ...]}."""
    tracks: dict = defaultdict(list)

    for frame_idx, result in frame_results:
        boxes = result.boxes
        if boxes is None or boxes.id is None:
            continue
        for i in range(len(boxes)):
            class_id = int(boxes.cls[i])
            class_name = model.names[class_id]
            if class_name not in VEHICLE_CLASSES:
                continue
            track_id = int(boxes.id[i])
            box = [float(v) for v in boxes.xyxy[i]]
            tracks[track_id].append(
                {
                    "frame": frame_idx,
                    "box": box,
                    "centroid": _centroid(box),
                    "confidence": float(boxes.conf[i]),
                    "class_name": class_name,
                }
            )

    return tracks


def detect_wrong_side(tracks: dict, correct_angle_deg: float) -> list[dict]:
    """For each sufficiently long, sufficiently-moving track, compare its
    net displacement direction to the marked correct direction. Large
    deviation => wrong-side violation."""
    violations = []

    for track_id, history in tracks.items():
        if len(history) < MIN_TRACK_FRAMES:
            continue

        first, last = history[0], history[-1]
        dx = last["centroid"][0] - first["centroid"][0]
        dy = last["centroid"][1] - first["centroid"][1]
        displacement = math.hypot(dx, dy)
        if displacement < MIN_DISPLACEMENT_PX:
            continue  # stationary/parked — not a direction violation

        movement_angle = math.degrees(math.atan2(dy, dx)) % 360
        raw_diff = abs(movement_angle - (correct_angle_deg % 360))
        angle_diff = min(raw_diff, 360 - raw_diff)

        if angle_diff > WRONG_SIDE_ANGLE_THRESHOLD:
            avg_conf = sum(h["confidence"] for h in history) / len(history)
            severity = min(1.0, angle_diff / 180.0)
            violations.append(
                {
                    "violation_type": "Wrong-Side Driving",
                    "track_id": track_id,
                    "confidence": round(avg_conf * severity, 4),
                    "box": last["box"],
                    "first_centroid": first["centroid"],
                    "last_centroid": last["centroid"],
                    "movement_angle": round(movement_angle, 1),
                    "last_frame": last["frame"],
                    "class_name": last["class_name"],
                }
            )

    return violations
