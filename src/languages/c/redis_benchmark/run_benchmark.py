#!/usr/bin/env python3
import subprocess
import time
import argparse

def start_redis():
    """Start Redis server with persistence disabled"""
    proc = subprocess.Popen(
        ["redis-server", "--save", "", "--appendonly", "no"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(1)  # wait for Redis to start
    return proc

def stop_redis(proc):
    """Stop Redis server using redis-cli shutdown nosave"""
    try:
        subprocess.run(
            ["redis-cli", "shutdown", "nosave"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
    except subprocess.CalledProcessError:
        # fallback in case redis-cli fails
        proc.terminate()
        proc.wait()

def run_benchmark(clients, threads, requests, datasize, pipeline, iterations):
    cmd_base = [
        "redis-benchmark",
        "-c", str(clients),
        "-n", str(requests),
        "-d", str(datasize),
        "-P", str(pipeline),
        "--threads", str(threads),
        "-q"
    ]

    # ---------- warmup ----------
    print(f"[INFO] Starting warmup (with fresh Redis).")
    redis_proc = start_redis()
    subprocess.run(cmd_base, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    stop_redis(redis_proc)
    print("[INFO] Warmup done.\n")

    # ---------- timing ----------
    times = []
    for i in range(iterations):
        redis_proc = start_redis()
        start = time.time()
        subprocess.run(cmd_base, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        end = time.time()
        stop_redis(redis_proc)
        duration = end - start
        times.append(duration)

    print("[INFO] Benchmark complete.")
    print(f"[RESULT] Total elapsed times: {sum(times):.4f} s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Redis CPU benchmark wrapper")
    parser.add_argument("--clients", type=int, default=50, help="Number of concurrent clients")
    parser.add_argument("--threads", type=int, default=1, help="Number of benchmark threads")
    parser.add_argument("--requests", type=int, default=100000, help="Total number of requests per iteration")
    parser.add_argument("--datasize", type=int, default=3, help="Size of each value in bytes")
    parser.add_argument("--pipeline", type=int, default=1, help="Number of requests to pipeline")
    parser.add_argument("--iterations", type=int, default=1, help="Number of iterations to run benchmark")
    args = parser.parse_args()

    run_benchmark(
        clients=args.clients,
        threads=args.threads,
        requests=args.requests,
        datasize=args.datasize,
        pipeline=args.pipeline,
        iterations=args.iterations
    )
