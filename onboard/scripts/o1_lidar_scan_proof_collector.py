#!/usr/bin/env python3
"""O1 LiDAR `/scan` proof collector：只读采集 readiness/proof/blocker。"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


SCHEMA = "trashbot.o1.lidar_scan_proof.v1"
DEFAULT_UPPER_API_BASE_URL = "http://127.0.0.1:8787"
DEFAULT_OUTPUT_PATH = "runtime/lidar_scan_proof_latest.json"
DEFAULT_TIMEOUT_S = 5.0
ROS_HUMBLE_SETUP = "/opt/ros/humble/setup.bash"
ROBER_INSTALL_SETUP = "/root/rober/onboard/install/setup.bash"
SCAN_TOPIC = "/scan"
RAW_PACKET_TOPIC = "/lidar/raw_packet"

# vendor 来源固定写入 artifact，现场回放时能直接追到资料入口。
VENDOR_SOURCES = (
    "AGENTS.md",
    "OKR.md",
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/lidar_pkg_ros2-main/README.md",
    "docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp",
    "docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml",
    "docs/vendor/lidar_pkg_ros2-main/launch/lidar.launch.py",
    "docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules",
)

# 本 collector 不启动 driver，不发送 A5 60；启动动作留给人工 no-motion smoke。
# 本 collector 不打开 LiDAR 串口，避免和 ROS2 driver 抢占 `/dev/ttyACM0`。
# 本 collector 不读取或写入 WAVE ROVER `/dev/ttyS5` 底盘串口。
# 本 collector 不发送 `T=1/T=13/T=130/T=131`，避免混入底盘材料。
# 本 collector 不发布 `/cmd_vel`，只允许读取已经存在的 ROS2 topic。
# `--expect-existing-topics` 只运行 `ros2 topic echo/hz`，不会启动节点。
# 任一 blocker 都保持 `safe_to_control=false`，不外推 HIL 或送达完成。
BLOCKED_COMMANDS_NOT_SENT = (
    {"command": {"T": 1}, "reason": "LiDAR proof must not send wheel speed commands"},
    {"command": {"T": 13}, "reason": "LiDAR proof must not send ROS velocity control JSON"},
    {"command": {"T": 130}, "reason": "base feedback probe is outside LiDAR scan proof"},
    {"command": {"T": 131}, "reason": "feedback-flow state change is outside LiDAR scan proof"},
    {"command": "cmd_vel", "reason": "collector reads LiDAR topics only and never publishes motion"},
    {"command": "A5 60", "reason": "collector does not start the LiDAR driver; run driver manually when runtime is ready"},
)


def now_ms() -> int:
    """毫秒时间便于和 8787 / PC artifact 做新鲜度对齐。"""
    return int(time.time() * 1000)


def utc_now() -> str:
    """UTC 字符串用于人工日志，不依赖目标机时区。"""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def compact_error(error: BaseException) -> dict[str, str]:
    """错误只保留短文本，避免远端环境噪声污染 artifact。"""
    return {"type": type(error).__name__, "message": str(error)[:300]}


def describe_path(path: str) -> dict[str, Any]:
    """只做路径元数据检查，不打开字符设备。"""
    entry: dict[str, Any] = {
        "path": path,
        "exists": os.path.exists(path),
        "lexists": os.path.lexists(path),
        "is_symlink": os.path.islink(path),
        "realpath": None,
        "error": None,
    }
    try:
        if entry["lexists"]:
            entry["realpath"] = os.path.realpath(path)
            stat_result = os.stat(path)
            entry["mode_octal"] = oct(stat_result.st_mode & 0o7777)
            entry["uid"] = stat_result.st_uid
            entry["gid"] = stat_result.st_gid
    except OSError as exc:
        entry["error"] = compact_error(exc)
    return entry


def fetch_json_url(url: str, timeout_s: float) -> dict[str, Any]:
    """只执行 GET 读取 8787 状态，不 POST、不触发硬件动作。"""
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as response:  # noqa: S310 - 现场 LAN 明确传入。
            raw = response.read(256 * 1024).decode("utf-8", errors="replace")
        parsed = json.loads(raw)
        return {"ok": isinstance(parsed, dict), "status": "loaded", "payload": parsed if isinstance(parsed, dict) else None}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status": "http_error", "error": {"type": "HTTPError", "message": str(exc), "code": exc.code}}
    except Exception as exc:  # noqa: BLE001 - 网络/JSON 异常统一进入 blocker。
        return {"ok": False, "status": "failed", "error": compact_error(exc)}


def run_bash(command: str, timeout_s: float) -> dict[str, Any]:
    """ROS2 topic read 走受限 timeout，避免 collector 长时间占用现场会话。"""
    try:
        completed = subprocess.run(
            ["bash", "-lc", command],
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout_s,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout_preview": completed.stdout[:2000],
            "stderr_preview": completed.stderr[:2000],
            "ok": completed.returncode == 0,
        }
    except subprocess.TimeoutExpired as exc:
        return {"command": command, "returncode": None, "ok": False, "error": {"type": "TimeoutExpired", "message": str(exc)}}


def ros2_source_prefix() -> str:
    """统一 source 顺序，确保远端 ROS2/install 缺口能被同一命令暴露。"""
    return f"source {ROS_HUMBLE_SETUP} && source {ROBER_INSTALL_SETUP}"


def build_topic_read_commands(timeout_s: float) -> dict[str, str]:
    """只构造 topic 读取命令，不构造 driver launch 或任何控制命令。"""
    inner_timeout = max(1, int(timeout_s))
    prefix = ros2_source_prefix()
    return {
        "scan_once": f"{prefix} && timeout {inner_timeout} ros2 topic echo --once {SCAN_TOPIC}",
        "raw_packet_once": f"{prefix} && timeout {inner_timeout} ros2 topic echo --once {RAW_PACKET_TOPIC}",
        "scan_hz": f"{prefix} && timeout {inner_timeout} ros2 topic hz {SCAN_TOPIC}",
    }


def proof_flags() -> dict[str, bool]:
    """LiDAR 材料不能被下游误读为底盘控制或 HIL 准入。"""
    return {
        "safe_to_control": False,
        "sends_commands": False,
        "sends_motion_commands": False,
        "robot_control_executed": False,
        "delivery_success": False,
        "hil_pass": False,
        "primary_actions_enabled": False,
    }


def build_probe_payload(
    *,
    upper_api_base_url: str = DEFAULT_UPPER_API_BASE_URL,
    expect_existing_topics: bool = False,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    path_exists: Callable[[str], bool] = os.path.exists,
    path_describer: Callable[[str], dict[str, Any]] = describe_path,
    url_fetcher: Callable[[str, float], dict[str, Any]] = fetch_json_url,
    command_runner: Callable[[str, float], dict[str, Any]] = run_bash,
) -> dict[str, Any]:
    """生成一次 LiDAR proof artifact；依赖全部可注入，方便单测证明边界。"""
    timeout_s = min(max(float(timeout_s), 1.0), 30.0)
    generated_at_ms = now_ms()
    humble_setup_exists = path_exists(ROS_HUMBLE_SETUP)
    install_setup_exists = path_exists(ROBER_INSTALL_SETUP)
    lidar_devices = {
        "/dev/lidar": path_describer("/dev/lidar"),
        "/dev/ttyACM0": path_describer("/dev/ttyACM0"),
        "/dev/serial/by-id/usb-STC_STC_USB_Serial-if00": path_describer("/dev/serial/by-id/usb-STC_STC_USB_Serial-if00"),
    }
    upper_api = {
        "health": url_fetcher(f"{upper_api_base_url.rstrip('/')}/health", timeout_s),
        "radar_status": url_fetcher(f"{upper_api_base_url.rstrip('/')}/api/radar/status", timeout_s),
    }
    ros2_available = shutil.which("ros2") is not None
    ros2_version: dict[str, Any] | None = None
    if humble_setup_exists:
        ros2_version = command_runner(f"{ros2_source_prefix()} && ros2 --version", timeout_s)
        ros2_available = bool(ros2_version.get("ok")) or ros2_available

    blockers: list[dict[str, str]] = []
    if not humble_setup_exists:
        blockers.append({"code": "ros2_humble_setup_missing", "detail": f"{ROS_HUMBLE_SETUP} not found"})
    if not install_setup_exists:
        blockers.append({"code": "rober_install_setup_missing", "detail": f"{ROBER_INSTALL_SETUP} not found"})
    if not ros2_available:
        blockers.append({"code": "ros2_command_unavailable", "detail": "ros2 command is unavailable in the current environment"})
    if not any(item.get("exists") for item in lidar_devices.values()):
        blockers.append({"code": "lidar_device_candidate_missing", "detail": "no /dev/lidar, /dev/ttyACM0, or STC by-id candidate exists"})
    radar_payload = upper_api["radar_status"].get("payload") if isinstance(upper_api["radar_status"], dict) else None
    radar_scan_status = radar_payload.get("scan_status") if isinstance(radar_payload, dict) else None
    if radar_scan_status not in {"proven", "scan_once_observed", "scan_hz_observed"}:
        blockers.append({"code": "upper_api_scan_not_proven", "detail": f"8787 radar scan_status={radar_scan_status!r}"})

    topic_reads: dict[str, Any] = {
        "attempted": False,
        "reason": "not_requested_without_expect_existing_topics",
        "commands": build_topic_read_commands(timeout_s),
        "results": {},
    }
    if expect_existing_topics and not any(item["code"] in {"ros2_humble_setup_missing", "rober_install_setup_missing", "ros2_command_unavailable"} for item in blockers):
        topic_reads["attempted"] = True
        topic_reads["reason"] = "expect_existing_topics_requested_read_only_ros2_topic_observation"
        for name, command in topic_reads["commands"].items():
            topic_reads["results"][name] = command_runner(command, timeout_s + 2)
    elif expect_existing_topics:
        topic_reads["reason"] = "blocked_before_topic_read_by_ros2_runtime"

    scan_once_ok = bool(topic_reads["results"].get("scan_once", {}).get("ok")) if topic_reads["attempted"] else False
    raw_packet_ok = bool(topic_reads["results"].get("raw_packet_once", {}).get("ok")) if topic_reads["attempted"] else False
    proof_status = "scan_and_raw_packet_observed" if scan_once_ok and raw_packet_ok else "blocked_or_not_observed"
    return {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "generated_at_ms": generated_at_ms,
        "vendor_sources": list(VENDOR_SOURCES),
        "evidence_boundary": "lidar_scan_proof_artifact_not_base_hil",
        "upper_api_base_url": upper_api_base_url,
        "ros_runtime": {
            "humble_setup": {"path": ROS_HUMBLE_SETUP, "exists": humble_setup_exists},
            "rober_install_setup": {"path": ROBER_INSTALL_SETUP, "exists": install_setup_exists},
            "ros2_available": ros2_available,
            "ros2_version": ros2_version,
        },
        "lidar_devices": lidar_devices,
        "upper_api": upper_api,
        "topic_reads": topic_reads,
        "proof": {
            "status": proof_status,
            "scan_topic": SCAN_TOPIC,
            "raw_packet_topic": RAW_PACKET_TOPIC,
            "scan_once_observed": scan_once_ok,
            "raw_packet_once_observed": raw_packet_ok,
            "pointcloud_fabricated": False,
            "driver_started_by_collector": False,
            "lidar_start_command_sent_by_collector": False,
        },
        "blockers": blockers,
        "blocked_commands_not_sent": list(BLOCKED_COMMANDS_NOT_SENT),
        **proof_flags(),
    }


def atomic_write_json(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    """artifact 用原子替换，避免 8787 readback 读到半截 JSON。"""
    destination = Path(path)
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        with tempfile.NamedTemporaryFile("wb", delete=False, dir=str(destination.parent), prefix=f".{destination.name}.") as handle:
            temp_name = handle.name
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, destination)
        return {"ok": True, "path": str(destination), "bytes_written": len(encoded), "method": "atomic_replace"}
    except Exception as exc:  # noqa: BLE001 - 写失败也必须结构化回传。
        return {"ok": False, "path": str(destination), "error": compact_error(exc), "method": "atomic_replace"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once-json", action="store_true", help="输出一次 JSON；保留该参数用于 SSH/stdin SOP")
    parser.add_argument("--output", default=None, help=f"写入 latest artifact，默认建议路径 {DEFAULT_OUTPUT_PATH}")
    parser.add_argument("--upper-api-base-url", default=os.getenv("ROBER_UPPER_API_BASE_URL", DEFAULT_UPPER_API_BASE_URL))
    parser.add_argument("--timeout-s", type=float, default=DEFAULT_TIMEOUT_S)
    parser.add_argument("--expect-existing-topics", action="store_true", help="只读取已存在 ROS2 topic，不启动 LiDAR driver")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_probe_payload(
        upper_api_base_url=args.upper_api_base_url,
        expect_existing_topics=args.expect_existing_topics,
        timeout_s=args.timeout_s,
    )
    if args.output:
        payload["artifact"] = atomic_write_json(args.output, payload)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
