## Python 

### numpy

NumPy 的很多底层运算（矩阵乘法、SVD、FFT 等）是调用 BLAS/LAPACK 实现的，比如：

Intel MKL

OpenBLAS

Apple Accelerate

这些库默认会使用所有可用 CPU 核心，而不仅仅是单线程。

因此测试单核性能时固定了BLAS线程数为 1 