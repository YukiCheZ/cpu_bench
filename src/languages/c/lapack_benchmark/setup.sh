#!/usr/bin/env bash
set -e
set -o pipefail

# -------------------------------
# Default configuration
# -------------------------------
COMPILER="gcc"
OPT_LEVEL="-O3"
OPENBLAS_VERSION="0.3.30"
OPENBLAS_URL="https://github.com/OpenMathLib/OpenBLAS/releases/download/v${OPENBLAS_VERSION}/OpenBLAS-${OPENBLAS_VERSION}.tar.gz"
BIN_DIR="./bin"
INSTALL_DIR="${BIN_DIR}/openblas_install"

# -------------------------------
# Argument parsing
# -------------------------------
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
        --help)
            echo "Usage: $0 [--compiler gcc|clang] [--opt -O0|-O1|-O2|-O3]"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "[INFO] Compiler: $COMPILER"
echo "[INFO] Optimization: $OPT_LEVEL"

# -------------------------------
# Prepare directories
# -------------------------------
mkdir -p "${BIN_DIR}"
cd "${BIN_DIR}"

# -------------------------------
# Download OpenBLAS if not exists
# -------------------------------
if [ ! -d "OpenBLAS-${OPENBLAS_VERSION}" ]; then
    echo "[INFO] Downloading OpenBLAS ${OPENBLAS_VERSION}..."
    curl -LO "${OPENBLAS_URL}"
    tar -xzf "OpenBLAS-${OPENBLAS_VERSION}.tar.gz"
fi

cd "OpenBLAS-${OPENBLAS_VERSION}"

# -------------------------------
# Build OpenBLAS + LAPACKE
# -------------------------------
echo "[INFO] Building OpenBLAS + LAPACKE..."
make CC=${COMPILER} MOREFLAGS="${OPT_LEVEL}" LAPACKE=1 -j$(nproc)

# -------------------------------
# Install to local directory
# -------------------------------
echo "[INFO] Installing to ${INSTALL_DIR}..."
make PREFIX="${INSTALL_DIR}" install

echo "[SUCCESS] OpenBLAS + LAPACKE built and installed."
echo "Include dir: ${INSTALL_DIR}/include"
echo "Library dir: ${INSTALL_DIR}/lib"
