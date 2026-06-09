#!/usr/bin/env python3
"""采集 /dev/video1 的 OpenCV 样本并输出亮度/纹理指标。"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np


CONTROL_NAMES = [
    "brightness",
    "contrast",
    "saturation",
    "gamma",
    "gain",
    "backlight_compensation",
    "auto_exposure",
    "exposure_time_absolute",
]


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    """统一封装命令执行，便于把失败 stderr 原样写入证据文件。"""
    return subprocess.run(command, text=True, capture_output=True, check=False)


def read_control(device: str, name: str) -> int | None:
    """读取单个 V4L2 控制项；不存在时返回 None，不把缺项误判成失败。"""
    result = run(["v4l2-ctl", "-d", device, "-C", name])
    match = re.search(rf"{re.escape(name)}:\s*(-?\d+)", result.stdout)
    if result.returncode != 0 or not match:
        return None
    return int(match.group(1))


def write_control(device: str, name: str, value: int) -> bool:
    """临时写控制项用于保守 sweep；结束必须由 restore_controls 恢复。"""
    result = run(["v4l2-ctl", "-d", device, "-c", f"{name}={value}"])
    return result.returncode == 0


def parse_control_ranges(text: str) -> dict[str, dict[str, int]]:
    """从 list-ctrls 文本提取 min/max/default，避免硬编码某个摄像头的范围。"""
    ranges: dict[str, dict[str, int]] = {}
    for line in text.splitlines():
        name_match = re.match(r"\s*([A-Za-z0-9_]+)\s+0x[0-9a-fA-F]+", line)
        if not name_match:
            continue
        name = name_match.group(1)
        values: dict[str, int] = {}
        for key in ("min", "max", "default", "value"):
            value_match = re.search(rf"{key}=(-?\d+)", line)
            if value_match:
                values[key] = int(value_match.group(1))
        if values:
            ranges[name] = values
    return ranges


def snapshot_controls(device: str) -> dict[str, int | None]:
    """记录关键控制项原值，保证 sweep 后能复原现场状态。"""
    return {name: read_control(device, name) for name in CONTROL_NAMES}


def restore_controls(device: str, original: dict[str, int | None]) -> dict[str, object]:
    """按原值恢复可读控制项，并返回恢复后的实际读数。"""
    restored: dict[str, object] = {"writes": {}, "after": {}}
    for name, value in original.items():
        if value is None:
            continue
        restored["writes"][name] = write_control(device, name, value)
    time.sleep(0.2)
    restored["after"] = snapshot_controls(device)
    return restored


def luma_metrics(frame: np.ndarray) -> dict[str, object]:
    """计算亮度、动态范围、非黑比例和边缘指标，用于区分黑场与可见纹理。"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    luma = gray.astype(np.float32)
    mean_luma = float(np.mean(luma))
    min_luma = float(np.min(luma))
    max_luma = float(np.max(luma))
    dynamic_range = max_luma - min_luma
    non_black_ratio = float(np.count_nonzero(luma > 10.0) / luma.size)
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    edges = cv2.Canny(gray, 50, 150)
    edge_count = int(np.count_nonzero(edges))
    edge_ratio = float(edge_count / luma.size)
    # 可见内容必须同时满足亮度、非黑和纹理条件；均匀白/灰不算路线可用内容。
    visible_content_candidate = (
        mean_luma >= 35.0
        and non_black_ratio >= 0.10
        and (dynamic_range >= 15.0 or laplacian_var >= 5.0 or edge_ratio >= 0.002)
    )
    return {
        "mean_luma": round(mean_luma, 6),
        "min_luma": round(min_luma, 6),
        "max_luma": round(max_luma, 6),
        "dynamic_range_luma": round(dynamic_range, 6),
        "non_black_ratio": round(non_black_ratio, 9),
        "laplacian_var": round(laplacian_var, 6),
        "edge_count": edge_count,
        "edge_ratio": round(edge_ratio, 9),
        "visible_content_candidate": visible_content_candidate,
    }


