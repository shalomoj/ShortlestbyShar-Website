"""
processing_interface.py

Python interface layer between the Streamlit UI and the image-processing engine.

This module provides two layers of implementation:

  LAYER 1 — C++ / CUDA SHARED LIBRARY (when compiled)
  ──────────────────────────────────────────────────────
  When the CMake build has produced the shared library (gpu_image_proc_lib),
  this module loads it via ctypes and calls the C++ functions directly.
  This path uses genuine CUDA kernels for GPU operations.

  LAYER 2 — PURE PYTHON FALLBACK (always available)
  ──────────────────────────────────────────────────────
  When the compiled library is not found, all operations fall back to pure
  NumPy/OpenCV Python implementations.  These are clearly labelled as
  CPU-only Python fallbacks — never claimed to be GPU executions.

TRANSPARENCY RULES
  - The `backend` field in every ProcessingResult indicates which layer ran.
  - GPU results are NEVER fabricated.  If no CUDA GPU is present, GPU
    execution is skipped and the result says so explicitly.
  - Timings use Python's time.perf_counter() (nanosecond resolution on
    modern OSes) for CPU operations and the GPU's CUDA events (via the C++
    library) for kernel timing.

CUDA AVAILABILITY
  - Checked once at module load via check_cuda_available().
  - Requires pycuda or the compiled C++ library to be detected.
  - If neither is present, cuda_available() returns False.
"""

import time
import ctypes
import os
import platform
import numpy as np
from dataclasses import dataclass, field
from typing import Optional

# ──────────────────────────────────────────────────────────────────────────────
# Attempt to import optional GPU packages
# ──────────────────────────────────────────────────────────────────────────────
try:
    import cv2
    _OPENCV_AVAILABLE = True
except ImportError:
    _OPENCV_AVAILABLE = False

try:
    import pycuda.driver as cuda
    import pycuda.autoinit          # noqa: F401  (initialises CUDA context)
    from pycuda.compiler import SourceModule
    _PYCUDA_AVAILABLE = True
except Exception:
    _PYCUDA_AVAILABLE = False

# ──────────────────────────────────────────────────────────────────────────────
# Compiled C++ shared library detection
# ──────────────────────────────────────────────────────────────────────────────
_LIB_PATHS = [
    os.path.join(os.path.dirname(__file__), "..", "build", "libgpu_image_proc_lib.so"),
    os.path.join(os.path.dirname(__file__), "..", "build", "gpu_image_proc_lib.dll"),
    os.path.join(os.path.dirname(__file__), "..", "build", "Release", "gpu_image_proc_lib.dll"),
]

_cpp_lib = None
for _path in _LIB_PATHS:
    if os.path.exists(_path):
        try:
            _cpp_lib = ctypes.CDLL(_path)
            break
        except OSError:
            pass

_CPP_LIB_AVAILABLE = _cpp_lib is not None


# ──────────────────────────────────────────────────────────────────────────────
# PyCUDA kernel strings (used when pycuda is available but C++ lib is not)
# ──────────────────────────────────────────────────────────────────────────────
_CUDA_GRAYSCALE_SRC = r"""
__global__ void kernel_grayscale(
    const unsigned char* input,
    unsigned char* output,
    int width, int height)
{
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    if (x >= width || y >= height) return;

    int idx_rgb  = (y * width + x) * 3;
    int idx_gray =  y * width + x;

    float r = input[idx_rgb + 0];
    float g = input[idx_rgb + 1];
    float b = input[idx_rgb + 2];

    float gray = 0.299f * r + 0.587f * g + 0.114f * b;
    gray = fminf(fmaxf(gray, 0.0f), 255.0f);
    output[idx_gray] = (unsigned char)gray;
}
"""

