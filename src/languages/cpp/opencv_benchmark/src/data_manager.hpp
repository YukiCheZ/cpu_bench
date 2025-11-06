#pragma once
#include <opencv2/core.hpp>
#include <string>
#include <vector>

class DataManager {
public:
    explicit DataManager(int seed = 42);
    std::vector<cv::Mat> generateDataset(const std::string& workload, int size, int numItems);

private:
    int seed_;
};
