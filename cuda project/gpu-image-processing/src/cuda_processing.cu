/**
 * cuda_processing.cu
 *
 * GPU implementations of four image-processing operations using CUDA C++:
 *   - Grayscale conversion
 *   - Gaussian blur
 *   - Sobel edge detection
 *   - Image sharpening
 *
 * FILE STRUCTURE
 * ──────────────
 * 1. CUDA kernel functions (__global__) — run on the GPU.
 * 2. Host wrapper functions — called from CPU code; handle memory management,
 *    kernel launches, and timing.
 *
 * THREAD INDEXING STRATEGY
 * ─────────────────────────
 * We use a 2D thread grid that maps naturally to the 2D pixel grid:
 *
 *   int x = blockIdx.x * blockDim.x + threadIdx.x;  // column (horizontal)
 *   int y = blockIdx.y * blockDim.y + threadIdx.y;  // row    (vertical)
 *
 * Each thread is responsible for exactly one output pixel.  Because pixels
 * are independent, thousands of threads execute simultaneously on the GPU,
 * drastically reducing wall-clock time compared to sequential CPU processing.
 *
 * MEMORY MANAGEMENT
 * ─────────────────
 * Host (CPU) memory and device (GPU) memory are separate address spaces.
 * Data must be explicitly transferred:
 *   cudaMalloc     — allocates memory on the GPU device.
 *   cudaMemcpy (HostToDevice) — copies input from CPU RAM to GPU VRAM.
 *   cudaMemcpy (DeviceToHost) — copies result from GPU VRAM back to CPU RAM.
 *   cudaFree       — releases GPU memory.
 *
 * TIMING
 * ──────
 * GPU kernels execute asynchronously.  We use CUDA Events to measure kernel
 * time accurately using the GPU's own hardware timer:
 *   cudaEventCreate / cudaEventRecord / cudaEventSynchronize / cudaEventElapsedTime
 *
 * ERROR HANDLING
 * ──────────────
 * Every CUDA API call returns a cudaError_t.  The CUDA_CHECK macro converts
 * errors into an early-return with a populated BenchmarkResult error message.
 */

#include "cuda_processing.h"

#include <cuda_runtime.h>
#include <cmath>
#include <cstdio>   // snprintf
#include <cstring>  // memset
#include <chrono>   // end-to-end host-side timing
#include <vector>   // std::vector (used in build_gaussian_kernel_device)

// ===========================================================================
// Utility macros
// ===========================================================================

/**
 * CUDA_CHECK
 *
 * Checks a cudaError_t return value.  On error, fills result.error_message,
 * sets result.cuda_available = false, frees any device pointers passed as
 * a brace-enclosed list, and returns the result immediately.
 *
 * Usage:
 *   CUDA_CHECK(cudaMalloc(&d_ptr, size), result, {d_ptr});
 */
#define CUDA_CHECK(call, result, ...)                                        \
    do {                                                                      \
        cudaError_t _err = (call);                                           \
        if (_err != cudaSuccess) {                                           \
            snprintf((result).error_message, sizeof((result).error_message), \
                     "CUDA error at %s:%d — %s",                            \
                     __FILE__, __LINE__, cudaGetErrorString(_err));          \
            (result).cuda_available = false;                                 \
            uint8_t* _ptrs[] = { __VA_ARGS__ };                             \
            for (uint8_t* _p : _ptrs) { if (_p) cudaFree(_p); }            \
            return result;                                                   \
        }                                                                    \
    } while (0)

// Helper to clamp a float to [0, 255] inside device code
__device__ static inline unsigned char dev_clamp(float v) {
    return (v < 0.0f) ? 0 : (v > 255.0f) ? 255 : (unsigned char)v;
}

// ===========================================================================
// SECTION 1 — CUDA KERNEL FUNCTIONS
//
// Functions declared __global__ are the GPU kernels.  They are compiled by
// nvcc and run on the GPU.  Each invocation of the function body is executed
// by a single GPU thread.
// ===========================================================================

