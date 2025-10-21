#!/usr/bin/env python3
import argparse
from pathlib import Path
from benchmarks.data_manager import DataManager

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate datasets for Requests benchmarks")
    parser.add_argument("--data_dir", type=str, default="data", help="Directory to save datasets")
    parser.add_argument("--size", type=int, default=262144, help="Dataset size")
    parser.add_argument("--force", action="store_true", help="Overwrite if file exists")
    args = parser.parse_args()

    dm = DataManager(data_dir=args.data_dir)
    filename = Path(args.data_dir) / f"data_{args.size}.json"

    if filename.exists() and not args.force:
        print(f"[INFO] Dataset already exists: {filename}")
        print("[INFO] Use --force to regenerate.")
    else:
        dm.generate_dataset(args.size)
        print(f"[INFO] Dataset generated and saved: {filename}")
    
    print(f"[DATA] Generating dataset of size {args.size} in directory: {args.data_dir}")
