#!/bin/bash

set -e  # Exit immediately if a command fails

echo "=============================="
echo " 🔧 Full System Setup Script"
echo "=============================="



# Step 2: Install required system packages (removed 'pigpio' from apt)
echo "[2/7] 📦 Installing system packages..."
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential redis-server python3-rpi.gpio git

# Step 3: Enable and start services
echo "[3/7] ⚙️ Enabling and starting services..."

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
    sudo systemctl enable pigpiod  # Enable autostart on boot
    sudo systemctl start pigpiod   # Start the pigpiod service immediately
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
pip install requests posix_ipc pigpio RPi.GPIO python-dotenv

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

# ==============================
# Sudoers Configuration for Passwordless Restart of Service
# ==============================

# Name of the user (change if needed)
USERNAME=$(whoami)

# Command to be granted passwordless sudo
SERVICE_CMD="/bin/systemctl restart run_python_programs.service"

# Sudoers file for custom command
SUDOERS_FILE="/etc/sudoers.d/${USERNAME}_nopasswd_service"

# Check if already exists
if sudo test -f "$SUDOERS_FILE"; then
    echo "[INFO] Sudoers file already exists: $SUDOERS_FILE"
else
    echo "[INFO] Creating sudoers rule for $USERNAME to restart the service without password."

    # Add the rule
    echo "$USERNAME ALL=(ALL) NOPASSWD: $SERVICE_CMD" | sudo tee "$SUDOERS_FILE" > /dev/null

    # Set correct permissions
    sudo chmod 440 "$SUDOERS_FILE"

    echo "[SUCCESS] Rule added. You can now run:"
    echo "  sudo systemctl restart run_python_programs.service"
    echo "without being prompted for a password."
fi
