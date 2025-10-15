import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""
import torch
import torchvision.models as models
import torch.nn as nn
import torch.optim as optim
import time
import argparse

def get_data_files(data_dir):
    """Return a sorted list of .pt files in the data directory"""
    file_list = sorted([os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".pt")])
    return file_list

def main(data_dir, num_threads, lr, iters, use_compile):
    # Set CPU threads
    torch.set_num_threads(num_threads)
    print(f"[INFO] Using CPU threads: {torch.get_num_threads()}")

    # Initialize model
    model = models.resnet50(weights=None).train().to("cpu")

    if use_compile:
        # Compile model using PyTorch 2.x torch.compile
        print("[INFO] Compiling ResNet50 model with torch.compile (PyTorch 2.x)...")
        model = torch.compile(model)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=lr)

    # Get list of pre-generated data files
    file_list = get_data_files(data_dir)
    print(f"[INFO] Found {len(file_list)} batches in {data_dir}")

    # Warm-up using the first batch
    inputs, labels = torch.load(file_list[0])
    inputs = inputs.to(torch.float32)
    optimizer.zero_grad()
    outputs = model(inputs)
    loss = criterion(outputs, labels)
    loss.backward()
    optimizer.step()

    print(f"[INFO] Starting CPU training benchmark for {iters} iterations...")
    iteration_times = []

    for r in range(iters):
        for i, file_path in enumerate(file_list):
            inputs, labels = torch.load(file_path)
            inputs = inputs.to(torch.float32)

            start_time = time.time()
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            end_time = time.time()

            iter_time = end_time - start_time
            iteration_times.append(iter_time)

            del inputs, labels  # free memory

    total_time = sum(iteration_times)

    print("="*50)
    print("[INFO] ResNet50 CPU Training Benchmark Completed")
    print(f"[INFO] Total iterations: {len(iteration_times)} (Rounds={iters}, Batches={len(file_list)})")
    print(f"[RESULT] Total elapsed time: {total_time:.4f} s")
    print("="*50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ResNet50 CPU training from pre-generated data (on-demand batch loading)")
    parser.add_argument("--data_dir", type=str, default="./data", help="Directory containing pre-generated data")
    parser.add_argument("--threads", type=int, default=1, help="Number of CPU threads to use")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--iters", type=int, default=20, help="Number of benchmark iterations (each runs all batches)")
    parser.add_argument("--compile", action="store_true", help="Use torch.compile (PyTorch 2.x only)")
    args = parser.parse_args()

    main(args.data_dir, args.threads, args.lr, args.iters, args.compile)
