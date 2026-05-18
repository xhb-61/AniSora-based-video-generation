# Benchmark Summary

- experiments: 12
- source manifest: `results/benchmark_manifest.json`
- csv: `results/benchmark.csv`

## Per-config overview

| Config | Runs | Avg duration (s) | Avg file size (KB) |
| --- | --- | --- | --- |
| smoke_49f | 4 | 3.06 | 71.0 |
| quality_49f | 4 | 3.06 | 243.8 |
| quality_97f | 4 | 6.06 | 493.9 |

## Notes

- `single_smoke_49f`: Smoke baseline for the single-image demo. Fast and light, but weaker in edge clarity and clothing detail.
- `single_quality_49f`: Higher-quality 3s result for the same single image. Character structure and texture detail are clearly improved.
- `single_quality_97f`: 6s version of the single-image demo. Motion is more complete, while later-frame drift becomes more visible.
- `batch360_sample1_smoke_49f`: Baseline batch sample 1 result. Motion is present, but visual fidelity remains limited.
- `batch360_sample2_smoke_49f`: Baseline batch sample 2 result. Useful as a low-cost reference point before raising resolution and steps.
- `batch360_sample3_smoke_49f`: Baseline batch sample 3 result. Lower detail and weaker clothing texture retention than the 480p run.
- `batch360_sample1_quality_49f`: Higher-quality batch sample 1 result. Character structure and clothing detail are noticeably better.
- `batch360_sample2_quality_49f`: Higher-quality batch sample 2 result. Better structure and richer texture than the smoke configuration.
- `batch360_sample3_quality_49f`: Higher-quality batch sample 3 result. The dress texture and silhouette are more stable than in the smoke run.
- `batch360_sample1_quality_97f`: Longer batch sample 1 result. More complete rotation, while later frames remain relatively stable overall.
- `batch360_sample2_quality_97f`: Longer batch sample 2 result. Motion is more complete, but later-frame appearance drift is more obvious.
- `batch360_sample3_quality_97f`: Longer batch sample 3 result. Motion is more graceful and generally stable, with mild drift in later frames.
