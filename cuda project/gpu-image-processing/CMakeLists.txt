cmake_minimum_required(VERSION 3.18)

# ─────────────────────────────────────────────────────────────────────────────
# Project declaration
# ─────────────────────────────────────────────────────────────────────────────
project(gpu_image_processing
        VERSION 1.0
        DESCRIPTION "GPU-Accelerated Image Processing Engine (CUDA C++)"
        LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ─────────────────────────────────────────────────────────────────────────────
# Optional CUDA support
#
# CMake 3.18+ provides first-class CUDA language support.
# We detect CUDA and only enable GPU features when it is available.
# The project builds and runs correctly with CPU-only mode.
# ─────────────────────────────────────────────────────────────────────────────
include(CheckLanguage)
check_language(CUDA)

if(CMAKE_CUDA_COMPILER)
    enable_language(CUDA)
    set(CUDA_AVAILABLE TRUE)
    message(STATUS "CUDA compiler found: ${CMAKE_CUDA_COMPILER}")

    # Minimum compute capability we target.
    # 5.0 covers Maxwell and newer GPUs (GTX 750 Ti and above).
    # Adjust upward (6.1, 7.5, 8.6, etc.) to target a specific GPU generation.
    set(CMAKE_CUDA_ARCHITECTURES "50;60;70;75;80;86" CACHE STRING
        "CUDA architectures to compile for")

    set(CMAKE_CUDA_STANDARD 17)
    set(CMAKE_CUDA_STANDARD_REQUIRED ON)
else()
    set(CUDA_AVAILABLE FALSE)
    message(STATUS "CUDA compiler NOT found — building CPU-only mode.")
endif()

# ─────────────────────────────────────────────────────────────────────────────
# Find OpenCV
# ─────────────────────────────────────────────────────────────────────────────
find_package(OpenCV REQUIRED COMPONENTS core imgcodecs imgproc)
message(STATUS "OpenCV version: ${OpenCV_VERSION}")

# ─────────────────────────────────────────────────────────────────────────────
# CPU processing library
# ─────────────────────────────────────────────────────────────────────────────
add_library(cpu_processing STATIC
    src/cpu_processing.cpp
    src/cpu_processing.h
    src/benchmark.cpp
    src/benchmark.h
)

target_include_directories(cpu_processing PUBLIC src)

# Link math library on Linux (not needed on Windows/MSVC)
if(UNIX)
    target_link_libraries(cpu_processing PUBLIC m)
endif()

# ─────────────────────────────────────────────────────────────────────────────
# CUDA processing library (only when CUDA is available)
# ─────────────────────────────────────────────────────────────────────────────
if(CUDA_AVAILABLE)
    add_library(cuda_processing STATIC
        src/cuda_processing.cu
        src/cuda_processing.h
    )

    target_include_directories(cuda_processing PUBLIC src)

    # CUDA separable compilation allows device functions to be called across
    # compilation units — useful for larger projects.
    set_target_properties(cuda_processing PROPERTIES
        CUDA_SEPARABLE_COMPILATION ON
    )

    # Tell all targets that CUDA is compiled in
    target_compile_definitions(cuda_processing PUBLIC CUDA_AVAILABLE)
    target_compile_definitions(cpu_processing  PUBLIC CUDA_AVAILABLE)
endif()

# ─────────────────────────────────────────────────────────────────────────────
# Main executable
# ─────────────────────────────────────────────────────────────────────────────
add_executable(gpu_image_proc src/main.cpp)

target_include_directories(gpu_image_proc PRIVATE src)
target_link_libraries(gpu_image_proc PRIVATE cpu_processing ${OpenCV_LIBS})

if(CUDA_AVAILABLE)
    target_link_libraries(gpu_image_proc PRIVATE cuda_processing)
    target_compile_definitions(gpu_image_proc PRIVATE CUDA_AVAILABLE)
endif()

# ─────────────────────────────────────────────────────────────────────────────
# Compiler warning flags (MSVC vs GCC/Clang)
# ─────────────────────────────────────────────────────────────────────────────
if(MSVC)
    target_compile_options(cpu_processing PRIVATE /W4)
    target_compile_options(gpu_image_proc PRIVATE /W4)
else()
    target_compile_options(cpu_processing PRIVATE -Wall -Wextra -O2)
    target_compile_options(gpu_image_proc PRIVATE -Wall -Wextra -O2)
endif()

# ─────────────────────────────────────────────────────────────────────────────
# Installation
# ─────────────────────────────────────────────────────────────────────────────
install(TARGETS gpu_image_proc RUNTIME DESTINATION bin)

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
message(STATUS "")
message(STATUS "──── GPU Image Processing Engine — Build Summary ────")
message(STATUS "  CUDA support   : ${CUDA_AVAILABLE}")
if(CUDA_AVAILABLE)
    message(STATUS "  CUDA archs     : ${CMAKE_CUDA_ARCHITECTURES}")
endif()
message(STATUS "  OpenCV version : ${OpenCV_VERSION}")
message(STATUS "  C++ standard   : ${CMAKE_CXX_STANDARD}")
message(STATUS "────────────────────────────────────────────────────")
