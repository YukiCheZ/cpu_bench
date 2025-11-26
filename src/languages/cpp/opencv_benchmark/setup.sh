#!/usr/bin/env bash
#
# build_opencv.sh
# Download, build, and locally install a minimal static OpenCV (no system pollution)
#
# Options:
#   --compiler [gcc|clang]
#   --opt [-O0|-O1|-O2|-O3]
#

set -e
set -u

# ===== Configuration =====
OPENCV_VERSION="4.12.0"
OPENCV_URL="https://github.com/opencv/opencv/archive/refs/tags/${OPENCV_VERSION}.tar.gz"

PROJECT_ROOT="$(pwd)"
BUILD_DIR="${PROJECT_ROOT}/bin/opencv_build"
INSTALL_DIR="${PROJECT_ROOT}/bin/opencv_install"
LOG_FILE="${BUILD_DIR}/build.log"

PROGRAM_SRC_DIR="${PROJECT_ROOT}/src"
PROGRAM_OUT="${PROJECT_ROOT}/bin/opencv_benchmark"

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

# Determine C++ compiler
if [[ "$COMPILER" == "gcc" ]]; then
    CXX_COMPILER="g++"
else
    CXX_COMPILER="${COMPILER}++"
fi

# ===== Display configuration =====
echo "[INFO] OpenCV version: ${OPENCV_VERSION}"
echo "[INFO] Compiler: ${COMPILER}"
echo "[INFO] Optimization: ${OPT_LEVEL}"
echo "[INFO] Install path: ${INSTALL_DIR}"
echo

# ===== Prepare directories =====
mkdir -p "${BUILD_DIR}"
mkdir -p "${INSTALL_DIR}"
cd "${BUILD_DIR}"

# ===== Download source =====
if [[ ! -f "opencv-${OPENCV_VERSION}.tar.gz" ]]; then
    echo "[INFO] Downloading OpenCV ${OPENCV_VERSION}..."
    curl -L -o "opencv-${OPENCV_VERSION}.tar.gz" "${OPENCV_URL}"
else
    echo "[INFO] Using cached OpenCV source tarball."
fi

# ===== Extract source =====
if [[ ! -d "opencv-${OPENCV_VERSION}" ]]; then
    echo "[INFO] Extracting source..."
    tar -xzf "opencv-${OPENCV_VERSION}.tar.gz"
fi

cd "opencv-${OPENCV_VERSION}"

# ===== Configure environment =====
export CC="${COMPILER}"
export CXX="${CXX_COMPILER}"
export CFLAGS="${OPT_LEVEL}"
export CXXFLAGS="${OPT_LEVEL}"

# ===== Clean old build =====
rm -rf build && mkdir build && cd build

# ===== Detect CPU cores =====
CPU_CORES=1
if command -v nproc >/dev/null 2>&1; then
    CPU_CORES=$(nproc)
elif [[ "$(uname -s)" == "Darwin" ]]; then
    CPU_CORES=$(sysctl -n hw.ncpu)
fi

# ===== Configure OpenCV =====
echo "[INFO] Configuring OpenCV..."
if ! cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="${INSTALL_DIR}" \
    -DCMAKE_C_COMPILER="${COMPILER}" \
    -DCMAKE_CXX_COMPILER="${CXX_COMPILER}" \
    -DBUILD_LIST=core,imgproc,highgui,imgcodecs,video,features2d \
    -DBUILD_SHARED_LIBS=OFF \
    -DBUILD_EXAMPLES=OFF \
    -DBUILD_TESTS=OFF \
    -DBUILD_PERF_TESTS=OFF \
    -DBUILD_DOCS=OFF \
    -DWITH_IPP=OFF \
    -DWITH_TBB=OFF \
    -DWITH_EIGEN=OFF \
    -DWITH_ITT=OFF \
    -DWITH_LAPACK=OFF \
    -DWITH_OPENCL=OFF \
    -DWITH_OPENMP=OFF \
    -DWITH_TIFF=OFF \
    -DWITH_JASPER=OFF \
    -DWITH_OPENJPEG=OFF \
    -DWITH_WEBP=OFF \
    -DWITH_PNG=ON \
    -DWITH_JPEG=ON \
    -DWITH_QT=OFF \
    -DWITH_V4L=OFF \
    -DWITH_GTK=OFF \
    -DWITH_FFMPEG=OFF \
    -DENABLE_NEON=OFF \
    -DWITH_CAROTENE=OFF \
    >"${LOG_FILE}" 2>&1; then
    echo "[ERROR] OpenCV configuration failed. See ${LOG_FILE}"
    exit 1
fi

# ===== Build and install =====
echo "[INFO] Building OpenCV with ${CPU_CORES} threads..."
if ! make -j"${CPU_CORES}" >"${LOG_FILE}" 2>&1; then
    echo "[ERROR] OpenCV build failed. Check ${LOG_FILE}"
    exit 1
fi

if ! make install >"${LOG_FILE}" 2>&1; then
    echo "[ERROR] OpenCV installation failed. Check ${LOG_FILE}"
    exit 1
fi

# ===== Compile your program =====
if [[ -f "${PROGRAM_SRC_DIR}/main.cpp" ]]; then
    echo "[INFO] Compiling your program..."
    SRC_FILES=$(find "${PROGRAM_SRC_DIR}" -name '*.cpp')
    if ! ${CXX_COMPILER} ${OPT_LEVEL} ${SRC_FILES} \
            -I"${INSTALL_DIR}/include/opencv4" \
            -L"${INSTALL_DIR}/lib" \
            -lopencv_features2d \
            -lopencv_imgcodecs \
            -lopencv_highgui \
            -lopencv_video \
            -lopencv_imgproc \
            -lopencv_core \
            -lpthread -ldl -lm -lz \
            -o "${PROGRAM_OUT}" >"${LOG_FILE}" 2>&1; then
        echo "[ERROR] Program compilation failed. Check ${LOG_FILE}"
        exit 1
    fi
    echo "[INFO] Program compiled successfully: ${PROGRAM_OUT}"
else
    echo "[WARN] No main.cpp found in src/. Skipping program compilation."
fi

# ===== Summary =====
echo
echo "[INFO] OpenCV ${OPENCV_VERSION} successfully built and installed!"
echo "[INFO] Headers: ${INSTALL_DIR}/include/opencv4"
echo "[INFO] Libraries: ${INSTALL_DIR}/lib"
echo
if [[ -f "${PROGRAM_OUT}" ]]; then
    echo "[INFO] Your executable: ${PROGRAM_OUT}"
    echo "[INFO] Run it with: ./bin/$(basename "${PROGRAM_OUT}")"
fi
echo
echo "[INFO] Build log saved to: ${LOG_FILE}"
