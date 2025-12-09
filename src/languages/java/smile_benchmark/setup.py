#!/usr/bin/env python3
import argparse
import subprocess
import sys
import shutil
import os 


def main():
    parser = argparse.ArgumentParser(description="Setup Smile Java benchmark workspace")
    parser.add_argument("--smile_version", type=str, default="2.6.0", help="Smile version to use")
    parser.add_argument("--maven_goal", type=str, default="-q -DskipTests clean package",
                        help="Maven goal to build and pull dependencies")
    args = parser.parse_args()

    MAVEN_OPTS_FIX = "--add-opens java.base/java.lang=ALL-UNNAMED -DsocksProxyHost=127.0.0.1 -DsocksProxyPort=7890"
    
    env_vars = os.environ.copy()
    current_maven_opts = env_vars.get("MAVEN_OPTS", "")
    if MAVEN_OPTS_FIX not in current_maven_opts:
        env_vars["MAVEN_OPTS"] = f"{current_maven_opts} {MAVEN_OPTS_FIX}".strip()
    # -------------------------------------------------------------

    # Check tools
    for tool in ("java", "javac", "mvn"):
        if shutil.which(tool) is None:
            print(f"[ERROR] Required tool not found in PATH: {tool}")
            sys.exit(1)

    # Show versions
    jv = subprocess.run(["java", "-version"], capture_output=True, text=True)
    cv = subprocess.run(["javac", "-version"], capture_output=True, text=True)
    print(jv.stderr.strip() or jv.stdout.strip())
    print(cv.stdout.strip() or cv.stderr.strip())

    # Parse major version
    def parse_version(text):
        import re
        m = re.search(r'version "(\d+)', text)
        return int(m.group(1)) if m else None
    major = parse_version(jv.stderr + jv.stdout)
    if major is None or major < 17:
        print(f"[ERROR] Java 17+ required, detected: {major}")
        sys.exit(1)

    # Try to prefetch Smile dependency so network is used only here
    print(f"[INFO] Prefetching Smile artifact com.github.haifengl:smile-core:{args.smile_version}")
    ret = subprocess.run([
        "mvn", "-Dmaven.repo.local=./.m2", "-q", "dependency:get",
        f"-Dartifact=com.github.haifengl:smile-core:{args.smile_version}",
    ], env=env_vars) 
    if ret.returncode != 0:
        print("[WARN] Prefetch failed. Maven build will try again during package.")

    # Build project
    print(f"[INFO] Building project: mvn -Dmaven.repo.local=./.m2 -Dsmile.version={args.smile_version} {args.maven_goal}")
    build_cmd = ["mvn", "-Dmaven.repo.local=./.m2", f"-Dsmile.version={args.smile_version}"] + args.maven_goal.split()
    ret = subprocess.run(build_cmd, env=env_vars) 
    if ret.returncode != 0:
        print("[ERROR] Maven build failed")
        sys.exit(1)

    # Prime exec-maven-plugin and its dependencies so later runs are offline
    print("[INFO] Priming exec:java plugin dependencies (one-time warmup)")

    data_cmd = [
        "python3", "generate_data.py",
    ]

    ret = subprocess.run(data_cmd, env=env_vars) 
    if ret.returncode != 0:
        print("[WARN] Data generation failed.")
    
    jvm_args = f"-Xms256m -Xmx256m -Dsmile.threads=1 {MAVEN_OPTS_FIX}" 
    
    prime_cmd = [
        "mvn", "-Dmaven.repo.local=./.m2", f"-Dsmile.version={args.smile_version}",
        "exec:java",
        "-Dexec.mainClass=benchmark.smile.BenchmarkRunner",
        f"-Dexec.jvmArgs={jvm_args}", 
        "-Dexec.args=--workload kmeans --data ./data/kmeans.csv --threads 1 --clusters 2 --iters 1",
    ]
    ret = subprocess.run(prime_cmd, env=env_vars) 
    if ret.returncode != 0:
        print("[WARN] exec:java warmup failed (this is usually safe to ignore; dependencies may already be cached)")

    print("[INFO] Setup complete.")


if __name__ == "__main__":
    main()