#!/usr/bin/env python3
import argparse
import yaml
import subprocess
import csv
import sys
import re
from pathlib import Path

# Path to the benchmark list file
BENCHMARKS_FILE = "configs/benchmarks_index.yaml"

# Default CSV output file name
RESULT_CSV = "results.csv"

# Pattern to extract result line from workload output
RESULT_PATTERN = re.compile(r"\[RESULT\]\s+Total elapsed time:\s+([0-9.]+)\s*s")

def load_yaml(path: Path):
    """Load a YAML file and return its content."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_command(cmd, cwd, expect_result=True):
    """
    Run a shell command in a specific working directory.
    If expect_result=True, parse the elapsed time from the output.
    """
    print(f"[*] Running: {cmd} (cwd={cwd})")
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    elapsed_time = None
    for line in process.stdout:
        line = line.rstrip()
        print(line)
        if expect_result:
            match = RESULT_PATTERN.search(line)
            if match:
                elapsed_time = float(match.group(1))

    process.wait()
    if process.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {process.returncode}")

    if expect_result and elapsed_time is None:
        raise RuntimeError("No result line found: [RESULT] Total elapsed time: ...")

    return elapsed_time

def run_workload(benchmark_name, benchmark_path: Path):
    """Run all workloads defined in the benchmark's metadata.yaml file."""
    metadata = load_yaml(benchmark_path / "metadata.yaml")

    results = []
    workloads = metadata.get("workloads", [])
    for wl in workloads:
        wl_name = wl["name"]
        print(f"\n==== Running workload: {benchmark_name} / {wl_name} ====")

        # Run data generation command if exists (no result expected)
        if "data" in wl and "command" in wl["data"]:
            data_cmd = wl["data"]["command"]
            print(f"[*] Generating data for {wl_name} ...")
            run_command(data_cmd, cwd=benchmark_path, expect_result=False)

        # Run main benchmark command (result expected)
        main_cmd = wl["command"]
        print(f"[*] Running benchmark for {wl_name} ...")
        elapsed_time = run_command(main_cmd, cwd=benchmark_path, expect_result=True)

        results.append((benchmark_name, wl_name, elapsed_time))

    return results

def main():
    parser = argparse.ArgumentParser(description="Run CPU benchmark workloads.")
    parser.add_argument("--benches", nargs="+", help="Names of benchmarks to run (default: all)")
    parser.add_argument("--out", default=RESULT_CSV, help="Output CSV file path")
    args = parser.parse_args()

    python_set = []


    # Load benchmark list
    benchmarks_config = load_yaml(Path(BENCHMARKS_FILE))
    all_benches = benchmarks_config.get("benchmarks", [])

    if args.benches:
        selected = [b for b in all_benches if b["name"] in args.benches]
    else:
        selected = all_benches

    if not selected:
        print("No matching benchmarks found. Check the benchmark names.")
        sys.exit(1)

    all_results = []
    for bench in selected:
        name = bench["name"]
        path = Path(bench["path"]).parent
        print(f"\n>>> Running benchmark: {name} at {path}")
        results = run_workload(name, path)
        all_results.extend(results)

    # Write results to CSV
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["benchmark_name", "workload_name", "elapsed_time(s)"])
        for r in all_results:
            writer.writerow(r)

    print(f"\n All results have been saved to {args.out}")

if __name__ == "__main__":
    main()
