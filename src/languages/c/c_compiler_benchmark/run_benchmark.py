#!/usr/bin/env python3
import os
import argparse
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("--compiler", default="gcc", choices=["gcc", "clang"])
parser.add_argument("--opt", default="-O3", choices=["-O0", "-O1", "-O2", "-O3", "-Ofast"])
parser.add_argument("--src_dir", default="./data/src")
parser.add_argument("--threads", type=int, default=1)
args = parser.parse_args()

# Gather all .c files
src_files = [
    os.path.join(args.src_dir, f)
    for f in os.listdir(args.src_dir)
    if f.endswith(".c")
]

def compile_copy(copy_id):
    """Each thread runs a full compilation independently into a temp file"""
    with tempfile.NamedTemporaryFile(suffix=".out", delete=False) as tmp_bin:
        bin_file = tmp_bin.name
    cmd = [args.compiler, args.opt, "-pthread"] + src_files + ["-o", bin_file, "-lm"]
    subprocess.check_call(cmd)
    os.remove(bin_file)  # discard binary immediately

start = time.time()

# Run multiple independent compilations in parallel
with ThreadPoolExecutor(max_workers=args.threads) as executor:
    futures = [executor.submit(compile_copy, i) for i in range(args.threads)]
    # Wait for all to complete
    for f in futures:
        f.result()

end = time.time()
print(f"[RESULT] Compilation time: {end-start:.6f} sec")
