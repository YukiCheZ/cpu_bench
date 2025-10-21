#!/usr/bin/env python3
import argparse
import pickle
import time
import random
from concurrent.futures import ProcessPoolExecutor, as_completed
from chaosgame_core import Chaosgame

def worker(task_args):
    width, height, iterations, thickness, rng_seed, splines, start_point = task_args
    random.seed(rng_seed)
    chaos = Chaosgame(splines, thickness)
    point = start_point
    for _ in range(iterations):
        point = chaos.transform_point(point)
    return True  

def run_once(params, threads, base_seed):
    seeds = [base_seed + i for i in range(threads)]
    tasks = []
    for i in range(threads):
        tasks.append((
            params["width"], params["height"], params["iterations"],
            params["thickness"], seeds[i],
            params["splines"], params["start_point"]
        ))
    with ProcessPoolExecutor(max_workers=threads) as ex:
        futures = [ex.submit(worker, t) for t in tasks]
        for f in as_completed(futures):
            f.result()

def main():
    parser = argparse.ArgumentParser(description="Chaosgame benchmark (load pre-generated data)")
    parser.add_argument("--input", type=str, default="data/chaos_input.pkl")
    parser.add_argument("--iters", type=int, default=1)
    parser.add_argument("--threads", type=int, default=1)
    args = parser.parse_args()

    with open(args.input, "rb") as f:
        params = pickle.load(f)

    print(f"[INFO] Loaded chaos input from {args.input}")

    times = []
    for outer in range(args.iters):
        start = time.perf_counter()
        run_once(params, args.threads, params["rng_seed"] + outer)
        end = time.perf_counter()
        elapsed = end - start
        times.append(elapsed)

    print(f"[RESULT] Total elapsed time: {sum(times):.4f} s")

if __name__ == "__main__":
    main()
