from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

import imageio.v3 as iio

from common import resolve_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a benchmark CSV and summary Markdown from a JSON manifest.")
    parser.add_argument("--manifest", required=True, help="JSON manifest describing benchmark experiments.")
    parser.add_argument("--output-csv", required=True, help="Output CSV path.")
    parser.add_argument("--output-md", required=True, help="Output Markdown summary path.")
    return parser.parse_args()


def probe_video(video_path: Path) -> dict:
    meta = iio.immeta(video_path)
    frames = list(iio.imiter(video_path))
    frame_count = len(frames)
    if frame_count:
        height, width = frames[0].shape[:2]
    else:
        width, height = meta.get("size", (None, None))
    return {
        "measured_width": width,
        "measured_height": height,
        "measured_fps": float(meta.get("fps")) if meta.get("fps") else None,
        "measured_duration_sec": float(meta.get("duration")) if meta.get("duration") else None,
        "measured_frame_count": frame_count,
    }


def format_float(value: float | None, digits: int = 2) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def main() -> int:
    args = parse_args()
    manifest_path = resolve_path(args.manifest)
    output_csv = resolve_path(args.output_csv)
    output_md = resolve_path(args.output_md)
    display_manifest = Path(args.manifest).as_posix()
    display_csv = Path(args.output_csv).as_posix()

    experiments = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = []
    grouped = defaultdict(list)

    for item in experiments:
        video_path = resolve_path(item["output_video"])
        probe = probe_video(video_path)
        fps = probe["measured_fps"] or item.get("fps")
        target_frames = item.get("target_frames")
        duration_from_frames = (target_frames / fps) if fps and target_frames else None
        row = {
            "experiment_id": item["experiment_id"],
            "family": item["family"],
            "sample_id": item["sample_id"],
            "config_id": item["config_id"],
            "config_path": item["config_path"],
            "source_image": item["source_image"],
            "prompt_source": item["prompt_source"],
            "output_video": item["output_video"],
            "infer_steps": item.get("infer_steps"),
            "target_frames": target_frames,
            "expected_resolution": item.get("expected_resolution", ""),
            "measured_width": probe["measured_width"],
            "measured_height": probe["measured_height"],
            "measured_fps": format_float(probe["measured_fps"]),
            "measured_duration_sec": format_float(probe["measured_duration_sec"]),
            "duration_from_frames_sec": format_float(duration_from_frames),
            "measured_frame_count": probe["measured_frame_count"],
            "file_size_kb": format_float(video_path.stat().st_size / 1024.0, 1),
            "peak_vram_gb_est": item.get("peak_vram_gb_est", ""),
            "status": item.get("status", "ok"),
            "notes": item.get("notes", ""),
        }
        rows.append(row)
        grouped[item["config_id"]].append(row)

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    output_md.parent.mkdir(parents=True, exist_ok=True)
    with output_md.open("w", encoding="utf-8") as handle:
        handle.write("# Benchmark Summary\n\n")
        handle.write(f"- experiments: {len(rows)}\n")
        handle.write(f"- source manifest: `{display_manifest}`\n")
        handle.write(f"- csv: `{display_csv}`\n\n")
        handle.write("## Per-config overview\n\n")
        handle.write("| Config | Runs | Avg duration (s) | Avg file size (KB) |\n")
        handle.write("| --- | --- | --- | --- |\n")
        for config_id, config_rows in grouped.items():
            durations = [float(r["measured_duration_sec"]) for r in config_rows if r["measured_duration_sec"]]
            sizes = [float(r["file_size_kb"]) for r in config_rows if r["file_size_kb"]]
            handle.write(
                f"| {config_id} | {len(config_rows)} | {mean(durations):.2f} | {mean(sizes):.1f} |\n"
            )

        handle.write("\n## Notes\n\n")
        for row in rows:
            handle.write(
                f"- `{row['experiment_id']}`: {row['notes']}\n"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
