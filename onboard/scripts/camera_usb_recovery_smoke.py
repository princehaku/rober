#!/usr/bin/env python3
"""相机 USB 恢复与首帧 smoke。

这个脚本面向真实上位机现场使用：换 USB 口/线后，快速确认 DV20 UVC
是否已经能 STREAMON 出帧。它不触碰底盘 UART，也不发布 /cmd_vel。
"""

from __future__ import annotations

import argparse
import json
import os
import re
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


def wait_service_inactive(service: str, timeout_s: float = 4.0) -> dict[str, Any]:
    """等待 systemd 服务真正停下；只看 stop 返回码会漏掉 `Job canceled`。"""
    started = time.time()
    samples: list[dict[str, Any]] = []
    while time.time() - started < timeout_s:
        state = run_command(["systemctl", "is-active", service], timeout_s=2)
        active_state = str(state.get("stdout") or state.get("stderr") or "").strip()
        samples.append({"elapsed_s": round(time.time() - started, 3), "state": active_state, "returncode": state.get("returncode")})
        if active_state in {"inactive", "failed", "unknown"} or state.get("returncode") not in {0, None}:
            return {"inactive": active_state != "active", "samples": samples}
        time.sleep(0.2)
    return {"inactive": False, "samples": samples, "timeout_s": timeout_s}


def service_main_pid(service: str) -> int | None:
    """读取 systemd MainPID；恢复脚本只允许处理目标相机服务自己的主进程。"""
    result = run_command(["systemctl", "show", service, "-p", "MainPID", "--value"], timeout_s=3)
    try:
        pid = int(str(result.get("stdout") or "").strip())
    except ValueError:
        return None
    return pid if pid > 1 else None


def stop_camera_service(service: str) -> dict[str, Any]:
    """停掉相机服务并处理 stop 被取消的现场漂移，确保后续 STREAMON 不被本服务占用。"""
    summary: dict[str, Any] = {
        "service": service,
        "stop": run_command(["systemctl", "stop", service], timeout_s=8),
    }
    summary["wait_after_stop"] = wait_service_inactive(service)
    if summary["wait_after_stop"].get("inactive"):
        summary["stopped"] = True
        return summary

    pid = service_main_pid(service)
    summary["main_pid_after_stop"] = pid
    if pid is None:
        summary["stopped"] = False
        summary["reason"] = "service_still_active_without_main_pid"
        return summary

    # 只杀 systemd 报告的 MainPID；不会扫描或误杀其它 camera/ROS/底盘进程。
    summary["kill_main_pid"] = run_command(["kill", str(pid)], timeout_s=3)
    time.sleep(0.5)
    summary["stop_after_kill"] = run_command(["systemctl", "stop", service], timeout_s=8)
    summary["wait_after_kill"] = wait_service_inactive(service)
    summary["stopped"] = bool(summary["wait_after_kill"].get("inactive"))
    return summary


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


def read_uvc_module_parameters(parameters_root: Path = Path("/sys/module/uvcvideo/parameters")) -> dict[str, str]:
    """记录 UVC 模块参数；现场恢复结果必须能解释是否受 quirk 污染。"""
    values: dict[str, str] = {}
    for name in ("quirks", "nodrop", "timeout"):
        value = read_sysfs(parameters_root / name)
        values[name] = value if value not in {None, ""} else "not_loaded"
    return values


def reset_uvc_quirks(parameters_root: Path = Path("/sys/module/uvcvideo/parameters")) -> dict[str, Any]:
    """把 uvcvideo quirks 复位到 0；配合 reauthorize 才能让新探测按干净参数绑定。"""
    quirks_path = parameters_root / "quirks"
    before = read_sysfs(quirks_path)
    action = write_sysfs(quirks_path, "0")
    after = read_sysfs(quirks_path)
    return {
        "parameter": str(quirks_path),
        "before": before if before not in {None, ""} else "not_loaded",
        "after": after if after not in {None, ""} else "not_loaded",
        "reset_to": "0",
        "ok": bool(action.get("ok")) and after == "0",
        "write": action,
    }


