#!/usr/bin/env bash

# Target installation directory
INSTALL_DIR="./bin"
FFMPEG_BIN_PATH="$INSTALL_DIR/bin/ffmpeg"

# Download links
X86_URL="https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"
ARM_URL="https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linuxarm64-gpl.tar.xz"

# Detect architecture
ARCH=$(uname -m 2>/dev/null || echo "unknown")
if [[ "$ARCH" == "x86_64" ]]; then
    URL=$X86_URL
elif [[ "$ARCH" == "aarch64" ]]; then
    URL=$ARM_URL
else
    echo "ERROR: Unsupported architecture: $ARCH"
    exit 1
fi

echo "Detected architecture: $ARCH"
echo "Using download URL: $URL"

# Check if required commands exist
for cmd in curl tar realpath; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "ERROR: Required command '$cmd' not found. Please install it first."
        exit 1
    fi
done

# Create bin directory
mkdir -p "$INSTALL_DIR" || { echo "ERROR: Failed to create directory $INSTALL_DIR"; exit 1; }

# Download and extract if ffmpeg does not exist
if [[ -f "$FFMPEG_BIN_PATH" ]]; then
    echo "ffmpeg already exists at $FFMPEG_BIN_PATH, skipping download."
else
    TMP_FILE=$(mktemp) || { echo "ERROR: Failed to create temp file"; exit 1; }
    echo "Downloading ffmpeg..."
    if ! curl -L "$URL" -o "$TMP_FILE"; then
        echo "ERROR: Failed to download ffmpeg from $URL"
        rm -f "$TMP_FILE"
        exit 1
    fi

    echo "Extracting ffmpeg..."
    if ! tar -xvf "$TMP_FILE" -C "$INSTALL_DIR" --strip-components=1; then
        echo "ERROR: Failed to extract ffmpeg"
        rm -f "$TMP_FILE"
        exit 1
    fi

    rm -f "$TMP_FILE"
    echo "ffmpeg has been installed to $INSTALL_DIR"
fi

echo "Setup completed successfully."
