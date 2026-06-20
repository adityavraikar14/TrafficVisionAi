import subprocess

CLIP_MIN_DURATION_SEC = 6.0
CLIP_MAX_DURATION_SEC = 10.0
CLIP_PAD_SEC = 2.5


def clip_window(event_start: float, event_end: float, video_duration: float) -> tuple[float, float]:
    """Expand an event's [start, end] span into a 6-10s evidence window,
    padded symmetrically and clamped to the source video's bounds."""
    span = event_end - event_start
    pad = max(CLIP_PAD_SEC, (CLIP_MIN_DURATION_SEC - span) / 2)
    start = max(0.0, event_start - pad)
    end = min(video_duration, event_end + pad)
    if end - start > CLIP_MAX_DURATION_SEC:
        mid = (start + end) / 2
        start = max(0.0, mid - CLIP_MAX_DURATION_SEC / 2)
        end = min(video_duration, start + CLIP_MAX_DURATION_SEC)
    return start, end


def extract_clip(video_path: str, start_sec: float, end_sec: float, output_path: str) -> bool:
    """Re-encode (not stream-copy) so the cut is frame-accurate and the
    output is a standard H.264/AAC mp4 that plays back in any browser,
    regardless of the source video's original codec."""
    duration = max(0.5, end_sec - start_sec)
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start_sec:.2f}",
        "-i", video_path,
        "-t", f"{duration:.2f}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac",
        "-movflags", "+faststart",
        output_path,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        return True
    except Exception:
        return False
