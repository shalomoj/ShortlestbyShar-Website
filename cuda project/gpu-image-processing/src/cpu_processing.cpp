/**
 * cpu_processing.cpp
 *
 * CPU implementations of four image-processing operations:
 *   - Grayscale conversion
 *   - Gaussian blur
 *   - Sobel edge detection
 *   - Image sharpening
 *
 * These serve as both the correctness reference and the performance baseline
 * that the CUDA GPU implementations are compared against.
 *
 * All operations work on raw uint8_t pixel buffers.  Pixel layout:
 *   RGB images:       [R0, G0, B0, R1, G1, B1, ...]  (3 bytes per pixel)
 *   Grayscale images: [Y0, Y1, Y2, ...]               (1 byte per pixel)
 *
 * Indexing: pixel at column x, row y has index (y * width + x).
 */

#include "cpu_processing.h"

#include <cmath>    // sqrt, exp
#include <vector>   // std::vector (used for kernel allocation)
#include <algorithm> // std::clamp

// ---------------------------------------------------------------------------
// Helper: clamp a float to [0, 255] and cast to uint8_t
// ---------------------------------------------------------------------------
static inline uint8_t clamp_byte(float v) {
    if (v < 0.0f)   return 0;
    if (v > 255.0f) return 255;
    return static_cast<uint8_t>(v);
}

// ---------------------------------------------------------------------------
// Helper: clamp integer coordinate to [0, max_val]
//         Used for boundary handling (clamp-to-edge).
// ---------------------------------------------------------------------------
static inline int clamp_coord(int val, int max_val) {
    if (val < 0)        return 0;
    if (val >= max_val) return max_val - 1;
    return val;
}

// ===========================================================================
// Grayscale Conversion
// ===========================================================================

void grayscale_cpu(const uint8_t* input, uint8_t* output,
                   int width, int height)
{
    // Process every pixel sequentially.
    // Each pixel is independent — this is why GPU parallelism works so well
    // for this operation: there are no data dependencies between pixels.
    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            // Calculate the flat index for this pixel in the RGB buffer.
            // Each pixel occupies 3 bytes (R, G, B) in the input.
            int idx_rgb  = (y * width + x) * 3;
            int idx_gray =  y * width + x;      // 1 byte per pixel in output

            uint8_t r = input[idx_rgb + 0];
            uint8_t g = input[idx_rgb + 1];
            uint8_t b = input[idx_rgb + 2];

            // Luminance-weighted formula (ITU-R BT.601):
            //   Green contributes most because the human eye is most sensitive to it.
            //   Blue contributes least.
            output[idx_gray] = clamp_byte(0.299f * r + 0.587f * g + 0.114f * b);
        }
    }
}

// ===========================================================================
// Gaussian Blur
// ===========================================================================

void gaussian_blur_cpu(const uint8_t* input, uint8_t* output,
                       int width, int height,
                       int blur_radius, float sigma)
{
    // -----------------------------------------------------------------------
    // Build the 1D Gaussian kernel.
    //
    // A Gaussian kernel is separable: a 2D Gaussian blur can be decomposed
    // into two 1D passes (horizontal then vertical), but here we use the
    // simpler full 2D kernel for clarity since this is the CPU reference.
    //
    // Gaussian function: G(x,y) = exp(-(x²+y²) / (2*sigma²))
    // -----------------------------------------------------------------------
    int kernel_size = 2 * blur_radius + 1;  // Always an odd number

    // Flat 2D kernel stored as a vector (row-major)
    std::vector<float> kernel(kernel_size * kernel_size);
    float kernel_sum = 0.0f;  // Used to normalise so weights sum to 1

    for (int ky = -blur_radius; ky <= blur_radius; ++ky) {
        for (int kx = -blur_radius; kx <= blur_radius; ++kx) {
            float value = std::exp(-(kx*kx + ky*ky) / (2.0f * sigma * sigma));
            int kid = (ky + blur_radius) * kernel_size + (kx + blur_radius);
            kernel[kid] = value;
            kernel_sum += value;
        }
    }

    // Normalise the kernel so all weights sum to 1 (prevents brightening/darkening)
    for (float& w : kernel) {
        w /= kernel_sum;
    }

    // -----------------------------------------------------------------------
    // Apply the 2D Gaussian kernel to every pixel.
    // For each output pixel, accumulate the weighted sum of neighbours.
    // -----------------------------------------------------------------------
    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {

            float acc_r = 0.0f, acc_g = 0.0f, acc_b = 0.0f;

            // Iterate over the kernel window centred at (x, y)
            for (int ky = -blur_radius; ky <= blur_radius; ++ky) {
                for (int kx = -blur_radius; kx <= blur_radius; ++kx) {
                    // Clamp coordinates to handle image borders
                    int nx = clamp_coord(x + kx, width);
                    int ny = clamp_coord(y + ky, height);

                    int src_idx = (ny * width + nx) * 3;
                    int kid = (ky + blur_radius) * kernel_size + (kx + blur_radius);

                    acc_r += kernel[kid] * input[src_idx + 0];
                    acc_g += kernel[kid] * input[src_idx + 1];
                    acc_b += kernel[kid] * input[src_idx + 2];
                }
            }

            int dst_idx = (y * width + x) * 3;
            output[dst_idx + 0] = clamp_byte(acc_r);
            output[dst_idx + 1] = clamp_byte(acc_g);
            output[dst_idx + 2] = clamp_byte(acc_b);
        }
    }
}