// ---------------------------------------------------------------------------
// Kernel 1: Grayscale Conversion
// ---------------------------------------------------------------------------

/**
 * kernel_grayscale
 *
 * Each thread converts one pixel from RGB to grayscale.
 * With (width × height) pixels and potentially thousands of CUDA cores,
 * many pixels are processed truly simultaneously.
 *
 * @param d_input   Device pointer to packed RGB input  (W * H * 3 bytes).
 * @param d_output  Device pointer to grayscale output  (W * H * 1 byte).
 * @param width     Image width in pixels.
 * @param height    Image height in pixels.
 */
__global__ void kernel_grayscale(const unsigned char* d_input,
                                  unsigned char* d_output,
                                  int width, int height)
{
    // Compute this thread's pixel coordinates in the image.
    // blockIdx and threadIdx are built-in CUDA variables; blockDim holds
    // the number of threads per block dimension.
    int x = blockIdx.x * blockDim.x + threadIdx.x;  // column
    int y = blockIdx.y * blockDim.y + threadIdx.y;  // row

    // Bounds check — the grid may be slightly larger than the image if the
    // image dimensions are not multiples of the block size.
    if (x >= width || y >= height) return;

    int idx_rgb  = (y * width + x) * 3;  // 3 bytes per RGB pixel
    int idx_gray =  y * width + x;       // 1 byte per grayscale pixel

    unsigned char r = d_input[idx_rgb + 0];
    unsigned char g = d_input[idx_rgb + 1];
    unsigned char b = d_input[idx_rgb + 2];

    // Luminance formula — identical to the CPU version for direct comparison
    d_output[idx_gray] = dev_clamp(0.299f * r + 0.587f * g + 0.114f * b);
}

// ---------------------------------------------------------------------------
// Kernel 2: Gaussian Blur
// ---------------------------------------------------------------------------

/**
 * kernel_gaussian_blur
 *
 * Each thread computes one output pixel by accumulating a weighted sum over
 * a (2*radius+1)² neighbourhood.  The Gaussian weights are passed in via
 * the d_kernel pointer (constant-memory read — every thread reads the same
 * kernel, making this a good candidate for __constant__ memory in a future
 * optimisation).
 *
 * Boundary handling: coordinates are clamped to the nearest valid pixel
 * (clamp-to-edge), so border pixels are processed correctly without branching
 * on every access.
 *
 * @param d_input    Device pointer to packed RGB input.
 * @param d_output   Device pointer to packed RGB output.
 * @param width      Image width in pixels.
 * @param height     Image height in pixels.
 * @param d_kernel   Device pointer to pre-computed, normalised Gaussian weights.
 * @param radius     Blur radius; kernel size = (2*radius+1)².
 */
__global__ void kernel_gaussian_blur(const unsigned char* d_input,
                                      unsigned char* d_output,
                                      int width, int height,
                                      const float* d_kernel,
                                      int radius)
{
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    if (x >= width || y >= height) return;

    int kernel_size = 2 * radius + 1;
    float acc_r = 0.0f, acc_g = 0.0f, acc_b = 0.0f;

    for (int ky = -radius; ky <= radius; ++ky) {
        for (int kx = -radius; kx <= radius; ++kx) {
            // Clamp-to-edge boundary handling
            int nx = max(0, min(x + kx, width  - 1));
            int ny = max(0, min(y + ky, height - 1));

            int src = (ny * width + nx) * 3;
            int kid = (ky + radius) * kernel_size + (kx + radius);

            float w = d_kernel[kid];
            acc_r += w * d_input[src + 0];
            acc_g += w * d_input[src + 1];
            acc_b += w * d_input[src + 2];
        }
    }

    int dst = (y * width + x) * 3;
    d_output[dst + 0] = dev_clamp(acc_r);
    d_output[dst + 1] = dev_clamp(acc_g);
    d_output[dst + 2] = dev_clamp(acc_b);
}

// ---------------------------------------------------------------------------
// Kernel 3: Sobel Edge Detection
// ---------------------------------------------------------------------------

