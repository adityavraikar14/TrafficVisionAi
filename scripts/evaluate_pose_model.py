"""Performance evaluation for the pose model used in seated-vs-standing
rider classification (triple-riding detection).

Evaluated on COCO8-pose (a small standard pose validation subset) — this
measures general keypoint-detection accuracy, not accuracy specific to
our seated/standing posture heuristic (which has no labeled dataset of
its own to evaluate against).

Usage: python scripts/evaluate_pose_model.py
"""
import json
import os
import time

from ultralytics import YOLO

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(ROOT, "models", "yolov8n-pose.pt")
OUTPUT_PATH = os.path.join(ROOT, "reports", "pose_model_metrics.json")
SAMPLE_IMAGE = os.path.join(ROOT, "sample_images", "test.jpg")


def main():
    model = YOLO(MODEL_PATH)
    metrics = model.val(data="coco8-pose.yaml", split="val")

    box_p = float(metrics.box.mp)
    box_r = float(metrics.box.mr)
    pose_p = float(metrics.pose.mp)
    pose_r = float(metrics.pose.mr)

    result = {
        "note": "Evaluated on COCO8-pose — general keypoint accuracy, not our seated/standing heuristic specifically.",
        "person_detection_precision": round(box_p, 4),
        "person_detection_recall": round(box_r, 4),
        "person_detection_map50": round(float(metrics.box.map50), 4),
        "keypoint_precision": round(pose_p, 4),
        "keypoint_recall": round(pose_r, 4),
        "keypoint_map50": round(float(metrics.pose.map50), 4),
        "keypoint_map50_95": round(float(metrics.pose.map), 4),
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
