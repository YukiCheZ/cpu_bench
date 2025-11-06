#include "workloads.hpp"
#include <opencv2/imgproc.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/video.hpp>
#include <opencv2/features2d.hpp>
#include <iostream>
#include <cmath>

// ===========================================================
// Main dispatcher
// ===========================================================
void Workloads::processImage(const cv::Mat& img, const std::string& workload) {
    if (workload == "fft_batch")          fftBatch(img);
    else if (workload == "conv_heavy")    convHeavy(img);
    else if (workload == "mandelbrot")    mandelbrot();
    else if (workload == "jacobi")        jacobiIter();
    else if (workload == "canny")         canny(img);
    else if (workload == "optical_flow")  opticalFlow(img);
    else if (workload == "motion_blur")   motionBlur(img);
    else if (workload == "background_sub") backgroundSub(img);
    else if (workload == "color_tracking") colorTracking(img);
    else if (workload == "feature_match") featureMatch(img);
    else {
        std::cerr << "[WARN] Unknown workload: " << workload << std::endl;
    }
}

// ===========================================================
// FFT Batch Transform
// ===========================================================
void Workloads::fftBatch(const cv::Mat& img) {
    cv::Mat grayFloat;

    if (img.channels() == 3) {
        cv::Mat gray8;
        cv::cvtColor(img, gray8, cv::COLOR_BGR2GRAY);
        gray8.convertTo(grayFloat, CV_32F);
    } else if (img.type() == CV_32F) {
        grayFloat = img.clone();
    } else {
        img.convertTo(grayFloat, CV_32F);
    }

    int m = cv::getOptimalDFTSize(grayFloat.rows);
    int n = cv::getOptimalDFTSize(grayFloat.cols);
    cv::copyMakeBorder(grayFloat, grayFloat, 0, m - grayFloat.rows, 0, n - grayFloat.cols,
                       cv::BORDER_CONSTANT, cv::Scalar::all(0));

    cv::Mat planes[] = {grayFloat, cv::Mat::zeros(grayFloat.size(), CV_32F)};
    cv::Mat complexImg;
    cv::merge(planes, 2, complexImg);

    for (int i = 0; i < 10; ++i)
        cv::dft(complexImg, complexImg);
}

// ===========================================================
// Heavy Convolution Stack
// ===========================================================
void Workloads::convHeavy(const cv::Mat& img) {
    cv::Mat current;
    if (img.channels() == 3) current = img.clone();
    else cv::cvtColor(img, current, cv::COLOR_GRAY2BGR);

    current.convertTo(current, CV_32F);
    cv::Mat kernel = cv::getGaussianKernel(11, 2.5, CV_32F);
    cv::Mat k2 = kernel * kernel.t();

    for (int i = 0; i < 15; ++i) {
        cv::Mat tmp;
        cv::filter2D(current, tmp, -1, k2);
        cv::normalize(tmp, current, 0, 255, cv::NORM_MINMAX);
    }
}

// ===========================================================
// Mandelbrot Fractal
// ===========================================================
void Workloads::mandelbrot() { mandelbrot(1024, 500); }

void Workloads::mandelbrot(int size, int maxIter) {
    cv::Mat result(size, size, CV_8UC1);
    const float scale = 3.0f / size;

    for (int y = 0; y < size; ++y) {
        for (int x = 0; x < size; ++x) {
            float cx = (x - size / 2) * scale - 0.7f;
            float cy = (y - size / 2) * scale;
            float zx = 0.0f, zy = 0.0f;
            int iter = 0;
            while (zx*zx + zy*zy < 4.0f && iter < maxIter) {
                float tmp = zx*zx - zy*zy + cx;
                zy = 2.0f*zx*zy + cy;
                zx = tmp;
                iter++;
            }
            result.at<uchar>(y, x) = static_cast<uchar>(255 * iter / maxIter);
        }
    }
}

// ===========================================================
// Jacobi Iteration (2D Poisson Solver)
// ===========================================================
void Workloads::jacobiIter() { jacobiIter(512, 200); }

