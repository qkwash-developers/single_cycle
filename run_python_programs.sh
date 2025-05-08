#!/bin/bash

# Directory containing your Python programs
SCRIPT_DIR="/home/dtrgenh1d1/code/single_cycle"

# Array of Python script names
SCRIPTS=(
    "adv_relay_control.py"
    "sensor_reader.py"
    "tacho_reader.py"
    "triac_control.py"
    "server_interactor.py"
    "first_cycle_qk.py"
)

# Navigate to the directory
cd "$SCRIPT_DIR" || { echo "Directory not found: $SCRIPT_DIR"; exit 1; }

# Start each script with a one-second delay in between
for script in "${SCRIPTS[@]}"; do
    if [[ -f "$script" ]]; then
        echo "Starting $script..."
        python3 "$script" &
        sleep 1  # Delay for 1 second before starting the next script
    else
        echo "File not found: $script"
    fi
done

# Wait for all background processes to complete
wait

echo "All scripts have completed execution."
