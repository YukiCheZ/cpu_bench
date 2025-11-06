#include "data_manager.hpp"
#include "workloads.hpp"
#include <opencv2/opencv.hpp>
#include <iostream>
#include <thread>
#include <vector>
#include <chrono>
#include <set>
#include <map>
#include <iomanip>
#include <cstdlib>

#ifndef RANDOM_SEED
#define RANDOM_SEED 42
#endif

void printHelp() {
    std::cout << "Usage: ./opencv_bench [options]\n\n"
              << "Options:\n"
              << "  --threads N        Number of parallel threads (default: 1)\n"
              << "  --iters N          Iterations per copy (default: per workload)\n"
              << "  --warmup N         Warm-up iterations (default: 2)\n"
              << "  --size N           Image size (default per workload)\n"
              << "  --images N         Number of generated images\n"
              << "  --workload NAME    Workload name (see --list-workloads)\n"
              << "  --list-workloads   Show all available workloads\n"
              << "  --help             Show this message\n\n";
}

int main(int argc, char* argv[]) {
    int copies = 1, iterations = -1, warmup = 2;
    int imgSize = -1, numImages = -1;
    std::string workload = "canny";

    const std::map<std::string, std::string> workloadDescriptions = {
        {"fft_batch",   "Batch FFT transform (10x DFT passes)"},
        {"conv_heavy",  "Deep convolution stack (15 Gaussian layers)"},
        {"mandelbrot",  "Mandelbrot fractal computation (float-intensive)"},
        {"jacobi",      "2D Jacobi iteration (Poisson PDE simulation)"},
        {"canny",       "Edge detection baseline"},
        {"optical_flow", "Dense optical flow estimation (Farneback)"},
        {"motion_blur", "Motion blur convolution kernel"},
        {"background_sub", "Background subtraction (MOG2 model)"},
        {"color_tracking", "HSV color threshold + morphology"},
        {"feature_match", "ORB feature detection and matching"}
    };

    const std::map<std::string, std::pair<int,int>> workloadDefaults = {
        {"fft_batch",      {1024, 50}},
        {"conv_heavy",     {1024, 50}},
        {"mandelbrot",     {1024, 50}},
        {"jacobi",         {2048, 50}},
        {"canny",          {2048, 50}},
        {"optical_flow",   {1024, 50}},
        {"motion_blur",    {2048, 50}},
        {"background_sub", {1080, 100}},
        {"color_tracking", {2160, 100}},
        {"feature_match",  {1024, 100}}
    };

    const std::map<std::string, int> workloadDefaultIters = {
        {"fft_batch",       50},
        {"conv_heavy",      25},
        {"mandelbrot",      40},
        {"jacobi",          400},
        {"canny",           150},
        {"optical_flow",    50},
        {"motion_blur",     40},
        {"background_sub",  50},
        {"color_tracking",  200},
        {"feature_match",   120}
    };

    std::set<std::string> availableWorkloads;
    for (auto& kv : workloadDescriptions) availableWorkloads.insert(kv.first);

    // ===== Parse CLI =====
    bool invalidArg = false;
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--threads" && i + 1 < argc) copies = std::stoi(argv[++i]);
        else if (arg == "--iters" && i + 1 < argc) iterations = std::stoi(argv[++i]);
        else if (arg == "--warmup" && i + 1 < argc) warmup = std::stoi(argv[++i]);
        else if (arg == "--size" && i + 1 < argc) imgSize = std::stoi(argv[++i]);
        else if (arg == "--images" && i + 1 < argc) numImages = std::stoi(argv[++i]);
        else if (arg == "--workload" && i + 1 < argc) workload = argv[++i];
        else if (arg == "--list-workloads") {
            std::cout << "Available workloads:\n";
            for (auto& kv : workloadDescriptions)
                std::cout << "  " << std::setw(16) << std::left << kv.first
                          << " - " << kv.second << "\n";
            return 0;
        } else if (arg == "--help") {
            printHelp();
            return 0;
        } else {
            std::cerr << "[Error] Unknown argument: " << arg << "\n";
            invalidArg = true;
            break;
        }
    }

    if (invalidArg) {
        std::cerr << "Use --help to see available options.\n";
        return 1;
    }

    if (availableWorkloads.find(workload) == availableWorkloads.end()) {
        std::cerr << "[Error] Unknown workload: " << workload << "\n";
        std::cerr << "Use --list-workloads to see all options.\n";
        return 1;
    }

    auto def = workloadDefaults.at(workload);
    if (imgSize == -1) imgSize = def.first;
    if (numImages == -1) numImages = def.second;

    auto defItersIt = workloadDefaultIters.at(workload);
    if (iterations == -1) iterations = defItersIt;

    std::cout << "============== OpenCV Benchmark ===============\n";
    std::cout << "Workload: " << workload << "\n";
    std::cout << "Description: " << workloadDescriptions.at(workload) << "\n";
    std::cout << "Copies: " << copies << " | Iterations: " << iterations
              << " | Warmup: " << warmup << "\n";
    std::cout << "Image Size: " << imgSize << " | Images: " << numImages << "\n";

    cv::setNumThreads(1);
    cv::setUseOptimized(true);

    // ===== Prepare dataset =====
    DataManager dm(RANDOM_SEED);
    auto dataset = dm.generateDataset(workload, imgSize, numImages);
    if (dataset.empty()) {
        std::cerr << "[Error] Dataset is empty, check DataManager logic.\n";
        return 1;
    }

    // ===== Warmup Phase =====
    if (warmup > 0) {
        std::cout << "\n[Warmup] Running " << warmup << " iterations per thread...\n";
        std::vector<std::thread> warmup_threads;
        for (int i = 0; i < copies; ++i) {
            warmup_threads.emplace_back([&, i]() {
                for (int w = 0; w < warmup; ++w)
                    for (const auto& img : dataset)
                        Workloads::processImage(img, workload);
            });
        }
        for (auto& t : warmup_threads) t.join();
    }

    // ===== Benchmark Phase =====
    std::cout << "\n[Benchmark] Running " << iterations << " iterations per thread...\n";

    std::vector<std::thread> threads;
    auto total_start = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < copies; ++i) {
        threads.emplace_back([&, i]() {
            for (int iter = 0; iter < iterations; ++iter)
                for (const auto& img : dataset)
                    Workloads::processImage(img, workload);
        });
    }

    for (auto& t : threads) t.join();

    auto total_end = std::chrono::high_resolution_clock::now();
    double total_time = std::chrono::duration<double>(total_end - total_start).count();

    std::cout << "\n============== Benchmark Results ==============\n";
    std::cout << "[RESULT] Total elapsed time: " << std::fixed << std::setprecision(3)
              << total_time << " s\n";
    std::cout << "===============================================\n";

    return 0;
}
