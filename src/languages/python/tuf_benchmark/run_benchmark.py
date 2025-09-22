#!/usr/bin/env python3
import argparse
import time
import hashlib
import json
from multiprocessing import Pool
from tuf.api.metadata import Metadata
import os

def expand_target(seed_data, size):
    repeats = size // len(seed_data) + 1
    return (seed_data * repeats)[:size]

def worker(args):
    repo_path, iterations, warmup_count = args

    metadata_files = []
    target_files = []

    for fname in os.listdir(repo_path):
        fpath = os.path.join(repo_path, fname)
        if fname.startswith("meta") and fname.endswith(".json"):
            with open(fpath, "rb") as f:
                metadata_files.append({"path": fname, "data": f.read()})
        elif fname.startswith("file") and fname.endswith(".bin"):
            base = fname.replace(".bin", "")
            with open(fpath, "rb") as f:
                seed = f.read()
            with open(os.path.join(repo_path, f"{base}.meta.json"), "r") as f:
                meta = json.load(f)
            expanded = expand_target(seed, meta["target_size"])
            target_files.append({"path": fname, "data": expanded})

    # Warmup
    for _ in range(warmup_count):
        for meta in metadata_files:
            Metadata.from_bytes(meta["data"])
        for target in target_files:
            hashlib.sha256(target["data"]).hexdigest()

    # Benchmark iterations
    start_time = time.perf_counter()
    for _ in range(iterations):
        for meta in metadata_files:
            Metadata.from_bytes(meta["data"])
        for target in target_files:
            hashlib.sha256(target["data"]).hexdigest()
    elapsed = time.perf_counter() - start_time

    total_bytes = sum(len(t["data"]) for t in target_files + metadata_files)
    total_ops = len(metadata_files) + len(target_files)
    return {"elapsed": elapsed, "bytes": total_bytes, "ops": total_ops}


def main():
    parser = argparse.ArgumentParser(description="TUF CPU Benchmark (load from data files)")
    parser.add_argument("--copies", type=int, default=1, help="Number of parallel worker processes")
    parser.add_argument("--iterations", type=int, default=1000, help="Iterations per worker")
    parser.add_argument("--warmup", type=int, default=3, help="Warmup iterations per worker")
    parser.add_argument("--repo", type=str, default="./data", help="Path to data directory")
    args = parser.parse_args()

    print(f"[INFO] Running {args.copies} copies, {args.iterations} iterations, warmup {args.warmup}, data-dir {args.repo}")

    worker_args = [(args.repo, args.iterations, args.warmup) for _ in range(args.copies)]

    start = time.perf_counter()
    with Pool(processes=args.copies) as pool:
        results = pool.map(worker, worker_args)
    total_wall_time = time.perf_counter() - start

    total_elapsed = sum(r["elapsed"] for r in results)
    total_bytes = sum(r["bytes"] for r in results) * args.iterations
    total_ops = sum(r["ops"] for r in results) * args.iterations

    avg_time_per_copy = total_elapsed / len(results)

    print(f"[Result] Avg time per copy: {avg_time_per_copy:.6f} sec")
    print(f"[Result] Wall-clock time: {total_wall_time:.6f} sec")

if __name__ == "__main__":
    main()
