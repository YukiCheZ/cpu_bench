#!/bin/bash
set -e

if [ $# -lt 3 ]; then
  echo "Usage: $0 <mode: collection|immutable|cache> <dataSize> <copies> [iterations]"
  exit 1
fi

MODE=$1
DATASIZE=$2
COPIES=$3
ITERATIONS=$4

SRC_DIR="benchmarks"
BIN_DIR="build"
GUAVA_JAR="guava-33.4.8-jre.jar"

mkdir -p "$BIN_DIR"

echo "[Build] Compiling Java sources..."
find $SRC_DIR -name "*.java" > sources.txt
javac -cp "$GUAVA_JAR" -d "$BIN_DIR" @sources.txt
rm sources.txt

echo "[Run] Starting benchmark"

# Run the benchmark
java -cp "$BIN_DIR:$GUAVA_JAR" benchmarks.GuavaCPUBenchmark $MODE $DATASIZE $COPIES $ITERATIONS
