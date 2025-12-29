#!/usr/bin/env python3
"""
usage:
  python3 gen_json.py --size 10 --seed 42
"""
import argparse
import json
import os
import random
import string
import math

def rand_name(rnd):
    return ''.join(rnd.choices(string.ascii_lowercase, k=8))

def make_child_template(rnd):
    return {
        "name": rand_name(rnd) + "-" + str(rnd.randint(0, 999999)),
        "kids": [],
        "cl_weight": round(rnd.random(), 6),
        "touches": rnd.randint(0, 1000),
        "min_t": rnd.randint(0, 1_000_000),
        "max_t": rnd.randint(1_000_000, 2_000_000),
        "mean_t": rnd.randint(0, 1_000_000),
    }

def main():
    p = argparse.ArgumentParser(description="Generate JSON input file (tree with many kids)")
    p.add_argument("--size", type=float, default=50000, help="target size in KB")
    p.add_argument("--seed", type=int, default=42, help="random seed")
    p.add_argument("--out", type=str, default=None, help="output file path (default ./data/input.json)")
    args = p.parse_args()

    target_bytes = int(args.size * 1024)
    rnd = random.Random(args.seed)
    os.makedirs("data", exist_ok=True)
    out_path = args.out if args.out else f"./data/input.json"

    root_name = "root"
    root_start = '{"username":"user","tree":{"name":"' + root_name + '","kids":['
    root_end = ']}}'

    sample_child = make_child_template(rnd)
    sample_child_json = json.dumps(sample_child, separators=(',',':'), ensure_ascii=False)
    per_child_size = len(sample_child_json)
    per_child_with_comma = per_child_size + 1  

    avail = target_bytes - (len(root_start) + len(root_end))
    if avail <= 0:
        print("Target size too small to hold base JSON structure; writing minimal file.")
        kids_count = 0
    else:
        kids_count = max(0, (avail + 1) // per_child_with_comma)  
    max_nodes = 50_000_000
    if kids_count > max_nodes:
        kids_count = max_nodes

    if kids_count == 0:
        final = root_start + root_end
    else:
        chunk = sample_child_json
        children_str = ','.join([chunk] * kids_count)
        final = root_start + children_str + root_end

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(final)

    actual_size = os.path.getsize(out_path)
    print(f"Generated {out_path}: requested {args.size} KB, actual {(actual_size/1024/1024):.4f} KB, nodes={kids_count}")

if __name__ == "__main__":
    main()