def sysfs_usb_device_for_video(
    video_device: str,
    *,
    sys_video_root: Path = Path("/sys/class/video4linux"),
    sys_usb_root: Path = Path("/sys/bus/usb/devices"),
) -> str | None:
    """从 videoX 的 sysfs 真实路径反查 `6-1`，避免把平台地址误当 USB 设备。"""
    video_name = Path(video_device).name
    device_link = sys_video_root / video_name / "device"
    try:
        resolved = device_link.resolve(strict=True)
    except OSError:
        return None
    for part in reversed(resolved.parts):
        # video interface 常见形态是 `6-1:1.0`；authorized/power/control 在父设备 `6-1` 上。
        interface_match = re.fullmatch(r"(\d+-[\d.]+):\d+\.\d+", part)
        if interface_match and (sys_usb_root / interface_match.group(1)).exists():
            return interface_match.group(1)
        # 某些内核路径会直接包含 `6-1` 这层设备目录，也要接受。
        if re.fullmatch(r"\d+-[\d.]+", part) and (sys_usb_root / part).exists():
            return part
    return None


def detect_usb_device(
    video_device: str,
    fallback: str,
    *,
    sys_video_root: Path = Path("/sys/class/video4linux"),
    sys_usb_root: Path = Path("/sys/bus/usb/devices"),
) -> str:
    """优先从 sysfs 找真实 USB kernel 地址；v4l2 bus_info 只作为兜底。"""
    sysfs_device = sysfs_usb_device_for_video(
        video_device,
        sys_video_root=sys_video_root,
        sys_usb_root=sys_usb_root,
    )
    if sysfs_device:
        return sysfs_device
    result = run_command(["v4l2-ctl", "-d", video_device, "--all"], timeout_s=5)
    text = result.get("stdout", "") + result.get("stderr", "")
    for line in text.splitlines():
        if "Bus info" in line and "usb-" in line:
            candidate = line.split("usb-", 1)[1].strip()
            # Orange Pi 的 v4l2 bus_info 会出现 `5310400.usb-1` 这种平台控制器地址；
            # 它不是 `/sys/bus/usb/devices/*` 下可写 authorized 的 kernel 地址，不能直接用。
            if re.fullmatch(r"\d+-[\d.]+", candidate) and (sys_usb_root / candidate).exists():
                return candidate
    return fallback


def set_usb_power_on(
    usb_device: str,
    *,
    sys_usb_root: Path = Path("/sys/bus/usb/devices"),
) -> list[dict[str, Any]]:
    """关闭目标设备和所在 root hub 的 autosuspend，排除省电导致的假失败。"""
    actions: list[dict[str, Any]] = []
    device_path = sys_usb_root / usb_device
    root_bus = "usb" + usb_device.split("-", 1)[0]
    # control=on 只禁止 runtime suspend；delay 也写成 -1，避免内核后续自动恢复到短延迟。
    for base_path in (device_path, sys_usb_root / root_bus):
        for filename, value in (
            ("power/control", "on"),
            ("power/autosuspend", "-1"),
            ("power/autosuspend_delay_ms", "-1"),
        ):
            target = base_path / filename
            before = read_sysfs(target)
            action = write_sysfs(target, value)
            action["setting"] = filename
            action["target"] = str(base_path)
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


def unbind_audio_interfaces(
    usb_device: str,
    *,
    sys_usb_root: Path = Path("/sys/bus/usb/devices"),
    driver_unbind: Path = Path("/sys/bus/usb/drivers/snd-usb-audio/unbind"),
) -> list[dict[str, Any]]:
    """解绑同一复合设备上的 USB audio，避免 full-speed 总线再被音频接口干扰。"""
    actions: list[dict[str, Any]] = []
    for iface in sorted(sys_usb_root.glob(f"{usb_device}:1.*")):
        driver_link = iface / "driver"
        try:
            driver = os.path.realpath(driver_link)
        except OSError:
            driver = ""
        if not driver.endswith("/snd-usb-audio"):
            continue
        actions.append(write_sysfs(driver_unbind, iface.name))
    return actions


