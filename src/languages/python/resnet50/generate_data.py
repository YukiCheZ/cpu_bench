import torch
import os
import argparse
import shutil  

def generate_data(batch_size, img_size, num_batches, output_dir):
    if os.path.exists(output_dir):
        print(f"Removing existing directory: {output_dir}")
        shutil.rmtree(output_dir)

    os.makedirs(output_dir, exist_ok=True)

    for i in range(num_batches):
        inputs = torch.randint(0, 256, (batch_size, 3, img_size, img_size), dtype=torch.uint8)
        labels = torch.randint(0, 1000, (batch_size,))
        file_path = os.path.join(output_dir, f"batch_{i}.pt")
        torch.save((inputs, labels), file_path)
        print(f"Saved {file_path} (uint8)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate random data for ResNet50 CPU inference")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size for each batch")
    parser.add_argument("--img_size", type=int, default=512, help="Input image size (height=width)")
    parser.add_argument("--num_batches", type=int, default=10, help="Number of batches to generate")
    parser.add_argument("--output_dir", type=str, default="./data", help="Directory to save generated data")
    args = parser.parse_args()

    generate_data(args.batch_size, args.img_size, args.num_batches, args.output_dir)