void Workloads::jacobiIter(int n, int iters) {
    cv::Mat grid(n, n, CV_32F);
    cv::randu(grid, 0, 1);
    cv::Mat newGrid = grid.clone();

    for (int k = 0; k < iters; ++k) {
        for (int i = 1; i < n - 1; ++i) {
            float* ng = newGrid.ptr<float>(i);
            const float* g0 = grid.ptr<float>(i - 1);
            const float* g1 = grid.ptr<float>(i);
            const float* g2 = grid.ptr<float>(i + 1);
            for (int j = 1; j < n - 1; ++j)
                ng[j] = 0.25f * (g1[j - 1] + g1[j + 1] + g0[j] + g2[j]);
        }
        std::swap(grid, newGrid);
    }
}

// ===========================================================
// Canny Edge Detection
// ===========================================================
void Workloads::canny(const cv::Mat& img) {
    cv::Mat gray, edges;
    if (img.channels() == 3)
        cv::cvtColor(img, gray, cv::COLOR_BGR2GRAY);
    else
        gray = img.clone();
    cv::Canny(gray, edges, 100, 200);
}

// ===========================================================
// Optical Flow (Farneback Dense)
// ===========================================================
void Workloads::opticalFlow(const cv::Mat& img) {
    static cv::Mat prevGray;
    cv::Mat gray;
    cv::cvtColor(img, gray, cv::COLOR_BGR2GRAY);

    if (prevGray.empty()) {
        prevGray = gray.clone();
        return;
    }

    cv::Mat flow;
    cv::calcOpticalFlowFarneback(prevGray, gray, flow,
                                 0.5, 3, 15, 3, 5, 1.2, 0);
    prevGray = gray.clone();
}

// ===========================================================
// Motion Blur Convolution
// ===========================================================
void Workloads::motionBlur(const cv::Mat& img) {
    int kernel_size = 15;
    cv::Mat kernel = cv::Mat::zeros(kernel_size, kernel_size, CV_32F);
    for (int i = 0; i < kernel_size; ++i)
        kernel.at<float>(i, i) = 1.0f / kernel_size;

    cv::Mat blurred;
    cv::filter2D(img, blurred, -1, kernel);
}

// ===========================================================
// Background Subtraction (MOG2)
// ===========================================================
void Workloads::backgroundSub(const cv::Mat& img) {
    static cv::Ptr<cv::BackgroundSubtractor> bg = cv::createBackgroundSubtractorMOG2();
    cv::Mat mask;
    bg->apply(img, mask);
}

// ===========================================================
// Color Tracking (HSV thresholding)
// ===========================================================
void Workloads::colorTracking(const cv::Mat& img) {
    cv::Mat hsv, mask;
    cv::cvtColor(img, hsv, cv::COLOR_BGR2HSV);
    cv::inRange(hsv, cv::Scalar(30, 150, 50), cv::Scalar(85, 255, 255), mask);
    cv::erode(mask, mask, cv::Mat(), cv::Point(-1, -1), 2);
    cv::dilate(mask, mask, cv::Mat(), cv::Point(-1, -1), 2);
}

// ===========================================================
// Feature Matching (ORB + BFMatcher)
// ===========================================================
void Workloads::featureMatch(const cv::Mat& img) {

    thread_local cv::Ptr<cv::ORB> orb = cv::ORB::create(500);
    thread_local std::vector<cv::KeyPoint> prevKeypoints;
    thread_local cv::Mat prevDescriptors;

    std::vector<cv::KeyPoint> keypoints;
    cv::Mat descriptors;
    orb->detectAndCompute(img, cv::noArray(), keypoints, descriptors);

    if (!prevDescriptors.empty() && !descriptors.empty()) {
        cv::BFMatcher matcher(cv::NORM_HAMMING);
        std::vector<cv::DMatch> matches;
        matcher.match(prevDescriptors, descriptors, matches);
    }

    prevKeypoints = keypoints;
    prevDescriptors = descriptors.clone();
}

