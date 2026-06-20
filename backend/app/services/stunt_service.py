"""Coarse geometric heuristic for wheelie/stunt riding, not a trained
classifier. A wheelie lifts the front wheel and tilts the bike steeply
backward, which (for the typical close, front-on framing of a wheelie
photo) makes the motorcycle's bounding box noticeably taller and narrower
than normal riding, while also dominating the frame (it's the near subject).

Validated directly against a real wheelie photo and 8 unrelated sample
photos (normal riding, parking, triple-riding): only the wheelie photo's
primary motorcycle crosses both thresholds — zero false positives in that
set. Two other single-signal heuristics were tried and rejected before this
one: pure aspect-ratio alone also fires on ordinary front-on (non-wheelie)
shots since camera angle alone produces a tall/narrow box; wheel-circle gap
analysis was too noisy (picked up clothing folds and shadows as false
circles). This is still just a heuristic — a different photo angle or a
parked bike shot from a low angle could fool it — so hits are reported at a
deliberately capped, sub-acceptance confidence and should be treated as
candidates for officer review, not an auto-confirmed violation.
"""

STUNT_ASPECT_MIN = 1.3
STUNT_AREA_FRACTION_MIN = 0.10
STUNT_REPORTED_CONFIDENCE_CAP = 0.55


def detect_stunt_riding(detections: list[dict], frame_width: int, frame_height: int) -> list[dict]:
    motorcycles = [d for d in detections if d["category"] == "Two-Wheeler"]
    if not motorcycles:
        return []

    frame_area = frame_width * frame_height
    largest = max(
        motorcycles,
        key=lambda d: (d["box"][2] - d["box"][0]) * (d["box"][3] - d["box"][1]),
    )
    x1, y1, x2, y2 = largest["box"]
    box_w, box_h = x2 - x1, y2 - y1
    if box_w <= 0 or box_h <= 0:
        return []

    aspect = box_h / box_w
    area_fraction = (box_w * box_h) / frame_area

    if aspect >= STUNT_ASPECT_MIN and area_fraction >= STUNT_AREA_FRACTION_MIN:
        return [
            {
                "violation_type": "Stunt Riding",
                "confidence": min(largest["confidence"], STUNT_REPORTED_CONFIDENCE_CAP),
                "box": largest["box"],
            }
        ]

    return []
