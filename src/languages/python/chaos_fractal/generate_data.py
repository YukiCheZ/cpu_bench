#!/usr/bin/env python3
import os
import argparse
import pickle
from chaosgame_core import _build_splines, Chaosgame, DEFAULT_THICKNESS, DEFAULT_WIDTH, DEFAULT_HEIGHT, DEFAULT_ITERATIONS, DEFAULT_RNG_SEED, GVector

def main():
    parser = argparse.ArgumentParser(description="Generate input for Chaosgame benchmark")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    parser.add_argument("--thickness", type=float, default=DEFAULT_THICKNESS)
    parser.add_argument("--rng-seed", type=int, default=DEFAULT_RNG_SEED)
    parser.add_argument("--output", type=str, default="chaos_input.pkl")
    args = parser.parse_args()

    os.makedirs("data", exist_ok=True)
    output_path = os.path.join("data", args.output)

    splines = _build_splines()
    chaos = Chaosgame(splines, args.thickness)

    input_data = {
        "width": args.width,
        "height": args.height,
        "iterations": args.iterations,
        "thickness": args.thickness,
        "rng_seed": args.rng_seed,
        "splines": splines,
        "start_point": GVector((chaos.maxx + chaos.minx)/2.0,
                               (chaos.maxy + chaos.miny)/2.0, 0.0)
    }

    with open(output_path, "wb") as f:
        pickle.dump(input_data, f)

    print(f"[DATA] Generated chaos input -> {output_path}")

if __name__ == "__main__":
    main()
