#!/bin/bash
set -euo pipefail

# Run script: only executes the benchmark. Compilation & dependency download moved to setup.sh.
# Expects:
#   build/lib/guava-<version>.jar
#   build/classes (compiled .class files)

GUAVA_VERSION="33.5.0-jre"
GUAVA_JAR="build/lib/guava-${GUAVA_VERSION}.jar"
CLASSES_DIR="build/classes"

WORKLOAD="event"
THREADS=1
DATASIZE=""       # optional override
ITERATIONS=""     # optional override
WARMUP=""         # --warmupIterations value
NO_WARMUP=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workload|--mode)
      WORKLOAD="$2"; shift 2 ;;
    --threads|--copies)
      THREADS="$2"; shift 2 ;;
    --dataSize)
      DATASIZE="$2"; shift 2 ;;
    --iterations)
      ITERATIONS="$2"; shift 2 ;;
    --warmupIterations)
      WARMUP="$2"; shift 2 ;;
    --noWarmup)
      NO_WARMUP=true; shift 1 ;;
    -h|--help)
      echo "[Usage] $0 --workload <event|graph|bloom|cache|immutable> [--threads N] [--dataSize N] [--iterations N] [--warmupIterations W | --noWarmup]";
      echo "[Note] defaults for dataSize/iterations are now inside the Java program.";
      exit 0 ;;
    *)
      echo "[WARN] Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ ! -d "$CLASSES_DIR" ]]; then
  echo "[ERROR] Compiled classes not found in $CLASSES_DIR. Run ./scripts/setup.sh first." >&2
  exit 1
fi
if [[ ! -f "$GUAVA_JAR" ]]; then
  echo "[ERROR] Guava JAR not found: $GUAVA_JAR. Run ./scripts/setup.sh first." >&2
  exit 1
fi

ARGS=(--workload "$WORKLOAD" --threads "$THREADS")
[[ -n "$DATASIZE" ]] && ARGS+=(--dataSize "$DATASIZE")
[[ -n "$ITERATIONS" ]] && ARGS+=(--iterations "$ITERATIONS")
[[ -n "$WARMUP" ]] && ARGS+=(--warmupIterations "$WARMUP")
[[ "$NO_WARMUP" == true ]] && ARGS+=(--noWarmup)

echo "[RUN] Workload=$WORKLOAD threads=$THREADS dataSize=${DATASIZE:-<default>} iterations=${ITERATIONS:-<default>} warmup=${WARMUP:-auto} noWarmup=$NO_WARMUP"

java -cp "$CLASSES_DIR:$GUAVA_JAR" benchmarks.BenchmarkRunner "${ARGS[@]}"
