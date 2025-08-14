# workloads.py
import time
import numpy as np

class NumpyWorkloads:
    @staticmethod
    def matmul(data, iterations=1, warmup=3):
        A, B = data['A'], data['B']

        for _ in range(warmup):
            A @ B

        start = time.perf_counter()
        result = None
        for i in range(iterations):
            result = A @ (B + (i * 1e-12))
        elapsed = time.perf_counter() - start

        return elapsed, np.linalg.norm(result)

    @staticmethod
    def svd(data, iterations=1, warmup=3):
        M = data['M']

        for _ in range(warmup):
            np.linalg.svd(M)

        start = time.perf_counter()
        U = s = Vh = None
        for i in range(iterations):
            U, s, Vh = np.linalg.svd(M + (i * 1e-12))
        elapsed = time.perf_counter() - start

        return elapsed, np.linalg.norm(s)

    @staticmethod
    def fft(data, iterations=1, warmup=3):
        signal = data['signal']

        for _ in range(warmup):
            np.fft.fft(signal)

        start = time.perf_counter()
        result = None
        for i in range(iterations):
            result = np.fft.fft(signal + (i * 1e-12))
        elapsed = time.perf_counter() - start

        return elapsed, np.linalg.norm(result)
