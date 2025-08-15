#include "data_manager.hpp"
#include "workloads.hpp"
#include <iostream>
#include <thread>
#include <vector>
#include <chrono>
#include <set>
#include <map>

#ifndef RANDOM_SEED
#define RANDOM_SEED 42
#endif

int main(int argc, char* argv[]) {
    int copies = 1;
    int iterations = 5;
    int warmup = 2;
    int imgSize = 1024;
    int numImages = 100;
    std::string workload = "canny";

    const std::map<std::string, std::string> workloadDescriptions = {
        {"canny",              "Grayscale + Gaussian blur + Canny edge detection"},
        {"blur",               "Large-kernel Gaussian blur (21x21)"},
        {"resize",             "Downscale then upscale (bilinear interpolation)"},
        {"sobel",              "Grayscale + Sobel operator gradient"},
        {"hist_eq",            "Grayscale + histogram equalization"},
        {"matmul",             "Matrix multiplied with its transpose (GEMM)"},
        {"color_hist",         "BGR → HSV + color histogram computation"},
        {"conv_custom",        "Custom convolution kernel processing"},
        {"pyramid",            "Image pyramid downsampling + upsampling"},
        {"threshold_bitwise",  "Thresholding + bitwise operations"},
        {"noise",              "Add random Gaussian noise"}
    };


    std::set<std::string> availableWorkloads;
    for (auto& kv : workloadDescriptions) availableWorkloads.insert(kv.first);

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--copies" && i + 1 < argc) copies = std::stoi(argv[++i]);
        else if (arg == "--iterations" && i + 1 < argc) iterations = std::stoi(argv[++i]);
        else if (arg == "--warmup" && i + 1 < argc) warmup = std::stoi(argv[++i]);
        else if (arg == "--size" && i + 1 < argc) imgSize = std::stoi(argv[++i]);
        else if (arg == "--images" && i + 1 < argc) numImages = std::stoi(argv[++i]);
        else if (arg == "--workload" && i + 1 < argc) workload = argv[++i];
        else if (arg == "--list-workloads") {
            std::cout << "Available workloads:\n";
            for (auto& kv : workloadDescriptions) {
                std::cout << "  " << kv.first << "  -  " << kv.second << "\n";
            }
            return 0;
        }
    }

    if (availableWorkloads.find(workload) == availableWorkloads.end()) {
        std::cerr << "[Error] Unknown workload: " << workload << "\n";
        std::cerr << "Use --list-workloads to see all options.\n";
        return 1;
    }

    std::cout << "[Info] Copies: " << copies
              << ", Iterations: " << iterations
              << ", Warmup: " << warmup
              << ", Image size: " << imgSize
              << ", Num images: " << numImages
              << ", Workload: " << workload << std::endl;

    cv::setNumThreads(1);
    cv::setUseOptimized(true);

    DataManager dm(RANDOM_SEED);
    auto dataset = dm.generateDataset(workload, imgSize, numImages);

    std::vector<std::thread> threads;
    std::vector<double> results(copies, 0.0);

    auto total_start = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < copies; ++i) {
        threads.emplace_back([&, i]() {
            // warmup part
            for (int w = 0; w < warmup; ++w) {
                for (const auto& img : dataset) {
                    Workloads::processImage(img, workload);
                }
            }
            // timing part
            auto start = std::chrono::high_resolution_clock::now();
            for (int iter = 0; iter < iterations; ++iter) {
                for (const auto& img : dataset) {
                    Workloads::processImage(img, workload);
                }
            }
            auto end = std::chrono::high_resolution_clock::now();
            results[i] = std::chrono::duration<double>(end - start).count();
            std::cout << "[Worker " << i << "] Finished " << workload
                      << " in " << results[i] << " sec" << std::endl;
        });
    }

    for (auto& t : threads) t.join();

    auto total_end = std::chrono::high_resolution_clock::now();
    double total_time = std::chrono::duration<double>(total_end - total_start).count();
    double avg_time = 0.0;
    for (auto t : results) avg_time += t;
    avg_time /= copies;

    std::cout << "[Result] Average time per copy: " << avg_time << " sec\n";
    std::cout << "[Result] Total wall-clock time: " << total_time << " sec\n";

    return 0;
}
