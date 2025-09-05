import torch
import os
import argparse

def generate_data(batch_size, seq_len, num_batches, output_dir):
    # 删除已有数据目录，重新生成
    if os.path.exists(output_dir):
        for f in os.listdir(output_dir):
            os.remove(os.path.join(output_dir, f))
    else:
        os.makedirs(output_dir, exist_ok=True)

    for i in range(num_batches):
        input_ids = torch.randint(0, 30522, (batch_size, seq_len))  # BERT vocab_size=30522
        attention_mask = torch.ones(batch_size, seq_len)
        file_path = os.path.join(output_dir, f"batch_{i}.pt")
        torch.save((input_ids, attention_mask), file_path)
        print(f"Saved {file_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate random data for BERT CPU inference")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size for each batch")
    parser.add_argument("--seq_len", type=int, default=1024, help="Sequence length of each input")
    parser.add_argument("--num_batches", type=int, default=3, help="Number of batches to generate")
    parser.add_argument("--output_dir", type=str, default="./data", help="Directory to save generated data")
    args = parser.parse_args()

    generate_data(args.batch_size, args.seq_len, args.num_batches, args.output_dir)
