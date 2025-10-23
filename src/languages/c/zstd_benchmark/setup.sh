#!/usr/bin/env bash

# Target installation directory
INSTALL_DIR="$(realpath ./bin)"   
ZSTD_SRC_DIR="$INSTALL_DIR/zstd-1.5.7"
ZSTD_BIN_PATH="$INSTALL_DIR/zstd"

# Download link
ZSTD_URL="https://github.com/facebook/zstd/releases/download/v1.5.7/zstd-1.5.7.tar.gz"

# Check if required commands exist
for cmd in curl tar make realpath; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "[ERROR] Required command '$cmd' not found. Please install it first."
        exit 1
    fi
done

# Create bin directory
mkdir -p "$INSTALL_DIR" || { echo "[ERROR] Failed to create directory $INSTALL_DIR"; exit 1; }

# Check if zstd already exists
if [[ -f "$ZSTD_BIN_PATH" ]]; then
    echo "[INFO] zstd already exists at $ZSTD_BIN_PATH, skipping download."
else
    TMP_FILE=$(mktemp) || { echo "[ERROR] Failed to create temp file"; exit 1; }
    echo "[INFO] Downloading zstd..."
    if ! curl -L "$ZSTD_URL" -o "$TMP_FILE"; then
        echo "[ERROR] Failed to download zstd from $ZSTD_URL"
        rm -f "$TMP_FILE"
        exit 1
    fi

    echo "[INFO] Extracting zstd..."
    if ! tar -xvzf "$TMP_FILE" -C "$INSTALL_DIR"; then
        echo "[ERROR] Failed to extract zstd"
        rm -f "$TMP_FILE"
        exit 1
    fi
    rm -f "$TMP_FILE"

    # Compile zstd
    cd "$ZSTD_SRC_DIR" || { echo "[ERROR] Failed to enter source dir"; exit 1; }
    echo "[INFO] Compiling zstd..."
    if ! make -j"$(nproc)"; then
        echo "[ERROR] Compilation failed"
        exit 1
    fi

    # Copy binary to INSTALL_DIR root
    cp "$ZSTD_SRC_DIR/programs/zstd" "$ZSTD_BIN_PATH" || { echo "[ERROR] Failed to copy zstd binary"; exit 1; }
    echo "[INFO] zstd has been installed to $ZSTD_BIN_PATH"
fi

echo "[SETUP] Setup completed successfully."
