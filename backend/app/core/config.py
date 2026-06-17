import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

STORAGE_DIR = os.path.join(BASE_DIR, "storage")
UPLOADS_DIR = os.path.join(STORAGE_DIR, "uploads")
EVIDENCE_DIR = os.path.join(STORAGE_DIR, "evidence")
DB_PATH = os.path.join(STORAGE_DIR, "trafficvision.db")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(EVIDENCE_DIR, exist_ok=True)

HELMET_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "helmet_best.pt")
GENERAL_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "yolov8n.pt")
POSE_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "yolov8n-pose.pt")

HELMET_MIN_CONFIDENCE = 0.40
TRIPLE_RIDING_MIN_CONFIDENCE = 0.35

PLATE_REGEX = r"^[A-Z]{2}\d{1,2}[A-Z]{1,2}\d{3,4}$"

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

SEED_DEMO_DATA = True

CITY_SEED = [
    {"city": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lon": 72.8777},
    {"city": "Delhi", "state": "Delhi", "lat": 28.6139, "lon": 77.2090},
    {"city": "Bangalore", "state": "Karnataka", "lat": 12.9716, "lon": 77.5946},
    {"city": "Hyderabad", "state": "Telangana", "lat": 17.3850, "lon": 78.4867},
    {"city": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lon": 80.2707},
    {"city": "Pune", "state": "Maharashtra", "lat": 18.5204, "lon": 73.8567},
]
