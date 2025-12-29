#!/usr/bin/env python3
import argparse
import os
import random

def generate_pseudorandom_file(filename, size_kb=50, seed=42):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    random.seed(seed)
    bytes_per_chunk = 1024 * 1024  
    total_bytes = size_kb * 1024

    with open(filename, "wb") as f:
        bytes_written = 0
        while bytes_written < total_bytes:
            chunk_size = min(bytes_per_chunk, total_bytes - bytes_written)
            try:
                chunk = random.randbytes(chunk_size)
            except AttributeError:
                chunk = os.urandom(chunk_size)
            f.write(chunk)
            bytes_written += chunk_size

    print(f"[DATA] Generated file: {filename} ({size_kb} KB)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="[INFO] Generate pseudo-random data for zstd CPU benchmark")
    parser.add_argument("--size", type=int, default=50000, help="Size of the generated file in KB")
    args = parser.parse_args()

    output_file = "./data/zstd_input.bin"
    generate_pseudorandom_file(output_file, args.size)