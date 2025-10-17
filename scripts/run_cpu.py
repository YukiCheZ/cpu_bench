#!/usr/bin/env python3
import argparse
import yaml
import subprocess
import csv
import sys
import re
from pathlib import Path
from datetime import datetime

BENCHMARKS_FILE = "configs/benchmarks_index.yaml"
RESULT_PATTERN = re.compile(r"\[RESULT\]\s+Total elapsed time:\s+([0-9.]+)\s*s")

missing_benchmarks = []
failed_workloads = []
log_file = None

def log(msg: str, also_print=False):
    """Write a message to log file, optionally print to console (only for debug)."""
    log_file.write(msg + "\n")
    log_file.flush()
    if also_print:
        print(msg)

def load_yaml(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_command(cmd, cwd, expect_result=True):
    log(f"[*] Running: {cmd} (cwd={cwd})")
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
        log(line)
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

def parse_set_param_entries(set_param_list):
    """
    Parse --set-param entries into a dict:
      overrides[(bench, workload, target)][param] = value

    Expected entry format:
      <benchmark>.<workload>.<target>.<param>=<value>
    where target is "data" or "workload".
    """
    overrides = {}  # key: (bench,wl,target) -> dict param->value
    if not set_param_list:
        return overrides

    pattern = re.compile(r"^([^.]+)\.([^.]+)\.(data|workload)\.([A-Za-z0-9_\-]+)=(.+)$")
    for entry in set_param_list:
        m = pattern.match(entry)
        if not m:
            # malformed entry
            log(f"[WARNING] Ignoring invalid --set-param entry: {entry}")
            continue
        bench, wl, target, param, value = m.groups()
        key = (bench, wl, target)
        overrides.setdefault(key, {})[param] = value
        log(f"[INFO] Parsed override: bench={bench}, workload={wl}, target={target}, {param}={value}")
    return overrides

def run_workload(benchmark_name, benchmark_path: Path, csv_writer, threads: int, overrides):
    """
    Run workloads; only append parameters if the user supplied overrides
    (and the param name exists in metadata's parameters for that target).
    """
    metadata = load_yaml(benchmark_path / "metadata.yaml")
    workloads = metadata.get("workloads", [])

    # get underlying file object for flushing
    writer_file = csv_writer.writerows.__self__

    for wl in workloads:
        wl_name = wl["name"]
        log(f"\n==== Running workload: {benchmark_name} / {wl_name} ====")
        try:
            # ---------- Data generation ----------
            if "data" in wl and "command" in wl["data"]:
                data_cmd = wl["data"]["command"]
                # only append overrides that exist in metadata data.parameters
                data_params_meta = wl["data"].get("parameters", {}) if "data" in wl else {}
                key = (benchmark_name, wl_name, "data")
                param_parts = []
                if key in overrides:
                    for p, v in overrides[key].items():
                        if p in data_params_meta:
                            param_parts.append(f"--{p} {v}")
                        else:
                            log(f"[WARNING] Override param '{p}' not found in {benchmark_name}/{wl_name}.data.parameters — ignored")
                if param_parts:
                    data_cmd = f"{data_cmd} " + " ".join(param_parts)
                log(f"[*] Generating data for {wl_name} with cmd: {data_cmd}")
                run_command(data_cmd, cwd=benchmark_path, expect_result=False)

            # ---------- Main workload ----------
            main_cmd = wl["command"]
            # prepare overrides for workload parameters
            workload_params_meta = wl.get("parameters", {})
            # If threads provided globally and 'threads' exists in metadata parameters,
            # we treat threads specially: we allow global --threads to override only
            # if 'threads' exists in metadata parameters OR user also provided override.
            key_w = (benchmark_name, wl_name, "workload")
            param_parts = []
            if key_w in overrides:
                for p, v in overrides[key_w].items():
                    if p in workload_params_meta:
                        param_parts.append(f"--{p} {v}")
                    else:
                        log(f"[WARNING] Override param '{p}' not found in {benchmark_name}/{wl_name}.parameters — ignored")

            # Global --threads argument: if provided, and parameter 'threads' is declared in metadata,
            # then append/override it (but do not append if metadata does not declare threads).
            if threads is not None:
                if "threads" in workload_params_meta:
                    # If user also set threads via overrides, overrides take precedence (we already appended above).
                    # To avoid duplicate, only append global threads if user didn't specify it in overrides.
                    if not (key_w in overrides and "threads" in overrides[key_w]):
                        param_parts.append(f"--threads {threads}")
                else:
                    # no 'threads' in metadata: we will NOT add global threads; warn user
                    log(f"[WARNING] Global --threads provided but '{benchmark_name}/{wl_name}' does not declare 'threads' parameter in metadata. Ignored.")

            if param_parts:
                main_cmd = f"{main_cmd} " + " ".join(param_parts)

            log(f"[*] Running benchmark for {wl_name} with cmd: {main_cmd}")
            elapsed_time = run_command(main_cmd, cwd=benchmark_path, expect_result=True)

            csv_writer.writerow([benchmark_name, wl_name, elapsed_time])
            writer_file.flush()
            log(f"[OK] {benchmark_name}/{wl_name}: {elapsed_time:.3f}s")
        except Exception as e:
            log(f"[WARNING] Workload {benchmark_name}/{wl_name} failed: {e}")
            failed_workloads.append(f"{benchmark_name}/{wl_name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Run CPU benchmark workloads.")
    parser.add_argument("--benches", nargs="+", help="Names of benchmarks to run (default: preset)")
    parser.add_argument("--out", help="Output CSV file path (auto timestamp if not set)")
    parser.add_argument("--log", help="Log file path (auto timestamp if not set)")
    parser.add_argument("--threads", type=int, help="Number of threads to use for each workload (global override)")
    parser.add_argument("--set-param", action="append", help=(
        "Override parameter for specific workload. Format: "
        "<benchmark>.<workload>.<data|workload>.<param>=<value>. "
        "Can be passed multiple times."
    ))
    args = parser.parse_args()

    # timestamped filenames
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    result_file = args.out or f"results_{timestamp}.csv"
    log_path = args.log or f"logs_{timestamp}.log"

    global log_file
    log_file = open(log_path, "w", encoding="utf-8")

    # default_set
    default_set = [
        "numpy_benchmark", "requests_benchmark", "tuf_benchmark",
        "raytrace", "go_board_game", "chaos_fractal", "deltablue",
        "pyflate", "resnet50_cpu", "transformer_inference", "transformer_train"
    ]

    # load benchmarks index
    benchmarks_config = load_yaml(Path(BENCHMARKS_FILE))
    all_benches = benchmarks_config.get("benchmarks", [])
    bench_map = {b["name"]: b for b in all_benches}

    if args.benches:
        selected = []
        for bname in args.benches:
            if bname in bench_map:
                selected.append(bench_map[bname])
            else:
                log(f"[WARNING] Benchmark '{bname}' not found in {BENCHMARKS_FILE}")
                missing_benchmarks.append(bname)
    else:
        selected = [bench_map[b] for b in default_set if b in bench_map]
        for b in default_set:
            if b not in bench_map:
                missing_benchmarks.append(b)

    if not selected:
        log("No valid benchmarks found to run. Exiting.")
        sys.exit(1)

    # parse overrides
    overrides = parse_set_param_entries(args.set_param)

    # write header and run
    with open(result_file, "w", newline="", encoding="utf-8") as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(["benchmark_name", "workload_name", "elapsed_time(s)"])
        f.flush()

        for bench in selected:
            name = bench["name"]
            path = Path(bench["path"]).parent
            log(f"\n>>> Running benchmark: {name} at {path}")
            # pass overrides into run_workload
            run_workload(name, path, csv_writer, args.threads, overrides)

    # summaries
    if missing_benchmarks:
        log("\n[WARNING SUMMARY] Missing benchmarks:")
        for b in missing_benchmarks:
            log(f"  - {b}")

    if failed_workloads:
        log("\n[WARNING SUMMARY] Failed workloads:")
        for w in failed_workloads:
            log(f"  - {w}")

    log(f"\n[INFO] All valid workloads finished. Results saved to {result_file}")
    log(f"[INFO] Full logs saved to {log_path}")
    log_file.close()

if __name__ == "__main__":
    main()