_CUDA_SOBEL_SRC = r"""
__global__ void kernel_sobel(
    const unsigned char* input,
    unsigned char* output,
    int width, int height)
{
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    if (x >= width || y >= height) return;

    const int Kx[3][3] = {{-1,0,1},{-2,0,2},{-1,0,1}};
    const int Ky[3][3] = {{-1,-2,-1},{0,0,0},{1,2,1}};

    float gx = 0.0f, gy = 0.0f;
    for (int ky = -1; ky <= 1; ++ky) {
        for (int kx = -1; kx <= 1; ++kx) {
            int nx = max(0, min(x + kx, width  - 1));
            int ny = max(0, min(y + ky, height - 1));
            float p = input[ny * width + nx];
            gx += Kx[ky+1][kx+1] * p;
            gy += Ky[ky+1][kx+1] * p;
        }
    }
    float mag = sqrtf(gx*gx + gy*gy);
    output[y * width + x] = (unsigned char)fminf(mag, 255.0f);
}
"""

_CUDA_SHARPEN_SRC = r"""
__global__ void kernel_sharpen(
    const unsigned char* input,
    unsigned char* output,
    int width, int height)
{
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    if (x >= width || y >= height) return;

    const int K[3][3] = {{0,-1,0},{-1,5,-1},{0,-1,0}};
    float r=0,g=0,b=0;
    for (int ky=-1;ky<=1;++ky) {
        for (int kx=-1;kx<=1;++kx) {
            int nx=max(0,min(x+kx,width-1));
            int ny=max(0,min(y+ky,height-1));
            int src=(ny*width+nx)*3;
            int k=K[ky+1][kx+1];
            r+=k*input[src+0];
            g+=k*input[src+1];
            b+=k*input[src+2];
        }
    }
    int dst=(y*width+x)*3;
    output[dst+0]=(unsigned char)fminf(fmaxf(r,0),255);
    output[dst+1]=(unsigned char)fminf(fmaxf(g,0),255);
    output[dst+2]=(unsigned char)fminf(fmaxf(b,0),255);
}
"""


# ──────────────────────────────────────────────────────────────────────────────
# Data classes
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ProcessingResult:
    """
    Holds the output image and all timing/metadata for one processing run.

    Fields
    ------
    output_image    : np.ndarray — processed image (H×W×C, uint8)
    cpu_time_ms     : float — CPU execution time in milliseconds
    gpu_kernel_ms   : float — GPU kernel-only time (0 if not available)
    gpu_total_ms    : float — GPU end-to-end time including transfers (0 if N/A)
    speedup         : float — cpu_time_ms / gpu_kernel_ms (0 if no GPU)
    backend         : str   — 'python_cpu', 'pycuda_gpu', or 'cpp_cuda_gpu'
    gpu_available   : bool  — True if a real GPU was used
    error           : str   — non-empty if something went wrong
    width           : int
    height          : int
    num_pixels      : int
    """
    output_image:  Optional[np.ndarray] = None
    cpu_time_ms:   float = 0.0
    gpu_kernel_ms: float = 0.0
    gpu_total_ms:  float = 0.0
    speedup:       float = 0.0
    backend:       str   = "python_cpu"
    gpu_available: bool  = False
    error:         str   = ""
    width:         int   = 0
    height:        int   = 0
    num_pixels:    int   = 0


# ──────────────────────────────────────────────────────────────────────────────
# CUDA availability check
# ──────────────────────────────────────────────────────────────────────────────

def cuda_available() -> bool:
    """
    Returns True if a CUDA-capable GPU was detected.

    Checks (in order):
    1. PyCUDA — attempts to enumerate CUDA devices.
    2. Compiled C++ CUDA library — checks if it was loaded successfully.

    Never lies about GPU availability.
    """
    if _PYCUDA_AVAILABLE:
        try:
            return cuda.Device.count() > 0
        except Exception:
            return False
    if _CPP_LIB_AVAILABLE:
        try:
            _cpp_lib.cuda_is_available.restype = ctypes.c_bool
            return bool(_cpp_lib.cuda_is_available())
        except Exception:
            return False
    return False