def capture_sample(device: str, output_dir: Path, label: str, width: int, height: int, fourcc_name: str) -> dict[str, object]:
    """打开设备、设置格式和分辨率、丢弃启动帧后保存一张样本。"""
    capture = cv2.VideoCapture(device, cv2.CAP_V4L2)
    opened = bool(capture.isOpened())
    metrics: dict[str, object] = {
        "sample_name": label,
        "device": device,
        "requested_width": width,
        "requested_height": height,
        "requested_fourcc": fourcc_name,
        "opened": opened,
        "read_ok": False,
    }
    if not opened:
        return metrics

    if fourcc_name:
        capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*fourcc_name))
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, float(width))
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, float(height))
    capture.set(cv2.CAP_PROP_FPS, 10.0)

    frame = None
    ok = False
    # 先读几帧，降低启动瞬态导致的黑场误判概率。
    for _ in range(8):
        ok, frame = capture.read()
        if ok and frame is not None:
            time.sleep(0.05)
    actual_fourcc = int(capture.get(cv2.CAP_PROP_FOURCC))
    actual_fourcc_text = "".join(chr((actual_fourcc >> 8 * idx) & 0xFF) for idx in range(4))
    actual_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    capture.release()

    metrics.update(
        {
            "read_ok": bool(ok and frame is not None),
            "actual_width": actual_width,
            "actual_height": actual_height,
            "actual_fourcc": actual_fourcc_text,
        }
    )
    if not ok or frame is None:
        return metrics

    image_path = output_dir / f"{label}.jpg"
    cv2.imwrite(str(image_path), frame)
    metrics.update({"width": int(frame.shape[1]), "height": int(frame.shape[0]), "frame_path": str(image_path)})
    metrics.update(luma_metrics(frame))
    (output_dir / f"{label}.metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return metrics


def choose_boost_values(ranges: dict[str, dict[str, int]]) -> dict[str, int]:
    """生成保守的临时补光控制值，只使用设备自己声明的范围。"""
    boost: dict[str, int] = {}
    for name in ("brightness", "gain"):
        item = ranges.get(name)
        if item and "min" in item and "max" in item:
            boost[name] = int(item["min"] + (item["max"] - item["min"]) * 0.75)
    if "backlight_compensation" in ranges and "max" in ranges["backlight_compensation"]:
        boost["backlight_compensation"] = int(ranges["backlight_compensation"]["max"])
    return boost


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="/dev/video1")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    controls_text = run(["v4l2-ctl", "-d", args.device, "--list-ctrls"]).stdout
    (output_dir / "v4l2_list_ctrls.txt").write_text(controls_text, encoding="utf-8")
    original_controls = snapshot_controls(args.device)
    (output_dir / "controls_before.json").write_text(json.dumps(original_controls, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    samples: list[dict[str, object]] = []
    for width, height in ((640, 480), (320, 240)):
        for fourcc_name in ("MJPG", "YUYV"):
            label = f"default_{fourcc_name.lower()}_{width}x{height}"
            samples.append(capture_sample(args.device, output_dir, label, width, height, fourcc_name))

    # 如果默认矩阵仍无可见纹理，做一次可恢复的保守亮度/增益 sweep。
    visible_default = any(bool(item.get("visible_content_candidate")) for item in samples)
    sweep: dict[str, object] = {"performed": False, "writes": {}, "restore": {}}
    if not visible_default:
        ranges = parse_control_ranges(controls_text)
        boost_values = choose_boost_values(ranges)
        sweep["performed"] = bool(boost_values)
        for name, value in boost_values.items():
            sweep["writes"][name] = {"target": value, "ok": write_control(args.device, name, value)}
        time.sleep(0.8)
        samples.append(capture_sample(args.device, output_dir, "boosted_mjpg_640x480", 640, 480, "MJPG"))

    sweep["restore"] = restore_controls(args.device, original_controls)
    (output_dir / "controls_after_restore.json").write_text(json.dumps(sweep["restore"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary = {
        "schema": "trashbot.camera_opencv_visibility_probe.v1",
        "device": args.device,
        "camera_device_opened": any(bool(item.get("opened")) for item in samples),
        "opencv_read_ok": any(bool(item.get("read_ok")) for item in samples),
        "visible_content_proven": any(bool(item.get("visible_content_candidate")) for item in samples),
        "samples": samples,
        "control_sweep": sweep,
        "motion_commands_sent": False,
    }
    (output_dir / "opencv_visibility_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
