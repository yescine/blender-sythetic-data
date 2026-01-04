import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image
import cv2
import xml.etree.ElementTree as ET
import sys


# ----------------------------------------------------------
# Utilities
# ----------------------------------------------------------

def load_mask(path: Path):
    return np.array(Image.open(path).convert("L"))


def find_unique_labels(mask):
    values = np.unique(mask)
    return [int(v) for v in values if v != 0]


def extract_binary_mask(mask, value):
    return (mask == value).astype(np.uint8) * 255


def extract_polygons(binary_mask, epsilon_ratio=0.002):
    contours, _ = cv2.findContours(
        binary_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_NONE
    )

    polygons = []

    for cnt in contours:
        if len(cnt) < 3:
            continue

        epsilon = epsilon_ratio * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)

        poly = [(int(x), int(y)) for [[x, y]] in approx]
        if len(poly) >= 3:
            polygons.append(poly)

    return polygons


def bbox_from_binary_mask(binary_mask):
    ys, xs = np.where(binary_mask == 255)
    if len(xs) == 0:
        return None
    return xs.min(), ys.min(), xs.max(), ys.max()


def convert_bbox_to_yolo(bbox, w, h):
    x_min, y_min, x_max, y_max = bbox
    bw = x_max - x_min
    bh = y_max - y_min
    return (
        (x_min + bw / 2) / w,
        (y_min + bh / 2) / h,
        bw / w,
        bh / h
    )

def filter_binary_mask_by_area(binary_mask, min_area_px, min_area_ratio):
    h, w = binary_mask.shape
    min_area = max(min_area_px, int(h * w * min_area_ratio))

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        binary_mask, connectivity=8
    )

    cleaned = np.zeros_like(binary_mask)

    for i in range(1, num_labels):  # skip background
        area = stats[i, cv2.CC_STAT_AREA]
        if area >= min_area:
            cleaned[labels == i] = 255

    return cleaned

def inline_print(msg: str):
    sys.stdout.write("\r" + msg)
    sys.stdout.flush()
# ----------------------------------------------------------
# CVAT helpers
# ----------------------------------------------------------

def create_cvat_root():
    root = ET.Element("annotations")
    ET.SubElement(root, "version").text = "1.1"
    return root


def create_cvat_image(root, image_id, filename, width, height):
    return ET.SubElement(root, "image", attrib={
        "id": str(image_id),
        "name": filename,
        "width": str(width),
        "height": str(height)
    })


def add_cvat_polygon(image_el, label, polygon_pts):
    pts_str = ";".join(f"{x},{y}" for x, y in polygon_pts)
    ET.SubElement(image_el, "polygon", attrib={
        "label": label,
        "points": pts_str,
        "occluded": "0",
        "source": "manual"
    })


# ----------------------------------------------------------
# Main
# ----------------------------------------------------------

MIN_COMPONENT_AREA_PX = 150      # hard floor (pixels)
MIN_COMPONENT_AREA_RATIO = 0.0005  # relative to image area (0.05%)

def main():
    parser = argparse.ArgumentParser(
        description="Convert masks → YOLO + CVAT with optional part fusion"
    )
    parser.add_argument("--mask-dir", required=True)
    parser.add_argument("--annotation-json", required=True)
    parser.add_argument("--fusion-json", required=False,
                        help="Optional JSON defining fusion rules")
    parser.add_argument("--out-dir", required=True)

    args = parser.parse_args()

    mask_dir = Path(args.mask_dir)
    out_dir = Path(args.out_dir)
    yolo_dir = out_dir / "yolo"
    cvat_dir = out_dir / "cvat"

    yolo_dir.mkdir(parents=True, exist_ok=True)
    cvat_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------
    # Load label map
    # ------------------------------------------------------

    with open(args.annotation_json) as f:
        label_map = json.load(f)

    value_to_label = {int(v): k for k, v in label_map.items()}

    # ------------------------------------------------------
    # Load fusion rules (optional)
    # ------------------------------------------------------

    fusion_rules = {}
    if args.fusion_json:
        with open(args.fusion_json) as f:
            fusion_rules = json.load(f)

    fusion_label_to_values = {}
    fused_values = set()

    for fusion_label, src_labels in fusion_rules.items():
        values = []
        for src in src_labels:
            if src not in label_map:
                raise ValueError(
                    f"Fusion source label '{src}' missing in annotation JSON"
                )
            values.append(label_map[src])
        fusion_label_to_values[fusion_label] = values
        fused_values.update(values)

    # ------------------------------------------------------
    # YOLO class ordering (stable)
    # ------------------------------------------------------

    yolo_labels = (
        [lbl for lbl, v in label_map.items() if v not in fused_values]
        + list(fusion_rules.keys())
    )

    yolo_label_to_id = {lbl: i for i, lbl in enumerate(yolo_labels)}

    print("\nYOLO classes:")
    for k, v in yolo_label_to_id.items():
        print(f"  {v:02d} → {k}")

    # ------------------------------------------------------
    # CVAT root
    # ------------------------------------------------------

    cvat_root = create_cvat_root()
    image_id = 0

    # ------------------------------------------------------
    # Process masks
    # ------------------------------------------------------

    for mask_path in sorted(mask_dir.glob("*.png")):
        inline_print(f"Processing {mask_path.name} / {len(list(mask_dir.glob('*.png')))}")

        mask = load_mask(mask_path)
        h, w = mask.shape[:2]
        unique_values = find_unique_labels(mask)

        image_el = create_cvat_image(
            cvat_root, image_id, mask_path.name, w, h
        )
        image_id += 1

        yolo_lines = []

        # ------------------ Non-fused ------------------

        for v in unique_values:
            if v in fused_values:
                continue
            if v not in value_to_label:
                continue

            label = value_to_label[v]
            cid = yolo_label_to_id[label]

            binary_raw = extract_binary_mask(mask, v)
            binary = filter_binary_mask_by_area(
                binary_raw,
                MIN_COMPONENT_AREA_PX,
                MIN_COMPONENT_AREA_RATIO
            )
            if not np.any(binary):
                continue

            bbox = bbox_from_binary_mask(binary)
            if bbox:
                xc, yc, bw, bh = convert_bbox_to_yolo(bbox, w, h)
                yolo_lines.append(
                    f"{cid} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}"
                )

            for poly in extract_polygons(binary):
                add_cvat_polygon(image_el, label, poly)

        # ------------------ Fused ------------------

        for fusion_label, values in fusion_label_to_values.items():
            merged = np.zeros((h, w), dtype=np.uint8)
            for v in values:
                merged |= extract_binary_mask(mask, v)

            if not np.any(merged):
                continue

            cid = yolo_label_to_id[fusion_label]

            bbox = bbox_from_binary_mask(merged)
            if bbox:
                xc, yc, bw, bh = convert_bbox_to_yolo(bbox, w, h)
                yolo_lines.append(
                    f"{cid} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}"
                )

            for poly in extract_polygons(merged):
                add_cvat_polygon(image_el, fusion_label, poly)

        # ------------------ Write YOLO ------------------

        with open(yolo_dir / f"{mask_path.stem}.txt", "w") as f:
            f.write("\n".join(yolo_lines))

    # ------------------------------------------------------
    # Save CVAT
    # ------------------------------------------------------

    cvat_xml_path = cvat_dir / "annotations.xml"
    ET.ElementTree(cvat_root).write(
        cvat_xml_path, encoding="utf-8", xml_declaration=True
    )

    print("\nDone.")
    print(f"YOLO → {yolo_dir}")
    print(f"CVAT → {cvat_xml_path}")


if __name__ == "__main__":
    main()
