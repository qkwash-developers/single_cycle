#!/bin/bash

SERVICE_NAME="run_python_programs"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SCRIPT_DIR="$(pwd)"
SCRIPT_PATH="${SCRIPT_DIR}/run_python_programs.sh"
PYTHON_BIN="/usr/bin/python3"

echo "Checking for existing service..."

# If service file exists, stop and remove the service
if systemctl list-units --full -all | grep -Fq "${SERVICE_NAME}.service"; then
    echo "Stopping existing service..."
    sudo systemctl stop "${SERVICE_NAME}.service"

    echo "Disabling existing service..."
    sudo systemctl disable "${SERVICE_NAME}.service"

    echo "Removing old service file..."
    sudo rm -f "${SERVICE_FILE}"
fi

echo "Creating new systemd service file at ${SERVICE_FILE}..."

# Write new systemd service
sudo bash -c "cat > ${SERVICE_FILE}" <<EOF
[Unit]
Description=Run Python Programs on Startup
After=network.target

[Service]
Type=simple
ExecStart=${PYTHON_BIN} ${SCRIPT_PATH}
WorkingDirectory=${SCRIPT_DIR}
StandardOutput=journal
StandardError=journal
Restart=always
User=$(whoami)
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

echo "Making the script executable..."
sudo chmod +x "${SCRIPT_PATH}"

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Enabling the new service..."
sudo systemctl enable "${SERVICE_NAME}.service"

echo "Starting the new service..."
sudo systemctl start "${SERVICE_NAME}.service"

echo "✅ Service '${SERVICE_NAME}' is now active and will start on boot."
