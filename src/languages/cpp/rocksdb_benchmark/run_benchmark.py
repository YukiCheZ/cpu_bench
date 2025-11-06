#!/usr/bin/env python3
import argparse
import subprocess
import sys
import time
import statistics
import shutil
import os
import signal

DB_PATH = "/tmp/rocksdb_bench"

CPU_BENCHMARK_SEQ = (
    "fillseq,"
    "fillrandom,"
    "readrandom,"
    "readwhilewriting,"
    "updaterandom,"
    "seekrandom,"
    "xxh3"
)


def clean_rocksdb_data():
    """Remove RocksDB data directory to avoid persistence effects."""
    if os.path.exists(DB_PATH):
        try:
            shutil.rmtree(DB_PATH)
            print(f"[CLEANUP] Removed {DB_PATH}")
        except Exception as e:
            print(f"[WARNING] Failed to remove {DB_PATH}: {e}")


def run_command(cmd):
    start = time.time()
    result = subprocess.run(
        cmd,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True
    )
    end = time.time()

    if result.returncode != 0:
        print(f"[ERROR] Benchmark failed with return code {result.returncode}")
        if result.stderr:
            print("------- db_bench stderr -------")
            print(result.stderr.strip())
            print("-------------------------------")
        clean_rocksdb_data()
        sys.exit(result.returncode)

    clean_rocksdb_data()
    return end - start


def main():
    parser = argparse.ArgumentParser(description="Run RocksDB CPU benchmark (composite sequence)")
    parser.add_argument("--num", type=int, default=4000000,
                        help="Number of key-value pairs to use in benchmark (default: 5000000)")
    parser.add_argument("--threads", type=int, default=1,
                        help="Number of concurrent threads (default: 1)")
    parser.add_argument("--warmup", type=int, default=1,
                        help="Number of warmup runs")
    parser.add_argument("--iters", type=int, default=1,
                        help="Number of benchmark iterations")
    args = parser.parse_args()

    warmup_cmd = (
        f"./bin/rocksdb_install/db_bench "
        f"--num=100000 "
        f"--threads={args.threads} "
        f"--benchmarks={CPU_BENCHMARK_SEQ} "
        f"--compression_type=snappy "
        f"--db={DB_PATH} "
    )

    cmd = (
        f"./bin/rocksdb_install/db_bench "
        f"--num={args.num} "
        f"--threads={args.threads} "
        f"--benchmarks={CPU_BENCHMARK_SEQ} "
        f"--compression_type=snappy "
        f"--db={DB_PATH} "
    )

    print(f"[INFO] Running RocksDB CPU benchmark sequence:")
    print(f"       {CPU_BENCHMARK_SEQ}")
    print(f"[INFO] num={args.num}, threads={args.threads}, warmup={args.warmup}, iters={args.iters}")

    try:
        # Warmup runs
        for i in range(args.warmup):
            _ = run_command(warmup_cmd)
        print(f"[INFO] Warmup runs completed.")

        print(f"[INFO] Starting measured benchmark runs...")
        times = []
        for i in range(args.iters):
            elapsed = run_command(cmd)
            times.append(elapsed)

        sum_time = sum(times)
        print(f"[RESULT] Total elapsed time: {sum_time:.4f} s")

    except KeyboardInterrupt:
        print("\n[INTERRUPT] Benchmark interrupted by user (Ctrl+C). Cleaning up...")
        sys.exit(130)  # 128 + SIGINT

    except Exception as e:
        print(f"[FATAL] Unexpected error: {e}")
        sys.exit(1)

    finally:
        clean_rocksdb_data()


if __name__ == "__main__":
    main()
