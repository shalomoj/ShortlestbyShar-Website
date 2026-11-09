"""
test_processing.py

Unit tests for the Python-layer image processing functions.

Tests verify:
  1. Grayscale conversion produces a valid single-channel output.
  2. Gaussian blur preserves image dimensions.
  3. Sobel edge detection produces valid output on a synthetic test image.
  4. Image sharpening preserves image dimensions.
  5. CPU implementations produce numerically valid results.
  6. Invalid inputs are handled gracefully.
  7. Benchmark results are positive and not fabricated.

Run with:
    pytest tests/test_processing.py -v

The tests do NOT require a GPU.  CPU-only operation is fully testable.
"""

import sys
import os

# Ensure the python/ package is importable from the tests/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

import numpy as np
import pytest

from processing_interface import (
    _cpu_grayscale,
    _cpu_gaussian_blur,
    _cpu_sobel,
    _cpu_sharpen,
    process_grayscale,
    process_gaussian_blur,
    process_sobel,
    process_sharpen,
    cuda_available,
    _OPENCV_AVAILABLE,
)


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_rgb_64():
    """64×64 synthetic RGB image with distinct regions for edge detection tests."""
    img = np.zeros((64, 64, 3), dtype=np.uint8)
    img[10:50, 10:30, :] = [200, 80, 80]    # Red block
    img[10:50, 34:54, :] = [80, 200, 80]    # Green block
    return img


@pytest.fixture
def sample_rgb_256():
    """256×256 synthetic RGB image for performance tests."""
    rng = np.random.default_rng(42)
    return rng.integers(0, 256, (256, 256, 3), dtype=np.uint8)


@pytest.fixture
def sample_gray_64(sample_rgb_64):
    """64×64 synthetic grayscale image derived from sample_rgb_64."""
    return _cpu_grayscale(sample_rgb_64)


# ──────────────────────────────────────────────────────────────────────────────
# Test: Grayscale Conversion
# ──────────────────────────────────────────────────────────────────────────────

class TestGrayscale:
    def test_output_shape(self, sample_rgb_64):
        """Output must be 2D (height × width) — single channel."""
        gray = _cpu_grayscale(sample_rgb_64)
        assert gray.ndim == 2, "Grayscale output must be 2D"
        assert gray.shape == (64, 64)

    def test_output_dtype(self, sample_rgb_64):
        """Output values must be uint8 in [0, 255]."""
        gray = _cpu_grayscale(sample_rgb_64)
        assert gray.dtype == np.uint8
        assert gray.min() >= 0
        assert gray.max() <= 255

    def test_pure_red_pixel(self):
        """A pure red pixel [255, 0, 0] should give approximately 76 (0.299*255)."""
        img = np.array([[[255, 0, 0]]], dtype=np.uint8)
        gray = _cpu_grayscale(img)
        expected = int(0.299 * 255)
        assert abs(int(gray[0, 0]) - expected) <= 1, (
            f"Expected ~{expected}, got {gray[0, 0]}"
        )

    def test_pure_green_pixel(self):
        """A pure green pixel [0, 255, 0] should give approximately 150 (0.587*255)."""
        img = np.array([[[0, 255, 0]]], dtype=np.uint8)
        gray = _cpu_grayscale(img)
        expected = int(0.587 * 255)
        assert abs(int(gray[0, 0]) - expected) <= 1

    def test_white_pixel(self):
        """A white pixel [255, 255, 255] should give 255."""
        img = np.array([[[255, 255, 255]]], dtype=np.uint8)
        gray = _cpu_grayscale(img)
        assert gray[0, 0] == 255

    def test_black_pixel(self):
        """A black pixel [0, 0, 0] should give 0."""
        img = np.array([[[0, 0, 0]]], dtype=np.uint8)
        gray = _cpu_grayscale(img)
        assert gray[0, 0] == 0

    def test_process_grayscale_result(self, sample_rgb_64):
        """process_grayscale returns a valid ProcessingResult."""
        res = process_grayscale(sample_rgb_64, use_gpu=False, iterations=2, warmup=1)
        assert res.output_image is not None
        assert res.output_image.shape == (64, 64)
        assert res.cpu_time_ms > 0, "CPU time must be positive"
        assert res.width  == 64
        assert res.height == 64
        assert res.num_pixels == 64 * 64


