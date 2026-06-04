#!/usr/bin/env python3
"""Orange Pi 上位机统一 Robot API：camera / radar / base 汇总入口。"""

from __future__ import annotations

import argparse
import asyncio
import glob
import json
import os
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin


SCHEMA = "trashbot.upper_robot_api.v1"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8787
DEFAULT_CAMERA_BASE_URL = "http://127.0.0.1:8088"
DEFAULT_BASE_PORT = "/dev/ttyS5"
DEFAULT_BASE_BAUDRATE = 115200
DEFAULT_MAX_SPEED = 0.12
DEFAULT_PULSE_MS = 260
MAX_PULSE_MS = 800
ALLOWED_DIRECTIONS = frozenset({"forward", "back", "left", "right", "stop"})
DEFAULT_FEEDBACK_READ_TIMEOUT_S = 0.2
DEFAULT_FEEDBACK_READ_WINDOW_S = 1.2
DEFAULT_FEEDBACK_SAMPLE_COUNT = 3
DEFAULT_FEEDBACK_SAMPLE_INTERVAL_S = 0.2
DEFAULT_FEEDBACK_SAMPLES_ARTIFACT_PATH = "runtime/base_feedback_samples_latest.json"
DEFAULT_LIDAR_SCAN_PROOF_ARTIFACT_PATH = "runtime/lidar_scan_proof_latest.json"
DEFAULT_LIDAR_RAW_PACKET_PROOF_ARTIFACT_PATH = "runtime/lidar_raw_packet_proof_latest.json"
DEFAULT_MAP_ARTIFACT_DIR = "runtime/maps"
DEFAULT_MAP_LIFECYCLE_PROOF_ARTIFACT_PATH = "runtime/map_lifecycle_latest.json"
DEFAULT_LOCALIZATION_ARTIFACT_PATH = "runtime/localization_reset_latest.json"
DEFAULT_NAV2_LIFECYCLE_ARTIFACT_PATH = "runtime/nav2_lifecycle_latest.json"
DEFAULT_ELEVATOR_STATUS_ARTIFACT_PATH = "runtime/elevator_status_latest.json"
DEFAULT_FEEDBACK_SAMPLES_STALE_AFTER_MS = 15 * 60 * 1000
MAX_FEEDBACK_READ_TIMEOUT_S = 2.0
MAX_FEEDBACK_READ_WINDOW_S = 5.0
MAX_FEEDBACK_SAMPLE_COUNT = 8
MAX_FEEDBACK_SAMPLE_INTERVAL_S = 2.0
BASE_FEEDBACK_REQUEST_COMMAND = {"T": 130}
BASE_FEEDBACK_ID = 1001
BLOCKED_BASE_FEEDBACK_COMMANDS = [
    "T=1",
    "T=13",
    "T=131",
    "cmd_vel",
    "/api/base/manual",
]
ROUTE_PATHS = {
    "camera_health": "/api/camera/health",
    "camera_devices": "/api/camera/devices",
    "camera_offer": "/api/camera/offer",
    "camera_peer_close": "/api/camera/peers/{peer_id}/close",
    "radar_status": "/api/radar/status",
    "radar_start": "/api/radar/start",
    "radar_stop": "/api/radar/stop",
    "radar_scan_proof_latest": "/api/radar/scan-proof/latest",
    "radar_raw_packet_proof_latest": "/api/radar/raw-packet-proof/latest",
    "map_start": "/api/map/start",
    "map_reset": "/api/map/reset",
    "map_save": "/api/map/save",
    "map_load": "/api/map/load",
    "map_list": "/api/map/list",
    "map_proof_latest": "/api/map/proof/latest",
    "localize_reset": "/api/localize/reset",
    "localize_proof_latest": "/api/localize/proof/latest",
    "nav2_status": "/api/nav2/status",
    "nav2_start": "/api/nav2/start",
    "nav2_stop": "/api/nav2/stop",
    "elevator_status": "/api/elevator/status",
    "base_status": "/api/base/status",
    "base_feedback_request": "/api/base/feedback-request",
    "base_feedback_samples": "/api/base/feedback-samples",
    "base_feedback_samples_latest": "/api/base/feedback-samples/latest",
    "base_manual": "/api/base/manual",
    "base_stop": "/api/base/stop",
}

VENDOR_SOURCES = [
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
]

LIDAR_VENDOR_SOURCES = [
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/lidar_pkg_ros2-main/README.md",
    "docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp",
    "docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml",
    "docs/vendor/lidar_pkg_ros2-main/launch/lidar.launch.py",
    "docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules",
]


def now_ms() -> int:
    """统一毫秒时间戳，方便 PC、上位机和远端日志对齐。"""
    return int(time.time() * 1000)


def proof_flags() -> dict[str, Any]:
    """统一 API 在线不等于自动驾驶或交付完成，所以安全字段必须集中固定。"""
    return {
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "cloud_relay": False,
    }


def json_response(payload: dict[str, Any], status: int = 200) -> Any:
    """aiohttp 响应统一走 JSON，附带 LAN 调试 CORS，方便 PC 同源/跨源两种接法。"""
    from aiohttp import web

    return web.json_response(
        payload,
        status=status,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,Accept",
        },
    )


def compact_error(error: BaseException) -> dict[str, str]:
    """错误只输出类型和短文本，不泄露系统无关上下文。"""
    return {"type": type(error).__name__, "message": str(error)[:240]}


def t1001_boundary(reason: str | None = None) -> dict[str, Any]:
    """当前 API 不读反馈包，避免把串口写入误包装成闭环 ACK。"""
    return {
        "t1001_observed": False,
        "robot_ack_connected": False,
        "reason": reason or "T=1001 feedback is not observed by this local API call",
        "source_boundary": "vendor T=130 requests FEEDBACK_BASE_INFO, but this API only records write results",
    }


def read_text(path: str, max_bytes: int = 4096) -> str | None:
    """只读 sysfs/procfs 小文本；失败返回 None，不让健康接口 500。"""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")[:max_bytes].strip()
    except OSError:
        return None


def describe_path(path: str) -> dict[str, Any]:
    """描述设备路径元数据，不打开串口或雷达设备。"""
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


def list_candidates(patterns: list[str]) -> list[dict[str, Any]]:
    """候选设备只做 glob/stat，避免状态接口误打开硬件。"""
    paths: set[str] = set()
    for pattern in patterns:
        paths.update(glob.glob(pattern))
    return [describe_path(path) for path in sorted(paths)]


def load_serial_module() -> tuple[Any | None, str | None]:
    """pyserial 是底盘写入口依赖；缺失时 API 继续返回可读 blocker。"""
    try:
        import serial  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001 - 现场裁剪 Python 可能缺依赖。
        return None, f"{type(exc).__name__}: {exc}"
    return serial, None


def wheel_command_for_direction(direction: str, speed: float) -> dict[str, float | int]:
    """把 PC 方向键转换为 vendor T=1 左右轮速，低速点动后必须自动停车。"""
    if direction == "forward":
        left, right = speed, speed
    elif direction == "back":
        left, right = -speed, -speed
    elif direction == "left":
        left, right = -speed, speed
    elif direction == "right":
        left, right = speed, -speed
    elif direction == "stop":
        left, right = 0.0, 0.0
    else:
        raise ValueError(f"unsupported_direction:{direction}")
    return {"T": 1, "L": round(left, 3), "R": round(right, 3)}


def write_serial_json(port: str, baudrate: int, command: dict[str, Any]) -> dict[str, Any]:
    """串口写入只发送一行 JSON，调用方负责动作边界和停车兜底。"""
    serial_module, import_error = load_serial_module()
    if serial_module is None:
        return {"ok": False, "error": {"type": "pyserial_unavailable", "message": import_error or "missing"}}
    serial_obj = None
    try:
        serial_obj = serial_module.Serial(port=port, baudrate=baudrate, timeout=0.2)
        frame = (json.dumps(command, separators=(",", ":")) + "\n").encode("utf-8")
        bytes_written = serial_obj.write(frame)
        return {"ok": True, "command": command, "bytes_written": bytes_written}
    except Exception as exc:  # noqa: BLE001 - 串口现场错误要结构化返回。
        return {"ok": False, "error": compact_error(exc), "command": command}
    finally:
        if serial_obj is not None:
            try:
                serial_obj.close()
            except Exception:
                pass


def clamp_float(value: Any, default: float, min_value: float, max_value: float) -> float:
    """HTTP body 里的窗口参数必须限幅，避免一次请求长时间占用串口。"""
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return min(max(parsed, min_value), max_value)


def clamp_int(value: Any, default: int, min_value: int, max_value: int) -> int:
    """样本数只允许短批量，防止现场误传大值让 8787 长时间占用串口。"""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return min(max(parsed, min_value), max_value)


def artifact_path_info(path: str) -> dict[str, Any]:
    """artifact path 是运营材料入口，回包要暴露但不读取或打开串口。"""
    return {
        "path": path,
        "configured_by": "ROBER_BASE_FEEDBACK_SAMPLES_ARTIFACT_PATH or --feedback-samples-artifact-path",
        "format": "json",
        "schema": f"{SCHEMA}.base_feedback_samples_result",
    }


def lidar_scan_proof_artifact_info(path: str) -> dict[str, Any]:
    """LiDAR `/scan` proof artifact 只读入口，不代表当前已经证明 `/scan`。"""
    return {
        "path": path,
        "configured_by": "ROBER_LIDAR_SCAN_PROOF_ARTIFACT_PATH or --lidar-scan-proof-artifact-path",
        "format": "json",
        "schema": "trashbot.o1.lidar_scan_proof.v1",
    }


def lidar_raw_packet_proof_artifact_info(path: str) -> dict[str, Any]:
    """LiDAR raw packet proof artifact 只读入口，只代表串口原始材料可回放。"""
    return {
        "path": path,
        "configured_by": "ROBER_LIDAR_RAW_PACKET_PROOF_ARTIFACT_PATH or --lidar-raw-packet-proof-artifact-path",
        "format": "json",
        "schema": "trashbot.o1.lidar_raw_packet_proof.v1",
    }


def map_artifact_info(path: str) -> dict[str, Any]:
    """地图 artifact 目录只作为软件合同入口，不证明 SLAM 已经产图。"""
    return {
        "path": path,
        "configured_by": "ROBER_MAP_ARTIFACT_DIR or --map-artifact-dir",
        "expected_files": ["*.yaml", "*.pgm", "*.pbstream"],
        "schema": f"{SCHEMA}.map_lifecycle_artifact",
    }


def map_lifecycle_proof_artifact_info(path: str) -> dict[str, Any]:
    """SLAM/map lifecycle runtime 材料入口，读取它也不能替代真实 ROS2 运行。"""
    return {
        "path": path,
        "configured_by": "ROBER_MAP_LIFECYCLE_PROOF_ARTIFACT_PATH or --map-lifecycle-proof-artifact-path",
        "format": "json",
        "schema": f"{SCHEMA}.map_lifecycle_runtime_proof",
        "expected_material": [
            "/map once",
            "map yaml/image or pbstream",
            "map metadata",
            "slam_toolbox lifecycle state",
        ],
    }


def localization_artifact_info(path: str) -> dict[str, Any]:
    """定位 reset artifact 是上层回放材料，不代表 AMCL 已恢复定位。"""
    return {
        "path": path,
        "configured_by": "ROBER_LOCALIZATION_ARTIFACT_PATH or --localization-artifact-path",
        "format": "json",
        "schema": f"{SCHEMA}.localization_reset_artifact",
    }


def nav2_lifecycle_artifact_info(path: str) -> dict[str, Any]:
    """Nav2 lifecycle 材料入口用于回放状态，不在 HTTP status 里探 ROS graph。"""
    return {
        "path": path,
        "configured_by": "ROBER_NAV2_LIFECYCLE_ARTIFACT_PATH or --nav2-lifecycle-artifact-path",
        "format": "json",
        "schema": f"{SCHEMA}.nav2_lifecycle_runtime_proof",
        "expected_material": [
            "map_server lifecycle state",
            "amcl lifecycle state",
            "planner/controller lifecycle state",
            "Nav2 consumes /scan + map",
            "path generated or explicitly blocked",
        ],
    }


def elevator_status_artifact_info(path: str) -> dict[str, Any]:
    """电梯 evidence 只读入口把 OpenCV/状态链材料暴露给 PC，但不宣称实景通过。"""
    return {
        "path": path,
        "configured_by": "ROBER_ELEVATOR_STATUS_ARTIFACT_PATH or --elevator-status-artifact-path",
        "format": "json",
        "schema": "trashbot.elevator_status_runtime_boundary.v1",
        "expected_material": [
            "opencv evidence_ref",
            "door/floor/safe_to_exit decision",
            "task_orchestrator elevator phase",
            "manual handoff reason",
        ],
    }


