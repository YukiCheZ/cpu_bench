#!/usr/bin/env python3
import argparse
import os
import json
import shutil

def main():
    parser = argparse.ArgumentParser(description="Generate data for TUF CPU Benchmark")
    parser.add_argument("--size", type=int, default=536870912,
                        help="Total target data size in bytes")
    parser.add_argument("--meta", type=int, default=10, help="Number of metadata files")
    parser.add_argument("--targets", type=int, default=5, help="Number of target files")
    parser.add_argument("--output", type=str, default="./data",
                        help="Output directory for generated data")
    args = parser.parse_args()

    if os.path.exists(args.output):
        for fname in os.listdir(args.output):
            fpath = os.path.join(args.output, fname)
            if os.path.isfile(fpath) or os.path.islink(fpath):
                os.remove(fpath)
            elif os.path.isdir(fpath):
                shutil.rmtree(fpath)
    else:
        os.makedirs(args.output, exist_ok=True)

    metadata_dict = {
        "signed": {
            "_type": "root",
            "spec_version": "1.0.0",
            "version": 1,
            "expires": "2030-01-01T00:00:00Z",
            "keys": {},
            "roles": {
                "root": {"keyids": [], "threshold": 1},
                "targets": {"keyids": [], "threshold": 1},
                "snapshot": {"keyids": [], "threshold": 1},
                "timestamp": {"keyids": [], "threshold": 1},
            },
            "consistent_snapshot": False
        },
        "signatures": []
    }
    metadata_bytes = json.dumps(metadata_dict).encode("utf-8")

    for i in range(args.meta):
        with open(os.path.join(args.output, f"meta{i}.json"), "wb") as f:
            f.write(metadata_bytes)

    seed = b"x" * 1024
    target_size = max(args.size // args.targets, 1)
    for i in range(args.targets):
        info = {"target_size": target_size}
        with open(os.path.join(args.output, f"file{i}.bin"), "wb") as f:
            f.write(seed)
        with open(os.path.join(args.output, f"file{i}.meta.json"), "w") as f:
            json.dump(info, f)

    print(f"[INFO] Cleared {args.output} and generated {args.meta} metadata files, {args.targets} target seeds")
    print(f"[INFO] Virtual target size per file ~ {target_size} bytes (expanded in runtime)")

if __name__ == "__main__":
    main()
