#pragma once
#include <opencv2/opencv.hpp>
#include <string>

class Workloads {
public:
    static void processImage(const cv::Mat& img, const std::string& workload);

private:
    static void canny(const cv::Mat& img);
    static void blurLargeKernel(const cv::Mat& img);
    static void resizeImage(const cv::Mat& img);
    static void sobelEdges(const cv::Mat& img);
    static void histEqualization(const cv::Mat& img);
    static void matrixMultiply(const cv::Mat& img);
    static void colorSpaceAndHistogram(const cv::Mat& img);
    static void customConvolution(const cv::Mat& img);
    static void pyramidProcessing(const cv::Mat& img);
    static void thresholdAndBitwise(const cv::Mat& img);
    static void addRandomNoise(const cv::Mat& img);
};
