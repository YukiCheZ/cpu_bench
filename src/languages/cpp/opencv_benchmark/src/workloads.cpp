#include "workloads.hpp"
#include <opencv2/imgproc.hpp>

void Workloads::processImage(const cv::Mat& img) {
    cv::Mat gray, blurred, edges;
    cv::cvtColor(img, gray, cv::COLOR_BGR2GRAY);
    cv::GaussianBlur(gray, blurred, cv::Size(7, 7), 1.5);
    cv::Canny(blurred, edges, 50, 150);
}
