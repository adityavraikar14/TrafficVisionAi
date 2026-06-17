import threading

from ultralytics import YOLO

from app.core.config import HELMET_MODEL_PATH, GENERAL_MODEL_PATH, POSE_MODEL_PATH

_lock = threading.Lock()
_helmet_model = None
_general_model = None
_pose_model = None


def get_helmet_model() -> YOLO:
    global _helmet_model
    if _helmet_model is None:
        with _lock:
            if _helmet_model is None:
                _helmet_model = YOLO(HELMET_MODEL_PATH)
    return _helmet_model


def get_general_model() -> YOLO:
    """Stock COCO-trained YOLO, used for person/motorcycle/vehicle detection
    (triple riding, vehicle counting) until dedicated models are trained."""
    global _general_model
    if _general_model is None:
        with _lock:
            if _general_model is None:
                _general_model = YOLO(GENERAL_MODEL_PATH)
    return _general_model


def get_pose_model() -> YOLO:
    """Pretrained COCO-pose YOLO (auto-downloaded, no training needed).
    Used to tell a seated rider (bent knees) apart from a standing
    bystander whose bounding box happens to overlap the bike in 2D."""
    global _pose_model
    if _pose_model is None:
        with _lock:
            if _pose_model is None:
                _pose_model = YOLO(POSE_MODEL_PATH)
    return _pose_model


def run_pose_detection(image):
    model = get_pose_model()
    results = model(image, verbose=False)
    return model, results


def run_helmet_detection(image):
    """image: numpy array (BGR) or file path. In-memory arrays avoid the
    disk round-trip the original Streamlit pipeline used per inference."""
    model = get_helmet_model()
    results = model(image, verbose=False)
    return model, results


def run_general_detection(image):
    model = get_general_model()
    results = model(image, verbose=False)
    return model, results
