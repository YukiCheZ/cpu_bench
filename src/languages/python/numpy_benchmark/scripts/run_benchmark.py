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
    workload, data, iters, warmup = args
    func = getattr(NumpyWorkloads, workload)
    return func(data, iters, warmup)

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
        "matrix": 4096,
        "svd": 4096,
        "fft": 1024*1024*16
    }

    default_iters = {
        "matrix": 1000,
        "svd": 100,
        "fft": 1000
    }

    size_default = default_sizes.get(temp_args.dataset, 2048)
    iter_default = default_iters.get(temp_args.dataset, 10)

    parser.add_argument("--size", type=int, default=size_default, help="Dataset size")
    parser.add_argument("--iters", type=int, default=iter_default, help="iters per copy")
    parser.add_argument("--threads", type=int, default=1, help="Number of parallel threads")
    parser.add_argument("--warmup", type=int, default=3, help="Warmup iters per copy")

    args = parser.parse_args()

    print(f"[INFO] dataset={args.dataset}, size={args.size}, iters={args.iters}, "
          f"threads={args.threads}, warmup={args.warmup}")
    print(f"[INFO] OMP_NUM_THREADS={os.environ['OMP_NUM_THREADS']}, "
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

    print(f"[INFO] Running {args.threads} threads of {workload} with size {args.size} x {args.size}")

    with Pool(args.threads) as p:
        results = p.map(
            run_instance,
            [(workload, dataset, args.iters, args.warmup)] * args.threads
        )

    total_time = sum(r[0] for r in results)

    print(f"[RESULT] Total elapsed time: {total_time:.4f} s")



if __name__ == "__main__":
    main()
