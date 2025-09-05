import torch
import torchvision.models as models
import torch.nn as nn
import torch.optim as optim
import time
import os
import argparse

def get_data_files(data_dir):
    """Return a sorted list of .pt files in the data directory"""
    file_list = sorted([os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".pt")])
    return file_list

def main(data_dir, num_threads, lr):
    # Set CPU threads
    torch.set_num_threads(num_threads)
    print(f"Using CPU threads: {torch.get_num_threads()}")

    # Initialize model
    model = models.resnet50(weights=None).train().to("cpu")
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=lr)

    # Get list of pre-generated data files
    file_list = get_data_files(data_dir)
    print(f"Found {len(file_list)} batches in {data_dir}")

    # Warm-up using the first batch
    inputs, labels = torch.load(file_list[0])
    optimizer.zero_grad()
    outputs = model(inputs)
    loss = criterion(outputs, labels)
    loss.backward()
    optimizer.step()

    print(f"Starting CPU training benchmark...")
    iteration_times = []

    for i, file_path in enumerate(file_list):
        # Load batch on demand
        inputs, labels = torch.load(file_path)

        start_time = time.time()
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        end_time = time.time()

        iter_time = end_time - start_time
        iteration_times.append(iter_time)
        print(f"Iteration {i+1}/{len(file_list)} - Time: {iter_time:.4f} s")

        # Optionally free memory immediately
        del inputs, labels

    total_time = sum(iteration_times)
    avg_time = total_time / len(file_list)

    print("="*50)
    print("ResNet50 CPU Training Benchmark Completed")
    print(f"Total iterations: {len(file_list)}")
    print(f"Total time: {total_time:.4f} s")
    print(f"Average time per iteration: {avg_time:.4f} s")
    print("="*50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ResNet50 CPU training from pre-generated data (on-demand batch loading)")
    parser.add_argument("--data_dir", type=str, default="./data", help="Directory containing pre-generated data")
    parser.add_argument("--threads", type=int, default=1, help="Number of CPU threads to use")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    args = parser.parse_args()

    main(args.data_dir, args.threads, args.lr)
