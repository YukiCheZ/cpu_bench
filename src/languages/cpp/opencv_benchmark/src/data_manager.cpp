#include "data_manager.hpp"
#include <opencv2/core.hpp>

DataManager::DataManager(int seed) : seed_(seed) {}

std::vector<cv::Mat> DataManager::generateDataset(int imgSize, int numImages) {
    cv::RNG rng(seed_);
    std::vector<cv::Mat> dataset;
    dataset.reserve(numImages);
    for (int i = 0; i < numImages; ++i) {
        cv::Mat img(imgSize, imgSize, CV_8UC3);
        rng.fill(img, cv::RNG::UNIFORM, 0, 256);
        dataset.push_back(img);
    }
    return dataset;
}
