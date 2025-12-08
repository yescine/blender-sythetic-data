import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image
import cv2
import xml.etree.ElementTree as ET


# ----------------------------------------------------------
# Utilities
# ----------------------------------------------------------

def load_mask(path: Path):
    """Load mask as numpy array (grayscale)."""
    return np.array(Image.open(path).convert("L"))


def find_unique_labels(mask):
    """Return all grayscale values > 0."""
    values = np.unique(mask)
    return [int(v) for v in values if v != 0]


def extract_binary_mask(mask, value):
    """Return a binary mask for a specific grayscale value."""
    return (mask == value).astype(np.uint8) * 255


def contours_from_mask(binary_mask):
    """Return polygon contours from a binary mask."""
    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours


def bbox_from_binary_mask(binary_mask):
    ys, xs = np.where(binary_mask == 255)
    if len(xs) == 0:
        return None
    return xs.min(), ys.min(), xs.max(), ys.max()


def convert_bbox_to_yolo(bbox, w, h):
    x_min, y_min, x_max, y_max = bbox
    bw = x_max - x_min
    bh = y_max - y_min
    x_center = x_min + bw / 2
    y_center = y_min + bh / 2
    return (
        x_center / w,
        y_center / h,
        bw / w,
        bh / h
    )


# ----------------------------------------------------------
# CVAT XML Handling
# ----------------------------------------------------------

def create_cvat_root():
    root = ET.Element("annotations")
    ET.SubElement(root, "version").text = "1.1"
    return root


def add_cvat_polygon(root, filename, width, height, label, polygons):
    image_el = ET.SubElement(root, "image", attrib={
        "name": filename,
        "width": str(width),
        "height": str(height)
    })

    for pts in polygons:
        pts_str = ";".join([f"{x},{y}" for x, y in pts])

        ET.SubElement(image_el, "polygon", attrib={
            "label": label,
            "points": pts_str,
            "occluded": "0",
            "source": "manual"
        })


# ----------------------------------------------------------
# Main
# ----------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Organize polygon masks → YOLO + CVAT")
    parser.add_argument("--mask-dir", required=True, help="Directory containing mask PNGs")
    parser.add_argument("--annotation-json", required=True, help="JSON mapping label → grayscale value")
    parser.add_argument("--out-dir", required=True, help="Output directory")

    args = parser.parse_args()

    mask_dir = Path(args.mask_dir)
    out_dir = Path(args.out_dir)
    yolo_dir = out_dir / "yolo"
    cvat_dir = out_dir / "cvat"

    yolo_dir.mkdir(parents=True, exist_ok=True)
    cvat_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------
    # Load user mapping {label → grayscale_value}
    # ------------------------------------------------------
    with open(args.annotation_json) as f:
        label_map = json.load(f)

    # Reverse mapping: grayscale_value → label
    value_to_label = {}
    for label, value in label_map.items():
        value_to_label[int(value)] = label

    sorted_values = sorted(value_to_label.keys())  # determines YOLO class id order

    cvat_root = create_cvat_root()

    # ------------------------------------------------------
    # Process mask files
    # ------------------------------------------------------
    for mask_path in sorted(mask_dir.glob("*.png")):
        print(f"Processing {mask_path.name}")

        mask = load_mask(mask_path)
        h, w = mask.shape[:2]

        unique_values = find_unique_labels(mask)

        yolo_lines = []
        cvat_polygons = []

        for v in unique_values:

            # ------------------------------
            # Validate grayscale value
            # ------------------------------
            if v not in value_to_label:
                print(f"[WARN] Grayscale {v} found in {mask_path.name}, NOT in JSON → skipped.")
                continue

            label_name = value_to_label[v]
            class_id = sorted_values.index(v)

            # ------------------------------
            # Binary mask for this segment
            # ------------------------------
            binary = extract_binary_mask(mask, v)

            # ------------------------------
            # BBOX for YOLO
            # ------------------------------
            bbox = bbox_from_binary_mask(binary)
            if bbox:
                xc, yc, bw, bh = convert_bbox_to_yolo(bbox, w, h)
                yolo_lines.append(f"{class_id} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")

            # ------------------------------
            # Extract polygons for CVAT
            # ------------------------------
            contours = contours_from_mask(binary)
            polygon_list = []

            for cnt in contours:
                pts = [(int(x), int(y)) for [[x, y]] in cnt]
                polygon_list.append(pts)

            if polygon_list:
                cvat_polygons.append((label_name, polygon_list))

        # ------------------------------
        # Write YOLO output
        # ------------------------------
        yolo_file = yolo_dir / f"{mask_path.stem}.txt"
        with open(yolo_file, "w") as f:
            f.write("\n".join(yolo_lines))

        # ------------------------------
        # Write CVAT polygons for this image
        # ------------------------------
        for label, polygons in cvat_polygons:
            add_cvat_polygon(
                root=cvat_root,
                filename=mask_path.name,
                width=w,
                height=h,
                label=label,
                polygons=polygons
            )

    # ------------------------------------------------------
    # Save CVAT XML
    # ------------------------------------------------------
    cvat_xml_path = cvat_dir / "annotations.xml"
    ET.ElementTree(cvat_root).write(cvat_xml_path, encoding="utf-8", xml_declaration=True)

    print(f"\nYOLO annotations saved in: {yolo_dir}")
    print(f"CVAT XML saved in: {cvat_xml_path}")


if __name__ == "__main__":
    main()
