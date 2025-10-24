#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
import time
import tempfile
import statistics
from concurrent.futures import ProcessPoolExecutor, as_completed

def check_executable(path):
    if not os.path.exists(path) or not os.access(path, os.X_OK):
        print(f"[ERROR] zstd binary not found or not executable: {path}", file=sys.stderr)
        sys.exit(1)

def run_cmd(cmd):
    """Run a subprocess command silently, return success."""
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0

def compress_once(zstd_bin, input_file, level, tid):
    """Single-process compression task."""
    with tempfile.NamedTemporaryFile(suffix=f"_{tid}.zst", delete=False) as tmp_out:
        out_path = tmp_out.name
    cmd = [zstd_bin, f"-{level}", "-T1", "-q", "-f", "-o", out_path, input_file]
    if run_cmd(cmd):
        return out_path
    else:
        raise RuntimeError(f"[ERROR] Compression failed in worker {tid}")

def decompress_once(zstd_bin, compressed_file, tid):
    """Single-process decompression task."""
    with tempfile.NamedTemporaryFile(suffix=f"_{tid}.bin", delete=False) as tmp_out:
        out_path = tmp_out.name
    cmd = [zstd_bin, "-d", "-T1", "-q", "-f", "-o", out_path, compressed_file]
    if run_cmd(cmd):
        return out_path
    else:
        raise RuntimeError(f"[ERROR] Decompression failed in worker {tid}")

def run_parallel(task_fn, nproc, args_list):
    """Run nproc parallel tasks with ProcessPoolExecutor."""
    with ProcessPoolExecutor(max_workers=nproc) as pool:
        futures = [pool.submit(task_fn, *args, tid=i) for i, args in enumerate(args_list)]
        t0 = time.perf_counter()
        results = [f.result() for f in as_completed(futures)]
        t1 = time.perf_counter()
    return t1 - t0, results

def run_zstd_benchmark(input_file, level, threads, zstd_bin, iters, warmup):
    check_executable(zstd_bin)

    if not os.path.isfile(input_file):
        print(f"[ERROR] Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Running zstd CPU benchmark (multi-process mode)")
    print(f"       processes={threads}, level={level}, iters={iters}, warmup={warmup}")

    compress_times, decompress_times = [], []

    # --- Warmup ---
    if warmup > 0:
        print(f"[INFO] Warmup phase ...")
        for _ in range(warmup):
            t_comp, tmp_compressed = run_parallel(
                compress_once,
                threads,
                [(zstd_bin, input_file, level)] * threads
            )
            _ , tmp_decomp = run_parallel(
                decompress_once,
                threads,
                [(zstd_bin, tmp_compressed[i]) for i in range(threads)]
            )
            for path in tmp_compressed + tmp_decomp:
                if os.path.exists(path):
                    os.remove(path)

    # --- Benchmark phase ---
    print(f"[INFO] Benchmark phase ...")
    for i in range(iters):
        t_comp, tmp_compressed = run_parallel(
            compress_once,
            threads,
            [(zstd_bin, input_file, level)] * threads
        )
        compress_times.append(t_comp)

        t_decomp, tmp_decomp = run_parallel(
            decompress_once,
            threads,
            [(zstd_bin, tmp_compressed[i]) for i in range(threads)]
        )
        decompress_times.append(t_decomp)

        for path in tmp_compressed + tmp_decomp:
            if os.path.exists(path):
                os.remove(path)

    # --- Results ---
    print(f"[INFO] Benchmark complete")
    print(f"[INFO] Level: {level}")
    total_compressed = sum(compress_times)
    total_decompressed = sum(decompress_times)
    total_time = sum(compress_times) + sum(decompress_times)
    print(f"[INFO] Compression time: {total_compressed:.4f} s")
    print(f"[INFO] Decompression time: {total_decompressed:.4f} s")
    print(f"[RESULT] Total elapsed time: {total_time:.4f} s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zstd CPU Benchmark (multi-process parallel mode)")
    parser.add_argument("--input", type=str, default="./data/zstd_input.bin", help="Input file for benchmark")
    parser.add_argument("--level", type=int, default=19, help="Compression level (1-19)")
    parser.add_argument("--threads", type=int, default=1, help="Number of parallel zstd processes")
    parser.add_argument("--iters", type=int, default=120, help="Number of timed iterations")
    parser.add_argument("--warmup", type=int, default=1, help="Number of warmup iterations before timing")
    parser.add_argument("--zstd-bin", type=str, default="./bin/zstd", help="Path to zstd executable")

    args = parser.parse_args()
    run_zstd_benchmark(args.input, args.level, args.threads, args.zstd_bin,
                       args.iters, args.warmup)
