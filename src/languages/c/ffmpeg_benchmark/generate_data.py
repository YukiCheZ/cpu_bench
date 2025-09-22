#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os

def generate_video(output, resolution, duration, framerate, codec, noise, ffmpeg_bin):
    if not ffmpeg_bin:
        ffmpeg_bin = "./bin/bin/ffmpeg"

    if not os.path.isfile(ffmpeg_bin):
        print(f"ERROR: FFmpeg executable not found at {ffmpeg_bin}", file=sys.stderr)
        sys.exit(1)

    output_dir = os.path.dirname(output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    input_filter = f"noise=size={resolution}:rate={framerate}" if noise else f"testsrc=size={resolution}:rate={framerate}"

    cmd = [
        ffmpeg_bin,
        "-y",  # overwrite output
        "-f", "lavfi",
        "-i", input_filter,
        "-t", str(duration),
        "-c:v", codec,
        "-pix_fmt", "yuv420p",
        output
    ]

    print("Running command:", " ".join(cmd))

    env = os.environ.copy()
    try:
        result = subprocess.run(cmd, env=env)
        if result.returncode != 0:
            print("ERROR: FFmpeg failed", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"Video successfully generated: {output}")
    except Exception as e:
        print(f"ERROR: FFmpeg execution failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate test video using FFmpeg")
    parser.add_argument("--output", type=str, default="data/test.mp4", help="Output file name")
    parser.add_argument("--resolution", type=str, default="3840x2160", help="Video resolution, e.g., 1280x720, 1920x1080, 3840x2160")
    parser.add_argument("--duration", type=int, default=360, help="Duration in seconds")
    parser.add_argument("--framerate", type=int, default=120, help="Frame rate (fps)")
    parser.add_argument("--codec", type=str, default="libx264", choices=["libx264", "libx265"], help="Video codec")
    parser.add_argument("--noise", action="store_true", help="Use random noise instead of test pattern (higher CPU load)")
    parser.add_argument("--ffmpeg-bin", type=str, default=None, help="Path to ffmpeg executable (default: ./bin/bin/ffmpeg)")

    args = parser.parse_args()
    generate_video(args.output, args.resolution, args.duration, args.framerate, args.codec, args.noise, args.ffmpeg_bin)
