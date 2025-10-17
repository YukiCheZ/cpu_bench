#!/usr/bin/env python3
import os
import sys
import argparse
import time
from multiprocessing import Pool

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

from benchmarks.data_manager import DataManager
from benchmarks.workloads import NumpyWorkloads

def run_warmup(args):
    workload, data, warmup = args
    func = getattr(NumpyWorkloads, workload)
    func(data, iterations=warmup)
    return None

def run_instance(args):
    workload, data, iters = args
    func = getattr(NumpyWorkloads, workload)
    return func(data, iterations=iters)

def main():
    parser = argparse.ArgumentParser(description="NumPy CPU Benchmark")
    parser.add_argument("--dataset", type=str, default="matrix",
                        choices=["matrix", "svd", "fft"], help="Dataset type")

    temp_args, _ = parser.parse_known_args()

    default_sizes = {
        "matrix": 4096,
        "svd": 2048,
        "fft": 1024 * 1024 * 8
    }
    default_iters = {
        "matrix": 300,
        "svd": 100,
        "fft": 1000
    }

    parser.add_argument("--size", type=int, default=default_sizes.get(temp_args.dataset, 2048))
    parser.add_argument("--iters", type=int, default=default_iters.get(temp_args.dataset, 10))
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--warmup", type=int, default=3)

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

    if args.warmup > 0:
        print(f"[INFO] Warmup phase: {args.warmup} iterations per thread ...")
        with Pool(args.threads) as p:
            p.map(
                run_warmup,
                [(workload, dataset, args.warmup)] * args.threads
            )

    start_time = time.perf_counter()
    with Pool(args.threads) as p:
        results = p.map(
            run_instance,
            [(workload, dataset, args.iters)] * args.threads
        )
    wall_time = time.perf_counter() - start_time

    print(f"[RESULT] Total elapsed time: {wall_time:.4f} s")

if __name__ == "__main__":
    main()
