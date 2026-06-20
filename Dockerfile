FROM python:3.11-slim

# opencv-python needs these system libs even headless on a slim base image.
# ffmpeg powers the Instant Replay clip extraction for stunt-riding events.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt

# CPU-only torch first — the plain PyPI `torch` wheel ultralytics/easyocr
# would otherwise pull in is the much larger CUDA build, and there's no GPU
# on a free CPU tier anyway.
# Pinned to the exact version already validated against this project's
# code locally, rather than whatever "latest" resolves to at build time.
RUN pip install --no-cache-dir torch==2.12.0 --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY models/ models/

WORKDIR /app/backend

# Hugging Face Spaces (Docker SDK) routes traffic to port 7860 by default.
EXPOSE 7860
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
