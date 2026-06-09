#!/usr/bin/env python3
"""分析上车相机采样帧的亮度可见性。"""

from __future__ import annotations

import csv
import json
import math
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path


SPRINT = "2026.06.10_02-50_board-camera-visibility-diagnostic"
# 脚本位于 sprints/<sprint>/scripts/，向上三级就是仓库根目录。
ROOT = Path(__file__).resolve().parents[3]
SPRINT_DIR = ROOT / "sprints" / SPRINT
ARTIFACTS = SPRINT_DIR / "artifacts"
REMOTE_CAPTURE = ARTIFACTS / "remote_capture"
SUMMARY_JSON = ARTIFACTS / "camera_visibility_summary.json"
SUMMARY_CSV = ARTIFACTS / "camera_visibility_samples.csv"
CONTACT_PPM = ARTIFACTS / "camera_visibility_contact_sheet.ppm"
CONTACT_JPG = ARTIFACTS / "camera_visibility_contact_sheet.jpg"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    """统一封装外部命令，失败时保留 stderr，便于定位解码工具问题。"""
    return subprocess.run(command, text=True, capture_output=True, check=False)


def decode_with_sips(image_path: Path, tmpdir: Path) -> Path:
    """用系统 sips 解码 JPEG，避免给本轮诊断引入 Pillow/OpenCV 依赖。"""
    bmp_path = tmpdir / f"{image_path.stem}.bmp"
    result = run(["sips", "-s", "format", "bmp", str(image_path), "--out", str(bmp_path)])
    if result.returncode != 0 or not bmp_path.exists():
        raise RuntimeError(f"sips decode failed for {image_path}: {result.stderr.strip()}")
    return bmp_path


