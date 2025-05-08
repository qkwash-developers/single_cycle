#!/bin/bash

# GitHub repository URL (HTTPS for no authentication)
REPO_URL="https://github.com/qkwash-developers/single_cycle.git"

# Directory to clone into (Home directory)
TARGET_DIR="$HOME/single_cycle"

# Check if the directory already exists
if [ -d "$TARGET_DIR" ]; then
    echo "Directory $TARGET_DIR already exists. Pulling the latest changes from the master branch..."
    cd "$TARGET_DIR"
    git checkout master   # Make sure you're on the master branch
    git pull origin master
else
    echo "Cloning repository into $TARGET_DIR from the master branch..."
    git clone -b master "$REPO_URL" "$TARGET_DIR"
fi
