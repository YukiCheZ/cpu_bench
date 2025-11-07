#!/usr/bin/env bash
set -e

COCKROACH_VERSION="v23.1.30"
INSTALL_DIR="./bin"
TARBALL="${INSTALL_DIR}/cockroach-${COCKROACH_VERSION}.tgz"

if [ -n "$COCKROACH_BIN" ]; then
    if [ ! -x "$COCKROACH_BIN" ]; then
        echo "[ERROR] COCKROACH_BIN is set but not executable: $COCKROACH_BIN"
        return 1 2>/dev/null || exit 1
    fi
    echo "[INFO] Using user-provided CockroachDB binary: $COCKROACH_BIN"
    return 0 2>/dev/null || exit 0
fi

ARCH=$(uname -m)
case "$ARCH" in
    x86_64) COCKROACH_URL="https://binaries.cockroachdb.com/cockroach-${COCKROACH_VERSION}.linux-amd64.tgz" ;;
    aarch64) COCKROACH_URL="https://binaries.cockroachdb.com/cockroach-${COCKROACH_VERSION}.linux-arm64.tgz" ;;
    *)
        echo "[ERROR] Unsupported architecture: $ARCH"
        return 1 2>/dev/null || exit 1
        ;;
esac

mkdir -p "$INSTALL_DIR"

if [ -x "$INSTALL_DIR/cockroach" ]; then
    echo "[INFO] CockroachDB binary already exists at $INSTALL_DIR/cockroach"
    echo "[INFO] Skipping download."
    echo "[INFO] You can run your benchmark now."
    return 0 2>/dev/null || exit 0
fi

if [ -f "$TARBALL" ]; then
    echo "[INFO] Found existing tarball: $TARBALL"
else
    echo "[INFO] Downloading CockroachDB ${COCKROACH_VERSION} for $ARCH..."
    curl -L "$COCKROACH_URL" -o "$TARBALL"
fi

echo "[INFO] Extracting..."
tar -xzf "$TARBALL" --strip-components=1 -C "$INSTALL_DIR"

echo "[INFO] Cleaning up..."
rm -f "$TARBALL"

if [ ! -x "$INSTALL_DIR/cockroach" ]; then
    echo "[ERROR] Installation failed: binary not found or not executable."
    exit 1
fi

echo "[INFO] CockroachDB installed successfully at $INSTALL_DIR/cockroach"
echo "[INFO] You can set COCKROACH_BIN=\"$INSTALL_DIR/cockroach\" in your environment."
