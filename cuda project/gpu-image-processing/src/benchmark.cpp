/**
 * benchmark.cpp
 *
 * Benchmarking utilities for the GPU Image Processing Engine.
 *
 * This module runs CPU and GPU implementations multiple times (with warm-up
 * iterations discarded), computes average execution times, and calculates
 * the GPU speedup relative to the CPU.
 *
 * METHODOLOGY
 * ───────────
 * 1. Both CPU and GPU execute on the IDENTICAL input image.
 * 2. A configurable number of warm-up iterations are run before timing starts.
 *    Warm-up is important because:
 *      - The first CPU iteration may incur branch-predictor cold-start costs.
 *      - The first GPU iteration includes CUDA context initialisation overhead.
 * 3. Timing iterations run back-to-back; the average is reported.
 * 4. Speedup = CPU_avg_time / GPU_kernel_time
 *              (kernel-only time is used because that is the pure compute comparison)
 *    End-to-end GPU time (including memory transfers) is also reported separately
 *    so users can understand the realistic overhead for a single-shot operation.
 *
 * IMPORTANT: Benchmark results are real measurements on the current hardware.
 *            Nothing is fabricated.  If no GPU is available, GPU timing is
 *            not reported and speedup is set to 0.
 */

#include "benchmark.h"
#include "cpu_processing.h"

#ifdef CUDA_AVAILABLE
#include "cuda_processing.h"
#endif

#include <chrono>
#include <cstring>   // memset
#include <cstdio>
#include <vector>
#include <numeric>   // std::accumulate

// ---------------------------------------------------------------------------
// Internal timing helper (CPU wall-clock, high resolution)
// ---------------------------------------------------------------------------
static double now_ms() {
    using namespace std::chrono;
    return duration<double, std::milli>(
        high_resolution_clock::now().time_since_epoch()
    ).count();
}

// ===========================================================================
// benchmark_grayscale
// ===========================================================================

BenchmarkReport benchmark_grayscale(const uint8_t* input,
                                     int width, int height,
                                     int warmup_iters, int measure_iters,
                                     int block_size_int)
{
    BenchmarkReport report = {};
    report.operation   = "Grayscale Conversion";
    report.width       = width;
    report.height      = height;
    report.num_pixels  = (long long)width * height;
    report.block_size  = block_size_int;
    report.gpu_available = false;

    size_t output_gray = (size_t)width * height;
    std::vector<uint8_t> out_cpu(output_gray);
    std::vector<uint8_t> out_gpu(output_gray);

    // ── CPU Benchmarking ────────────────────────────────────────────────
    // Warm-up: discard these iterations so caches are primed
    for (int i = 0; i < warmup_iters; ++i)
        grayscale_cpu(input, out_cpu.data(), width, height);

    // Measured iterations
    std::vector<double> cpu_times(measure_iters);
    for (int i = 0; i < measure_iters; ++i) {
        double t0 = now_ms();
        grayscale_cpu(input, out_cpu.data(), width, height);
        cpu_times[i] = now_ms() - t0;
    }
    report.cpu_time_ms = std::accumulate(cpu_times.begin(), cpu_times.end(), 0.0)
                         / measure_iters;

    // ── GPU Benchmarking ────────────────────────────────────────────────
#ifdef CUDA_AVAILABLE
    BlockSize bsz = (block_size_int == 8)  ? BlockSize::BLOCK_8  :
                    (block_size_int == 32) ? BlockSize::BLOCK_32 : BlockSize::BLOCK_16;

    // GPU warm-up
    for (int i = 0; i < warmup_iters; ++i)
        grayscale_gpu(input, out_gpu.data(), width, height, bsz);

    std::vector<float> gpu_kernel_times(measure_iters);
    std::vector<float> gpu_total_times(measure_iters);

    for (int i = 0; i < measure_iters; ++i) {
        BenchmarkResult r = grayscale_gpu(input, out_gpu.data(), width, height, bsz);
        if (!r.cuda_available) {
            snprintf(report.error_message, sizeof(report.error_message),
                     "%s", r.error_message);
            goto cpu_only;
        }
        gpu_kernel_times[i] = r.kernel_time_ms;
        gpu_total_times[i]  = r.total_time_ms;
    }

    report.gpu_kernel_time_ms =
        std::accumulate(gpu_kernel_times.begin(), gpu_kernel_times.end(), 0.0f)
        / measure_iters;
    report.gpu_total_time_ms =
        std::accumulate(gpu_total_times.begin(), gpu_total_times.end(), 0.0f)
        / measure_iters;
    report.gpu_available = true;

    if (report.gpu_kernel_time_ms > 0.0f)
        report.speedup = (float)(report.cpu_time_ms / report.gpu_kernel_time_ms);

cpu_only:;
#else
    snprintf(report.error_message, sizeof(report.error_message),
             "CUDA not compiled in — GPU benchmarking unavailable.");
#endif

    return report;
}