/**
 * kernel_sobel
 *
 * Each thread applies the 3×3 Sobel kernels to one grayscale pixel and
 * writes the gradient magnitude.
 *
 * Sobel kernels:
 *   Gx = [-1  0 +1; -2  0 +2; -1  0 +1]   (detects vertical edges)
 *   Gy = [-1 -2 -1;  0  0  0; +1 +2 +1]   (detects horizontal edges)
 *
 * Magnitude = sqrt(Gx² + Gy²)
 *
 * @param d_input   Device pointer to grayscale input  (W * H * 1 byte).
 * @param d_output  Device pointer to grayscale output (W * H * 1 byte).
 * @param width     Image width in pixels.
 * @param height    Image height in pixels.
 */
__global__ void kernel_sobel(const unsigned char* d_input,
                              unsigned char* d_output,
                              int width, int height)
{
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    if (x >= width || y >= height) return;

    // Sobel kernel weights stored as constant arrays within the kernel.
    // These are read-only and the same for every thread.
    const int Kx[3][3] = { {-1, 0, +1}, {-2, 0, +2}, {-1, 0, +1} };
    const int Ky[3][3] = { {-1, -2, -1}, {0, 0, 0}, {+1, +2, +1} };

    float gx = 0.0f, gy = 0.0f;

    for (int ky = -1; ky <= 1; ++ky) {
        for (int kx = -1; kx <= 1; ++kx) {
            int nx = max(0, min(x + kx, width  - 1));
            int ny = max(0, min(y + ky, height - 1));

            float pixel = d_input[ny * width + nx];
            gx += Kx[ky + 1][kx + 1] * pixel;
            gy += Ky[ky + 1][kx + 1] * pixel;
        }
    }

    // sqrtf is the device single-precision square root (faster than sqrt)
    float magnitude = sqrtf(gx * gx + gy * gy);
    d_output[y * width + x] = dev_clamp(magnitude);
}

// ---------------------------------------------------------------------------
// Kernel 4: Image Sharpening
// ---------------------------------------------------------------------------

/**
 * kernel_sharpen
 *
 * Applies the 3×3 Laplacian-based sharpening kernel to each RGB pixel.
 *
 * Kernel:
 *   [  0  -1   0 ]
 *   [ -1   5  -1 ]
 *   [  0  -1   0 ]
 *
 * Result is clamped to [0, 255].
 *
 * @param d_input   Device pointer to packed RGB input.
 * @param d_output  Device pointer to packed RGB output.
 * @param width     Image width in pixels.
 * @param height    Image height in pixels.
 */
__global__ void kernel_sharpen(const unsigned char* d_input,
                                unsigned char* d_output,
                                int width, int height)
{
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    if (x >= width || y >= height) return;

    const int kernel[3][3] = { {0, -1, 0}, {-1, 5, -1}, {0, -1, 0} };

    float acc_r = 0.0f, acc_g = 0.0f, acc_b = 0.0f;

    for (int ky = -1; ky <= 1; ++ky) {
        for (int kx = -1; kx <= 1; ++kx) {
            int nx = max(0, min(x + kx, width  - 1));
            int ny = max(0, min(y + ky, height - 1));

            int src = (ny * width + nx) * 3;
            int k   = kernel[ky + 1][kx + 1];

            acc_r += k * d_input[src + 0];
            acc_g += k * d_input[src + 1];
            acc_b += k * d_input[src + 2];
        }
    }

    int dst = (y * width + x) * 3;
    d_output[dst + 0] = dev_clamp(acc_r);
    d_output[dst + 1] = dev_clamp(acc_g);
    d_output[dst + 2] = dev_clamp(acc_b);
}

// ===========================================================================
// SECTION 2 — HOST WRAPPER FUNCTIONS
//
// These run on the CPU.  They:
//   1. Check GPU availability.
//   2. Allocate device memory.
//   3. Transfer input to the GPU.
//   4. Configure the grid/block dimensions.
//   5. Launch the kernel.
//   6. Transfer output back to the CPU.
//   7. Clean up device memory.
//   8. Return timing results.
// ===========================================================================

