/**
 * cpu_processing.h
 *
 * Declares the CPU-side image processing functions implemented in cpu_processing.cpp.
 *
 * Each function takes a raw byte array (row-major, packed RGB or grayscale),
 * its width and height in pixels, and (where relevant) processing parameters.
 * All output arrays are assumed to be pre-allocated by the caller.
 *
 * These implementations run entirely on the host CPU.  They serve two purposes:
 *   1. Provide a correct reference for validating CUDA output.
 *   2. Provide the baseline execution time for speedup calculations.
 */

#pragma once

#include <cstdint>   // uint8_t
#include <cstddef>   // size_t

// ---------------------------------------------------------------------------
// Grayscale Conversion
// ---------------------------------------------------------------------------

/**
 * grayscale_cpu
 *
 * Converts an RGB image to a single-channel grayscale image using the
 * standard luminance-weighted formula:
 *
 *   Gray = 0.299*R + 0.587*G + 0.114*B
 *
 * The weights account for human eye sensitivity — we perceive green
 * most strongly and blue least strongly.
 *
 * @param input   Pointer to packed RGB pixel data (width * height * 3 bytes).
 * @param output  Pointer to output grayscale data  (width * height * 1 byte).
 * @param width   Image width in pixels.
 * @param height  Image height in pixels.
 */
void grayscale_cpu(const uint8_t* input, uint8_t* output,
                   int width, int height);

// ---------------------------------------------------------------------------
// Gaussian Blur
// ---------------------------------------------------------------------------

/**
 * gaussian_blur_cpu
 *
 * Applies a Gaussian blur by convolving the image with a Gaussian kernel of
 * the given radius.  Each output pixel is a weighted average of its
 * neighbourhood — pixels close to the centre receive higher weight.
 *
 * Boundary pixels are handled with clamp-to-edge: coordinates that fall
 * outside the image are clamped to the nearest valid coordinate.
 *
 * @param input       Pointer to packed RGB input  (width * height * 3 bytes).
 * @param output      Pointer to packed RGB output (width * height * 3 bytes).
 * @param width       Image width in pixels.
 * @param height      Image height in pixels.
 * @param blur_radius Radius of the Gaussian kernel (kernel size = 2*radius+1).
 * @param sigma       Standard deviation of the Gaussian distribution.
 */
void gaussian_blur_cpu(const uint8_t* input, uint8_t* output,
                       int width, int height,
                       int blur_radius, float sigma);

// ---------------------------------------------------------------------------
// Sobel Edge Detection
// ---------------------------------------------------------------------------

/**
 * sobel_edge_cpu
 *
 * Detects edges in a grayscale image using Sobel convolution kernels.
 * Two 3x3 kernels are applied — one for horizontal gradients (Gx) and one
 * for vertical gradients (Gy) — and the edge magnitude is:
 *
 *   Magnitude = sqrt(Gx^2 + Gy^2)
 *
 * Strong magnitude values indicate sharp intensity transitions (edges).
 *
 * @param input   Pointer to single-channel grayscale input  (width * height bytes).
 * @param output  Pointer to single-channel grayscale output (width * height bytes).
 * @param width   Image width in pixels.
 * @param height  Image height in pixels.
 */
void sobel_edge_cpu(const uint8_t* input, uint8_t* output,
                    int width, int height);

// ---------------------------------------------------------------------------
// Image Sharpening
// ---------------------------------------------------------------------------

/**
 * sharpen_cpu
 *
 * Sharpens an RGB image by convolving it with a 3x3 sharpening kernel
 * that amplifies high-frequency (edge) information.
 * Output pixel values are clamped to [0, 255] to prevent overflow.
 *
 * @param input   Pointer to packed RGB input  (width * height * 3 bytes).
 * @param output  Pointer to packed RGB output (width * height * 3 bytes).
 * @param width   Image width in pixels.
 * @param height  Image height in pixels.
 */
void sharpen_cpu(const uint8_t* input, uint8_t* output,
                 int width, int height);
