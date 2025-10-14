import bpy, json, os

def get_scene_structure(include_vertex_groups=True):
    """
    Collects structured info about objects, meshes, and armatures in the current Blender scene.
    """
    scene_info = {
        "objects": [],
        "armatures": [],
        "meshes": [],
    }

    # All objects
    for o in bpy.data.objects:
        scene_info["objects"].append({
            "name": o.name,
            "type": o.type,
            "data_type": type(o.data).__name__ if o.data else None,
            "location": list(o.location),
            "rotation_euler": list(o.rotation_euler),
            "scale": list(o.scale),
            "parent": o.parent.name if o.parent else None,
        })

    # Armatures
    for a in [o for o in bpy.data.objects if o.type == "ARMATURE"]:
        armature_entry = {
            "name": a.name,
            "bones_count": len(a.data.bones),
            "pose_bones_count": len(a.pose.bones),
            "pose": []
        }

        for pb in a.pose.bones:
            bone_data = {
                "name": pb.name,
                "location": list(pb.location),
                "rotation_quaternion": list(pb.rotation_quaternion),
                "rotation_euler": list(pb.rotation_euler),
                "scale": list(pb.scale),
                # world-space transform matrix
                "matrix": [list(row) for row in pb.matrix],
            }
            armature_entry["pose"].append(bone_data)

        scene_info["armatures"].append(armature_entry)

    # Meshes
    for m in [o for o in bpy.data.objects if o.type == "MESH"]:
        arm_mods = [md for md in m.modifiers if md.type == "ARMATURE"]
        parent_arm = m.parent if (m.parent and m.parent.type == "ARMATURE") else None
        armature_name = (
            parent_arm.name if parent_arm
            else (arm_mods[0].object.name if arm_mods and arm_mods[0].object else None)
        )

        mesh_data = {
            "name": m.name,
            "vertex_count": len(m.data.vertices),
            "armature": armature_name,
            "materials": [],
        }
        
        for slot in m.material_slots:
            mat = slot.material
            if not mat:
                continue

            mat_entry = {"name": mat.name, "textures": []}
            if mat.use_nodes:
                for node in mat.node_tree.nodes:
                    if node.type == "TEX_IMAGE" and node.image:
                        mat_entry["textures"].append({
                            "node_name": node.name,
                            "image_name": node.image.name,
                            "image_path": bpy.path.abspath(node.image.filepath),
                        })
            mesh_data["materials"].append(mat_entry)


        # Vertex group ↔ bone mapping
        if include_vertex_groups:
            mesh_data["vertex_groups"] = [
                {"group": vg.name, "index": vg.index}
                for vg in m.vertex_groups
            ]

        scene_info["meshes"].append(mesh_data)

    return scene_info


def save_scene_structure(filepath, include_vertex_groups=True):
    """
    Dumps the scene info as JSON to a given filepath.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    data = get_scene_structure(include_vertex_groups)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Scene info saved to: {filepath}")
