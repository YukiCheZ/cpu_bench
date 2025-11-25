#!/usr/bin/env python3
import os
import argparse
import numpy as np  # optional

def ensure_dir_clean(path: str):
    os.makedirs(path, exist_ok=True)
    for f in os.listdir(path):
        fp = os.path.join(path, f)
        if os.path.isfile(fp):
            os.remove(fp)


def gen_numeric(output: str, filename: str, samples: int, features: int, seed: int = 42):
    import random
    random.seed(seed)
    out = os.path.join(output, filename)
    if np is not None:
        rng = np.random.default_rng(seed)
        data = rng.random((samples, features), dtype=np.float64)
        np.savetxt(out, data, delimiter=",")
    else:
        with open(out, "w") as f:
            for _ in range(samples):
                row = ",".join(f"{random.random():.10f}" for _ in range(features))
                f.write(row + "\n")
    print(f"[INFO] Saved: {out} ({samples}x{features})")


def gen_regression(output: str, filename: str, samples: int, features: int, noise: float = 0.1, seed: int = 42):
    import random, math
    random.seed(seed)
    out = os.path.join(output, filename)
    header = [f"x{i}" for i in range(features)] + ["y"]
    if np is not None:
        rng = np.random.default_rng(seed)
        X = rng.standard_normal((samples, features))
        w = rng.standard_normal(features)
        y = X @ w + noise * rng.standard_normal(samples)
        with open(out, "w") as f:
            f.write(",".join(header) + "\n")
            for i in range(samples):
                row = ",".join(f"{X[i, j]:.10f}" for j in range(features)) + f",{y[i]:.10f}\n"
                f.write(row)
    else:
        w = [random.gauss(0, 1) for _ in range(features)]
        with open(out, "w") as f:
            f.write(",".join(header) + "\n")
            for _ in range(samples):
                x = [random.gauss(0, 1) for _ in range(features)]
                y = sum(x[j] * w[j] for j in range(features)) + noise * random.gauss(0, 1)
                row = ",".join(f"{x[j]:.10f}" for j in range(features)) + f",{y:.10f}\n"
                f.write(row)
    print(f"[INFO] Saved: {out} ({samples}x{features}+y)")


def main():
    parser = argparse.ArgumentParser(description="Generate data for Smile CPU benchmarks")
    parser.add_argument("--task", type=str, default="kmeans", choices=["kmeans"],
                        help="Dataset type to generate")
    parser.add_argument("--samples", type=int, default=10000, help="Number of samples")
    parser.add_argument("--features", type=int, default=100, help="Number of features")
    parser.add_argument("--output", type=str, default="./data", help="Output directory")
    parser.add_argument("--noise", type=float, default=0.1, help="Noise level for regression")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--queries", type=int, default=1000, help="Number of queries for KNN")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    if args.task in ("kmeans"):
        gen_numeric(args.output, f"{args.task}.csv", args.samples, args.features, args.seed)
    else:
        raise ValueError(f"Unknown task: {args.task}")


if __name__ == "__main__":
    main()
