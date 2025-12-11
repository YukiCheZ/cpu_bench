#!/usr/bin/env python3
import argparse
import os
import shlex
import shutil
import subprocess
import sys


def resolve_maven_cmd(root_dir: str):
    """Prefer mvnw in the project, fall back to mvn in PATH."""
    mvnw_path = os.path.join(root_dir, "mvnw")
    if os.path.isfile(mvnw_path) and os.access(mvnw_path, os.X_OK):
        return [mvnw_path]
    mvn = shutil.which("mvn")
    if mvn:
        return [mvn]
    print("[ERROR] Neither mvnw nor mvn found. Install Maven or include mvnw.")
    sys.exit(1)


def run_step(cmd, label):
    print(f"[INFO] {label}: {' '.join(shlex.quote(str(c)) for c in cmd)}")
    ret = subprocess.run(cmd)
    if ret.returncode != 0:
        print(f"[ERROR] {label} failed")
        sys.exit(ret.returncode)


def main():
    parser = argparse.ArgumentParser(description="Setup Smile Java benchmark workspace")
    parser.add_argument("--smile_version", type=str, default="2.6.0", help="Smile version to use")
    parser.add_argument("--maven_goal", type=str, default="-q -DskipTests clean package",
                        help="Maven goal to build and pull dependencies")
    parser.add_argument("--maven_repo", type=str, default=".m2",
                        help="Local Maven repository directory (relative or absolute)")
    parser.add_argument("--offline", action="store_true",
                        help="Use Maven offline mode (assumes dependencies already cached)")
    parser.add_argument("--skip_prefetch", action="store_true",
                        help="Skip dependency:get warm-up fetch")
    parser.add_argument("--skip_prime", action="store_true",
                        help="Skip exec:java warmup run")
    args = parser.parse_args()

    root_dir = os.path.dirname(os.path.abspath(__file__))
    maven_repo = os.path.abspath(os.path.join(root_dir, args.maven_repo))

    maven_cmd = resolve_maven_cmd(root_dir)

    # Check tools
    for tool in ("java", "javac"):
        if shutil.which(tool) is None:
            print(f"[ERROR] Required tool not found in PATH: {tool}")
            sys.exit(1)

    # Show versions
    jv = subprocess.run(["java", "-version"], capture_output=True, text=True)
    cv = subprocess.run(["javac", "-version"], capture_output=True, text=True)
    mv = subprocess.run(maven_cmd + ["-version"], capture_output=True, text=True)
    print(jv.stderr.strip() or jv.stdout.strip())
    print(cv.stdout.strip() or cv.stderr.strip())
    print(mv.stdout.strip() or mv.stderr.strip())

    # Parse major version
    def parse_version(text):
        import re
        m = re.search(r'version "(\d+)', text)
        return int(m.group(1)) if m else None
    major = parse_version(jv.stderr + jv.stdout)
    if major is None or major < 17:
        print(f"[ERROR] Java 17+ required, detected: {major}")
        sys.exit(1)

    base_cmd = maven_cmd + [f"-Dmaven.repo.local={maven_repo}"]
    if args.offline:
        base_cmd.append("-o")

    # Try to prefetch Smile dependency so network is used only here
    if not args.skip_prefetch and not args.offline:
        prefetch_cmd = base_cmd + ["-q", "dependency:get", f"-Dartifact=com.github.haifengl:smile-core:{args.smile_version}"]
        ret = subprocess.run(prefetch_cmd)
        if ret.returncode != 0:
            print("[WARN] Prefetch failed. Maven build will try again during package.")

    # Build project
    build_cmd = base_cmd + [f"-Dsmile.version={args.smile_version}"] + args.maven_goal.split()
    run_step(build_cmd, "Building project")

    # Prime exec-maven-plugin and its dependencies so later runs are offline
    if not args.skip_prime:
        data_gererate_cmd = [
            f"python3",
            f"{os.path.join(root_dir, 'generate_data.py')}",
            "--task", "kmeans",
            "--samples", "10",
            "--features", "5",
        ]
        ret = subprocess.run(data_gererate_cmd)
        if ret.returncode != 0:
            print("[ERROR] Data generation failed")
            sys.exit(ret.returncode)

        print("[INFO] Priming exec:java plugin dependencies (one-time warmup)")
        prime_cmd = base_cmd + [
            f"-Dsmile.version={args.smile_version}",
            "exec:java",
            "-Dexec.mainClass=benchmark.smile.BenchmarkRunner",
            "-Dexec.jvmArgs=-Xms256m -Xmx256m -Dsmile.threads=1",
            "-Dexec.args=--workload kmeans --data ./data/kmeans.csv --threads 1 --clusters 2 --iters 1",
        ]
        ret = subprocess.run(prime_cmd)
        if ret.returncode != 0:
            print("[WARN] exec:java warmup failed (this is usually safe to ignore; dependencies may already be cached)")

    print("[INFO] Setup complete.")


if __name__ == "__main__":
    main()
