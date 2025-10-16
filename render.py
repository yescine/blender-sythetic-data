import bpy
import math
import os
from mathutils import Euler

# ──────────────────────────────
# CONFIGURATION
# ──────────────────────────────
mainObjectId = "SMPLX-male-material-seg"
secondObjectId = "SMPLX-male-material-seg-dup"

mainMeshId = "SMPLX-mesh-male-material"
secondMeshId = "SMPLX-mesh-male-color"

envTextures = [
    r"C:/tmp/blender-scripts/data/university_workshop_4k.exr",
    r"C:/tmp/blender-scripts/data/warm_reception_dinner_4k.exr"
]


# Define your camera positions (camera names or transforms)
camera_positions = {
    "isometric":(3, -3, 4),
    # "front": (0.5, -6, 1),
}

# Define the Z-axis rotation angles for the body
zAngles = [0, 90] # [0, 45, 90, 135, 180]

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
# MAIN LOOP
# ──────────────────────────────
for env_path in envTextures:
    env_name = os.path.splitext(os.path.basename(env_path))[0] if os.path.exists(env_path) else "noenv"
    set_environment_texture(env_path if os.path.exists(env_path) else None)

    for cam_name, cam_rot in camera_positions.items():
        set_camera_rotation(cam_rot)

        for rotZ_deg in zAngles:
            print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"ENV: {env_name} | CAMERA: {cam_name} | ROTZ: {rotZ_deg}")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

            for current_obj in [mainObjectId, secondObjectId]:
                prepare_scene_for_object(current_obj, rotZ_deg)

                # Update output file paths
                scene = bpy.context.scene
                tree = scene.node_tree
                for node in tree.nodes:
                    if node.type == "OUTPUT_FILE" and not node.mute:
                        node.file_slots[0].path = (
                            f"{node.name}&env={env_name}&cam={cam_name}&rotZ={rotZ_deg}"
                        )
                        print(f"📂 Output path for '{node.name}' → {node.file_slots[0].path}")

                bpy.ops.render.render(write_still=True)
                print(f"🖼️ Render done for '{current_obj}' under {env_name}, {cam_name}, rotZ={rotZ_deg}\n")
