#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
import time

def run_zstd_benchmark(input_file, level, threads, zstd_bin, iters, warmup):
    if not zstd_bin:
        zstd_bin = "zstd"  # assume in PATH

    if not os.path.isfile(input_file):
        print(f"[ERROR] Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Running zstd CPU benchmark (threads: {threads}, level: {level}, iters: {iters}, warmup: {warmup})")

    with open(input_file, "rb") as f:
        input_data = f.read()

    for i in range(warmup):
        compress_proc = subprocess.run(
            [zstd_bin, f"-{level}", f"-T{threads}", "-q", "-c"],
            input=input_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        if compress_proc.returncode != 0:
            print(f"[ERROR] Warmup compression failed at iteration {i+1}", file=sys.stderr)
            sys.exit(1)
        decompress_proc = subprocess.run(
            [zstd_bin, "-d", f"-T{threads}", "-q", "-c"],
            input=compress_proc.stdout,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if decompress_proc.returncode != 0:
            print(f"[ERROR] Warmup decompression failed at iteration {i+1}", file=sys.stderr)
            sys.exit(1)

    start_time = time.time()
    for i in range(iters):
        compress_proc = subprocess.run(
            [zstd_bin, f"-{level}", f"-T{threads}", "-q", "-c"],
            input=input_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        if compress_proc.returncode != 0:
            print(f"[ERROR] Compression failed at iteration {i+1}", file=sys.stderr)
            sys.exit(1)
        decompress_proc = subprocess.run(
            [zstd_bin, "-d", f"-T{threads}", "-q", "-c"],
            input=compress_proc.stdout,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if decompress_proc.returncode != 0:
            print(f"[ERROR] Decompression failed at iteration {i+1}", file=sys.stderr)
            sys.exit(1)

    total_time = time.time() - start_time

    print(f"[RESULT] Total elapsed time: {total_time:.4f} s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zstd CPU Benchmark (in-memory, multi-iteration)")
    parser.add_argument("--input", type=str, default="./data/zstd_input.bin", help="Input file for benchmark")
    parser.add_argument("--level", type=int, default=19, help="Compression level (1-19)")
    parser.add_argument("--threads", type=int, default=1, help="Number of threads")
    parser.add_argument("--iters", type=int, default=3, help="Number of timed iterations")
    parser.add_argument("--warmup", type=int, default=1, help="Number of warmup iterations before timing")
    parser.add_argument("--zstd-bin", type=str, default="./bin/zstd", help="Path to zstd executable")

    args = parser.parse_args()
    run_zstd_benchmark(args.input, args.level, args.threads, args.zstd_bin, args.iters, args.warmup)
