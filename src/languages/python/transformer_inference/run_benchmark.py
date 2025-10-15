#!/usr/bin/env python3
# transformer_cpu_benchmark.py
import os
import json
import torch
import torch.nn as nn
import argparse
import time

def load_metadata(data_dir: str):
    meta_path = os.path.join(data_dir, "metadata.json")
    if not os.path.exists(meta_path):
        raise FileNotFoundError(f"[ERROR] metadata.json not found in {data_dir}. Please run data generator first.")
    with open(meta_path, "r") as f:
        return json.load(f)

def list_batch_files(data_dir: str):
    files = sorted([os.path.join(data_dir, f) for f in os.listdir(data_dir)
                    if f.startswith("batch_") and f.endswith(".pt")])
    if not files:
        raise FileNotFoundError(f"[ERROR] No batch_*.pt files found in {data_dir}")
    return files

def main(data_dir, iters, threads, num_encoder_layers, num_decoder_layers, d_model, nhead, dim_feedforward, use_compile):
    torch.set_num_threads(threads)
    device = torch.device("cpu")
    print(f"[INFO] Running Transformer CPU Inference Benchmark with {threads} threads")

    meta = load_metadata(data_dir)
    batch_size = meta["batch_size"]
    seq_len = meta["seq_len"]
    vocab_size = meta["vocab_size"]
    print(f"[INFO] Loaded metadata: batch_size={batch_size}, seq_len={seq_len}, d_model={d_model}, vocab_size={vocab_size}")

    # Embedding + Transformer
    embedding = nn.Embedding(vocab_size, d_model).to(device)
    transformer = nn.Transformer(
        d_model=d_model,
        nhead=nhead,
        num_encoder_layers=num_encoder_layers,
        num_decoder_layers=num_decoder_layers,
        dim_feedforward=dim_feedforward,
        batch_first=True
    ).to(device)
    embedding.eval()
    transformer.eval()

    if use_compile:
        print("[INFO] Compiling model with torch.compile (PyTorch 2.x)...")
        embedding = torch.compile(embedding)
        transformer = torch.compile(transformer)

    batch_files = list_batch_files(data_dir)
    print(f"[INFO] Found {len(batch_files)} batch files.")

    # Warm-up
    src, tgt = torch.load(batch_files[0], map_location="cpu")
    with torch.no_grad():
        src_emb = embedding(src)
        tgt_emb = embedding(tgt)
        _ = transformer(src_emb, tgt_emb)

    # Benchmark: each iteration runs all batches
    start_time = time.time()
    for it in range(iters):
        for f in batch_files:
            src, tgt = torch.load(f, map_location="cpu")
            with torch.no_grad():
                src_emb = embedding(src)
                tgt_emb = embedding(tgt)
                _ = transformer(src_emb, tgt_emb)
    end_time = time.time()

    total_time = end_time - start_time

    print("="*50)
    print("[INFO] Transformer CPU Inference Benchmark Completed")
    print(f"[INFO] Encoder layers: {num_encoder_layers}, Decoder layers: {num_decoder_layers}, d_model: {d_model}, nhead: {nhead}, dim_feedforward: {dim_feedforward}")
    print(f"[INFO] iters: {iters}, Num batches per iteration: {len(batch_files)}, Threads: {threads}")
    print(f"[RESULT] Total elapsed time: {total_time:.4f} s")
    print("="*50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Full Transformer CPU Inference Benchmark (Encoder + Decoder)")
    parser.add_argument("--data_dir", type=str, default="./data", help="Directory with pre-generated batches")
    parser.add_argument("--iters", type=int, default=1, help="Number of iters")
    parser.add_argument("--threads", type=int, default=1, help="CPU threads")
    parser.add_argument("--num_encoder_layers", type=int, default=24, help="Number of encoder layers")
    parser.add_argument("--num_decoder_layers", type=int, default=24, help="Number of decoder layers")
    parser.add_argument("--d_model", type=int, default=1024, help="Transformer embedding dimension")
    parser.add_argument("--nhead", type=int, default=32, help="Number of attention heads")
    parser.add_argument("--dim_feedforward", type=int, default=4096, help="Feedforward hidden size")
    parser.add_argument("--compile", action="store_true", help="Use torch.compile (PyTorch 2.x only)")
    args = parser.parse_args()

    main(args.data_dir, args.iters, args.threads, args.num_encoder_layers,
         args.num_decoder_layers, args.d_model, args.nhead, args.dim_feedforward, args.compile)