// ===========================================================================
// benchmark_gaussian_blur
// ===========================================================================

BenchmarkReport benchmark_gaussian_blur(const uint8_t* input,
                                         int width, int height,
                                         int blur_radius, float sigma,
                                         int warmup_iters, int measure_iters,
                                         int block_size_int)
{
    BenchmarkReport report = {};
    report.operation   = "Gaussian Blur";
    report.width       = width;
    report.height      = height;
    report.num_pixels  = (long long)width * height;
    report.block_size  = block_size_int;
    report.gpu_available = false;

    size_t bytes = (size_t)width * height * 3;
    std::vector<uint8_t> out_cpu(bytes);
    std::vector<uint8_t> out_gpu(bytes);

    // CPU warm-up + measurement
    for (int i = 0; i < warmup_iters; ++i)
        gaussian_blur_cpu(input, out_cpu.data(), width, height, blur_radius, sigma);

    std::vector<double> cpu_times(measure_iters);
    for (int i = 0; i < measure_iters; ++i) {
        double t0 = now_ms();
        gaussian_blur_cpu(input, out_cpu.data(), width, height, blur_radius, sigma);
        cpu_times[i] = now_ms() - t0;
    }
    report.cpu_time_ms = std::accumulate(cpu_times.begin(), cpu_times.end(), 0.0)
                         / measure_iters;

#ifdef CUDA_AVAILABLE
    BlockSize bsz = (block_size_int == 8)  ? BlockSize::BLOCK_8  :
                    (block_size_int == 32) ? BlockSize::BLOCK_32 : BlockSize::BLOCK_16;

    for (int i = 0; i < warmup_iters; ++i)
        gaussian_blur_gpu(input, out_gpu.data(), width, height, blur_radius, sigma, bsz);

    std::vector<float> gpu_kernel_times(measure_iters);
    std::vector<float> gpu_total_times(measure_iters);
    for (int i = 0; i < measure_iters; ++i) {
        BenchmarkResult r = gaussian_blur_gpu(input, out_gpu.data(), width, height,
                                               blur_radius, sigma, bsz);
        if (!r.cuda_available) {
            snprintf(report.error_message, sizeof(report.error_message),
                     "%s", r.error_message);
            goto cpu_only_blur;
        }
        gpu_kernel_times[i] = r.kernel_time_ms;
        gpu_total_times[i]  = r.total_time_ms;
    }
    report.gpu_kernel_time_ms =
        std::accumulate(gpu_kernel_times.begin(), gpu_kernel_times.end(), 0.0f) / measure_iters;
    report.gpu_total_time_ms =
        std::accumulate(gpu_total_times.begin(), gpu_total_times.end(), 0.0f) / measure_iters;
    report.gpu_available = true;
    if (report.gpu_kernel_time_ms > 0.0f)
        report.speedup = (float)(report.cpu_time_ms / report.gpu_kernel_time_ms);
cpu_only_blur:;
#else
    snprintf(report.error_message, sizeof(report.error_message),
             "CUDA not compiled in — GPU benchmarking unavailable.");
#endif

    return report;
}

// ===========================================================================
// benchmark_sobel
// ===========================================================================

