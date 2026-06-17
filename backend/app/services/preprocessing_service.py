import cv2
import numpy as np


def _estimate_brightness(image_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    return float(gray.mean())


def _clahe_enhance(image_bgr: np.ndarray) -> np.ndarray:
    """Adaptive histogram equalization on the luminance channel.
    Lifts shadows and recovers detail in low-light frames without
    blowing out already-bright regions (unlike global gamma correction)."""
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l = clahe.apply(l)
    return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)


def _denoise(image_bgr: np.ndarray) -> np.ndarray:
    """Mild edge-preserving denoise — mitigates rain/sensor-noise speckle
    while keeping bounding-box-relevant edges sharp."""
    return cv2.bilateralFilter(image_bgr, d=5, sigmaColor=35, sigmaSpace=35)


def _sharpen(image_bgr: np.ndarray) -> np.ndarray:
    """Unsharp mask — recovers edge contrast lost to mild motion blur."""
    blurred = cv2.GaussianBlur(image_bgr, (0, 0), sigmaX=3)
    return cv2.addWeighted(image_bgr, 1.5, blurred, -0.5, 0)


def _estimate_blur(image_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def enhance_image(image_bgr: np.ndarray) -> tuple[np.ndarray, dict]:
    """Run an adaptive preprocessing pipeline based on detected image
    quality issues. Returns the enhanced image plus a report of which
    corrections were applied (useful for evidence transparency)."""
    report = {}

    brightness = _estimate_brightness(image_bgr)
    blur_score = _estimate_blur(image_bgr)

    out = image_bgr

    if brightness < 95:
        out = _clahe_enhance(out)
        report["low_light_correction"] = True
    else:
        report["low_light_correction"] = False

    out = _denoise(out)
    report["denoise_applied"] = True

    if blur_score < 250:
        out = _sharpen(out)
        report["motion_blur_correction"] = True
    else:
        report["motion_blur_correction"] = False

    report["brightness_score"] = round(brightness, 1)
    report["sharpness_score"] = round(blur_score, 1)

    return out, report