def command_config_info(env_name: str, command: str | None) -> dict[str, Any]:
    """命令入口显式暴露配置来源，避免 PC 把默认 dry-run 误判为真实 ROS2。"""
    configured = bool(command and command.strip())
    try:
        argv = shlex.split(command) if configured else []
        error = None
    except ValueError as exc:
        # status 接口也要 fail-closed；配置写坏时给 PC 明确错误，不让 8787 变 500。
        argv = []
        error = compact_error(exc)
    return {
        "env": env_name,
        "configured": configured,
        "mode": "command" if configured else "dry_run_stub",
        "argv": argv,
        "error": error,
    }


def run_configured_command(command: str | None, timeout_s: float = 12.0) -> dict[str, Any]:
    """只执行显式配置的非 shell 命令；默认 dry-run，保持 HTTP 合同先行。"""
    if not command or not command.strip():
        return {
            "mode": "dry_run_stub",
            "executed": False,
            "ok": False,
            "reason": "no_command_configured",
        }
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        return {"mode": "command", "executed": False, "ok": False, "error": compact_error(exc)}
    if not argv:
        return {"mode": "dry_run_stub", "executed": False, "ok": False, "reason": "empty_command"}
    try:
        completed = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except Exception as exc:  # noqa: BLE001 - 现场 ROS2 命令失败要结构化给 PC。
        return {"mode": "command", "executed": False, "ok": False, "argv": argv, "error": compact_error(exc)}
    return {
        "mode": "command",
        "executed": True,
        "ok": completed.returncode == 0,
        "argv": argv,
        "returncode": completed.returncode,
        "stdout_preview": completed.stdout[-1200:],
        "stderr_preview": completed.stderr[-1200:],
    }


