/**
 * cuda_processing.h
 *
 * Declares the host-callable wrapper functions that launch the CUDA GPU kernels
 * defined in cuda_processing.cu.
 *
 * Each wrapper function:
 *   1. Allocates GPU memory with cudaMalloc.
 *   2. Copies input data from host (CPU) to device (GPU) with cudaMemcpy.
 *   3. Configures and launches the CUDA kernel.
 *   4. Copies the result back from device to host.
 *   5. Frees GPU memory with cudaFree.
 *   6. Returns timing information via output parameters.
 *
 * The kernel-only time is measured with CUDA events (cudaEvent) which use the
 * GPU's own high-resolution timer — more accurate than host-side chrono for
 * measuring kernel execution.
 *
 * End-to-end time (including memory transfers) is measured with host-side
 * std::chrono and is also reported so callers can compare the full overhead.
 *
 * IMPORTANT: These functions require a CUDA-capable NVIDIA GPU and the CUDA
 * Toolkit (nvcc) to compile.  They are compiled by CMake only when CUDA is
 * detected.  The Python interface provides a CPU-only fallback when the
 * compiled CUDA library is not available.
 */

#pragma once

#include <cstdint>

// ---------------------------------------------------------------------------
// CUDA block-size selection
//
// Thread blocks are square; common sizes are 8, 16, or 32 threads per side.
// A block of 16×16 = 256 threads is a common default that saturates many GPUs.
// ---------------------------------------------------------------------------
enum class BlockSize : int {
    BLOCK_8  =  8,
    BLOCK_16 = 16,
    BLOCK_32 = 32
};

// ---------------------------------------------------------------------------
// BenchmarkResult
//
// Returned by every GPU wrapper function.  Separates kernel-only time from
// the full end-to-end time (which includes host↔device memory transfers).
// ---------------------------------------------------------------------------
struct BenchmarkResult {
    float kernel_time_ms;       // Time for the GPU kernel execution only
    float total_time_ms;        // End-to-end time including memory transfers
    bool  cuda_available;       // True if a CUDA GPU was used; false = fallback
    char  error_message[256];   // Populated when cuda_available == false
};

// ---------------------------------------------------------------------------
// GPU Grayscale Conversion
// ---------------------------------------------------------------------------

/**
 * grayscale_gpu
 *
 * Converts an RGB image to grayscale on the GPU.
 * Assigns one CUDA thread per output pixel.
 * Each thread computes Gray = 0.299R + 0.587G + 0.114B independently.
 *
 * @param input       Host pointer to packed RGB input  (width * height * 3 bytes).
 * @param output      Host pointer to output grayscale  (width * height * 1 byte).
 * @param width       Image width in pixels.
 * @param height      Image height in pixels.
 * @param block_size  Number of threads per block dimension (8, 16, or 32).
 * @return            BenchmarkResult with timing and availability information.
 */
BenchmarkResult grayscale_gpu(const uint8_t* input, uint8_t* output,
                               int width, int height,
                               BlockSize block_size = BlockSize::BLOCK_16);

// ---------------------------------------------------------------------------
// GPU Gaussian Blur
// ---------------------------------------------------------------------------

/**
 * gaussian_blur_gpu
 *
 * Applies Gaussian blur on the GPU.  Each thread computes one output pixel
 * by iterating over its kernel neighbourhood in global GPU memory.
 *
 * @param input       Host pointer to packed RGB input  (width * height * 3 bytes).
 * @param output      Host pointer to packed RGB output (width * height * 3 bytes).
 * @param width       Image width in pixels.
 * @param height      Image height in pixels.
 * @param blur_radius Radius of the Gaussian kernel.
 * @param sigma       Standard deviation of the Gaussian.
 * @param block_size  Thread block side length.
 * @return            BenchmarkResult with timing and availability information.
 */
BenchmarkResult gaussian_blur_gpu(const uint8_t* input, uint8_t* output,
                                   int width, int height,
                                   int blur_radius, float sigma,
                                   BlockSize block_size = BlockSize::BLOCK_16);

// ---------------------------------------------------------------------------
// GPU Sobel Edge Detection
// ---------------------------------------------------------------------------

/**
 * sobel_edge_gpu
 *
 * Runs Sobel edge detection on the GPU.  Each thread applies the 3×3 Sobel
 * kernels to one grayscale input pixel and writes the gradient magnitude.
 *
 * @param input       Host pointer to single-channel grayscale input.
 * @param output      Host pointer to single-channel grayscale output.
 * @param width       Image width in pixels.
 * @param height      Image height in pixels.
 * @param block_size  Thread block side length.
 * @return            BenchmarkResult with timing and availability information.
 */
BenchmarkResult sobel_edge_gpu(const uint8_t* input, uint8_t* output,
                                int width, int height,
                                BlockSize block_size = BlockSize::BLOCK_16);

// ---------------------------------------------------------------------------
// GPU Image Sharpening
// ---------------------------------------------------------------------------

/**
 * sharpen_gpu
 *
 * Applies the sharpening convolution kernel on the GPU.
 * Output values are clamped to [0, 255] inside the kernel.
 *
 * @param input       Host pointer to packed RGB input  (width * height * 3 bytes).
 * @param output      Host pointer to packed RGB output (width * height * 3 bytes).
 * @param width       Image width in pixels.
 * @param height      Image height in pixels.
 * @param block_size  Thread block side length.
 * @return            BenchmarkResult with timing and availability information.
 */
BenchmarkResult sharpen_gpu(const uint8_t* input, uint8_t* output,
                             int width, int height,
                             BlockSize block_size = BlockSize::BLOCK_16);

// ---------------------------------------------------------------------------
// Utility: check whether a CUDA-capable device is present at runtime
// ---------------------------------------------------------------------------

/**
 * cuda_is_available
 *
 * Returns true if at least one CUDA-capable GPU is detected by the CUDA
 * runtime.  Returns false if the runtime is absent or no compatible GPU
 * is found.  Safe to call even when CUDA is not compiled in — returns false.
 */
bool cuda_is_available();
