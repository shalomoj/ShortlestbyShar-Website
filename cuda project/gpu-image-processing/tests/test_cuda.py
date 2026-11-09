"""
test_cuda.py

Tests specifically for CUDA availability, GPU device properties, and
the accuracy / consistency of CUDA kernel outputs vs CPU reference outputs.

All GPU tests are decorated with @pytest.mark.skipif(not cuda_available())
so the test suite still passes (with skips) on machines without a CUDA GPU.

Run with:
    pytest tests/test_cuda.py -v

Or to run only on machines with a GPU (fail if GPU not available):
    pytest tests/test_cuda.py -v -m "not skip"
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

import numpy as np
import pytest
import time

from processing_interface import (
    cuda_available,
    get_gpu_info,
    process_grayscale,
    process_sobel,
    process_sharpen,
    _cpu_grayscale,
    _cpu_sobel,
    _cpu_sharpen,
    _PYCUDA_AVAILABLE,
)


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def test_image_128():
    """128×128 RGB image with checkerboard pattern — good for edge detection."""
    img = np.zeros((128, 128, 3), dtype=np.uint8)
    for y in range(0, 128, 16):
        for x in range(0, 128, 16):
            if (y // 16 + x // 16) % 2 == 0:
                img[y:y+16, x:x+16] = [200, 200, 200]
    return img


@pytest.fixture
def test_image_512():
    """512×512 random RGB image for performance benchmarking."""
    rng = np.random.default_rng(0)
    return rng.integers(0, 256, (512, 512, 3), dtype=np.uint8)


# ──────────────────────────────────────────────────────────────────────────────
# Test: CUDA Detection
# ──────────────────────────────────────────────────────────────────────────────

class TestCUDADetection:
    def test_cuda_available_returns_bool(self):
        """cuda_available() must return a bool, never raise an exception."""
        result = cuda_available()
        assert isinstance(result, bool)

    def test_get_gpu_info_returns_dict(self):
        """get_gpu_info() must return a dict even when GPU is absent."""
        info = get_gpu_info()
        assert isinstance(info, dict)

    @pytest.mark.skipif(not cuda_available(), reason="No CUDA GPU available")
    def test_gpu_info_has_name(self):
        """When GPU is available, info dict must contain a non-empty name."""
        info = get_gpu_info()
        assert "name" in info
        assert len(info["name"]) > 0

    @pytest.mark.skipif(not cuda_available(), reason="No CUDA GPU available")
    def test_gpu_memory_positive(self):
        """GPU total memory must be a positive number."""
        info = get_gpu_info()
        assert info.get("total_memory_mb", 0) > 0

    @pytest.mark.skipif(not cuda_available(), reason="No CUDA GPU available")
    def test_compute_capability_format(self):
        """Compute capability should be a string like '7.5'."""
        info = get_gpu_info()
        cc = info.get("compute_capability", "")
        assert "." in cc, f"Compute capability should contain '.', got '{cc}'"


# ──────────────────────────────────────────────────────────────────────────────
# Test: PyCUDA / CUDA Kernel Correctness
# ──────────────────────────────────────────────────────────────────────────────

class TestCUDAKernelCorrectness:
    """
    These tests check that GPU kernel outputs match CPU reference outputs
    within a small numerical tolerance.

    Tolerances are loose (max ±2 per pixel for grayscale, ±5 for Sobel)
    because GPU floating-point operations can produce slightly different
    rounding than CPU operations, especially for convolution.
    """

    @pytest.mark.skipif(not cuda_available() or not _PYCUDA_AVAILABLE,
                        reason="PyCUDA or CUDA GPU not available")
    def test_grayscale_cpu_gpu_consistency(self, test_image_128):
        """GPU grayscale must match CPU reference within ±2 per pixel."""
        cpu_res = process_grayscale(test_image_128, use_gpu=False, iterations=1, warmup=0)
        gpu_res = process_grayscale(test_image_128, use_gpu=True,  iterations=1, warmup=0)

        if not gpu_res.gpu_available:
            pytest.skip(f"GPU not available: {gpu_res.error}")

        diff = np.abs(cpu_res.output_image.astype(np.int32) -
                      gpu_res.output_image.astype(np.int32))

        assert diff.max() <= 2, (
            f"Grayscale CPU/GPU max pixel diff = {diff.max()} (tolerance = 2)"
        )
        mean_diff = diff.mean()
        assert mean_diff < 0.5, (
            f"Grayscale CPU/GPU mean pixel diff = {mean_diff:.3f} (expected < 0.5)"
        )

    @pytest.mark.skipif(not cuda_available() or not _PYCUDA_AVAILABLE,
                        reason="PyCUDA or CUDA GPU not available")
    def test_sobel_cpu_gpu_consistency(self, test_image_128):
        """GPU Sobel must match CPU reference within ±5 per pixel."""
        cpu_res = process_sobel(test_image_128, use_gpu=False, iterations=1, warmup=0)
        gpu_res = process_sobel(test_image_128, use_gpu=True,  iterations=1, warmup=0)

        if not gpu_res.gpu_available:
            pytest.skip(f"GPU not available: {gpu_res.error}")

        diff = np.abs(cpu_res.output_image.astype(np.int32) -
                      gpu_res.output_image.astype(np.int32))

        assert diff.max() <= 5, (
            f"Sobel CPU/GPU max pixel diff = {diff.max()} (tolerance = 5)"
        )

    @pytest.mark.skipif(not cuda_available() or not _PYCUDA_AVAILABLE,
                        reason="PyCUDA or CUDA GPU not available")
    def test_sharpen_cpu_gpu_consistency(self, test_image_128):
        """GPU sharpen must match CPU reference within ±3 per pixel."""
        cpu_res = process_sharpen(test_image_128, use_gpu=False, iterations=1, warmup=0)
        gpu_res = process_sharpen(test_image_128, use_gpu=True,  iterations=1, warmup=0)

        if not gpu_res.gpu_available:
            pytest.skip(f"GPU not available: {gpu_res.error}")

        diff = np.abs(cpu_res.output_image.astype(np.int32) -
                      gpu_res.output_image.astype(np.int32))

        assert diff.max() <= 3, (
            f"Sharpen CPU/GPU max pixel diff = {diff.max()} (tolerance = 3)"
        )

    @pytest.mark.skipif(not cuda_available() or not _PYCUDA_AVAILABLE,
                        reason="PyCUDA or CUDA GPU not available")
    def test_gpu_output_dtype(self, test_image_128):
        """GPU output must be uint8 (same as CPU output)."""
        res = process_grayscale(test_image_128, use_gpu=True, iterations=1, warmup=0)
        if res.gpu_available:
            assert res.output_image.dtype == np.uint8

    @pytest.mark.skipif(not cuda_available() or not _PYCUDA_AVAILABLE,
                        reason="PyCUDA or CUDA GPU not available")
    def test_gpu_output_shape_grayscale(self, test_image_128):
        """GPU grayscale output shape must be (H, W)."""
        res = process_grayscale(test_image_128, use_gpu=True, iterations=1, warmup=0)
        if res.gpu_available:
            assert res.output_image.shape == (128, 128)

    @pytest.mark.skipif(not cuda_available() or not _PYCUDA_AVAILABLE,
                        reason="PyCUDA or CUDA GPU not available")
    def test_gpu_output_shape_sobel(self, test_image_128):
        """GPU Sobel output shape must match input spatial dimensions."""
        res = process_sobel(test_image_128, use_gpu=True, iterations=1, warmup=0)
        if res.gpu_available:
            assert res.output_image.shape == (128, 128)


# ──────────────────────────────────────────────────────────────────────────────
# Test: CUDA Timing Integrity
# ──────────────────────────────────────────────────────────────────────────────

class TestCUDATiming:
    @pytest.mark.skipif(not cuda_available() or not _PYCUDA_AVAILABLE,
                        reason="PyCUDA or CUDA GPU not available")
    def test_gpu_kernel_time_is_positive(self, test_image_128):
        """GPU kernel time must be a positive number."""
        res = process_grayscale(test_image_128, use_gpu=True, iterations=3, warmup=1)
        if res.gpu_available:
            assert res.gpu_kernel_ms > 0.0, "GPU kernel time must be positive"

    @pytest.mark.skipif(not cuda_available() or not _PYCUDA_AVAILABLE,
                        reason="PyCUDA or CUDA GPU not available")
    def test_gpu_total_time_geq_kernel_time(self, test_image_128):
        """
        GPU total time (including transfers) must be >= kernel-only time.
        Memory transfers add overhead that is always non-negative.
        """
        res = process_grayscale(test_image_128, use_gpu=True, iterations=3, warmup=1)
        if res.gpu_available:
            assert res.gpu_total_ms >= res.gpu_kernel_ms, (
                "Total GPU time must be >= kernel-only time"
            )

    @pytest.mark.skipif(not cuda_available() or not _PYCUDA_AVAILABLE,
                        reason="PyCUDA or CUDA GPU not available")
    def test_speedup_calculation_correct(self, test_image_512):
        """
        Speedup must equal cpu_time / gpu_kernel_time within floating-point tolerance.
        Verifies that the speedup value is not hardcoded or fabricated.
        """
        res = process_grayscale(test_image_512, use_gpu=True, iterations=5, warmup=2)
        if res.gpu_available and res.gpu_kernel_ms > 0:
            expected = res.cpu_time_ms / res.gpu_kernel_ms
            assert abs(res.speedup - expected) < 0.01, (
                f"Speedup mismatch: stored={res.speedup:.4f}, "
                f"recomputed={expected:.4f}"
            )

    @pytest.mark.skipif(not cuda_available() or not _PYCUDA_AVAILABLE,
                        reason="PyCUDA or CUDA GPU not available")
    def test_cpu_time_is_positive(self, test_image_512):
        """CPU time must always be positive, even when GPU is used."""
        res = process_grayscale(test_image_512, use_gpu=True, iterations=3, warmup=1)
        assert res.cpu_time_ms > 0.0


# ──────────────────────────────────────────────────────────────────────────────
# Test: Block Size Variation
# ──────────────────────────────────────────────────────────────────────────────

class TestBlockSizes:
    """
    Verifies that different CUDA block sizes produce equivalent results.
    GPU output should not change significantly with block size — block size
    affects performance but not correctness.
    """

    @pytest.mark.skipif(not cuda_available() or not _PYCUDA_AVAILABLE,
                        reason="PyCUDA or CUDA GPU not available")
    @pytest.mark.parametrize("bsz", [8, 16, 32])
    def test_block_size_correctness(self, test_image_128, bsz):
        """All block sizes must produce output within ±2 of the CPU reference."""
        cpu_res = process_grayscale(test_image_128, use_gpu=False, iterations=1, warmup=0)
        gpu_res = process_grayscale(test_image_128, use_gpu=True,
                                     block_size=bsz, iterations=1, warmup=0)

        if not gpu_res.gpu_available:
            pytest.skip("GPU not available")

        diff = np.abs(cpu_res.output_image.astype(np.int32) -
                      gpu_res.output_image.astype(np.int32))
        assert diff.max() <= 2, (
            f"Block size {bsz}×{bsz}: max pixel diff = {diff.max()} (tolerance = 2)"
        )
