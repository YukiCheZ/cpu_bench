#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
import time

def cpu_benchmark(input_file, threads, ffmpeg_bin, scale, blur_sigma, fps):
    """
    Run a CPU-intensive FFmpeg benchmark with multiple operations:
    1. Decode input
    2. Apply video filters (scale + gaussian blur + fps)
    3. Re-encode to H.265
    """
    if not ffmpeg_bin:
        ffmpeg_bin = "./bin/bin/ffmpeg"

    if not os.path.isfile(ffmpeg_bin):
        print(f"[ERROR] FFmpeg executable not found at {ffmpeg_bin}", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(input_file):
        print(f"[ERROR] Input file not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    output_file = "temp_output.mp4"

    # Construct filter chain
    filter_chain = f"scale={scale},gblur=sigma={blur_sigma},fps={fps}"

    cmd = [
        "taskset", "-c", ",".join(str(i) for i in range(threads)),
        ffmpeg_bin,
        "-y",
        "-i", input_file,
        "-vf", filter_chain,
        "-c:v", "libx265",
        "-preset", "ultrafast",
        "-f", "mp4",
        output_file
    ]

    print(f"[INFO] Running benchmark with {threads} threads...")
    print("[INFO] Command:", " ".join(cmd))

    start_time = time.time()
    try:
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        elapsed_time = time.time() - start_time

        if result.returncode != 0:
            print("[ERROR] FFmpeg benchmark failed", file=sys.stderr)
            print(result.stderr.decode(), file=sys.stderr)
            sys.exit(1)
        else:
            print(f"[RESULT] Total elapsed time: {elapsed_time:.4f} s")
    finally:
        if os.path.exists(output_file):
            os.remove(output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FFmpeg CPU Multi-operation Benchmark")
    parser.add_argument("--input", type=str, default="data/test.mp4", help="Input video file")
    parser.add_argument("--threads", type=int, default=1, help="Number of threads to use")
    parser.add_argument("--scale", type=str, default="1280:720", help="Video scale, e.g., 1280:720")
    parser.add_argument("--blur-sigma", type=float, default=5.0, help="Gaussian blur sigma")
    parser.add_argument("--fps", type=int, default=30, help="Output frame rate")
    parser.add_argument("--ffmpeg-bin", type=str, default=None, help="Path to ffmpeg executable (default: ./bin/bin/ffmpeg)")

    args = parser.parse_args()
    cpu_benchmark(args.input, args.threads, args.ffmpeg_bin, args.scale, args.blur_sigma, args.fps)
