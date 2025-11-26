#!/usr/bin/env python3
import argparse
import yaml
import shutil
import sys
from pathlib import Path
from datetime import datetime

BENCHMARKS_FILE = "configs/benchmarks_index.yaml"
TARGETS = [
    "data",
    "bin",
    ".m2",
    "build",
    "target",
    "deps_vendored",
    "go.mod",
    "go.sum",
    "vendor",
]


def load_yaml(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def remove_path(p: Path, dry_run: bool, verbose: bool):
    if not p.exists():
        if verbose:
            print(f"[SKIP] {p} (not found)")
        return False

    try:
        if p.is_dir():
            if verbose:
                print(f"[DEL DIR] {p}")
            if not dry_run:
                shutil.rmtree(p)
        else:
            if verbose:
                print(f"[DEL FILE] {p}")
            if not dry_run:
                p.unlink()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to remove {p}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Clean build/data artifacts from benchmark project directories.")
    parser.add_argument("--benches", nargs="+", help="Names of benchmarks to clean. If omitted, use --all.")
    parser.add_argument("--all", action="store_true", help="Clean all benchmarks defined in index.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without removing.")
    parser.add_argument("--verbose", action="store_true", help="Print detailed progress.")
    args = parser.parse_args()

    benchmarks_config = load_yaml(Path(BENCHMARKS_FILE))
    bench_map = {b["name"]: b for b in benchmarks_config.get("benchmarks", [])}

    # Determine benches to clean
    target_benches = []
    if args.all:
        target_benches = list(bench_map.keys())
        if not target_benches:
            print("[ERROR] No benchmarks defined in index.")
            sys.exit(1)
    elif args.benches:
        for bench_name in args.benches:
            if bench_name not in bench_map:
                print(f"[WARNING] Benchmark '{bench_name}' not found in {BENCHMARKS_FILE}")
                continue
            target_benches.append(bench_name)
    else:
        print("[ERROR] You must specify --benches or --all.")
        sys.exit(1)

    total_removed = 0
    for bench_name in target_benches:
        root = Path(bench_map[bench_name]["path"]).resolve()
        if args.verbose:
            print(f"\n[INFO] Cleaning: {bench_name} (root={root})")
        for rel in TARGETS:
            p = (root / rel).resolve()
            removed = remove_path(p, args.dry_run, args.verbose)
            if removed:
                total_removed += 1

    if args.dry_run:
        print(f"\n[SUMMARY] Dry-run complete. Targets matched: {total_removed}")
    else:
        print(f"\n[SUMMARY] Cleanup complete. Items removed: {total_removed}")


if __name__ == "__main__":
    main()