# ──────────────────────────────────────────────────────────────────────────────
# Test: Gaussian Blur
# ──────────────────────────────────────────────────────────────────────────────

class TestGaussianBlur:
    def test_preserves_dimensions(self, sample_rgb_64):
        """Gaussian blur must not change image dimensions."""
        blurred = _cpu_gaussian_blur(sample_rgb_64, radius=3, sigma=1.5)
        assert blurred.shape == sample_rgb_64.shape

    def test_preserves_dtype(self, sample_rgb_64):
        """Output must be uint8."""
        blurred = _cpu_gaussian_blur(sample_rgb_64, radius=3, sigma=1.5)
        assert blurred.dtype == np.uint8

    def test_values_in_range(self, sample_rgb_64):
        """All output pixel values must be in [0, 255]."""
        blurred = _cpu_gaussian_blur(sample_rgb_64, radius=3, sigma=1.5)
        assert blurred.min() >= 0
        assert blurred.max() <= 255

    def test_blurring_reduces_variance(self, sample_rgb_256):
        """Blurring a noisy image should reduce pixel-level variance."""
        blurred = _cpu_gaussian_blur(sample_rgb_256, radius=5, sigma=2.0)
        var_before = np.var(sample_rgb_256.astype(float))
        var_after  = np.var(blurred.astype(float))
        assert var_after < var_before, (
            "Gaussian blur should reduce variance in a noisy image"
        )

    def test_radius_one(self, sample_rgb_64):
        """Blur with radius=1 should still work without errors."""
        blurred = _cpu_gaussian_blur(sample_rgb_64, radius=1, sigma=0.5)
        assert blurred.shape == sample_rgb_64.shape

    def test_process_gaussian_blur_result(self, sample_rgb_64):
        """process_gaussian_blur returns a valid ProcessingResult."""
        res = process_gaussian_blur(sample_rgb_64, use_gpu=False,
                                     blur_radius=3, sigma=1.5,
                                     iterations=2, warmup=1)
        assert res.output_image is not None
        assert res.output_image.shape == sample_rgb_64.shape
        assert res.cpu_time_ms > 0


# ──────────────────────────────────────────────────────────────────────────────
# Test: Sobel Edge Detection
# ──────────────────────────────────────────────────────────────────────────────

class TestSobel:
    def test_output_shape(self, sample_gray_64):
        """Sobel output must have the same spatial dimensions as input (single channel)."""
        edges = _cpu_sobel(sample_gray_64)
        assert edges.shape == sample_gray_64.shape

    def test_output_dtype(self, sample_gray_64):
        """Output must be uint8."""
        edges = _cpu_sobel(sample_gray_64)
        assert edges.dtype == np.uint8

    def test_detects_edges(self):
        """
        On an image with a sharp vertical edge, Sobel should produce
        strong response at the edge and near-zero elsewhere.
        """
        # Create a 32×32 image with a sharp vertical edge in the middle
        img = np.zeros((32, 32), dtype=np.uint8)
        img[:, 16:] = 200   # Right half is bright

        edges = _cpu_sobel(img)

        # The column at x=16 (the edge) should have the highest average response
        edge_col_mean = float(edges[:, 15:18].mean())
        flat_col_mean = float(edges[:, 2:12].mean())

        assert edge_col_mean > flat_col_mean, (
            f"Sobel should detect the vertical edge "
            f"(edge_mean={edge_col_mean:.1f}, flat_mean={flat_col_mean:.1f})"
        )

    def test_uniform_image_zero_edges(self):
        """A completely uniform image should produce near-zero Sobel output."""
        img = np.full((32, 32), 128, dtype=np.uint8)
        edges = _cpu_sobel(img)
        # Interior pixels should be zero; borders may have small values due to clamping
        interior = edges[1:-1, 1:-1]
        assert interior.max() == 0, "Uniform image should have no edges"

    def test_process_sobel_result(self, sample_rgb_64):
        """process_sobel returns a valid ProcessingResult."""
        res = process_sobel(sample_rgb_64, use_gpu=False, iterations=2, warmup=1)
        assert res.output_image is not None
        assert res.output_image.shape == (64, 64)
        assert res.cpu_time_ms > 0