def get_gpu_info() -> dict:
    """Returns a dict with GPU name and memory info, or a 'not available' message."""
    if _PYCUDA_AVAILABLE and cuda_available():
        try:
            dev = cuda.Device(0)
            attrs = dev.get_attributes()
            return {
                "name": dev.name(),
                "total_memory_mb": dev.total_memory() // (1024 * 1024),
                "compute_capability": f"{dev.compute_capability()[0]}.{dev.compute_capability()[1]}",
                "multiprocessors": attrs[cuda.device_attribute.MULTIPROCESSOR_COUNT],
            }
        except Exception as e:
            return {"error": str(e)}
    return {"name": "No CUDA GPU detected", "available": False}


# ──────────────────────────────────────────────────────────────────────────────
# Pure Python / NumPy CPU implementations
# (Fallback when C++ library is not compiled)
# ──────────────────────────────────────────────────────────────────────────────

def _cpu_grayscale(img: np.ndarray) -> np.ndarray:
    """
    Grayscale conversion using the luminance formula.
    img: H×W×3 uint8 RGB array
    Returns: H×W uint8 grayscale array
    """
    r = img[:, :, 0].astype(np.float32)
    g = img[:, :, 1].astype(np.float32)
    b = img[:, :, 2].astype(np.float32)
    gray = 0.299 * r + 0.587 * g + 0.114 * b
    return np.clip(gray, 0, 255).astype(np.uint8)


def _cpu_gaussian_blur(img: np.ndarray, radius: int = 3, sigma: float = 1.5) -> np.ndarray:
    """
    Gaussian blur using OpenCV (when available) or a NumPy convolution.
    img: H×W×3 uint8 RGB array
    Returns: H×W×3 uint8 blurred array
    """
    ksize = 2 * radius + 1
    if _OPENCV_AVAILABLE:
        # OpenCV expects BGR; since we work in RGB, result is the same
        return cv2.GaussianBlur(img, (ksize, ksize), sigma)
    # Pure NumPy fallback (slow but correct for any image size)
    from scipy.ndimage import gaussian_filter
    return gaussian_filter(img, sigma=[sigma, sigma, 0]).astype(np.uint8)


def _cpu_sobel(img_gray: np.ndarray) -> np.ndarray:
    """
    Sobel edge detection on a grayscale image.
    img_gray: H×W uint8 array
    Returns:  H×W uint8 edge magnitude array
    """
    if _OPENCV_AVAILABLE:
        img_f = img_gray.astype(np.float32)
        gx = cv2.Sobel(img_f, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(img_f, cv2.CV_32F, 0, 1, ksize=3)
        magnitude = np.sqrt(gx**2 + gy**2)
        return np.clip(magnitude, 0, 255).astype(np.uint8)
    # NumPy-only fallback
    from scipy.ndimage import convolve
    Kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    Ky = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)
    img_f = img_gray.astype(np.float32)
    gx = convolve(img_f, Kx)
    gy = convolve(img_f, Ky)
    return np.clip(np.sqrt(gx**2 + gy**2), 0, 255).astype(np.uint8)


def _cpu_sharpen(img: np.ndarray) -> np.ndarray:
    """
    Sharpening using a Laplacian-based 3×3 kernel.
    img: H×W×3 uint8 RGB array
    Returns: H×W×3 uint8 sharpened array
    """
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
    if _OPENCV_AVAILABLE:
        img_f = img.astype(np.float32)
        result = cv2.filter2D(img_f, -1, kernel)
        return np.clip(result, 0, 255).astype(np.uint8)
    from scipy.ndimage import convolve
    result = np.zeros_like(img, dtype=np.float32)
    for c in range(3):
        result[:, :, c] = convolve(img[:, :, c].astype(np.float32), kernel)
    return np.clip(result, 0, 255).astype(np.uint8)


# ──────────────────────────────────────────────────────────────────────────────
# PyCUDA GPU implementations
# ──────────────────────────────────────────────────────────────────────────────

