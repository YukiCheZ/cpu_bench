#!/usr/bin/env bash
#
# build_rocksdb.sh
# Download, build, and locally install RocksDB + gflags + Snappy (no system pollution)
#
# Options:
#   --compiler [gcc|clang]
#   --opt [-O0|-O1|-O2|-O3]
#

set -e
set -u

# ===== Configuration =====
ROCKSDB_VERSION="10.7.5"
ROCKSDB_URL="https://github.com/facebook/rocksdb/archive/refs/tags/v${ROCKSDB_VERSION}.tar.gz"

GFLAGS_VERSION="2.2.2"
GFLAGS_URL="https://github.com/gflags/gflags/archive/refs/tags/v${GFLAGS_VERSION}.tar.gz"

SNAPPY_VERSION="1.2.2"
SNAPPY_URL="https://github.com/google/snappy/archive/refs/tags/${SNAPPY_VERSION}.tar.gz"

PROJECT_ROOT="$(pwd)"
BUILD_DIR="${PROJECT_ROOT}/bin/rocksdb_build"
INSTALL_DIR="${PROJECT_ROOT}/bin/rocksdb_install"
LOG_FILE="${BUILD_DIR}/build.log"

COMPILER="gcc"
OPT_LEVEL="-O3"

# ===== Parse arguments =====
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

# Determine C++ compiler
if [[ "$COMPILER" == "gcc" ]]; then
    CXX_COMPILER="g++"
else
    CXX_COMPILER="${COMPILER}++"
fi

# ===== Display configuration =====
echo "[INFO] RocksDB version: ${ROCKSDB_VERSION}"
echo "[INFO] gflags version:  ${GFLAGS_VERSION}"
echo "[INFO] Snappy version:  ${SNAPPY_VERSION}"
echo "[INFO] Compiler: ${COMPILER} / ${CXX_COMPILER}"
echo "[INFO] Optimization: ${OPT_LEVEL}"
echo "[INFO] Install path: ${INSTALL_DIR}"
echo

# ===== Prepare directories =====
mkdir -p "${BUILD_DIR}" "${INSTALL_DIR}"
cd "${BUILD_DIR}"

# ===== Determine CPU cores =====
CPU_CORES=1
if command -v nproc >/dev/null 2>&1; then
    CPU_CORES=$(nproc)
elif [[ "$(uname -s)" == "Darwin" ]]; then
    CPU_CORES=$(sysctl -n hw.ncpu)
fi

# ===== Step 0: Build Snappy locally =====
SNAPPY_SRC_DIR="${BUILD_DIR}/snappy-${SNAPPY_VERSION}"
SNAPPY_BUILD_DIR="${SNAPPY_SRC_DIR}/_build"

# Clean previous builds
rm -rf "${SNAPPY_SRC_DIR}" "${SNAPPY_BUILD_DIR}"

if [[ ! -f "snappy-${SNAPPY_VERSION}.tar.gz" ]]; then
    echo "[INFO] Downloading Snappy ${SNAPPY_VERSION}..."
    curl -L -o "snappy-${SNAPPY_VERSION}.tar.gz" "${SNAPPY_URL}"
else
    echo "[INFO] Using cached Snappy source."
fi

if [[ ! -d "${SNAPPY_SRC_DIR}" ]]; then
    echo "[INFO] Extracting Snappy..."
    tar -xzf "snappy-${SNAPPY_VERSION}.tar.gz"
fi

mkdir -p "${SNAPPY_BUILD_DIR}"
cd "${SNAPPY_BUILD_DIR}"

echo "[INFO] Building Snappy (tests OFF)..."
cmake .. \
    -DCMAKE_INSTALL_PREFIX="${INSTALL_DIR}" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_C_COMPILER="${COMPILER}" \
    -DCMAKE_CXX_COMPILER="${CXX_COMPILER}" \
    -DBUILD_SHARED_LIBS=OFF \
    -DSNAPPY_BUILD_TESTS=OFF \
    -DSNAPPY_BUILD_BENCHMARKS=OFF >"${LOG_FILE}" 2>&1

make -j"${CPU_CORES}" >>"${LOG_FILE}" 2>&1
make install >>"${LOG_FILE}" 2>&1

cd "${BUILD_DIR}"
echo "[INFO] Snappy installed locally to ${INSTALL_DIR}"
echo

# ===== Step 1: Build gflags locally =====
GFLAGS_SRC_DIR="${BUILD_DIR}/gflags-${GFLAGS_VERSION}"
GFLAGS_BUILD_DIR="${GFLAGS_SRC_DIR}/_build"

# Clean previous builds
rm -rf "${GFLAGS_SRC_DIR}" "${GFLAGS_BUILD_DIR}"

