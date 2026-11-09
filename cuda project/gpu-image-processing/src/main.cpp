/**
 * main.cpp
 *
 * Command-line entry point for the GPU Image Processing & Performance
 * Optimization Engine.
 *
 * This program demonstrates all four image-processing operations on a
 * supplied input image, benchmarks CPU vs GPU performance, and saves
 * the processed results to disk.
 *
 * It is separate from the Streamlit Python UI but shares the same C++
 * processing and benchmarking library, making it easy to test the C++
 * implementation independently.
 *
 * USAGE
 * ─────
 *   ./gpu_image_proc <input_image> [output_dir] [block_size] [iterations]
 *
 *   input_image : Path to a JPEG, PNG, or BMP image.
 *   output_dir  : Directory to write processed images (default: results/).
 *   block_size  : CUDA thread-block side length: 8, 16, or 32 (default: 16).
 *   iterations  : Number of benchmark measurement iterations (default: 5).
 *
 * DEPENDENCIES
 * ────────────
 * This file links against OpenCV (for image I/O), the cpu_processing and
 * benchmark objects, and optionally the CUDA objects when CUDA is available.
 *
 * BUILD
 * ─────
 *   See CMakeLists.txt for build instructions.
 */

#include <iostream>
#include <string>
#include <vector>
#include <cstring>

// OpenCV — used only for image loading and saving (not for processing)
#include <opencv2/core.hpp>
#include <opencv2/imgcodecs.hpp>
#include <opencv2/imgproc.hpp>

#include "cpu_processing.h"
#include "benchmark.h"

#ifdef CUDA_AVAILABLE
#include "cuda_processing.h"
#endif

// ---------------------------------------------------------------------------
// Helper: pretty-print a BenchmarkReport to stdout
// ---------------------------------------------------------------------------
static void print_report(const BenchmarkReport& r) {
    std::cout << "\n──────────────────────────────────────────────────\n";
    std::cout << "  Operation : " << r.operation << "\n";
    std::cout << "  Image     : " << r.width << " × " << r.height
              << "  (" << r.num_pixels << " pixels)\n";
    std::cout << "  Block     : " << r.block_size << "×" << r.block_size << "\n";
    std::cout << "──────────────────────────────────────────────────\n";
    std::cout << "  CPU time  : " << r.cpu_time_ms << " ms\n";

    if (r.gpu_available) {
        std::cout << "  GPU kernel: " << r.gpu_kernel_time_ms << " ms\n";
        std::cout << "  GPU total : " << r.gpu_total_time_ms
                  << " ms  (includes memory transfers)\n";
        std::cout << "  Speedup   : " << r.speedup << "×\n";
    } else {
        std::cout << "  GPU       : NOT AVAILABLE\n";
        if (r.error_message[0])
            std::cout << "  Reason    : " << r.error_message << "\n";
    }
}

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------
int main(int argc, char* argv[])
{
    // ── Parse arguments ───────────────────────────────────────────────────
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0]
                  << " <input_image> [output_dir] [block_size] [iterations]\n";
        return 1;
    }

    std::string input_path  = argv[1];
    std::string output_dir  = (argc > 2) ? argv[2] : "results";
    int         block_size  = (argc > 3) ? std::atoi(argv[3]) : 16;
    int         iterations  = (argc > 4) ? std::atoi(argv[4]) : 5;

    // Validate block size
    if (block_size != 8 && block_size != 16 && block_size != 32) {
        std::cerr << "Invalid block_size. Use 8, 16, or 32.\n";
        return 1;
    }

    // ── Load image via OpenCV ─────────────────────────────────────────────
    // cv::IMREAD_COLOR always loads as BGR; we convert to RGB for processing.
    cv::Mat img_bgr = cv::imread(input_path, cv::IMREAD_COLOR);
    if (img_bgr.empty()) {
        std::cerr << "Error: cannot load image '" << input_path << "'\n";
        return 1;
    }

    // Convert BGR → RGB (OpenCV stores as BGR by default)
    cv::Mat img_rgb;
    cv::cvtColor(img_bgr, img_rgb, cv::COLOR_BGR2RGB);

    int width  = img_rgb.cols;
    int height = img_rgb.rows;

    std::cout << "Image loaded: " << width << " × " << height
              << "  (" << (width * height) << " pixels)\n";

    // ── Print CUDA availability ───────────────────────────────────────────
#ifdef CUDA_AVAILABLE
    bool gpu = cuda_is_available();
    std::cout << "CUDA GPU: " << (gpu ? "AVAILABLE" : "NOT FOUND") << "\n";
#else
    std::cout << "CUDA GPU: NOT COMPILED IN\n";
#endif

    const uint8_t* rgb_data = img_rgb.data;

    // ── Grayscale ─────────────────────────────────────────────────────────
    {
        // CPU processing — run once to produce the output image
        std::vector<uint8_t> gray_out(width * height);
        grayscale_cpu(rgb_data, gray_out.data(), width, height);

        // Save result: convert grayscale back to 3-channel for OpenCV imwrite
        cv::Mat gray_mat(height, width, CV_8UC1, gray_out.data());
        cv::imwrite(output_dir + "/grayscale.jpg", gray_mat);

        // Benchmark
        BenchmarkReport r = benchmark_grayscale(rgb_data, width, height,
                                                 2, iterations, block_size);
        print_report(r);
    }

    // ── Gaussian Blur ─────────────────────────────────────────────────────
    {
        int blur_radius = 3;
        float sigma     = 1.5f;

        std::vector<uint8_t> blur_out(width * height * 3);
        gaussian_blur_cpu(rgb_data, blur_out.data(), width, height, blur_radius, sigma);

        cv::Mat blur_mat(height, width, CV_8UC3, blur_out.data());
        cv::cvtColor(blur_mat, blur_mat, cv::COLOR_RGB2BGR);
        cv::imwrite(output_dir + "/gaussian_blur.jpg", blur_mat);

        BenchmarkReport r = benchmark_gaussian_blur(rgb_data, width, height,
                                                     blur_radius, sigma,
                                                     2, iterations, block_size);
        print_report(r);
    }

    // ── Sobel Edge Detection ──────────────────────────────────────────────
    {
        // Sobel requires a grayscale input — convert first
        std::vector<uint8_t> gray_in(width * height);
        grayscale_cpu(rgb_data, gray_in.data(), width, height);

        std::vector<uint8_t> sobel_out(width * height);
        sobel_edge_cpu(gray_in.data(), sobel_out.data(), width, height);

        cv::Mat sobel_mat(height, width, CV_8UC1, sobel_out.data());
        cv::imwrite(output_dir + "/sobel_edges.jpg", sobel_mat);

        BenchmarkReport r = benchmark_sobel(gray_in.data(), width, height,
                                             2, iterations, block_size);
        print_report(r);
    }

    // ── Image Sharpening ──────────────────────────────────────────────────
    {
        std::vector<uint8_t> sharp_out(width * height * 3);
        sharpen_cpu(rgb_data, sharp_out.data(), width, height);

        cv::Mat sharp_mat(height, width, CV_8UC3, sharp_out.data());
        cv::cvtColor(sharp_mat, sharp_mat, cv::COLOR_RGB2BGR);
        cv::imwrite(output_dir + "/sharpened.jpg", sharp_mat);

        BenchmarkReport r = benchmark_sharpen(rgb_data, width, height,
                                               2, iterations, block_size);
        print_report(r);
    }

    std::cout << "\nDone. Results saved to: " << output_dir << "/\n";
    return 0;
}
