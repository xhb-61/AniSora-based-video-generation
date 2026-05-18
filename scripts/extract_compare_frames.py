from __future__ import annotations

import argparse
from pathlib import Path

import imageio.v3 as iio
from PIL import Image, ImageDraw, ImageFont

from common import resolve_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract key frames from several videos and stitch them into one comparison board.")
    parser.add_argument("--videos", nargs="+", required=True, help="Video files to compare.")
    parser.add_argument("--labels", nargs="*", default=None, help="Optional row labels. Defaults to video stems.")
    parser.add_argument("--frame-ratios", default="0.0,0.5,0.98", help="Comma-separated ratios in [0, 1].")
    parser.add_argument("--output", required=True, help="Output PNG path.")
    parser.add_argument("--title", default="", help="Optional title shown above the board.")
    parser.add_argument("--cell-width", type=int, default=256, help="Target width for each frame cell.")
    return parser.parse_args()


def to_pil(frame) -> Image.Image:
    return Image.fromarray(frame).convert("RGB")


def main() -> int:
    args = parse_args()
    video_paths = [resolve_path(path) for path in args.videos]
    labels = args.labels or [path.stem for path in video_paths]
    ratios = [float(part.strip()) for part in args.frame_ratios.split(",") if part.strip()]
    if len(labels) != len(video_paths):
        raise ValueError("Number of labels must match number of videos.")

    font = ImageFont.load_default()
    row_label_width = 180
    header_height = 36
    title_height = 38 if args.title else 0
    padding = 12

    frames_per_video = []
    max_cell_height = 0

    for video_path in video_paths:
        frames = list(iio.imiter(video_path))
        if not frames:
            raise RuntimeError(f"No frames decoded from: {video_path}")

        selected = []
        for ratio in ratios:
            index = min(max(int(round((len(frames) - 1) * ratio)), 0), len(frames) - 1)
            image = to_pil(frames[index])
            scale = args.cell_width / image.width
            resized = image.resize((args.cell_width, int(image.height * scale)))
            selected.append(resized)
            max_cell_height = max(max_cell_height, resized.height)
        frames_per_video.append(selected)

    board_width = row_label_width + len(ratios) * (args.cell_width + padding) + padding
    board_height = title_height + header_height + len(video_paths) * (max_cell_height + header_height) + padding
    board = Image.new("RGB", (board_width, board_height), color="white")
    draw = ImageDraw.Draw(board)

    y = padding
    if args.title:
        draw.text((padding, y), args.title, fill="black", font=font)
        y += title_height

    for col, ratio in enumerate(ratios):
        x = row_label_width + padding + col * (args.cell_width + padding)
        draw.text((x, y), f"{int(ratio * 100)}%", fill="black", font=font)
    y += header_height

    for row_idx, (label, row_frames) in enumerate(zip(labels, frames_per_video)):
        draw.text((padding, y + max_cell_height // 2), label, fill="black", font=font)
        for col_idx, image in enumerate(row_frames):
            x = row_label_width + padding + col_idx * (args.cell_width + padding)
            board.paste(image, (x, y))
        y += max_cell_height + header_height

    output_path = resolve_path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    board.save(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
