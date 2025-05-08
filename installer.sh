#!/bin/bash

set -e  # Exit immediately if a command fails

echo "=============================="
echo " 🔧 Full System Setup Script"
echo "=============================="

# Step 1: Update system package index only (no upgrade!)
echo "[1/7] 🔄 Updating package index..."
sudo apt update

# Step 2: Install required system packages
echo "[2/7] 📦 Installing system packages..."
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential pigpio redis-server python3-rpi.gpio

# Step 3: Enable and start services
echo "[3/7] ⚙️ Enabling and starting services..."

# Enable and start pigpiod
if ! pgrep pigpiod > /dev/null; then
    echo "  ➤ Starting pigpiod..."
    sudo systemctl enable pigpiod
    sudo systemctl start pigpiod
else
    echo "  ➤ pigpiod already running."
fi

# Enable and start redis-server
echo "  ➤ Ensuring redis-server is running..."
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Step 4: Optional - Create virtual environment
ENV_NAME="project_env"
if [ ! -d "$ENV_NAME" ]; then
    echo "[4/7] 🧪 Creating virtual environment: $ENV_NAME"
    python3 -m venv "$ENV_NAME"
fi
source "$ENV_NAME/bin/activate"

# Step 5: Install required Python packages
echo "[5/7] 🐍 Installing Python dependencies..."
pip install --upgrade pip
pip install requests posix_ipc pigpio RPi.GPIO

# Step 6: Custom module install (uncomment if needed)
# echo "[6/7] Installing from requirements.txt..."
# pip install -r requirements.txt

# Step 7: Verification of critical services
echo "[7/7] ✅ Verifying pigpiod service..."
if pgrep pigpiod > /dev/null; then
    echo "  ✔ pigpiod is running."
else
    echo "  ❌ pigpiod failed to start."
    exit 1
fi

echo "🎉 Environment setup complete."