def rebind_audio_interfaces(
    unbind_actions: list[dict[str, Any]],
    *,
    driver_bind: Path = Path("/sys/bus/usb/drivers/snd-usb-audio/bind"),
) -> list[dict[str, Any]]:
    """把脚本本次解绑过的 USB audio 接口恢复绑定，避免诊断结束后留下状态漂移。"""
    actions: list[dict[str, Any]] = []
    seen: set[str] = set()
    for unbind_action in unbind_actions:
        iface = str(unbind_action.get("value") or "")
        if not iface or iface in seen or not unbind_action.get("ok"):
            continue
        seen.add(iface)
        action = write_sysfs(driver_bind, iface)
        action["value"] = iface
        action["restores_unbind_action"] = iface
        actions.append(action)
    return actions


def audio_interface_driver_status(
    interface_names: set[str],
    *,
    sys_usb_root: Path = Path("/sys/bus/usb/devices"),
) -> dict[str, dict[str, Any]]:
    """按最终 driver 链接判断 audio 是否恢复；sysfs bind 返回码有时比最终状态更保守。"""
    status: dict[str, dict[str, Any]] = {}
    for iface in sorted(interface_names):
        driver_link = sys_usb_root / iface / "driver"
        try:
            driver = os.path.realpath(driver_link)
        except OSError:
            driver = ""
        status[iface] = {
            "driver": driver,
            "bound_to_snd_usb_audio": driver.endswith("/snd-usb-audio"),
        }
    return status


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
            "--stream-poll",
            "--verbose",
            f"--stream-to={output}",
        ],
        timeout_s=10,
    )
    size = output.stat().st_size if output.exists() else 0
    combined = f"{result.get('stdout', '')}\n{result.get('stderr', '')}"
    # STREAMON 成功但 select timeout 说明内核已进入采集态，只是设备没有交出视频 buffer。
    # 这个状态和真正 STREAMON 失败的修复方向不同，必须单独上报给 PC 端。
    lower_combined = combined.lower()
    streamon_observed = "vidioc_streamon" in lower_combined
    streamon_success = "vidioc_streamon returned 0" in lower_combined
    streamon_error = (
        ("vidioc_streamon" in lower_combined and not streamon_success)
        or "input/output error" in lower_combined
    )
    select_timeout = "select timeout" in lower_combined
    command_timeout = bool(result.get("timed_out"))
    zero_byte_no_frame = size == 0 and not streamon_error and (streamon_success or select_timeout or command_timeout)
    frame_observed = size > 0 and not streamon_error
    status = (
        "frame_observed"
        if frame_observed
        else "streamon_success_zero_byte_no_frame"
        if zero_byte_no_frame
        else "streamon_failed"
    )
    return {
        "format": f"{pixelformat}@{width}x{height}@{fps}",
        "output": str(output),
        "bytes": size,
        "status": status,
        "streamon_observed": streamon_observed,
        "streamon_success": streamon_success,
        "streamon_error": streamon_error,
        "select_timeout": select_timeout,
        "command_timeout": command_timeout,
        "zero_byte_no_frame": zero_byte_no_frame,
        "ok": frame_observed,
        "command": result,
    }


def usb_video_speed_from_topology(topology_text: str, usb_device: str) -> str:
    """从 `lsusb -t` 里读取目标 UVC Video 接口速率，避免 480M 时仍提示换高速口。"""
    current_bus = ""
    for raw_line in topology_text.splitlines():
        bus_match = re.search(r"Bus\s+(\d+)", raw_line)
        if raw_line.startswith("/:") and bus_match:
            current_bus = bus_match.group(1).lstrip("0") or "0"
        if "Class=Video" not in raw_line:
            continue
        port_match = re.search(r"Port\s+(\d+):", raw_line)
        speed_match = re.search(r",\s*([0-9]+[MGK])\s*$", raw_line.strip())
        kernel_address = f"{current_bus}-{port_match.group(1)}" if current_bus and port_match else ""
        if kernel_address == usb_device:
            return speed_match.group(1) if speed_match else "unknown"
    return "not_loaded"


