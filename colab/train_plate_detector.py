"""
Run this in Google Colab (Runtime -> Change runtime type -> T4 GPU).
Paste cell-by-cell or all at once.

Dataset: barkataliarbab/license-plate-detection-dataset-10125-images (Kaggle)
"""

# --- Cell 1: install deps ---
# !pip install -q ultralytics kagglehub

# --- Cell 2: download dataset ---
import kagglehub
import os

path = kagglehub.dataset_download("barkataliarbab/license-plate-detection-dataset-10125-images")
print("Dataset downloaded to:", path)

# Walk the directory so we can see the actual structure before assuming anything
for root, dirs, files in os.walk(path):
    level = root.replace(path, "").count(os.sep)
    indent = " " * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    if level < 2:
        for f in files[:5]:
            print(f"{indent}  {f}")

# --- Cell 3: locate the data.yaml ---
yaml_path = None
for root, dirs, files in os.walk(path):
    for f in files:
        if f.endswith(".yaml") or f.endswith(".yml"):
            yaml_path = os.path.join(root, f)
            break
    if yaml_path:
        break

print("Found data.yaml at:", yaml_path)
with open(yaml_path) as f:
    print(f.read())

# --- Cell 4: fix paths in data.yaml if needed ---
# Roboflow/Kaggle exports often use relative paths that assume a specific
# working directory. Rewrite them to absolute paths based on where the
# dataset actually landed, so training doesn't fail on "file not found".
import yaml as pyyaml

with open(yaml_path) as f:
    data_cfg = pyyaml.safe_load(f)

print("Original config:", data_cfg)

base_dir = os.path.dirname(yaml_path)
for split in ["train", "val", "test"]:
    if split in data_cfg and data_cfg[split]:
        candidate = os.path.join(base_dir, data_cfg[split])
        if os.path.exists(candidate):
            data_cfg[split] = candidate

fixed_yaml_path = "/content/plate_data.yaml"
with open(fixed_yaml_path, "w") as f:
    pyyaml.dump(data_cfg, f)

print("Fixed config:", data_cfg)

# --- Cell 5: train ---
from ultralytics import YOLO

model = YOLO("yolov8n.pt")
model.train(
    data=fixed_yaml_path,
    epochs=50,
    imgsz=640,
    batch=16,
    name="plate_detector",
    patience=10,
)

# --- Cell 6: validate (get real Precision/Recall/F1/mAP) ---
metrics = model.val()
precision = float(metrics.box.mp)
recall = float(metrics.box.mr)
f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1: {f1:.4f}")
print(f"mAP50: {float(metrics.box.map50):.4f}")
print(f"mAP50-95: {float(metrics.box.map):.4f}")

# --- Cell 7: download the trained weights ---
from google.colab import files

best_pt = "runs/detect/plate_detector/weights/best.pt"
files.download(best_pt)
