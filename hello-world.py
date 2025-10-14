import sys, os, bpy,importlib


sys.path.append(r"C:\tmp\blender-scripts")
import scene_export_utils
importlib.reload(scene_export_utils)

from scene_export_utils import save_scene_structure


output_path = r"C:\tmp\blender-outputs\scene_structure.json"
save_scene_structure(output_path, include_vertex_groups=False)

tree = bpy.context.scene.node_tree

print("— Compositor nodes —")
for n in tree.nodes:
    print(f"{n.name:25s}  type={n.type:30s}  location={n.location}")
    # show useful attributes for common node types
    if n.type == "OUTPUT_FILE":
        print(f"   base_path={n.base_path}")
        for s in n.file_slots:
            print(f"      slot: {s.path}")
    elif n.type == "ID_MASK":
        print(f"   ID value={n.index}")
    elif n.type == "COMPOSITE":
        print(f"   use_alpha={n.use_alpha}")
print("— End of node list —")


