import argparse
import csv
import shutil
from pathlib import Path

def parse_filename_metadata(filename: str):
    """
    Extract key=value parts from filename like:
    env=university_workshop_4k&cam=front&rotZ=0&pose=alexandra0001.png
    """
    name = Path(filename).stem
    meta = {}
    for part in name.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            meta[k] = v
    return meta

def detect_type(file_path: Path):
    """
    Detect image or mask type.
    """
    name = file_path.name.lower()
    parent = file_path.parent.name.lower()
    if any(k in name for k in ["mask", "seg", "segmentation"]) or "mask" in parent:
        return "mask"
    return "image"

def main():
    parser = argparse.ArgumentParser(description="Organize first-level images/masks and build CSV metadata")
    parser.add_argument("--img-dir", required=True, help="Path to directory containing rendered images/masks (non-recursive)")
    parser.add_argument("--out-dir", default="./data", help="Output base directory")
    args = parser.parse_args()

    img_dir = Path(args.img_dir)
    if not img_dir.exists():
        print(f"❌ Path not found: {img_dir}")
        return

    base_dir = Path(args.out_dir) / Path("./images-masks")
    img_out = base_dir / "images"
    mask_out = base_dir / "masks"
    base_dir.mkdir(exist_ok=True)
    img_out.mkdir(exist_ok=True)
    mask_out.mkdir(exist_ok=True)

    # only list files directly inside img_dir (not recursive)
    files = sorted([p for p in img_dir.iterdir() if p.is_file() and p.suffix.lower() in [".png", ".jpg", ".jpeg"]])
    print(f"📂 Found {len(files)} top-level image files in {img_dir}")

    # collect metadata and group image + mask pairs
    groups = {}   # key: tuple(sorted meta excluding type)), value: dict(image=Path, mask=Path, meta=dict)

    for f in files:
        meta = parse_filename_metadata(f.name)
        t = detect_type(f)
        meta_no_type = tuple(sorted((k, v) for k, v in meta.items() if k != "type"))

        if meta_no_type not in groups:
            groups[meta_no_type] = {"image": None, "mask": None, "meta": meta}

        groups[meta_no_type][t] = f
        groups[meta_no_type]["meta"].update(meta)  # combine metadata if needed

    # collect all keys
    all_keys = sorted({k for g in groups.values() for k in g["meta"].keys()})

    # write CSV + copy files
    csv_path = base_dir / "data.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["filename"] + all_keys)

        count = 1
        for _, entry in groups.items():
            idx_name = f"{count:04d}.png"

            # copy image
            if entry["image"] is not None:
                shutil.copy(entry["image"], img_out / idx_name)

            # copy mask
            if entry["mask"] is not None:
                shutil.copy(entry["mask"], mask_out / idx_name)

            # write metadata row
            row = [idx_name] + [entry["meta"].get(k, "") for k in all_keys]
            writer.writerow(row)
            count += 1

    print(f"✅ Done. {count-1} pairs processed.")

    print(f"Images → {img_out}")
    print(f"Masks → {mask_out}")
    print(f"Metadata → {csv_path}")

if __name__ == "__main__":
    main()
