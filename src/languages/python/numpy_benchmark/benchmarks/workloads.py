# workloads.py
import time
import numpy as np

class NumpyWorkloads:
    @staticmethod
    def matmul(data, iterations=1):
        A, B = data['A'], data['B']

        start = time.perf_counter()
        result = None
        for i in range(iterations):
            result = A @ (B + (i * 1e-12))
        elapsed = time.perf_counter() - start

        return elapsed, np.linalg.norm(result)

    @staticmethod
    def svd(data, iterations=1):
        M = data['M']

        start = time.perf_counter()
        U = s = Vh = None
        for i in range(iterations):
            U, s, Vh = np.linalg.svd(M + (i * 1e-12))
        elapsed = time.perf_counter() - start

        return elapsed, np.linalg.norm(s)

    @staticmethod
    def fft(data, iterations=1):
        signal = data['signal']

        start = time.perf_counter()
        result = None
        for i in range(iterations):
            result = np.fft.fft(signal + (i * 1e-12))
        elapsed = time.perf_counter() - start

        return elapsed, np.linalg.norm(result)
