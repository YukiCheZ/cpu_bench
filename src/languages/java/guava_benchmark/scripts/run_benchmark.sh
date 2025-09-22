#!/bin/bash
set -e

CONFIG_FILE="$(dirname "$0")/config.sh"
if [ -f "$CONFIG_FILE" ]; then
  source "$CONFIG_FILE"
fi

MODE=$DEFAULT_MODE
COPIES=$DEFAULT_COPIES
ITERATIONS=$DEFAULT_ITERATIONS

declare -A MODE_CONFIG_VARS=(
    ["collection"]="COLLECTION_DATASIZE"
    ["immutable"]="IMMUTABLE_DATASIZE"
    ["cache"]="CACHE_DATASIZE"
)

CONFIG_VAR="${MODE_CONFIG_VARS[$MODE]}"
DATASIZE="${!CONFIG_VAR}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="$2"
      if [[ -z "$DATASIZE_SET" && -n "${MODE_CONFIG_VARS[$MODE]}" ]]; then
        CONFIG_VAR="${MODE_CONFIG_VARS[$MODE]}"
        DATASIZE="${!CONFIG_VAR}"
      fi
      shift 2
      ;;
    --dataSize)
      DATASIZE="$2"
      DATASIZE_SET=true  
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
      echo "Mode-specific default data sizes:"
      echo "  collection: $COLLECTION_DATASIZE"
      echo "  immutable: $IMMUTABLE_DATASIZE"
      echo "  cache: $CACHE_DATASIZE"
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

JVM_OPTS="
  -Xms8g -Xmx8g \
  -XX:+TieredCompilation -XX:TieredStopAtLevel=1 \
  -XX:-UseBiasedLocking
"

java $JVM_OPTS -cp "$BIN_DIR:$GUAVA_JAR" benchmarks.GuavaCPUBenchmark "$MODE" "$DATASIZE" "$COPIES" "$ITERATIONS"
