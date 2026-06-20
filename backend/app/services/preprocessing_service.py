import cv2
import numpy as np

# ---------------------------------------------------------------------------
# Quality measurement
# ---------------------------------------------------------------------------


def _estimate_brightness(image_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    return float(gray.mean())


def _estimate_blur(image_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _estimate_shadow_spread(image_bgr: np.ndarray) -> float:
    """Max-min brightness spread across a 4x4 grid of blocks. A uniformly
    lit image has a small spread; a cast shadow or strong lighting gradient
    produces a large one — distinct from low overall brightness (which can
    be uniform)."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    bh, bw = max(1, h // 4), max(1, w // 4)
    means = [
        gray[i * bh:(i + 1) * bh, j * bw:(j + 1) * bw].mean()
        for i in range(4) for j in range(4)
        if gray[i * bh:(i + 1) * bh, j * bw:(j + 1) * bw].size
    ]
    return float(max(means) - min(means)) if means else 0.0


def _streak_components(image_bgr: np.ndarray):
    """Binarize edges (Canny), then keep only thin vertically-elongated
    connected components via morphological opening with a tall, narrow
    kernel — the standard way to isolate rain-streak-like structure from
    a binary edge map (continuous-valued frequency maps don't threshold
    cleanly: a single faint 1px streak gets smeared away by Gaussian
    blur before it can be isolated)."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 40, 120)
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 7))
    opened = cv2.morphologyEx(edges, cv2.MORPH_OPEN, vertical_kernel)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(opened)
    elongated_ids = [i for i in range(1, n) if stats[i][3] >= 6 and stats[i][2] <= 3]
    return labels, elongated_ids


def _estimate_rain_streak_score(image_bgr: np.ndarray) -> float:
    """Density of thin vertically-elongated streak components per 100k
    pixels — rain produces many scattered thin vertical streaks; natural
    scene edges (rock texture, guardrails) produce far fewer at this
    strict height/width ratio."""
    _, elongated_ids = _streak_components(image_bgr)
    area = image_bgr.shape[0] * image_bgr.shape[1] / 1e5
    return float(len(elongated_ids) / area) if area else 0.0


# ---------------------------------------------------------------------------
# Shadow removal — illumination-gradient normalization
# ---------------------------------------------------------------------------


SHADOW_BLEND_RATIO = 0.3  # how much of the corrected image to mix in


def _remove_shadow(image_bgr: np.ndarray) -> np.ndarray:
    """A shadow is, physically, a smooth multiplicative lighting gradient
    laid over the scene. Estimate that gradient (heavy blur of the
    luminance channel) and divide it out, rescaling to the original mean
    brightness. This directly targets uneven illumination, unlike CLAHE
    which only redistributes local contrast.

    Blended at SHADOW_BLEND_RATIO rather than applied at full strength:
    the detection heuristic (_estimate_shadow_spread) triggers on any
    large brightness range across the frame, including normal outdoor
    lighting variation (sky/foliage/sun) that isn't actually a problem —
    a full-strength correction in those false-positive cases measurably
    degraded downstream model confidence (verified directly: it flipped
    a correct helmet classification to incorrect on a real test photo).
    A partial blend keeps the real benefit on genuinely shadowed images
    while limiting the damage when the heuristic over-triggers."""
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l_f = l.astype(np.float32)

    illumination = cv2.GaussianBlur(l_f, (0, 0), sigmaX=31)
    illumination = np.clip(illumination, 1.0, 255.0)

    normalized = (l_f / illumination) * illumination.mean()
    l_corrected = np.clip(normalized, 0, 255).astype(np.uint8)
    corrected = cv2.cvtColor(cv2.merge((l_corrected, a, b)), cv2.COLOR_LAB2BGR)

    return cv2.addWeighted(corrected, SHADOW_BLEND_RATIO, image_bgr, 1 - SHADOW_BLEND_RATIO, 0)


# ---------------------------------------------------------------------------
# Low-light correction — CLAHE
# ---------------------------------------------------------------------------


def _clahe_enhance(image_bgr: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l = clahe.apply(l)
    return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)


# ---------------------------------------------------------------------------
# Rain streak attenuation — frequency decomposition + directional morphology
# ---------------------------------------------------------------------------