// ---------------------------------------------------------------------------
// Helper: build and upload a normalised Gaussian kernel to the GPU
// ---------------------------------------------------------------------------
static void build_gaussian_kernel_device(float** d_kernel_out,
                                          int radius, float sigma)
{
    int kernel_size = 2 * radius + 1;
    int n = kernel_size * kernel_size;

    // Build on host first
    std::vector<float> h_kernel(n);
    float sum = 0.0f;
    for (int ky = -radius; ky <= radius; ++ky)
        for (int kx = -radius; kx <= radius; ++kx) {
            float v = expf(-(kx*kx + ky*ky) / (2.0f * sigma * sigma));
            h_kernel[(ky + radius) * kernel_size + (kx + radius)] = v;
            sum += v;
        }
    for (float& w : h_kernel) w /= sum;

    // Allocate and upload to device
    cudaMalloc(d_kernel_out, n * sizeof(float));
    cudaMemcpy(*d_kernel_out, h_kernel.data(), n * sizeof(float),
               cudaMemcpyHostToDevice);
}

// ---------------------------------------------------------------------------
// Helper: compute grid dimensions given image size and block size
// ---------------------------------------------------------------------------
static dim3 make_grid(int width, int height, int block_dim) {
    // Use ceiling division so every pixel is covered even when
    // image dimensions are not multiples of block_dim.
    return dim3((width  + block_dim - 1) / block_dim,
                (height + block_dim - 1) / block_dim);
}

// ---------------------------------------------------------------------------
// cuda_is_available
// ---------------------------------------------------------------------------
bool cuda_is_available() {
    int device_count = 0;
    cudaError_t err = cudaGetDeviceCount(&device_count);
    return (err == cudaSuccess && device_count > 0);
}

// ---------------------------------------------------------------------------
// grayscale_gpu
// ---------------------------------------------------------------------------
BenchmarkResult grayscale_gpu(const uint8_t* input, uint8_t* output,
                               int width, int height, BlockSize block_size)
{
    BenchmarkResult result = {};
    result.cuda_available = true;
    memset(result.error_message, 0, sizeof(result.error_message));

    if (!cuda_is_available()) {
        snprintf(result.error_message, sizeof(result.error_message),
                 "No CUDA-capable GPU found.");
        result.cuda_available = false;
        return result;
    }

    size_t input_bytes  = (size_t)width * height * 3;  // RGB
    size_t output_bytes = (size_t)width * height * 1;  // Grayscale

    unsigned char* d_input  = nullptr;
    unsigned char* d_output = nullptr;

    // ── Start end-to-end host timer ──────────────────────────────────────
    auto t0 = std::chrono::high_resolution_clock::now();

    // Allocate GPU memory
    CUDA_CHECK(cudaMalloc(&d_input,  input_bytes),  result, {});
    CUDA_CHECK(cudaMalloc(&d_output, output_bytes), result, {d_input});

    // Copy input from host (CPU RAM) to device (GPU VRAM)
    CUDA_CHECK(cudaMemcpy(d_input, input, input_bytes, cudaMemcpyHostToDevice),
               result, {d_input, d_output});

    // Configure thread block and grid dimensions.
    // dim3 is a CUDA type representing a 3D dimension; here we use 2D (x, y).
    int bsz = static_cast<int>(block_size);
    dim3 block(bsz, bsz);          // bsz × bsz threads per block
    dim3 grid = make_grid(width, height, bsz);

    // ── CUDA event timing (kernel only) ──────────────────────────────────
    cudaEvent_t start_ev, stop_ev;
    cudaEventCreate(&start_ev);
    cudaEventCreate(&stop_ev);

    cudaEventRecord(start_ev);  // Mark start on the GPU timeline

    // Launch the kernel — triple-angle-bracket syntax: <<<grid, block>>>
    kernel_grayscale<<<grid, block>>>(d_input, d_output, width, height);

    cudaEventRecord(stop_ev);   // Mark end on the GPU timeline
    cudaEventSynchronize(stop_ev); // Wait for GPU to finish

    // Retrieve kernel execution time from the GPU's hardware timer
    cudaEventElapsedTime(&result.kernel_time_ms, start_ev, stop_ev);
    cudaEventDestroy(start_ev);
    cudaEventDestroy(stop_ev);

    // Check for kernel launch errors
    CUDA_CHECK(cudaGetLastError(), result, {d_input, d_output});

    // Copy result from device (GPU VRAM) back to host (CPU RAM)
    CUDA_CHECK(cudaMemcpy(output, d_output, output_bytes, cudaMemcpyDeviceToHost),
               result, {d_input, d_output});

    // ── End end-to-end host timer ────────────────────────────────────────
    auto t1 = std::chrono::high_resolution_clock::now();
    result.total_time_ms = std::chrono::duration<float, std::milli>(t1 - t0).count();

    // Free GPU memory — always do this even if cudaMemcpy above succeeded
    cudaFree(d_input);
    cudaFree(d_output);

    return result;
}

