#include "data_manager.hpp"
#include <opencv2/opencv.hpp>

DataManager::DataManager(int seed) : seed_(seed) {}

std::vector<cv::Mat> DataManager::generateDataset(const std::string& workload, int size, int numItems) {
    cv::RNG rng(seed_);
    std::vector<cv::Mat> dataset;
    dataset.reserve(numItems);

    if (size <= 0 || numItems <= 0)
        return dataset;

    if (workload == "jacobi") {
        for (int i = 0; i < numItems; ++i) {
            cv::Mat mat(size, size, CV_32F);
            rng.fill(mat, cv::RNG::UNIFORM, 0.f, 1.f);
            dataset.push_back(mat);
        }
    }
    else if (workload == "fft_batch") {
        for (int i = 0; i < numItems; ++i) {
            cv::Mat gray(size, size, CV_32F);
            rng.fill(gray, cv::RNG::UNIFORM, 0.f, 255.f);
            dataset.push_back(gray);
        }
    }
    else {
        for (int i = 0; i < numItems; ++i) {
            cv::Mat img(size, size, CV_8UC3);
            rng.fill(img, cv::RNG::UNIFORM, 0, 256);
            dataset.push_back(img);
        }
    }

    return dataset;
}
