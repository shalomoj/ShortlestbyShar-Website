# GPU Image Processing & Performance Optimization Engine

A GPU-accelerated image processing application that demonstrates parallel computing
performance using **CUDA C++**, with a professional **Streamlit** dashboard for
visual comparison of CPU vs GPU execution.

Built as a Computer Science portfolio project to demonstrate:
- CUDA C++ parallel programming
- GPU thread indexing and memory management
- CPU vs GPU performance benchmarking
- Python–C++ integration via ctypes / PyCUDA
- Real-time image processing algorithms

---

## Problem Statement

Image processing operations like blurring, edge detection, and filtering are
computationally expensive when applied to high-resolution images.  A CPU processes
pixels **sequentially** — one after another.  A modern GPU has **thousands of cores**
that can process thousands of pixels **simultaneously**.

This project measures exactly how much faster GPU parallel execution is compared to
sequential CPU execution for four common image-processing algorithms.

---

## Why GPU Acceleration Matters

| Image | Pixels | Sequential CPU iterations | GPU threads launched |
|-------|--------|--------------------------|----------------------|
| 480p  | 345,600 | 345,600 | 345,600 (simultaneous) |
| 1080p | 2,073,600 | 2,073,600 | 2,073,600 (simultaneous) |
| 4K    | 8,294,400 | 8,294,400 | 8,294,400 (simultaneous) |

Each GPU thread handles **one pixel independently**.  Because pixels in most
image-processing operations do not depend on each other, the entire image can be
processed in approximately the time it takes to process **one pixel** on the CPU.

---

## Technologies Used

| Technology | Purpose |
|---|---|
| **CUDA C++** | GPU parallel kernel execution |
| **C++17** | CPU reference implementations |
| **Python 3.10+** | Application interface and benchmarking |
| **Streamlit** | Web-based dashboard UI |
| **NumPy** | Image array manipulation |
| **OpenCV** | Image loading, saving, CPU processing |
| **Matplotlib** | Performance comparison charts |
| **PyCUDA** | Python–CUDA bridge (optional, for GPU) |
| **CMake 3.18+** | C++/CUDA build system |

---

## Features

- **4 image-processing algorithms**: Grayscale, Gaussian Blur, Sobel Edge Detection, Image Sharpening
- **CPU + GPU parallel implementations** for each algorithm
- **CUDA kernels** with configurable block sizes (8×8, 16×16, 32×32)
- **Accurate benchmarking**: CUDA events for kernel timing, `std::chrono` for CPU timing
- **Warm-up iterations** before measurement for fair results
- **Speedup and improvement percentage** calculations
- **Clear GPU unavailability handling** — never fabricates GPU results
- **Interactive Streamlit dashboard** with image upload, parameter controls, and charts
- **Automated test suite** with GPU-skipping when CUDA is absent

---

## Project Architecture

```
gpu-image-processing/
│
├── app.py                    # Streamlit dashboard (UI only)
├── requirements.txt          # Python dependencies
├── CMakeLists.txt            # C++/CUDA build configuration
├── README.md
│
├── src/
│   ├── cpu_processing.h      # CPU function declarations
│   ├── cpu_processing.cpp    # CPU implementations (grayscale, blur, sobel, sharpen)
│   ├── cuda_processing.h     # GPU function declarations + BenchmarkResult struct
│   ├── cuda_processing.cu    # CUDA kernels + host wrapper functions
│   ├── benchmark.h           # BenchmarkReport struct declaration
│   ├── benchmark.cpp         # CPU vs GPU benchmarking driver
│   └── main.cpp              # CLI entry point (image I/O + benchmark runner)
│
├── python/
│   └── processing_interface.py   # Python layer: PyCUDA kernels + CPU fallbacks
│
├── tests/
│   ├── test_processing.py    # CPU algorithm correctness tests
│   └── test_cuda.py          # GPU correctness and timing tests
│
├── images/
│   └── sample.jpg            # Built-in sample image
│
└── results/                  # Processed image outputs (git-ignored)
    └── .gitkeep
```

