#!/usr/bin/env python3
"""Orange Pi 上位机统一 Robot API：camera / radar / base 汇总入口。"""

from __future__ import annotations

import argparse
import asyncio
import base64
import glob
import json
import math
import os
import re
import shlex
import signal
import struct
import subprocess
import sys
import tempfile
import threading
import time
import zlib
from pathlib import Path
from typing import Any
from urllib.parse import urljoin


SCHEMA = "trashbot.upper_robot_api.v1"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8787
DEFAULT_CAMERA_BASE_URL = "http://127.0.0.1:8088"
CAMERA_MJPEG_RELAY_HEADER_TIMEOUT_S = 12.0
CAMERA_MJPEG_RELAY_SOCK_READ_TIMEOUT_S = 12.0
# 这些原因都表示已经真实打开过视频源但没有拿到首帧，不能在 status 中退回“未探测”。
CAMERA_FIRST_FRAME_FAILURE_REASONS = frozenset({
    "capture_read_call_timeout",
    "capture_read_no_result",
    "capture_read_returned_false",
    "ffmpeg_mjpeg_first_frame_unreadable",
    "first_frame_format_attempts_failed",
    "first_frame_timeout",
    "first_frame_total_timeout",
    "mjpeg_auto_retry_cooldown_after_first_frame_failure",
    "opencv_capture_not_opened",
})
DEFAULT_BASE_PORT = "/dev/ttyS5"
DEFAULT_BASE_BAUDRATE = 115200
DEFAULT_MAX_SPEED = 0.12
DEFAULT_BASE_COMMAND_MODE = "ros"
DEFAULT_NAV2_BASE_COMMAND_MODE = "pwm"
DEFAULT_MANUAL_PWM_MIN_ABS = 164
DEFAULT_MANUAL_PWM_MAX_ABS = 164
DEFAULT_PULSE_MS = 260
STATUS_SECTION_TIMEOUT_S = 5.0
STATUS_TOTAL_TIMEOUT_S = 7.0
MAX_PULSE_MS = 800
MIN_HOLD_WATCHDOG_MS = 240
ALLOWED_DIRECTIONS = frozenset({"forward", "back", "left", "right", "stop"})
ALLOWED_BASE_COMMAND_MODES = frozenset({"ros", "speed", "pwm"})
ALLOWED_NAV2_BASE_COMMAND_MODES = frozenset({"ros", "speed", "pwm"})
DEFAULT_FEEDBACK_READ_TIMEOUT_S = 0.2
DEFAULT_FEEDBACK_READ_WINDOW_S = 1.2
BASE_STATUS_DIRECT_FEEDBACK_ENV = "ROBER_BASE_STATUS_DIRECT_FEEDBACK_ON_GET"
DEFAULT_FEEDBACK_SAMPLE_COUNT = 3
DEFAULT_FEEDBACK_SAMPLE_INTERVAL_S = 0.2
DEFAULT_FEEDBACK_SAMPLES_ARTIFACT_PATH = "runtime/base_feedback_samples_latest.json"
DEFAULT_BRIDGE_FEEDBACK_DEBUG_LOG_PATH = "/root/rober/onboard/runtime/wave_rover_feedback_debug.jsonl"
DEFAULT_BRIDGE_FEEDBACK_DEBUG_STALE_AFTER_MS = 15 * 1000
DEFAULT_BRIDGE_COMMAND_DEBUG_LOG_PATH = "/root/rober/onboard/runtime/wave_rover_command_debug.jsonl"
DEFAULT_BRIDGE_COMMAND_DEBUG_STALE_AFTER_MS = 15 * 60 * 1000
DEFAULT_LIDAR_SCAN_PROOF_ARTIFACT_PATH = "runtime/lidar_scan_proof_latest.json"
DEFAULT_LIDAR_SCAN_PROOF_REFRESH_TIMEOUT_S = 12.0
DEFAULT_LIDAR_SCAN_PROOF_RUNTIME_WARMUP_S = 6.0
MAP_COLOR_OVERLAY_BOUNDARY_POINT_LIMIT = 900
MAP_COLOR_OVERLAY_PILLAR_POINT_LIMIT = 120
MAP_COLOR_OVERLAY_COSTMAP_POINT_LIMIT = 700
DEFAULT_LIDAR_DRIVER_DIAGNOSTICS_STALE_AFTER_MS = 5 * 1000
DEFAULT_RADAR_LIFECYCLE_STATUS_TIMEOUT_S = 3.0
DEFAULT_LIDAR_RAW_PACKET_PROOF_ARTIFACT_PATH = "runtime/lidar_raw_packet_proof_latest.json"
DEFAULT_ROBER_ROOT = "/root/rober"
DEFAULT_ONBOARD_WORKDIR = "/root/rober/onboard"
DEFAULT_MAP_ARTIFACT_DIR = "/root/rober/onboard/runtime/maps"
DEFAULT_MAP_LIFECYCLE_PROOF_ARTIFACT_PATH = "/root/rober/onboard/runtime/map_lifecycle_latest.json"
LEGACY_MAP_LIFECYCLE_PROOF_ARTIFACT_PATH = "/root/rober/runtime/map_lifecycle_latest.json"
DEFAULT_MAP_LIFECYCLE_PROOF_REFRESH_TIMEOUT_S = 70.0
MAP_LIFECYCLE_OBSERVED_STATUS = "map_once_artifact_metadata_observed"
SAFE_MAP_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
DEFAULT_LOCALIZATION_ARTIFACT_PATH = "runtime/localization_reset_latest.json"
DEFAULT_NAV2_LIFECYCLE_ARTIFACT_PATH = "/root/rober/onboard/runtime/nav2_lifecycle_latest.json"
DEFAULT_NAV2_GOAL_EXECUTION_ARTIFACT_PATH = "/root/rober/onboard/runtime/nav2_goal_execution_latest.json"
DEFAULT_DELIVERY_COMPLETION_ARTIFACT_PATH = "/root/rober/onboard/runtime/delivery_completion_latest.json"
DEFAULT_FREE_ROAM_AUTONOMY_ARTIFACT_PATH = "/root/rober/onboard/runtime/free_roam_autonomy_latest.json"
FREE_ROAM_PARAM_LOAD_TIMEOUT_S = 30.0
FREE_ROAM_MANAGED_START_WAIT_TIMEOUT_S = 5.0
FREE_ROAM_MANAGED_START_WAIT_INTERVAL_S = 0.25
FREE_ROAM_AUTONOMY_NODE_NAME = "/free_roam_autonomy"
DEFAULT_FREE_ROAM_MANAGED_LOG_NAME = "free_roam_autonomy_managed.log"
FREE_ROAM_START_ARTIFACT_WAIT_TIMEOUT_S = 1.8
FREE_ROAM_START_ARTIFACT_WAIT_INTERVAL_S = 0.2
DEFAULT_ROS_SETUP_PATH = "/opt/ros/humble/setup.bash"
DEFAULT_ONBOARD_SETUP_PATH = "/root/rober/onboard/install/setup.bash"
ROS_CMD_VEL_TOPIC = "/cmd_vel"
ROS_CMD_VEL_BURST_RATE_HZ = 20.0
ROS_CMD_VEL_SUBSCRIPTION_WAIT_S = 1.2
ROS_CMD_VEL_STOP_HOLD_S = 0.16
DEFAULT_NAV2_RUNTIME_PROOF_REFRESH_TIMEOUT_S = 8.0
NAV2_PROOF_PROCESS_BASE_MARGIN_S = 12.0
NAV2_PROOF_PROCESS_PATH_MARGIN_S = 8.0
NAV2_PROOF_PROCESS_MANAGED_MARGIN_S = 6.0
NAV2_PROOF_PROCESS_INITIALPOSE_MARGIN_S = 4.0
# 30s collector + 30s managed runtime + 30s path generation 的固定 PC body
# 会形成 120s helper raw 预算；cap 必须高于该值，避免外层 wrapper 先误杀。
NAV2_PROOF_PROCESS_TIMEOUT_CAP_S = 132.0
# PC workstation proxy 的 Nav2 POST timeout 当前固定为 150s；上位机只记录该契约，
# 用于 artifact/测试表达“PC 等得比 upper helper 久”，不从这里控制 PC 行为。
NAV2_PROOF_PC_PROXY_TIMEOUT_BUDGET_S = 150.0
DEFAULT_ELEVATOR_STATUS_ARTIFACT_PATH = "runtime/elevator_status_latest.json"
DEFAULT_OPERATOR_REPORT_ARTIFACT_PATH = "runtime/operator_report_latest.json"
DEFAULT_FEEDBACK_SAMPLES_STALE_AFTER_MS = 15 * 60 * 1000
LIDAR_SCAN_PREVIEW_POINT_LIMIT = 240
NAV2_PATH_PREVIEW_POINT_LIMIT = 240
MAX_FEEDBACK_READ_TIMEOUT_S = 2.0
MAX_FEEDBACK_READ_WINDOW_S = 5.0
MAX_FEEDBACK_SAMPLE_COUNT = 8
MAX_FEEDBACK_SAMPLE_INTERVAL_S = 2.0
BASE_FEEDBACK_REQUEST_COMMAND = {"T": 130}
BASE_FEEDBACK_ID = 1001
_ROS_CMD_VEL_CONTEXT: dict[str, Any] = {}
# rclpy node 不能被 watchdog thread 与 aiohttp request 同时 spin/publish；短临界区不包含 burst sleep。
_ROS_CMD_VEL_LOCK = threading.RLock()
LATENCY_TRACE_SCHEMA = "trashbot.keyboard_wheel_latency_trace.v1"
# trace 只接受短关联键，避免把诊断 envelope 变成任意字符串回显面。
LATENCY_TRACE_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")
BLOCKED_BASE_FEEDBACK_COMMANDS = [
    "T=1",
    "T=13",
    "T=131",
    "cmd_vel",
    "/api/base/manual",
]
BLOCKED_LIDAR_RUNTIME_COMMAND_TOKENS = (
    "/dev/ttyS5",
    "/api/base",
    "/cmd_vel",
    "cmd_vel",
    "T=1",
    "T=13",
    "T=130",
    "T=131",
)
SAFE_LIDAR_RUNTIME_SCRIPT = "o1_lidar_ros2_scan_smoke.sh"
SAFE_RADAR_LIFECYCLE_SCRIPT = "o1_lidar_lifecycle.sh"
SAFE_NAV2_LIFECYCLE_SCRIPT = "o11_nav2_lifecycle.sh"
SAFE_LIDAR_RUNTIME_SHELLS = ("bash", "sh")
DEFAULT_RADAR_START_COMMAND = (
    "bash /root/rober/onboard/scripts/o1_lidar_lifecycle.sh start "
    "--serial-port /dev/ttyACM0 --serial-baudrate 230400 --frame-id laser_frame"
)
DEFAULT_RADAR_STOP_COMMAND = "bash /root/rober/onboard/scripts/o1_lidar_lifecycle.sh stop"
DEFAULT_NAV2_MAP_FILE = "/root/rober/onboard/runtime/maps/trashbot_map.yaml"
DEFAULT_NAV2_START_COMMAND = (
    "bash /root/rober/onboard/scripts/o11_nav2_lifecycle.sh start "
    f"--map-file {DEFAULT_NAV2_MAP_FILE} "
    "--base-port /dev/ttyS5 --base-baudrate 115200 --command-mode ros "
    "--base-enabled false --lidar-enabled false --lidar-serial-port /dev/ttyACM0 "
    "--lidar-serial-baudrate 230400 --reuse-existing-scan true "
    "--static-laser-tf-enabled true"
)
DEFAULT_NAV2_STOP_COMMAND = "bash /root/rober/onboard/scripts/o11_nav2_lifecycle.sh stop"
DEFAULT_NAV2_STATUS_COMMAND = "bash /root/rober/onboard/scripts/o11_nav2_lifecycle.sh status"
# strict start 必须显式提交完整 JSON；缺字段与多字段都可能掩盖旧客户端合同漂移。
STRICT_NAV2_START_REQUEST_FIELDS = frozenset(
    {"strict_no_motion", "base_enabled", "lidar_enabled", "reuse_existing_scan", "timeout_s"}
)
# start 脚本自身最多等待 8 秒；4..20 秒既覆盖慢板启动，也避免请求无限占住 API worker。
# 下界拒绝短于脚本内部启动观测窗口的假 timeout。
STRICT_NAV2_START_TIMEOUT_MIN_S = 4.0
# 上界限制单个 HTTP worker 的最长占用，不做静默 clamp。
STRICT_NAV2_START_TIMEOUT_MAX_S = 20.0
OPERATOR_REPORT_FIELDS = (
    "operator_present",
    "evidence_ref",
    "physical_clearance_confirmed",
    "emergency_stop_ready",
    "observed_motion",
    "observed_stop",
    "operator_notes",
    "reported_at",
)
OPERATOR_REPORT_HIL_BOOL_CLAIM_FIELDS = (
    "external_video_recorded",
    "visible_content_proven",
    "wheel_feedback_lr_nonzero_proven",
    "physical_motion_lidar_delta_proven",
    "real_route_map_proven",
    "delivery_success",
)
OPERATOR_REPORT_HIL_REF_CLAIM_FIELDS = (
    "external_video_ref",
    "camera_artifacts_ref",
    "wheel_feedback_ref",
    "scan_delta_ref",
    "route_map_ref",
    "site_state",
)
OPERATOR_REPORT_STRUCTURED_HIL_FIELDS = OPERATOR_REPORT_HIL_BOOL_CLAIM_FIELDS + OPERATOR_REPORT_HIL_REF_CLAIM_FIELDS
OPERATOR_REPORT_PREFLIGHT_BOOL_FIELDS = (
    "operator_present",
    "physical_clearance_confirmed",
    "emergency_stop_ready",
)
OPERATOR_REPORT_REVIEW_BOOL_FIELDS = (
    "observed_motion",
    "observed_stop",
)
OPERATOR_REPORT_REQUIRED_REVIEW_TEXT_FIELDS = ("operator_notes", "reported_at")
OPERATOR_REPORT_DOES_NOT_REPLACE = [
    "/api/base/stop",
    "/api/base/status",
    "/api/base/feedback-request",
    "/api/base/feedback-samples",
    "T=1001",
    "robot ACK",
    "HIL",
    "ROS /odom /imu/data /battery",
    "field video or现场记录",
]
ROUTE_PATHS = {
    "health": "/api/health",
    "camera_health": "/api/camera/health",
    "camera_devices": "/api/camera/devices",
    "camera_offer": "/api/camera/offer",
    "camera_peer_close": "/api/camera/peers/{peer_id}/close",
    "camera_first_frame_probe": "/api/camera/first-frame/probe",
    "camera_usb_recovery": "/api/camera/usb-recovery",
    "camera_mjpeg": "/api/camera/mjpeg",
    "camera_mjpeg_status": "/api/camera/mjpeg/status",
    "radar_status": "/api/radar/status",
    "radar_start": "/api/radar/start",
    "radar_stop": "/api/radar/stop",
    "radar_scan_proof_refresh": "/api/radar/scan-proof/refresh",
    "radar_scan_proof_latest": "/api/radar/scan-proof/latest",
    "radar_raw_packet_proof_latest": "/api/radar/raw-packet-proof/latest",
    "map_status": "/api/map/status",
    "map_start": "/api/map/start",
    "map_reset": "/api/map/reset",
    "map_save": "/api/map/save",
    "map_load": "/api/map/load",
    "map_list": "/api/map/list",
    "map_preview": "/api/map/preview",
    "map_proof_refresh": "/api/map/proof/refresh",
    "map_proof_latest": "/api/map/proof/latest",
    "localize_reset": "/api/localize/reset",
    "localize_proof_latest": "/api/localize/proof/latest",
    "nav2_status": "/api/nav2/status",
    "nav2_proof_refresh": "/api/nav2/proof/refresh",
    "nav2_proof_latest": "/api/nav2/proof/latest",
    "nav2_goal_execute": "/api/nav2/goal/execute",
    "nav2_goal_execution_latest": "/api/nav2/goal/execution/latest",
    "delivery_complete": "/api/delivery/complete",
    "delivery_latest": "/api/delivery/latest",
    "free_roam_autonomy_latest": "/api/free-roam/autonomy/latest",
    "free_roam_autonomy_start": "/api/free-roam/autonomy/start",
    "free_roam_autonomy_stop": "/api/free-roam/autonomy/stop",
    "nav2_start": "/api/nav2/start",
    "nav2_stop": "/api/nav2/stop",
    "elevator_status": "/api/elevator/status",
    "operator_report": "/api/operator/report",
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
LIDAR_VENDOR_REFERENCE_BAUDRATE = 230400
LIDAR_HISTORICAL_FIELD_BAUDRATE_CANDIDATE = 150000


def now_ms() -> int:
    """统一毫秒时间戳，方便 PC、上位机和远端日志对齐。"""
    return int(time.time() * 1000)


def normalize_latency_trace(value: Any) -> dict[str, Any] | None:
    """校验可选 latency envelope；未知字段不回显，缺 envelope 保持旧接口兼容。"""
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("latency_trace_invalid_object")

    def safe_token(field: str, max_length: int = 96) -> str:
        # trace id/session 不是授权凭证，只允许短关联字符，拒绝控制字符和路径片段。
        normalized = str(value.get(field) or "").strip()
        if not normalized or len(normalized) > max_length or not LATENCY_TRACE_TOKEN_PATTERN.fullmatch(normalized):
            raise ValueError(f"latency_trace_invalid_{field}")
        return normalized

    def finite_nonnegative(field: str) -> float:
        # browser 数值只原样关联；upper 不拿它与 monotonic 时钟做跨机相减。
        raw = value.get(field)
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(float(raw)) or float(raw) < 0:
            raise ValueError(f"latency_trace_invalid_{field}")
        return float(raw)

    if value.get("schema") != LATENCY_TRACE_SCHEMA:
        raise ValueError("latency_trace_invalid_schema")
    sequence_value = finite_nonnegative("hold_sequence")
    if not sequence_value.is_integer() or sequence_value > 1_000_000_000:
        raise ValueError("latency_trace_invalid_hold_sequence")
    sample_kind = value.get("sample_kind")
    if sample_kind not in {"cold", "warm"}:
        raise ValueError("latency_trace_invalid_sample_kind")
    return {
        "schema": LATENCY_TRACE_SCHEMA,
        "latency_trace_id": safe_token("latency_trace_id"),
        "client_keydown_perf_ms": finite_nonnegative("client_keydown_perf_ms"),
        "client_time_origin_ms": finite_nonnegative("client_time_origin_ms"),
        "hold_session_id": safe_token("hold_session_id"),
        "hold_sequence": int(sequence_value),
        "sample_kind": sample_kind,
    }


def upper_latency_timing(
    upper_receive_mono_ns: int,
    manual_gate_done_mono_ns: int,
    command_result: dict[str, Any],
    upper_response_ready_mono_ns: int,
) -> dict[str, Any]:
    """只计算 upper 本进程 span；browser、PC、bridge 时钟必须在各自进程内分账。"""
    first_publish = int(command_result.get("cmd_vel_first_publish_mono_ns") or 0)
    publish_done = int(command_result.get("cmd_vel_publish_done_mono_ns") or 0)
    timing = {
        "clock_id": "python_monotonic_ns",
        "upper_receive_mono_ns": upper_receive_mono_ns,
        "manual_gate_done_mono_ns": manual_gate_done_mono_ns,
        "rclpy_context_status": command_result.get("rclpy_context_status", "not_applicable"),
        "rclpy_ready_mono_ns": command_result.get("rclpy_ready_mono_ns"),
        "cmd_vel_first_publish_mono_ns": first_publish or None,
        "cmd_vel_publish_done_mono_ns": publish_done or None,
        "upper_response_ready_mono_ns": upper_response_ready_mono_ns,
        "upper_receive_to_gate_ms": round((manual_gate_done_mono_ns - upper_receive_mono_ns) / 1_000_000, 6),
        "upper_receive_to_response_ready_ms": round((upper_response_ready_mono_ns - upper_receive_mono_ns) / 1_000_000, 6),
        "latency_pass_eligible": bool(command_result.get("latency_pass_eligible")),
        "cli_fallback_attempted": bool(command_result.get("cli_fallback_attempted")),
    }
    if first_publish:
        timing["upper_receive_to_first_publish_ms"] = round((first_publish - upper_receive_mono_ns) / 1_000_000, 6)
        timing["manual_gate_to_first_publish_ms"] = round((first_publish - manual_gate_done_mono_ns) / 1_000_000, 6)
    if first_publish and publish_done:
        timing["cmd_vel_publish_span_ms"] = round((publish_done - first_publish) / 1_000_000, 6)
    return timing


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


class SharedCameraMjpegRelay:
    """把 camera service 的 MJPEG 源流复用给多个浏览器，避免每人都抢一次摄像头。"""

    def __init__(self, target_url: str) -> None:
        self.target_url = target_url
        self.clients: set[asyncio.Queue[bytes | None]] = set()
        self.upstream_task: asyncio.Task[None] | None = None
        self.content_type = ""
        self.content_type_loaded = asyncio.Event()
        self.last_failure_reason = ""
        self.last_remote_http_status: int | None = None
        self.last_failure_at_ms: int | None = None
        self.last_error_payload: dict[str, Any] | None = None

    def snapshot(self) -> dict[str, Any]:
        """状态只给诊断使用；不能据此宣称画面像素已经可见。"""
        return {
            "client_count": len(self.clients),
            "upstream_active": self.upstream_task is not None and not self.upstream_task.done(),
            "content_type_loaded": self.content_type_loaded.is_set(),
            "shared_capture": True,
            "exclusive_camera_claim": False,
            "last_failure_reason": self.last_failure_reason,
            "last_remote_http_status": self.last_remote_http_status,
            "last_failure_at_ms": self.last_failure_at_ms,
            "last_error_payload": self.last_error_payload,
        }

    def register(self) -> asyncio.Queue[bytes | None]:
        """每个浏览器只拿自己的队列；上游任务最多同时保留一个。"""
        queue: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=4)
        self.clients.add(queue)
        if self.upstream_task is None or self.upstream_task.done():
            self.content_type = ""
            self.content_type_loaded.clear()
            self.last_error_payload = None
            self.upstream_task = asyncio.create_task(self._run_upstream())
        return queue

    def unregister(self, queue: asyncio.Queue[bytes | None]) -> None:
        """最后一个客户端离开时主动关掉上游，释放 camera service 连接。"""
        self.clients.discard(queue)
        if not self.clients and self.upstream_task is not None and not self.upstream_task.done():
            self.upstream_task.cancel()

    async def _broadcast(self, chunk: bytes | None) -> None:
        """慢客户端只保留最新帧块，避免一个页面卡住整条预览流。"""
        for queue in list(self.clients):
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            await queue.put(chunk)

    def mark_upstream_failure(self, status: int | None, payload: dict[str, Any] | None = None, fallback_reason: str = "") -> None:
        """记录 8088 失败体；无首帧 attempts 要能穿过 8787 给 PC 做 WYSIWYG 诊断。"""
        self.last_remote_http_status = status
        self.last_error_payload = payload
        failure_reason = ""
        if payload:
            failure_reason = str(payload.get("failure_reason") or payload.get("error") or "")
        self.last_failure_reason = failure_reason or fallback_reason or (f"camera_mjpeg_http_status_{status}" if status is not None else "camera_mjpeg_upstream_failed")
        self.last_failure_at_ms = now_ms()
        self.content_type_loaded.set()

    async def _run_upstream(self) -> None:
        """真实摄像头只由这一条协程拉取；失败后所有等待者都收到结束信号。"""
        from aiohttp import ClientSession, ClientTimeout

        try:
            async with ClientSession(timeout=ClientTimeout(total=None, sock_connect=6, sock_read=CAMERA_MJPEG_RELAY_SOCK_READ_TIMEOUT_S)) as session:
                async with session.get(self.target_url) as upstream:
                    self.last_remote_http_status = upstream.status
                    content_type = upstream.headers.get("Content-Type", "")
                    if upstream.status != 200 or "multipart/x-mixed-replace" not in content_type:
                        upstream_error_payload: dict[str, Any] | None = None
                        if "json" in content_type.lower():
                            try:
                                maybe_payload = await upstream.json(content_type=None)
                                if isinstance(maybe_payload, dict):
                                    upstream_error_payload = maybe_payload
                            except Exception as exc:  # noqa: BLE001 - 失败体读不到时仍保留 HTTP 状态。
                                upstream_error_payload = {"error": "camera_mjpeg_error_body_unreadable", "detail": compact_error(exc)}
                        # 8088 会在无首帧时返回结构化 JSON；保留根因，PC 才能看到 YUYV/default 尝试矩阵。
                        self.mark_upstream_failure(upstream.status, upstream_error_payload)
                        return
                    self.content_type = content_type
                    self.last_failure_reason = ""
                    self.last_error_payload = None
                    self.content_type_loaded.set()
                    async for chunk in upstream.content.iter_chunked(65536):
                        if not self.clients:
                            break
                        await self._broadcast(chunk)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - 流式预览失败必须降级成诊断状态，不能拖垮主 API。
            error_detail = compact_error(exc)
            self.mark_upstream_failure(
                None,
                {"error": "camera_mjpeg_upstream_exception", "detail": error_detail},
                fallback_reason=error_detail["message"],
            )
        finally:
            await self._broadcast(None)


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


def pwm_command_for_direction(
    direction: str,
    speed: float,
    *,
    max_speed: float,
    pwm_min_abs: int,
    pwm_max_abs: int,
) -> dict[str, int]:
    """把 PC 点动速度映射到 vendor T=11 PWM；轮速反馈与运动证据分开判断。"""
    if direction == "stop" or speed <= 0:
        pwm = 0
    else:
        # vendor json_cmd.h 给出的 PWM 示例是 164；当前现场 T1001 L/R 可能一直为 0，
        # 所以这里只负责发足够短的点动命令，运动证据由 IMU/外部观察另行记录。
        scaled = round(abs(speed) / max(max_speed, 1e-6) * pwm_max_abs)
        pwm = min(max(pwm_min_abs, scaled), pwm_max_abs)
    if direction == "forward":
        left, right = pwm, pwm
    elif direction == "back":
        left, right = -pwm, -pwm
    elif direction == "left":
        left, right = -pwm, pwm
    elif direction == "right":
        left, right = pwm, -pwm
    elif direction == "stop":
        left, right = 0, 0
    else:
        raise ValueError(f"unsupported_direction:{direction}")
    return {"T": 11, "L": left, "R": right}


def ros_command_for_direction(direction: str, speed: float) -> dict[str, float | int]:
    """把 PC 方向键转换为 ROS Twist 语义；bridge 再按当前参数落成 T=11/T=13/T=1。"""
    if direction == "forward":
        linear_x, angular_z = speed, 0.0
    elif direction == "back":
        linear_x, angular_z = -speed, 0.0
    elif direction == "left":
        linear_x, angular_z = 0.0, speed
    elif direction == "right":
        linear_x, angular_z = 0.0, -speed
    elif direction == "stop":
        linear_x, angular_z = 0.0, 0.0
    else:
        raise ValueError(f"unsupported_direction:{direction}")
    return {"T": 13, "X": round(linear_x, 3), "Z": round(angular_z, 3)}


def optional_float(value: Any) -> float | None:
    """从可选 JSON 字段读取有限浮点数；缺失或非法时保持 None，避免 silently 放大控制输入。"""
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def ros_command_for_optional_twist(body: dict[str, Any], fallback: dict[str, float | int], *, max_speed: float) -> tuple[dict[str, float | int], dict[str, Any]]:
    """键盘组合键可直接给 ROS X/Z；仍按 max_speed 对线速度和角速度做同一低速限幅。"""
    requested_linear = optional_float(body.get("linear_x_mps", body.get("linear_x", body.get("linear_mps"))))
    requested_angular = optional_float(body.get("angular_z_radps", body.get("angular_z", body.get("angular_radps"))))
    if requested_linear is None and requested_angular is None:
        return fallback, {
            "ros_twist_override_applied": False,
            "requested_linear_x_mps": None,
            "requested_angular_z_radps": None,
            "clamped_linear_x_mps": fallback.get("X"),
            "clamped_angular_z_radps": fallback.get("Z"),
        }
    clamped_linear = min(max(requested_linear if requested_linear is not None else 0.0, -max_speed), max_speed)
    clamped_angular = min(max(requested_angular if requested_angular is not None else 0.0, -max_speed), max_speed)
    return {"T": 13, "X": round(clamped_linear, 3), "Z": round(clamped_angular, 3)}, {
        "ros_twist_override_applied": True,
        "requested_linear_x_mps": requested_linear,
        "requested_angular_z_radps": requested_angular,
        "clamped_linear_x_mps": round(clamped_linear, 3),
        "clamped_angular_z_radps": round(clamped_angular, 3),
    }


def manual_command_for_direction(
    direction: str,
    speed: float,
    *,
    command_mode: str,
    max_speed: float,
    pwm_min_abs: int,
    pwm_max_abs: int,
) -> dict[str, float | int]:
    """按调用方指定的现场模式选择底盘命令；PC 低速试动可显式走 PWM。"""
    if command_mode == "ros":
        return ros_command_for_direction(direction, speed)
    if command_mode == "pwm":
        return pwm_command_for_direction(
            direction,
            speed,
            max_speed=max_speed,
            pwm_min_abs=pwm_min_abs,
            pwm_max_abs=pwm_max_abs,
        )
    return wheel_command_for_direction(direction, speed)


def stop_commands_for_mode(command_mode: str) -> list[dict[str, float | int]]:
    """停车同时覆盖 PWM、speed 和 ROS 三种 vendor 控制面，避免模式切换后残留运动。"""
    if command_mode == "pwm":
        primary: dict[str, float | int] = {"T": 11, "L": 0, "R": 0}
    elif command_mode == "ros":
        primary = {"T": 13, "X": 0, "Z": 0}
    else:
        primary = {"T": 1, "L": 0, "R": 0}
    backups: list[dict[str, float | int]] = [
        {"T": 11, "L": 0, "R": 0},
        {"T": 1, "L": 0, "R": 0},
        {"T": 13, "X": 0, "Z": 0},
    ]
    ordered: list[dict[str, float | int]] = [primary]
    for command in backups:
        if command not in ordered:
            ordered.append(command)
    return ordered


def default_motion_read_window_s(pulse_ms: int) -> float:
    """反馈采样尽量覆盖点动窗口；预留 50ms 给停车兜底，避免错过 200ms 级底盘反馈。"""
    pulse_s = max(pulse_ms, 0) / 1000.0
    if pulse_s <= 0:
        return 0.05
    return max(0.05, min(0.75, max(pulse_s - 0.05, 0.05)))


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


def lidar_driver_diagnostics_artifact_info(path: str | None) -> dict[str, Any]:
    """LiDAR driver 诊断文件只读入口，用于区分无字节、无 packet 和无 scan。"""
    return {
        "path": path or "",
        "configured_by": "o1_lidar_lifecycle.sh driver_diagnostics_path",
        "format": "json",
        "schema": "trashbot.o1.lidar_driver_diagnostics.v1",
    }


def read_lidar_driver_diagnostics_artifact(path: str | None) -> dict[str, Any]:
    """读取 driver 运行时诊断；失败只作为状态材料，不影响 radar/status。"""
    artifact = lidar_driver_diagnostics_artifact_info(path)
    if not path:
        return {
            "status": "not_configured",
            "artifact": artifact,
            "diagnosis_status": "not_configured",
            "next_action_plain": "LiDAR driver 诊断路径未配置；重启 lifecycle 后应由脚本注入 diagnostics_path。",
        }
    resolved = Path(path)
    try:
        data = resolved.read_text(encoding="utf-8")
        payload = json.loads(data)
    except FileNotFoundError:
        return {
            "status": "missing",
            "artifact": artifact,
            "diagnosis_status": "missing",
            "next_action_plain": "LiDAR driver 诊断文件还没生成；确认 lifecycle 使用新版脚本并重启雷达。",
        }
    except Exception as exc:  # noqa: BLE001 - artifact 可能损坏，API 要给出可读原因。
        return {
            "status": "invalid",
            "artifact": artifact,
            "diagnosis_status": "invalid",
            "failure_reason": compact_error(exc),
            "next_action_plain": "LiDAR driver 诊断文件不可读；查看 lifecycle 日志和磁盘权限。",
        }
    diagnosis = payload.get("diagnosis") if isinstance(payload.get("diagnosis"), dict) else {}
    serial = payload.get("serial") if isinstance(payload.get("serial"), dict) else {}
    runtime = payload.get("runtime") if isinstance(payload.get("runtime"), dict) else {}
    scan_preview = payload.get("scan_preview") if isinstance(payload.get("scan_preview"), dict) else {}
    return {
        "status": "loaded",
        "artifact": {
            **artifact,
            "bytes_read": len(data.encode("utf-8")),
            "mtime_ms": int(resolved.stat().st_mtime * 1000),
        },
        "schema": payload.get("schema"),
        "state": payload.get("state"),
        "diagnosis_status": str(diagnosis.get("status") or "not_loaded"),
        "next_action_plain": str(diagnosis.get("next_action_plain") or "LiDAR driver 诊断未给出下一步。"),
        "serial": serial,
        "runtime": runtime,
        "scan_preview": scan_preview,
        "readback_sends_commands": False,
        "sends_base_motion_commands": False,
        "publishes_cmd_vel": False,
        "robot_control_executed": False,
        "hil_pass": False,
    }


def safe_lidar_evidence_ref_suffix(value: Any) -> str | None:
    """把时间字段转成稳定 ref 后缀，避免 ISO 冒号等字符影响 URL/文件名消费。"""
    if value is None:
        return None
    # bool 也是 int 的子类，但它不是时间戳；显式排除能防止派生出 True/False 证据号。
    if isinstance(value, bool):
        return None
    raw = str(value).strip()
    if not raw:
        return None
    # 证据 ref 只保留常见安全字符；其它字符统一折叠成单个 `-`，保持可读且可比对。
    suffix = re.sub(r"[^A-Za-z0-9]+", "-", raw).strip("-")
    return suffix[:96] if suffix else None


def derive_lidar_scan_proof_evidence_ref(artifact_payload: dict[str, Any]) -> str | None:
    """从成功加载的 LiDAR artifact 获取稳定 evidence_ref，缺坏材料时调用方保持 null。"""
    proof = artifact_payload.get("proof") if isinstance(artifact_payload.get("proof"), dict) else {}
    # 已有 evidence_ref 是 producer 最强合同；既兼容根节点，也兼容 proof 子节点。
    for candidate in (artifact_payload.get("evidence_ref"), proof.get("evidence_ref")):
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    # 没有显式 ref 时，优先用毫秒时间戳，保证同一 artifact 多次 readback 得到同一 ID。
    generated_at_ms = artifact_payload.get("generated_at_ms", proof.get("generated_at_ms"))
    suffix = safe_lidar_evidence_ref_suffix(generated_at_ms)
    if suffix:
        return f"o1-lidar-scan-proof-{suffix}"
    # 旧 artifact 可能只有 ISO generated_at；保留可读时间但移除 URL/路径不友好的字符。
    generated_at = artifact_payload.get("generated_at", proof.get("generated_at"))
    suffix = safe_lidar_evidence_ref_suffix(generated_at)
    if suffix:
        return f"o1-lidar-scan-proof-{suffix}"
    return None


def finite_lidar_scan_number(value: Any) -> float | None:
    """LaserScan 文本来自 ROS2 CLI，只接受有限数字，NaN/inf 不能进入地图点位。"""
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def parse_lidar_scan_scalar(stdout_preview: str, key: str) -> float | None:
    """从 YAML 预览中读取简单数字标量，避免为一个只读预览引入额外依赖。"""
    pattern = re.compile(rf"^\s*{re.escape(key)}:\s*([^#\s]+)")
    for line in stdout_preview.splitlines():
        match = pattern.match(line)
        if match:
            return finite_lidar_scan_number(match.group(1))
    return None


def parse_lidar_scan_frame_id(stdout_preview: str) -> str:
    """frame_id 是地图叠点的坐标系来源；缺失时前端必须继续显示等待材料。"""
    for line in stdout_preview.splitlines():
        match = re.match(r"^\s*frame_id:\s*(.+?)\s*$", line)
        if match:
            return match.group(1).strip().strip("'\"")
    return ""


def parse_lidar_scan_ranges(stdout_preview: str) -> list[float | None]:
    """只解析 `ranges:` 下的列表值，保留无效槽位用于维持 source_index 和角度。"""
    ranges: list[float | None] = []
    in_ranges = False
    for raw_line in stdout_preview.splitlines():
        line = raw_line.strip()
        if line == "ranges:":
            in_ranges = True
            continue
        if not in_ranges:
            continue
        if not line.startswith("- "):
            # ROS2 YAML 的下一个顶层字段代表 ranges 已结束。
            if line and not raw_line.startswith(" "):
                break
            continue
        ranges.append(finite_lidar_scan_number(line[2:].strip()))
    return ranges


def parse_lidar_scan_stdout_preview(stdout_preview: Any) -> dict[str, Any] | None:
    """把 scan_once 的 YAML 预览转成 PC 可直接消费的相对雷达点，不启动 ROS2。"""
    if not isinstance(stdout_preview, str) or "ranges:" not in stdout_preview:
        return None
    ranges = parse_lidar_scan_ranges(stdout_preview)
    if not ranges:
        return None
    angle_min = parse_lidar_scan_scalar(stdout_preview, "angle_min")
    angle_increment = parse_lidar_scan_scalar(stdout_preview, "angle_increment")
    range_min = parse_lidar_scan_scalar(stdout_preview, "range_min") or 0.05
    range_max = parse_lidar_scan_scalar(stdout_preview, "range_max") or 30.0
    if angle_min is None:
        angle_min = -math.pi
    if angle_increment is None:
        angle_increment = (2 * math.pi) / max(len(ranges), 1)
    frame_id = parse_lidar_scan_frame_id(stdout_preview)
    step = max(1, math.ceil(len(ranges) / LIDAR_SCAN_PREVIEW_POINT_LIMIT))
    points: list[dict[str, Any]] = []
    for index in range(0, len(ranges), step):
        scan_range = ranges[index]
        # 低于 range_min 的贴脸噪声和高于 range_max 的值都不能画成真实障碍物。
        if scan_range is None or scan_range < range_min or scan_range > range_max:
            continue
        angle = angle_min + angle_increment * index
        points.append(
            {
                "x_m": scan_range * math.cos(angle),
                "y_m": scan_range * math.sin(angle),
                "range_m": scan_range,
                "angle_rad": angle,
                "frame_id": frame_id,
                "source_index": index,
            }
        )
        if len(points) >= LIDAR_SCAN_PREVIEW_POINT_LIMIT:
            break
    return {
        "scan_preview_points": points,
        "scan_preview_point_count": len(points),
        "scan_preview_source_point_count": len(ranges),
        "scan_preview_frame_id": frame_id,
        "scan_preview_angle_min": angle_min,
        "scan_preview_angle_increment": angle_increment,
        "scan_preview_range_min": range_min,
        "scan_preview_range_max": range_max,
        "scan_preview_source": "topic_reads.results.scan_once.stdout_preview",
    }


def lidar_scan_stdout_preview_from_artifact(artifact_payload: dict[str, Any]) -> str | None:
    """优先读取 collector 固定位置；找不到时再递归寻找像 LaserScan 的 stdout 预览。"""
    topic_reads = artifact_payload.get("topic_reads") if isinstance(artifact_payload.get("topic_reads"), dict) else {}
    results = topic_reads.get("results") if isinstance(topic_reads.get("results"), dict) else {}
    scan_once = results.get("scan_once") if isinstance(results.get("scan_once"), dict) else {}
    fixed_preview = scan_once.get("stdout_preview")
    if isinstance(fixed_preview, str) and "ranges:" in fixed_preview:
        return fixed_preview

    def visit(value: Any) -> str | None:
        if isinstance(value, dict):
            preview = value.get("stdout_preview")
            if isinstance(preview, str) and "ranges:" in preview and "angle_increment:" in preview:
                return preview
            for child in value.values():
                found = visit(child)
                if found:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = visit(child)
                if found:
                    return found
        return None

    return visit(artifact_payload)


def lidar_scan_preview_from_artifact(artifact_payload: dict[str, Any]) -> dict[str, Any] | None:
    """从 artifact 已有文本材料派生点位；失败时返回 None，调用方保持 fail-closed。"""
    stdout_preview = lidar_scan_stdout_preview_from_artifact(artifact_payload)
    return parse_lidar_scan_stdout_preview(stdout_preview)


def structured_lidar_scan_preview_from_artifact(artifact_payload: dict[str, Any]) -> dict[str, Any] | None:
    """读取 driver diagnostics 已落盘的结构化点位；只接受 producer 明确写出的坐标。"""
    points = artifact_payload.get("scan_preview_points")
    if not isinstance(points, list) or not points:
        return None
    return {
        "scan_preview_points": points[:LIDAR_SCAN_PREVIEW_POINT_LIMIT],
        "scan_preview_point_count": min(len(points), LIDAR_SCAN_PREVIEW_POINT_LIMIT),
        "scan_preview_source_point_count": artifact_payload.get("scan_preview_source_point_count"),
        "scan_preview_frame_id": artifact_payload.get("scan_preview_frame_id", ""),
        "scan_preview_source": artifact_payload.get("scan_preview_source", "artifact.scan_preview_points"),
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
    resolved_path = resolve_onboard_runtime_path(path)
    return {
        "path": resolved_path,
        "configured_path": path,
        "resolved_path": resolved_path,
        "canonical_path": DEFAULT_MAP_ARTIFACT_DIR,
        "configured_by": "ROBER_MAP_ARTIFACT_DIR or --map-artifact-dir",
        "expected_files": ["*.yaml", "*.pgm", "*.pbstream"],
        "schema": f"{SCHEMA}.map_lifecycle_artifact",
    }


def parse_map_yaml_for_quality(yaml_path: Path) -> dict[str, Any]:
    """只读解析 map YAML 的 image/resolution/origin，给 PC 判断是否需要重新建图。"""
    text = yaml_path.read_text(encoding="utf-8", errors="replace")
    image_name = ""
    resolution: float | None = None
    origin_values: list[float] = []
    lines = text.splitlines()
    for index, raw_line in enumerate(lines):
        line = raw_line.strip()
        if line.startswith("image:"):
            image_name = line.split(":", 1)[1].strip().strip("'\"")
        elif line.startswith("resolution:"):
            resolution = float(line.split(":", 1)[1].strip())
        elif line.startswith("origin:"):
            # map_server 常见写法是 origin: [x, y, yaw]；旧 helper 也兼容多行列表。
            inline = line.split(":", 1)[1].strip()
            if inline.startswith("[") and inline.endswith("]"):
                origin_values = [float(part.strip()) for part in inline.strip("[]").split(",") if part.strip()]
            else:
                for offset in range(1, 4):
                    if index + offset >= len(lines):
                        continue
                    value_text = lines[index + offset].strip()
                    if value_text.startswith("-"):
                        value_text = value_text[1:].strip()
                    origin_values.append(float(value_text))
    if resolution is None or len(origin_values) < 2:
        raise ValueError("map yaml missing resolution or origin")
    image_path = (yaml_path.parent / image_name) if image_name else yaml_path.with_suffix(".pgm")
    return {
        "image": str(image_path),
        "resolution": resolution,
        "origin": origin_values[:3],
    }


def read_pgm_cell_counts(image_path: Path) -> dict[str, Any]:
    """读取二进制 PGM 栅格统计；free=254/unknown=205/occupied=0 来自 ROS map_saver 输出约定。"""
    with image_path.open("rb") as pgm_file:
        if pgm_file.readline().strip() != b"P5":
            raise ValueError("map image is not binary PGM P5")
        size_line = pgm_file.readline()
        while size_line.startswith(b"#"):
            size_line = pgm_file.readline()
        width, height = [int(value) for value in size_line.split()]
        pgm_file.readline()
        data = pgm_file.read()
    free_cells = data.count(254)
    unknown_cells = data.count(205)
    occupied_cells = data.count(0)
    return {
        "width": width,
        "height": height,
        "cell_counts": {
            "free": free_cells,
            "unknown": unknown_cells,
            "occupied": occupied_cells,
            "other": len(data) - free_cells - unknown_cells - occupied_cells,
        },
    }


def read_pgm_image(image_path: Path) -> dict[str, Any]:
    """读取 P5 PGM 原始像素；地图预览只做格式转换，不改变地图内容。"""
    with image_path.open("rb") as pgm_file:
        if pgm_file.readline().strip() != b"P5":
            raise ValueError("map image is not binary PGM P5")
        size_line = pgm_file.readline()
        while size_line.startswith(b"#"):
            size_line = pgm_file.readline()
        width, height = [int(value) for value in size_line.split()]
        max_value = int(pgm_file.readline().strip() or b"255")
        if max_value <= 0 or max_value > 255:
            raise ValueError("unsupported PGM max value")
        data = pgm_file.read()
    expected_size = width * height
    if len(data) < expected_size:
        raise ValueError("PGM pixel data is shorter than width*height")
    # PGM 可能多带换行或尾部字节；预览只取声明尺寸，避免浏览器展示与 YAML 尺寸分叉。
    return {"width": width, "height": height, "pixels": data[:expected_size]}


def default_map_color_overlay(reason: str = "not_loaded") -> dict[str, Any]:
    """地图彩色层保持同形返回；缺地图时前端也能给出明确的未接入口径。"""
    return {
        "schema": "trashbot.upper_robot_api.v1.map_color_overlay",
        "status": "not_loaded",
        "source": "not_loaded",
        "map_width": 0,
        "map_height": 0,
        "occupied_boundary_points": [],
        "occupied_boundary_count": 0,
        "occupied_boundary_source_count": 0,
        "pillar_candidate_points": [],
        "pillar_candidate_count": 0,
        "pillar_candidate_source_count": 0,
        "nav2_costmap_points": [],
        "nav2_costmap_count": 0,
        "nav2_costmap_source_count": 0,
        "nav2_costmap_status": "not_loaded",
        "nav2_costmap_source": "not_loaded",
        "nav2_costmap_topics": ["/global_costmap/costmap", "/local_costmap/costmap"],
        "failure_reason": reason,
        "blocked_reasons": [reason] if reason else [],
        "plain_hint": "地图彩色层未加载。",
    }


def map_overlay_percent_point(x_cell: float, y_cell: float, width: int, height: int, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """把 PGM 像素坐标转成浏览器 SVG 百分比；直接贴在同一张地图图像上，不做 ROS 坐标猜测。"""
    left = ((float(x_cell) + 0.5) / max(1, width)) * 100.0
    top = ((float(y_cell) + 0.5) / max(1, height)) * 100.0
    point: dict[str, Any] = {
        "x_cell": round(float(x_cell), 3),
        "y_cell": round(float(y_cell), 3),
        "left": round(left, 3),
        "top": round(top, 3),
    }
    if extra:
        point.update(extra)
    return point


def evenly_sample_map_points(points: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """大地图点数可能上万；均匀抽样保留全局轮廓，避免 PC 首屏 JSON 过大。"""
    if limit <= 0 or len(points) <= limit:
        return points
    step = len(points) / float(limit)
    sampled: list[dict[str, Any]] = []
    for index in range(limit):
        sampled.append(points[min(len(points) - 1, int(index * step))])
    return sampled


def pgm_occupied_boundary_points(pixels: bytes, width: int, height: int) -> tuple[list[dict[str, Any]], int]:
    """从静态地图中抽出占用边界；边界比整片墙体更像 RViz 里的彩色轮廓。"""
    boundary: list[dict[str, Any]] = []
    occupied_source_count = 0
    for offset, value in enumerate(pixels):
        if value != 0:
            continue
        occupied_source_count += 1
        x_cell = offset % width
        y_cell = offset // width
        exposed_neighbor_count = 0
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx = x_cell + dx
            ny = y_cell + dy
            if nx < 0 or ny < 0 or nx >= width or ny >= height:
                exposed_neighbor_count += 1
                continue
            if pixels[ny * width + nx] != 0:
                exposed_neighbor_count += 1
        if exposed_neighbor_count > 0:
            boundary.append(map_overlay_percent_point(x_cell, y_cell, width, height, {"weight": exposed_neighbor_count}))
    return boundary, occupied_source_count


def pgm_pillar_candidate_points(pixels: bytes, width: int, height: int) -> tuple[list[dict[str, Any]], int]:
    """用小型连通占用块标记疑似柱子；这是静态地图提示，不替代人工确认或 Nav2 costmap。"""
    occupied = {index for index, value in enumerate(pixels) if value == 0}
    visited: set[int] = set()
    candidates: list[dict[str, Any]] = []
    for start in sorted(occupied):
        if start in visited:
            continue
        stack = [start]
        visited.add(start)
        xs: list[int] = []
        ys: list[int] = []
        while stack:
            current = stack.pop()
            x_cell = current % width
            y_cell = current // width
            xs.append(x_cell)
            ys.append(y_cell)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx = x_cell + dx
                ny = y_cell + dy
                if nx < 0 or ny < 0 or nx >= width or ny >= height:
                    continue
                neighbor = ny * width + nx
                if neighbor in occupied and neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
        area = len(xs)
        if area < 4 or area > 220:
            continue
        bbox_width = max(xs) - min(xs) + 1
        bbox_height = max(ys) - min(ys) + 1
        long_side = max(bbox_width, bbox_height)
        short_side = max(1, min(bbox_width, bbox_height))
        aspect = long_side / short_side
        if long_side > 26 or aspect > 2.8:
            continue
        cx = sum(xs) / area
        cy = sum(ys) / area
        candidates.append(map_overlay_percent_point(cx, cy, width, height, {
            "area_cells": area,
            "bbox_width_cells": bbox_width,
            "bbox_height_cells": bbox_height,
            "confidence": round(min(1.0, area / max(1, bbox_width * bbox_height)), 3),
        }))
    return candidates, len(candidates)


def map_color_overlay_for_pgm(image_path: Path) -> dict[str, Any]:
    """为 PC 地图生成彩色工程层；所有点都来自静态 PGM，Nav2 costmap 不伪造实时数据。"""
    pgm = read_pgm_image(image_path)
    width = int(pgm["width"])
    height = int(pgm["height"])
    pixels = bytes(pgm["pixels"])
    boundary_points, occupied_source_count = pgm_occupied_boundary_points(pixels, width, height)
    pillar_points, pillar_source_count = pgm_pillar_candidate_points(pixels, width, height)
    boundary_sample = evenly_sample_map_points(boundary_points, MAP_COLOR_OVERLAY_BOUNDARY_POINT_LIMIT)
    pillar_sample = evenly_sample_map_points(pillar_points, MAP_COLOR_OVERLAY_PILLAR_POINT_LIMIT)
    nav2_blocked_reason = "nav2_costmap_runtime_topic_not_captured_by_map_preview"
    return {
        "schema": "trashbot.upper_robot_api.v1.map_color_overlay",
        "status": "loaded",
        "source": "map_pgm_static_analysis",
        "map_width": width,
        "map_height": height,
        "occupied_boundary_points": boundary_sample,
        "occupied_boundary_count": len(boundary_sample),
        "occupied_boundary_source_count": len(boundary_points),
        "occupied_cell_source_count": occupied_source_count,
        "pillar_candidate_points": pillar_sample,
        "pillar_candidate_count": len(pillar_sample),
        "pillar_candidate_source_count": pillar_source_count,
        "nav2_costmap_points": [],
        "nav2_costmap_count": 0,
        "nav2_costmap_source_count": 0,
        "nav2_costmap_status": "not_loaded",
        "nav2_costmap_source": "not_loaded",
        "nav2_costmap_topics": ["/global_costmap/costmap", "/local_costmap/costmap"],
        "failure_reason": "",
        "blocked_reasons": [nav2_blocked_reason],
        "plain_hint": (
            f"静态地图彩色层已加载：边界 {len(boundary_sample)} 个点、"
            f"疑似柱子 {len(pillar_sample)} 个；Nav2 costmap 尚未接入实时 topic。"
        ),
    }


def png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
    """PNG chunk 编码保持在本文件内，避免上位机为了地图预览新增图像库依赖。"""
    return (
        struct.pack(">I", len(payload))
        + chunk_type
        + payload
        + struct.pack(">I", zlib.crc32(chunk_type + payload) & 0xFFFFFFFF)
    )


def grayscale_png_bytes(width: int, height: int, pixels: bytes) -> bytes:
    """把 8-bit 灰度栅格写成 PNG；每行 filter=0，像素值保持 PGM 原样。"""
    if width <= 0 or height <= 0 or len(pixels) < width * height:
        raise ValueError("invalid grayscale image dimensions")
    rows = [b"\x00" + pixels[row * width : (row + 1) * width] for row in range(height)]
    raw = b"".join(rows)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(raw, level=6))
        + png_chunk(b"IEND", b"")
    )


def data_url_for_pgm(image_path: Path) -> dict[str, Any]:
    """把本地 PGM 转成浏览器可直接显示的 PNG data URL。"""
    pgm = read_pgm_image(image_path)
    png_bytes = grayscale_png_bytes(int(pgm["width"]), int(pgm["height"]), bytes(pgm["pixels"]))
    return {
        "width": int(pgm["width"]),
        "height": int(pgm["height"]),
        "image_mime_type": "image/png",
        "image_data_url": "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii"),
        "source_image_format": "pgm_p5",
    }


def analyze_map_yaml_quality(path: Path) -> dict[str, Any]:
    """地图文件存在不等于可导航；free cell 为 0 时必须提示重新建图。"""
    result: dict[str, Any] = {
        "checked": path.suffix == ".yaml",
        "ok": False,
        "map_yaml": str(path),
        "image": None,
        "resolution": None,
        "origin": None,
        "width": None,
        "height": None,
        "cell_counts": {},
        "has_free_cells": False,
        "navigation_quality": "not_checked" if path.suffix != ".yaml" else "blocked",
        "failure_reason": None,
    }
    if path.suffix != ".yaml":
        return result
    try:
        yaml_quality = parse_map_yaml_for_quality(path)
        image_path = Path(str(yaml_quality["image"]))
        pgm_quality = read_pgm_cell_counts(image_path)
        cell_counts = pgm_quality["cell_counts"]
        free_cells = int(cell_counts.get("free") or 0)
        result.update(
            {
                "ok": True,
                **yaml_quality,
                **pgm_quality,
                "has_free_cells": free_cells > 0,
                "navigation_quality": "has_free_cells" if free_cells > 0 else "no_free_cells",
            }
        )
    except Exception as exc:  # noqa: BLE001 - 坏地图也要进入列表，不能让 PC 误以为没有地图。
        result["failure_reason"] = compact_error(exc)
        result["navigation_quality"] = "analysis_failed"
    return result


def summarize_map_quality(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """把多张地图压成 PC 可读摘要，避免普通首屏展示一堆文件细节。"""
    checked_entries = [entry for entry in entries if isinstance(entry.get("quality"), dict) and entry["quality"].get("checked")]
    usable_entries = [entry for entry in checked_entries if entry["quality"].get("has_free_cells")]
    no_free_entries = [
        entry for entry in checked_entries if entry["quality"].get("ok") and not entry["quality"].get("has_free_cells")
    ]
    failed_entries = [entry for entry in checked_entries if not entry["quality"].get("ok")]
    return {
        "checked_yaml_count": len(checked_entries),
        "usable_map_count": len(usable_entries),
        "no_free_cell_map_count": len(no_free_entries),
        "analysis_failed_count": len(failed_entries),
        "status": (
            "has_usable_map"
            if usable_entries
            else "no_free_cells"
            if no_free_entries
            else "analysis_failed"
            if failed_entries
            else "not_checked"
        ),
        "message": (
            "至少一张地图包含 free cell，可进入后续定位/路径检查。"
            if usable_entries
            else "当前地图没有可通行区域，需要重新建图。"
            if no_free_entries
            else "地图质量分析失败，需要检查 YAML/PGM。"
            if failed_entries
            else "没有可分析的 YAML 地图。"
        ),
    }


def safe_preview_map_name(value: str | None) -> str | None:
    """预览只接受地图基名；不允许路径、穿越或任意文件读取。"""
    if value is None:
        return None
    trimmed = str(value).strip()
    if not trimmed:
        return None
    if trimmed.endswith(".yaml"):
        trimmed = trimmed[:-5]
    if not SAFE_MAP_NAME_PATTERN.fullmatch(trimmed):
        raise ValueError("map_name_invalid_or_too_long")
    return trimmed


def path_is_under(child: Path, parent: Path) -> bool:
    """YAML image 字段也必须落在地图目录内，避免借预览读取任意文件。"""
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def map_preview_candidates(root: Path, requested_map_name: str | None) -> list[Path]:
    """按现场直觉选择地图：指定优先，其次 canonical，再选最近可用 YAML。"""
    if requested_map_name:
        return [root / f"{requested_map_name}.yaml"]
    canonical = root / "trashbot_map.yaml"
    yaml_files = sorted(root.glob("*.yaml"), key=lambda path: path.stat().st_mtime if path.exists() else 0, reverse=True)
    usable = [path for path in yaml_files if analyze_map_yaml_quality(path).get("has_free_cells")]
    candidates: list[Path] = []
    if canonical.exists():
        candidates.append(canonical)
    for path in usable + yaml_files:
        if path not in candidates:
            candidates.append(path)
    return candidates


def resolve_onboard_runtime_path(path: str) -> str:
    """map proof 相对路径统一落到 onboard workdir，避免 systemd cwd 漂到仓库根。"""
    candidate = Path(path)
    if candidate.is_absolute():
        return str(candidate)
    # 这里只改 map lifecycle 合同；其它 runtime artifact 暂不扩大迁移范围。
    return str(Path(DEFAULT_ONBOARD_WORKDIR) / candidate)


def map_lifecycle_proof_artifact_info(path: str) -> dict[str, Any]:
    """SLAM/map lifecycle runtime 材料入口，读取它也不能替代真实 ROS2 运行。"""
    resolved_path = resolve_onboard_runtime_path(path)
    return {
        "path": resolved_path,
        "configured_path": path,
        "resolved_path": resolved_path,
        "canonical_path": DEFAULT_MAP_LIFECYCLE_PROOF_ARTIFACT_PATH,
        "legacy_path": LEGACY_MAP_LIFECYCLE_PROOF_ARTIFACT_PATH,
        "compatibility_paths": [LEGACY_MAP_LIFECYCLE_PROOF_ARTIFACT_PATH],
        "legacy_exists": Path(LEGACY_MAP_LIFECYCLE_PROOF_ARTIFACT_PATH).exists(),
        "configured_by": "ROBER_MAP_LIFECYCLE_PROOF_ARTIFACT_PATH or --map-lifecycle-proof-artifact-path",
        "format": "json",
        "schema": f"{SCHEMA}.map_lifecycle_runtime_proof",
        "expected_material": [
            "/scan once",
            "/map once",
            "map yaml/image or pbstream",
            "map metadata",
            "slam_toolbox lifecycle state",
        ],
    }


def run_map_lifecycle_proof_helper(
    *,
    artifact_path: str,
    map_artifact_dir: str,
    timeout_s: float,
    map_name: str | None = None,
) -> dict[str, Any]:
    """运行 no-motion map proof helper；该入口只启动 LiDAR/SLAM，不接触底盘控制。"""
    script_path = Path(__file__).resolve().with_name("o3_map_lifecycle_proof.py")
    command = [
        sys.executable,
        str(script_path),
        "--output",
        artifact_path,
        "--map-dir",
        map_artifact_dir,
        "--timeout-s",
        str(timeout_s),
    ]
    if map_name:
        # map_name 已由 API body 白名单校验；这里仍用 argv 传参，禁止 shell 拼接。
        command.extend(["--map-name", map_name])
    started_ms = now_ms()
    try:
        completed = subprocess.run(  # noqa: S603 - command argv 固定为本仓库 helper。
            command,
            check=False,
            text=True,
            capture_output=True,
            timeout=max(timeout_s + 10.0, 15.0),
        )
        return {
            "mode": "map_lifecycle_proof_helper",
            "executed": True,
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "argv": command,
            "elapsed_ms": now_ms() - started_ms,
            "stdout_preview": completed.stdout[-4000:],
            "stderr_preview": completed.stderr[-4000:],
            "safe_to_control": False,
            "sends_motion_commands": False,
            "sends_base_motion_commands": False,
            "publishes_cmd_vel": False,
            "calls_base_manual": False,
            "uses_base_uart": False,
            "robot_control_executed": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "mode": "map_lifecycle_proof_helper",
            "executed": True,
            "ok": False,
            "argv": command,
            "elapsed_ms": now_ms() - started_ms,
            "error": compact_error(exc),
            "stdout_preview": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr_preview": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
            "safe_to_control": False,
            "sends_motion_commands": False,
            "sends_base_motion_commands": False,
            "publishes_cmd_vel": False,
            "calls_base_manual": False,
            "uses_base_uart": False,
            "robot_control_executed": False,
        }
    except Exception as exc:  # noqa: BLE001 - 现场脚本/权限问题必须结构化写回。
        return {
            "mode": "map_lifecycle_proof_helper",
            "executed": False,
            "ok": False,
            "argv": command,
            "elapsed_ms": now_ms() - started_ms,
            "error": compact_error(exc),
            "safe_to_control": False,
            "sends_motion_commands": False,
            "sends_base_motion_commands": False,
            "publishes_cmd_vel": False,
            "calls_base_manual": False,
            "uses_base_uart": False,
            "robot_control_executed": False,
        }


def nav2_runtime_proof_process_timeout_budget(
    *,
    timeout_s: float,
    managed_runtime_opt_in: bool,
    managed_timeout_s: float,
    initialpose_opt_in: bool,
    path_generation_opt_in: bool,
    path_generation_timeout_s: float,
) -> dict[str, Any]:
    """计算 HTTP refresh 等待 helper 的预算，确保 PC proxy 先收到结构化结果。"""
    # `timeout_s` 是 collector 基础观测窗口；它不应再被乘以 8，否则 PC 46s 会先超时。
    collector_timeout_s = max(float(timeout_s), 1.0)
    # path generation 是 PC `检查路径` 的主要耗时项，只在显式 opt-in 时计入预算。
    path_timeout_s = max(float(path_generation_timeout_s), 0.0) if path_generation_opt_in else 0.0
    # managed runtime 默认关闭；只有上位机需要临时拉起 localization graph 时才计入额外窗口。
    managed_window_s = max(float(managed_timeout_s), 0.0) if managed_runtime_opt_in else 0.0
    # initialpose 发布本身很短，单独给小余量，避免把定位 opt-in 和 managed 启动时间混在一起。
    initialpose_margin_s = NAV2_PROOF_PROCESS_INITIALPOSE_MARGIN_S if initialpose_opt_in else 0.0
    # 固定余量覆盖 bash/source/Python 启动、artifact 落盘和 HTTP 组装。
    raw_timeout_s = (
        collector_timeout_s
        + NAV2_PROOF_PROCESS_BASE_MARGIN_S
        + path_timeout_s
        + (NAV2_PROOF_PROCESS_PATH_MARGIN_S if path_generation_opt_in else 0.0)
        + managed_window_s
        + (NAV2_PROOF_PROCESS_MANAGED_MARGIN_S if managed_runtime_opt_in else 0.0)
        + initialpose_margin_s
    )
    # 上限仍是有限值，避免异常 helper 无限占住 HTTP；PC proxy 预算必须比它更长。
    process_timeout_s = min(max(raw_timeout_s, 15.0), NAV2_PROOF_PROCESS_TIMEOUT_CAP_S)
    return {
        "collector_timeout_s": collector_timeout_s,
        "path_generation_timeout_s": path_timeout_s,
        "managed_runtime_timeout_s": managed_window_s,
        "initialpose_margin_s": initialpose_margin_s,
        "base_margin_s": NAV2_PROOF_PROCESS_BASE_MARGIN_S,
        "path_margin_s": NAV2_PROOF_PROCESS_PATH_MARGIN_S if path_generation_opt_in else 0.0,
        "managed_margin_s": NAV2_PROOF_PROCESS_MANAGED_MARGIN_S if managed_runtime_opt_in else 0.0,
        "raw_timeout_s": raw_timeout_s,
        "process_timeout_s": process_timeout_s,
        "cap_s": NAV2_PROOF_PROCESS_TIMEOUT_CAP_S,
        "pc_proxy_budget_s": NAV2_PROOF_PC_PROXY_TIMEOUT_BUDGET_S,
        "budget_policy": "finish_before_pc_proxy_timeout_or_return_structured_timeout",
    }


def write_nav2_helper_failure_artifact(
    *,
    artifact_path: str,
    status: str,
    reason: str,
    timeout_budget: dict[str, Any],
    command_result: dict[str, Any],
    managed_runtime_opt_in: bool,
    initialpose_opt_in: bool,
    path_generation_opt_in: bool,
    partial_artifact: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """helper 进程超时/异常时也要写 latest，避免 PC 只看到 missing artifact。"""
    partial_proof = (
        partial_artifact.get("proof")
        if isinstance(partial_artifact, dict) and isinstance(partial_artifact.get("proof"), dict)
        else {}
    )
    partial_root_causes = partial_proof.get("root_causes") if isinstance(partial_proof.get("root_causes"), list) else []
    root_cause = {"layer": "upper API helper process", "reason": reason}
    base_link_to_laser_frame_transform = extract_base_link_to_laser_frame_transform(partial_proof)
    proof = {
        "status": status,
        "evidence_ref": f"o10-amcl-nav2-runtime-wrapper-failure-{now_ms()}",
        "evidence_type": "blocked_with_root_cause",
        "generated_at_ms": now_ms(),
        "partial_artifact_preserved": bool(partial_proof),
        "last_phase": partial_proof.get("last_phase"),
        "last_successful_phase": partial_proof.get("last_successful_phase"),
        "phase_history": partial_proof.get("phase_history") if isinstance(partial_proof.get("phase_history"), list) else [],
        "current_command": partial_proof.get("current_command") if isinstance(partial_proof.get("current_command"), dict) else None,
        "recent_commands": partial_proof.get("recent_commands") if isinstance(partial_proof.get("recent_commands"), list) else [],
        "package_availability": partial_proof.get("package_availability") if isinstance(partial_proof.get("package_availability"), dict) else {},
        "package_check_mode": partial_proof.get("package_check_mode"),
        "package_checks_batch_ok": bool(partial_proof.get("package_checks_batch_ok")),
        "initialpose_publish_attempted": bool(partial_proof.get("initialpose_publish_attempted", initialpose_opt_in)),
        "initialpose_published": bool(partial_proof.get("initialpose_published")),
        "amcl_pose_observed": bool(partial_proof.get("amcl_pose_observed")),
        "base_link_to_laser_frame_transform": base_link_to_laser_frame_transform,
        "localization_tf_observed": (
            partial_proof.get("localization_tf_observed")
            if isinstance(partial_proof.get("localization_tf_observed"), dict)
            else {"map_to_odom": False, "map_to_base_link": False}
        ),
        "tf_chain_observed": (
            partial_proof.get("tf_chain_observed")
            if isinstance(partial_proof.get("tf_chain_observed"), dict)
            else {
                "map_to_odom": False,
                "odom_to_base_link": False,
                "base_link_to_laser_frame": False,
                "map_to_base_link": False,
            }
        ),
        "tf_chain_diagnostics": (
            partial_proof.get("tf_chain_diagnostics")
            if isinstance(partial_proof.get("tf_chain_diagnostics"), dict)
            else {}
        ),
        "tf_topics_observed": (
            partial_proof.get("tf_topics_observed")
            if isinstance(partial_proof.get("tf_topics_observed"), dict)
            else {"/tf": False, "/tf_static": False}
        ),
        "tf_static_observed": bool(partial_proof.get("tf_static_observed")),
        "tf_frame_inventory": (
            partial_proof.get("tf_frame_inventory")
            if isinstance(partial_proof.get("tf_frame_inventory"), dict)
            else {"frames": [], "edges": [], "dynamic_edges": [], "static_edges": [], "transforms": []}
        ),
        "amcl_pose_frame_id": partial_proof.get("amcl_pose_frame_id"),
        "amcl_node_publishers": (
            partial_proof.get("amcl_node_publishers")
            if isinstance(partial_proof.get("amcl_node_publishers"), list)
            else []
        ),
        "amcl_node_subscribers": (
            partial_proof.get("amcl_node_subscribers")
            if isinstance(partial_proof.get("amcl_node_subscribers"), list)
            else []
        ),
        "amcl_param_probe_ok": bool(partial_proof.get("amcl_param_probe_ok")),
        "amcl_node_info_observed": bool(partial_proof.get("amcl_node_info_observed")),
        "amcl_tf_broadcast_param": partial_proof.get("amcl_tf_broadcast_param"),
        "amcl_frame_params": (
            partial_proof.get("amcl_frame_params")
            if isinstance(partial_proof.get("amcl_frame_params"), dict)
            else {}
        ),
        "amcl_log_tail": partial_proof.get("amcl_log_tail") if isinstance(partial_proof.get("amcl_log_tail"), str) else "",
        "managed_static_tf_processes": (
            partial_proof.get("managed_static_tf_processes")
            if isinstance(partial_proof.get("managed_static_tf_processes"), dict)
            else {}
        ),
        "static_tf_source_observed": bool(partial_proof.get("static_tf_source_observed")),
        "tf_source_root_cause_detail": (
            partial_proof.get("tf_source_root_cause_detail")
            if isinstance(partial_proof.get("tf_source_root_cause_detail"), dict)
            else {}
        ),
        "amcl_broadcast_conditions": (
            partial_proof.get("amcl_broadcast_conditions")
            if isinstance(partial_proof.get("amcl_broadcast_conditions"), dict)
            else {}
        ),
        "map_frame_observed": bool(partial_proof.get("map_frame_observed")),
        "odom_frame_observed": bool(partial_proof.get("odom_frame_observed")),
        "amcl_tf_root_cause": partial_proof.get("amcl_tf_root_cause"),
        "tf_failure_classification": (
            partial_proof.get("tf_failure_classification")
            if isinstance(partial_proof.get("tf_failure_classification"), dict)
            else {"map_to_base_link": "not_evaluated", "frame_naming_consistent": True}
        ),
        "managed_runtime_requested": bool(partial_proof.get("managed_runtime_requested", managed_runtime_opt_in)),
        "managed_runtime_started": bool(partial_proof.get("managed_runtime_started")),
        "managed_runtime_cleanup_ok": bool(partial_proof.get("managed_runtime_cleanup_ok")),
        "path_generation_requested": bool(partial_proof.get("path_generation_requested", path_generation_opt_in)),
        "path_generation_attempted": bool(partial_proof.get("path_generation_attempted")),
        "path_generated": bool(partial_proof.get("path_generated")),
        "path_generation_succeeded": bool(partial_proof.get("path_generation_succeeded")),
        "path_point_count": int(partial_proof.get("path_point_count") or 0),
        "root_causes": [*partial_root_causes, root_cause],
        "blockers": [*partial_root_causes, root_cause],
        "timeout_budget": timeout_budget,
        "command_result": command_result,
        "blocked_commands_not_sent": [
            "T=1",
            "T=13",
            "T=130",
            "T=131",
            "/cmd_vel",
            "/api/base/manual",
            "/api/nav2/start",
            "/api/nav2/stop",
            "navigate_to_pose",
            "compute_path_to_pose",
        ],
        "blocked_devices_not_opened": ["/dev/ttyS5"],
        "sends_motion_commands": False,
        "sends_base_motion_commands": False,
        "publishes_cmd_vel": False,
        "calls_base_manual": False,
        "uses_base_uart": False,
        "opens_serial": False,
        "robot_control_executed": False,
        "safe_to_control": False,
        "delivery_success": False,
        "hil_pass": False,
    }
    payload = {
        "schema": "trashbot.upper_robot_api.v1.nav2_lifecycle_runtime_proof",
        "generated_at_ms": now_ms(),
        "status": status,
        "evidence_type": "blocked_with_root_cause",
        "proof": proof,
        "software_guard": True,
        "not_proven": True,
        "sends_motion_commands": False,
        "sends_base_motion_commands": False,
        "publishes_cmd_vel": False,
        "calls_base_manual": False,
        "uses_base_uart": False,
        "opens_serial": False,
        "robot_control_executed": False,
        "safe_to_control": False,
        "delivery_success": False,
        "hil_pass": False,
    }
    write_result = atomic_write_json_artifact(artifact_path, payload)
    payload["artifact"] = {"path": artifact_path, "write": write_result}
    return payload


def read_nav2_helper_partial_artifact(artifact_path: str) -> dict[str, Any] | None:
    """timeout fallback 先读 helper 已写 partial，避免覆盖掉阶段证据链。"""
    try:
        parsed = json.loads(Path(artifact_path).read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(parsed, dict):
        return None
    proof = parsed.get("proof")
    if not isinstance(proof, dict):
        return None
    if not proof.get("phase_history") and not proof.get("last_phase"):
        return None
    return parsed


def wait_for_nav2_helper_partial_artifact(artifact_path: str, wait_s: float = 2.0) -> dict[str, Any] | None:
    """helper 收到 SIGINT 后可能还在落盘，timeout fallback 短等一次 partial。"""
    deadline = time.time() + max(0.0, wait_s)
    latest: dict[str, Any] | None = None
    while time.time() <= deadline:
        latest = read_nav2_helper_partial_artifact(artifact_path)
        if latest is not None:
            return latest
        time.sleep(0.2)
    return latest


def run_helper_bash_process_group(
    command: str,
    timeout_s: float,
    cwd: str,
    *,
    cleanup_residuals: bool = True,
    deadline_monotonic_s: float | None = None,
) -> dict[str, Any]:
    """运行 helper shell；absolute deadline 存在时 Popen 开销也计入同一预算。"""
    # absolute deadline 是同机 parent/helper 的一次性预算上界，不是允许外部传入的新控制参数。
    # 选择 monotonic clock 是为了避免墙钟校时、时区或 NTP 跳变改变 timeout 的安全语义。
    # 检查发生在 Popen 之前，确保命令构造与调度延迟不会在进程创建后被偷偷重置。
    # 这里不尝试把 absolute deadline 换算成 epoch；跨时钟域换算会重新引入 clock origin 漂移。
    # 非有限 deadline 与已经耗尽的 deadline 都属于不可信预算，必须采用同一 fail-closed 结果。
    # pre-Popen 耗尽时没有自有子进程需要 cleanup，因此禁止为了“清理”而创建一个新进程。
    # 返回结构仍模拟 timeout runner，目的是让上层复用既有结构化 artifact 路径而非另造分支。
    # wait_timeout_s 固定为零，给 artifact 留下明确的“未获得主等待预算”审计事实。
    # 旧调用不传 absolute deadline 时保留原 communicate timeout，避免影响 goal helper 等既有路径。
    if deadline_monotonic_s is not None:
        remaining_before_popen_s = float(deadline_monotonic_s) - time.monotonic()
        if not math.isfinite(float(deadline_monotonic_s)) or remaining_before_popen_s <= 0.0:
            # 已耗尽时禁止再创建子进程；上层会沿用 timeout fallback 写结构化 fail-closed artifact。
            return {
                "timed_out": True,
                "returncode": None,
                "stdout": "",
                "stderr": "",
                "process_group": None,
                "deadline_monotonic_s": deadline_monotonic_s,
                "wait_timeout_s": 0.0,
                "cleanup_result": {
                    "attempted": False,
                    "ok": True,
                    "reason": "absolute_deadline_exhausted_before_popen",
                },
                "error": {
                    "type": "TimeoutExpired",
                    "message": "helper absolute monotonic deadline exhausted before Popen",
                },
            }
    process = subprocess.Popen(  # noqa: S603 - command 由本 API 固定生成，不能来自用户输入。
        ["bash", "-lc", command],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        start_new_session=True,
    )
    try:
        # Popen 返回只说明进程已经创建，不说明剩余预算仍等于最初的 relative timeout。
        # 因此必须再次读取同一 monotonic clock，扣除 bash 调度、source 与 Python startup 的成本。
        # communicate 的 timeout 是 parent 剩余量；helper 自己也消费同一个 absolute deadline。
        # 两层使用同一截止点，才能保证 helper 的 final reserve 不被 parent startup 抢占。
        # legacy 分支没有 absolute deadline，才允许继续使用调用者传入的完整 relative timeout。
        # parent/helper 共用 absolute deadline 时，bash/source/Python startup 不再获得免费预算。
        remaining_after_popen_s = (
            float(deadline_monotonic_s) - time.monotonic()
            if deadline_monotonic_s is not None
            else float(timeout_s)
        )
        # artifact/result 中的 remaining 固定非负；负值只作为“Popen 已耗尽预算”的判定事实。
        # 钳制为零只服务于序列化和 TimeoutExpired；它绝不能变成下一轮新的完整等待预算。
        # 非有限 remaining 同样 fail closed，避免 NaN 绕过 <=0 比较后进入不可预测的 wait。
        # post-Popen 耗尽与 pre-Popen 不同：此时 parent 已拥有进程组，必须进入既有清理路径。
        # 手工抛 TimeoutExpired 可复用同一 SIGINT、grace wait、residual cleanup 与 fallback 合同。
        # 该路径只清理 start_new_session 创建的自有 PGID，不扩大到系统上其他 ROS 进程。
        wait_timeout_s = max(remaining_after_popen_s, 0.0) if math.isfinite(remaining_after_popen_s) else 0.0
        if not math.isfinite(remaining_after_popen_s) or remaining_after_popen_s <= 0.0:
            raise subprocess.TimeoutExpired(["bash", "-lc", command], wait_timeout_s)
        stdout, stderr = process.communicate(timeout=wait_timeout_s)
        return {
            "timed_out": False,
            "returncode": process.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "process_group": process.pid,
            "deadline_monotonic_s": deadline_monotonic_s,
            "wait_timeout_s": wait_timeout_s,
            "cleanup_result": {"attempted": False, "ok": True, "reason": "process_exited_before_timeout"},
        }
    except subprocess.TimeoutExpired as exc:
        cleanup_result: dict[str, Any] = {
            "attempted": True,
            "process_group": process.pid,
            "sent_signal": None,
            "killed_with_sigkill": False,
            "ok": False,
            "error": None,
        }
        try:
            os.killpg(process.pid, signal.SIGINT)
            cleanup_result["sent_signal"] = "SIGINT"
        except ProcessLookupError:
            cleanup_result["sent_signal"] = "already_exited"
        try:
            stdout, stderr = process.communicate(timeout=4.0)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
                cleanup_result["killed_with_sigkill"] = True
            except ProcessLookupError:
                pass
            stdout, stderr = process.communicate()
        except Exception as cleanup_exc:  # noqa: BLE001 - 清场异常也要写进 artifact。
            stdout = preview_text(exc.stdout, 4000)
            stderr = preview_text(exc.stderr, 4000)
            cleanup_result["error"] = compact_error(cleanup_exc)
        if cleanup_residuals:
            cleanup_result["residual_cleanup"] = cleanup_nav2_helper_residual_processes()
        else:
            # 复用外部 Nav2 lifecycle 时，helper 超时只能清自己的进程组，不能扫杀现场 ROS 栈。
            cleanup_result["residual_cleanup"] = {
                "attempted": False,
                "ok": True,
                "reason": "skipped_external_runtime_cleanup",
            }
        cleanup_result["ok"] = process.poll() is not None and cleanup_result["residual_cleanup"].get("ok") is True
        return {
            "timed_out": True,
            "returncode": process.returncode,
            "stdout": stdout or preview_text(exc.stdout, 4000),
            "stderr": stderr or preview_text(exc.stderr, 4000),
            "process_group": process.pid,
            "deadline_monotonic_s": deadline_monotonic_s,
            "wait_timeout_s": wait_timeout_s,
            "cleanup_result": cleanup_result,
            "error": compact_error(exc),
        }


def cleanup_nav2_helper_residual_processes() -> dict[str, Any]:
    """helper 被强杀时 managed runtime 可能另起进程组；这里按本项目命令特征兜底清场。"""
    patterns = (
        "rober_nav2_localization_",
        "ros2 run ros2_trashbot_hardware lidar_driver",
        "ros2_trashbot_hardware/lidar_driver",
        "ros2 run nav2_map_server map_server",
        "/nav2_map_server/map_server",
        "ros2 run nav2_amcl amcl",
        "/nav2_amcl/amcl",
        "ros2 run tf2_ros static_transform_publisher",
    )
    try:
        completed = subprocess.run(
            ["ps", "-eo", "pid=,pgid=,command="],
            check=False,
            text=True,
            capture_output=True,
            timeout=5.0,
        )
    except Exception as exc:  # noqa: BLE001 - 清理失败仍要结构化回传。
        return {"attempted": True, "ok": False, "error": compact_error(exc), "matched": []}
    current_pid = os.getpid()
    matched: list[dict[str, Any]] = []
    pgids: set[int] = set()
    for raw_line in completed.stdout.splitlines():
        parts = raw_line.strip().split(None, 2)
        if len(parts) != 3:
            continue
        pid_text, pgid_text, command_text = parts
        try:
            pid = int(pid_text)
            pgid = int(pgid_text)
        except ValueError:
            continue
        if pid == current_pid:
            continue
        if not any(pattern in command_text for pattern in patterns):
            continue
        matched.append({"pid": pid, "pgid": pgid, "command": command_text[:240]})
        if pgid > 0 and pgid != os.getpgrp():
            pgids.add(pgid)
    for pgid in sorted(pgids):
        try:
            os.killpg(pgid, signal.SIGINT)
        except ProcessLookupError:
            pass
    if pgids:
        time.sleep(2.0)
    for pgid in sorted(pgids):
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    time.sleep(0.3 if pgids else 0.0)
    remaining: list[dict[str, Any]] = []
    try:
        check = subprocess.run(
            ["ps", "-eo", "pid=,pgid=,command="],
            check=False,
            text=True,
            capture_output=True,
            timeout=5.0,
        )
        for raw_line in check.stdout.splitlines():
            parts = raw_line.strip().split(None, 2)
            if len(parts) != 3:
                continue
            pid_text, pgid_text, command_text = parts
            if any(pattern in command_text for pattern in patterns):
                remaining.append({"pid": int(pid_text), "pgid": int(pgid_text), "command": command_text[:240]})
    except Exception as exc:  # noqa: BLE001
        return {"attempted": True, "ok": False, "matched": matched, "killed_pgids": sorted(pgids), "error": compact_error(exc)}
    return {
        "attempted": True,
        "ok": not remaining,
        "matched": matched,
        "killed_pgids": sorted(pgids),
        "remaining": remaining,
    }


def run_nav2_runtime_proof_helper(
    *,
    artifact_path: str,
    map_proof_path: str,
    map_artifact_dir: str,
    timeout_s: float,
    managed_runtime_opt_in: bool,
    managed_timeout_s: float,
    managed_map_yaml: str,
    initialpose_opt_in: bool,
    initialpose_x: float,
    initialpose_y: float,
    initialpose_yaw: float,
    initialpose_frame_id: str,
    path_generation_opt_in: bool,
    path_generation_timeout_s: float,
    path_goal_frame_id: str,
    path_goal_x: float,
    path_goal_y: float,
    path_goal_yaw: float,
    reuse_existing_lidar_lifecycle: bool = False,
    initialpose_canonical_free_cell_opt_in: bool = False,
) -> dict[str, Any]:
    """运行 no-motion AMCL/Nav2 collector；managed runtime 与 initialpose 都必须显式 opt-in。"""
    script_path = Path(__file__).resolve().with_name("o10_amcl_nav2_runtime_proof.py")
    # 外层进程预算仍由 API 的既有公式计算，不能为了 helper 收口而放大 HTTP 等待窗口。
    timeout_budget = nav2_runtime_proof_process_timeout_budget(
        timeout_s=timeout_s,
        managed_runtime_opt_in=managed_runtime_opt_in,
        managed_timeout_s=managed_timeout_s,
        initialpose_opt_in=initialpose_opt_in,
        path_generation_opt_in=path_generation_opt_in,
        path_generation_timeout_s=path_generation_timeout_s,
    )
    # producer 合同先冻结 absolute deadline，再开始拼接 argv；这样 argv 构造也不能免费消耗 reserve。
    # relative timeout 仍是预算公式的结果，absolute deadline 只是把这份预算绑定到 parent clock origin。
    # 两个参数同时下发是兼容迁移要求：旧审计仍能读取 relative，更新后的 helper 取二者更早值。
    # 禁止只把 absolute deadline 传给 helper 却让 parent communicate 重开 80 秒，否则双层仍会漂移。
    # 禁止只收紧 parent 却不给 helper deadline，否则 helper 无法在 SIGINT 前主动进入 final assembly。
    # deadline 在本函数每次调用只计算一次；重复读取并重算会把准备开销重新送回预算。
    # 该 monotonic 数值只在同机子进程间有效，不写成可跨主机重放的长期业务时间戳。
    # parent 在命令构造和 Popen 前冻结同机 monotonic deadline，startup 也必须消费 80s 外层预算。
    process_timeout_s = timeout_budget["process_timeout_s"]
    parent_deadline_monotonic_s = time.monotonic() + process_timeout_s
    timeout_budget = {
        **timeout_budget,
        "outer_process_deadline_monotonic_s": parent_deadline_monotonic_s,
        "deadline_source": "parent_absolute_monotonic",
    }
    helper_argv = [
        sys.executable,
        str(script_path),
        "--output",
        artifact_path,
        "--map-proof",
        map_proof_path,
        "--map-dir",
        map_artifact_dir,
        "--timeout-s",
        str(timeout_s),
        # helper 必须消费同一 outer budget，才能在 API 发信号前主动预留 final artifact 收口时间。
        "--outer-process-timeout-s",
        str(process_timeout_s),
        # absolute 值来自 relative 预算的一次加法，因此它只能维持或收紧剩余时间，不能扩大预算。
        # helper 对无效 absolute 值 fail closed；parent 也会在 Popen 前独立检查，形成双层防线。
        # relative 参数继续保留；absolute 参数只收紧 clock origin，不能扩大兼容预算。
        "--outer-process-deadline-monotonic-s",
        str(parent_deadline_monotonic_s),
    ]
    if managed_runtime_opt_in:
        # managed runtime 默认关闭；只有 body 明确 opt-in 才允许 helper 短暂拉起 localization graph。
        helper_argv.extend(
            [
                "--managed-runtime-opt-in",
                "--managed-timeout-s",
                str(managed_timeout_s),
            ]
        )
        if managed_map_yaml:
            helper_argv.extend(["--managed-map-yaml", managed_map_yaml])
        if reuse_existing_lidar_lifecycle:
            # O11 已拥有 LiDAR 时，O10 只能复用当前 lifecycle，禁止再启动第二个 serial driver。
            helper_argv.append("--reuse-existing-lidar-lifecycle")
    if initialpose_opt_in:
        # 只有 HTTP body 明确 opt-in 时才把定位种子传给 helper，避免默认 refresh 变成写 topic。
        helper_argv.extend(
            [
                "--initialpose-opt-in",
                "--initialpose-x",
                str(initialpose_x),
                "--initialpose-y",
                str(initialpose_y),
                "--initialpose-yaw",
                str(initialpose_yaw),
                "--initialpose-frame-id",
                initialpose_frame_id,
            ]
        )
        if initialpose_canonical_free_cell_opt_in:
            # initialpose 只能消费 canonical map 可复算 free-cell，不允许 HTTP x/y 直接落地。
            helper_argv.append("--initialpose-canonical-free-cell-opt-in")
    if path_generation_opt_in:
        # 路径生成同样必须显式 opt-in，默认 refresh 只做只读定位 proof。
        helper_argv.extend(
            [
                "--path-generation-opt-in",
                "--path-generation-timeout-s",
                str(path_generation_timeout_s),
                "--path-goal-frame-id",
                path_goal_frame_id,
                "--path-goal-x",
                str(path_goal_x),
                "--path-goal-y",
                str(path_goal_y),
                "--path-goal-yaw",
                str(path_goal_yaw),
            ]
        )
    ros_setup_parts = [
        "source /opt/ros/humble/setup.bash",
        f"if [ -f {shlex.quote(str(Path(DEFAULT_ONBOARD_WORKDIR) / 'install' / 'setup.bash'))} ]; then source {shlex.quote(str(Path(DEFAULT_ONBOARD_WORKDIR) / 'install' / 'setup.bash'))}; fi",
    ]
    helper_command = " && ".join(ros_setup_parts + [shlex.join(helper_argv)])
    started_ms = now_ms()
    try:
        completed = run_helper_bash_process_group(
            helper_command,
            process_timeout_s,
            DEFAULT_ONBOARD_WORKDIR,
            cleanup_residuals=managed_runtime_opt_in,
            deadline_monotonic_s=parent_deadline_monotonic_s,
        )
        if completed.get("timed_out"):
            partial_artifact = wait_for_nav2_helper_partial_artifact(artifact_path)
            timeout_reason = (
                "helper_process_timeout_after_partial_artifact"
                if partial_artifact is not None
                else "helper_process_timeout_before_artifact"
            )
            command_result = {
                "mode": "o10_amcl_nav2_runtime_proof_helper",
                "executed": True,
                "ok": False,
                "argv": ["bash", "-lc", helper_command],
                "helper_argv": helper_argv,
                "elapsed_ms": now_ms() - started_ms,
                "timeout_budget": timeout_budget,
                "process_timeout_s": process_timeout_s,
                "outer_process_deadline_monotonic_s": parent_deadline_monotonic_s,
                "process_wait_timeout_s": completed.get("wait_timeout_s"),
                "error": completed.get("error") or {"type": "TimeoutExpired", "message": "helper process timed out"},
                "stdout_preview": str(completed.get("stdout") or "")[-4000:],
                "stderr_preview": str(completed.get("stderr") or "")[-4000:],
                "helper_process_group": completed.get("process_group"),
                "helper_cleanup_result": completed.get("cleanup_result"),
                "safe_to_control": False,
                "sends_base_motion_commands": False,
                "publishes_cmd_vel": False,
                "calls_base_manual": False,
                "managed_runtime_opt_in": managed_runtime_opt_in,
                "initialpose_opt_in": initialpose_opt_in,
                "path_generation_opt_in": path_generation_opt_in,
                "robot_control_executed": False,
                "hil_pass": False,
            }
            fallback_artifact = write_nav2_helper_failure_artifact(
                artifact_path=artifact_path,
                status="blocked_with_root_cause",
                reason=timeout_reason,
                timeout_budget=timeout_budget,
                command_result=command_result,
                managed_runtime_opt_in=managed_runtime_opt_in,
                initialpose_opt_in=initialpose_opt_in,
                path_generation_opt_in=path_generation_opt_in,
                partial_artifact=partial_artifact,
            )
            command_result["fallback_artifact_written"] = fallback_artifact.get("artifact", {}).get("write", {}).get("ok") is True
            command_result["partial_artifact_preserved"] = partial_artifact is not None
            return command_result
        return {
            "mode": "o10_amcl_nav2_runtime_proof_helper",
            "executed": True,
            "ok": completed["returncode"] == 0,
            "returncode": completed["returncode"],
            "argv": ["bash", "-lc", helper_command],
            "helper_argv": helper_argv,
            "elapsed_ms": now_ms() - started_ms,
            "timeout_budget": timeout_budget,
            "process_timeout_s": process_timeout_s,
            "outer_process_deadline_monotonic_s": parent_deadline_monotonic_s,
            "process_wait_timeout_s": completed.get("wait_timeout_s"),
            "stdout_preview": str(completed.get("stdout") or "")[-4000:],
            "stderr_preview": str(completed.get("stderr") or "")[-4000:],
            "helper_process_group": completed.get("process_group"),
            "helper_cleanup_result": completed.get("cleanup_result"),
            "safe_to_control": False,
            "sends_base_motion_commands": False,
            "publishes_cmd_vel": False,
            "calls_base_manual": False,
            "managed_runtime_opt_in": managed_runtime_opt_in,
            "initialpose_opt_in": initialpose_opt_in,
            "path_generation_opt_in": path_generation_opt_in,
            "robot_control_executed": False,
            "hil_pass": False,
        }
    except subprocess.TimeoutExpired as exc:
        partial_artifact = wait_for_nav2_helper_partial_artifact(artifact_path)
        timeout_reason = (
            "helper_process_timeout_after_partial_artifact"
            if partial_artifact is not None
            else "helper_process_timeout_before_artifact"
        )
        cleanup_result = {}
        if isinstance(getattr(exc, "cmd", None), list):
            cleanup_result = {"attempted": True, "ok": True, "reason": "process_group_cleanup_attempted_before_timeout_response"}
        command_result = {
            "mode": "o10_amcl_nav2_runtime_proof_helper",
            "executed": True,
            "ok": False,
            "argv": ["bash", "-lc", helper_command],
            "helper_argv": helper_argv,
            "elapsed_ms": now_ms() - started_ms,
            "timeout_budget": timeout_budget,
            "process_timeout_s": process_timeout_s,
            "outer_process_deadline_monotonic_s": parent_deadline_monotonic_s,
            "error": compact_error(exc),
            "stdout_preview": preview_text(exc.stdout, 4000),
            "stderr_preview": preview_text(exc.stderr, 4000),
            "helper_cleanup_result": cleanup_result,
            "safe_to_control": False,
            "sends_base_motion_commands": False,
            "publishes_cmd_vel": False,
            "calls_base_manual": False,
            "managed_runtime_opt_in": managed_runtime_opt_in,
            "initialpose_opt_in": initialpose_opt_in,
            "path_generation_opt_in": path_generation_opt_in,
            "robot_control_executed": False,
            "hil_pass": False,
        }
        fallback_artifact = write_nav2_helper_failure_artifact(
            artifact_path=artifact_path,
            status="blocked_with_root_cause",
            reason=timeout_reason,
            timeout_budget=timeout_budget,
            command_result=command_result,
            managed_runtime_opt_in=managed_runtime_opt_in,
            initialpose_opt_in=initialpose_opt_in,
            path_generation_opt_in=path_generation_opt_in,
            partial_artifact=partial_artifact,
        )
        command_result["fallback_artifact_written"] = fallback_artifact.get("artifact", {}).get("write", {}).get("ok") is True
        command_result["partial_artifact_preserved"] = partial_artifact is not None
        return {
            **command_result,
        }
    except Exception as exc:  # noqa: BLE001 - 远端 Python/权限缺口必须给出结构化 blocker。
        command_result = {
            "mode": "o10_amcl_nav2_runtime_proof_helper",
            "executed": False,
            "ok": False,
            "argv": ["bash", "-lc", helper_command],
            "helper_argv": helper_argv,
            "elapsed_ms": now_ms() - started_ms,
            "timeout_budget": timeout_budget,
            "process_timeout_s": process_timeout_s,
            "outer_process_deadline_monotonic_s": parent_deadline_monotonic_s,
            "error": compact_error(exc),
            "safe_to_control": False,
            "sends_base_motion_commands": False,
            "publishes_cmd_vel": False,
            "calls_base_manual": False,
            "managed_runtime_opt_in": managed_runtime_opt_in,
            "initialpose_opt_in": initialpose_opt_in,
            "path_generation_opt_in": path_generation_opt_in,
            "robot_control_executed": False,
            "hil_pass": False,
        }
        fallback_artifact = write_nav2_helper_failure_artifact(
            artifact_path=artifact_path,
            status="blocked_with_root_cause",
            reason="helper_process_exception_before_artifact",
            timeout_budget=timeout_budget,
            command_result=command_result,
            managed_runtime_opt_in=managed_runtime_opt_in,
            initialpose_opt_in=initialpose_opt_in,
            path_generation_opt_in=path_generation_opt_in,
        )
        command_result["fallback_artifact_written"] = fallback_artifact.get("artifact", {}).get("write", {}).get("ok") is True
        return {
            **command_result,
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
    resolved_path = resolve_onboard_runtime_path(path)
    return {
        "path": resolved_path,
        "configured_path": path,
        "resolved_path": resolved_path,
        "canonical_path": DEFAULT_NAV2_LIFECYCLE_ARTIFACT_PATH,
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


def nav2_goal_execution_artifact_info(path: str) -> dict[str, Any]:
    """Nav2 目标执行 artifact 只记录一次 bounded NavigateToPose，不等同交付成功。"""
    resolved_path = resolve_onboard_runtime_path(path)
    return {
        "path": resolved_path,
        "configured_path": path,
        "resolved_path": resolved_path,
        "canonical_path": DEFAULT_NAV2_GOAL_EXECUTION_ARTIFACT_PATH,
        "configured_by": "ROBER_NAV2_GOAL_EXECUTION_ARTIFACT_PATH or --nav2-goal-execution-artifact-path",
        "format": "json",
        "schema": f"{SCHEMA}.nav2_goal_execution_proof",
        "expected_material": [
            "NavigateToPose action server availability",
            "goal accepted/rejected",
            "bounded result or cancel response",
            "feedback distance remaining samples",
        ],
    }


def bool_field_true(value: Any) -> bool:
    """兼容 bool 和 JSON 字符串；外层证明字段不能被任意 truthy 文本误抬高。"""
    return value is True or (isinstance(value, str) and value.strip().lower() == "true")


def nav2_goal_execution_proven_from_latest_result(latest_result: dict[str, Any]) -> bool:
    """完整 Nav2 路线必须同窗口 wheel L/R 非零；action success 本身只算导航返回。"""
    if not isinstance(latest_result, dict):
        return False
    base_feedback = latest_result.get("base_feedback_summary") if isinstance(latest_result.get("base_feedback_summary"), dict) else {}
    wheel_nonzero = bool_field_true(base_feedback.get("wheel_feedback_lr_nonzero_proven"))
    if not wheel_nonzero:
        return False
    if bool_field_true(latest_result.get("nav2_goal_execution_proven")):
        return True
    return (
        latest_result.get("status") == "goal_succeeded"
        and bool_field_true(latest_result.get("goal_accepted"))
        and bool_field_true(latest_result.get("result_received"))
        and latest_result.get("result_status") == "succeeded"
        and bool_field_true(latest_result.get("robot_control_executed"))
    )


def nav2_goal_execution_not_proven_reasons(latest_result: dict[str, Any], proven: bool) -> list[str]:
    """外层 execute 回包要解释还差什么，不能只留下泛化 delivery 缺口。"""
    reasons = ["delivery_success", "operator_dropoff_confirmation"]
    if proven:
        return reasons
    status = latest_result.get("status") if isinstance(latest_result, dict) else "not_loaded"
    base_feedback = latest_result.get("base_feedback_summary") if isinstance(latest_result.get("base_feedback_summary"), dict) else {}
    wheel_nonzero = bool_field_true(base_feedback.get("wheel_feedback_lr_nonzero_proven"))
    if status == "goal_succeeded" and not wheel_nonzero:
        return ["wheel_feedback_lr_nonzero", *reasons]
    return ["nav2_goal_execution", *reasons]


def enrich_nav2_goal_execution_latest_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """latest 只读回包补派生结论，旧 artifact 不改盘也能暴露 wheel raw 根因。"""
    latest_result = payload.get("latest_result") if isinstance(payload.get("latest_result"), dict) else {}
    if not latest_result:
        return payload
    proven = nav2_goal_execution_proven_from_latest_result(latest_result)
    reasons = nav2_goal_execution_not_proven_reasons(latest_result, proven)
    hil_pass = bool(latest_result.get("hil_pass")) and proven
    enriched_latest = dict(latest_result)
    enriched_latest["nav2_goal_execution_proven"] = proven
    enriched_latest["hil_pass"] = hil_pass
    enriched_latest["not_proven"] = reasons
    payload["latest_result"] = enriched_latest
    payload["status"] = enriched_latest.get("status") or payload.get("status")
    payload["result_status"] = enriched_latest.get("result_status")
    payload["goal_accepted"] = bool_field_true(enriched_latest.get("goal_accepted"))
    payload["result_received"] = bool_field_true(enriched_latest.get("result_received"))
    payload["base_command_mode"] = enriched_latest.get("base_command_mode")
    payload["next_base_command_mode"] = nav2_goal_next_base_command_mode(enriched_latest)
    payload["nav2_goal_execution_proven"] = proven
    payload["nav2_goal_execution_not_proven"] = reasons
    payload["hil_pass"] = hil_pass
    payload["not_proven"] = reasons
    base_feedback = enriched_latest.get("base_feedback_summary") if isinstance(enriched_latest.get("base_feedback_summary"), dict) else {}
    payload["wheel_feedback_lr_nonzero_proven"] = bool_field_true(base_feedback.get("wheel_feedback_lr_nonzero_proven"))
    payload["wheel_feedback_summary"] = base_feedback
    base_command = enriched_latest.get("base_command_summary") if isinstance(enriched_latest.get("base_command_summary"), dict) else {}
    payload["base_command_summary"] = base_command
    payload["robot_control_executed"] = False
    payload["readback_robot_control_executed"] = bool_field_true(enriched_latest.get("robot_control_executed"))
    payload["sends_motion_commands"] = False
    payload["readback_sends_motion_commands"] = bool_field_true(enriched_latest.get("sends_motion_commands"))
    payload["sends_base_motion_commands"] = False
    payload["readback_sends_base_motion_commands"] = bool_field_true(enriched_latest.get("sends_base_motion_commands"))
    payload["publishes_cmd_vel"] = False
    payload["readback_publishes_cmd_vel"] = enriched_latest.get("publishes_cmd_vel")
    payload["delivery_success"] = False
    payload["safe_to_control"] = False
    payload["primary_actions_enabled"] = False
    return payload


def nav2_goal_next_base_command_mode(latest_result: dict[str, Any]) -> str:
    """基于上次执行证据给下一次建议模式；只读建议不自动发车。"""
    raw_mode = latest_result.get("base_command_mode")
    mode = raw_mode.strip().lower() if isinstance(raw_mode, str) else DEFAULT_NAV2_BASE_COMMAND_MODE
    if mode not in ALLOWED_NAV2_BASE_COMMAND_MODES:
        mode = DEFAULT_NAV2_BASE_COMMAND_MODE
    base_feedback = latest_result.get("base_feedback_summary") if isinstance(latest_result.get("base_feedback_summary"), dict) else {}
    if bool_field_true(base_feedback.get("wheel_feedback_lr_nonzero_proven")):
        return mode
    if (
        bool_field_true(base_feedback.get("motion_signal_observed"))
        or bool_field_true(base_feedback.get("imu_attitude_delta_observed"))
    ):
        return mode
    # 当前 WAVE ROVER 现场已证明 T=13 可能持续 L/R=0/0；缺运动信号时回到 vendor PWM164。
    return "pwm"


def nav2_goal_execute_base_command_mode_from_latest(default_mode: str, latest_payload: dict[str, Any]) -> str:
    """未显式指定时复用 latest 的下一次模式，避免 ROS/T=13 零轮速后无限重复同一路径。"""
    configured = default_mode if default_mode in ALLOWED_NAV2_BASE_COMMAND_MODES else DEFAULT_NAV2_BASE_COMMAND_MODE
    next_mode = latest_payload.get("next_base_command_mode")
    if not isinstance(next_mode, str):
        return configured
    normalized = next_mode.strip().lower()
    return normalized if normalized in ALLOWED_NAV2_BASE_COMMAND_MODES else configured


def delivery_completion_artifact_info(path: str) -> dict[str, Any]:
    """送达完成 artifact 只由 delivery gate 写入，不能由 Nav2 或 operator report 单独替代。"""
    resolved_path = resolve_onboard_runtime_path(path)
    return {
        "path": resolved_path,
        "configured_path": path,
        "resolved_path": resolved_path,
        "canonical_path": DEFAULT_DELIVERY_COMPLETION_ARTIFACT_PATH,
        "configured_by": "ROBER_DELIVERY_COMPLETION_ARTIFACT_PATH or --delivery-completion-artifact-path",
        "format": "json",
        "schema": f"{SCHEMA}.delivery_completion_result",
        "expected_material": [
            "latest NavigateToPose goal_succeeded",
            "operator report ready_for_review",
            "structured_hil_claims.delivery_success=true",
            "route/map evidence ref",
            "motion/stop observation",
        ],
    }


def free_roam_autonomy_artifact_info(path: str) -> dict[str, Any]:
    """自动扫图 runtime artifact 只证明状态机读数，不等同 PC 自动发车已开放。"""
    resolved_path = resolve_onboard_runtime_path(path)
    return {
        "path": resolved_path,
        "configured_path": path,
        "resolved_path": resolved_path,
        "canonical_path": DEFAULT_FREE_ROAM_AUTONOMY_ARTIFACT_PATH,
        "configured_by": "ROBER_FREE_ROAM_AUTONOMY_ARTIFACT_PATH or --free-roam-autonomy-artifact-path",
        "format": "json",
        "schema": "trashbot.free_roam_autonomy.runtime.v1",
        "expected_material": [
            "/scan finite min distance and freshness",
            "/map free/unknown coverage metrics",
            "FreeRoamDecision state and gates",
            "stop_required and artifact_only/cmd_vel publish boundary",
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


def operator_report_artifact_info(path: str) -> dict[str, Any]:
    """operator report 是人工现场材料入口，不能被下游当成控制或 HIL 结果。"""
    return {
        "path": path,
        "configured_by": "ROBER_OPERATOR_REPORT_ARTIFACT_PATH or --operator-report-artifact-path",
        "format": "json",
        "schema": f"{SCHEMA}.operator_report_result",
    }


def operator_report_guard_flags() -> dict[str, Any]:
    """operator report 只收材料；这些固定假值防止 PC 把报告误解成 ACK 或可控状态。"""
    return {
        "operator_report_material_only": True,
        "software_guard": True,
        "not_proven": True,
        "evidence_type": "software_guard",
        "report_replaces_stop_status_ack_or_hil": False,
        "field_hil_material": False,
        "readback_sends_commands": False,
        "sends_commands": False,
        "sends_motion_commands": False,
        "sends_base_motion_commands": False,
        "publishes_cmd_vel": False,
        "calls_base_manual": False,
        "uses_base_uart": False,
        "opens_serial": False,
        "starts_ros2": False,
        "robot_control_executed": False,
        "hil_pass": False,
        **proof_flags(),
    }


def coerce_report_bool(value: Any) -> bool | None:
    """PC 表单和 SSH 手写 JSON 都可能传字符串布尔值，归一化时宁可保守失败。"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "on"}:
            return True
        if normalized in {"false", "0", "no", "n", "off"}:
            return False
    return None


def normalize_optional_report_text(value: Any) -> str | None:
    """结构化材料引用允许留空；有值时统一成短字符串，便于 artifact 稳定 diff。"""
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def normalize_structured_hil_claims(report: dict[str, Any]) -> dict[str, Any]:
    """把 HIL 细分声明提升为机器字段；它们仍只是材料 claim，不会翻转 HIL pass。"""
    nested_claims = report.get("structured_hil_claims")
    if not isinstance(nested_claims, dict):
        nested_claims = {}
    claims: dict[str, Any] = {}
    missing_or_invalid_bool_fields: list[str] = []
    provided_fields: list[str] = []
    for field in OPERATOR_REPORT_HIL_BOOL_CLAIM_FIELDS:
        # 顶层字段服务 curl/PC 表单，nested 字段服务未来稳定 schema；顶层优先便于人工覆盖。
        raw_value = report[field] if field in report else nested_claims.get(field)
        value = coerce_report_bool(raw_value)
        claims[field] = value
        if raw_value is not None:
            provided_fields.append(field)
        if raw_value is not None and value is None:
            missing_or_invalid_bool_fields.append(field)
    for field in OPERATOR_REPORT_HIL_REF_CLAIM_FIELDS:
        raw_value = report[field] if field in report else nested_claims.get(field)
        claims[field] = normalize_optional_report_text(raw_value)
        if raw_value is not None:
            provided_fields.append(field)
    claims["normalization"] = {
        "source": "top_level_fields_or_structured_hil_claims",
        "source_fields": list(OPERATOR_REPORT_STRUCTURED_HIL_FIELDS),
        "provided_fields": provided_fields,
        "missing_or_invalid_bool_fields": missing_or_invalid_bool_fields,
        "material_only": True,
        "top_level_delivery_success_forced_false": True,
    }
    return claims


def normalize_operator_report(report: dict[str, Any] | None) -> tuple[dict[str, Any] | None, str]:
    """把人工报告拆成执行前安全字段和执行后观察字段，避免用事后材料放行运动。"""
    if report is None:
        return None, "missing"
    normalized: dict[str, Any] = {}
    evidence_ref = report.get("evidence_ref")
    normalized["evidence_ref"] = str(evidence_ref).strip() if evidence_ref else None
    preflight_missing_or_invalid: list[str] = []
    review_missing_or_invalid: list[str] = []
    unsafe_fields: list[str] = []
    for field in OPERATOR_REPORT_PREFLIGHT_BOOL_FIELDS:
        value = coerce_report_bool(report.get(field))
        normalized[field] = value
        if value is None:
            preflight_missing_or_invalid.append(field)
        elif value is False:
            unsafe_fields.append(field)
    for field in OPERATOR_REPORT_REVIEW_BOOL_FIELDS:
        value = coerce_report_bool(report.get(field))
        normalized[field] = value
        if value is None:
            review_missing_or_invalid.append(field)
    # PC 侧当前发送 note；runner 历史字段是 operator_notes，这里兼容两种入口。
    notes = report.get("operator_notes", report.get("note"))
    normalized["operator_notes"] = "" if notes is None else str(notes)
    normalized["note"] = normalized["operator_notes"]
    reported_at = report.get("reported_at")
    normalized["reported_at"] = str(reported_at).strip() if reported_at else None
    structured_hil_claims = normalize_structured_hil_claims(report)
    normalized["structured_hil_claims"] = structured_hil_claims
    for field in OPERATOR_REPORT_REQUIRED_REVIEW_TEXT_FIELDS:
        value = normalized.get(field)
        if not isinstance(value, str) or not value.strip():
            review_missing_or_invalid.append(field)
    status = "ready_for_execution"
    if preflight_missing_or_invalid or unsafe_fields:
        status = "unsafe_or_incomplete"
    elif not review_missing_or_invalid and all(normalized.get(field) is True for field in OPERATOR_REPORT_REVIEW_BOOL_FIELDS):
        status = "ready_for_review"
    normalized["normalization"] = {
        "source_fields": list(OPERATOR_REPORT_FIELDS),
        "preflight_required_fields": list(OPERATOR_REPORT_PREFLIGHT_BOOL_FIELDS),
        "review_required_fields": list(OPERATOR_REPORT_REVIEW_BOOL_FIELDS) + list(OPERATOR_REPORT_REQUIRED_REVIEW_TEXT_FIELDS),
        "structured_hil_fields": list(OPERATOR_REPORT_STRUCTURED_HIL_FIELDS),
        "missing_or_invalid_fields": preflight_missing_or_invalid + review_missing_or_invalid,
        "preflight_missing_or_invalid_fields": preflight_missing_or_invalid,
        "review_missing_or_invalid_fields": review_missing_or_invalid,
        "unsafe_fields": unsafe_fields,
        "structured_hil_missing_or_invalid_bool_fields": structured_hil_claims["normalization"]["missing_or_invalid_bool_fields"],
    }
    return normalized, status


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


def command_stdout_preview(stdout: str, *, text_limit: int = 1200, json_limit: int = 12000) -> str:
    """普通命令只保留短尾部；完整单行 JSON 在受控上限内原样保留。"""
    # 只提升最后一条完整 JSON 行，避免普通 ROS 日志意外放大 API 响应。
    # 空行先剔除，避免命令末尾换行让最后一条结构化记录无法识别。
    nonempty_lines = [line for line in stdout.splitlines() if line.strip()]
    if nonempty_lines:
        # strip 仅删除行边界空白，不改动 JSON 字符串内部的证据内容。
        candidate = nonempty_lines[-1].strip()
        if len(candidate) <= json_limit:
            # 必须真实解析成功才扩大预览，不能只凭首尾大括号猜测日志类型。
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                # 解析失败仍走普通短预览，防止半截 JSON 被调用方误当作完整事实。
                parsed = None
            # O11/O10 的结构化回包都是 JSON object；数组或标量不扩大预览窗口。
            if isinstance(parsed, dict):
                return candidate
    # 普通日志保留既有 1200 字符边界，避免本修复影响其它命令响应体积。
    return stdout[-text_limit:]


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
        # lifecycle status 是单行结构化 JSON，字段扩展后可能超过普通日志预览上限；
        # 若仍只截取尾部，JSON 起始括号会丢失，Upper 就无法证明 current owner 与串口归属。
        "stdout_preview": command_stdout_preview(completed.stdout),
        "stderr_preview": completed.stderr[-1200:],
    }


def resolve_fixed_argv_with_ros2_setup(argv: list[str]) -> tuple[list[str], bool]:
    """ROS2 命令统一补 source；argv 仍由代码固定生成，不吃 HTTP body 命令。"""
    resolved_argv = argv
    ros2_setup_used = False
    if argv[0] == "ros2":
        # 上位机 API 常由 system/nohup 裸 python 启动，不能假设 shell 已经 source ROS2。
        # 这里仍只执行代码内固定 argv；shlex.join 只负责把内部参数安全传给 bash -lc。
        setup_parts = []
        if Path(DEFAULT_ROS_SETUP_PATH).exists():
            setup_parts.append(f"source {shlex.quote(DEFAULT_ROS_SETUP_PATH)}")
        if Path(DEFAULT_ONBOARD_SETUP_PATH).exists():
            setup_parts.append(f"source {shlex.quote(DEFAULT_ONBOARD_SETUP_PATH)}")
        setup_prefix = "; ".join(setup_parts)
        command = f"{setup_prefix}; exec {shlex.join(argv)}" if setup_prefix else f"exec {shlex.join(argv)}"
        resolved_argv = ["bash", "-lc", command]
        ros2_setup_used = bool(setup_prefix)
    return resolved_argv, ros2_setup_used


def run_fixed_argv_command(argv: list[str], timeout_s: float = 8.0) -> dict[str, Any]:
    """执行代码内固定 argv；不经过 shell，避免 HTTP body 变成任意命令入口。"""
    if not argv:
        return {"mode": "fixed_argv", "executed": False, "ok": False, "reason": "empty_argv"}
    resolved_argv, ros2_setup_used = resolve_fixed_argv_with_ros2_setup(argv)
    process: subprocess.Popen[str] | None = None
    try:
        # ROS2 CLI 偶尔会在 graph 抖动时卡住；单独进程组便于 timeout 时整组收口。
        process = subprocess.Popen(
            resolved_argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        stdout, stderr = process.communicate(timeout=timeout_s)
    except subprocess.TimeoutExpired as exc:
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout, stderr = process.communicate()
        else:
            stdout, stderr = "", ""
        return {
            "mode": "fixed_argv",
            "executed": True,
            "ok": False,
            "argv": argv,
            "resolved_argv": resolved_argv if resolved_argv != argv else None,
            "ros2_setup_used": ros2_setup_used,
            "returncode": None,
            "stdout_preview": stdout[-1200:],
            "stderr_preview": stderr[-1200:],
            "error": compact_error(exc),
        }
    except Exception as exc:  # noqa: BLE001 - ROS2 CLI 缺失或 graph 不通都要结构化返回。
        return {
            "mode": "fixed_argv",
            "executed": False,
            "ok": False,
            "argv": argv,
            "resolved_argv": resolved_argv if resolved_argv != argv else None,
            "ros2_setup_used": ros2_setup_used,
            "error": compact_error(exc),
        }
    return {
        "mode": "fixed_argv",
        "executed": True,
        "ok": process.returncode == 0 if process is not None else False,
        "argv": argv,
        "resolved_argv": resolved_argv if resolved_argv != argv else None,
        "ros2_setup_used": ros2_setup_used,
        "returncode": process.returncode if process is not None else None,
        "stdout_preview": stdout[-1200:],
        "stderr_preview": stderr[-1200:],
    }


def free_roam_managed_log_path(artifact_path: str) -> str:
    """托管节点日志放在 artifact 同目录，方便现场只看 runtime 目录定位启动失败。"""
    parent = os.path.dirname(os.path.abspath(os.path.expanduser(artifact_path))) if artifact_path else ""
    return os.path.join(parent or "/tmp", DEFAULT_FREE_ROAM_MANAGED_LOG_NAME)


def free_roam_param_probe() -> dict[str, Any]:
    """检查自由移动节点参数服务；失败时保留 ROS2 CLI 证据给 PC 诊断。"""
    result = run_fixed_argv_command(["ros2", "param", "list", FREE_ROAM_AUTONOMY_NODE_NAME], timeout_s=8.0)
    stderr = str(result.get("stderr_preview") or "")
    stdout = str(result.get("stdout_preview") or "")
    combined = f"{stdout}\n{stderr}"
    if result.get("ok"):
        status = "available"
    elif "Node not found" in combined or "not found" in combined.lower():
        status = "node_not_found"
    else:
        status = "probe_failed"
    return {
        "mode": "free_roam_param_probe",
        "available": bool(result.get("ok")),
        "status": status,
        "command_result": result,
    }


def free_roam_node_list_probe() -> dict[str, Any]:
    """轻量确认 free-roam 节点是否已在 ROS graph；避免 param list 慢时重复启动。"""
    result = run_fixed_argv_command(["ros2", "node", "list"], timeout_s=8.0)
    stdout = str(result.get("stdout_preview") or "")
    nodes = [line.strip() for line in stdout.splitlines() if line.strip()]
    observed = FREE_ROAM_AUTONOMY_NODE_NAME in nodes
    return {
        "mode": "free_roam_node_list_probe",
        "observed": observed,
        "status": "observed" if observed else "not_observed" if result.get("ok") else "probe_failed",
        "nodes": nodes[-20:],
        "command_result": result,
    }


def start_managed_free_roam_runtime(artifact_path: str) -> dict[str, Any]:
    """后台启动自由移动 runtime；argv 固定且默认锁住运动发布。"""
    log_path = free_roam_managed_log_path(artifact_path)
    argv = [
        "ros2",
        "run",
        "ros2_trashbot_nav",
        "free_roam_autonomy_node",
        "--ros-args",
        "-p",
        "artifact_path:=" + os.path.expanduser(artifact_path),
        "-p",
        "scan_topic:=/scan",
        "-p",
        "map_topic:=/map",
        "-p",
        "cmd_vel_topic:=/cmd_vel",
        "-p",
        "enable_cmd_vel_publish:=false",
        "-p",
        "motion_hil_unlocked:=false",
    ]
    resolved_argv, ros2_setup_used = resolve_fixed_argv_with_ros2_setup(argv)
    try:
        os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as log_stream:
            # 记录启动边界；真正速度发布仍由后续 param load 双锁控制。
            log_stream.write(json.dumps({"event": "managed_free_roam_runtime_start", "argv": argv, "at_ms": now_ms()}, ensure_ascii=False) + "\n")
            log_stream.flush()
            process = subprocess.Popen(
                resolved_argv,
                stdout=log_stream,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,
            )
    except Exception as exc:  # noqa: BLE001 - 启动失败必须结构化返回，不让 PC 只看到 400。
        return {
            "mode": "managed_free_roam_runtime_start",
            "executed": False,
            "ok": False,
            "argv": argv,
            "resolved_argv": resolved_argv if resolved_argv != argv else None,
            "ros2_setup_used": ros2_setup_used,
            "log_path": log_path,
            "error": compact_error(exc),
        }
    return {
        "mode": "managed_free_roam_runtime_start",
        "executed": True,
        "ok": True,
        "argv": argv,
        "resolved_argv": resolved_argv if resolved_argv != argv else None,
        "ros2_setup_used": ros2_setup_used,
        "pid": process.pid,
        "log_path": log_path,
        "starts_motion_unlocked": False,
        "starts_cmd_vel_publish": False,
    }


def ensure_free_roam_runtime_for_param_load(artifact_path: str) -> dict[str, Any]:
    """start/stop 入口自愈缺失 runtime；已有节点时不重复启动。"""
    before = free_roam_param_probe()
    if before["available"]:
        return {
            "mode": "free_roam_runtime_ensure",
            "status": "already_available",
            "available": True,
            "started_by_api": False,
            "before": before,
        }
    node_before = free_roam_node_list_probe()
    if node_before["observed"]:
        return {
            "mode": "free_roam_runtime_ensure",
            "status": "node_observed_param_probe_not_available",
            "available": True,
            "started_by_api": False,
            "before": before,
            "node_before": node_before,
        }
    start = start_managed_free_roam_runtime(artifact_path)
    if not start.get("ok"):
        return {
            "mode": "free_roam_runtime_ensure",
            "status": "managed_start_failed",
            "available": False,
            "started_by_api": False,
            "before": before,
            "node_before": node_before,
            "start": start,
        }
    deadline = time.monotonic() + FREE_ROAM_MANAGED_START_WAIT_TIMEOUT_S
    attempts = 0
    after = before
    node_after = node_before
    while time.monotonic() < deadline:
        attempts += 1
        time.sleep(FREE_ROAM_MANAGED_START_WAIT_INTERVAL_S)
        node_after = free_roam_node_list_probe()
        if node_after["observed"]:
            return {
                "mode": "free_roam_runtime_ensure",
                "status": "started_and_node_observed",
                "available": True,
                "started_by_api": True,
                "attempts": attempts,
                "before": before,
                "node_before": node_before,
                "start": start,
                "after": after,
                "node_after": node_after,
            }
        after = free_roam_param_probe()
        if after["available"]:
            return {
                "mode": "free_roam_runtime_ensure",
                "status": "started_and_param_available",
                "available": True,
                "started_by_api": True,
                "attempts": attempts,
                "before": before,
                "node_before": node_before,
                "start": start,
                "after": after,
                "node_after": node_after,
            }
    return {
        "mode": "free_roam_runtime_ensure",
        "status": "unavailable_after_managed_start",
        "available": False,
        "started_by_api": True,
        "attempts": attempts,
        "before": before,
        "node_before": node_before,
        "start": start,
        "after": after,
        "node_after": node_after,
    }


def free_roam_param_sequence_failure_reason(command_result: dict[str, Any]) -> str | None:
    """把参数写入失败压成现场可行动的短 reason，避免只返回泛化失败。"""
    if command_result.get("ok"):
        return None
    reason = command_result.get("reason")
    if isinstance(reason, str) and reason:
        return reason
    runtime_ensure = command_result.get("runtime_ensure")
    if isinstance(runtime_ensure, dict) and not runtime_ensure.get("available"):
        status = str(runtime_ensure.get("status") or "runtime_unavailable")
        return f"free_roam_runtime_{status}"
    results = command_result.get("results")
    if isinstance(results, list):
        for item in results:
            if not isinstance(item, dict) or item.get("ok"):
                continue
            item_reason = item.get("reason")
            if isinstance(item_reason, str) and item_reason:
                return item_reason
            stderr = str(item.get("stderr_preview") or "").strip().splitlines()
            stdout = str(item.get("stdout_preview") or "").strip().splitlines()
            if stderr:
                return stderr[-1][-160:]
            if stdout:
                return stdout[-1][-160:]
    return "free_roam_param_sequence_failed"


def run_free_roam_param_sequence(
    action: str,
    *,
    enable_motion: bool = False,
    mapping_active: bool = True,
    artifact_path: str = DEFAULT_FREE_ROAM_AUTONOMY_ARTIFACT_PATH,
) -> dict[str, Any]:
    """自由移动只由安全确认解锁；mapping_active 只表达本轮是否可作为建图会话。"""
    sequences = {
        "start": [
            ("operator_confirmed", "true"),
            ("mapping_active", "true" if mapping_active else "false"),
            ("stop_available", "true"),
            ("external_stop_requested", "false"),
        ],
        "stop": [
            ("enable_cmd_vel_publish", "false"),
            ("motion_hil_unlocked", "false"),
            ("external_stop_requested", "true"),
            ("mapping_active", "false"),
            ("operator_confirmed", "false"),
        ],
    }
    if action not in sequences:
        return {
            "mode": "free_roam_param_sequence",
            "executed": False,
            "ok": False,
            "reason": "unsupported_free_roam_action",
        }
    if action == "start" and enable_motion:
        # 双锁放在状态机门禁之后设置；任何一步失败都会停止后续写入，避免半启动。
        sequences[action].extend([
            ("motion_hil_unlocked", "true"),
            ("enable_cmd_vel_publish", "true"),
        ])
    param_names = [name for name, _value in sequences[action]]
    runtime_ensure = ensure_free_roam_runtime_for_param_load(artifact_path)
    if not runtime_ensure.get("available"):
        return {
            "mode": "free_roam_param_sequence",
            "action": action,
            "motion_unlock_requested": bool(action == "start" and enable_motion),
            "executed": bool(runtime_ensure.get("start", {}).get("executed")) if isinstance(runtime_ensure.get("start"), dict) else False,
            "ok": False,
            "reason": free_roam_param_sequence_failure_reason({"runtime_ensure": runtime_ensure}),
            "runtime_ensure": runtime_ensure,
            "touched_parameters": [],
            "blocked_parameters_not_touched": ["motion_hil_unlocked", "enable_cmd_vel_publish", "cmd_vel_topic"],
        }
    yaml_lines = ["/free_roam_autonomy:", "  ros__parameters:"]
    for name, value in sequences[action]:
        yaml_lines.append(f"    {name}: {value}")
    temp_path: str | None = None
    result: dict[str, Any] = {
        "mode": "fixed_argv",
        "executed": False,
        "ok": False,
        "reason": "free_roam_param_yaml_not_created",
    }
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".yaml", delete=False) as temp_file:
            # 一次 param load 比逐个 param set 更适合真实 ROS graph；避免 PC start/stop 被 5-6 个 CLI 启动拖慢。
            temp_file.write("\n".join(yaml_lines) + "\n")
            temp_path = temp_file.name
        result = run_fixed_argv_command(
            ["ros2", "param", "load", "/free_roam_autonomy", temp_path],
            timeout_s=FREE_ROAM_PARAM_LOAD_TIMEOUT_S,
        )
    finally:
        if temp_path:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except Exception:
                pass
    results = [{
        "parameters": param_names,
        "values": {name: value for name, value in sequences[action]},
        "write_strategy": "ros2_param_load",
        **result,
    }]
    touched = param_names if result.get("ok") else []
    blocked_not_touched = [
        name
        for name in ("motion_hil_unlocked", "enable_cmd_vel_publish", "cmd_vel_topic")
        if name not in touched
    ]
    return {
        "mode": "free_roam_param_sequence",
        "action": action,
        "motion_unlock_requested": bool(action == "start" and enable_motion),
        "executed": any(bool(item.get("executed")) for item in results),
        "ok": all(bool(item.get("ok")) for item in results),
        "reason": None if all(bool(item.get("ok")) for item in results) else free_roam_param_sequence_failure_reason({"results": results}),
        "runtime_ensure": runtime_ensure,
        "results": results,
        "touched_parameters": touched,
        "blocked_parameters_not_touched": blocked_not_touched,
    }


def free_roam_param_sequence_used_ros2_param_load(command_result: dict[str, Any]) -> bool:
    """只在真实 ros2 param load 成功后等待 artifact；mock 响应不拖慢单元测试。"""
    if not bool(command_result.get("ok")):
        return False
    results = command_result.get("results")
    if not isinstance(results, list):
        return False
    return any(
        isinstance(item, dict)
        and item.get("write_strategy") == "ros2_param_load"
        and bool(item.get("ok"))
        for item in results
    )


def _extract_flag_value(argv: list[str], flag: str) -> str | None:
    """兼容 `--flag value` 和 `--flag=value` 两种脚本参数写法。"""
    for index, item in enumerate(argv):
        if item == flag and index + 1 < len(argv):
            return argv[index + 1]
        if item.startswith(f"{flag}="):
            return item.split("=", 1)[1]
    return None


def parse_lidar_baudrate(value: Any) -> int | None:
    """把多来源 baudrate 归一成正整数；非法值不能参与 current readback。"""
    if isinstance(value, bool) or value is None:
        return None
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return parsed if 0 < parsed <= 4_000_000 else None


def radar_baudrate_from_command_info(command_info: dict[str, Any] | None) -> int | None:
    """只从已解析 argv 读取 `--serial-baudrate`，避免从整段命令字符串做脆弱匹配。"""
    if not isinstance(command_info, dict) or command_info.get("error"):
        return None
    argv = command_info.get("argv")
    if not isinstance(argv, list):
        return None
    return parse_lidar_baudrate(_extract_flag_value([str(item) for item in argv], "--serial-baudrate"))


def build_radar_baudrate_readback(
    *,
    lifecycle_status_readback: dict[str, Any],
    driver_diagnostics_latest: dict[str, Any],
    start_command_info: dict[str, Any],
    scan_proof_runtime_command_info: dict[str, Any],
    radar_start_command: str | None,
    lidar_scan_proof_runtime_command: str | None,
) -> dict[str, Any]:
    """选择 `/api/radar/status` current baudrate，并把 stale/reference 候选完整暴露。"""
    lifecycle_latest = lifecycle_status_readback.get("latest_result")
    lifecycle_latest = lifecycle_latest if isinstance(lifecycle_latest, dict) else {}
    diagnostics_serial = driver_diagnostics_latest.get("serial")
    diagnostics_serial = diagnostics_serial if isinstance(diagnostics_serial, dict) else {}
    diagnostics_runtime = driver_diagnostics_latest.get("runtime")
    diagnostics_runtime = diagnostics_runtime if isinstance(diagnostics_runtime, dict) else {}
    candidates: list[dict[str, Any]] = []

    def add(source: str, value: Any, kind: str, *, static_default: bool = False) -> None:
        baudrate = parse_lidar_baudrate(value)
        if baudrate is None:
            return
        candidates.append(
            {
                "source": source,
                "baudrate": baudrate,
                "kind": kind,
                "trusted_current": False,
                "status": "candidate",
                "static_default": static_default,
            }
        )

    add("lifecycle_status_readback.baudrate", lifecycle_status_readback.get("baudrate"), "lifecycle_status")
    add(
        "lifecycle_status_readback.serial_baudrate",
        lifecycle_status_readback.get("serial_baudrate"),
        "lifecycle_status",
    )
    add("lifecycle_status_readback.latest_result.baudrate", lifecycle_latest.get("baudrate"), "lifecycle_status")
    add(
        "lifecycle_status_readback.latest_result.serial_baudrate",
        lifecycle_latest.get("serial_baudrate"),
        "lifecycle_status",
    )
    add(
        "driver_diagnostics_latest.serial.serial_baudrate",
        diagnostics_serial.get("serial_baudrate"),
        "driver_diagnostics",
    )
    add(
        "driver_diagnostics_latest.serial.baudrate",
        diagnostics_serial.get("baudrate"),
        "driver_diagnostics",
    )
    add(
        "driver_diagnostics_latest.runtime.serial_baudrate",
        diagnostics_runtime.get("serial_baudrate"),
        "driver_diagnostics",
    )
    add(
        "controls.start.command.argv",
        radar_baudrate_from_command_info(start_command_info),
        "control_command",
        static_default=radar_start_command == DEFAULT_RADAR_START_COMMAND,
    )
    add(
        "controls.scan_proof_refresh.runtime_command.argv",
        radar_baudrate_from_command_info(scan_proof_runtime_command_info),
        "control_command",
        static_default=not bool(lidar_scan_proof_runtime_command and lidar_scan_proof_runtime_command.strip()),
    )

    current_evidence_values = {
        item["baudrate"]
        for item in candidates
        if item["kind"] in {"driver_diagnostics", "control_command"} and not item["static_default"]
    }
    for item in candidates:
        if item["kind"] == "lifecycle_status":
            # status 脚本历史上会把 vendor/reference 230400 当成默认字段；和 current command
            # 或 diagnostics 冲突时必须只当 drift 证据，不能覆盖真实运行窗口。
            if item["baudrate"] == LIDAR_VENDOR_REFERENCE_BAUDRATE and item["baudrate"] not in current_evidence_values:
                item["status"] = (
                    "reference_conflict_not_current"
                    if current_evidence_values
                    else "reference_only_not_current"
                )
                continue
            item["trusted_current"] = True
            item["status"] = "trusted_current_candidate"
            continue
        if item["kind"] == "driver_diagnostics":
            item["trusted_current"] = driver_diagnostics_latest.get("status") == "loaded"
            item["status"] = "trusted_current_candidate" if item["trusted_current"] else "diagnostics_not_loaded"
            continue
        if item["kind"] == "control_command":
            item["trusted_current"] = not item["static_default"]
            item["status"] = (
                "trusted_current_candidate"
                if item["trusted_current"]
                else "static_default_not_current_readback"
            )

    selected = next((item for item in candidates if item["trusted_current"]), None)
    reference_conflict = any(str(item.get("status", "")).endswith("not_current") for item in candidates)
    return {
        "baudrate": selected["baudrate"] if selected else None,
        "baudrate_readback_source": selected["source"] if selected else "unknown",
        "baudrate_readback_status": (
            "current_with_reference_conflict"
            if selected and reference_conflict
            else "current"
            if selected
            else "unknown_no_current_readback"
        ),
        "baudrate_candidates": candidates,
        "vendor_reference_baudrate": LIDAR_VENDOR_REFERENCE_BAUDRATE,
        "historical_field_baudrate_candidate": LIDAR_HISTORICAL_FIELD_BAUDRATE_CANDIDATE,
    }


def _is_lidar_serial_path(path: str) -> bool:
    """只允许看起来像 STC LiDAR 的串口路径，避免配置误指到底盘 UART。"""
    return (
        path == "/dev/lidar"
        or path.startswith("/dev/ttyACM")
        or (path.startswith("/dev/serial/by-id/") and "stc" in path.lower())
        or (path.startswith("/dev/serial/by-path/") and path.strip())
    )


def _is_wave_rover_base_serial_path(path: str) -> bool:
    """只允许现场确认过的 WAVE ROVER 底盘 UART 或稳定 udev 路径。"""
    return (
        path == "/dev/ttyS5"
        or (path.startswith("/dev/serial/by-id/") and path.strip())
        or (path.startswith("/dev/serial/by-path/") and path.strip())
    )


def validate_lidar_runtime_command(command: str | None) -> tuple[list[str], dict[str, str] | None]:
    """只接受项目 LiDAR-only smoke 脚本，拒绝任意 shell/底盘控制命令。"""
    if not command or not command.strip():
        return [], {"type": "no_command_configured", "message": "ROBER_LIDAR_SCAN_PROOF_RUNTIME_COMMAND is not configured"}
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        return [], compact_error(exc)
    if not argv:
        return [], {"type": "empty_command", "message": "runtime command parsed to empty argv"}
    joined = " ".join(argv)
    if any(token in joined for token in (";", "&&", "||", "|", "$(", "`")):
        return [], {"type": "unsafe_runtime_command", "message": "shell operators are not allowed in LiDAR runtime command"}
    for token in BLOCKED_LIDAR_RUNTIME_COMMAND_TOKENS:
        if token in joined:
            return [], {"type": "unsafe_runtime_command", "message": f"blocked token in LiDAR runtime command: {token}"}
    script_index = 1 if Path(argv[0]).name in SAFE_LIDAR_RUNTIME_SHELLS else 0
    if script_index >= len(argv) or Path(argv[script_index]).name != SAFE_LIDAR_RUNTIME_SCRIPT:
        return [], {
            "type": "unsupported_runtime_command",
            "message": f"only {SAFE_LIDAR_RUNTIME_SCRIPT} is allowed for API-managed scan proof runtime",
        }
    serial_port = _extract_flag_value(argv, "--serial-port")
    if serial_port and not _is_lidar_serial_path(serial_port):
        return [], {"type": "unsafe_lidar_serial_path", "message": f"refusing non-LiDAR serial path: {serial_port}"}
    return argv, None


def validate_radar_lifecycle_command(command: str | None, action: str) -> tuple[list[str], dict[str, str] | None]:
    """雷达 start/stop 只能调用受管 lifecycle 脚本，防止 PC 代理变成任意命令入口。"""
    if not command or not command.strip():
        return [], {"type": "no_command_configured", "message": f"ROBER_RADAR_{action.upper()}_COMMAND is not configured"}
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        return [], compact_error(exc)
    if not argv:
        return [], {"type": "empty_command", "message": "radar lifecycle command parsed to empty argv"}
    joined = " ".join(argv)
    if any(token in joined for token in (";", "&&", "||", "|", "$(", "`")):
        return [], {"type": "unsafe_runtime_command", "message": "shell operators are not allowed in radar lifecycle command"}
    for token in BLOCKED_LIDAR_RUNTIME_COMMAND_TOKENS:
        if token in joined:
            return [], {"type": "unsafe_runtime_command", "message": f"blocked token in radar lifecycle command: {token}"}
    script_index = 1 if Path(argv[0]).name in SAFE_LIDAR_RUNTIME_SHELLS else 0
    if script_index >= len(argv) or Path(argv[script_index]).name != SAFE_RADAR_LIFECYCLE_SCRIPT:
        return [], {
            "type": "unsupported_runtime_command",
            "message": f"only {SAFE_RADAR_LIFECYCLE_SCRIPT} is allowed for radar start/stop",
        }
    action_index = script_index + 1
    if action_index >= len(argv) or argv[action_index] != action:
        return [], {"type": "unsupported_radar_action", "message": f"radar lifecycle command must call {action}"}
    serial_port = _extract_flag_value(argv, "--serial-port")
    if serial_port and not _is_lidar_serial_path(serial_port):
        return [], {"type": "unsafe_lidar_serial_path", "message": f"refusing non-LiDAR serial path: {serial_port}"}
    return argv, None


def run_radar_lifecycle_command(command: str | None, action: str) -> dict[str, Any]:
    """先校验 lifecycle 白名单，再执行显式配置命令。"""
    argv, error = validate_radar_lifecycle_command(command, action)
    if error:
        return {
            "mode": "command" if command and command.strip() else "dry_run_stub",
            "executed": False,
            "ok": False,
            "argv": argv,
            "error": error,
            "allowed_script": SAFE_RADAR_LIFECYCLE_SCRIPT,
            "sends_base_motion_commands": False,
            "uses_base_uart": False,
        }
    return run_configured_command(command)


def normalize_strict_nav2_start_request(
    body: dict[str, Any] | None,
    *,
    request_error: dict[str, str] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """只接受完整 strict-no-motion start 合同；旧 `{}` 请求必须 fail closed。"""
    # handler 传入的解码错误不得与“缺 body”混在一起，便于调用方修复格式。
    if request_error is not None:
        # JSON 解析失败发生在任何 subprocess 前；错误必须结构化回包，不能让 aiohttp 返回裸 500。
        return None, {
            "type": "invalid_nav2_start_json",
            "message": "nav2 start body must be a JSON object",
            "detail": request_error,
        }
    if not isinstance(body, dict) or not body:
        # bodyless 与历史 `{}` 都没有能力证明调用方理解新的零串口合同。
        return None, {
            "type": "strict_nav2_start_body_required",
            "message": "explicit strict no-motion nav2 start JSON body is required",
        }
    # 精确字段集可防止调用方误以为 mode/goal 等参数已被消费。
    unknown_fields = sorted(str(key) for key in body if key not in STRICT_NAV2_START_REQUEST_FIELDS)
    # 缺失字段不使用服务端默认值，否则旧客户端会意外绕过升级门禁。
    missing_fields = sorted(field for field in STRICT_NAV2_START_REQUEST_FIELDS if field not in body)
    if unknown_fields or missing_fields:
        # 拒绝未知 mode/goal/速度等字段，避免客户端以为服务端消费了实际被忽略的参数。
        return None, {
            "type": "invalid_nav2_start_fields",
            "message": "nav2 start body must contain exactly the strict no-motion fields",
            "unknown_fields": unknown_fields,
            "missing_fields": missing_fields,
        }
    # 用 `is True` 而非 truthy 判定，拒绝 1 或字符串等模糊值。
    if body.get("strict_no_motion") is not True:
        return None, {
            "type": "strict_no_motion_required",
            "message": "strict_no_motion must be true",
        }
    # 用 `is False` 确保不会把 0、null 或空字符串解释为底盘已禁用。
    if body.get("base_enabled") is not False:
        # `auto` 可能在没有 holder 时解析为 true，因此不能作为零 UART new-open 合同。
        return None, {
            "type": "base_must_be_disabled",
            "message": "base_enabled must be false",
        }
    # LiDAR 与 scan 复用位都必须是 JSON bool，拒绝 auto、0/1 与字符串造成模式歧义。
    lidar_enabled = body.get("lidar_enabled")
    reuse_existing_scan = body.get("reuse_existing_scan")
    if type(lidar_enabled) is not bool or type(reuse_existing_scan) is not bool:
        return None, {
            "type": "invalid_nav2_sensor_mode_types",
            "message": "lidar_enabled and reuse_existing_scan must be JSON booleans",
        }
    # 仅保留 legacy 外部 scan 与 sensor-owned 两个互斥模式；其余组合全部 fail closed。
    legacy_existing_scan = lidar_enabled is False and reuse_existing_scan is True
    sensor_owned_scan = lidar_enabled is True and reuse_existing_scan is False
    if not (legacy_existing_scan or sensor_owned_scan):
        return None, {
            "type": "invalid_nav2_sensor_mode",
            "message": "allowed modes are lidar=false/reuse=true or lidar=true/reuse=false",
            "allowed_modes": [
                {"lidar_enabled": False, "reuse_existing_scan": True},
                {"lidar_enabled": True, "reuse_existing_scan": False},
            ],
        }
    # bool 是 int 的子类，必须先单独拦截，避免 true 被当成 1 秒。
    raw_timeout = body.get("timeout_s")
    if isinstance(raw_timeout, bool) or not isinstance(raw_timeout, (int, float)):
        return None, {
            "type": "invalid_nav2_start_timeout",
            "message": "timeout_s must be a finite JSON number between 4 and 20 seconds",
        }
    # JSON 数字类型统一成浮点秒；字符串不做隐式转换，避免客户端误判合同类型。
    timeout_s = float(raw_timeout)
    if not math.isfinite(timeout_s) or not STRICT_NAV2_START_TIMEOUT_MIN_S <= timeout_s <= STRICT_NAV2_START_TIMEOUT_MAX_S:
        # timeout 不做 clamp；静默限幅会让调用方误以为自己提交的窗口已生效。
        return None, {
            "type": "invalid_nav2_start_timeout",
            "message": "timeout_s must be a finite JSON number between 4 and 20 seconds",
            "received": raw_timeout,
        }
    # 返回规范化合同，后续代码只使用这个对象而不再读原始 body。
    return {
        # 安全模式在规范化后始终为布尔 true。
        "strict_no_motion": True,
        # 底盘禁用值在规范化后始终为布尔 false。
        "base_enabled": False,
        # LiDAR 与复用位来自已经验证的互斥安全模式，不做服务端隐式翻转。
        "lidar_enabled": lidar_enabled,
        "reuse_existing_scan": reuse_existing_scan,
        # 模式名用于后置 holder/publisher 语义验收，避免只看两个裸布尔值。
        "sensor_mode": "sensor_owned_scan" if sensor_owned_scan else "legacy_existing_scan",
        # timeout 统一为浮点秒，便于直接传给 subprocess 运行器。
        "timeout_s": timeout_s,
    }, None


def replace_nav2_lifecycle_flag(argv: list[str], flag: str, value: str) -> list[str]:
    """删除配置中的同名 flag 后追加唯一安全值，避免重复参数的 last-one-wins 漂移。"""
    # 新列表不在原 argv 上就地修改，避免调用方持有的配置被污染。
    result: list[str] = []
    # 显式索引用来同时跳过 `--flag value` 的两个 token。
    index = 0
    while index < len(argv):
        item = argv[index]
        if item == flag:
            # `--flag value` 两个 token 一起删除；缺值配置会在后续白名单校验中失败。
            index += 2
            continue
        # 兼容 `--flag=value` 配置写法，避免遗留第二个同名参数。
        if item.startswith(f"{flag}="):
            index += 1
            continue
        result.append(item)
        index += 1
    # 安全值最后追加且只追加一次，便于证据中直接审计。
    return [*result, flag, value]


def strict_no_motion_nav2_start_command(
    command: str | None,
    contract: dict[str, Any],
) -> tuple[str | None, dict[str, Any] | None]:
    """从受管 o11 配置构造 canonical no-motion argv；body 只能选择已验证的传感器模式。"""
    # 先审计原命令的脚本路径、action、串口与禁止 token。
    argv, error = validate_nav2_lifecycle_command(command, "start")
    if error is not None:
        return None, error
    # 底盘永远重写为 false；LiDAR 只取规范化合同中的精确 bool，不接受任意字符串。
    argv = replace_nav2_lifecycle_flag(argv, "--base-enabled", "false")
    lidar_value = "true" if contract.get("lidar_enabled") is True else "false"
    reuse_value = "true" if contract.get("reuse_existing_scan") is True else "false"
    argv = replace_nav2_lifecycle_flag(argv, "--lidar-enabled", lidar_value)
    argv = replace_nav2_lifecycle_flag(argv, "--reuse-existing-scan", reuse_value)
    # strict start 固定 canonical map，不能由部署环境中的旧命令切换到未知地图。
    argv = replace_nav2_lifecycle_flag(argv, "--map-file", DEFAULT_NAV2_MAP_FILE)
    # shlex.join 只序列化已验证 token，不接收 body 中的任何字符串。
    effective_command = shlex.join(argv)
    # 重建后再跑一次同一白名单，防止参数重写破坏脚本合同。
    effective_argv, effective_error = validate_nav2_lifecycle_command(effective_command, "start")
    if effective_error is not None:
        return None, effective_error
    # 底盘有效值必须从最终 argv 反解，不仅信任重写函数。
    if _extract_flag_value(effective_argv, "--base-enabled") != "false":
        return None, {"type": "unsafe_effective_base_flag", "message": "effective base_enabled must be false"}
    # LiDAR 与复用位必须逐项等于已验证模式，避免重复 flag 或配置默认值漂移。
    if _extract_flag_value(effective_argv, "--lidar-enabled") != lidar_value:
        return None, {"type": "unsafe_effective_lidar_flag", "message": "effective lidar_enabled mismatch"}
    if _extract_flag_value(effective_argv, "--reuse-existing-scan") != reuse_value:
        return None, {"type": "unsafe_effective_scan_reuse_flag", "message": "effective scan reuse mismatch"}
    # map 路径也从最终 argv 反解，确保本轮不会消费非 canonical map。
    if _extract_flag_value(effective_argv, "--map-file") != DEFAULT_NAV2_MAP_FILE:
        return None, {"type": "unsafe_effective_map_file", "message": "effective map file must be canonical"}
    return effective_command, None


def validate_nav2_lifecycle_command(command: str | None, action: str) -> tuple[list[str], dict[str, str] | None]:
    """Nav2 start/stop/status 只能调用受管 stack-only 脚本，不能退化成任意 shell。"""
    if not command or not command.strip():
        return [], {"type": "no_command_configured", "message": f"ROBER_NAV2_{action.upper()}_COMMAND is not configured"}
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        return [], compact_error(exc)
    if not argv:
        return [], {"type": "empty_command", "message": "nav2 lifecycle command parsed to empty argv"}
    joined = " ".join(argv)
    if any(token in joined for token in (";", "&&", "||", "|", "$(", "`")):
        return [], {"type": "unsafe_runtime_command", "message": "shell operators are not allowed in Nav2 lifecycle command"}
    # lifecycle 命令只能启停 stack；所有可执行路径/控制器 action 都必须在独立门禁处理。
    for token in (
        "/api/base", "/cmd_vel", "cmd_vel", "T=1", "T=11", "T=13", "T=130", "T=131",
        "NavigateToPose", "NavigateThroughPoses", "FollowPath",
    ):
        if token in joined:
            return [], {"type": "unsafe_runtime_command", "message": f"blocked token in Nav2 lifecycle command: {token}"}
    script_index = 1 if Path(argv[0]).name in SAFE_LIDAR_RUNTIME_SHELLS else 0
    if script_index >= len(argv) or Path(argv[script_index]).name != SAFE_NAV2_LIFECYCLE_SCRIPT:
        return [], {
            "type": "unsupported_runtime_command",
            "message": f"only {SAFE_NAV2_LIFECYCLE_SCRIPT} is allowed for Nav2 start/stop",
        }
    action_index = script_index + 1
    if action_index >= len(argv) or argv[action_index] != action:
        return [], {"type": "unsupported_nav2_action", "message": f"Nav2 lifecycle command must call {action}"}
    base_port = _extract_flag_value(argv, "--base-port")
    if base_port and not _is_wave_rover_base_serial_path(base_port):
        return [], {"type": "unsafe_base_serial_path", "message": f"refusing unexpected WAVE ROVER UART: {base_port}"}
    command_mode = _extract_flag_value(argv, "--command-mode")
    if command_mode and command_mode not in ALLOWED_NAV2_BASE_COMMAND_MODES:
        return [], {"type": "unsupported_nav2_command_mode", "message": f"unsupported Nav2 base command mode: {command_mode}"}
    lidar_port = _extract_flag_value(argv, "--lidar-serial-port")
    if lidar_port and not _is_lidar_serial_path(lidar_port):
        return [], {"type": "unsafe_lidar_serial_path", "message": f"refusing unexpected LiDAR serial path: {lidar_port}"}
    for bool_flag in ("--base-enabled", "--lidar-enabled", "--reuse-existing-scan", "--static-laser-tf-enabled"):
        bool_value = _extract_flag_value(argv, bool_flag)
        if bool_value and bool_value not in ("true", "false", "auto"):
            return [], {"type": "unsupported_nav2_lifecycle_flag", "message": f"{bool_flag} must be true, false, or auto"}
    return argv, None


def run_nav2_lifecycle_command(command: str | None, action: str, *, timeout_s: float = 20.0) -> dict[str, Any]:
    """先做 Nav2 lifecycle 白名单校验，再运行受管 stack-only 脚本。"""
    argv, error = validate_nav2_lifecycle_command(command, action)
    if error:
        return {
            "mode": "command" if command and command.strip() else "dry_run_stub",
            "executed": False,
            "ok": False,
            "argv": argv,
            "error": error,
            "allowed_script": SAFE_NAV2_LIFECYCLE_SCRIPT,
            "sends_base_motion_commands": False,
            "uses_base_uart": False,
        }
    return run_configured_command(command, timeout_s=timeout_s)


def parse_nav2_lifecycle_status_result(command_result: dict[str, Any]) -> dict[str, Any]:
    """把 o11 status 的 stdout JSON 压成只读状态；解析失败也不能影响 /api/nav2/status。"""
    stdout = command_result.get("stdout", command_result.get("stdout_preview"))
    payload: dict[str, Any] | None = None
    if isinstance(stdout, str) and stdout.strip():
        try:
            parsed = json.loads(stdout)
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            payload = None
    running = payload.get("running") if payload else "not_loaded"
    state = payload.get("state") if payload else "not_loaded"
    message = payload.get("message") if payload else command_result.get("reason") or "not_loaded"
    # 数值型 holder/publisher 事实必须保持整数；bool 虽是 int 子类，但不能冒充计数。
    def payload_count(key: str) -> int | str:
        value = payload.get(key) if payload else None
        return value if isinstance(value, int) and not isinstance(value, bool) else "not_loaded"

    return {
        "schema": "trashbot.upper_robot_api.v1.nav2_lifecycle_manager_status",
        "status": "loaded" if payload else "not_loaded",
        "running": running if isinstance(running, bool) else "not_loaded",
        "state": str(state or "not_loaded"),
        "message": str(message or "not_loaded"),
        "pid": payload.get("pid") if payload else None,
        "start_owned_process_created": (
            payload.get("start_owned_process_created")
            if payload and isinstance(payload.get("start_owned_process_created"), bool)
            else "not_loaded"
        ),
        # start 语义验收必须读取脚本最终生效值，不能只相信请求或配置 argv。
        "base_enabled": str(payload.get("base_enabled")) if payload and payload.get("base_enabled") is not None else "not_loaded",
        "lidar_enabled": str(payload.get("lidar_enabled")) if payload and payload.get("lidar_enabled") is not None else "not_loaded",
        "reuse_existing_scan": (
            str(payload.get("reuse_existing_scan"))
            if payload and payload.get("reuse_existing_scan") is not None
            else "not_loaded"
        ),
        # sensor mode 与 ownership 来自 O11 当前 status，不从请求体或历史 artifact 推导。
        "sensor_mode": str(payload.get("sensor_mode") or "not_loaded") if payload else "not_loaded",
        "sensor_ownership": payload.get("sensor_ownership") if payload and isinstance(payload.get("sensor_ownership"), dict) else {},
        "base_uart_pre_holder_pids": payload.get("base_uart_pre_holder_pids") if payload and isinstance(payload.get("base_uart_pre_holder_pids"), list) else [],
        "base_uart_post_holder_pids": payload.get("base_uart_post_holder_pids") if payload and isinstance(payload.get("base_uart_post_holder_pids"), list) else [],
        "base_uart_new_open_count": payload_count("base_uart_new_open_count"),
        "lidar_serial_pre_holder_pids": payload.get("lidar_serial_pre_holder_pids") if payload and isinstance(payload.get("lidar_serial_pre_holder_pids"), list) else [],
        "lidar_serial_post_holder_pids": payload.get("lidar_serial_post_holder_pids") if payload and isinstance(payload.get("lidar_serial_post_holder_pids"), list) else [],
        "lidar_serial_new_open_count": payload_count("lidar_serial_new_open_count"),
        "lidar_holder_owned": payload.get("lidar_holder_owned") if payload and isinstance(payload.get("lidar_holder_owned"), bool) else "not_loaded",
        "scan_publisher_pre_count": payload_count("scan_publisher_pre_count"),
        "scan_publisher_post_count": payload_count("scan_publisher_post_count"),
        "scan_publisher_owned": payload.get("scan_publisher_owned") if payload and isinstance(payload.get("scan_publisher_owned"), bool) else "not_loaded",
        "physical_motion": payload.get("physical_motion") if payload and isinstance(payload.get("physical_motion"), bool) else "not_loaded",
        "broad_kill_used": payload.get("broad_kill_used") if payload and isinstance(payload.get("broad_kill_used"), bool) else "not_loaded",
        "map_identity": payload.get("map_identity") if payload and isinstance(payload.get("map_identity"), dict) else {},
        "motion_requires_explicit_goal_execute": (
            payload.get("motion_requires_explicit_goal_execute")
            if payload and isinstance(payload.get("motion_requires_explicit_goal_execute"), bool)
            else "not_loaded"
        ),
        "command_result": command_result,
        "sends_motion_commands": False,
        "sends_base_motion_commands": False,
        "robot_control_executed": False,
        "safe_to_control": False,
        "delivery_success": False,
    }


def status_section_unavailable_payload(section: str, reason: str, error: Any = None) -> dict[str, Any]:
    """聚合 status 的单区块失败必须结构化返回，避免一个慢端点拖死 PC 首屏。"""
    payload: dict[str, Any] = {
        "schema": f"{SCHEMA}.{section}_status_unavailable",
        "generated_at_ms": now_ms(),
        "status": "status_section_unavailable",
        "section": section,
        "failure_reason": reason,
        "readback_sends_commands": False,
        "sends_commands": False,
        "sends_motion_commands": False,
        "sends_base_motion_commands": False,
        "publishes_cmd_vel": False,
        "calls_base_manual": False,
        "robot_control_executed": False,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    if error is not None:
        payload["error"] = compact_error(error)
    return payload


def status_timeout_payload(reason: str, error: Any = None) -> dict[str, Any]:
    """顶层 status 超时也要 fail-closed 返回，不能让 PC 首屏一直等连接。"""
    payload: dict[str, Any] = {
        "schema": f"{SCHEMA}.status",
        "generated_at_ms": now_ms(),
        "status": "status_unavailable",
        "failure_reason": reason,
        "camera": status_section_unavailable_payload("camera", reason),
        "radar": status_section_unavailable_payload("radar", reason),
        "map": status_section_unavailable_payload("map", reason),
        "localization": status_section_unavailable_payload("localization", reason),
        "nav2": status_section_unavailable_payload("nav2", reason),
        "free_roam_autonomy": status_section_unavailable_payload("free_roam_autonomy", reason),
        "elevator": status_section_unavailable_payload("elevator", reason),
        "base": status_section_unavailable_payload("base", reason),
        "routes": dict(ROUTE_PATHS),
        "sends_commands": False,
        "sends_motion_commands": False,
        "sends_base_motion_commands": False,
        "publishes_cmd_vel": False,
        "calls_base_manual": False,
        "robot_control_executed": False,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    if error is not None:
        payload["error"] = compact_error(error)
    return payload


def base_status_deferred_payload(feedback_samples_artifact_path: str) -> dict[str, Any]:
    """聚合 status 不直接做底盘慢读；完整底盘状态由独立端点提供。"""
    payload = status_section_unavailable_payload("base", "deferred_to_base_status_endpoint")
    payload.update(
        {
            "status": "deferred_to_base_status_endpoint",
            "endpoint": ROUTE_PATHS["base_status"],
            "next_action": "read /api/base/status for current base feedback",
            "feedback_samples_latest_artifact": artifact_path_info(feedback_samples_artifact_path),
        }
    )
    return payload


async def read_status_section(name: str, loader: Any) -> dict[str, Any]:
    """用线程隔离同步只读区块；超时后让 /api/status 先返回可用部分。"""
    try:
        result = await asyncio.wait_for(asyncio.to_thread(loader), timeout=STATUS_SECTION_TIMEOUT_S)
    except asyncio.TimeoutError as exc:
        return status_section_unavailable_payload(name, f"status_section_timeout_{STATUS_SECTION_TIMEOUT_S:g}s", exc)
    except Exception as exc:  # noqa: BLE001 - status 聚合不能因单区块异常整体 500。
        return status_section_unavailable_payload(name, "status_section_exception", exc)
    if isinstance(result, dict):
        return result
    return status_section_unavailable_payload(name, "status_section_non_object")


async def read_camera_status_section(api: Any) -> tuple[int, dict[str, Any]]:
    """camera health 是 async HTTP 代理，也要纳入 status 聚合软超时。"""
    try:
        status, payload = await asyncio.wait_for(api.camera_health(), timeout=STATUS_SECTION_TIMEOUT_S)
    except asyncio.TimeoutError as exc:
        return 504, status_section_unavailable_payload("camera", f"status_section_timeout_{STATUS_SECTION_TIMEOUT_S:g}s", exc)
    except Exception as exc:  # noqa: BLE001 - 相机状态慢/异常时不拖死整车 status。
        return 502, status_section_unavailable_payload("camera", "status_section_exception", exc)
    if isinstance(payload, dict):
        return int(status), payload
    return 502, status_section_unavailable_payload("camera", "status_section_non_object")


def start_lidar_scan_proof_runtime(command: str | None, warmup_s: float) -> dict[str, Any]:
    """后台启动 LiDAR-only runtime，让随后 collector 能读取新鲜 `/scan`/TF。"""
    argv, error = validate_lidar_runtime_command(command)
    warmup_s = min(max(float(warmup_s), 0.0), 30.0)
    if error:
        return {
            "mode": "api_managed_lidar_runtime",
            "executed": False,
            "ok": False,
            "argv": argv,
            "error": error,
            "warmup_s": warmup_s,
            "allowed_script": SAFE_LIDAR_RUNTIME_SCRIPT,
            "safe_to_control": False,
            "sends_base_motion_commands": False,
            "uses_base_uart": False,
        }
    log_path = f"/tmp/rober_lidar_scan_proof_runtime_{now_ms()}.log"
    try:
        log_handle = open(log_path, "ab", buffering=0)
        process = subprocess.Popen(  # noqa: S603 - argv 已经按 LiDAR-only 脚本白名单校验。
            argv,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
        log_handle.close()
        if warmup_s > 0:
            time.sleep(warmup_s)
        returncode = process.poll()
        log_tail = read_text(log_path, max_bytes=2000) or ""
        return {
            "mode": "api_managed_lidar_runtime",
            "executed": True,
            "ok": returncode is None or returncode == 0,
            "argv": argv,
            "pid": process.pid,
            "returncode_after_warmup": returncode,
            "warmup_s": warmup_s,
            "log_path": log_path,
            "log_tail": log_tail[-2000:],
            "allowed_script": SAFE_LIDAR_RUNTIME_SCRIPT,
            "starts_lidar_driver": True,
            "opens_lidar_serial": True,
            "sends_lidar_start_command": True,
            "sends_base_motion_commands": False,
            "uses_base_uart": False,
            "safe_to_control": False,
        }
    except Exception as exc:  # noqa: BLE001 - 现场权限/脚本缺失要回到 blocked artifact。
        return {
            "mode": "api_managed_lidar_runtime",
            "executed": False,
            "ok": False,
            "argv": argv,
            "warmup_s": warmup_s,
            "error": compact_error(exc),
            "allowed_script": SAFE_LIDAR_RUNTIME_SCRIPT,
            "safe_to_control": False,
            "sends_base_motion_commands": False,
            "uses_base_uart": False,
        }


def lidar_runtime_output_dir(runtime_result: dict[str, Any] | None) -> str | None:
    """从 smoke 日志里取 output_dir；取不到时不猜新路径，保持 fallback 可审计。"""
    if not isinstance(runtime_result, dict):
        return None
    for line in str(runtime_result.get("log_tail") or "").splitlines():
        marker = "[o1-lidar-smoke] output_dir="
        if marker in line:
            return line.split(marker, 1)[1].strip() or None
    return None


def read_lidar_runtime_summary(runtime_result: dict[str, Any] | None) -> dict[str, Any] | None:
    """读取同轮 LiDAR-only smoke summary；它是 runtime 自身采集的 topic/TF 材料。"""
    output_dir = lidar_runtime_output_dir(runtime_result)
    if not output_dir:
        return None
    summary_path = Path(output_dir) / "summary.json"
    try:
        parsed = json.loads(summary_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(parsed, dict):
        return None
    parsed["_summary_path"] = str(summary_path)
    return parsed


def _average_rate_from_runtime_summary(summary: dict[str, Any]) -> float | None:
    """summary 只存 observed；需要数值时从同目录 scan_hz.txt 提取 average rate。"""
    summary_path = summary.get("_summary_path")
    if not isinstance(summary_path, str):
        return None
    text = read_text(str(Path(summary_path).with_name("scan_hz.txt")), max_bytes=4096) or ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("average rate:"):
            value = stripped.split(":", 1)[1].strip().split()[0]
            try:
                return float(value)
            except ValueError:
                return None
    return None


def apply_lidar_runtime_summary_fallback(
    *,
    artifact_path: str,
    refresh_result: dict[str, Any],
    runtime_result: dict[str, Any] | None,
) -> None:
    """collector 错过短窗口时，用同轮 smoke summary 修正 latest proof artifact。"""
    collector_payload = refresh_result.get("collector_payload")
    if not isinstance(collector_payload, dict):
        return
    proof = collector_payload.get("proof")
    if not isinstance(proof, dict) or proof.get("all_required_observations_observed") is True:
        return
    summary = read_lidar_runtime_summary(runtime_result)
    required = summary.get("required_observations") if isinstance(summary, dict) else None
    if not isinstance(required, dict) or not all(isinstance(item, dict) and item.get("observed") is True for item in required.values()):
        return
    average_rate = _average_rate_from_runtime_summary(summary)
    required_observations = proof.setdefault("required_observations", {})
    # smoke summary 是本轮 API-managed runtime 自己采的证据；写入来源字段，避免和 collector 混淆。
    for key, observation in required.items():
        if not isinstance(observation, dict):
            continue
        stable = required_observations.setdefault(key, {})
        if isinstance(stable, dict):
            stable.update(observation)
            stable["observed"] = True
            stable["source"] = "api_managed_lidar_runtime_summary"
            stable["summary_path"] = summary.get("_summary_path")
    if isinstance(required_observations.get("scan_hz"), dict):
        required_observations["scan_hz"]["average_rate_hz"] = average_rate
    proof.update(
        {
            "status": "scan_once_hz_raw_packet_tf_observed",
            "scan_once_observed": True,
            "scan_hz_observed": True,
            "scan_hz_average_rate_hz": average_rate,
            "raw_packet_once_observed": True,
            "tf_observed": True,
            "all_required_observations_observed": True,
            "runtime_summary_fallback_used": True,
            "runtime_summary_path": summary.get("_summary_path"),
        }
    )
    topic_reads = collector_payload.setdefault("topic_reads", {})
    if isinstance(topic_reads, dict):
        topic_reads["runtime_summary_fallback"] = {
            "used": True,
            "reason": "collector_topic_processes_missed_short_lidar_runtime_window",
            "summary_path": summary.get("_summary_path"),
        }
    collector_payload["blockers"] = [
        item
        for item in collector_payload.get("blockers", [])
        if not (isinstance(item, dict) and item.get("code") == "upper_api_scan_not_proven")
    ]
    collector_payload["artifact"] = atomic_write_json_artifact(artifact_path, collector_payload)


def lidar_scan_proof_collector_script_path() -> str:
    """collector 固定从同目录寻找，部署时能精确发现脚本是否同步到上位机。"""
    return str(Path(__file__).resolve().with_name("o1_lidar_scan_proof_collector.py"))


def parse_last_json_object(text: str) -> tuple[dict[str, Any] | None, dict[str, str] | None]:
    """collector stdout 只信最后一个 JSON object，避免日志行干扰 HTTP 回包。"""
    for line in reversed(text.splitlines()):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed, None
        return None, {"type": "ValueError", "message": "collector JSON root is not an object"}
    return None, {"type": "ValueError", "message": "collector did not print a JSON object"}


def preview_text(value: Any, limit: int = 1200) -> str:
    """subprocess timeout 里 stdout/stderr 可能不是 str，统一压成短文本。"""
    if value is None:
        return ""
    if isinstance(value, bytes):
        text = value.decode("utf-8", errors="replace")
    else:
        text = str(value)
    return text[-limit:]


def run_lidar_scan_proof_collector(
    *,
    artifact_path: str,
    upper_api_base_url: str = "http://127.0.0.1:8787",
    timeout_s: float = DEFAULT_LIDAR_SCAN_PROOF_REFRESH_TIMEOUT_S,
    script_path: str | None = None,
) -> dict[str, Any]:
    """运行只读 proof collector；这里不拼 shell，避免注入和误触发控制命令。"""
    script = script_path or lidar_scan_proof_collector_script_path()
    if not Path(script).exists():
        return {
            "command_result": {
                "mode": "read_only_scan_proof_collector",
                "executed": False,
                "ok": False,
                "reason": "collector_script_missing",
                "script_path": script,
                "error": {"type": "FileNotFoundError", "message": f"{script} is missing"},
            },
            "collector_payload": None,
            "parse_error": None,
        }
    collector_timeout_s = min(max(float(timeout_s), 1.0), 30.0)
    # collector 内部会做 ROS2 CLI/topic timeout，这里额外给进程总时限，防止 HTTP refresh 卡死。
    process_timeout_s = min(max(collector_timeout_s * 6 + 12.0, 20.0), 210.0)
    argv = [
        sys.executable or "python3",
        script,
        "--once-json",
        "--expect-existing-topics",
        "--output",
        artifact_path,
        "--upper-api-base-url",
        upper_api_base_url,
        "--timeout-s",
        str(collector_timeout_s),
    ]
    try:
        completed = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=process_timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "command_result": {
                "mode": "read_only_scan_proof_collector",
                "executed": True,
                "ok": False,
                "argv": argv,
                "script_path": script,
                "timeout_s": process_timeout_s,
                "error": {"type": "TimeoutExpired", "message": str(exc)},
                "stdout_preview": preview_text(exc.stdout),
                "stderr_preview": preview_text(exc.stderr),
            },
            "collector_payload": None,
            "parse_error": {"type": "TimeoutExpired", "message": "collector process timed out before JSON artifact could be trusted"},
        }
    except Exception as exc:  # noqa: BLE001 - 现场 Python/权限异常要结构化返回给 PC。
        return {
            "command_result": {
                "mode": "read_only_scan_proof_collector",
                "executed": False,
                "ok": False,
                "argv": argv,
                "script_path": script,
                "error": compact_error(exc),
            },
            "collector_payload": None,
            "parse_error": None,
        }
    parsed, parse_error = parse_last_json_object(completed.stdout)
    command_ok = completed.returncode == 0 and parsed is not None
    return {
        "command_result": {
            "mode": "read_only_scan_proof_collector",
            "executed": True,
            "ok": command_ok,
            "argv": argv,
            "script_path": script,
            "timeout_s": process_timeout_s,
            "returncode": completed.returncode,
            "stdout_preview": completed.stdout[-1200:],
            "stderr_preview": completed.stderr[-1200:],
            "parse_error": parse_error,
        },
        "collector_payload": parsed,
        "parse_error": parse_error,
    }


def run_lidar_driver_diagnostics_scan_proof_refresh(
    *,
    artifact_path: str,
    diagnostics_path: str | None = None,
    lifecycle_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """默认 refresh 只消费 driver 每秒诊断，避免 Orange Pi 上再拉起 ROS2 CLI 子进程。"""
    lifecycle_status = lifecycle_status if isinstance(lifecycle_status, dict) else read_radar_lifecycle_status()
    lifecycle_latest = lifecycle_status.get("latest_result") if isinstance(lifecycle_status.get("latest_result"), dict) else {}
    resolved_diagnostics_path = (
        diagnostics_path
        or lifecycle_status.get("driver_diagnostics_path")
        or lifecycle_latest.get("driver_diagnostics_path")
    )
    diagnostics = read_lidar_driver_diagnostics_artifact(str(resolved_diagnostics_path) if resolved_diagnostics_path else None)
    artifact = diagnostics.get("artifact") if isinstance(diagnostics.get("artifact"), dict) else {}
    runtime = diagnostics.get("runtime") if isinstance(diagnostics.get("runtime"), dict) else {}
    serial = diagnostics.get("serial") if isinstance(diagnostics.get("serial"), dict) else {}
    scan_preview = diagnostics.get("scan_preview") if isinstance(diagnostics.get("scan_preview"), dict) else {}
    generated_at_ms = now_ms()
    diagnostics_age_ms = None
    if isinstance(artifact.get("mtime_ms"), int):
        diagnostics_age_ms = max(0, generated_at_ms - int(artifact["mtime_ms"]))
    diagnostics_fresh = diagnostics.get("status") == "loaded" and (
        diagnostics_age_ms is None or diagnostics_age_ms <= 5_000
    )
    scan_point_count = int(scan_preview.get("scan_preview_point_count") or 0)
    scan_source_count = int(scan_preview.get("scan_preview_source_point_count") or runtime.get("last_scan_range_count") or 0)
    scan_once_observed = diagnostics_fresh and diagnostics.get("diagnosis_status") == "scan_published" and scan_source_count > 0
    # fresh 诊断文件由 driver 秒级重写；这里把它作为轻量连续窗口，而不是再执行 `ros2 topic hz`。
    scan_hz_observed = bool(scan_once_observed)
    raw_packet_once_observed = diagnostics_fresh and (
        int(runtime.get("published_raw_packet_count") or 0) > 0
        or int(serial.get("packet_count_total") or 0) > 0
    )
    static_tf_text = str(lifecycle_latest.get("static_tf") or "")
    frame_id = str(scan_preview.get("scan_preview_frame_id") or lifecycle_latest.get("frame_id") or "laser_frame")
    tf_observed = bool(lifecycle_status.get("running") and "base_link" in static_tf_text and frame_id in static_tf_text)
    required_observations = {
        "scan_once": {
            "topic": "/scan",
            "observed": scan_once_observed,
            "result_key": "driver_diagnostics.runtime.last_scan_range_count",
            "source": "lidar_driver_diagnostics_file",
        },
        "scan_hz": {
            "topic": "/scan",
            "observed": scan_hz_observed,
            "average_rate_hz": None,
            "result_key": "driver_diagnostics.artifact.mtime_ms",
            "source": "fresh_lidar_driver_diagnostics_file",
        },
        "raw_packet_once": {
            "topic": "/lidar/raw_packet",
            "observed": raw_packet_once_observed,
            "result_key": "driver_diagnostics.runtime.published_raw_packet_count",
            "source": "lidar_driver_diagnostics_file",
        },
        "tf": {
            "parent_frame": "base_link",
            "child_frame": frame_id,
            "observed": tf_observed,
            "result_key": "lidar_lifecycle_status.static_tf",
            "source": "lidar_lifecycle_status_managed_runtime",
        },
    }
    all_required_observations_observed = all(item["observed"] for item in required_observations.values())
    blockers = []
    if diagnostics.get("status") != "loaded":
        blockers.append({"code": "driver_diagnostics_not_loaded", "detail": str(diagnostics.get("status") or "not_loaded")})
    if not diagnostics_fresh:
        blockers.append({"code": "driver_diagnostics_stale", "detail": f"age_ms={diagnostics_age_ms}"})
    if not scan_once_observed:
        blockers.append({"code": "scan_preview_not_observed", "detail": str(diagnostics.get("diagnosis_status") or "not_loaded")})
    if not raw_packet_once_observed:
        blockers.append({"code": "raw_packet_not_observed", "detail": "driver diagnostics has no raw packet evidence"})
    if not tf_observed:
        blockers.append({"code": "static_tf_not_observed", "detail": str(static_tf_text or "not_loaded")})
    current_scan_preview = scan_preview if diagnostics_fresh and scan_once_observed and scan_point_count > 0 else {}
    payload: dict[str, Any] = {
        "schema": "trashbot.o1.lidar_scan_proof.v1",
        "generated_at_ms": generated_at_ms,
        "vendor_sources": LIDAR_VENDOR_SOURCES,
        "evidence_boundary": "lidar_driver_diagnostics_scan_proof_not_base_hil",
        "collector_mode": "driver_diagnostics",
        "driver_diagnostics": diagnostics,
        "lifecycle_status": lifecycle_status,
        "topic_reads": {
            "attempted": False,
            "reason": "driver_diagnostics_lightweight_refresh_avoids_ros2_cli_oom",
            "results": {},
        },
        "proof": {
            "status": "scan_once_hz_raw_packet_tf_observed" if all_required_observations_observed else "driver_diagnostics_partial_or_blocked",
            "scan_topic": "/scan",
            "raw_packet_topic": "/lidar/raw_packet",
            "tf_parent_frame": "base_link",
            "tf_child_frame": frame_id,
            "scan_once_observed": scan_once_observed,
            "scan_hz_observed": scan_hz_observed,
            "scan_hz_average_rate_hz": None,
            "raw_packet_once_observed": raw_packet_once_observed,
            "tf_observed": tf_observed,
            "required_observations": required_observations,
            "all_required_observations_observed": all_required_observations_observed,
            "runtime_summary_fallback_used": False,
            "pointcloud_fabricated": False,
            "driver_started_by_collector": False,
            "lidar_start_command_sent_by_collector": False,
        },
        "blockers": blockers,
        "blocked_commands_not_sent": ["T=1", "T=13", "T=130", "T=131", "/cmd_vel", "/api/base/manual"],
        "readback_sends_commands": False,
        "sends_commands": False,
        "sends_motion_commands": False,
        "sends_base_motion_commands": False,
        "uses_base_uart": False,
        "opens_serial": False,
        **proof_flags(),
    }
    if current_scan_preview:
        payload.update({
            "scan_preview_points": current_scan_preview.get("scan_preview_points", []),
            "scan_preview_point_count": current_scan_preview.get("scan_preview_point_count", 0),
            "scan_preview_source_point_count": current_scan_preview.get("scan_preview_source_point_count"),
            "scan_preview_frame_id": current_scan_preview.get("scan_preview_frame_id", ""),
            "scan_preview_source": current_scan_preview.get("scan_preview_source"),
        })
    payload["artifact"] = atomic_write_json_artifact(artifact_path, payload)
    return {
        "command_result": {
            "mode": "lidar_driver_diagnostics_refresh",
            "executed": True,
            "ok": all_required_observations_observed,
            "diagnostics_path": str(resolved_diagnostics_path or ""),
            "diagnostics_fresh": diagnostics_fresh,
            "diagnostics_age_ms": diagnostics_age_ms,
            "collector_replaced": "read_only_scan_proof_collector",
        },
        "collector_payload": payload,
        "parse_error": None,
    }


def summarize_lidar_refresh_blockers(
    command_result: dict[str, Any],
    collector_payload: dict[str, Any] | None,
    parse_error: dict[str, str] | None,
    runtime_result: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """把部署、进程、artifact 和 ROS2 topic blocker 合成 PC 可读列表。"""
    blockers: list[dict[str, str]] = []
    if runtime_result and runtime_result.get("ok") is not True:
        error = runtime_result.get("error") if isinstance(runtime_result.get("error"), dict) else {}
        detail = error.get("message") or "LiDAR runtime command did not start or stay healthy through warmup"
        blockers.append({"code": str(error.get("type") or "lidar_runtime_start_failed"), "detail": str(detail)})
    if not command_result.get("ok"):
        reason = command_result.get("reason") or "collector_process_failed"
        detail = command_result.get("error", {}).get("message") if isinstance(command_result.get("error"), dict) else None
        blockers.append({"code": str(reason), "detail": str(detail or "read-only scan proof collector did not complete successfully")})
    if parse_error:
        blockers.append({"code": "collector_json_parse_failed", "detail": parse_error.get("message", "collector JSON parse failed")})
    if isinstance(collector_payload, dict):
        artifact = collector_payload.get("artifact") if isinstance(collector_payload.get("artifact"), dict) else {}
        artifact_ok = artifact.get("ok")
        if artifact and artifact_ok is not True:
            blockers.append({"code": "scan_proof_artifact_write_failed", "detail": str(artifact.get("error") or artifact)})
        for item in collector_payload.get("blockers", []):
            if isinstance(item, dict):
                blockers.append({"code": str(item.get("code", "collector_blocker")), "detail": str(item.get("detail", ""))})
        proof = collector_payload.get("proof") if isinstance(collector_payload.get("proof"), dict) else {}
        if proof and proof.get("all_required_observations_observed") is not True and not blockers:
            blockers.append({"code": "required_observations_not_all_observed", "detail": str(proof.get("status", "not_proven"))})
    return blockers


def lidar_refresh_proof_summary(collector_payload: dict[str, Any] | None) -> dict[str, Any]:
    """从 collector payload 提取稳定 proof 字段，避免 PC 解析 stdout。"""
    proof = collector_payload.get("proof") if isinstance(collector_payload, dict) and isinstance(collector_payload.get("proof"), dict) else {}
    return {
        "proof_status": proof.get("status") if isinstance(proof, dict) else None,
        "scan_once_observed": proof.get("scan_once_observed") if isinstance(proof, dict) else None,
        "scan_hz_observed": proof.get("scan_hz_observed") if isinstance(proof, dict) else None,
        "scan_hz_average_rate_hz": proof.get("scan_hz_average_rate_hz") if isinstance(proof, dict) else None,
        "raw_packet_once_observed": proof.get("raw_packet_once_observed") if isinstance(proof, dict) else None,
        "tf_observed": proof.get("tf_observed") if isinstance(proof, dict) else None,
        "all_required_observations_observed": proof.get("all_required_observations_observed") if isinstance(proof, dict) else None,
    }


def build_lidar_scan_proof_refresh_payload(
    *,
    artifact_path: str,
    refresh_result: dict[str, Any],
    timeout_s: float,
    runtime_result: dict[str, Any] | None = None,
    runtime_requested: bool = False,
    runtime_warmup_s: float = DEFAULT_LIDAR_SCAN_PROOF_RUNTIME_WARMUP_S,
    collector_mode: str = "driver_diagnostics",
) -> dict[str, Any]:
    """构造 refresh 回包；即使 proof 观察到 `/scan`，也不能外推到底盘可控。"""
    command_result = refresh_result.get("command_result", {})
    collector_payload = refresh_result.get("collector_payload") if isinstance(refresh_result.get("collector_payload"), dict) else None
    parse_error = refresh_result.get("parse_error") if isinstance(refresh_result.get("parse_error"), dict) else None
    proof_summary = lidar_refresh_proof_summary(collector_payload)
    blockers = summarize_lidar_refresh_blockers(command_result, collector_payload, parse_error, runtime_result)
    latest_http_status, latest_readback = read_lidar_scan_proof_latest_artifact(artifact_path)
    latest_evidence_ref = latest_readback.get("latest_evidence_ref") if latest_http_status == 200 else None
    scan_runtime_proven = bool(proof_summary.get("scan_once_observed") and proof_summary.get("scan_hz_observed"))
    all_required_observed = bool(proof_summary.get("all_required_observations_observed"))
    runtime_ok = not runtime_requested or bool(runtime_result and runtime_result.get("ok"))
    runtime_started = bool(runtime_result and runtime_result.get("ok"))
    evidence_type = "robot_runtime_material" if all_required_observed and runtime_ok else "blocked_with_root_cause"
    status = "refreshed" if command_result.get("ok") and runtime_ok else "blocked"
    # API-managed runtime 会碰 LiDAR 串口/A5 60；blocked 字段只能列仍被禁止的底盘动作。
    blocked_commands_not_sent = ["T=1", "T=13", "T=130", "T=131", "/cmd_vel", "/api/base/manual"]
    if not runtime_requested:
        blocked_commands_not_sent.insert(0, "A5 60")
    blocked_devices_not_opened = ["/dev/ttyS5"] if runtime_requested else ["/dev/ttyS5", "/dev/ttyACM0", "/dev/lidar"]
    return {
        "schema": f"{SCHEMA}.lidar_scan_proof_refresh_result",
        "generated_at_ms": now_ms(),
        "endpoint": ROUTE_PATHS["radar_scan_proof_refresh"],
        "request": {
            "method": "POST",
            "endpoint": ROUTE_PATHS["radar_scan_proof_refresh"],
            "mode": collector_mode,
            "timeout_s": timeout_s,
            "runtime_requested": runtime_requested,
            "runtime_warmup_s": runtime_warmup_s,
        },
        "status": status,
        "proof_state": proof_summary.get("proof_status") or "not_proven",
        "evidence_ref": latest_evidence_ref,
        "latest_evidence_ref": latest_evidence_ref,
        "latest_readback_http_status": latest_http_status,
        "evidence_type": evidence_type,
        "runtime_start": runtime_result,
        "collector": {
            "script_path": command_result.get("script_path"),
            "expect_existing_topics": True,
            "starts_driver": runtime_started,
            "opens_lidar_serial": runtime_started,
            "sends_lidar_start_command": runtime_started,
        },
        "command_result": command_result,
        "artifact": lidar_scan_proof_artifact_info(artifact_path),
        "artifact_path": artifact_path,
        "latest_result": collector_payload,
        "proof_summary": proof_summary,
        "blockers_summary": blockers,
        "blocked_commands_not_sent": blocked_commands_not_sent,
        "blocked_devices_not_opened": blocked_devices_not_opened,
        "read_only_topic_observation": True,
        "runtime_start_proven": runtime_started,
        "ros2_runtime_proven": all_required_observed and runtime_ok,
        "scan_runtime_proven": scan_runtime_proven,
        "software_guard": evidence_type != "robot_runtime_material",
        "not_proven": evidence_type != "robot_runtime_material",
        "sends_commands": bool(runtime_requested),
        "sends_motion_commands": False,
        "sends_base_motion_commands": False,
        "uses_base_uart": False,
        "opens_serial": False,
        "opens_lidar_serial": runtime_started,
        "starts_ros2": runtime_started,
        "starts_lidar_driver": runtime_started,
        "sends_lidar_start_command": runtime_started,
        "robot_control_executed": False,
        "delivery_success": False,
        "hil_pass": False,
        "safe_to_control": False,
        "primary_actions_enabled": False,
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
        "sends_commands": bool(configured and result_ok),
        **proof_flags(),
    }
    if extra:
        payload.update(extra)
    return payload


def normalize_map_runtime_body(body: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str] | None]:
    """直连上位机也必须校验 body；artifact_path 只回显忽略，不能成为写文件入口。"""
    raw_map_name = body.get("map_name")
    map_name = "trashbot_map"
    if raw_map_name is not None:
        if not isinstance(raw_map_name, str):
            return {}, {"type": "invalid_map_name", "message": "map_name must be a string"}
        candidate = raw_map_name.strip()
        if not SAFE_MAP_NAME_PATTERN.fullmatch(candidate):
            return {}, {
                "type": "invalid_map_name",
                "message": "map_name must match ^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$",
            }
        map_name = candidate
    ignored_artifact_path = body.get("artifact_path") if body.get("artifact_path") is not None else None
    return {
        "map_name": map_name,
        "requested_map_name": raw_map_name,
        "requested_artifact_path": ignored_artifact_path,
        "artifact_path_ignored": ignored_artifact_path is not None,
        "artifact_path_policy": "ignored_by_upper_api; map files always go under configured map_artifact_dir",
    }, None


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


def camera_source_usage_summary(source_usage: dict[str, Any]) -> str:
    """把相机占用列表压成短文本；顶层 health 只需要说明有没有进程占用。"""
    owners = source_usage.get("owners") if isinstance(source_usage.get("owners"), list) else []
    if not owners:
        return "none"
    summary_items: list[str] = []
    for owner in owners[:4]:
        if not isinstance(owner, dict):
            continue
        pid = owner.get("pid", "unknown")
        command = str(owner.get("command") or "unknown").strip()
        summary_items.append(f"pid={pid} {command[:80]}")
    return "；".join(summary_items) if summary_items else "none"


def camera_action_plain_text(action: Any) -> str:
    """把 8088 的短 token 翻译成现场可执行中文；这里只解释状态，不执行动作。"""
    value = str(action or "").strip()
    if not value or value in {"not_loaded", "none"}:
        return ""
    normalized = re.sub(r"\s+", "_", value).lower()
    if normalized == "check_usb_camera_input_power_or_known_good_uvc":
        return "检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。"
    if normalized == "check_usb_cable_port_power_or_known_good_uvc":
        return "检查 USB 线、接口和摄像头供电，必要时换 known-good UVC 复测；共享预览不是页面独占。"
    if normalized == "move_camera_to_high_speed_usb_port_or_powered_hub":
        return "摄像头现在挂在 USB 12M full-speed，换高速 USB 口/线或带供电 USB Hub，减少转接并确认供电后复测；共享预览不是页面独占。"
    if normalized == "free_memory_or_reboot_then_probe_known_good_uvc":
        return "先释放上位机内存或重启上位机，再复测相机首帧；若仍无画面，换 known-good UVC 复测；共享预览不是页面独占。"
    if normalized == "free_memory_or_reboot_if_no_frame_persists":
        return "若无首帧持续，先释放上位机内存或重启后复测；共享预览不是页面独占。"
    if normalized in {"open_shared_preview", "open_shared_preview_or_run_first_frame_probe"}:
        return "需要看画面时打开共享预览，或点只读检查复测首帧。"
    return f"{value.replace('_', ' ')}。"


def camera_hardware_action_label(source_diagnosis_status: Any, usb_speed: Any) -> str:
    """硬件动作标签给 PC/curl 短读；它不是按钮动作，也不改变控制门禁。"""
    status = str(source_diagnosis_status or "")
    speed = str(usb_speed or "")
    if status == "uvc_full_speed_usb_not_exclusive" or speed == "12M":
        return "换高速USB后复测"
    if status == "uvc_transport_error_not_exclusive":
        return "检查USB/供电后复测"
    if status == "uvc_cma_alloc_failed_not_exclusive":
        return "释放内存/重启后复测"
    if status in {"uvc_no_frame_not_exclusive", "source_first_frame_failed", "first_frame_failed"}:
        return "检查摄像头输入/供电后复测"
    return "复测相机首帧"


def flatten_camera_health_aliases(payload: dict[str, Any]) -> dict[str, Any]:
    """把 8088 health 的嵌套诊断平铺到 8787 顶层，方便 PC/ curl 直接判断是不是独占。"""
    if not isinstance(payload, dict):
        return {}
    current_selection = payload.get("current_selection") if isinstance(payload.get("current_selection"), dict) else {}
    source_usage = payload.get("source_usage") if isinstance(payload.get("source_usage"), dict) else {}
    media_diagnostics = payload.get("media_diagnostics") if isinstance(payload.get("media_diagnostics"), dict) else {}
    media_source_usage = (
        media_diagnostics.get("source_usage")
        if isinstance(media_diagnostics.get("source_usage"), dict)
        else {}
    )
    source_diagnosis = payload.get("source_diagnosis") if isinstance(payload.get("source_diagnosis"), dict) else {}
    uvc_usb_topology = payload.get("uvc_usb_topology") if isinstance(payload.get("uvc_usb_topology"), dict) else {}
    cma_memory_diagnostics = payload.get("cma_memory_diagnostics") if isinstance(payload.get("cma_memory_diagnostics"), dict) else {}
    media_source_diagnosis = (
        media_diagnostics.get("source_diagnosis")
        if isinstance(media_diagnostics.get("source_diagnosis"), dict)
        else {}
    )
    media_uvc_usb_topology = (
        media_diagnostics.get("uvc_usb_topology")
        if isinstance(media_diagnostics.get("uvc_usb_topology"), dict)
        else {}
    )
    media_cma_memory_diagnostics = (
        media_diagnostics.get("cma_memory_diagnostics")
        if isinstance(media_diagnostics.get("cma_memory_diagnostics"), dict)
        else {}
    )
    diagnosis = source_diagnosis or media_source_diagnosis
    usb_topology = uvc_usb_topology or media_uvc_usb_topology
    cma_diagnostics = cma_memory_diagnostics or media_cma_memory_diagnostics
    usage = source_usage or media_source_usage
    selected_path = payload.get("selected_path") or current_selection.get("selected_path") or payload.get("video_source")
    selected_name = payload.get("selected_name") or current_selection.get("selected_name") or diagnosis.get("selected_name")
    # 顶层 alias 只复制已有只读事实，不打开摄像头，也不改变 8088 原始嵌套合同。
    return {
        "selected_path": selected_path or None,
        "selected_name": selected_name or None,
        "selected_is_uvc_or_usb": bool(current_selection.get("selected_is_uvc_or_usb") or diagnosis.get("selected_is_uvc_or_usb")),
        "selected_formats_summary": current_selection.get("selected_formats_summary") or "not_loaded",
        "source_usage_status": usage.get("status") or diagnosis.get("source_usage_status") or "not_loaded",
        "source_usage_owner_count": usage.get("owner_count") if usage.get("owner_count") is not None else diagnosis.get("source_usage_owner_count", "not_loaded"),
        "source_usage_other_owner_count": usage.get("other_owner_count", "not_loaded"),
        "source_usage_summary": camera_source_usage_summary(usage) if usage else "not_loaded",
        "source_diagnosis_status": diagnosis.get("status") or "not_loaded",
        "source_diagnosis_plain_hint": diagnosis.get("plain_hint") or "not_loaded",
        "source_diagnosis_next_action": diagnosis.get("next_action") or "not_loaded",
        "source_diagnosis_not_exclusive": diagnosis.get("not_exclusive") if diagnosis.get("not_exclusive") is not None else "not_loaded",
        "uvc_usb_topology_status": usb_topology.get("status") or diagnosis.get("uvc_usb_topology_status") or "not_loaded",
        "uvc_usb_topology_plain_hint": usb_topology.get("plain_hint") or "not_loaded",
        "uvc_usb_topology_next_action": usb_topology.get("next_action") or "not_loaded",
        "uvc_usb_topology_video_usb_speed": usb_topology.get("video_usb_speed") or diagnosis.get("uvc_usb_topology_video_usb_speed") or "not_loaded",
        "uvc_usb_topology_kernel_usb_address": usb_topology.get("kernel_usb_address") or "not_loaded",
        "uvc_usb_topology_video_interface_count": usb_topology.get("video_interface_count", "not_loaded"),
        "cma_memory_diagnostics_status": cma_diagnostics.get("status") or diagnosis.get("cma_memory_diagnostics_status") or "not_loaded",
        "cma_memory_diagnostics_plain_hint": cma_diagnostics.get("plain_hint") or "not_loaded",
        "cma_memory_diagnostics_next_action": cma_diagnostics.get("next_action") or "not_loaded",
        "cma_memory_diagnostics_cma_total_kb": cma_diagnostics.get("cma_total_kb", "not_loaded"),
        "cma_memory_diagnostics_cma_free_kb": cma_diagnostics.get("cma_free_kb", "not_loaded"),
        "cma_memory_diagnostics_failure_count": cma_diagnostics.get("failure_count", "not_loaded"),
        "cma_memory_diagnostics_latest_failure": cma_diagnostics.get("latest_failure") or "",
        "shared_preview_contract": payload.get("shared_preview_contract")
        or media_diagnostics.get("shared_preview_contract")
        or diagnosis.get("shared_preview_contract")
        or "single_shared_capture_for_multiple_clients",
    }


def camera_first_frame_attempts_summary(payload: dict[str, Any]) -> str:
    """把相机首帧尝试矩阵压成一行，方便现场 curl 直接判断哪种格式无帧。"""
    if not isinstance(payload, dict):
        return "none"
    candidates: list[Any] = []
    last_error = payload.get("last_first_frame_error") if isinstance(payload.get("last_first_frame_error"), dict) else {}
    for key in ("first_frame_format_attempts", "last_first_frame_format_attempts"):
        value = payload.get(key)
        if isinstance(value, list):
            candidates = value
            break
    if not candidates and isinstance(last_error.get("first_frame_format_attempts"), list):
        candidates = last_error["first_frame_format_attempts"]
    if not candidates:
        return "none"
    parts: list[str] = []
    for item in candidates[:6]:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or item.get("fourcc") or item.get("open_source") or "unknown").strip()
        backend = str(item.get("open_backend") or "").strip()
        source = str(item.get("open_source") or "").strip()
        status = str(item.get("status") or item.get("failure_reason") or "not_loaded").strip()
        suffix_items = [value for value in (source, backend if backend and backend != "default" else "") if value]
        suffix = f"({'/'.join(suffix_items)})" if suffix_items and source not in label else ""
        plain_status = "无首帧" if "unreadable" in status or "false" in status or "timeout" in status else status
        parts.append(f"{label}{suffix} {plain_status}")
    return "；".join(parts) if parts else "none"


def camera_first_frame_fallback_aliases(payload: dict[str, Any]) -> dict[str, Any]:
    """透传共享 MJPEG 首帧兜底结果，避免现场只能从长 attempts 文案里猜。"""
    if not isinstance(payload, dict):
        return {
            "mjpeg_open_source_fallback_attempted": False,
            "open_source_fallback_failure_reason": "not_loaded",
            "primary_source_failure_reason": "not_loaded",
        }
    last_error = payload.get("last_first_frame_error") if isinstance(payload.get("last_first_frame_error"), dict) else {}
    fallback_attempted = bool(
        payload.get("mjpeg_open_source_fallback_attempted")
        or last_error.get("mjpeg_open_source_fallback_attempted")
    )
    open_source_reason = (
        payload.get("open_source_fallback_failure_reason")
        or last_error.get("open_source_fallback_failure_reason")
        or "not_loaded"
    )
    primary_reason = (
        payload.get("primary_source_failure_reason")
        or last_error.get("primary_source_failure_reason")
        or payload.get("source_failure_reason")
        or last_error.get("failure_reason")
        or "not_loaded"
    )
    return {
        "mjpeg_open_source_fallback_attempted": fallback_attempted,
        "open_source_fallback_failure_reason": str(open_source_reason),
        "primary_source_failure_reason": str(primary_reason),
    }


def camera_relay_first_frame_error_payload(relay_snapshot: dict[str, Any]) -> dict[str, Any]:
    """从 relay 失败体里取真实首帧失败；cooldown 外壳不能遮住内层无帧事实。"""
    if not isinstance(relay_snapshot, dict):
        return {}
    payload = relay_snapshot.get("last_error_payload")
    if not isinstance(payload, dict):
        return {}
    nested = payload.get("last_first_frame_error")
    if isinstance(nested, dict):
        return nested
    return payload


def camera_failure_reason_from_payload(payload: dict[str, Any]) -> str:
    """按优先级提取首帧失败原因，供 status 判断硬件动作和 PC 文案。"""
    if not isinstance(payload, dict):
        return ""
    for key in ("source_failure_reason", "primary_source_failure_reason", "failure_reason", "error"):
        value = str(payload.get(key) or "").strip()
        if value and value not in {"none", "not_loaded", "error"}:
            return value
    return ""


def camera_mjpeg_preview_status(health_payload: dict[str, Any], relay_snapshot: dict[str, Any]) -> str:
    """状态端点只表达当前可见性，不因为 health 已选源就假装页面已经看到画面。"""
    if relay_snapshot.get("last_error_payload") or relay_snapshot.get("last_failure_reason"):
        return "source_first_frame_failed"
    if relay_snapshot.get("content_type_loaded") or relay_snapshot.get("has_recent_frame"):
        return "visible"
    readiness = str(health_payload.get("source_readiness") or "")
    status = str(health_payload.get("status") or "")
    failure_reason = str(health_payload.get("source_failure_reason") or "")
    if status == "source_first_frame_failed" or readiness == "first_frame_failed" or failure_reason:
        return "source_first_frame_failed"
    if status == "ready" and readiness == "first_frame_observed":
        return "source_ready_not_viewing"
    return "no_current_frame"


def camera_mjpeg_status_payload(
    *,
    camera_base_url: str,
    health_http_status: int,
    health_payload: dict[str, Any],
    relay_snapshot: dict[str, Any],
) -> dict[str, Any]:
    """8787 直连状态只汇总 8088 health 与本进程 relay，不拉流、不打开相机。"""
    aliases = flatten_camera_health_aliases(health_payload)
    relay_first_frame_error = camera_relay_first_frame_error_payload(relay_snapshot)
    relay_first_frame_failure_reason = camera_failure_reason_from_payload(relay_first_frame_error)
    source_readiness = str(health_payload.get("source_readiness") or aliases.get("source_readiness") or "not_loaded")
    source_failure_reason = str(health_payload.get("source_failure_reason") or "not_loaded")
    fallback_aliases = camera_first_frame_fallback_aliases(health_payload)
    relay_fallback_aliases = camera_first_frame_fallback_aliases(relay_first_frame_error)
    preview_status = camera_mjpeg_preview_status(health_payload, relay_snapshot)
    selected_name = str(aliases.get("selected_name") or "not_loaded")
    source_diagnosis_status = str(aliases.get("source_diagnosis_status") or "not_loaded")
    relay_no_frame_failure = (
        preview_status == "source_first_frame_failed"
        and relay_first_frame_failure_reason in CAMERA_FIRST_FRAME_FAILURE_REASONS
    )
    weak_source_diagnosis = source_diagnosis_status in {
        "",
        "none",
        "not_loaded",
        "source_not_probed",
        "source_selected_not_probed",
    }
    if relay_no_frame_failure and weak_source_diagnosis:
        source_diagnosis_status = "uvc_no_frame_not_exclusive"
        aliases["source_diagnosis_plain_hint"] = (
            f"不是页面独占：{selected_name} 当前没人占用，但 UVC 设备没有输出视频帧。"
        )
        aliases["source_diagnosis_next_action"] = "check_usb_camera_input_power_or_known_good_uvc"
        aliases["source_diagnosis_not_exclusive"] = True
        source_readiness = "first_frame_failed"
        source_failure_reason = relay_first_frame_failure_reason
    source_diagnosis_next_action = aliases.get("source_diagnosis_next_action") or "not_loaded"
    source_diagnosis_next_action_plain = camera_action_plain_text(source_diagnosis_next_action)
    source_diagnosis_plain_hint = str(aliases.get("source_diagnosis_plain_hint") or "")
    hardware_action_label = camera_hardware_action_label(source_diagnosis_status, aliases.get("uvc_usb_topology_video_usb_speed"))
    hardware_action_required = source_diagnosis_status in {
        "uvc_full_speed_usb_not_exclusive",
        "uvc_transport_error_not_exclusive",
        "uvc_cma_alloc_failed_not_exclusive",
        "uvc_no_frame_not_exclusive",
        "source_first_frame_failed",
        "first_frame_failed",
    } or str(aliases.get("uvc_usb_topology_video_usb_speed") or "") == "12M"
    if preview_status == "visible":
        visible_plain = "共享 MJPEG 预览已有当前画面或最近帧。"
        next_action_plain = "继续使用同一条共享预览；多人页面会复用同一个上游流。"
        visible_status = "visible"
        wysiwyg_status_plain = "画面已可见：共享 MJPEG 预览已有当前画面。"
    elif preview_status == "source_first_frame_failed":
        visible_plain = f"画面未可见：{source_diagnosis_plain_hint}" if source_diagnosis_plain_hint and source_diagnosis_plain_hint != "not_loaded" else f"画面未可见：不是页面独占：{selected_name} 当前没有证明被其他页面独占，但 UVC 设备没有输出视频帧。"
        next_action_plain = source_diagnosis_next_action_plain or "检查 USB、摄像头输入或供电，必要时换 known-good UVC 复测；共享预览不是页面独占。"
        visible_status = "not_visible_source_first_frame_failed"
        wysiwyg_status_plain = visible_plain
    elif preview_status == "source_ready_not_viewing":
        visible_plain = "相机源已有首帧证明，但当前没有浏览器正在拉共享 MJPEG。"
        next_action_plain = "打开 PC 实时画面；多人页面会复用同一条共享预览。"
        visible_status = "not_visible_no_viewer"
        wysiwyg_status_plain = "画面未可见：当前没有页面正在显示共享 MJPEG。"
    else:
        visible_plain = "画面未可见：共享 MJPEG 还没有当前帧。"
        next_action_plain = "打开共享预览或运行只读首帧检查；不要用多个页面各自抢占相机。"
        visible_status = "not_visible_no_current_frame"
        wysiwyg_status_plain = visible_plain

    client_count = int(relay_snapshot.get("client_count") or 0)
    health_attempts_summary = camera_first_frame_attempts_summary(health_payload)
    relay_attempts_summary = camera_first_frame_attempts_summary(relay_first_frame_error)
    attempts_summary = health_attempts_summary if health_attempts_summary != "none" else relay_attempts_summary
    return {
        "schema": f"{SCHEMA}.camera_mjpeg_status",
        "proxy_status": "status_loaded" if health_http_status == 200 else "camera_health_unavailable",
        "endpoint": ROUTE_PATHS["camera_mjpeg_status"],
        "camera_health_endpoint": ROUTE_PATHS["camera_health"],
        "remote_endpoint": "/mjpeg",
        "upper_api_proxy": True,
        "upper_api_camera_base_url": camera_base_url,
        "camera_health_http_status": health_http_status,
        "client_count": client_count,
        "shared_preview_client_count": client_count,
        "viewer_count": client_count,
        "upstream_active": bool(relay_snapshot.get("upstream_active")),
        "shared_preview_upstream_active": bool(relay_snapshot.get("upstream_active")),
        "content_type_loaded": bool(relay_snapshot.get("content_type_loaded")),
        "shared_preview_content_type_loaded": bool(relay_snapshot.get("content_type_loaded")),
        "shared_capture": True,
        "shared_preview_shared_capture": True,
        "exclusive_camera_claim": False,
        "shared_preview_exclusive_camera_claim": False,
        "shared_preview_contract": aliases.get("shared_preview_contract") or "single_shared_capture_for_multiple_clients",
        "shared_preview_multi_viewer_status": "single_upstream_multi_viewer",
        "last_failure_reason": relay_snapshot.get("last_failure_reason") or source_failure_reason,
        "shared_preview_last_failure_reason": relay_snapshot.get("last_failure_reason") or source_failure_reason,
        "last_remote_http_status": relay_snapshot.get("last_remote_http_status"),
        "shared_preview_last_remote_http_status": relay_snapshot.get("last_remote_http_status"),
        "last_failure_at_ms": relay_snapshot.get("last_failure_at_ms"),
        "shared_preview_last_failure_at_ms": relay_snapshot.get("last_failure_at_ms"),
        "source_diagnosis_status": source_diagnosis_status,
        "source_diagnosis_plain_hint": aliases.get("source_diagnosis_plain_hint") or "not_loaded",
        "source_diagnosis_next_action": source_diagnosis_next_action,
        "source_diagnosis_next_action_plain": source_diagnosis_next_action_plain,
        "source_diagnosis_not_exclusive": aliases.get("source_diagnosis_not_exclusive", "not_loaded"),
        "uvc_usb_topology_status": aliases.get("uvc_usb_topology_status") or "not_loaded",
        "uvc_usb_topology_plain_hint": aliases.get("uvc_usb_topology_plain_hint") or "not_loaded",
        "uvc_usb_topology_next_action": aliases.get("uvc_usb_topology_next_action") or "not_loaded",
        "uvc_usb_topology_video_usb_speed": aliases.get("uvc_usb_topology_video_usb_speed") or "not_loaded",
        "uvc_usb_topology_kernel_usb_address": aliases.get("uvc_usb_topology_kernel_usb_address") or "not_loaded",
        "uvc_usb_topology_video_interface_count": aliases.get("uvc_usb_topology_video_interface_count", "not_loaded"),
        "cma_memory_diagnostics_status": aliases.get("cma_memory_diagnostics_status") or "not_loaded",
        "cma_memory_diagnostics_plain_hint": aliases.get("cma_memory_diagnostics_plain_hint") or "not_loaded",
        "cma_memory_diagnostics_next_action": aliases.get("cma_memory_diagnostics_next_action") or "not_loaded",
        "cma_memory_diagnostics_cma_total_kb": aliases.get("cma_memory_diagnostics_cma_total_kb", "not_loaded"),
        "cma_memory_diagnostics_cma_free_kb": aliases.get("cma_memory_diagnostics_cma_free_kb", "not_loaded"),
        "cma_memory_diagnostics_failure_count": aliases.get("cma_memory_diagnostics_failure_count", "not_loaded"),
        "cma_memory_diagnostics_latest_failure": aliases.get("cma_memory_diagnostics_latest_failure") or "",
        "source_readiness": source_readiness,
        "source_failure_reason": source_failure_reason,
        "last_first_frame_format_attempts_summary": attempts_summary,
        **{
            **fallback_aliases,
            "mjpeg_open_source_fallback_attempted": bool(
                fallback_aliases["mjpeg_open_source_fallback_attempted"]
                or relay_fallback_aliases["mjpeg_open_source_fallback_attempted"]
            ),
            "open_source_fallback_failure_reason": (
                fallback_aliases["open_source_fallback_failure_reason"]
                if fallback_aliases["open_source_fallback_failure_reason"] != "not_loaded"
                else relay_fallback_aliases["open_source_fallback_failure_reason"]
            ),
            "primary_source_failure_reason": (
                fallback_aliases["primary_source_failure_reason"]
                if fallback_aliases["primary_source_failure_reason"] != "not_loaded"
                else relay_fallback_aliases["primary_source_failure_reason"]
            ),
        },
        "selected_path": aliases.get("selected_path") or "not_loaded",
        "selected_name": selected_name,
        "selected_is_uvc_or_usb": aliases.get("selected_is_uvc_or_usb", "not_loaded"),
        "source_usage_status": aliases.get("source_usage_status") or "not_loaded",
        "source_usage_owner_count": aliases.get("source_usage_owner_count", "not_loaded"),
        "source_usage_summary": aliases.get("source_usage_summary") or "not_loaded",
        "status": preview_status,
        "plain_hint": visible_plain,
        "next_action_plain": next_action_plain,
        "preview_status": preview_status,
        "preview_plain_hint": visible_plain,
        "preview_next_action_plain": next_action_plain,
        "preview_visible_status": visible_status,
        "preview_visible_plain": visible_plain,
        "camera_wysiwyg_status_plain": wysiwyg_status_plain,
        "camera_wysiwyg_next_action_plain": next_action_plain,
        "hardware_action_required": hardware_action_required,
        "hardware_action_label": hardware_action_label if hardware_action_required else "复测相机首帧",
        "camera_hardware_action_required": hardware_action_required,
        "camera_hardware_action_label": hardware_action_label if hardware_action_required else "复测相机首帧",
        "camera_reprobe_after_hardware_action_required": hardware_action_required,
        "opens_camera_device": False,
        "starts_camera_webrtc": False,
        "starts_camera_mjpeg_stream": False,
        "sends_motion_commands": False,
        "sends_base_motion_commands": False,
        **proof_flags(),
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
    """压缩 SLAM/map proof；观测齐全时才把顶层状态抬成可消费读回。"""
    http_status, payload = read_runtime_artifact_latest(
        path,
        artifact_info=map_lifecycle_proof_artifact_info(path),
        schema_suffix="map_lifecycle_proof_latest",
        endpoint=ROUTE_PATHS["map_proof_latest"],
        boundary="software_guard_only_not_real_slam_map_or_nav2_consumption",
        source="map_lifecycle_runtime_artifact",
    )
    latest = payload.get("latest_result") if isinstance(payload.get("latest_result"), dict) else None
    observed = map_lifecycle_runtime_readback_contract(latest)
    summary: dict[str, Any] = {
        "schema": f"{SCHEMA}.map_lifecycle_proof_latest_summary",
        "generated_at_ms": now_ms(),
        "endpoint": ROUTE_PATHS["map_proof_latest"],
        "http_status": http_status,
        "artifact": payload["artifact"],
        "latest_result_schema": latest.get("schema") if isinstance(latest, dict) else None,
        "latest_proof_status": latest_proof_value(latest, "status"),
        "latest_evidence_ref": latest_proof_value(latest, "evidence_ref"),
        "latest_map_once_observed": latest_proof_value(latest, "map_once_observed", "/map_once_observed"),
        "latest_map_file_observed": latest_proof_value(
            latest,
            "map_file_observed",
            "map_yaml_observed",
            "map_pbstream_observed",
        ),
        "latest_map_metadata_observed": latest_proof_value(latest, "map_metadata_observed", "metadata_observed"),
        "latest_slam_toolbox_state": latest_proof_value(latest, "slam_toolbox_state", "slam_state"),
        **observed,
        "boundary": "software_guard_only_not_real_slam_map_or_nav2_consumption",
    }
    return summary


def map_lifecycle_runtime_readback_contract(latest: dict[str, Any] | None) -> dict[str, Any]:
    """把 map lifecycle runtime artifact 折成可消费读回合同，失败时继续 fail-closed。"""
    latest_status = latest_proof_value(latest, "status")
    latest_scan_once = latest_proof_value(latest, "scan_once_observed")
    latest_map_once = latest_proof_value(latest, "map_once_observed", "/map_once_observed")
    latest_map_file = latest_proof_value(latest, "map_file_observed", "map_yaml_observed", "map_pbstream_observed")
    latest_map_metadata = latest_proof_value(latest, "map_metadata_observed", "metadata_observed")
    proof = latest.get("proof") if isinstance(latest, dict) and isinstance(latest.get("proof"), dict) else {}
    algorithm_boundary = proof.get("algorithm_boundary") if isinstance(proof.get("algorithm_boundary"), dict) else {}
    slam_map_quality = proof.get("slam_map_quality") if isinstance(proof.get("slam_map_quality"), dict) else {}
    latest_map_usable_for_navigation = bool(algorithm_boundary.get("map_usable_for_navigation"))
    latest_map_quality_status = str(slam_map_quality.get("navigation_quality") or "not_loaded")
    cell_counts = slam_map_quality.get("cell_counts") if isinstance(slam_map_quality.get("cell_counts"), dict) else {}
    raw_free_cells = cell_counts.get("free")
    latest_map_free_cell_count = int(raw_free_cells) if isinstance(raw_free_cells, (int, float)) else 0
    required_observations = (
        latest_status == MAP_LIFECYCLE_OBSERVED_STATUS
        and latest_scan_once is True
        and latest_map_once is True
        and latest_map_file is True
        and latest_map_metadata is True
    )
    # 只有观测链条齐全时，PC 才能消费地图生命周期 proof；其它情况继续按 software guard 处理。
    contract_status = MAP_LIFECYCLE_OBSERVED_STATUS if required_observations else "not_proven"
    return {
        "status": contract_status,
        "proof_state": contract_status,
        "latest_proof_status": latest_status,
        "scan_once_observed": latest_scan_once is True,
        "map_once_observed": latest_map_once is True,
        "map_file_observed": latest_map_file is True,
        "map_metadata_observed": latest_map_metadata is True,
        "latest_map_usable_for_navigation": latest_map_usable_for_navigation,
        "latest_map_quality_status": latest_map_quality_status,
        "latest_map_free_cell_count": latest_map_free_cell_count,
        "ros2_runtime_proven": required_observations,
        "map_artifact_proven": required_observations,
        "not_proven": not required_observations,
        "software_guard": not required_observations,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "sends_motion_commands": False,
        "sends_base_motion_commands": False,
        "publishes_cmd_vel": False,
        "calls_base_manual": False,
        "uses_base_uart": False,
        "opens_serial": False,
        "starts_ros2": False,
        "cloud_relay": False,
    }


def summarize_localization_latest_artifact(path: str) -> dict[str, Any]:
    """压缩 AMCL/initialpose proof；只做 artifact 摘要，不发布 /initialpose。"""
    summary = runtime_artifact_summary(
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
    latest = read_latest_result_from_summary(summary)
    summary.update(localization_runtime_readback_contract(latest))
    return summary


def read_latest_result_from_summary(summary: dict[str, Any]) -> dict[str, Any] | None:
    """summary 里不放 raw latest；需要合同提升时只按 artifact path 再读一次 JSON。"""
    artifact = summary.get("artifact") if isinstance(summary.get("artifact"), dict) else {}
    path = artifact.get("path") if isinstance(artifact.get("path"), str) else None
    if not path:
        return None
    try:
        parsed = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def extract_base_link_to_laser_frame_transform(proof: dict[str, Any]) -> dict[str, Any] | None:
    """从 O10 proof 的多个兼容位置提升雷达外参，避免 timeout fallback 丢顶层合同。"""
    direct = proof.get("base_link_to_laser_frame_transform")
    if isinstance(direct, dict):
        return direct
    detail = proof.get("tf_source_root_cause_detail") if isinstance(proof.get("tf_source_root_cause_detail"), dict) else {}
    from_detail = detail.get("base_link_to_laser_frame_source_transform")
    if isinstance(from_detail, dict):
        return from_detail
    inventory = proof.get("tf_frame_inventory") if isinstance(proof.get("tf_frame_inventory"), dict) else {}
    candidates: list[Any] = []
    for key in ("static_transforms", "transforms"):
        values = inventory.get(key)
        if isinstance(values, list):
            candidates.extend(values)
    for transform in candidates:
        if not isinstance(transform, dict):
            continue
        if transform.get("parent_frame_id") == "base_link" and transform.get("child_frame_id") == "laser_frame":
            return transform
    return None


def localization_runtime_readback_contract(latest: dict[str, Any] | None) -> dict[str, Any]:
    """把 O10 helper artifact 折成定位 reset 可读合同，安全字段仍全部 fail-closed。"""
    proof = latest.get("proof") if isinstance(latest, dict) and isinstance(latest.get("proof"), dict) else {}
    tf_value = proof.get("localization_tf_observed") if isinstance(proof.get("localization_tf_observed"), dict) else {}
    tf_chain_value = proof.get("tf_chain_observed") if isinstance(proof.get("tf_chain_observed"), dict) else {}
    initialpose_published = proof.get("initialpose_published") is True
    amcl_pose_observed = proof.get("amcl_pose_observed") is True
    amcl_pose = proof.get("amcl_pose") if isinstance(proof.get("amcl_pose"), dict) else None
    base_link_to_laser_frame_transform = extract_base_link_to_laser_frame_transform(proof)
    odom_to_base_link = tf_chain_value.get("odom_to_base_link") is True
    base_link_to_laser_frame = tf_chain_value.get("base_link_to_laser_frame") is True
    map_to_odom = tf_value.get("map_to_odom") is True or tf_chain_value.get("map_to_odom") is True
    map_to_base_link = tf_value.get("map_to_base_link") is True or tf_chain_value.get("map_to_base_link") is True
    managed_runtime_started = proof.get("managed_runtime_started") is True
    root_causes = proof.get("root_causes") if isinstance(proof.get("root_causes"), list) else []
    helper_status = proof.get("status") if isinstance(proof.get("status"), str) else latest_proof_value(latest, "status")
    reset_observed = bool(initialpose_published and amcl_pose_observed and map_to_odom and map_to_base_link)
    status = "localization_reset_observed" if reset_observed else (helper_status or "not_proven")
    return {
        "status": status,
        "proof_state": status,
        "latest_proof_status": helper_status,
        "last_phase": proof.get("last_phase"),
        "last_successful_phase": proof.get("last_successful_phase"),
        "phase_history": proof.get("phase_history") if isinstance(proof.get("phase_history"), list) else [],
        "current_command": proof.get("current_command") if isinstance(proof.get("current_command"), dict) else None,
        "recent_commands": proof.get("recent_commands") if isinstance(proof.get("recent_commands"), list) else [],
        "partial_artifact_preserved": proof.get("partial_artifact_preserved") is True,
        "package_availability": proof.get("package_availability") if isinstance(proof.get("package_availability"), dict) else {},
        "package_check_mode": proof.get("package_check_mode"),
        "package_checks_batch_ok": proof.get("package_checks_batch_ok") is True,
        "initialpose_published": initialpose_published,
        "latest_initialpose_published": initialpose_published,
        "amcl_pose_observed": amcl_pose_observed,
        "latest_amcl_pose_observed": amcl_pose_observed,
        "amcl_pose": amcl_pose,
        "base_link_to_laser_frame_transform": base_link_to_laser_frame_transform,
        "localization_tf_observed": {"map_to_odom": map_to_odom, "map_to_base_link": map_to_base_link},
        "tf_chain_observed": {
            "map_to_odom": map_to_odom,
            "odom_to_base_link": odom_to_base_link,
            "base_link_to_laser_frame": base_link_to_laser_frame,
            "map_to_base_link": map_to_base_link,
        },
        "tf_chain_diagnostics": proof.get("tf_chain_diagnostics") if isinstance(proof.get("tf_chain_diagnostics"), dict) else {},
        "tf_topics_observed": (
            proof.get("tf_topics_observed")
            if isinstance(proof.get("tf_topics_observed"), dict)
            else {"/tf": False, "/tf_static": False}
        ),
        "tf_static_observed": proof.get("tf_static_observed") is True,
        "tf_frame_inventory": (
            proof.get("tf_frame_inventory")
            if isinstance(proof.get("tf_frame_inventory"), dict)
            else {"frames": [], "edges": [], "dynamic_edges": [], "static_edges": []}
        ),
        "amcl_pose_frame_id": proof.get("amcl_pose_frame_id"),
        "amcl_node_publishers": (
            proof.get("amcl_node_publishers")
            if isinstance(proof.get("amcl_node_publishers"), list)
            else []
        ),
        "amcl_node_subscribers": (
            proof.get("amcl_node_subscribers")
            if isinstance(proof.get("amcl_node_subscribers"), list)
            else []
        ),
        "amcl_param_probe_ok": proof.get("amcl_param_probe_ok") is True,
        "amcl_node_info_observed": proof.get("amcl_node_info_observed") is True,
        "amcl_tf_broadcast_param": proof.get("amcl_tf_broadcast_param"),
        "amcl_frame_params": proof.get("amcl_frame_params") if isinstance(proof.get("amcl_frame_params"), dict) else {},
        "amcl_log_tail": proof.get("amcl_log_tail") if isinstance(proof.get("amcl_log_tail"), str) else "",
        "managed_static_tf_processes": (
            proof.get("managed_static_tf_processes")
            if isinstance(proof.get("managed_static_tf_processes"), dict)
            else {}
        ),
        "static_tf_source_observed": proof.get("static_tf_source_observed") is True,
        "tf_source_root_cause_detail": (
            proof.get("tf_source_root_cause_detail")
            if isinstance(proof.get("tf_source_root_cause_detail"), dict)
            else {}
        ),
        "amcl_broadcast_conditions": (
            proof.get("amcl_broadcast_conditions")
            if isinstance(proof.get("amcl_broadcast_conditions"), dict)
            else {}
        ),
        "map_frame_observed": proof.get("map_frame_observed") is True,
        "odom_frame_observed": proof.get("odom_frame_observed") is True,
        "amcl_tf_root_cause": proof.get("amcl_tf_root_cause"),
        "tf_failure_classification": (
            proof.get("tf_failure_classification")
            if isinstance(proof.get("tf_failure_classification"), dict)
            else {"map_to_base_link": "not_evaluated", "frame_naming_consistent": True}
        ),
        "latest_localization_tf_observed": bool(map_to_odom and map_to_base_link),
        "managed_runtime_started": managed_runtime_started,
        "managed_runtime_requested": proof.get("managed_runtime_requested") is True,
        "managed_runtime_cleanup_ok": proof.get("managed_runtime_cleanup_ok") is True,
        "root_causes": root_causes,
        "blockers": proof.get("blockers") if isinstance(proof.get("blockers"), list) else root_causes,
        "localization_reset_observed": reset_observed,
        "path_generation_requested": proof.get("path_generation_requested") is True,
        "path_generation_attempted": proof.get("path_generation_attempted") is True,
        "path_generated": proof.get("path_generated") is True,
        "path_generation_service_name": proof.get("path_generation_service_name"),
        "path_generation_service_available": proof.get("path_generation_service_available") is True,
        "path_generation_succeeded": proof.get("path_generation_succeeded") is True,
        "path_point_count": int(proof.get("path_point_count") or 0),
        "blocked_commands_not_sent": proof.get("blocked_commands_not_sent") if isinstance(proof.get("blocked_commands_not_sent"), list) else [
            "T=1",
            "T=13",
            "T=130",
            "T=131",
            "/cmd_vel",
            "/api/base/manual",
            "/api/nav2/start",
            "/api/nav2/stop",
            "navigate_to_pose",
        ],
        "blocked_devices_not_opened": proof.get("blocked_devices_not_opened") if isinstance(proof.get("blocked_devices_not_opened"), list) else ["/dev/ttyS5"],
        "readback_sends_commands": False,
        "sends_commands": False,
        "sends_motion_commands": False,
        "sends_base_motion_commands": False,
        "publishes_cmd_vel": False,
        "calls_base_manual": False,
        "opens_serial": False,
        "opens_base_uart": False,
        "uses_base_uart": False,
        "starts_ros2": False,
        "starts_nav2": False,
        "robot_control_executed": False,
        "hil_pass": False,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "cloud_relay": False,
    }


def summarize_nav2_lifecycle_latest_artifact(path: str) -> dict[str, Any]:
    """压缩 Nav2 lifecycle proof；Nav2 消费 /scan+map 仍由 runtime artifact 证明。"""
    summary = runtime_artifact_summary(
        path,
        artifact_info=nav2_lifecycle_artifact_info(path),
        schema_suffix="nav2_lifecycle_proof_latest",
        endpoint=ROUTE_PATHS["nav2_proof_latest"],
        boundary="software_guard_only_not_real_nav2_runtime_or_path_execution",
        source="nav2_lifecycle_runtime_artifact",
        fields={
            "latest_map_server_active": ("map_server_active", "map_server_lifecycle_active"),
            "latest_amcl_active": ("amcl_active", "amcl_lifecycle_active"),
            "latest_planner_active": ("planner_active", "planner_server_active"),
            "latest_controller_active": ("controller_active", "controller_server_active"),
            "latest_scan_consumed": ("scan_consumed", "laser_scan_consumed"),
            "latest_map_consumed": ("map_consumed", "map_server_map_consumed"),
            "latest_amcl_pose_observed": ("amcl_pose_observed", "/amcl_pose_observed"),
            "latest_path_generation_ready": ("path_generation_ready", "global_path_generation_ready"),
            "latest_path_generated": ("path_generated", "global_path_generated"),
            "latest_path_generation_requested": ("path_generation_requested", "global_path_generation_requested"),
            "latest_path_generation_attempted": ("path_generation_attempted", "global_path_generation_attempted"),
            "latest_path_generation_service_name": ("path_generation_service_name", "global_path_generation_service_name"),
            "latest_path_generation_service_available": ("path_generation_service_available", "global_path_generation_service_available"),
            "latest_path_generation_succeeded": ("path_generation_succeeded", "global_path_generation_succeeded"),
            "latest_path_point_count": ("path_point_count", "global_path_point_count"),
        },
    )
    latest = read_latest_result_from_summary(summary)
    readback = localization_runtime_readback_contract(latest)
    # Nav2 summary 保持自己的 status，只把 PC 叠图/定位诊断需要的只读字段提升到顶层。
    for key in (
        "base_link_to_laser_frame_transform",
        "tf_chain_observed",
        "tf_chain_diagnostics",
        "tf_topics_observed",
        "tf_static_observed",
        "tf_frame_inventory",
        "localization_tf_observed",
        "amcl_pose",
        "amcl_pose_observed",
        "last_phase",
        "last_successful_phase",
        "partial_artifact_preserved",
        "path_generation_requested",
        "path_generation_attempted",
        "path_generated",
        "path_generation_service_name",
        "path_generation_service_available",
        "path_generation_succeeded",
        "path_point_count",
        "blocked_commands_not_sent",
        "blocked_devices_not_opened",
        "readback_sends_commands",
        "sends_commands",
        "sends_motion_commands",
        "sends_base_motion_commands",
        "publishes_cmd_vel",
        "calls_base_manual",
        "uses_base_uart",
    ):
        summary[key] = readback.get(key)
    proof = latest.get("proof") if isinstance(latest, dict) and isinstance(latest.get("proof"), dict) else {}
    for key in (
        "planner_server_active",
        "controller_server_active",
        "controller_server_requested",
        "planner_readiness_summary",
        "path_goal_request",
        "path_goal_response",
        "path_generation_boundary",
    ):
        if key in proof:
            summary[key] = proof.get(key)
    summary.update(nav2_path_preview_overlay_from_latest(latest))
    return summary


def finite_nav2_path_coordinate(value: Any) -> float | None:
    """路线点来自 runtime artifact；只接受有限数字，避免坏 JSON 污染地图。"""
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed):
        return None
    return min(max(parsed, -1000.0), 1000.0)


def nav2_path_preview_overlay_from_latest(latest: dict[str, Any] | None) -> dict[str, Any]:
    """把 Nav2 proof 的路径点折成地图 overlay；没有点数组时不能冒充已贴图。"""
    proof = latest.get("proof") if isinstance(latest, dict) and isinstance(latest.get("proof"), dict) else {}
    raw_points = proof.get("path_preview_points") if isinstance(proof.get("path_preview_points"), list) else []
    path_goal_response = proof.get("path_goal_response") if isinstance(proof.get("path_goal_response"), dict) else {}
    frame_id = str(proof.get("path_preview_frame_id") or path_goal_response.get("path_frame_id") or "map")[:40]
    points: list[dict[str, Any]] = []
    for fallback_index, raw_point in enumerate(raw_points[:NAV2_PATH_PREVIEW_POINT_LIMIT]):
        if not isinstance(raw_point, dict):
            continue
        x = finite_nav2_path_coordinate(raw_point.get("x"))
        y = finite_nav2_path_coordinate(raw_point.get("y"))
        if x is None or y is None:
            continue
        source_index_raw = finite_nav2_path_coordinate(raw_point.get("source_index"))
        # source_index 只用于前端稳定 key；缺失时用过滤后的原始顺序兜底。
        source_index = int(source_index_raw) if source_index_raw is not None else fallback_index
        point_frame_id = str(raw_point.get("frame_id") or frame_id or "map")[:40]
        points.append({"x": x, "y": y, "frame_id": point_frame_id, "source_index": source_index})
    source_count_raw = finite_nav2_path_coordinate(proof.get("path_preview_source_point_count"))
    source_count = int(source_count_raw) if source_count_raw is not None else len(raw_points)
    point_count_raw = finite_nav2_path_coordinate(proof.get("path_preview_point_count") or proof.get("path_point_count"))
    reported_point_count = int(point_count_raw) if point_count_raw is not None else len(raw_points)
    if points:
        status = "path_preview_observed"
        next_action = "图上路线已贴到地图；勾选现场安全确认后可执行，并复验 wheel raw L/R。"
        status_plain = f"图上路线已显示，当前地图路径点 {len(points)} 个。"
    elif reported_point_count > 0:
        status = "metadata_only"
        next_action = "Nav2 已生成路线点数但缺少可绘制点数组；刷新 Nav2 路径 proof 后再刷新地图画面。"
        status_plain = f"图上路线只有点数 {reported_point_count}，没有点数组，当前不贴图。"
    else:
        status = "not_observed"
        next_action = "先刷新 Nav2 路径 proof，再刷新地图画面。"
        status_plain = "图上路线未显示；不能把旧路线或空路线当作当前所见。"
    return {
        "path_preview_points": points,
        "path_preview_status": status,
        "path_preview_point_count": len(points),
        "path_preview_source_point_count": source_count if source_count > 0 else None,
        "path_preview_reported_point_count": reported_point_count,
        "path_preview_frame_id": points[0]["frame_id"] if points else (frame_id or "not_loaded"),
        "path_preview_next_action_plain": next_action,
        "path_wysiwyg_status_plain": status_plain,
        "path_wysiwyg_next_action_plain": next_action,
        "nav2_route_overlay_status": status,
        "nav2_route_overlay_point_count": len(points),
        "nav2_route_overlay_next_action_plain": next_action,
    }


def nav2_path_preview_overlay_from_artifact(path: str) -> dict[str, Any]:
    """地图预览只需要路径 overlay 字段；不能把 Nav2 summary 的 status 覆盖地图 status。"""
    try:
        latest = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        latest = None
    return nav2_path_preview_overlay_from_latest(latest if isinstance(latest, dict) else None)


def route_target_overlay_from_path_preview(path_overlay: dict[str, Any]) -> dict[str, Any]:
    """优先把已生成的 path 终点作为地图目标；这比最近 goal_request 更贴近当前图上路线。"""
    points = path_overlay.get("path_preview_points") if isinstance(path_overlay.get("path_preview_points"), list) else []
    map_points = [point for point in points if isinstance(point, dict) and str(point.get("frame_id") or "map") == "map"]
    if len(map_points) < 2:
        return {}
    last_point = map_points[-1]
    x = finite_nav2_path_coordinate(last_point.get("x"))
    y = finite_nav2_path_coordinate(last_point.get("y"))
    if x is None or y is None:
        return {}
    source_index = finite_nav2_path_coordinate(last_point.get("source_index"))
    return {
        "target": {
            "x": x,
            "y": y,
            "frame_id": "map",
            "source": "path_preview_points",
            "source_index": int(source_index) if source_index is not None else None,
        },
        "route_target_state": "path_preview_goal_observed",
        "route_target_visible": True,
        "route_target_source": "path_preview_points",
    }


def nav2_goal_target_overlay_from_latest(latest: dict[str, Any] | None) -> dict[str, Any]:
    """没有可画 path 时，仍把最近 NavigateToPose 目标点返回给 PC 大地图。"""
    if not isinstance(latest, dict):
        return {}
    latest_result = latest.get("latest_result") if isinstance(latest.get("latest_result"), dict) else latest
    goal_request = latest_result.get("goal_request") if isinstance(latest_result.get("goal_request"), dict) else {}
    frame_id = str(goal_request.get("frame_id") or goal_request.get("goal_frame_id") or "map")[:40]
    if frame_id != "map":
        return {}
    x = finite_nav2_path_coordinate(goal_request.get("x", goal_request.get("goal_x")))
    y = finite_nav2_path_coordinate(goal_request.get("y", goal_request.get("goal_y")))
    if x is None or y is None:
        return {}
    return {
        "target": {
            "x": x,
            "y": y,
            "frame_id": "map",
            "source": "latest_goal_request",
            "source_index": None,
        },
        "route_target_state": "latest_goal_request_observed",
        "route_target_visible": True,
        "route_target_source": "latest_goal_request",
    }


def nav2_goal_target_overlay_from_artifact(path: str) -> dict[str, Any]:
    """地图预览读取最近一次目标执行 artifact，只用于显示目标点，不触发 Nav2。"""
    try:
        latest = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        latest = None
    return nav2_goal_target_overlay_from_latest(latest if isinstance(latest, dict) else None)


def build_amcl_nav2_readiness_from_map_proof(map_proof_path: str, map_artifact_dir: str) -> dict[str, Any]:
    """把 canonical map proof 折成 Nav2 输入状态；这里只读文件，不探 ROS graph。"""
    http_status, readback = read_runtime_artifact_latest(
        map_proof_path,
        artifact_info=map_lifecycle_proof_artifact_info(map_proof_path),
        schema_suffix="amcl_nav2_map_input_latest",
        endpoint=ROUTE_PATHS["nav2_status"],
        boundary="software_guard_only_map_input_not_amcl_or_nav2_runtime",
        source="map_lifecycle_runtime_artifact",
    )
    latest = readback.get("latest_result") if isinstance(readback.get("latest_result"), dict) else None
    proof = latest.get("proof") if isinstance(latest, dict) and isinstance(latest.get("proof"), dict) else {}
    expected_map_dir = resolve_onboard_runtime_path(map_artifact_dir)
    observed_map_dir = proof.get("map_artifact_dir") if isinstance(proof.get("map_artifact_dir"), str) else None
    map_files = proof.get("map_files") if isinstance(proof.get("map_files"), list) else []
    yaml_files = _successful_map_files(map_files, ".yaml")
    pgm_files = _successful_map_files(map_files, ".pgm")
    root_causes = _amcl_nav2_readiness_root_causes(
        http_status=http_status,
        proof=proof,
        observed_map_dir=observed_map_dir,
        expected_map_dir=expected_map_dir,
        yaml_files=yaml_files,
        pgm_files=pgm_files,
    )
    inputs_ready = not root_causes
    # 这里即使输入齐了也只解锁下一步 collector，不把地图质量或 Nav2 runtime 写成已证明。
    status = "map_inputs_ready_for_no_motion_nav2_collector" if inputs_ready else "blocked_with_root_cause"
    return {
        "schema": f"{SCHEMA}.amcl_nav2_readiness_from_map_proof.v1",
        "generated_at_ms": now_ms(),
        "status": status,
        "evidence_type": "software_guard",
        "source_evidence_type": latest.get("evidence_type") if isinstance(latest, dict) else None,
        "source_evidence_ref": proof.get("evidence_ref"),
        "source_http_status": http_status,
        "source_latest_status": latest_proof_value(latest, "status"),
        "map_proof_artifact": readback["artifact"],
        "expected_map_artifact_dir": expected_map_dir,
        "observed_map_artifact_dir": observed_map_dir,
        "map_yaml_candidates": yaml_files,
        "map_image_candidates": pgm_files,
        "map_metadata": proof.get("map_metadata") if isinstance(proof.get("map_metadata"), dict) else {},
        "readiness_inputs": {
            "canonical_latest_loaded": http_status == 200,
            "map_once_observed": proof.get("map_once_observed") is True,
            "map_file_observed": proof.get("map_file_observed") is True,
            "map_metadata_observed": proof.get("map_metadata_observed") is True,
            "canonical_map_dir_matched": observed_map_dir == expected_map_dir,
            "map_yaml_available": bool(yaml_files),
            "map_image_available": bool(pgm_files),
        },
        "root_causes": root_causes,
        "blockers": root_causes,
        "next_no_motion_steps": [
            "run map quality gate against selected YAML and same-frame waypoints",
            "collect AMCL /initialpose and /amcl_pose material under a new artifact",
            "collect map_server/amcl/planner/controller lifecycle readback without /cmd_vel",
        ],
        "not_proven": [
            "map_quality_pass",
            "real_amcl_localization",
            "real_nav2_scan_map_consumption",
            "path_generated",
            "fixed_route_execution",
            "delivery_success",
        ],
        "software_guard": True,
        "readback_sends_commands": False,
        "sends_commands": False,
        "sends_motion_commands": False,
        "sends_base_motion_commands": False,
        "publishes_cmd_vel": False,
        "calls_base_manual": False,
        "uses_base_uart": False,
        "starts_ros2": False,
        "robot_control_executed": False,
        "safe_to_control": False,
        "hil_pass": False,
        **proof_flags(),
    }


def _successful_map_files(map_files: list[Any], suffix: str) -> list[dict[str, Any]]:
    """只接受 proof 中已经 stat 成功的文件，避免把错误项当成 Nav2 输入。"""
    result: list[dict[str, Any]] = []
    for item in map_files:
        if not isinstance(item, dict):
            continue
        if item.get("ok") is False:
            continue
        path = str(item.get("path") or "")
        item_suffix = str(item.get("suffix") or Path(path).suffix)
        if item_suffix == suffix:
            result.append(dict(item))
    return result


def _amcl_nav2_readiness_root_causes(
    *,
    http_status: int,
    proof: dict[str, Any],
    observed_map_dir: str | None,
    expected_map_dir: str,
    yaml_files: list[dict[str, Any]],
    pgm_files: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """root cause 必须落到输入层，方便下一轮选择 map、waypoint 或 runtime collector。"""
    causes: list[dict[str, str]] = []
    if http_status != 200:
        causes.append({"layer": "map proof latest", "reason": f"canonical_latest_http_status_{http_status}"})
        return causes
    if proof.get("status") != "map_once_artifact_metadata_observed":
        causes.append({"layer": "map proof latest", "reason": "map_lifecycle_proof_not_clean"})
    if proof.get("map_once_observed") is not True:
        causes.append({"layer": "map proof latest", "reason": "map_once_not_observed"})
    if proof.get("map_file_observed") is not True:
        causes.append({"layer": "map artifact", "reason": "map_file_not_observed"})
    if proof.get("map_metadata_observed") is not True:
        causes.append({"layer": "map metadata", "reason": "map_metadata_not_observed"})
    if observed_map_dir != expected_map_dir:
        causes.append({"layer": "map artifact contract", "reason": "canonical_map_artifact_dir_mismatch"})
    if not yaml_files:
        causes.append({"layer": "map artifact", "reason": "map_yaml_missing"})
    if not pgm_files:
        causes.append({"layer": "map artifact", "reason": "map_image_pgm_missing"})
    return causes


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
        "evidence_ref": None,
        "latest_evidence_ref": None,
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
    evidence_ref = derive_lidar_scan_proof_evidence_ref(parsed)
    payload["evidence_ref"] = evidence_ref
    payload["latest_evidence_ref"] = evidence_ref
    payload["latest_result"] = parsed
    scan_preview = structured_lidar_scan_preview_from_artifact(parsed) or lidar_scan_preview_from_artifact(parsed)
    if scan_preview:
        # 点位来自 artifact 内已记录的结构化 `/scan` 材料，不会在 latest readback 阶段触发硬件。
        payload.update(scan_preview)
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
    scan_preview = {
        "scan_preview_points": payload.get("scan_preview_points", []),
        "scan_preview_point_count": payload.get("scan_preview_point_count", 0),
        "scan_preview_source_point_count": payload.get("scan_preview_source_point_count"),
        "scan_preview_frame_id": payload.get("scan_preview_frame_id", ""),
        "scan_preview_source": payload.get("scan_preview_source"),
    }
    required_observations = proof.get("required_observations") if isinstance(proof, dict) else None
    generated_at_ms = now_ms()
    stale_after_ms = DEFAULT_FEEDBACK_SAMPLES_STALE_AFTER_MS
    artifact = payload["artifact"]
    freshness: dict[str, Any] = {
        "status": "unknown",
        "age_seconds": None,
        "stale_after_ms": stale_after_ms,
        "basis": "artifact_mtime_only_material_freshness_not_hil_or_safe_to_control",
    }
    artifact_path = artifact.get("path")
    if isinstance(artifact_path, str):
        try:
            stat_result = Path(artifact_path).stat()
        except FileNotFoundError:
            freshness["status"] = "missing"
        except OSError:
            freshness["status"] = "read_failed"
        else:
            mtime_ms = int(stat_result.st_mtime_ns / 1_000_000)
            age_ms = max(0, generated_at_ms - mtime_ms)
            artifact["mtime_ms"] = mtime_ms
            artifact["age_ms"] = age_ms
            freshness["age_seconds"] = round(age_ms / 1000.0, 3)
            freshness["status"] = freshness_from_age(age_ms, stale_after_ms)
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
        "evidence_ref": payload.get("latest_evidence_ref"),
        "latest_evidence_ref": payload.get("latest_evidence_ref"),
        "latest_proof_status": proof.get("status") if isinstance(proof, dict) else None,
        "latest_scan_once_observed": proof.get("scan_once_observed") if isinstance(proof, dict) else None,
        "latest_scan_hz_observed": proof.get("scan_hz_observed") if isinstance(proof, dict) else None,
        "latest_scan_hz_average_rate_hz": proof.get("scan_hz_average_rate_hz") if isinstance(proof, dict) else None,
        "latest_raw_packet_once_observed": proof.get("raw_packet_once_observed") if isinstance(proof, dict) else None,
        "latest_tf_observed": proof.get("tf_observed") if isinstance(proof, dict) else None,
        "latest_all_required_observations_observed": proof.get("all_required_observations_observed") if isinstance(proof, dict) else None,
        "latest_required_observations": compact_required_observations,
        "latest_runtime_summary_fallback_used": proof.get("runtime_summary_fallback_used") if isinstance(proof, dict) else None,
        "latest_runtime_summary_path": proof.get("runtime_summary_path") if isinstance(proof, dict) else None,
        **scan_preview,
        "freshness": freshness,
        "readback_sends_commands": False,
        "sends_commands": False,
        "sends_motion_commands": False,
        "robot_control_executed": False,
        "delivery_success": False,
        "hil_pass": False,
        "safe_to_control": False,
        "primary_actions_enabled": False,
    }


def build_radar_latest_scan_proof_status(scan_proof_latest: dict[str, Any]) -> dict[str, Any]:
    """把 latest artifact 摘要提升成 status 顶层字段，但不在这里重新探 ROS2。"""
    artifact = scan_proof_latest.get("artifact") if isinstance(scan_proof_latest.get("artifact"), dict) else {}
    artifact_status = str(artifact.get("status") or "unknown")
    state = str(scan_proof_latest.get("latest_proof_status") or artifact_status)
    freshness = scan_proof_latest.get("freshness") if isinstance(scan_proof_latest.get("freshness"), dict) else {}
    freshness_status = str(freshness.get("status") or "unknown")
    # fresh proof 必须四项机器字段全为 True；这里保留缺项名，方便 PC/协调者直接定位。
    required_fields = {
        "latest_scan_once_observed": "scan_once",
        "latest_scan_hz_observed": "scan_hz",
        "latest_raw_packet_once_observed": "raw_packet_once",
        "latest_tf_observed": "tf",
        "latest_all_required_observations_observed": "all_required_observations",
    }
    missing_required_observations = [
        name for field, name in required_fields.items() if scan_proof_latest.get(field) is not True
    ]
    observed = not missing_required_observations
    failure_reason: str | None = None
    if not observed:
        if artifact_status == "missing":
            failure_reason = "latest_scan_proof_missing"
        elif artifact_status in {"bad_json", "json_not_object", "read_failed"}:
            failure_reason = f"latest_scan_proof_{artifact_status}"
        elif artifact_status == "loaded":
            failure_reason = "latest_scan_proof_required_observations_missing:" + ",".join(missing_required_observations)
        else:
            failure_reason = f"latest_scan_proof_unavailable:{artifact_status}"
    return {
        "endpoint": scan_proof_latest.get("endpoint"),
        "artifact": artifact,
        "state": state,
        "observed": observed,
        "freshness": freshness,
        "freshness_status": freshness_status,
        "fresh_while_observed": observed and freshness_status == "fresh",
        "evidence_ref": scan_proof_latest.get("latest_evidence_ref"),
        "latest_evidence_ref": scan_proof_latest.get("latest_evidence_ref"),
        "failure_reason": failure_reason,
        "scan_once_observed": scan_proof_latest.get("latest_scan_once_observed"),
        "scan_hz_observed": scan_proof_latest.get("latest_scan_hz_observed"),
        "scan_hz_average_rate_hz": scan_proof_latest.get("latest_scan_hz_average_rate_hz"),
        "raw_packet_once_observed": scan_proof_latest.get("latest_raw_packet_once_observed"),
        "tf_observed": scan_proof_latest.get("latest_tf_observed"),
        "all_required_observations_observed": scan_proof_latest.get("latest_all_required_observations_observed"),
        "missing_required_observations": missing_required_observations,
        "required_observations": scan_proof_latest.get("latest_required_observations"),
        "runtime_summary_fallback_used": bool(scan_proof_latest.get("latest_runtime_summary_fallback_used")),
        "runtime_summary_path": scan_proof_latest.get("latest_runtime_summary_path"),
        "readback_sends_commands": False,
        "sends_commands": False,
        "sends_motion_commands": False,
        "sends_base_motion_commands": False,
        "calls_base_manual": False,
        "publishes_cmd_vel": False,
        "robot_control_executed": False,
        "delivery_success": False,
        "hil_pass": False,
        "safe_to_control": False,
        "primary_actions_enabled": False,
    }


def default_radar_lifecycle_status_commands() -> list[dict[str, str]]:
    """优先走真实部署脚本，缺失时再退回同目录脚本，避免只因路径漂移丢掉状态读回。"""
    local_script = Path(__file__).resolve().with_name(SAFE_RADAR_LIFECYCLE_SCRIPT)
    return [
        {
            "source": "managed_runtime_absolute",
            "command": f"bash {DEFAULT_ONBOARD_WORKDIR}/scripts/{SAFE_RADAR_LIFECYCLE_SCRIPT} status",
        },
        {
            "source": "local_script_fallback",
            "command": f"bash {local_script} status",
        },
    ]


def read_radar_lifecycle_status(timeout_s: float = DEFAULT_RADAR_LIFECYCLE_STATUS_TIMEOUT_S) -> dict[str, Any]:
    """只读 lifecycle status 脚本；失败时继续 fail-closed，不影响 radar status 主响应。"""
    attempts: list[dict[str, Any]] = []
    for candidate in default_radar_lifecycle_status_commands():
        command = candidate["command"]
        source = candidate["source"]
        argv, error = validate_radar_lifecycle_command(command, "status")
        if error:
            attempts.append({"source": source, "command": command, "status": "invalid_command", "error": error})
            continue
        try:
            completed = subprocess.run(
                argv,
                check=False,
                capture_output=True,
                text=True,
                timeout=max(0.5, float(timeout_s)),
            )
        except subprocess.TimeoutExpired as exc:
            attempts.append(
                {
                    "source": source,
                    "command": command,
                    "argv": argv,
                    "status": "timeout",
                    "error": {"type": "TimeoutExpired", "message": str(exc)},
                    "stdout_preview": preview_text(exc.stdout),
                    "stderr_preview": preview_text(exc.stderr),
                }
            )
            continue
        except FileNotFoundError as exc:
            attempts.append(
                {
                    "source": source,
                    "command": command,
                    "argv": argv,
                    "status": "script_missing",
                    "error": compact_error(exc),
                }
            )
            continue
        except OSError as exc:
            attempts.append(
                {
                    "source": source,
                    "command": command,
                    "argv": argv,
                    "status": "exec_failed",
                    "error": compact_error(exc),
                }
            )
            continue
        stdout_text = completed.stdout or ""
        stderr_text = completed.stderr or ""
        if completed.returncode != 0:
            attempts.append(
                {
                    "source": source,
                    "command": command,
                    "argv": argv,
                    "status": "command_failed",
                    "returncode": completed.returncode,
                    "stdout_preview": preview_text(stdout_text),
                    "stderr_preview": preview_text(stderr_text),
                }
            )
            continue
        try:
            parsed = json.loads(stdout_text)
        except json.JSONDecodeError as exc:
            attempts.append(
                {
                    "source": source,
                    "command": command,
                    "argv": argv,
                    "status": "bad_json",
                    "returncode": completed.returncode,
                    "stdout_preview": preview_text(stdout_text),
                    "stderr_preview": preview_text(stderr_text),
                    "error": compact_error(exc),
                }
            )
            continue
        if not isinstance(parsed, dict):
            attempts.append(
                {
                    "source": source,
                    "command": command,
                    "argv": argv,
                    "status": "json_not_object",
                    "returncode": completed.returncode,
                    "stdout_preview": preview_text(stdout_text),
                    "stderr_preview": preview_text(stderr_text),
                }
            )
            continue
        return {
            "status": "loaded",
            "source": source,
            "command": command,
            "argv": argv,
            "running": bool(parsed.get("running")),
            "state": parsed.get("state"),
            "pid": parsed.get("pid") if isinstance(parsed.get("pid"), int) else None,
            "message": parsed.get("message"),
            "latest_result": parsed,
            "attempts": attempts,
            "readback_sends_commands": False,
            "sends_commands": False,
            "sends_motion_commands": False,
            "uses_base_uart": False,
            "robot_control_executed": False,
            **proof_flags(),
        }
    return {
        "status": "read_failed",
        "source": attempts[-1].get("source") if attempts else None,
        "command": attempts[-1].get("command") if attempts else None,
        "argv": attempts[-1].get("argv") if attempts else None,
        "running": False,
        "state": "unknown",
        "pid": None,
        "message": "radar lifecycle status read failed",
        "latest_result": None,
        "attempts": attempts,
        "failure_reason": str(attempts[-1].get("status") or "lifecycle_status_read_failed") if attempts else "lifecycle_status_read_failed",
        "readback_sends_commands": False,
        "sends_commands": False,
        "sends_motion_commands": False,
        "uses_base_uart": False,
        "robot_control_executed": False,
        **proof_flags(),
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
        "wheel_feedback_summary": {},
        "wheel_feedback_nonzero_observed": False,
        "wheel_feedback_lr_nonzero_proven": False,
        "imu_attitude_delta_summary": {},
        "imu_attitude_delta_observed": False,
        "motion_signal_observed": False,
        "motion_signal_source": "not_observed",
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
    wheel_summary = parsed.get("wheel_feedback_summary") if isinstance(parsed.get("wheel_feedback_summary"), dict) else {}
    imu_summary = parsed.get("imu_attitude_delta_summary") if isinstance(parsed.get("imu_attitude_delta_summary"), dict) else {}
    wheel_nonzero = bool(wheel_summary.get("lr_nonzero_observed") or parsed.get("wheel_feedback_lr_nonzero_proven") is True)
    imu_delta = bool(imu_summary.get("imu_attitude_delta_observed") or parsed.get("imu_attitude_delta_observed") is True)
    base_summary["wheel_feedback_summary"] = wheel_summary
    base_summary["wheel_feedback_nonzero_observed"] = wheel_nonzero
    base_summary["wheel_feedback_lr_nonzero_proven"] = wheel_nonzero
    base_summary["imu_attitude_delta_summary"] = imu_summary
    base_summary["imu_attitude_delta_observed"] = imu_delta
    base_summary["motion_signal_observed"] = bool(wheel_nonzero or imu_delta or parsed.get("motion_signal_observed") is True)
    base_summary["motion_signal_source"] = parsed.get("motion_signal_source") or (
        "wheel_feedback_lr" if wheel_nonzero else "imu_attitude_delta" if imu_delta else "not_observed"
    )
    return base_summary


def read_recent_text_lines(path: str, *, max_lines: int, max_bytes: int = 256 * 1024) -> tuple[list[str], int]:
    """从大日志尾部读最近行，避免 PC 状态刷新把几百 MB JSONL 全量读入内存。"""
    max_lines = max(1, int(max_lines))
    max_bytes = max(1024, int(max_bytes))
    with Path(path).open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        file_size = handle.tell()
        remaining = min(file_size, max_bytes)
        chunks: list[bytes] = []
        bytes_read = 0
        while remaining > 0:
            chunk_size = min(64 * 1024, remaining)
            handle.seek(file_size - bytes_read - chunk_size)
            chunk = handle.read(chunk_size)
            chunks.append(chunk)
            bytes_read += len(chunk)
            remaining -= chunk_size
            if b"\n".join(reversed(chunks)).count(b"\n") >= max_lines + 1:
                break
    raw_tail = b"".join(reversed(chunks))
    text_tail = raw_tail.decode("utf-8", errors="ignore")
    return text_tail.splitlines()[-max_lines:], bytes_read


def summarize_bridge_feedback_debug_log(
    path: str,
    stale_after_ms: int = DEFAULT_BRIDGE_FEEDBACK_DEBUG_STALE_AFTER_MS,
    max_lines: int = 80,
) -> dict[str, Any]:
    """读取 esp32_bridge 已解析 T1001 JSONL，避免上位机 API 抢占底盘 UART。"""
    generated_at_ms = now_ms()
    artifact = {
        **artifact_path_info(path),
        "ok": False,
        "status": "unknown",
    }
    summary: dict[str, Any] = {
        "schema": f"{SCHEMA}.bridge_feedback_debug_summary",
        "generated_at_ms": generated_at_ms,
        "source": "esp32_bridge_feedback_debug_log",
        "artifact": artifact,
        "freshness": {
            "status": "unknown",
            "stale_after_ms": stale_after_ms,
            "basis": "artifact_mtime_only_bridge_feedback_not_hil_or_safe_to_control",
        },
        "t1001_observed_count": 0,
        "wheel_feedback_summary": {},
        "wheel_feedback_nonzero_observed": False,
        "wheel_feedback_lr_nonzero_proven": False,
        "imu_attitude_delta_summary": {},
        "imu_attitude_delta_observed": False,
        "motion_signal_observed": False,
        "motion_signal_source": "not_observed",
        "latest_frame": None,
        "t1001_feedback_frames": [],
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
        summary["freshness"]["status"] = "missing"
        return summary
    except OSError as exc:
        artifact.update({"ok": False, "status": "read_failed", "error": compact_error(exc)})
        summary["freshness"]["status"] = "read_failed"
        return summary

    mtime_ms = int(stat_result.st_mtime_ns / 1_000_000)
    age_ms = max(0, generated_at_ms - mtime_ms)
    artifact.update({"mtime_ms": mtime_ms, "age_ms": age_ms})
    try:
        lines, bytes_scanned = read_recent_text_lines(path, max_lines=max_lines)
    except OSError as exc:
        artifact.update({"ok": False, "status": "read_failed", "error": compact_error(exc)})
        summary["freshness"]["status"] = "read_failed"
        return summary

    frames: list[dict[str, Any]] = []
    bad_line_count = 0
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            bad_line_count += 1
            continue
        if not isinstance(record, dict) or record.get("source") != "wave_rover_uart_t1001":
            continue
        vendor_frame = record.get("vendor_frame") if isinstance(record.get("vendor_frame"), dict) else {}
        frame = {
            "T": BASE_FEEDBACK_ID,
            "L": vendor_frame.get("L", record.get("left_speed")),
            "R": vendor_frame.get("R", record.get("right_speed")),
            "r": vendor_frame.get("r", record.get("roll")),
            "p": vendor_frame.get("p", record.get("pitch")),
            "y": vendor_frame.get("y", record.get("yaw") if record.get("yaw_available") is not False else "null"),
            "v": vendor_frame.get("v", record.get("voltage")),
        }
        if compact_t1001_feedback_frame(frame) is not None:
            frames.append(frame)

    artifact.update({"ok": True, "status": "loaded", "bytes_read": stat_result.st_size, "bytes_scanned": bytes_scanned, "tail_line_count": len(lines)})
    summary["freshness"]["status"] = freshness_from_age(age_ms, stale_after_ms)
    wheel_summary = wheel_feedback_summary_from_frames(frames)
    imu_summary = imu_attitude_delta_summary_from_frames(frames)
    wheel_nonzero = bool(wheel_summary["lr_nonzero_observed"])
    imu_delta = bool(imu_summary["imu_attitude_delta_observed"])
    summary.update(
        {
            "bad_line_count": bad_line_count,
            "t1001_observed_count": len(frames),
            "latest_frame": frames[-1] if frames else None,
            "t1001_feedback_frames": frames,
            "wheel_feedback_summary": wheel_summary,
            "wheel_feedback_nonzero_observed": wheel_nonzero,
            "wheel_feedback_lr_nonzero_proven": wheel_nonzero,
            "imu_attitude_delta_summary": imu_summary,
            "imu_attitude_delta_observed": imu_delta,
            "motion_signal_observed": bool(wheel_nonzero or imu_delta),
            "motion_signal_source": "wheel_feedback_lr" if wheel_nonzero else "imu_attitude_delta" if imu_delta else "not_observed",
        }
    )
    return summary


def vendor_motion_command_nonzero(command: dict[str, Any]) -> bool:
    """判断 vendor 底盘命令是否为非零运动命令；只用于命令链路诊断，不代表车已移动。"""
    try:
        command_id = int(command.get("T"))
    except (TypeError, ValueError):
        return False
    if command_id in (1, 11):
        return any(abs(float(command.get(key, 0))) > 1e-9 for key in ("L", "R"))
    if command_id == 13:
        return any(abs(float(command.get(key, 0))) > 1e-9 for key in ("X", "Z"))
    return False


def command_mode_for_vendor_command(command: dict[str, Any]) -> str:
    """把 vendor T 指令归类为控制模式，方便 PC 手控和 ROS bridge 共用命令证据。"""
    try:
        command_id = int(command.get("T"))
    except (TypeError, ValueError):
        return "unknown"
    if command_id == 11:
        return "pwm"
    if command_id == 13:
        return "ros"
    if command_id == 1:
        return "speed"
    return "vendor"


def append_upper_manual_command_debug_line(
    command: dict[str, Any],
    write_result: dict[str, Any],
    *,
    transaction_mode: str,
    log_path: str = DEFAULT_BRIDGE_COMMAND_DEBUG_LOG_PATH,
) -> None:
    """记录 PC/上位机手控直接写出的 vendor 命令；失败不能阻断停车兜底。"""
    if not log_path:
        return
    sent = bool(write_result.get("ok"))
    record = {
        "schema": "trashbot.wave_rover.command_debug.v1",
        "observed_at_unix_s": time.time(),
        "source": "upper_robot_api_manual_control",
        "manual_transaction_mode": transaction_mode,
        "command_mode": command_mode_for_vendor_command(command),
        "command_transport": "serial",
        "vendor_command": command,
        "sent": sent,
        "serial_write_returned": sent,
        "http_write_returned": None,
        "transport_write_returned": sent,
        "bytes_written": write_result.get("bytes_written"),
        "sends_motion": vendor_motion_command_nonzero(command),
    }
    try:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
    except OSError:
        # 命令日志只是验收材料，不能影响低速手控和 stop。
        return


def summarize_bridge_command_debug_log(
    path: str,
    stale_after_ms: int = DEFAULT_BRIDGE_COMMAND_DEBUG_STALE_AFTER_MS,
    max_lines: int = 600,
) -> dict[str, Any]:
    """读取 esp32_bridge 命令 JSONL，区分“命令已到 UART”和“轮速/运动未证明”。"""
    generated_at_ms = now_ms()
    artifact = {
        **artifact_path_info(path),
        "ok": False,
        "status": "unknown",
    }
    summary: dict[str, Any] = {
        "schema": f"{SCHEMA}.bridge_command_debug_summary",
        "generated_at_ms": generated_at_ms,
        "source": "esp32_bridge_command_debug_log",
        "artifact": artifact,
        "freshness": {
            "status": "unknown",
            "stale_after_ms": stale_after_ms,
            "basis": "artifact_mtime_only_bridge_command_not_hil_or_motion_proof",
        },
        "startup_main_type_config_sent": False,
        "startup_main_type": None,
        "startup_module_type": None,
        "startup_config_sent_count": 0,
        "nonzero_command_observed": False,
        "nonzero_command_count": 0,
        "nonzero_command_sent_observed": False,
        "nonzero_command_sent_count": 0,
        "serial_write_success_observed": False,
        "serial_write_success_count": 0,
        "http_write_success_observed": False,
        "http_write_success_count": 0,
        "transport_write_success_observed": False,
        "transport_write_success_count": 0,
        "command_write_failed_count": 0,
        "latest_nonzero_command": None,
        "latest_sent_nonzero_command": None,
        "latest_write_failed_command": None,
        "latest_command": None,
        "command_mode_counts": {},
        "bad_line_count": 0,
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
        summary["freshness"]["status"] = "missing"
        return summary
    except OSError as exc:
        artifact.update({"ok": False, "status": "read_failed", "error": compact_error(exc)})
        summary["freshness"]["status"] = "read_failed"
        return summary

    mtime_ms = int(stat_result.st_mtime_ns / 1_000_000)
    age_ms = max(0, generated_at_ms - mtime_ms)
    artifact.update({"mtime_ms": mtime_ms, "age_ms": age_ms})
    try:
        lines, bytes_scanned = read_recent_text_lines(path, max_lines=max_lines)
    except OSError as exc:
        artifact.update({"ok": False, "status": "read_failed", "error": compact_error(exc)})
        summary["freshness"]["status"] = "read_failed"
        return summary

    latest_command: dict[str, Any] | None = None
    latest_nonzero: dict[str, Any] | None = None
    latest_sent_nonzero: dict[str, Any] | None = None
    latest_write_failed: dict[str, Any] | None = None
    nonzero_count = 0
    nonzero_sent_count = 0
    serial_write_success_count = 0
    http_write_success_count = 0
    transport_write_success_count = 0
    command_write_failed_count = 0
    startup_count = 0
    mode_counts: dict[str, int] = {}
    bad_line_count = 0
    startup_main_type: Any = None
    startup_module_type: Any = None
    startup_main_type_sent = False
    for line in lines:
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            bad_line_count += 1
            continue
        if not isinstance(record, dict):
            continue
        source = record.get("source")
        command = record.get("vendor_command") if isinstance(record.get("vendor_command"), dict) else {}
        if source == "esp32_bridge_startup_config":
            startup_count += 1
            if command.get("T") == 900:
                startup_main_type_sent = bool(record.get("sent") is not False)
                startup_main_type = command.get("main")
                startup_module_type = command.get("module")
            continue
        if source not in {"esp32_bridge_cmd_vel_callback", "upper_robot_api_manual_control"} or not command:
            continue
        latest_command = {
            "observed_at_unix_s": record.get("observed_at_unix_s"),
            "command_mode": record.get("command_mode"),
            "linear_x": record.get("linear_x"),
            "angular_z": record.get("angular_z"),
            "vendor_command": command,
            "sent": record.get("sent"),
            "serial_write_returned": record.get("serial_write_returned", record.get("sent")),
            "http_write_returned": record.get("http_write_returned"),
            "transport_write_returned": record.get("transport_write_returned", record.get("sent")),
            "command_transport": record.get("command_transport"),
        }
        command_mode = str(record.get("command_mode") or "unknown")
        mode_counts[command_mode] = mode_counts.get(command_mode, 0) + 1
        transport_value = record.get("transport_write_returned", record.get("serial_write_returned", record.get("sent")))
        serial_value = record.get("serial_write_returned")
        http_value = record.get("http_write_returned")
        sent_value = transport_value
        sent_true = sent_value is True
        sent_false = sent_value is False
        if serial_value is True:
            serial_write_success_count += 1
        if http_value is True:
            http_write_success_count += 1
        if sent_true:
            transport_write_success_count += 1
        elif sent_false:
            command_write_failed_count += 1
            latest_write_failed = latest_command
        if vendor_motion_command_nonzero(command):
            nonzero_count += 1
            latest_nonzero = latest_command
            if sent_true:
                nonzero_sent_count += 1
                latest_sent_nonzero = latest_command

    artifact.update({"ok": True, "status": "loaded", "bytes_read": stat_result.st_size, "bytes_scanned": bytes_scanned, "tail_line_count": len(lines)})
    summary["freshness"]["status"] = freshness_from_age(age_ms, stale_after_ms)
    summary.update(
        {
            "bad_line_count": bad_line_count,
            "startup_main_type_config_sent": startup_main_type_sent,
            "startup_main_type": startup_main_type,
            "startup_module_type": startup_module_type,
            "startup_config_sent_count": startup_count,
            "nonzero_command_observed": nonzero_count > 0,
            "nonzero_command_count": nonzero_count,
            "nonzero_command_sent_observed": nonzero_sent_count > 0,
            "nonzero_command_sent_count": nonzero_sent_count,
            "serial_write_success_observed": serial_write_success_count > 0,
            "serial_write_success_count": serial_write_success_count,
            "http_write_success_observed": http_write_success_count > 0,
            "http_write_success_count": http_write_success_count,
            "transport_write_success_observed": transport_write_success_count > 0,
            "transport_write_success_count": transport_write_success_count,
            "command_write_failed_count": command_write_failed_count,
            "latest_nonzero_command": latest_nonzero,
            "latest_sent_nonzero_command": latest_sent_nonzero,
            "latest_write_failed_command": latest_write_failed,
            "latest_command": latest_command,
            "command_mode_counts": mode_counts,
            "robot_control_executed": nonzero_count > 0,
        }
    )
    return summary


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
    wheel_summary = latest_result.get("wheel_feedback_summary") if isinstance(latest_result, dict) and isinstance(latest_result.get("wheel_feedback_summary"), dict) else {}
    imu_summary = latest_result.get("imu_attitude_delta_summary") if isinstance(latest_result, dict) and isinstance(latest_result.get("imu_attitude_delta_summary"), dict) else {}
    wheel_nonzero = bool(wheel_summary.get("lr_nonzero_observed") or (isinstance(latest_result, dict) and latest_result.get("wheel_feedback_lr_nonzero_proven") is True))
    imu_delta = bool(imu_summary.get("imu_attitude_delta_observed") or (isinstance(latest_result, dict) and latest_result.get("imu_attitude_delta_observed") is True))
    motion_signal = bool(
        wheel_nonzero
        or imu_delta
        or (isinstance(latest_result, dict) and latest_result.get("motion_signal_observed") is True)
    )
    return {
        "schema": f"{SCHEMA}.base_feedback_samples_latest_result",
        "generated_at_ms": now_ms(),
        "artifact": artifact_status,
        "latest_result": latest_result,
        "latest_endpoint_path": ROUTE_PATHS["base_feedback_samples_latest"],
        "wheel_feedback_summary": wheel_summary,
        "wheel_feedback_nonzero_observed": wheel_nonzero,
        "wheel_feedback_lr_nonzero_proven": wheel_nonzero,
        "imu_attitude_delta_summary": imu_summary,
        "imu_attitude_delta_observed": imu_delta,
        "motion_signal_observed": motion_signal,
        "motion_signal_source": (
            latest_result.get("motion_signal_source")
            if isinstance(latest_result, dict) and latest_result.get("motion_signal_source")
            else "wheel_feedback_lr"
            if wheel_nonzero
            else "imu_attitude_delta"
            if imu_delta
            else "not_observed"
        ),
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


def build_operator_report_payload(path: str, report: dict[str, Any]) -> dict[str, Any]:
    """构造并持久化 operator report；写文件是唯一副作用，不触碰 ROS2 或串口。"""
    normalized_report, report_status = normalize_operator_report(report)
    report_note = ""
    if isinstance(normalized_report, dict):
        report_note = str(normalized_report.get("operator_notes") or "")[:120]
    payload: dict[str, Any] = {
        "schema": f"{SCHEMA}.operator_report_result",
        "generated_at_ms": now_ms(),
        "endpoint": ROUTE_PATHS["operator_report"],
        "request": {"method": "POST", "endpoint": ROUTE_PATHS["operator_report"]},
        "operator_report": normalized_report,
        "structured_hil_claims": normalized_report.get("structured_hil_claims") if isinstance(normalized_report, dict) else None,
        "operator_report_status": report_status,
        "command_payload_summary": {
            "evidence_ref": normalized_report.get("evidence_ref") if isinstance(normalized_report, dict) else None,
            "structured_hil_fields": list(OPERATOR_REPORT_STRUCTURED_HIL_FIELDS),
            "report_note": report_note,
        },
        "artifact": {
            **operator_report_artifact_info(path),
            "written_at_ms": now_ms(),
            "write": {"ok": True, "method": "atomic_replace"},
        },
        "does_not_replace": list(OPERATOR_REPORT_DOES_NOT_REPLACE),
        "boundary": "operator_report_is_human_site_material_only_not_ack_t1001_hil_stop_status_or_motion",
        **operator_report_guard_flags(),
    }
    write_result = atomic_write_json_artifact(path, payload)
    payload["artifact"]["write"] = write_result
    return payload


def build_operator_report_latest_payload(
    artifact_status: dict[str, Any],
    latest_result: dict[str, Any] | None,
) -> dict[str, Any]:
    """GET readback 只回放 latest report 文件，不能把人工材料升级成 runtime proof。"""
    structured_hil_claims = None
    if isinstance(latest_result, dict):
        structured_hil_claims = latest_result.get("structured_hil_claims")
        if structured_hil_claims is None and isinstance(latest_result.get("operator_report"), dict):
            structured_hil_claims = latest_result["operator_report"].get("structured_hil_claims")
    return {
        "schema": f"{SCHEMA}.operator_report_latest_result",
        "generated_at_ms": now_ms(),
        "endpoint": ROUTE_PATHS["operator_report"],
        "artifact": artifact_status,
        "latest_result": latest_result,
        "structured_hil_claims": structured_hil_claims,
        "latest_endpoint_path": ROUTE_PATHS["operator_report"],
        "does_not_replace": list(OPERATOR_REPORT_DOES_NOT_REPLACE),
        "boundary": "operator_report_readback_only_not_ack_t1001_hil_stop_status_or_motion",
        **operator_report_guard_flags(),
    }


def read_operator_report_latest_artifact(path: str) -> tuple[int, dict[str, Any]]:
    """只读 operator report artifact，不调用 stop/status/manual，也不读取串口。"""
    artifact = operator_report_artifact_info(path)
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        artifact.update({"ok": False, "status": "missing", "error": {"type": "FileNotFoundError", "message": "latest operator report artifact is missing"}})
        return 404, build_operator_report_latest_payload(artifact, None)
    except OSError as exc:
        artifact.update({"ok": False, "status": "read_failed", "error": compact_error(exc)})
        return 500, build_operator_report_latest_payload(artifact, None)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        artifact.update({"ok": False, "status": "bad_json", "error": compact_error(exc)})
        return 422, build_operator_report_latest_payload(artifact, None)
    if not isinstance(parsed, dict):
        artifact.update({"ok": False, "status": "json_not_object", "error": {"type": "ValueError", "message": "latest operator report JSON root is not an object"}})
        return 422, build_operator_report_latest_payload(artifact, None)
    artifact.update({"ok": True, "status": "loaded", "bytes_read": len(raw.encode("utf-8"))})
    return 200, build_operator_report_latest_payload(artifact, parsed)


def summarize_operator_report_latest_artifact(path: str) -> dict[str, Any]:
    """status 页面只摘要 report artifact，避免统一状态接口顺手读取硬件或远端服务。"""
    http_status, payload = read_operator_report_latest_artifact(path)
    latest = payload.get("latest_result") if isinstance(payload.get("latest_result"), dict) else None
    report = latest.get("operator_report") if isinstance(latest, dict) and isinstance(latest.get("operator_report"), dict) else {}
    return {
        "schema": f"{SCHEMA}.operator_report_latest_summary",
        "generated_at_ms": now_ms(),
        "endpoint": ROUTE_PATHS["operator_report"],
        "http_status": http_status,
        "artifact": payload["artifact"],
        "operator_report_status": latest.get("operator_report_status") if isinstance(latest, dict) else None,
        "latest_evidence_ref": report.get("evidence_ref") if isinstance(report, dict) else None,
        "latest_report_note": report.get("operator_notes") if isinstance(report, dict) else None,
        "structured_hil_claims": report.get("structured_hil_claims") if isinstance(report, dict) else None,
        **operator_report_guard_flags(),
    }


def build_delivery_completion_payload(
    *,
    path: str,
    request: dict[str, Any],
    nav2_http_status: int,
    nav2_latest: dict[str, Any],
    operator_http_status: int,
    operator_latest: dict[str, Any],
) -> dict[str, Any]:
    """把 Nav2 执行证据和现场报告合成交付完成结论；任一材料缺失都 fail closed。"""
    nav2_result = nav2_latest.get("latest_result") if isinstance(nav2_latest.get("latest_result"), dict) else {}
    operator_result = operator_latest.get("latest_result") if isinstance(operator_latest.get("latest_result"), dict) else {}
    operator_report = operator_result.get("operator_report") if isinstance(operator_result.get("operator_report"), dict) else {}
    claims = operator_result.get("structured_hil_claims")
    if not isinstance(claims, dict) and isinstance(operator_report.get("structured_hil_claims"), dict):
        claims = operator_report["structured_hil_claims"]
    claims = claims if isinstance(claims, dict) else {}

    missing: list[str] = []
    if request.get("confirm_delivery_completion") is not True:
        missing.append("confirm_delivery_completion")
    if nav2_http_status != 200:
        missing.append("nav2_goal_execution_latest_http_200")
    if nav2_result.get("status") != "goal_succeeded":
        missing.append("nav2_goal_succeeded")
    if nav2_result.get("goal_accepted") is not True:
        missing.append("nav2_goal_accepted")
    if nav2_result.get("result_received") is not True:
        missing.append("nav2_result_received")
    if nav2_result.get("result_status") != "succeeded":
        missing.append("nav2_result_status_succeeded")
    if operator_http_status != 200:
        missing.append("operator_report_latest_http_200")
    if operator_result.get("operator_report_status") != "ready_for_review":
        missing.append("operator_report_ready_for_review")
    if operator_report.get("observed_motion") is not True:
        missing.append("operator_observed_motion")
    if operator_report.get("observed_stop") is not True:
        missing.append("operator_observed_stop")
    if claims.get("delivery_success") is not True:
        missing.append("structured_hil_claims.delivery_success")
    if claims.get("real_route_map_proven") is not True:
        missing.append("structured_hil_claims.real_route_map_proven")
    if not str(claims.get("route_map_ref") or "").strip():
        missing.append("structured_hil_claims.route_map_ref")
    visual_ok = (
        claims.get("external_video_recorded") is True
        and bool(str(claims.get("external_video_ref") or "").strip())
    ) or (
        claims.get("visible_content_proven") is True
        and bool(str(claims.get("camera_artifacts_ref") or "").strip())
    )
    if not visual_ok:
        missing.append("external_video_or_visible_camera_ref")

    delivery_success = not missing
    now = now_ms()
    payload: dict[str, Any] = {
        "schema": f"{SCHEMA}.delivery_completion_result",
        "generated_at_ms": now,
        "endpoint": ROUTE_PATHS["delivery_complete"],
        "request": {
            "method": "POST",
            "endpoint": ROUTE_PATHS["delivery_complete"],
            "confirm_delivery_completion": request.get("confirm_delivery_completion") is True,
            "delivery_evidence_ref": normalize_optional_report_text(request.get("delivery_evidence_ref")),
            "operator_notes": normalize_optional_report_text(request.get("operator_notes")),
        },
        "status": "delivery_success_confirmed" if delivery_success else "blocked_missing_delivery_material",
        "delivery_success": delivery_success,
        "safe_to_control": False,
        "primary_actions_enabled": False,
        "hil_pass": False,
        "robot_control_executed": False,
        "sends_commands": False,
        "sends_motion_commands": False,
        "publishes_cmd_vel": False,
        "calls_base_manual": False,
        "uses_base_uart": False,
        "source": "nav2_goal_execution_plus_operator_report",
        "nav2_goal_execution": {
            "http_status": nav2_http_status,
            "status": nav2_result.get("status"),
            "evidence_ref": nav2_result.get("evidence_ref"),
            "goal_accepted": bool(nav2_result.get("goal_accepted")),
            "result_received": bool(nav2_result.get("result_received")),
            "result_status": nav2_result.get("result_status"),
            "feedback_sample_count": int(nav2_result.get("feedback_sample_count") or 0),
        },
        "operator_report": {
            "http_status": operator_http_status,
            "operator_report_status": operator_result.get("operator_report_status"),
            "evidence_ref": operator_report.get("evidence_ref"),
            "observed_motion": operator_report.get("observed_motion"),
            "observed_stop": operator_report.get("observed_stop"),
            "structured_hil_claims": claims,
        },
        "missing_required_material": missing,
        "required_material": [
            "confirm_delivery_completion",
            "nav2_goal_succeeded",
            "operator_report_ready_for_review",
            "operator_observed_motion",
            "operator_observed_stop",
            "structured_hil_claims.delivery_success",
            "structured_hil_claims.real_route_map_proven + route_map_ref",
            "external_video_or_visible_camera_ref",
        ],
        "artifact": {
            **delivery_completion_artifact_info(path),
            "written_at_ms": now,
            "write": {"ok": True, "method": "atomic_replace"},
        },
        "boundary": "delivery_success_requires_nav2_goal_succeeded_and_operator_dropoff_confirmation",
    }
    write_result = atomic_write_json_artifact(path, payload)
    payload["artifact"]["write"] = write_result
    return payload


def build_delivery_completion_latest_payload(artifact_status: dict[str, Any], latest_result: dict[str, Any] | None) -> dict[str, Any]:
    """送达完成 latest 只读 artifact；缺失时显式 fail closed。"""
    delivery_success = bool(isinstance(latest_result, dict) and latest_result.get("delivery_success") is True)
    status = latest_result.get("status") if isinstance(latest_result, dict) else None
    missing_required_material = (
        latest_result.get("missing_required_material")
        if isinstance(latest_result, dict) and isinstance(latest_result.get("missing_required_material"), list)
        else []
    )
    nav2_goal_execution = (
        latest_result.get("nav2_goal_execution")
        if isinstance(latest_result, dict) and isinstance(latest_result.get("nav2_goal_execution"), dict)
        else {}
    )
    operator_report = (
        latest_result.get("operator_report")
        if isinstance(latest_result, dict) and isinstance(latest_result.get("operator_report"), dict)
        else {}
    )
    required_material = (
        latest_result.get("required_material")
        if isinstance(latest_result, dict) and isinstance(latest_result.get("required_material"), list)
        else []
    )
    return {
        "schema": f"{SCHEMA}.delivery_completion_latest_result",
        "generated_at_ms": now_ms(),
        "endpoint": ROUTE_PATHS["delivery_latest"],
        "artifact": artifact_status,
        "latest_result": latest_result,
        "status": status or ("delivery_success_confirmed" if delivery_success else "not_loaded"),
        "proof_state": "delivery_success_confirmed" if delivery_success else "not_proven",
        "missing_required_material": missing_required_material,
        "required_material": required_material,
        "nav2_goal_execution": nav2_goal_execution,
        "operator_report": operator_report,
        "delivery_success": delivery_success,
        "safe_to_control": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "boundary": "readback_only_delivery_completion_gate",
    }


def read_delivery_completion_latest_artifact(path: str) -> tuple[int, dict[str, Any]]:
    """读取 delivery completion latest，不触发机器人动作。"""
    artifact = delivery_completion_artifact_info(path)
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        artifact.update({"ok": False, "status": "missing", "error": {"type": "FileNotFoundError", "message": "latest delivery completion artifact is missing"}})
        return 404, build_delivery_completion_latest_payload(artifact, None)
    except OSError as exc:
        artifact.update({"ok": False, "status": "read_failed", "error": compact_error(exc)})
        return 500, build_delivery_completion_latest_payload(artifact, None)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        artifact.update({"ok": False, "status": "bad_json", "error": compact_error(exc)})
        return 422, build_delivery_completion_latest_payload(artifact, None)
    if not isinstance(parsed, dict):
        artifact.update({"ok": False, "status": "json_not_object", "error": {"type": "ValueError", "message": "latest delivery completion JSON root is not an object"}})
        return 422, build_delivery_completion_latest_payload(artifact, None)
    artifact.update({"ok": True, "status": "loaded", "bytes_read": len(raw.encode("utf-8"))})
    return 200, build_delivery_completion_latest_payload(artifact, parsed)


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
    if read_error and t1001_observed:
        return "observed_with_read_error"
    if read_error:
        return "read_error"
    if t1001_observed:
        return "observed"
    return "not_observed_after_t130"


def feedback_type_from_frame(frame: dict[str, Any]) -> int | None:
    """只用 vendor `T` 字段识别反馈类型，避免 `y:null` 误伤整帧 ACK。"""
    feedback_type = frame.get("T")
    if isinstance(feedback_type, int):
        return feedback_type
    if isinstance(feedback_type, str) and feedback_type.isdigit():
        return int(feedback_type)
    return None


def t1001_feedback_observed_in_frame(frame: dict[str, Any]) -> bool:
    """T=1001 是底盘反馈身份；yaw 缺失只能影响姿态，不影响反馈到达判定。"""
    return feedback_type_from_frame(frame) == BASE_FEEDBACK_ID


def finite_feedback_number(value: Any) -> float | None:
    """只接受有限数值或数字字符串，避免把 null/yaw 字符串误算成轮速。"""
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def parse_serial_json_objects(raw_line: bytes) -> list[dict[str, Any]]:
    """从一行 UART 噪声里提取完整 JSON 对象，允许 CR 后粘连损坏碎片。"""
    try:
        decoded = raw_line.decode("utf-8", errors="ignore").strip()
    except Exception:
        return []
    if not decoded:
        return []
    decoder = json.JSONDecoder()
    objects: list[dict[str, Any]] = []
    index = 0
    while index < len(decoded):
        start = decoded.find("{", index)
        if start < 0:
            break
        try:
            parsed, end = decoder.raw_decode(decoded[start:])
        except json.JSONDecodeError:
            # 现场串口可能把损坏碎片和下一帧粘在同一行；跳过这个左花括号继续找下一段。
            index = start + 1
            continue
        if isinstance(parsed, dict):
            objects.append(parsed)
        index = start + max(end, 1)
    return objects


def compact_t1001_feedback_frame(frame: dict[str, Any]) -> dict[str, Any] | None:
    """保留 vendor T=1001 复核所需最小字段，不把整行串口内容暴露给 PC。"""
    if not t1001_feedback_observed_in_frame(frame):
        return None
    compact: dict[str, Any] = {"T": BASE_FEEDBACK_ID}
    for key in ("L", "R", "r", "p", "y", "v"):
        if key in frame:
            compact[key] = frame.get(key)
    return compact


def wheel_feedback_summary_from_frames(frames: list[dict[str, Any]]) -> dict[str, Any]:
    """从同一 T=1001 帧内提取 L/R 非零材料；单侧非零或跨帧拼接都不算通过。"""
    matched_frames: list[dict[str, Any]] = []
    nonzero_frames: list[dict[str, Any]] = []
    latest_pair: dict[str, Any] | None = None
    latest_nonzero_pair: dict[str, Any] | None = None
    for frame in frames:
        left_speed = finite_feedback_number(frame.get("L"))
        right_speed = finite_feedback_number(frame.get("R"))
        if left_speed is None or right_speed is None:
            continue
        pair = {
            "source": "vendor_t1001_L_R",
            "left_speed": left_speed,
            "right_speed": right_speed,
        }
        matched_frames.append(pair)
        latest_pair = pair
        if abs(left_speed) > 0.0 and abs(right_speed) > 0.0:
            nonzero_frames.append(pair)
            latest_nonzero_pair = pair

    observed = bool(nonzero_frames)
    return {
        "source": "vendor_t1001_L_R",
        "frame_count": len(frames),
        "matched_frame_count": len(matched_frames),
        "nonzero_frame_count": len(nonzero_frames),
        "lr_nonzero_observed": observed,
        "latest_pair": latest_pair,
        "latest_nonzero_pair": latest_nonzero_pair,
        "reason": (
            "same T=1001 frame contains finite nonzero L/R wheel feedback"
            if observed
            else "no same T=1001 frame contained finite nonzero L/R wheel feedback"
        ),
    }


def command_raw_motion_summary(
    command: dict[str, Any] | None,
    write_result: dict[str, Any] | None = None,
    *,
    source: str,
) -> dict[str, Any]:
    """把本次下发命令的 raw 非零事实单独成证；它不能替代 T1001 feedback。"""
    command = command if isinstance(command, dict) else {}
    write_result = write_result if isinstance(write_result, dict) else {}
    try:
        command_id = int(command.get("T"))
    except (TypeError, ValueError):
        command_id = None
    left = finite_feedback_number(command.get("L"))
    right = finite_feedback_number(command.get("R"))
    linear_x = finite_feedback_number(command.get("X"))
    angular_z = finite_feedback_number(command.get("Z"))
    lr_pair_available = left is not None and right is not None
    lr_nonzero = bool(lr_pair_available and abs(left or 0.0) > 0.0 and abs(right or 0.0) > 0.0)
    twist_nonzero = bool(
        command_id == 13
        and ((linear_x is not None and abs(linear_x) > 0.0) or (angular_z is not None and abs(angular_z) > 0.0))
    )
    transport_write_returned = (
        write_result.get("transport_write_returned")
        if "transport_write_returned" in write_result
        else write_result.get("serial_write_returned")
        if "serial_write_returned" in write_result
        else write_result.get("http_write_returned")
        if "http_write_returned" in write_result
        else write_result.get("sent")
        if "sent" in write_result
        else write_result.get("ok")
    )
    sent = transport_write_returned is True
    raw_nonzero = bool(lr_nonzero or twist_nonzero)
    return {
        "source": source,
        "command_type": command_id,
        "command_mode": command_mode_for_vendor_command(command) if command_id is not None else "unknown",
        "sent": sent,
        "transport_write_returned": transport_write_returned,
        "raw_nonzero_observed": raw_nonzero,
        "raw_nonzero_proven": bool(sent and raw_nonzero),
        "lr_pair_available": lr_pair_available,
        "lr_nonzero_observed": lr_nonzero,
        "lr_nonzero_proven": bool(sent and lr_nonzero),
        "left_raw": left,
        "right_raw": right,
        "twist_nonzero_observed": twist_nonzero,
        "twist_nonzero_proven": bool(sent and twist_nonzero),
        "linear_x": linear_x,
        "angular_z": angular_z,
        "vendor_command": command,
        "reason": (
            "sent command contains finite nonzero L/R raw values"
            if sent and lr_nonzero
            else "sent ROS/T=13 command contains nonzero X/Z raw values"
            if sent and twist_nonzero
            else "command was not sent or did not contain nonzero raw motion values"
        ),
    }


def command_raw_motion_summary_from_debug_record(
    record: dict[str, Any] | None,
    *,
    source: str,
) -> dict[str, Any]:
    """从 bridge command debug 的 latest record 中派生命令 raw 证据，供 PC 区分命令与反馈。"""
    if not isinstance(record, dict):
        return command_raw_motion_summary(None, None, source=source)
    command = record.get("vendor_command") if isinstance(record.get("vendor_command"), dict) else {}
    return command_raw_motion_summary(command, record, source=source)


# PC 低速短脉冲不会总是带来 1 度以上姿态变化；0.35 度能覆盖现场 0.5 度级别的真实动静信号。
IMU_ATTITUDE_DELTA_MOTION_THRESHOLD_DEGREES = 0.35


def imu_attitude_delta_summary_from_frames(frames: list[dict[str, Any]]) -> dict[str, Any]:
    """用 T1001 r/p 计算姿态变化迹象；它不能替代轮速闭环或交付成功。"""
    matched_frames: list[dict[str, float]] = []
    for frame in frames:
        roll = finite_feedback_number(frame.get("r"))
        pitch = finite_feedback_number(frame.get("p"))
        if roll is None or pitch is None:
            continue
        matched_frames.append({"roll": roll, "pitch": pitch})

    threshold_degrees = IMU_ATTITUDE_DELTA_MOTION_THRESHOLD_DEGREES
    max_roll_delta = 0.0
    max_pitch_delta = 0.0
    if matched_frames:
        base_roll = matched_frames[0]["roll"]
        base_pitch = matched_frames[0]["pitch"]
        max_roll_delta = max(abs(item["roll"] - base_roll) for item in matched_frames)
        max_pitch_delta = max(abs(item["pitch"] - base_pitch) for item in matched_frames)
    observed = max(max_roll_delta, max_pitch_delta) >= threshold_degrees
    return {
        "source": "vendor_t1001_r_p",
        "frame_count": len(frames),
        "matched_frame_count": len(matched_frames),
        "imu_attitude_delta_observed": observed,
        "max_abs_roll_delta": round(max_roll_delta, 6),
        "max_abs_pitch_delta": round(max_pitch_delta, 6),
        "threshold_degrees": threshold_degrees,
        "reason": (
            "T=1001 roll/pitch changed during the sample window"
            if observed
            else "no T=1001 roll/pitch delta above threshold was observed"
        ),
    }


def t1001_frames_from_feedback_payload(payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    """从一次反馈 payload 中取出精简 T1001 帧；缺失时返回空列表便于合并。"""
    if not isinstance(payload, dict):
        return []
    frames = payload.get("t1001_feedback_frames")
    if not isinstance(frames, list):
        return []
    return [frame for frame in frames if isinstance(frame, dict)]


def feedback_ack_from_fresh_evidence(
    readback: dict[str, Any],
    latest_artifact_summary: dict[str, Any],
) -> dict[str, Any]:
    """status 只能信本次 readback 或 fresh artifact，旧材料不得抬高 ACK。"""
    readback_ack = readback.get("feedback_ack") if isinstance(readback.get("feedback_ack"), dict) else {}
    if readback_ack.get("t1001_observed") is True:
        return {
            "t1001_observed": True,
            "robot_ack_connected": False,
            "source": "fresh_readback",
            "reason": "T=1001 observed by this /api/base/status non-motion T=130 readback",
        }
    freshness = latest_artifact_summary.get("freshness")
    artifact_is_fresh = isinstance(freshness, dict) and freshness.get("status") == "fresh"
    artifact_count = latest_artifact_summary.get("latest_t1001_observed_count")
    if artifact_is_fresh and isinstance(artifact_count, int) and artifact_count > 0:
        return {
            "t1001_observed": True,
            "robot_ack_connected": False,
            "source": "fresh_artifact",
            "reason": "T=1001 observed in fresh feedback samples artifact; this is not robot ACK or HIL proof",
        }
    return {
        "t1001_observed": False,
        "robot_ack_connected": False,
        "source": "fresh_readback_or_fresh_artifact",
        "reason": str(readback_ack.get("reason") or "T=1001 not observed in fresh /api/base/status evidence"),
    }


def feedback_ack_from_bridge_debug(bridge_summary: dict[str, Any]) -> dict[str, Any]:
    """bridge 已持有 UART 时，status ACK 优先来自 fresh JSONL，避免 API 再开串口。"""
    count = bridge_summary.get("t1001_observed_count")
    if isinstance(count, int) and count > 0:
        return {
            "t1001_observed": True,
            "robot_ack_connected": False,
            "source": "fresh_bridge_feedback_debug_log",
            "reason": "T=1001 observed in fresh esp32_bridge feedback debug log; /api/base/status skipped direct T=130 UART read",
        }
    return {
        "t1001_observed": False,
        "robot_ack_connected": False,
        "source": "fresh_bridge_feedback_debug_log",
        "reason": "fresh esp32_bridge feedback debug log available but no T=1001 frame observed",
    }


def bridge_debug_summary_as_feedback_sample(bridge_summary: dict[str, Any]) -> dict[str, Any]:
    """把 bridge JSONL 摘要包装成 samples payload 的单个 sample，不重新打开 UART。"""
    frames = bridge_summary.get("t1001_feedback_frames")
    frames = [frame for frame in frames if isinstance(frame, dict)] if isinstance(frames, list) else []
    return {
        "schema": f"{SCHEMA}.bridge_feedback_debug_sample",
        "serial_open": {"ok": False, "source": "esp32_bridge_feedback_debug_log", "reason": "bridge_already_owns_uart"},
        "serial_write": {"ok": False, "command": None, "reason": "no_direct_t130_request_for_ros_manual_pulse"},
        "serial_read": {"ok": True, "source": "esp32_bridge_feedback_debug_log"},
        "read_line_count": len(frames),
        "parsed_json_count": len(frames),
        "invalid_json_count": int(bridge_summary.get("bad_line_count") or 0),
        "observed_feedback_types": [BASE_FEEDBACK_ID] if frames else [],
        "t1001_feedback_frames": frames,
        "t1001_feedback_status": "observed" if frames else "not_observed",
        "feedback_ack": feedback_ack_from_bridge_debug(bridge_summary),
        "wheel_feedback_summary": bridge_summary.get("wheel_feedback_summary"),
        "safe_to_control": False,
        "sends_motion_commands": False,
        "robot_control_executed": False,
        "delivery_success": False,
        "hil_pass": False,
    }


def bridge_debug_summary_as_manual_feedback_payload(
    bridge_summary: dict[str, Any],
    *,
    port: str,
    baudrate: int,
    reason: str,
) -> dict[str, Any]:
    """把 bridge-owned T1001 帧放回本次手控运动窗口，避免 API 抢 UART 后误报 0 帧。"""
    sample = bridge_debug_summary_as_feedback_sample(bridge_summary)
    frames = t1001_frames_from_feedback_payload(sample)
    return {
        **sample,
        "schema": f"{SCHEMA}.base_manual_bridge_feedback",
        "generated_at_ms": now_ms(),
        "vendor_sources": VENDOR_SOURCES,
        "port": port,
        "baudrate": baudrate,
        "request": {
            "method": "POST",
            "endpoint": "/api/base/manual",
            "command": None,
            "attempted": False,
            "reason": reason,
            "source": "esp32_bridge_feedback_debug_log",
        },
        "read_line_count": len(frames),
        "parsed_json_count": len(frames),
        "t1001_feedback_status": "observed_from_bridge_debug" if frames else "not_observed_from_bridge_debug",
        "feedback_source": "esp32_bridge_feedback_debug_log",
    }


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
    t1001_feedback_frames: list[dict[str, Any]] = []
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
            t1001_feedback_frames=[],
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
            t1001_feedback_frames=[],
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
                parsed_objects = parse_serial_json_objects(raw_line)
                if not parsed_objects:
                    invalid_json_count += 1
                    continue
                for parsed in parsed_objects:
                    parsed_json_count += 1
                    feedback_type = feedback_type_from_frame(parsed)
                    if feedback_type is not None:
                        observed_feedback_types.append(feedback_type)
                    compact_frame = compact_t1001_feedback_frame(parsed)
                    if compact_frame is not None:
                        # T1001 帧数量由短 read window 限制；保留精简字段可直接复核 L/R。
                        t1001_feedback_frames.append(compact_frame)
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
        t1001_feedback_frames=t1001_feedback_frames,
        t1001_feedback_status=status,
    )


def write_json_to_open_serial(serial_obj: Any, command: dict[str, Any]) -> dict[str, Any]:
    """复用已打开串口写 JSON；manual 点动需要同一会话内写运动、读反馈、写 stop。"""
    try:
        frame = (json.dumps(command, separators=(",", ":")) + "\n").encode("utf-8")
        return {"ok": True, "command": command, "bytes_written": serial_obj.write(frame)}
    except Exception as exc:  # noqa: BLE001 - 串口现场错误必须结构化上报。
        return {"ok": False, "command": command, "error": compact_error(exc)}


def read_serial_json_window(serial_obj: Any, read_window_s: float) -> dict[str, Any]:
    """在短窗口内收集换行 JSON；只保留精简帧，避免把无限串口流灌到 API。"""
    read_line_count = 0
    parsed_json_count = 0
    invalid_json_count = 0
    observed_feedback_types: list[int] = []
    t1001_feedback_frames: list[dict[str, Any]] = []
    compact_frames: list[dict[str, Any]] = []
    read_error: dict[str, str] | None = None
    deadline = time.monotonic() + read_window_s
    try:
        while time.monotonic() < deadline:
            raw_line = serial_obj.readline()
            if not raw_line:
                continue
            read_line_count += 1
            parsed_objects = parse_serial_json_objects(raw_line)
            if not parsed_objects:
                invalid_json_count += 1
                continue
            for parsed in parsed_objects:
                parsed_json_count += 1
                compact_frame = {key: parsed.get(key) for key in ("T", "L", "R", "X", "Z", "cmd", "r", "p", "y", "v") if key in parsed}
                if len(compact_frames) < 24:
                    compact_frames.append(compact_frame)
                feedback_type = feedback_type_from_frame(parsed)
                if feedback_type is not None:
                    observed_feedback_types.append(feedback_type)
                compact_t1001 = compact_t1001_feedback_frame(parsed)
                if compact_t1001 is not None:
                    t1001_feedback_frames.append(compact_t1001)
    except Exception as exc:  # noqa: BLE001 - 读阶段错误不能吞掉，否则现场会误判为无反馈。
        read_error = compact_error(exc)
    return {
        "read_line_count": read_line_count,
        "parsed_json_count": parsed_json_count,
        "invalid_json_count": invalid_json_count,
        "observed_feedback_types": observed_feedback_types,
        "t1001_feedback_frames": t1001_feedback_frames,
        "compact_frames": compact_frames,
        "read_error": read_error,
    }


def build_feedback_payload_from_open_serial_read(
    *,
    port: str,
    baudrate: int,
    read_timeout_s: float,
    read_window_s: float,
    serial_open: dict[str, Any],
    serial_write: dict[str, Any],
    read_summary: dict[str, Any],
) -> dict[str, Any]:
    """把同一串口会话里的 read window 包装成既有 T1001 feedback 合同。"""
    observed_types = sorted(set(read_summary["observed_feedback_types"]))
    status = feedback_request_status(
        serial_open_ok=bool(serial_open.get("ok")),
        serial_write_ok=bool(serial_write.get("ok")),
        t1001_observed=BASE_FEEDBACK_ID in observed_types,
        import_error=None,
        read_error=read_summary.get("read_error"),
    )
    payload = build_base_feedback_payload(
        port=port,
        baudrate=baudrate,
        read_timeout_s=read_timeout_s,
        read_window_s=read_window_s,
        serial_open=serial_open,
        serial_write=serial_write,
        serial_read={"ok": read_summary.get("read_error") is None, "window_s": read_window_s, "error": read_summary.get("read_error")},
        read_line_count=read_summary["read_line_count"],
        parsed_json_count=read_summary["parsed_json_count"],
        invalid_json_count=read_summary["invalid_json_count"],
        observed_feedback_types=observed_types,
        t1001_feedback_frames=read_summary["t1001_feedback_frames"],
        t1001_feedback_status=status,
    )
    payload["compact_frames"] = read_summary["compact_frames"]
    return payload


def _ros_cmd_vel_message(linear_x: float, angular_z: float) -> str:
    """生成 ros2 CLI 可接受的 Twist YAML；数值已在调用侧限幅。"""
    return (
        "{linear: {x: "
        f"{linear_x}, y: 0.0, z: 0.0"
        "}, angular: {x: 0.0, y: 0.0, z: "
        f"{angular_z}"
        "}}"
    )


def _ros_python_import_paths() -> list[str]:
    """裸 python 启动时补 ROS Python 路径；动态库仍依赖进程启动时的 ROS 环境。"""
    return [
        "/opt/ros/humble/lib/python3.10/site-packages",
        "/opt/ros/humble/local/lib/python3.10/dist-packages",
        "/root/rober/onboard/install/ros2_trashbot_interfaces/local/lib/python3.10/dist-packages",
    ]


def _ensure_ros_cmd_vel_context() -> dict[str, Any]:
    """懒加载 rclpy publisher；成功后每次 WASD 复用同一个 node，避免 CLI 冷启动。"""
    if _ROS_CMD_VEL_CONTEXT.get("status") == "ready":
        return _ROS_CMD_VEL_CONTEXT
    if _ROS_CMD_VEL_CONTEXT.get("status") == "unavailable":
        return _ROS_CMD_VEL_CONTEXT
    # 现场 Orange Pi 的 FastDDS SHM 锁文件会让 rclpy/ros2 pub 初始化抖到数秒；
    # 上位机进程内 publisher 和 CLI 兜底都统一关闭 SHM，优先走稳定的 UDP 发现。
    os.environ.setdefault("RMW_FASTRTPS_USE_SHM", "0")
    for path in _ros_python_import_paths():
        if path not in sys.path:
            sys.path.append(path)
    try:
        import rclpy  # type: ignore[import-not-found]
        from geometry_msgs.msg import Twist  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001 - ROS 环境缺失时必须保留 CLI 回退。
        _ROS_CMD_VEL_CONTEXT.clear()
        _ROS_CMD_VEL_CONTEXT.update(
            {
                "status": "unavailable",
                "error": compact_error(exc),
                "next_action": "start upper_robot_api from sourced ROS environment",
            }
        )
        return _ROS_CMD_VEL_CONTEXT
    try:
        if not rclpy.ok():
            rclpy.init(args=None)
        node = rclpy.create_node("upper_robot_api_cmd_vel_publisher")
        publisher = node.create_publisher(Twist, ROS_CMD_VEL_TOPIC, 10)
    except Exception as exc:  # noqa: BLE001 - ROS graph 初始化失败时继续走 CLI 兜底。
        _ROS_CMD_VEL_CONTEXT.clear()
        _ROS_CMD_VEL_CONTEXT.update({"status": "unavailable", "error": compact_error(exc)})
        return _ROS_CMD_VEL_CONTEXT
    _ROS_CMD_VEL_CONTEXT.clear()
    _ROS_CMD_VEL_CONTEXT.update(
        {
            "status": "ready",
            "rclpy": rclpy,
            "twist_type": Twist,
            "node": node,
            "publisher": publisher,
            "ready_mono_ns": time.monotonic_ns(),
            "topic": ROS_CMD_VEL_TOPIC,
            "rmw_fastrtps_use_shm": os.environ.get("RMW_FASTRTPS_USE_SHM"),
        }
    )
    return _ROS_CMD_VEL_CONTEXT


def prewarm_ros_cmd_vel_context(wait_subscription_s: float = 0.6) -> dict[str, Any]:
    """服务启动时预热 publisher/DDS graph；不发布任何运动或停车帧。"""
    context = _ensure_ros_cmd_vel_context()
    if context.get("status") != "ready":
        context["prewarm_status"] = "unavailable_fail_closed"
        context["prewarm_subscription_count"] = 0
        return context
    publisher = context["publisher"]
    rclpy = context["rclpy"]
    node = context["node"]
    deadline = time.monotonic() + max(float(wait_subscription_s), 0.0)
    with _ROS_CMD_VEL_LOCK:
        subscription_count = int(publisher.get_subscription_count())
    while subscription_count <= 0 and time.monotonic() < deadline:
        # discovery 只在 startup 等待；正常 keydown hot path 不再承担这段等待。
        with _ROS_CMD_VEL_LOCK:
            rclpy.spin_once(node, timeout_sec=min(0.05, max(deadline - time.monotonic(), 0.0)))
            subscription_count = int(publisher.get_subscription_count())
    context["prewarm_subscription_count"] = subscription_count
    context["prewarm_done_mono_ns"] = time.monotonic_ns()
    context["prewarm_status"] = "ready" if subscription_count > 0 else "degraded_subscription_unproven"
    return context


def publish_ros_cmd_vel_inprocess_burst(
    linear_x: float,
    angular_z: float,
    *,
    hold_s: float,
    rate_hz: float = ROS_CMD_VEL_BURST_RATE_HZ,
    wait_subscription_s: float = ROS_CMD_VEL_SUBSCRIPTION_WAIT_S,
    require_subscription_match: bool = False,
) -> dict[str, Any]:
    """进程内连续发布 cmd_vel；这是 PC 键盘手控的低延迟主路径。"""
    linear_x = round(float(linear_x), 6)
    angular_z = round(float(angular_z), 6)
    hold_s = max(float(hold_s), 0.0)
    rate_hz = max(float(rate_hz), 1.0)
    context = _ensure_ros_cmd_vel_context()
    result: dict[str, Any] = {
        "ok": False,
        "mode": "ros_cmd_vel_once",
        "publish_backend": "rclpy_inprocess_burst",
        "topic": ROS_CMD_VEL_TOPIC,
        "message_type": "geometry_msgs/msg/Twist",
        "rmw_fastrtps_use_shm": os.environ.get("RMW_FASTRTPS_USE_SHM", ""),
        "linear_x": linear_x,
        "angular_z": angular_z,
        "hold_s": round(hold_s, 6),
        "rate_hz": rate_hz,
    }
    if context.get("status") != "ready":
        result["error"] = context.get("error") or {"type": "rclpy_unavailable", "message": "rclpy context unavailable"}
        result["fallback_required"] = True
        result["rclpy_context_status"] = context.get("prewarm_status", "unavailable_fail_closed")
        result["rclpy_ready_mono_ns"] = context.get("ready_mono_ns")
        return result

    rclpy = context["rclpy"]
    twist_type = context["twist_type"]
    node = context["node"]
    publisher = context["publisher"]
    function_enter_mono_ns = time.monotonic_ns()
    wait_started = time.monotonic()
    with _ROS_CMD_VEL_LOCK:
        if require_subscription_match:
            # 零等待 spin 只刷新当前 graph cache；bridge 未出现时立即 fail-closed，不阻塞 keydown。
            rclpy.spin_once(node, timeout_sec=0.0)
        subscription_count = int(publisher.get_subscription_count())
    if require_subscription_match and subscription_count <= 0:
        context["prewarm_status"] = "degraded_subscription_unproven"
        context["prewarm_subscription_count"] = 0
        failed_mono_ns = time.monotonic_ns()
        return {
            **result,
            "subscription_match_required": True,
            "subscription_match_proven": False,
            "subscription_count": 0,
            "frames_published": 0,
            "rclpy_context_status": "degraded_subscription_unproven",
            "rclpy_ready_mono_ns": context.get("ready_mono_ns"),
            "publish_function_enter_mono_ns": function_enter_mono_ns,
            "cmd_vel_first_publish_mono_ns": None,
            "cmd_vel_publish_done_mono_ns": failed_mono_ns,
            "error": {
                "type": "cmd_vel_subscription_unavailable_fail_closed",
                "message": "realtime_hold requires a currently matched /cmd_vel subscriber",
            },
            "fallback_required": False,
            "wait_subscription_s": 0.0,
        }
    if require_subscription_match:
        # bridge 后启动/重启后，当前 count 一旦恢复即可把 context 从 degraded 提升回 ready。
        context["prewarm_status"] = "ready"
        context["prewarm_subscription_count"] = subscription_count
    frame_interval_s = 1.0 / rate_hz
    frame_count = max(1, int(math.ceil(max(hold_s, frame_interval_s) * rate_hz)))
    message = twist_type()
    message.linear.x = linear_x
    message.linear.y = 0.0
    message.linear.z = 0.0
    message.angular.x = 0.0
    message.angular.y = 0.0
    message.angular.z = angular_z
    publish_started = time.monotonic()
    frames_published = 0
    # 首帧在任何 sleep/discovery wait 前发出；startup prewarm 已承担正常 DDS graph 等待。
    cmd_vel_first_publish_mono_ns = time.monotonic_ns()
    with _ROS_CMD_VEL_LOCK:
        publisher.publish(message)
        rclpy.spin_once(node, timeout_sec=0.0)
    frames_published = 1
    while subscription_count <= 0 and time.monotonic() - wait_started < wait_subscription_s:
        # 若 subscriber 重启，只在首帧后推进 discovery；这段等待不再增加按下到首次 publish 的延迟。
        with _ROS_CMD_VEL_LOCK:
            rclpy.spin_once(node, timeout_sec=min(0.05, wait_subscription_s))
            subscription_count = int(publisher.get_subscription_count())
    for _index in range(1, frame_count):
        time.sleep(frame_interval_s)
        with _ROS_CMD_VEL_LOCK:
            publisher.publish(message)
            rclpy.spin_once(node, timeout_sec=0.0)
        frames_published += 1
    cmd_vel_publish_done_mono_ns = time.monotonic_ns()
    subscription_match_proven = subscription_count > 0
    payload = {
        **result,
        # 现场 Orange Pi/FastDDS graph discovery 可能短时间仍报 0 个订阅者，但 bridge 已收到帧；
        # 所以发布成功和订阅匹配证明分开，避免 PC 键盘手控被 CLI 兜底拖到 HTTP 超时。
        "ok": frames_published > 0,
        "subscription_match_proven": subscription_match_proven,
        "subscription_match_required": require_subscription_match,
        "subscription_count": subscription_count,
        "frames_published": frames_published,
        "rclpy_context_status": context.get("prewarm_status", "ready_not_preheated"),
        "rclpy_ready_mono_ns": context.get("ready_mono_ns"),
        "publish_function_enter_mono_ns": function_enter_mono_ns,
        "cmd_vel_first_publish_mono_ns": cmd_vel_first_publish_mono_ns,
        "cmd_vel_publish_done_mono_ns": cmd_vel_publish_done_mono_ns,
        "context_ready_to_first_publish_ms": round((cmd_vel_first_publish_mono_ns - int(context.get("ready_mono_ns") or cmd_vel_first_publish_mono_ns)) / 1_000_000, 6),
        "publish_call_to_done_ms": round((cmd_vel_publish_done_mono_ns - cmd_vel_first_publish_mono_ns) / 1_000_000, 6),
        "elapsed_s": round(time.monotonic() - publish_started, 6),
        "wait_subscription_s": round(time.monotonic() - wait_started, 6),
    }
    if not subscription_match_proven:
        payload["warning"] = {
            "type": "cmd_vel_subscription_count_unproven",
            "message": "published /cmd_vel frames, but DDS graph did not prove a matched subscription before publish",
        }
    return payload


def publish_ros_cmd_vel_cli_burst(
    linear_x: float,
    angular_z: float,
    *,
    hold_s: float,
    rate_hz: float = ROS_CMD_VEL_BURST_RATE_HZ,
    timeout_s: float = 10.0,
) -> dict[str, Any]:
    """CLI 回退路径；比单帧 --once 更可靠，但只作为 ROS 环境没进进程时的兜底。"""
    linear_x = round(float(linear_x), 6)
    angular_z = round(float(angular_z), 6)
    hold_s = max(float(hold_s), 0.0)
    rate_hz = max(float(rate_hz), 1.0)
    times = max(1, int(math.ceil(max(hold_s, 1.0 / rate_hz) * rate_hz)))
    message = _ros_cmd_vel_message(linear_x, angular_z)
    setup_script = (
        "set +u; "
        # 现场 Orange Pi 的 /dev/shm 里存在 FastDDS 历史锁文件；关闭 SHM 可避免 ros2 CLI 建 publisher 卡死。
        "export RMW_FASTRTPS_USE_SHM=0; "
        f"source {shlex.quote(DEFAULT_ROS_SETUP_PATH)}; "
        f"if [ -f {shlex.quote(DEFAULT_ONBOARD_SETUP_PATH)} ]; then source {shlex.quote(DEFAULT_ONBOARD_SETUP_PATH)}; fi; "
        "set -u; "
        "RMW_FASTRTPS_USE_SHM=0 ros2 topic pub "
        f"--times {times} --rate {rate_hz:.3f} --wait-matching-subscriptions 1 "
        f"{shlex.quote(ROS_CMD_VEL_TOPIC)} geometry_msgs/msg/Twist "
        f"{shlex.quote(message)}"
    )
    result: dict[str, Any] = {
        "ok": False,
        "mode": "ros_cmd_vel_once",
        "publish_backend": "ros2_cli_burst",
        "topic": ROS_CMD_VEL_TOPIC,
        "message_type": "geometry_msgs/msg/Twist",
        "linear_x": linear_x,
        "angular_z": angular_z,
        "hold_s": round(hold_s, 6),
        "rate_hz": rate_hz,
        "frames_requested": times,
        "argv": ["bash", "-lc", setup_script],
    }
    try:
        completed = subprocess.run(  # noqa: S603 - 命令内容由固定 topic/type 和限速数值组成。
            result["argv"],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001 - ROS CLI 不可用时必须结构化 fail-closed。
        result["error"] = compact_error(exc)
        return result
    result.update(
        {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout_preview": completed.stdout[-800:],
            "stderr_preview": completed.stderr[-800:],
        }
    )
    if completed.returncode != 0:
        result["error"] = {
            "type": "ros_cmd_vel_publish_failed",
            "message": (completed.stderr or completed.stdout or f"ros2 topic pub exited {completed.returncode}")[-300:],
        }
    return result


def publish_ros_cmd_vel_once(linear_x: float, angular_z: float, *, timeout_s: float = 10.0) -> dict[str, Any]:
    """兼容旧调用：优先进程内发一帧，失败再走 CLI burst。"""
    primary = publish_ros_cmd_vel_inprocess_burst(linear_x, angular_z, hold_s=1.0 / ROS_CMD_VEL_BURST_RATE_HZ)
    if primary.get("ok"):
        return primary
    fallback = publish_ros_cmd_vel_cli_burst(
        linear_x,
        angular_z,
        hold_s=1.0 / ROS_CMD_VEL_BURST_RATE_HZ,
        timeout_s=timeout_s,
    )
    fallback["primary_error"] = primary.get("error")
    return fallback


def manual_motion_ros_cmd_vel_transaction(
    *,
    port: str,
    baudrate: int,
    command: dict[str, Any],
    pulse_ms: int,
) -> dict[str, Any]:
    """ROS 模式手控走 /cmd_vel 到 esp32_bridge，不直接打开 /dev/ttyS5。"""
    linear_x = finite_feedback_number(command.get("X")) or 0.0
    angular_z = finite_feedback_number(command.get("Z")) or 0.0
    command_result = publish_ros_cmd_vel_inprocess_burst(linear_x, angular_z, hold_s=max(pulse_ms / 1000.0, 0.0))
    if not command_result.get("ok"):
        command_result = publish_ros_cmd_vel_cli_burst(linear_x, angular_z, hold_s=max(pulse_ms / 1000.0, 0.0))
    stop_result = publish_ros_cmd_vel_inprocess_burst(0.0, 0.0, hold_s=ROS_CMD_VEL_STOP_HOLD_S)
    if not stop_result.get("ok"):
        stop_result = publish_ros_cmd_vel_cli_burst(0.0, 0.0, hold_s=ROS_CMD_VEL_STOP_HOLD_S)
    return {
        "mode": "ros_cmd_vel_bridge",
        "command_result": command_result,
        "stop_result": stop_result,
        "feedback_during_motion": skipped_manual_feedback_payload(
            port,
            baudrate,
            "ros_cmd_vel_path_uses_bridge_feedback_not_direct_uart",
        ),
        "feedback_after_stop": skipped_manual_feedback_payload(
            port,
            baudrate,
            "ros_cmd_vel_path_uses_bridge_feedback_not_direct_uart",
        ),
        "serial_session_error": None,
        "blocked_base_uart": port,
    }


def manual_motion_serial_transaction(
    *,
    port: str,
    baudrate: int,
    command: dict[str, Any],
    stop_commands: list[dict[str, Any]],
    pulse_ms: int,
    motion_read_timeout_s: float,
    motion_read_window_s: float,
    after_stop_read_timeout_s: float,
    after_stop_read_window_s: float,
) -> dict[str, Any]:
    """同一串口会话内完成点动、运动中 T130、stop、停车后 T130，用于排除会话切换误差。"""
    serial_module, import_error = load_serial_module()
    serial_open: dict[str, Any] = {"ok": False, "port": port, "baudrate": baudrate, "timeout_s": motion_read_timeout_s}
    input_reset: dict[str, Any] = {"attempted": False, "ok": False}
    command_write: dict[str, Any] = {"ok": False, "command": command}
    stop_plan = stop_commands or [{"T": 1, "L": 0, "R": 0}]
    stop_write: dict[str, Any] = {"ok": False, "command": stop_plan[0]}
    additional_stop_writes: list[dict[str, Any]] = []
    motion_feedback_write: dict[str, Any] = {"ok": False, "command": BASE_FEEDBACK_REQUEST_COMMAND}
    after_stop_feedback_write: dict[str, Any] = {"ok": False, "command": BASE_FEEDBACK_REQUEST_COMMAND}
    serial_obj = None
    started_monotonic = time.monotonic()

    if serial_module is None:
        error = {"type": "pyserial_unavailable", "message": import_error or "missing"}
        command_write["error"] = error
        return {
            "serial_open": {**serial_open, "error": error},
            "input_reset": input_reset,
            "command_result": command_write,
            "stop_result": stop_write,
            "additional_stop_results": additional_stop_writes,
            "feedback_during_motion": skipped_manual_feedback_payload(port, baudrate, "pyserial_unavailable"),
            "feedback_after_stop": skipped_manual_feedback_payload(port, baudrate, "pyserial_unavailable"),
            "serial_session_error": error,
        }

    try:
        serial_obj = serial_module.Serial(port=port, baudrate=baudrate, timeout=motion_read_timeout_s)
        serial_open["ok"] = True
    except Exception as exc:  # noqa: BLE001 - 打不开串口时仍返回完整 fail-closed 形状。
        error = compact_error(exc)
        command_write["error"] = error
        return {
            "serial_open": {**serial_open, "error": error},
            "input_reset": input_reset,
            "command_result": command_write,
            "stop_result": stop_write,
            "additional_stop_results": additional_stop_writes,
            "feedback_during_motion": skipped_manual_feedback_payload(port, baudrate, "serial_not_opened"),
            "feedback_after_stop": skipped_manual_feedback_payload(port, baudrate, "serial_not_opened"),
            "serial_session_error": error,
        }

    try:
        if hasattr(serial_obj, "reset_input_buffer"):
            input_reset["attempted"] = True
            try:
                serial_obj.reset_input_buffer()
                input_reset["ok"] = True
            except Exception as exc:  # noqa: BLE001 - 清缓冲失败不阻止停车兜底。
                input_reset["error"] = compact_error(exc)

        command_write = write_json_to_open_serial(serial_obj, command)
        if command_write.get("ok"):
            # 运动反馈必须在 stop 前请求；同一串口会话能看见命令 echo、T130 和 T1001 的相对顺序。
            motion_feedback_write = write_json_to_open_serial(serial_obj, BASE_FEEDBACK_REQUEST_COMMAND)
            motion_read = read_serial_json_window(serial_obj, motion_read_window_s) if motion_feedback_write.get("ok") else {
                "read_line_count": 0,
                "parsed_json_count": 0,
                "invalid_json_count": 0,
                "observed_feedback_types": [],
                "t1001_feedback_frames": [],
                "compact_frames": [],
                "read_error": motion_feedback_write.get("error"),
            }
            feedback_during_motion = build_feedback_payload_from_open_serial_read(
                port=port,
                baudrate=baudrate,
                read_timeout_s=motion_read_timeout_s,
                read_window_s=motion_read_window_s,
                serial_open=serial_open,
                serial_write=motion_feedback_write,
                read_summary=motion_read,
            )
        else:
            feedback_during_motion = skipped_manual_feedback_payload(port, baudrate, "motion_command_write_failed")

        remaining_s = max(pulse_ms / 1000.0 - (time.monotonic() - started_monotonic), 0.0)
        if remaining_s > 0:
            time.sleep(remaining_s)
        stop_write = write_json_to_open_serial(serial_obj, stop_plan[0])
        for stop_command in stop_plan[1:]:
            additional_stop_writes.append(write_json_to_open_serial(serial_obj, stop_command))
        if stop_write.get("ok"):
            serial_obj.timeout = after_stop_read_timeout_s
            after_stop_feedback_write = write_json_to_open_serial(serial_obj, BASE_FEEDBACK_REQUEST_COMMAND)
            after_read = read_serial_json_window(serial_obj, after_stop_read_window_s) if after_stop_feedback_write.get("ok") else {
                "read_line_count": 0,
                "parsed_json_count": 0,
                "invalid_json_count": 0,
                "observed_feedback_types": [],
                "t1001_feedback_frames": [],
                "compact_frames": [],
                "read_error": after_stop_feedback_write.get("error"),
            }
            feedback_after_stop = build_feedback_payload_from_open_serial_read(
                port=port,
                baudrate=baudrate,
                read_timeout_s=after_stop_read_timeout_s,
                read_window_s=after_stop_read_window_s,
                serial_open=serial_open,
                serial_write=after_stop_feedback_write,
                read_summary=after_read,
            )
        else:
            feedback_after_stop = skipped_manual_feedback_payload(port, baudrate, "stop_write_failed")
    finally:
        if serial_obj is not None:
            try:
                serial_obj.close()
            except Exception:
                pass

    return {
        "serial_open": serial_open,
        "input_reset": input_reset,
        "command_result": command_write,
        "motion_feedback_request_result": motion_feedback_write,
        "stop_result": stop_write,
        "additional_stop_results": additional_stop_writes,
        "after_stop_feedback_request_result": after_stop_feedback_write,
        "feedback_during_motion": feedback_during_motion,
        "feedback_after_stop": feedback_after_stop,
        "serial_session_error": None,
    }


def manual_motion_serial_write_only_transaction(
    *,
    port: str,
    baudrate: int,
    command: dict[str, Any],
    stop_commands: list[dict[str, Any]],
    pulse_ms: int,
    mode: str = "serial_write_only_bridge_debug",
    feedback_reason: str = "serial_write_only_uses_bridge_feedback_debug_log",
    feedback_source: str = "esp32_bridge_feedback_debug_log",
) -> dict[str, Any]:
    """只写低速点动和停车命令，不抢 esp32_bridge 正在读取的 UART 反馈。"""
    serial_module, import_error = load_serial_module()
    serial_open: dict[str, Any] = {"ok": False, "port": port, "baudrate": baudrate, "timeout_s": 0.05}
    input_reset: dict[str, Any] = {"attempted": False, "ok": False, "skipped_reason": "preserve_bridge_reader_buffer"}
    command_write: dict[str, Any] = {"ok": False, "command": command}
    stop_plan = stop_commands or [{"T": 1, "L": 0, "R": 0}]
    stop_write: dict[str, Any] = {"ok": False, "command": stop_plan[0]}
    additional_stop_writes: list[dict[str, Any]] = []
    serial_obj = None
    started_monotonic = time.monotonic()

    if serial_module is None:
        error = {"type": "pyserial_unavailable", "message": import_error or "missing"}
        command_write["error"] = error
        return {
            "mode": mode,
            "serial_open": {**serial_open, "error": error},
            "input_reset": input_reset,
            "command_result": command_write,
            "stop_result": stop_write,
            "additional_stop_results": additional_stop_writes,
            "feedback_during_motion": skipped_manual_feedback_payload(port, baudrate, "pyserial_unavailable"),
            "feedback_after_stop": skipped_manual_feedback_payload(port, baudrate, "pyserial_unavailable"),
            "serial_session_error": error,
        }

    try:
        serial_obj = serial_module.Serial(port=port, baudrate=baudrate, timeout=0.05)
        serial_open["ok"] = True
        command_write = write_json_to_open_serial(serial_obj, command)
        append_upper_manual_command_debug_line(command, command_write, transaction_mode=mode)
        remaining_s = max(pulse_ms / 1000.0 - (time.monotonic() - started_monotonic), 0.0)
        if remaining_s > 0:
            time.sleep(remaining_s)
        stop_write = write_json_to_open_serial(serial_obj, stop_plan[0])
        append_upper_manual_command_debug_line(stop_plan[0], stop_write, transaction_mode=mode)
        for stop_command in stop_plan[1:]:
            additional_stop_write = write_json_to_open_serial(serial_obj, stop_command)
            append_upper_manual_command_debug_line(stop_command, additional_stop_write, transaction_mode=mode)
            additional_stop_writes.append(additional_stop_write)
    except Exception as exc:  # noqa: BLE001 - 现场串口错误必须结构化返回，stop 证据也要保留。
        error = compact_error(exc)
        if not command_write.get("ok"):
            command_write["error"] = error
        if not stop_write.get("ok"):
            stop_write["error"] = error
        return {
            "mode": mode,
            "serial_open": {**serial_open, "error": error},
            "input_reset": input_reset,
            "command_result": command_write,
            "stop_result": stop_write,
            "additional_stop_results": additional_stop_writes,
            "feedback_during_motion": skipped_manual_feedback_payload(port, baudrate, "serial_write_only_error"),
            "feedback_after_stop": skipped_manual_feedback_payload(port, baudrate, "serial_write_only_error"),
            "serial_session_error": error,
        }
    finally:
        if serial_obj is not None:
            try:
                serial_obj.close()
            except Exception:
                pass

    return {
        "mode": mode,
        "serial_open": serial_open,
        "input_reset": input_reset,
        "command_result": command_write,
        "stop_result": stop_write,
        "additional_stop_results": additional_stop_writes,
        "feedback_during_motion": skipped_manual_feedback_payload(port, baudrate, feedback_reason),
        "feedback_after_stop": skipped_manual_feedback_payload(port, baudrate, feedback_reason),
        "serial_session_error": None,
        "feedback_source": feedback_source,
    }


def manual_motion_ros_cmd_vel_hold_refresh_transaction(
    *,
    port: str,
    baudrate: int,
    command: dict[str, Any],
) -> dict[str, Any]:
    """键盘 hold 刷新只发布当前速度帧；停车交给 release stop 或 watchdog，避免每拍末尾主动刹车。"""
    linear_x = finite_feedback_number(command.get("X")) or 0.0
    angular_z = finite_feedback_number(command.get("Z")) or 0.0
    command_result = publish_ros_cmd_vel_inprocess_burst(
        linear_x,
        angular_z,
        hold_s=1.0 / ROS_CMD_VEL_BURST_RATE_HZ,
        wait_subscription_s=0.0,
        require_subscription_match=True,
    )
    # 键盘 hot path 若预热失败就结构化 fail-closed；秒级 CLI 只能保留给旧的非 hold 接口。
    command_result["cli_fallback_attempted"] = False
    command_result["latency_pass_eligible"] = bool(
        command_result.get("ok")
        and command_result.get("publish_backend") == "rclpy_inprocess_burst"
        and command_result.get("rclpy_context_status") == "ready"
    )
    stop_result = {
        "ok": False,
        "skipped_reason": "realtime_hold_stop_deferred_to_release_or_watchdog",
        "command": {"T": 13, "X": 0, "Z": 0},
    }
    return {
        "mode": "ros_cmd_vel_realtime_hold",
        "command_result": command_result,
        "stop_result": stop_result,
        "feedback_during_motion": skipped_manual_feedback_payload(port, baudrate, "realtime_hold_feedback_skipped_until_release_readback"),
        "feedback_after_stop": skipped_manual_feedback_payload(port, baudrate, "realtime_hold_feedback_skipped_until_release_readback"),
        "serial_session_error": None,
        "feedback_source": "keyboard_release_readback",
    }


def manual_motion_serial_hold_refresh_transaction(
    *,
    port: str,
    baudrate: int,
    command: dict[str, Any],
    stop_commands: list[dict[str, Any]],
) -> dict[str, Any]:
    """串口 hold 刷新只写运动命令，不 sleep、不写 stop；watchdog 到期再统一停车。"""
    serial_module, import_error = load_serial_module()
    serial_open: dict[str, Any] = {"ok": False, "port": port, "baudrate": baudrate, "timeout_s": 0.05}
    command_write: dict[str, Any] = {"ok": False, "command": command}
    if serial_module is None:
        error = {"type": "pyserial_unavailable", "message": import_error or "missing"}
        command_write["error"] = error
        return {
            "mode": "serial_write_only_realtime_hold",
            "serial_open": {**serial_open, "error": error},
            "input_reset": {"attempted": False, "ok": False, "skipped_reason": "preserve_bridge_reader_buffer"},
            "command_result": command_write,
            "stop_result": {"ok": False, "skipped_reason": "serial_not_opened", "command": (stop_commands or [{"T": 1, "L": 0, "R": 0}])[0]},
            "additional_stop_results": [],
            "feedback_during_motion": skipped_manual_feedback_payload(port, baudrate, "pyserial_unavailable"),
            "feedback_after_stop": skipped_manual_feedback_payload(port, baudrate, "pyserial_unavailable"),
            "serial_session_error": error,
            "feedback_source": "keyboard_release_readback",
        }
    serial_obj = None
    try:
        serial_obj = serial_module.Serial(port=port, baudrate=baudrate, timeout=0.05)
        serial_open["ok"] = True
        command_write = write_json_to_open_serial(serial_obj, command)
        append_upper_manual_command_debug_line(command, command_write, transaction_mode="serial_write_only_realtime_hold")
    except Exception as exc:  # noqa: BLE001 - hold 刷新失败也要结构化返回，watchdog/release 仍可停车。
        error = compact_error(exc)
        if not command_write.get("ok"):
            command_write["error"] = error
        return {
            "mode": "serial_write_only_realtime_hold",
            "serial_open": {**serial_open, "error": error},
            "input_reset": {"attempted": False, "ok": False, "skipped_reason": "preserve_bridge_reader_buffer"},
            "command_result": command_write,
            "stop_result": {"ok": False, "skipped_reason": "realtime_hold_stop_deferred_to_release_or_watchdog", "command": (stop_commands or [{"T": 1, "L": 0, "R": 0}])[0]},
            "additional_stop_results": [],
            "feedback_during_motion": skipped_manual_feedback_payload(port, baudrate, "serial_write_only_error"),
            "feedback_after_stop": skipped_manual_feedback_payload(port, baudrate, "serial_write_only_error"),
            "serial_session_error": error,
            "feedback_source": "keyboard_release_readback",
        }
    finally:
        if serial_obj is not None:
            try:
                serial_obj.close()
            except Exception:
                pass
    return {
        "mode": "serial_write_only_realtime_hold",
        "serial_open": serial_open,
        "input_reset": {"attempted": False, "ok": False, "skipped_reason": "preserve_bridge_reader_buffer"},
        "command_result": command_write,
        "stop_result": {"ok": False, "skipped_reason": "realtime_hold_stop_deferred_to_release_or_watchdog", "command": (stop_commands or [{"T": 1, "L": 0, "R": 0}])[0]},
        "additional_stop_results": [],
        "feedback_during_motion": skipped_manual_feedback_payload(port, baudrate, "realtime_hold_feedback_skipped_until_release_readback"),
        "feedback_after_stop": skipped_manual_feedback_payload(port, baudrate, "realtime_hold_feedback_skipped_until_release_readback"),
        "serial_session_error": None,
        "feedback_source": "keyboard_release_readback",
    }


def run_nav2_goal_execution_helper(
    *,
    artifact_path: str,
    goal_frame_id: str,
    goal_x: float,
    goal_y: float,
    goal_yaw: float,
    result_timeout_s: float,
    server_timeout_s: float,
    managed_runtime_opt_in: bool,
    managed_map_yaml: str,
    managed_startup_s: float,
    managed_ready_timeout_s: float,
    base_command_mode: str,
) -> dict[str, Any]:
    """运行 bounded NavigateToPose helper；超时由 helper cancel，外层保留结构化结果。"""
    script_path = Path(__file__).resolve().with_name("o11_nav2_goal_execution_proof.py")
    helper_argv = [
        sys.executable,
        str(script_path),
        "--output",
        artifact_path,
        "--goal-frame-id",
        goal_frame_id,
        "--goal-x",
        str(goal_x),
        "--goal-y",
        str(goal_y),
        "--goal-yaw",
        str(goal_yaw),
        "--server-timeout-s",
        str(server_timeout_s),
        "--result-timeout-s",
        str(result_timeout_s),
        "--base-command-mode",
        base_command_mode,
    ]
    if managed_runtime_opt_in:
        helper_argv.extend(
            [
                "--managed-runtime-opt-in",
                "--managed-map-yaml",
                managed_map_yaml,
                "--managed-startup-s",
                str(managed_startup_s),
                "--managed-ready-timeout-s",
                str(managed_ready_timeout_s),
            ]
        )
    ros_setup_parts = [
        "source /opt/ros/humble/setup.bash",
        f"if [ -f {shlex.quote(str(Path(DEFAULT_ONBOARD_WORKDIR) / 'install' / 'setup.bash'))} ]; then source {shlex.quote(str(Path(DEFAULT_ONBOARD_WORKDIR) / 'install' / 'setup.bash'))}; fi",
    ]
    helper_command = " && ".join(ros_setup_parts + [shlex.join(helper_argv)])
    process_timeout_s = min(max(server_timeout_s + result_timeout_s + managed_startup_s + managed_ready_timeout_s + 15.0, 20.0), 140.0)
    started_ms = now_ms()
    try:
        completed = run_helper_bash_process_group(
            helper_command,
            process_timeout_s,
            DEFAULT_ONBOARD_WORKDIR,
            cleanup_residuals=managed_runtime_opt_in,
        )
        return {
            "mode": "o11_nav2_goal_execution_helper",
            "executed": True,
            "ok": bool(completed.get("returncode") == 0),
            "returncode": completed.get("returncode"),
            "argv": ["bash", "-lc", helper_command],
            "helper_argv": helper_argv,
            "elapsed_ms": now_ms() - started_ms,
            "process_timeout_s": process_timeout_s,
            "timed_out": bool(completed.get("timed_out")),
            "stdout_preview": str(completed.get("stdout") or "")[-4000:],
            "stderr_preview": str(completed.get("stderr") or "")[-4000:],
            "helper_process_group": completed.get("process_group"),
            "helper_cleanup_result": completed.get("cleanup_result"),
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    except Exception as exc:  # noqa: BLE001 - helper 启动失败也要结构化返回。
        return {
            "mode": "o11_nav2_goal_execution_helper",
            "executed": False,
            "ok": False,
            "argv": ["bash", "-lc", helper_command],
            "helper_argv": helper_argv,
            "elapsed_ms": now_ms() - started_ms,
            "process_timeout_s": process_timeout_s,
            "error": compact_error(exc),
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }


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
    t1001_feedback_frames: list[dict[str, Any]],
    t1001_feedback_status: str,
) -> dict[str, Any]:
    """统一反馈请求输出；即使看到 T=1001，也只能作为材料而不是 HIL pass。"""
    t1001_observed = BASE_FEEDBACK_ID in observed_feedback_types
    wheel_summary = wheel_feedback_summary_from_frames(t1001_feedback_frames)
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
        "t1001_feedback_frames": t1001_feedback_frames,
        "t1001_feedback_status": t1001_feedback_status,
        "wheel_feedback_summary": wheel_summary,
        "wheel_feedback_nonzero_observed": wheel_summary["lr_nonzero_observed"],
        "wheel_feedback_lr_nonzero_proven": wheel_summary["lr_nonzero_observed"],
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
    t1001_feedback_frames: list[dict[str, Any]] = []
    for index, sample in enumerate(samples, start=1):
        observed_types = [
            item for item in sample.get("observed_feedback_types", [])
            if isinstance(item, int)
        ]
        observed_type_set.update(observed_types)
        sample_frames = [
            item for item in sample.get("t1001_feedback_frames", [])
            if isinstance(item, dict)
        ]
        t1001_feedback_frames.extend(sample_frames)
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
                "t1001_feedback_frame_count": len(sample_frames),
                "t1001_feedback_status": sample.get("t1001_feedback_status"),
                "feedback_ack": sample.get("feedback_ack"),
                "wheel_feedback_summary": sample.get("wheel_feedback_summary"),
                "safe_to_control": False,
                "sends_motion_commands": False,
                "robot_control_executed": False,
                "delivery_success": False,
                "hil_pass": False,
            }
        )
    all_samples_observed = bool(samples) and t1001_observed_count == len(samples)
    partial_samples_observed = 0 < t1001_observed_count < len(samples)
    wheel_summary = wheel_feedback_summary_from_frames(t1001_feedback_frames)
    imu_delta_summary = imu_attitude_delta_summary_from_frames(t1001_feedback_frames)
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
        "t1001_feedback_frames": t1001_feedback_frames,
        "t1001_observed_count": t1001_observed_count,
        "observed_feedback_types": sorted(observed_type_set),
        "all_samples_observed_t1001": all_samples_observed,
        "partial_samples_observed_t1001": partial_samples_observed,
        "wheel_feedback_summary": wheel_summary,
        "wheel_feedback_nonzero_observed": wheel_summary["lr_nonzero_observed"],
        "wheel_feedback_lr_nonzero_proven": wheel_summary["lr_nonzero_observed"],
        "imu_attitude_delta_summary": imu_delta_summary,
        "imu_attitude_delta_observed": imu_delta_summary["imu_attitude_delta_observed"],
        "motion_signal_observed": bool(
            wheel_summary["lr_nonzero_observed"]
            or imu_delta_summary["imu_attitude_delta_observed"]
        ),
        "motion_signal_source": (
            "wheel_feedback_lr"
            if wheel_summary["lr_nonzero_observed"]
            else "imu_attitude_delta"
            if imu_delta_summary["imu_attitude_delta_observed"]
            else "not_observed"
        ),
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


def skipped_base_status_feedback_payload(port: str, baudrate: int, reason: str) -> dict[str, Any]:
    """GET status 默认不直接抢 UART；需要 T=130 时走显式采样接口。"""
    if reason == "fresh_bridge_feedback_debug_log_available":
        ack_reason = "direct T=130 feedback request skipped because esp32_bridge feedback debug log is fresh"
    elif reason == "base_status_get_lightweight_no_direct_t130":
        ack_reason = "direct T=130 feedback request skipped for lightweight GET /api/base/status; use /api/base/feedback-request or /api/base/feedback-samples for explicit sampling"
    else:
        ack_reason = f"direct T=130 feedback request skipped: {reason}"
    return {
        "schema": f"{SCHEMA}.base_status_feedback_skipped",
        "generated_at_ms": now_ms(),
        "vendor_sources": VENDOR_SOURCES,
        "port": port,
        "baudrate": baudrate,
        "request": {
            "method": "GET",
            "endpoint": "/api/base/status",
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
        "t1001_feedback_frames": [],
        "t1001_feedback_status": reason,
        "feedback_ack": {
            "t1001_observed": False,
            "robot_ack_connected": False,
            "reason": ack_reason,
        },
        "wheel_feedback_summary": {},
        "wheel_feedback_nonzero_observed": False,
        "wheel_feedback_lr_nonzero_proven": False,
        "safe_to_control": False,
        "sends_commands": False,
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
    stop_commands = stop_commands_for_mode("ros")
    ros_stop_result = publish_ros_cmd_vel_inprocess_burst(0.0, 0.0, hold_s=ROS_CMD_VEL_STOP_HOLD_S, wait_subscription_s=0.15)
    if not ros_stop_result.get("ok"):
        ros_stop_result = publish_ros_cmd_vel_cli_burst(0.0, 0.0, hold_s=ROS_CMD_VEL_STOP_HOLD_S, timeout_s=2.0)
    serial_stop_results = [write_serial_json(port, baudrate, command) for command in stop_commands]
    stop_result = serial_stop_results[0] if serial_stop_results else {"ok": False, "error": {"type": "stop_plan_empty"}}
    stop_ok = bool(ros_stop_result.get("ok")) or any(bool(result.get("ok")) for result in serial_stop_results)
    return {
        "schema": f"{SCHEMA}.base_stop_result",
        "generated_at_ms": now_ms(),
        "stop_result": stop_result,
        "ros_stop_result": ros_stop_result,
        "serial_stop_results": serial_stop_results,
        "serial_write_failures": [result.get("error") for result in serial_stop_results if not result.get("ok")],
        "stop_covers_command_modes": ["ros", "speed", "pwm"],
        "feedback_ack": t1001_boundary("stop write does not prove T=1001 or ACK"),
        "safe_to_control": False,
        "sends_commands": True,
        "robot_control_executed": stop_ok,
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


def safe_camera_probe_request(body: dict[str, Any] | None = None) -> dict[str, Any]:
    """相机首帧 probe 只接受短白名单参数，避免 HTTP body 变成任意 argv。"""
    payload = body if isinstance(body, dict) else {}
    device = payload.get("device", "/dev/video1")
    if not isinstance(device, str) or not re.fullmatch(r"/dev/video[0-9]{1,2}", device):
        device = "/dev/video1"
    fourcc = payload.get("fourcc", "MJPG")
    if fourcc not in ("MJPG", "YUYV", None, ""):
        fourcc = "MJPG"
    width = int(payload.get("width", 640)) if str(payload.get("width", 640)).isdigit() else 640
    height = int(payload.get("height", 480)) if str(payload.get("height", 480)).isdigit() else 480
    fps = float(payload.get("fps", 15.0)) if isinstance(payload.get("fps", 15.0), (int, float)) else 15.0
    timeout_s = float(payload.get("timeout_s", 3.0)) if isinstance(payload.get("timeout_s", 3.0), (int, float)) else 3.0
    read_call_timeout_s = (
        float(payload.get("read_call_timeout_s", 4.0))
        if isinstance(payload.get("read_call_timeout_s", 4.0), (int, float))
        else 4.0
    )
    return {
        "device": device,
        "fourcc": fourcc or None,
        "width": min(max(width, 160), 1920),
        "height": min(max(height, 120), 1080),
        "fps": min(max(fps, 1.0), 30.0),
        "timeout_s": min(max(timeout_s, 0.5), 8.0),
        "read_call_timeout_s": min(max(read_call_timeout_s, 0.5), 8.0),
        "include_backend_smoke": bool(payload.get("include_backend_smoke") is True),
        "auto_format_fallback": bool(payload.get("auto_format_fallback") is True),
    }


def camera_probe_fallback_requests(request: dict[str, Any]) -> list[dict[str, Any]]:
    """生成快速格式 fallback；同一组参数去重，避免重复打开同一个失败组合。"""
    base = dict(request)
    if not request.get("auto_format_fallback") or request.get("include_backend_smoke"):
        return [base]
    # 现场 DV20 无帧时，640x480 阻塞 read 会吃掉全部预算；fallback 必须先覆盖低负载模式。
    quick_timeout = min(float(request["timeout_s"]), 1.2)
    quick_read_timeout = min(float(request["read_call_timeout_s"]), 1.2)
    candidates = [
        {"fourcc": request.get("fourcc"), "width": request["width"], "height": request["height"], "fps": request["fps"]},
        # 先跑低负载格式，确保 PC 12s 窗口里能证明“小分辨率也不出帧”。
        {"fourcc": "YUYV", "width": 320, "height": 240, "fps": 20.0},
        {"fourcc": "YUYV", "width": 320, "height": 240, "fps": 25.0},
        {"fourcc": "MJPG", "width": 160, "height": 120, "fps": 30.0},
        {"fourcc": "YUYV", "width": 160, "height": 120, "fps": 15.0},
        {"fourcc": "YUYV", "width": 160, "height": 120, "fps": 10.0},
        {"fourcc": "MJPG", "width": 480, "height": 320, "fps": 30.0},
        # DV20/UVC 在实板枚举里 MJPG 只暴露 30fps；probe 不能一直拿默认 15fps 去试。
        {"fourcc": "MJPG", "width": 640, "height": 480, "fps": 30.0},
        # YUYV 的离散 fps 与 MJPG 不同；按枚举值尝试，避免格式正确但帧率不兼容。
        {"fourcc": "YUYV", "width": 640, "height": 480, "fps": 22.0},
        {"fourcc": "MJPG", "width": 1280, "height": 720, "fps": 30.0},
        {"fourcc": None, "width": 640, "height": 480, "fps": request["fps"]},
    ]
    seen: set[tuple[Any, Any, Any, Any]] = set()
    requests: list[dict[str, Any]] = []
    for candidate in candidates:
        key = (candidate["fourcc"], candidate["width"], candidate["height"], candidate["fps"])
        if key in seen:
            continue
        seen.add(key)
        next_request = dict(base)
        next_request.update(candidate)
        next_request["timeout_s"] = quick_timeout
        next_request["read_call_timeout_s"] = quick_read_timeout
        next_request["include_backend_smoke"] = False
        requests.append(next_request)
    return requests


def camera_probe_command(script_path: Path, request: dict[str, Any], sample_path: Path) -> list[str]:
    """把白名单 probe request 转成固定脚本 argv，禁止 HTTP body 影响任意命令。"""
    command = [
        sys.executable,
        str(script_path),
        "--device",
        request["device"],
        "--width",
        str(request["width"]),
        "--height",
        str(request["height"]),
        "--fps",
        str(request["fps"]),
        "--timeout-s",
        str(request["timeout_s"]),
        "--read-call-timeout-s",
        str(request["read_call_timeout_s"]),
        "--sample-path",
        str(sample_path),
    ]
    if request["fourcc"]:
        command.extend(["--fourcc", request["fourcc"]])
    if request["include_backend_smoke"]:
        command.append("--include-backend-smoke")
    return command


async def run_camera_probe_attempt(
    script_path: Path,
    request: dict[str, Any],
    sample_path: Path,
    max_process_timeout_s: float | None = None,
) -> dict[str, Any]:
    """执行一次固定首帧探针；失败也返回结构化 payload，供 fallback 汇总。"""
    command = camera_probe_command(script_path, request, sample_path)

    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=str(Path(__file__).resolve().parents[1]),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        # backend smoke 现在覆盖 mmap、userptr、ffmpeg 和设备自报低负载模式；深度探针预算要能容纳完整矩阵。
        base_process_timeout_s = request["read_call_timeout_s"] + (60.0 if request["include_backend_smoke"] else 1.5)
        process_timeout_s = base_process_timeout_s if max_process_timeout_s is None else min(
            base_process_timeout_s,
            max(0.5, max_process_timeout_s),
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=process_timeout_s)
    except asyncio.TimeoutError:
        try:
            if process.returncode is None:
                # 子进程可能刚好在超时边界退出；这里吞掉竞争态，保证 API 返回诊断 JSON。
                process.kill()
        except ProcessLookupError:
            pass
        await process.communicate()
        return {
            "status": "probe_process_timeout",
            "probe_request": request,
            "probe_payload": {"status": "probe_process_timeout"},
            "probe_returncode": None,
            "process_timeout_s": process_timeout_s,
            "stderr_preview": "process_timeout",
        }

    stdout_text = stdout.decode("utf-8", errors="replace").strip()
    stderr_text = stderr.decode("utf-8", errors="replace").strip()
    try:
        probe_payload = json.loads(stdout_text.splitlines()[-1]) if stdout_text else {}
    except json.JSONDecodeError:
        probe_payload = {"status": "bad_probe_json", "stdout_preview": stdout_text[:400]}
    if not isinstance(probe_payload, dict):
        probe_payload = {"status": "probe_json_not_object"}

    status = str(probe_payload.get("status", "unknown"))
    return {
        "status": status,
        "probe_request": request,
        "probe_payload": probe_payload,
        "probe_returncode": process.returncode,
        "process_timeout_s": process_timeout_s,
        "stderr_preview": stderr_text[:400],
    }


def camera_probe_attempt_summary(attempt: dict[str, Any]) -> dict[str, Any]:
    """fallback 尝试只暴露短事实，避免把完整 stdout/stderr 塞进普通 API。"""
    payload = attempt.get("probe_payload") if isinstance(attempt.get("probe_payload"), dict) else {}
    request = attempt.get("probe_request") if isinstance(attempt.get("probe_request"), dict) else {}
    return {
        "status": attempt.get("status") or payload.get("status") or "unknown",
        "fourcc": payload.get("requested_fourcc", request.get("fourcc")),
        "width": payload.get("requested_width", request.get("width")),
        "height": payload.get("requested_height", request.get("height")),
        "fps": payload.get("requested_fps", request.get("fps")),
        "open_ok": bool(payload.get("open_ok")),
        "read_ok": bool(payload.get("read_ok")),
        "failure_reason": payload.get("failure_reason") or "none",
        "elapsed_ms": payload.get("elapsed_ms"),
    }


async def run_camera_first_frame_probe(body: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    """执行入仓首帧探针；该路径只读 camera，不导入 ROS2、不打开底盘串口。"""
    request = safe_camera_probe_request(body)
    script_path = Path(__file__).with_name("camera_first_frame_probe.py")
    started_ms = now_ms()
    started_monotonic = time.monotonic()
    # PC 代理 12s quick probe 需要拿到低带宽矩阵结论；上位机预算略短于 PC timeout。
    # 深度相机探针只由显式 include_backend_smoke 触发，给足预算换来可落地的“软件采集已穷尽”证据。
    total_budget_s = 68.0 if request.get("include_backend_smoke") else 11.0
    sample_root = Path(__file__).resolve().parents[1] / "runtime" / "camera"
    if not script_path.exists():
        return 503, {
            "schema": f"{SCHEMA}.camera_first_frame_probe_proxy",
            "status": "probe_script_missing",
            "probe_request": request,
            "script_path": str(script_path),
            **proof_flags(),
            "opens_serial": False,
            "sends_motion_commands": False,
        }

    attempts: list[dict[str, Any]] = []
    for index, attempt_request in enumerate(camera_probe_fallback_requests(request)):
        elapsed_s = time.monotonic() - started_monotonic
        remaining_s = total_budget_s - elapsed_s
        if remaining_s <= 0.4:
            # UVC 无帧时不能让 fallback 矩阵把 HTTP 请求拖到一分钟；保留已尝试材料后快速返回。
            attempts.append({
                "status": "probe_total_timeout",
                "probe_request": attempt_request,
                "probe_payload": {"status": "probe_total_timeout", "failure_reason": "probe_total_timeout"},
                "probe_returncode": None,
                "process_timeout_s": 0.0,
                "stderr_preview": "probe_total_timeout",
            })
            break
        sample_path = sample_root / f"first_frame_probe_{started_ms}_{index}.jpg"
        bounded_attempt_request = dict(attempt_request)
        if not bounded_attempt_request.get("include_backend_smoke"):
            # 每次尝试都按剩余总预算收缩读帧窗口，避免最后一个格式独占整个剩余时间。
            bounded_window_s = max(0.5, min(float(bounded_attempt_request["read_call_timeout_s"]), remaining_s - 0.3))
            bounded_attempt_request["timeout_s"] = min(float(bounded_attempt_request["timeout_s"]), bounded_window_s)
            bounded_attempt_request["read_call_timeout_s"] = bounded_window_s
        attempt = await run_camera_probe_attempt(script_path, bounded_attempt_request, sample_path, remaining_s)
        attempts.append(attempt)
        if attempt.get("status") == "frame_read":
            break

    selected = next((attempt for attempt in attempts if attempt.get("status") == "frame_read"), attempts[-1])
    probe_payload = selected.get("probe_payload") if isinstance(selected.get("probe_payload"), dict) else {}
    status = str(selected.get("status") or probe_payload.get("status") or "unknown")
    http_status = 200 if selected.get("probe_returncode") == 0 and status == "frame_read" else 503
    fallback_summaries = [camera_probe_attempt_summary(attempt) for attempt in attempts]
    low_bandwidth_attempts = [
        item for item in fallback_summaries
        if int(item.get("width") or 9999) <= 160 and int(item.get("height") or 9999) <= 120
    ]
    low_bandwidth_min_area = min(
        (int(item.get("width") or 0) * int(item.get("height") or 0) for item in low_bandwidth_attempts),
        default=0,
    )
    low_bandwidth_min_size = next(
        (
            f"{item.get('width')}x{item.get('height')}"
            for item in low_bandwidth_attempts
            if int(item.get("width") or 0) * int(item.get("height") or 0) == low_bandwidth_min_area
        ),
        "none",
    )
    return http_status, {
        "schema": f"{SCHEMA}.camera_first_frame_probe_proxy",
        "status": status,
        "generated_at_ms": now_ms(),
        "probe_request": selected.get("probe_request", request),
        "probe_payload": probe_payload,
        "probe_returncode": selected.get("probe_returncode"),
        "stderr_preview": str(selected.get("stderr_preview") or "")[:400],
        "auto_format_fallback": bool(request.get("auto_format_fallback")),
        "fallback_attempts": fallback_summaries,
        "low_bandwidth_fallback_attempted": bool(low_bandwidth_attempts),
        "low_bandwidth_fallback_min_size": low_bandwidth_min_size,
        "elapsed_ms": now_ms() - started_ms,
        "upper_api_proxy": True,
        **proof_flags(),
        "opens_serial": False,
        "sends_motion_commands": False,
        "robot_control_executed": False,
    }


def safe_camera_usb_recovery_request(body: dict[str, Any] | None = None) -> dict[str, Any]:
    """USB 恢复只能接受少量白名单参数，不能让 PC body 变成任意 root 命令。"""
    payload = body if isinstance(body, dict) else {}
    device = payload.get("device", "/dev/video1")
    if not isinstance(device, str) or not re.fullmatch(r"/dev/video[0-9]{1,2}", device):
        device = "/dev/video1"
    return {
        "device": device,
        "skip_service": bool(payload.get("skip_service") is True),
        "skip_reauthorize": bool(payload.get("skip_reauthorize") is True),
        "skip_audio_unbind": bool(payload.get("skip_audio_unbind") is True),
        "skip_uvc_quirks_reset": bool(payload.get("skip_uvc_quirks_reset") is True),
        "skip_control_reset": bool(payload.get("skip_control_reset") is True),
        "reload_uvc_module": bool(payload.get("reload_uvc_module") is True),
        "usbreset_device": bool(payload.get("usbreset_device") is True),
    }


def camera_usb_recovery_command(script_path: Path, request: dict[str, Any]) -> list[str]:
    """固定恢复脚本 argv；恢复动作只作用于相机 USB，不触碰底盘或 ROS graph。"""
    command = [
        sys.executable,
        str(script_path),
        "--device",
        str(request["device"]),
    ]
    if request.get("skip_service"):
        command.append("--skip-service")
    if request.get("skip_reauthorize"):
        command.append("--skip-reauthorize")
    if request.get("skip_audio_unbind"):
        command.append("--skip-audio-unbind")
    if request.get("skip_uvc_quirks_reset"):
        command.append("--skip-uvc-quirks-reset")
    if request.get("skip_control_reset"):
        command.append("--skip-control-reset")
    if request.get("reload_uvc_module"):
        command.append("--reload-uvc-module")
    if request.get("usbreset_device"):
        command.append("--usbreset-device")
    return command


async def run_camera_usb_recovery(body: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    """运行相机 USB 恢复 smoke；它会短暂重启相机服务，但绝不发送运动命令。"""
    request = safe_camera_usb_recovery_request(body)
    script_path = Path(__file__).with_name("camera_usb_recovery_smoke.py")
    started_ms = now_ms()
    if not script_path.exists():
        return 503, {
            "schema": f"{SCHEMA}.camera_usb_recovery_proxy",
            "status": "recovery_script_missing",
            "recovery_request": request,
            "script_path": str(script_path),
            **proof_flags(),
            "publishes_cmd_vel": False,
            "opens_base_uart": False,
            "sends_motion_commands": False,
        }

    command = camera_usb_recovery_command(script_path, request)
    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=str(Path(__file__).resolve().parents[1]),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    process_timeout_s = 120.0
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=process_timeout_s)
    except asyncio.TimeoutError:
        try:
            if process.returncode is None:
                # 恢复脚本可能已完成但 aio wait_for 已超时；避免 kill 已退出进程抛异常。
                process.kill()
        except ProcessLookupError:
            pass
        await process.communicate()
        return 504, {
            "schema": f"{SCHEMA}.camera_usb_recovery_proxy",
            "status": "recovery_process_timeout",
            "recovery_request": request,
            "argv": command,
            "elapsed_ms": now_ms() - started_ms,
            "process_timeout_s": process_timeout_s,
            **proof_flags(),
            "publishes_cmd_vel": False,
            "opens_base_uart": False,
            "sends_motion_commands": False,
        }

    stdout_text = stdout.decode("utf-8", errors="replace").strip()
    stderr_text = stderr.decode("utf-8", errors="replace").strip()
    try:
        recovery_payload = json.loads(stdout_text[stdout_text.find("{"):]) if "{" in stdout_text else {}
    except json.JSONDecodeError:
        recovery_payload = {"status": "bad_recovery_json", "stdout_preview": stdout_text[-800:]}
    if not isinstance(recovery_payload, dict):
        recovery_payload = {"status": "recovery_json_not_object"}

    # 脚本 returncode=2 表示恢复执行完成但仍未读到帧；HTTP 仍返回 200，让 PC 能显示诊断材料。
    http_status = 200 if process.returncode in (0, 2) else 502
    recovery_payload.update({
        "schema": recovery_payload.get("schema") or f"{SCHEMA}.camera_usb_recovery_proxy",
        "upper_api_proxy": True,
        "upper_api_recovery_endpoint": ROUTE_PATHS["camera_usb_recovery"],
        "recovery_request": request,
        "argv": command,
        "returncode": process.returncode,
        "elapsed_ms": now_ms() - started_ms,
        "stderr_preview": stderr_text[-800:],
        **proof_flags(),
        "publishes_cmd_vel": False,
        "opens_base_uart": False,
        "sends_motion_commands": False,
        "robot_control_executed": False,
    })
    return http_status, recovery_payload


def default_map_preview_radar_overlay(reason: str = "not_loaded") -> dict[str, Any]:
    """地图预览即使没有雷达层，也返回稳定同形结构，避免 UI 猜字段是否存在。"""
    return {
        "overlay_status": "not_loaded",
        "scan_preview_points": [],
        "scan_preview_point_count": 0,
        "scan_preview_source_point_count": None,
        "scan_preview_frame_id": "",
        "robot_pose": None,
        "source_endpoint_ids": [],
        "blocked_reasons": [reason] if reason else [],
    }


def map_preview_scan_preview_from_driver_diagnostics(
    radar: dict[str, Any],
    generated_at_ms: int | None = None,
) -> dict[str, Any] | None:
    """优先用正在运行的 driver diagnostics 画实时雷达点，避免 stale proof 遮住当前 `/scan`。"""
    diagnostics = radar.get("driver_diagnostics_latest") if isinstance(radar.get("driver_diagnostics_latest"), dict) else {}
    artifact = diagnostics.get("artifact") if isinstance(diagnostics.get("artifact"), dict) else {}
    scan_preview = diagnostics.get("scan_preview") if isinstance(diagnostics.get("scan_preview"), dict) else {}
    runtime = diagnostics.get("runtime") if isinstance(diagnostics.get("runtime"), dict) else {}
    points = scan_preview.get("scan_preview_points") if isinstance(scan_preview.get("scan_preview_points"), list) else []
    point_count = int(scan_preview.get("scan_preview_point_count") or len(points) or 0)
    source_point_count = scan_preview.get("scan_preview_source_point_count") or runtime.get("last_scan_range_count")
    frame_id = str(scan_preview.get("scan_preview_frame_id") or "")
    mtime_ms = artifact.get("mtime_ms")
    age_ms = None
    if isinstance(mtime_ms, int):
        age_ms = max(0, int(generated_at_ms or now_ms()) - mtime_ms)
    diagnostics_fresh = diagnostics.get("status") == "loaded" and (
        age_ms is None or age_ms <= DEFAULT_LIDAR_DRIVER_DIAGNOSTICS_STALE_AFTER_MS
    )
    # 旧 scan-proof 过期时仍不能画旧点；只有 driver 正在秒级写新 diagnostics 才能作为实时画布来源。
    if not diagnostics_fresh or diagnostics.get("diagnosis_status") != "scan_published" or point_count <= 0:
        return None
    return {
        "scan_preview_points": points,
        "scan_preview_point_count": point_count,
        "scan_preview_source_point_count": source_point_count,
        "scan_preview_frame_id": frame_id,
        "scan_preview_source": scan_preview.get("scan_preview_source") or "lidar_driver_diagnostics.scan_preview",
        "freshness": {
            "status": "fresh",
            "age_ms": age_ms,
            "stale_after_ms": DEFAULT_LIDAR_DRIVER_DIAGNOSTICS_STALE_AFTER_MS,
            "basis": "lidar_driver_diagnostics_mtime_for_map_overlay",
        },
    }


class UpperRobotApi:
    """把上位机各硬件入口收敛到一个 HTTP API，PC 不再分散猜端口。"""

    def __init__(
        self,
        camera_base_url: str,
        base_port: str,
        base_baudrate: int,
        max_speed: float,
        base_command_mode: str = DEFAULT_BASE_COMMAND_MODE,
        nav2_base_command_mode: str = DEFAULT_NAV2_BASE_COMMAND_MODE,
        manual_pwm_min_abs: int = DEFAULT_MANUAL_PWM_MIN_ABS,
        manual_pwm_max_abs: int = DEFAULT_MANUAL_PWM_MAX_ABS,
        feedback_samples_artifact_path: str = DEFAULT_FEEDBACK_SAMPLES_ARTIFACT_PATH,
        lidar_scan_proof_artifact_path: str = DEFAULT_LIDAR_SCAN_PROOF_ARTIFACT_PATH,
        lidar_raw_packet_proof_artifact_path: str = DEFAULT_LIDAR_RAW_PACKET_PROOF_ARTIFACT_PATH,
        map_artifact_dir: str = DEFAULT_MAP_ARTIFACT_DIR,
        map_lifecycle_proof_artifact_path: str = DEFAULT_MAP_LIFECYCLE_PROOF_ARTIFACT_PATH,
        localization_artifact_path: str = DEFAULT_LOCALIZATION_ARTIFACT_PATH,
        nav2_lifecycle_artifact_path: str = DEFAULT_NAV2_LIFECYCLE_ARTIFACT_PATH,
        nav2_goal_execution_artifact_path: str = DEFAULT_NAV2_GOAL_EXECUTION_ARTIFACT_PATH,
        delivery_completion_artifact_path: str = DEFAULT_DELIVERY_COMPLETION_ARTIFACT_PATH,
        free_roam_autonomy_artifact_path: str = DEFAULT_FREE_ROAM_AUTONOMY_ARTIFACT_PATH,
        elevator_status_artifact_path: str = DEFAULT_ELEVATOR_STATUS_ARTIFACT_PATH,
        operator_report_artifact_path: str = DEFAULT_OPERATOR_REPORT_ARTIFACT_PATH,
        radar_start_command: str | None = DEFAULT_RADAR_START_COMMAND,
        radar_stop_command: str | None = DEFAULT_RADAR_STOP_COMMAND,
        lidar_scan_proof_runtime_command: str | None = None,
        lidar_scan_proof_runtime_warmup_s: float = DEFAULT_LIDAR_SCAN_PROOF_RUNTIME_WARMUP_S,
        map_start_command: str | None = None,
        map_reset_command: str | None = None,
        map_save_command: str | None = None,
        map_load_command: str | None = None,
        localize_reset_command: str | None = None,
        nav2_start_command: str | None = DEFAULT_NAV2_START_COMMAND,
        nav2_stop_command: str | None = DEFAULT_NAV2_STOP_COMMAND,
        nav2_status_command: str | None = DEFAULT_NAV2_STATUS_COMMAND,
    ) -> None:
        self.camera_base_url = camera_base_url.rstrip("/")
        self.base_port = base_port
        self.base_baudrate = base_baudrate
        self.max_speed = max_speed
        self.base_command_mode = base_command_mode if base_command_mode in ALLOWED_BASE_COMMAND_MODES else DEFAULT_BASE_COMMAND_MODE
        self.nav2_base_command_mode = (
            nav2_base_command_mode if nav2_base_command_mode in ALLOWED_NAV2_BASE_COMMAND_MODES else DEFAULT_NAV2_BASE_COMMAND_MODE
        )
        self.manual_pwm_min_abs = max(0, min(int(manual_pwm_min_abs), 255))
        self.manual_pwm_max_abs = max(self.manual_pwm_min_abs, min(int(manual_pwm_max_abs), 255))
        self.feedback_samples_artifact_path = feedback_samples_artifact_path
        self.lidar_scan_proof_artifact_path = lidar_scan_proof_artifact_path
        self.lidar_raw_packet_proof_artifact_path = lidar_raw_packet_proof_artifact_path
        self.map_artifact_dir = resolve_onboard_runtime_path(map_artifact_dir)
        self.map_lifecycle_proof_artifact_path = resolve_onboard_runtime_path(map_lifecycle_proof_artifact_path)
        self.localization_artifact_path = resolve_onboard_runtime_path(localization_artifact_path)
        self.nav2_lifecycle_artifact_path = resolve_onboard_runtime_path(nav2_lifecycle_artifact_path)
        self.nav2_goal_execution_artifact_path = resolve_onboard_runtime_path(nav2_goal_execution_artifact_path)
        self.delivery_completion_artifact_path = resolve_onboard_runtime_path(delivery_completion_artifact_path)
        self.free_roam_autonomy_artifact_path = resolve_onboard_runtime_path(free_roam_autonomy_artifact_path)
        self.elevator_status_artifact_path = elevator_status_artifact_path
        self.operator_report_artifact_path = operator_report_artifact_path
        self._manual_hold_state: dict[str, Any] = {}
        self._manual_hold_watchdog_task: asyncio.Task[Any] | None = None
        self.radar_start_command = radar_start_command
        self.radar_stop_command = radar_stop_command
        self.lidar_scan_proof_runtime_command = lidar_scan_proof_runtime_command
        self.lidar_scan_proof_runtime_warmup_s = min(max(float(lidar_scan_proof_runtime_warmup_s), 0.0), 30.0)
        self.map_start_command = map_start_command
        self.map_reset_command = map_reset_command
        self.map_save_command = map_save_command
        self.map_load_command = map_load_command
        self.localize_reset_command = localize_reset_command
        self.nav2_start_command = nav2_start_command
        self.nav2_stop_command = nav2_stop_command
        self.nav2_status_command = nav2_status_command

    def map_preview_radar_overlay(self) -> dict[str, Any]:
        """把当前雷达点和 map-frame 位姿合并给 map preview；stale/停止雷达只报 not_current，不贴旧点。"""
        generated_at_ms = now_ms()
        try:
            radar = self.radar_status()
            _, nav2_latest = self.nav2_proof_latest()
        except Exception as exc:  # noqa: BLE001 - overlay 失败不能阻断地图图片本身。
            overlay = default_map_preview_radar_overlay("map_preview_overlay_read_failed")
            overlay["blocked_reasons"].append(str(compact_error(exc)))
            return overlay

        scan_proof = radar.get("scan_proof_latest") if isinstance(radar.get("scan_proof_latest"), dict) else {}
        freshness = scan_proof.get("freshness") if isinstance(scan_proof.get("freshness"), dict) else {}
        radar_stopped = radar.get("lifecycle_running") is False or radar.get("lifecycle_state") == "stopped"
        driver_scan_preview = None if radar_stopped else map_preview_scan_preview_from_driver_diagnostics(radar, generated_at_ms)
        scan_source = driver_scan_preview or scan_proof
        points = scan_source.get("scan_preview_points") if isinstance(scan_source.get("scan_preview_points"), list) else []
        point_count = int(scan_source.get("scan_preview_point_count") or len(points) or 0)
        source_point_count = scan_source.get("scan_preview_source_point_count")
        frame_id = str(scan_source.get("scan_preview_frame_id") or "")
        radar_stale = freshness.get("status") == "stale" and driver_scan_preview is None
        robot_pose = nav2_latest.get("amcl_pose") if isinstance(nav2_latest.get("amcl_pose"), dict) else None
        has_pose = bool(robot_pose and robot_pose.get("frame_id") == "map")
        has_points = point_count > 0 or bool(points)
        current_points_allowed = has_points and not radar_stale and not radar_stopped
        blocked_reasons = [
            "runtime_scan_stale_for_map_radar_overlay" if radar_stale else "",
            "radar_lifecycle_not_running_for_map_radar_overlay" if radar_stopped else "",
            "robot_pose_missing_for_map_radar_overlay" if has_points and not has_pose else "",
            "scan_preview_points_missing_for_map_radar_overlay" if has_pose and not has_points else "",
        ]
        blocked_reasons = [reason for reason in blocked_reasons if reason]
        if has_points and not current_points_allowed:
            overlay_status = "not_current"
        elif current_points_allowed or has_pose:
            overlay_status = "loaded" if current_points_allowed and has_pose and not blocked_reasons else "partial"
        else:
            overlay_status = "blocked" if blocked_reasons else "not_loaded"
        return {
            "overlay_status": overlay_status,
            "scan_preview_points": points if current_points_allowed else [],
            "scan_preview_point_count": point_count if current_points_allowed else 0,
            "scan_preview_source_point_count": source_point_count,
            "scan_preview_frame_id": frame_id,
            "scan_preview_source": scan_source.get("scan_preview_source"),
            "robot_pose": robot_pose if has_pose else None,
            "source_endpoint_ids": ["radar_status", "nav2_proof_latest"],
            "blocked_reasons": blocked_reasons,
        }

    def base_status(self) -> dict[str, Any]:
        """底盘状态默认只聚合已落盘读数；显式采样接口才发送非运动 T=130。"""
        serial_module, import_error = load_serial_module()
        port_info = describe_path(self.base_port)
        feedback_samples_latest = summarize_feedback_samples_latest_artifact(
            self.feedback_samples_artifact_path,
            DEFAULT_FEEDBACK_SAMPLES_STALE_AFTER_MS,
        )
        bridge_feedback_debug = summarize_bridge_feedback_debug_log(DEFAULT_BRIDGE_FEEDBACK_DEBUG_LOG_PATH)
        bridge_command_debug = summarize_bridge_command_debug_log(DEFAULT_BRIDGE_COMMAND_DEBUG_LOG_PATH)
        feedback_samples_freshness = feedback_samples_latest.get("freshness")
        feedback_samples_is_fresh = isinstance(feedback_samples_freshness, dict) and feedback_samples_freshness.get("status") == "fresh"
        bridge_feedback_freshness = bridge_feedback_debug.get("freshness")
        bridge_feedback_is_fresh = isinstance(bridge_feedback_freshness, dict) and bridge_feedback_freshness.get("status") == "fresh"
        bridge_command_freshness = bridge_command_debug.get("freshness")
        bridge_command_is_fresh = isinstance(bridge_command_freshness, dict) and bridge_command_freshness.get("status") == "fresh"
        if bridge_feedback_is_fresh:
            # bridge 已经独占 UART 并持续写 fresh T1001 日志时，status 不能再为了只读轮速抢串口。
            feedback_readback = skipped_base_status_feedback_payload(
                self.base_port,
                self.base_baudrate,
                "fresh_bridge_feedback_debug_log_available",
            )
            feedback_ack = feedback_ack_from_bridge_debug(bridge_feedback_debug)
        elif os.getenv(BASE_STATUS_DIRECT_FEEDBACK_ENV) == "1":
            # 只有显式打开兼容开关时，GET 状态端点才做旧式 T=130；默认由专用采样接口承担轮速复验。
            feedback_readback = request_base_feedback_once(
                self.base_port,
                self.base_baudrate,
                read_timeout_s=DEFAULT_FEEDBACK_READ_TIMEOUT_S,
                read_window_s=DEFAULT_FEEDBACK_READ_WINDOW_S,
            )
            feedback_ack = feedback_ack_from_fresh_evidence(feedback_readback, feedback_samples_latest)
        else:
            # 普通 PC summary 会高频读取 base/status；默认跳过直接 T=130，避免状态刷新长时间占用 WAVE ROVER UART。
            feedback_readback = skipped_base_status_feedback_payload(
                self.base_port,
                self.base_baudrate,
                "base_status_get_lightweight_no_direct_t130",
            )
            feedback_ack = feedback_ack_from_fresh_evidence(feedback_readback, feedback_samples_latest)
        best_wheel_summary = (
            bridge_feedback_debug.get("wheel_feedback_summary")
            if bridge_feedback_is_fresh and isinstance(bridge_feedback_debug.get("wheel_feedback_summary"), dict)
            else feedback_readback.get("wheel_feedback_summary")
            if isinstance(feedback_readback.get("wheel_feedback_summary"), dict)
            else feedback_samples_latest.get("wheel_feedback_summary")
            if feedback_samples_is_fresh and isinstance(feedback_samples_latest.get("wheel_feedback_summary"), dict)
            else {}
        )
        best_motion_signal = (
            bridge_feedback_debug
            if bridge_feedback_is_fresh
            else feedback_samples_latest
            if feedback_samples_is_fresh
            else {}
        )
        wheel_feedback_nonzero = bool(
            feedback_readback.get("wheel_feedback_lr_nonzero_proven")
            or (bridge_feedback_is_fresh and bridge_feedback_debug.get("wheel_feedback_lr_nonzero_proven"))
            or (feedback_samples_is_fresh and feedback_samples_latest.get("wheel_feedback_lr_nonzero_proven"))
        )
        command_raw_summary = command_raw_motion_summary_from_debug_record(
            bridge_command_debug.get("latest_sent_nonzero_command") if bridge_command_is_fresh else None,
            source="fresh_bridge_command_debug_latest_sent_nonzero_command",
        )
        command_motion_evidence_complete = bool(
            command_raw_summary.get("raw_nonzero_proven")
            and (wheel_feedback_nonzero or best_motion_signal.get("motion_signal_observed"))
        )
        return {
            "schema": f"{SCHEMA}.base_status",
            "generated_at_ms": now_ms(),
            "vendor_sources": VENDOR_SOURCES,
            "port": self.base_port,
            "baudrate": self.base_baudrate,
            "base_command_mode": self.base_command_mode,
            "nav2_base_command_mode": self.nav2_base_command_mode,
            "port_info": port_info,
            "pyserial_available": serial_module is not None,
            "pyserial_error": import_error,
            "write_control_available": bool(port_info["exists"] and serial_module is not None),
            "feedback_ack": feedback_ack,
            "feedback_readback": feedback_readback,
            "direct_feedback_on_get_enabled": os.getenv(BASE_STATUS_DIRECT_FEEDBACK_ENV) == "1",
            "explicit_feedback_request_endpoint": ROUTE_PATHS["base_feedback_request"],
            "explicit_feedback_samples_endpoint": ROUTE_PATHS["base_feedback_samples"],
            "feedback_samples_latest": feedback_samples_latest,
            "bridge_feedback_debug": bridge_feedback_debug,
            "bridge_command_debug": bridge_command_debug,
            "base_command_chain_observed": bool(bridge_command_debug.get("nonzero_command_observed")),
            "base_command_chain_nonzero_count": bridge_command_debug.get("nonzero_command_count"),
            "base_command_chain_nonzero_sent_count": bridge_command_debug.get("nonzero_command_sent_count"),
            "base_command_chain_serial_write_success_observed": bool(
                bridge_command_debug.get("serial_write_success_observed")
            ),
            "base_command_chain_serial_write_success_count": bridge_command_debug.get("serial_write_success_count"),
            "base_command_chain_http_write_success_observed": bool(
                bridge_command_debug.get("http_write_success_observed")
            ),
            "base_command_chain_http_write_success_count": bridge_command_debug.get("http_write_success_count"),
            "base_command_chain_transport_write_success_observed": bool(
                bridge_command_debug.get("transport_write_success_observed")
            ),
            "base_command_chain_transport_write_success_count": bridge_command_debug.get("transport_write_success_count"),
            "base_command_chain_write_failed_count": bridge_command_debug.get("command_write_failed_count"),
            "base_command_chain_latest_nonzero_command": bridge_command_debug.get("latest_nonzero_command"),
            "base_command_chain_latest_sent_nonzero_command": bridge_command_debug.get("latest_sent_nonzero_command"),
            "base_command_chain_latest_write_failed_command": bridge_command_debug.get("latest_write_failed_command"),
            "base_command_chain_latest_command": bridge_command_debug.get("latest_command"),
            "base_command_chain_mode_counts": bridge_command_debug.get("command_mode_counts"),
            "base_command_chain_startup_main_type_config_sent": bool(
                bridge_command_debug.get("startup_main_type_config_sent")
            ),
            "base_command_chain_startup_main_type": bridge_command_debug.get("startup_main_type"),
            "base_command_chain_startup_module_type": bridge_command_debug.get("startup_module_type"),
            "command_raw_summary": command_raw_summary,
            "command_raw_nonzero_proven": bool(command_raw_summary.get("raw_nonzero_proven")),
            "command_raw_lr_nonzero_proven": bool(command_raw_summary.get("lr_nonzero_proven")),
            "command_raw_twist_nonzero_proven": bool(command_raw_summary.get("twist_nonzero_proven")),
            "command_raw_latest_left": command_raw_summary.get("left_raw"),
            "command_raw_latest_right": command_raw_summary.get("right_raw"),
            "command_raw_latest_linear_x": command_raw_summary.get("linear_x"),
            "command_raw_latest_angular_z": command_raw_summary.get("angular_z"),
            "command_raw_motion_evidence_complete": command_motion_evidence_complete,
            "motion_evidence_complete": command_motion_evidence_complete,
            "motion_evidence_source": (
                "command_raw_lr_plus_motion_signal"
                if command_raw_summary.get("lr_nonzero_proven") and best_motion_signal.get("motion_signal_observed")
                else "command_raw_twist_plus_motion_signal"
                if command_raw_summary.get("twist_nonzero_proven") and best_motion_signal.get("motion_signal_observed")
                else "not_complete"
            ),
            "wheel_feedback_summary": best_wheel_summary,
            "wheel_feedback_nonzero_observed": wheel_feedback_nonzero,
            "wheel_feedback_lr_nonzero_proven": wheel_feedback_nonzero,
            "imu_attitude_delta_observed": bool(best_motion_signal.get("imu_attitude_delta_observed")),
            "motion_signal_observed": bool(wheel_feedback_nonzero or best_motion_signal.get("motion_signal_observed")),
            "motion_signal_source": best_motion_signal.get("motion_signal_source") or (
                "wheel_feedback_lr" if wheel_feedback_nonzero else "not_observed"
            ),
            "control_policy": {
                "mode": "low_speed_pulse_with_auto_stop",
                "base_command_mode": self.base_command_mode,
                "nav2_base_command_mode": self.nav2_base_command_mode,
                "max_speed": self.max_speed,
                "manual_pwm_min_abs": self.manual_pwm_min_abs,
                "manual_pwm_max_abs": self.manual_pwm_max_abs,
                "max_pulse_ms": MAX_PULSE_MS,
                "stop_commands": stop_commands_for_mode(self.base_command_mode),
            },
            "readback_sends_commands": bool(feedback_readback.get("sends_commands")),
            "sends_commands": bool(feedback_readback.get("sends_commands")),
            "sends_motion_commands": False,
            **proof_flags(),
        }

    def radar_status(self) -> dict[str, Any]:
        """雷达当前先合并设备状态，真实 /scan 仍需 ROS2/LiDAR 节点证明。"""
        candidates = list_candidates(["/dev/lidar", "/dev/ttyACM*", "/dev/serial/by-id/*", "/dev/serial/by-path/*"])
        tty_acm0 = describe_path("/dev/ttyACM0")
        lidar_observed = bool(tty_acm0["exists"])
        scan_proof_latest = summarize_lidar_scan_proof_latest_artifact(self.lidar_scan_proof_artifact_path)
        latest_scan_proof = build_radar_latest_scan_proof_status(scan_proof_latest)
        lifecycle_status_readback = read_radar_lifecycle_status()
        lifecycle_running = bool(lifecycle_status_readback.get("running"))
        lifecycle_state = lifecycle_status_readback.get("state")
        lifecycle_pid = lifecycle_status_readback.get("pid")
        lifecycle_latest = lifecycle_status_readback.get("latest_result")
        lifecycle_latest = lifecycle_latest if isinstance(lifecycle_latest, dict) else {}
        driver_diagnostics_path = (
            lifecycle_status_readback.get("driver_diagnostics_path")
            or lifecycle_latest.get("driver_diagnostics_path")
        )
        driver_diagnostics_latest = read_lidar_driver_diagnostics_artifact(
            str(driver_diagnostics_path) if driver_diagnostics_path else None
        )
        fresh_scan_proof_observed = bool(latest_scan_proof["observed"])
        latest_scan_proof_fresh = bool(latest_scan_proof.get("fresh_while_observed"))
        latest_scan_proof_blocked_reasons = (
            [] if fresh_scan_proof_observed else [str(latest_scan_proof["failure_reason"] or "latest_scan_proof_not_observed")]
        )
        continuity_window_status = "lifecycle_status_unavailable"
        continuity_blocked_reasons: list[str] = []
        if lifecycle_status_readback.get("status") != "loaded":
            continuity_blocked_reasons.append("lifecycle_status_read_failed")
        elif not lifecycle_running:
            continuity_window_status = "lifecycle_not_running"
            continuity_blocked_reasons.append("lidar_lifecycle_not_running")
            if fresh_scan_proof_observed:
                continuity_window_status = "latest_proof_present_but_lifecycle_not_running"
            else:
                continuity_window_status = "lifecycle_not_running"
        elif latest_scan_proof_fresh:
            continuity_window_status = "latest_proof_fresh_while_lifecycle_running"
        elif fresh_scan_proof_observed:
            continuity_window_status = "latest_proof_stale_while_lifecycle_running"
            continuity_blocked_reasons.append("latest_scan_proof_stale")
        elif latest_scan_proof.get("artifact", {}).get("status") == "missing":
            continuity_window_status = "latest_proof_missing_while_lifecycle_running"
            continuity_blocked_reasons.append("latest_scan_proof_missing")
        else:
            continuity_window_status = "latest_proof_incomplete_while_lifecycle_running"
            continuity_blocked_reasons.extend(latest_scan_proof_blocked_reasons)
        continuous_window_observed = continuity_window_status == "latest_proof_fresh_while_lifecycle_running"
        continuous_scan_status = continuity_window_status
        continuous_blocked_reasons = [] if continuous_window_observed else list(dict.fromkeys(continuity_blocked_reasons or ["scan_continuity_not_observed"]))
        start_command_info = command_config_info("ROBER_RADAR_START_COMMAND", self.radar_start_command)
        stop_command_info = command_config_info("ROBER_RADAR_STOP_COMMAND", self.radar_stop_command)
        scan_proof_runtime_command_info = command_config_info(
            "ROBER_LIDAR_SCAN_PROOF_RUNTIME_COMMAND",
            self.lidar_scan_proof_runtime_command,
        )
        baudrate_readback = build_radar_baudrate_readback(
            lifecycle_status_readback=lifecycle_status_readback,
            driver_diagnostics_latest=driver_diagnostics_latest,
            start_command_info=start_command_info,
            scan_proof_runtime_command_info=scan_proof_runtime_command_info,
            radar_start_command=self.radar_start_command,
            lidar_scan_proof_runtime_command=self.lidar_scan_proof_runtime_command,
        )
        return {
            "schema": f"{SCHEMA}.radar_status",
            "generated_at_ms": now_ms(),
            "evidence_ref": latest_scan_proof["latest_evidence_ref"],
            "latest_evidence_ref": latest_scan_proof["latest_evidence_ref"],
            "scan_status": "fresh_scan_proof_observed" if fresh_scan_proof_observed else "not_proven",
            "continuous_scan_status": continuous_scan_status,
            "fresh_scan_proof_observed": fresh_scan_proof_observed,
            "latest_scan_proof_fresh": latest_scan_proof_fresh,
            "latest_scan_proof_state": latest_scan_proof["state"],
            "latest_scan_hz_average_rate_hz": latest_scan_proof["scan_hz_average_rate_hz"],
            "runtime_summary_fallback_used": latest_scan_proof["runtime_summary_fallback_used"],
            "latest_scan_proof": latest_scan_proof,
            "lifecycle_status": continuity_window_status if lifecycle_status_readback.get("status") == "loaded" else "status_read_failed",
            "lifecycle_running": lifecycle_running,
            "lifecycle_state": lifecycle_state,
            "lifecycle_pid": lifecycle_pid,
            "lifecycle_status_readback": lifecycle_status_readback,
            "driver_diagnostics_latest": driver_diagnostics_latest,
            "driver_diagnostics_status": driver_diagnostics_latest.get("diagnosis_status"),
            "driver_diagnostics_next_action_plain": driver_diagnostics_latest.get("next_action_plain"),
            "continuous_window_observed": continuous_window_observed,
            "continuity_window_status": continuity_window_status,
            "continuity_blocked_reasons": continuous_blocked_reasons,
            "pointcloud_fabricated": False,
            "dev_lidar": describe_path("/dev/lidar"),
            "observed_lidar_port": "/dev/ttyACM0" if lidar_observed else None,
            "observed_lidar_port_info": tty_acm0,
            "baudrate": baudrate_readback["baudrate"],
            "baudrate_readback_source": baudrate_readback["baudrate_readback_source"],
            "baudrate_readback_status": baudrate_readback["baudrate_readback_status"],
            "baudrate_candidates": baudrate_readback["baudrate_candidates"],
            "vendor_reference_baudrate": baudrate_readback["vendor_reference_baudrate"],
            "historical_field_baudrate_candidate": baudrate_readback["historical_field_baudrate_candidate"],
            "start_command_hex": "a5 60",
            "stop_command_hex": "a5 00 a5 65 a5 65",
            "candidates": candidates,
            "ros2": {
                "driver": "ros2_trashbot_hardware lidar_driver",
                "launch": "ros2 launch ros2_trashbot_bringup learn.launch.py lidar_enabled:=true lidar_serial_port:=/dev/ttyACM0 lidar_serial_baudrate:=230400 lidar_publish_raw_packets:=true",
                "scan_topic": "/scan",
                "raw_packet_topic": "/lidar/raw_packet",
                "frame_id": "laser_frame",
            },
            "scan_proof_latest": scan_proof_latest,
            "raw_packet_proof_latest": summarize_lidar_raw_packet_proof_latest_artifact(
                self.lidar_raw_packet_proof_artifact_path
            ),
            "controls": {
                "start": {
                    "endpoint": ROUTE_PATHS["radar_start"],
                    "command": start_command_info,
                    "recommended_command": DEFAULT_RADAR_START_COMMAND,
                    "allowed_runtime_script": SAFE_RADAR_LIFECYCLE_SCRIPT,
                },
                "stop": {
                    "endpoint": ROUTE_PATHS["radar_stop"],
                    "command": stop_command_info,
                    "recommended_command": DEFAULT_RADAR_STOP_COMMAND,
                    "allowed_runtime_script": SAFE_RADAR_LIFECYCLE_SCRIPT,
                },
                "scan_proof_refresh": {
                    "endpoint": ROUTE_PATHS["radar_scan_proof_refresh"],
                    "mode": "driver_diagnostics",
                    "legacy_mode": "legacy_ros2_cli",
                    "artifact": lidar_scan_proof_artifact_info(self.lidar_scan_proof_artifact_path),
                    "runtime_command": scan_proof_runtime_command_info,
                    "runtime_warmup_s": self.lidar_scan_proof_runtime_warmup_s,
                    "allowed_runtime_script": SAFE_LIDAR_RUNTIME_SCRIPT,
                    "starts_driver": False,
                    "opens_lidar_serial": False,
                    "sends_lidar_start_command": False,
                    "sends_motion_commands": False,
                },
            },
            "latest_scan_proof_blocked_reasons": latest_scan_proof_blocked_reasons,
            "continuous_blocked_reasons": continuous_blocked_reasons,
            "blocked_reasons": [
                *(["ttyACM0_lidar_not_present"] if not lidar_observed else []),
                *latest_scan_proof_blocked_reasons,
                *continuous_blocked_reasons,
            ],
            "sends_commands": False,
            "sends_motion_commands": False,
            "sends_base_motion_commands": False,
            "calls_base_manual": False,
            "publishes_cmd_vel": False,
            "uses_base_uart": False,
            "route_execution_success": False,
            "hil_pass": False,
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
        command_result = run_radar_lifecycle_command(command, action)
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

    async def radar_scan_proof_refresh(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """显式刷新 LiDAR proof artifact；默认只读 driver diagnostics，永不触碰底盘。"""
        body = body if isinstance(body, dict) else {}
        collector_mode = str(body.get("collector_mode") or body.get("mode") or "driver_diagnostics").strip() or "driver_diagnostics"
        timeout_s = clamp_float(
            body.get("timeout_s"),
            DEFAULT_LIDAR_SCAN_PROOF_REFRESH_TIMEOUT_S,
            1.0,
            30.0,
        )
        runtime_warmup_s = clamp_float(
            body.get("runtime_warmup_s"),
            self.lidar_scan_proof_runtime_warmup_s,
            0.0,
            30.0,
        )
        runtime_requested = bool(body.get("start_runtime")) if "start_runtime" in body else False
        upper_api_base_url = str(body.get("upper_api_base_url") or "http://127.0.0.1:8787")
        runtime_result = None
        if runtime_requested:
            runtime_result = await asyncio.to_thread(
                start_lidar_scan_proof_runtime,
                self.lidar_scan_proof_runtime_command,
                runtime_warmup_s,
            )
        if collector_mode in {"legacy_ros2_cli", "ros2_cli", "read_only_scan_proof_collector"}:
            # legacy 模式保留给工程深采样；普通 PC 刷新不再默认启动 ROS2 CLI 子进程。
            refresh_result = await asyncio.to_thread(
                run_lidar_scan_proof_collector,
                artifact_path=self.lidar_scan_proof_artifact_path,
                upper_api_base_url=upper_api_base_url,
                timeout_s=timeout_s,
            )
        else:
            refresh_result = await asyncio.to_thread(
                run_lidar_driver_diagnostics_scan_proof_refresh,
                artifact_path=self.lidar_scan_proof_artifact_path,
            )
        if runtime_requested:
            await asyncio.to_thread(
                apply_lidar_runtime_summary_fallback,
                artifact_path=self.lidar_scan_proof_artifact_path,
                refresh_result=refresh_result,
                runtime_result=runtime_result,
            )
        return build_lidar_scan_proof_refresh_payload(
            artifact_path=self.lidar_scan_proof_artifact_path,
            refresh_result=refresh_result,
            timeout_s=timeout_s,
            runtime_result=runtime_result,
            runtime_requested=runtime_requested,
            runtime_warmup_s=runtime_warmup_s,
            collector_mode=collector_mode,
        )

    def map_status(self) -> dict[str, Any]:
        """地图生命周期状态只列出软件入口和 artifact 目录，不读取 ROS graph。"""
        proof_latest = summarize_map_lifecycle_latest_artifact(self.map_lifecycle_proof_artifact_path)
        return {
            "schema": f"{SCHEMA}.map_lifecycle_status",
            "generated_at_ms": now_ms(),
            "artifact": map_artifact_info(self.map_artifact_dir),
            "proof_latest": proof_latest,
            "routes": {
                "status": ROUTE_PATHS["map_status"],
                "start": ROUTE_PATHS["map_start"],
                "reset": ROUTE_PATHS["map_reset"],
                "save": ROUTE_PATHS["map_save"],
                "load": ROUTE_PATHS["map_load"],
                "list": ROUTE_PATHS["map_list"],
                "proof_refresh": ROUTE_PATHS["map_proof_refresh"],
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
            "status": proof_latest.get("status", "not_proven"),
            "software_guard": proof_latest.get("software_guard", True),
            "not_proven": proof_latest.get("not_proven", True),
            "sends_motion_commands": False,
            "sends_base_motion_commands": False,
            "uses_base_uart": False,
            "sends_commands": False,
            **proof_flags(),
        }

    def map_control(self, action: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """建图 start/save 进入 no-motion helper；reset/load 继续保持 guard。"""
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
        normalized_body, body_error = normalize_map_runtime_body(body)
        if body_error:
            return software_guard_payload(
                schema_suffix="map_lifecycle_result",
                action=f"map_{action}",
                endpoint=endpoint,
                command_env=command_env,
                command=command,
                command_result={"mode": "map_lifecycle_body_guard", "executed": False, "ok": False, "error": body_error},
                artifact=map_artifact_info(self.map_artifact_dir),
                extra={
                    "failure_reason": body_error["type"],
                    "blocked_reasons": [body_error["type"]],
                    "requested_map_name": body.get("map_name"),
                    "requested_artifact_path": body.get("artifact_path"),
                },
            )
        if action in {"start", "save"}:
            # V1 使用同一个受控 no-motion runtime：启动 LiDAR+SLAM、观测 /map、调用 save_map、清场。
            command_result = run_map_lifecycle_proof_helper(
                artifact_path=self.map_lifecycle_proof_artifact_path,
                map_artifact_dir=self.map_artifact_dir,
                timeout_s=DEFAULT_MAP_LIFECYCLE_PROOF_REFRESH_TIMEOUT_S,
                map_name=str(normalized_body["map_name"]),
            )
            latest_http_status, latest_payload = self.map_proof_latest()
            latest_result = latest_payload.get("latest_result") if isinstance(latest_payload.get("latest_result"), dict) else None
            contract = map_lifecycle_runtime_readback_contract(latest_result)
            failure_reason = None
            blocked_reasons: list[str] = []
            if not command_result.get("ok"):
                failure_reason = "map_lifecycle_runtime_helper_failed"
                blocked_reasons.append(failure_reason)
            elif contract["status"] != MAP_LIFECYCLE_OBSERVED_STATUS:
                failure_reason = "map_lifecycle_runtime_proof_not_clean"
                blocked_reasons.append(failure_reason)
            payload = software_guard_payload(
                schema_suffix="map_lifecycle_result",
                action=f"map_{action}",
                endpoint=endpoint,
                command_env="built_in_no_motion_map_lifecycle_helper",
                command="o3_map_lifecycle_proof.py",
                command_result=command_result,
                artifact=map_artifact_info(self.map_artifact_dir),
                extra={
                    **normalized_body,
                    **contract,
                    "failure_reason": failure_reason,
                    "blocked_reasons": blocked_reasons,
                    "latest_readback_http_status": latest_http_status,
                    "latest_result": latest_result,
                    "proof_artifact": map_lifecycle_proof_artifact_info(self.map_lifecycle_proof_artifact_path),
                    "map_lifecycle_status": self.map_status(),
                    "scope": "no_motion_lidar_slam_map_runtime_control",
                    "no_motion_runtime_control": True,
                    "does_not_prove": [
                        "slam_map_quality",
                        "nav2_execution",
                        "real_motion",
                        "delivery_success",
                    ],
                },
            )
            payload["operator_message"] = (
                "no-motion map runtime proof attached; artifact_path was ignored"
                if not failure_reason
                else "no-motion map runtime helper failed; inspect latest_result.root_causes"
            )
            return payload
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
                **normalized_body,
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
                            "quality": analyze_map_yaml_quality(path),
                        }
                    )
        map_quality_summary = summarize_map_quality(entries)
        return software_guard_payload(
            schema_suffix="map_list_result",
            action="map_list",
            endpoint=ROUTE_PATHS["map_list"],
            artifact=map_artifact_info(self.map_artifact_dir),
            extra={
                "artifact_dir_exists": root.exists(),
                "maps": entries,
                "map_count": len(entries),
                "map_quality_summary": map_quality_summary,
                "map_usable_for_navigation": map_quality_summary["status"] == "has_usable_map",
                "map_needs_rebuild": map_quality_summary["status"] in {"no_free_cells", "analysis_failed"},
                "command_result": {"mode": "read_only_local_files", "executed": False, "ok": root.exists()},
                "failure_reason": None if root.exists() else "map_artifact_dir_missing",
            },
        )

    def map_preview(self, map_name: str | None = None) -> dict[str, Any]:
        """读取真实 YAML/PGM 并返回浏览器可显示的 PNG data URL；不启动任何 ROS2 或底盘动作。"""
        root = Path(self.map_artifact_dir)
        path_overlay = nav2_path_preview_overlay_from_artifact(self.nav2_lifecycle_artifact_path)
        target_overlay = (
            route_target_overlay_from_path_preview(path_overlay)
            or nav2_goal_target_overlay_from_artifact(self.nav2_goal_execution_artifact_path)
        )
        try:
            requested_map_name = safe_preview_map_name(map_name)
        except ValueError as exc:
            radar_overlay = default_map_preview_radar_overlay(str(exc))
            color_overlay = default_map_color_overlay(str(exc))
            return software_guard_payload(
                schema_suffix="map_preview_result",
                action="map_preview",
                endpoint=ROUTE_PATHS["map_preview"],
                artifact=map_artifact_info(self.map_artifact_dir),
                extra={
                    "status": "blocked",
                    "failure_reason": str(exc),
                    "blocked_reasons": [str(exc)],
                    "map_name": map_name,
                    "image_data_url": "",
                    "radar_overlay": radar_overlay,
                    "color_overlay": color_overlay,
                    **path_overlay,
                    **target_overlay,
                    "command_result": {"mode": "read_only_local_files", "executed": False, "ok": False},
                },
            )
        if not root.exists() or not root.is_dir():
            radar_overlay = default_map_preview_radar_overlay("map_artifact_dir_missing")
            color_overlay = default_map_color_overlay("map_artifact_dir_missing")
            return software_guard_payload(
                schema_suffix="map_preview_result",
                action="map_preview",
                endpoint=ROUTE_PATHS["map_preview"],
                artifact=map_artifact_info(self.map_artifact_dir),
                extra={
                    "status": "blocked",
                    "failure_reason": "map_artifact_dir_missing",
                    "blocked_reasons": ["map_artifact_dir_missing"],
                    "map_name": requested_map_name or "",
                    "image_data_url": "",
                    "radar_overlay": radar_overlay,
                    "color_overlay": color_overlay,
                    **path_overlay,
                    **target_overlay,
                    "command_result": {"mode": "read_only_local_files", "executed": False, "ok": False},
                },
            )
        failures: list[str] = []
        radar_overlay = self.map_preview_radar_overlay()
        for yaml_path in map_preview_candidates(root, requested_map_name):
            if not path_is_under(yaml_path, root):
                failures.append("map_yaml_outside_artifact_dir")
                continue
            if not yaml_path.exists() or not yaml_path.is_file():
                failures.append(f"map_yaml_missing:{yaml_path.name}")
                continue
            try:
                quality = analyze_map_yaml_quality(yaml_path)
                image_path = Path(str(quality.get("image") or ""))
                if not path_is_under(image_path, root):
                    raise ValueError("map_image_outside_artifact_dir")
                image_preview = data_url_for_pgm(image_path)
                color_overlay = map_color_overlay_for_pgm(image_path)
                return software_guard_payload(
                    schema_suffix="map_preview_result",
                    action="map_preview",
                    endpoint=ROUTE_PATHS["map_preview"],
                    artifact=map_artifact_info(self.map_artifact_dir),
                    extra={
                        "status": "loaded",
                        "map_name": yaml_path.stem,
                        "map_yaml_name": yaml_path.name,
                        "map_image_name": image_path.name,
                        "resolution": quality.get("resolution"),
                        "origin": quality.get("origin"),
                        "cell_counts": quality.get("cell_counts", {}),
                        "has_free_cells": bool(quality.get("has_free_cells")),
                        "navigation_quality": quality.get("navigation_quality"),
                        "width": image_preview["width"],
                        "height": image_preview["height"],
                        "image_mime_type": image_preview["image_mime_type"],
                        "image_data_url": image_preview["image_data_url"],
                        "source_image_format": image_preview["source_image_format"],
                        "radar_overlay": radar_overlay,
                        "color_overlay": color_overlay,
                        **path_overlay,
                        **target_overlay,
                        "failure_reason": None,
                        "blocked_reasons": [],
                        "command_result": {"mode": "read_only_local_files", "executed": False, "ok": True},
                        "opens_base_uart": False,
                        "sends_motion_commands": False,
                        "publishes_cmd_vel": False,
                        "calls_base_manual": False,
                        "sends_base_motion_commands": False,
                    },
                )
            except Exception as exc:  # noqa: BLE001 - 单张坏图不能阻断 fallback 候选。
                failures.append(f"{yaml_path.name}:{compact_error(exc)}")
        reason = failures[0] if failures else "map_yaml_missing"
        color_overlay = default_map_color_overlay(reason)
        return software_guard_payload(
            schema_suffix="map_preview_result",
            action="map_preview",
            endpoint=ROUTE_PATHS["map_preview"],
            artifact=map_artifact_info(self.map_artifact_dir),
            extra={
                "status": "blocked",
                "failure_reason": reason,
                "blocked_reasons": failures[:8] or [reason],
                "map_name": requested_map_name or "",
                "image_data_url": "",
                "radar_overlay": radar_overlay,
                "color_overlay": color_overlay,
                **path_overlay,
                **target_overlay,
                "command_result": {"mode": "read_only_local_files", "executed": False, "ok": False},
            },
        )

    async def map_proof_refresh(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """触发 no-motion `/map` lifecycle proof，并把失败写成可回放 artifact。"""
        body = body if isinstance(body, dict) else {}
        timeout_s = clamp_float(
            body.get("timeout_s"),
            DEFAULT_MAP_LIFECYCLE_PROOF_REFRESH_TIMEOUT_S,
            10.0,
            180.0,
        )
        command_result = await asyncio.to_thread(
            run_map_lifecycle_proof_helper,
            artifact_path=self.map_lifecycle_proof_artifact_path,
            map_artifact_dir=self.map_artifact_dir,
            timeout_s=timeout_s,
        )
        http_status, latest = self.map_proof_latest()
        payload = software_guard_payload(
            schema_suffix="map_lifecycle_proof_refresh_result",
            action="map_proof_refresh",
            endpoint=ROUTE_PATHS["map_proof_refresh"],
            command_env="built_in_no_motion_map_lifecycle_helper",
            command="o3_map_lifecycle_proof.py",
            command_result=command_result,
            artifact=map_lifecycle_proof_artifact_info(self.map_lifecycle_proof_artifact_path),
            extra={
                "map_artifact": map_artifact_info(self.map_artifact_dir),
                "latest_readback_http_status": http_status,
                "latest_result": latest.get("latest_result"),
                "map_lifecycle_status": self.map_status(),
                "opens_base_uart": False,
                "publishes_cmd_vel": False,
                "calls_base_manual": False,
                "sends_base_motion_commands": False,
                "robot_control_executed": False,
                "safe_to_control": False,
                "transition_to_proven": [
                    "/scan once observed",
                    "/map once observed",
                    "map recorder saves YAML/PGM artifact",
                    f"GET {ROUTE_PATHS['map_proof_latest']} returns the same runtime artifact",
                ],
            },
        )
        contract = map_lifecycle_runtime_readback_contract(latest.get("latest_result"))
        if bool(command_result.get("ok")) and contract.get("not_proven") is False:
            payload.update(contract)
            payload["failure_reason"] = None
            payload["operator_message"] = "map lifecycle proof attached and ready for read-only consumption"
        return payload

    def map_proof_latest(self) -> tuple[int, dict[str, Any]]:
        """只读最近一次 SLAM/map lifecycle proof，不能启动 SLAM 或保存地图。"""
        http_status, payload = read_runtime_artifact_latest(
            self.map_lifecycle_proof_artifact_path,
            artifact_info=map_lifecycle_proof_artifact_info(self.map_lifecycle_proof_artifact_path),
            schema_suffix="map_lifecycle_proof_latest",
            endpoint=ROUTE_PATHS["map_proof_latest"],
            boundary="software_guard_only_not_real_slam_map_or_nav2_consumption",
            source="map_lifecycle_runtime_artifact",
        )
        payload.update(map_lifecycle_runtime_readback_contract(payload.get("latest_result") if isinstance(payload.get("latest_result"), dict) else None))
        return http_status, payload

    async def localize_reset(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """定位 reset 默认走 O10 no-motion helper；只发布一次 /initialpose，不做路径执行。"""
        body = body if isinstance(body, dict) else {}
        timeout_s = clamp_float(body.get("timeout_s"), 30.0, 4.0, 30.0)
        managed_timeout_s = clamp_float(body.get("managed_timeout_s"), 30.0, 4.0, 45.0)
        managed_runtime_opt_in = body.get("managed_runtime_opt_in") is not False
        initialpose_opt_in = body.get("initialpose_opt_in") is not False
        command_result = await asyncio.to_thread(
            run_nav2_runtime_proof_helper,
            artifact_path=self.localization_artifact_path,
            map_proof_path=self.map_lifecycle_proof_artifact_path,
            map_artifact_dir=self.map_artifact_dir,
            timeout_s=timeout_s,
            managed_runtime_opt_in=managed_runtime_opt_in,
            managed_timeout_s=managed_timeout_s,
            managed_map_yaml=str(body.get("managed_map_yaml") or "")[:400],
            initialpose_opt_in=initialpose_opt_in,
            initialpose_x=clamp_float(body.get("initialpose_x"), 0.0, -1000.0, 1000.0),
            initialpose_y=clamp_float(body.get("initialpose_y"), 0.0, -1000.0, 1000.0),
            initialpose_yaw=clamp_float(body.get("initialpose_yaw"), 0.0, -6.283185307179586, 6.283185307179586),
            initialpose_frame_id=str(body.get("initialpose_frame_id") or "map")[:80],
            path_generation_opt_in=False,
            path_generation_timeout_s=4.0,
            path_goal_frame_id="map",
            path_goal_x=0.0,
            path_goal_y=0.0,
            path_goal_yaw=0.0,
        )
        http_status, latest = self.localize_proof_latest()
        latest_result = latest.get("latest_result") if isinstance(latest.get("latest_result"), dict) else None
        proof = latest_result.get("proof") if isinstance(latest_result, dict) and isinstance(latest_result.get("proof"), dict) else {}
        readback_contract = localization_runtime_readback_contract(latest_result)
        evidence_type = latest_proof_value(latest_result, "evidence_type") or "blocked_with_root_cause"
        root_causes = proof.get("root_causes") if isinstance(proof.get("root_causes"), list) else []
        return software_guard_payload(
            schema_suffix="localization_reset_result",
            action="localize_reset",
            endpoint=ROUTE_PATHS["localize_reset"],
            command_env="built_in_no_motion_amcl_nav2_runtime_helper",
            command="o10_amcl_nav2_runtime_proof.py --output runtime/localization_reset_latest.json",
            command_result=command_result,
            artifact=localization_artifact_info(self.localization_artifact_path),
            extra={
                "status": "refreshed" if readback_contract["localization_reset_observed"] else "blocked_with_root_cause",
                "proof_state": readback_contract["proof_state"],
                "evidence_type": evidence_type,
                "requested_pose": {
                    "frame_id": str(body.get("initialpose_frame_id") or "map")[:80],
                    "x": clamp_float(body.get("initialpose_x"), 0.0, -1000.0, 1000.0),
                    "y": clamp_float(body.get("initialpose_y"), 0.0, -1000.0, 1000.0),
                    "yaw": clamp_float(body.get("initialpose_yaw"), 0.0, -6.283185307179586, 6.283185307179586),
                },
                "target_ros2_topic": "/initialpose",
                "proof_artifact": localization_artifact_info(self.localization_artifact_path),
                "managed_runtime_opt_in": managed_runtime_opt_in,
                "managed_timeout_s": managed_timeout_s,
                "initialpose_opt_in": initialpose_opt_in,
                "path_generation_opt_in": False,
                "path_generation_opt_in_ignored": body.get("path_generation_opt_in") is not None,
                "latest_readback_http_status": http_status,
                "latest_result": latest_result,
                "proof_latest": summarize_localization_latest_artifact(self.localization_artifact_path),
                "initialpose_published": readback_contract["initialpose_published"],
                "amcl_pose_observed": readback_contract["amcl_pose_observed"],
                "amcl_pose": readback_contract["amcl_pose"],
                "base_link_to_laser_frame_transform": readback_contract["base_link_to_laser_frame_transform"],
                "localization_tf_observed": readback_contract["localization_tf_observed"],
                "tf_chain_observed": readback_contract["tf_chain_observed"],
                "tf_chain_diagnostics": readback_contract["tf_chain_diagnostics"],
                "tf_topics_observed": readback_contract["tf_topics_observed"],
                "tf_static_observed": readback_contract["tf_static_observed"],
                "tf_frame_inventory": readback_contract["tf_frame_inventory"],
                "amcl_pose_frame_id": readback_contract["amcl_pose_frame_id"],
                "amcl_node_publishers": readback_contract["amcl_node_publishers"],
                "amcl_node_subscribers": readback_contract["amcl_node_subscribers"],
                "amcl_param_probe_ok": readback_contract["amcl_param_probe_ok"],
                "amcl_node_info_observed": readback_contract["amcl_node_info_observed"],
                "amcl_tf_broadcast_param": readback_contract["amcl_tf_broadcast_param"],
                "amcl_frame_params": readback_contract["amcl_frame_params"],
                "amcl_log_tail": readback_contract["amcl_log_tail"],
                "managed_static_tf_processes": readback_contract["managed_static_tf_processes"],
                "static_tf_source_observed": readback_contract["static_tf_source_observed"],
                "tf_source_root_cause_detail": readback_contract["tf_source_root_cause_detail"],
                "amcl_broadcast_conditions": readback_contract["amcl_broadcast_conditions"],
                "map_frame_observed": readback_contract["map_frame_observed"],
                "odom_frame_observed": readback_contract["odom_frame_observed"],
                "amcl_tf_root_cause": readback_contract["amcl_tf_root_cause"],
                "tf_failure_classification": readback_contract["tf_failure_classification"],
                "managed_runtime_started": readback_contract["managed_runtime_started"],
                "managed_runtime_cleanup_ok": readback_contract["managed_runtime_cleanup_ok"],
                "root_causes": root_causes,
                "blockers": readback_contract["blockers"],
                "localization_reset_observed": readback_contract["localization_reset_observed"],
                "opens_base_uart": False,
                "uses_base_uart": False,
                "opens_serial": False,
                "starts_ros2": False,
                "starts_nav2": False,
                "sends_commands": False,
                "sends_motion_commands": False,
                "publishes_cmd_vel": False,
                "calls_base_manual": False,
                "sends_base_motion_commands": False,
                "robot_control_executed": False,
                "safe_to_control": False,
                "hil_pass": False,
                "blocked_commands_not_sent": [
                    "T=1",
                    "T=13",
                    "T=130",
                    "T=131",
                    "/cmd_vel",
                    "/api/base/manual",
                    "/api/nav2/start",
                    "/api/nav2/stop",
                    "navigate_to_pose",
                    "compute_path_to_pose",
                ],
                "blocked_devices_not_opened": ["/dev/ttyS5"],
                "expected_runtime_proof": [
                    "/initialpose once",
                    "/amcl_pose",
                    "tf map->odom",
                    "tf odom->base_link",
                    "tf base_link->laser_frame",
                    "tf map->base_link",
                ],
                "transition_to_proven": [
                    "built-in helper publishes one /initialpose only when initialpose_opt_in is true",
                    "managed runtime is limited to localization graph when opted in",
                    "AMCL pose observed after reset",
                    "localization TF map->odom and map->base_link observed",
                    "artifact update at localization_artifact.path",
                    f"GET {ROUTE_PATHS['localize_proof_latest']} returns AMCL/TF material",
                ],
            },
        )

    def localize_proof_latest(self) -> tuple[int, dict[str, Any]]:
        """只读定位 runtime proof，避免 status 接口误发布 /initialpose。"""
        http_status, payload = read_runtime_artifact_latest(
            self.localization_artifact_path,
            artifact_info=localization_artifact_info(self.localization_artifact_path),
            schema_suffix="localization_proof_latest",
            endpoint=ROUTE_PATHS["localize_proof_latest"],
            boundary="software_guard_only_not_real_amcl_localization_reset",
            source="localization_runtime_artifact",
        )
        latest = payload.get("latest_result") if isinstance(payload.get("latest_result"), dict) else None
        payload.update(localization_runtime_readback_contract(latest))
        return http_status, payload

    async def nav2_proof_refresh(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """触发 no-motion AMCL/Nav2 proof refresh；失败也必须写成 latest artifact。"""
        body = body if isinstance(body, dict) else {}
        timeout_s = clamp_float(
            body.get("timeout_s"),
            DEFAULT_NAV2_RUNTIME_PROOF_REFRESH_TIMEOUT_S,
            4.0,
            30.0,
        )
        managed_runtime_opt_in = bool(body.get("managed_runtime_opt_in") is True)
        initialpose_opt_in = bool(body.get("initialpose_opt_in") is True)
        # O11-owned runtime 下这两个门禁必须显式为 true，缺失时 helper 仍会执行只读/NO-GO 路径。
        reuse_existing_lidar_lifecycle = bool(body.get("reuse_existing_lidar_lifecycle") is True)
        initialpose_canonical_free_cell_opt_in = bool(
            body.get("initialpose_canonical_free_cell_opt_in") is True
        )
        proof_contract_errors: list[str] = []
        if managed_runtime_opt_in and not reuse_existing_lidar_lifecycle:
            # managed proof 与 O11 同窗时只能复用既有 LiDAR，缺 flag 必须在创建子进程前拒绝。
            proof_contract_errors.append("reuse_existing_lidar_lifecycle_required_for_managed_runtime")
        if initialpose_opt_in and not initialpose_canonical_free_cell_opt_in:
            # initialpose 写 topic 前必须绑定 canonical free-cell 审计，禁止回退请求中的任意坐标。
            proof_contract_errors.append("initialpose_canonical_free_cell_opt_in_required")
        if proof_contract_errors:
            return software_guard_payload(
                schema_suffix="nav2_runtime_proof_refresh_result",
                action="nav2_proof_refresh",
                endpoint=ROUTE_PATHS["nav2_proof_refresh"],
                artifact=nav2_lifecycle_artifact_info(self.nav2_lifecycle_artifact_path),
                extra={
                    "status": "blocked_proof_request_contract",
                    "proof_state": "blocked_proof_request_contract",
                    "evidence_type": "blocked_with_root_cause",
                    "failure_reason": proof_contract_errors[0],
                    "root_causes": [
                        {"layer": "proof_request_contract", "reason": reason}
                        for reason in proof_contract_errors
                    ],
                    "blockers": proof_contract_errors,
                    # invocation_count=0 是请求门禁证据，不能用旧 latest artifact 覆盖。
                    "managed_runtime_opt_in": managed_runtime_opt_in,
                    "reuse_existing_lidar_lifecycle": reuse_existing_lidar_lifecycle,
                    "initialpose_opt_in": initialpose_opt_in,
                    "initialpose_canonical_free_cell_opt_in": initialpose_canonical_free_cell_opt_in,
                    "helper_invocation_count": 0,
                    "sends_motion_commands": False,
                    "publishes_cmd_vel": False,
                    "calls_base_manual": False,
                    "uses_base_uart": False,
                    "robot_control_executed": False,
                    "safe_to_control": False,
                    "delivery_success": False,
                    "hil_pass": False,
                    "transition_to_proven": [
                        # 修复动作只补 ownership/canonical opt-in，不扩大运动或控制权限。
                        "set reuse_existing_lidar_lifecycle=true when managed_runtime_opt_in=true",
                        "set initialpose_canonical_free_cell_opt_in=true when initialpose_opt_in=true",
                    ],
                },
            )
        command_result = await asyncio.to_thread(
            run_nav2_runtime_proof_helper,
            artifact_path=self.nav2_lifecycle_artifact_path,
            map_proof_path=self.map_lifecycle_proof_artifact_path,
            map_artifact_dir=self.map_artifact_dir,
            timeout_s=timeout_s,
            managed_runtime_opt_in=managed_runtime_opt_in,
            managed_timeout_s=clamp_float(body.get("managed_timeout_s"), timeout_s, 4.0, 45.0),
            managed_map_yaml=str(body.get("managed_map_yaml") or "")[:400],
            initialpose_opt_in=initialpose_opt_in,
            initialpose_x=clamp_float(body.get("initialpose_x"), 0.0, -1000.0, 1000.0),
            initialpose_y=clamp_float(body.get("initialpose_y"), 0.0, -1000.0, 1000.0),
            initialpose_yaw=clamp_float(body.get("initialpose_yaw"), 0.0, -6.283185307179586, 6.283185307179586),
            initialpose_frame_id=str(body.get("initialpose_frame_id") or "map")[:80],
            path_generation_opt_in=bool(body.get("path_generation_opt_in") is True),
            path_generation_timeout_s=clamp_float(body.get("path_generation_timeout_s"), timeout_s, 4.0, 45.0),
            path_goal_frame_id=str(body.get("path_goal_frame_id") or "map")[:80],
            path_goal_x=clamp_float(body.get("path_goal_x"), 0.8, -1000.0, 1000.0),
            # 固定短路径终点与已审计 route 合同一致，避免请求省略 y 时退回旧坐标。
            path_goal_y=clamp_float(body.get("path_goal_y"), 0.25, -1000.0, 1000.0),
            path_goal_yaw=clamp_float(body.get("path_goal_yaw"), 0.0, -6.283185307179586, 6.283185307179586),
            reuse_existing_lidar_lifecycle=reuse_existing_lidar_lifecycle,
            initialpose_canonical_free_cell_opt_in=initialpose_canonical_free_cell_opt_in,
        )
        http_status, latest = self.nav2_proof_latest()
        proof = latest.get("latest_result", {}).get("proof") if isinstance(latest.get("latest_result"), dict) else {}
        proof_status = proof.get("status") if isinstance(proof, dict) else "not_proven"
        latest_result = latest.get("latest_result") if isinstance(latest.get("latest_result"), dict) else {}
        # refresh 允许 helper 在 no-motion 边界内短暂拉起 managed runtime。
        # readback 必须显式回传这个事实，避免 body opt-in 与结果层状态打架。
        managed_runtime_started = bool(proof.get("managed_runtime_started")) if isinstance(proof, dict) else False
        # collector 可能把 evidence_type 放在顶层或 proof 内；两处都缺失时必须保守 blocked。
        evidence_type = latest_proof_value(latest_result, "evidence_type") or "blocked_with_root_cause"
        return software_guard_payload(
            schema_suffix="nav2_runtime_proof_refresh_result",
            action="nav2_proof_refresh",
            endpoint=ROUTE_PATHS["nav2_proof_refresh"],
            command_env="built_in_no_motion_amcl_nav2_runtime_helper",
            command="o10_amcl_nav2_runtime_proof.py",
            command_result=command_result,
            artifact=nav2_lifecycle_artifact_info(self.nav2_lifecycle_artifact_path),
            extra={
                "status": "refreshed" if evidence_type == "robot_runtime_material" else "blocked_with_root_cause",
                "proof_state": proof_status,
                "evidence_type": evidence_type,
                "managed_runtime_opt_in": managed_runtime_opt_in,
                "reuse_existing_lidar_lifecycle": reuse_existing_lidar_lifecycle,
                "managed_timeout_s": clamp_float(body.get("managed_timeout_s"), timeout_s, 4.0, 45.0),
                "managed_map_yaml": str(body.get("managed_map_yaml") or "")[:400],
                "initialpose_opt_in": initialpose_opt_in,
                "initialpose_canonical_free_cell_opt_in": initialpose_canonical_free_cell_opt_in,
                "path_generation_opt_in": bool(body.get("path_generation_opt_in") is True),
                "path_generation_timeout_s": clamp_float(body.get("path_generation_timeout_s"), timeout_s, 4.0, 45.0),
                "path_goal_frame_id": str(body.get("path_goal_frame_id") or "map")[:80],
                "path_goal_x": clamp_float(body.get("path_goal_x"), 0.8, -1000.0, 1000.0),
                # readback 必须回显实际采用的固定 y，便于冻结请求与 helper argv 对照。
                "path_goal_y": clamp_float(body.get("path_goal_y"), 0.25, -1000.0, 1000.0),
                "path_goal_yaw": clamp_float(body.get("path_goal_yaw"), 0.0, -6.283185307179586, 6.283185307179586),
                "latest_readback_http_status": http_status,
                "latest_result": latest.get("latest_result"),
                "proof_latest": summarize_nav2_lifecycle_latest_artifact(self.nav2_lifecycle_artifact_path),
                "map_readiness": build_amcl_nav2_readiness_from_map_proof(
                    self.map_lifecycle_proof_artifact_path,
                    self.map_artifact_dir,
                ),
                "opens_base_uart": False,
                "sends_commands": False,
                "sends_motion_commands": False,
                "publishes_cmd_vel": False,
                "calls_base_manual": False,
                "sends_base_motion_commands": False,
                "starts_ros2": managed_runtime_opt_in,
                "starts_nav2": managed_runtime_started,
                "robot_control_executed": False,
                "safe_to_control": False,
                "hil_pass": False,
                "path_generated": bool(proof.get("path_generated")) if isinstance(proof, dict) else False,
                "path_execution_attempted": False,
                "path_generation_requested": bool(proof.get("path_generation_requested")) if isinstance(proof, dict) else False,
                "path_generation_attempted": bool(proof.get("path_generation_attempted")) if isinstance(proof, dict) else False,
                "path_generation_service_name": proof.get("path_generation_service_name") if isinstance(proof, dict) else None,
                "path_generation_service_available": bool(proof.get("path_generation_service_available")) if isinstance(proof, dict) else False,
                "path_generation_succeeded": bool(proof.get("path_generation_succeeded")) if isinstance(proof, dict) else False,
                "path_point_count": int(proof.get("path_point_count") or 0) if isinstance(proof, dict) else 0,
                "path_goal_request": proof.get("path_goal_request") if isinstance(proof, dict) else None,
                "path_goal_response": proof.get("path_goal_response") if isinstance(proof, dict) else None,
                "path_generation_boundary": proof.get("path_generation_boundary") if isinstance(proof, dict) else None,
                "planner_server_active": bool(proof.get("planner_server_active")) if isinstance(proof, dict) else False,
                "controller_server_active": bool(proof.get("controller_server_active")) if isinstance(proof, dict) else False,
                "controller_server_requested": bool(proof.get("controller_server_requested")) if isinstance(proof, dict) else False,
                "planner_readiness_summary": proof.get("planner_readiness_summary") if isinstance(proof, dict) else None,
                "read_only_existing_ros_graph": not managed_runtime_opt_in,
                "blocked_commands_not_sent": ["T=1", "T=13", "T=130", "T=131", "/cmd_vel", "/api/base/manual"],
                "transition_to_proven": [
                    "managed runtime or existing graph keeps map_server/amcl active without /dev/ttyS5",
                    "/scan and /map observed in the same no-motion ROS2 graph",
                    "/amcl_pose observed when initialpose opt-in is requested",
                    "explicit opt-in path generation may call ComputePathToPose without publishing /cmd_vel",
                    "cleanup leaves no managed runtime process group behind",
                    f"GET {ROUTE_PATHS['nav2_proof_latest']} returns the same artifact",
                ],
            },
        )

    def nav2_proof_latest(self) -> tuple[int, dict[str, Any]]:
        """只读 AMCL/Nav2 proof artifact，不探 ROS graph，不发布 initialpose/goal。"""
        http_status, payload = read_runtime_artifact_latest(
            self.nav2_lifecycle_artifact_path,
            artifact_info=nav2_lifecycle_artifact_info(self.nav2_lifecycle_artifact_path),
            schema_suffix="nav2_runtime_proof_latest",
            endpoint=ROUTE_PATHS["nav2_proof_latest"],
            boundary="software_guard_only_not_real_nav2_path_execution_or_delivery",
            source="nav2_lifecycle_runtime_artifact",
        )
        latest = payload.get("latest_result") if isinstance(payload.get("latest_result"), dict) else None
        readback = localization_runtime_readback_contract(latest)
        # 保留 nav2 proof latest 的原始 status，只提升 no-motion readback 证据字段。
        for key in (
            "base_link_to_laser_frame_transform",
            "tf_chain_observed",
            "tf_chain_diagnostics",
            "tf_topics_observed",
            "tf_static_observed",
            "tf_frame_inventory",
            "localization_tf_observed",
            "amcl_pose",
            "amcl_pose_observed",
            "last_phase",
            "last_successful_phase",
            "partial_artifact_preserved",
        ):
            payload[key] = readback.get(key)
        return http_status, payload

    async def nav2_goal_execute(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """显式执行 bounded NavigateToPose；超时自动 cancel，不宣称 delivery success。"""
        body = body if isinstance(body, dict) else {}
        if body.get("confirm_navigation_execution") is not True:
            return software_guard_payload(
                schema_suffix="nav2_goal_execution_result",
                action="nav2_goal_execute",
                endpoint=ROUTE_PATHS["nav2_goal_execute"],
                artifact=nav2_goal_execution_artifact_info(self.nav2_goal_execution_artifact_path),
                extra={
                    "status": "blocked_missing_confirm_navigation_execution",
                    "failure_reason": "confirm_navigation_execution_required",
                    "command_result": {"executed": False, "ok": False},
                    "robot_control_executed": False,
                },
            )
        goal_frame_id = str(body.get("goal_frame_id") or "map")[:40]
        goal_x = clamp_float(body.get("goal_x"), 0.8, -3.0, 3.0)
        goal_y = clamp_float(body.get("goal_y"), 0.0, -3.0, 3.0)
        goal_yaw = clamp_float(body.get("goal_yaw"), 0.0, -math.pi, math.pi)
        route_preview = body.get("route_preview") if isinstance(body.get("route_preview"), dict) else {}
        route_preview_point_count = int(clamp_float(body.get("route_preview_point_count", route_preview.get("point_count")), 0.0, 0.0, 10000.0))
        route_preview_source_point_count = int(
            clamp_float(
                body.get("route_preview_source_point_count", route_preview.get("source_point_count", route_preview_point_count)),
                float(route_preview_point_count),
                0.0,
                100000.0,
            )
        )
        route_preview_frame_id = str(body.get("route_preview_frame_id") or route_preview.get("frame_id") or goal_frame_id)[:40]
        def route_optional_float(value: Any) -> float | None:
            # 路线起点只做证据回显；缺失时保留 null，不能替代真实定位或目标点。
            try:
                parsed = float(value)
            except (TypeError, ValueError):
                return None
            return min(max(parsed, -1000.0), 1000.0)
        route_start_x = route_optional_float(body.get("route_start_x", route_preview.get("start_x")))
        route_start_y = route_optional_float(body.get("route_start_y", route_preview.get("start_y")))
        route_goal_x = clamp_float(body.get("route_goal_x", route_preview.get("goal_x")), goal_x, -1000.0, 1000.0)
        route_goal_y = clamp_float(body.get("route_goal_y", route_preview.get("goal_y")), goal_y, -1000.0, 1000.0)
        result_timeout_s = clamp_float(body.get("result_timeout_s"), 8.0, 2.0, 20.0)
        # 实车 Nav2 托管 runtime 在 lifecycle active 后仍可能需要数秒返回 goal response；窗口太短会误判 goal_handle_missing。
        server_timeout_s = clamp_float(body.get("server_timeout_s"), 12.0, 1.0, 20.0)
        latest_nav2_http_status, latest_nav2 = self.nav2_proof_latest()
        latest_nav2_result = latest_nav2.get("latest_result") if isinstance(latest_nav2.get("latest_result"), dict) else {}
        latest_nav2_proof = latest_nav2_result.get("proof") if isinstance(latest_nav2_result.get("proof"), dict) else {}
        default_map_yaml = str(latest_nav2_proof.get("managed_runtime_map_yaml") or "")
        managed_runtime_opt_in = body.get("managed_runtime_opt_in") is not False
        managed_map_yaml = str(body.get("managed_map_yaml") or default_map_yaml)[:400]
        # O11 自己轮询 Nav2 lifecycle active；startup 只保留进程组启动余量。
        managed_startup_s = clamp_float(body.get("managed_startup_s"), 2.0, 0.0, 5.0)
        # O11 只看 lifecycle manager 日志；现场慢启动时给 Nav2 执行层更宽的 active 窗口。
        managed_ready_timeout_s = clamp_float(body.get("managed_ready_timeout_s"), 90.0, 10.0, 90.0)
        raw_base_command_mode = body.get("base_command_mode") or body.get("nav2_base_command_mode")
        request_base_command_mode = str(raw_base_command_mode or "").strip().lower()
        if request_base_command_mode:
            # 显式请求只接受白名单；非法值仍按配置默认，不从旧 latest 偷偷切模式。
            nav2_base_command_mode = (
                request_base_command_mode if request_base_command_mode in ALLOWED_NAV2_BASE_COMMAND_MODES else self.nav2_base_command_mode
            )
        else:
            # PC 以外的调用方可能不传 base_command_mode；这里复用 latest next mode，保证 ROS/T=13 零轮速后可自动切 SPEED/T=1。
            _, latest_execution = self.nav2_goal_execution_latest()
            nav2_base_command_mode = nav2_goal_execute_base_command_mode_from_latest(self.nav2_base_command_mode, latest_execution)
        command_result = await asyncio.to_thread(
            run_nav2_goal_execution_helper,
            artifact_path=self.nav2_goal_execution_artifact_path,
            goal_frame_id=goal_frame_id,
            goal_x=goal_x,
            goal_y=goal_y,
            goal_yaw=goal_yaw,
            result_timeout_s=result_timeout_s,
            server_timeout_s=server_timeout_s,
            managed_runtime_opt_in=managed_runtime_opt_in,
            managed_map_yaml=managed_map_yaml,
            managed_startup_s=managed_startup_s,
            managed_ready_timeout_s=managed_ready_timeout_s,
            base_command_mode=nav2_base_command_mode,
        )
        http_status, latest = self.nav2_goal_execution_latest()
        latest_result = latest.get("latest_result") if isinstance(latest.get("latest_result"), dict) else {}
        latest_status = latest_result.get("status") if isinstance(latest_result, dict) else "not_loaded"
        nav2_execution_proven = nav2_goal_execution_proven_from_latest_result(latest_result)
        nav2_not_proven = nav2_goal_execution_not_proven_reasons(latest_result, nav2_execution_proven)
        return software_guard_payload(
            schema_suffix="nav2_goal_execution_result",
            action="nav2_goal_execute",
            endpoint=ROUTE_PATHS["nav2_goal_execute"],
            command_env="built_in_bounded_navigate_to_pose_helper",
            command="o11_nav2_goal_execution_proof.py",
            command_result=command_result,
            artifact=nav2_goal_execution_artifact_info(self.nav2_goal_execution_artifact_path),
            extra={
                "status": latest_status,
                "goal_request": {
                    "goal_frame_id": goal_frame_id,
                    "goal_x": goal_x,
                    "goal_y": goal_y,
                    "goal_yaw": goal_yaw,
                    "result_timeout_s": result_timeout_s,
                    "managed_runtime_opt_in": managed_runtime_opt_in,
                    "managed_map_yaml": managed_map_yaml,
                    "managed_startup_s": managed_startup_s,
                    "managed_ready_timeout_s": managed_ready_timeout_s,
                    "base_command_mode": nav2_base_command_mode,
                    "route_preview": {
                        "point_count": route_preview_point_count,
                        "source_point_count": route_preview_source_point_count,
                        "frame_id": route_preview_frame_id,
                        "start_x": route_start_x,
                        "start_y": route_start_y,
                        "goal_x": route_goal_x,
                        "goal_y": route_goal_y,
                    },
                    "route_preview_point_count": route_preview_point_count,
                    "route_preview_source_point_count": route_preview_source_point_count,
                    "route_preview_frame_id": route_preview_frame_id,
                    "route_start_x": route_start_x,
                    "route_start_y": route_start_y,
                    "route_goal_x": route_goal_x,
                    "route_goal_y": route_goal_y,
                    "managed_map_yaml_source": "latest_nav2_proof_managed_runtime_map_yaml" if managed_map_yaml == default_map_yaml else "request_body",
                    "latest_nav2_readback_http_status": latest_nav2_http_status,
                },
                "latest_readback_http_status": http_status,
                "latest_result": latest_result,
                "goal_accepted": bool(latest_result.get("goal_accepted")) if isinstance(latest_result, dict) else False,
                "result_received": bool(latest_result.get("result_received")) if isinstance(latest_result, dict) else False,
                "result_status": latest_result.get("result_status") if isinstance(latest_result, dict) else "not_loaded",
                "cancel_requested": bool(latest_result.get("cancel_requested")) if isinstance(latest_result, dict) else False,
                "feedback_sample_count": int(latest_result.get("feedback_sample_count") or 0) if isinstance(latest_result, dict) else 0,
                "nav2_goal_execution_proven": nav2_execution_proven,
                "sends_commands": bool(latest_result.get("sends_motion_commands")) if isinstance(latest_result, dict) else False,
                "sends_motion_commands": bool(latest_result.get("sends_motion_commands")) if isinstance(latest_result, dict) else False,
                "sends_base_motion_commands": bool(latest_result.get("sends_base_motion_commands")) if isinstance(latest_result, dict) else False,
                "uses_base_uart": bool(latest_result.get("uses_base_uart")) if isinstance(latest_result, dict) else False,
                "publishes_cmd_vel": latest_result.get("publishes_cmd_vel") if isinstance(latest_result, dict) else False,
                "calls_base_manual": bool(latest_result.get("calls_base_manual")) if isinstance(latest_result, dict) else False,
                "hil_pass": bool(latest_result.get("hil_pass")) and nav2_execution_proven if isinstance(latest_result, dict) else False,
                "blocked_devices_not_touched": [],
                "blocked_commands_not_sent": [],
                "delivery_success": False,
                "safe_to_control": False,
                "primary_actions_enabled": False,
                "robot_control_executed": bool(latest_result.get("robot_control_executed")) if isinstance(latest_result, dict) else False,
                "not_proven": nav2_not_proven,
            },
        )

    def nav2_goal_execution_latest(self) -> tuple[int, dict[str, Any]]:
        """只读最近一次 NavigateToPose 执行 artifact，不触发 action。"""
        http_status, payload = read_runtime_artifact_latest(
            self.nav2_goal_execution_artifact_path,
            artifact_info=nav2_goal_execution_artifact_info(self.nav2_goal_execution_artifact_path),
            schema_suffix="nav2_goal_execution_latest",
            endpoint=ROUTE_PATHS["nav2_goal_execution_latest"],
            boundary="readback_only_not_delivery_success",
            source="nav2_goal_execution_artifact",
        )
        return http_status, enrich_nav2_goal_execution_latest_payload(payload)

    def delivery_complete(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """确认交付完成；只合成 Nav2 latest 与 operator report latest，不触发机器人动作。"""
        request = body if isinstance(body, dict) else {}
        nav2_http_status, nav2_latest = self.nav2_goal_execution_latest()
        operator_http_status, operator_latest = self.operator_report_latest()
        return build_delivery_completion_payload(
            path=self.delivery_completion_artifact_path,
            request=request,
            nav2_http_status=nav2_http_status,
            nav2_latest=nav2_latest,
            operator_http_status=operator_http_status,
            operator_latest=operator_latest,
        )

    def delivery_latest(self) -> tuple[int, dict[str, Any]]:
        """只读交付完成 latest artifact。"""
        return read_delivery_completion_latest_artifact(self.delivery_completion_artifact_path)

    def free_roam_autonomy_latest(self) -> tuple[int, dict[str, Any]]:
        """只读自动扫图 runtime artifact，不探 ROS graph，不发布 /cmd_vel。"""
        http_status, payload = read_runtime_artifact_latest(
            self.free_roam_autonomy_artifact_path,
            artifact_info=free_roam_autonomy_artifact_info(self.free_roam_autonomy_artifact_path),
            schema_suffix="free_roam_autonomy_latest",
            endpoint=ROUTE_PATHS["free_roam_autonomy_latest"],
            boundary="readback_only_free_roam_autonomy_not_unlocked",
            source="free_roam_autonomy_runtime_artifact",
        )
        latest = payload.get("latest_result") if isinstance(payload.get("latest_result"), dict) else {}
        decision = latest.get("decision") if isinstance(latest.get("decision"), dict) else {}
        snapshot = latest.get("snapshot") if isinstance(latest.get("snapshot"), dict) else {}
        runtime_artifact_proven = (
            http_status == 200
            and isinstance(latest, dict)
            and latest.get("schema") == "trashbot.free_roam_autonomy.runtime.v1"
        )
        camera = {
            "ready": False,
            "status": "deferred_to_camera_health_endpoint",
            "source_readiness": "not_checked_by_free_roam_latest",
            "missing": ["camera_first_frame_not_observed"],
            "endpoint": ROUTE_PATHS["camera_health"],
            "reason": "free_roam_latest_is_artifact_only_and_must_not_block_on_camera_http",
        }
        scan_proof_latest = summarize_lidar_scan_proof_latest_artifact(self.lidar_scan_proof_artifact_path)
        latest_scan_proof = build_radar_latest_scan_proof_status(scan_proof_latest)
        lidar_age_s = finite_lidar_scan_number(snapshot.get("lidar_age_s"))
        lidar_min_distance_m = finite_lidar_scan_number(snapshot.get("lidar_min_distance_m"))
        # latest endpoint 不能调用 free_roam_runtime_lidar_readiness()，否则会递归回到本函数。
        runtime_lidar_ready = (
            runtime_artifact_proven
            and lidar_age_s is not None
            and lidar_age_s <= 1.5
            and lidar_min_distance_m is not None
        )
        # 这里只消费已落盘 proof 和 free-roam artifact，避免 latest 被 lifecycle/status 慢读拖死。
        radar_proof_ready = bool(latest_scan_proof.get("fresh_while_observed"))
        radar_ready = radar_proof_ready or runtime_lidar_ready
        camera_missing = camera.get("missing") if isinstance(camera.get("missing"), list) else ["camera_not_ready"]
        mapping_missing: list[str] = []
        if not camera.get("ready"):
            mapping_missing.extend(str(item) for item in camera_missing)
        if not radar_ready:
            mapping_missing.append("radar_scan_proof_not_fresh")
        mapping_missing = list(dict.fromkeys(mapping_missing))
        mapping_ready = not mapping_missing
        payload.update(
            {
                "runtime_status": "loaded" if http_status == 200 else "not_loaded",
                "free_roam_runtime_artifact_proven": runtime_artifact_proven,
                "free_roam_state_machine_observed": runtime_artifact_proven,
                "ros2_runtime_proven": runtime_artifact_proven,
                "free_roam_motion_start_ready": True,
                "free_move_start_ready": True,
                "motion_start_ready": True,
                "motion_without_radar_allowed": True,
                "free_move_without_camera_allowed": True,
                "free_roam_motion_minimal_precheck_plain": "自由移动只要求现场安全确认和停止兜底；相机、雷达、地图记录只影响建图验收。",
                "mapping_readiness": {
                    "ready": mapping_ready,
                    "missing": mapping_missing,
                    "requires_camera_first_frame": True,
                    "requires_fresh_radar_scan": True,
                    "free_move_allowed_when_mapping_not_ready": True,
                },
                "free_roam_mapping_start_ready": mapping_ready,
                "free_roam_mapping_start_missing_reasons": mapping_missing,
                "free_roam_mapping_ready": mapping_ready,
                "free_roam_mapping_missing_reasons": mapping_missing,
                "free_roam_mapping_start_plain": (
                    "画面和雷达已 ready；勾选安全确认后可以启动建图。"
                    if mapping_ready
                    else f"建图启动未就绪，还差 {','.join(mapping_missing)}；低速自由移动不受影响。"
                ),
                "free_roam_mapping_start_next_action": (
                    "勾选现场安全确认后启动建图。"
                    if mapping_ready
                    else "先补齐画面首帧和雷达新鲜扫描；需要移动时可先勾安全确认低速自由移动。"
                ),
                "camera_readiness": camera,
                "radar_readiness": {
                    "ready": radar_ready,
                    "proof_ready": radar_proof_ready,
                    "runtime_scan_ready": runtime_lidar_ready,
                    "lifecycle_running": "not_checked_by_free_roam_latest",
                    "lifecycle_state": "not_checked_by_free_roam_latest",
                    "latest_scan_proof_fresh": bool(latest_scan_proof.get("fresh_while_observed")),
                    "latest_scan_proof_state": latest_scan_proof.get("state"),
                    "latest_scan_proof_failure_reason": latest_scan_proof.get("failure_reason"),
                    "scan_proof_latest": scan_proof_latest,
                    "lidar_age_s": lidar_age_s,
                    "lidar_min_distance_m": lidar_min_distance_m,
                },
                "decision_state": decision.get("state") or "not_loaded",
                "decision_reason": decision.get("reason") or "not_loaded",
                "stop_required": bool(decision.get("stop_required")) if isinstance(decision, dict) else True,
                "artifact_only": bool(latest.get("artifact_only")) if isinstance(latest, dict) else True,
                "cmd_vel_publish_enabled": bool(latest.get("cmd_vel_publish_enabled")) if isinstance(latest, dict) else False,
                "safe_to_control": False,
                "primary_actions_enabled": False,
                "publishes_cmd_vel": False,
                "sends_commands": False,
                "sends_motion_commands": False,
                "robot_control_executed": False,
                "delivery_success": False,
            }
        )
        return http_status, payload

    def free_roam_autonomy_status(self) -> dict[str, Any]:
        """自动扫图状态给 PC 消费；有 artifact 也继续保持 fail-closed。"""
        http_status, payload = self.free_roam_autonomy_latest()
        latest = payload.get("latest_result") if isinstance(payload.get("latest_result"), dict) else {}
        decision = latest.get("decision") if isinstance(latest.get("decision"), dict) else {}
        snapshot = latest.get("snapshot") if isinstance(latest.get("snapshot"), dict) else {}
        map_metrics = latest.get("map_metrics") if isinstance(latest.get("map_metrics"), dict) else {}
        runtime_artifact_proven = bool(payload.get("free_roam_runtime_artifact_proven"))
        try:
            sensor_readiness = self.free_roam_motion_readiness()
        except Exception as exc:  # noqa: BLE001 - status 也必须 fail-closed 返回，不能因为 readiness 慢读无响应。
            sensor_readiness = {
                "ready": True,
                "free_move_ready": True,
                "motion_without_radar_allowed": True,
                "free_move_without_camera_allowed": True,
                "mapping_readiness": {
                    "ready": False,
                    "missing": ["sensor_readiness_unavailable"],
                    "requires_camera_first_frame": True,
                    "requires_fresh_radar_scan": True,
                    "free_move_allowed_when_mapping_not_ready": True,
                },
                "failure_reason": compact_error(exc),
            }
        mapping_readiness = sensor_readiness.get("mapping_readiness") if isinstance(sensor_readiness.get("mapping_readiness"), dict) else {}
        mapping_ready = bool(mapping_readiness.get("ready"))
        mapping_missing = (
            mapping_readiness.get("missing")
            if isinstance(mapping_readiness.get("missing"), list)
            else payload.get("free_roam_mapping_start_missing_reasons", [])
        )
        return {
            "schema": f"{SCHEMA}.free_roam_autonomy_status",
            "generated_at_ms": now_ms(),
            "status": "artifact_loaded" if http_status == 200 else "artifact_missing",
            "http_status": http_status,
            "latest": payload,
            "artifact": free_roam_autonomy_artifact_info(self.free_roam_autonomy_artifact_path),
            "free_roam_runtime_artifact_proven": runtime_artifact_proven,
            "free_roam_state_machine_observed": runtime_artifact_proven,
            "ros2_runtime_proven": runtime_artifact_proven,
            "decision_state": decision.get("state") or "not_loaded",
            "decision_reason": decision.get("reason") or "not_loaded",
            "decision_gates": decision.get("gates") if isinstance(decision.get("gates"), list) else [],
            "free_roam_motion_start_ready": bool(sensor_readiness.get("free_move_ready", payload.get("free_roam_motion_start_ready"))),
            "free_move_start_ready": bool(sensor_readiness.get("free_move_ready", payload.get("free_move_start_ready"))),
            "motion_without_radar_allowed": bool(sensor_readiness.get("motion_without_radar_allowed", payload.get("motion_without_radar_allowed"))),
            "free_move_without_camera_allowed": bool(sensor_readiness.get("free_move_without_camera_allowed", payload.get("free_move_without_camera_allowed"))),
            "mapping_readiness": mapping_readiness,
            "free_roam_mapping_start_ready": mapping_ready,
            "free_roam_mapping_start_missing_reasons": list(dict.fromkeys(str(item) for item in mapping_missing)),
            "free_roam_motion_minimal_precheck_plain": payload.get("free_roam_motion_minimal_precheck_plain"),
            "free_roam_mapping_start_plain": (
                "画面和雷达已 ready；勾选安全确认后可以启动建图。"
                if mapping_ready
                else f"建图启动未就绪，还差 {','.join(str(item) for item in mapping_missing)}；低速自由移动不受影响。"
            ),
            "free_roam_mapping_start_next_action": (
                "勾选现场安全确认后启动建图。"
                if mapping_ready
                else "先补齐画面首帧和雷达新鲜扫描；需要移动时可先勾安全确认低速自由移动。"
            ),
            "sensor_readiness": sensor_readiness,
            "snapshot": snapshot,
            "map_metrics": map_metrics,
            "artifact_only": bool(latest.get("artifact_only")) if isinstance(latest, dict) else True,
            "cmd_vel_publish_enabled": bool(latest.get("cmd_vel_publish_enabled")) if isinstance(latest, dict) else False,
            "routes": {
                "latest": ROUTE_PATHS["free_roam_autonomy_latest"],
                "start": ROUTE_PATHS["free_roam_autonomy_start"],
                "stop": ROUTE_PATHS["free_roam_autonomy_stop"],
            },
            "safe_to_control": False,
            "primary_actions_enabled": False,
            "publishes_cmd_vel": False,
            "robot_control_executed": False,
            "delivery_success": False,
            "not_proven": http_status != 200,
            "software_guard": True,
        }

    def free_roam_runtime_lidar_readiness(self) -> dict[str, Any]:
        """建图雷达 readiness 优先复用 free-roam 节点的实时 /scan 快照。"""
        http_status, payload = self.free_roam_autonomy_latest()
        latest = payload.get("latest_result") if isinstance(payload.get("latest_result"), dict) else {}
        snapshot = latest.get("snapshot") if isinstance(latest.get("snapshot"), dict) else {}
        decision = latest.get("decision") if isinstance(latest.get("decision"), dict) else {}
        gates = decision.get("gates") if isinstance(decision.get("gates"), list) else []
        lidar_gate = next(
            (
                gate
                for gate in gates
                if isinstance(gate, dict) and gate.get("id") == "lidar_fresh"
            ),
            {},
        )
        lidar_age_s = finite_lidar_scan_number(snapshot.get("lidar_age_s"))
        lidar_min_distance_m = finite_lidar_scan_number(snapshot.get("lidar_min_distance_m"))
        # free_roam_autonomy_node 默认同样使用 1.5s 雷达新鲜度；这里不猜测硬件，只消费该 runtime 事实。
        fresh_timeout_s = 1.5
        ready = (
            http_status == 200
            and lidar_age_s is not None
            and lidar_age_s <= fresh_timeout_s
            and lidar_min_distance_m is not None
        )
        return {
            "ready": ready,
            "source": "free_roam_runtime_scan_snapshot",
            "http_status": http_status,
            "runtime_status": payload.get("runtime_status") or "not_loaded",
            "lidar_age_s": lidar_age_s,
            "lidar_min_distance_m": lidar_min_distance_m,
            "fresh_timeout_s": fresh_timeout_s,
            "gate_state": lidar_gate.get("state") if isinstance(lidar_gate, dict) else "not_loaded",
            "gate_evidence": lidar_gate.get("evidence") if isinstance(lidar_gate, dict) else "not_loaded",
            "artifact_status": (payload.get("artifact") or {}).get("status") if isinstance(payload.get("artifact"), dict) else "not_loaded",
        }

    def camera_motion_readiness(self) -> dict[str, Any]:
        """建图验收前同步确认相机首帧；自由移动本身不把相机作为硬门禁。"""
        import urllib.error
        import urllib.request

        health_url = urljoin(self.camera_base_url + "/", "health")
        try:
            # start 路径不能长期卡住 ROS 参数写入；2s 足够判断本机 8088 是否健康。
            with urllib.request.urlopen(health_url, timeout=2.0) as response:  # noqa: S310 - URL 来自上车端固定配置。
                text = response.read(256 * 1024).decode("utf-8", errors="replace")
                parsed = json.loads(text) if text else {}
                payload = parsed if isinstance(parsed, dict) else {"error": "camera_health_not_object"}
                http_status = int(response.status)
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            return {
                "ready": False,
                "http_status": None,
                "health_url": health_url,
                "status": "blocked",
                "missing": ["camera_health_unreachable"],
                "failure_reason": compact_error(exc),
            }

        status = str(payload.get("status") or "not_loaded")
        video_source = str(payload.get("video_source") or "")
        source_failure_reason = str(payload.get("source_failure_reason") or "")
        source_readiness = str(payload.get("source_readiness") or "")
        last_successful_frame = payload.get("last_successful_frame") if isinstance(payload.get("last_successful_frame"), dict) else None
        ready = (
            http_status == 200
            and status == "ready"
            and bool(video_source)
            and not source_failure_reason
            and source_readiness == "first_frame_observed"
            and bool(last_successful_frame)
        )
        return {
            "ready": ready,
            "http_status": http_status,
            "health_url": health_url,
            "status": status,
            "video_source": video_source or "not_loaded",
            "source_readiness": source_readiness or "not_loaded",
            "source_failure_reason": source_failure_reason,
            "last_successful_frame": last_successful_frame,
            "missing": [] if ready else ["camera_first_frame_not_observed"],
        }

    def free_roam_motion_readiness(self) -> dict[str, Any]:
        """自由自助移动不把相机/雷达当硬门禁；建图能力单独用 mapping_readiness 表达。"""
        camera = self.camera_motion_readiness()
        radar = self.radar_status()
        runtime_lidar = self.free_roam_runtime_lidar_readiness()
        radar_proof_ready = bool(radar.get("lifecycle_running")) and bool(radar.get("latest_scan_proof_fresh"))
        radar_ready = radar_proof_ready or bool(runtime_lidar.get("ready"))
        camera_missing = camera.get("missing") if isinstance(camera.get("missing"), list) else ["camera_not_ready"]
        mapping_missing = []
        if not camera.get("ready"):
            mapping_missing.extend(camera_missing)
        if not radar_ready:
            mapping_missing.append("radar_scan_proof_not_fresh")
        return {
            "ready": True,
            "missing": [],
            "free_move_ready": True,
            "free_move_without_camera_allowed": True,
            "motion_without_radar_allowed": True,
            "degraded_without_radar": not radar_ready,
            "mapping_readiness": {
                "ready": not mapping_missing,
                "missing": list(dict.fromkeys(str(item) for item in mapping_missing)),
                "requires_camera_first_frame": True,
                "requires_fresh_radar_scan": True,
                "free_move_allowed_when_mapping_not_ready": True,
            },
            "camera": camera,
            "radar": {
                "ready": radar_ready,
                "optional": True,
                "blocking": False,
                "proof_ready": radar_proof_ready,
                "runtime_scan_ready": bool(runtime_lidar.get("ready")),
                "runtime_scan": runtime_lidar,
                "lifecycle_running": bool(radar.get("lifecycle_running")),
                "lifecycle_state": radar.get("lifecycle_state") or "not_loaded",
                "latest_scan_proof_fresh": bool(radar.get("latest_scan_proof_fresh")),
                "continuous_window_observed": bool(radar.get("continuous_window_observed")),
                "continuity_blocked_reasons": radar.get("continuity_blocked_reasons", []),
            },
        }

    def wait_for_free_roam_start_runtime(self, command_result: dict[str, Any]) -> dict[str, Any]:
        """start 写参后短等一次状态机 tick，避免 PC 立刻读到旧 stopping artifact。"""
        if not free_roam_param_sequence_used_ros2_param_load(command_result):
            return {
                "waited": False,
                "reason": "not_real_ros2_param_load_result",
                "ok": False,
            }
        deadline = time.monotonic() + FREE_ROAM_START_ARTIFACT_WAIT_TIMEOUT_S
        attempts = 0
        last_http_status = 0
        last_latest: dict[str, Any] = {}
        while True:
            attempts += 1
            http_status, latest = self.free_roam_autonomy_latest()
            last_http_status = http_status
            last_latest = latest if isinstance(latest, dict) else {}
            decision_state = str(last_latest.get("decision_state") or "")
            cmd_vel_publish_enabled = bool(last_latest.get("cmd_vel_publish_enabled"))
            # 运行态可能是直行、避障或覆盖换向；这些都说明 stop 请求已被 start 参数清掉。
            runtime_started = cmd_vel_publish_enabled and decision_state in {"running", "avoiding", "turning_for_coverage"}
            if runtime_started:
                return {
                    "waited": True,
                    "ok": True,
                    "attempts": attempts,
                    "http_status": http_status,
                    "decision_state": decision_state,
                    "cmd_vel_publish_enabled": cmd_vel_publish_enabled,
                }
            if time.monotonic() >= deadline:
                return {
                    "waited": True,
                    "ok": False,
                    "attempts": attempts,
                    "http_status": last_http_status,
                    "decision_state": decision_state or "not_loaded",
                    "cmd_vel_publish_enabled": cmd_vel_publish_enabled,
                    "failure_reason": "free_roam_start_runtime_not_observed_before_timeout",
                }
            time.sleep(FREE_ROAM_START_ARTIFACT_WAIT_INTERVAL_S)

    def free_roam_autonomy_control(self, action: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """固定 start/stop 入口只设置 free_roam_autonomy_node 参数，不直接发布速度。"""
        request = body if isinstance(body, dict) else {}
        if action == "start":
            endpoint = ROUTE_PATHS["free_roam_autonomy_start"]
            missing_confirms = [
                name
                for name in ("confirm_operator_safety",)
                if request.get(name) is not True
            ]
            if missing_confirms:
                return software_guard_payload(
                    schema_suffix="free_roam_autonomy_control_result",
                    action="free_roam_autonomy_start",
                    endpoint=endpoint,
                    artifact=free_roam_autonomy_artifact_info(self.free_roam_autonomy_artifact_path),
                    extra={
                        "status": "blocked_missing_confirmation",
                        "failure_reason": "missing_free_roam_operator_confirmation",
                        "missing_confirmations": missing_confirms,
                        "command_result": {
                            "mode": "free_roam_param_sequence",
                            "executed": False,
                            "ok": False,
                            "reason": "missing_free_roam_operator_confirmation",
                        },
                        "publishes_cmd_vel": False,
                        "sends_motion_commands": False,
                        "robot_control_executed": False,
                    },
                )
            sensor_readiness = self.free_roam_motion_readiness()
            free_move_ready = bool(sensor_readiness.get("free_move_ready", sensor_readiness.get("ready")))
            if not free_move_ready:
                return software_guard_payload(
                    schema_suffix="free_roam_autonomy_control_result",
                    action="free_roam_autonomy_start",
                    endpoint=endpoint,
                    artifact=free_roam_autonomy_artifact_info(self.free_roam_autonomy_artifact_path),
                    extra={
                        "status": "blocked_sensor_readiness",
                        "failure_reason": "free_roam_motion_sensors_not_ready",
                        "blocked_reasons": sensor_readiness.get("missing", ["sensor_readiness_not_ready"]),
                        "sensor_readiness": sensor_readiness,
                        "command_result": {
                            "mode": "free_roam_param_sequence",
                            "executed": False,
                            "ok": False,
                            "reason": "free_roam_motion_sensors_not_ready",
                        },
                        "sets_state_machine_parameters": False,
                        "motion_unlock_requested": False,
                        "direct_cmd_vel_publish": False,
                        "does_not_set_motion_unlock": True,
                        "publishes_cmd_vel": False,
                        "sends_motion_commands": False,
                        "robot_control_executed": False,
                        "blocked_parameters_not_touched": ["enable_cmd_vel_publish", "motion_hil_unlocked", "cmd_vel_topic"],
                    },
                )
        elif action == "stop":
            endpoint = ROUTE_PATHS["free_roam_autonomy_stop"]
            sensor_readiness = {"ready": False, "missing": ["not_required_for_stop"]}
        else:
            return software_guard_payload(
                schema_suffix="free_roam_autonomy_control_result",
                action=action,
                endpoint="/api/free-roam/autonomy/{action}",
                artifact=free_roam_autonomy_artifact_info(self.free_roam_autonomy_artifact_path),
                extra={"error": {"type": "unsupported_free_roam_action", "message": "action must be start or stop"}},
            )

        mapping_active_requested = bool(request.get("confirm_mapping_active") is True)
        mapping_readiness = (
            sensor_readiness.get("mapping_readiness")
            if isinstance(sensor_readiness, dict)
            else None
        )
        mapping_ready = (
            bool(mapping_readiness.get("ready"))
            if isinstance(mapping_readiness, dict)
            else False
        )
        mapping_blocked_reasons = (
            list(mapping_readiness.get("missing", []))
            if isinstance(mapping_readiness, dict) and isinstance(mapping_readiness.get("missing"), list)
            else []
        )
        # 自由移动只需要现场安全确认；建图会话必须由上位机再次确认相机和雷达质量，避免直接打 API 绕过 PC 门禁。
        mapping_active_applied = bool(mapping_active_requested and mapping_ready)
        if action == "start":
            command_result = run_free_roam_param_sequence(
                action,
                enable_motion=True,
                mapping_active=mapping_active_applied,
                artifact_path=self.free_roam_autonomy_artifact_path,
            )
        else:
            command_result = run_free_roam_param_sequence(
                action,
                enable_motion=False,
                artifact_path=self.free_roam_autonomy_artifact_path,
            )
        start_runtime_wait = self.wait_for_free_roam_start_runtime(command_result) if action == "start" else {
            "waited": False,
            "reason": "stop_does_not_wait_for_motion_runtime",
            "ok": False,
        }
        http_status, latest = self.free_roam_autonomy_latest()
        motion_unlock_requested = bool(command_result.get("motion_unlock_requested"))
        failure_reason = free_roam_param_sequence_failure_reason(command_result)
        return software_guard_payload(
            schema_suffix="free_roam_autonomy_control_result",
            action=f"free_roam_autonomy_{action}",
            endpoint=endpoint,
            artifact=free_roam_autonomy_artifact_info(self.free_roam_autonomy_artifact_path),
            command_result=command_result,
            extra={
                "status": "requested" if command_result.get("ok") else "blocked",
                "failure_reason": None if command_result.get("ok") else failure_reason,
                "blocked_reasons": [] if command_result.get("ok") else [failure_reason or "free_roam_param_sequence_failed"],
                "request_body": {
                    key: bool(request.get(key))
                    for key in ("confirm_operator_safety", "confirm_mapping_active")
                    if key in request
                },
                "mapping_active_requested": mapping_active_requested,
                "mapping_active_applied": mapping_active_applied,
                "free_move_start_ready": bool(sensor_readiness.get("free_move_ready", sensor_readiness.get("ready")))
                if isinstance(sensor_readiness, dict)
                else False,
                "free_move_blocked_reasons": sensor_readiness.get("missing", [])
                if isinstance(sensor_readiness, dict) and not bool(sensor_readiness.get("free_move_ready", sensor_readiness.get("ready")))
                else [],
                "mapping_readiness_ready": mapping_ready,
                "mapping_blocked_reasons": mapping_blocked_reasons,
                "start_runtime_wait": start_runtime_wait,
                "latest_http_status": http_status,
                "latest_decision_state": (
                    latest.get("decision_state")
                    if isinstance(latest, dict)
                    else "not_loaded"
                ),
                "latest_cmd_vel_publish_enabled": (
                    bool(latest.get("cmd_vel_publish_enabled"))
                    if isinstance(latest, dict)
                    else False
                ),
                "sets_state_machine_parameters": True,
                "direct_cmd_vel_publish": False,
                "motion_unlock_requested": motion_unlock_requested,
                "does_not_set_motion_unlock": not motion_unlock_requested,
                "sensor_readiness": sensor_readiness,
                "managed_runtime": command_result.get("runtime_ensure", {}),
                "publishes_cmd_vel": bool(motion_unlock_requested and command_result.get("ok")),
                "sends_motion_commands": bool(motion_unlock_requested and command_result.get("ok")),
                "robot_control_executed": False,
                "blocked_parameters_not_touched": command_result.get("blocked_parameters_not_touched", []),
            },
        )

    def nav2_status(self) -> dict[str, Any]:
        """Nav2 lifecycle 状态只读 artifact；真实 graph 查询由外部 collector 写材料。"""
        lifecycle_manager = parse_nav2_lifecycle_status_result(
            run_nav2_lifecycle_command(self.nav2_status_command, "status")
        )
        proof_latest = summarize_nav2_lifecycle_latest_artifact(self.nav2_lifecycle_artifact_path)
        proof_blockers = proof_latest.get("blockers") if isinstance(proof_latest.get("blockers"), list) else []
        if lifecycle_manager["running"] is False:
            proof_blockers = [*proof_blockers, "nav2_lifecycle_not_running"]
        status = "path_generated" if proof_latest.get("path_generated") else "not_proven"
        if proof_blockers:
            status = "blocked_with_root_cause" if status == "not_proven" else "path_ready_with_service_blockers"
        return {
            "schema": f"{SCHEMA}.nav2_lifecycle_status",
            "generated_at_ms": now_ms(),
            "status": status,
            "proof_state": status,
            "base_command_mode": self.base_command_mode,
            "nav2_base_command_mode": self.nav2_base_command_mode,
            "nav2_goal_execute_default_base_command_mode": self.nav2_base_command_mode,
            "software_guard": True,
            "not_proven": not bool(proof_latest.get("path_generated")),
            "artifact": nav2_lifecycle_artifact_info(self.nav2_lifecycle_artifact_path),
            "proof_latest": proof_latest,
            "amcl_nav2_readiness": build_amcl_nav2_readiness_from_map_proof(
                self.map_lifecycle_proof_artifact_path,
                self.map_artifact_dir,
            ),
            "amcl_pose": proof_latest.get("amcl_pose"),
            "amcl_pose_observed": proof_latest.get("amcl_pose_observed"),
            "localization_tf_observed": proof_latest.get("localization_tf_observed"),
            "tf_chain_observed": proof_latest.get("tf_chain_observed"),
            "base_link_to_laser_frame_transform": proof_latest.get("base_link_to_laser_frame_transform"),
            "path_generation_requested": proof_latest.get("path_generation_requested"),
            "path_generation_attempted": proof_latest.get("path_generation_attempted"),
            "path_generated": bool(proof_latest.get("path_generated")),
            "path_point_count": int(proof_latest.get("path_point_count") or 0),
            "path_generation_service_name": proof_latest.get("path_generation_service_name"),
            "path_generation_service_available": bool(proof_latest.get("path_generation_service_available")),
            "path_generation_succeeded": bool(proof_latest.get("path_generation_succeeded")),
            "path_preview_points": proof_latest.get("path_preview_points") if isinstance(proof_latest.get("path_preview_points"), list) else [],
            "path_preview_status": proof_latest.get("path_preview_status") or "not_observed",
            "path_preview_point_count": int(proof_latest.get("path_preview_point_count") or 0),
            "path_preview_source_point_count": proof_latest.get("path_preview_source_point_count"),
            "path_preview_frame_id": proof_latest.get("path_preview_frame_id") or "not_loaded",
            "path_preview_next_action_plain": proof_latest.get("path_preview_next_action_plain"),
            "path_wysiwyg_status_plain": proof_latest.get("path_wysiwyg_status_plain"),
            "path_wysiwyg_next_action_plain": proof_latest.get("path_wysiwyg_next_action_plain"),
            "nav2_route_overlay_status": proof_latest.get("nav2_route_overlay_status") or "not_observed",
            "nav2_route_overlay_point_count": int(proof_latest.get("nav2_route_overlay_point_count") or 0),
            "nav2_route_overlay_next_action_plain": proof_latest.get("nav2_route_overlay_next_action_plain"),
            "planner_server_active": proof_latest.get("planner_server_active"),
            "controller_server_active": proof_latest.get("controller_server_active"),
            "controller_server_requested": proof_latest.get("controller_server_requested"),
            "planner_readiness_summary": proof_latest.get("planner_readiness_summary"),
            "path_goal_request": proof_latest.get("path_goal_request"),
            "path_goal_response": proof_latest.get("path_goal_response"),
            "path_generation_boundary": proof_latest.get("path_generation_boundary"),
            "blocked_reasons": list(dict.fromkeys(str(item) for item in proof_blockers)),
            "root_causes": list(dict.fromkeys(str(item) for item in proof_blockers)),
            "next_action": (
                "启动或恢复 Nav2 lifecycle 后再执行图上路线"
                if lifecycle_manager["running"] is False and proof_latest.get("path_generated")
                else "先刷新 Nav2 路径 proof"
                if not proof_latest.get("path_generated")
                else "勾选现场安全确认后可执行图上路线，并复验 wheel raw L/R"
            ),
            "routes": {
                "status": ROUTE_PATHS["nav2_status"],
                "proof_refresh": ROUTE_PATHS["nav2_proof_refresh"],
                "proof_latest": ROUTE_PATHS["nav2_proof_latest"],
                "goal_execute": ROUTE_PATHS["nav2_goal_execute"],
                "goal_execution_latest": ROUTE_PATHS["nav2_goal_execution_latest"],
                "start": ROUTE_PATHS["nav2_start"],
                "stop": ROUTE_PATHS["nav2_stop"],
            },
            "commands": {
                "start": command_config_info("ROBER_NAV2_START_COMMAND", self.nav2_start_command),
                "stop": command_config_info("ROBER_NAV2_STOP_COMMAND", self.nav2_stop_command),
                "status": command_config_info("ROBER_NAV2_STATUS_COMMAND", self.nav2_status_command),
            },
            "sends_commands": False,
            "sends_motion_commands": False,
            "sends_base_motion_commands": False,
            "publishes_cmd_vel": False,
            "calls_base_manual": False,
            "uses_base_uart": False,
            "lifecycle_manager": lifecycle_manager,
            "lifecycle_running": lifecycle_manager["running"],
            "lifecycle_state": lifecycle_manager["state"],
            "runtime_entrypoints": {
                "autonomous_launch": "ros2 launch ros2_trashbot_bringup autonomous.launch.py map_file:=<map.yaml>",
                "lifecycle_nodes_expected": ["map_server", "amcl", "planner_server", "controller_server"],
                "required_inputs": ["/scan", "map yaml/image", "tf map->base_link"],
                "proof_refresh": ROUTE_PATHS["nav2_proof_refresh"],
                "proof_latest": ROUTE_PATHS["nav2_proof_latest"],
                "goal_execute": ROUTE_PATHS["nav2_goal_execute"],
                "goal_execution_latest": ROUTE_PATHS["nav2_goal_execution_latest"],
            },
            **runtime_boundary_flags(),
            **proof_flags(),
        }

    # Nav2 strict start 在这一层统一实现下列安全与兼容约束。
    # 必须消费 JSON body，否则旧空 body 代理会继续隐藏合同漂移。
    # 必须要求精确字段集，否则调用方无法知道哪些字段被忽略。
    # 必须要求 strict_no_motion 为布尔 true，不接受 truthy 替代值。
    # 必须要求 base_enabled 为布尔 false，防止 auto 意外打开 UART。
    # LiDAR 与 scan 复用只接受 legacy false/true 或 sensor-owned true/false。
    # legacy 的合法性只表示请求可执行，实际仍需已有 `/scan` 才能由 O11 返回成功。
    # sensor-owned 的合法性只表示允许尝试，不能跳过串口 holder 与 publisher 后置验收。
    # 两个模式共享 canonical map，避免同一 endpoint 因环境变量读取不同地图。
    # sensor_mode 是服务端派生字段，客户端不能自行提交并影响分支。
    # O11 status 是 effective truth；请求值与最终 argv 只能作为交叉核对材料。
    # base UART 只看 pre/post holder 差集，现场既有 holder 不等于本轮打开。
    # LiDAR holder 必须是 post 新增且 PGID 归属 O11，单纯端口忙不能判 owned。
    # `/scan` publisher 必须当前可见，历史 artifact 或 topic name 不能替代 publisher count。
    # publisher ownership 依赖 start 前零 publisher、start 后新增 publisher 与 owned holder 同时成立。
    # physical_motion=false 是 O11 status 明示事实，不从“未发送 goal”一句话间接推导。
    # broad_kill_used=false 防止 cleanup 以扫描式杀进程换取表面 stopped。
    # start command stdout 区分“当前请求创建进程”和“请求前已有 owner 冲突”。
    # 明确未创建 current owner 时禁止自动 stop，避免误杀前一请求的仍用 runtime。
    # timeout 或不可解析 stdout 仍保守执行 owned cleanup，因为子进程可能已经落地。
    # cleanup 成功只关闭安全尾巴，不会把 semantic failure 改写为 start success。
    # Upper 回包保留 holder/publisher 原始计数，调用方不得用 HTTP 状态码覆盖这些字段。
    # O10 managed proof 必须复用 O11 LiDAR，避免同一 `/dev/ttyACM0` 出现第二个 driver。
    # O10 initialpose 必须绑定 canonical free-cell，HTTP x/y 不能直接绕过地图审计。
    # 以上所有门禁仍固定 no-motion，不授予 NavigateToPose、cmd_vel 或 manual 权限。
    # timeout 必须有限且在安全窗口内，避免 worker 被异常占用。
    # timeout 不允许静默 clamp，否则客户端会误以为原值已生效。
    # body 不得参与 shell 拼接，从源头切断路径与参数注入。
    # 有效命令必须来自受管 o11 白名单，不允许退化成直接 ros2 launch。
    # 最终 argv 必须只保留一个 base-enabled，避免重复 flag 的顺序语义。
    # 最终 argv 必须只保留一个 lidar-enabled，避免部署配置漂移。
    # 两个 enabled flag 都必须从最终 argv 反解验收，不仅信任请求。
    # 合同拒绝时不得调用 status，才能证明子进程调用数为零。
    # 配置拒绝时不得调用 status，避免被动探针混入执行证据。
    # 拒绝响应必须回显 invocation_count=0，便于上层做机器验收。
    # 拒绝响应必须回显 new-open=0/0，明确没有触达两类串口。
    # start returncode=0 只是一个输入，不得直接推导语义成功。
    # start 后必须独立读回 lifecycle running，避免接受已退出进程。
    # start 后必须读回 base_enabled=false，避免只相信命令行外观。
    # start 后必须读回 lidar/reuse 生效值，确认服务没有改变请求模式。
    # sensor-owned 成功还必须证明 owned holder/current publisher 与 base UART zero-open。
    # 任一语义失败都必须回收本次 o11 可能留下的 owned 进程组。
    # 语义成功时不自动 stop，因为后续 Algorithm proof 需要 persistent lifecycle。
    # cleanup 仅能通过 o11 stop，不允许按进程名扫描式杀进程。
    # cleanup 不得发送底盘 stop，因为本合同没有打开底盘 UART。
    # cleanup 不得另开 LiDAR 串口；sensor-owned holder 只能随 O11 owned process group 回收。
    # stop 必须同时验收命令回包与独立 status readback。
    # stop 只要任一 stopped 观测未成立，即使 HTTP 200 也必须 NO-GO。
    # root_causes 必须标注 request、config、runtime 或 cleanup 层，便于精确路由修复。
    # effective_contract 必须保留最终 argv，便于远程 artifact 后续结构审计。
    # response 必须显式回显 cleanup，不得让调用方从日志猜测收口结果。
    # response 必须显式回显 lifecycle status，不得用 HTTP code 替代 runtime 事实。
    # 顶层安全标志始终保持 fail closed，strict start 不会授予路线执行权。
    # 本入口不发 NavigateToPose、cmd_vel 或 manual，真实运动仍由独立门禁负责。
    def nav2_control(
        self,
        action: str,
        body: dict[str, Any] | None = None,
        *,
        request_error: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Nav2 lifecycle 只允许 strict start 或 owned stop；两者都不发送底盘命令。"""
        if action not in {"start", "stop"}:
            return software_guard_payload(
                schema_suffix="nav2_lifecycle_result",
                action=action,
                endpoint="/api/nav2/{action}",
                artifact=nav2_lifecycle_artifact_info(self.nav2_lifecycle_artifact_path),
                extra={"error": {"type": "unsupported_nav2_action", "message": "action must be start or stop"}},
            )

        if action == "start":
            contract, contract_error = normalize_strict_nav2_start_request(body, request_error=request_error)
            if contract_error is not None:
                # 请求合同失败时禁止 status 探针；这样能明确证明 lifecycle command invocation 为零。
                command_result = {
                    "mode": "strict_nav2_start_guard",
                    "executed": False,
                    "ok": False,
                    "invocation_count": 0,
                    "error": contract_error,
                }
                skipped_status = {
                    "status": "not_checked",
                    "failure_reason": "strict_nav2_start_request_rejected_before_status_probe",
                    "lifecycle_running": "not_loaded",
                    "lifecycle_state": "not_loaded",
                    "lifecycle_manager": {
                        "status": "not_loaded",
                        "running": "not_loaded",
                        "state": "not_loaded",
                        "base_enabled": "not_loaded",
                        "lidar_enabled": "not_loaded",
                    },
                }
                return software_guard_payload(
                    schema_suffix="nav2_lifecycle_result",
                    action="nav2_start",
                    endpoint=ROUTE_PATHS["nav2_start"],
                    command_env="ROBER_NAV2_START_COMMAND",
                    command=self.nav2_start_command,
                    command_result=command_result,
                    artifact=nav2_lifecycle_artifact_info(self.nav2_lifecycle_artifact_path),
                    extra={
                        "status": "blocked_strict_no_motion_contract",
                        "proof_state": "blocked_strict_no_motion_contract",
                        "evidence_type": "blocked_with_root_cause",
                        "semantic_success": False,
                        "failure_reason": str(contract_error.get("type") or "strict_nav2_start_request_rejected"),
                        "root_causes": [{"layer": "request_contract", **contract_error}],
                        "evidence": {
                            # bodyless 本身没有内容可消费；非空错误体仍标注 handler 已处理。
                            "request_body_consumed": body is not None or request_error is not None,
                            # 请求未过门禁时不生成任何生效合同，避免上层误读。
                            "effective_contract": None,
                            # 两个 0 来自 subprocess 前拒绝，不是历史 artifact 的替代。
                            "base_uart_new_open_count": 0,
                            "lidar_serial_new_open_count": 0,
                            # invocation_count 是可机械断言的拒绝边界，不要用 HTTP 200 反推执行。
                            "lifecycle_command_invocation_count": 0,
                            "new_open_count_source": "request_rejected_before_subprocess",
                        },
                        "cleanup": {
                            "status": "not_required_no_process_started",
                            "attempted": False,
                            "ok": True,
                            "scope": "o11_owned_pid_process_group_only",
                        },
                        "nav2_lifecycle_status": skipped_status,
                        "opens_base_uart": False,
                        "opens_lidar_serial": False,
                    },
                )

            effective_command, command_error = strict_no_motion_nav2_start_command(self.nav2_start_command, contract)
            if command_error is not None or effective_command is None:
                # 配置命令不在 o11 白名单时同样禁止执行，不能退回默认 shell 或直接 ros2 launch。
                command_result = {
                    "mode": "strict_nav2_start_guard",
                    "executed": False,
                    "ok": False,
                    "invocation_count": 0,
                    "error": command_error or {"type": "effective_command_missing", "message": "safe command missing"},
                }
                root_cause = {"layer": "configured_command", **dict(command_result["error"])}
                return software_guard_payload(
                    schema_suffix="nav2_lifecycle_result",
                    action="nav2_start",
                    endpoint=ROUTE_PATHS["nav2_start"],
                    command_env="ROBER_NAV2_START_COMMAND",
                    command=self.nav2_start_command,
                    command_result=command_result,
                    artifact=nav2_lifecycle_artifact_info(self.nav2_lifecycle_artifact_path),
                    extra={
                        "status": "blocked_strict_no_motion_command",
                        "proof_state": "blocked_strict_no_motion_command",
                        "evidence_type": "blocked_with_root_cause",
                        "semantic_success": False,
                        "failure_reason": str(command_result["error"].get("type") or "strict_nav2_start_command_rejected"),
                        "root_causes": [root_cause],
                        "evidence": {
                            # 配置错误发生在 body 归一化之后，因此请求确已消费。
                            "request_body_consumed": True,
                            # 这里只回显请求合同，没有 effective argv，不得解读为已启动。
                            "effective_contract": contract,
                            # 白名单拒绝发生在任何脚本调用前，所以两类串口增量均为零。
                            "base_uart_new_open_count": 0,
                            "lidar_serial_new_open_count": 0,
                            # 不额外探测 status，避免配置拒绝材料混入另一条子进程调用。
                            "lifecycle_command_invocation_count": 0,
                            "new_open_count_source": "configured_command_rejected_before_subprocess",
                        },
                        "cleanup": {
                            "status": "not_required_no_process_started",
                            "attempted": False,
                            "ok": True,
                            "scope": "o11_owned_pid_process_group_only",
                        },
                        "nav2_lifecycle_status": {
                            "status": "not_checked",
                            "lifecycle_running": "not_loaded",
                            "lifecycle_state": "not_loaded",
                        },
                        "opens_base_uart": False,
                        "opens_lidar_serial": False,
                    },
                )

            # start 只执行代码生成的 base=false 与已验证传感器模式；body 永远不能携带路径或 shell。
            command_result = run_nav2_lifecycle_command(
                effective_command,
                "start",
                timeout_s=float(contract["timeout_s"]),
            )
            # start 自身的结构化 stdout 用于区分“本次未创建进程的冲突”和“可能已创建需回收的进程”。
            start_command_status = parse_nav2_lifecycle_status_result(command_result)
            nav2_lifecycle_status = self.nav2_status()
            lifecycle_manager = nav2_lifecycle_status.get("lifecycle_manager")
            lifecycle_manager = lifecycle_manager if isinstance(lifecycle_manager, dict) else {}
            root_causes: list[dict[str, Any]] = []
            if not command_result.get("executed") or not command_result.get("ok"):
                # HTTP 仍可为 200；真实成功必须依赖 command_result 与后置 lifecycle readback。
                # timeout 与 nonzero 共用同一收口，因为两者都可能已留下 manager 进程组。
                root_causes.append(
                    {
                        "layer": "start_command",
                        "reason": "nav2_start_command_failed_or_timed_out",
                        "detail": command_result.get("error") or command_result.get("stderr_preview"),
                    }
                )
            # 独立 status 可能恰好读到旧 runtime；成功必须先证明 start 回包属于本次新建 manager。
            if not (
                # 三项来自同一 start stdout，缺一项都不能把独立 status 归到本请求。
                start_command_status.get("start_owned_process_created") is True
                and start_command_status.get("running") is True
                and start_command_status.get("state") == "running"
            ):
                root_causes.append(
                    {
                        "layer": "start_ownership",
                        "reason": "current_start_owned_process_not_confirmed",
                        "start_owned_process_created": start_command_status.get(
                            "start_owned_process_created", "not_loaded"
                        ),
                        "running": start_command_status.get("running", "not_loaded"),
                        "state": start_command_status.get("state", "not_loaded"),
                    }
                )
            if lifecycle_manager.get("running") is not True:
                root_causes.append(
                    {
                        "layer": "lifecycle_status",
                        "reason": "nav2_lifecycle_not_running_after_start",
                        "observed": lifecycle_manager.get("running", "not_loaded"),
                    }
                )
            if lifecycle_manager.get("base_enabled") != "false":
                root_causes.append(
                    {
                        "layer": "effective_contract",
                        "reason": "base_enabled_false_not_confirmed",
                        "observed": lifecycle_manager.get("base_enabled", "not_loaded"),
                    }
                )
            expected_lidar = "true" if contract.get("lidar_enabled") is True else "false"
            expected_reuse = "true" if contract.get("reuse_existing_scan") is True else "false"
            if lifecycle_manager.get("lidar_enabled") != expected_lidar:
                root_causes.append(
                    {
                        "layer": "effective_contract",
                        "reason": "lidar_enabled_mode_not_confirmed",
                        "observed": lifecycle_manager.get("lidar_enabled", "not_loaded"),
                    }
                )
            if lifecycle_manager.get("reuse_existing_scan") != expected_reuse:
                root_causes.append(
                    {
                        "layer": "effective_contract",
                        "reason": "reuse_existing_scan_mode_not_confirmed",
                        "observed": lifecycle_manager.get("reuse_existing_scan", "not_loaded"),
                    }
                )
            if lifecycle_manager.get("sensor_mode") != contract.get("sensor_mode"):
                root_causes.append(
                    {
                        "layer": "effective_contract",
                        "reason": "sensor_mode_not_confirmed",
                        "observed": lifecycle_manager.get("sensor_mode", "not_loaded"),
                    }
                )
            # 两种合法模式都必须证明 base-disabled 没有产生新 UART holder，且整个 start 保持无运动。
            common_runtime_requirements = (
                # UART、运动和 broad-kill 是与传感器选择无关的共同安全不变量。
                (lifecycle_manager.get("base_uart_new_open_count") == 0, "base_uart_zero_open_not_confirmed"),
                (lifecycle_manager.get("physical_motion") is False, "physical_motion_false_not_confirmed"),
                (lifecycle_manager.get("broad_kill_used") is False, "broad_kill_false_not_confirmed"),
            )
            for requirement_met, reason in common_runtime_requirements:
                if not requirement_met:
                    root_causes.append({"layer": "runtime_safety", "reason": reason})
            # sensor-owned 模式必须用当前 O11 status 证明串口与 publisher 都属于本进程组。
            if contract.get("sensor_mode") == "sensor_owned_scan":
                sensor_requirements = (
                    (lifecycle_manager.get("lidar_serial_new_open_count", 0) >= 1 if isinstance(lifecycle_manager.get("lidar_serial_new_open_count"), int) else False, "owned_lidar_serial_new_open_not_confirmed"),
                    (lifecycle_manager.get("lidar_holder_owned") is True, "owned_lidar_holder_not_confirmed"),
                    (lifecycle_manager.get("scan_publisher_post_count", 0) >= 1 if isinstance(lifecycle_manager.get("scan_publisher_post_count"), int) else False, "current_scan_publisher_not_confirmed"),
                    (lifecycle_manager.get("scan_publisher_owned") is True, "owned_scan_publisher_not_confirmed"),
                )
                for requirement_met, reason in sensor_requirements:
                    if not requirement_met:
                        root_causes.append({"layer": "sensor_ownership", "reason": reason})
            else:
                # legacy 模式不拥有 LiDAR，但必须证明没有新开串口且 current `/scan` 确实仍存在。
                legacy_requirements = (
                    (lifecycle_manager.get("lidar_serial_new_open_count") == 0, "legacy_lidar_zero_open_not_confirmed"),
                    (lifecycle_manager.get("scan_publisher_post_count", 0) >= 1 if isinstance(lifecycle_manager.get("scan_publisher_post_count"), int) else False, "legacy_current_scan_publisher_not_confirmed"),
                )
                for requirement_met, reason in legacy_requirements:
                    if not requirement_met:
                        root_causes.append({"layer": "sensor_reuse", "reason": reason})

            cleanup: dict[str, Any] = {
                # 语义成功后保持 persistent runtime，留给 Algorithm 串行执行 proof。
                "status": "not_required_persistent_owned_lifecycle",
                "attempted": False,
                "ok": True,
                # 即使未 cleanup 也回显所有权范围，便于后续 stop 对齐。
                "scope": "o11_owned_pid_process_group_only",
            }
            lifecycle_invocation_count = 2
            # timeout/不可解析响应仍保守 cleanup；只有脚本明确证明未创建 current owner 才跳过 stop。
            cleanup_required = start_command_status.get("start_owned_process_created") is not False
            if root_causes and cleanup_required:
                # 任何语义失败都只调用 o11 stop，收口本次可能留下的 owned process group。
                cleanup_result = run_nav2_lifecycle_command(self.nav2_stop_command, "stop")
                cleanup_status = parse_nav2_lifecycle_status_result(cleanup_result)
                cleanup_ok = bool(
                    cleanup_result.get("executed")
                    and cleanup_result.get("ok")
                    and cleanup_status.get("running") is False
                    and cleanup_status.get("state") == "stopped"
                )
                cleanup = {
                    # stop 脚本的结构化 stopped 回包是 cleanup 成功的必要条件。
                    "status": "owned_process_group_stopped" if cleanup_ok else "owned_process_group_cleanup_failed",
                    "attempted": True,
                    "ok": cleanup_ok,
                    # 这个 scope 禁止调用方把广泛扫杀当成等价恢复策略。
                    "scope": "o11_owned_pid_process_group_only",
                    "command_result": cleanup_result,
                    "lifecycle_status": cleanup_status,
                    "sends_base_stop_command": False,
                    "uses_base_uart": False,
                }
                lifecycle_invocation_count += 1
                if not cleanup_ok:
                    root_causes.append(
                        {"layer": "cleanup", "reason": "owned_process_group_cleanup_not_confirmed"}
                    )
            elif root_causes:
                cleanup = {
                    # preflight/owner 冲突未创建本次进程；调用 stop 反而可能终止既有 runtime。
                    "status": "not_required_no_current_owned_process_started",
                    "attempted": False,
                    "ok": True,
                    "scope": "o11_current_request_owned_pid_process_group_only",
                    "start_command_status": start_command_status,
                    "sends_base_stop_command": False,
                    "uses_base_uart": False,
                }

            semantic_success = not root_causes
            effective_contract = {
                **contract,
                # argv 是重建后再经白名单验证的最终 token 列表，不包含 body 字符串。
                "effective_argv": shlex.split(effective_command),
                # lifecycle 必须在 start 返回后存活，否则无法接受后续串行 proof。
                "persistent_lifecycle": True,
                # 该标志只说明 start 不发目标，不授予任何 goal execute 权限。
                "motion_requires_explicit_goal_execute": True,
            }
            return software_guard_payload(
                schema_suffix="nav2_lifecycle_result",
                action="nav2_start",
                endpoint=ROUTE_PATHS["nav2_start"],
                command_env="ROBER_NAV2_START_COMMAND",
                command=effective_command,
                command_result=command_result,
                artifact=nav2_lifecycle_artifact_info(self.nav2_lifecycle_artifact_path),
                extra={
                    "status": "started_strict_no_motion" if semantic_success else "blocked_start_semantic_failure",
                    "proof_state": "strict_no_motion_lifecycle_running" if semantic_success else "blocked_start_semantic_failure",
                    "evidence_type": (
                        "strict_no_motion_lifecycle_runtime_material"
                        if semantic_success
                        else "blocked_with_root_cause"
                    ),
                    "semantic_success": semantic_success,
                    "failure_reason": None if semantic_success else str(root_causes[0].get("reason")),
                    "root_causes": root_causes,
                    "evidence": {
                        # 进入执行分支即表示五字段 strict body 已完整验证。
                        "request_body_consumed": True,
                        # 生效合同同时保留请求值与服务端重建 argv，支持双向对账。
                        "effective_contract": effective_contract,
                        # 串口增量只能来自 O11 status；sensor-owned 模式不再把 LiDAR new-open 写死为零。
                        "base_uart_new_open_count": lifecycle_manager.get("base_uart_new_open_count", "not_loaded"),
                        "lidar_serial_new_open_count": lifecycle_manager.get("lidar_serial_new_open_count", "not_loaded"),
                        "sensor_ownership": lifecycle_manager.get("sensor_ownership", {}),
                        "scan_publisher_post_count": lifecycle_manager.get("scan_publisher_post_count", "not_loaded"),
                        "lidar_holder_owned": lifecycle_manager.get("lidar_holder_owned", "not_loaded"),
                        "scan_publisher_owned": lifecycle_manager.get("scan_publisher_owned", "not_loaded"),
                        # 计数包含 start/status，语义失败时再加一次 owned stop。
                        "lifecycle_command_invocation_count": lifecycle_invocation_count,
                        "new_open_count_source": "o11_current_holder_and_publisher_status_readback",
                    },
                    "cleanup": cleanup,
                    "start_command_status": start_command_status,
                    "nav2_lifecycle_status": nav2_lifecycle_status,
                    "opens_base_uart": False,
                    # capability 不等于事实；只有本次 owner 回包与 new-open readback 同时成立才声明已打开。
                    "opens_lidar_serial": bool(
                        contract.get("sensor_mode") == "sensor_owned_scan"
                        and start_command_status.get("start_owned_process_created") is True
                        and isinstance(lifecycle_manager.get("lidar_serial_new_open_count"), int)
                        and lifecycle_manager.get("lidar_serial_new_open_count", 0) >= 1
                    ),
                    "transition_to_proven": [
                        "effective o11 argv and status confirm the selected legacy or sensor-owned mode",
                        "sensor-owned mode confirms base UART zero-open, owned LiDAR holder and current /scan publisher",
                        "map_server/amcl/planner/controller lifecycle states observed by the proof collector",
                        "fresh persisted localization and planner-only path are verified in the next serial phase",
                    ],
                },
            )

        # stop 不消费 body，也不调用底盘 stop；o11 只终止 PID 文件归属的自身进程组。
        command_result = run_nav2_lifecycle_command(self.nav2_stop_command, "stop")
        command_status = parse_nav2_lifecycle_status_result(command_result)
        nav2_lifecycle_status = self.nav2_status()
        lifecycle_manager = nav2_lifecycle_status.get("lifecycle_manager")
        lifecycle_manager = lifecycle_manager if isinstance(lifecycle_manager, dict) else {}
        cleanup_ok = bool(
            command_result.get("executed")
            and command_result.get("ok")
            and command_status.get("running") is False
            and command_status.get("state") == "stopped"
            and lifecycle_manager.get("running") is False
            and lifecycle_manager.get("state") == "stopped"
        )
        root_causes = [] if cleanup_ok else [
            {
                "layer": "cleanup",
                "reason": "owned_process_group_stop_not_confirmed",
                "command_running": command_status.get("running"),
                "readback_running": lifecycle_manager.get("running"),
            }
        ]
        cleanup = {
            # stop 回包与独立 status 必须同时证明 stopped，避免单一 HTTP 假阳性。
            "status": "owned_process_group_stopped" if cleanup_ok else "owned_process_group_cleanup_failed",
            "attempted": True,
            "ok": cleanup_ok,
            # 不使用进程名匹配或 pkill，只消费 o11 PID 文件归属。
            "scope": "o11_owned_pid_process_group_only",
            "command_status": command_status,
            "readback_status": lifecycle_manager,
            "sends_base_stop_command": False,
            "uses_base_uart": False,
        }
        return software_guard_payload(
            schema_suffix="nav2_lifecycle_result",
            action="nav2_stop",
            endpoint=ROUTE_PATHS["nav2_stop"],
            command_env="ROBER_NAV2_STOP_COMMAND",
            command=self.nav2_stop_command,
            command_result=command_result,
            artifact=nav2_lifecycle_artifact_info(self.nav2_lifecycle_artifact_path),
            extra={
                "status": "stopped_owned_process_group" if cleanup_ok else "blocked_stop_cleanup_failure",
                "proof_state": "owned_lifecycle_stopped" if cleanup_ok else "blocked_stop_cleanup_failure",
                "evidence_type": "owned_lifecycle_cleanup_material" if cleanup_ok else "blocked_with_root_cause",
                "semantic_success": cleanup_ok,
                "failure_reason": None if cleanup_ok else "owned_process_group_stop_not_confirmed",
                "root_causes": root_causes,
                "evidence": {
                    "effective_contract": {
                        # cleanup 合同显式禁止底盘 stop frame，因为本 API 未拥有 UART。
                        "cleanup_scope": "o11_owned_pid_process_group_only",
                        "sends_base_stop_command": False,
                        "uses_base_uart": False,
                    },
                    # stop 不传入 base/lidar 启动参数，也不打开任何串口设备。
                    "base_uart_new_open_count": 0,
                    "lidar_serial_new_open_count": 0,
                    "lifecycle_command_invocation_count": 2,
                    "new_open_count_source": "owned_stop_contains_no_base_or_lidar_command",
                },
                "cleanup": cleanup,
                "nav2_lifecycle_status": nav2_lifecycle_status,
                "opens_base_uart": False,
                "opens_lidar_serial": False,
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

    def operator_report(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """POST operator report 只写人工材料，不能触发底盘、stop、status 或 ROS2 运行。"""
        report = body if isinstance(body, dict) else {}
        return build_operator_report_payload(self.operator_report_artifact_path, report)

    def operator_report_latest(self) -> tuple[int, dict[str, Any]]:
        """GET operator report 只读 latest artifact，给 PC 做 readback 和 evidence_ref 对齐。"""
        return read_operator_report_latest_artifact(self.operator_report_artifact_path)

    async def camera_health(self) -> tuple[int, dict[str, Any]]:
        """camera 子接口代理 8088 /health，并标注统一 API 来源。"""
        status, payload = await fetch_json(urljoin(self.camera_base_url + "/", "health"))
        payload.update(flatten_camera_health_aliases(payload))
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

    async def camera_first_frame_probe(self, body: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
        """PC 高级诊断触发的相机首帧探针；不经过 WebRTC，也不触碰底盘。"""
        return await run_camera_first_frame_probe(body)

    async def camera_usb_recovery(self, body: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
        """PC 触发的相机 USB 恢复；只重启相机链路，不触碰底盘控制链路。"""
        return await run_camera_usb_recovery(body)

    async def unified_status(self) -> dict[str, Any]:
        """PC 首屏只拉一个状态接口即可获得 camera/radar/base 总览。"""
        (
            camera_result,
            radar,
            map_status,
            nav2,
            free_roam_autonomy,
            elevator,
        ) = await asyncio.gather(
            read_camera_status_section(self),
            read_status_section("radar", self.radar_status),
            read_status_section("map", self.map_status),
            read_status_section("nav2", self.nav2_status),
            read_status_section("free_roam_autonomy", self.free_roam_autonomy_status),
            read_status_section("elevator", self.elevator_status),
        )
        camera_http_status, camera = camera_result
        base = base_status_deferred_payload(self.feedback_samples_artifact_path)
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
            "radar": radar,
            "map": map_status,
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
            "nav2": nav2,
            "free_roam_autonomy": free_roam_autonomy,
            "elevator": elevator,
            "operator_report": summarize_operator_report_latest_artifact(self.operator_report_artifact_path),
            "base": base,
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
            "free_roam_autonomy_artifact": free_roam_autonomy_artifact_info(self.free_roam_autonomy_artifact_path),
            "elevator_status_artifact": elevator_status_artifact_info(self.elevator_status_artifact_path),
            "operator_report_artifact": operator_report_artifact_info(self.operator_report_artifact_path),
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

    def _manual_hold_stop_sync(self, command_mode: str) -> dict[str, Any]:
        """watchdog/release 共用停车兜底；ROS 先发 /cmd_vel 零速度，串口再补三种 vendor 零命令。"""
        stop_plan = stop_commands_for_mode(command_mode)
        ros_stop = publish_ros_cmd_vel_inprocess_burst(0.0, 0.0, hold_s=ROS_CMD_VEL_STOP_HOLD_S, wait_subscription_s=0.15)
        if not ros_stop.get("ok"):
            ros_stop = publish_ros_cmd_vel_cli_burst(0.0, 0.0, hold_s=ROS_CMD_VEL_STOP_HOLD_S, timeout_s=2.0)
        serial_results = [write_serial_json(self.base_port, self.base_baudrate, stop_command) for stop_command in stop_plan]
        return {
            "mode": "manual_hold_stop_all_surfaces",
            "command_mode": command_mode,
            "ros_stop_result": ros_stop,
            "serial_stop_results": serial_results,
            "ok": bool(ros_stop.get("ok")) or any(bool(item.get("ok")) for item in serial_results),
        }

    async def _manual_hold_watchdog(self, session_id: str, sequence: int) -> None:
        """如果 PC 按住循环断拍，最后一次 hold 到期后自动停车。"""
        try:
            while True:
                state = self._manual_hold_state
                if state.get("session_id") != session_id or int(state.get("sequence") or -1) != sequence:
                    return
                delay_s = max(float(state.get("expires_at_monotonic") or 0.0) - time.monotonic(), 0.0)
                if delay_s > 0:
                    await asyncio.sleep(delay_s)
                    continue
                result = await asyncio.to_thread(self._manual_hold_stop_sync, str(state.get("command_mode") or self.base_command_mode))
                state["watchdog_stop_result"] = result
                state["watchdog_stopped_at_ms"] = now_ms()
                state["active"] = False
                return
        except asyncio.CancelledError:
            return

    def _schedule_manual_hold_watchdog(self, session_id: str, sequence: int, command_mode: str, watchdog_ms: int) -> dict[str, Any]:
        """每个 keyboard hold 请求只延长 watchdog，不在本次请求末尾立即 stop。"""
        if self._manual_hold_watchdog_task is not None and not self._manual_hold_watchdog_task.done():
            self._manual_hold_watchdog_task.cancel()
        watchdog_ms = min(max(int(watchdog_ms), MIN_HOLD_WATCHDOG_MS), MAX_PULSE_MS)
        expires_at = time.monotonic() + watchdog_ms / 1000.0
        self._manual_hold_state = {
            "active": True,
            "session_id": session_id,
            "sequence": sequence,
            "command_mode": command_mode,
            "watchdog_ms": watchdog_ms,
            "expires_at_monotonic": expires_at,
            "updated_at_ms": now_ms(),
        }
        self._manual_hold_watchdog_task = asyncio.create_task(self._manual_hold_watchdog(session_id, sequence))
        return dict(self._manual_hold_state)

    async def manual_control(self, body: dict[str, Any]) -> dict[str, Any]:
        """低速点动控制：发送方向命令后等待短窗口，再无条件发送停车命令。"""
        upper_receive_mono_ns = int(body.get("_upper_receive_mono_ns") or time.monotonic_ns())
        latency_trace = normalize_latency_trace(body.get("latency_trace"))
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
        request_command_mode = str(body.get("command_mode", self.base_command_mode)).strip().lower()
        command_mode = request_command_mode if request_command_mode in ALLOWED_BASE_COMMAND_MODES else self.base_command_mode
        feedback_mode = str(body.get("feedback_mode", "")).strip().lower()
        use_bridge_debug_feedback = feedback_mode == "bridge_debug"
        use_realtime_feedback = feedback_mode == "realtime"
        use_realtime_hold = feedback_mode == "realtime_hold"
        hold_session_id = str(body.get("hold_session_id") or "").strip()[:96]
        try:
            hold_sequence = int(body.get("hold_sequence", 0))
        except (TypeError, ValueError):
            hold_sequence = 0
        try:
            requested_hold_watchdog_ms = int(body.get("hold_watchdog_ms", pulse_ms))
        except (TypeError, ValueError):
            requested_hold_watchdog_ms = pulse_ms
        hold_watchdog_ms = min(max(requested_hold_watchdog_ms, MIN_HOLD_WATCHDOG_MS), MAX_PULSE_MS)
        command = manual_command_for_direction(
            direction,
            speed,
            command_mode=command_mode,
            max_speed=self.max_speed,
            pwm_min_abs=self.manual_pwm_min_abs,
            pwm_max_abs=self.manual_pwm_max_abs,
        )
        twist_override = {
            "ros_twist_override_applied": False,
            "requested_linear_x_mps": None,
            "requested_angular_z_radps": None,
            "clamped_linear_x_mps": command.get("X") if command_mode == "ros" else None,
            "clamped_angular_z_radps": command.get("Z") if command_mode == "ros" else None,
        }
        if command_mode == "ros":
            command, twist_override = ros_command_for_optional_twist(body, command, max_speed=self.max_speed)
        stop_plan = stop_commands_for_mode(command_mode)
        # WAVE ROVER 固件的 setpoint/feedback 节奏约 200ms；first-jog 500ms 若只读 220ms，
        # 容易在停车前错过非零 T1001。默认读窗覆盖大部分脉冲，但不超过脉冲本身。
        motion_read_window_s = clamp_float(
            body.get("motion_read_window_s"),
            default_motion_read_window_s(pulse_ms),
            0.05,
            max(0.05, min(pulse_ms / 1000.0, 0.8)),
        )
        motion_read_timeout_s = clamp_float(body.get("motion_read_timeout_s"), 0.05, 0.01, 0.2)
        read_timeout_s = clamp_float(body.get("read_timeout_s"), DEFAULT_FEEDBACK_READ_TIMEOUT_S, 0.01, MAX_FEEDBACK_READ_TIMEOUT_S)
        read_window_s = clamp_float(body.get("read_window_s"), DEFAULT_FEEDBACK_READ_WINDOW_S, 0.01, MAX_FEEDBACK_READ_WINDOW_S)
        # 到这里方向、速度、持续时间、模式和 watchdog 均已收敛；首帧只能发生在 gate 完成之后。
        manual_gate_done_mono_ns = time.monotonic_ns()
        feedback_during_motion_attempted = direction != "stop" and pulse_ms > 0
        serial_motion_transaction: dict[str, Any] | None = None
        ros_cmd_vel_transaction: dict[str, Any] | None = None
        manual_hold_watchdog: dict[str, Any] | None = None
        if feedback_during_motion_attempted:
            if use_realtime_hold and hold_session_id:
                if command_mode == "ros":
                    ros_cmd_vel_transaction = manual_motion_ros_cmd_vel_hold_refresh_transaction(
                        port=self.base_port,
                        baudrate=self.base_baudrate,
                        command=command,
                    )
                    first = ros_cmd_vel_transaction["command_result"]
                    stop = ros_cmd_vel_transaction["stop_result"]
                    feedback_during_motion = ros_cmd_vel_transaction["feedback_during_motion"]
                    feedback_evidence = ros_cmd_vel_transaction["feedback_after_stop"]
                else:
                    serial_motion_transaction = manual_motion_serial_hold_refresh_transaction(
                        port=self.base_port,
                        baudrate=self.base_baudrate,
                        command=command,
                        stop_commands=stop_plan,
                    )
                    first = serial_motion_transaction["command_result"]
                    stop = serial_motion_transaction["stop_result"]
                    feedback_during_motion = serial_motion_transaction["feedback_during_motion"]
                    feedback_evidence = serial_motion_transaction["feedback_after_stop"]
                # 只有首帧真实交给 backend 后才延长 hold；失败请求不能留下“仍在运动”的假 watchdog 状态。
                if first.get("ok"):
                    manual_hold_watchdog = self._schedule_manual_hold_watchdog(hold_session_id, hold_sequence, command_mode, hold_watchdog_ms)
                feedback_after_stop_attempted = False
            elif command_mode == "ros":
                ros_cmd_vel_transaction = manual_motion_ros_cmd_vel_transaction(
                    port=self.base_port,
                    baudrate=self.base_baudrate,
                    command=command,
                    pulse_ms=pulse_ms,
                )
                first = ros_cmd_vel_transaction["command_result"]
                stop = ros_cmd_vel_transaction["stop_result"]
                feedback_during_motion = ros_cmd_vel_transaction["feedback_during_motion"]
                feedback_evidence = ros_cmd_vel_transaction["feedback_after_stop"]
                feedback_after_stop_attempted = False
            elif use_bridge_debug_feedback:
                serial_motion_transaction = manual_motion_serial_write_only_transaction(
                    port=self.base_port,
                    baudrate=self.base_baudrate,
                    command=command,
                    stop_commands=stop_plan,
                    pulse_ms=pulse_ms,
                )
                first = serial_motion_transaction["command_result"]
                stop = serial_motion_transaction["stop_result"]
                feedback_during_motion = serial_motion_transaction["feedback_during_motion"]
                feedback_evidence = serial_motion_transaction["feedback_after_stop"]
                feedback_after_stop_attempted = False
            elif use_realtime_feedback:
                serial_motion_transaction = manual_motion_serial_write_only_transaction(
                    port=self.base_port,
                    baudrate=self.base_baudrate,
                    command=command,
                    stop_commands=stop_plan,
                    pulse_ms=pulse_ms,
                    mode="serial_write_only_realtime",
                    feedback_reason="realtime_manual_feedback_skipped_until_release_readback",
                    feedback_source="keyboard_release_readback",
                )
                first = serial_motion_transaction["command_result"]
                stop = serial_motion_transaction["stop_result"]
                feedback_during_motion = serial_motion_transaction["feedback_during_motion"]
                feedback_evidence = serial_motion_transaction["feedback_after_stop"]
                feedback_after_stop_attempted = False
            else:
                serial_motion_transaction = manual_motion_serial_transaction(
                    port=self.base_port,
                    baudrate=self.base_baudrate,
                    command=command,
                    stop_commands=stop_plan,
                    pulse_ms=pulse_ms,
                    motion_read_timeout_s=motion_read_timeout_s,
                    motion_read_window_s=motion_read_window_s,
                    after_stop_read_timeout_s=read_timeout_s,
                    after_stop_read_window_s=read_window_s,
                )
                first = serial_motion_transaction["command_result"]
                stop = serial_motion_transaction["stop_result"]
                feedback_during_motion = serial_motion_transaction["feedback_during_motion"]
                feedback_evidence = serial_motion_transaction["feedback_after_stop"]
                feedback_after_stop_attempted = bool(stop.get("ok"))
        else:
            started_monotonic = time.monotonic()
            first = write_serial_json(self.base_port, self.base_baudrate, command)
            feedback_during_motion = skipped_manual_feedback_payload(
                self.base_port,
                self.base_baudrate,
                "manual_motion_feedback_not_attempted",
            )
            elapsed_s = time.monotonic() - started_monotonic
            remaining_s = max(pulse_ms / 1000.0 - elapsed_s, 0.0)
            if remaining_s > 0:
                await asyncio.sleep(remaining_s)
            stop = write_serial_json(self.base_port, self.base_baudrate, stop_plan[0])
            additional_stop_results = [write_serial_json(self.base_port, self.base_baudrate, stop_command) for stop_command in stop_plan[1:]]
            if first.get("ok") and stop.get("ok"):
                # stop-only 仍可读停车后反馈，但不会产生运动窗口证据。
                feedback_evidence = request_base_feedback_once(
                    self.base_port,
                    self.base_baudrate,
                    read_timeout_s=read_timeout_s,
                    read_window_s=read_window_s,
                )
                feedback_after_stop_attempted = True
            else:
                feedback_evidence = skipped_manual_feedback_payload(
                    self.base_port,
                    self.base_baudrate,
                    "skipped_due_to_manual_write_failure",
                )
                feedback_after_stop_attempted = False
        serial_write_failures = [
            result["error"]
            for result in (first, stop, *((serial_motion_transaction or {}).get("additional_stop_results") or []))
            if isinstance(result, dict) and not result.get("ok") and "error" in result
        ]
        manual_feedback_samples_latest = None
        bridge_feedback_sample = None
        if feedback_during_motion_attempted and (command_mode == "ros" or use_bridge_debug_feedback) and bool(first.get("ok")):
            # ROS/PC 只写手控都不抢 esp32_bridge 持有的 UART；短脉冲后只读 bridge 已写出的 fresh T1001 debug log。
            bridge_feedback_debug = summarize_bridge_feedback_debug_log(DEFAULT_BRIDGE_FEEDBACK_DEBUG_LOG_PATH)
            bridge_freshness = bridge_feedback_debug.get("freshness")
            bridge_is_fresh = isinstance(bridge_freshness, dict) and bridge_freshness.get("status") == "fresh"
            if bridge_is_fresh and int(bridge_feedback_debug.get("t1001_observed_count") or 0) > 0:
                bridge_feedback_sample = bridge_debug_summary_as_manual_feedback_payload(
                    bridge_feedback_debug,
                    port=self.base_port,
                    baudrate=self.base_baudrate,
                    reason="manual_motion_feedback_read_from_bridge_debug_log",
                )
        if bridge_feedback_sample is not None and not t1001_frames_from_feedback_payload(feedback_during_motion):
            # 串口由 esp32_bridge 持有时，manual_control 自己的反馈对象会是 skipped；这里把同源 bridge 帧并入本次窗口。
            feedback_during_motion = bridge_feedback_sample
        wheel_feedback_frames = [
            *t1001_frames_from_feedback_payload(feedback_during_motion),
            *t1001_frames_from_feedback_payload(feedback_evidence),
        ]
        manual_wheel_feedback_summary = wheel_feedback_summary_from_frames(wheel_feedback_frames)
        manual_imu_delta_summary = imu_attitude_delta_summary_from_frames(wheel_feedback_frames)
        manual_command_raw_summary = command_raw_motion_summary(
            command,
            first,
            source="manual_command_result",
        )
        manual_bridge_command_debug = summarize_bridge_command_debug_log(DEFAULT_BRIDGE_COMMAND_DEBUG_LOG_PATH)
        manual_bridge_command_freshness = manual_bridge_command_debug.get("freshness")
        manual_bridge_command_is_fresh = (
            isinstance(manual_bridge_command_freshness, dict)
            and manual_bridge_command_freshness.get("status") == "fresh"
        )
        manual_bridge_command_raw_summary = command_raw_motion_summary_from_debug_record(
            manual_bridge_command_debug.get("latest_sent_nonzero_command") if manual_bridge_command_is_fresh else None,
            source="manual_bridge_command_debug_latest_sent_nonzero_command",
        )
        manual_command_raw_nonzero_proven = bool(
            manual_command_raw_summary.get("raw_nonzero_proven")
            or manual_bridge_command_raw_summary.get("raw_nonzero_proven")
        )
        manual_command_raw_lr_nonzero_proven = bool(
            manual_command_raw_summary.get("lr_nonzero_proven")
            or manual_bridge_command_raw_summary.get("lr_nonzero_proven")
        )
        manual_command_raw_twist_nonzero_proven = bool(
            manual_command_raw_summary.get("twist_nonzero_proven")
            or manual_bridge_command_raw_summary.get("twist_nonzero_proven")
        )
        manual_motion_signal_observed = bool(
            manual_wheel_feedback_summary["lr_nonzero_observed"]
            or manual_imu_delta_summary["imu_attitude_delta_observed"]
        )
        manual_motion_signal_source = (
            "wheel_feedback_lr"
            if manual_wheel_feedback_summary["lr_nonzero_observed"]
            else "imu_attitude_delta"
            if manual_imu_delta_summary["imu_attitude_delta_observed"]
            else "not_observed"
        )
        manual_motion_evidence_complete = bool(
            manual_command_raw_nonzero_proven and manual_motion_signal_observed
        )
        if feedback_during_motion_attempted and (wheel_feedback_frames or (command_mode != "ros" and not use_bridge_debug_feedback and not use_realtime_feedback)):
            # first-jog/键盘手控的非零 T1001 必须落到 latest artifact，
            # 否则 PC 刷新 summary 会被停车后的 0/0 读回覆盖成“看似丢证据”。
            manual_feedback_samples_latest = persist_feedback_samples_artifact(
                self.feedback_samples_artifact_path,
                build_base_feedback_samples_payload(
                    port=self.base_port,
                    baudrate=self.base_baudrate,
                    sample_count=2,
                    sample_interval_s=0.0,
                    read_timeout_s=max(motion_read_timeout_s, read_timeout_s),
                    read_window_s=max(motion_read_window_s, read_window_s),
                    samples=[feedback_during_motion, feedback_evidence],
                ),
            )
        feedback_ack = feedback_during_motion.get("feedback_ack") if isinstance(feedback_during_motion.get("feedback_ack"), dict) else {}
        if feedback_ack.get("t1001_observed") is not True:
            feedback_ack = feedback_evidence.get("feedback_ack", t1001_boundary("manual feedback evidence unavailable"))
        upper_response_ready_mono_ns = time.monotonic_ns()
        latency_fields = (
            {
                "latency_trace": latency_trace,
                "latency_timing": upper_latency_timing(
                    upper_receive_mono_ns,
                    manual_gate_done_mono_ns,
                    first,
                    upper_response_ready_mono_ns,
                ),
            }
            if latency_trace is not None
            else {}
        )
        # realtime_hold 不允许 CLI fallback；进程内 publisher 失败时 HTTP 也必须 fail-closed，不能报 command_forwarded。
        realtime_hold_hot_path_blocked = bool(
            use_realtime_hold and command_mode == "ros" and not first.get("ok")
        )
        return {
            "schema": f"{SCHEMA}.base_manual_result",
            "generated_at_ms": now_ms(),
            "accepted": not realtime_hold_hot_path_blocked,
            "status": "blocked_realtime_hold_rclpy_not_ready" if realtime_hold_hot_path_blocked else "manual_command_completed",
            "failure_reason": "realtime_hold_rclpy_prewarm_unavailable" if realtime_hold_hot_path_blocked else "",
            "direction": direction,
            "speed": speed,
            "base_command_mode": command_mode,
            **twist_override,
            "feedback_mode": feedback_mode or "direct_feedback",
            "stop_commands": stop_plan,
            "duration_ms": pulse_ms,
            "hold_session_id": hold_session_id if use_realtime_hold else "",
            "hold_sequence": hold_sequence if use_realtime_hold else 0,
            "hold_watchdog_ms": hold_watchdog_ms if use_realtime_hold else 0,
            "manual_hold_watchdog": manual_hold_watchdog,
            "requested_speed": requested_speed,
            "requested_duration_ms": requested_pulse_ms,
            "command_result": first,
            "stop_result": stop,
            "serial_write_failures": serial_write_failures,
            "auto_stop_attempted": False if realtime_hold_hot_path_blocked else not bool(manual_hold_watchdog),
            "auto_stop_executed": False if manual_hold_watchdog else bool(stop.get("ok")),
            "auto_stop_deferred_to_watchdog": bool(manual_hold_watchdog),
            "manual_command_executed": bool(first.get("ok")),
            "feedback_during_motion_attempted": feedback_during_motion_attempted,
            "feedback_during_motion": feedback_during_motion,
            "feedback_after_stop_attempted": feedback_after_stop_attempted,
            "feedback_evidence": feedback_evidence,
            "manual_feedback_samples_latest": manual_feedback_samples_latest,
            "serial_motion_transaction": serial_motion_transaction,
            "ros_cmd_vel_transaction": ros_cmd_vel_transaction,
            "t1001_feedback_status": feedback_during_motion.get("t1001_feedback_status") or feedback_evidence.get("t1001_feedback_status"),
            "manual_wheel_feedback_summary": manual_wheel_feedback_summary,
            "manual_imu_attitude_delta_summary": manual_imu_delta_summary,
            "manual_command_raw_summary": manual_command_raw_summary,
            "manual_bridge_command_raw_summary": manual_bridge_command_raw_summary,
            "command_raw_nonzero_proven": manual_command_raw_nonzero_proven,
            "command_raw_lr_nonzero_proven": manual_command_raw_lr_nonzero_proven,
            "command_raw_twist_nonzero_proven": manual_command_raw_twist_nonzero_proven,
            "command_raw_latest_left": (
                manual_bridge_command_raw_summary.get("left_raw")
                if manual_bridge_command_raw_summary.get("lr_pair_available")
                else manual_command_raw_summary.get("left_raw")
            ),
            "command_raw_latest_right": (
                manual_bridge_command_raw_summary.get("right_raw")
                if manual_bridge_command_raw_summary.get("lr_pair_available")
                else manual_command_raw_summary.get("right_raw")
            ),
            "command_raw_latest_linear_x": manual_command_raw_summary.get("linear_x"),
            "command_raw_latest_angular_z": manual_command_raw_summary.get("angular_z"),
            "wheel_feedback_nonzero_observed": manual_wheel_feedback_summary["lr_nonzero_observed"],
            "wheel_feedback_lr_nonzero_proven": manual_wheel_feedback_summary["lr_nonzero_observed"],
            "imu_attitude_delta_observed": manual_imu_delta_summary["imu_attitude_delta_observed"],
            "motion_signal_observed": manual_motion_signal_observed,
            "motion_signal_source": manual_motion_signal_source,
            "motion_evidence_complete": manual_motion_evidence_complete,
            "motion_evidence_source": (
                "command_raw_lr_plus_motion_signal"
                if manual_command_raw_lr_nonzero_proven and manual_motion_signal_observed
                else "command_raw_twist_plus_motion_signal"
                if manual_command_raw_twist_nonzero_proven and manual_motion_signal_observed
                else "not_complete"
            ),
            "feedback_ack": feedback_ack,
            "safe_to_control": False,
            "sends_commands": True,
            "robot_control_executed": bool(first.get("ok")),
            "delivery_success": False,
            "hil_pass": False,
            "primary_actions_enabled": False,
            **latency_fields,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=os.getenv("HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", str(DEFAULT_PORT))))
    parser.add_argument("--camera-base-url", default=os.getenv("ROBER_CAMERA_BASE_URL", DEFAULT_CAMERA_BASE_URL))
    parser.add_argument("--base-port", default=os.getenv("ROBER_BASE_SERIAL_PORT", DEFAULT_BASE_PORT))
    parser.add_argument("--base-baudrate", type=int, default=int(os.getenv("ROBER_BASE_BAUDRATE", str(DEFAULT_BASE_BAUDRATE))))
    parser.add_argument("--max-speed", type=float, default=float(os.getenv("ROBER_BASE_MAX_SPEED", str(DEFAULT_MAX_SPEED))))
    parser.add_argument("--base-command-mode", choices=sorted(ALLOWED_BASE_COMMAND_MODES), default=os.getenv("ROBER_BASE_COMMAND_MODE", DEFAULT_BASE_COMMAND_MODE))
    parser.add_argument(
        "--nav2-base-command-mode",
        choices=sorted(ALLOWED_NAV2_BASE_COMMAND_MODES),
        default=os.getenv("ROBER_NAV2_BASE_COMMAND_MODE", DEFAULT_NAV2_BASE_COMMAND_MODE),
    )
    parser.add_argument("--manual-pwm-min-abs", type=int, default=int(os.getenv("ROBER_MANUAL_PWM_MIN_ABS", str(DEFAULT_MANUAL_PWM_MIN_ABS))))
    parser.add_argument("--manual-pwm-max-abs", type=int, default=int(os.getenv("ROBER_MANUAL_PWM_MAX_ABS", str(DEFAULT_MANUAL_PWM_MAX_ABS))))
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
        "--nav2-goal-execution-artifact-path",
        default=os.getenv("ROBER_NAV2_GOAL_EXECUTION_ARTIFACT_PATH", DEFAULT_NAV2_GOAL_EXECUTION_ARTIFACT_PATH),
    )
    parser.add_argument(
        "--delivery-completion-artifact-path",
        default=os.getenv("ROBER_DELIVERY_COMPLETION_ARTIFACT_PATH", DEFAULT_DELIVERY_COMPLETION_ARTIFACT_PATH),
    )
    parser.add_argument(
        "--free-roam-autonomy-artifact-path",
        default=os.getenv("ROBER_FREE_ROAM_AUTONOMY_ARTIFACT_PATH", DEFAULT_FREE_ROAM_AUTONOMY_ARTIFACT_PATH),
    )
    parser.add_argument(
        "--elevator-status-artifact-path",
        default=os.getenv("ROBER_ELEVATOR_STATUS_ARTIFACT_PATH", DEFAULT_ELEVATOR_STATUS_ARTIFACT_PATH),
    )
    parser.add_argument(
        "--operator-report-artifact-path",
        default=os.getenv("ROBER_OPERATOR_REPORT_ARTIFACT_PATH", DEFAULT_OPERATOR_REPORT_ARTIFACT_PATH),
    )
    parser.add_argument("--radar-start-command", default=os.getenv("ROBER_RADAR_START_COMMAND", DEFAULT_RADAR_START_COMMAND))
    parser.add_argument("--radar-stop-command", default=os.getenv("ROBER_RADAR_STOP_COMMAND", DEFAULT_RADAR_STOP_COMMAND))
    parser.add_argument("--lidar-scan-proof-runtime-command", default=os.getenv("ROBER_LIDAR_SCAN_PROOF_RUNTIME_COMMAND"))
    parser.add_argument(
        "--lidar-scan-proof-runtime-warmup-s",
        type=float,
        default=float(os.getenv("ROBER_LIDAR_SCAN_PROOF_RUNTIME_WARMUP_S", str(DEFAULT_LIDAR_SCAN_PROOF_RUNTIME_WARMUP_S))),
    )
    parser.add_argument("--map-start-command", default=os.getenv("ROBER_MAP_START_COMMAND"))
    parser.add_argument("--map-reset-command", default=os.getenv("ROBER_MAP_RESET_COMMAND"))
    parser.add_argument("--map-save-command", default=os.getenv("ROBER_MAP_SAVE_COMMAND"))
    parser.add_argument("--map-load-command", default=os.getenv("ROBER_MAP_LOAD_COMMAND"))
    parser.add_argument("--localize-reset-command", default=os.getenv("ROBER_LOCALIZE_RESET_COMMAND"))
    parser.add_argument("--nav2-start-command", default=os.getenv("ROBER_NAV2_START_COMMAND", DEFAULT_NAV2_START_COMMAND))
    parser.add_argument("--nav2-stop-command", default=os.getenv("ROBER_NAV2_STOP_COMMAND", DEFAULT_NAV2_STOP_COMMAND))
    parser.add_argument("--nav2-status-command", default=os.getenv("ROBER_NAV2_STATUS_COMMAND", DEFAULT_NAV2_STATUS_COMMAND))
    return parser.parse_args()


async def run_server(args: argparse.Namespace) -> None:
    """启动 aiohttp API，所有硬件子面都挂在 /api 下。"""
    from aiohttp import web

    api = UpperRobotApi(
        camera_base_url=args.camera_base_url,
        base_port=args.base_port,
        base_baudrate=args.base_baudrate,
        max_speed=args.max_speed,
        base_command_mode=args.base_command_mode,
        nav2_base_command_mode=args.nav2_base_command_mode,
        manual_pwm_min_abs=args.manual_pwm_min_abs,
        manual_pwm_max_abs=args.manual_pwm_max_abs,
        feedback_samples_artifact_path=args.feedback_samples_artifact_path,
        lidar_scan_proof_artifact_path=args.lidar_scan_proof_artifact_path,
        lidar_raw_packet_proof_artifact_path=args.lidar_raw_packet_proof_artifact_path,
        map_artifact_dir=args.map_artifact_dir,
        map_lifecycle_proof_artifact_path=args.map_lifecycle_proof_artifact_path,
        localization_artifact_path=args.localization_artifact_path,
        nav2_lifecycle_artifact_path=args.nav2_lifecycle_artifact_path,
        nav2_goal_execution_artifact_path=args.nav2_goal_execution_artifact_path,
        delivery_completion_artifact_path=args.delivery_completion_artifact_path,
        free_roam_autonomy_artifact_path=args.free_roam_autonomy_artifact_path,
        elevator_status_artifact_path=args.elevator_status_artifact_path,
        operator_report_artifact_path=args.operator_report_artifact_path,
        radar_start_command=args.radar_start_command,
        radar_stop_command=args.radar_stop_command,
        lidar_scan_proof_runtime_command=args.lidar_scan_proof_runtime_command,
        lidar_scan_proof_runtime_warmup_s=args.lidar_scan_proof_runtime_warmup_s,
        map_start_command=args.map_start_command,
        map_reset_command=args.map_reset_command,
        map_save_command=args.map_save_command,
        map_load_command=args.map_load_command,
        localize_reset_command=args.localize_reset_command,
        nav2_start_command=args.nav2_start_command,
        nav2_stop_command=args.nav2_stop_command,
        nav2_status_command=args.nav2_status_command,
    )
    # 在开始监听 HTTP 前完成 rclpy import/node/publisher/DDS graph 预热；该步骤绝不发布 /cmd_vel。
    prewarm = prewarm_ros_cmd_vel_context()
    app = create_app(api)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, args.host, args.port)
    await site.start()
    print(
        json.dumps(
            {
                "event": "upper_robot_api_started",
                "host": args.host,
                "port": args.port,
                "rclpy_cmd_vel_prewarm_status": prewarm.get("prewarm_status"),
                "rclpy_cmd_vel_subscription_count": prewarm.get("prewarm_subscription_count", 0),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    while True:
        await asyncio.sleep(3600)


def create_app(api: UpperRobotApi) -> Any:
    """集中注册 aiohttp 路由，测试可直接解析路由而不启动监听端口。"""
    from aiohttp import web

    camera_mjpeg_relay = SharedCameraMjpegRelay(urljoin(api.camera_base_url + "/", "mjpeg"))

    async def options(_: web.Request) -> Any:
        return json_response({})

    async def root(_: web.Request) -> Any:
        return json_response({"schema": SCHEMA, "status": "ready", "routes": (await api.unified_status())["routes"], **proof_flags()})

    async def health(_: web.Request) -> Any:
        return json_response({"schema": f"{SCHEMA}.health", "status": "ready", "generated_at_ms": now_ms(), **proof_flags()})

    async def status(_: web.Request) -> Any:
        try:
            return json_response(await asyncio.wait_for(api.unified_status(), timeout=STATUS_TOTAL_TIMEOUT_S))
        except asyncio.TimeoutError as exc:
            return json_response(
                status_timeout_payload(f"status_total_timeout_{STATUS_TOTAL_TIMEOUT_S:g}s", exc),
                status=504,
            )
        except Exception as exc:  # noqa: BLE001 - 顶层 status 也必须 fail-closed，不让 aiohttp 500 泄漏到 PC。
            return json_response(status_timeout_payload("status_total_exception", exc), status=502)

    async def camera_health(_: web.Request) -> Any:
        http_status, payload = await api.camera_health()
        return json_response(payload, status=http_status)

    async def camera_mjpeg_status(_: web.Request) -> Any:
        """共享 MJPEG 状态只读汇总；不能因为查状态就启动新视频流。"""
        http_status, payload = await api.camera_health()
        return json_response(
            camera_mjpeg_status_payload(
                camera_base_url=api.camera_base_url,
                health_http_status=http_status,
                health_payload=payload,
                relay_snapshot=camera_mjpeg_relay.snapshot(),
            ),
            status=200,
        )

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

    async def camera_first_frame_probe(request: web.Request) -> Any:
        body = await request.json() if request.can_read_body else {}
        http_status, payload = await api.camera_first_frame_probe(body if isinstance(body, dict) else {})
        return json_response(payload, status=http_status)

    async def camera_usb_recovery(request: web.Request) -> Any:
        body = await request.json() if request.can_read_body else {}
        http_status, payload = await api.camera_usb_recovery(body if isinstance(body, dict) else {})
        return json_response(payload, status=http_status)

    async def camera_mjpeg(request: web.Request) -> Any:
        """只读 MJPEG 预览代理；用于 WebRTC ICE 未连通时仍能显示真实连续画面。"""
        queue = camera_mjpeg_relay.register()
        stream_response: Any | None = None
        try:
            # 首个客户端负责拉起共享上游；后续客户端只等待同一个 content-type 事件。
            await asyncio.wait_for(camera_mjpeg_relay.content_type_loaded.wait(), timeout=CAMERA_MJPEG_RELAY_HEADER_TIMEOUT_S)
            content_type = camera_mjpeg_relay.content_type
            if "multipart/x-mixed-replace" not in content_type:
                return json_response(
                    {
                        "error": "camera_mjpeg_proxy_failed",
                        "remote_http_status": camera_mjpeg_relay.last_remote_http_status,
                        "relay": camera_mjpeg_relay.snapshot(),
                        **proof_flags(),
                    },
                    status=502,
                )
            response = web.StreamResponse(
                status=200,
                headers={
                    "Content-Type": content_type,
                    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                    "Access-Control-Allow-Origin": "*",
                    "X-Rober-Camera-Relay": "shared-mjpeg",
                },
            )
            await response.prepare(request)
            stream_response = response
            while True:
                chunk = await queue.get()
                if chunk is None:
                    break
                try:
                    await response.write(chunk)
                except (ConnectionResetError, asyncio.CancelledError):
                    break
            return response
        except asyncio.TimeoutError:
            return json_response(
                {
                    "error": "camera_mjpeg_proxy_failed",
                    "detail": "shared_mjpeg_relay_timeout",
                    "relay": camera_mjpeg_relay.snapshot(),
                    **proof_flags(),
                },
                status=502,
            )
        except Exception as exc:  # noqa: BLE001 - 摄像头流失败不能影响其他上位 API。
            if stream_response is not None:
                return stream_response
            return json_response({"error": "camera_mjpeg_proxy_failed", "detail": compact_error(exc), "relay": camera_mjpeg_relay.snapshot(), **proof_flags()}, status=502)
        finally:
            camera_mjpeg_relay.unregister(queue)

    async def radar_status(_: web.Request) -> Any:
        # 同步硬件/文件状态读取放到线程，避免并发 PC summary 卡住 aiohttp 事件循环。
        return json_response(await asyncio.to_thread(api.radar_status))

    async def radar_start(_: web.Request) -> Any:
        return json_response(api.radar_control("start"))

    async def radar_stop(_: web.Request) -> Any:
        return json_response(api.radar_control("stop"))

    async def radar_scan_proof_refresh(request: web.Request) -> Any:
        body = await request.json() if request.can_read_body else {}
        payload = await api.radar_scan_proof_refresh(body if isinstance(body, dict) else {})
        return json_response(payload)

    async def radar_scan_proof_latest(_: web.Request) -> Any:
        http_status, payload = await asyncio.to_thread(api.radar_scan_proof_latest)
        return json_response(payload, status=http_status)

    async def radar_raw_packet_proof_latest(_: web.Request) -> Any:
        http_status, payload = await asyncio.to_thread(api.radar_raw_packet_proof_latest)
        return json_response(payload, status=http_status)

    async def base_status(_: web.Request) -> Any:
        return json_response(await asyncio.to_thread(api.base_status))

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
        return json_response(await asyncio.to_thread(api.map_list))

    async def map_status(_: web.Request) -> Any:
        # 只读地图状态入口，方便现场脚本直接 GET，不触发建图、保存或 ROS 查询。
        return json_response(await asyncio.to_thread(api.map_status))

    async def map_preview(request: web.Request) -> Any:
        # 地图预览只读本地 YAML/PGM，不触发 SLAM、Nav2、底盘或串口。
        return json_response(await asyncio.to_thread(api.map_preview, request.query.get("map_name")))

    async def map_proof_refresh(request: web.Request) -> Any:
        body = await request.json() if request.can_read_body else {}
        payload = await api.map_proof_refresh(body if isinstance(body, dict) else {})
        return json_response(payload)

    async def map_proof_latest(_: web.Request) -> Any:
        http_status, payload = await asyncio.to_thread(api.map_proof_latest)
        return json_response(payload, status=http_status)

    async def localize_reset(request: web.Request) -> Any:
        body = await request.json() if request.can_read_body else {}
        return json_response(await api.localize_reset(body if isinstance(body, dict) else {}))

    async def localize_proof_latest(_: web.Request) -> Any:
        http_status, payload = await asyncio.to_thread(api.localize_proof_latest)
        return json_response(payload, status=http_status)

    async def nav2_status(_: web.Request) -> Any:
        return json_response(await asyncio.to_thread(api.nav2_status))

    async def nav2_proof_refresh(request: web.Request) -> Any:
        body = await request.json() if request.can_read_body else {}
        payload = await api.nav2_proof_refresh(body if isinstance(body, dict) else {})
        return json_response(payload)

    async def nav2_proof_latest(_: web.Request) -> Any:
        http_status, payload = await asyncio.to_thread(api.nav2_proof_latest)
        return json_response(payload, status=http_status)

    async def nav2_goal_execute(request: web.Request) -> Any:
        body = await request.json() if request.can_read_body else {}
        return json_response(await api.nav2_goal_execute(body if isinstance(body, dict) else {}))

    async def nav2_goal_execution_latest(_: web.Request) -> Any:
        http_status, payload = await asyncio.to_thread(api.nav2_goal_execution_latest)
        return json_response(payload, status=http_status)

    async def delivery_complete(request: web.Request) -> Any:
        body = await request.json() if request.can_read_body else {}
        return json_response(api.delivery_complete(body if isinstance(body, dict) else {}))

    async def delivery_latest(_: web.Request) -> Any:
        http_status, payload = await asyncio.to_thread(api.delivery_latest)
        return json_response(payload, status=http_status)

    async def free_roam_autonomy_latest(_: web.Request) -> Any:
        http_status, payload = await asyncio.to_thread(api.free_roam_autonomy_latest)
        return json_response(payload, status=http_status)

    async def free_roam_autonomy_start(request: web.Request) -> Any:
        body = await request.json() if request.can_read_body else {}
        payload = api.free_roam_autonomy_control("start", body if isinstance(body, dict) else {})
        return json_response(payload, status=200 if payload.get("status") == "requested" else 400)

    async def free_roam_autonomy_stop(request: web.Request) -> Any:
        body = await request.json() if request.can_read_body else {}
        payload = api.free_roam_autonomy_control("stop", body if isinstance(body, dict) else {})
        return json_response(payload, status=200 if payload.get("status") == "requested" else 502)

    async def nav2_start(request: web.Request) -> Any:
        # strict start 必须消费 JSON；bodyless/非法 JSON 也返回结构化 NO-GO，而不是落到旧 `{}` 语义。
        if not request.can_read_body:
            return json_response(api.nav2_control("start", None))
        try:
            body = await request.json()
        except Exception as exc:  # noqa: BLE001 - JSON 解码失败必须在任何 lifecycle 命令前 fail closed。
            return json_response(api.nav2_control("start", None, request_error=compact_error(exc)))
        if not isinstance(body, dict):
            error = {"type": "invalid_nav2_start_body", "message": "nav2 start JSON body must be an object"}
            return json_response(api.nav2_control("start", None, request_error=error))
        return json_response(api.nav2_control("start", body))

    async def nav2_stop(_: web.Request) -> Any:
        return json_response(api.nav2_control("stop"))

    async def elevator_status(_: web.Request) -> Any:
        return json_response(await asyncio.to_thread(api.elevator_status))

    async def operator_report_post(request: web.Request) -> Any:
        body = await request.json() if request.can_read_body else {}
        if not isinstance(body, dict):
            payload = {
                "schema": f"{SCHEMA}.operator_report_result",
                "generated_at_ms": now_ms(),
                "endpoint": ROUTE_PATHS["operator_report"],
                "error": {"type": "invalid_operator_report", "message": "JSON body must be an object"},
                "operator_report": None,
                "operator_report_status": "unsafe_or_incomplete",
                "does_not_replace": list(OPERATOR_REPORT_DOES_NOT_REPLACE),
                **operator_report_guard_flags(),
            }
            return json_response(payload, status=400)
        return json_response(api.operator_report(body))

    async def operator_report_get(_: web.Request) -> Any:
        http_status, payload = await asyncio.to_thread(api.operator_report_latest)
        return json_response(payload, status=http_status)

    async def base_stop(_: web.Request) -> Any:
        if api._manual_hold_watchdog_task is not None and not api._manual_hold_watchdog_task.done():
            api._manual_hold_watchdog_task.cancel()
        api._manual_hold_state = {**api._manual_hold_state, "active": False, "release_stop_at_ms": now_ms()}
        return json_response(build_stop_payload(api.base_port, api.base_baudrate))

    async def base_feedback_request(request: web.Request) -> Any:
        body = await request.json() if request.can_read_body else {}
        return json_response(await api.base_feedback_request(body if isinstance(body, dict) else {}))

    async def base_feedback_samples(request: web.Request) -> Any:
        body = await request.json() if request.can_read_body else {}
        return json_response(await api.base_feedback_samples(body if isinstance(body, dict) else {}))

    async def base_feedback_samples_latest(_: web.Request) -> Any:
        http_status, payload = await asyncio.to_thread(api.base_feedback_samples_latest)
        return json_response(payload, status=http_status)

    async def base_manual(request: web.Request) -> Any:
        # receive 点位必须在 JSON 解析前记录；但只在 upper 本进程内计算 span。
        upper_receive_mono_ns = time.monotonic_ns()
        body = await request.json()
        body = body if isinstance(body, dict) else {}
        try:
            latency_trace = normalize_latency_trace(body.get("latency_trace"))
        except ValueError as exc:
            return json_response(
                {
                    "schema": f"{SCHEMA}.base_manual_result",
                    "accepted": False,
                    "error": {"type": "latency_trace_invalid", "message": str(exc)},
                    "safe_to_control": False,
                    "robot_control_executed": False,
                    "delivery_success": False,
                    "hil_pass": False,
                },
                status=400,
            )
        if latency_trace is not None:
            # 只把白名单后的 envelope 和内部 receive 点交给 manual_control，未知字段已丢弃。
            body = {**body, "latency_trace": latency_trace, "_upper_receive_mono_ns": upper_receive_mono_ns}
        payload = await api.manual_control(body)
        return json_response(payload, status=200 if payload.get("accepted", True) else 400)

    app = web.Application()
    app.router.add_route("OPTIONS", "/{tail:.*}", options)
    app.router.add_get("/", root)
    app.router.add_get("/health", health)
    app.router.add_get(ROUTE_PATHS["health"], health)
    app.router.add_get("/api/status", status)
    app.router.add_get(ROUTE_PATHS["camera_health"], camera_health)
    app.router.add_get(ROUTE_PATHS["camera_devices"], camera_devices)
    app.router.add_post(ROUTE_PATHS["camera_offer"], camera_offer)
    app.router.add_post(ROUTE_PATHS["camera_peer_close"], camera_peer_close)
    app.router.add_post(ROUTE_PATHS["camera_first_frame_probe"], camera_first_frame_probe)
    app.router.add_post(ROUTE_PATHS["camera_usb_recovery"], camera_usb_recovery)
    app.router.add_get(ROUTE_PATHS["camera_mjpeg"], camera_mjpeg)
    app.router.add_get(ROUTE_PATHS["camera_mjpeg_status"], camera_mjpeg_status)
    app.router.add_get(ROUTE_PATHS["radar_status"], radar_status)
    app.router.add_post(ROUTE_PATHS["radar_start"], radar_start)
    app.router.add_post(ROUTE_PATHS["radar_stop"], radar_stop)
    app.router.add_post(ROUTE_PATHS["radar_scan_proof_refresh"], radar_scan_proof_refresh)
    app.router.add_get(ROUTE_PATHS["radar_scan_proof_latest"], radar_scan_proof_latest)
    app.router.add_get(ROUTE_PATHS["radar_raw_packet_proof_latest"], radar_raw_packet_proof_latest)
    app.router.add_post(ROUTE_PATHS["map_start"], map_start)
    app.router.add_post(ROUTE_PATHS["map_reset"], map_reset)
    app.router.add_post(ROUTE_PATHS["map_save"], map_save)
    app.router.add_post(ROUTE_PATHS["map_load"], map_load)
    app.router.add_get(ROUTE_PATHS["map_status"], map_status)
    app.router.add_get(ROUTE_PATHS["map_list"], map_list)
    app.router.add_get(ROUTE_PATHS["map_preview"], map_preview)
    app.router.add_post(ROUTE_PATHS["map_proof_refresh"], map_proof_refresh)
    app.router.add_get(ROUTE_PATHS["map_proof_latest"], map_proof_latest)
    app.router.add_post(ROUTE_PATHS["localize_reset"], localize_reset)
    app.router.add_get(ROUTE_PATHS["localize_proof_latest"], localize_proof_latest)
    app.router.add_get(ROUTE_PATHS["nav2_status"], nav2_status)
    app.router.add_post(ROUTE_PATHS["nav2_proof_refresh"], nav2_proof_refresh)
    app.router.add_get(ROUTE_PATHS["nav2_proof_latest"], nav2_proof_latest)
    app.router.add_post(ROUTE_PATHS["nav2_goal_execute"], nav2_goal_execute)
    app.router.add_get(ROUTE_PATHS["nav2_goal_execution_latest"], nav2_goal_execution_latest)
    app.router.add_post(ROUTE_PATHS["delivery_complete"], delivery_complete)
    app.router.add_get(ROUTE_PATHS["delivery_latest"], delivery_latest)
    app.router.add_get(ROUTE_PATHS["free_roam_autonomy_latest"], free_roam_autonomy_latest)
    app.router.add_post(ROUTE_PATHS["free_roam_autonomy_start"], free_roam_autonomy_start)
    app.router.add_post(ROUTE_PATHS["free_roam_autonomy_stop"], free_roam_autonomy_stop)
    app.router.add_post(ROUTE_PATHS["nav2_start"], nav2_start)
    app.router.add_post(ROUTE_PATHS["nav2_stop"], nav2_stop)
    app.router.add_get(ROUTE_PATHS["elevator_status"], elevator_status)
    app.router.add_post(ROUTE_PATHS["operator_report"], operator_report_post)
    app.router.add_get(ROUTE_PATHS["operator_report"], operator_report_get)
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
