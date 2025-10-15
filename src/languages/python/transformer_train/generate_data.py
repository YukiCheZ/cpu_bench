#!/usr/bin/env python3
# generate_transformer_train_data.py
import os
import json
import torch
import argparse
import shutil

def generate_batches(output_dir, num_batches, batch_size, seq_len, vocab_size):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    for i in range(num_batches):
        src = torch.randint(0, vocab_size, (batch_size, seq_len))
        tgt = torch.randint(0, vocab_size, (batch_size, seq_len))
        target = torch.randint(0, vocab_size, (batch_size, seq_len))
        file_path = os.path.join(output_dir, f"batch_{i}.pt")
        torch.save((src, tgt, target), file_path)

    meta = {
        "batch_size": batch_size,
        "seq_len": seq_len,
        "vocab_size": vocab_size,
        "num_batches": num_batches
    }
    with open(os.path.join(output_dir, "metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(f"[INFO] Generated {num_batches} batches, saved metadata.json in {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Transformer CPU training batches")
    parser.add_argument("--output_dir", type=str, default="./data", help="Directory to save batches")
    parser.add_argument("--num_batches", type=int, default=40, help="Number of batches to generate")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size")
    parser.add_argument("--seq_len", type=int, default=128, help="Sequence length")
    parser.add_argument("--vocab_size", type=int, default=10000, help="Vocabulary size for input tokens")
    args = parser.parse_args()

    generate_batches(
        output_dir=args.output_dir,
        num_batches=args.num_batches,
        batch_size=args.batch_size,
        seq_len=args.seq_len,
        vocab_size=args.vocab_size
    )
