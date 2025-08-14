#!/usr/bin/env python3
import argparse
import time
import hashlib
import json
from multiprocessing import Pool
from tuf.api.metadata import Metadata

# ---------------------------
# Worker process
# ---------------------------
def worker(args):
    repo_path, iterations, warmup_count, data_size = args

    meta_count = 10
    target_count = 5

    # 固定合法 TUF Root 元数据
    metadata_dict = {
        "signed": {
            "_type": "root",
            "spec_version": "1.0.0",
            "version": 1,
            "expires": "2030-01-01T00:00:00Z",
            "keys": {},
            "roles": {
                "root": {"keyids": [], "threshold": 1},
                "targets": {"keyids": [], "threshold": 1},
                "snapshot": {"keyids": [], "threshold": 1},
                "timestamp": {"keyids": [], "threshold": 1},
            },
            "consistent_snapshot": False
        },
        "signatures": []
    }
    metadata_bytes = json.dumps(metadata_dict).encode("utf-8")

    # 构造 metadata 文件（固定大小合法 JSON）
    metadata_files = [{"path": f"meta{i}", "data": metadata_bytes} for i in range(meta_count)]

    # 构造 target 文件，按用户指定总大小均分
    target_size = max(data_size // target_count, 1)
    target_files = [{"path": f"file{i}", "data": b"x"*target_size} for i in range(target_count)]

    # Warmup
    for _ in range(warmup_count):
        for meta in metadata_files:
            m = Metadata.from_bytes(meta["data"])
        for target in target_files:
            hashlib.sha256(target["data"]).hexdigest()

    # Benchmark iterations
    start_time = time.perf_counter()
    for _ in range(iterations):
        for meta in metadata_files:
            m = Metadata.from_bytes(meta["data"])
        for target in target_files:
            hashlib.sha256(target["data"]).hexdigest()
    elapsed = time.perf_counter() - start_time

    total_bytes = sum(len(t["data"]) for t in target_files + metadata_files)
    total_ops = len(metadata_files) + len(target_files)
    return {"elapsed": elapsed, "bytes": total_bytes, "ops": total_ops}


# ---------------------------
# Main
# ---------------------------
def main():
    parser = argparse.ArgumentParser(description="TUF CPU Benchmark")
    parser.add_argument("--copies", type=int, default=1, help="Number of parallel worker processes")
    parser.add_argument("--iterations", type=int, default=10, help="Iterations per worker")
    parser.add_argument("--warmup", type=int, default=2, help="Warmup iterations per worker")
    parser.add_argument("--data-size", type=int, default=10*1024*1024,
                        help="Total target data size per worker (bytes)")
    parser.add_argument("--repo", type=str, default="repo", help="Path to test repository (not used in memory mode)")
    args = parser.parse_args()

    print(f"[Benchmark] Running {args.copies} copies, {args.iterations} iterations, warmup {args.warmup}, data-size {args.data_size} bytes per worker")

    worker_args = [(args.repo, args.iterations, args.warmup, args.data_size) for _ in range(args.copies)]

    start = time.perf_counter()
    with Pool(processes=args.copies) as pool:
        results = pool.map(worker, worker_args)
    total_wall_time = time.perf_counter() - start

    total_elapsed = sum(r["elapsed"] for r in results)
    total_bytes = sum(r["bytes"] for r in results) * args.iterations
    total_ops = sum(r["ops"] for r in results) * args.iterations

    avg_time_per_copy = total_elapsed / len(results)
    throughput_mb_s = total_bytes / total_elapsed / (1024*1024)
    ops_per_sec = total_ops / total_elapsed

    print(f"[Result] Avg time per copy: {avg_time_per_copy:.6f} sec")
    print(f"[Result] Wall-clock time: {total_wall_time:.6f} sec")
    print(f"[Result] Total operations: {total_ops}")
    print(f"[Result] Ops/sec: {ops_per_sec:.2f}")
    print(f"[Result] Throughput: {throughput_mb_s:.2f} MB/s")


if __name__ == "__main__":
    main()
