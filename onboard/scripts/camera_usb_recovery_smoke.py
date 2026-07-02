#!/usr/bin/env python3
"""相机 USB 恢复与首帧 smoke。

这个脚本面向真实上位机现场使用：换 USB 口/线后，快速确认 DV20 UVC
是否已经能 STREAMON 出帧。它不触碰底盘 UART，也不发布 /cmd_vel。
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any


def run_command(argv: list[str], timeout_s: float = 8.0) -> dict[str, Any]:
    """统一捕获命令结果；现场 smoke 不能因为单步失败丢掉后续证据。"""
    started = time.time()
    try:
        completed = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        return {
            "argv": argv,
            "returncode": completed.returncode,
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
            "elapsed_s": round(time.time() - started, 3),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": argv,
            "returncode": None,
            "stdout": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
            "elapsed_s": round(time.time() - started, 3),
            "timed_out": True,
        }


def write_sysfs(path: Path, value: str) -> dict[str, Any]:
    """写 sysfs 前先记录路径存在性；权限不足时给出可读错误。"""
    if not path.exists():
        return {"path": str(path), "ok": False, "reason": "missing"}
    try:
        path.write_text(value, encoding="utf-8")
        return {"path": str(path), "ok": True, "value": value}
    except OSError as exc:
        return {"path": str(path), "ok": False, "reason": str(exc)}


def read_sysfs(path: Path) -> str | None:
    """读取 USB 电源策略时允许文件缺失，兼容不同内核导出。"""
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def detect_usb_device(video_device: str, fallback: str) -> str:
    """从 v4l2 bus_info 里提取 usb-x-y；失败时使用现场默认值。"""
    result = run_command(["v4l2-ctl", "-d", video_device, "--all"], timeout_s=5)
    text = result.get("stdout", "") + result.get("stderr", "")
    for line in text.splitlines():
        if "Bus info" in line and "usb-" in line:
            return line.split("usb-", 1)[1].strip()
    return fallback


def set_usb_power_on(usb_device: str) -> list[dict[str, Any]]:
    """关闭目标设备和所在 root hub 的 autosuspend，排除省电导致的假失败。"""
    actions: list[dict[str, Any]] = []
    device_path = Path("/sys/bus/usb/devices") / usb_device
    root_bus = "usb" + usb_device.split("-", 1)[0]
    for target in (device_path / "power/control", Path("/sys/bus/usb/devices") / root_bus / "power/control"):
        before = read_sysfs(target)
        action = write_sysfs(target, "on")
        action["before"] = before
        action["after"] = read_sysfs(target)
        actions.append(action)
    return actions


def reauthorize_usb(usb_device: str) -> list[dict[str, Any]]:
    """模拟重新插拔目标 USB 设备；这一步只作用于相机所在 USB 设备。"""
    authorized = Path("/sys/bus/usb/devices") / usb_device / "authorized"
    actions = [write_sysfs(authorized, "0")]
    time.sleep(1.0)
    actions.append(write_sysfs(authorized, "1"))
    time.sleep(2.0)
    return actions


def unbind_audio_interfaces(usb_device: str) -> list[dict[str, Any]]:
    """解绑同一复合设备上的 USB audio，避免 full-speed 总线再被音频接口干扰。"""
    actions: list[dict[str, Any]] = []
    driver_unbind = Path("/sys/bus/usb/drivers/snd-usb-audio/unbind")
    for iface in sorted(Path("/sys/bus/usb/devices").glob(f"{usb_device}:1.*")):
        driver_link = iface / "driver"
        try:
            driver = os.path.realpath(driver_link)
        except OSError:
            driver = ""
        if not driver.endswith("/snd-usb-audio"):
            continue
        actions.append(write_sysfs(driver_unbind, iface.name))
    return actions


def stream_once(device: str, width: int, height: int, pixelformat: str, fps: int, output: Path) -> dict[str, Any]:
    """使用 v4l2-ctl 直接 STREAMON；文件大于 0 才算真的出帧。"""
    try:
        output.unlink()
    except FileNotFoundError:
        pass
    result = run_command(
        [
            "v4l2-ctl",
            "-d",
            device,
            f"--set-fmt-video=width={width},height={height},pixelformat={pixelformat}",
            f"--set-parm={fps}",
            "--stream-mmap=3",
            "--stream-count=5",
            f"--stream-to={output}",
        ],
        timeout_s=10,
    )
    size = output.stat().st_size if output.exists() else 0
    combined = f"{result.get('stdout', '')}\n{result.get('stderr', '')}"
    return {
        "format": f"{pixelformat}@{width}x{height}@{fps}",
        "output": str(output),
        "bytes": size,
        "streamon_error": "VIDIOC_STREAMON" in combined or "Input/output error" in combined,
        "ok": size > 0 and "VIDIOC_STREAMON" not in combined,
        "command": result,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Recover and smoke-test a USB UVC camera on the upper computer.")
    parser.add_argument("--device", default="/dev/video1", help="Video capture device, default /dev/video1.")
    parser.add_argument("--usb-device", default="auto", help="USB kernel address such as 6-1, or auto.")
    parser.add_argument("--service", default="trashbot-local-webrtc-camera.service", help="Camera service to restart.")
    parser.add_argument("--skip-service", action="store_true", help="Do not stop/start the camera service.")
    parser.add_argument("--skip-reauthorize", action="store_true", help="Do not toggle USB authorized.")
    parser.add_argument("--skip-audio-unbind", action="store_true", help="Do not unbind snd-usb-audio interfaces.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    usb_device = detect_usb_device(args.device, "6-1") if args.usb_device == "auto" else args.usb_device
    summary: dict[str, Any] = {
        "schema": "trashbot.camera_usb_recovery_smoke.v1",
        "device": args.device,
        "usb_device": usb_device,
        "vendor_sources": [
            "docs/vendor/VENDOR_INDEX.md",
            "docs/vendor/orangepizero3/OrangePi_Zero3_H618_用户手册_v1.6.pdf",
            "docs/vendor/orangepizero3/OrangePi-ZERO3_电路图.pdf",
        ],
        "robot_control_executed": False,
        "publishes_cmd_vel": False,
        "opens_base_uart": False,
    }

    # 先停共享预览，确保 STREAMON 失败不是页面或服务独占导致。
    if not args.skip_service:
        summary["service_stop"] = run_command(["systemctl", "stop", args.service], timeout_s=8)

    summary["owners_before_stream"] = run_command(["lsof", args.device], timeout_s=4)
    summary["power_actions"] = set_usb_power_on(usb_device)
    if not args.skip_reauthorize:
        summary["reauthorize_actions"] = reauthorize_usb(usb_device)
        summary["power_actions_after_reauthorize"] = set_usb_power_on(usb_device)
    if not args.skip_audio_unbind:
        summary["audio_unbind_actions"] = unbind_audio_interfaces(usb_device)

    summary["topology"] = run_command(["lsusb", "-t"], timeout_s=5)
    summary["formats"] = run_command(["v4l2-ctl", "-d", args.device, "--list-formats-ext"], timeout_s=5)
    summary["streams"] = [
        stream_once(args.device, 320, 240, "YUYV", 20, Path("/tmp/rober_camera_usb_recovery_yuyv.raw")),
        stream_once(args.device, 480, 320, "MJPG", 30, Path("/tmp/rober_camera_usb_recovery_mjpg.raw")),
    ]
    summary["frame_observed"] = any(item["ok"] for item in summary["streams"])
    summary["status"] = "frame_observed" if summary["frame_observed"] else "streamon_failed"
    summary["next_action"] = (
        "camera_preview_ready_to_restart"
        if summary["frame_observed"]
        else "move_camera_to_high_speed_usb_port_or_powered_hub"
    )

    if not args.skip_service:
        summary["service_start"] = run_command(["systemctl", "start", args.service], timeout_s=8)

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["frame_observed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
