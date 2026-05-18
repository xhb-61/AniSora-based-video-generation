# AniSora-based-video-generation

> Deployment, Linux compatibility adaptation, and inference experiments for the Bilibili AniSora 12GB image-to-video runtime package.

## Overview

This repository records my work around **deploying and validating AniSora on a Linux multi-GPU server**, with a focus on:

- analyzing the 12GB low-VRAM runtime package structure
- adapting Windows-oriented runtime dependencies for Linux inference
- validating multiple inference settings for quality, duration, consistency, and VRAM trade-offs
- organizing reusable configs, minimal compatibility patches, and experiment notes

This project is **not** about model pretraining or large-scale finetuning. It is an **engineering + inference optimization** project centered on getting a practical AniSora pipeline running in a real Linux environment.

## What I Did

- Deployed the AniSora 12GB runtime package on a Linux multi-GPU server
- Investigated blocking dependencies such as `q8_kernels` and `vllm` custom quantization ops
- Implemented minimal **PyTorch fallback shims** to replace missing Windows-only runtime pieces
- Preserved low-VRAM strategies such as `cpu_offload`, `lazy_load`, and `offload_to_disk`
- Designed and ran multiple image-to-video demos, including:
  - smoke config: `320p / 1 step / 49 frames`
  - quality config: `480p / 4 steps / 49 frames`
  - longer video config: `480p / 4 steps / 97 frames`
- Compared results across visual quality, temporal consistency, and memory usage

## Key Results

| Setting | Resolution | Steps | Frames | Approx. Duration | Main Observation |
| --- | --- | --- | --- | --- | --- |
| Smoke | 320 x 192 | 1 | 49 | 3.06s | Fast and light, but visibly weaker in structure and texture quality |
| Quality | 832 x 480 | 4 | 49 | 3.06s | Clear improvement in character structure, texture details, and edges |
| Longer video | 832 x 480 | 4 | 97 | 6.06s | More complete motion, but more temporal drift in later frames |

Additional observations:

- `480p / 4 steps` was clearly better than the smoke setting in visual quality
- extending from `3s` to `6s` improved motion completeness
- longer duration also made later-frame drift more noticeable
- the `97-frame` setup pushed VRAM to around **17GB - 18GB** on RTX 4090 during testing

## Visual Comparison

### Input example

![Input example](assets/input_example1.png)

### Smoke vs 480p / 4 steps

![Smoke vs 480p/4 steps](assets/compare_frames_example1.png)

### 3s vs 6s

![3s vs 6s](assets/compare_duration_example1.png)

## Repository Structure

```text
.
├── README.md
├── assets
│   ├── compare_duration_example1.png
│   ├── compare_frames_example1.png
│   └── input_example1.png
├── configs
│   ├── anisora_linux_demo_480p4_49f.example.json
│   ├── anisora_linux_demo_480p4_97f.example.json
│   └── anisora_linux_demo_smoke_49f.example.json
├── docs
│   └── project_report_zh.md
└── runtime_patches
    ├── q8_kernels
    └── vllm
```

## Notes on the Linux Compatibility Fix

The original AniSora 12GB runtime package contained Windows-oriented pieces that could not be used directly on Linux. To quickly validate model usability, I followed a **minimal runnable pipeline first** strategy:

- traced the quantized linear / custom-op call path
- replaced unavailable runtime pieces with lightweight PyTorch fallback implementations
- adjusted config choices to avoid unavailable kernel paths
- kept low-VRAM loading and offload strategies enabled

The patches in `runtime_patches/` are **minimal experiment-time shims**, intended for compatibility validation rather than peak inference speed.

## Included Artifacts

- `docs/project_report_zh.md`
  - a complete Chinese project report for this AniSora deployment and experiment workflow
- `configs/*.example.json`
  - reusable example configs matching the tested smoke / 480p / 6s settings
- `runtime_patches/`
  - minimal Linux fallback shims used to validate the runtime pipeline

## Important Disclaimer

- This repository does **not** include AniSora model weights
- This repository does **not** mirror the full upstream runtime package
- The code here mainly records my own deployment notes, compatibility patches, configs, and experiment summaries

## Project Report

For the full Chinese write-up, see:

- [docs/project_report_zh.md](docs/project_report_zh.md)
