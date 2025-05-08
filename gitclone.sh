#!/bin/bash

# GitHub repository URL (HTTPS for no authentication)
REPO_URL="https://github.com/qkwash-developers/single_cycle.git"

# Directory to clone into (Home directory)
TARGET_DIR="$HOME/single_cycle"

# Check if the directory already exists
if [ -d "$TARGET_DIR/.git" ]; then
    echo "📁 Directory $TARGET_DIR already exists. Syncing with remote master branch..."
    cd "$TARGET_DIR" || { echo "❌ Failed to access directory $TARGET_DIR"; exit 1; }

    echo "🔄 Fetching latest changes from remote..."
    git fetch origin

    echo "⚙️  Resetting to origin/master (discarding local changes)..."
    git reset --hard origin/master

    echo "✅ Repository is now in sync with origin/master."
else
    echo "📥 Cloning repository into $TARGET_DIR from the master branch..."
    git clone -b master "$REPO_URL" "$TARGET_DIR"
    echo "✅ Repository cloned successfully."
fi
