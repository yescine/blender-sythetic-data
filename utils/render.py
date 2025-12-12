import bpy

def set_resolution_by_ar(ar: str = "9:16", base_width: int = 720):
    """
    Set Blender render resolution using an aspect-ratio string like:
      - "9:16"  -> 720 × 1280
      - "2:3"   -> 720 × 1080
      - "3:4"   -> 720 × 960
      - "1:1"   -> 720 × 720

    If input is invalid, fallback is "9:16".
    """
    scene = bpy.context.scene

    # --- Parse AR ---
    try:
        w_str, h_str = ar.split(":")
        ar_w = float(w_str)
        ar_h = float(h_str)
    except Exception:
        print(f"[WARN] Invalid AR '{ar}', using default 9:16")
        ar_w, ar_h = 9.0, 16.0

    # --- Compute resolution ---
    # scale height relative to base width
    height = int(base_width * (ar_h / ar_w))

    # Apply to Blender
    scene.render.resolution_x = int(base_width)
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = 1.0
    scene.render.pixel_aspect_y = 1.0

    print(f"✓ Resolution set: {base_width} × {height}  (AR {ar})")

    return base_width, height
