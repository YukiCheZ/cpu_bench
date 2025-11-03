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

# -------------------------------
# Paths (absolute)
# -------------------------------
ROOT_DIR="$(pwd)"
BIN_DIR="${ROOT_DIR}/bin"
SRC_DIR="${BIN_DIR}/OpenBLAS-${OPENBLAS_VERSION}"
INSTALL_DIR="${BIN_DIR}/openblas_install"
BENCHMARK_SRC="${ROOT_DIR}/lapack_benchmark.c"
BENCHMARK_BIN="${BIN_DIR}/lapack_benchmark"

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

# -------------------------------
# Download OpenBLAS if not exists
# -------------------------------
if [ ! -d "${SRC_DIR}" ]; then
    if [ ! -f "${BIN_DIR}/OpenBLAS-${OPENBLAS_VERSION}.tar.gz" ]; then
        echo "[INFO] Downloading OpenBLAS ${OPENBLAS_VERSION}..."
        curl -L -o "${BIN_DIR}/OpenBLAS-${OPENBLAS_VERSION}.tar.gz" "${OPENBLAS_URL}"
    else
        echo "[INFO] Using existing tarball."
    fi
    tar -xzf "${BIN_DIR}/OpenBLAS-${OPENBLAS_VERSION}.tar.gz" -C "${BIN_DIR}"
else
    echo "[INFO] OpenBLAS source already exists."
fi

# -------------------------------
# Clean previous build
# -------------------------------
echo "[INFO] Cleaning previous build artifacts..."
make -C "${SRC_DIR}" clean > /dev/null 2>&1 || true

# -------------------------------
# Build OpenBLAS + LAPACKE
# -------------------------------
echo "[INFO] Building OpenBLAS + LAPACKE..."
if ! make -C "${SRC_DIR}" CC=${COMPILER} LAPACKE=1 USE_OPENMP=0 CFLAGS="${OPT_LEVEL}" -j$(nproc) > "${BIN_DIR}/build.log" 2>&1; then
    echo "[ERROR] Build failed! See build.log for details."
    tail -n 50 "${BIN_DIR}/build.log"
    exit 1
fi

# -------------------------------
# Install to local directory
# -------------------------------
echo "[INFO] Installing to ${INSTALL_DIR}..."
make -C "${SRC_DIR}" PREFIX="${INSTALL_DIR}" LAPACKE=1 install > /dev/null

# -------------------------------
# Compile benchmark program
# -------------------------------
echo "[INFO] Compiling benchmark program..."
${COMPILER} "${BENCHMARK_SRC}" \
    ${OPT_LEVEL} -I "${INSTALL_DIR}/include" \
    -L "${INSTALL_DIR}/lib" \
    -Wl,-rpath,"${INSTALL_DIR}/lib" \
    -lopenblas -lpthread -lm -o "${BENCHMARK_BIN}"

# -------------------------------
# Summary
# -------------------------------
echo "[SETUP] OpenBLAS + LAPACKE built and installed."
echo "[SETUP] Benchmark executable: ${BENCHMARK_BIN}"
