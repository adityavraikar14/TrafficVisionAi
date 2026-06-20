"""
Run in Google Colab or Kaggle Notebooks. Just inspects the dataset
structure first — don't assume classification vs detection format
until we actually see it.
"""

# --- Cell 1: install + download ---
# !pip install -q kagglehub

import kagglehub
import os

path = kagglehub.dataset_download("alexandresintes/seatbelt-detection-dataset-real-car-photos")
print("Dataset downloaded to:", path)

for root, dirs, files in os.walk(path):
    level = root.replace(path, "").count(os.sep)
    indent = " " * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    if level < 3:
        for f in files[:5]:
            print(f"{indent}  {f}")

# --- Cell 2: if there's a yaml/json/csv labels file, print it ---
for root, dirs, files in os.walk(path):
    for f in files:
        if f.endswith((".yaml", ".yml", ".json", ".csv", ".txt")) and "readme" not in f.lower():
            full = os.path.join(root, f)
            print(f"\n--- {full} ---")
            try:
                with open(full) as fh:
                    print(fh.read()[:1000])
            except Exception as e:
                print("(couldn't read as text:", e, ")")
