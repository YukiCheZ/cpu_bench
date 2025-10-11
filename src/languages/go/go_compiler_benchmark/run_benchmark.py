#!/usr/bin/env python3
import argparse
import subprocess
import time
import os
import sys

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
    parser = argparse.ArgumentParser(description="Go compiler benchmark runner")
    parser.add_argument("--go-root", type=str, default="data/go",
                        help="Path to Go root directory (if not provided, will attempt to download Go source)")
    parser.add_argument("--scale", choices=["small", "std", "all"], default="all",
                        help="Benchmark scale: small=compile cmd/compile, std=compile standard lib, all=build full Go toolchain")
    parser.add_argument("--iterations", type=int, default=1,
                        help="Number of times to repeat the benchmark")
    parser.add_argument("--threads", type=int, default=1,
                        help="Number of parallel build threads")
    parser.add_argument("--no-clean", action="store_true",
                        help="Do not clean build cache before each run (not counted in timing)")
    args = parser.parse_args()

    project_root = os.path.dirname(__file__)

    go_src_dir = os.path.join(project_root, args.go_root, "src")

    if not os.path.exists(go_src_dir):
        print(f"[WARN] Go source directory not found: {go_src_dir}")
        download_script = os.path.join(project_root, "download_go.sh")
        if os.path.exists(download_script):
            print(f"[INFO] Running {download_script} to fetch Go source...")
            ret = subprocess.run(["bash", download_script])
            if ret.returncode != 0:
                print("[ERROR] Failed to download Go source via download_go.sh")
                sys.exit(1)
        else:
            print("[ERROR] download_go.sh not found, please provide Go source manually.")
            sys.exit(1)

    if not os.path.exists(go_src_dir):
        print(f"[ERROR] Go source directory still not found after attempting download: {go_src_dir}")
        sys.exit(1)

    os.chdir(go_src_dir)

    env = os.environ.copy()
    if "GOCACHE" not in env:
        env["GOCACHE"] = "/tmp/gocache"
        print(f"[INFO] GOCACHE not set, defaulting to {env['GOCACHE']}")

    original_gomaxprocs = env.get("GOMAXPROCS")
    env["GOMAXPROCS"] = str(args.threads)

    if args.scale == "small":
        build_cmd = "go build -o /dev/null cmd/compile"
    elif args.scale == "std":
        build_cmd = "go build -o /dev/null std"
    elif args.scale == "all":
        tmp_bin = "/tmp/go-bin"
        os.makedirs(tmp_bin, exist_ok=True)
        env["GOBIN"] = tmp_bin
        print(f"[INFO] Redirecting GOBIN to {tmp_bin} for all mode to avoid modifying ./go")
        build_cmd = "./make.bash"
    else:
        print("[ERROR] Unknown scale")
        sys.exit(1)

    print(f">>> Benchmark: scale={args.scale}, iterations={args.iterations}, threads={args.threads}, no_clean={args.no_clean}")
    print(f">>> Working directory: {go_src_dir}")
    print(f">>> Using GOCACHE: {env['GOCACHE']}\n")

    times = []
    for i in range(1, args.iterations + 1):
        print(f"[Run {i}] Preparing...")

        if not args.no_clean:
            print(f"[Run {i}] Cleaning build cache...")
            env_clean = env.copy()
            env_clean.pop("GOFLAGS", None)
            run_command("go clean -cache -testcache -modcache", env=env_clean, measure_time=False)

        print(f"[Run {i}] Building with command: {build_cmd}")
        elapsed = run_command(build_cmd, env=env, measure_time=True)
        print(f"[Run {i}] Elapsed: {elapsed:.2f} sec\n")
        times.append(elapsed)

    # 恢复 GOMAXPROCS
    if original_gomaxprocs is None:
        env.pop("GOMAXPROCS", None)
    else:
        env["GOMAXPROCS"] = original_gomaxprocs

    avg = sum(times) / len(times)
    print("========== Benchmark Summary ==========")
    for i, t in enumerate(times, 1):
        print(f"Run {i}: {t:.2f} sec")
    print(f"Average: {avg:.2f} sec")

if __name__ == "__main__":
    main()