def software_guard_payload(
    *,
    schema_suffix: str,
    action: str,
    endpoint: str,
    command_env: str | None = None,
    command: str | None = None,
    command_result: dict[str, Any] | None = None,
    artifact: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """所有新生命周期入口都先 fail-closed，真实证明只能来自后续 ROS2/runtime artifact。"""
    configured = bool(command and command.strip())
    result_ok = bool(command_result and command_result.get("ok"))
    payload: dict[str, Any] = {
        "schema": f"{SCHEMA}.{schema_suffix}",
        "generated_at_ms": now_ms(),
        "action": action,
        "endpoint": endpoint,
        "status": "not_proven",
        "proof_state": "not_proven",
        "software_guard": True,
        "not_proven": True,
        "configured_command": command_config_info(command_env, command) if command_env else None,
        "command_result": command_result,
        "artifact": artifact,
        "ros2_runtime_proven": False,
        "map_artifact_proven": False,
        "localization_proven": False,
        "scan_runtime_proven": False,
        "sends_base_motion_commands": False,
        "uses_base_uart": False,
        "blocked_devices_not_touched": [DEFAULT_BASE_PORT, "/dev/ttyS5"],
        "blocked_commands_not_sent": ["T=1", "T=13", "T=130", "T=131", "/cmd_vel", "/api/base/manual"],
        "failure_reason": None if result_ok else ("command_not_configured" if not configured else "configured_command_failed"),
        "operator_message": (
            "command executed but ROS2/runtime proof is still not attached"
            if result_ok
            else "software guard only; configure ROS2 command and attach runtime artifact before claiming proof"
        ),
        "sends_commands": result_ok,
        **proof_flags(),
    }
    if extra:
        payload.update(extra)
    return payload


def runtime_boundary_flags() -> dict[str, Any]:
    """所有 ROS2 runtime 材料 readback 都保守关闭控制和 OKR 完成宣称。"""
    return {
        "readback_sends_commands": False,
        "sends_commands": False,
        "sends_motion_commands": False,
        "sends_base_motion_commands": False,
        "uses_base_uart": False,
        "opens_serial": False,
        "starts_ros2": False,
        "ros2_runtime_proven": False,
        "map_artifact_proven": False,
        "localization_proven": False,
        "nav2_runtime_proven": False,
        "elevator_runtime_proven": False,
        "field_hil_material": False,
    }


def build_runtime_artifact_readback_payload(
    *,
    schema_suffix: str,
    endpoint: str,
    artifact: dict[str, Any],
    latest_result: dict[str, Any] | None,
    boundary: str,
    source: str,
) -> dict[str, Any]:
    """统一 latest artifact 输出，避免每个入口遗漏 fail-closed 字段。"""
    return {
        "schema": f"{SCHEMA}.{schema_suffix}",
        "generated_at_ms": now_ms(),
        "endpoint": endpoint,
        "source": source,
        "artifact": artifact,
        "latest_result": latest_result,
        "status": "not_proven",
        "proof_state": "not_proven",
        "software_guard": True,
        "not_proven": True,
        "boundary": boundary,
        **runtime_boundary_flags(),
        **proof_flags(),
    }


def read_runtime_artifact_latest(
    path: str,
    *,
    artifact_info: dict[str, Any],
    schema_suffix: str,
    endpoint: str,
    boundary: str,
    source: str,
) -> tuple[int, dict[str, Any]]:
    """只读 JSON artifact；缺失、坏 JSON、非对象都不能触发 ROS2 或硬件。"""
    artifact = dict(artifact_info)
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        artifact.update({"ok": False, "status": "missing", "error": {"type": "FileNotFoundError", "message": "latest runtime artifact is missing"}})
        return 404, build_runtime_artifact_readback_payload(
            schema_suffix=schema_suffix,
            endpoint=endpoint,
            artifact=artifact,
            latest_result=None,
            boundary=boundary,
            source=source,
        )
    except OSError as exc:
        artifact.update({"ok": False, "status": "read_failed", "error": compact_error(exc)})
        return 500, build_runtime_artifact_readback_payload(
            schema_suffix=schema_suffix,
            endpoint=endpoint,
            artifact=artifact,
            latest_result=None,
            boundary=boundary,
            source=source,
        )
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        artifact.update({"ok": False, "status": "bad_json", "bytes_read": len(raw.encode("utf-8")), "error": compact_error(exc)})
        return 422, build_runtime_artifact_readback_payload(
            schema_suffix=schema_suffix,
            endpoint=endpoint,
            artifact=artifact,
            latest_result=None,
            boundary=boundary,
            source=source,
        )
    if not isinstance(parsed, dict):
        artifact.update({"ok": False, "status": "json_not_object", "bytes_read": len(raw.encode("utf-8"))})
        return 422, build_runtime_artifact_readback_payload(
            schema_suffix=schema_suffix,
            endpoint=endpoint,
            artifact=artifact,
            latest_result=None,
            boundary=boundary,
            source=source,
        )
    artifact.update({"ok": True, "status": "loaded", "bytes_read": len(raw.encode("utf-8"))})
    return 200, build_runtime_artifact_readback_payload(
        schema_suffix=schema_suffix,
        endpoint=endpoint,
        artifact=artifact,
        latest_result=parsed,
        boundary=boundary,
        source=source,
    )


def latest_proof_value(parsed: dict[str, Any] | None, *keys: str) -> Any:
    """兼容 collector 把字段写在 proof 或顶层两种形态，减少 artifact 格式返工。"""
    if not isinstance(parsed, dict):
        return None
    proof = parsed.get("proof") if isinstance(parsed.get("proof"), dict) else {}
    for key in keys:
        if key in proof:
            return proof.get(key)
        if key in parsed:
            return parsed.get(key)
    return None


def runtime_artifact_summary(
    path: str,
    *,
    artifact_info: dict[str, Any],
    schema_suffix: str,
    endpoint: str,
    boundary: str,
    source: str,
    fields: dict[str, tuple[str, ...]],
) -> dict[str, Any]:
    """status 页面用压缩摘要，既能给 PC 点灯，也保留 not_proven 边界。"""
    http_status, payload = read_runtime_artifact_latest(
        path,
        artifact_info=artifact_info,
        schema_suffix=schema_suffix,
        endpoint=endpoint,
        boundary=boundary,
        source=source,
    )
    latest = payload.get("latest_result") if isinstance(payload.get("latest_result"), dict) else None
    summary: dict[str, Any] = {
        "schema": f"{SCHEMA}.{schema_suffix}_summary",
        "generated_at_ms": now_ms(),
        "endpoint": endpoint,
        "http_status": http_status,
        "artifact": payload["artifact"],
        "latest_result_schema": latest.get("schema") if isinstance(latest, dict) else None,
        "latest_proof_status": latest_proof_value(latest, "status"),
        "latest_evidence_ref": latest_proof_value(latest, "evidence_ref"),
        "status": "not_proven",
        "software_guard": True,
        "not_proven": True,
        "boundary": boundary,
        **runtime_boundary_flags(),
        **proof_flags(),
    }
    for output_key, candidate_keys in fields.items():
        summary[output_key] = latest_proof_value(latest, *candidate_keys)
    return summary


def summarize_map_lifecycle_latest_artifact(path: str) -> dict[str, Any]:
    """压缩 SLAM/map proof；字段缺失保持 None，不能默认判定 observed。"""
    return runtime_artifact_summary(
        path,
        artifact_info=map_lifecycle_proof_artifact_info(path),
        schema_suffix="map_lifecycle_proof_latest",
        endpoint=ROUTE_PATHS["map_proof_latest"],
        boundary="software_guard_only_not_real_slam_map_or_nav2_consumption",
        source="map_lifecycle_runtime_artifact",
        fields={
            "latest_map_once_observed": ("map_once_observed", "/map_once_observed"),
            "latest_map_file_observed": ("map_file_observed", "map_yaml_observed", "map_pbstream_observed"),
            "latest_map_metadata_observed": ("map_metadata_observed", "metadata_observed"),
            "latest_slam_toolbox_state": ("slam_toolbox_state", "slam_state"),
        },
    )


def summarize_localization_latest_artifact(path: str) -> dict[str, Any]:
    """压缩 AMCL/initialpose proof；只做 artifact 摘要，不发布 /initialpose。"""
    return runtime_artifact_summary(
        path,
        artifact_info=localization_artifact_info(path),
        schema_suffix="localization_proof_latest",
        endpoint=ROUTE_PATHS["localize_proof_latest"],
        boundary="software_guard_only_not_real_amcl_localization_reset",
        source="localization_runtime_artifact",
        fields={
            "latest_initialpose_published": ("initialpose_published", "initial_pose_published"),
            "latest_amcl_pose_observed": ("amcl_pose_observed", "/amcl_pose_observed"),
            "latest_tf_fresh": ("tf_fresh", "map_to_base_link_tf_fresh"),
            "latest_pose_fresh": ("pose_fresh", "pose_timestamp_fresh"),
        },
    )


def summarize_nav2_lifecycle_latest_artifact(path: str) -> dict[str, Any]:
    """压缩 Nav2 lifecycle proof；Nav2 消费 /scan+map 仍由 runtime artifact 证明。"""
    return runtime_artifact_summary(
        path,
        artifact_info=nav2_lifecycle_artifact_info(path),
        schema_suffix="nav2_lifecycle_proof_latest",
        endpoint=ROUTE_PATHS["nav2_status"],
        boundary="software_guard_only_not_real_nav2_runtime_or_path_execution",
        source="nav2_lifecycle_runtime_artifact",
        fields={
            "latest_map_server_active": ("map_server_active", "map_server_lifecycle_active"),
            "latest_amcl_active": ("amcl_active", "amcl_lifecycle_active"),
            "latest_planner_active": ("planner_active", "planner_server_active"),
            "latest_controller_active": ("controller_active", "controller_server_active"),
            "latest_scan_consumed": ("scan_consumed", "laser_scan_consumed"),
            "latest_path_generated": ("path_generated", "global_path_generated"),
        },
    )


def summarize_elevator_status_latest_artifact(path: str) -> dict[str, Any]:
    """压缩电梯 evidence；OpenCV/状态链未进真实电梯前必须持续 not_proven。"""
    return runtime_artifact_summary(
        path,
        artifact_info=elevator_status_artifact_info(path),
        schema_suffix="elevator_status_latest",
        endpoint=ROUTE_PATHS["elevator_status"],
        boundary="software_guard_only_not_real_elevator_opencv_or_field_delivery",
        source="elevator_status_runtime_artifact",
        fields={
            "latest_elevator_phase": ("elevator_phase", "phase"),
            "latest_opencv_evidence_ref": ("opencv_evidence_ref", "evidence_ref"),
            "latest_target_floor_confirmed": ("target_floor_confirmed",),
            "latest_safe_to_exit": ("safe_to_exit",),
            "latest_handoff_required": ("handoff_required", "manual_handoff_required"),
        },
    )


def read_lidar_scan_proof_latest_artifact(path: str) -> tuple[int, dict[str, Any]]:
    """只读 LiDAR proof artifact，不启动 driver、不打开串口、不发送 A5 60。"""
    artifact = lidar_scan_proof_artifact_info(path)
    payload: dict[str, Any] = {
        "schema": f"{SCHEMA}.lidar_scan_proof_latest_result",
        "generated_at_ms": now_ms(),
        "vendor_sources": LIDAR_VENDOR_SOURCES,
        "artifact": artifact,
        "latest_result": None,
        "readback_sends_commands": False,
        "sends_commands": False,
        "sends_motion_commands": False,
        "robot_control_executed": False,
        "delivery_success": False,
        "hil_pass": False,
        "safe_to_control": False,
        "primary_actions_enabled": False,
    }
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        artifact.update({"ok": False, "status": "missing", "error": {"type": "FileNotFoundError", "message": "latest LiDAR scan proof artifact is missing"}})
        return 404, payload
    except OSError as exc:
        artifact.update({"ok": False, "status": "read_failed", "error": compact_error(exc)})
        return 500, payload
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        artifact.update({"ok": False, "status": "bad_json", "error": compact_error(exc)})
        return 422, payload
    if not isinstance(parsed, dict):
        artifact.update({"ok": False, "status": "json_not_object", "error": {"type": "ValueError", "message": "latest LiDAR artifact JSON root is not an object"}})
        return 422, payload
    artifact.update({"ok": True, "status": "loaded", "bytes_read": len(raw.encode("utf-8"))})
    payload["latest_result"] = parsed
    return 200, payload


def build_lidar_raw_packet_readback_payload(
    artifact_status: dict[str, Any],
    latest_result: dict[str, Any] | None,
) -> dict[str, Any]:
    """raw packet latest 回放必须 fail-closed，避免 PC 把材料入口当控制入口。"""
    return {
        "schema": f"{SCHEMA}.lidar_raw_packet_proof_latest_result",
        "generated_at_ms": now_ms(),
        "vendor_sources": LIDAR_VENDOR_SOURCES,
        "artifact": artifact_status,
        "latest_result": latest_result,
        "latest_endpoint_path": ROUTE_PATHS["radar_raw_packet_proof_latest"],
        "readback_sends_commands": False,
        "sends_commands": False,
        "sends_lidar_start_command": False,
        "sends_motion_commands": False,
        "opens_lidar_serial": False,
        "starts_ros2": False,
        "calls_base_manual": False,
        "robot_control_executed": False,
        "delivery_success": False,
        "hil_pass": False,
        "safe_to_control": False,
        "primary_actions_enabled": False,
    }


def read_lidar_raw_packet_proof_latest_artifact(path: str) -> tuple[int, dict[str, Any]]:
    """只读 raw packet artifact，不打开 LiDAR 串口、不发送 A5 60、不启动 ROS2。"""
    artifact = lidar_raw_packet_proof_artifact_info(path)
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        artifact.update({"ok": False, "status": "missing", "error": {"type": "FileNotFoundError", "message": "latest LiDAR raw packet proof artifact is missing"}})
        return 404, build_lidar_raw_packet_readback_payload(artifact, None)
    except OSError as exc:
        artifact.update({"ok": False, "status": "read_failed", "error": compact_error(exc)})
        return 500, build_lidar_raw_packet_readback_payload(artifact, None)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        artifact.update({"ok": False, "status": "bad_json", "error": compact_error(exc)})
        return 422, build_lidar_raw_packet_readback_payload(artifact, None)
    if not isinstance(parsed, dict):
        artifact.update({"ok": False, "status": "json_not_object", "error": {"type": "ValueError", "message": "latest raw packet artifact JSON root is not an object"}})
        return 422, build_lidar_raw_packet_readback_payload(artifact, None)
    artifact.update({"ok": True, "status": "loaded", "bytes_read": len(raw.encode("utf-8"))})
    return 200, build_lidar_raw_packet_readback_payload(artifact, parsed)


def summarize_lidar_scan_proof_latest_artifact(path: str) -> dict[str, Any]:
    """status 里只做 artifact readback 摘要，避免状态页触发 ROS2 或硬件。"""
    http_status, payload = read_lidar_scan_proof_latest_artifact(path)
    latest_result = payload.get("latest_result") if isinstance(payload.get("latest_result"), dict) else None
    proof = latest_result.get("proof", {}) if isinstance(latest_result, dict) else {}
    required_observations = proof.get("required_observations") if isinstance(proof, dict) else None
    # status 面只压缩 artifact 已经写好的机器字段，不能在这里从 stdout 猜结果或触发 ROS2。
    compact_required_observations = {
        key: {
            "observed": value.get("observed"),
            "result_key": value.get("result_key"),
            "topic": value.get("topic"),
            "parent_frame": value.get("parent_frame"),
            "child_frame": value.get("child_frame"),
            "average_rate_hz": value.get("average_rate_hz"),
        }
        for key, value in required_observations.items()
        if isinstance(value, dict)
    } if isinstance(required_observations, dict) else None
    return {
        "schema": f"{SCHEMA}.lidar_scan_proof_latest_summary",
        "generated_at_ms": now_ms(),
        "endpoint": ROUTE_PATHS["radar_scan_proof_latest"],
        "http_status": http_status,
        "artifact": payload["artifact"],
        "latest_proof_status": proof.get("status") if isinstance(proof, dict) else None,
        "latest_scan_once_observed": proof.get("scan_once_observed") if isinstance(proof, dict) else None,
        "latest_scan_hz_observed": proof.get("scan_hz_observed") if isinstance(proof, dict) else None,
        "latest_scan_hz_average_rate_hz": proof.get("scan_hz_average_rate_hz") if isinstance(proof, dict) else None,
        "latest_raw_packet_once_observed": proof.get("raw_packet_once_observed") if isinstance(proof, dict) else None,
        "latest_tf_observed": proof.get("tf_observed") if isinstance(proof, dict) else None,
        "latest_all_required_observations_observed": proof.get("all_required_observations_observed") if isinstance(proof, dict) else None,
        "latest_required_observations": compact_required_observations,
        "readback_sends_commands": False,
        "sends_commands": False,
        "sends_motion_commands": False,
        "robot_control_executed": False,
        "delivery_success": False,
        "hil_pass": False,
        "safe_to_control": False,
        "primary_actions_enabled": False,
    }


def summarize_lidar_raw_packet_proof_latest_artifact(path: str) -> dict[str, Any]:
    """status 里摘要 raw packet artifact；只读文件，禁止串口和启动命令。"""
    endpoint = ROUTE_PATHS["radar_raw_packet_proof_latest"]
    generated_at_ms = now_ms()
    stale_after_ms = DEFAULT_FEEDBACK_SAMPLES_STALE_AFTER_MS
    artifact = {
        **lidar_raw_packet_proof_artifact_info(path),
        "ok": False,
        "status": "unknown",
    }
    summary: dict[str, Any] = {
        "schema": f"{SCHEMA}.lidar_raw_packet_proof_latest_summary",
        "generated_at_ms": generated_at_ms,
        "endpoint": endpoint,
        "artifact": artifact,
        "latest_proof_status": None,
        "raw_bytes_observed": None,
        "sync_header_observed": None,
        "packet_parse_ok": None,
        "points_observed": None,
        "bytes_read": None,
        "sync_header_count": None,
        "packets_parse_ok": None,
        "points_total": None,
        "latest_raw_bytes_observed": None,
        "latest_sync_header_observed": None,
        "latest_packet_parse_ok": None,
        "latest_points_observed": None,
        "latest_bytes_read": None,
        "latest_sync_header_count": None,
        "latest_packets_parse_ok": None,
        "latest_points_total": None,
        "freshness": {
            "status": "unknown",
            "age_seconds": None,
            "stale_after_ms": stale_after_ms,
            "basis": "artifact_mtime_only_material_freshness_not_hil_or_safe_to_control",
        },
        "readback_sends_commands": False,
        "sends_commands": False,
        "sends_lidar_start_command": False,
        "sends_motion_commands": False,
        "opens_lidar_serial": False,
        "starts_ros2": False,
        "calls_base_manual": False,
        "robot_control_executed": False,
        "delivery_success": False,
        "hil_pass": False,
        "safe_to_control": False,
        "primary_actions_enabled": False,
    }
    try:
        stat_result = Path(path).stat()
    except FileNotFoundError:
        artifact.update({"ok": False, "status": "missing"})
        summary["freshness"]["status"] = "missing"
        return summary
    except OSError as exc:
        artifact.update({"ok": False, "status": "read_failed", "error": compact_error(exc)})
        summary["freshness"]["status"] = "read_failed"
        return summary

    mtime_ms = int(stat_result.st_mtime_ns / 1_000_000)
    age_ms = max(0, generated_at_ms - mtime_ms)
    artifact.update({"mtime_ms": mtime_ms, "age_ms": age_ms})
    # freshness 只表达 artifact 文件年龄，不能被 PC 解读成 HIL 或可控状态。
    summary["freshness"]["age_seconds"] = round(age_ms / 1000.0, 3)
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        artifact.update({"ok": False, "status": "read_failed", "error": compact_error(exc)})
        summary["freshness"]["status"] = "read_failed"
        return summary
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        artifact.update({"ok": False, "status": "bad_json", "bytes_read": len(raw.encode("utf-8")), "error": compact_error(exc)})
        summary["freshness"]["status"] = "bad_json"
        return summary
    if not isinstance(parsed, dict):
        artifact.update({"ok": False, "status": "json_not_object", "bytes_read": len(raw.encode("utf-8"))})
        summary["freshness"]["status"] = "json_not_object"
        return summary

    updated_at_ms = parsed.get("generated_at_ms")
    if isinstance(updated_at_ms, int):
        artifact["updated_at_ms"] = updated_at_ms
    proof = parsed.get("proof", {}) if isinstance(parsed.get("proof"), dict) else {}
    packet_stats = parsed.get("packet_stats", {}) if isinstance(parsed.get("packet_stats"), dict) else {}
    artifact.update({"ok": True, "status": "loaded", "bytes_read": len(raw.encode("utf-8"))})
    raw_bytes_observed = proof.get("raw_bytes_observed")
    sync_header_observed = proof.get("sync_header_observed")
    packet_parse_ok = proof.get("packet_parse_ok")
    points_observed = proof.get("points_observed")
    bytes_read = packet_stats.get("bytes_read")
    sync_header_count = packet_stats.get("sync_header_count")
    packets_parse_ok = packet_stats.get("packets_parse_ok")
    points_total = packet_stats.get("points_total")
    summary["freshness"]["status"] = freshness_from_age(age_ms, stale_after_ms)
    summary.update(
        {
            "latest_proof_status": proof.get("status"),
            "raw_bytes_observed": raw_bytes_observed,
            "sync_header_observed": sync_header_observed,
            "packet_parse_ok": packet_parse_ok,
            "points_observed": points_observed,
            "bytes_read": bytes_read,
            "sync_header_count": sync_header_count,
            "packets_parse_ok": packets_parse_ok,
            "points_total": points_total,
            "latest_raw_bytes_observed": raw_bytes_observed,
            "latest_sync_header_observed": sync_header_observed,
            "latest_packet_parse_ok": packet_parse_ok,
            "latest_points_observed": points_observed,
            "latest_bytes_read": bytes_read,
            "latest_sync_header_count": sync_header_count,
            "latest_packets_parse_ok": packets_parse_ok,
            "latest_points_total": points_total,
        }
    )
    return summary


def feedback_samples_summary_artifact_status(path: str) -> dict[str, Any]:
    """status summary 只暴露 artifact 配置来源，避免调用 latest GET 或串口路径。"""
    return {
        **artifact_path_info(path),
        "ok": False,
        "status": "unknown",
    }


def freshness_from_age(age_ms: int | None, stale_after_ms: int) -> str:
    """freshness 只是材料文件年龄，不代表 ACK、HIL 或 safe-to-control。"""
    if age_ms is None:
        return "unknown"
    if age_ms <= stale_after_ms:
        return "fresh"
    return "stale"


def summarize_feedback_samples_latest_artifact(
    path: str,
    stale_after_ms: int = DEFAULT_FEEDBACK_SAMPLES_STALE_AFTER_MS,
) -> dict[str, Any]:
    """只用 stat/read_text/json.loads 生成 latest artifact 摘要，禁止触发硬件。"""
    endpoint = ROUTE_PATHS["base_feedback_samples_latest"]
    artifact = feedback_samples_summary_artifact_status(path)
    generated_at_ms = now_ms()
    stale_after_ms = max(0, int(stale_after_ms))
    base_summary: dict[str, Any] = {
        "schema": f"{SCHEMA}.base_feedback_samples_latest_summary",
        "generated_at_ms": generated_at_ms,
        "endpoint": endpoint,
        "artifact": artifact,
        "freshness": {
            "status": "unknown",
            "stale_after_ms": stale_after_ms,
            "basis": "artifact_mtime_only_material_freshness_not_hil_or_safe_to_control",
        },
        "latest_t1001_observed_count": None,
        "latest_all_samples_observed_t1001": None,
        "readback_sends_commands": False,
        "sends_commands": False,
        "sends_motion_commands": False,
        "robot_control_executed": False,
        "delivery_success": False,
        "hil_pass": False,
        "safe_to_control": False,
        "primary_actions_enabled": False,
    }
    try:
        stat_result = Path(path).stat()
    except FileNotFoundError:
        artifact.update({"ok": False, "status": "missing"})
        base_summary["freshness"]["status"] = "missing"
        return base_summary
    except OSError as exc:
        artifact.update({"ok": False, "status": "read_failed", "error": compact_error(exc)})
        base_summary["freshness"]["status"] = "read_failed"
        return base_summary

    mtime_ms = int(stat_result.st_mtime_ns / 1_000_000)
    age_ms = max(0, generated_at_ms - mtime_ms)
    artifact.update({"mtime_ms": mtime_ms, "age_ms": age_ms})
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        artifact.update({"ok": False, "status": "read_failed", "error": compact_error(exc)})
        base_summary["freshness"]["status"] = "read_failed"
        return base_summary
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        artifact.update({"ok": False, "status": "bad_json", "bytes_read": len(raw.encode("utf-8")), "error": compact_error(exc)})
        base_summary["freshness"]["status"] = "bad_json"
        return base_summary
    if not isinstance(parsed, dict):
        artifact.update({"ok": False, "status": "json_not_object", "bytes_read": len(raw.encode("utf-8"))})
        base_summary["freshness"]["status"] = "json_not_object"
        return base_summary

    updated_at_ms = parsed.get("generated_at_ms")
    if not isinstance(updated_at_ms, int):
        updated_at_ms = parsed.get("artifact", {}).get("written_at_ms") if isinstance(parsed.get("artifact"), dict) else None
    if isinstance(updated_at_ms, int):
        artifact["updated_at_ms"] = updated_at_ms
    artifact.update({"ok": True, "status": "loaded", "bytes_read": len(raw.encode("utf-8"))})
    base_summary["freshness"]["status"] = freshness_from_age(age_ms, stale_after_ms)
    base_summary["latest_t1001_observed_count"] = parsed.get("t1001_observed_count")
    base_summary["latest_all_samples_observed_t1001"] = parsed.get("all_samples_observed_t1001")
    return base_summary


def atomic_write_json_artifact(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    """用同目录临时文件 + replace，避免运营侧读到半截 JSON。"""
    destination = Path(path)
    temp_path: Path | None = None
    try:
        if destination.parent and str(destination.parent) not in ("", "."):
            destination.parent.mkdir(parents=True, exist_ok=True)
        temp_path = destination.with_name(f".{destination.name}.{os.getpid()}.{now_ms()}.tmp")
        encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        with temp_path.open("wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, destination)
        try:
            # 目录 fsync 让 replace 元数据尽量落盘；不支持的平台只记录成功写入。
            directory_fd = os.open(str(destination.parent or Path(".")), os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError:
            pass
        return {"ok": True, "path": str(destination), "bytes_written": len(encoded), "method": "atomic_replace"}
    except Exception as exc:  # noqa: BLE001 - artifact 失败不能让非运动采样被包装成成功落盘。
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
        return {"ok": False, "path": str(destination), "error": compact_error(exc), "method": "atomic_replace"}


def persist_feedback_samples_artifact(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    """把 latest 采样结果落成可回放材料；写失败也必须结构化返回。"""
    storable = dict(payload)
    storable["artifact"] = {
        **artifact_path_info(path),
        "written_at_ms": now_ms(),
        "write": {"ok": True, "method": "atomic_replace"},
    }
    write_result = atomic_write_json_artifact(path, storable)
    storable["artifact"]["write"] = write_result
    return storable


def build_latest_readback_payload(path: str, artifact_status: dict[str, Any], latest_result: dict[str, Any] | None) -> dict[str, Any]:
    """latest 回放只描述文件读取结果，历史 payload 放在 latest_result 里。"""
    return {
        "schema": f"{SCHEMA}.base_feedback_samples_latest_result",
        "generated_at_ms": now_ms(),
        "artifact": artifact_status,
        "latest_result": latest_result,
        "latest_endpoint_path": ROUTE_PATHS["base_feedback_samples_latest"],
        "readback_sends_commands": False,
        "safe_to_control": False,
        "sends_commands": False,
        "sends_motion_commands": False,
        "robot_control_executed": False,
        "delivery_success": False,
        "hil_pass": False,
        "primary_actions_enabled": False,
    }


def read_feedback_samples_latest_artifact(path: str) -> tuple[int, dict[str, Any]]:
    """只读 artifact，不打开 serial、不 import pyserial、不触发任何 T=130/T=1。"""
    artifact = artifact_path_info(path)
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        artifact.update({"ok": False, "status": "missing", "error": {"type": "FileNotFoundError", "message": "latest feedback samples artifact is missing"}})
        return 404, build_latest_readback_payload(path, artifact, None)
    except OSError as exc:
        artifact.update({"ok": False, "status": "read_failed", "error": compact_error(exc)})
        return 500, build_latest_readback_payload(path, artifact, None)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        artifact.update({"ok": False, "status": "bad_json", "error": compact_error(exc)})
        return 422, build_latest_readback_payload(path, artifact, None)
    if not isinstance(parsed, dict):
        artifact.update({"ok": False, "status": "json_not_object", "error": {"type": "ValueError", "message": "latest artifact JSON root is not an object"}})
        return 422, build_latest_readback_payload(path, artifact, None)
    artifact.update({"ok": True, "status": "loaded", "bytes_read": len(raw.encode("utf-8"))})
    return 200, build_latest_readback_payload(path, artifact, parsed)


def feedback_request_status(
    *,
    serial_open_ok: bool,
    serial_write_ok: bool,
    t1001_observed: bool,
    import_error: str | None,
    read_error: dict[str, str] | None,
) -> str:
    """把串口阶段结果压成稳定机器字段，便于 OKR/HIL 材料做保守判定。"""
    if import_error:
        return "pyserial_unavailable"
    if not serial_open_ok:
        return "serial_not_opened"
    if not serial_write_ok:
        return "write_failed"
    if read_error:
        return "read_error"
    if t1001_observed:
        return "observed"
    return "not_observed_after_t130"


def request_base_feedback_once(
    port: str,
    baudrate: int,
    *,
    read_timeout_s: float = DEFAULT_FEEDBACK_READ_TIMEOUT_S,
    read_window_s: float = DEFAULT_FEEDBACK_READ_WINDOW_S,
) -> dict[str, Any]:
    """显式发送一次 vendor T=130，并短窗口读取换行 JSON；这里绝不发运动命令。"""
    read_timeout_s = clamp_float(read_timeout_s, DEFAULT_FEEDBACK_READ_TIMEOUT_S, 0.01, MAX_FEEDBACK_READ_TIMEOUT_S)
    read_window_s = clamp_float(read_window_s, DEFAULT_FEEDBACK_READ_WINDOW_S, 0.01, MAX_FEEDBACK_READ_WINDOW_S)
    serial_module, import_error = load_serial_module()
    serial_open: dict[str, Any] = {"ok": False, "port": port, "baudrate": baudrate, "timeout_s": read_timeout_s}
    serial_write: dict[str, Any] = {"ok": False, "command": BASE_FEEDBACK_REQUEST_COMMAND}
    serial_read: dict[str, Any] = {"ok": False, "window_s": read_window_s, "error": None}
    read_line_count = 0
    parsed_json_count = 0
    invalid_json_count = 0
    observed_feedback_types: list[int] = []
    serial_obj = None

    if serial_module is None:
        status = feedback_request_status(
            serial_open_ok=False,
            serial_write_ok=False,
            t1001_observed=False,
            import_error=import_error,
            read_error=None,
        )
        return build_base_feedback_payload(
            port=port,
            baudrate=baudrate,
            read_timeout_s=read_timeout_s,
            read_window_s=read_window_s,
            serial_open=serial_open,
            serial_write={"ok": False, "command": BASE_FEEDBACK_REQUEST_COMMAND, "error": {"type": "pyserial_unavailable", "message": import_error or "missing"}},
            serial_read=serial_read,
            read_line_count=0,
            parsed_json_count=0,
            invalid_json_count=0,
            observed_feedback_types=[],
            t1001_feedback_status=status,
        )

    try:
        serial_obj = serial_module.Serial(port=port, baudrate=baudrate, timeout=read_timeout_s)
        serial_open["ok"] = True
    except Exception as exc:  # noqa: BLE001 - 现场串口打开失败必须结构化返回。
        serial_open["error"] = compact_error(exc)
        status = feedback_request_status(
            serial_open_ok=False,
            serial_write_ok=False,
            t1001_observed=False,
            import_error=None,
            read_error=None,
        )
        return build_base_feedback_payload(
            port=port,
            baudrate=baudrate,
            read_timeout_s=read_timeout_s,
            read_window_s=read_window_s,
            serial_open=serial_open,
            serial_write=serial_write,
            serial_read=serial_read,
            read_line_count=0,
            parsed_json_count=0,
            invalid_json_count=0,
            observed_feedback_types=[],
            t1001_feedback_status=status,
        )

    try:
        frame = (json.dumps(BASE_FEEDBACK_REQUEST_COMMAND, separators=(",", ":")) + "\n").encode("utf-8")
        serial_write["bytes_written"] = serial_obj.write(frame)
        serial_write["ok"] = True
    except Exception as exc:  # noqa: BLE001 - 写失败时不能继续包装成 ACK 探测成功。
        serial_write["error"] = compact_error(exc)

    if serial_write["ok"]:
        deadline = time.monotonic() + read_window_s
        try:
            while time.monotonic() < deadline:
                raw_line = serial_obj.readline()
                if not raw_line:
                    continue
                read_line_count += 1
                try:
                    decoded = raw_line.decode("utf-8").strip()
                    parsed = json.loads(decoded)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    invalid_json_count += 1
                    continue
                if not isinstance(parsed, dict):
                    invalid_json_count += 1
                    continue
                parsed_json_count += 1
                feedback_type = parsed.get("T")
                if isinstance(feedback_type, int):
                    observed_feedback_types.append(feedback_type)
        except Exception as exc:  # noqa: BLE001 - 读阶段错误独立暴露，不改写 open/write 结果。
            serial_read["error"] = compact_error(exc)
        else:
            serial_read["ok"] = True

    t1001_observed = BASE_FEEDBACK_ID in observed_feedback_types
    status = feedback_request_status(
        serial_open_ok=bool(serial_open.get("ok")),
        serial_write_ok=bool(serial_write.get("ok")),
        t1001_observed=t1001_observed,
        import_error=None,
        read_error=serial_read.get("error"),
    )
    if serial_obj is not None:
        try:
            serial_obj.close()
        except Exception:
            pass
    return build_base_feedback_payload(
        port=port,
        baudrate=baudrate,
        read_timeout_s=read_timeout_s,
        read_window_s=read_window_s,
        serial_open=serial_open,
        serial_write=serial_write,
        serial_read=serial_read,
        read_line_count=read_line_count,
        parsed_json_count=parsed_json_count,
        invalid_json_count=invalid_json_count,
        observed_feedback_types=sorted(set(observed_feedback_types)),
        t1001_feedback_status=status,
    )


def build_base_feedback_payload(
    *,
    port: str,
    baudrate: int,
    read_timeout_s: float,
    read_window_s: float,
    serial_open: dict[str, Any],
    serial_write: dict[str, Any],
    serial_read: dict[str, Any],
    read_line_count: int,
    parsed_json_count: int,
    invalid_json_count: int,
    observed_feedback_types: list[int],
    t1001_feedback_status: str,
) -> dict[str, Any]:
    """统一反馈请求输出；即使看到 T=1001，也只能作为材料而不是 HIL pass。"""
    t1001_observed = BASE_FEEDBACK_ID in observed_feedback_types
    return {
        "schema": f"{SCHEMA}.base_feedback_request_result",
        "generated_at_ms": now_ms(),
        "vendor_sources": VENDOR_SOURCES,
        "port": port,
        "baudrate": baudrate,
        "request": {
            "method": "POST",
            "endpoint": "/api/base/feedback-request",
            "command": BASE_FEEDBACK_REQUEST_COMMAND,
            "read_timeout_s": read_timeout_s,
            "read_window_s": read_window_s,
        },
        "serial_open": serial_open,
        "serial_write": serial_write,
        "serial_read": serial_read,
        "read_line_count": read_line_count,
        "parsed_json_count": parsed_json_count,
        "invalid_json_count": invalid_json_count,
        "observed_feedback_types": observed_feedback_types,
        "t1001_feedback_status": t1001_feedback_status,
        "feedback_ack": {
            "t1001_observed": t1001_observed,
            "robot_ack_connected": False,
            "reason": (
                "T=1001 observed after explicit T=130 request; this is vendor feedback material, not project robot ACK or HIL proof"
                if t1001_observed
                else "T=1001 not observed after explicit T=130 request; robot ACK/HIL remains unproven"
            ),
        },
        "blocked_commands_not_sent": BLOCKED_BASE_FEEDBACK_COMMANDS,
        "safe_to_control": False,
        "sends_commands": bool(serial_write.get("ok")),
        "sends_motion_commands": False,
        "robot_control_executed": False,
        "delivery_success": False,
        "hil_pass": False,
        "primary_actions_enabled": False,
    }


def build_base_feedback_samples_payload(
    *,
    port: str,
    baudrate: int,
    sample_count: int,
    sample_interval_s: float,
    read_timeout_s: float,
    read_window_s: float,
    samples: list[dict[str, Any]],
) -> dict[str, Any]:
    """多样本只聚合 T=130 反馈材料，不把重复观察包装成运动控制许可。"""
    observed_type_set: set[int] = set()
    t1001_observed_count = 0
    sample_results: list[dict[str, Any]] = []
    for index, sample in enumerate(samples, start=1):
        observed_types = [
            item for item in sample.get("observed_feedback_types", [])
            if isinstance(item, int)
        ]
        observed_type_set.update(observed_types)
        sample_t1001_observed = bool(sample.get("feedback_ack", {}).get("t1001_observed"))
        if sample_t1001_observed:
            t1001_observed_count += 1
        # 每个 sample 保留完整阶段结果，方便远端材料回放和失败定位。
        sample_results.append(
            {
                "sample_index": index,
                "schema": sample.get("schema"),
                "serial_open": sample.get("serial_open"),
                "serial_write": sample.get("serial_write"),
                "serial_read": sample.get("serial_read"),
                "read_line_count": sample.get("read_line_count"),
                "parsed_json_count": sample.get("parsed_json_count"),
                "invalid_json_count": sample.get("invalid_json_count"),
                "observed_feedback_types": observed_types,
                "t1001_feedback_status": sample.get("t1001_feedback_status"),
                "feedback_ack": sample.get("feedback_ack"),
                "safe_to_control": False,
                "sends_motion_commands": False,
                "robot_control_executed": False,
                "delivery_success": False,
                "hil_pass": False,
            }
        )
    all_samples_observed = bool(samples) and t1001_observed_count == len(samples)
    partial_samples_observed = 0 < t1001_observed_count < len(samples)
    return {
        "schema": f"{SCHEMA}.base_feedback_samples_result",
        "generated_at_ms": now_ms(),
        "vendor_sources": VENDOR_SOURCES,
        "port": port,
        "baudrate": baudrate,
        "request": {
            "method": "POST",
            "endpoint": "/api/base/feedback-samples",
            "command": BASE_FEEDBACK_REQUEST_COMMAND,
            "sample_count": sample_count,
            "sample_interval_s": sample_interval_s,
            "read_timeout_s": read_timeout_s,
            "read_window_s": read_window_s,
        },
        "requested_sample_count": sample_count,
        "completed_sample_count": len(samples),
        "samples": sample_results,
        "t1001_observed_count": t1001_observed_count,
        "observed_feedback_types": sorted(observed_type_set),
        "all_samples_observed_t1001": all_samples_observed,
        "partial_samples_observed_t1001": partial_samples_observed,
        "feedback_ack": {
            "t1001_observed": bool(t1001_observed_count),
            "robot_ack_connected": False,
            "reason": (
                f"T=1001 observed in {t1001_observed_count}/{len(samples)} samples; this is vendor feedback material, not project robot ACK or HIL proof"
                if t1001_observed_count
                else "T=1001 not observed in completed samples; robot ACK/HIL remains unproven"
            ),
        },
        "blocked_commands_not_sent": BLOCKED_BASE_FEEDBACK_COMMANDS,
        "safe_to_control": False,
        "sends_commands": bool(samples),
        "sends_motion_commands": False,
        "robot_control_executed": False,
        "delivery_success": False,
        "hil_pass": False,
        "primary_actions_enabled": False,
    }


def skipped_manual_feedback_payload(port: str, baudrate: int, reason: str) -> dict[str, Any]:
    """manual 写入失败时不追加 T=130，避免反馈读取挤占停车兜底后的故障定位。"""
    return {
        "schema": f"{SCHEMA}.base_manual_feedback_skipped",
        "generated_at_ms": now_ms(),
        "vendor_sources": VENDOR_SOURCES,
        "port": port,
        "baudrate": baudrate,
        "request": {
            "method": "POST",
            "endpoint": "/api/base/manual",
            "command": BASE_FEEDBACK_REQUEST_COMMAND,
            "attempted": False,
            "reason": reason,
        },
        "serial_open": None,
        "serial_write": None,
        "serial_read": None,
        "read_line_count": 0,
        "parsed_json_count": 0,
        "invalid_json_count": 0,
        "observed_feedback_types": [],
        "t1001_feedback_status": reason,
        "feedback_ack": {
            "t1001_observed": False,
            "robot_ack_connected": False,
            "reason": "manual direction/stop write failed; T=130 feedback request skipped to preserve fail-closed evidence",
        },
        "safe_to_control": False,
        "sends_commands": False,
        "sends_motion_commands": False,
        "robot_control_executed": False,
        "delivery_success": False,
        "hil_pass": False,
        "primary_actions_enabled": False,
    }


def build_stop_payload(port: str, baudrate: int) -> dict[str, Any]:
    """停车接口必须以写入结果为准，不能把 HTTP 调用成功当成底盘已停车。"""
    stop_result = write_serial_json(port, baudrate, {"T": 1, "L": 0, "R": 0})
    return {
        "schema": f"{SCHEMA}.base_stop_result",
        "generated_at_ms": now_ms(),
        "stop_result": stop_result,
        "serial_write_failures": [] if stop_result.get("ok") else [stop_result.get("error")],
        "feedback_ack": t1001_boundary("stop write does not prove T=1001 or ACK"),
        "safe_to_control": False,
        "sends_commands": True,
        "robot_control_executed": bool(stop_result.get("ok")),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


async def fetch_json(url: str, method: str = "GET", payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    """代理 camera smoke JSON；远端异常压成结构化错误，不影响统一 API 存活。"""
    from aiohttp import ClientSession, ClientTimeout

    try:
        async with ClientSession(timeout=ClientTimeout(total=6)) as session:
            async with session.request(method, url, json=payload) as response:
                text = await response.text()
                try:
                    parsed = json.loads(text) if text else {}
                except json.JSONDecodeError:
                    parsed = {"error": "remote_non_json_response", "body_preview": text[:200]}
                return response.status, parsed if isinstance(parsed, dict) else {"error": "remote_json_not_object"}
    except Exception as exc:  # noqa: BLE001 - camera 子服务不在线时主 API 仍要可查。
        return 502, {"error": "camera_proxy_failed", "detail": compact_error(exc)}


class UpperRobotApi:
    """把上位机各硬件入口收敛到一个 HTTP API，PC 不再分散猜端口。"""

    def __init__(
        self,
        camera_base_url: str,
        base_port: str,
        base_baudrate: int,
        max_speed: float,
        feedback_samples_artifact_path: str = DEFAULT_FEEDBACK_SAMPLES_ARTIFACT_PATH,
        lidar_scan_proof_artifact_path: str = DEFAULT_LIDAR_SCAN_PROOF_ARTIFACT_PATH,
        lidar_raw_packet_proof_artifact_path: str = DEFAULT_LIDAR_RAW_PACKET_PROOF_ARTIFACT_PATH,
        map_artifact_dir: str = DEFAULT_MAP_ARTIFACT_DIR,
        map_lifecycle_proof_artifact_path: str = DEFAULT_MAP_LIFECYCLE_PROOF_ARTIFACT_PATH,
        localization_artifact_path: str = DEFAULT_LOCALIZATION_ARTIFACT_PATH,
        nav2_lifecycle_artifact_path: str = DEFAULT_NAV2_LIFECYCLE_ARTIFACT_PATH,
        elevator_status_artifact_path: str = DEFAULT_ELEVATOR_STATUS_ARTIFACT_PATH,
        radar_start_command: str | None = None,
        radar_stop_command: str | None = None,
        map_start_command: str | None = None,
        map_reset_command: str | None = None,
        map_save_command: str | None = None,
        map_load_command: str | None = None,
        localize_reset_command: str | None = None,
        nav2_start_command: str | None = None,
        nav2_stop_command: str | None = None,
    ) -> None:
        self.camera_base_url = camera_base_url.rstrip("/")
        self.base_port = base_port
        self.base_baudrate = base_baudrate
        self.max_speed = max_speed
        self.feedback_samples_artifact_path = feedback_samples_artifact_path
        self.lidar_scan_proof_artifact_path = lidar_scan_proof_artifact_path
        self.lidar_raw_packet_proof_artifact_path = lidar_raw_packet_proof_artifact_path
        self.map_artifact_dir = map_artifact_dir
        self.map_lifecycle_proof_artifact_path = map_lifecycle_proof_artifact_path
        self.localization_artifact_path = localization_artifact_path
        self.nav2_lifecycle_artifact_path = nav2_lifecycle_artifact_path
        self.elevator_status_artifact_path = elevator_status_artifact_path
        self.radar_start_command = radar_start_command
        self.radar_stop_command = radar_stop_command
        self.map_start_command = map_start_command
        self.map_reset_command = map_reset_command
        self.map_save_command = map_save_command
        self.map_load_command = map_load_command
        self.localize_reset_command = localize_reset_command
        self.nav2_start_command = nav2_start_command
        self.nav2_stop_command = nav2_stop_command

    def base_status(self) -> dict[str, Any]:
        """底盘状态只证明写入口配置和设备存在，不伪造 T=1001 ACK。"""
        serial_module, import_error = load_serial_module()
        port_info = describe_path(self.base_port)
        return {
            "schema": f"{SCHEMA}.base_status",
            "generated_at_ms": now_ms(),
            "vendor_sources": VENDOR_SOURCES,
            "port": self.base_port,
            "baudrate": self.base_baudrate,
            "port_info": port_info,
            "pyserial_available": serial_module is not None,
            "pyserial_error": import_error,
            "write_control_available": bool(port_info["exists"] and serial_module is not None),
            "feedback_ack": {
                "t1001_observed": False,
                "robot_ack_connected": False,
                "reason": "T=130 on /dev/ttyS5 did not return T=1001 in current evidence",
            },
            "feedback_samples_latest": summarize_feedback_samples_latest_artifact(
                self.feedback_samples_artifact_path,
                DEFAULT_FEEDBACK_SAMPLES_STALE_AFTER_MS,
            ),
            "control_policy": {
                "mode": "low_speed_pulse_with_auto_stop",
                "max_speed": self.max_speed,
                "max_pulse_ms": MAX_PULSE_MS,
                "stop_command": {"T": 1, "L": 0, "R": 0},
            },
            "sends_commands": False,
            **proof_flags(),
        }

    def radar_status(self) -> dict[str, Any]:
        """雷达当前先合并设备状态，真实 /scan 仍需 ROS2/LiDAR 节点证明。"""
        candidates = list_candidates(["/dev/lidar", "/dev/ttyACM*", "/dev/serial/by-id/*", "/dev/serial/by-path/*"])
        tty_acm0 = describe_path("/dev/ttyACM0")
        lidar_observed = bool(tty_acm0["exists"])
        return {
            "schema": f"{SCHEMA}.radar_status",
            "generated_at_ms": now_ms(),
            "scan_status": "not_proven",
            "pointcloud_fabricated": False,
            "dev_lidar": describe_path("/dev/lidar"),
            "observed_lidar_port": "/dev/ttyACM0" if lidar_observed else None,
            "observed_lidar_port_info": tty_acm0,
            "baudrate": 150000,
            "start_command_hex": "a5 60",
            "stop_command_hex": "a5 00 a5 65 a5 65",
            "candidates": candidates,
            "ros2": {
                "driver": "ros2_trashbot_hardware lidar_driver",
                "launch": "ros2 launch ros2_trashbot_bringup learn.launch.py lidar_enabled:=true lidar_serial_port:=/dev/ttyACM0 lidar_serial_baudrate:=150000 lidar_publish_raw_packets:=true",
                "scan_topic": "/scan",
                "raw_packet_topic": "/lidar/raw_packet",
                "frame_id": "laser_frame",
            },
            "scan_proof_latest": summarize_lidar_scan_proof_latest_artifact(self.lidar_scan_proof_artifact_path),
            "raw_packet_proof_latest": summarize_lidar_raw_packet_proof_latest_artifact(
                self.lidar_raw_packet_proof_artifact_path
            ),
            "controls": {
                "start": {
                    "endpoint": ROUTE_PATHS["radar_start"],
                    "command": command_config_info("ROBER_RADAR_START_COMMAND", self.radar_start_command),
                },
                "stop": {
                    "endpoint": ROUTE_PATHS["radar_stop"],
                    "command": command_config_info("ROBER_RADAR_STOP_COMMAND", self.radar_stop_command),
                },
            },
            "blocked_reasons": [
                *(["ttyACM0_lidar_not_present"] if not lidar_observed else []),
                "ros2_lidar_scan_not_connected",
                "scan_continuity_not_observed",
            ],
            "sends_commands": False,
            **proof_flags(),
        }

    def radar_control(self, action: str) -> dict[str, Any]:
        """雷达 start/stop 只允许走 LiDAR/ROS2 driver 命令，不触碰底盘 UART。"""
        if action == "start":
            endpoint = ROUTE_PATHS["radar_start"]
            command_env = "ROBER_RADAR_START_COMMAND"
            command = self.radar_start_command
        elif action == "stop":
            endpoint = ROUTE_PATHS["radar_stop"]
            command_env = "ROBER_RADAR_STOP_COMMAND"
            command = self.radar_stop_command
        else:
            return software_guard_payload(
                schema_suffix="radar_control_result",
                action=action,
                endpoint="/api/radar/{action}",
                extra={"error": {"type": "unsupported_radar_action", "message": "action must be start or stop"}},
            )
        command_result = run_configured_command(command)
        return software_guard_payload(
            schema_suffix="radar_control_result",
            action=f"radar_{action}",
            endpoint=endpoint,
            command_env=command_env,
            command=command,
            command_result=command_result,
            artifact=lidar_scan_proof_artifact_info(self.lidar_scan_proof_artifact_path),
            extra={
                "scope": "lidar_ros2_driver_only",
                "base_uart_touched": False,
                "lidar_start_stop_only": True,
                "transition_to_proven": [
                    "ros2 topic echo --once /scan",
                    "ros2 topic hz /scan",
                    "artifact update at lidar_scan_proof_latest_artifact.path",
                ],
            },
        )

    def map_status(self) -> dict[str, Any]:
        """地图生命周期状态只列出软件入口和 artifact 目录，不读取 ROS graph。"""
        return {
            "schema": f"{SCHEMA}.map_lifecycle_status",
            "generated_at_ms": now_ms(),
            "artifact": map_artifact_info(self.map_artifact_dir),
            "proof_latest": summarize_map_lifecycle_latest_artifact(self.map_lifecycle_proof_artifact_path),
            "routes": {
                "start": ROUTE_PATHS["map_start"],
                "reset": ROUTE_PATHS["map_reset"],
                "save": ROUTE_PATHS["map_save"],
                "load": ROUTE_PATHS["map_load"],
                "list": ROUTE_PATHS["map_list"],
                "proof_latest": ROUTE_PATHS["map_proof_latest"],
                "localize_reset": ROUTE_PATHS["localize_reset"],
                "localize_proof_latest": ROUTE_PATHS["localize_proof_latest"],
            },
            "commands": {
                "start": command_config_info("ROBER_MAP_START_COMMAND", self.map_start_command),
                "reset": command_config_info("ROBER_MAP_RESET_COMMAND", self.map_reset_command),
                "save": command_config_info("ROBER_MAP_SAVE_COMMAND", self.map_save_command),
                "load": command_config_info("ROBER_MAP_LOAD_COMMAND", self.map_load_command),
                "localize_reset": command_config_info("ROBER_LOCALIZE_RESET_COMMAND", self.localize_reset_command),
            },
            "runtime_entrypoints": {
                "learn_launch": "ros2 launch ros2_trashbot_bringup learn.launch.py lidar_enabled:=true lidar_serial_port:=/dev/ttyACM0",
                "save_service": "ros2 service call /trashbot/save_map std_srvs/srv/Trigger {}",
                "map_topic": "/map",
                "proof_artifact_path": self.map_lifecycle_proof_artifact_path,
            },
            "status": "not_proven",
            "software_guard": True,
            "not_proven": True,
            "sends_base_motion_commands": False,
            "uses_base_uart": False,
            "sends_commands": False,
            **proof_flags(),
        }

    def map_control(self, action: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """建图 lifecycle 先提供 HTTP 合同；默认不启动 ROS2，不伪造地图产物。"""
        body = body if isinstance(body, dict) else {}
        command_by_action = {
            "start": ("ROBER_MAP_START_COMMAND", self.map_start_command, ROUTE_PATHS["map_start"]),
            "reset": ("ROBER_MAP_RESET_COMMAND", self.map_reset_command, ROUTE_PATHS["map_reset"]),
            "save": ("ROBER_MAP_SAVE_COMMAND", self.map_save_command, ROUTE_PATHS["map_save"]),
            "load": ("ROBER_MAP_LOAD_COMMAND", self.map_load_command, ROUTE_PATHS["map_load"]),
        }
        if action not in command_by_action:
            return software_guard_payload(
                schema_suffix="map_lifecycle_result",
                action=action,
                endpoint="/api/map/{action}",
                artifact=map_artifact_info(self.map_artifact_dir),
                extra={"error": {"type": "unsupported_map_action", "message": "action must be start/reset/save/load"}},
            )
        command_env, command, endpoint = command_by_action[action]
        command_result = run_configured_command(command)
        return software_guard_payload(
            schema_suffix="map_lifecycle_result",
            action=f"map_{action}",
            endpoint=endpoint,
            command_env=command_env,
            command=command,
            command_result=command_result,
            artifact=map_artifact_info(self.map_artifact_dir),
            extra={
                "requested_map_name": body.get("map_name"),
                "requested_artifact_path": body.get("artifact_path"),
                "proof_artifact": map_lifecycle_proof_artifact_info(self.map_lifecycle_proof_artifact_path),
                "map_lifecycle_status": self.map_status(),
                "transition_to_proven": [
                    "/map once observed",
                    "map YAML/image or pbstream artifact exists",
                    "PC/upper API readback references the same artifact path",
                    f"GET {ROUTE_PATHS['map_proof_latest']} returns runtime material",
                ],
            },
        )

    def map_list(self) -> dict[str, Any]:
        """列出本地 map artifact 候选；文件存在仍不等于地图质量已验收。"""
        root = Path(self.map_artifact_dir)
        entries: list[dict[str, Any]] = []
        if root.exists() and root.is_dir():
            for pattern in ("*.yaml", "*.pgm", "*.pbstream"):
                for path in sorted(root.glob(pattern)):
                    try:
                        stat_result = path.stat()
                    except OSError as exc:
                        entries.append({"path": str(path), "ok": False, "error": compact_error(exc)})
                        continue
                    entries.append(
                        {
                            "path": str(path),
                            "name": path.name,
                            "suffix": path.suffix,
                            "size_bytes": stat_result.st_size,
                            "mtime_ms": int(stat_result.st_mtime_ns / 1_000_000),
                        }
                    )
        return software_guard_payload(
            schema_suffix="map_list_result",
            action="map_list",
            endpoint=ROUTE_PATHS["map_list"],
            artifact=map_artifact_info(self.map_artifact_dir),
            extra={
                "artifact_dir_exists": root.exists(),
                "maps": entries,
                "map_count": len(entries),
                "command_result": {"mode": "read_only_local_files", "executed": False, "ok": root.exists()},
                "failure_reason": None if root.exists() else "map_artifact_dir_missing",
            },
        )

    def map_proof_latest(self) -> tuple[int, dict[str, Any]]:
        """只读最近一次 SLAM/map lifecycle proof，不能启动 SLAM 或保存地图。"""
        return read_runtime_artifact_latest(
            self.map_lifecycle_proof_artifact_path,
            artifact_info=map_lifecycle_proof_artifact_info(self.map_lifecycle_proof_artifact_path),
            schema_suffix="map_lifecycle_proof_latest",
            endpoint=ROUTE_PATHS["map_proof_latest"],
            boundary="software_guard_only_not_real_slam_map_or_nav2_consumption",
            source="map_lifecycle_runtime_artifact",
        )

    def localize_reset(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """定位 reset 合同预留 AMCL /initialpose；默认不发布 ROS2 pose。"""
        body = body if isinstance(body, dict) else {}
        command_result = run_configured_command(self.localize_reset_command)
        return software_guard_payload(
            schema_suffix="localization_reset_result",
            action="localize_reset",
            endpoint=ROUTE_PATHS["localize_reset"],
            command_env="ROBER_LOCALIZE_RESET_COMMAND",
            command=self.localize_reset_command,
            command_result=command_result,
            artifact=localization_artifact_info(self.localization_artifact_path),
            extra={
                "requested_pose": body.get("pose"),
                "target_ros2_topic": "/initialpose",
                "proof_artifact": localization_artifact_info(self.localization_artifact_path),
                "expected_runtime_proof": ["/amcl_pose", "tf map->base_link freshness", "pose timestamp freshness"],
                "transition_to_proven": [
                    "configured command publishes or calls ROS2 localization reset",
                    "AMCL pose observed after reset",
                    "artifact update at localization_artifact.path",
                    f"GET {ROUTE_PATHS['localize_proof_latest']} returns AMCL/TF material",
                ],
            },
        )

    def localize_proof_latest(self) -> tuple[int, dict[str, Any]]:
        """只读定位 runtime proof，避免 status 接口误发布 /initialpose。"""
        return read_runtime_artifact_latest(
            self.localization_artifact_path,
            artifact_info=localization_artifact_info(self.localization_artifact_path),
            schema_suffix="localization_proof_latest",
            endpoint=ROUTE_PATHS["localize_proof_latest"],
            boundary="software_guard_only_not_real_amcl_localization_reset",
            source="localization_runtime_artifact",
        )

    def nav2_status(self) -> dict[str, Any]:
        """Nav2 lifecycle 状态只读 artifact；真实 graph 查询由外部 collector 写材料。"""
        return {
            "schema": f"{SCHEMA}.nav2_lifecycle_status",
            "generated_at_ms": now_ms(),
            "status": "not_proven",
            "software_guard": True,
            "not_proven": True,
            "artifact": nav2_lifecycle_artifact_info(self.nav2_lifecycle_artifact_path),
            "proof_latest": summarize_nav2_lifecycle_latest_artifact(self.nav2_lifecycle_artifact_path),
            "routes": {
                "status": ROUTE_PATHS["nav2_status"],
                "start": ROUTE_PATHS["nav2_start"],
                "stop": ROUTE_PATHS["nav2_stop"],
            },
            "commands": {
                "start": command_config_info("ROBER_NAV2_START_COMMAND", self.nav2_start_command),
                "stop": command_config_info("ROBER_NAV2_STOP_COMMAND", self.nav2_stop_command),
            },
            "runtime_entrypoints": {
                "autonomous_launch": "ros2 launch ros2_trashbot_bringup autonomous.launch.py map_file:=<map.yaml>",
                "lifecycle_nodes_expected": ["map_server", "amcl", "planner_server", "controller_server"],
                "required_inputs": ["/scan", "map yaml/image", "tf map->base_link"],
            },
            **runtime_boundary_flags(),
            **proof_flags(),
        }

    def nav2_control(self, action: str) -> dict[str, Any]:
        """Nav2 start/stop 是配置命令入口；默认不启动 lifecycle manager。"""
        if action == "start":
            endpoint = ROUTE_PATHS["nav2_start"]
            command_env = "ROBER_NAV2_START_COMMAND"
            command = self.nav2_start_command
        elif action == "stop":
            endpoint = ROUTE_PATHS["nav2_stop"]
            command_env = "ROBER_NAV2_STOP_COMMAND"
            command = self.nav2_stop_command
        else:
            return software_guard_payload(
                schema_suffix="nav2_lifecycle_result",
                action=action,
                endpoint="/api/nav2/{action}",
                artifact=nav2_lifecycle_artifact_info(self.nav2_lifecycle_artifact_path),
                extra={"error": {"type": "unsupported_nav2_action", "message": "action must be start or stop"}},
            )
        command_result = run_configured_command(command)
        return software_guard_payload(
            schema_suffix="nav2_lifecycle_result",
            action=f"nav2_{action}",
            endpoint=endpoint,
            command_env=command_env,
            command=command,
            command_result=command_result,
            artifact=nav2_lifecycle_artifact_info(self.nav2_lifecycle_artifact_path),
            extra={
                "nav2_lifecycle_status": self.nav2_status(),
                "transition_to_proven": [
                    "map_server/amcl/planner/controller lifecycle states observed",
                    "/scan and map consumed by Nav2 stack",
                    "path generated or explicit blocked reason recorded",
                    f"artifact update at {self.nav2_lifecycle_artifact_path}",
                ],
            },
        )

    def elevator_status(self) -> dict[str, Any]:
        """电梯 status 将 OpenCV evidence 和状态机边界暴露给上层，默认不证明实景。"""
        return {
            "schema": f"{SCHEMA}.elevator_status",
            "generated_at_ms": now_ms(),
            "status": "not_proven",
            "software_guard": True,
            "not_proven": True,
            "artifact": elevator_status_artifact_info(self.elevator_status_artifact_path),
            "proof_latest": summarize_elevator_status_latest_artifact(self.elevator_status_artifact_path),
            "routes": {"status": ROUTE_PATHS["elevator_status"]},
            "expected_state_chain": [
                "waiting_elevator_open",
                "entering_elevator",
                "requesting_floor_help",
                "waiting_target_floor",
                "exiting_elevator",
                "manual_handoff_or_resume_delivery",
            ],
            "transition_to_proven": [
                "OpenCV evidence_ref points to real/controlled images",
                "task_orchestrator record keeps elevator phase and failure reason",
                "operator can see handoff/safe_to_exit status without claiming delivery_success",
            ],
            **runtime_boundary_flags(),
            **proof_flags(),
        }

    async def camera_health(self) -> tuple[int, dict[str, Any]]:
        """camera 子接口代理 8088 /health，并标注统一 API 来源。"""
        status, payload = await fetch_json(urljoin(self.camera_base_url + "/", "health"))
        payload["upper_api_proxy"] = True
        payload["upper_api_camera_base_url"] = self.camera_base_url
        return status, payload

    async def camera_devices(self) -> tuple[int, dict[str, Any]]:
        """camera 子接口代理 8088 /devices。"""
        status, payload = await fetch_json(urljoin(self.camera_base_url + "/", "devices"))
        payload["upper_api_proxy"] = True
        return status, payload

    async def camera_offer(self, offer: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        """camera WebRTC 信令只代理媒体 offer，不发送任何机器人控制。"""
        status, payload = await fetch_json(urljoin(self.camera_base_url + "/", "offer"), method="POST", payload=offer)
        payload["upper_api_proxy"] = True
        payload["safe_to_control"] = False
        payload["robot_control_executed"] = False
        return status, payload

    async def camera_peer_close(self, peer_id: str, body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        """释放 8088 active peer，避免 PC 页面刷新后摄像头被占用。"""
        if not peer_id or not all(char.isalnum() for char in peer_id):
            return 400, {"error": "peer_id_invalid", **proof_flags()}
        status, payload = await fetch_json(
            urljoin(self.camera_base_url + "/", f"peers/{peer_id}/close"),
            method="POST",
            payload=body,
        )
        payload["upper_api_proxy"] = True
        return status, payload

    async def unified_status(self) -> dict[str, Any]:
        """PC 首屏只拉一个状态接口即可获得 camera/radar/base 总览。"""
        camera_http_status, camera = await self.camera_health()
        return {
            "schema": f"{SCHEMA}.status",
            "generated_at_ms": now_ms(),
            "camera": {
                "http_status": camera_http_status,
                "status": camera.get("status", "not_loaded"),
                "video_source": camera.get("video_source", "not_loaded"),
                "base_url": self.camera_base_url,
                "offer_path": "/api/camera/offer",
            },
            "radar": self.radar_status(),
            "map": self.map_status(),
            "localization": {
                "schema": f"{SCHEMA}.localization_status",
                "generated_at_ms": now_ms(),
                "reset_endpoint": ROUTE_PATHS["localize_reset"],
                "proof_latest_endpoint": ROUTE_PATHS["localize_proof_latest"],
                "artifact": localization_artifact_info(self.localization_artifact_path),
                "proof_latest": summarize_localization_latest_artifact(self.localization_artifact_path),
                "command": command_config_info("ROBER_LOCALIZE_RESET_COMMAND", self.localize_reset_command),
                "status": "not_proven",
                "software_guard": True,
                "not_proven": True,
                "sends_commands": False,
                **proof_flags(),
            },
            "nav2": self.nav2_status(),
            "elevator": self.elevator_status(),
            "base": self.base_status(),
            "routes": dict(ROUTE_PATHS),
            "base_feedback_samples_latest_artifact": artifact_path_info(self.feedback_samples_artifact_path),
            "lidar_scan_proof_latest_artifact": lidar_scan_proof_artifact_info(self.lidar_scan_proof_artifact_path),
            "lidar_raw_packet_proof_latest_artifact": lidar_raw_packet_proof_artifact_info(
                self.lidar_raw_packet_proof_artifact_path
            ),
            "map_artifact": map_artifact_info(self.map_artifact_dir),
            "map_lifecycle_proof_artifact": map_lifecycle_proof_artifact_info(self.map_lifecycle_proof_artifact_path),
            "localization_artifact": localization_artifact_info(self.localization_artifact_path),
            "nav2_lifecycle_artifact": nav2_lifecycle_artifact_info(self.nav2_lifecycle_artifact_path),
            "elevator_status_artifact": elevator_status_artifact_info(self.elevator_status_artifact_path),
            "sends_commands": False,
            **proof_flags(),
        }

    async def base_feedback_request(self, body: dict[str, Any]) -> dict[str, Any]:
        """非运动反馈请求必须由显式 POST 触发，状态接口永远不自动探测。"""
        read_timeout_s = clamp_float(
            body.get("read_timeout_s"),
            DEFAULT_FEEDBACK_READ_TIMEOUT_S,
            0.01,
            MAX_FEEDBACK_READ_TIMEOUT_S,
        )
        read_window_s = clamp_float(
            body.get("read_window_s"),
            DEFAULT_FEEDBACK_READ_WINDOW_S,
            0.01,
            MAX_FEEDBACK_READ_WINDOW_S,
        )
        return request_base_feedback_once(
            self.base_port,
            self.base_baudrate,
            read_timeout_s=read_timeout_s,
            read_window_s=read_window_s,
        )

    async def base_feedback_samples(self, body: dict[str, Any]) -> dict[str, Any]:
        """重复执行显式 T=130 采集；默认短批量，不触发 manual 或 feedback-flow。"""
        sample_count = clamp_int(
            body.get("sample_count"),
            DEFAULT_FEEDBACK_SAMPLE_COUNT,
            1,
            MAX_FEEDBACK_SAMPLE_COUNT,
        )
        sample_interval_s = clamp_float(
            body.get("sample_interval_s"),
            DEFAULT_FEEDBACK_SAMPLE_INTERVAL_S,
            0.0,
            MAX_FEEDBACK_SAMPLE_INTERVAL_S,
        )
        read_timeout_s = clamp_float(
            body.get("read_timeout_s"),
            DEFAULT_FEEDBACK_READ_TIMEOUT_S,
            0.01,
            MAX_FEEDBACK_READ_TIMEOUT_S,
        )
        read_window_s = clamp_float(
            body.get("read_window_s"),
            DEFAULT_FEEDBACK_READ_WINDOW_S,
            0.01,
            MAX_FEEDBACK_READ_WINDOW_S,
        )
        samples: list[dict[str, Any]] = []
        for index in range(sample_count):
            samples.append(
                request_base_feedback_once(
                    self.base_port,
                    self.base_baudrate,
                    read_timeout_s=read_timeout_s,
                    read_window_s=read_window_s,
                )
            )
            # 最后一帧后不额外 sleep，避免默认请求尾部无意义等待。
            if index < sample_count - 1 and sample_interval_s > 0:
                await asyncio.sleep(sample_interval_s)
        payload = build_base_feedback_samples_payload(
            port=self.base_port,
            baudrate=self.base_baudrate,
            sample_count=sample_count,
            sample_interval_s=sample_interval_s,
            read_timeout_s=read_timeout_s,
            read_window_s=read_window_s,
            samples=samples,
        )
        return persist_feedback_samples_artifact(self.feedback_samples_artifact_path, payload)

    def base_feedback_samples_latest(self) -> tuple[int, dict[str, Any]]:
        """latest 回放只读取 artifact，不能打开串口或发送任何 feedback request。"""
        return read_feedback_samples_latest_artifact(self.feedback_samples_artifact_path)

    def radar_scan_proof_latest(self) -> tuple[int, dict[str, Any]]:
        """LiDAR `/scan` proof 回放只读取 artifact，不能启动 driver 或发送命令。"""
        return read_lidar_scan_proof_latest_artifact(self.lidar_scan_proof_artifact_path)

    def radar_raw_packet_proof_latest(self) -> tuple[int, dict[str, Any]]:
        """LiDAR raw packet proof 回放只读取 artifact，不能打开串口或发送 A5 60。"""
        return read_lidar_raw_packet_proof_latest_artifact(self.lidar_raw_packet_proof_artifact_path)

    async def manual_control(self, body: dict[str, Any]) -> dict[str, Any]:
        """低速点动控制：发送方向命令后等待短窗口，再无条件发送停车命令。"""
        direction = str(body.get("direction", "stop")).strip().lower()
        if direction not in ALLOWED_DIRECTIONS:
            return {
                "schema": f"{SCHEMA}.base_manual_result",
                "generated_at_ms": now_ms(),
                "accepted": False,
                "error": {
                    "type": "unsupported_direction",
                    "message": f"direction must be one of {sorted(ALLOWED_DIRECTIONS)}",
                },
                "direction": direction,
                "allowed_directions": sorted(ALLOWED_DIRECTIONS),
                "command_result": None,
                "stop_result": None,
                "serial_write_failures": [],
                "auto_stop_attempted": False,
                "auto_stop_executed": False,
                "feedback_ack": t1001_boundary("manual command rejected before serial write"),
                "safe_to_control": False,
                "sends_commands": False,
                "robot_control_executed": False,
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
        try:
            requested_speed = float(body.get("speed", 0.08))
        except (TypeError, ValueError):
            requested_speed = 0.08
        # 手控只允许低速正数，方向由左右轮符号表达，避免 PC 传大速度。
        speed = min(max(abs(requested_speed), 0.0), self.max_speed)
        try:
            requested_pulse_ms = int(body.get("duration_ms", DEFAULT_PULSE_MS))
        except (TypeError, ValueError):
            requested_pulse_ms = DEFAULT_PULSE_MS
        # 点动窗口强制限时，任何非 stop 方向都必须进入停车兜底。
        pulse_ms = min(max(requested_pulse_ms, 0), MAX_PULSE_MS)
        command = wheel_command_for_direction(direction, speed)
        first = write_serial_json(self.base_port, self.base_baudrate, command)
        await asyncio.sleep(pulse_ms / 1000.0)
        stop = write_serial_json(self.base_port, self.base_baudrate, {"T": 1, "L": 0, "R": 0})
        serial_write_failures = [
            result["error"]
            for result in (first, stop)
            if isinstance(result, dict) and not result.get("ok") and "error" in result
        ]
        if first.get("ok") and stop.get("ok"):
            # 反馈请求必须排在停车之后，避免读窗口影响点动停车兜底。
            feedback_evidence = request_base_feedback_once(
                self.base_port,
                self.base_baudrate,
                read_timeout_s=body.get("read_timeout_s", DEFAULT_FEEDBACK_READ_TIMEOUT_S),
                read_window_s=body.get("read_window_s", DEFAULT_FEEDBACK_READ_WINDOW_S),
            )
            feedback_after_stop_attempted = True
        else:
            feedback_evidence = skipped_manual_feedback_payload(
                self.base_port,
                self.base_baudrate,
                "skipped_due_to_manual_write_failure",
            )
            feedback_after_stop_attempted = False
        return {
            "schema": f"{SCHEMA}.base_manual_result",
            "generated_at_ms": now_ms(),
            "accepted": True,
            "direction": direction,
            "speed": speed,
            "duration_ms": pulse_ms,
            "requested_speed": requested_speed,
            "requested_duration_ms": requested_pulse_ms,
            "command_result": first,
            "stop_result": stop,
            "serial_write_failures": serial_write_failures,
            "auto_stop_attempted": True,
            "auto_stop_executed": bool(stop.get("ok")),
            "manual_command_executed": bool(first.get("ok")),
            "feedback_after_stop_attempted": feedback_after_stop_attempted,
            "feedback_evidence": feedback_evidence,
            "t1001_feedback_status": feedback_evidence.get("t1001_feedback_status"),
            "feedback_ack": feedback_evidence.get("feedback_ack", t1001_boundary("manual feedback evidence unavailable")),
            "safe_to_control": False,
            "sends_commands": True,
            "robot_control_executed": bool(first.get("ok")),
            "delivery_success": False,
            "hil_pass": False,
            "primary_actions_enabled": False,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.getenv("HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", str(DEFAULT_PORT))))
    parser.add_argument("--camera-base-url", default=os.getenv("ROBER_CAMERA_BASE_URL", DEFAULT_CAMERA_BASE_URL))
    parser.add_argument("--base-port", default=os.getenv("ROBER_BASE_SERIAL_PORT", DEFAULT_BASE_PORT))
    parser.add_argument("--base-baudrate", type=int, default=int(os.getenv("ROBER_BASE_BAUDRATE", str(DEFAULT_BASE_BAUDRATE))))
    parser.add_argument("--max-speed", type=float, default=float(os.getenv("ROBER_BASE_MAX_SPEED", str(DEFAULT_MAX_SPEED))))
    parser.add_argument(
        "--feedback-samples-artifact-path",
        default=os.getenv("ROBER_BASE_FEEDBACK_SAMPLES_ARTIFACT_PATH", DEFAULT_FEEDBACK_SAMPLES_ARTIFACT_PATH),
    )
    parser.add_argument(
        "--lidar-scan-proof-artifact-path",
        default=os.getenv("ROBER_LIDAR_SCAN_PROOF_ARTIFACT_PATH", DEFAULT_LIDAR_SCAN_PROOF_ARTIFACT_PATH),
    )
    parser.add_argument(
        "--lidar-raw-packet-proof-artifact-path",
        default=os.getenv("ROBER_LIDAR_RAW_PACKET_PROOF_ARTIFACT_PATH", DEFAULT_LIDAR_RAW_PACKET_PROOF_ARTIFACT_PATH),
    )
    parser.add_argument("--map-artifact-dir", default=os.getenv("ROBER_MAP_ARTIFACT_DIR", DEFAULT_MAP_ARTIFACT_DIR))
    parser.add_argument(
        "--map-lifecycle-proof-artifact-path",
        default=os.getenv("ROBER_MAP_LIFECYCLE_PROOF_ARTIFACT_PATH", DEFAULT_MAP_LIFECYCLE_PROOF_ARTIFACT_PATH),
    )
    parser.add_argument(
        "--localization-artifact-path",
        default=os.getenv("ROBER_LOCALIZATION_ARTIFACT_PATH", DEFAULT_LOCALIZATION_ARTIFACT_PATH),
    )
    parser.add_argument(
        "--nav2-lifecycle-artifact-path",
        default=os.getenv("ROBER_NAV2_LIFECYCLE_ARTIFACT_PATH", DEFAULT_NAV2_LIFECYCLE_ARTIFACT_PATH),
    )
    parser.add_argument(
        "--elevator-status-artifact-path",
        default=os.getenv("ROBER_ELEVATOR_STATUS_ARTIFACT_PATH", DEFAULT_ELEVATOR_STATUS_ARTIFACT_PATH),
    )
    parser.add_argument("--radar-start-command", default=os.getenv("ROBER_RADAR_START_COMMAND"))
    parser.add_argument("--radar-stop-command", default=os.getenv("ROBER_RADAR_STOP_COMMAND"))
    parser.add_argument("--map-start-command", default=os.getenv("ROBER_MAP_START_COMMAND"))
    parser.add_argument("--map-reset-command", default=os.getenv("ROBER_MAP_RESET_COMMAND"))
    parser.add_argument("--map-save-command", default=os.getenv("ROBER_MAP_SAVE_COMMAND"))
    parser.add_argument("--map-load-command", default=os.getenv("ROBER_MAP_LOAD_COMMAND"))
    parser.add_argument("--localize-reset-command", default=os.getenv("ROBER_LOCALIZE_RESET_COMMAND"))
    parser.add_argument("--nav2-start-command", default=os.getenv("ROBER_NAV2_START_COMMAND"))
    parser.add_argument("--nav2-stop-command", default=os.getenv("ROBER_NAV2_STOP_COMMAND"))
    return parser.parse_args()


async def run_server(args: argparse.Namespace) -> None:
    """启动 aiohttp API，所有硬件子面都挂在 /api 下。"""
    from aiohttp import web

    api = UpperRobotApi(
        camera_base_url=args.camera_base_url,
        base_port=args.base_port,
        base_baudrate=args.base_baudrate,
        max_speed=args.max_speed,
        feedback_samples_artifact_path=args.feedback_samples_artifact_path,
        lidar_scan_proof_artifact_path=args.lidar_scan_proof_artifact_path,
        lidar_raw_packet_proof_artifact_path=args.lidar_raw_packet_proof_artifact_path,
        map_artifact_dir=args.map_artifact_dir,
        map_lifecycle_proof_artifact_path=args.map_lifecycle_proof_artifact_path,
        localization_artifact_path=args.localization_artifact_path,
        nav2_lifecycle_artifact_path=args.nav2_lifecycle_artifact_path,
        elevator_status_artifact_path=args.elevator_status_artifact_path,
        radar_start_command=args.radar_start_command,
        radar_stop_command=args.radar_stop_command,
        map_start_command=args.map_start_command,
        map_reset_command=args.map_reset_command,
        map_save_command=args.map_save_command,
        map_load_command=args.map_load_command,
        localize_reset_command=args.localize_reset_command,
        nav2_start_command=args.nav2_start_command,
        nav2_stop_command=args.nav2_stop_command,
    )
    app = create_app(api)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, args.host, args.port)
    await site.start()
    print(json.dumps({"event": "upper_robot_api_started", "host": args.host, "port": args.port}, ensure_ascii=False), flush=True)
    while True:
        await asyncio.sleep(3600)


def create_app(api: UpperRobotApi) -> Any:
    """集中注册 aiohttp 路由，测试可直接解析路由而不启动监听端口。"""
    from aiohttp import web

    async def options(_: web.Request) -> Any:
        return json_response({})

    async def root(_: web.Request) -> Any:
        return json_response({"schema": SCHEMA, "status": "ready", "routes": (await api.unified_status())["routes"], **proof_flags()})

    async def health(_: web.Request) -> Any:
        return json_response({"schema": f"{SCHEMA}.health", "status": "ready", "generated_at_ms": now_ms(), **proof_flags()})

    async def status(_: web.Request) -> Any:
        return json_response(await api.unified_status())

    async def camera_health(_: web.Request) -> Any:
        http_status, payload = await api.camera_health()
        return json_response(payload, status=http_status)

    async def camera_devices(_: web.Request) -> Any:
        http_status, payload = await api.camera_devices()
        return json_response(payload, status=http_status)

    async def camera_offer(request: web.Request) -> Any:
        body = await request.json()
        http_status, payload = await api.camera_offer(body if isinstance(body, dict) else {})
        return json_response(payload, status=http_status)

    async def camera_peer_close(request: web.Request) -> Any:
        body = await request.json() if request.can_read_body else {}
        http_status, payload = await api.camera_peer_close(request.match_info["peer_id"], body if isinstance(body, dict) else {})
        return json_response(payload, status=http_status)

    async def radar_status(_: web.Request) -> Any:
        return json_response(api.radar_status())

    async def radar_start(_: web.Request) -> Any:
        return json_response(api.radar_control("start"))

    async def radar_stop(_: web.Request) -> Any:
        return json_response(api.radar_control("stop"))

    async def radar_scan_proof_latest(_: web.Request) -> Any:
        http_status, payload = api.radar_scan_proof_latest()
        return json_response(payload, status=http_status)

    async def radar_raw_packet_proof_latest(_: web.Request) -> Any:
        http_status, payload = api.radar_raw_packet_proof_latest()
        return json_response(payload, status=http_status)

    async def base_status(_: web.Request) -> Any:
        return json_response(api.base_status())

    async def map_start(request: web.Request) -> Any:
        body = await request.json() if request.can_read_body else {}
        return json_response(api.map_control("start", body if isinstance(body, dict) else {}))

    async def map_reset(request: web.Request) -> Any:
        body = await request.json() if request.can_read_body else {}
        return json_response(api.map_control("reset", body if isinstance(body, dict) else {}))

    async def map_save(request: web.Request) -> Any:
        body = await request.json() if request.can_read_body else {}
        return json_response(api.map_control("save", body if isinstance(body, dict) else {}))

    async def map_load(request: web.Request) -> Any:
        body = await request.json() if request.can_read_body else {}
        return json_response(api.map_control("load", body if isinstance(body, dict) else {}))

    async def map_list(_: web.Request) -> Any:
        return json_response(api.map_list())

    async def map_proof_latest(_: web.Request) -> Any:
        http_status, payload = api.map_proof_latest()
        return json_response(payload, status=http_status)

    async def localize_reset(request: web.Request) -> Any:
        body = await request.json() if request.can_read_body else {}
        return json_response(api.localize_reset(body if isinstance(body, dict) else {}))

    async def localize_proof_latest(_: web.Request) -> Any:
        http_status, payload = api.localize_proof_latest()
        return json_response(payload, status=http_status)

    async def nav2_status(_: web.Request) -> Any:
        return json_response(api.nav2_status())

    async def nav2_start(_: web.Request) -> Any:
        return json_response(api.nav2_control("start"))

    async def nav2_stop(_: web.Request) -> Any:
        return json_response(api.nav2_control("stop"))

    async def elevator_status(_: web.Request) -> Any:
        return json_response(api.elevator_status())

    async def base_stop(_: web.Request) -> Any:
        return json_response(build_stop_payload(api.base_port, api.base_baudrate))

    async def base_feedback_request(request: web.Request) -> Any:
        body = await request.json() if request.can_read_body else {}
        return json_response(await api.base_feedback_request(body if isinstance(body, dict) else {}))

    async def base_feedback_samples(request: web.Request) -> Any:
        body = await request.json() if request.can_read_body else {}
        return json_response(await api.base_feedback_samples(body if isinstance(body, dict) else {}))

    async def base_feedback_samples_latest(_: web.Request) -> Any:
        http_status, payload = api.base_feedback_samples_latest()
        return json_response(payload, status=http_status)

    async def base_manual(request: web.Request) -> Any:
        body = await request.json()
        payload = await api.manual_control(body if isinstance(body, dict) else {})
        return json_response(payload, status=200 if payload.get("accepted", True) else 400)

    app = web.Application()
    app.router.add_route("OPTIONS", "/{tail:.*}", options)
    app.router.add_get("/", root)
    app.router.add_get("/health", health)
    app.router.add_get("/api/status", status)
    app.router.add_get(ROUTE_PATHS["camera_health"], camera_health)
    app.router.add_get(ROUTE_PATHS["camera_devices"], camera_devices)
    app.router.add_post(ROUTE_PATHS["camera_offer"], camera_offer)
    app.router.add_post(ROUTE_PATHS["camera_peer_close"], camera_peer_close)
    app.router.add_get(ROUTE_PATHS["radar_status"], radar_status)
    app.router.add_post(ROUTE_PATHS["radar_start"], radar_start)
    app.router.add_post(ROUTE_PATHS["radar_stop"], radar_stop)
    app.router.add_get(ROUTE_PATHS["radar_scan_proof_latest"], radar_scan_proof_latest)
    app.router.add_get(ROUTE_PATHS["radar_raw_packet_proof_latest"], radar_raw_packet_proof_latest)
    app.router.add_post(ROUTE_PATHS["map_start"], map_start)
    app.router.add_post(ROUTE_PATHS["map_reset"], map_reset)
    app.router.add_post(ROUTE_PATHS["map_save"], map_save)
    app.router.add_post(ROUTE_PATHS["map_load"], map_load)
    app.router.add_get(ROUTE_PATHS["map_list"], map_list)
    app.router.add_get(ROUTE_PATHS["map_proof_latest"], map_proof_latest)
    app.router.add_post(ROUTE_PATHS["localize_reset"], localize_reset)
    app.router.add_get(ROUTE_PATHS["localize_proof_latest"], localize_proof_latest)
    app.router.add_get(ROUTE_PATHS["nav2_status"], nav2_status)
    app.router.add_post(ROUTE_PATHS["nav2_start"], nav2_start)
    app.router.add_post(ROUTE_PATHS["nav2_stop"], nav2_stop)
    app.router.add_get(ROUTE_PATHS["elevator_status"], elevator_status)
    app.router.add_get(ROUTE_PATHS["base_status"], base_status)
    app.router.add_post(ROUTE_PATHS["base_feedback_request"], base_feedback_request)
    app.router.add_post(ROUTE_PATHS["base_feedback_samples"], base_feedback_samples)
    app.router.add_get(ROUTE_PATHS["base_feedback_samples_latest"], base_feedback_samples_latest)
    app.router.add_post(ROUTE_PATHS["base_stop"], base_stop)
    app.router.add_post(ROUTE_PATHS["base_manual"], base_manual)
    return app


def main() -> int:
    args = parse_args()
    asyncio.run(run_server(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
