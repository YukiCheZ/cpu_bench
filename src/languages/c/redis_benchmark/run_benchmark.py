#!/usr/bin/env python3
import subprocess
import time
import argparse
import signal
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

REDIS_PATH = "bin/redis_install"

# Global process registry (for safe shutdown)
active_procs = []

def start_redis(port):
    """Start a Redis server instance on the given port"""
    proc = subprocess.Popen(
        [f"{REDIS_PATH}/redis-server", "--port", str(port), "--save", "", "--appendonly", "no"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(0.8)
    active_procs.append((port, proc))
    return proc

def stop_redis(port, proc):
    """Stop Redis server via redis-cli"""
    try:
        subprocess.run(
            [f"{REDIS_PATH}/redis-cli", "-p", str(port), "shutdown", "nosave"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
    except subprocess.CalledProcessError:
        proc.terminate()
        proc.wait()

def cleanup_all():
    """Ensure all Redis processes are stopped"""
    for port, proc in active_procs:
        try:
            stop_redis(port, proc)
        except Exception:
            proc.terminate()
    print("\n[INFO] Cleaned up all Redis instances.")

def handle_interrupt(signum, frame):
    """Handle Ctrl+C and terminate cleanly"""
    print("\n[WARN] Interrupt received. Cleaning up Redis servers...")
    cleanup_all()
    sys.exit(1)

def run_single_benchmark(port, clients, requests, datasize, pipeline):
    """Run redis-benchmark for one Redis instance"""
    cmd = [
        f"{REDIS_PATH}/redis-benchmark",
        "-h", "127.0.0.1",
        "--seed", "42",
        "-p", str(port),
        "-c", str(clients),
        "-n", str(requests),
        "-d", str(datasize),
        "-P", str(pipeline),
        "-q"
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def run_multi_instance(num_instances, clients, requests, datasize, pipeline):
    base_port = 6379
    ports = []

    try:
        # start instances
        for i in range(num_instances):
            port = base_port + i
            start_redis(port)
            ports.append(port)
        print(f"[INFO] Used ports: {ports}")
        print(f"[INFO] Started {num_instances} Redis instances ({2*num_instances} threads).")
        print(f"[INFO] Number of requests per instance: {requests}")
        print(f"[INFO] Number of clients per instance: {clients}")
        print(f"[INFO] Data size per request: {datasize} bytes")
        print(f"[INFO] Pipeline length: {pipeline}")

        # run benchmarks in parallel
        start = time.time()
        with ThreadPoolExecutor(max_workers=num_instances) as executor:
            futures = {
                executor.submit(run_single_benchmark, ports[i], clients, requests, datasize, pipeline): ports[i]
                for i in range(num_instances)
            }
            for future in as_completed(futures):
                future.result()  # ensure any exceptions are raised
        total_duration = time.time() - start

        print(f"[RESULT] Total elapsed time: {total_duration:.4f} s")
    finally:
        cleanup_all()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Redis multi-instance CPU benchmark")
    parser.add_argument("--threads", type=int, default=2, help="Total logical CPU threads to use (each 2 threads -> 1 Redis instance)")
    parser.add_argument("--clients", type=int, default=100)
    parser.add_argument("--requests", type=int, default=4000000)
    parser.add_argument("--datasize", type=int, default=16)
    parser.add_argument("--pipeline", type=int, default=1)
    args = parser.parse_args()

    # Convert threads to instances (2 threads per instance)
    num_instances = max(1, args.threads // 2)

    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, handle_interrupt)
    signal.signal(signal.SIGTERM, handle_interrupt)

    run_multi_instance(
        num_instances=num_instances,
        clients=args.clients,
        requests=args.requests,
        datasize=args.datasize,
        pipeline=args.pipeline
    )
