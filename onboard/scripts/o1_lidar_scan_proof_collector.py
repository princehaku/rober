#!/usr/bin/env python3
"""O1 LiDAR `/scan` proof collector：只读采集 readiness/proof/blocker。"""

from __future__ import annotations

import argparse
import json
import os
import re
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
DEFAULT_TIMEOUT_S = 12.0
ROS_HUMBLE_SETUP = "/opt/ros/humble/setup.bash"
ROBER_INSTALL_SETUP = "/root/rober/onboard/install/setup.bash"
DEFAULT_ROS_HOME = "/root/.ros"
SCAN_TOPIC = "/scan"
RAW_PACKET_TOPIC = "/lidar/raw_packet"
BASE_FRAME = "base_link"
LIDAR_FRAME = "laser_frame"

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
        # `ros2 topic hz` 和 `tf2_echo` 本来就常靠 timeout 收尾；如果丢掉已打印文本，
        # live proof 会把真实观察误判成未观察，所以 timeout 分支也必须保留输出。
        return {
            "command": command,
            "returncode": None,
            "ok": False,
            "stdout_preview": preview_timeout_text(exc.stdout),
            "stderr_preview": preview_timeout_text(exc.stderr),
            "error": {"type": "TimeoutExpired", "message": str(exc)},
        }


def preview_timeout_text(value: Any, limit: int = 2000) -> str:
    """TimeoutExpired 可能给 bytes 或 str；统一保留尾部证据文本。"""
    if value is None:
        return ""
    if isinstance(value, bytes):
        text = value.decode("utf-8", errors="replace")
    else:
        text = str(value)
    return text[-limit:]


def ros2_environment_prefix() -> str:
    """systemd 服务常缺 HOME/USER，先固定 ROS 日志目录再调用 ROS2 CLI。"""
    # rcl logging 会展开 `~/.ros/log`；服务环境缺 HOME 时会先于 topic read 崩溃。
    # 这里显式补齐 root 服务身份，并创建日志目录，让 artifact 暴露真实 topic 状态。
    return (
        "export HOME=${HOME:-/root} && "
        "export USER=${USER:-root} && "
        "export LOGNAME=${LOGNAME:-root} && "
        "export ROS_HOME=${ROS_HOME:-$HOME/.ros} && "
        'mkdir -p "$ROS_HOME/log" && '
        "export ROS_LOG_DIR=${ROS_LOG_DIR:-$ROS_HOME/log}"
    )


def ros2_source_prefix() -> str:
    """统一 source/env 顺序，确保远端 ROS2/install 缺口能被同一命令暴露。"""
    return f"{ros2_environment_prefix()} && source {ROS_HUMBLE_SETUP} && source {ROBER_INSTALL_SETUP}"


def ros2_presence_command() -> str:
    """用 Humble 兼容的方式验证 ROS2 CLI；`ros2 --version` 在目标机上会误报失败。"""
    # Humble 的 ros2 CLI 没有稳定 `--version`，所以用 `command -v` 加 `--help` 做最小可执行检查。
    return f"{ros2_source_prefix()} && command -v ros2 && ros2 --help >/dev/null"


def build_topic_read_commands(timeout_s: float) -> dict[str, str]:
    """只构造 topic/TF 读取命令，不构造 driver launch 或任何控制命令。"""
    # 真机 DDS discovery 在禁用 daemon 后常超过 5 秒；12 秒能覆盖现场观测且仍保持短只读窗口。
    inner_timeout = max(12, int(timeout_s))
    prefix = ros2_source_prefix()
    return {
        # 现场 ROS daemon 偶发 `rclpy.ok()` XML-RPC 异常；proof 只需读 DDS topic，禁用 daemon 更稳。
        "scan_once": (
            f"{prefix} && timeout {inner_timeout} "
            f"ros2 topic echo --no-daemon --once {SCAN_TOPIC} sensor_msgs/msg/LaserScan"
        ),
        "scan_hz": f"{prefix} && timeout {inner_timeout} ros2 topic hz {SCAN_TOPIC}",
        "raw_packet_once": (
            f"{prefix} && timeout {inner_timeout} "
            f"ros2 topic echo --no-daemon --once {RAW_PACKET_TOPIC} std_msgs/msg/UInt8MultiArray"
        ),
        "tf": f"{prefix} && timeout {inner_timeout} ros2 run tf2_ros tf2_echo {BASE_FRAME} {LIDAR_FRAME}",
    }


