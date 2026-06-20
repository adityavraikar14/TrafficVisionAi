"""Computational efficiency measurement for the wrong-side-driving video
pipeline (the one part of the system that isn't single-image — see
backend/app/api/routes/detect_video.py for the detection logic itself).

Usage: python scripts/evaluate_video_pipeline.py
"""
import json
import os
import sys
import time

import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

from app.services.detection_service import get_general_model  # noqa: E402
from app.services.wrong_side_service import build_tracks, detect_wrong_side  # noqa: E402

SAMPLE_VIDEO = os.path.join(ROOT, "sample_images", "Video-418.mp4")
OUTPUT_PATH = os.path.join(ROOT, "reports", "video_pipeline_metrics.json")
TARGET_SAMPLE_FPS = 3
INFERENCE_SIZE = 480


def main():
    if not os.path.exists(SAMPLE_VIDEO):
        print(f"Sample video not found at {SAMPLE_VIDEO}")
        return

    cap = cv2.VideoCapture(SAMPLE_VIDEO)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    duration = frame_count / fps if fps else 0
    cap.release()

    vid_stride = max(1, round(fps / TARGET_SAMPLE_FPS))
    model = get_general_model()

    start = time.perf_counter()
    track_results = model.track(
        source=SAMPLE_VIDEO,
        persist=True,
        conf=0.35,
        vid_stride=vid_stride,
        verbose=False,
        tracker="bytetrack.yaml",
        imgsz=INFERENCE_SIZE,
    )
    elapsed = time.perf_counter() - start

    frame_results = [(i * vid_stride, r) for i, r in enumerate(track_results)]
    tracks = build_tracks(model, frame_results)
    hits = detect_wrong_side(tracks, correct_angle_deg=0)

    result = {
        "note": "Measured on a single real CPU run against sample_images/Video-418.mp4 — not averaged across multiple runs or hardware configs.",
        "video_duration_sec": round(duration, 1),
        "frames_processed": len(frame_results),
        "sample_fps_target": TARGET_SAMPLE_FPS,
        "inference_resolution_px": INFERENCE_SIZE,
        "total_processing_time_sec": round(elapsed, 1),
        "processing_to_video_ratio": round(elapsed / duration, 2) if duration else None,
        "vehicles_tracked": len(tracks),
        "violations_found_at_0deg_reference": len(hits),
        "hardware": "CPU (no GPU) — local machine",
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
    print(f"\nSaved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
