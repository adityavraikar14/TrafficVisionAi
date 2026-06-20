import io
import os

import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.core.config import BASE_DIR, FINE_SCHEDULE, DEFAULT_FINE_AMOUNT


def _disk_path(url_path: str | None) -> str | None:
    if not url_path:
        return None
    full = os.path.join(BASE_DIR, url_path.lstrip("/"))
    return full if os.path.exists(full) else None


def generate_challan_pdf(violation: dict, review: dict) -> bytes:
    fine = FINE_SCHEDULE.get(violation["violation_type"], DEFAULT_FINE_AMOUNT)

    qr_payload = (
        f"TrafficVision Challan | {violation['violation_id']} | "
        f"Verified by {review['officer_name']} ({review['officer_badge_id']}) | {review['reviewed_at']}"
    )
    qr_img = qrcode.make(qr_payload)
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 20 * mm
    y = height - margin

    c.setFont("Helvetica-Bold", 18)
    c.drawString(margin, y, "TrafficVision AI — E-Challan")
    y -= 8 * mm
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, "Smart-City Traffic Enforcement Notice")
    y -= 10 * mm

    c.setStrokeColorRGB(0.85, 0.85, 0.85)
    c.line(margin, y, width - margin, y)
    y -= 10 * mm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, y, f"Challan ID: {violation['violation_id']}")
    y -= 7 * mm
    c.setFont("Helvetica", 11)
    c.drawString(margin, y, f"Vehicle Number: {violation['vehicle_number'] or 'Not Clearly Visible'}")
    y -= 6 * mm
    c.drawString(margin, y, f"Violation Type: {violation['violation_type']}")
    y -= 6 * mm
    c.drawString(margin, y, f"Detection Confidence: {violation['confidence'] * 100:.1f}%")
    y -= 6 * mm
    c.drawString(margin, y, f"Location: {violation['location'] or violation['city'] or 'Unknown'}")
    y -= 6 * mm
    c.drawString(margin, y, f"Detected At: {violation['created_at']}")
    y -= 6 * mm
    if violation.get("repeat_count", 0) >= 2:
        c.setFillColorRGB(0.7, 0, 0)
        c.drawString(margin, y, f"Repeat Offender — Violation #{violation['repeat_count']} for this vehicle")
        c.setFillColorRGB(0, 0, 0)
        y -= 6 * mm

    y -= 4 * mm
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin, y, f"Indicative Fine Amount: Rs. {fine}")
    y -= 10 * mm

    c.setStrokeColorRGB(0.85, 0.85, 0.85)
    c.line(margin, y, width - margin, y)
    y -= 10 * mm

    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, "Verified By")
    y -= 6 * mm
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, f"Officer: {review['officer_name']}  (Badge ID: {review['officer_badge_id']})")
    y -= 6 * mm
    c.drawString(margin, y, f"Decision: {review['decision']}  on  {review['reviewed_at']}")
    if review.get("notes"):
        y -= 6 * mm
        c.drawString(margin, y, f"Notes: {review['notes']}")
    y -= 10 * mm

    image_y = y - 70 * mm
    annotated_path = _disk_path(violation.get("annotated_image_path"))
    if annotated_path:
        try:
            c.drawImage(ImageReader(annotated_path), margin, image_y, width=90 * mm, height=70 * mm, preserveAspectRatio=True, anchor="sw")
        except Exception:
            pass

    c.drawImage(ImageReader(qr_buffer), width - margin - 35 * mm, image_y, width=35 * mm, height=35 * mm)
    c.setFont("Helvetica", 7)
    c.drawString(width - margin - 35 * mm, image_y - 5 * mm, "Scan to verify challan")

    c.setFont("Helvetica-Oblique", 7)
    c.drawString(margin, margin / 2, "Fine amounts shown are indicative for demonstration purposes and are not a legally binding assessment.")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()
