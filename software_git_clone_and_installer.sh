#!/bin/bash

# GitHub repository URL (HTTPS for no authentication)
REPO_URL="https://github.com/qkwash-developers/single_cycle.git"

# Target directory
TARGET_DIR="$HOME/single_cycle"

# Function to run installer
run_installer() {
    INSTALLER="$TARGET_DIR/installer.sh"
    if [ -f "$INSTALLER" ]; then
        echo "🚀 Running installer.sh..."
        chmod +x "$INSTALLER"
        "$INSTALLER"
        echo "✅ installer.sh executed successfully."
    else
        echo "❌ installer.sh not found in $TARGET_DIR"
    fi
}

# Function to run creator.sh with sudo
run_creator() {
    CREATOR="$TARGET_DIR/creator.sh"
    if [ -f "$CREATOR" ]; then
        echo "🔧 Running creator.sh with sudo..."
        sudo bash "$CREATOR"
        echo "✅ creator.sh executed successfully."
    else
        echo "❌ creator.sh not found in $TARGET_DIR"
    fi
}

# Check if the directory already exists and is a git repo
if [ -d "$TARGET_DIR/.git" ]; then
    echo "📁 Directory $TARGET_DIR already exists. Syncing with remote master branch..."
    cd "$TARGET_DIR" || { echo "❌ Failed to enter $TARGET_DIR"; exit 1; }

    echo "🔄 Fetching and resetting to origin/master..."
    git fetch origin
    git reset --hard origin/master

    run_installer
    run_creator
else
    echo "📥 Cloning repository into $TARGET_DIR..."
    git clone -b master "$REPO_URL" "$TARGET_DIR" && run_installer && run_creator
fi
