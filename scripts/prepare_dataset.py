import os
import random
import shutil
import xml.etree.ElementTree as ET

# Paths
IMAGE_DIR = "datasets/images"
ANNOTATION_DIR = "datasets/annotations"

TRAIN_IMAGE_DIR = "datasets/helmet_yolo/images/train"
VAL_IMAGE_DIR = "datasets/helmet_yolo/images/val"

TRAIN_LABEL_DIR = "datasets/helmet_yolo/labels/train"
VAL_LABEL_DIR = "datasets/helmet_yolo/labels/val"

# Class mapping
CLASS_MAP = {
    "With Helmet": 0,
    "Without Helmet": 1
}

# Train-validation split
TRAIN_RATIO = 0.8


def convert_bbox(size, box):
    width, height = size

    xmin, ymin, xmax, ymax = box

    x_center = ((xmin + xmax) / 2) / width
    y_center = ((ymin + ymax) / 2) / height

    box_width = (xmax - xmin) / width
    box_height = (ymax - ymin) / height

    return x_center, y_center, box_width, box_height


# Get all XML files
xml_files = [f for f in os.listdir(ANNOTATION_DIR) if f.endswith(".xml")]

# Shuffle dataset
random.shuffle(xml_files)

split_index = int(len(xml_files) * TRAIN_RATIO)

train_files = xml_files[:split_index]
val_files = xml_files[split_index:]


def process_files(file_list, image_output_dir, label_output_dir):

    for xml_file in file_list:

        xml_path = os.path.join(ANNOTATION_DIR, xml_file)

        tree = ET.parse(xml_path)
        root = tree.getroot()

        filename = root.find("filename").text

        width = int(root.find("size/width").text)
        height = int(root.find("size/height").text)

        label_lines = []

        for obj in root.findall("object"):

            class_name = obj.find("name").text

            if class_name not in CLASS_MAP:
                continue

            class_id = CLASS_MAP[class_name]

            bbox = obj.find("bndbox")

            xmin = int(bbox.find("xmin").text)
            ymin = int(bbox.find("ymin").text)
            xmax = int(bbox.find("xmax").text)
            ymax = int(bbox.find("ymax").text)

            x, y, w, h = convert_bbox(
                (width, height),
                (xmin, ymin, xmax, ymax)
            )

            label_lines.append(
                f"{class_id} {x} {y} {w} {h}"
            )

        # Save label file
        txt_filename = os.path.splitext(filename)[0] + ".txt"

        txt_path = os.path.join(label_output_dir, txt_filename)

        with open(txt_path, "w") as f:
            f.write("\n".join(label_lines))

        # Copy image
        src_image = os.path.join(IMAGE_DIR, filename)
        dst_image = os.path.join(image_output_dir, filename)

        shutil.copy(src_image, dst_image)


# Process datasets
process_files(
    train_files,
    TRAIN_IMAGE_DIR,
    TRAIN_LABEL_DIR
)

process_files(
    val_files,
    VAL_IMAGE_DIR,
    VAL_LABEL_DIR
)

print("Dataset preparation completed!")

print(f"Training Images: {len(train_files)}")
print(f"Validation Images: {len(val_files)}")