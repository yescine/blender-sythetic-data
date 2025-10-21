import bpy
import math
import os
import json
import mathutils
from mathutils import Euler
# ──────────────────────────────
# CONFIGURATION
# ──────────────────────────────
characterArmature="SMPLX-h170w60"
mainObjectId = "SMPLX-male-material-seg"
secondObjectId = "SMPLX-male-material-seg-dup"

mainMeshId = "SMPLX-mesh-male-material"
secondMeshId = "SMPLX-mesh-male-color"

# Environment textures (.hdr)
envTextures = [
    r"C:/tmp/blender-scripts/data/lights/university_workshop_4k.exr",
    # r"C:/tmp/blender-scripts/data/warm_reception_dinner_4k.exr"
]

# Camera positions (Euler rotations in radians)
camera_positions = {
    "isometric":(3, -3, 4),
     # "front": (0.5, -6, 1),
}

# Texture list (each applied to "SMPLX-male.001" slot)
textures = [
    r"C:/tmp/blender-scripts/data/textures/f_alb.png",
    r"C:/tmp/blender-scripts/data/textures/m_alb.png",
]

# Pose JSON folder (each file contains {"pose": [..floats..]})
poses_dir = r"C:/tmp/blender-scripts/data/poses"
pose_files = [os.path.join(poses_dir, f) for f in os.listdir(poses_dir) if f.endswith(".json")]


# Define the Z-axis rotation angles for the body
zAngles = [0] # [0, 45, 90, 135, 180]

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

def set_camera_rotation(rotation_tuple):
    cam = bpy.context.scene.camera
    if cam:
        cam.rotation_euler = rotation_tuple
        print(f"🎥 Set camera rotation to {tuple(round(math.degrees(a), 1) for a in rotation_tuple)}°")
    else:
        print("⚠️ No active camera found.")

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

pose_to_bone_map = {
    0: "pelvis",
    1: "left_hip",
    2: "right_hip",
    3: "spine1",
    4: "left_knee",
    5: "right_knee",
    6: "spine2",
    7: "left_ankle",
    8: "right_ankle",
    9: "spine3",
    10: "left_foot",
    11: "right_foot",
    12: "neck",
    13: "left_collar",
    14: "right_collar",
    15: "head",
    16: "left_shoulder",
    17: "right_shoulder",
    18: "left_elbow",
    19: "right_elbow",
    20: "left_wrist",
    21: "right_wrist",
    22: "jaw",
    23: "left_eye_smplhf",
    24: "right_eye_smplhf",
    # then continue with hand joints:
    25: "left_thumb1", 26: "left_thumb2", 27: "left_thumb3",
    28: "left_index1", 29: "left_index2", 30: "left_index3",
    31: "left_middle1", 32: "left_middle2", 33: "left_middle3",
    34: "left_ring1", 35: "left_ring2", 36: "left_ring3",
    37: "left_pinky1", 38: "left_pinky2", 39: "left_pinky3",
    40: "right_thumb1", 41: "right_thumb2", 42: "right_thumb3",
    43: "right_index1", 44: "right_index2", 45: "right_index3",
    46: "right_middle1", 47: "right_middle2", 48: "right_middle3",
    49: "right_ring1", 50: "right_ring2", 51: "right_ring3",
    52: "right_pinky1", 53: "right_pinky2", 54: "right_pinky3"
}

def apply_smplx_pose_mapped(filepath, armature_name, pose_to_bone_map):
    if not os.path.exists(filepath):
        print("Pose file not found:", filepath); return
    with open(filepath, "r") as f:
        data = json.load(f)
    pose = data.get("pose") if isinstance(data, dict) else data

    arm = bpy.data.objects.get(armature_name)
    if not arm or arm.type != 'ARMATURE':
        print("Armature not valid."); return

    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')

    for i, bone_name in pose_to_bone_map.items():
        base = i * 3
        if base + 2 >= len(pose): continue
        rx, ry, rz = pose[base:base+3]
        angle = math.sqrt(rx*rx + ry*ry + rz*rz)
        if angle < 1e-8:
            quat = mathutils.Quaternion((1, 0, 0, 0))
        else:
            axis = mathutils.Vector((rx, ry, rz)) / angle
            quat = mathutils.Quaternion(axis, angle)
        bone = arm.pose.bones.get(bone_name)
        if not bone: continue
        bone.rotation_mode = 'QUATERNION'
        bone.rotation_quaternion = quat

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()
    print(f"✅ Pose '{os.path.basename(filepath)}' applied correctly to {armature_name}")


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
    elif armature_name == secondObjectId:
        toggle_output_nodes("image")
        set_visibility(mainMeshId, False)
        set_visibility(secondMeshId, True)

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

for e_idx, env_path in enumerate(envTextures, start=1):
    env_name = os.path.splitext(os.path.basename(env_path))[0] if os.path.exists(env_path) else "noenv"
    set_environment_texture(env_path if os.path.exists(env_path) else None)

    for c_idx, (cam_name, cam_rot) in enumerate(camera_positions.items(), start=1):
        set_camera_rotation(cam_rot)

        for t_idx, tex_path in enumerate(textures, start=1):
            tex_name = os.path.splitext(os.path.basename(tex_path))[0]
            set_mesh_texture(secondMeshId, "SMPLX-male.001", tex_path)

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

                    apply_smplx_pose_mapped(pose_path, mainObjectId, pose_to_bone_map)
                    apply_smplx_pose_mapped(pose_path, secondObjectId, pose_to_bone_map)

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

