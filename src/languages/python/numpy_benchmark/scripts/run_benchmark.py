#!/usr/bin/env python3
import os
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
    parser.add_argument("--size", type=int, default=2048, help="Dataset size")
    parser.add_argument("--dataset", type=str, default="matrix", choices=["matrix", "svd", "fft"], help="Dataset type")
    parser.add_argument("--iterations", type=int, default=5, help="Iterations per copy")
    parser.add_argument("--copies", type=int, default=1, help="Number of parallel copies")
    parser.add_argument("--warmup", type=int, default=3, help="Warmup iterations per copy")
    parser.add_argument("--omp_threads", type=int, default=1, help="OMP_NUM_THREADS setting for BLAS")

    args = parser.parse_args()

    # 限制 BLAS 线程数（避免多进程时超额占用 CPU 核心）
    os.environ["OMP_NUM_THREADS"] = str(args.omp_threads)
    os.environ["MKL_NUM_THREADS"] = str(args.omp_threads)
    os.environ["OPENBLAS_NUM_THREADS"] = str(args.omp_threads)

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
        results = p.map(run_instance, [(workload, dataset, args.iterations, args.warmup)] * args.copies)

    total_time = sum(r[0] for r in results)
    avg_time = total_time / args.copies

    print(f"[Result] Average time per copy: {avg_time:.6f} sec")
    print(f"[Result] Total time for all copies: {total_time:.6f} sec")

if __name__ == "__main__":
    main()
