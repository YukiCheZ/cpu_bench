#!/usr/bin/env python3
import argparse
import subprocess
import time
import os
import sys
import multiprocessing

def run_command(cmd, env=None, measure_time=True):
    start = time.time() if measure_time else None
    result = subprocess.run(cmd, shell=True, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(f"[ERROR] Command failed: {cmd}")
        print(result.stderr.decode())
        sys.exit(1)
    if measure_time:
        end = time.time()
        return end - start
    return None

def main():
    parser = argparse.ArgumentParser(description="Compile generated Go code benchmark")
    parser.add_argument("--data-dir", type=str, default="data",
                        help="Directory containing previously generated Go code")
    parser.add_argument("--iterations", type=int, default=5,
                        help="Number of times to repeat the benchmark")
    parser.add_argument("--threads", type=int, default=1,
                        help="Number of parallel Go build threads")
    parser.add_argument("--no-clean", action="store_true",
                        help="Do not clean Go build cache before each run")
    args = parser.parse_args()

    data_dir = os.path.abspath(args.data_dir)
    if not os.path.exists(data_dir):
        print(f"[ERROR] Data directory not found: {data_dir}")
        sys.exit(1)

    os.chdir(data_dir)
    env = os.environ.copy()
    if( args.threads < 1):
        args.threads = multiprocessing.cpu_count()
        if args.threads < 1:
            args.threads = 1
    env["GOMAXPROCS"] = str(args.threads)
    if "GOCACHE" not in env:
        env["GOCACHE"] = os.path.join("/tmp", "gocache_generated")
        print(f"[INFO] GOCACHE not set, defaulting to {env['GOCACHE']}")

    build_cmd = "go build -a -o /dev/null ./..."

    print(f"[INFO] Benchmark: iterations={args.iterations}, threads={args.threads}, no_clean={args.no_clean}")
    print(f"[INFO] Working directory: {data_dir}")
    print(f"[INFO] Using GOCACHE: {env['GOCACHE']}\n")

    times = []
    for i in range(1, args.iterations + 1):

        if not args.no_clean:
            env_clean = env.copy()
            run_command("go clean -cache -testcache -modcache", env=env_clean, measure_time=False)

        elapsed = run_command(build_cmd, env=env, measure_time=True)
        times.append(elapsed)

    print(f"[RESULT] Total elapsed time: {sum(times):.4f} s")

if __name__ == "__main__":
    main()
