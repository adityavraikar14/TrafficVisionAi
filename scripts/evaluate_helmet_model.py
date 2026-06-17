"""Performance evaluation for the helmet detection model.

Computes Precision, Recall, F1, mAP50, and mAP50-95 on the held-out
validation split, plus per-image inference latency. Run after every
retrain to track whether accuracy improved.

Usage: python scripts/evaluate_helmet_model.py
"""
import json
import os
import time

from ultralytics import YOLO

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(ROOT, "models", "helmet_best.pt")
DATA_YAML = os.path.join(ROOT, "datasets", "helmet_yolo", "dataset.yaml")
OUTPUT_PATH = os.path.join(ROOT, "reports", "helmet_model_metrics.json")


def main():
    model = YOLO(MODEL_PATH)
    metrics = model.val(data=DATA_YAML, split="val")

    precision = float(metrics.box.mp)
    recall = float(metrics.box.mr)
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    result = {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "map50": round(float(metrics.box.map50), 4),
        "map50_95": round(float(metrics.box.map), 4),
        "per_class_map50_95": {
            name: round(float(v), 4) for name, v in zip(model.names.values(), metrics.box.maps)
        },
    }

    # Quick latency benchmark on a single sample image.
    sample = os.path.join(ROOT, "sample_images", "test.jpg")
    if os.path.exists(sample):
        timings = []
        for _ in range(10):
            start = time.perf_counter()
            model(sample, verbose=False)
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
