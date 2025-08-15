#pragma once
#include <opencv2/opencv.hpp>
#include <vector>

class DataManager {
public:
    DataManager(int seed = 42);
    std::vector<cv::Mat> generateDataset(int imgSize, int numImages);

private:
    int seed_;
};
