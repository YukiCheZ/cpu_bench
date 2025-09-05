#!/usr/bin/env python3
"""
Chaosgame fractal benchmark (multiprocess version)

- Use --iters for number of benchmark repetitions (outer)
- Use --threads to control number of parallel processes (each process does ~iterations/threads work)
- Each outer iteration reports elapsed time; final prints average elapsed time.
"""

import math
import random
import argparse
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Optional, Tuple

DEFAULT_THICKNESS = 0.25
DEFAULT_WIDTH = 4096
DEFAULT_HEIGHT = 4096
DEFAULT_ITERATIONS = 1000000
DEFAULT_RNG_SEED = 1234


class GVector(object):
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def Mag(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def dist(self, other):
        return math.sqrt((self.x - other.x) ** 2
                         + (self.y - other.y) ** 2
                         + (self.z - other.z) ** 2)

    def __add__(self, other):
        if not isinstance(other, GVector):
            raise ValueError("Can't add GVector to " + str(type(other)))
        return GVector(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return self + other * -1

    def __mul__(self, other):
        return GVector(self.x * other, self.y * other, self.z * other)
    __rmul__ = __mul__

    def linear_combination(self, other, l1, l2=None):
        if l2 is None:
            l2 = 1 - l1
        return GVector(self.x * l1 + other.x * l2,
                       self.y * l1 + other.y * l2,
                       self.z * l1 + other.z * l2)


class Spline(object):
    """Class for representing B-Splines and NURBS of arbitrary degree"""

    def __init__(self, points, degree, knots):
        if len(points) > len(knots) - degree + 1:
            raise ValueError("too many control points")
        elif len(points) < len(knots) - degree + 1:
            raise ValueError("not enough control points")
        last = knots[0]
        for cur in knots[1:]:
            if cur < last:
                raise ValueError("knots not strictly increasing")
            last = cur
        self.knots = knots
        self.points = points
        self.degree = degree

    def GetDomain(self):
        return (self.knots[self.degree - 1],
                self.knots[len(self.knots) - self.degree])

    def __call__(self, u):
        dom = self.GetDomain()
        if u < dom[0] or u > dom[1]:
            raise ValueError("Function value not in domain")
        if u == dom[0]:
            return self.points[0]
        if u == dom[1]:
            return self.points[-1]
        I = self.GetIndex(u)
        d = [self.points[I - self.degree + 1 + ii]
             for ii in range(self.degree + 1)]
        U = self.knots
        for ik in range(1, self.degree + 1):
            for ii in range(I - self.degree + ik + 1, I + 2):
                ua = U[ii + self.degree - ik]
                ub = U[ii - 1]
                co1 = (ua - u) / (ua - ub)
                co2 = (u - ub) / (ua - ub)
                index = ii - I + self.degree - ik - 1
                d[index] = d[index].linear_combination(d[index + 1], co1, co2)
        return d[0]

    def GetIndex(self, u):
        dom = self.GetDomain()
        for ii in range(self.degree - 1, len(self.knots) - self.degree):
            if u >= self.knots[ii] and u < self.knots[ii + 1]:
                return ii
        # fallback
        return int(dom[1]) - 1


class Chaosgame(object):
    def __init__(self, splines, thickness=0.1):
        self.splines = splines
        self.thickness = thickness
        self.minx = min([p.x for spl in splines for p in spl.points])
        self.miny = min([p.y for spl in splines for p in spl.points])
        self.maxx = max([p.x for spl in splines for p in spl.points])
        self.maxy = max([p.y for spl in splines for p in splines for p in spl.points]) \
            if False else max([p.y for spl in splines for p in spl.points])
        # the above is a safe expression; keep height/width calculation simple:
        self.height = self.maxy - self.miny
        self.width = self.maxx - self.minx
        self.num_trafos = []
        maxlength = thickness * (self.width / self.height if self.height != 0 else 1.0)
        for spl in splines:
            length = 0.0
            curr = spl(0)
            for i in range(1, 1000):
                last = curr
                t = 1.0 / 999.0 * i
                curr = spl(t)
                length += curr.dist(last)
            self.num_trafos.append(max(1, int(length / maxlength * 1.5)))
        self.num_total = sum(self.num_trafos)

    def get_random_trafo(self):
        r = random.randrange(int(self.num_total) + 1)
        l = 0
        for i in range(len(self.num_trafos)):
            if r >= l and r < l + self.num_trafos[i]:
                return i, random.randrange(self.num_trafos[i])
            l += self.num_trafos[i]
        return len(self.num_trafos) - 1, random.randrange(self.num_trafos[-1])

    def transform_point(self, point, trafo=None):
        x = (point.x - self.minx) / self.width
        y = (point.y - self.miny) / self.height
        if trafo is None:
            trafo = self.get_random_trafo()
        start, end = self.splines[trafo[0]].GetDomain()
        length = end - start
        seg_length = length / self.num_trafos[trafo[0]]
        t = start + seg_length * trafo[1] + seg_length * x
        basepoint = self.splines[trafo[0]](t)
        if t + 1 / 50000.0 > end:
            neighbour = self.splines[trafo[0]](t - 1 / 50000.0)
            derivative = neighbour - basepoint
        else:
            neighbour = self.splines[trafo[0]](t + 1 / 50000.0)
            derivative = basepoint - neighbour
        if derivative.Mag() != 0:
            basepoint.x += derivative.y / derivative.Mag() * (y - 0.5) * self.thickness
            basepoint.y += -derivative.x / derivative.Mag() * (y - 0.5) * self.thickness
        self.truncate(basepoint)
        return basepoint

    def truncate(self, point):
        point.x = max(self.minx, min(point.x, self.maxx))
        point.y = max(self.miny, min(point.y, self.maxy))

    def create_image_chaos(self, w, h, iterations, rng_seed, filename: Optional[str] = None):
        """
        Performs 'iterations' transform steps and optionally writes a PPM file.
        This can be heavy in memory when w*h is large.
        """
        random.seed(rng_seed)
        # allocate image as list of lists (like original)
        im = [[1] * h for _ in range(w)]
        point = GVector((self.maxx + self.minx) / 2.0,
                        (self.maxy + self.miny) / 2.0, 0.0)
        for _ in range(iterations):
            point = self.transform_point(point)
            x = int((point.x - self.minx) / self.width * w)
            y = int((point.y - self.miny) / self.height * h)
            if x >= w:
                x = w - 1
            if y >= h:
                y = h - 1
            im[x][h - y - 1] = 0
        if filename:
            # write ppm (text) as in original
            try:
                with open(filename, "wb") as fp:
                    # P6 binary header
                    fp.write(b"P6\n")
                    fp.write(("%d %d\n255\n" % (w, h)).encode("ascii"))
                    for j in range(h):
                        row = bytearray()
                        for i in range(w):
                            v = im[i][j]
                            c = int(v * 255) & 0xFF
                            row.extend(bytes((c, c, c)))
                        fp.write(row)
            except Exception as e:
                # do not crash the worker just because of output
                print("Warning: failed to write file", filename, ":", e)

# ---------------------------------------------------------------------
# Worker function run in each process
# ---------------------------------------------------------------------
def _build_splines():
    return [
        Spline([
            GVector(1.597350, 3.304460, 0.000000),
            GVector(1.575810, 4.123260, 0.000000),
            GVector(1.313210, 5.288350, 0.000000),
            GVector(1.618900, 5.329910, 0.000000),
            GVector(2.889940, 5.502700, 0.000000),
            GVector(2.373060, 4.381830, 0.000000),
            GVector(1.662000, 4.360280, 0.000000)],
            3, [0, 0, 0, 1, 1, 1, 2, 2, 2]),
        Spline([
            GVector(2.804500, 4.017350, 0.000000),
            GVector(2.550500, 3.525230, 0.000000),
            GVector(1.979010, 2.620360, 0.000000),
            GVector(1.979010, 2.620360, 0.000000)],
            3, [0, 0, 0, 1, 1, 1]),
        Spline([
            GVector(2.001670, 4.011320, 0.000000),
            GVector(2.335040, 3.312830, 0.000000),
            GVector(2.366800, 3.233460, 0.000000),
            GVector(2.366800, 3.233460, 0.000000)],
            3, [0, 0, 0, 1, 1, 1])
    ]


def worker_process_task(task_args: Tuple[int, int, int, float, int, Optional[str], int]) -> bool:
    """
    task_args = (width, height, iterations_chunk, thickness, rng_seed, filename_or_none, part_index)
    Each worker is a separate process; builds its own splines and chaos object.
    """
    width, height, iters_chunk, thickness, rng_seed, filename, part_index = task_args
    # Each process should set its own random seed
    random.seed(rng_seed)
    splines = _build_splines()
    chaos = Chaosgame(splines, thickness)
    outname = None
    if filename:
        # write separate part files to avoid race
        outname = f"{filename}.part{part_index}"
    chaos.create_image_chaos(width, height, iters_chunk, rng_seed, outname)
    return True


# ---------------------------------------------------------------------
# Coordinator: splits work among processes and runs them via ProcessPoolExecutor
# ---------------------------------------------------------------------
def run_once_mp(width: int, height: int, iterations: int, thickness: float,
                rng_seed: int, threads: int, filename: Optional[str]) -> None:
    """
    Dispatch work to 'threads' processes. Each process runs 'iterations' iterations.
    This function blocks until all processes complete.
    """
    if threads <= 0:
        threads = 1

    # prepare seeds for reproducibility (parent generates seeds)
    parent_rand = random.Random(rng_seed)
    seeds = [parent_rand.randint(1, 2**31 - 1) for _ in range(threads)]

    # prepare tasks: each process receives the full `iterations`
    tasks = []
    for i in range(threads):
        tasks.append((width, height, iterations, thickness, seeds[i], filename, i))

    # Use ProcessPoolExecutor to spawn worker processes
    with ProcessPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(worker_process_task, t) for t in tasks]
        # Wait for completion and propagate exceptions if any
        for f in as_completed(futures):
            f.result()


# ---------------------------------------------------------------------
# CLI and main loop: outer iters repetitions and timing
# ---------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Chaos fractal benchmark (multiprocess)")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH,
                        help="Image width (pixels)")
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT,
                        help="Image height (pixels)")
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS,
                        help="Number of inner iterations (points) for the fractal generator)")
    parser.add_argument("--thickness", type=float, default=DEFAULT_THICKNESS,
                        help="Thickness parameter for the chaos algorithm")
    parser.add_argument("--rng-seed", type=int, default=DEFAULT_RNG_SEED,
                        help="Base RNG seed")
    parser.add_argument("--iters", type=int, default=3,
                        help="Number of timed benchmark repetitions (outer)")
    parser.add_argument("--threads", type=int, default=1,
                        help="Number of parallel worker processes")
    args = parser.parse_args()

    # Warmup note: you can run an extra warmup iteration externally if needed
    times = []
    # ensure parent RNG is seeded deterministically (so seeds across iterations can be stable)
    random.seed(args.rng_seed)

    for outer in range(args.iters):
        start = time.perf_counter()
        run_once_mp(args.width, args.height, args.iterations,
                    args.thickness, args.rng_seed + outer, args.threads, None)
        end = time.perf_counter()
        elapsed = end - start
        times.append(elapsed)
        print(f"[ITER {outer + 1}] elapsed time: {elapsed:.6f} seconds")

    avg = sum(times) / len(times) if times else 0.0
    print(f"\n[RESULT] Average elapsed time over {args.iters} iterations: {avg:.6f} seconds")


if __name__ == "__main__":
    main()
