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

log_file = None
VERBOSE = False  # global flag for optional console output
USE_PERF = False
log_path = None  # global to access in run_workload()

# ============================================================
# Perf configuration
# ============================================================
PERF_CMD_PREFIX = (
    "time perf stat -r 3 "
    "-e 'r010E, r00C0, r00C4, r00C5, r0183, r0283, r3F24, r20D1, r81D0, r82D0' "
    "-e 'r01C7, r02C7, r04C7, r08C7, r10C7, r20C7' "
    "-e 'L1-dcache-load-misses,L1-dcache-loads,L1-dcache-misses,L1-dcache' "
    "-e 'LLC' "
    "-e 'dTLB-load-misses,dTLB-loads,dTLB,dTLB-misses' "
    "-e 'iTLB-load-misses,iTLB-loads,iTLB,iTLB-misses' "
    "-e 'branch-load-misses,branch-load,branch-misses,branch-instructions' "
    "-e 'instructions,cache-misses,cycles'"
)


# ============================================================
# Logging
# ============================================================
def log(msg: str, also_print=False):
    """Write a message to log file, optionally print to console when verbose."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    log_file.write(line + "\n")
    log_file.flush()
    if also_print and VERBOSE:
        print(line)


# ============================================================
# Helpers
# ============================================================
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
        log(f"[ERROR] Command failed with exit code {process.returncode}")
        raise RuntimeError(f"Command failed with exit code {process.returncode}")

    if expect_result and elapsed_time is None:
        raise RuntimeError(f"No result line found in output for command: {cmd}")

    return elapsed_time


# ============================================================
# Setup phase
# ============================================================
def run_setup_for_benchmark(bench_name: str, bench_path: Path, overrides) -> bool:
    meta_path = bench_path / "metadata.yaml"
    if not meta_path.exists():
        log(f"[WARNING] metadata.yaml not found in {bench_path}")
        return False

    metadata = load_yaml(meta_path)
    setup_info = metadata.get("setup")
    if not setup_info or "command" not in setup_info:
        log(f"[INFO] No setup command defined for {bench_name}, skipping setup.")
        return True

    cmd = setup_info["command"]
    setup_params_meta = setup_info.get("parameters", {})

    # setup overrides use key (bench_name, "_", "setup")
    key = (bench_name, "_", "setup")
    param_str = ""
    if key in overrides:
        cmd, param_str = apply_param_overrides(
            cmd, overrides[key], setup_params_meta, bench_name, "_", "setup"
        )
        if param_str:
            log(f"[INFO] Setup parameters applied: {param_str}")

    log(f"=============== Running setup for {bench_name}: {cmd} ===============")
    try:
        process = subprocess.Popen(
            cmd,
            cwd=bench_path,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            executable="/bin/bash"
        )
        for line in process.stdout:
            log(line.rstrip())
        process.wait()
        if process.returncode == 0:
            log(f"[OK] Setup completed successfully for {bench_name}")
            return True
        else:
            log(f"[ERROR] Setup failed for {bench_name} (exit {process.returncode})")
            return False
    except Exception as e:
        log(f"[ERROR] Setup for {bench_name} failed: {e}")
        return False


# ============================================================
# Parameter parsing & override
# ============================================================
def parse_set_param_entries(set_param_list):
    """
    Parse --set-param entries into a dict:
      overrides[(bench, workload, target)][param] = value or None
    Supports:
      <benchmark>.<workload>.<target>.<param>=<value>
      <benchmark>.<workload>.<target>.<param>
    Extended to support:
      <benchmark>._.setup.<param>=<value>  # for setup parameters
    """
    overrides = {}
    if not set_param_list:
        return overrides

    pattern_with_val = re.compile(r"^([^.]+)\.([^.]+|_)\.(data|workload|setup)\.([A-Za-z0-9_\-]+)=(.+)$")
    pattern_flag = re.compile(r"^([^.]+)\.([^.]+|_)\.(data|workload|setup)\.([A-Za-z0-9_\-]+)$")

    for entry in set_param_list:
        if m := pattern_with_val.match(entry):
            bench, wl, target, param, value = m.groups()
            key = (bench, wl, target)
            overrides.setdefault(key, {})[param] = value
            log(f"[INFO] Parsed override: {bench}/{wl}.{target}.{param}={value}")
        elif m := pattern_flag.match(entry):
            bench, wl, target, param = m.groups()
            key = (bench, wl, target)
            overrides.setdefault(key, {})[param] = None
            log(f"[INFO] Parsed override: {bench}/{wl}.{target}.{param} (flag)")
        else:
            log(f"[WARNING] Ignoring invalid --set-param entry: {entry}")
    return overrides


def apply_param_overrides(base_cmd, overrides_dict, param_meta, bench, wl, target):
    """
    Append parameters to base_cmd if they exist in param_meta.
    Supports boolean flags (no value) and normal key=value pairs.
    """
    if not overrides_dict:
        return base_cmd, ""
    param_parts = []
    for p, v in overrides_dict.items():
        exists = False
        param_default = None

        # check existence
        if isinstance(param_meta, dict):
            exists = p in param_meta
            param_default = param_meta[p].get("default") if exists and isinstance(param_meta[p], dict) else param_meta.get(p, None)
        elif isinstance(param_meta, list):
            exists = p in param_meta

        if not exists:
            log(f"[WARNING] Override param '{p}' not found in {bench}/{wl}.{target}.parameters — ignored")
            continue

        # boolean flag
        if v is None and (isinstance(param_default, bool) or str(param_default).lower() in ("true", "false")):
            param_parts.append(f"--{p}")
        elif v is not None:
            if isinstance(param_default, bool) or str(param_default).lower() in ("true", "false"):
                if v.lower() == "true":
                    param_parts.append(f"--{p}")
                else:
                    log(f"[INFO] Skipping flag {p} since value={v}")
            else:
                param_parts.append(f"--{p} {v}")
        elif v is None and param_default is None:
            param_parts.append(f"--{p}")

    if param_parts:
        base_cmd = f"{base_cmd} {' '.join(param_parts)}"

    return base_cmd, " ".join(param_parts)


# ============================================================
# Workload execution
# ============================================================
def run_workload(benchmark_name, benchmark_path: Path, csv_writer, csv_file, overrides, target_workloads=None):
    global USE_PERF, log_path
    metadata = load_yaml(benchmark_path / "metadata.yaml")
    workloads = metadata.get("workloads", [])

    for wl in workloads:
        wl_name = wl["name"]

        if target_workloads is not None and wl_name not in target_workloads:
            continue

        log(f"\n==== Running workload: {benchmark_name} / {wl_name} ====")
        try:
            param_str = ""
            # ---------- Data generation ----------
            if "data" in wl and "command" in wl["data"]:
                data_cmd = wl["data"]["command"]
                key = (benchmark_name, wl_name, "data")
                data_params_meta = wl["data"].get("parameters", {})
                if key in overrides:
                    data_cmd, data_param_str = apply_param_overrides(
                        data_cmd, overrides[key], data_params_meta, benchmark_name, wl_name, "data"
                    )
                    param_str += ("data: " + data_param_str + "; ")
                log(f"[*] Generating data for {wl_name} with cmd: {data_cmd}")
                run_command(data_cmd, cwd=benchmark_path, expect_result=False)

            # ---------- Main workload ----------
            main_cmd = wl["command"]
            key_w = (benchmark_name, wl_name, "workload")
            workload_params_meta = wl.get("parameters", {})
            if key_w in overrides:
                main_cmd, workload_param_str = apply_param_overrides(
                    main_cmd, overrides[key_w], workload_params_meta, benchmark_name, wl_name, "workload"
                )
                param_str += ("workload: " + workload_param_str + "; ")

            # ---------- Perf wrapper ----------
            # ---------- Drop system caches before perf ----------
            if USE_PERF:
                log("[INFO] Dropping system caches before perf measurement...")
                drop_cache_cmd = "sync; echo 3 > /proc/sys/vm/drop_caches"
                try:
                    subprocess.run(drop_cache_cmd, shell=True, check=True, executable="/bin/bash")
                    log("[OK] System caches dropped.")
                except subprocess.CalledProcessError as e:
                    log(f"[WARNING] Failed to drop caches: {e}")

            if USE_PERF:
                perf_dir = Path(log_path).parent.resolve() / "perf"
                perf_dir.mkdir(exist_ok=True)
                time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                perf_out = perf_dir / f"{benchmark_name}_{wl_name}_{time_stamp}.out"
                cmd_to_run = f"{PERF_CMD_PREFIX} -o {perf_out} {main_cmd}"
                log(f"[*] Running with perf stat, output -> {perf_out}")
            else:
                cmd_to_run = main_cmd

            log(f"[*] Running benchmark for {wl_name} with cmd: {cmd_to_run}")
            elapsed_time = run_command(cmd_to_run, cwd=benchmark_path, expect_result=True)

            csv_writer.writerow([benchmark_name, wl_name, elapsed_time, param_str])
            csv_file.flush()
            log(f"[OK] {benchmark_name}/{wl_name}: {elapsed_time:.4f} s")
        except Exception as e:
            log(f"[WARNING] Workload {benchmark_name}/{wl_name} failed: {e}")
            failed_workloads.append(f"{benchmark_name}/{wl_name}: {e}")


# ============================================================
# Main
# ============================================================
def main():
    global log_file, VERBOSE, failed_workloads, USE_PERF, log_path
    failed_workloads = []
    missing_items = []

    parser = argparse.ArgumentParser(description="Run CPU benchmark workloads with optional perf collection.")
    parser.add_argument("--workloads", nargs="+", help="Specific workloads to run, format: <benchmark>.<workload>")
    parser.add_argument("--benches", nargs="+", help="Names of benchmarks to run.")
    parser.add_argument("--out", help="Output CSV file path (auto timestamp if not set)")
    parser.add_argument("--log", help="Log file path (auto timestamp if not set)")
    parser.add_argument("--set-param", action="append", help="Override parameters")
    parser.add_argument("--setup-env", action="store_true", help="Run setup commands before execution.")
    parser.add_argument("--verbose", action="store_true", help="Print logs to console as well.")
    parser.add_argument("--use-perf", action="store_true", help="Enable perf stat measurement for workloads.")
    args = parser.parse_args()

    VERBOSE = args.verbose
    USE_PERF = args.use_perf

    # ======= log init =======
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    result_file = args.out or f"results_{timestamp}.csv"
    log_path = args.log or f"logs_{timestamp}.log"
    log_file = open(log_path, "w", encoding="utf-8")

    # ======= load benchmark definitions =======
    benchmarks_config = load_yaml(Path(BENCHMARKS_FILE))
    bench_map = {b["name"]: b for b in benchmarks_config.get("benchmarks", [])}
    overrides = parse_set_param_entries(args.set_param or [])

    workload_map = {}   # {bench_name: set(workload_names)}

    # ============================================================
    # --workloads mode
    # ============================================================
    if args.workloads:
        for wl_full in args.workloads:
            if "." not in wl_full:
                log(f"[WARNING] Invalid workload format: {wl_full}, expected <bench>.<workload>")
                missing_items.append(wl_full)
                continue
            bench_name, wl_name = wl_full.split(".", 1)
            if bench_name not in bench_map:
                log(f"[WARNING] Benchmark '{bench_name}' not found in {BENCHMARKS_FILE}")
                missing_items.append(wl_full)
                continue
            workload_map.setdefault(bench_name, set()).add(wl_name)
        mode = "workload"

    # ============================================================
    # --benches mode
    # ============================================================
    elif args.benches:
        for bench_name in args.benches:
            if bench_name not in bench_map:
                log(f"[WARNING] Benchmark '{bench_name}' not found in {BENCHMARKS_FILE}")
                missing_items.append(bench_name)
                continue
            meta_path = Path(bench_map[bench_name]["path"]) / "metadata.yaml"
            if not meta_path.exists():
                log(f"[WARNING] metadata.yaml missing for {bench_name}")
                missing_items.append(bench_name)
                continue
            metadata = load_yaml(meta_path)
            workloads = metadata.get("workloads", [])
            if not workloads:
                log(f"[WARNING] No workloads defined in {meta_path}")
                missing_items.append(bench_name)
                continue
            workload_map[bench_name] = set(wl["name"] for wl in workloads)
        mode = "bench"
    else:
        log("[ERROR] You must specify either --workloads or --benches.")
        sys.exit(1)

    # ============================================================
    # Setup phase
    # ============================================================
    failed_setups = set()
    if args.setup_env:
        log("\n[INFO] Running setup phase for selected benchmarks...")
        for bench_name in workload_map:
            bench = bench_map[bench_name]
            ok = run_setup_for_benchmark(bench_name, Path(bench["path"]), overrides)
            if not ok:
                failed_setups.add(bench_name)
                log(f"[WARNING] Skipping workloads for {bench_name} due to setup failure.")

    # ============================================================
    # Run phase
    # ============================================================
    with open(result_file, "w", newline="", encoding="utf-8") as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(["benchmark_name", "workload_name", "elapsed_time(s)", "param_overrides"])
        f.flush()

        for bench_name, wl_names in workload_map.items():
            bench = bench_map[bench_name]
            if bench_name in failed_setups:
                log(f"[SKIP] {bench_name}: setup failed, skipping workloads.")
                continue
            log(f"\n>>> Running workloads for benchmark: {bench_name}")
            run_workload(bench_name, Path(bench["path"]), csv_writer, f, overrides, target_workloads=wl_names)

    # ============================================================
    # Summary
    # ============================================================
    if missing_items:
        log("\n[WARNING SUMMARY] Missing or invalid items:")
        for w in missing_items:
            log(f"  - {w}")

    if failed_workloads:
        log("\n[WARNING SUMMARY] Failed workloads:")
        for w in failed_workloads:
            log(f"  - {w}")

    log(f"\n[INFO] All selected {'workloads' if mode == 'workload' else 'benchmarks'} finished.")
    log(f"[INFO] Results saved to {result_file}")
    log(f"[INFO] Full logs saved to {log_path}")
    log_file.close()


if __name__ == "__main__":
    main()
