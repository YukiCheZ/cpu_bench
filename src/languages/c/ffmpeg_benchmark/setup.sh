#!/usr/bin/env bash
#
# build_ffmpeg.sh
# Download, build, and locally install FFmpeg (CPU-only, no external codecs)
#
# Options:
#   --compiler [gcc|clang]
#   --opt [-O0|-O1|-O2|-O3]
#

set -e
set -u

# ===== Configuration =====
FFMPEG_VERSION="n7.1.2"
FFMPEG_URL="https://github.com/FFmpeg/FFmpeg/archive/refs/tags/${FFMPEG_VERSION}.tar.gz"

PROJECT_ROOT="$(pwd)"
BUILD_DIR="${PROJECT_ROOT}/bin/ffmpeg_build"
INSTALL_DIR="${PROJECT_ROOT}/bin/ffmpeg_install"
LOG_FILE="${BUILD_DIR}/build.log"
PROGRAM_SRC="${PROJECT_ROOT}/ffmpeg_benchmark.c"
PROGRAM_OUT="${PROJECT_ROOT}/bin/ffmpeg_benchmark"

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
echo "[INFO] FFmpeg version: ${FFMPEG_VERSION}"
echo "[INFO] Compiler: ${COMPILER}"
echo "[INFO] Optimization: ${OPT_LEVEL}"
echo "[INFO] Install path: ${INSTALL_DIR}"
echo

# ===== Prepare directories =====
mkdir -p "${BUILD_DIR}"
mkdir -p "${INSTALL_DIR}"
cd "${BUILD_DIR}"

# ===== Download source if missing =====
if [[ ! -f "ffmpeg-${FFMPEG_VERSION}.tar.gz" ]]; then
    echo "[INFO] Downloading FFmpeg ${FFMPEG_VERSION}..."
    curl -L -o "ffmpeg-${FFMPEG_VERSION}.tar.gz" "${FFMPEG_URL}"
else
    echo "[INFO] Using cached FFmpeg source tarball."
fi

# ===== Extract if not already done =====
if [[ ! -d "FFmpeg-${FFMPEG_VERSION}" ]]; then
    echo "[INFO] Extracting source..."
    tar -xzf "ffmpeg-${FFMPEG_VERSION}.tar.gz"
fi

cd "FFmpeg-${FFMPEG_VERSION}"

# ===== Configure environment =====
export CC="${COMPILER}"
export CFLAGS="${OPT_LEVEL}"

# ===== Clean old build =====
if [[ -f "config.h" ]]; then
    echo "[INFO] Cleaning previous build..."
    make clean >"${LOG_FILE}" 2>&1 || true
fi

# ===== Configure FFmpeg =====
echo "[INFO] Configuring FFmpeg..."
if ! ./configure \
    --prefix="${INSTALL_DIR}" \
    --disable-debug \
    --disable-doc \
    --disable-network \
    --disable-autodetect \
    --disable-x86asm \
    --disable-programs \
    --enable-ffmpeg \
    --enable-avfilter \
    --enable-swscale \
    --enable-avformat \
    --enable-avcodec \
    --enable-swresample \
    --enable-avdevice \
    --enable-static \
    --disable-shared \
    >"${LOG_FILE}" 2>&1; then
    echo "[ERROR] FFmpeg configuration failed. See ${LOG_FILE}"
    exit 1
fi

# ===== Determine CPU cores =====
CPU_CORES=1
if command -v nproc >/dev/null 2>&1; then
    CPU_CORES=$(nproc)
elif [[ "$(uname -s)" == "Darwin" ]]; then
    CPU_CORES=$(sysctl -n hw.ncpu)
fi

# ===== Build and install FFmpeg =====
echo "[INFO] Building FFmpeg with ${CPU_CORES} threads..."
if ! make -j"${CPU_CORES}" >"${LOG_FILE}" 2>&1; then
    echo "[ERROR] FFmpeg build failed. Check ${LOG_FILE}"
    exit 1
fi

if ! make install >"${LOG_FILE}" 2>&1; then
    echo "[ERROR] FFmpeg installation failed. Check ${LOG_FILE}"
    exit 1
fi

# # ===== Compile benchmark program (optional) =====
# if [[ -f "${PROGRAM_SRC}" ]]; then
#     echo "[INFO] Compiling benchmark: ${PROGRAM_SRC}"
#     echo "[INFO] Output binary: ${PROGRAM_OUT}"
#     if ! ${COMPILER} "${PROGRAM_SRC}" -o "${PROGRAM_OUT}" \
#         -I"${INSTALL_DIR}/include" \
#         -L"${INSTALL_DIR}/lib" \
#         ${OPT_LEVEL} >"${LOG_FILE}" 2>&1; then
#         echo "[ERROR] Benchmark compilation failed. Check ${LOG_FILE}"
#         exit 1
#     fi
#     echo "[INFO] Benchmark program compiled successfully!"
# else
#     echo "[WARN] No ffmpeg_benchmark.c found in project root. Skipping program compilation."
# fi

# ===== Summary =====
echo
echo "[INFO] FFmpeg ${FFMPEG_VERSION} successfully built and installed!"
echo "[INFO] Header files: ${INSTALL_DIR}/include"
echo "[INFO] Libraries:    ${INSTALL_DIR}/lib"
echo "[INFO] Binaries:     ${INSTALL_DIR}/bin"
if [[ -f "${PROGRAM_OUT}" ]]; then
    echo "[INFO] Program:      ${PROGRAM_OUT}"
fi
echo
echo "[INFO] Run benchmark with:"
echo "  ${INSTALL_DIR}/bin/ffmpeg -benchmark -f lavfi -i \"testsrc=rate=60:size=1280x720\" -t 10 -f null -"
echo
echo "[INFO] Build log saved to: ${LOG_FILE}"
echo
