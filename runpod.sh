#!/bin/bash

set -e

echo "🔧 Updating package list..."
apt-get update -y

echo "📦 Installing system dependencies: git, zip, unzip, curl, build tools..."
apt-get install -y \
  git \
  gh \
  zip \
  unzip \
  curl \
  build-essential \
  libssl-dev \
  libffi-dev

echo "🐍 Upgrading pip and installing pipenv..."
python3 -m pip install --upgrade pip
pip install pipenv
pip install gdown
pip install tqdm pandas minio

echo "☁️ Installing rclone..."
curl https://rclone.org/install.sh | bash
echo "Rclone version: $(rclone --version | head -n 1)"

echo "☁️ Installing MinIO Client (mc)..."
curl -fsSL https://dl.min.io/client/mc/release/linux-amd64/mc -o /usr/local/bin/mc
chmod +x /usr/local/bin/mc
echo "MinIO Client version: $(mc --version)"

echo "✅ Installed versions:"
echo "Git version: $(git --version)"
echo "Python version: $(python3 --version)"
echo "Pip version: $(pip --version)"
echo "Pipenv version: $(pipenv --version)"
echo "Zip version: $(zip -v | head -n 1)"


# Configure MinIO alias if all env variables are present
if [[ -n "$RUNPOD_SECRET_MINIO_HOST" && -n "$RUNPOD_SECRET_MINIO_PORT" && -n "$RUNPOD_SECRET_MINIO_USER" && -n "$RUNPOD_SECRET_MINIO_SECRET" ]]; then
    echo "☁️ Configuring MinIO alias..."
    mc alias set myminio "${RUNPOD_SECRET_MINIO_HOST}:${RUNPOD_SECRET_MINIO_PORT}" "$RUNPOD_SECRET_MINIO_USER" "$RUNPOD_SECRET_MINIO_SECRET"
    echo "✅ MinIO alias 'myminio' is configured."
else
    echo "⚠️ MinIO environment variables are not fully set. Skipping mc alias configuration."
fi

# GitHub CLI Authentication (non-interactive)
if [[ -n "$RUNPOD_SECRET_GITHUB_TOKEN" ]]; then
    echo "🔑 Authenticating GitHub CLI using token..."
    echo "$RUNPOD_SECRET_GITHUB_TOKEN" | gh auth login --with-token
    gh config set -h github.com git_protocol https
    echo "✅ GitHub CLI logged in as: $(gh api user | jq -r .login 2>/dev/null || echo 'unknown')"
else
    echo "⚠️ RUNPOD_SECRET_GITHUB_TOKEN not set. Skipping GitHub CLI authentication."
fi

if [[ -n "$RUNPOD_SECRET_GITHUB_TOKEN" ]]; then
    echo "🔑 Configuring git to use GITHUB_TOKEN for HTTPS..."
    git config --global credential.helper store
    git config --global credential.helper '!f() { echo "username=oauth2"; echo "password=${RUNPOD_SECRET_GITHUB_TOKEN}"; }; f'
    echo "✅ Git is now configured."
else
    echo "⚠️ GITHUB_TOKEN not set. Git HTTPS clones may ask for username/password."
fi

echo -e "\n\n🚀 Development environment ready!"


#####################################################################
# 🧩 ADDITIONS: Blender Headless Installation for RunPod Rendering
#####################################################################

echo "🎨 Installing system dependencies required for Blender headless run..."

apt-get update -y
apt-get install -y \
  libxi6 libxrandr2 libxrender1 libxkbcommon0 libx11-xcb1 \
  libgl1-mesa-glx libglu1-mesa \
  libegl1 libopengl0 \
  libxxf86vm1 libxcursor1 libasound2 \
  mesa-utils

echo "🔍 Checking OpenGL availability..."
glxinfo | grep "OpenGL" || echo "⚠️ OpenGL info not available (expected in headless mode, OK)"

BLENDER_VERSION="4.5.3"
BLENDER_DIR="/workspace/blender"

if [[ ! -d "$BLENDER_DIR" ]]; then
    echo "⬇️ Downloading Blender $BLENDER_VERSION..."
    cd /workspace
    wget https://download.blender.org/release/Blender3.6/blender-$BLENDER_VERSION-linux-x64.tar.xz
    tar -xf blender-$BLENDER_VERSION-linux-x64.tar.xz
    mv blender-$BLENDER_VERSION-linux-x64 blender
    rm blender-$BLENDER_VERSION-linux-x64.tar.xz
else
    echo "📁 Blender directory already exists. Skipping download."
fi

echo "🧪 Testing Blender installation..."
/workspace/blender/blender -b --version

echo "⚙️ Setting Blender to use CUDA GPU (Cycles)..."
cat << 'EOF' > /workspace/configure_cycles_gpu.py
import bpy
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "CUDA"
prefs.get_devices()
for d in prefs.devices:
    d.use = True
print("CUDA devices enabled:", prefs.devices)
EOF

echo "Running GPU configuration..."
/workspace/blender/blender -b -P /workspace/configure_cycles_gpu.py || echo "⚠️ Could not configure CUDA (may require matching drivers)."

echo -e "\n🎉 Blender headless environment installed and ready!"
echo "You can now render using:"
echo "    /workspace/blender/blender -b /workspace/scene.blend -P /workspace/your_script.py"
echo "---------------------------------------------------------------------"
