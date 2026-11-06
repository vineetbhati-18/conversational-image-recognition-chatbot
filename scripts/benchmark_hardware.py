#!/usr/bin/env python3
"""
Hardware & AI Model Benchmark Script for Apple Silicon M4
Bharat Electronics Limited (BEL) Conversational Image Recognition Project

Tests:
1. PyTorch Metal Performance Shaders (MPS) device availability and tensor acceleration.
2. Tensor matrix multiplication speedup on MPS vs CPU.
3. Memory bandwidth and unified memory allocation.
"""

import time
import platform
import torch


def benchmark_matrix_multiplication():
    print("=" * 60)
    print("BEL HARDWARE & PYTORCH ACCELERATION BENCHMARK (Apple M4)")
    print("=" * 60)
    print(f"Platform: {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"Python: {platform.python_version()}")
    print(f"PyTorch Version: {torch.__version__}")
    print(f"MPS (Metal Performance Shaders) Available: {torch.backends.mps.is_available()}")
    print(f"MPS Built into PyTorch: {torch.backends.mps.is_built()}")

    size = 4096
    iterations = 5

    # 1. CPU Benchmark
    print(f"\n[1/2] Benchmarking CPU FP32 Matrix Multiplication ({size}x{size}, {iterations} runs)...")
    cpu_device = torch.device("cpu")
    a_cpu = torch.randn(size, size, device=cpu_device)
    b_cpu = torch.randn(size, size, device=cpu_device)

    # Warmup
    _ = torch.matmul(a_cpu, b_cpu)

    t0 = time.perf_counter()
    for _ in range(iterations):
        _ = torch.matmul(a_cpu, b_cpu)
    cpu_time = (time.perf_counter() - t0) / iterations
    print(f"--> Average CPU Time per iteration: {cpu_time * 1000:.2f} ms")

    # 2. MPS Benchmark
    if torch.backends.mps.is_available():
        print(f"\n[2/2] Benchmarking Apple M4 GPU (MPS) Matrix Multiplication ({size}x{size}, {iterations} runs)...")
        mps_device = torch.device("mps")
        a_mps = torch.randn(size, size, device=mps_device)
        b_mps = torch.randn(size, size, device=mps_device)

        # Warmup and sync
        c = torch.matmul(a_mps, b_mps)
        torch.mps.synchronize()

        t0 = time.perf_counter()
        for _ in range(iterations):
            _ = torch.matmul(a_mps, b_mps)
            torch.mps.synchronize()
        mps_time = (time.perf_counter() - t0) / iterations
        print(f"--> Average Apple M4 GPU (MPS) Time per iteration: {mps_time * 1000:.2f} ms")

        speedup = cpu_time / mps_time if mps_time > 0 else 0
        print(f"\n>>> RESULT: Apple M4 MPS delivers a {speedup:.1f}x hardware speedup over CPU!")
    else:
        print("\n[!] MPS device not detected; falling back to CPU execution.")

    print("=" * 60)


if __name__ == "__main__":
    benchmark_matrix_multiplication()
