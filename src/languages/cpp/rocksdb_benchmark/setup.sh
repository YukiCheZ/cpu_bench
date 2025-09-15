#!/usr/bin/env bash

set -e

# Default parameters
COMPILER="gcc"
OPT_LEVEL="-O2"

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --compiler)
            COMPILER="$2"
            shift 2
            ;;
        --opt)
            OPT_LEVEL="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1"
            echo "Usage: $0 [--compiler clang|gcc] [--opt -O2|-O3]"
            exit 1
            ;;
    esac
done

# Target installation directory
INSTALL_DIR="$(realpath ./bin)"
ROCKSDB_SRC_DIR="$INSTALL_DIR/rocksdb"
DB_BENCH_BIN_PATH="$INSTALL_DIR/db_bench"

# Download link (latest stable release)
ROCKSDB_URL="https://github.com/facebook/rocksdb.git"

# Check if required commands exist
for cmd in git make cmake realpath; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "ERROR: Required command '$cmd' not found. Please install it first."
        exit 1
    fi
done

echo "Please ensure that the following libraries are installed on your system:"
echo "  - gflags (for command-line options)"
echo "  - snappy (for compression support)"
echo "  These are required before compiling db_bench."
echo

# Create bin directory
mkdir -p "$INSTALL_DIR" || { echo "ERROR: Failed to create directory $INSTALL_DIR"; exit 1; }

# Clone or update RocksDB source
if [[ -d "$ROCKSDB_SRC_DIR" ]]; then
    echo "RocksDB source already exists, updating..."
    cd "$ROCKSDB_SRC_DIR" || { echo "ERROR: Failed to enter $ROCKSDB_SRC_DIR"; exit 1; }
    git pull --rebase || { echo "ERROR: Failed to update RocksDB repo"; exit 1; }
else
    echo "Cloning RocksDB..."
    git clone --depth 1 "$ROCKSDB_URL" "$ROCKSDB_SRC_DIR" || { echo "ERROR: Failed to clone RocksDB"; exit 1; }
    cd "$ROCKSDB_SRC_DIR"
fi

echo "Cleaning previous build..."
make clean || true

echo "Compiling RocksDB db_bench..."
BUILD_LOG=$(mktemp)

if ! DEBUG_LEVEL=0 \
    USE_CLANG=$([ "$COMPILER" == "clang" ] && echo 1 || echo 0) \
    OPTIMIZE_LEVEL="$OPT_LEVEL" \
    DISABLE_WARNING_AS_ERROR=1 \
    USE_SNAPPY=1 \
    make db_bench -j"$(nproc)" >"$BUILD_LOG" 2>&1; then
    echo "ERROR: Compilation failed. Build output:"
    cat "$BUILD_LOG"
    rm -f "$BUILD_LOG"
    exit 1
fi

rm -f "$BUILD_LOG"

# Copy db_bench binary to INSTALL_DIR root
cp "$ROCKSDB_SRC_DIR/db_bench" "$DB_BENCH_BIN_PATH" || { echo "ERROR: Failed to copy db_bench binary"; exit 1; }
echo "db_bench has been installed to $DB_BENCH_BIN_PATH"

echo "Setup completed successfully."
echo "Run './bin/db_bench --help' to see available benchmarks and options."
