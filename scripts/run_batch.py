from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from common import (
    build_infer_command,
    default_model_path,
    default_python_bin,
    default_runtime_root,
    ensure_parent,
    make_safe_name,
    parse_inference_line,
    resolve_path,
    repo_root,
    shell_preview,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run batch AniSora demos from an inference_360-style TXT file.")
    parser.add_argument("--runtime-root", default=default_runtime_root(), help="Root directory of the AniSora runtime package.")
    parser.add_argument("--python-bin", default=default_python_bin(), help="Python executable used inside the runtime environment.")
    parser.add_argument("--entrypoint", default="lightx2v/infer.py", help="Relative entrypoint inside the runtime root.")
    parser.add_argument("--config-json", required=True, help="Inference config JSON.")
    parser.add_argument("--model-path", default=default_model_path(), help="AniSora model directory used by --model_path.")
    parser.add_argument("--model-cls", default="wan2.1")
    parser.add_argument("--task", default="i2v")
    parser.add_argument("--batch-file", required=True, help="TXT file whose lines look like: prompt@@image&&0")
    parser.add_argument("--data-root", default=None, help="Optional root used to resolve relative image paths.")
    parser.add_argument("--output-dir", required=True, help="Directory for generated videos.")
    parser.add_argument("--output-suffix", default="", help="Suffix appended to each output filename.")
    parser.add_argument("--manifest-out", default=None, help="Optional JSONL manifest file for executed commands.")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit on the number of prompts to run.")
    parser.add_argument("--skip-existing", action="store_true", help="Skip items whose output video already exists.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.runtime_root:
        print("Missing --runtime-root or ANISORA_RUNTIME_ROOT.", file=sys.stderr)
        return 2
    if not args.model_path:
        print("Missing --model-path or ANISORA_MODEL_PATH.", file=sys.stderr)
        return 2

    runtime_root = resolve_path(args.runtime_root, Path.cwd())
    config_json = resolve_path(args.config_json)
    batch_file = resolve_path(args.batch_file)
    output_dir = resolve_path(args.output_dir)
    data_root = resolve_path(args.data_root, Path.cwd()) if args.data_root else batch_file.parent
    manifest_out = resolve_path(args.manifest_out) if args.manifest_out else output_dir / "run_manifest.jsonl"

    output_dir.mkdir(parents=True, exist_ok=True)
    ensure_parent(manifest_out)

    lines = batch_file.read_text(encoding="utf-8").splitlines()
    records = []
    failures = 0

    for idx, line in enumerate(lines, start=1):
        if args.limit is not None and len(records) >= args.limit:
            break
        try:
            prompt, image_rel, tail = parse_inference_line(line)
        except ValueError:
            continue

        image_path = resolve_path(image_rel, data_root)
        if not image_path.exists():
            candidate = resolve_path(image_rel, repo_root())
            if candidate.exists():
                image_path = candidate
        stem = make_safe_name(image_path.stem)
        suffix = f"_{args.output_suffix}" if args.output_suffix else ""
        save_video_path = output_dir / f"{idx:03d}_{stem}{suffix}.mp4"

        command = build_infer_command(
            python_bin=args.python_bin,
            runtime_root=runtime_root,
            config_json=config_json,
            model_path=args.model_path,
            image_path=image_path,
            prompt=prompt,
            save_video_path=save_video_path,
            entrypoint=args.entrypoint,
            model_cls=args.model_cls,
            task=args.task,
        )

        record = {
            "index": idx,
            "image_path": str(image_path),
            "output_video": str(save_video_path),
            "tag": tail,
            "command": command,
            "command_preview": shell_preview(command),
            "prompt_preview": prompt[:140],
        }

        if args.skip_existing and save_video_path.exists():
            record["status"] = "skipped_existing"
            print(f"[skip] {save_video_path}")
            records.append(record)
            continue

        print(record["command_preview"])
        if args.dry_run:
            record["status"] = "dry_run"
            records.append(record)
            continue

        completed = subprocess.run(command, cwd=runtime_root, check=False)
        record["return_code"] = completed.returncode
        record["status"] = "ok" if completed.returncode == 0 else "failed"
        failures += int(completed.returncode != 0)
        records.append(record)

    with manifest_out.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
