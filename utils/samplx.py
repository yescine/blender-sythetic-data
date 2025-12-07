import bpy
import mathutils

def apply_pose_to_bones(filepath: str, armature_name: str):
    """
    Apply a SMPL-X pose vector (like the 'Write Pose To Console' output)
    directly to armature bones using quaternion rotations.
    Works even if no smplx.update() operator exists.
    """
    import json, os, math
    if not os.path.exists(filepath):
        print(f"⚠️ Pose file not found: {filepath}")
        return
    with open(filepath, "r") as f:
        data = json.load(f)
    pose = data.get("pose") if isinstance(data, dict) else data
    print(len(pose)/3,"len (poses)")
    if not isinstance(pose, list):
        print(f"⚠️ Invalid pose format in {filepath}")
        return

    arm = bpy.data.objects.get(armature_name)
    if not arm or arm.type != 'ARMATURE':
        print(f"⚠️ '{armature_name}' is not an armature.")
        return

    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')

    bones = arm.pose.bones
    total_joints = len(pose) // 3  # each joint has 3 rotation params (axis-angle)
    idx = 0

    for b in bones:
        if idx + 2 >= len(pose):
            break
        x, y, z = pose[idx:idx+3]
        idx += 3
        # convert to quaternion; you may tweak order if model expects YXZ
        quat = mathutils.Euler((x, y, z), 'XYZ').to_quaternion()
        b.rotation_mode = 'QUATERNION'
        b.rotation_quaternion = quat

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.view_layer.update()
    print(f"🦴 Applied pose with {total_joints} joints to '{armature_name}' from {os.path.basename(filepath)}")
