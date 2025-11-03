#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os

def generate_video(output, resolution, duration, framerate, ffmpeg_bin):

    if not os.path.isfile(ffmpeg_bin):
        print(f"[ERROR] FFmpeg executable not found at {ffmpeg_bin}", file=sys.stderr)
        sys.exit(1)

    output_dir = os.path.dirname(output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    input_filter =  f"testsrc=size={resolution}:rate={framerate}"

    cmd = [
        ffmpeg_bin,
        "-y",  # overwrite output
        "-f", "lavfi",
        "-i", input_filter,
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        output
    ]

    print("[INFO] Running command:", " ".join(cmd))

    env = os.environ.copy()
    try:
        result = subprocess.run(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print("[ERROR] FFmpeg failed", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"[DATA] Video successfully generated: {output}")
    except Exception as e:
        print(f"[ERROR] FFmpeg execution failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate test video using FFmpeg")
    parser.add_argument("--output", type=str, default="data/test.mp4", help="Output file name")
    parser.add_argument("--resolution", type=str, default="1280x720", help="Video resolution, e.g., 1280x720, 1920x1080, 3840x2160")
    parser.add_argument("--duration", type=int, default=480, help="Duration in seconds")
    parser.add_argument("--framerate", type=int, default=10, help="Frame rate (fps)")
    parser.add_argument("--ffmpeg-bin", type=str, default="./bin/ffmpeg_install/bin/ffmpeg", help="Path to ffmpeg executable (default: ./bin/bin/ffmpeg)")

    args = parser.parse_args()
    generate_video(args.output, args.resolution, args.duration, args.framerate, args.ffmpeg_bin)
