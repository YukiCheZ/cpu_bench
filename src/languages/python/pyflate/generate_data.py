#!/usr/bin/env python3
import argparse
import os
import bz2

def generate_data(size, output_file):
    raw_data = os.urandom(size)
    
    compressed = bz2.compress(raw_data, compresslevel=9)
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "wb") as f:
        f.write(compressed)
    
    print(f"Generated {len(compressed)} bytes of compressed data "
          f"from {size} bytes input at {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate input data for pyflate benchmark")
    parser.add_argument("--size", type=int, default=100000000,
                        help="Size of uncompressed random data in bytes")
    parser.add_argument("--output", type=str, default="data/interpreter.tar.bz2",
                        help="Output compressed file path (default: data/interpreter.tar.bz2)")
    args = parser.parse_args()
    
    generate_data(args.size, args.output)
