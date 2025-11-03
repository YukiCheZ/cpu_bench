#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
import time
from multiprocessing import Process, cpu_count

def run_ffmpeg_instance(instance_id, cpu_core, input_file, ffmpeg_bin, scale, fps):
    """
    Run a single FFmpeg process pinned to a specific CPU core with CPU-intensive filter chain
    """
    filter_chain = (
        f"scale={scale},"
        f"gblur=sigma=5.0,"
        "split=2[a][b];"
        "[a]unsharp=5:5:1.0:5:5:0.0[a1];"
        "[b]gblur=sigma=1[b1];"
        f"[a1][b1]blend=all_mode='addition',fps={fps}"
    )

    cmd = [
        "taskset", "-c", str(cpu_core),
        ffmpeg_bin,
        "-y",
        "-i", input_file,
        "-vf", filter_chain,
        "-f", "null", "-"
    ]

    try:
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print(result.stderr.decode(), file=sys.stderr)
    except Exception as e:
        print(f"[ERROR] Instance {instance_id} execution error: {e}", file=sys.stderr)

def cpu_benchmark(input_file, num_instances, ffmpeg_bin, scale, fps):
    max_cores = cpu_count()
    if num_instances > max_cores:
        print(f"[WARN] Requested {num_instances} instances, but only {max_cores} CPU cores available. Limiting to {max_cores}.")
        num_instances = max_cores

    processes = []
    print(f"[INFO] Starting {num_instances} FFmpeg copies for CPU benchmark...")
    print(f"[INFO] input video transport to scale={scale}, fps={fps}")
    start = time.time()
    for i in range(num_instances):
        p = Process(target=run_ffmpeg_instance,
                    args=(i, i, input_file, ffmpeg_bin, scale, fps))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
    elapsed = time.time() - start
    print(f"[RESULT] Total elapsed time: {elapsed:.4f} s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FFmpeg CPU Benchmark (1 thread per process, multi-instance)")
    parser.add_argument("--input", type=str, default="data/test.mp4", help="Input video file")
    parser.add_argument("--threads", type=int, default=1, help="Number of FFmpeg instances to run in parallel")
    parser.add_argument("--scale", type=str, default="1920:1080", help="Video scale, e.g., 1280:720")
    parser.add_argument("--fps", type=int, default=160, help="Output frame rate")
    parser.add_argument("--ffmpeg-bin", type=str, default="./bin/ffmpeg_install/bin/ffmpeg", help="Path to ffmpeg executable (default: ./bin/ffmpeg_install/bin/ffmpeg)")

    args = parser.parse_args()

    if not os.path.isfile(args.ffmpeg_bin):
        print(f"[ERROR] FFmpeg executable not found at {args.ffmpeg_bin}", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(args.input):
        print(f"[ERROR] Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    cpu_benchmark(args.input, args.threads, args.ffmpeg_bin, args.scale, args.fps)