if [[ ! -f "gflags-${GFLAGS_VERSION}.tar.gz" ]]; then
    echo "[INFO] Downloading gflags ${GFLAGS_VERSION}..."
    curl -L -o "gflags-${GFLAGS_VERSION}.tar.gz" "${GFLAGS_URL}"
else
    echo "[INFO] Using cached gflags source."
fi

if [[ ! -d "${GFLAGS_SRC_DIR}" ]]; then
    echo "[INFO] Extracting gflags..."
    tar -xzf "gflags-${GFLAGS_VERSION}.tar.gz"
fi

# Fix cmake_minimum_required for old versions
if grep -q "cmake_minimum_required" "${GFLAGS_SRC_DIR}/CMakeLists.txt"; then
    sed -i.bak 's/cmake_minimum_required(VERSION .*)/cmake_minimum_required(VERSION 3.5)/' "${GFLAGS_SRC_DIR}/CMakeLists.txt" || true
else
    echo "cmake_minimum_required(VERSION 3.5)" | cat - "${GFLAGS_SRC_DIR}/CMakeLists.txt" > "${GFLAGS_SRC_DIR}/CMakeLists.tmp"
    mv "${GFLAGS_SRC_DIR}/CMakeLists.tmp" "${GFLAGS_SRC_DIR}/CMakeLists.txt"
fi

# Clean previous builds
rm -rf "${GFLAGS_BUILD_DIR}"
mkdir -p "${GFLAGS_BUILD_DIR}"
cd "${GFLAGS_BUILD_DIR}"

echo "[INFO] Building gflags..."
cmake .. \
    -DCMAKE_INSTALL_PREFIX="${INSTALL_DIR}" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_C_COMPILER="${COMPILER}" \
    -DCMAKE_CXX_COMPILER="${CXX_COMPILER}" \
    -DBUILD_SHARED_LIBS=OFF \
    -DCMAKE_POLICY_VERSION_MINIMUM=3.5 >"${LOG_FILE}" 2>&1

make -j"${CPU_CORES}" >>"${LOG_FILE}" 2>&1
make install >>"${LOG_FILE}" 2>&1

cd "${BUILD_DIR}"
echo "[INFO] gflags installed locally to ${INSTALL_DIR}"
echo

# ===== Step 2: Build RocksDB =====
ROCKSDB_SRC_DIR="${BUILD_DIR}/rocksdb-${ROCKSDB_VERSION}"

# Clean previous builds
rm -rf "${ROCKSDB_SRC_DIR}"

if [[ ! -f "rocksdb-${ROCKSDB_VERSION}.tar.gz" ]]; then
    echo "[INFO] Downloading RocksDB ${ROCKSDB_VERSION}..."
    curl -L -o "rocksdb-${ROCKSDB_VERSION}.tar.gz" "${ROCKSDB_URL}"
else
    echo "[INFO] Using cached RocksDB source."
fi

if [[ ! -d "${ROCKSDB_SRC_DIR}" ]]; then
    echo "[INFO] Extracting RocksDB..."
    tar -xzf "rocksdb-${ROCKSDB_VERSION}.tar.gz"
fi

cd "${ROCKSDB_SRC_DIR}"
echo "[INFO] Cleaning previous RocksDB build..."
make clean > /dev/null 2>&1 || true

# ===== Include & library paths =====
USE_CLANG=$([ "$COMPILER" == "clang" ] && echo 1 || echo 0)
EXTRA_INCLUDE_FLAGS="-I${INSTALL_DIR}/include"
EXTRA_LIB_FLAGS="-L${INSTALL_DIR}/lib"

# ===== Build =====
echo "[INFO] Building RocksDB with Snappy + gflags support..."
if ! USE_CLANG=$USE_CLANG \
    OPTIMIZE_LEVEL="$OPT_LEVEL" \
    DISABLE_WARNING_AS_ERROR=1 \
    DEBUG_LEVEL=0 \
    USE_SNAPPY=1 \
    USE_GFLAGS=1 \
    EXTRA_CXXFLAGS="${EXTRA_INCLUDE_FLAGS}" \
    EXTRA_LDFLAGS="${EXTRA_LIB_FLAGS} -lgflags -lsnappy" \
    make db_bench -j"${CPU_CORES}" >"${LOG_FILE}" 2>&1; then
    echo "[ERROR] RocksDB build failed. Check ${LOG_FILE}"
    exit 1
fi

# ===== Install db_bench =====
echo "[INFO] Installing db_bench..."
cp "db_bench" "${INSTALL_DIR}/"
echo "[INFO] RocksDB db_bench installed to ${INSTALL_DIR}/db_bench"

# ===== Summary =====
echo
echo "[INFO] RocksDB + gflags + Snappy built successfully (no system pollution)!"
echo "[INFO] Snappy + gflags installed at: ${INSTALL_DIR}"
echo "[INFO]
