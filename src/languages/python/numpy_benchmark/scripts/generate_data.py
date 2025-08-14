#!/usr/bin/env python3
import argparse
from pathlib import Path
from benchmarks.data_manager import DataManager

def main():
    parser = argparse.ArgumentParser(description="Generate datasets for NumPy benchmarks")
    parser.add_argument("--size", type=int, required=True, help="Dataset size (e.g., 2048 for 2048x2048 matrix)")
    parser.add_argument("--dataset", type=str, required=True, choices=["matrix", "svd", "fft"], help="Dataset type")
    parser.add_argument("--data_dir", type=str, default="data", help="Directory to save datasets")
    parser.add_argument("--dtype", type=str, default="float64", help="Data type (default: float64)")
    parser.add_argument("--force", action="store_true", help="Force regenerate data even if file exists")

    args = parser.parse_args()

    import numpy as np
    dtype = np.dtype(args.dtype)

    dm = DataManager(data_dir=args.data_dir, dtype=dtype)
    file_path = Path(args.data_dir) / f"{args.dataset}_{args.size}_{dtype.name}.npz"

    if file_path.exists() and not args.force:
        print(f"[GenerateData] Dataset already exists: {file_path}")
        print("Use --force to regenerate.")
    else:
        dm.generate_dataset(args.size, args.dataset)
        print(f"[GenerateData] Dataset generated and saved: {file_path}")

if __name__ == "__main__":
    main()
