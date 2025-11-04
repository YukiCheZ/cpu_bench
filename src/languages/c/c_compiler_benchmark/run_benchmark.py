#!/usr/bin/env python3
import os
import argparse
import subprocess
import time
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

parser = argparse.ArgumentParser()
parser.add_argument("--compiler", default="gcc", choices=["gcc", "clang"])
parser.add_argument("--opt", default="-O3", choices=["-O0", "-O1", "-O2", "-O3", "-Ofast"])
parser.add_argument("--src_dir", default="./data/src")
parser.add_argument("--threads", type=int, default=1)
parser.add_argument("--iters", type=int, default=1)
args = parser.parse_args()

# Collect all .c source files
src_files = [
    os.path.join(args.src_dir, f)
    for f in os.listdir(args.src_dir)
    if f.endswith(".c")
]

def compile_copy(copy_id, iters, warmup=1):
    """Each thread independently performs full compilation to a temp binary."""
    with tempfile.NamedTemporaryFile(suffix=".out", delete=False) as tmp_bin:
        bin_file = tmp_bin.name
    start = time.time()
    try:
        for _ in range(warmup):
            cmd = [args.compiler, args.opt, "-pthread"] + src_files + ["-o", bin_file, "-lm"]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(iters):
            cmd = [args.compiler, args.opt, "-pthread"] + src_files + ["-o", bin_file, "-lm"]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        if os.path.exists(bin_file):
            os.remove(bin_file)
    end = time.time()
    return end - start

print(f"[INFO] Compiler: {args.compiler} {args.opt}")
print(f"[INFO] Threads: {args.threads}, Iters: {args.iters}, Sources: {len(src_files)}")

print("[INFO] Starting benchmark ...")
try:
    start = time.time()
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = {executor.submit(compile_copy, i, args.iters): i for i in range(args.threads)}
        for f in as_completed(futures):
            t = f.result()
    end = time.time()
    print(f"[RESULT] Total elapsed time: {end - start:.4f}s")
except KeyboardInterrupt:
    print("\n[WARNING] Interrupted by user.")
