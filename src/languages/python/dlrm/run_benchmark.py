# dlrm_cpu_inference.py
import os
import json
import time
import argparse
import torch
from torchrec.models.dlrm import DLRM
from torchrec.modules.embedding_configs import EmbeddingBagConfig
from torchrec.modules.embedding_modules import EmbeddingBagCollection
from torchrec.sparse.jagged_tensor import KeyedJaggedTensor

def load_metadata(data_dir: str):
    meta_path = os.path.join(data_dir, "metadata.json")
    if not os.path.exists(meta_path):
        raise FileNotFoundError(f"metadata.json not found in {data_dir}. Please run data generator first.")
    with open(meta_path, "r") as f:
        return json.load(f)

def list_batch_files(data_dir: str):
    files = sorted([os.path.join(data_dir, f) for f in os.listdir(data_dir) 
                    if f.startswith("batch_") and f.endswith(".pt")])
    if not files:
        raise FileNotFoundError(f"No batch_*.pt files found in {data_dir}")
    return files

def load_batch_as_kjt(batch_path: str, sparse_dim: int, device: torch.device):
    data = torch.load(batch_path, map_location="cpu")
    if isinstance(data, dict):
        dense = data["dense"].to(device)
        sparse = data["sparse"].long()
        values = sparse.reshape(-1).to(device)
        lengths = torch.ones(sparse.numel(), dtype=torch.int32).to(device)
    else:
        dense, sparse = data
        dense = dense.to(device)
        sparse = sparse.long()
        values = sparse.reshape(-1).to(device)
        lengths = torch.ones(sparse.numel(), dtype=torch.int32).to(device)
    keys = [f"f_{i}" for i in range(sparse_dim)]
    kjt = KeyedJaggedTensor.from_lengths_sync(keys=keys, values=values, lengths=lengths)
    return dense, kjt

def main(data_dir: str, iterations: int, threads: int):
    torch.set_num_threads(threads)
    print(f"Using CPU threads: {threads}")

    meta = load_metadata(data_dir)
    print(f"Loaded metadata: {meta}")
    batch_size = int(meta["batch_size"])
    dense_dim = int(meta["dense_dim"])
    sparse_dim = int(meta["sparse_dim"])
    num_embeddings = int(meta["num_embeddings"])

    device = torch.device("cpu")

    # Build DLRM model
    embedding_dim = dense_dim
    tables = [
        EmbeddingBagConfig(
            name=f"t_{i}",
            embedding_dim=embedding_dim,
            num_embeddings=num_embeddings,
            feature_names=[f"f_{i}"],
        ) for i in range(sparse_dim)
    ]
    ebc = EmbeddingBagCollection(tables=tables, device=device)
    model = DLRM(
        embedding_bag_collection=ebc,
        dense_in_features=dense_dim,
        dense_arch_layer_sizes=[max(512, 2 * dense_dim), dense_dim, embedding_dim],
        over_arch_layer_sizes=[max(512, 2 * dense_dim), dense_dim, 1]
    ).to(device)
    model.eval()

    batch_files = list_batch_files(data_dir)
    print(f"Found {len(batch_files)} batch files.")

    # Warm-up on first batch
    dense, kjt = load_batch_as_kjt(batch_files[0], sparse_dim, device)
    with torch.no_grad():
        _ = model(dense, kjt)
    del dense, kjt

    # Benchmark
    start_time = time.time()
    for it in range(iterations):
        f = batch_files[it % len(batch_files)]
        dense, kjt = load_batch_as_kjt(f, sparse_dim, device)
        with torch.no_grad():
            _ = model(dense, kjt)
        del dense, kjt  # immediately free memory
    end_time = time.time()

    total_time = end_time - start_time
    avg_time = total_time / iterations

    print("="*50)
    print("DLRM CPU Inference Benchmark Completed")
    print(f"Batch size: {batch_size}, Dense dim: {dense_dim}, Sparse dim: {sparse_dim}, Num embeddings: {num_embeddings}")
    print(f"Iterations: {iterations}, Threads: {threads}")
    print(f"Total time: {total_time:.4f}s, Average per iteration: {avg_time:.6f}s")
    print("="*50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DLRM CPU Inference Benchmark (Low memory, high CPU load)")
    parser.add_argument("--data_dir", type=str, default="./data", help="Directory containing pre-generated batches and metadata.json")
    parser.add_argument("--iterations", type=int, default=50, help="Number of iterations (can be > number of batches)")
    parser.add_argument("--threads", type=int, default=1, help="Number of CPU threads to use")
    args = parser.parse_args()

    main(args.data_dir, args.iterations, args.threads)
