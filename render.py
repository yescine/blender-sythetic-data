import sys, os, bpy, importlib
import math, random, time
from mathutils import Euler
from pathlib import Path


mainObjectId = "SMPLX-male-material-seg"
secondObjectId = "SMPLX-male-material-seg-dup"

# Set rotation in degrees
rotZ_deg = 0
rotZ_rad = math.radians(rotZ_deg)

# ──────────────────────────────
# Apply rotation
# ──────────────────────────────
obj = bpy.context.scene.objects.get(mainObjectId)
if obj:
    obj.rotation_euler = Euler((0, 0, rotZ_rad))
else:
    print(f"⚠️ Object '{mainObjectId}' not found.")

# ──────────────────────────────
# Update compositor file output
# ──────────────────────────────
scene = bpy.context.scene
scene.use_nodes = True
tree = scene.node_tree

file_output_node = None
for node in tree.nodes:
    if node.type == 'OUTPUT_FILE':
        file_output_node = node
        break

slot_files = {0:"image", 1:"segmentation-material", 2:"depth"}
if not file_output_node:
    print("⚠️ No File Output node found in compositor.")
else:
    # Iterate through file slots
    for idx, file_slot in enumerate(file_output_node.file_slots):
        base_path = file_output_node.base_path or ""
        slot_name = file_slot.path.strip() or file_slot.label or file_slot.name
        
        new_name = f"{slot_files[idx]}&rotZ={rotZ_deg}"
        file_slot.path = new_name
        print(f"✅ Updated file slot '{slot_name}' → '{new_name}'")

# ──────────────────────────────
# Optional: Render image
# ──────────────────────────────
# bpy.ops.render.render(write_still=True)
