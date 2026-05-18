from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from common import (
    build_infer_command,
    default_model_path,
    default_python_bin,
    default_runtime_root,
    ensure_parent,
    load_prompt_text,
    resolve_path,
    shell_preview,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single AniSora image-to-video demo.")
    parser.add_argument("--runtime-root", default=default_runtime_root(), help="Root directory of the AniSora runtime package.")
    parser.add_argument("--python-bin", default=default_python_bin(), help="Python executable used inside the runtime environment.")
    parser.add_argument("--entrypoint", default="lightx2v/infer.py", help="Relative entrypoint inside the runtime root.")
    parser.add_argument("--config-json", required=True, help="Inference config JSON.")
    parser.add_argument("--model-path", default=default_model_path(), help="AniSora model directory used by --model_path.")
    parser.add_argument("--model-cls", default="wan2.1")
    parser.add_argument("--task", default="i2v")
    parser.add_argument("--image-path", required=True, help="Input image path.")
    parser.add_argument("--prompt", default=None, help="Prompt text.")
    parser.add_argument("--prompt-file", default=None, help="UTF-8 text file containing the prompt.")
    parser.add_argument("--save-video-path", required=True, help="Output video path.")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without executing it.")
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
    image_path = resolve_path(args.image_path)
    save_video_path = resolve_path(args.save_video_path)
    prompt = load_prompt_text(args.prompt, args.prompt_file)

    ensure_parent(save_video_path)
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

    print(shell_preview(command))
    if args.dry_run:
        return 0

    completed = subprocess.run(command, cwd=runtime_root, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
