#!/usr/bin/env python3
import os
import sys

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import argparse
from multiprocessing import Pool
from benchmarks.data_manager import DataManager
from benchmarks.workloads import NumpyWorkloads

def run_instance(args):
    workload, data, iterations, warmup = args
    func = getattr(NumpyWorkloads, workload)
    return func(data, iterations, warmup)

def main():
    parser = argparse.ArgumentParser(description="NumPy CPU Benchmark")
    parser.add_argument(
        "--dataset",
        type=str,
        default="matrix",
        choices=["matrix", "svd", "fft"],
        help="Dataset type"
    )

    temp_args, _ = parser.parse_known_args()

    default_sizes = {
        "matrix": 8192,
        "svd": 4096,
        "fft": 1024*1024*128
    }
    size_default = default_sizes.get(temp_args.dataset, 2048)

    parser.add_argument("--size", type=int, default=size_default, help="Dataset size")
    parser.add_argument("--iterations", type=int, default=5, help="Iterations per copy")
    parser.add_argument("--copies", type=int, default=1, help="Number of parallel copies")
    parser.add_argument("--warmup", type=int, default=3, help="Warmup iterations per copy")

    args = parser.parse_args()

    print(f"[Config] dataset={args.dataset}, size={args.size}, iterations={args.iterations}, "
          f"copies={args.copies}, warmup={args.warmup}")
    print(f"[Config] OMP_NUM_THREADS={os.environ['OMP_NUM_THREADS']}, "
          f"MKL_NUM_THREADS={os.environ['MKL_NUM_THREADS']}, "
          f"OPENBLAS_NUM_THREADS={os.environ['OPENBLAS_NUM_THREADS']}")

    dm = DataManager()
    workload_map = {
        "matrix": "matmul",
        "svd": "svd",
        "fft": "fft"
    }
    workload = workload_map[args.dataset]
    dataset = dm.generate_dataset(args.size, args.dataset)

    print(f"[Benchmark] Running {args.copies} copies of {workload} with size {args.size} x {args.size}")

    with Pool(args.copies) as p:
        results = p.map(
            run_instance,
            [(workload, dataset, args.iterations, args.warmup)] * args.copies
        )

    total_time = sum(r[0] for r in results)
    avg_time = total_time / args.copies

    print(f"[Result] Average time per copy: {avg_time:.6f} sec")
    print(f"[Result] Total time for all copies: {total_time:.6f} sec")

if __name__ == "__main__":
    main()
