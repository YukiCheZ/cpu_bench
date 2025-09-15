#!/bin/bash
# build.sh - compile the OpenSSL CPU benchmark

COMPILER="gcc"
OPT_LEVEL="-O3"
SRC="openssl_benchmark.c"
OUT_DIR="./bin"
OUT_NAME="openssl_benchmark"

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
            echo "Usage: $0 [--compiler gcc|clang] [--opt O0|O1|O2|O3|Ofast]"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/$OUT_NAME"

echo "Compiling $SRC with $COMPILER $OPT_LEVEL ..."

$COMPILER $OPT_LEVEL -march=native -o "$OUT" "$SRC" -lcrypto 
if [ $? -ne 0 ]; then
    echo "Compilation failed!"
    exit 1
fi

echo "Build finished. Output: $OUT"
