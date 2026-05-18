# Linux Compatibility Notes

## Context

The AniSora 12GB runtime package used in this project was originally packaged around a Windows-oriented runtime layout. In practice, this meant that simply copying the package onto a Linux multi-GPU server did not produce a runnable image-to-video pipeline.

This document records the main blockers, the minimal compatibility strategy used during the project, and the limitations of the resulting runtime patches.

## Main blockers observed on Linux

### 1. Windows-specific runtime artifacts

The package included runtime pieces that were designed around a Windows Python environment, especially compiled extensions packaged in a way that could not be used directly on Linux.

### 2. Missing quantization kernels

The low-VRAM AniSora package relied on custom quantization-related components such as:

- `q8_kernels_cuda`
- `vllm` custom quantization ops

Once these components were unavailable, the quantized linear path could not be executed as-is.

### 3. Unavailable optimized kernel paths

Some configuration branches depended on kernel paths that were not available in the Linux validation environment. In particular, avoiding unavailable branches such as `cutlass_scaled_mm` was necessary to restore a working pipeline.

## Minimal compatibility strategy

The project followed a **minimal runnable pipeline first** approach rather than attempting a full runtime refactor.

The main steps were:

1. Trace the actual inference call path from the image-to-video entrypoint.
2. Identify where quantized linear layers and custom ops were invoked.
3. Replace the missing Windows-only runtime pieces with lightweight PyTorch fallback shims.
4. Keep low-VRAM loading strategies enabled to preserve practical usability.
5. Separate Linux-oriented configs from the original packaged runtime files.

## Patch contents in this repository

### `runtime_patches/q8_kernels/`

This patch provides a minimal PyTorch fallback for quantized linear operations.

What it does:

- dequantizes the tensor inputs using the provided scale tensors
- performs matrix multiplication with standard PyTorch ops
- supports the `q8_linear` and `fp8_linear` entrypoints used during validation

Why it was useful:

- it was enough to unblock the minimal runnable inference path
- it allowed the rest of the pipeline to execute without requiring the original custom kernel build

Limitation:

- this fallback is aimed at compatibility and validation, not peak performance

### `runtime_patches/vllm/_custom_ops.py`

This patch provides a lightweight replacement for quantization helper ops used by the runtime.

What it does:

- computes a safe activation scale from the tensor maximum
- provides a fallback `scaled_int8_quant`
- provides a fallback `scaled_fp8_quant`

Why it was useful:

- it restored the quantization-related API surface expected by the runtime
- it reduced the amount of invasive code changes needed elsewhere in the pipeline

Limitation:

- it is only intended to support experimentation and validation of the runtime path

## Config-side changes

Besides the Python-level compatibility patches, the following config-side choices were important:

- keep `cpu_offload` enabled
- keep `lazy_load` enabled
- keep `offload_to_disk` enabled
- route CLIP quantization through `fp8-q8f`
- avoid unavailable optimized kernel branches

These choices were essential because the goal was not just “make it import,” but “make it generate usable video results under practical VRAM limits.”

## Why this matters

The value of this project was not only in getting a demo to run once. The more important outcome was proving that:

- the low-VRAM AniSora package could be adapted to Linux without a full reimplementation
- the quantized model path could still be exercised with fallback logic
- low-VRAM strategies remained usable enough for practical 3s and 6s inference experiments

## Remaining limitations

The current compatibility layer should be understood as an **experiment-time Linux adaptation**, not as a production-grade runtime replacement.

Open limitations include:

- fallback ops are slower than the original custom kernel path
- not every upstream optimization path is covered
- the patches were validated on the exercised inference routes, not exhaustively across all tasks
- longer video settings still expose quality and temporal consistency trade-offs

## Related files

- `runtime_patches/q8_kernels/functional/linear.py`
- `runtime_patches/vllm/_custom_ops.py`
- `configs/anisora_linux_demo_smoke_49f.example.json`
- `configs/anisora_linux_demo_480p4_49f.example.json`
- `configs/anisora_linux_demo_480p4_97f.example.json`
