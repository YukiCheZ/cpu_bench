#!/usr/bin/env python3
import argparse
import subprocess
import sys
import time
import statistics

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
            sys.exit(result.returncode)

    return end - start

def main():
    parser = argparse.ArgumentParser(description="Run RocksDB CPU benchmark")
    parser.add_argument("--num", type=int, default=1000000,
                        help="Number of key-value pairs to use in benchmark (default: 1000000)")
    parser.add_argument("--threads", type=int, default=1,
                        help="Number of concurrent threads (default: 1)")
    parser.add_argument("--benchmarks", type=str, default="fillseq,readrandom",
                        help="Comma-separated list of benchmarks (default: fillseq,readrandom)")
    parser.add_argument("--compression", type=str, default="snappy",
                        help="Compression type (none, snappy, zlib, bzip2, lz4, zstd)")
    parser.add_argument("--warmup", type=int, default=1,
                        help="Number of warmup runs (default: 1)")
    parser.add_argument("--iters", type=int, default=3,
                        help="Number of benchmark iterations (default: 3)")
    args = parser.parse_args()

    cmd = (
        f"./bin/db_bench "
        f"--num={args.num} "
        f"--threads={args.threads} "
        f"--benchmarks={args.benchmarks} "
        f"--compression_type={args.compression} "
        f"--db=/tmp/rocksdb_bench "
        f"--disable_auto_compactions=true "
    )

    print(f"[INFO] Running benchmark: num={args.num}, threads={args.threads}, "
          f"warmup={args.warmup}, iters={args.iters}")

    # Warmup runs
    for i in range(args.warmup):
        _ = run_command(cmd)
        print(f"[WARMUP] Iteration {i+1}/{args.warmup} done")

    # Measured runs
    times = []
    for i in range(args.iters):
        elapsed = run_command(cmd)
        times.append(elapsed)
        print(f"[ITER {i+1}] {elapsed:.3f} sec")

    avg_time = statistics.mean(times)
    std_time = statistics.pstdev(times) if len(times) > 1 else 0.0
    print(f"[RESULT] Avg time = {avg_time:.3f} sec, StdDev = {std_time:.3f} sec over {args.iters} runs")

if __name__ == "__main__":
    main()
