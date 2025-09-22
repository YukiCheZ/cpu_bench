#!/usr/bin/env python3
# transformer_cpu_training_benchmark.py
import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
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

def main(data_dir, iterations, threads, num_encoder_layers, num_decoder_layers, d_model, nhead, dim_feedforward, lr):
    torch.set_num_threads(threads)
    device = torch.device("cpu")
    print(f"[INFO] Running Transformer CPU Training Benchmark with {threads} threads")

    # load dataset metadata
    meta = load_metadata(data_dir)
    batch_size = meta["batch_size"]
    seq_len = meta["seq_len"]
    vocab_size = meta["vocab_size"]

    print(f"[INFO] Loaded metadata: batch_size={batch_size}, seq_len={seq_len}, d_model={d_model}, vocab_size={vocab_size}")

    # build model
    model = nn.Transformer(
        d_model=d_model,
        nhead=nhead,
        num_encoder_layers=num_encoder_layers,
        num_decoder_layers=num_decoder_layers,
        dim_feedforward=dim_feedforward,
        batch_first=True
    ).to(device)

    src_embedding = nn.Embedding(vocab_size, d_model).to(device)
    tgt_embedding = nn.Embedding(vocab_size, d_model).to(device)
    output_proj = nn.Linear(d_model, vocab_size).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(list(model.parameters()) + list(src_embedding.parameters()) +
                           list(tgt_embedding.parameters()) + list(output_proj.parameters()), lr=lr)

    batch_files = list_batch_files(data_dir)
    print(f"Found {len(batch_files)} batch files.")

    # warmup
    src, tgt, target = torch.load(batch_files[0], map_location="cpu")
    with torch.no_grad():
        out = model(src_embedding(src), tgt_embedding(tgt))
        _ = output_proj(out)

    # training loop: each iteration runs all batches
    start_time = time.time()
    for it in range(iterations):
        for f in batch_files:
            src, tgt, target = torch.load(f, map_location="cpu")
            src_emb = src_embedding(src)
            tgt_emb = tgt_embedding(tgt)
            optimizer.zero_grad()
            out = model(src_emb, tgt_emb)
            logits = output_proj(out)
            loss = criterion(logits.view(-1, vocab_size), target.view(-1))
            loss.backward()
            optimizer.step()
    end_time = time.time()

    total_time = end_time - start_time

    print("="*50)
    print("[INFO] Transformer CPU Training Benchmark Completed")
    print(f"[INFO] Encoder={num_encoder_layers}, Decoder={num_decoder_layers}, nhead={nhead}, ff={dim_feedforward}")
    print(f"[INFO] Batch={batch_size}, SeqLen={seq_len}, d_model={d_model}, Vocab={vocab_size}")
    print(f"[INFO] Iterations={iterations}, Num batches per iteration={len(batch_files)}")
    print(f"[INFO] Threads={threads}, LR={lr}")
    print(f"[RESULT] Total={total_time:.4f}s")
    print("="*50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transformer CPU Training Benchmark (Encoder + Decoder)")
    parser.add_argument("--data_dir", type=str, default="./data", help="Directory with pre-generated batches")
    parser.add_argument("--iterations", type=int, default=1, help="Number of training iterations")
    parser.add_argument("--threads", type=int, default=1, help="CPU threads")
    parser.add_argument("--num_encoder_layers", type=int, default=12, help="Number of encoder layers")
    parser.add_argument("--num_decoder_layers", type=int, default=12, help="Number of decoder layers")
    parser.add_argument("--d_model", type=int, default=512, help="Embedding dimension")
    parser.add_argument("--nhead", type=int, default=16, help="Number of attention heads")
    parser.add_argument("--dim_feedforward", type=int, default=4096, help="Feedforward hidden size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    args = parser.parse_args()

    main(args.data_dir, args.iterations, args.threads, args.num_encoder_layers,
         args.num_decoder_layers, args.d_model, args.nhead, args.dim_feedforward, args.lr)
