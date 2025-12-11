#!/usr/bin/env python3
import argparse
import os
import shlex
import shutil
import subprocess
import sys


def resolve_maven_cmd(root_dir: str):
    mvnw_path = os.path.join(root_dir, "mvnw")
    if os.path.isfile(mvnw_path) and os.access(mvnw_path, os.X_OK):
        return [mvnw_path]
    mvn = shutil.which("mvn")
    if mvn:
        return [mvn]
    print("[ERROR] Neither mvnw nor mvn found. Install Maven or include mvnw.")
    sys.exit(1)


def run_step(cmd, label, env=None):
    print(f"[INFO] {label}: {' '.join(shlex.quote(str(c)) for c in cmd)}")
    ret = subprocess.run(cmd, env=env)
    if ret.returncode != 0:
        print(f"[ERROR] {label} failed")
        sys.exit(ret.returncode)


def main():
    parser = argparse.ArgumentParser(description="Run Smile CPU benchmarks")
    parser.add_argument("--workload", type=str, default="kmeans",
                        choices=["kmeans"],
                        help="Workload to run")
    parser.add_argument("--data", type=str, default=None,
                        help="Path to input data (CSV)")
    parser.add_argument("--threads", type=int, default=1,
                        help="Number of concurrent threads (copies)")
    parser.add_argument("--clusters", type=int, default=1000, help="KMeans clusters")
    parser.add_argument("--heap_gb", type=int, default=8, help="JVM heap GB")
    parser.add_argument("--maven_goal", type=str, default="-q -DskipTests clean compile",
                        help="Maven goal for compilation")
    parser.add_argument("--smile_version", type=str, default="2.6.0",
                        help="Override Smile version (matches pom property smile.version)")
    parser.add_argument("--maven_repo", type=str, default=".m2",
                        help="Local Maven repository directory (relative or absolute)")
    parser.add_argument("--offline", action="store_true",
                        help="Use Maven offline mode (assumes dependencies already cached)")
    parser.add_argument("--skip_compile", action="store_true",
                        help="Skip Maven compilation step")
    args = parser.parse_args()

    root_dir = os.path.dirname(os.path.abspath(__file__))
    maven_repo = os.path.abspath(os.path.join(root_dir, args.maven_repo))
    maven_cmd = resolve_maven_cmd(root_dir)

    # Default data paths per workload if not provided
    default_data = {
        "kmeans": "./data/kmeans.csv",
    }
    data_path = args.data or default_data[args.workload]

    if not os.path.exists(data_path):
        print(f"[ERROR] Data file not found: {data_path}")
        sys.exit(1)

    base_cmd = maven_cmd + [f"-Dmaven.repo.local={maven_repo}"]
    if args.offline:
        base_cmd.append("-o")

    if args.maven_goal and args.maven_goal.strip() and not args.skip_compile:
        compile_cmd = base_cmd + (([f"-Dsmile.version={args.smile_version}"] if args.smile_version else [])) + args.maven_goal.split()
        run_step(compile_cmd, "Compiling Java project with Maven")

    # Force BLAS/OpenMP-based libs to use a single thread per JVM process
    env = os.environ.copy()
    env.setdefault("OPENBLAS_NUM_THREADS", "1")
    env.setdefault("OMP_NUM_THREADS", "1")
    env.setdefault("MKL_NUM_THREADS", "1")
    env.setdefault("BLIS_NUM_THREADS", "1")
    env.setdefault("VECLIB_MAXIMUM_THREADS", "1")

    jvm_args = f"-Xms{args.heap_gb}g -Xmx{args.heap_gb}g -XX:+TieredCompilation -XX:-UseBiasedLocking -Dsmile.threads=1"

    exec_args = [
        f"--workload", args.workload,
        f"--data", data_path,
        f"--threads", str(args.threads),
    ]
    if args.workload == "kmeans":
        exec_args += ["--clusters", str(args.clusters)]

    print("[INFO] Running benchmark:")
    run_cmd = base_cmd + [
        f"-Dsmile.version={args.smile_version}",
        "exec:java",
        f"-Dexec.jvmArgs={jvm_args}",
        "-Dexec.mainClass=benchmark.smile.BenchmarkRunner",
        "-Dexec.args=" + " ".join(exec_args),
    ]
    run_step(run_cmd, "Executing benchmark", env=env)

    print("[INFO] Benchmark finished successfully")


if __name__ == "__main__":
    main()
