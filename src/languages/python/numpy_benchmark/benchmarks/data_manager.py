# data_manager.py
import os
import numpy as np
from pathlib import Path

class DataManager:
    def __init__(self, data_dir="data", seed=42, dtype=np.float64):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.seed = seed
        self.dtype = dtype

    def generate_dataset(self, size, dataset_type="matrix"):
        """Generate and load datasets"""
        dtype_name = np.dtype(self.dtype).name
        file_path = self.data_dir / f"{dataset_type}_{size}_{dtype_name}.npz"

        if file_path.exists():
            print(f"[DataManager] Loading existing dataset: {file_path}")
            return dict(np.load(file_path))

        print(f"[DataManager] Generating new dataset: {file_path}")
        np.random.seed(self.seed + os.getpid())  

        if dataset_type == "matrix":
            return self._generate_matrix_data(size, file_path)
        elif dataset_type == "svd":
            return self._generate_svd_data(size, file_path)
        elif dataset_type == "fft":
            return self._generate_fft_data(size, file_path)
        else:
            raise ValueError(f"Unknown dataset_type: {dataset_type}")

    def _generate_matrix_data(self, size, file_path):
        """Generate two matrices A and B"""
        A = np.random.rand(size, size).astype(self.dtype)
        B = np.random.rand(size, size).astype(self.dtype)
        np.savez(file_path, A=A, B=B)
        return dict(np.load(file_path))

    def _generate_svd_data(self, size, file_path):
        """Generate matrix M for SVD"""
        M = np.random.rand(size, size).astype(self.dtype)
        np.savez(file_path, M=M)
        return dict(np.load(file_path))

    def _generate_fft_data(self, size, file_path):
        """Generate 1D signal for FFT"""
        signal = np.random.rand(size).astype(self.dtype)
        np.savez(file_path, signal=signal)
        return dict(np.load(file_path))
