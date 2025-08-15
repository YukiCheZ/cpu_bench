#pragma once
#include <opencv2/opencv.hpp>
#include <vector>
#include <string>

class DataManager {
public:
    DataManager(int seed = 42);

    std::vector<cv::Mat> generateDataset(const std::string& workload, int size, int numItems);

private:
    int seed_;
};
