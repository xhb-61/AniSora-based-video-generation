from __future__ import annotations

import os
import shlex
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(value: str | Path, base: Path | None = None) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if base is None:
        base = repo_root()
    return (base / path).resolve()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_prompt_text(prompt: str | None, prompt_file: str | None) -> str:
    if prompt and prompt_file:
        raise ValueError("Use either --prompt or --prompt-file, not both.")
    if prompt_file:
        return Path(prompt_file).read_text(encoding="utf-8").strip()
    if prompt:
        return prompt.strip()
    raise ValueError("Either --prompt or --prompt-file is required.")


def parse_inference_line(line: str) -> tuple[str, str, str]:
    raw = line.strip()
    if not raw or raw.startswith("#"):
        raise ValueError("Empty or comment line")
    if "@@" not in raw:
        raise ValueError(f"Invalid line, missing @@ separator: {raw}")
    prompt, remainder = raw.split("@@", 1)
    image_path, _, tail = remainder.partition("&&")
    return prompt.strip(), image_path.strip(), tail.strip()


def make_safe_name(text: str) -> str:
    keep = []
    for char in text:
        if char.isalnum() or char in {"-", "_"}:
            keep.append(char)
        else:
            keep.append("_")
    safe = "".join(keep).strip("_")
    return safe or "sample"


def build_infer_command(
    *,
    python_bin: str,
    runtime_root: Path,
    config_json: Path,
    model_path: str,
    image_path: Path,
    prompt: str,
    save_video_path: Path,
    entrypoint: str = "lightx2v/infer.py",
    model_cls: str = "wan2.1",
    task: str = "i2v",
) -> list[str]:
    entry = runtime_root / entrypoint
    return [
        python_bin,
        str(entry),
        "--model_cls",
        model_cls,
        "--task",
        task,
        "--model_path",
        model_path,
        "--config_json",
        str(config_json),
        "--image_path",
        str(image_path),
        "--prompt",
        prompt,
        "--save_video_path",
        str(save_video_path),
    ]


def shell_preview(command: list[str]) -> str:
    return shlex.join(command)


def default_runtime_root() -> str:
    return os.environ.get("ANISORA_RUNTIME_ROOT", "")


def default_model_path() -> str:
    return os.environ.get("ANISORA_MODEL_PATH", "")


def default_python_bin() -> str:
    return os.environ.get("ANISORA_PYTHON_BIN", "python")
