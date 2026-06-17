from app.core.config import TRIPLE_RIDING_MIN_CONFIDENCE
from app.services.pose_service import match_posture

EXPAND_RATIO = 0.05
MIN_HORIZONTAL_CONTAINMENT = 0.55
STRICT_HORIZONTAL_CONTAINMENT = 0.78  # fallback when posture is unavailable


def _horizontal_containment(person_box, moto_box) -> float:
    """Fraction of the person's bbox width that horizontally overlaps the
    motorcycle's bbox. A genuine rider sits centered over the bike, so most
    of their body width falls within the bike's horizontal span. A bystander
    merely standing nearby typically does not."""
    px1, _, px2, _ = person_box
    mx1, _, mx2, _ = moto_box
    mx1 -= (mx2 - mx1) * EXPAND_RATIO
    mx2 += (mx2 - mx1) * EXPAND_RATIO

    overlap = max(0.0, min(px2, mx2) - max(px1, mx1))
    person_width = px2 - px1
    return overlap / person_width if person_width else 0.0


def _vertical_overlap(person_box, moto_box) -> bool:
    _, py1, _, py2 = person_box
    _, my1, _, my2 = moto_box
    return py1 <= my2 and py2 >= my1


def _is_confirmed_rider(person: dict, moto: dict, postures: list[dict]) -> bool:
    if not _vertical_overlap(person["box"], moto["box"]):
        return False
    containment = _horizontal_containment(person["box"], moto["box"])

    posture = match_posture(person["box"], postures)
    if posture is None or posture["posture"] == "unknown":
        # No reliable posture signal (occluded legs, low keypoint confidence) —
        # fall back to a much stricter position-only bar to stay conservative.
        return containment >= STRICT_HORIZONTAL_CONTAINMENT
    if posture["posture"] == "standing":
        # Bent-knee test says this person is standing, not seated on the
        # bike — exclude regardless of how much their box overlaps it.
        return False
    return containment >= MIN_HORIZONTAL_CONTAINMENT


def detect_triple_riding(detections: list[dict], postures: list[dict] | None = None) -> list[dict]:
    """Rule-based triple riding detection on classified, de-duplicated
    road-user detections (see vehicle_service.classify_frame): for each
    motorcycle, count person boxes that overlap it AND whose posture (from
    a pretrained pose model) indicates they're seated, not standing nearby.
    3+ confirmed riders => triple riding violation.
    """
    postures = postures or []
    motorcycles = [d for d in detections if d["category"] == "Two-Wheeler" and d["confidence"] >= TRIPLE_RIDING_MIN_CONFIDENCE]
    persons = [d for d in detections if d["category"] == "Pedestrian / Rider"]

    violations = []
    for moto in motorcycles:
        riders = [p for p in persons if _is_confirmed_rider(p, moto, postures)]
        if len(riders) >= 3:
            violations.append(
                {
                    "violation_type": "Triple Riding",
                    "confidence": moto["confidence"],
                    "rider_count": len(riders),
                    "box": moto["box"],
                }
            )

    return violations
