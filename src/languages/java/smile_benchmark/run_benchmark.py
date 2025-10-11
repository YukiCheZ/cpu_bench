#!/usr/bin/env python3
import argparse
import subprocess
import sys

def main():
    parser = argparse.ArgumentParser(description="Run KMeans Java benchmark")
    parser.add_argument("--data", type=str, default="./data/kmeans.csv",
                        help="Path to input CSV data")
    parser.add_argument("--clusters", type=int, default=1000,
                        help="Number of clusters")
    parser.add_argument("--copies", type=int, default=1,
                        help="Number of concurrent copies")
    parser.add_argument("--maven_goal", type=str, default="clean compile",
                        help="Maven goal for compilation")
    args = parser.parse_args()

    print(f"[INFO] Compiling Java project with Maven: mvn {args.maven_goal}")
    compile_cmd = ["mvn"] + args.maven_goal.split()
    ret = subprocess.run(compile_cmd)
    if ret.returncode != 0:
        print("[ERROR] Maven compilation failed")
        sys.exit(1)

    print("[INFO] Running KMeans benchmark")
    run_mixed_cmd = [
        "mvn", "exec:java",
        "-Dexec.mainClass=benchmark.smile.KMeansBenchmark",
        "-Dexec.jvmArgs=-Xms8g -Xmx8g -XX:+TieredCompilation -XX:-UseBiasedLocking",
        "-Dexec.args={data} {clusters} {copies}".format(
            data=args.data,
            clusters=args.clusters,
            copies=args.copies
        )
    ]
    run_int_cmd = [
        "mvn", "exec:java",
        "-Dexec.mainClass=benchmark.smile.KMeansBenchmark",
        "-Dexec.jvmArgs=-Xint -Xms8g -Xmx8g -XX:-UseBiasedLocking",
        "-Dexec.args={data} {clusters} {copies}".format(
            data=args.data,
            clusters=args.clusters,
            copies=args.copies
        )
    ]

    run_comp_cmd = [
        "mvn", "exec:java",
        "-Dexec.mainClass=benchmark.smile.KMeansBenchmark",
        "-Dexec.jvmArgs=-Xcomp -Xms8g -Xmx8g -XX:+TieredCompilation -XX:-UseBiasedLocking",
        "-Dexec.args={data} {clusters} {copies}".format(
            data=args.data,
            clusters=args.clusters,
            copies=args.copies
        )
    ]
    ret = subprocess.run(run_mixed_cmd)
    if ret.returncode != 0:
        print("[ERROR] Benchmark execution failed")
        sys.exit(1)

    print("[INFO] Benchmark finished successfully")

if __name__ == "__main__":
    main()
