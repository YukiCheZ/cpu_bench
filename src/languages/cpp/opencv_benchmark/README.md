# CPU Benchmark for OpenCV

本项目是一个基于 OpenCV 的 CPU 负载测试工具，用于评估常见图像处理与矩阵运算在不同 CPU 环境下的性能。
支持多线程拷贝、预热、迭代次数等自定义参数，可方便地进行性能对比和调优。

## 📦 支持的负载（Workloads）

| CLI 参数名             | 对应函数                     | 功能说明                          |
| ------------------- | ------------------------ | ----------------------------- |
| `canny`             | `canny`                  | 灰度化 + 高斯模糊 + Canny 边缘检测       |
| `blur`              | `blurLargeKernel`        | 大核高斯模糊（21×21）模拟重度平滑处理         |
| `resize`            | `resizeImage`            | 缩小再放大（双线性插值）测试缩放性能            |
| `sobel`             | `sobelEdges`             | 灰度化 + Sobel 算子计算梯度并融合         |
| `hist_eq`           | `histEqualization`       | 灰度化 + 直方图均衡化                  |
| `matmul`            | `matrixMultiply`         | 矩阵与转置矩阵相乘，测试 GEMM 性能          |
| `color_hist`        | `colorSpaceAndHistogram` | BGR → HSV 转换 + 计算颜色直方图        |
| `conv_custom`       | `customConvolution`      | 自定义卷积核进行图像卷积运算                |
| `pyramid`           | `pyramidProcessing`      | 图像金字塔降采样（pyrDown）+ 上采样（pyrUp） |
| `threshold_bitwise` | `thresholdAndBitwise`    | 阈值化 + 位运算（按位与）                |
| `noise`             | `addRandomNoise`         | 添加随机高斯噪声到图像                   |

## 🚀 使用方法

编译：

```bash
mkdir build && cd build
cmake ..
make -j
```

运行：

```bash
./cpu_benchmark [参数...]
```

参数说明：

```
--copies <n>       同时运行的线程副本数（默认 1）
--iterations <n>   每个副本运行迭代次数（默认 5）
--warmup <n>       预热迭代次数（默认 2，不计时）
--size <n>         生成图片尺寸（默认 1024）
--images <n>       数据集图片数量（默认 100）
--workload <name>  负载类型（见上表）
```

示例：

```bash
# 单线程跑 canny 负载
./cpu_benchmark --workload canny --size 1024 --images 100 --copies 1 --iterations 5

# 多线程跑矩阵乘法
./cpu_benchmark --workload matmul --copies 4 --iterations 10

# 颜色空间转换 + 直方图
./cpu_benchmark --workload color_hist
```

## 📊 输出示例

```
[Info] Copies: 1, Iterations: 5, Warmup: 2, Image size: 1024, Num images: 100, Workload: canny
[Worker 0] Finished canny in 0.753 sec
[Result] Average time per copy: 0.753 sec
[Result] Total wall-clock time: 0.754 sec
```
