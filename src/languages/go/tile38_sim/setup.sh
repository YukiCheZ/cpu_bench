#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# prepare_env_vendor.sh
# Prepare Go project dependencies using vendor mode.
# Idempotent: running multiple times will not re-download dependencies unnecessarily.
# -----------------------------------------------------------------------------

# Set your module name here
MODULE="tile38_sim"   # <-- Replace with your actual module name

echo "[INFO] Checking Go environment..."
if ! command -v go &>/dev/null; then
    echo "[ERROR] Go not found. Please install Go first."
    exit 1
fi

# Check Go version
GO_VERSION_FULL=$(go version | awk '{print $3}')  # e.g., go1.20.5
GO_VERSION_NUM=${GO_VERSION_FULL#go}             # strip 'go' prefix
GO_MAJOR=$(echo "$GO_VERSION_NUM" | cut -d. -f1)
GO_MINOR=$(echo "$GO_VERSION_NUM" | cut -d. -f2)

if [ "$GO_MAJOR" -lt 1 ] || { [ "$GO_MAJOR" -eq 1 ] && [ "$GO_MINOR" -lt 14 ]; }; then
    echo "[WARNING] Go version $GO_VERSION_NUM detected. Go 1.14 or higher is recommended for automatic vendor usage."
    echo "[WARNING] You may need to set environment variable: export GOFLAGS=-mod=vendor"
fi

# Initialize Go module if go.mod does not exist
if [ ! -f "go.mod" ]; then
    echo "[INFO] go.mod not found, initializing module '$MODULE'..."
    go mod init "$MODULE"
else
    echo "[INFO] go.mod already exists, skipping initialization."
fi

# Define a flag file to indicate dependencies have been vendored
CACHE_FLAG=".deps_vendored"

# Function to check if vendor directory exists and is non-empty
vendor_exists() {
    [ -d "vendor" ] && [ "$(ls -A vendor)" ]
}

# If dependencies already vendored and vendor dir exists, skip
if [ -f "$CACHE_FLAG" ] && vendor_exists; then
    echo "[INFO] Dependencies already vendored, skipping."
else
    echo "[INFO] Tidying modules and creating vendor directory..."
    go mod tidy
    go mod vendor

    # Verify vendor directory created successfully
    if vendor_exists; then
        touch "$CACHE_FLAG"
        echo "[INFO] Vendor directory created successfully."
    else
        echo "[ERROR] Failed to create vendor directory."
        exit 1
    fi
fi

echo "[INFO] Environment preparation complete."
echo "[INFO] You can now build and run your program fully offline using 'go build' or 'go run'."
