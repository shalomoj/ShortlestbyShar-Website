/**
 * benchmark.h
 *
 * Declares the BenchmarkReport struct and the four benchmarking functions.
 * Each function runs both CPU and GPU implementations (when available)
 * for one operation and returns a populated BenchmarkReport.
 */

#pragma once

#include <cstdint>
#include <string>

// ---------------------------------------------------------------------------
// BenchmarkReport
//
// Returned by every benchmark_* function.  Contains all timing data,
// image metadata, and GPU availability status needed to build charts and
// produce comparisons in the Python dashboard.
// ---------------------------------------------------------------------------
struct BenchmarkReport {
    std::string operation;          // Human-readable operation name

    // Image metadata
    int       width;
    int       height;
    long long num_pixels;
    int       block_size;           // CUDA block dimension used (8, 16, or 32)

    // Timing (milliseconds, averaged over measure_iters)
    double cpu_time_ms;             // Average CPU wall-clock time
    float  gpu_kernel_time_ms;      // Average GPU kernel-only time (CUDA events)
    float  gpu_total_time_ms;       // Average GPU end-to-end time (incl. transfers)

    // Derived metrics
    float  speedup;                 // cpu_time_ms / gpu_kernel_time_ms (0 if no GPU)

    // Status
    bool   gpu_available;
    char   error_message[512];      // Non-empty when gpu_available == false
};

// ---------------------------------------------------------------------------
// Benchmarking functions
// ---------------------------------------------------------------------------

BenchmarkReport benchmark_grayscale(const uint8_t* input,
                                     int width, int height,
                                     int warmup_iters  = 2,
                                     int measure_iters = 5,
                                     int block_size    = 16);

BenchmarkReport benchmark_gaussian_blur(const uint8_t* input,
                                         int width, int height,
                                         int blur_radius   = 3,
                                         float sigma       = 1.5f,
                                         int warmup_iters  = 2,
                                         int measure_iters = 5,
                                         int block_size    = 16);

BenchmarkReport benchmark_sobel(const uint8_t* input,
                                 int width, int height,
                                 int warmup_iters  = 2,
                                 int measure_iters = 5,
                                 int block_size    = 16);

BenchmarkReport benchmark_sharpen(const uint8_t* input,
                                   int width, int height,
                                   int warmup_iters  = 2,
                                   int measure_iters = 5,
                                   int block_size    = 16);