# ──────────────────────────────────────────────────────────────────────────────
# Test: Image Sharpening
# ──────────────────────────────────────────────────────────────────────────────

class TestSharpen:
    def test_preserves_dimensions(self, sample_rgb_64):
        """Sharpening must not change image dimensions."""
        sharpened = _cpu_sharpen(sample_rgb_64)
        assert sharpened.shape == sample_rgb_64.shape

    def test_preserves_dtype(self, sample_rgb_64):
        """Output must be uint8."""
        sharpened = _cpu_sharpen(sample_rgb_64)
        assert sharpened.dtype == np.uint8

    def test_values_in_range(self, sample_rgb_64):
        """Output pixel values must remain in [0, 255]."""
        sharpened = _cpu_sharpen(sample_rgb_64)
        assert sharpened.min() >= 0
        assert sharpened.max() <= 255

    def test_uniform_image_unchanged(self):
        """
        A perfectly uniform image (no edges) should be essentially unchanged
        by sharpening — the kernel sums to 0 for uniform regions, so the
        centre weight (5) plus surrounding (-1*4) = 1 → output ≈ input.
        """
        img = np.full((32, 32, 3), 100, dtype=np.uint8)
        sharpened = _cpu_sharpen(img)
        # Interior pixels should be identical to input (100)
        interior = sharpened[1:-1, 1:-1, :]
        assert np.all(interior == 100), "Uniform regions should be unchanged by sharpening"

    def test_process_sharpen_result(self, sample_rgb_64):
        """process_sharpen returns a valid ProcessingResult."""
        res = process_sharpen(sample_rgb_64, use_gpu=False, iterations=2, warmup=1)
        assert res.output_image is not None
        assert res.output_image.shape == sample_rgb_64.shape
        assert res.cpu_time_ms > 0


# ──────────────────────────────────────────────────────────────────────────────
# Test: Input Validation / Error Handling
# ──────────────────────────────────────────────────────────────────────────────

class TestInputHandling:
    def test_single_pixel_grayscale(self):
        """Processing a 1×1 image must not crash."""
        img = np.array([[[128, 64, 32]]], dtype=np.uint8)
        gray = _cpu_grayscale(img)
        assert gray.shape == (1, 1)

    def test_single_pixel_sharpen(self):
        """Sharpening a 1×1 image must not crash."""
        img = np.array([[[128, 64, 32]]], dtype=np.uint8)
        sharpened = _cpu_sharpen(img)
        assert sharpened.shape == (1, 1, 3)

    def test_tall_image(self):
        """Non-square tall image (100×10) must be handled correctly."""
        img = np.random.randint(0, 256, (100, 10, 3), dtype=np.uint8)
        gray = _cpu_grayscale(img)
        assert gray.shape == (100, 10)

    def test_wide_image(self):
        """Non-square wide image (10×100) must be handled correctly."""
        img = np.random.randint(0, 256, (10, 100, 3), dtype=np.uint8)
        blurred = _cpu_gaussian_blur(img, radius=2, sigma=1.0)
        assert blurred.shape == (10, 100, 3)


# ──────────────────────────────────────────────────────────────────────────────
# Test: Benchmark Validity
# ──────────────────────────────────────────────────────────────────────────────

