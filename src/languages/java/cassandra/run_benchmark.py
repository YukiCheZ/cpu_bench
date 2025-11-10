#!/usr/bin/env python3
import subprocess
import os
import shutil
import sys
import re
import argparse
import multiprocessing


CASSANDRA_VERSION = "4.0.18"
CASSANDRA_DIR = f"./bin/apache-cassandra-{CASSANDRA_VERSION}/"
CASSANDRA_BIN = os.path.join(CASSANDRA_DIR, "bin/cassandra")
NODETOOL_BIN = os.path.join(CASSANDRA_DIR, "bin/nodetool")
STRESS_BIN = os.path.join(CASSANDRA_DIR, "tools/bin/cassandra-stress")
LOG_DIR = os.path.join(CASSANDRA_DIR, "logs")
DATA_DIR = os.path.join(CASSANDRA_DIR, "data")


def run_cassandra_stress(cmd, n_ops):
    """Run cassandra-stress and parse Op rate to compute actual elapsed time"""
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        print(f"[FATAL] Command failed: {cmd}")
        print(proc.stderr.decode())
        raise RuntimeError("Stress test failed")

    output = proc.stdout.decode()
    match = re.search(r"Op rate\s*:\s*([\d,]+)\s+op/s", output)
    if not match:
        raise RuntimeError("Failed to parse Op rate")
    op_rate = int(match.group(1).replace(",", ""))
    elapsed = n_ops / op_rate
    return elapsed


def run_command(cmd, check=True):
    """Run a shell command, raise exception if it fails"""
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        print(f"[FATAL] Command failed: {cmd}")
        print(proc.stderr.decode())
        if check:
            raise RuntimeError(f"Command failed: {cmd}")


def start_cassandra():
    print("[INFO] Starting Cassandra...")
    run_command(f"{CASSANDRA_BIN} -R")
    print("[INFO] Cassandra started")


def stop_cassandra():
    print("[INFO] Stopping Cassandra...")
    try:
        run_command(f"{NODETOOL_BIN} stopdaemon")
    except RuntimeError:
        print("[WARN] nodetool stopdaemon failed, Cassandra might have already stopped.")
    print("[INFO] Cassandra stopped")


def clean_data_logs():
    print("[INFO] Cleaning data and logs...")
    if os.path.exists(DATA_DIR):
        shutil.rmtree(DATA_DIR)
    if os.path.exists(LOG_DIR):
        shutil.rmtree(LOG_DIR)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    print("[INFO] Data and log cleanup completed")


def main():
    parser = argparse.ArgumentParser(description="Cassandra CPU Benchmark")
    parser.add_argument("--write-n", type=int, default=2000000, help="Total operations for write test")
    parser.add_argument("--write-threads", type=int, default=128, help="Number of threads for write test")
    parser.add_argument("--read-n", type=int, default=2000000, help="Total operations for read test")
    parser.add_argument("--read-threads", type=int, default=128, help="Number of threads for read test")
    parser.add_argument("--threads", type=int, default=1, help="Limit number of CPU cores to use by client")
    parser.add_argument("--iters", type=int, default=25, help="Number of iterations for read test")
    args = parser.parse_args()

    # Automatically select CPU cores if threads is specified
    if args.threads > 0:
        available_cores = list(range(multiprocessing.cpu_count()))
        selected_cores = ",".join(str(c) for c in available_cores[:args.threads])
        taskset_prefix = f"taskset -c {selected_cores} "
    else:
        taskset_prefix = ""

    try:
        start_cassandra()

        # Run write test (not timed, output ignored)
        print(f"[INFO] Starting write {args.write_n} records, preparing data...")
        write_cmd = f"{STRESS_BIN} write n={args.write_n} -rate threads={args.write_threads}"
        run_cassandra_stress(write_cmd, n_ops=args.write_n)
        print("[INFO] Write completed.")

        # Run read test (timed, multiple iterations)
        total_elapsed = 0.0
        print(f"[INFO] Starting read tests: {args.read_n} records, {args.iters} iterations...")
        for i in range(args.iters):
            read_cmd = f"{taskset_prefix}{STRESS_BIN} read n={args.read_n} -rate threads={args.read_threads}"
            elapsed = run_cassandra_stress(read_cmd, n_ops=args.read_n)
            total_elapsed += elapsed
        print(f"[RESULT] Total elapsed time: {total_elapsed:.4f} s")

    except RuntimeError as e:
        print(f"[ERROR] Cassandra-stress benchmark failed: {e}")
        sys.exit(1)
    finally:
        stop_cassandra()
        clean_data_logs()


if __name__ == "__main__":
    main()
