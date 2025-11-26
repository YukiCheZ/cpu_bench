#!/usr/bin/env python3
import argparse
import yaml
import subprocess
import sys
import re
from pathlib import Path
from datetime import datetime

BENCHMARKS_FILE = "configs/benchmarks_index.yaml"

# ============================================================
# Logging
# ============================================================
def log(msg: str, also_print=False):
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


def parse_set_param_entries(set_param_list):
    """
    Parse --set-param entries into a dict for setup only:
      overrides[(bench, "_", "setup")][param] = value or None
    Supports:
      <benchmark>._.setup.<param>=<value>
      <benchmark>._.setup.<param>
    """
    overrides = {}
    if not set_param_list:
        return overrides

    pattern_with_val = re.compile(r"^([^.]+)\._\.setup\.([A-Za-z0-9_\-]+)=(.+)$")
    pattern_flag = re.compile(r"^([^.]+)\._\.setup\.([A-Za-z0-9_\-]+)$")

    for entry in set_param_list:
        if m := pattern_with_val.match(entry):
            bench, param, value = m.groups()
            key = (bench, "_", "setup")
            overrides.setdefault(key, {})[param] = value
            log(f"[INFO] Parsed override: {bench}/_.setup.{param}={value}")
        elif m := pattern_flag.match(entry):
            bench, param = m.groups()
            key = (bench, "_", "setup")
            overrides.setdefault(key, {})[param] = None
            log(f"[INFO] Parsed override: {bench}/_.setup.{param} (flag)")
        else:
            log(f"[WARNING] Ignoring invalid --set-param entry: {entry}")
    return overrides


def apply_param_overrides(base_cmd, overrides_dict, param_meta, bench):
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

        if isinstance(param_meta, dict):
            exists = p in param_meta
            param_default = (
                param_meta[p].get("default")
                if exists and isinstance(param_meta[p], dict)
                else param_meta.get(p, None)
            )
        elif isinstance(param_meta, list):
            exists = p in param_meta

        if not exists:
            log(f"[WARNING] Override param '{p}' not found in {bench}/_.setup.parameters — ignored")
            continue

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

    key = (bench_name, "_", "setup")
    param_str = ""
    if key in overrides:
        cmd, param_str = apply_param_overrides(
            cmd, overrides[key], setup_params_meta, bench_name
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
            executable="/bin/bash",
        )
        for line in process.stdout:
            log(line.rstrip(), also_print=True)
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
# Main
# ============================================================
def main():
    global log_file, VERBOSE
    missing_items = []

    parser = argparse.ArgumentParser(description="Run setup for CPU benchmarks only.")
    parser.add_argument("--benches", nargs="+", help="Names of benchmarks to setup. If omitted, use --all.")
    parser.add_argument("--all", action="store_true", help="Run setup for all benchmarks defined.")
    parser.add_argument("--set-param", action="append", help="Override setup parameters, format: <bench>._.setup.<param>=<value> or flag without value.")
    parser.add_argument("--out-log", help="Log file path (auto timestamp if not set)")
    parser.add_argument("--verbose", action="store_true", help="Print logs to console as well.")
    args = parser.parse_args()

    VERBOSE = args.verbose

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = args.out_log or f"setup_logs_{timestamp}.log"
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Open log file
    global log_file
    log_file = open(log_path, "w", encoding="utf-8")

    # Load benchmark definitions
    benchmarks_config = load_yaml(Path(BENCHMARKS_FILE))
    bench_map = {b["name"]: b for b in benchmarks_config.get("benchmarks", [])}
    overrides = parse_set_param_entries(args.set_param or [])

    # Decide target benches
    target_benches = []
    if args.all:
        target_benches = list(bench_map.keys())
        if not target_benches:
            log("[ERROR] No benchmarks defined in index.")
            sys.exit(1)
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
            target_benches.append(bench_name)
    else:
        log("[ERROR] You must specify --benches or --all.")
        sys.exit(1)

    # Run setup
    failed_setups = []
    for bench_name in target_benches:
        bench = bench_map[bench_name]
        ok = run_setup_for_benchmark(bench_name, Path(bench["path"]), overrides)
        if not ok:
            failed_setups.append(bench_name)

    # Summary
    if missing_items:
        log("\n[WARNING SUMMARY] Missing or invalid items:")
        for w in missing_items:
            log(f"  - {w}")

    if failed_setups:
        log("\n[WARNING SUMMARY] Failed setups:")
        for w in failed_setups:
            log(f"  - {w}")

    log("\n[INFO] Setup phase finished.")
    log(f"[INFO] Full logs saved to {log_path}")
    log_file.close()


if __name__ == "__main__":
    main()
