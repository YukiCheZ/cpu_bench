#!/usr/bin/env python3
import yaml
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

CONFIG_FILE = "configs/benchmarks_index.yaml"

def log(msg: str, logfile):
    """Write message to log file only."""
    logfile.write(msg + "\n")
    logfile.flush()

def run_command(cmd: str, cwd: Path, logfile):
    """Run setup command and log output."""
    try:
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            executable="/bin/bash"
        )
        for line in process.stdout:
            logfile.write(line)
        process.wait()
        return process.returncode == 0
    except Exception as e:
        log(f"[ERROR] Failed to run setup command: {e}", logfile)
        return False

def load_benchmarks():
    """Load benchmark list from configs/benchmarks_index.yaml."""
    config_path = Path(CONFIG_FILE)
    if not config_path.exists():
        raise FileNotFoundError(f"Benchmark index file not found: {CONFIG_FILE}")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config.get("benchmarks", [])

def setup_environment(bench_name: str, bench_path: Path, logfile):
    """Run setup.command from metadata.yaml if present."""
    meta_path = bench_path / "metadata.yaml"
    if not meta_path.exists():
        log(f"[WARNING] metadata.yaml not found in {bench_path}", logfile)
        return False

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = yaml.safe_load(f)

    setup_info = meta.get("setup")
    if not setup_info or "command" not in setup_info:
        log(f"[INFO] No setup command defined for {bench_name}, skipping.", logfile)
        return True

    cmd = setup_info["command"]
    log(f"\n[INFO] Setting up benchmark: {bench_name}", logfile)
    log(f"[INFO] Running setup command: {cmd}", logfile)

    success = run_command(cmd, cwd=bench_path, logfile=logfile)
    if success:
        log(f"[OK] Setup completed successfully for {bench_name}", logfile)
    else:
        log(f"[WARNING] Setup failed for {bench_name}", logfile)
    return success

def main():
    parser = argparse.ArgumentParser(description="Setup environments for benchmarks defined in configs/benchmarks_index.yaml")
    parser.add_argument("--benches", nargs="*", help="List of benchmark names to setup (default: all)")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / f"setup_envs_{timestamp}.log"

    with open(log_path, "w", encoding="utf-8") as logfile:
        try:
            benchmarks = load_benchmarks()
        except FileNotFoundError as e:
            log(f"[ERROR] {e}", logfile)
            return

        bench_map = {b["name"]: b for b in benchmarks}

        # Select benchmarks
        if args.benches:
            selected = []
            for bname in args.benches:
                if bname in bench_map:
                    selected.append(bench_map[bname])
                else:
                    log(f"[WARNING] Benchmark '{bname}' not found in {CONFIG_FILE}", logfile)
            if not selected:
                log("[ERROR] No valid benchmarks selected.", logfile)
                return
        else:
            selected = benchmarks

        log(f"[INFO] Starting environment setup for {len(selected)} benchmarks", logfile)
        failed = []

        for bench in selected:
            bench_name = bench["name"]
            bench_path = Path(bench["path"])
            if not bench_path.exists():
                log(f"[WARNING] Benchmark path not found: {bench_path}", logfile)
                failed.append(bench_name)
                continue

            ok = setup_environment(bench_name, bench_path, logfile)
            if not ok:
                failed.append(bench_name)

        log("\n[INFO] Environment setup finished.", logfile)
        if failed:
            log(f"[WARNING] The following benchmarks failed setup: {', '.join(failed)}", logfile)
        else:
            log("[INFO] All benchmarks configured successfully.", logfile)

if __name__ == "__main__":
    main()
