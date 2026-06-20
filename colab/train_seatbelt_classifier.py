"""
Run in Google Colab or Kaggle Notebooks (GPU runtime).

Dataset: Seat_Belt2 (2-class classification: Seat_Belt / WithoutSeat_Belt)
Replace DATASET_SLUG with the actual owner/dataset-name once you find it
on the dataset's own Kaggle page.
"""

# --- Cell 1: install deps ---
# !pip install -q ultralytics kagglehub

# --- Cell 2: download dataset ---
import kagglehub
import os
DATASET_SLUG = "yehiahassanain/seat-belt2"
  # <-- fill this in with the real slug
path = kagglehub.dataset_download(DATASET_SLUG)
print("Dataset downloaded to:", path)

for root, dirs, files in os.walk(path):
    level = root.replace(path, "").count(os.sep)
    indent = " " * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    if level < 3:
        for f in files[:3]:
            print(f"{indent}  {f}")

# --- Cell 3: locate the actual class folders (handles Train/Test or train/val naming) ---
import glob

def find_class_dir(base_path, split_names, class_name):
    for split in split_names:
        for candidate in glob.glob(os.path.join(base_path, "**", split, class_name), recursive=True):
            if os.path.isdir(candidate):
                return candidate
    return None

train_seatbelt = find_class_dir(path, ["Train", "train"], "Seat_Belt")
train_no_seatbelt = find_class_dir(path, ["Train", "train"], "WithoutSeat_Belt")
test_seatbelt = find_class_dir(path, ["Test", "test", "Val", "val"], "Seat_Belt")
test_no_seatbelt = find_class_dir(path, ["Test", "test", "Val", "val"], "WithoutSeat_Belt")

print("train/seatbelt:", train_seatbelt)
print("train/no_seatbelt:", train_no_seatbelt)
print("val/seatbelt:", test_seatbelt)
print("val/no_seatbelt:", test_no_seatbelt)

if not all([train_seatbelt, train_no_seatbelt, test_seatbelt, test_no_seatbelt]):
    raise RuntimeError("Couldn't find all 4 class folders — paste the Cell 2 tree output to fix the search.")

# --- Cell 4: build the folder structure Ultralytics classification mode expects ---
import shutil

CLS_ROOT = "/content/seatbelt_cls"
for split, (sb_src, nosb_src) in {
    "train": (train_seatbelt, train_no_seatbelt),
    "val": (test_seatbelt, test_no_seatbelt),
}.items():
    os.makedirs(f"{CLS_ROOT}/{split}/seatbelt", exist_ok=True)
    os.makedirs(f"{CLS_ROOT}/{split}/no_seatbelt", exist_ok=True)
    # symlink rather than copy — avoids duplicating 500MB+ of data
    for f in os.listdir(sb_src):
        src = os.path.join(sb_src, f)
        if os.path.isfile(src):
            os.symlink(src, f"{CLS_ROOT}/{split}/seatbelt/{f}")
    for f in os.listdir(nosb_src):
        src = os.path.join(nosb_src, f)
        if os.path.isfile(src):
            os.symlink(src, f"{CLS_ROOT}/{split}/no_seatbelt/{f}")

print("Train seatbelt:", len(os.listdir(f"{CLS_ROOT}/train/seatbelt")))
print("Train no_seatbelt:", len(os.listdir(f"{CLS_ROOT}/train/no_seatbelt")))
print("Val seatbelt:", len(os.listdir(f"{CLS_ROOT}/val/seatbelt")))
print("Val no_seatbelt:", len(os.listdir(f"{CLS_ROOT}/val/no_seatbelt")))

# --- Cell 5: train (classification mode, not detection) ---
from ultralytics import YOLO

model = YOLO("yolov8n-cls.pt")
model.train(
    data=CLS_ROOT,
    epochs=20,
    imgsz=128,
    batch=32,
    name="seatbelt_classifier",
    patience=8,
)

# --- Cell 6: validate ---
metrics = model.val()
print(f"Top-1 Accuracy: {metrics.top1:.4f}")
print(f"Top-5 Accuracy: {metrics.top5:.4f}")

# --- Cell 7: download weights ---
src = "runs/classify/seatbelt_classifier/weights/best.pt"
print("Exists:", os.path.exists(src))

try:
    from google.colab import files
    files.download(src)
    print("Triggered browser download (Colab)")
except ImportError:
    os.makedirs("/kaggle/working", exist_ok=True)
    shutil.copy(src, "/kaggle/working/seatbelt_best.pt")
    print("Copied to /kaggle/working/seatbelt_best.pt — check Output panel (Kaggle)")
