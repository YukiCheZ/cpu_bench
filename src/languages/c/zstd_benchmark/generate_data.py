#!/usr/bin/env python3
import argparse
import os
import random

def generate_pseudorandom_file(filename, size_mb=100, seed=42):
    """Generate a reproducible pseudo-random binary file using only standard library."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    random.seed(seed)
    bytes_per_chunk = 1024 * 1024  # 1 MB per write
    total_bytes = size_mb * 1024 * 1024

    with open(filename, "wb") as f:
        bytes_written = 0
        while bytes_written < total_bytes:
            chunk_size = min(bytes_per_chunk, total_bytes - bytes_written)
            chunk = bytearray(random.getrandbits(8) for _ in range(chunk_size))
            f.write(chunk)
            bytes_written += chunk_size

    print(f"Generated file: {filename} ({size_mb} MB)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate pseudo-random data for zstd CPU benchmark")
    parser.add_argument("--size", type=int, default=100, help="Size of the generated file in MB")
    args = parser.parse_args()

    output_file = "./data/zstd_input.bin"
    generate_pseudorandom_file(output_file, args.size)
