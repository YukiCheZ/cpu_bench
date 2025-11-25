#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os


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
    args = parser.parse_args()

    # Default data paths per workload if not provided
    default_data = {
        "kmeans": "./data/kmeans.csv",
    }
    data_path = args.data or default_data[args.workload]

    if args.maven_goal and args.maven_goal.strip():
        print(f"[INFO] Compiling Java project with Maven: mvn -Dmaven.repo.local=./.m2 {('-Dsmile.version='+args.smile_version+' ') if args.smile_version else ''}{args.maven_goal}")
        compile_cmd = ["mvn", "-Dmaven.repo.local=./.m2"] + (([f"-Dsmile.version={args.smile_version}"] if args.smile_version else [])) + args.maven_goal.split()
        ret = subprocess.run(compile_cmd)
        if ret.returncode != 0:
            print("[ERROR] Maven compilation failed")
            sys.exit(1)

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
    run_cmd = [
        "mvn", "-Dmaven.repo.local=./.m2", "exec:java",
        "-Dexec.mainClass=benchmark.smile.BenchmarkRunner",
        f"-Dexec.jvmArgs={jvm_args}",
        "-Dexec.args=" + " ".join(exec_args),
    ]
    if args.smile_version:
        run_cmd.insert(1, f"-Dsmile.version={args.smile_version}")
    print(" ", " ".join(run_cmd))

    ret = subprocess.run(run_cmd, env=env)
    if ret.returncode != 0:
        print("[ERROR] Benchmark execution failed")
        sys.exit(1)

    print("[INFO] Benchmark finished successfully")


if __name__ == "__main__":
    main()
