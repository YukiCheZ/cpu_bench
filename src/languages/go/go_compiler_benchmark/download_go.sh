#!/usr/bin/env bash
set -e
VERSION=go1.24.5
if [ ! -d go ]; then
    echo "[INFO] Downloading Go source $VERSION..."
    curl -LO https://go.dev/dl/$VERSION.src.tar.gz
    tar -xzf $VERSION.src.tar.gz
    rm $VERSION.src.tar.gz
else
    echo "[INFO] Go source already exists."
fi
