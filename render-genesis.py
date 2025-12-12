import bpy
import math
import os
import json
import mathutils
from mathutils import Euler
import platform
import random

# ────────────────────────────────────────────────────────────────
# CROSS-PLATFORM BASE PATH RESOLVER
# ────────────────────────────────────────────────────────────────

def resolve(path_win: str, path_linux: str):
    """
    Returns the correct path depending on OS.
    Windows -> use path_win
    Linux   -> use path_linux
    """
    if platform.system().lower().startswith("win"):
        return path_win.replace("\\", "/")
    return path_linux


# Set your base folders once
WINDOWS_BASE = r"C:/tmp/blender-scripts/data"
LINUX_BASE   = r"/workspace/data-assets"

def targetPath(*parts):
    """
    Cross-platform join using the correct root directory.
    Usage: targetPath("lights", "file.exr")
    """
    if platform.system().lower().startswith("win"):
        return os.path.join(WINDOWS_BASE, *parts).replace("\\", "/")
    return os.path.join(LINUX_BASE, *parts)

# ──────────────────────────────
# FORCE Cycles to use GPU in headless mode
# ──────────────────────────────
if(platform.system().lower().startswith("linux")):
    # Set device to GPU
    bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "CUDA" # or "OPTIX" or "HIP"

    # Enable CUDA kernel persistence
    bpy.context.preferences.addons['cycles'].preferences.use_cuda_kernel_persistence = True

    # Enable all CUDA devices
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.get_devices()
    for device in prefs.devices:
        device.use = True

    # Ensure scene uses Cycles GPU
    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.cycles.device = "GPU"
    
    # Set Cycles render settings
    cycles = bpy.context.scene.cycles
    
    cycles.tile_size = 1024
    
    cycles.samples = 4096
    cycles.use_adaptive_sampling = True
    cycles.adaptive_threshold = 0.01
    
    cycles.max_bounces = 12
    cycles.diffuse_bounces = 4
    cycles.glossy_bounces = 4
    cycles.transmission_bounces = 12
    
    cycles.use_guiding = True
    cycles.guiding_training_samples = 64

# ──────────────────────────────
# CONFIGURATION
# ──────────────────────────────
characterArmature="raiden"
targetChar="male"
mainObjectId = f"main-{targetChar}-material-seg"
secondObjectId = f"main-{targetChar}-material-seg-dup"

mainMeshId = f"main-mesh-{targetChar}-material"
secondMeshId = f"main-mesh-{targetChar}-color"

# Environment textures (.hdr)
envTextures = [
    targetPath("lights", "university_workshop_4k.exr"),
    # targetPath("lights", "warm_reception_dinner_4k.exr")
]

# Camera positions (Euler rotations in radians)
camera_positions = {
    "isometric":(2.5, -2.5, 3.5),
    "front": (0.1, -4.5, 1),
    "isometricbottom":(2.5, -2.5, -2.5),
}

# Texture list (each applied to "main-male.001" slot)
textures = ["none"]

# Pose JSON folder (each file contains {"pose": [..floats..]})
poses_dir = targetPath("poses") # ("characters", characterArmature, "poses")
pose_files = [os.path.join(poses_dir, f) for f in os.listdir(poses_dir) if f.endswith(".json")]


# Define the Z-axis rotation angles for the body
zAngles = [0, 45, 90, 135, 180]

# ──────────────────────────────
# UTILITIES
# ──────────────────────────────
def toggle_output_nodes(enable_node_name: str):
    scene = bpy.context.scene
    scene.use_nodes = True
    for node in scene.node_tree.nodes:
        if node.type != 'OUTPUT_FILE':
            continue
        node.mute = node.name != enable_node_name
        print(f"{'✅ Enabled' if not node.mute else '⏸️ Disabled'} node '{node.name}'")

def set_visibility(name: str, visible: bool):
    obj = bpy.context.scene.objects.get(name)
    if not obj:
        print(f"⚠️ Object '{name}' not found.")
        return
    obj.hide_viewport = not visible
    obj.hide_render = not visible
    print(f"🔁 {name} visible={visible}")