// ===========================================================================
// Sobel Edge Detection
// ===========================================================================

void sobel_edge_cpu(const uint8_t* input, uint8_t* output,
                    int width, int height)
{
    // -----------------------------------------------------------------------
    // Sobel kernels:
    //
    //   Gx detects horizontal edges (vertical gradient):
    //   [ -1  0  +1 ]
    //   [ -2  0  +2 ]
    //   [ -1  0  +1 ]
    //
    //   Gy detects vertical edges (horizontal gradient):
    //   [ -1 -2  -1 ]
    //   [  0  0   0 ]
    //   [ +1 +2  +1 ]
    //
    // The centre weighting (±2) improves noise resistance.
    // -----------------------------------------------------------------------
    const int Kx[3][3] = { {-1, 0, +1},
                            {-2, 0, +2},
                            {-1, 0, +1} };

    const int Ky[3][3] = { {-1, -2, -1},
                            { 0,  0,  0},
                            {+1, +2, +1} };

    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {

            float gx = 0.0f, gy = 0.0f;

            // Convolve the 3×3 kernel window centred at (x, y)
            for (int ky = -1; ky <= 1; ++ky) {
                for (int kx = -1; kx <= 1; ++kx) {
                    int nx = clamp_coord(x + kx, width);
                    int ny = clamp_coord(y + ky, height);

                    uint8_t pixel = input[ny * width + nx]; // grayscale input

                    gx += Kx[ky + 1][kx + 1] * pixel;
                    gy += Ky[ky + 1][kx + 1] * pixel;
                }
            }

            // Edge magnitude: the Euclidean length of the gradient vector
            float magnitude = std::sqrt(gx * gx + gy * gy);
            output[y * width + x] = clamp_byte(magnitude);
        }
    }
}

// ===========================================================================
// Image Sharpening
// ===========================================================================

void sharpen_cpu(const uint8_t* input, uint8_t* output,
                 int width, int height)
{
    // -----------------------------------------------------------------------
    // Sharpening kernel (Laplacian-based):
    //
    //   [  0  -1   0 ]
    //   [ -1   5  -1 ]
    //   [  0  -1   0 ]
    //
    // The centre weight (5) emphasises the current pixel.
    // The -1 weights subtract the average of neighbours, amplifying edges.
    // This is equivalent to: output = input + (input - blurred_input).
    // -----------------------------------------------------------------------
    const int kernel[3][3] = { { 0, -1,  0},
                                {-1,  5, -1},
                                { 0, -1,  0} };

    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {

            float acc_r = 0.0f, acc_g = 0.0f, acc_b = 0.0f;

            for (int ky = -1; ky <= 1; ++ky) {
                for (int kx = -1; kx <= 1; ++kx) {
                    int nx = clamp_coord(x + kx, width);
                    int ny = clamp_coord(y + ky, height);

                    int src_idx = (ny * width + nx) * 3;
                    int k = kernel[ky + 1][kx + 1];

                    acc_r += k * input[src_idx + 0];
                    acc_g += k * input[src_idx + 1];
                    acc_b += k * input[src_idx + 2];
                }
            }

            // Clamp to [0, 255] — sharpening can produce values outside this range
            int dst_idx = (y * width + x) * 3;
            output[dst_idx + 0] = clamp_byte(acc_r);
            output[dst_idx + 1] = clamp_byte(acc_g);
            output[dst_idx + 2] = clamp_byte(acc_b);
        }
    }
}
