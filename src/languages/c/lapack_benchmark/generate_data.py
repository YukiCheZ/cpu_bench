#!/usr/bin/env python3
import os
import argparse
import random
import struct

def write_matrix(path, n):
    with open(path, "wb") as f:
        for i in range(n * n):
            val = random.random()  
            f.write(struct.pack("d", val))  

def write_vector(path, n):
    with open(path, "wb") as f:
        for i in range(n):
            val = random.random()
            f.write(struct.pack("d", val))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, required=True, help="matrix size N")
    args = parser.parse_args()
    n = args.size

    os.makedirs("data", exist_ok=True)

    write_matrix(f"data/solve_A_{n}.bin", n)
    write_vector(f"data/solve_b_{n}.bin", n)

    path = f"data/eigen_A_{n}.bin"
    with open(path, "wb") as f:
        mat = [[random.random() for _ in range(n)] for _ in range(n)]
        for i in range(n):
            for j in range(n):
                val = (mat[i][j] + mat[j][i]) / 2.0
                f.write(struct.pack("d", val))

    write_matrix(f"data/svd_A_{n}.bin", n)

    print(f"[INFO] Generated data files for size={n} in ./data")

if __name__ == "__main__":
    main()
