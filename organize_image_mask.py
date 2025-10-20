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

    # collect metadata keys
    all_keys = set()
    parsed_data = []
    for f in files:
        meta = parse_filename_metadata(f.name)
        meta["type"] = detect_type(f)
        parsed_data.append((f, meta))
        all_keys.update(meta.keys())

    all_keys = sorted(all_keys)

    # write CSV + copy files
    csv_path = base_dir / "data.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["filename"] + all_keys)
        count = 1
        for file, meta in parsed_data:
            new_name = f"{count:04d}.png"
            dst = img_out if meta.get("type") == "image" else mask_out
            shutil.copy(file, dst / new_name)
            row = [new_name] + [meta.get(k, "") for k in all_keys]
            writer.writerow(row)
            count += 1

    print(f"✅ Done. {count-1} files processed.")
    print(f"Images → {img_out}")
    print(f"Masks → {mask_out}")
    print(f"Metadata → {csv_path}")

if __name__ == "__main__":
    main()
