#!/bin/bash

# Get the current directory dynamically where the script is located
SCRIPT_DIR="$(pwd)"

# Define the service name and location for the Upstart configuration
SERVICE_NAME="run_python_programs"
SERVICE_PATH="/etc/init/${SERVICE_NAME}.conf"
SCRIPT_PATH="${SCRIPT_DIR}/run_python_programs.sh"

# Create the Upstart configuration file with the necessary content
echo "Creating Upstart service file at ${SERVICE_PATH}..."

sudo bash -c "cat > ${SERVICE_PATH}" <<EOF
description "Run Python Programs on Startup"

# Automatically start on boot (adjust as needed, this can be changed to a specific runlevel or event)
start on filesystem and net-device-up IFACE=eth0
stop on runlevel [!2345]

# This defines the service that will be launched
exec /bin/bash ${SCRIPT_PATH}
respawn
respawn limit 10 5
EOF

# Make sure the script is executable
echo "Making the script executable..."
sudo chmod +x ${SCRIPT_PATH}

# Provide feedback to the user
echo "Upstart service for ${SERVICE_NAME} has been created."

# Optionally, start the service immediately
echo "Starting the service now..."
sudo start ${SERVICE_NAME}

echo "Service has been started. The script will now run on boot."
