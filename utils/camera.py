import bpy
import math
import random 

def set_camera_rotation(rotation_tuple):
    cam = bpy.context.scene.camera
    if cam:
        cam.rotation_euler = rotation_tuple
        print(f"🎥 Set camera rotation to {tuple(round(math.degrees(a), 1) for a in rotation_tuple)}°")
    else:
        print("⚠️ No active camera found.")

def add_camera_variance(base_rot, variance_ratio=0.10):
    """
    Adds up to ±variance_ratio (default ±10%) noise to each Euler axis.
    base_rot is a tuple (x, y, z) in radians.
    Returns a new tuple with randomized offsets.
    """
    noisy = []
    for angle in base_rot:
        max_delta = abs(angle) * variance_ratio
        delta = random.uniform(-max_delta, max_delta)
        noisy.append(angle + delta)
    return tuple(noisy)

def add_camera_gaussian_noise(base_rot, sigma_ratio=0.05, clamp_ratio=0.15):
    """
    Adds Gaussian noise to each Euler axis.
    - sigma_ratio: standard deviation as a fraction of the base rotation (default = 5%)
    - clamp_ratio: hard cap to limit extreme values (default = ±15%)

    If a rotation axis is zero, σ becomes a small constant so we still allow noise.
    """
    noisy = []
    for angle in base_rot:
        # avoid zero-variance when angle = 0
        angle_abs = abs(angle) if abs(angle) > 1e-6 else 1.0

        sigma = angle_abs * sigma_ratio
        clamp = angle_abs * clamp_ratio

        # Gaussian noise centered on 0
        delta = random.gauss(0, sigma)

        # Limit extreme noise
        delta = max(-clamp, min(clamp, delta))

        noisy.append(angle + delta)

    return tuple(noisy)

def add_camera_position_variance(base_loc, variance_ratio=0.10):
    """
    Adds up to ±variance_ratio noise to each camera *position* axis.
    base_loc is a tuple (x, y, z).
    Returns a new tuple with randomized offsets.
    """
    noisy = []
    for coord in base_loc:
        max_delta = abs(coord) * variance_ratio
        delta = random.uniform(-max_delta, max_delta)
        noisy.append(coord + delta)
    return tuple(noisy)

def add_camera_position_gaussian(base_loc, sigma_ratio=0.05, clamp_ratio=0.15):
    """
    Adds Gaussian noise to each camera *position* axis.
    - sigma_ratio: σ = percentage of base coordinate (default = 5%)
    - clamp_ratio: hard cap for max deviation (default = 15%)

    If a coordinate is zero, a fallback value (1.0) is used to allow noise.
    """
    noisy = []
    for coord in base_loc:
        # avoid zero-variance when coordinate = 0
        coord_abs = abs(coord) if abs(coord) > 1e-6 else 1.0

        sigma = coord_abs * sigma_ratio
        clamp = coord_abs * clamp_ratio

        # Gaussian noise
        delta = random.gauss(0, sigma)

        # clamp extreme values
        delta = max(-clamp, min(clamp, delta))

        noisy.append(coord + delta)

    return tuple(noisy)