def set_environment_texture(path: str | None):
    world = bpy.context.scene.world
    if not world:
        print("⚠️ No World in scene.")
        return
    world.use_nodes = True
    tree = world.node_tree
    env_node = next((n for n in tree.nodes if n.type == "TEX_ENVIRONMENT"), None)
    if not env_node:
        env_node = tree.nodes.new("ShaderNodeTexEnvironment")
        env_node.location = (-300, 0)
        bg_node = next((n for n in tree.nodes if n.type == "BACKGROUND"), None)
        if bg_node:
            tree.links.new(env_node.outputs["Color"], bg_node.inputs["Color"])

    bg_node = next((n for n in tree.nodes if n.type == "BACKGROUND"), None)
    if path and os.path.exists(path):
        env_node.image = bpy.data.images.load(path, check_existing=True)
        print(f"🌍 Loaded environment: {os.path.basename(path)}")
    else:
        env_node.image = None
        if bg_node:
            bg_node.inputs["Color"].default_value = (0.5, 0.5, 0.5, 1)
        print("🌫️ Using default gray environment.")

def set_camera_location(location_tuple):
    cam = bpy.context.scene.camera
    if cam:
        cam.location = location_tuple
        print(f"🎥 Set camera location to {tuple(round(v, 3) for v in location_tuple)}")
    else:
        print("⚠️ No active camera found.")

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

def set_mesh_texture(mesh_name: str, slot_name: str, texture_path: str):
    """Assigns texture to specific material slot if exists."""
    obj = bpy.context.scene.objects.get(mesh_name)
    if not obj:
        print(f"⚠️ Object '{mesh_name}' not found.")
        return

    mat_slot = next((m for m in obj.material_slots if m.name == slot_name), None)
    if not mat_slot or not mat_slot.material:
        print(f"⚠️ Material slot '{slot_name}' not found on '{mesh_name}'.")
        return

    mat = mat_slot.material
    mat.use_nodes = True
    tree = mat.node_tree
    tex_node = next((n for n in tree.nodes if n.type == "TEX_IMAGE"), None)
    if not tex_node:
        tex_node = tree.nodes.new("ShaderNodeTexImage")
        tex_node.location = (-300, 0)
        bsdf = next((n for n in tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf:
            tree.links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])

    if os.path.exists(texture_path):
        tex_node.image = bpy.data.images.load(texture_path, check_existing=True)
        print(f"🧩 Applied texture '{os.path.basename(texture_path)}' to '{slot_name}'")
    else:
        print(f"⚠️ Texture file not found: {texture_path}")

def apply_pose_dict(armature_obj, pose_dict):
    """
    Apply pose transforms to armature based on JSON-friendly data structure.
    """
    if armature_obj.type != 'ARMATURE':
        raise ValueError("Provided object is not an armature")

    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode='POSE')

    for bone_name, data in pose_dict.items():
        if bone_name not in armature_obj.pose.bones:
            print(f"[WARN] Bone '{bone_name}' not found in armature; skipping")
            continue

        pb = armature_obj.pose.bones[bone_name]

        # Apply transforms
        if "rotation_quaternion" in data:
            pb.rotation_mode = 'QUATERNION'
            pb.rotation_quaternion = data["rotation_quaternion"]

        if "location" in data:
            pb.location = data["location"]

        if "scale" in data:
            pb.scale = data["scale"]

    bpy.ops.object.mode_set(mode='OBJECT')
    print("[OK] Pose applied successfully")
    
def load_pose_from_json_file(armature_obj, filepath):
    with open(filepath, "r") as f:
        pose_dict = json.load(f)
    apply_pose_dict(armature_obj, pose_dict)

