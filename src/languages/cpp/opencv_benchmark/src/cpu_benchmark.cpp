#include <opencv2/opencv.hpp>
#include <iostream>
#include <vector>
#include <thread>
#include <chrono>

// 生成随机图像（8-bit 彩色）
cv::Mat generateRandomImage(int width, int height) {
    cv::Mat img(height, width, CV_8UC3); // 8 位 3 通道
    cv::randu(img, cv::Scalar::all(0), cv::Scalar::all(256)); // [0,255] 随机值
    return img;
}

// 图像处理任务：灰度 + 高斯模糊 + Canny
void processImage(const cv::Mat& img, int thread_id) {
    // 防御性检查，确保是 8 位图
    if (img.depth() != CV_8U) {
        std::cerr << "[Thread " << thread_id << "] Error: Image depth is not CV_8U!" << std::endl;
        return;
    }

    auto start = std::chrono::high_resolution_clock::now();

    cv::Mat gray, blurred, edges;
    cv::cvtColor(img, gray, cv::COLOR_BGR2GRAY); // 转灰度
    cv::GaussianBlur(gray, blurred, cv::Size(7, 7), 1.5);
    cv::Canny(blurred, edges, 50, 150);

    auto end = std::chrono::high_resolution_clock::now();
    double ms = std::chrono::duration<double, std::milli>(end - start).count();
    std::cout << "[Thread " << thread_id << "] Processed one image in " << ms << " ms" << std::endl;
}

int main(int argc, char* argv[]) {
    // 禁用 OpenCV 内部多线程
    cv::setNumThreads(1);
    std::cout << "OpenCV internal threads: " << cv::getNumThreads() << std::endl;

    // 默认参数
    int numImages = 10;
    int imgSize = 1024;
    int numCopies = 4;

    // 解析命令行参数
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--num-images" && i + 1 < argc) numImages = std::stoi(argv[++i]);
        else if (arg == "--img-size" && i + 1 < argc) imgSize = std::stoi(argv[++i]);
        else if (arg == "--num-copies" && i + 1 < argc) numCopies = std::stoi(argv[++i]);
        else {
            std::cerr << "Unknown argument: " << arg << std::endl;
            return -1;
        }
    }

    std::cout << "CPU Benchmark: " 
              << numImages << " images, " 
              << imgSize << "x" << imgSize << ", " 
              << numCopies << " copies/threads." << std::endl;

    // 生成随机图像数据集
    std::vector<cv::Mat> dataset;
    dataset.reserve(numImages);
    for (int i = 0; i < numImages; i++) {
        dataset.push_back(generateRandomImage(imgSize, imgSize));
    }

    // 多线程执行副本
    std::vector<std::thread> threads;
    auto total_start = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < numCopies; i++) {
        threads.emplace_back([&, i]() {
            for (const auto& img : dataset) {
                processImage(img, i);
            }
        });
    }

    for (auto& t : threads) t.join();

    auto total_end = std::chrono::high_resolution_clock::now();
    double total_ms = std::chrono::duration<double, std::milli>(total_end - total_start).count();

    std::cout << "All threads finished. Total elapsed time: " << total_ms << " ms" << std::endl;
    return 0;
}