// ---------------------------------------------------------------------------
// gaussian_blur_gpu
// ---------------------------------------------------------------------------
BenchmarkResult gaussian_blur_gpu(const uint8_t* input, uint8_t* output,
                                   int width, int height,
                                   int blur_radius, float sigma,
                                   BlockSize block_size)
{
    BenchmarkResult result = {};
    result.cuda_available = true;
    memset(result.error_message, 0, sizeof(result.error_message));

    if (!cuda_is_available()) {
        snprintf(result.error_message, sizeof(result.error_message),
                 "No CUDA-capable GPU found.");
        result.cuda_available = false;
        return result;
    }

    size_t bytes = (size_t)width * height * 3;

    unsigned char* d_input  = nullptr;
    unsigned char* d_output = nullptr;
    float*         d_kernel = nullptr;

    auto t0 = std::chrono::high_resolution_clock::now();

    CUDA_CHECK(cudaMalloc(&d_input,  bytes), result, {});
    CUDA_CHECK(cudaMalloc(&d_output, bytes), result, {d_input});
    CUDA_CHECK(cudaMemcpy(d_input, input, bytes, cudaMemcpyHostToDevice),
               result, {d_input, d_output});

    // Build the Gaussian kernel on host and upload it to device
    build_gaussian_kernel_device(&d_kernel, blur_radius, sigma);

    int bsz = static_cast<int>(block_size);
    dim3 block(bsz, bsz);
    dim3 grid = make_grid(width, height, bsz);

    cudaEvent_t start_ev, stop_ev;
    cudaEventCreate(&start_ev);
    cudaEventCreate(&stop_ev);
    cudaEventRecord(start_ev);

    kernel_gaussian_blur<<<grid, block>>>(d_input, d_output,
                                          width, height,
                                          d_kernel, blur_radius);

    cudaEventRecord(stop_ev);
    cudaEventSynchronize(stop_ev);
    cudaEventElapsedTime(&result.kernel_time_ms, start_ev, stop_ev);
    cudaEventDestroy(start_ev);
    cudaEventDestroy(stop_ev);

    CUDA_CHECK(cudaGetLastError(), result, {d_input, d_output, (uint8_t*)d_kernel});
    CUDA_CHECK(cudaMemcpy(output, d_output, bytes, cudaMemcpyDeviceToHost),
               result, {d_input, d_output, (uint8_t*)d_kernel});

    auto t1 = std::chrono::high_resolution_clock::now();
    result.total_time_ms = std::chrono::duration<float, std::milli>(t1 - t0).count();

    cudaFree(d_input);
    cudaFree(d_output);
    cudaFree(d_kernel);

    return result;
}

