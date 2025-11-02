#!/bin/bash

# Get the current user running the script
USER_NAME="$(whoami)"

# Current working directory (where the script resides)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Log file
LOG_FILE="${SCRIPT_DIR}/update.log"

# Navigate to repo directory
cd "${SCRIPT_DIR}" || { echo "Failed to cd to ${SCRIPT_DIR}" >> "${LOG_FILE}"; exit 1; }

# Pull latest code from master
git checkout master
git pull origin master >> "${LOG_FILE}" 2>&1

# Log the update
echo "[$(date)] Code updated by ${USER_NAME}." >> "${LOG_FILE}"

# Check if sudoers already allows passwordless reboot
SUDOERS_LINE="${USER_NAME} ALL=(ALL) NOPASSWD: /sbin/reboot"
if ! sudo grep -Fxq "$SUDOERS_LINE" /etc/sudoers 2>/dev/null; then
    echo "[$(date)] Adding passwordless reboot for ${USER_NAME}."
    # Add passwordless reboot entry safely
    echo "$SUDOERS_LINE" | sudo EDITOR='tee -a' visudo >/dev/null
fi

# Reboot the system
echo "[$(date)] System rebooting now." >> "${LOG_FILE}"
sudo reboot
