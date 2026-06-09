#!/usr/bin/env python3
"""生成视觉关键帧与路线里程计的 micro sprint 证据包。"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE_SPRINT = REPO_ROOT / "sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf"
SOURCE_ROUTE = SOURCE_SPRINT / "artifacts/route/route.csv"
SOURCE_MANIFEST = SOURCE_SPRINT / "artifacts/route/manifest.json"
SOURCE_KEYFRAMES = SOURCE_SPRINT / "artifacts/route/keyframes"
OUTPUT_DIR = REPO_ROOT / "sprints/2026.06.10_02-40_visual-route-motion-evidence/artifacts"
SUMMARY_JSON = OUTPUT_DIR / "visual_motion_summary.json"
DIFF_CSV = OUTPUT_DIR / "keyframe_diff_summary.csv"
CONTACT_SHEET = OUTPUT_DIR / "keyframe_contact_sheet.jpg"
LOG_FILE = OUTPUT_DIR / "visual_motion_analysis.log"


@dataclass(frozen=True)
class BmpImage:
    width: int
    height: int
    pixels: bytes


def log_line(lines: list[str], message: str) -> None:
    lines.append(message)
    print(message)


def require_sips() -> str:
    sips = shutil.which("sips")
    if not sips:
        raise RuntimeError("macOS sips 未找到，无法在无 Pillow/OpenCV 环境中解码 JPEG。")
    return sips


def convert_jpeg_to_bmp(sips: str, source: Path, target: Path, *, width: int | None = None) -> None:
    cmd = [sips]
    if width is not None:
        # 用固定宽度生成联系图缩略图，避免原图直接拼接导致证据文件过大。
        cmd.extend(["--resampleWidth", str(width)])
    cmd.extend(["-s", "format", "bmp", str(source), "--out", str(target)])
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def read_bmp(path: Path) -> BmpImage:
    data = path.read_bytes()
    if data[:2] != b"BM":
        raise ValueError(f"{path} 不是 BMP 文件")
    offset = int.from_bytes(data[10:14], "little")
    dib_size = int.from_bytes(data[14:18], "little")
    if dib_size < 40:
        raise ValueError(f"{path} 的 DIB header 太短")
    width = int.from_bytes(data[18:22], "little", signed=True)
    height_signed = int.from_bytes(data[22:26], "little", signed=True)
    planes = int.from_bytes(data[26:28], "little")
    bit_count = int.from_bytes(data[28:30], "little")
    compression = int.from_bytes(data[30:34], "little")
    if planes != 1 or compression != 0 or bit_count not in (24, 32):
        raise ValueError(f"{path} 不是未压缩 24/32-bit BMP: bit_count={bit_count}, compression={compression}")

    height = abs(height_signed)
    row_stride = ((abs(width) * bit_count + 31) // 32) * 4
    rows: list[bytes] = []
    for row_index in range(height):
        # BMP 默认自底向上存储；统一转成自顶向下 RGB，后续差分才不受格式影响。
        source_row = height - 1 - row_index if height_signed > 0 else row_index
        start = offset + source_row * row_stride
        row = data[start : start + row_stride]
        rgb = bytearray()
        for col in range(abs(width)):
            base = col * (bit_count // 8)
            b, g, r = row[base], row[base + 1], row[base + 2]
            rgb.extend((r, g, b))
        rows.append(bytes(rgb))
    return BmpImage(width=abs(width), height=height, pixels=b"".join(rows))


def write_bmp(path: Path, image: BmpImage) -> None:
    row_stride = ((image.width * 3 + 3) // 4) * 4
    pixel_size = row_stride * image.height
    file_size = 14 + 40 + pixel_size
    header = bytearray()
    header.extend(b"BM")
    header.extend(file_size.to_bytes(4, "little"))
    header.extend((0).to_bytes(4, "little"))
    header.extend((54).to_bytes(4, "little"))
    header.extend((40).to_bytes(4, "little"))
    header.extend(image.width.to_bytes(4, "little", signed=True))
    header.extend(image.height.to_bytes(4, "little", signed=True))
    header.extend((1).to_bytes(2, "little"))
    header.extend((24).to_bytes(2, "little"))
    header.extend((0).to_bytes(4, "little"))
    header.extend(pixel_size.to_bytes(4, "little"))
    header.extend((72).to_bytes(4, "little"))
    header.extend((72).to_bytes(4, "little"))
    header.extend((0).to_bytes(4, "little"))
    header.extend((0).to_bytes(4, "little"))

    body = bytearray()
    for row_index in range(image.height - 1, -1, -1):
        start = row_index * image.width * 3
        row = image.pixels[start : start + image.width * 3]
        encoded = bytearray()
        for col in range(image.width):
            r, g, b = row[col * 3], row[col * 3 + 1], row[col * 3 + 2]
            encoded.extend((b, g, r))
        encoded.extend(b"\x00" * (row_stride - len(encoded)))
        body.extend(encoded)
    path.write_bytes(bytes(header) + bytes(body))


def image_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def diff_images(left: BmpImage, right: BmpImage) -> dict[str, float | int]:
    if left.width != right.width or left.height != right.height:
        raise ValueError("关键帧尺寸不一致，不能直接逐像素差分")
    total_channels = len(left.pixels)
    abs_sum = 0
    sq_sum = 0
    changed_pixels = 0
    for index in range(0, total_channels, 3):
        dr = abs(left.pixels[index] - right.pixels[index])
        dg = abs(left.pixels[index + 1] - right.pixels[index + 1])
        db = abs(left.pixels[index + 2] - right.pixels[index + 2])
        pixel_mean = (dr + dg + db) / 3.0
        abs_sum += dr + dg + db
        sq_sum += dr * dr + dg * dg + db * db
        if pixel_mean > 2.0:
            # 2.0 阈值用于过滤 JPEG 微小噪声，保留肉眼可复核的画面变化。
            changed_pixels += 1
    pixel_count = left.width * left.height
    return {
        "mean_absdiff": abs_sum / total_channels,
        "rms_diff": math.sqrt(sq_sum / total_channels),
        "changed_pixel_ratio": changed_pixels / pixel_count,
        "pixel_count": pixel_count,
    }


def route_rows() -> list[dict[str, str]]:
    with SOURCE_ROUTE.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def route_metrics(rows: list[dict[str, str]]) -> dict[str, object]:
    poses = [(float(row["x"]), float(row["y"]), float(row["z"])) for row in rows]
    stamps = [float(row["sec"]) + float(row["nanosec"]) / 1_000_000_000 for row in rows]
    segment_distances = []
    for left, right in zip(poses, poses[1:]):
        segment_distances.append(math.dist(left, right))
    positive_segments = [value for value in segment_distances if value > 1e-9]
    x_values = [pose[0] for pose in poses]
    time_gaps = [right - left for left, right in zip(stamps, stamps[1:])]
    active_stamps = stamps[1:] if len(stamps) > 1 else stamps

    return {
        "route_row_count": len(rows),
        "route_frame_id": rows[0].get("frame_id", "") if rows else "",
        "route_total_path_m": sum(segment_distances),
        "route_total_displacement_m": math.dist(poses[0], poses[-1]) if len(poses) >= 2 else 0.0,
        "route_positive_segment_count": len(positive_segments),
        "route_min_step_m": min(segment_distances) if segment_distances else 0.0,
        "route_max_step_m": max(segment_distances) if segment_distances else 0.0,
        "route_median_step_m": sorted(segment_distances)[len(segment_distances) // 2] if segment_distances else 0.0,
        "route_duration_sec": stamps[-1] - stamps[0] if len(stamps) >= 2 else 0.0,
        "route_active_duration_sec": active_stamps[-1] - active_stamps[0] if len(active_stamps) >= 2 else 0.0,
        "route_max_time_gap_sec": max(time_gaps) if time_gaps else 0.0,
        "route_x_monotonic_non_decreasing": all(right >= left for left, right in zip(x_values, x_values[1:])),
        "route_start": {"x": poses[0][0], "y": poses[0][1], "z": poses[0][2]} if poses else {},
        "route_end": {"x": poses[-1][0], "y": poses[-1][1], "z": poses[-1][2]} if poses else {},
    }


def manifest_keyframes() -> list[Path]:
    with SOURCE_MANIFEST.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    paths: list[Path] = []
    for sample in manifest.get("samples", []):
        raw_image = sample.get("raw_image", "")
        if raw_image:
            paths.append(SOURCE_SPRINT / "artifacts/route" / raw_image)
    return paths


def make_contact_sheet(thumbnails: list[BmpImage], output_jpg: Path, sips: str, temp_dir: Path) -> None:
    if not thumbnails:
        return
    columns = 4
    tile_w = thumbnails[0].width
    tile_h = thumbnails[0].height
    rows = math.ceil(len(thumbnails) / columns)
    canvas = bytearray(b"\xff" * (columns * tile_w * rows * tile_h * 3))
    for idx, image in enumerate(thumbnails):
        col = idx % columns
        row = idx // columns
        for y in range(image.height):
            src_start = y * image.width * 3
            dst_start = ((row * tile_h + y) * columns * tile_w + col * tile_w) * 3
            canvas[dst_start : dst_start + image.width * 3] = image.pixels[src_start : src_start + image.width * 3]
    bmp_path = temp_dir / "keyframe_contact_sheet.bmp"
    write_bmp(bmp_path, BmpImage(width=columns * tile_w, height=rows * tile_h, pixels=bytes(canvas)))
    subprocess.run(
        [sips, "-s", "format", "jpeg", str(bmp_path), "--out", str(output_jpg)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    log_lines: list[str] = []
    sips = require_sips()
    log_line(log_lines, f"source_route={SOURCE_ROUTE}")
    log_line(log_lines, f"source_keyframes={SOURCE_KEYFRAMES}")
    log_line(log_lines, f"source_manifest={SOURCE_MANIFEST}")
    log_line(log_lines, f"decoder={sips}")

    rows = route_rows()
    route = route_metrics(rows)
    keyframes = [path for path in manifest_keyframes() if path.exists()]
    if not keyframes:
        keyframes = sorted(SOURCE_KEYFRAMES.glob("*.jpg"))
    keyframe_hashes = {path.name: image_sha256(path) for path in keyframes}

    diff_rows: list[dict[str, object]] = []
    thumbnails: list[BmpImage] = []
    with tempfile.TemporaryDirectory(prefix="visual_motion_") as tmp:
        temp_dir = Path(tmp)
        decoded: list[tuple[Path, BmpImage]] = []
        for path in keyframes:
            bmp_path = temp_dir / f"{path.stem}.bmp"
            convert_jpeg_to_bmp(sips, path, bmp_path)
            decoded.append((path, read_bmp(bmp_path)))

            thumb_path = temp_dir / f"{path.stem}.thumb.bmp"
            convert_jpeg_to_bmp(sips, path, thumb_path, width=160)
            thumbnails.append(read_bmp(thumb_path))

        for (left_path, left), (right_path, right) in zip(decoded, decoded[1:]):
            metrics = diff_images(left, right)
            diff_rows.append(
                {
                    "left_frame": left_path.name,
                    "right_frame": right_path.name,
                    "left_sha256_prefix": keyframe_hashes[left_path.name][:12],
                    "right_sha256_prefix": keyframe_hashes[right_path.name][:12],
                    "sha256_identical": keyframe_hashes[left_path.name] == keyframe_hashes[right_path.name],
                    **metrics,
                }
            )

        make_contact_sheet(thumbnails, CONTACT_SHEET, sips, temp_dir)

    image_size = {
        "width": decoded[0][1].width if decoded else 0,
        "height": decoded[0][1].height if decoded else 0,
    }
    non_identical = sum(1 for row in diff_rows if not row["sha256_identical"])
    visually_changed = sum(1 for row in diff_rows if float(row["mean_absdiff"]) > 1.0)
    summary = {
        "schema": "trashbot.visual_route_motion_evidence.v1",
        "sprint": "2026.06.10_02-40_visual-route-motion-evidence",
        "source_sprint": "sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf",
        "source_files": {
            "route_csv": str(SOURCE_ROUTE.relative_to(REPO_ROOT)),
            "manifest_json": str(SOURCE_MANIFEST.relative_to(REPO_ROOT)),
            "keyframes_dir": str(SOURCE_KEYFRAMES.relative_to(REPO_ROOT)),
            "map_dir": "sprints/2026.06.10_01-15_esp32-bridge-dynamic-odom-tf/artifacts/map",
            "vendor_index": "docs/vendor/VENDOR_INDEX.md",
        },
        "vendor_fact_boundary": {
            "main_sbc": "Orange Pi Zero 3, H618",
            "mobile_base": "Waveshare WAVE ROVER",
            "lower_controller": "ESP32 firmware from Waveshare WAVE ROVER package",
            "upper_lower_link": "UART, newline-delimited UTF-8 JSON",
            "vendor_default_uart": "/dev/ttyAMA0 at 115200 on Raspberry Pi reference; Orange Pi device must be confirmed on robot",
        },
        "keyframe_count": len(keyframes),
        "adjacent_pair_count": len(diff_rows),
        "non_identical_adjacent_pairs": non_identical,
        "visually_changed_adjacent_pairs_mean_absdiff_gt_1": visually_changed,
        "keyframe_image_size": image_size,
        "keyframe_mean_absdiff": {
            "min": min((float(row["mean_absdiff"]) for row in diff_rows), default=0.0),
            "max": max((float(row["mean_absdiff"]) for row in diff_rows), default=0.0),
            "avg": sum(float(row["mean_absdiff"]) for row in diff_rows) / len(diff_rows) if diff_rows else 0.0,
        },
        "keyframe_changed_pixel_ratio": {
            "min": min((float(row["changed_pixel_ratio"]) for row in diff_rows), default=0.0),
            "max": max((float(row["changed_pixel_ratio"]) for row in diff_rows), default=0.0),
            "avg": sum(float(row["changed_pixel_ratio"]) for row in diff_rows) / len(diff_rows) if diff_rows else 0.0,
        },
        **route,
        "boundary_flags": {
            "safe_to_control": False,
            "delivery_success": False,
            "not_proven": True,
        },
        "evidence_claim": (
            "仅证明上一轮真实相机关键帧存在相邻图像变化，且 command-integration route.csv "
            "存在连续 odom 位移；不证明 encoder wheel speed、真实 Nav2 完成或垃圾收集送达闭环完成。"
        ),
        "outputs": {
            "summary_json": str(SUMMARY_JSON.relative_to(REPO_ROOT)),
            "keyframe_diff_summary_csv": str(DIFF_CSV.relative_to(REPO_ROOT)),
            "contact_sheet_jpg": str(CONTACT_SHEET.relative_to(REPO_ROOT)),
            "analysis_log": str(LOG_FILE.relative_to(REPO_ROOT)),
        },
    }

    with DIFF_CSV.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "left_frame",
            "right_frame",
            "left_sha256_prefix",
            "right_sha256_prefix",
            "sha256_identical",
            "mean_absdiff",
            "rms_diff",
            "changed_pixel_ratio",
            "pixel_count",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(diff_rows)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    log_line(log_lines, f"keyframe_count={summary['keyframe_count']}")
    log_line(log_lines, f"non_identical_adjacent_pairs={summary['non_identical_adjacent_pairs']}")
    log_line(log_lines, f"visual_mean_absdiff_avg={summary['keyframe_mean_absdiff']['avg']:.6f}")
    log_line(log_lines, f"route_row_count={summary['route_row_count']}")
    log_line(log_lines, f"route_total_displacement_m={summary['route_total_displacement_m']:.9f}")
    log_line(log_lines, f"route_positive_segment_count={summary['route_positive_segment_count']}")
    log_line(log_lines, "safe_to_control=false delivery_success=false not_proven=true")
    LOG_FILE.write_text("\n".join(log_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
