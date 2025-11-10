#!/usr/bin/env python3
import os
import argparse
import numpy as np

def main():
    parser = argparse.ArgumentParser(description="Generate data for KMeans benchmark")
    parser.add_argument("--samples", type=int, default=10000, help="Number of samples")
    parser.add_argument("--features", type=int, default=100, help="Number of features")
    parser.add_argument("--output", type=str, default="./data", help="Output directory")
    args = parser.parse_args()

    if os.path.exists(args.output):
        for file in os.listdir(args.output):
            os.remove(os.path.join(args.output, file))
    else:
        os.makedirs(args.output, exist_ok=True)

    output_file = os.path.join(args.output, f"kmeans.csv")

    print(f"[INFO] Generating data: samples={args.samples}, features={args.features}")
    data = np.random.rand(args.samples, args.features)

    np.savetxt(output_file, data, delimiter=",")
    print(f"[INFO] Data saved to {output_file}")

if __name__ == "__main__":
    main()
