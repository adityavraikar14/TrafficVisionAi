"""Seatbelt non-compliance detection via image classification.

Important honesty note: the classifier was trained on close-up,
in-cabin/dashcam-style photos of a driver's torso (the public dataset's
images are tight crops centered on the chest/seatbelt area). Our pipeline
runs on third-person exterior street photos instead, where we crop the
detected vehicle's full bounding box as a proxy for "the area where a
driver/seatbelt would be visible" — there is no separate "driver" box to
crop, since drivers are usually occluded by the cabin/windshield in
exterior shots (see vehicle_service.py's notes on this same limitation).
This is a heuristic, not a guarantee: accuracy on real exterior photos
where the vehicle/occupant is small or the windshield obscures the view
will likely be lower than the model's validation accuracy suggests.
Only applied to Car/Bus/Truck — not Two-Wheeler (riders wear helmets,
not seatbelts).
"""

import threading

import cv2
import numpy as np
from ultralytics import YOLO

from app.core.config import SEATBELT_MODEL_PATH, SEATBELT_MIN_CONFIDENCE

VEHICLE_CATEGORIES = {"Car", "Bus", "Truck"}

_lock = threading.Lock()
_seatbelt_model = None


def get_seatbelt_model() -> YOLO:
    global _seatbelt_model
    if _seatbelt_model is None:
        with _lock:
            if _seatbelt_model is None:
                _seatbelt_model = YOLO(SEATBELT_MODEL_PATH)
    return _seatbelt_model


def classify_crop(crop_bgr: np.ndarray) -> tuple[str, float] | None:
    """Returns (label, confidence) for a single cropped region, or None
    if the crop is empty."""
    if crop_bgr.size == 0:
        return None
    model = get_seatbelt_model()
    results = model(crop_bgr, verbose=False)
    probs = results[0].probs
    class_id = int(probs.top1)
    confidence = float(probs.top1conf)
    label = model.names[class_id]
    return label, confidence


def detect_seatbelt_violations(image_bgr: np.ndarray, vehicle_detections: list[dict]) -> list[dict]:
    """For each detected Car/Bus/Truck, classify its bounding-box crop as
    seatbelt/no_seatbelt. Flags a violation only when the model says
    'no_seatbelt' with confidence above SEATBELT_MIN_CONFIDENCE."""
    violations = []

    for det in vehicle_detections:
        if det["category"] not in VEHICLE_CATEGORIES:
            continue

        x1, y1, x2, y2 = (int(v) for v in det["box"])
        crop = image_bgr[max(0, y1):y2, max(0, x1):x2]
        result = classify_crop(crop)
        if result is None:
            continue

        label, confidence = result
        if label == "no_seatbelt" and confidence >= SEATBELT_MIN_CONFIDENCE:
            violations.append(
                {
                    "violation_type": "Seatbelt Non-Compliance",
                    "confidence": confidence,
                    "box": det["box"],
                    "vehicle_class": det["class_name"],
                }
            )

    return violations