class TestBenchmarks:
    def test_cpu_time_positive(self, sample_rgb_64):
        """CPU execution time must always be a positive number."""
        res = process_grayscale(sample_rgb_64, use_gpu=False, iterations=3, warmup=1)
        assert res.cpu_time_ms > 0, "CPU time must be > 0"

    def test_num_pixels_correct(self, sample_rgb_64):
        """num_pixels must equal width × height."""
        res = process_grayscale(sample_rgb_64, use_gpu=False)
        assert res.num_pixels == res.width * res.height

    def test_speedup_zero_without_gpu(self, sample_rgb_64):
        """Speedup must be 0 (not fabricated) when GPU is not available."""
        res = process_grayscale(sample_rgb_64, use_gpu=False)
        if not res.gpu_available:
            assert res.speedup == 0.0, (
                "Speedup must not be fabricated when GPU is unavailable"
            )

    def test_backend_label_cpu(self, sample_rgb_64):
        """Backend label must be 'python_cpu' when GPU is not requested."""
        res = process_grayscale(sample_rgb_64, use_gpu=False)
        assert "cpu" in res.backend.lower(), (
            f"Backend should contain 'cpu', got '{res.backend}'"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Test: GPU (skipped when CUDA unavailable)
# ──────────────────────────────────────────────────────────────────────────────

class TestGPU:
    @pytest.mark.skipif(not cuda_available(), reason="No CUDA GPU available")
    def test_gpu_grayscale_matches_cpu(self, sample_rgb_64):
        """
        GPU grayscale output must match CPU output within tolerance of ±2 per pixel.
        Small differences are expected due to floating-point rounding on GPU.
        """
        cpu_result = process_grayscale(sample_rgb_64, use_gpu=False, iterations=1, warmup=0)
        gpu_result = process_grayscale(sample_rgb_64, use_gpu=True,  iterations=1, warmup=0)

        assert gpu_result.gpu_available, "GPU should be available for this test"

        diff = np.abs(cpu_result.output_image.astype(np.int32) -
                      gpu_result.output_image.astype(np.int32))
        assert diff.max() <= 2, (
            f"CPU and GPU grayscale outputs differ by more than 2 at some pixel "
            f"(max diff = {diff.max()})"
        )

    @pytest.mark.skipif(not cuda_available(), reason="No CUDA GPU available")
    def test_gpu_sobel_matches_cpu(self, sample_rgb_64):
        """GPU Sobel output must match CPU output within tolerance of ±5 per pixel."""
        cpu_result = process_sobel(sample_rgb_64, use_gpu=False, iterations=1, warmup=0)
        gpu_result = process_sobel(sample_rgb_64, use_gpu=True,  iterations=1, warmup=0)

        diff = np.abs(cpu_result.output_image.astype(np.int32) -
                      gpu_result.output_image.astype(np.int32))
        assert diff.max() <= 5, (
            f"CPU and GPU Sobel outputs differ by more than 5 (max diff = {diff.max()})"
        )

    @pytest.mark.skipif(not cuda_available(), reason="No CUDA GPU available")
    def test_gpu_kernel_time_positive(self, sample_rgb_64):
        """GPU kernel time must be a positive number when GPU is available."""
        res = process_grayscale(sample_rgb_64, use_gpu=True, iterations=3, warmup=1)
        if res.gpu_available:
            assert res.gpu_kernel_ms > 0
            assert res.gpu_total_ms  > 0
            assert res.gpu_total_ms  >= res.gpu_kernel_ms

    @pytest.mark.skipif(not cuda_available(), reason="No CUDA GPU available")
    def test_gpu_speedup_calculation(self, sample_rgb_256):
        """Speedup must equal cpu_time / gpu_kernel_time when both are available."""
        res = process_grayscale(sample_rgb_256, use_gpu=True, iterations=5, warmup=2)
        if res.gpu_available and res.gpu_kernel_ms > 0:
            expected_speedup = res.cpu_time_ms / res.gpu_kernel_ms
            assert abs(res.speedup - expected_speedup) < 0.01, (
                "Speedup calculation mismatch"
            )
