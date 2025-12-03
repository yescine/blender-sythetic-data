# 📦 Installation

## ⚙️ Environment Configuration

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

## Render

Example

```bash
cd /workspace
/workspace/blender/blender -b /workspace/data-assets/samplex-render-workflow.blend -P /workspace/data-assets/render.py

```
