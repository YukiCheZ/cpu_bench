#!/usr/bin/env bash
#
# build_redis.sh
# Download, build, and locally install Redis (CPU-only)
#
# Options:
#   --compiler [gcc|clang]
#   --opt [-O0|-O1|-O2|-O3]
#

set -e
set -u

# ===== Configuration =====
REDIS_VERSION="8.2.2"
REDIS_URL="https://github.com/redis/redis/archive/refs/tags/${REDIS_VERSION}.tar.gz"

PROJECT_ROOT="$(pwd)"
BUILD_DIR="${PROJECT_ROOT}/bin/redis_build"
INSTALL_DIR="${PROJECT_ROOT}/bin/redis_install"
LOG_FILE="${BUILD_DIR}/build.log"

# redis-8.2.2 can not be built with clang.
COMPILER="gcc"
OPT_LEVEL="-O3"

# ===== Argument parsing =====
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
            echo "Unknown option: $1"
            echo "Usage: $0 [--compiler gcc|clang] [--opt -O1|-O2|-O3]"
            exit 1
            ;;
    esac
done

# ===== Display configuration =====
echo "[INFO] Redis version: ${REDIS_VERSION}"
echo "[INFO] Compiler: ${COMPILER}"
echo "[INFO] Optimization: ${OPT_LEVEL}"
echo "[INFO] Install path: ${INSTALL_DIR}"
echo

# ===== Prepare directories =====
mkdir -p "${BUILD_DIR}"
mkdir -p "${INSTALL_DIR}"
cd "${BUILD_DIR}"

# ===== Download source if missing =====
if [[ ! -f "redis-${REDIS_VERSION}.tar.gz" ]]; then
    echo "[INFO] Downloading Redis ${REDIS_VERSION}..."
    curl -L -o "redis-${REDIS_VERSION}.tar.gz" "${REDIS_URL}"
else
    echo "[INFO] Using cached Redis source tarball."
fi

# ===== Extract if not already done =====
if [[ ! -d "redis-${REDIS_VERSION}" ]]; then
    echo "[INFO] Extracting source..."
    tar -xzf "redis-${REDIS_VERSION}.tar.gz"
fi

cd "redis-${REDIS_VERSION}"

# ===== Configure environment =====
export CC="${COMPILER}"
export CFLAGS="${OPT_LEVEL}"

# ===== Clean old build =====
if [[ -f "src/redis-server" ]]; then
    echo "[INFO] Cleaning previous build..."
    make distclean >"${LOG_FILE}" 2>&1 || true
fi

# ===== Determine CPU cores =====
CPU_CORES=1
if command -v nproc >/dev/null 2>&1; then
    CPU_CORES=$(nproc)
elif [[ "$(uname -s)" == "Darwin" ]]; then
    CPU_CORES=$(sysctl -n hw.ncpu)
fi

# ===== Build Redis =====
echo "[INFO] Building Redis with ${CPU_CORES} threads..."
if ! make -j"${CPU_CORES}" CC="${COMPILER}" CFLAGS="${OPT_LEVEL}" >"${LOG_FILE}" 2>&1; then
    echo "[ERROR] Redis build failed. Check ${LOG_FILE}"
    exit 1
fi

# ===== Install locally =====
echo "[INFO] Installing Redis binaries to ${INSTALL_DIR}/..."
cp src/redis-server src/redis-cli src/redis-benchmark "${INSTALL_DIR}/"

# ===== Summary =====
echo
echo "[INFO] Redis ${REDIS_VERSION} successfully built and installed!"
echo "[INFO] Binaries: ${INSTALL_DIR}"
echo
echo "[INFO] Example usage:"
echo "  ${INSTALL_DIR}/redis-server --save '' --appendonly no"
echo "  ${INSTALL_DIR}/redis-benchmark -n 100000 -q"
echo
echo "[INFO] Build log saved to: ${LOG_FILE}"
echo
