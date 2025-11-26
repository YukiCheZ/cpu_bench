#!/usr/bin/env python3
import argparse
import random
import os

def generate_dna_sequence(length):
    return ''.join(random.choices('ACGT', k=length))

def main():
    parser = argparse.ArgumentParser(description="Generate DNA input for gopher-lua knucleotide benchmark")
    parser.add_argument("--size", type=int, default=1000000,
                        help="Length of the DNA sequence")
    parser.add_argument("--output", type=str, default="dna_input.fasta",
                        help="Output file name (will be placed in data/ directory by default)")
    args = parser.parse_args()

    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, args.output)

    with open(output_path, "w") as f:
        seq = generate_dna_sequence(args.size)
        for i in range(0, len(seq), 80):
            f.write(seq[i:i+80] + "\n")

    print(f"DNA sequence of length {args.size} written to {output_path}")

if __name__ == "__main__":
    main()
