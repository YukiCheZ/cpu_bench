#include "data_manager.hpp"

DataManager::DataManager(int seed) : seed_(seed) {}

std::vector<cv::Mat> DataManager::generateDataset(const std::string& workload, int size, int numItems) {
    cv::RNG rng(seed_);
    std::vector<cv::Mat> dataset;
    dataset.reserve(numItems);

    if (workload == "matmul") {
        for (int i = 0; i < numItems; ++i) {
            cv::Mat mat(size, size, CV_32F);
            rng.fill(mat, cv::RNG::UNIFORM, 0.f, 1.f);
            dataset.push_back(mat);
        }
    } else {
        for (int i = 0; i < numItems; ++i) {
            cv::Mat img(size, size, CV_8UC3);
            rng.fill(img, cv::RNG::UNIFORM, 0, 256);
            dataset.push_back(img);
        }
    }

    return dataset;
}
