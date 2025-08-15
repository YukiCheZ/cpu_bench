#include "workloads.hpp"
#include <opencv2/imgproc.hpp>
#include <opencv2/core.hpp>

void Workloads::processImage(const cv::Mat& img, const std::string& workload) {
    if (workload == "canny") canny(img);
    else if (workload == "blur") blurLargeKernel(img);
    else if (workload == "resize") resizeImage(img);
    else if (workload == "sobel") sobelEdges(img);
    else if (workload == "hist_eq") histEqualization(img);
    else if (workload == "matmul") matrixMultiply(img);
    else if (workload == "color_hist") colorSpaceAndHistogram(img);
    else if (workload == "convolution") customConvolution(img);
    else if (workload == "pyramid") pyramidProcessing(img);
    else if (workload == "threshold") thresholdAndBitwise(img);
    else if (workload == "noise") addRandomNoise(img);
    else canny(img);  
}

void Workloads::canny(const cv::Mat& img) {
    cv::Mat gray, blurred, edges;
    cv::cvtColor(img, gray, cv::COLOR_BGR2GRAY);
    cv::GaussianBlur(gray, blurred, cv::Size(7,7), 1.5);
    cv::Canny(blurred, edges, 50, 150);
}

void Workloads::blurLargeKernel(const cv::Mat& img) {
    cv::Mat result;
    cv::GaussianBlur(img, result, cv::Size(21,21), 5.0);
}

void Workloads::resizeImage(const cv::Mat& img) {
    cv::Mat tmp, result;
    cv::resize(img, tmp, cv::Size(), 0.5, 0.5, cv::INTER_LINEAR);
    cv::resize(tmp, result, cv::Size(img.cols, img.rows), 0, 0, cv::INTER_LINEAR);
}

void Workloads::sobelEdges(const cv::Mat& img) {
    cv::Mat gray, grad_x, grad_y, abs_grad_x, abs_grad_y, edges;
    cv::cvtColor(img, gray, cv::COLOR_BGR2GRAY);
    cv::Sobel(gray, grad_x, CV_16S, 1, 0, 3);
    cv::Sobel(gray, grad_y, CV_16S, 0, 1, 3);
    cv::convertScaleAbs(grad_x, abs_grad_x);
    cv::convertScaleAbs(grad_y, abs_grad_y);
    cv::addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0, edges);
}

void Workloads::histEqualization(const cv::Mat& img) {
    cv::Mat gray, hist_eq;
    cv::cvtColor(img, gray, cv::COLOR_BGR2GRAY);
    cv::equalizeHist(gray, hist_eq);
}

void Workloads::matrixMultiply(const cv::Mat& mat) {
    cv::Mat mat32f, result;
    mat.convertTo(mat32f, CV_32F);
    cv::gemm(mat32f, mat32f.t(), 1.0, cv::Mat(), 0.0, result);
}

void Workloads::colorSpaceAndHistogram(const cv::Mat& img) {
    cv::Mat hsv;
    cv::cvtColor(img, hsv, cv::COLOR_BGR2HSV);
    int h_bins = 50, s_bins = 60;
    int histSize[] = {h_bins, s_bins};
    float h_ranges[] = {0, 180};
    float s_ranges[] = {0, 256};
    const float* ranges[] = {h_ranges, s_ranges};
    int channels[] = {0,1};
    cv::Mat hist;
    cv::calcHist(&hsv, 1, channels, cv::Mat(), hist, 2, histSize, ranges, true, false);
}

void Workloads::customConvolution(const cv::Mat& img) {
    cv::Mat kernel = (cv::Mat_<float>(5,5) <<
                      1, 1, 1, 1, 1,
                      1, 2, 2, 2, 1,
                      1, 2, 3, 2, 1,
                      1, 2, 2, 2, 1,
                      1, 1, 1, 1, 1) / 35.0;
    cv::Mat result;
    cv::filter2D(img, result, -1, kernel);
}

void Workloads::pyramidProcessing(const cv::Mat& img) {
    cv::Mat resized = img;
    if (img.cols % 2 != 0 || img.rows % 2 != 0) {
        cv::resize(img, resized, cv::Size(img.cols & ~1, img.rows & ~1));
    }

    cv::Mat down, up;
    cv::pyrDown(resized, down);
    cv::pyrUp(down, up);
}

void Workloads::thresholdAndBitwise(const cv::Mat& img) {
    cv::Mat gray, bin, mask;
    cv::cvtColor(img, gray, cv::COLOR_BGR2GRAY);
    cv::threshold(gray, bin, 128, 255, cv::THRESH_BINARY);
    cv::bitwise_not(bin, mask);
}

void Workloads::addRandomNoise(const cv::Mat& img) {
    cv::Mat noise(img.size(), img.type());
    cv::RNG rng;
    rng.fill(noise, cv::RNG::NORMAL, 0, 50);
    cv::Mat result;
    cv::add(img, noise, result);
}
