#!/usr/bin/env python3
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description="Generate binary data for CPU benchmark")
    parser.add_argument('--size', type=int, default=50,
                        help="Size of data to generate in MB (default: 10)")
    parser.add_argument('--output', type=str, default="./data/data.bin",
                        help="Output file path (default: ./data/data.bin)")
    args = parser.parse_args()

    size_bytes = args.size * 1024 * 1024
    output_path = args.output

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"[INFO] Generating {args.size} MB of random data into {output_path}...")
    with open(output_path, "wb") as f:
        chunk_size = 1024 * 1024  # 1 MB
        for _ in range(args.size):
            f.write(os.urandom(chunk_size))

    print("[DATA] Data generation completed.")

if __name__ == "__main__":
    main()
