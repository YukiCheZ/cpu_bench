#!/bin/bash
set -e

# 加载默认配置文件
CONFIG_FILE="$(dirname "$0")/config.sh"
if [ -f "$CONFIG_FILE" ]; then
  source "$CONFIG_FILE"
fi

# 初始化参数为默认值
MODE=$DEFAULT_MODE
DATASIZE=$DEFAULT_DATASIZE
COPIES=$DEFAULT_COPIES
ITERATIONS=$DEFAULT_ITERATIONS

# 参数解析
while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="$2"
      shift 2
      ;;
    --dataSize)
      DATASIZE="$2"
      shift 2
      ;;
    --copies)
      COPIES="$2"
      shift 2
      ;;
    --iterations)
      ITERATIONS="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [--mode <collection|immutable|cache>] [--dataSize <int>] [--copies <int>] [--iterations <int>]"
      echo "Defaults are loaded from $CONFIG_FILE"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage."
      exit 1
      ;;
  esac
done

SRC_DIR="benchmarks"
BIN_DIR="build"
GUAVA_JAR="guava-33.4.8-jre.jar"

mkdir -p "$BIN_DIR"

echo "[Build] Compiling Java sources..."
find $SRC_DIR -name "*.java" > sources.txt
javac -cp "$GUAVA_JAR" -d "$BIN_DIR" @sources.txt
rm sources.txt

echo "[Run] Starting benchmark"
echo "Mode: $MODE, Data size: $DATASIZE, Copies: $COPIES, Iterations per copy: $ITERATIONS"

# Run benchmark
java -cp "$BIN_DIR:$GUAVA_JAR" benchmarks.GuavaCPUBenchmark "$MODE" "$DATASIZE" "$COPIES" "$ITERATIONS"