def _remove_rain_streaks(image_bgr: np.ndarray) -> np.ndarray:
    """Classical single-image rain removal (pre-deep-learning approach):
    split into a low-frequency base layer and a high-frequency detail
    layer, build a mask from the same vertically-elongated streak
    components used for detection, dilate it slightly to cover each
    streak's visual width, and attenuate just that component within the
    detail layer before recombining. This suppresses rain streaks
    specifically rather than blurring the whole image like a generic
    denoise would."""
    labels, elongated_ids = _streak_components(image_bgr)

    streak_mask = np.isin(labels, elongated_ids).astype(np.float32)
    streak_mask = cv2.dilate(streak_mask, np.ones((3, 3), np.uint8), iterations=2)
    # Soften only the mask's edges, not its peak — re-normalize after blur
    # so fully-masked streak pixels still get the full attenuation factor.
    streak_mask = cv2.GaussianBlur(streak_mask, (0, 0), sigmaX=0.8)
    if streak_mask.max() > 0:
        streak_mask = streak_mask / streak_mask.max()

    base = cv2.GaussianBlur(image_bgr, (0, 0), sigmaX=9).astype(np.float32)
    hf = image_bgr.astype(np.float32) - base

    attenuation = 1.0 - (0.95 * streak_mask)
    attenuation_3ch = cv2.merge([attenuation, attenuation, attenuation])

    corrected = base + (hf * attenuation_3ch)
    return np.clip(corrected, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------------------
# Motion-blur correction — Wiener deconvolution with an estimated motion PSF
# ---------------------------------------------------------------------------


def _estimate_blur_angle(gray: np.ndarray) -> float:
    """Motion blur smooths gradients along the direction of motion, so
    edges remain strongest perpendicular to it. Find the dominant
    gradient-magnitude orientation and rotate 90deg to get the blur angle."""
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    magnitude = np.sqrt(gx ** 2 + gy ** 2)
    angle_deg = np.degrees(np.arctan2(gy, gx)) % 180

    hist, edges = np.histogram(angle_deg, bins=36, range=(0, 180), weights=magnitude)
    dominant = edges[np.argmax(hist)] + 2.5
    return float((dominant + 90) % 180)


def _motion_psf(length: int, angle_deg: float, size: int = 21) -> np.ndarray:
    psf = np.zeros((size, size), dtype=np.float32)
    center = size // 2
    angle_rad = np.deg2rad(angle_deg)
    for t in range(-length // 2, length // 2 + 1):
        x = int(round(center + t * np.cos(angle_rad)))
        y = int(round(center + t * np.sin(angle_rad)))
        if 0 <= x < size and 0 <= y < size:
            psf[y, x] = 1.0
    total = psf.sum()
    return psf / total if total > 0 else psf


def _wiener_deconvolve_channel(channel: np.ndarray, psf: np.ndarray, k: float = 0.04) -> np.ndarray:
    h, w = channel.shape
    psf_padded = np.zeros((h, w), dtype=np.float32)
    ph, pw = psf.shape
    psf_padded[:ph, :pw] = psf
    psf_padded = np.roll(psf_padded, -(ph // 2), axis=0)
    psf_padded = np.roll(psf_padded, -(pw // 2), axis=1)

    H = np.fft.fft2(psf_padded)
    F = np.fft.fft2(channel.astype(np.float32))
    H_conj = np.conj(H)
    denom = (H * H_conj) + k
    result = np.fft.ifft2(F * H_conj / denom)
    return np.abs(result)


def _motion_deblur(image_bgr: np.ndarray, blur_score: float) -> np.ndarray:
    """Wiener deconvolution: estimate the motion kernel (angle from gradient
    analysis, length from blur severity) and deconvolve each channel in the
    frequency domain. A real deblurring operation, not just edge sharpening
    — recovers structure a blur kernel destroyed, within the limits of how
    accurately the kernel is estimated."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    angle = _estimate_blur_angle(gray)
    length = int(np.clip(15 - (blur_score / 250) * 10, 5, 15))
    psf = _motion_psf(length=length, angle_deg=angle)

    # FFT-based deconvolution assumes circular boundary conditions, which
    # causes ringing artifacts at the image edges. Reflect-pad before
    # deconvolving and crop back to the original size to suppress this.
    pad = length * 2
    padded = cv2.copyMakeBorder(image_bgr, pad, pad, pad, pad, cv2.BORDER_REFLECT)

    channels = cv2.split(padded)
    deconvolved = [np.clip(_wiener_deconvolve_channel(ch, psf), 0, 255).astype(np.uint8) for ch in channels]
    padded_result = cv2.merge(deconvolved)
    h, w = image_bgr.shape[:2]
    result = padded_result[pad:pad + h, pad:pad + w]

    # Light polish pass — Wiener output with an imperfect kernel estimate
    # can be slightly soft; this is secondary to the deconvolution itself.
    blurred = cv2.GaussianBlur(result, (0, 0), sigmaX=1.2)
    return cv2.addWeighted(result, 1.3, blurred, -0.3, 0)


# ---------------------------------------------------------------------------
# Denoise — generic sensor-noise smoothing (separate from rain-specific pass)
# ---------------------------------------------------------------------------


def _denoise(image_bgr: np.ndarray) -> np.ndarray:
    return cv2.bilateralFilter(image_bgr, d=5, sigmaColor=35, sigmaSpace=35)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

SHADOW_SPREAD_THRESHOLD = 55.0
RAIN_STREAK_THRESHOLD = 100.0  # elongated streak components per 100k pixels
LOW_LIGHT_THRESHOLD = 95.0
BLUR_THRESHOLD = 250.0


def enhance_image(image_bgr: np.ndarray) -> tuple[np.ndarray, dict]:
    """Adaptive preprocessing pipeline: measure specific quality issues
    (uneven lighting/shadow, low light, rain streaks, motion blur) and
    apply the dedicated correction for each one actually detected."""
    report = {}

    brightness = _estimate_brightness(image_bgr)
    blur_score = _estimate_blur(image_bgr)
    shadow_spread = _estimate_shadow_spread(image_bgr)
    rain_score = _estimate_rain_streak_score(image_bgr)

    out = image_bgr

    if shadow_spread > SHADOW_SPREAD_THRESHOLD:
        out = _remove_shadow(out)
        report["shadow_correction"] = True
    else:
        report["shadow_correction"] = False

    if brightness < LOW_LIGHT_THRESHOLD:
        out = _clahe_enhance(out)
        report["low_light_correction"] = True
    else:
        report["low_light_correction"] = False

    if rain_score > RAIN_STREAK_THRESHOLD:
        out = _remove_rain_streaks(out)
        report["rain_correction"] = True
    else:
        report["rain_correction"] = False

    out = _denoise(out)
    report["denoise_applied"] = True

    if blur_score < BLUR_THRESHOLD:
        out = _motion_deblur(out, blur_score)
        report["motion_blur_correction"] = True
    else:
        report["motion_blur_correction"] = False

    report["brightness_score"] = round(brightness, 1)
    report["sharpness_score"] = round(blur_score, 1)
    report["shadow_spread_score"] = round(shadow_spread, 1)
    report["rain_streak_score"] = round(rain_score, 2)

    return out, report
