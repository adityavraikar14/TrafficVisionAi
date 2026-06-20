import os
import uuid

import cv2
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.core.config import UPLOADS_DIR, EVIDENCE_DIR
from app.services.detection_service import get_general_model
from app.services.wrong_side_service import build_tracks, detect_wrong_side
from app.services.annotation_service import draw_wrong_side_evidence
from app.services.ocr_service import extract_vehicle_number
from app.services.evidence_service import create_violation_record

router = APIRouter(prefix="/api/detect", tags=["detect"])

ALLOWED_EXT = {".mp4", ".avi", ".mov", ".mkv"}
MAX_DURATION_SEC = 60
TARGET_SAMPLE_FPS = 3
INFERENCE_SIZE = 480


@router.post("/video")
async def detect_video(
    file: UploadFile = File(...),
    correct_direction_angle: float = Form(...),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, "Only MP4/AVI/MOV/MKV videos are supported.")

    uid = uuid.uuid4().hex[:10]
    video_name = f"{uid}_video{ext}"
    video_path = os.path.join(UPLOADS_DIR, video_name)

    contents = await file.read()
    with open(video_path, "wb") as f:
        f.write(contents)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise HTTPException(400, "Could not read the uploaded video.")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    duration = frame_count / fps if fps else 0
    cap.release()

    if duration > MAX_DURATION_SEC:
        raise HTTPException(400, f"Video too long ({duration:.0f}s) — max {MAX_DURATION_SEC}s for live analysis.")

    vid_stride = max(1, round(fps / TARGET_SAMPLE_FPS))

    model = get_general_model()
    track_results = model.track(
        source=video_path,
        persist=True,
        conf=0.35,
        vid_stride=vid_stride,
        verbose=False,
        tracker="bytetrack.yaml",
        imgsz=INFERENCE_SIZE,
    )

    frame_results = [(i * vid_stride, r) for i, r in enumerate(track_results)]
    tracks = build_tracks(model, frame_results)
    hits = detect_wrong_side(tracks, correct_direction_angle)

    cap = cv2.VideoCapture(video_path)
    violations_payload = []

    for hit in hits:
        cap.set(cv2.CAP_PROP_POS_FRAMES, hit["last_frame"])
        ok, frame = cap.read()
        if not ok:
            continue

        vehicle_number, _ = extract_vehicle_number(frame)
        annotated = draw_wrong_side_evidence(frame, hit, correct_direction_angle)

        evidence_name = f"{uid}_wrongside_{hit['track_id']}.jpg"
        evidence_path = os.path.join(EVIDENCE_DIR, evidence_name)
        cv2.imwrite(evidence_path, annotated)

        record = create_violation_record(
            vehicle_number=vehicle_number,
            violation_type="Wrong-Side Driving",
            confidence=hit["confidence"],
            original_image_path=f"/storage/uploads/{video_name}",
            annotated_image_path=f"/storage/evidence/{evidence_name}",
            source="video",
        )
        violations_payload.append(record)

    cap.release()

    return {
        "vehicles_tracked": len(tracks),
        "frames_processed": len(frame_results),
        "video_duration_sec": round(duration, 1),
        "violations": violations_payload,
        "is_compliant": len(violations_payload) == 0,
    }
