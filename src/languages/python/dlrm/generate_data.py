# generate_dlrm_data.py
import os
import json
import torch
import argparse
import shutil

def generate_batches(output_dir: str, num_batches: int, batch_size: int,
                     dense_dim: int, sparse_dim: int, num_embeddings: int):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    for i in range(num_batches):
        dense = torch.randn(batch_size, dense_dim)
        sparse = torch.randint(0, num_embeddings, (batch_size, sparse_dim))
        file_path = os.path.join(output_dir, f"batch_{i}.pt")
        torch.save((dense, sparse), file_path)
        print(f"Saved {file_path}")

    meta = {
        "batch_size": batch_size,
        "dense_dim": dense_dim,
        "sparse_dim": sparse_dim,
        "num_embeddings": num_embeddings,
        "num_batches": num_batches
    }
    with open(os.path.join(output_dir, "metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Saved metadata.json in {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate DLRM CPU inference batches")
    parser.add_argument("--output_dir", type=str, default="./data", help="Directory to save batches")
    parser.add_argument("--num_batches", type=int, default=3, help="Number of batches to generate")
    parser.add_argument("--batch_size", type=int, default=256, help="Number of samples per batch")
    parser.add_argument("--dense_dim", type=int, default=256, help="Dense feature dimension")
    parser.add_argument("--sparse_dim", type=int, default=256, help="Sparse feature dimension")
    parser.add_argument("--num_embeddings", type=int, default=10000, help="Number of embedding entries per table")
    args = parser.parse_args()

    generate_batches(
        output_dir=args.output_dir,
        num_batches=args.num_batches,
        batch_size=args.batch_size,
        dense_dim=args.dense_dim,
        sparse_dim=args.sparse_dim,
        num_embeddings=args.num_embeddings
    )