BenchmarkReport benchmark_sobel(const uint8_t* input,
                                 int width, int height,
                                 int warmup_iters, int measure_iters,
                                 int block_size_int)
{
    BenchmarkReport report = {};
    report.operation   = "Sobel Edge Detection";
    report.width       = width;
    report.height      = height;
    report.num_pixels  = (long long)width * height;
    report.block_size  = block_size_int;
    report.gpu_available = false;

    size_t bytes = (size_t)width * height;
    std::vector<uint8_t> out_cpu(bytes);
    std::vector<uint8_t> out_gpu(bytes);

    for (int i = 0; i < warmup_iters; ++i)
        sobel_edge_cpu(input, out_cpu.data(), width, height);

    std::vector<double> cpu_times(measure_iters);
    for (int i = 0; i < measure_iters; ++i) {
        double t0 = now_ms();
        sobel_edge_cpu(input, out_cpu.data(), width, height);
        cpu_times[i] = now_ms() - t0;
    }
    report.cpu_time_ms = std::accumulate(cpu_times.begin(), cpu_times.end(), 0.0)
                         / measure_iters;

#ifdef CUDA_AVAILABLE
    BlockSize bsz = (block_size_int == 8)  ? BlockSize::BLOCK_8  :
                    (block_size_int == 32) ? BlockSize::BLOCK_32 : BlockSize::BLOCK_16;

    for (int i = 0; i < warmup_iters; ++i)
        sobel_edge_gpu(input, out_gpu.data(), width, height, bsz);

    std::vector<float> gpu_kernel_times(measure_iters);
    std::vector<float> gpu_total_times(measure_iters);
    for (int i = 0; i < measure_iters; ++i) {
        BenchmarkResult r = sobel_edge_gpu(input, out_gpu.data(), width, height, bsz);
        if (!r.cuda_available) {
            snprintf(report.error_message, sizeof(report.error_message),
                     "%s", r.error_message);
            goto cpu_only_sobel;
        }
        gpu_kernel_times[i] = r.kernel_time_ms;
        gpu_total_times[i]  = r.total_time_ms;
    }
    report.gpu_kernel_time_ms =
        std::accumulate(gpu_kernel_times.begin(), gpu_kernel_times.end(), 0.0f) / measure_iters;
    report.gpu_total_time_ms =
        std::accumulate(gpu_total_times.begin(), gpu_total_times.end(), 0.0f) / measure_iters;
    report.gpu_available = true;
    if (report.gpu_kernel_time_ms > 0.0f)
        report.speedup = (float)(report.cpu_time_ms / report.gpu_kernel_time_ms);
cpu_only_sobel:;
#else
    snprintf(report.error_message, sizeof(report.error_message),
             "CUDA not compiled in — GPU benchmarking unavailable.");
#endif

    return report;
}

// ===========================================================================
// benchmark_sharpen
// ===========================================================================

BenchmarkReport benchmark_sharpen(const uint8_t* input,
                                   int width, int height,
                                   int warmup_iters, int measure_iters,
                                   int block_size_int)
{
    BenchmarkReport report = {};
    report.operation   = "Image Sharpening";
    report.width       = width;
    report.height      = height;
    report.num_pixels  = (long long)width * height;
    report.block_size  = block_size_int;
    report.gpu_available = false;

    size_t bytes = (size_t)width * height * 3;
    std::vector<uint8_t> out_cpu(bytes);
    std::vector<uint8_t> out_gpu(bytes);

    for (int i = 0; i < warmup_iters; ++i)
        sharpen_cpu(input, out_cpu.data(), width, height);

    std::vector<double> cpu_times(measure_iters);
    for (int i = 0; i < measure_iters; ++i) {
        double t0 = now_ms();
        sharpen_cpu(input, out_cpu.data(), width, height);
        cpu_times[i] = now_ms() - t0;
    }
    report.cpu_time_ms = std::accumulate(cpu_times.begin(), cpu_times.end(), 0.0)
                         / measure_iters;

#ifdef CUDA_AVAILABLE
    BlockSize bsz = (block_size_int == 8)  ? BlockSize::BLOCK_8  :
                    (block_size_int == 32) ? BlockSize::BLOCK_32 : BlockSize::BLOCK_16;

    for (int i = 0; i < warmup_iters; ++i)
        sharpen_gpu(input, out_gpu.data(), width, height, bsz);

    std::vector<float> gpu_kernel_times(measure_iters);
    std::vector<float> gpu_total_times(measure_iters);
    for (int i = 0; i < measure_iters; ++i) {
        BenchmarkResult r = sharpen_gpu(input, out_gpu.data(), width, height, bsz);
        if (!r.cuda_available) {
            snprintf(report.error_message, sizeof(report.error_message),
                     "%s", r.error_message);
            goto cpu_only_sharpen;
        }
        gpu_kernel_times[i] = r.kernel_time_ms;
        gpu_total_times[i]  = r.total_time_ms;
    }
    report.gpu_kernel_time_ms =
        std::accumulate(gpu_kernel_times.begin(), gpu_kernel_times.end(), 0.0f) / measure_iters;
    report.gpu_total_time_ms =
        std::accumulate(gpu_total_times.begin(), gpu_total_times.end(), 0.0f) / measure_iters;
    report.gpu_available = true;
    if (report.gpu_kernel_time_ms > 0.0f)
        report.speedup = (float)(report.cpu_time_ms / report.gpu_kernel_time_ms);
cpu_only_sharpen:;
#else
    snprintf(report.error_message, sizeof(report.error_message),
             "CUDA not compiled in — GPU benchmarking unavailable.");
#endif

    return report;
}
