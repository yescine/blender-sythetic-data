import bpy
import json
import os

# Output file (absolute path or relative to blend file)
OUTPUT_JSON = os.path.join(bpy.path.abspath("//"), "materials_pass_index.json")

# -----------------------------------------------------------
# 1. PRINT MATERIALS PassIndex
# -----------------------------------------------------------

def export_material_pass_indices(output_path=None):
    materials = bpy.data.materials

    result = {}
    for mat in materials:
        # Ensure material exists and has pass index
        name = mat.name
        pass_index = getattr(mat, "pass_index", 0)

        result[name] = pass_index

    # Write to JSON
    if(output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        print(f"✓ Exported {len(result)} materials to {output_path}")
    
    return result

# Run the exporter
data = export_material_pass_indices()
#print("Material Passes",data)

# -----------------------------------------------------------
# 2. EXPORT MATERIALS
# -----------------------------------------------------------

def export_materials(output_path):
    """
    Export all materials including Principled, Emission, Diffuse, Glossy, Transparent…
    Extracts shader type and relevant parameters.
    """
    export = {}

    def serialize_color(value):
        return list(value) if hasattr(value, "__iter__") else [value]

    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        
        nt = mat.node_tree
        shader = None

        # Find first shader node
        for node in nt.nodes:
            if node.type.endswith("BSDF") or node.type in ["EMISSION", "TRANSPARENT", "HOLDOUT"]:
                shader = node
                break

        if not shader:
            continue

        material_entry = {
            "shader_type": shader.type,
            "pass_index": mat.pass_index,
            "params": {}
        }

        # Handle Principled
        if shader.type == "BSDF_PRINCIPLED":
            material_entry["params"] = {
                "base_color": serialize_color(shader.inputs["Base Color"].default_value),
                "roughness": float(shader.inputs["Roughness"].default_value),
                "metallic": float(shader.inputs["Metallic"].default_value),
                "specular": float(shader.inputs["Specular"].default_value),
                "emission_color": serialize_color(shader.inputs["Emission"].default_value),
                "emission_strength": float(shader.inputs["Emission Strength"].default_value),
            }

        # Handle Emission
        elif shader.type == "EMISSION":
            material_entry["params"] = {
                "color": serialize_color(shader.inputs["Color"].default_value),
                "strength": float(shader.inputs["Strength"].default_value)
            }

        # Handle Diffuse BSDF
        elif shader.type == "BSDF_DIFFUSE":
            material_entry["params"] = {
                "color": serialize_color(shader.inputs["Color"].default_value),
                "roughness": float(shader.inputs["Roughness"].default_value)
            }

        # Glossy BSDF
        elif shader.type == "BSDF_GLOSSY":
            material_entry["params"] = {
                "color": serialize_color(shader.inputs["Color"].default_value),
                "roughness": float(shader.inputs["Roughness"].default_value)
            }

        # Transparent BSDF
        elif shader.type == "BSDF_TRANSPARENT":
            material_entry["params"] = {
                "color": serialize_color(shader.inputs["Color"].default_value)
            }

        export[mat.name] = material_entry

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(export, f, indent=2)

    print(f"✓ Exported {len(export)} materials → {output_path}")


# -----------------------------------------------------------
# 3. IMPORT MATERIALS
# -----------------------------------------------------------

def import_materials(json_path):
    """
    Rebuild materials based on exported JSON.
    Automatically creates Principled, Emission, Diffuse, Glossy, Transparent.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        imported = json.load(f)

    for mat_name, mat_def in imported.items():
        shader_type = mat_def["shader_type"]
        params = mat_def["params"]

        # Create or reuse material
        if mat_name in bpy.data.materials:
            mat = bpy.data.materials[mat_name]
        else:
            mat = bpy.data.materials.new(mat_name)
            mat.use_nodes = True

        mat.pass_index = mat_def.get("pass_index", 0)

        nt = mat.node_tree
        nt.nodes.clear()

        # Create shader
        shader = nt.nodes.new("ShaderNode" + shader_type.title().replace("_", ""))
        shader.location = (0, 0)

        output = nt.nodes.new("ShaderNodeOutputMaterial")
        output.location = (200, 0)
        nt.links.new(shader.outputs[0], output.inputs[0])

        # Restore parameters
        for key, value in params.items():
            try:
                if key == "base_color":
                    shader.inputs["Base Color"].default_value = value
                elif key == "color":
                    shader.inputs["Color"].default_value = value
                elif key == "roughness":
                    shader.inputs["Roughness"].default_value = value
                elif key == "metallic":
                    shader.inputs["Metallic"].default_value = value
                elif key == "specular":
                    shader.inputs["Specular"].default_value = value
                elif key == "emission_color":
                    shader.inputs["Emission"].default_value = value
                elif key == "emission_strength":
                    shader.inputs["Emission Strength"].default_value = value
                elif key == "strength":
                    shader.inputs["Strength"].default_value = value
            except Exception:
                pass  # Some materials do not support every input

    print(f"✓ Imported/Rebuilt {len(imported)} materials")


# -----------------------------------------------------------
# EXAMPLE USAGE
# -----------------------------------------------------------

# Export from any .blend
export_materials("/tmp/materials_export.json")

# Import into a new empty blend
# import_materials("/tmp/materials_export.json")