def read_bmp_pixels(bmp_path: Path) -> tuple[int, int, list[tuple[int, int, int]]]:
    """读取 sips 生成的 24/32 位 BMP；BMP 自底向上存储，所以需要按行翻转。"""
    data = bmp_path.read_bytes()
    if data[:2] != b"BM":
        raise ValueError(f"not a BMP file: {bmp_path}")

    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    dib_size = struct.unpack_from("<I", data, 14)[0]
    if dib_size < 40:
        raise ValueError(f"unsupported BMP DIB header: {bmp_path}")

    width = struct.unpack_from("<i", data, 18)[0]
    height_signed = struct.unpack_from("<i", data, 22)[0]
    planes = struct.unpack_from("<H", data, 26)[0]
    bits_per_pixel = struct.unpack_from("<H", data, 28)[0]
    compression = struct.unpack_from("<I", data, 30)[0]
    if planes != 1 or bits_per_pixel not in (24, 32) or compression != 0:
        raise ValueError(f"unsupported BMP layout for {bmp_path}")

    # BMP 高度为正时表示底部行先出现；转成常规从上到下的像素序列，方便后续拼 contact sheet。
    top_down = height_signed < 0
    height = abs(height_signed)
    bytes_per_pixel = bits_per_pixel // 8
    stride = ((width * bits_per_pixel + 31) // 32) * 4
    pixels: list[tuple[int, int, int]] = []
    row_indices = range(height) if top_down else range(height - 1, -1, -1)
    for row in row_indices:
        start = pixel_offset + row * stride
        for col in range(width):
            b, g, r = data[start + col * bytes_per_pixel : start + col * bytes_per_pixel + 3]
            pixels.append((r, g, b))
    return width, height, pixels


def luma(rgb: tuple[int, int, int]) -> float:
    """使用 Rec. 601 luma，和 UVC/YUYV 常见标定更接近。"""
    r, g, b = rgb
    return 0.299 * r + 0.587 * g + 0.114 * b


def analyze_pixels(name: str, width: int, height: int, pixels: list[tuple[int, int, int]]) -> dict[str, object]:
    """输出均值、极值和非黑比例；阈值用于判断画面是否仍只能算黑场。"""
    values = [luma(pixel) for pixel in pixels]
    non_black_threshold = 10.0
    visible_threshold = 35.0
    non_black = sum(1 for value in values if value > non_black_threshold)
    bright = sum(1 for value in values if value > visible_threshold)
    total = len(values)
    mean_luma = sum(values) / total if total else 0.0
    variance = sum((value - mean_luma) ** 2 for value in values) / total if total else 0.0
    stddev_luma = math.sqrt(variance)
    min_luma = min(values) if values else 0.0
    max_luma = max(values) if values else 0.0
    dynamic_range_luma = max_luma - min_luma
    non_black_ratio = non_black / total if total else 0.0
    bright_ratio = bright / total if total else 0.0

    # mostly_dark 是诊断判据，不是视觉模型指标；均值低或非黑像素太少都不能证明环境内容可用。
    mostly_dark = mean_luma < 20.0 or non_black_ratio < 0.05
    # 纯灰/纯白帧可能只是亮度偏置或曝光探测结果；必须有足够动态范围才算可见内容候选。
    has_texture = dynamic_range_luma >= 15.0 or stddev_luma >= 5.0
    visible_content = mean_luma >= 35.0 and non_black_ratio >= 0.10 and bright_ratio >= 0.05 and has_texture
    return {
        "sample_name": name,
        "width": width,
        "height": height,
        "mean_luma": round(mean_luma, 6),
        "min_luma": round(min_luma, 6),
        "max_luma": round(max_luma, 6),
        "dynamic_range_luma": round(dynamic_range_luma, 6),
        "stddev_luma": round(stddev_luma, 6),
        "non_black_threshold_luma": non_black_threshold,
        "non_black_ratio": round(non_black_ratio, 9),
        "bright_threshold_luma": visible_threshold,
        "bright_ratio": round(bright_ratio, 9),
        "has_texture_candidate": has_texture,
        "mostly_dark": mostly_dark,
        "visible_content_candidate": visible_content,
        "file": str((REMOTE_CAPTURE / f"{name}.jpg").relative_to(ROOT)),
    }


def downsample(width: int, height: int, pixels: list[tuple[int, int, int]], target_w: int = 160) -> tuple[int, int, list[tuple[int, int, int]]]:
    """最近邻缩略图足够用于黑场 contact sheet，避免引入图像库。"""
    target_h = max(1, round(height * target_w / width))
    output: list[tuple[int, int, int]] = []
    for y in range(target_h):
        src_y = min(height - 1, int(y * height / target_h))
        for x in range(target_w):
            src_x = min(width - 1, int(x * width / target_w))
            output.append(pixels[src_y * width + src_x])
    return target_w, target_h, output


def write_contact_sheet(thumbnails: list[tuple[str, int, int, list[tuple[int, int, int]]]]) -> None:
    """写 PPM contact sheet；再尽量转 JPEG，方便人工打开复核。"""
    if not thumbnails:
        return

    padding = 8
    columns = 2
    tile_w = max(item[1] for item in thumbnails)
    tile_h = max(item[2] for item in thumbnails)
    rows = (len(thumbnails) + columns - 1) // columns
    sheet_w = columns * tile_w + (columns + 1) * padding
    sheet_h = rows * tile_h + (rows + 1) * padding
    background = (24, 24, 24)
    sheet = [background] * (sheet_w * sheet_h)

    for index, (_name, width, height, pixels) in enumerate(thumbnails):
        row = index // columns
        col = index % columns
        origin_x = padding + col * (tile_w + padding)
        origin_y = padding + row * (tile_h + padding)
        for y in range(height):
            for x in range(width):
                sheet[(origin_y + y) * sheet_w + origin_x + x] = pixels[y * width + x]

    with CONTACT_PPM.open("wb") as handle:
        handle.write(f"P6\n{sheet_w} {sheet_h}\n255\n".encode("ascii"))
        for r, g, b in sheet:
            handle.write(bytes((r, g, b)))

    result = run(["sips", "-s", "format", "jpeg", str(CONTACT_PPM), "--out", str(CONTACT_JPG)])
    if result.returncode != 0:
        (ARTIFACTS / "contact_sheet_convert.log").write_text(result.stderr, encoding="utf-8")


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    sample_paths = sorted(REMOTE_CAPTURE.glob("*.jpg"))
    if not sample_paths:
        raise SystemExit(f"no jpg samples found under {REMOTE_CAPTURE}")
    if not shutil.which("sips"):
        raise SystemExit("sips is required on macOS for this sprint-local analysis")

    rows: list[dict[str, object]] = []
    thumbnails: list[tuple[str, int, int, list[tuple[int, int, int]]]] = []
    with tempfile.TemporaryDirectory(prefix="rober_camera_visibility_") as tmp:
        tmpdir = Path(tmp)
        for image_path in sample_paths:
            bmp_path = decode_with_sips(image_path, tmpdir)
            width, height, pixels = read_bmp_pixels(bmp_path)
            rows.append(analyze_pixels(image_path.stem, width, height, pixels))
            thumb_w, thumb_h, thumb_pixels = downsample(width, height, pixels)
            thumbnails.append((image_path.stem, thumb_w, thumb_h, thumb_pixels))

    rows.sort(key=lambda item: float(item["mean_luma"]), reverse=True)
    best = rows[0]
    visible_content_proven = any(bool(row["visible_content_candidate"]) for row in rows)
    summary = {
        "schema": "trashbot.camera_visibility_diagnostic.v1",
        "sprint": SPRINT,
        "source_files": {
            "vendor_index": "docs/vendor/VENDOR_INDEX.md",
            "ssh_host_info": str((ARTIFACTS / "ssh_host_info.log").relative_to(ROOT)),
            "v4l2_enumeration": str((ARTIFACTS / "v4l2_enumeration.log").relative_to(ROOT)),
            "remote_capture_session": str((ARTIFACTS / "remote_capture_session.log").relative_to(ROOT)),
            "remote_control_restore": str((ARTIFACTS / "remote_control_restore.log").relative_to(ROOT)),
        },
        "device_enumeration": {
            "video_nodes_seen": ["/dev/video0", "/dev/video1", "/dev/video2"],
            "camera_device": "/dev/video1",
            "camera_card": "USB Composite Device: DV20 USB",
            "camera_driver": "uvcvideo",
            "non_camera_nodes": {
                "/dev/video0": "cedrus video decoder, not camera capture",
                "/dev/video2": "UVC metadata capture node",
            },
            "formats_observed": ["MJPG 1280x720/640x480/480x320/1920x1080 @30fps", "YUYV 640x480 @22fps, 320x240 @25/20fps"],
            "controls_observed": ["brightness", "contrast", "saturation", "gamma", "gain", "backlight_compensation", "auto_exposure", "exposure_time_absolute"],
        },
        "motion_commands_sent": False,
        "safe_to_control": False,
        "delivery_success": False,
        "sample_count": len(rows),
        "best_sample": best,
        "best_sample_mean_luma": best["mean_luma"],
        "best_sample_non_black_ratio": best["non_black_ratio"],
        "best_sample_mostly_dark": best["mostly_dark"],
        "visible_content_proven": visible_content_proven,
        "samples": rows,
        "claim_boundary": "采样帧均可从 UVC 设备成功获得；亮度指标若仍 mostly_dark，则不能宣称摄像头已提供可用环境视觉内容。",
        "next_steps_if_dark": ["确认镜头盖/遮挡", "打开现场照明或对准高亮目标", "确认 ROS camera 使用 /dev/video1 而非 metadata/decoder 节点", "复核曝光/增益控制是否被驱动或上层节点覆盖", "需要时采集一段视频而非单帧排除启动瞬态"],
        "outputs": {
            "summary_json": str(SUMMARY_JSON.relative_to(ROOT)),
            "summary_csv": str(SUMMARY_CSV.relative_to(ROOT)),
            "contact_sheet_ppm": str(CONTACT_PPM.relative_to(ROOT)),
            "contact_sheet_jpg": str(CONTACT_JPG.relative_to(ROOT)),
        },
    }

    fieldnames = [
        "sample_name",
        "file",
        "width",
        "height",
        "mean_luma",
        "min_luma",
        "max_luma",
        "dynamic_range_luma",
        "stddev_luma",
        "non_black_ratio",
        "bright_ratio",
        "has_texture_candidate",
        "mostly_dark",
        "visible_content_candidate",
    ]
    with SUMMARY_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in fieldnames})

    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_contact_sheet(thumbnails)
    print(json.dumps({
        "sample_count": len(rows),
        "best_sample_mean_luma": best["mean_luma"],
        "best_sample_non_black_ratio": best["non_black_ratio"],
        "best_sample_mostly_dark": best["mostly_dark"],
        "visible_content_proven": visible_content_proven,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
