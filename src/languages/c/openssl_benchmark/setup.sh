#!/usr/bin/env bash
#
# build_openssl.sh
# Download, build, and locally install OpenSSL under ./bin/openssl_install,
# then compile your C program using the same compiler and optimization flags.
#
# Options:
#   --compiler [gcc|clang]
#   --opt [-O0|-O1|-O2|-O3]
#

set -e
set -u

# ===== Configuration =====
OPENSSL_VERSION="3.6.0"
OPENSSL_URL="https://github.com/openssl/openssl/releases/download/openssl-${OPENSSL_VERSION}/openssl-${OPENSSL_VERSION}.tar.gz"
PROJECT_ROOT="$(pwd)"
BUILD_DIR="${PROJECT_ROOT}/bin/openssl"
INSTALL_DIR="${PROJECT_ROOT}/bin/openssl_install"
LOG_FILE="${BUILD_DIR}/build.log"
PROGRAM_SRC="${PROJECT_ROOT}/openssl_benchmark.c"
PROGRAM_OUT="${PROJECT_ROOT}/bin/openssl_benchmark"

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
echo "[INFO] OpenSSL version: ${OPENSSL_VERSION}"
echo "[INFO] Compiler: ${COMPILER}"
echo "[INFO] Optimization: ${OPT_LEVEL}"
echo "[INFO] Install path: ${INSTALL_DIR}"
echo

# ===== Prepare directories =====
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"
mkdir -p "${INSTALL_DIR}"
cd "${BUILD_DIR}"

# ===== Download source =====
if [[ ! -f "openssl-${OPENSSL_VERSION}.tar.gz" ]]; then
    echo "[INFO] Downloading OpenSSL ${OPENSSL_VERSION}..."
    curl -L -o "openssl-${OPENSSL_VERSION}.tar.gz" "${OPENSSL_URL}"
else
    echo "[INFO] Using cached source tarball."
fi

# ===== Extract source =====
tar -xzf "openssl-${OPENSSL_VERSION}.tar.gz"
cd "openssl-${OPENSSL_VERSION}"

# ===== Detect platform =====
UNAME_OUT="$(uname -s)"
case "${UNAME_OUT}" in
    Linux*)     TARGET="linux-x86_64" ;;
    Darwin*)
        ARCH=$(uname -m)
        if [[ "${ARCH}" == "arm64" ]]; then
            TARGET="darwin64-arm64-cc"
        else
            TARGET="darwin64-x86_64-cc"
        fi ;;
    *) echo "[ERROR] Unsupported platform: ${UNAME_OUT}"; exit 1 ;;
esac

# ===== Configure build =====
echo "[INFO] Configuring OpenSSL for ${TARGET}..."
export CC="${COMPILER}"
export CFLAGS="${OPT_LEVEL}"

if ! ./Configure "${TARGET}" \
    --prefix="${INSTALL_DIR}" \
    --openssldir="${INSTALL_DIR}" \
    shared >"${LOG_FILE}" 2>&1; then
    echo "[ERROR] OpenSSL configuration failed. See ${LOG_FILE}"
    exit 1
fi

# ===== Determine CPU cores =====
CPU_CORES=1
if command -v nproc >/dev/null 2>&1; then
    CPU_CORES=$(nproc)
elif [[ "${UNAME_OUT}" == "Darwin" ]]; then
    CPU_CORES=$(sysctl -n hw.ncpu)
fi

# ===== Build and install OpenSSL =====
echo "[INFO] Building OpenSSL with ${CPU_CORES} threads..."
if ! make -j"${CPU_CORES}" >"${LOG_FILE}" 2>&1; then
    echo "[ERROR] OpenSSL build failed. Check ${LOG_FILE}"
    exit 1
fi

if ! make install_sw >"${LOG_FILE}" 2>&1; then
    echo "[ERROR] OpenSSL installation failed. Check ${LOG_FILE}"
    exit 1
fi

# ===== Compile user program =====
if [[ -f "${PROGRAM_SRC}" ]]; then
    echo "[INFO] Compiling program: ${PROGRAM_SRC}"
    echo "[INFO] Output binary: ${PROGRAM_OUT}"
    if ! ${COMPILER} "${PROGRAM_SRC}" -o "${PROGRAM_OUT}" \
        -I"${INSTALL_DIR}/include" \
        -L"${INSTALL_DIR}/lib" \
        -lssl -lcrypto \
        ${OPT_LEVEL} >"${LOG_FILE}" 2>&1; then
        echo "[ERROR] Program compilation failed. Check ${LOG_FILE}"
        exit 1
    fi
    echo "[SETUP] Program compiled successfully!"
else
    echo "[WARN] No main.c found in project root. Skipping program compilation."
fi

# ===== Summary =====
echo
echo "[INFO] OpenSSL ${OPENSSL_VERSION} successfully built!"
echo "[INFO] Header files: ${INSTALL_DIR}/include"
echo "[INFO] Libraries:    ${INSTALL_DIR}/lib"
echo "[INFO] Binaries:     ${INSTALL_DIR}/bin"
if [[ -f "${PROGRAM_OUT}" ]]; then
    echo "[INFO] Program:      ${PROGRAM_OUT}"
fi
echo
echo "[INFO] To manually compile later:"
echo "  ${COMPILER} main.c -I${INSTALL_DIR}/include -L${INSTALL_DIR}/lib -lssl -lcrypto ${OPT_LEVEL} -o main"
echo
echo "[INFO] Detailed build log saved to ${LOG_FILE}"
echo
