# AniSora-based-video-generation

> Deployment, Linux compatibility adaptation, inference experiments, and lightweight benchmarking for the Bilibili AniSora 12GB image-to-video runtime package.

## Overview

This repository records my work around **deploying and validating AniSora on a Linux multi-GPU server**, with a focus on:

- upstream reference: [bilibili/Index-anisora](https://github.com/bilibili/Index-anisora/tree/main)
- analyzing the 12GB low-VRAM runtime package structure
- adapting Windows-oriented runtime dependencies for Linux inference
- validating multiple inference settings for quality, duration, consistency, and VRAM trade-offs
- organizing reusable configs, runtime patches, recorded outputs, and benchmark artifacts

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
- Added reusable scripts for single-run, batch-run, benchmark building, and comparison board extraction

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
│   ├── inference_360_inputs
│   └── input_example1.png
├── configs
│   ├── anisora_linux_demo_480p4_49f.example.json
│   ├── anisora_linux_demo_480p4_97f.example.json
│   └── anisora_linux_demo_smoke_49f.example.json
├── data
│   ├── inference-imgs-360
│   └── inference_360.txt
├── docs
│   ├── benchmark_report.md
│   ├── linux_compatibility.md
│   └── project_report_zh.md
├── results
│   ├── benchmark.csv
│   ├── benchmark_manifest.json
│   ├── benchmark_summary.md
│   ├── boards
│   └── videos
├── runtime_patches
│   ├── q8_kernels
│   └── vllm
└── scripts
    ├── build_benchmark.py
    ├── common.py
    ├── extract_compare_frames.py
    ├── run_batch.py
    └── run_single.py
```

## Notes on the Linux Compatibility Fix

The original AniSora 12GB runtime package contained Windows-oriented pieces that could not be used directly on Linux. To quickly validate model usability, I followed a **minimal runnable pipeline first** strategy:

- traced the quantized linear / custom-op call path
- replaced unavailable runtime pieces with lightweight PyTorch fallback implementations
- adjusted config choices to avoid unavailable kernel paths
- kept low-VRAM loading and offload strategies enabled

The patches in `runtime_patches/` are **minimal experiment-time shims**, intended for compatibility validation rather than peak inference speed.

More details are documented in:

- [docs/linux_compatibility.md](docs/linux_compatibility.md)

## Benchmark Artifacts

This repository now includes:

- recorded output videos for the tested single-demo and batch-360 runs
- `results/benchmark_manifest.json` with structured experiment metadata
- `results/benchmark.csv` generated from the manifest and probed video metadata
- `results/benchmark_summary.md` with per-config aggregates
- `results/boards/*.png` comparison boards generated from the saved videos

For the benchmark-oriented write-up, see:

- [docs/benchmark_report.md](docs/benchmark_report.md)

## Reproduction Helpers

### Single run

```bash
python scripts/run_single.py \
  --runtime-root "/mnt/local/home/hbxu/Bilibili vedio/models/wan" \
  --model-path "/home/hbxu/local/Bilibili vedio/models/wan/models/anisora" \
  --config-json configs/anisora_linux_demo_480p4_49f.example.json \
  --image-path assets/input_example1.png \
  --prompt "your prompt here" \
  --save-video-path outputs/single_demo.mp4 \
  --dry-run
```

### Batch run

```bash
python scripts/run_batch.py \
  --runtime-root "/mnt/local/home/hbxu/Bilibili vedio/models/wan" \
  --model-path "/home/hbxu/local/Bilibili vedio/models/wan/models/anisora" \
  --config-json configs/anisora_linux_demo_480p4_49f.example.json \
  --batch-file data/inference_360.txt \
  --data-root . \
  --output-dir outputs/batch_360 \
  --output-suffix quality_49f \
  --dry-run
```

### Benchmark generation

```bash
python scripts/build_benchmark.py \
  --manifest results/benchmark_manifest.json \
  --output-csv results/benchmark.csv \
  --output-md results/benchmark_summary.md
```

### Comparison board extraction

```bash
python scripts/extract_compare_frames.py \
  --videos results/videos/single/single_demo_quality_49f.mp4 results/videos/single/single_demo_quality_97f.mp4 \
  --labels quality_49f quality_97f \
  --title "Single demo: 3s vs 6s" \
  --output results/boards/single_3s_vs_6s.png
```

## Included Artifacts

- `docs/project_report_zh.md`
  - a complete Chinese project report for this AniSora deployment and experiment workflow
- `docs/linux_compatibility.md`
  - Linux-side runtime blockers, fallback patches, and limitations
- `docs/benchmark_report.md`
  - a benchmark-oriented summary built from the recorded outputs in this repository
- `configs/*.example.json`
  - reusable example configs matching the tested smoke / 480p / 6s settings
- `data/inference_360.txt`
  - the batch prompt file used for the 360-degree turning experiments
- `runtime_patches/`
  - minimal Linux fallback shims used to validate the runtime pipeline
- `results/`
  - benchmark tables, comparison boards, and the recorded sample output videos
- `scripts/`
  - helper scripts for single-run, batch-run, benchmark generation, and comparison board extraction

## Important Disclaimer

- This repository does **not** include AniSora model weights
- This repository does **not** mirror the full upstream runtime package
- The code here mainly records my own deployment notes, compatibility patches, configs, scripts, and experiment summaries

## Project Reports

- [docs/project_report_zh.md](docs/project_report_zh.md)
- [docs/linux_compatibility.md](docs/linux_compatibility.md)
- [docs/benchmark_report.md](docs/benchmark_report.md)
