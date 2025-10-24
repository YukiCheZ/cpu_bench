#!/usr/bin/env bash
set -e

# -------------------------------
# Argument parsing
# -------------------------------
COMPILER="gcc"
OPT_LEVEL="-O3"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --compiler)
            COMPILER="$2"
            shift 2
            ;;
        --opt)
            OPT_LEVEL="$2"
            shift 2
            ;;
        *)
            echo "[ERROR] Unknown option: $1"
            echo "Usage: $0 [--compiler gcc|clang] [--opt -O0|-O1|-O2|-O3]"
            exit 1
            ;;
    esac
done

# Validate compiler
if [[ "$COMPILER" != "gcc" && "$COMPILER" != "clang" ]]; then
    echo "[ERROR] Unsupported compiler: $COMPILER (must be gcc or clang)"
    exit 1
fi

# Validate optimization level
if [[ ! "$OPT_LEVEL" =~ ^-O[0-3]$ ]]; then
    echo "[ERROR] Invalid optimization level: $OPT_LEVEL"
    exit 1
fi

echo "[CONFIG] Using compiler: $COMPILER"
echo "[CONFIG] Using optimization: $OPT_LEVEL"

# -------------------------------
# Paths and URLs
# -------------------------------
INSTALL_DIR="./bin"
mkdir -p "$INSTALL_DIR"
INSTALL_DIR=$(realpath "$INSTALL_DIR")

ZSTD_VERSION="1.5.7"
ZSTD_SRC_DIR="$INSTALL_DIR/zstd-$ZSTD_VERSION"
ZSTD_BIN_PATH="$INSTALL_DIR/zstd"
ZSTD_URL="https://github.com/facebook/zstd/releases/download/v${ZSTD_VERSION}/zstd-${ZSTD_VERSION}.tar.gz"

# -------------------------------
# Prerequisite checks
# -------------------------------
for cmd in curl tar make realpath; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "[ERROR] Required command '$cmd' not found. Please install it first."
        exit 1
    fi
done

# -------------------------------
# Download & extract (only once)
# -------------------------------
if [[ ! -d "$ZSTD_SRC_DIR" ]]; then
    TMP_FILE=$(mktemp)
    echo "[INFO] Downloading zstd from $ZSTD_URL..."
    curl -L "$ZSTD_URL" -o "$TMP_FILE"

    echo "[INFO] Extracting zstd..."
    tar -xvzf "$TMP_FILE" -C "$INSTALL_DIR" >/dev/null
    rm -f "$TMP_FILE"
else
    echo "[INFO] Source directory already exists: $ZSTD_SRC_DIR"
fi

# -------------------------------
# Compile
# -------------------------------
cd "$ZSTD_SRC_DIR"
echo "[INFO] Cleaning old build..."
make clean >/dev/null 2>&1 || true

echo "[INFO] Compiling zstd with $COMPILER $OPT_LEVEL ..."
BUILD_LOG=$(mktemp)

if make -j"$(nproc)" CC="$COMPILER" MOREFLAGS="$OPT_LEVEL" >"$BUILD_LOG" 2>&1; then
    echo "[INFO] Compilation succeeded."
else
    echo "[ERROR] Compilation failed. See build log below:"
    echo "--------------------------------"
    cat "$BUILD_LOG"
    echo "--------------------------------"
    rm -f "$BUILD_LOG"
    exit 1
fi

rm -f "$BUILD_LOG"

# Copy binary
cp "$ZSTD_SRC_DIR/programs/zstd" "$ZSTD_BIN_PATH"
echo "[INFO] zstd has been built and installed to $ZSTD_BIN_PATH"

echo "[SETUP] Setup completed successfully."
