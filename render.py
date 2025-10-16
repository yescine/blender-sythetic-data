import bpy
import math
from mathutils import Euler

# ──────────────────────────────
# Configuration
# ──────────────────────────────
mainObjectId = "SMPLX-male-material-seg"
secondObjectId = "SMPLX-male-material-seg-dup"

# Associated meshes
mainMeshId = "SMPLX-mesh-male-material"
secondMeshId = "SMPLX-mesh-male-color"

rotZ_deg = -90
rotZ_rad = math.radians(rotZ_deg)

# ──────────────────────────────
# Utility: toggle node enable state
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

# ──────────────────────────────
# Utility: set object visibility
# ──────────────────────────────
def set_visibility(name: str, visible: bool):
    obj = bpy.context.scene.objects.get(name)
    if not obj:
        print(f"⚠️ Object '{name}' not found.")
        return
    obj.hide_viewport = not visible
    obj.hide_render = not visible
    print(f"🔁 {name} visible={visible}")

# ──────────────────────────────
# Prepare scene for rendering one character
# ──────────────────────────────
def prepare_scene_for_object(armature_name: str):
    arm = bpy.context.scene.objects.get(armature_name)
    if not arm:
        print(f"⚠️ Armature '{armature_name}' not found.")
        return

    arm.rotation_euler = Euler((0, 0, rotZ_rad))
    print(f"✅ Applied rotation {rotZ_deg}° Z to '{armature_name}'")

    # Main
    if armature_name == mainObjectId:
        toggle_output_nodes("segmentation-material")
        set_visibility(mainMeshId, True)
        set_visibility(secondMeshId, False)
    # Second
    elif armature_name == secondObjectId:
        toggle_output_nodes("image")
        set_visibility(mainMeshId, False)
        set_visibility(secondMeshId, True)

# ──────────────────────────────
# Execution
# ──────────────────────────────
for current_obj in [mainObjectId, secondObjectId]:
    prepare_scene_for_object(current_obj)

    # Update output file path
    scene = bpy.context.scene
    tree = scene.node_tree
    for node in tree.nodes:
        if node.type == 'OUTPUT_FILE' and not node.mute:
            node.file_slots[0].path = f"{node.name}&rotZ={rotZ_deg}"
            print(f"📂 Active output '{node.name}' → {node.file_slots[0].path}")

    # bpy.ops.render.render(write_still=True)
    print(f"🖼️ Render completed for '{current_obj}'\n")
