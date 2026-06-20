import os
import uuid

import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.core.config import UPLOADS_DIR, EVIDENCE_DIR, HELMET_MIN_CONFIDENCE
from app.services.detection_service import run_helmet_detection, run_general_detection, run_pose_detection
from app.services.preprocessing_service import enhance_image
from app.services.ocr_service import extract_vehicle_number
from app.services.triple_riding_service import detect_triple_riding
from app.services.stunt_service import detect_stunt_riding
from app.services.vehicle_service import classify_frame
from app.services.pose_service import get_postures
from app.services.annotation_service import draw_annotations
from app.services.evidence_service import create_violation_record
from app.services import zone_service

router = APIRouter(prefix="/api/detect", tags=["detect"])

ALLOWED_EXT = {".jpg", ".jpeg", ".png"}


@router.post("/image")
async def detect_image(
    file: UploadFile = File(...),
    enable_signal_zone: bool = Form(False),
    stop_line_y: float = Form(70.0),
    signal_state: str = Form("red"),
    enable_parking_zone: bool = Form(False),
    zone_top: float = Form(60.0),
    zone_bottom: float = Form(95.0),
    zone_left: float = Form(0.0),
    zone_right: float = Form(25.0),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, "Only JPG/JPEG/PNG images are supported.")

    uid = uuid.uuid4().hex[:10]
    original_name = f"{uid}_original{ext}"
    annotated_name = f"{uid}_annotated.jpg"
    original_path = os.path.join(UPLOADS_DIR, original_name)
    annotated_path = os.path.join(EVIDENCE_DIR, annotated_name)

    contents = await file.read()
    with open(original_path, "wb") as f:
        f.write(contents)

    original_bgr = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
    if original_bgr is None:
        raise HTTPException(400, "Could not read the uploaded image.")

    h, w = original_bgr.shape[:2]

    enhanced_bgr, preprocessing_report = enhance_image(original_bgr)

    # Ultralytics treats raw ndarrays as already BGR (it only does PIL->BGR
    # conversion for actual PIL Image inputs) — feeding it RGB here silently
    # swaps the R/B channels and degrades every detection's confidence.
    helmet_model, helmet_results = run_helmet_detection(enhanced_bgr)
    general_model, general_results = run_general_detection(enhanced_bgr)

    vehicle_summary = classify_frame(general_model, general_results)

    postures = []
    if vehicle_summary["counts"].get("Two-Wheeler"):
        _, pose_results = run_pose_detection(enhanced_bgr)
        postures = get_postures(pose_results)

    triple_hits = detect_triple_riding(vehicle_summary["detections"], postures)
    stunt_hits = detect_stunt_riding(vehicle_summary["detections"], w, h)
    vehicle_number, plate_box = extract_vehicle_number(original_bgr, detection_image=enhanced_bgr)

    helmet_boxes = []
    violations_payload = []

    for box in helmet_results[0].boxes:
        class_id = int(box.cls)
        class_name = helmet_model.names[class_id]
        confidence = float(box.conf)
        if confidence < HELMET_MIN_CONFIDENCE:
            continue

        is_violation = class_name == "Without Helmet"
        helmet_boxes.append(
            {
                "box": [float(v) for v in box.xyxy[0]],
                "class_name": class_name,
                "confidence": confidence,
                "is_violation": is_violation,
            }
        )

        if is_violation:
            record = create_violation_record(
                vehicle_number=vehicle_number,
                violation_type="Helmet Non-Compliance",
                confidence=confidence,
                original_image_path=f"/storage/uploads/{original_name}",
                annotated_image_path=f"/storage/evidence/{annotated_name}",
                source="upload",
            )
            violations_payload.append(record)

    for hit in triple_hits:
        record = create_violation_record(
            vehicle_number=vehicle_number,
            violation_type="Triple Riding",
            confidence=hit["confidence"],
            original_image_path=f"/storage/uploads/{original_name}",
            annotated_image_path=f"/storage/evidence/{annotated_name}",
            source="upload",
        )
        violations_payload.append(record)

    for hit in stunt_hits:
        record = create_violation_record(
            vehicle_number=vehicle_number,
            violation_type="Stunt Riding",
            confidence=hit["confidence"],
            original_image_path=f"/storage/uploads/{original_name}",
            annotated_image_path=f"/storage/evidence/{annotated_name}",
            source="upload",
        )
        violations_payload.append(record)

    signal_hits: list[dict] = []
    stop_line_px = None
    if enable_signal_zone:
        stop_line_px = zone_service.line_y_px(stop_line_y, h)
        signal_hits = zone_service.detect_signal_violations(
            vehicle_summary["detections"], stop_line_px, signal_state
        )
        for hit in signal_hits:
            record = create_violation_record(
                vehicle_number=vehicle_number,
                violation_type=hit["violation_type"],
                confidence=hit["confidence"],
                original_image_path=f"/storage/uploads/{original_name}",
                annotated_image_path=f"/storage/evidence/{annotated_name}",
                source="upload",
            )
            violations_payload.append(record)

    parking_hits: list[dict] = []
    parking_zone_px = None
    if enable_parking_zone:
        parking_zone_px = zone_service.zone_rect_px(zone_top, zone_bottom, zone_left, zone_right, w, h)
        parking_hits = zone_service.detect_illegal_parking(vehicle_summary["detections"], parking_zone_px)
        for hit in parking_hits:
            record = create_violation_record(
                vehicle_number=vehicle_number,
                violation_type=hit["violation_type"],
                confidence=hit["confidence"],
                original_image_path=f"/storage/uploads/{original_name}",
                annotated_image_path=f"/storage/evidence/{annotated_name}",
                source="upload",
            )
            violations_payload.append(record)

    annotated_bgr = draw_annotations(
        original_bgr,
        helmet_boxes=helmet_boxes,
        triple_riding_hits=triple_hits,
        stunt_hits=stunt_hits,
        vehicle_detections=vehicle_summary["detections"],
        plate_box=plate_box,
        signal_hits=signal_hits,
        parking_hits=parking_hits,
        stop_line_y=stop_line_px,
        parking_zone=parking_zone_px,
    )
    cv2.imwrite(annotated_path, annotated_bgr)

    return {
        "vehicle_number": vehicle_number,
        "violations": violations_payload,
        "annotated_image_url": f"/storage/evidence/{annotated_name}",
        "original_image_url": f"/storage/uploads/{original_name}",
        "helmet_checks_performed": len(helmet_boxes),
        "vehicles_detected": vehicle_summary["vehicles_detected"],
        "is_compliant": len(violations_payload) == 0,
        "preprocessing": preprocessing_report,
        "road_users": vehicle_summary,
    }
