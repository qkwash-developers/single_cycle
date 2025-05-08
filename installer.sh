#!/bin/bash

set -e  # Exit immediately if a command fails

echo "=============================="
echo " 🔧 Full System Setup Script"
echo "=============================="

# Step 1: Install required system packages
echo "[1/6] 📦 Installing system packages..."
sudo apt update
sudo apt install -y python3 python3-pip python3-dev build-essential redis-server python3-rpi.gpio git

# Step 2: Enable and start services
echo "[2/6] ⚙️ Enabling and starting services..."

# Check if pigpiod exists
if ! command -v pigpiod &> /dev/null; then
    echo "  ➤ 'pigpiod' not found. Installing manually from source..."
    git clone https://github.com/joan2937/pigpio.git
    cd pigpio
    make
    sudo make install
    cd ..
    rm -rf pigpio
fi

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

# Step 3: Install required Python packages globally
echo "[3/6] 🐍 Installing Python dependencies globally..."
sudo pip3 install --upgrade pip
sudo pip3 install requests posix_ipc pigpio RPi.GPIO python-dotenv

# Step 4: Verification of critical services
echo "[4/6] ✅ Verifying pigpiod service..."
if pgrep pigpiod > /dev/null; then
    echo "  ✔ pigpiod is running."
else
    echo "  ❌ pigpiod failed to start."
    exit 1
fi

# Step 5: Sudoers Configuration for Passwordless Restart of Service
echo "[5/6] 🔐 Configuring sudoers for passwordless service restart..."

USERNAME=$(whoami)
SERVICE_CMD="/bin/systemctl restart run_python_programs.service"
SUDOERS_FILE="/etc/sudoers.d/${USERNAME}_nopasswd_service"

if sudo test -f "$SUDOERS_FILE"; then
    echo "  ➤ Sudoers file already exists: $SUDOERS_FILE"
else
    echo "  ➤ Creating sudoers rule for $USERNAME to restart the service without password."
    echo "$USERNAME ALL=(ALL) NOPASSWD: $SERVICE_CMD" | sudo tee "$SUDOERS_FILE" > /dev/null
    sudo chmod 440 "$SUDOERS_FILE"
    echo "  ✔ Rule added. You can now run:"
    echo "    sudo systemctl restart run_python_programs.service"
    echo "    without being prompted for a password."
fi

echo "[6/6] 🎉 Environment setup complete."
