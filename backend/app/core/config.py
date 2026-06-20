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
GENERAL_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "yolov8s.pt")
POSE_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "yolov8n-pose.pt")
PLATE_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "plate-best.pt")
SEATBELT_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "seat-belt.pt")

HELMET_MIN_CONFIDENCE = 0.40
TRIPLE_RIDING_MIN_CONFIDENCE = 0.35
SEATBELT_MIN_CONFIDENCE = 0.55

PLATE_REGEX = r"^[A-Z]{2}\d{1,2}[A-Z]{1,2}\d{3,4}$"

# Deployed frontend origins (e.g. a Vercel URL) are added via the
# EXTRA_CORS_ORIGINS env var (comma-separated) — no code change/redeploy
# needed when the frontend's domain changes.
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
] + [o.strip() for o in os.environ.get("EXTRA_CORS_ORIGINS", "").split(",") if o.strip()]

SEED_DEMO_DATA = True

CITY_SEED = [
    {"city": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lon": 72.8777},
    {"city": "Delhi", "state": "Delhi", "lat": 28.6139, "lon": 77.2090},
    {"city": "Bangalore", "state": "Karnataka", "lat": 12.9716, "lon": 77.5946},
    {"city": "Hyderabad", "state": "Telangana", "lat": 17.3850, "lon": 78.4867},
    {"city": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lon": 80.2707},
    {"city": "Pune", "state": "Maharashtra", "lat": 18.5204, "lon": 73.8567},
    {"city": "Kolkata", "state": "West Bengal", "lat": 22.5726, "lon": 88.3639},
    {"city": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lon": 72.5714},
    {"city": "Jaipur", "state": "Rajasthan", "lat": 26.9124, "lon": 75.7873},
    {"city": "Lucknow", "state": "Uttar Pradesh", "lat": 26.8467, "lon": 80.9462},
    {"city": "Kochi", "state": "Kerala", "lat": 9.9312, "lon": 76.2673},
    {"city": "Surat", "state": "Gujarat", "lat": 21.1702, "lon": 72.8311},
    {"city": "Indore", "state": "Madhya Pradesh", "lat": 22.7196, "lon": 75.8577},
    {"city": "Bhopal", "state": "Madhya Pradesh", "lat": 23.2599, "lon": 77.4126},
    {"city": "Nagpur", "state": "Maharashtra", "lat": 21.1458, "lon": 79.0882},
    {"city": "Patna", "state": "Bihar", "lat": 25.5941, "lon": 85.1376},
    {"city": "Chandigarh", "state": "Chandigarh", "lat": 30.7333, "lon": 76.7794},
    {"city": "Visakhapatnam", "state": "Andhra Pradesh", "lat": 17.6868, "lon": 83.2185},
    {"city": "Coimbatore", "state": "Tamil Nadu", "lat": 11.0168, "lon": 76.9558},
    {"city": "Guwahati", "state": "Assam", "lat": 26.1445, "lon": 91.7362},
    {"city": "Bhubaneswar", "state": "Odisha", "lat": 20.2961, "lon": 85.8245},
    {"city": "Thiruvananthapuram", "state": "Kerala", "lat": 8.5241, "lon": 76.9366},
    {"city": "Nashik", "state": "Maharashtra", "lat": 19.9975, "lon": 73.7898},
    {"city": "Vadodara", "state": "Gujarat", "lat": 22.3072, "lon": 73.1812},
    {"city": "Agra", "state": "Uttar Pradesh", "lat": 27.1767, "lon": 78.0081},
    {"city": "Varanasi", "state": "Uttar Pradesh", "lat": 25.3176, "lon": 82.9739},
    {"city": "Amritsar", "state": "Punjab", "lat": 31.6340, "lon": 74.8723},
    {"city": "Raipur", "state": "Chhattisgarh", "lat": 21.2514, "lon": 81.6296},
    {"city": "Ranchi", "state": "Jharkhand", "lat": 23.3441, "lon": 85.3096},
    {"city": "Mysore", "state": "Karnataka", "lat": 12.2958, "lon": 76.6394},
]

OFFICER_USERNAME = "officer1"
OFFICER_PASSWORD = "TrafficPolice@123"
OFFICER_NAME = "Officer Rao"

# Indicative fine amounts (INR) shown on the e-challan — illustrative, not
# legally authoritative figures.
FINE_SCHEDULE = {
    "Helmet Non-Compliance": 1000,
    "Triple Riding": 1000,
    "Illegal Parking": 500,
    "Stop-Line Violation": 500,
    "Red-Light Violation": 1000,
    "Wrong-Side Driving": 1000,
}
DEFAULT_FINE_AMOUNT = 500
