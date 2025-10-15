#!/usr/bin/env python3
import argparse
import time
from multiprocessing import Pool
from benchmarks.client import RequestsWorkloads
from benchmarks.data_manager import DataManager

def worker(args):
    """Worker process: run benchmark on given file."""
    filepath, iters, warmup_count = args
    bench = RequestsWorkloads(filepath)
    elapsed = bench.run(iters=iters, warmup_count=warmup_count)
    return elapsed

def main():
    parser = argparse.ArgumentParser(description="Requests JSON Parsing CPU Benchmark")
    parser.add_argument("--copies", type=int, default=1, help="Number of parallel worker processes")
    parser.add_argument("--iters", type=int, default=1000, help="iters per worker")
    parser.add_argument("--warmup", type=int, default=3, help="Warmup iters per worker")
    parser.add_argument("--size", type=int, default=1024*1024, help="Dataset size, affects filename")
    parser.add_argument("--force", action="store_true", help="Force regenerate dataset even if it exists")
    
    args = parser.parse_args()

    dm = DataManager()
    filename = f"data/data_{args.size}.json"

    # Generate or load dataset
    if args.force:
        print(f"[DataManager] Force regenerating dataset: {filename}")
        dm.generate_dataset(args.size)
    else:
        try:
            dm.load_dataset(args.size)
            print(f"[DataManager] Loaded existing dataset: {filename}")
        except FileNotFoundError:
            print(f"[DataManager] Dataset not found. Generating: {filename}")
            dm.generate_dataset(args.size)

    # Full memory warm-up
    print(f"[Warmup] Loading entire dataset into memory: {filename}")
    with open(filename, "r") as f:
        _ = f.read()

    print(f"[Benchmark] Running {args.copies} copies, {args.iters} iters each, warmup {args.warmup}, file: {filename}")

    worker_args = [(filename, args.iters, args.warmup) for _ in range(args.copies)]

    start = time.perf_counter()
    with Pool(processes=args.copies) as pool:
        results = pool.map(worker, worker_args)
    total_time = time.perf_counter() - start

    print(f"[RESULT] Total elapsed time: {total_time:.4f} s")
    
if __name__ == "__main__":
    main()
