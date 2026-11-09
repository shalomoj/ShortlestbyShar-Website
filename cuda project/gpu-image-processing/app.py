"""
app.py

Streamlit dashboard for the GPU Image Processing & Performance Optimization Engine.

Launches with:
    streamlit run app.py

Architecture
────────────
  This file is the UI layer only.  All image processing logic lives in
  python/processing_interface.py, which in turn calls:
    - Pure NumPy/OpenCV CPU implementations (always available)
    - PyCUDA GPU kernels (when an NVIDIA GPU + CUDA Toolkit is present)
    - The compiled C++ CUDA shared library (when CMake build is complete)

  The UI never performs image processing directly — it only calls the
  processing_interface module and displays results.

GPU Transparency
────────────────
  - A visible banner shows whether CUDA GPU execution is actually available.
  - GPU results are never fabricated.
  - CPU fallback is clearly labelled.
"""

import sys
import os

# Ensure the python/ package is importable regardless of working directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "python"))

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")   # Non-interactive backend for server-side rendering
import io
import time
from PIL import Image

from processing_interface import (
    process_grayscale,
    process_gaussian_blur,
    process_sobel,
    process_sharpen,
    cuda_available,
    get_gpu_info,
    ProcessingResult,
)

# ──────────────────────────────────────────────────────────────────────────────
# Page configuration
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GPU Image Processing Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# Custom CSS — minimal, professional
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1f2328;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #57606a;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #f7f8fa;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #3b82d4;
    }
    .metric-label {
        font-size: 0.82rem;
        color: #57606a;
        margin-top: 0.2rem;
    }
    .gpu-available {
        background: #d1fae5;
        border: 1px solid #6ee7b7;
        border-radius: 6px;
        padding: 0.6rem 1rem;
        color: #065f46;
        font-weight: 600;
    }
    .gpu-unavailable {
        background: #fef3c7;
        border: 1px solid #fcd34d;
        border-radius: 6px;
        padding: 0.6rem 1rem;
        color: #92400e;
        font-weight: 600;
    }
    .section-divider {
        border-top: 1px solid #e5e7eb;
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────────────────────────────────────
st.markdown('<p class="main-header">⚡ GPU Image Processing & Performance Optimization Engine</p>',
            unsafe_allow_html=True)
st.markdown('<p class="sub-header">Comparing CPU and GPU Parallel Computing Performance Using CUDA C++</p>',
            unsafe_allow_html=True)

# ── GPU Status Banner ────────────────────────────────────────────────────────
_gpu_ok = cuda_available()
if _gpu_ok:
    gpu_info = get_gpu_info()
    gpu_name = gpu_info.get("name", "CUDA GPU")
    st.markdown(
        f'<div class="gpu-available">✅ CUDA GPU Available — {gpu_name}</div>',
        unsafe_allow_html=True
    )
else:
    st.markdown(
        '<div class="gpu-unavailable">⚠️ No CUDA GPU detected — running in CPU-only mode. '
        'GPU sections will show CPU results with a clear label.</div>',
        unsafe_allow_html=True
    )

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar — Controls
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Controls")
    st.markdown("---")

    # Image upload
    st.subheader("📁 Image Input")
    uploaded_file = st.file_uploader(
        "Upload an image (JPG, PNG, BMP)",
        type=["jpg", "jpeg", "png", "bmp", "webp"],
        help="The same image is used for both CPU and GPU execution."
    )

    # Use sample image if no upload
    use_sample = st.checkbox("Use built-in sample image", value=(uploaded_file is None))

    st.markdown("---")

    # Operation selection
    st.subheader("🔧 Processing Operation")
    operation = st.selectbox(
        "Select algorithm",
        options=[
            "Grayscale Conversion",
            "Gaussian Blur",
            "Sobel Edge Detection",
            "Image Sharpening",
        ],
    )

    st.markdown("---")

    # Execution mode
    st.subheader("🖥️ Execution Mode")
    exec_mode = st.radio(
        "Run on",
        options=["CPU only", "GPU only", "CPU + GPU (compare)"],
        index=2,
        help="CPU+GPU compare runs both and shows speedup."
    )
    use_gpu = exec_mode in ("GPU only", "CPU + GPU (compare)")

    st.markdown("---")

    # CUDA block size
    st.subheader("🧮 CUDA Block Size")
    block_size = st.selectbox(
        "Thread block dimension",
        options=[8, 16, 32],
        index=1,
        help="A block of N×N threads. 16×16=256 threads is a common default."
    )

    st.markdown("---")

    # Benchmark settings
    st.subheader("📊 Benchmark Settings")
    iterations = st.slider("Measurement iterations", 1, 20, 5,
                            help="Average over this many runs.")
    warmup     = st.slider("Warm-up iterations", 0, 5, 2,
                            help="Discarded before timing starts.")

    st.markdown("---")

    # Operation-specific parameters
    st.subheader("🔩 Algorithm Parameters")
    blur_radius = sigma = None
    if operation == "Gaussian Blur":
        blur_radius = st.slider("Blur radius", 1, 10, 3)
        sigma       = st.slider("Sigma (σ)", 0.5, 5.0, 1.5, step=0.1)

    run_button = st.button("▶ Run Processing", type="primary", use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# Image loading
# ──────────────────────────────────────────────────────────────────────────────

def load_image(uploaded, use_sample_flag: bool) -> np.ndarray:
    """
    Load image from upload or generate a synthetic sample.
    Returns an H×W×3 uint8 RGB NumPy array.
    """
    if uploaded is not None:
        pil_img = Image.open(uploaded).convert("RGB")
        return np.array(pil_img, dtype=np.uint8)

    if use_sample_flag:
        # Generate a colourful synthetic test image (512×512) with geometric shapes
        img = np.zeros((512, 512, 3), dtype=np.uint8)
        # Background gradient
        for y in range(512):
            img[y, :, 2] = int(50 + y * 0.4)  # blue gradient
        # Red circle
        cx, cy, r = 160, 160, 100
        Y, X = np.ogrid[:512, :512]
        mask = (X - cx)**2 + (Y - cy)**2 <= r**2
        img[mask] = [220, 50, 50]
        # Green rectangle
        img[280:420, 80:250, :] = [50, 180, 70]
        # White diagonal stripe
        for i in range(512):
            for d in range(-4, 5):
                j = i + d
                if 0 <= j < 512:
                    img[i, j] = [240, 240, 240]
        return img

    return None


img_array = load_image(uploaded_file, use_sample)

# ──────────────────────────────────────────────────────────────────────────────
# Main content area
# ──────────────────────────────────────────────────────────────────────────────

if img_array is None:
    st.info("👈 Upload an image or enable 'Use built-in sample image' in the sidebar.")
    st.stop()

# Display original image
col_orig, col_proc = st.columns(2)
with col_orig:
    st.subheader("Original Image")
    st.image(img_array, caption=f"{img_array.shape[1]}×{img_array.shape[0]} px", use_column_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# Processing
# ──────────────────────────────────────────────────────────────────────────────

result: ProcessingResult = None

if run_button or True:  # Always show result area; only compute when button pressed
    if run_button:
        with st.spinner(f"Running {operation}…"):
            try:
                if operation == "Grayscale Conversion":
                    result = process_grayscale(
                        img_array, use_gpu=use_gpu,
                        block_size=block_size,
                        iterations=iterations, warmup=warmup
                    )
                elif operation == "Gaussian Blur":
                    result = process_gaussian_blur(
                        img_array, use_gpu=use_gpu,
                        block_size=block_size,
                        blur_radius=blur_radius, sigma=sigma,
                        iterations=iterations, warmup=warmup
                    )
                elif operation == "Sobel Edge Detection":
                    result = process_sobel(
                        img_array, use_gpu=use_gpu,
                        block_size=block_size,
                        iterations=iterations, warmup=warmup
                    )
                elif operation == "Image Sharpening":
                    result = process_sharpen(
                        img_array, use_gpu=use_gpu,
                        block_size=block_size,
                        iterations=iterations, warmup=warmup
                    )
            except Exception as e:
                st.error(f"Processing error: {e}")
                st.stop()

    if result is not None:
        # ── Processed image ───────────────────────────────────────────────
        with col_proc:
            st.subheader("Processed Image")
            out_img = result.output_image
            if out_img is not None:
                # Convert grayscale to displayable format
                if out_img.ndim == 2:
                    display_img = out_img
                else:
                    display_img = out_img
                st.image(display_img,
                         caption=f"{operation} — Backend: {result.backend}",
                         use_column_width=True, clamp=True)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # ── Performance metrics ───────────────────────────────────────────
        st.subheader("📈 Performance Metrics")

        m1, m2, m3, m4, m5 = st.columns(5)

        with m1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{result.cpu_time_ms:.2f}</div>
                <div class="metric-label">CPU Time (ms)</div>
            </div>""", unsafe_allow_html=True)

        with m2:
            gpu_k = f"{result.gpu_kernel_ms:.2f}" if result.gpu_available else "N/A"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{gpu_k}</div>
                <div class="metric-label">GPU Kernel (ms)</div>
            </div>""", unsafe_allow_html=True)

        with m3:
            gpu_t = f"{result.gpu_total_ms:.2f}" if result.gpu_available else "N/A"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{gpu_t}</div>
                <div class="metric-label">GPU Total (ms)</div>
            </div>""", unsafe_allow_html=True)

        with m4:
            speedup = f"{result.speedup:.1f}×" if result.gpu_available else "N/A"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{speedup}</div>
                <div class="metric-label">Speedup</div>
            </div>""", unsafe_allow_html=True)

        with m5:
            improvement = f"{(result.speedup - 1) * 100:.0f}%" if result.gpu_available and result.speedup > 1 else "N/A"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{improvement}</div>
                <div class="metric-label">Improvement</div>
            </div>""", unsafe_allow_html=True)

        # Warnings
        if result.error:
            st.warning(f"ℹ️ {result.error}")

        if not result.gpu_available and use_gpu:
            st.info("GPU execution was requested but no CUDA GPU is available. "
                    "CPU result is displayed.")

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # ── Benchmark chart ───────────────────────────────────────────────
        st.subheader("📊 Performance Comparison Chart")

        fig, axes = plt.subplots(1, 2, figsize=(12, 4))

        # Chart 1: Execution Time Comparison
        ax1 = axes[0]
        labels = ["CPU"]
        times  = [result.cpu_time_ms]
        colors = ["#3b82d4"]

        if result.gpu_available:
            labels += ["GPU Kernel", "GPU Total"]
            times  += [result.gpu_kernel_ms, result.gpu_total_ms]
            colors += ["#7c5cd8", "#10b981"]

        bars = ax1.bar(labels, times, color=colors, width=0.5, edgecolor="none")
        ax1.set_title(f"{operation}\nExecution Time Comparison", fontsize=11, pad=10)
        ax1.set_ylabel("Time (ms)", fontsize=10)
        ax1.set_xlabel("Processing Mode", fontsize=10)
        ax1.spines["top"].set_visible(False)
        ax1.spines["right"].set_visible(False)

        # Annotate bars with values
        for bar, val in zip(bars, times):
            ax1.text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + max(times) * 0.01,
                     f"{val:.2f} ms", ha="center", va="bottom", fontsize=9)

        # Chart 2: Speedup (only meaningful with GPU)
        ax2 = axes[1]
        if result.gpu_available and result.speedup > 0:
            categories = ["Speedup\n(CPU/GPU kernel)", "GPU overhead\n(total/kernel)"]
            values     = [result.speedup,
                          result.gpu_total_ms / result.gpu_kernel_ms if result.gpu_kernel_ms > 0 else 1.0]
            ax2.bar(categories, values, color=["#3b82d4", "#f59e0b"],
                    width=0.4, edgecolor="none")
            ax2.axhline(y=1, color="#e5e7eb", linestyle="--", linewidth=1)
            ax2.set_title("Speedup & Memory Transfer Overhead", fontsize=11, pad=10)
            ax2.set_ylabel("Ratio", fontsize=10)
            ax2.spines["top"].set_visible(False)
            ax2.spines["right"].set_visible(False)
            for i, (cat, val) in enumerate(zip(categories, values)):
                ax2.text(i, val + 0.05, f"{val:.2f}×",
                         ha="center", va="bottom", fontsize=10, fontweight="bold")
        else:
            ax2.text(0.5, 0.5,
                     "GPU not available\n(speedup chart requires CUDA GPU)",
                     ha="center", va="center", transform=ax2.transAxes,
                     fontsize=11, color="#57606a")
            ax2.set_title("Speedup (GPU not available)", fontsize=11)
            ax2.spines["top"].set_visible(False)
            ax2.spines["right"].set_visible(False)

        plt.tight_layout(pad=2)
        st.pyplot(fig)
        plt.close(fig)

        # ── Results table ─────────────────────────────────────────────────
        st.subheader("📋 Detailed Results")
        table_data = {
            "Metric": [
                "Operation",
                "Image Resolution",
                "Total Pixels",
                "CUDA Block Size",
                "Backend",
                "CPU Time (avg)",
                "GPU Kernel Time (avg)",
                "GPU Total Time (avg)",
                "Speedup (CPU / GPU kernel)",
                "Improvement",
                "GPU Available",
            ],
            "Value": [
                operation,
                f"{result.width} × {result.height}",
                f"{result.num_pixels:,}",
                f"{block_size}×{block_size} = {block_size**2} threads/block",
                result.backend,
                f"{result.cpu_time_ms:.3f} ms",
                f"{result.gpu_kernel_ms:.3f} ms" if result.gpu_available else "N/A",
                f"{result.gpu_total_ms:.3f} ms" if result.gpu_available else "N/A",
                f"{result.speedup:.2f}×" if result.gpu_available else "N/A",
                f"{(result.speedup - 1) * 100:.1f}%" if result.gpu_available and result.speedup > 1 else "N/A",
                "✅ Yes" if result.gpu_available else "❌ No",
            ],
        }
        st.table(table_data)

# ──────────────────────────────────────────────────────────────────────────────
# Technical Information Section
# ──────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.subheader("📚 Technical Reference")

with st.expander("How CUDA Works — GPU Architecture Overview"):
    st.markdown("""
    ### CPU vs GPU Architecture

    | | CPU | GPU |
    |---|---|---|
    | Core count | 4–32 powerful cores | Thousands of small cores |
    | Optimised for | Sequential, branchy code | Massively parallel, uniform work |
    | Clock speed | 3–5 GHz | 1–2 GHz |
    | Memory | Low latency, small cache | High bandwidth, large VRAM |
    | Best use case | OS, databases, branching logic | Rendering, deep learning, simulations |

    An NVIDIA GPU (e.g. RTX 3080) has **8704 CUDA cores** that can all execute simultaneously.
    A typical image at 1920×1080 has **2,073,600 pixels** — each pixel processed by its own thread.
    """)

with st.expander("CUDA Kernels, Threads, Blocks, and Grids"):
    st.markdown("""
    ### CUDA Execution Model

    **Kernel** — A function declared with `__global__` that runs on the GPU:
    ```cpp
    __global__ void kernel_grayscale(unsigned char* input, unsigned char* output,
                                      int width, int height) {
        int x = blockIdx.x * blockDim.x + threadIdx.x;
        int y = blockIdx.y * blockDim.y + threadIdx.y;
        if (x >= width || y >= height) return;
        // ... process pixel (x, y)
    }
    ```

    **Thread** — The smallest unit of execution. One thread = one pixel.

    **Block** — A group of threads that share fast shared memory and can synchronize.
    - This project uses 16×16 = 256 threads per block (configurable to 8×8 or 32×32).

    **Grid** — The collection of all blocks needed to cover the entire image:
    ```cpp
    dim3 block(16, 16);
    dim3 grid((width + 15) / 16, (height + 15) / 16);
    kernel<<<grid, block>>>(d_input, d_output, width, height);
    ```

    The `<<<grid, block>>>` syntax is CUDA's kernel launch syntax (compiled by nvcc).
    """)

with st.expander("GPU Memory Transfers — cudaMalloc, cudaMemcpy, cudaFree"):
    st.markdown("""
    ### GPU Memory Management

    CPU (host) and GPU (device) have **separate memory spaces**.
    Data must be explicitly transferred between them:

    ```cpp
    uint8_t* d_input;
    uint8_t* d_output;

    // 1. Allocate memory on the GPU
    cudaMalloc(&d_input,  width * height * 3);
    cudaMalloc(&d_output, width * height);

    // 2. Copy input from CPU RAM → GPU VRAM
    cudaMemcpy(d_input, h_input, bytes, cudaMemcpyHostToDevice);

    // 3. Launch kernel
    kernel<<<grid, block>>>(d_input, d_output, width, height);

    // 4. Copy result from GPU VRAM → CPU RAM
    cudaMemcpy(h_output, d_output, bytes, cudaMemcpyDeviceToHost);

    // 5. Free GPU memory (must always do this!)
    cudaFree(d_input);
    cudaFree(d_output);
    ```

    **Memory transfer overhead** is why GPU total time > GPU kernel time.
    For large images processed many times, this overhead amortises — the GPU wins.
    For a single tiny image, the overhead can make GPU slower than CPU.
    """)

with st.expander("Image Processing Algorithms — Mathematical Foundations"):
    st.markdown("""
    ### Grayscale Conversion
    Uses the **ITU-R BT.601 luminance formula**:
    ```
    Gray = 0.299 × R + 0.587 × G + 0.114 × B
    ```
    Green has the highest weight because human vision is most sensitive to green light.

    ### Gaussian Blur
    Convolves the image with a 2D Gaussian kernel:
    ```
    G(x,y) = exp(-(x² + y²) / (2σ²))
    ```
    Larger σ → stronger blur. Each output pixel is a weighted average of its neighbourhood.

    ### Sobel Edge Detection
    Applies two 3×3 convolution kernels:
    ```
    Gx = [-1  0 +1; -2  0 +2; -1  0 +1]   (horizontal edges)
    Gy = [-1 -2 -1;  0  0  0; +1 +2 +1]   (vertical edges)
    Magnitude = √(Gx² + Gy²)
    ```
    High magnitude = sharp intensity transition = edge.

    ### Image Sharpening
    Uses a Laplacian-based kernel:
    ```
    K = [0 -1 0; -1 5 -1; 0 -1 0]
    ```
    Equivalent to: `output = input + (input - blurred_input)`
    — amplifies high-frequency detail (edges).
    """)

with st.expander("Benchmark Methodology"):
    st.markdown("""
    ### How Benchmarks Are Measured

    1. **Identical input** — CPU and GPU process the same pixel data.
    2. **Warm-up iterations** — Discarded before timing begins. Eliminates:
       - CPU branch-predictor cold starts
       - CUDA context initialisation overhead
    3. **Multiple iterations** — Average of N runs is reported (configurable in sidebar).
    4. **CPU timing** — `time.perf_counter()` (nanosecond resolution on modern OS).
    5. **GPU kernel timing** — `cudaEvent_t` records timestamps on the GPU hardware timer,
       which is more accurate than host-side timing for GPU kernels.
    6. **Speedup calculation**:
       ```
       Speedup = CPU_avg_time_ms / GPU_kernel_avg_time_ms
       ```
       Kernel-only time is used for the pure compute comparison.
       End-to-end GPU time (including memory transfers) is also shown separately.

    **What these results tell you:**
    - `Speedup > 1` → GPU kernel is faster for pure computation.
    - GPU total time may still be higher for small images (transfer overhead dominates).
    - For large images processed repeatedly, GPU wins clearly.
    """)

# ──────────────────────────────────────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<hr style="border: none; border-top: 1px solid #e5e7eb; margin-top: 2rem;">
<p style="text-align: center; color: #57606a; font-size: 0.82rem;">
    GPU Image Processing & Performance Optimization Engine
    — Built with CUDA C++, Python, and Streamlit
</p>
""", unsafe_allow_html=True)
