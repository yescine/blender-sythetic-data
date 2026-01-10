
import bpy
import math
from mathutils import Euler
import random

def set_camera_location(location_tuple):
    cam = bpy.context.scene.camera
    if cam:
        cam.location = location_tuple
        print(f"🎥 Set camera location to {tuple(round(v, 3) for v in location_tuple)}")
    else:
        print("⚠️ No active camera found.")

def add_object_position_noise(
    base_loc: tuple[float, float, float],
    sigma_ratio=0.05,
    clamp_ratio=0.15
):
    """
    Gaussian XYZ noise for object location.
    - sigma_ratio: % of base coordinate used as σ
    - clamp_ratio: hard clamp as % of base coordinate
    """
    noisy = []
    for coord in base_loc:
        ref = abs(coord) if abs(coord) > 1e-6 else 1.0
        sigma = ref * sigma_ratio
        clamp = ref * clamp_ratio

        delta = random.gauss(0, sigma)
        delta = max(-clamp, min(clamp, delta))

        noisy.append(coord + delta)

    return tuple(noisy)

def set_object_location(obj_name: str, location: tuple):
    obj = bpy.context.scene.objects.get(obj_name)
    if not obj:
        print(f"⚠️ Object '{obj_name}' not found for positioning")
        return
    obj.location = location
    # print(
    #     f"📍 {obj_name} location → "
    #     f"{tuple(round(v, 3) for v in location)}"
    # )
    
def compute_object_position_from_camera(
    cam_loc: tuple[float, float, float],
    rel_pos: tuple[float, float, float]
) -> tuple[float, float, float]:
    """
    Convert relative object position into world-space position
    by scaling it with the current camera XYZ.
    """
    return (
        cam_loc[0] * rel_pos[0],
        cam_loc[1] * rel_pos[1],
        cam_loc[2] * rel_pos[2],
    )


targetChar="female"
mainObjectId = f"main-{targetChar}-material-seg"
secondObjectId = f"main-{targetChar}-material-seg-dup"

camera_positions = {
    "isometric":(2.5, -2.5, 3.5),
    "front": (0.1, -4.5, 1.75),
    "isometricbottom":(2.5, -2.5, -2.5),
}

object_positions_relative = {
    "center": (0.1, 0.1, 0.1), 
    "medium": (0.22, 0.22, 0.11), 
    "close": (0.44, 0.44, 0.22),
    # "far": (0, 0, 0),
}

targetCamera = camera_positions["isometric"]
targetPosition = object_positions_relative["medium"]

set_camera_location(targetCamera)

obj_base_pos = compute_object_position_from_camera(
    targetCamera,
    targetPosition
)

# Apply Gaussian noise in world space
obj_pos_noisy = add_object_position_noise(
    obj_base_pos,
    sigma_ratio=0.05,
    clamp_ratio=0.10
)

set_object_location(mainObjectId, obj_base_pos)
