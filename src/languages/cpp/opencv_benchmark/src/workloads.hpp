#pragma once
#include <opencv2/opencv.hpp>
#include <string>

class Workloads {
public:
    static void processImage(const cv::Mat& img, const std::string& workload);

    static void fftBatch(const cv::Mat& img);
    static void convHeavy(const cv::Mat& img);
    static void mandelbrot();
    static void mandelbrot(int size, int maxIter);
    static void jacobiIter();
    static void jacobiIter(int n, int iters);
    static void canny(const cv::Mat& img);
    static void opticalFlow(const cv::Mat& img);
    static void motionBlur(const cv::Mat& img);
    static void backgroundSub(const cv::Mat& img);
    static void colorTracking(const cv::Mat& img);
    static void featureMatch(const cv::Mat& img);
};
