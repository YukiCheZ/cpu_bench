#!/bin/bash
set -e

INSTALL_DIR="./bin"

if [ -n "$ESBUILD_BIN" ]; then
    if [ ! -x "$ESBUILD_BIN" ]; then
        echo "Error: ESBUILD_BIN is set but not executable: $ESBUILD_BIN"
        return 1 2>/dev/null || true
    fi
    echo "Using user-provided esbuild binary: $ESBUILD_BIN"
    return 0 2>/dev/null || true
fi

mkdir -p "$INSTALL_DIR"

if [ -x "$INSTALL_DIR/esbuild" ]; then
    echo "esbuild binary already exists at $INSTALL_DIR/esbuild"
    export ESBUILD_BIN="$(pwd)/bin/esbuild"
    echo "ESBUILD_BIN has been set for this shell session."
    return 0 2>/dev/null || true
fi

echo "Downloading esbuild..."
curl -fsSL https://esbuild.github.io/dl/v0.25.7 | sh

mv esbuild "$INSTALL_DIR/esbuild"

export ESBUILD_BIN="$(pwd)/bin/esbuild"
echo "esbuild installed at $ESBUILD_BIN"
echo "ESBUILD_BIN has been set for this shell session."
