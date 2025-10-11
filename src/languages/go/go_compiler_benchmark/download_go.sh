#!/usr/bin/env bash

VERSION="go1.24.5"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"
GO_DIR="$DATA_DIR/go"
TARBALL="$DATA_DIR/$VERSION.src.tar.gz"
URL="https://go.dev/dl/$VERSION.src.tar.gz"

if [ ! -d "$DATA_DIR" ]; then
    echo "[INFO] Creating data directory..."
    mkdir -p "$DATA_DIR" || {
        echo "[ERROR] Failed to create $DATA_DIR"
        exit 1
    }
fi

if [ -d "$GO_DIR" ]; then
    echo "[INFO] Go source already exists at $GO_DIR."
    exit 0
fi

echo "[INFO] Downloading Go source $VERSION..."
curl -L -o "$TARBALL" "$URL"
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to download $URL"
    rm -f "$TARBALL"
    exit 1
fi

echo "[INFO] Extracting Go source..."
tar -xzf "$TARBALL" -C "$DATA_DIR"
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to extract $TARBALL"
    rm -f "$TARBALL"
    exit 1
fi

rm -f "$TARBALL"

echo "[INFO] Go source installed at $GO_DIR."