---

## Installation

### 1. Install Python (3.10 or newer)

Download from [python.org](https://www.python.org/downloads/).

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. (Optional) Install CUDA Toolkit for GPU support

Download the CUDA Toolkit from [developer.nvidia.com/cuda-downloads](https://developer.nvidia.com/cuda-downloads).

Requirements:
- NVIDIA GPU with compute capability ≥ 3.5
- CUDA Toolkit 11.0 or newer
- Compatible GPU driver

Verify installation:
```bash
nvcc --version
```

### 4. (Optional) Install PyCUDA

After installing the CUDA Toolkit:
```bash
pip install pycuda
```

---

## Building the C++ / CUDA Library

The C++ library enables the full benchmark suite and CLI runner.
The Python Streamlit app works without it (falls back to CPU-only mode).

### Prerequisites

- CMake 3.18+
- C++17 compiler (MSVC 2019+, GCC 9+, or Clang 10+)
- OpenCV 4.x
- CUDA Toolkit (optional, for GPU support)

### Build steps

```bash
# From the project root
mkdir build && cd build

# Configure (with CUDA detection)
cmake ..

# Build
cmake --build . --config Release

# Run the CLI tool
./gpu_image_proc ../images/sample.jpg ../results/ 16 5
```

On Windows with Visual Studio:
```powershell
mkdir build; cd build
cmake .. -G "Visual Studio 17 2022" -A x64
cmake --build . --config Release
.\Release\gpu_image_proc.exe ..\images\sample.jpg ..\results\ 16 5
```

---

## Launching the Streamlit Application

```bash
# From the project root
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

### Dashboard walkthrough

1. **Upload an image** in the sidebar (or use the built-in sample).
2. **Select an operation**: Grayscale, Gaussian Blur, Sobel, or Sharpen.
3. **Choose execution mode**: CPU only, GPU only, or CPU + GPU compare.
4. **Select CUDA block size**: 8×8, 16×16, or 32×32 threads per block.
5. **Set benchmark iterations** and warm-up count.
6. Click **▶ Run Processing**.
7. View the processed image, timing metrics, comparison chart, and detailed table.

---

## Running the Tests

```bash
# All tests (CPU tests run always; GPU tests skip if CUDA is unavailable)
pytest tests/ -v

# CPU tests only
pytest tests/test_processing.py -v

# GPU tests only (will skip if no CUDA GPU)
pytest tests/test_cuda.py -v
```

Expected output without a GPU:
```
tests/test_processing.py::TestGrayscale::test_output_shape     PASSED
tests/test_processing.py::TestGrayscale::test_output_dtype     PASSED
...
tests/test_cuda.py::TestCUDAKernelCorrectness::test_grayscale_cpu_gpu_consistency  SKIPPED
...
```

---

## CUDA Implementation Details

### Thread Indexing

Each CUDA thread handles exactly one output pixel.
Thread coordinates are computed using CUDA's built-in block and thread variables:

```cpp
int x = blockIdx.x * blockDim.x + threadIdx.x;  // column (horizontal)
int y = blockIdx.y * blockDim.y + threadIdx.y;  // row    (vertical)
if (x >= width || y >= height) return;           // bounds check
```

### Grid Configuration

The 2D thread grid covers the entire image with ceiling division:

```cpp
dim3 block(block_size, block_size);  // e.g. 16×16 = 256 threads per block
dim3 grid((width  + block_size - 1) / block_size,
          (height + block_size - 1) / block_size);
kernel<<<grid, block>>>(d_input, d_output, width, height);
```

### Memory Management

```cpp
// 1. Allocate on GPU
cudaMalloc(&d_input, width * height * 3);

// 2. Host → Device transfer
cudaMemcpy(d_input, h_input, bytes, cudaMemcpyHostToDevice);

// 3. Launch kernel
kernel<<<grid, block>>>(d_input, d_output, width, height);

// 4. Device → Host transfer
cudaMemcpy(h_output, d_output, bytes, cudaMemcpyDeviceToHost);

// 5. Free GPU memory
cudaFree(d_input);
cudaFree(d_output);
```

### Kernel Timing (CUDA Events)

CUDA events use the GPU's own hardware timer — more accurate than host-side timing:

```cpp
cudaEvent_t start, stop;
cudaEventCreate(&start);
cudaEventCreate(&stop);

cudaEventRecord(start);
kernel<<<grid, block>>>(...);
cudaEventRecord(stop);
cudaEventSynchronize(stop);     // Wait for GPU to finish

float kernel_ms;
cudaEventElapsedTime(&kernel_ms, start, stop);
```

---

## Benchmark Methodology

| Aspect | Method |
|--------|--------|
| CPU timing | `std::chrono::high_resolution_clock` |
| GPU kernel timing | `cudaEvent_t` hardware timer |
| GPU total timing | Host-side `std::chrono` (includes memory transfers) |
| Warm-up | 2 iterations discarded before measurement starts |
| Measurement | Average of N iterations (configurable, default 5) |
| Input data | Identical image for CPU and GPU |

**Speedup formula:**
```
Speedup = CPU_avg_time_ms / GPU_kernel_avg_time_ms
```

Kernel-only time is used for the pure compute comparison.
End-to-end GPU time (including memory transfers) is reported separately.

> ⚠️ Speedup values depend on hardware. No specific numbers are claimed here.
> Run the benchmark on your own machine to get real measurements.

---

## Algorithms

### Grayscale Conversion
```
Gray = 0.299·R + 0.587·G + 0.114·B   (ITU-R BT.601 luminance)
```
Each pixel is independent — ideal for GPU parallelism.

### Gaussian Blur
```
G(x,y) = exp(-(x²+y²) / (2σ²))
```
Each output pixel is a weighted average of its neighbourhood.
Kernel size = `2·radius + 1` (e.g. radius=3 → 7×7 kernel).

### Sobel Edge Detection
```
Gx = [-1  0 +1; -2  0 +2; -1  0 +1]
Gy = [-1 -2 -1;  0  0  0; +1 +2 +1]
Magnitude = √(Gx² + Gy²)
```
Works on grayscale input. High magnitude = edge.

### Image Sharpening
```
K = [0 -1 0; -1 5 -1; 0 -1 0]
```
Equivalent to: `output = input + (input - blurred_input)`

---

## Known Limitations

1. **PyCUDA Gaussian Blur** — The configurable Gaussian kernel requires passing
   kernel weights at runtime.  The full GPU Gaussian blur is implemented in the
   C++ CUDA library (`cuda_processing.cu`).  The PyCUDA Python path shows CPU
   results for this operation with an explanatory message.

2. **Shared memory optimisation** — The convolution kernels use global GPU memory.
   Using CUDA shared memory would reduce latency for large kernels.  This is
   documented as future work in the source code.

3. **Memory transfer overhead** — For small images, GPU total time may exceed CPU
   time due to host↔device transfer overhead.  The speedup is most visible on
   images ≥ 1024×1024 px.

4. **Windows PyCUDA installation** — PyCUDA on Windows requires the CUDA Toolkit
   and a compatible C++ compiler.  Linux is easier for GPU development.

---

## Future Improvements

- [ ] CUDA shared memory for convolution kernels (reduces global memory latency)
- [ ] CUDA constant memory for filter kernels (broadcast to all threads efficiently)
- [ ] Multi-image batch processing benchmark
- [ ] Half-precision (FP16) GPU operations for modern GPUs
- [ ] CUDA Unified Memory for simplified memory management
- [ ] Additional operations: histogram equalisation, dilation/erosion

---

## Quick-Start Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Launch dashboard
streamlit run app.py

# Run tests
pytest tests/ -v

# Build C++ library (requires CMake + compiler)
mkdir build && cd build && cmake .. && cmake --build .

# CLI benchmark
./gpu_image_proc images/sample.jpg results/ 16 5
```

---

*GPU Image Processing & Performance Optimization Engine — CUDA C++ Portfolio Project*