def camera_recovery_next_action(frame_observed: bool, usb_video_speed: str) -> dict[str, Any]:
    """把恢复脚本结论压成现场动作；高速口仍无帧时要转向线缆/供电/摄像头本体。"""
    high_speed = usb_video_speed not in {"", "not_loaded", "unknown", "1.5M", "12M"}
    full_speed = usb_video_speed in {"1.5M", "12M"}
    if frame_observed:
        return {
            "next_action": "camera_preview_ready_to_restart",
            "next_action_plain": "相机已读到首帧，重启共享预览后从 PC 打开实时画面。",
            "stream_failure_class": "none",
            "usb_high_speed_observed": high_speed,
            "software_capture_exhausted": False,
            "known_good_uvc_required": False,
            "camera_input_signal_check_required": False,
        }
    if full_speed:
        return {
            "next_action": "move_camera_to_high_speed_usb_port_or_powered_hub",
            "next_action_plain": "摄像头仍在 USB 12M/full-speed，先换高速 USB 口/线或带供电 Hub 后复测。",
            "stream_failure_class": "full_speed_no_frame",
            "usb_high_speed_observed": False,
            "software_capture_exhausted": False,
            "known_good_uvc_required": False,
            "camera_input_signal_check_required": False,
        }
    if high_speed:
        return {
            "next_action": "check_usb_cable_port_power_or_known_good_uvc",
            "next_action_plain": "摄像头已在高速 USB 上，STREAMON 成功但没有任何视频 buffer；优先检查摄像头输入信号、USB 线/供电/接口，或换 known-good UVC 复测。",
            "stream_failure_class": "high_speed_zero_byte_no_frame",
            "usb_high_speed_observed": True,
            "software_capture_exhausted": True,
            "known_good_uvc_required": True,
            "camera_input_signal_check_required": True,
        }
    return {
        "next_action": "check_camera_usb_enumeration",
        "next_action_plain": "未能确认目标 UVC 的 USB 速率；先检查摄像头枚举、线缆和接口后复测。",
        "stream_failure_class": "speed_unknown_no_frame",
        "usb_high_speed_observed": False,
        "software_capture_exhausted": False,
        "known_good_uvc_required": False,
        "camera_input_signal_check_required": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Recover and smoke-test a USB UVC camera on the upper computer.")
    parser.add_argument("--device", default="/dev/video1", help="Video capture device, default /dev/video1.")
    parser.add_argument("--usb-device", default="auto", help="USB kernel address such as 6-1, or auto.")
    parser.add_argument("--service", default="trashbot-local-webrtc-camera.service", help="Camera service to restart.")
    parser.add_argument("--skip-service", action="store_true", help="Do not stop/start the camera service.")
    parser.add_argument("--skip-reauthorize", action="store_true", help="Do not toggle USB authorized.")
    parser.add_argument("--skip-audio-unbind", action="store_true", help="Do not unbind snd-usb-audio interfaces.")
    parser.add_argument("--skip-uvc-quirks-reset", action="store_true", help="Do not reset uvcvideo quirks to 0 before reauthorize.")
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
        summary["service_stop"] = stop_camera_service(args.service)

    summary["owners_before_stream"] = run_command(["lsof", args.device], timeout_s=4)
    summary["power_actions"] = set_usb_power_on(usb_device)
    summary["uvc_module_parameters_before"] = read_uvc_module_parameters()
    summary["uvc_quirks_before"] = summary["uvc_module_parameters_before"].get("quirks", "not_loaded")
    if args.skip_uvc_quirks_reset:
        summary["uvc_quirks_reset"] = {"skipped": True, "reason": "skip_uvc_quirks_reset"}
    else:
        summary["uvc_quirks_reset"] = reset_uvc_quirks()
        summary["uvc_module_parameters_after_quirks_reset"] = read_uvc_module_parameters()
    summary["uvc_quirks_after_reset"] = read_uvc_module_parameters().get("quirks", "not_loaded")
    if not args.skip_reauthorize:
        summary["reauthorize_actions"] = reauthorize_usb(usb_device)
        summary["power_actions_after_reauthorize"] = set_usb_power_on(usb_device)
        summary["uvc_module_parameters_after_reauthorize"] = read_uvc_module_parameters()
    if not args.skip_audio_unbind:
        summary["audio_unbind_actions"] = unbind_audio_interfaces(usb_device)
    else:
        summary["audio_unbind_actions"] = []

    summary["topology"] = run_command(["lsusb", "-t"], timeout_s=5)
    summary["usb_video_speed"] = usb_video_speed_from_topology(str(summary["topology"].get("stdout") or ""), usb_device)
    summary["formats"] = run_command(["v4l2-ctl", "-d", args.device, "--list-formats-ext"], timeout_s=5)
    summary["streams"] = [
        stream_once(args.device, 320, 240, "YUYV", 20, Path("/tmp/rober_camera_usb_recovery_yuyv.raw")),
        stream_once(args.device, 480, 320, "MJPG", 30, Path("/tmp/rober_camera_usb_recovery_mjpg.raw")),
    ]
    summary["uvc_module_parameters_after_stream"] = read_uvc_module_parameters()
    summary["uvc_quirks_after"] = summary["uvc_module_parameters_after_stream"].get("quirks", "not_loaded")
    summary["frame_observed"] = any(item["ok"] for item in summary["streams"])
    summary["streamon_success_observed"] = any(item.get("streamon_success") for item in summary["streams"])
    summary["select_timeout_observed"] = any(item.get("select_timeout") for item in summary["streams"])
    summary["zero_byte_no_frame_observed"] = any(item.get("zero_byte_no_frame") for item in summary["streams"])
    summary["stream_status_summary"] = ";".join(f"{item['format']}={item.get('status')}" for item in summary["streams"])
    summary["status"] = (
        "frame_observed"
        if summary["frame_observed"]
        else "streamon_success_zero_byte_no_frame"
        if summary["streamon_success_observed"] and summary["zero_byte_no_frame_observed"]
        else "streamon_failed"
    )
    summary.update(camera_recovery_next_action(bool(summary["frame_observed"]), str(summary["usb_video_speed"])))
    if args.skip_audio_unbind:
        summary["audio_rebind_actions"] = []
        summary["audio_rebind_ok"] = True
        summary["audio_rebind_skipped_reason"] = "skip_audio_unbind"
    else:
        summary["audio_rebind_actions"] = rebind_audio_interfaces(summary["audio_unbind_actions"])
        audio_unbound_ok_ifaces = {
            str(action.get("value") or "")
            for action in summary["audio_unbind_actions"]
            if action.get("ok") and action.get("value")
        }
        audio_rebound_ok_ifaces = {
            str(action.get("value") or "")
            for action in summary["audio_rebind_actions"]
            if action.get("ok") and action.get("value")
        }
        time.sleep(0.2)
        summary["audio_unbound_ok_ifaces"] = sorted(audio_unbound_ok_ifaces)
        summary["audio_rebound_write_ok_ifaces"] = sorted(audio_rebound_ok_ifaces)
        summary["audio_bind_status_after_rebind"] = audio_interface_driver_status(audio_unbound_ok_ifaces)
        summary["audio_rebind_ok"] = all(
            item.get("bound_to_snd_usb_audio")
            for item in summary["audio_bind_status_after_rebind"].values()
        )
        if not audio_unbound_ok_ifaces:
            summary["audio_rebind_ok"] = True
            summary["audio_rebind_skipped_reason"] = "no_audio_interfaces_unbound"
        summary["topology_after_audio_rebind"] = run_command(["lsusb", "-t"], timeout_s=5)

    if not args.skip_service:
        summary["service_start"] = run_command(["systemctl", "start", args.service], timeout_s=8)

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["frame_observed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
