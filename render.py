import bpy
import math
from mathutils import Euler, Vector

# ──────────────────────────────
# Configuration
# ──────────────────────────────
mainObjectId = "SMPLX-male-material-seg"
secondObjectId = "SMPLX-male-material-seg-dup"

mainMeshId = "SMPLX-mesh-male-material"
secondMeshId = "SMPLX-mesh-male-color"

# camera configurations
camera_positions = [
    ((3, -3, 4), "isometric"),
    ((0.5, -6, 1), "front"),
]
zAngles = [0, 45, 90, 135, 180]

# ──────────────────────────────
# Utilities
# ──────────────────────────────
def toggle_output_nodes(enable_node_name: str):
    scene = bpy.context.scene
    scene.use_nodes = True
    tree = scene.node_tree
    for node in tree.nodes:
        if node.type != 'OUTPUT_FILE':
            continue
        node.mute = node.name != enable_node_name
        state = "✅ Enabled" if node.name == enable_node_name else "⏸️ Disabled"
        print(f"{state} node '{node.name}'")

def set_visibility(name: str, visible: bool):
    obj = bpy.context.scene.objects.get(name)
    if obj:
        obj.hide_viewport = not visible
        obj.hide_render = not visible
        print(f"🔁 {name} visible={visible}")
    else:
        print(f"⚠️ Object '{name}' not found.")

def set_camera_position(position):
    cam = bpy.context.scene.camera
    if not cam:
        print("⚠️ No active camera in scene.")
        return
    cam.location = Vector(position)
    cam.rotation_euler = (math.radians(90), 0, 0)  # adjust if needed
    print(f"🎥 Camera moved to {position}")

# ──────────────────────────────
# Main rendering function
# ──────────────────────────────
def prepare_scene_for_object(armature_name: str, rotZ_deg: float, pov_label: str):
    arm = bpy.context.scene.objects.get(armature_name)
    if not arm:
        print(f"⚠️ Armature '{armature_name}' not found.")
        return

    arm.rotation_euler = Euler((0, 0, math.radians(rotZ_deg)))
    print(f"✅ Applied rotation {rotZ_deg}° Z to '{armature_name}'")

    if armature_name == mainObjectId:
        toggle_output_nodes("segmentation-material")
        set_visibility(mainMeshId, True)
        set_visibility(secondMeshId, False)
    elif armature_name == secondObjectId:
        toggle_output_nodes("image")
        set_visibility(mainMeshId, False)
        set_visibility(secondMeshId, True)

    # Update output path
    scene = bpy.context.scene
    tree = scene.node_tree
    for node in tree.nodes:
        if node.type == 'OUTPUT_FILE' and not node.mute:
            node.file_slots[0].path = f"{node.name}&rotZ={rotZ_deg}&pov={pov_label}"
            print(f"📂 Updated output path: {node.file_slots[0].path}")

    bpy.ops.render.render(write_still=True)
    print(f"🖼️ Render completed for '{armature_name}' | rotZ={rotZ_deg} | pov={pov_label}\n")

# ──────────────────────────────
# Execution loops
# ──────────────────────────────
for pos, pov_label in camera_positions:
    set_camera_position(pos)

    for rotZ_deg in zAngles:
        for current_obj in [mainObjectId, secondObjectId]:
            prepare_scene_for_object(current_obj, rotZ_deg, pov_label)
            
print("✅ All renders completed.")