def prepare_scene_for_object(armature_name: str, rotZ_deg: float):
    arm = bpy.context.scene.objects.get(armature_name)
    if not arm:
        print(f"⚠️ Armature '{armature_name}' not found.")
        return

    arm.rotation_euler = Euler((0, 0, math.radians(rotZ_deg)))
    print(f"✅ Rotated '{armature_name}' Z={rotZ_deg}°")

    if armature_name == mainObjectId:
        toggle_output_nodes("segmentation-material")
        set_visibility(mainMeshId, True)
        set_visibility(secondMeshId, False)

        set_visibility("main-hair-material", True)
        set_visibility("main-eyes-material", True)
        set_visibility("main-eyelashes-material", True)
        set_visibility("main-eyebrows-material", True)
        set_visibility("main-hair-color", False)
        set_visibility("main-eyes-color", False)
        set_visibility("main-eyelashes-color", False)
        set_visibility("main-eyebrows-color", False)
        
        
    elif armature_name == secondObjectId:
        toggle_output_nodes("image")
        set_visibility(mainMeshId, False)
        set_visibility(secondMeshId, True)

        set_visibility("main-hair-material", False)
        set_visibility("main-eyes-material", False)
        set_visibility("main-eyelashes-material", False)
        set_visibility("main-eyebrows-material", False)
        set_visibility("main-hair-color", True)
        set_visibility("main-eyes-color", True)
        set_visibility("main-eyelashes-color", True)
        set_visibility("main-eyebrows-color", True)

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

# ──────────────────────────────
# MAIN LOOP (with per-loop progress)
# ──────────────────────────────
total_envs = len(envTextures)
total_cams = len(camera_positions)
total_rots = len(zAngles)
total_poses = len(pose_files)
total_textures = len(textures)
total_objs = 2  # mainObjectId + secondObjectId
total_combinations = total_envs * total_cams * total_textures * total_rots * total_poses * total_objs

progress = 0

# set_resolution_by_ar("9:16", 1024)

for e_idx, env_path in enumerate(envTextures, start=1):
    env_name = os.path.splitext(os.path.basename(env_path))[0] if os.path.exists(env_path) else "noenv"
    set_environment_texture(env_path if os.path.exists(env_path) else None)

    for c_idx, (cam_name, cam_pos) in enumerate(camera_positions.items(), start=1):
        # apply ±20% random variance
        # cam_pos_noisy = add_camera_position_variance(cam_pos, 0.20)
        cam_pos_noisy = add_camera_position_gaussian(
            cam_pos,
            sigma_ratio=0.1,   # 10% natural variation
            clamp_ratio=0.20    # max allowed ±20% deviation
        )
        set_camera_location(cam_pos_noisy)

        for t_idx, tex_path in enumerate(textures, start=1):
            if(os.path.exists(tex_path)):
                tex_name = os.path.splitext(os.path.basename(tex_path))[0]
                set_mesh_texture(secondMeshId, "main-male.001", tex_path)
            else:
                tex_name = "none"

            for r_idx, rotZ_deg in enumerate(zAngles, start=1):
                for p_idx, pose_path in enumerate(pose_files, start=1):
                    pose_name = os.path.splitext(os.path.basename(pose_path))[0]

                    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                    print(
                        f"ENV: {env_name} ({e_idx}/{total_envs}) | "
                        f"CAM: {cam_name} ({c_idx}/{total_cams}) | "
                        f"TEX: {tex_name} ({t_idx}/{total_textures}) | "
                        f"ROTZ: {rotZ_deg}° ({r_idx}/{total_rots}) | "
                        f"POSE: {pose_name} ({p_idx}/{total_poses})"
                    )
                    print(f"Global progress: {progress}/{total_combinations} total")
                    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

                    mainArmature = bpy.data.objects[mainObjectId]
                    load_pose_from_json_file(mainArmature, pose_path)
                    
                    secondArmature = bpy.data.objects[secondObjectId]
                    load_pose_from_json_file(secondArmature, pose_path)

                    for current_obj in [mainObjectId, secondObjectId]:
                        progress += 1
                        prepare_scene_for_object(current_obj, rotZ_deg)

                        scene = bpy.context.scene
                        tree = scene.node_tree
                        for node in tree.nodes:
                            if node.type == "OUTPUT_FILE" and not node.mute:
                                node.file_slots[0].path = (
                                    f"{node.name}&env={env_name}&cam={cam_name}&tex={tex_name}&rotZ={rotZ_deg}&pose={pose_name}&char={characterArmature}"
                                )
                                print(f"📂 Output path for '{node.name}' → {node.file_slots[0].path}")

                        bpy.ops.render.render(write_still=True)
                        print(f"🖼️ Render done for '{current_obj}' ({pose_name}) [{progress}/{total_combinations}] ✅\n")

