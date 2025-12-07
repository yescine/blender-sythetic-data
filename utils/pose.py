import bpy
import json

def export_armature_pose(armature_obj):
    """
    Export current pose of an Armature into a JSON-friendly dict.
    Each bone includes:
      - rotation_quaternion: [w, x, y, z]
      - location: [x, y, z]
      - scale: [x, y, z]
    """
    if armature_obj.type != 'ARMATURE':
        raise ValueError("Provided object is not an armature")

    pose_data = {}

    for bone in armature_obj.pose.bones:
        pose_data[bone.name] = {
            "rotation_quaternion": list(bone.rotation_quaternion),
            "location": list(bone.location),
            "scale": list(bone.scale),
        }

    return pose_data


def export_pose_to_json_file(armature_obj, filepath):
    """Write pose data to a JSON file."""
    pose_dict = export_armature_pose(armature_obj)
    with open(filepath, "w") as f:
        json.dump(pose_dict, f, indent=2)
    print(f"[OK] Pose exported → {filepath}")


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


characterObject = "main_armature"
arm = bpy.data.objects[characterObject]
export_pose_to_json_file(arm, "/tmp/blender-outputs/poses/default.json")

# load_pose_from_json_file(arm, "/tmp/blender-outputs/poses/default.json")