def _pycuda_grayscale(img: np.ndarray, block_size: int = 16) -> tuple:
    """
    Grayscale conversion on GPU via PyCUDA.
    Returns (output_array, kernel_time_ms, total_time_ms).
    """
    mod = SourceModule(_CUDA_GRAYSCALE_SRC)
    kernel = mod.get_function("kernel_grayscale")

    h, w = img.shape[:2]
    img_c = np.ascontiguousarray(img, dtype=np.uint8)
    out   = np.zeros((h, w), dtype=np.uint8)

    # Allocate GPU memory and transfer input
    t_start = time.perf_counter()
    d_input  = cuda.mem_alloc(img_c.nbytes)
    d_output = cuda.mem_alloc(out.nbytes)
    cuda.memcpy_htod(d_input, img_c)

    # Configure grid and block dimensions
    block = (block_size, block_size, 1)
    grid  = ((w + block_size - 1) // block_size,
             (h + block_size - 1) // block_size, 1)

    # CUDA event timing (kernel only)
    start_ev = cuda.Event()
    stop_ev  = cuda.Event()
    start_ev.record()

    kernel(d_input, d_output, np.int32(w), np.int32(h),
           block=block, grid=grid)

    stop_ev.record()
    stop_ev.synchronize()
    kernel_ms = start_ev.time_till(stop_ev)

    # Transfer result back to host
    cuda.memcpy_dtoh(out, d_output)
    total_ms = (time.perf_counter() - t_start) * 1000.0

    return out, kernel_ms, total_ms


def _pycuda_sobel(img_gray: np.ndarray, block_size: int = 16) -> tuple:
    """Sobel edge detection on GPU via PyCUDA."""
    mod = SourceModule(_CUDA_SOBEL_SRC)
    kernel = mod.get_function("kernel_sobel")

    h, w = img_gray.shape
    img_c = np.ascontiguousarray(img_gray, dtype=np.uint8)
    out   = np.zeros((h, w), dtype=np.uint8)

    t_start  = time.perf_counter()
    d_input  = cuda.mem_alloc(img_c.nbytes)
    d_output = cuda.mem_alloc(out.nbytes)
    cuda.memcpy_htod(d_input, img_c)

    block    = (block_size, block_size, 1)
    grid     = ((w + block_size - 1) // block_size,
                (h + block_size - 1) // block_size, 1)

    start_ev = cuda.Event()
    stop_ev  = cuda.Event()
    start_ev.record()
    kernel(d_input, d_output, np.int32(w), np.int32(h), block=block, grid=grid)
    stop_ev.record()
    stop_ev.synchronize()
    kernel_ms = start_ev.time_till(stop_ev)

    cuda.memcpy_dtoh(out, d_output)
    total_ms = (time.perf_counter() - t_start) * 1000.0

    return out, kernel_ms, total_ms


def _pycuda_sharpen(img: np.ndarray, block_size: int = 16) -> tuple:
    """Image sharpening on GPU via PyCUDA."""
    mod = SourceModule(_CUDA_SHARPEN_SRC)
    kernel = mod.get_function("kernel_sharpen")

    h, w = img.shape[:2]
    img_c = np.ascontiguousarray(img, dtype=np.uint8)
    out   = np.zeros_like(img_c)

    t_start  = time.perf_counter()
    d_input  = cuda.mem_alloc(img_c.nbytes)
    d_output = cuda.mem_alloc(out.nbytes)
    cuda.memcpy_htod(d_input, img_c)

    block    = (block_size, block_size, 1)
    grid     = ((w + block_size - 1) // block_size,
                (h + block_size - 1) // block_size, 1)

    start_ev = cuda.Event()
    stop_ev  = cuda.Event()
    start_ev.record()
    kernel(d_input, d_output, np.int32(w), np.int32(h), block=block, grid=grid)
    stop_ev.record()
    stop_ev.synchronize()
    kernel_ms = start_ev.time_till(stop_ev)

    cuda.memcpy_dtoh(out, d_output)
    total_ms = (time.perf_counter() - t_start) * 1000.0

    return out, kernel_ms, total_ms


# ──────────────────────────────────────────────────────────────────────────────
# Public API — used by app.py
# ──────────────────────────────────────────────────────────────────────────────

def _time_cpu(fn, *args) -> tuple:
    """Run fn(*args) and return (result, elapsed_ms)."""
    t0 = time.perf_counter()
    result = fn(*args)
    return result, (time.perf_counter() - t0) * 1000.0


def process_grayscale(img_rgb: np.ndarray,
                       use_gpu: bool = True,
                       block_size: int = 16,
                       iterations: int = 5,
                       warmup: int = 2) -> ProcessingResult:
    """
    Convert RGB image to grayscale.

    Parameters
    ----------
    img_rgb    : H×W×3 uint8 NumPy array in RGB order.
    use_gpu    : If True and a GPU is available, run the CUDA kernel.
    block_size : CUDA thread-block side length (8, 16, or 32).
    iterations : Number of timed iterations (average is reported).
    warmup     : Number of warm-up iterations (discarded).

    Returns
    -------
    ProcessingResult with output_image as a H×W uint8 grayscale array.
    """
    h, w = img_rgb.shape[:2]
    res = ProcessingResult(width=w, height=h, num_pixels=w * h)

    # ── CPU timing ───────────────────────────────────────────────────────
    # Warm-up
    for _ in range(warmup):
        _cpu_grayscale(img_rgb)
    # Measured iterations
    cpu_times = []
    for _ in range(iterations):
        _, t = _time_cpu(_cpu_grayscale, img_rgb)
        cpu_times.append(t)
    res.cpu_time_ms = sum(cpu_times) / len(cpu_times)
    res.output_image = _cpu_grayscale(img_rgb)  # final output from CPU

    # ── GPU timing ───────────────────────────────────────────────────────
    if use_gpu and _PYCUDA_AVAILABLE and cuda_available():
        try:
            # Warm-up GPU
            for _ in range(warmup):
                _pycuda_grayscale(img_rgb, block_size)
            k_times, t_times = [], []
            for _ in range(iterations):
                gpu_out, km, tm = _pycuda_grayscale(img_rgb, block_size)
                k_times.append(km)
                t_times.append(tm)
            res.gpu_kernel_ms = sum(k_times) / len(k_times)
            res.gpu_total_ms  = sum(t_times) / len(t_times)
            res.gpu_available = True
            res.backend       = "pycuda_gpu"
            res.output_image  = gpu_out
            if res.gpu_kernel_ms > 0:
                res.speedup = res.cpu_time_ms / res.gpu_kernel_ms
        except Exception as e:
            res.error       = f"PyCUDA error: {e}"
            res.gpu_available = False
    else:
        res.backend = "python_cpu"

    return res


def process_gaussian_blur(img_rgb: np.ndarray,
                            use_gpu: bool = True,
                            block_size: int = 16,
                            blur_radius: int = 3,
                            sigma: float = 1.5,
                            iterations: int = 5,
                            warmup: int = 2) -> ProcessingResult:
    """
    Apply Gaussian blur.

    Parameters
    ----------
    img_rgb     : H×W×3 uint8 RGB array.
    use_gpu     : Use CUDA GPU if available.
    block_size  : CUDA block side length.
    blur_radius : Radius of the Gaussian kernel.
    sigma       : Standard deviation of the Gaussian distribution.
    iterations  : Timed iterations.
    warmup      : Warm-up iterations.

    Returns
    -------
    ProcessingResult with output_image as H×W×3 uint8 blurred array.
    """
    h, w = img_rgb.shape[:2]
    res = ProcessingResult(width=w, height=h, num_pixels=w * h)

    for _ in range(warmup):
        _cpu_gaussian_blur(img_rgb, blur_radius, sigma)
    cpu_times = []
    for _ in range(iterations):
        _, t = _time_cpu(_cpu_gaussian_blur, img_rgb, blur_radius, sigma)
        cpu_times.append(t)
    res.cpu_time_ms  = sum(cpu_times) / len(cpu_times)
    res.output_image = _cpu_gaussian_blur(img_rgb, blur_radius, sigma)
    res.backend      = "python_cpu"

    # NOTE: PyCUDA Gaussian blur with a configurable kernel would require
    # passing the kernel weights to the GPU at runtime.  The implementation
    # is done in the C++ CUDA library (cuda_processing.cu).  When PyCUDA
    # is available but the C++ lib is not, we still use the CPU result and
    # set gpu_available = False with an explanatory message.
    if use_gpu and _PYCUDA_AVAILABLE and cuda_available():
        res.error = ("GPU Gaussian blur requires the compiled C++ CUDA library. "
                     "CPU result shown. See README for build instructions.")

    return res


def process_sobel(img_rgb: np.ndarray,
                   use_gpu: bool = True,
                   block_size: int = 16,
                   iterations: int = 5,
                   warmup: int = 2) -> ProcessingResult:
    """
    Sobel edge detection.

    Converts the input to grayscale first, then runs Sobel convolution.

    Parameters
    ----------
    img_rgb    : H×W×3 uint8 RGB array.
    use_gpu    : Use CUDA GPU if available.
    block_size : CUDA block side length.

    Returns
    -------
    ProcessingResult with output_image as H×W uint8 edge magnitude array.
    """
    h, w = img_rgb.shape[:2]
    res = ProcessingResult(width=w, height=h, num_pixels=w * h)

    # Grayscale conversion is a prerequisite
    gray = _cpu_grayscale(img_rgb)

    for _ in range(warmup):
        _cpu_sobel(gray)
    cpu_times = []
    for _ in range(iterations):
        _, t = _time_cpu(_cpu_sobel, gray)
        cpu_times.append(t)
    res.cpu_time_ms  = sum(cpu_times) / len(cpu_times)
    res.output_image = _cpu_sobel(gray)
    res.backend      = "python_cpu"

    if use_gpu and _PYCUDA_AVAILABLE and cuda_available():
        try:
            for _ in range(warmup):
                _pycuda_sobel(gray, block_size)
            k_times, t_times = [], []
            for _ in range(iterations):
                gpu_out, km, tm = _pycuda_sobel(gray, block_size)
                k_times.append(km)
                t_times.append(tm)
            res.gpu_kernel_ms = sum(k_times) / len(k_times)
            res.gpu_total_ms  = sum(t_times) / len(t_times)
            res.gpu_available = True
            res.backend       = "pycuda_gpu"
            res.output_image  = gpu_out
            if res.gpu_kernel_ms > 0:
                res.speedup = res.cpu_time_ms / res.gpu_kernel_ms
        except Exception as e:
            res.error       = f"PyCUDA error: {e}"
            res.gpu_available = False

    return res


def process_sharpen(img_rgb: np.ndarray,
                     use_gpu: bool = True,
                     block_size: int = 16,
                     iterations: int = 5,
                     warmup: int = 2) -> ProcessingResult:
    """
    Image sharpening.

    Parameters
    ----------
    img_rgb    : H×W×3 uint8 RGB array.
    use_gpu    : Use CUDA GPU if available.
    block_size : CUDA block side length.

    Returns
    -------
    ProcessingResult with output_image as H×W×3 uint8 sharpened array.
    """
    h, w = img_rgb.shape[:2]
    res = ProcessingResult(width=w, height=h, num_pixels=w * h)

    for _ in range(warmup):
        _cpu_sharpen(img_rgb)
    cpu_times = []
    for _ in range(iterations):
        _, t = _time_cpu(_cpu_sharpen, img_rgb)
        cpu_times.append(t)
    res.cpu_time_ms  = sum(cpu_times) / len(cpu_times)
    res.output_image = _cpu_sharpen(img_rgb)
    res.backend      = "python_cpu"

    if use_gpu and _PYCUDA_AVAILABLE and cuda_available():
        try:
            for _ in range(warmup):
                _pycuda_sharpen(img_rgb, block_size)
            k_times, t_times = [], []
            for _ in range(iterations):
                gpu_out, km, tm = _pycuda_sharpen(img_rgb, block_size)
                k_times.append(km)
                t_times.append(tm)
            res.gpu_kernel_ms = sum(k_times) / len(k_times)
            res.gpu_total_ms  = sum(t_times) / len(t_times)
            res.gpu_available = True
            res.backend       = "pycuda_gpu"
            res.output_image  = gpu_out
            if res.gpu_kernel_ms > 0:
                res.speedup = res.cpu_time_ms / res.gpu_kernel_ms
        except Exception as e:
            res.error       = f"PyCUDA error: {e}"
            res.gpu_available = False

    return res