def run_topic_read_commands(
    commands: dict[str, str],
    *,
    timeout_s: float,
    command_runner: Callable[[str, float], dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """顺序读取 ROS2 topic/TF，避免多路 ros2 CLI 同时 discovery 时互相拖垮。"""
    results: dict[str, dict[str, Any]] = {}
    if not commands:
        return results
    # 真机上 4 个 `ros2` CLI 并发启动会让 DDS discovery 抖动，出现手工读取成功、
    # collector 却三个 topic 全 timeout 的假阴性。顺序读取虽然稍慢，但仍在 API 预算内。
    for name, command in commands.items():
        try:
            results[name] = command_runner(command, timeout_s + 2)
        except Exception as exc:  # noqa: BLE001 - 单个 probe 异常不能吞掉后续 topic 证据。
            results[name] = {
                "command": command,
                "returncode": None,
                "ok": False,
                "stdout_preview": "",
                "stderr_preview": "",
                "error": compact_error(exc),
            }
    return results


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


def command_text(result: dict[str, Any]) -> str:
    """合并 stdout/stderr 摘要，便于 timeout 后仍从已打印文本识别证据。"""
    return f"{result.get('stdout_preview', '')}\n{result.get('stderr_preview', '')}"


def marker_observed(result: dict[str, Any], markers: tuple[str, ...]) -> bool:
    """命令可能被 timeout 终止；只要已输出关键证据，就按 observed 记录。"""
    if result.get("ok"):
        return True
    text = command_text(result)
    return any(marker in text for marker in markers)


def parse_scan_hz_average(result: dict[str, Any]) -> float | None:
    """解析 ros2 topic hz 的 average rate，供 PC 用数值判断实时雷达质量。"""
    match = re.search(r"average rate:\s*([0-9]+(?:\.[0-9]+)?)", command_text(result))
    return float(match.group(1)) if match else None


def build_required_observations(topic_reads: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """把四个验收点做成稳定字段，避免 PC 从 stdout 文本里猜结果。"""
    results = topic_reads.get("results", {}) if topic_reads.get("attempted") else {}
    scan_once_result = results.get("scan_once", {})
    scan_hz_result = results.get("scan_hz", {})
    raw_packet_result = results.get("raw_packet_once", {})
    tf_result = results.get("tf", {})
    scan_hz_average = parse_scan_hz_average(scan_hz_result)
    # 四个 key 独立表达，raw packet 只证明驱动发布原始包，不参与 `/scan` ready 判定。
    return {
        "scan_once": {
            "topic": SCAN_TOPIC,
            "observed": marker_observed(scan_once_result, ("ranges:", "angle_min:", "LaserScan")),
            "result_key": "scan_once",
        },
        "scan_hz": {
            "topic": SCAN_TOPIC,
            "observed": marker_observed(scan_hz_result, ("average rate:",)),
            "average_rate_hz": scan_hz_average,
            "result_key": "scan_hz",
        },
        "raw_packet_once": {
            "topic": RAW_PACKET_TOPIC,
            "observed": marker_observed(raw_packet_result, ("data:", "header:", "LidarRawPacket")),
            "result_key": "raw_packet_once",
        },
        "tf": {
            "parent_frame": BASE_FRAME,
            "child_frame": LIDAR_FRAME,
            "observed": marker_observed(tf_result, ("At time", "Translation:", "Rotation:")),
            "result_key": "tf",
        },
    }


def required_observations_from_upper_latest(radar_payload: dict[str, Any] | None) -> dict[str, dict[str, Any]] | None:
    """短窗口 topic 采样抖动时，复用 8787 已加载的 fresh latest proof，避免把好材料覆盖坏。"""
    if not isinstance(radar_payload, dict):
        return None
    latest = radar_payload.get("latest_scan_proof")
    if not isinstance(latest, dict):
        return None
    # 只有 fresh 且已完整观察的 latest proof 才能兜底；旧材料不能重新提升成当前雷达证明。
    if latest.get("fresh_while_observed") is not True or latest.get("all_required_observations_observed") is not True:
        return None
    required = latest.get("required_observations")
    if isinstance(required, dict) and required:
        copied: dict[str, dict[str, Any]] = {}
        for key in ("scan_once", "scan_hz", "raw_packet_once", "tf"):
            value = required.get(key)
            if not isinstance(value, dict) or value.get("observed") is not True:
                return None
            copied[key] = {
                "topic": value.get("topic"),
                "parent_frame": value.get("parent_frame"),
                "child_frame": value.get("child_frame"),
                "observed": True,
                "average_rate_hz": value.get("average_rate_hz"),
                "result_key": value.get("result_key") or key,
                "fallback_source": "upper_api_radar_status_latest_scan_proof",
            }
        return copied
    if not all(latest.get(key) is True for key in ("scan_once_observed", "scan_hz_observed", "raw_packet_once_observed", "tf_observed")):
        return None
    return {
        "scan_once": {
            "topic": SCAN_TOPIC,
            "observed": True,
            "result_key": "scan_once",
            "fallback_source": "upper_api_radar_status_latest_scan_proof",
        },
        "scan_hz": {
            "topic": SCAN_TOPIC,
            "observed": True,
            "average_rate_hz": latest.get("scan_hz_average_rate_hz"),
            "result_key": "scan_hz",
            "fallback_source": "upper_api_radar_status_latest_scan_proof",
        },
        "raw_packet_once": {
            "topic": RAW_PACKET_TOPIC,
            "observed": True,
            "result_key": "raw_packet_once",
            "fallback_source": "upper_api_radar_status_latest_scan_proof",
        },
        "tf": {
            "parent_frame": BASE_FRAME,
            "child_frame": LIDAR_FRAME,
            "observed": True,
            "result_key": "tf",
            "fallback_source": "upper_api_radar_status_latest_scan_proof",
        },
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
    timeout_s = min(max(float(timeout_s), 12.0), 30.0)
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
    ros2_cli_check: dict[str, Any] | None = None
    if humble_setup_exists:
        ros2_cli_check = command_runner(ros2_presence_command(), timeout_s)
        ros2_available = bool(ros2_cli_check.get("ok")) or ros2_available

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
    if radar_scan_status not in {"proven", "scan_once_observed", "scan_hz_observed", "fresh_scan_proof_observed"}:
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
        topic_reads["mode"] = "parallel_topic_and_tf_observation"
        topic_reads["results"] = run_topic_read_commands(
            topic_reads["commands"],
            timeout_s=timeout_s,
            command_runner=command_runner,
        )
    elif expect_existing_topics:
        topic_reads["reason"] = "blocked_before_topic_read_by_ros2_runtime"

    required_observations = build_required_observations(topic_reads)
    fallback_required_observations = required_observations_from_upper_latest(radar_payload)
    fallback_used = False
    # collector 是短只读窗口，DDS discovery 偶发 miss 时不能把 8787 已证明 fresh 的材料覆盖成坏 artifact。
    if not all(item["observed"] for item in required_observations.values()) and fallback_required_observations:
        required_observations = fallback_required_observations
        fallback_used = True
    scan_once_ok = required_observations["scan_once"]["observed"]
    scan_hz_ok = required_observations["scan_hz"]["observed"]
    raw_packet_ok = required_observations["raw_packet_once"]["observed"]
    tf_ok = required_observations["tf"]["observed"]
    all_required_observations_ok = all(item["observed"] for item in required_observations.values())
    if all_required_observations_ok:
        proof_status = "scan_once_hz_raw_packet_tf_observed"
        # direct topic/TF proof 比 8787 status 摘要更新；全量观察到时不再保留旧 status blocker。
        blockers = [item for item in blockers if item.get("code") != "upper_api_scan_not_proven"]
    elif any(item["observed"] for item in required_observations.values()):
        proof_status = "partially_observed"
    else:
        proof_status = "blocked_or_not_observed"
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
            # 只记录默认目录，避免把服务环境差异藏进 stderr 里让 PC 难以诊断。
            "ros_home_default": DEFAULT_ROS_HOME,
            "ros_log_dir_default": f"{DEFAULT_ROS_HOME}/log",
            "ros2_available": ros2_available,
            "ros2_cli_check": ros2_cli_check,
        },
        "lidar_devices": lidar_devices,
        "upper_api": upper_api,
        "topic_reads": topic_reads,
        "proof": {
            "status": proof_status,
            "scan_topic": SCAN_TOPIC,
            "raw_packet_topic": RAW_PACKET_TOPIC,
            "tf_parent_frame": BASE_FRAME,
            "tf_child_frame": LIDAR_FRAME,
            "scan_once_observed": scan_once_ok,
            "scan_hz_observed": scan_hz_ok,
            "scan_hz_average_rate_hz": required_observations["scan_hz"]["average_rate_hz"],
            "raw_packet_once_observed": raw_packet_ok,
            "tf_observed": tf_ok,
            "required_observations": required_observations,
            "all_required_observations_observed": all_required_observations_ok,
            "runtime_summary_fallback_used": fallback_used,
            "runtime_summary_fallback_source": "upper_api_radar_status_latest_scan_proof" if fallback_used else None,
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
