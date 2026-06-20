"""Performance evaluation for the general road-user detector (yolov8s).

We don't have our own labeled traffic-camera dataset for this model, so
this evaluates against a standard COCO validation subset — honest framing:
this measures the model's general-purpose accuracy on the classes we
actually use (person, car, motorcycle, bus, truck), not accuracy specific
to Indian traffic-camera conditions. Real numbers, just a different
distribution than our deployment scenario.

Usage: python scripts/evaluate_general_detector.py
"""
import json
import os
import time

from ultralytics import YOLO

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(ROOT, "models", "yolov8s.pt")
OUTPUT_PATH = os.path.join(ROOT, "reports", "general_detector_metrics.json")
SAMPLE_IMAGE = os.path.join(ROOT, "sample_images", "test.jpg")

RELEVANT_CLASSES = {"person", "car", "motorcycle", "bus", "truck"}


def main():
    model = YOLO(MODEL_PATH)
    metrics = model.val(data="coco128.yaml", split="val")

    precision = float(metrics.box.mp)
    recall = float(metrics.box.mr)
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    per_class = {}
    for class_id, map_value in enumerate(metrics.box.maps):
        name = model.names.get(class_id, str(class_id))
        if name in RELEVANT_CLASSES:
            per_class[name] = round(float(map_value), 4)

    result = {
        "note": "Evaluated on COCO128 (subset of COCO val) — general-purpose accuracy, not traffic-camera-specific.",
        "overall_precision": round(precision, 4),
        "overall_recall": round(recall, 4),
        "overall_f1": round(f1, 4),
        "overall_map50": round(float(metrics.box.map50), 4),
        "overall_map50_95": round(float(metrics.box.map), 4),
        "relevant_class_map50_95": per_class,
    }

    if os.path.exists(SAMPLE_IMAGE):
        timings = []
        for _ in range(10):
            start = time.perf_counter()
            model(SAMPLE_IMAGE, verbose=False)
            timings.append(time.perf_counter() - start)
        result["avg_inference_latency_ms"] = round(sum(timings) / len(timings) * 1000, 2)
        result["throughput_images_per_sec"] = round(1 / (sum(timings) / len(timings)), 2)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
    print(f"\nSaved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
