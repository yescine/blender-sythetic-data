# 📦 Scripts

## Main

- Windows View, copy `render-*.py` into script pannel and execute

- run to organize masks

```bash
python organize_image_mask.py --img-dir /tmp/blender-outputs  --out-dir ./data/
```

Generate Yolo, CVAT data sets

```bash
python ./organize_masks_annotation.py --mask-dir ./data/images-masks/masks --annotation-json ./data/material_dic.json --out-dir ./data/images-masks
```

## Misc

- `hello-world.py`: basic script execution, mainly logs
- `scene_export_utils.py`: Logs console log object in the scene
- `extract_materials_idx.py`: log in json all material with their "Pass Index"

## ⚙️ Environment Configuration

```bash
touch runpod.sh && chmod 777 runpod.sh
```

### Runpod

```md
RUNPOD_SECRET_GITHUB_TOKEN="{{ RUNPOD_SECRET_GITHUB_TOKEN }}"
RUNPOD_SECRET_MINIO_HOST="{{ RUNPOD_SECRET_MINIO_HOST }}"
RUNPOD_SECRET_MINIO_PORT ="{{ RUNPOD_SECRET_MINIO_PORT }}"
RUNPOD_SECRET_MINIO_SECRET ="{{ RUNPOD_SECRET_MINIO_SECRET }}"
RUNPOD_SECRET_MINIO_USER="{{ RUNPOD_SECRET_MINIO_USER }}"
```

### Minio

Mirror files to local dir:

Example

```bash
mc mirror --max-workers=4 myminio/public/shared/blender /workspace/data-assets
```

Upload outputed files continously

```bash
mc mirror --watch --max-workers=4 /tmp/blender-outputs myminio/public/shared/blender-outputs
```

## Render

Example

```bash
cd /workspace
/workspace/blender/blender -b /workspace/data-assets/samplex-render-workflow.blend -P /workspace/blender-sythetic-data/render.py

```

## Visualize

inside `./apps` single html file to visulize different outputs
