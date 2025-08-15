#include "data_manager.hpp"
#include "workloads.hpp"
#include <iostream>
#include <thread>
#include <vector>
#include <chrono>

#ifndef RANDOM_SEED
#define RANDOM_SEED 42
#endif

int main(int argc, char* argv[]) {
    int copies = 1;
    int iterations = 5;
    int warmup = 2; 
    int imgSize = 1024;
    int numImages = 100;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--copies" && i + 1 < argc) copies = std::stoi(argv[++i]);
        else if (arg == "--iterations" && i + 1 < argc) iterations = std::stoi(argv[++i]);
        else if (arg == "--warmup" && i + 1 < argc) warmup = std::stoi(argv[++i]);
        else if (arg == "--size" && i + 1 < argc) imgSize = std::stoi(argv[++i]);
        else if (arg == "--images" && i + 1 < argc) numImages = std::stoi(argv[++i]);
    }

    std::cout << "[Info] Copies: " << copies 
              << ", Iterations: " << iterations
              << ", Warmup: " << warmup
              << ", Image size: " << imgSize 
              << ", Num images: " << numImages << std::endl;

    cv::setNumThreads(1);
    cv::setUseOptimized(true);

    DataManager dm(RANDOM_SEED);
    auto dataset = dm.generateDataset(imgSize, numImages);

    std::vector<std::thread> threads;
    std::vector<double> results(copies, 0.0);

    auto total_start = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < copies; ++i) {
        threads.emplace_back([&, i]() {
            // -----------------------------
            // Warmup 
            // -----------------------------
            for (int w = 0; w < warmup; ++w) {
                for (const auto& img : dataset) {
                    Workloads::processImage(img);
                }
            }

            // -----------------------------
            // time
            // -----------------------------
            auto start = std::chrono::high_resolution_clock::now();
            for (int iter = 0; iter < iterations; ++iter) {
                for (const auto& img : dataset) {
                    Workloads::processImage(img);
                }
            }
            auto end = std::chrono::high_resolution_clock::now();

            results[i] = std::chrono::duration<double>(end - start).count();
            std::cout << "[Worker " << i << "] Finished in " << results[i] << " sec" << std::endl;
        });
    }

    for (auto& t : threads) t.join();

    auto total_end = std::chrono::high_resolution_clock::now();
    double total_time = std::chrono::duration<double>(total_end - total_start).count();

    double avg_time = 0.0;
    for (auto t : results) avg_time += t;
    avg_time /= copies;

    std::cout << "[Result] Average time per copy: " << avg_time << " sec" << std::endl;
    std::cout << "[Result] Total wall-clock time: " << total_time << " sec" << std::endl;

    return 0;
}
