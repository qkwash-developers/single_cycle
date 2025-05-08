#!/bin/bash

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