// ---------------------------------------------------------------------------
// sobel_edge_gpu
// ---------------------------------------------------------------------------
BenchmarkResult sobel_edge_gpu(const uint8_t* input, uint8_t* output,
                                int width, int height, BlockSize block_size)
{
    BenchmarkResult result = {};
    result.cuda_available = true;
    memset(result.error_message, 0, sizeof(result.error_message));

    if (!cuda_is_available()) {
        snprintf(result.error_message, sizeof(result.error_message),
                 "No CUDA-capable GPU found.");
        result.cuda_available = false;
        return result;
    }

    size_t bytes = (size_t)width * height * 1;  // Grayscale input and output

    unsigned char* d_input  = nullptr;
    unsigned char* d_output = nullptr;

    auto t0 = std::chrono::high_resolution_clock::now();

    CUDA_CHECK(cudaMalloc(&d_input,  bytes), result, {});
    CUDA_CHECK(cudaMalloc(&d_output, bytes), result, {d_input});
    CUDA_CHECK(cudaMemcpy(d_input, input, bytes, cudaMemcpyHostToDevice),
               result, {d_input, d_output});

    int bsz = static_cast<int>(block_size);
    dim3 block(bsz, bsz);
    dim3 grid = make_grid(width, height, bsz);

    cudaEvent_t start_ev, stop_ev;
    cudaEventCreate(&start_ev);
    cudaEventCreate(&stop_ev);
    cudaEventRecord(start_ev);

    kernel_sobel<<<grid, block>>>(d_input, d_output, width, height);

    cudaEventRecord(stop_ev);
    cudaEventSynchronize(stop_ev);
    cudaEventElapsedTime(&result.kernel_time_ms, start_ev, stop_ev);
    cudaEventDestroy(start_ev);
    cudaEventDestroy(stop_ev);

    CUDA_CHECK(cudaGetLastError(), result, {d_input, d_output});
    CUDA_CHECK(cudaMemcpy(output, d_output, bytes, cudaMemcpyDeviceToHost),
               result, {d_input, d_output});

    auto t1 = std::chrono::high_resolution_clock::now();
    result.total_time_ms = std::chrono::duration<float, std::milli>(t1 - t0).count();

    cudaFree(d_input);
    cudaFree(d_output);

    return result;
}

// ---------------------------------------------------------------------------
// sharpen_gpu
// ---------------------------------------------------------------------------
BenchmarkResult sharpen_gpu(const uint8_t* input, uint8_t* output,
                             int width, int height, BlockSize block_size)
{
    BenchmarkResult result = {};
    result.cuda_available = true;
    memset(result.error_message, 0, sizeof(result.error_message));

    if (!cuda_is_available()) {
        snprintf(result.error_message, sizeof(result.error_message),
                 "No CUDA-capable GPU found.");
        result.cuda_available = false;
        return result;
    }

    size_t bytes = (size_t)width * height * 3;

    unsigned char* d_input  = nullptr;
    unsigned char* d_output = nullptr;

    auto t0 = std::chrono::high_resolution_clock::now();

    CUDA_CHECK(cudaMalloc(&d_input,  bytes), result, {});
    CUDA_CHECK(cudaMalloc(&d_output, bytes), result, {d_input});
    CUDA_CHECK(cudaMemcpy(d_input, input, bytes, cudaMemcpyHostToDevice),
               result, {d_input, d_output});

    int bsz = static_cast<int>(block_size);
    dim3 block(bsz, bsz);
    dim3 grid = make_grid(width, height, bsz);

    cudaEvent_t start_ev, stop_ev;
    cudaEventCreate(&start_ev);
    cudaEventCreate(&stop_ev);
    cudaEventRecord(start_ev);

    kernel_sharpen<<<grid, block>>>(d_input, d_output, width, height);

    cudaEventRecord(stop_ev);
    cudaEventSynchronize(stop_ev);
    cudaEventElapsedTime(&result.kernel_time_ms, start_ev, stop_ev);
    cudaEventDestroy(start_ev);
    cudaEventDestroy(stop_ev);

    CUDA_CHECK(cudaGetLastError(), result, {d_input, d_output});
    CUDA_CHECK(cudaMemcpy(output, d_output, bytes, cudaMemcpyDeviceToHost),
               result, {d_input, d_output});

    auto t1 = std::chrono::high_resolution_clock::now();
    result.total_time_ms = std::chrono::duration<float, std::milli>(t1 - t0).count();

    cudaFree(d_input);
    cudaFree(d_output);

    return result;
}
