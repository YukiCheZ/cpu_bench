#!/bin/bash
set -e

VERSION="0.25.7"
INSTALL_DIR="./bin"
TARGET="$INSTALL_DIR/esbuild"

mkdir -p "$INSTALL_DIR"

if [ -x "$TARGET" ]; then
    echo "esbuild already exists."
    exit 0
fi

if ! command -v go &> /dev/null; then
    echo "Error: Building from GitHub source requires Go. Please install Go or use Scheme B."
    exit 1
fi

echo "Downloading source from GitHub..."
curl -L "https://github.com/evanw/esbuild/archive/refs/tags/v$VERSION.tar.gz" -o esbuild-src.tar.gz

tar -xzf esbuild-src.tar.gz
cd "esbuild-$VERSION"

echo "Building esbuild from source..."
go build -ldflags "-s -w" ./cmd/esbuild

mv esbuild "../$TARGET"
cd ..

rm -rf "esbuild-$VERSION" esbuild-src.tar.gz

echo "Successfully built from GitHub: $($TARGET --version)"