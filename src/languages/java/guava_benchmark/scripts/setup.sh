#!/bin/bash
set -euo pipefail

# Setup script: download Guava dependency and compile Java sources.
# Output directories:
#   build/lib      -> third-party jars
#   build/classes  -> compiled .class files

GUAVA_VERSION="33.5.0-jre"
GUAVA_GROUP_PATH="com/google/guava/guava"
GUAVA_JAR="guava-${GUAVA_VERSION}.jar"
GUAVA_URL="https://repo1.maven.org/maven2/${GUAVA_GROUP_PATH}/${GUAVA_VERSION}/${GUAVA_JAR}"

ROOT_DIR="$(dirname "$0")/.."
cd "$ROOT_DIR"

LIB_DIR="build/lib"
CLS_DIR="build/classes"
SRC_DIR="benchmarks"

mkdir -p "$LIB_DIR" "$CLS_DIR"

if [[ ! -f "$LIB_DIR/$GUAVA_JAR" ]]; then
  echo "[SETUP] Downloading Guava $GUAVA_VERSION ..." >&2
  if command -v curl >/dev/null 2>&1; then
    curl -fL "$GUAVA_URL" -o "$LIB_DIR/$GUAVA_JAR"
  elif command -v wget >/dev/null 2>&1; then
    wget -q "$GUAVA_URL" -O "$LIB_DIR/$GUAVA_JAR"
  else
    echo "[ERROR] Neither curl nor wget found; cannot download Guava." >&2
    exit 1
  fi
else
  echo "[SETUP] Guava JAR already exists: $LIB_DIR/$GUAVA_JAR" >&2
fi

echo "[SETUP] Compiling Java sources..." >&2
find "$SRC_DIR" -name "*.java" > sources.txt
javac -cp "$LIB_DIR/$GUAVA_JAR" -d "$CLS_DIR" @sources.txt
rm sources.txt

echo "[SETUP] Done. To run a benchmark: ./scripts/run_benchmark.sh --workload event" >&2
