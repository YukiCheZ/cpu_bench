import torch
from transformers import BertModel, BertConfig
import time
import os
import argparse

def get_data_files(data_dir):
    """Return sorted list of .pt files in data directory"""
    return sorted([os.path.join(data_dir, f) for f in os.listdir(data_dir) if f.endswith(".pt")])

def main(data_dir, num_threads):
    # Set CPU threads
    torch.set_num_threads(num_threads)
    print(f"[INFO] Using CPU threads: {torch.get_num_threads()}")

    # Find data files
    file_list = get_data_files(data_dir)
    print(f"[INFO] Found {len(file_list)} batches in {data_dir}")

    if len(file_list) == 0:
        print("[ERROR] No data found in data_dir.")
        return

    # Load first batch to get sequence length and batch size
    input_ids, attention_mask = torch.load(file_list[0])
    batch_size, seq_len = input_ids.shape

    # Initialize BERT model with matching max_position_embeddings
    config = BertConfig(max_position_embeddings=seq_len)
    model = BertModel(config).eval().to("cpu")

    # Warm-up
    with torch.no_grad():
        _ = model(input_ids=input_ids, attention_mask=attention_mask)

    # Run inference for each batch
    iteration_times = []
    for i, file_path in enumerate(file_list):
        input_ids, attention_mask = torch.load(file_path)
        start_time = time.time()
        with torch.no_grad():
            _ = model(input_ids=input_ids, attention_mask=attention_mask)
        end_time = time.time()
        iter_time = end_time - start_time
        iteration_times.append(iter_time)
        del input_ids, attention_mask  # free memory

    total_time = sum(iteration_times)
    avg_time = total_time / len(file_list)

    print("="*50)
    print("[INFO] BERT CPU Inference Benchmark Completed")
    print(f"[INFO] Total batches: {len(file_list)}")
    print(f"[RESULT] Total time: {total_time:.4f} seconds")
    print("="*50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BERT CPU inference from pre-generated data")
    parser.add_argument("--data_dir", type=str, default="./data", help="Directory containing pre-generated data")
    parser.add_argument("--threads", type=int, default=1, help="Number of CPU threads to use")
    args = parser.parse_args()

    main(args.data_dir, args.threads)
