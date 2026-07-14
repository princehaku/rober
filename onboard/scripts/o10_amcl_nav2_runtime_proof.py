#!/usr/bin/env python3
"""No-motion AMCL/Nav2 runtime proof collector for O10."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shlex
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.upper_robot_api.v1.nav2_lifecycle_runtime_proof"
DEFAULT_ROS_SETUP = "/opt/ros/humble/setup.bash"
DEFAULT_ONBOARD_SETUP = "/root/rober/onboard/install/setup.bash"
DEFAULT_WORKDIR = "/root/rober/onboard"
DEFAULT_OUTPUT = "/root/rober/onboard/runtime/nav2_lifecycle_latest.json"
DEFAULT_MAP_PROOF = "/root/rober/onboard/runtime/map_lifecycle_latest.json"
DEFAULT_MAP_DIR = "/root/rober/onboard/runtime/maps"
DEFAULT_MANAGED_MAP_YAML = "/root/rober/onboard/runtime/maps/trashbot_map.yaml"
DEFAULT_MANAGED_LIDAR_SERIAL_PORT = "/dev/ttyACM0"
DEFAULT_MANAGED_LIDAR_SERIAL_BAUDRATE = 230400
DEFAULT_MANAGED_TIMEOUT_S = 20.0
DEFAULT_MANAGED_LIFECYCLE_START_DELAY_S = 3.0
DEFAULT_MANAGED_BASE_FRAME_ID = "base_link"
DEFAULT_MANAGED_ODOM_FRAME_ID = "odom"
DEFAULT_MANAGED_LASER_FRAME_ID = "laser_frame"
STALE_MANAGED_RUNTIME_MARKERS = (
    "rober_nav2_localization_",
    "managed_static_tf_broadcaster",
)
STALE_MANAGED_RUNTIME_ROLE_MARKERS = (
    "nav2_map_server",
    "nav2_amcl",
    "nav2_lifecycle_manager",
    "nav2_planner",
    "ros2_trashbot_hardware lidar_driver",
    "managed_static_tf_broadcaster",
    "managed_runtime_boundary=no_motion_",
)
DDS_NO_SHM_ENV = {
    "RMW_FASTRTPS_USE_SHM": "0",
    "FASTDDS_BUILTIN_TRANSPORTS": "UDPv4",
}
MANAGED_RUNTIME_GRAPH_HISTORY_LIMIT = 12
MANAGED_RUNTIME_GRAPH_CHILD_COMMAND_TIMEOUT_S = 3.0
MANAGED_RUNTIME_GRAPH_FALLBACK_TIMEOUT_S = 2.5
MANAGED_RUNTIME_GRAPH_CLOSEOUT_RESERVE_S = 0.75
AMCL_CLI_FALLBACK_TIMEOUT_S = 3.0
ROS2_GRAPH_ROOT_CAUSE_PROBE_TIMEOUTS = {
    "ros2_node_list": 2.5,
    "ros2_node_list_no_daemon": 2.5,
    "ros2_daemon_status": 2.0,
    "ros2_node_list_help": 5.0,
    "ros2_topic_list": 2.5,
    "rclpy_graph_segments": 4.0,
    "workspace_environment": 2.0,
}
# batch 内现在还会执行一次 daemon-safe reset retry；总外层预算必须覆盖 source、
# 原始 graph 命令、stop/start 和 retry graph 命令，避免只留下半截 current_command。
ROS2_GRAPH_SOURCE_AMORTIZED_BATCH_TIMEOUT_S = 52.0
ROS2_GRAPH_SOURCE_AMORTIZED_RCLPY_WAIT_S = 1.2
ROS2_GRAPH_SOURCE_AMORTIZED_COMMANDS = {
    "ros2_node_list": ("ros2 node list", 2.5),
    "ros2_node_list_no_daemon": ("ros2 node list --no-daemon", 2.5),
    "ros2_daemon_status": ("ros2 daemon status", 2.0),
    "ros2_node_list_help": ("ros2 node list --help", 5.0),
    "ros2_topic_list": ("ros2 topic list", 2.5),
}
ROS2_GRAPH_DAEMON_SAFE_RETRY_COMMANDS = {
    "ros2_daemon_stop": ("ros2 daemon stop", 2.5),
    "ros2_daemon_start": ("ros2 daemon start", 3.0),
    "ros2_daemon_status_after_reset": ("ros2 daemon status", 2.0),
    # 这一轮要对齐上一轮 next_live_command 的 8s graph readback，避免 3s budget 过短又把
    # reset 后 graph 是否恢复混成同一 blocker。
    "ros2_node_list_after_daemon_reset": ("ros2 node list", 8.0),
    "ros2_topic_list_after_daemon_reset": ("ros2 topic list", 8.0),
}
ROS2_GRAPH_TIMEOUT_CLASSIFICATIONS = {
    "ros2_daemon_or_dds_graph_discovery_timeout",
    "ros2_cli_plugin_or_import_timeout",
    "workspace_source_or_env_mismatch",
    "managed_process_lifecycle_not_ready",
    "tf_runtime_secondary_after_graph_blocked",
    "root_cause_unclassified_after_probe",
}
MAP_SERVER_GRAPH_LIFECYCLE_CLASSIFICATIONS = {
    "map_server_node_absent",
    "lifecycle_manager_or_process_startup_missing",
    "daemon_or_dds_graph_visibility_failed",
    "helper_budget_or_timing_exhausted",
    "map_server_lifecycle_active",
}
MAP_SERVER_PRESENCE_RECOVERY_CLASSIFICATIONS = {
    "presence_recovery_not_requested_read_only_existing_graph",
    "managed_map_yaml_missing",
    "managed_map_yaml_unreadable",
    "managed_runtime_start_failed",
    "managed_runtime_process_exited_before_map_server_presence",
    "managed_runtime_graph_unreadable_after_start",
    "managed_runtime_started_map_server_not_observed",
    "lifecycle_manager_not_serving_map_server",
    "map_server_lifecycle_rpc_timeout_after_recovery",
    "map_server_lifecycle_not_active_after_recovery",
    "map_server_lifecycle_command_failed_after_recovery",
    "map_server_lifecycle_active",
}
MAP_SERVER_LIFECYCLE_ACTIVATION_CLASSIFICATIONS = {
    "map_server_yaml_image_unreadable",
    "map_server_yaml_invalid_fields",
    "map_server_frame_id_missing_or_invalid",
    "map_server_process_exited_during_configure",
    "map_server_configure_exception",
    "lifecycle_manager_map_server_name_mismatch",
    "lifecycle_manager_map_server_namespace_mismatch",
    "map_server_activate_callback_failed",
    "map_server_lifecycle_service_timeout_with_process_alive",
    "map_server_lifecycle_active",
    "map_server_lifecycle_activation_not_requested",
    "map_server_configure_completed_lifecycle_blocked_by_amcl_configure_failure",
}
MAP_SERVER_TRANSITION_CALLBACK_CLASSIFICATIONS = {
    "map_server_transition_probe_not_requested",
    "map_server_lifecycle_active",
    "map_server_configure_callback_return_failure",
    "map_server_changestate_response_failure_before_configure_callback_log",
    "map_server_changestate_response_false_before_map_io_completion",
    "map_server_on_configure_return_false_after_valid_map_io_deferred_completion",
    "map_server_loadmap_response_success_equivalent_after_changestate_failure",
    "map_server_changestate_response_failure_after_image_load_before_map_read_completed",
    "map_server_configure_return_failure_before_deferred_map_read_completed",
    "map_server_configure_return_failure_after_map_read_completed",
    "map_server_activate_callback_return_failure",
    "map_server_change_state_rpc_dds_shm_transport_port_lock",
    "map_server_lifecycle_service_rpc_timeout",
    "map_server_lifecycle_change_state_response_error",
    "map_server_configure_completed_lifecycle_blocked_by_amcl_configure_failure",
    "map_server_bond_creation_timeout",
    "map_server_bond_wait_timeout_after_active",
    "map_server_process_exited_during_transition",
    "map_server_transition_callback_exception",
    "map_server_transition_callback_unclassified",
}
MANAGED_RUNTIME_GRAPH_BLOCKED_REASONS = {
    "ros2_node_list_timeout",
    "ros2_node_list_empty_after_wait",
    "ros2_node_list_failed",
    "rclpy_node_names_empty_after_wait",
    "rclpy_node_names_failed",
    "rclpy_node_names_parse_failed",
    "managed_runtime_process_active_graph_not_observable",
    "managed_runtime_required_nodes_not_observed",
}
TF_CHAIN_KEYS = (
    "map_to_odom",
    "odom_to_base_link",
    "base_link_to_laser_frame",
    "map_to_base_link",
)
LOCALIZATION_SIGNAL_TOPICS = {
    "/scan": "sensor_msgs/msg/LaserScan",
    "/map": "nav_msgs/msg/OccupancyGrid",
    "/amcl_pose": "geometry_msgs/msg/PoseWithCovarianceStamped",
    "/odom": "nav_msgs/msg/Odometry",
    "/tf": "tf2_msgs/msg/TFMessage",
    "/tf_static": "tf2_msgs/msg/TFMessage",
}
FRESHNESS_WALL_CLOCK_MIN_MS = 946684800000
FRESHNESS_STALE_AFTER_MS = 3000
ROS2_PREFLIGHT_COMMAND = "command -v ros2"
# 板端 API 子进程首次 source ROS/workspace 可能超过 3 秒；preflight 只查可执行文件，允许稍宽窗口。
ROS2_PREFLIGHT_TIMEOUT_S = 6.0
# 真板 source ROS + workspace 在负载高时会略超过 8s；放宽到 12s，避免把可恢复的
# sourced shell 抖动误收口为 workspace/source mismatch。
SOURCE_PREFLIGHT_TIMEOUT_S = 12.0
ROS2_CLI_LAYER_TIMEOUT_S = 12.0
ROS2_LAYER_COMMAND_TIMEOUT_S = 2.0
ROS2_LIGHTWEIGHT_READINESS_TIMEOUT_S = 3.0
ROS2_LIGHTWEIGHT_NODE_LIST_TIMEOUT_S = 8.0
# 真板上 `ros2 --help` 冷启动稳定在 4.5s 左右；这里放到 6s，避免把可用 CLI 误判成不可用。
ROS2_LAYER_INVOCATION_TIMEOUT_S = 6.0
RCLPY_PREFLIGHT_TIMEOUT_S = 6.0
# lifecycle CLI 是本轮主 blocker；第一次保持旧预算，retry 用现场 `--timeout-s`
# 拉宽窗口，从而把“节点可见但 lifecycle RPC 卡住”和“确实 inactive”分开落盘。
LIFECYCLE_CLI_FIRST_ATTEMPT_TIMEOUT_S = 10.0
LIFECYCLE_CLI_RETRY_MIN_TIMEOUT_S = 12.0
LIFECYCLE_CLI_RETRY_MAX_TIMEOUT_S = 24.0
LIFECYCLE_GRAPH_VISIBILITY_TIMEOUT_S = 8.0
# 这个预算覆盖一次 source、三条 PATH 查询、一次最小 CLI invocation 和一次 rclpy import。
# 关键点是只 source 一次；各子命令继承同一个环境，避免把重复 source 抖动混进 PATH/CLI blocker。
SOURCE_AMORTIZED_CLI_PREFLIGHT_SCHEMA = "trashbot.o10.source_amortized_cli_preflight.v1"
SOURCE_AMORTIZED_CLI_PREFLIGHT_TIMEOUT_S = 30.0
LOCALIZATION_LIFECYCLE_NODES = {
    "map_server": "/map_server",
    "amcl": "/amcl",
}
EXPECTED_PACKAGES = [
    "ros2_trashbot_bringup",
    "ros2_trashbot_nav",
    "nav2_map_server",
    "nav2_amcl",
    "nav2_lifecycle_manager",
]
PACKAGE_CHECK_BATCH_TIMEOUT_S = 5.0
TF_ECHO_SHELL_TIMEOUT_S = 10.0
# 板端 ros2 run/tf2_echo 退出会比 shell timeout 多耗一段启动和清理时间；外层必须留足余量。
TF_ECHO_PROCESS_TIMEOUT_S = 14.0
BLOCKED_COMMAND_TOKENS = [
    "T=1",
    "T=13",
    "T=130",
    "T=131",
    "/cmd_vel",
    "/api/base/manual",
    "/api/base/",
    "/api/nav2/start",
    "/api/nav2/stop",
    "navigate_to_pose",
]
PATH_GENERATION_ACTION_CANDIDATES = [
    "/planner_server/compute_path_to_pose",
    "/compute_path_to_pose",
    "compute_path_to_pose",
]
NAV2_PLANNER_CONFIG_PATH = Path(__file__).resolve().parents[1] / "src" / "ros2_trashbot_nav" / "config" / "nav2_params.yaml"
ACTIVE_PHASE_WRITER: PhaseArtifactWriter | None = None


def now_ms() -> int:
    """统一毫秒时间戳，方便和 upper API latest/readback 做同轮对齐。"""
    return int(time.time() * 1000)


def safety_flags() -> dict[str, Any]:
    """O10 collector 只做 no-motion proof，所有可控/交付/HIL 标志都必须固定关闭。"""
    return {
        "safe_to_control": False,
        "sends_base_motion_commands": False,
        "sends_motion_commands": False,
        "publishes_cmd_vel": False,
        "calls_base_manual": False,
        "robot_control_executed": False,
        "delivery_success": False,
        "route_execution_success": False,
        "hil_pass": False,
        "uses_base_uart": False,
    }


def path_generation_envelope_fields(proof: dict[str, Any] | None) -> dict[str, bool]:
    """顶层 artifact 兼容字段只镜像 proof，避免 strict no-motion 产物出现 null。"""
    if not isinstance(proof, dict):
        return {"path_generation_attempted": False, "path_generated": False}
    return {
        "path_generation_attempted": bool(proof.get("path_generation_attempted")),
        "path_generated": bool(proof.get("path_generated")),
    }


class PhaseArtifactWriter:
    """阶段性写 latest，避免 helper 被外层 timeout 打断时丢失现场定位进度。"""

    def __init__(self, args: argparse.Namespace, started_ms: int) -> None:
        self.output = str(args.output)
        self.started_ms = started_ms
        self.last_phase = "start"
        self.last_successful_phase: str | None = None
        self.current_command: dict[str, Any] | None = None
        self.recent_commands: list[dict[str, Any]] = []
        self.phase_history: list[dict[str, Any]] = []
        self.root_causes: list[dict[str, str]] = []
        self.snapshot: dict[str, Any] = {
            "initialpose_publish_attempted": bool(getattr(args, "initialpose_opt_in", False)),
            "initialpose_published": False,
            "initialpose_publish_method": None,
            "initialpose_subscriber_count": None,
            "initialpose_publish_attempts": 0,
            "initialpose_publish_elapsed_ms": None,
            "initialpose_publish_error": None,
            "amcl_pose_observed": False,
            "base_link_to_laser_frame_transform": None,
            "localization_tf_observed": {"map_to_odom": False, "map_to_base_link": False},
            "tf_chain_observed": default_tf_chain_observed(),
            "tf_chain_diagnostics": {},
            "tf_topics_observed": {"/tf": False, "/tf_static": False},
            "tf_static_observed": False,
            "tf_frame_inventory": {"frames": [], "edges": [], "dynamic_edges": [], "static_edges": [], "transforms": []},
            "localization_signal_freshness": {
                topic: {
                    "topic": topic,
                    "expected_type": topic_type,
                    "topic_type": None,
                    "topic_present": False,
                    "source_class": "static" if topic == "/tf_static" else "dynamic" if topic == "/tf" else "message",
                    "probe": {"executed": False, "observed": False, "boundary": "not_evaluated"},
                    "timestamp": {"parsed": False, "reason": "not_evaluated"},
                    "freshness": {"status": "unknown", "reason": "not_evaluated"},
                    "publishers": {"count": 0, "nodes": []},
                    "subscribers": {"count": 0, "nodes": []},
                }
                for topic, topic_type in LOCALIZATION_SIGNAL_TOPICS.items()
            },
            "tf_source_freshness": {"edges": {}, "dynamic_edge_count": 0, "static_edge_count": 0},
            "amcl_pose_frame_id": None,
            "amcl_node_publishers": [],
            "amcl_node_subscribers": [],
            "amcl_param_probe_ok": False,
            "amcl_node_info_observed": False,
            "amcl_tf_broadcast_param": None,
            "amcl_frame_params": {},
            "amcl_log_tail": "",
            "managed_static_tf_processes": {},
            "static_tf_source_observed": False,
            "tf_source_root_cause_detail": {},
            "amcl_broadcast_conditions": {},
            "map_frame_observed": False,
            "odom_frame_observed": False,
            "amcl_tf_root_cause": "not_evaluated",
            "tf_failure_classification": {
                "map_to_base_link": "not_evaluated",
                "frame_naming_consistent": True,
            },
            "package_availability": {package: None for package in EXPECTED_PACKAGES},
            "package_check_mode": "deferred_after_localization_main_path",
            "package_checks_batch_ok": False,
            "managed_runtime_requested": bool(getattr(args, "managed_runtime_opt_in", False)),
            "managed_runtime_started": False,
            "managed_runtime_cleanup_ok": False,
            "path_generation_requested": bool(getattr(args, "path_generation_opt_in", False)),
            "path_generation_attempted": False,
            "path_generated": False,
            "path_generation_succeeded": False,
            "path_point_count": 0,
            "blocked_commands_not_sent": list(BLOCKED_COMMAND_TOKENS),
            "blocked_devices_not_opened": ["/dev/ttyS5"],
        }

    def record_phase(
        self,
        phase: str,
        *,
        ok: bool | None = None,
        detail: dict[str, Any] | None = None,
        root_cause: dict[str, str] | None = None,
    ) -> None:
        """每个耗时阶段前后都落盘一次，latest 可以展示 last_phase 和成功边界。"""
        self.last_phase = phase
        if ok is True:
            self.last_successful_phase = phase
        if root_cause:
            self.root_causes.append(root_cause)
        entry: dict[str, Any] = {"phase": phase, "at_ms": now_ms()}
        if ok is not None:
            entry["ok"] = ok
        if detail:
            entry["detail"] = detail
        if root_cause:
            entry["root_cause"] = root_cause
        self.phase_history.append(entry)
        self.write_partial()

    def before_command(self, command: str, timeout_s: float) -> None:
        """ROS2 CLI 前先写 current_command，外层 SIGINT 时也能知道卡在哪条命令。"""
        self.current_command = {
            "command": command,
            "timeout_s": timeout_s,
            "started_at_ms": now_ms(),
        }
        self.write_partial()

    def after_command(self, result: dict[str, Any]) -> None:
        """命令结束后保存短摘要；stdout/stderr 已在 result 中截断，避免 artifact 过大。"""
        command = {
            "command": result.get("command"),
            "ok": bool(result.get("ok")),
            "returncode": result.get("returncode"),
            "elapsed_ms": result.get("elapsed_ms"),
            "error": result.get("error"),
            "finished_at_ms": now_ms(),
        }
        self.recent_commands.append(command)
        self.recent_commands = self.recent_commands[-12:]
        self.current_command = None
        self.write_partial()

    def update_snapshot(self, **values: Any) -> None:
        """阶段结果统一进 snapshot，确保 partial 和 final 字段形状一致。"""
        self.snapshot.update(values)
        self.write_partial()

    def write_partial(self, *, status: str = "partial_runtime_in_progress") -> None:
        """写入可被 upper 合并的 partial artifact；写失败不打断主 proof 流程。"""
        proof = {
            "status": status,
            "evidence_ref": f"o10-amcl-nav2-runtime-partial-{self.started_ms}",
            "evidence_type": "partial_runtime_material",
            "started_at_ms": self.started_ms,
            "generated_at_ms": now_ms(),
            "elapsed_ms": now_ms() - self.started_ms,
            "last_phase": self.last_phase,
            "last_successful_phase": self.last_successful_phase,
            "phase_history": self.phase_history[-60:],
            "current_command": self.current_command,
            "recent_commands": self.recent_commands[-12:],
            "root_causes": list(self.root_causes),
            "blockers": list(self.root_causes),
            **self.snapshot,
            **safety_flags(),
        }
        attach_artifact_summaries(proof, status=status)
        payload = {
            "schema": SCHEMA,
            "generated_at_ms": now_ms(),
            "status": status,
            "evidence_type": "partial_runtime_material",
            "proof": proof,
            "software_guard": True,
            "not_proven": True,
            **path_generation_envelope_fields(proof),
            **safety_flags(),
        }
        try:
            write_json_atomic(self.output, payload)
        except OSError:
            # partial artifact 是证据增强，不应因为磁盘瞬态失败掩盖原始 ROS2 blocker。
            pass


def install_phase_signal_handlers(writer: PhaseArtifactWriter) -> None:
    """外层 timeout 会发 SIGINT/SIGTERM；helper 必须先写中断状态再退出。"""

    def handle_signal(signum: int, _frame: Any) -> None:
        signal_name = signal.Signals(signum).name
        contextual_root_cause = None
        command_text = ""
        if isinstance(writer.current_command, dict):
            command_text = str(writer.current_command.get("command") or "")
        if "tf2_echo map base_link" in command_text:
            contextual_root_cause = {"layer": "Localization TF", "reason": "map_to_base_link_tf_probe_interrupted_before_transform_observed"}
        elif "tf2_echo odom base_link" in command_text:
            contextual_root_cause = {"layer": "Localization TF", "reason": "odom_to_base_link_tf_probe_interrupted_before_transform_observed"}
        elif "tf2_echo base_link laser_frame" in command_text:
            contextual_root_cause = {"layer": "Localization TF", "reason": "base_link_to_laser_frame_tf_probe_interrupted_before_transform_observed"}
        elif "tf2_echo map odom" in command_text:
            contextual_root_cause = {"layer": "Localization TF", "reason": "map_to_odom_tf_probe_interrupted_before_transform_observed"}
        elif "/amcl_pose" in command_text:
            contextual_root_cause = {"layer": "AMCL localization", "reason": "amcl_pose_probe_interrupted_before_observation"}
        if contextual_root_cause:
            writer.record_phase("interrupted_context", ok=False, root_cause=contextual_root_cause)
        writer.record_phase(
            "interrupted",
            ok=False,
            root_cause={"layer": "helper process", "reason": f"{signal_name.lower()}_before_final_artifact"},
        )
        writer.write_partial(status="interrupted_before_final_artifact")
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)


def compact_error(error: BaseException) -> dict[str, str]:
    """artifact 只保留短错误，避免现场日志把 readback 页面刷爆。"""
    return {"type": type(error).__name__, "message": str(error)[:240]}


def dds_no_shm_export_lines() -> list[str]:
    """所有 ROS 子进程统一禁用 FastDDS SHM，避免板端残留端口锁污染 lifecycle RPC。"""
    return [f"export {key}={shlex.quote(value)}" for key, value in DDS_NO_SHM_ENV.items()]


def source_prefix(args: argparse.Namespace) -> str:
    """ROS2 setup 必须走 bash -lc，避免远端 zsh 直接 source bash 脚本失败。"""
    return "; ".join(
        [
            "set -e",
            f"source {shlex.quote(args.ros_setup)}",
            f"[ -f {shlex.quote(args.onboard_setup)} ] && source {shlex.quote(args.onboard_setup)} || true",
            *dds_no_shm_export_lines(),
            f"cd {shlex.quote(args.workdir)}",
        ]
    )


def run_ros(args: argparse.Namespace, command: str, timeout_s: float) -> dict[str, Any]:
    """执行 ROS2 CLI；命令文本固定来自 helper 本身，不接受外部 shell 注入。"""
    return run_bash(
        f"{source_prefix(args)}; {command}",
        timeout_s=timeout_s,
        artifact_command=command,
        phase_writer=getattr(args, "_phase_writer", None),
    )


def run_bash(
    command: str,
    *,
    timeout_s: float,
    artifact_command: str | None = None,
    phase_writer: Any | None = None,
) -> dict[str, Any]:
    """执行内部 bash probe；artifact_command 只写短标签，避免把整段脚本刷进 JSON。"""
    started_ms = now_ms()
    process: subprocess.Popen[str] | None = None
    display_command = artifact_command or command
    if isinstance(phase_writer, PhaseArtifactWriter):
        phase_writer.before_command(display_command, timeout_s)
    try:
        process = subprocess.Popen(  # noqa: S603 - argv 固定为 bash -lc，命令来自本 helper。
            ["bash", "-lc", command],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        stdout, stderr = process.communicate(timeout=timeout_s)
        result = {
            "command": display_command,
            "executed": True,
            "ok": process.returncode == 0,
            "returncode": process.returncode,
            "started_at_ms": started_ms,
            "finished_at_ms": now_ms(),
            "timeout_s": timeout_s,
            "timed_out": False,
            "elapsed_ms": now_ms() - started_ms,
            "stdout": stdout[-8000:],
            "stderr": stderr[-4000:],
        }
        if isinstance(phase_writer, PhaseArtifactWriter):
            phase_writer.after_command(result)
        return result
    except subprocess.TimeoutExpired as exc:
        # ROS2 CLI 超时必须杀整个进程组，否则 echo/pub/tf2_echo 子进程会残留污染下一轮 proof。
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
                stdout, stderr = process.communicate(timeout=2.0)
            except ProcessLookupError:
                pass
            except subprocess.TimeoutExpired as kill_exc:
                stdout = kill_exc.stdout if isinstance(kill_exc.stdout, str) else stdout
                stderr = kill_exc.stderr if isinstance(kill_exc.stderr, str) else stderr
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                try:
                    stdout, stderr = process.communicate(timeout=1.0)
                except subprocess.TimeoutExpired as drain_exc:
                    # 某些板端 CLI 被 SIGKILL 后仍会短暂持有 pipe；这里保留已收集输出并直接返回超时结果。
                    stdout = drain_exc.stdout if isinstance(drain_exc.stdout, str) else stdout
                    stderr = drain_exc.stderr if isinstance(drain_exc.stderr, str) else stderr
        result = {
            "command": display_command,
            "executed": True,
            "ok": False,
            "returncode": None,
            "started_at_ms": started_ms,
            "finished_at_ms": now_ms(),
            "timeout_s": timeout_s,
            "timed_out": True,
            "elapsed_ms": now_ms() - started_ms,
            "error": compact_error(exc),
            "stdout": (stdout or "")[-8000:],
            "stderr": (stderr or "")[-4000:],
        }
        if isinstance(phase_writer, PhaseArtifactWriter):
            phase_writer.after_command(result)
        return result


def parse_json_stdout(result: dict[str, Any]) -> dict[str, Any] | None:
    """只解析 helper 自己打印的 JSON；失败时返回 None，避免诊断解析反过来阻断收口。"""
    stdout = str(result.get("stdout") or "").strip()
    if not stdout:
        return None
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        # 某些 ROS setup 脚本会向 stdout 打提示；真正 JSON 固定在最后一行。
        for line in reversed(stdout.splitlines()):
            try:
                parsed = json.loads(line)
                break
            except json.JSONDecodeError:
                continue
        else:
            return None
    return parsed if isinstance(parsed, dict) else None


def board_source_stage_probe_command(args: argparse.Namespace) -> str:
    """单独量测 ROS/workspace source，避免把 source 卡顿误算成 `command -v ros2` 卡顿。"""
    ros_setup = shlex.quote(args.ros_setup)
    onboard_setup = shlex.quote(args.onboard_setup)
    workdir = shlex.quote(args.workdir)
    template = """
set +e
o10_now_ms() {
  python3 -c 'import time; print(int(time.time() * 1000))'
}
started_ms=$(o10_now_ms)
ros_setup_exists=false
ros_setup_sourced=false
ros_setup_rc=127
ros_setup_started_ms=$(o10_now_ms)
ros_setup_finished_ms=$ros_setup_started_ms
workspace_setup_exists=false
workspace_setup_sourced=false
workspace_setup_skipped=false
workspace_setup_rc=0
workspace_setup_started_ms=$(o10_now_ms)
workspace_setup_finished_ms=$workspace_setup_started_ms
cd_ok=false
if [ -f __ROS_SETUP_SH__ ]; then
  ros_setup_exists=true
  ros_setup_started_ms=$(o10_now_ms)
  source __ROS_SETUP_SH__
  ros_setup_rc=$?
  ros_setup_finished_ms=$(o10_now_ms)
  if [ "$ros_setup_rc" -eq 0 ]; then
    ros_setup_sourced=true
  fi
fi
if [ "$ros_setup_sourced" = "true" ]; then
  if [ -f __ONBOARD_SETUP_SH__ ]; then
    workspace_setup_exists=true
    workspace_setup_started_ms=$(o10_now_ms)
    source __ONBOARD_SETUP_SH__
    workspace_setup_rc=$?
    workspace_setup_finished_ms=$(o10_now_ms)
    if [ "$workspace_setup_rc" -eq 0 ]; then
      workspace_setup_sourced=true
    fi
  else
    workspace_setup_skipped=true
  fi
  cd __WORKDIR_SH__
  if [ "$?" -eq 0 ]; then
    cd_ok=true
  fi
fi
finished_ms=$(o10_now_ms)
export O10_STARTED_MS="$started_ms"
export O10_FINISHED_MS="$finished_ms"
export O10_ROS_SETUP_EXISTS="$ros_setup_exists"
export O10_ROS_SETUP_SOURCED="$ros_setup_sourced"
export O10_ROS_SETUP_RC="$ros_setup_rc"
export O10_ROS_SETUP_ELAPSED_MS="$((ros_setup_finished_ms - ros_setup_started_ms))"
export O10_WORKSPACE_SETUP_EXISTS="$workspace_setup_exists"
export O10_WORKSPACE_SETUP_SOURCED="$workspace_setup_sourced"
export O10_WORKSPACE_SETUP_SKIPPED="$workspace_setup_skipped"
export O10_WORKSPACE_SETUP_RC="$workspace_setup_rc"
export O10_WORKSPACE_SETUP_ELAPSED_MS="$((workspace_setup_finished_ms - workspace_setup_started_ms))"
export O10_CD_OK="$cd_ok"
python3 - <<'PY'
import json
import os

def flag(name):
    return os.environ.get(name) == "true"

def number(name):
    try:
        return int(os.environ.get(name, "0"))
    except ValueError:
        return 0

payload = {
    "started_at_ms": number("O10_STARTED_MS"),
    "finished_at_ms": number("O10_FINISHED_MS"),
    "elapsed_ms": max(0, number("O10_FINISHED_MS") - number("O10_STARTED_MS")),
    "ros_setup": {
        "path": __ROS_SETUP_JSON__,
        "exists": flag("O10_ROS_SETUP_EXISTS"),
        "sourced": flag("O10_ROS_SETUP_SOURCED"),
        "returncode": number("O10_ROS_SETUP_RC"),
        "elapsed_ms": number("O10_ROS_SETUP_ELAPSED_MS"),
    },
    "workspace_setup": {
        "path": __ONBOARD_SETUP_JSON__,
        "exists": flag("O10_WORKSPACE_SETUP_EXISTS"),
        "sourced": flag("O10_WORKSPACE_SETUP_SOURCED"),
        "skipped": flag("O10_WORKSPACE_SETUP_SKIPPED"),
        "returncode": number("O10_WORKSPACE_SETUP_RC"),
        "elapsed_ms": number("O10_WORKSPACE_SETUP_ELAPSED_MS"),
        "failure_tolerated": flag("O10_WORKSPACE_SETUP_EXISTS") and not flag("O10_WORKSPACE_SETUP_SOURCED"),
    },
    "workdir": __WORKDIR_JSON__,
    "cd_ok": flag("O10_CD_OK"),
}
print(json.dumps(payload, ensure_ascii=False))
PY
if [ "$ros_setup_sourced" = "true" ] && [ "$cd_ok" = "true" ]; then
  exit 0
fi
exit 3
""".strip()
    return (
        template.replace("__ROS_SETUP_SH__", ros_setup)
        .replace("__ONBOARD_SETUP_SH__", onboard_setup)
        .replace("__WORKDIR_SH__", workdir)
        .replace("__ROS_SETUP_JSON__", json.dumps(args.ros_setup, ensure_ascii=False))
        .replace("__ONBOARD_SETUP_JSON__", json.dumps(args.onboard_setup, ensure_ascii=False))
        .replace("__WORKDIR_JSON__", json.dumps(args.workdir, ensure_ascii=False))
    )


def board_cli_layer_probe_command() -> str:
    """在已 source 的 shell 内分层跑 PATH/which 与最小 `ros2` invocation。"""
    code = f"""
import json
import os
import subprocess
import time

PATH_TIMEOUT_S = {ROS2_LAYER_COMMAND_TIMEOUT_S!r}
INVOCATION_TIMEOUT_S = {ROS2_LAYER_INVOCATION_TIMEOUT_S!r}

def now_ms():
    return int(time.time() * 1000)

def compact(text, limit):
    return (text or "")[-limit:]

def run_layer(label, command, timeout_s):
    started_ms = now_ms()
    try:
        completed = subprocess.run(
            ["bash", "-lc", command],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_s,
        )
        return {{
            "label": label,
            "command": command,
            "executed": True,
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "started_at_ms": started_ms,
            "finished_at_ms": now_ms(),
            "timeout_s": timeout_s,
            "timed_out": False,
            "elapsed_ms": now_ms() - started_ms,
            "stdout": compact(completed.stdout, 2000),
            "stderr": compact(completed.stderr, 1000),
        }}
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return {{
            "label": label,
            "command": command,
            "executed": True,
            "ok": False,
            "returncode": None,
            "started_at_ms": started_ms,
            "finished_at_ms": now_ms(),
            "timeout_s": timeout_s,
            "timed_out": True,
            "elapsed_ms": now_ms() - started_ms,
            "stdout": compact(stdout, 2000),
            "stderr": compact(stderr, 1000),
            "error": {{"type": "TimeoutExpired", "message": f"{{label}} timed out after {{timeout_s}}s"}},
        }}

path_lookup = {{
    "command_v": run_layer("command_v", "command -v ros2", PATH_TIMEOUT_S),
    "type_a": run_layer("type_a", "type -a ros2", PATH_TIMEOUT_S),
    "which": run_layer("which", "which ros2", PATH_TIMEOUT_S),
}}
ros2_path = ""
for key in ("command_v", "which"):
    candidate = str(path_lookup[key].get("stdout") or "").strip().splitlines()
    if candidate:
        ros2_path = candidate[0].strip()
        break
if ros2_path:
    cli_invocation = run_layer("ros2_help", "ros2 --help >/dev/null", INVOCATION_TIMEOUT_S)
else:
    cli_invocation = {{
        "label": "ros2_help",
        "command": "ros2 --help >/dev/null",
        "executed": False,
        "ok": False,
        "timeout_s": INVOCATION_TIMEOUT_S,
        "timed_out": False,
        "boundary": "ros2_path_missing_skip_cli_invocation",
        "stdout": "",
        "stderr": "",
    }}
payload = {{
    "environment": {{
        "PATH": os.environ.get("PATH", ""),
        "AMENT_PREFIX_PATH": os.environ.get("AMENT_PREFIX_PATH", ""),
        "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
        "LD_LIBRARY_PATH": os.environ.get("LD_LIBRARY_PATH", ""),
    }},
    "path_lookup": path_lookup,
    "ros2_cli_path": ros2_path or None,
    "cli_invocation": cli_invocation,
}}
print(json.dumps(payload, ensure_ascii=False))
""".strip()
    return f"python3 -c {shlex.quote(code)}"


def board_source_python_probe_command() -> str:
    """在 sourced shell 中收集 rclpy import 与 Python 路径摘要。"""
    code = """
import json
import sys

payload = {
    "python_executable": sys.executable,
    "python_version": sys.version.split()[0],
    "sys_path_head": sys.path[:8],
    "rclpy_import_ok": False,
    "rclpy_file": None,
    "error": None,
}

try:
    import rclpy
    payload["rclpy_import_ok"] = True
    payload["rclpy_file"] = getattr(rclpy, "__file__", None)
except Exception as exc:
    payload["error"] = {
        "type": type(exc).__name__,
        "message": str(exc)[:240],
    }

print(json.dumps(payload, ensure_ascii=False))
""".strip()
    return f"python3 -c {shlex.quote(code)}"


def board_source_amortized_cli_preflight_command(args: argparse.Namespace) -> str:
    """一次 source 后完成 PATH、CLI invocation 和 rclpy import 预检。"""
    ros_setup = shlex.quote(args.ros_setup)
    onboard_setup = shlex.quote(args.onboard_setup)
    workdir = shlex.quote(args.workdir)
    template = """
set +e
o10_now_ms() {
  python3 -c 'import time; print(int(time.time() * 1000))'
}
started_ms=$(o10_now_ms)
ros_setup_exists=false
ros_setup_sourced=false
ros_setup_rc=127
ros_setup_started_ms=$(o10_now_ms)
ros_setup_finished_ms=$ros_setup_started_ms
workspace_setup_exists=false
workspace_setup_sourced=false
workspace_setup_skipped=false
workspace_setup_rc=0
workspace_setup_started_ms=$(o10_now_ms)
workspace_setup_finished_ms=$workspace_setup_started_ms
cd_ok=false
if [ -f __ROS_SETUP_SH__ ]; then
  ros_setup_exists=true
  ros_setup_started_ms=$(o10_now_ms)
  source __ROS_SETUP_SH__
  ros_setup_rc=$?
  ros_setup_finished_ms=$(o10_now_ms)
  if [ "$ros_setup_rc" -eq 0 ]; then
    ros_setup_sourced=true
  fi
fi
if [ "$ros_setup_sourced" = "true" ]; then
  if [ -f __ONBOARD_SETUP_SH__ ]; then
    workspace_setup_exists=true
    workspace_setup_started_ms=$(o10_now_ms)
    source __ONBOARD_SETUP_SH__
    workspace_setup_rc=$?
    workspace_setup_finished_ms=$(o10_now_ms)
    if [ "$workspace_setup_rc" -eq 0 ]; then
      workspace_setup_sourced=true
    fi
  else
    workspace_setup_skipped=true
  fi
  cd __WORKDIR_SH__
  if [ "$?" -eq 0 ]; then
    cd_ok=true
  fi
fi
finished_ms=$(o10_now_ms)
export O10_STARTED_MS="$started_ms"
export O10_FINISHED_MS="$finished_ms"
export O10_ROS_SETUP_EXISTS="$ros_setup_exists"
export O10_ROS_SETUP_SOURCED="$ros_setup_sourced"
export O10_ROS_SETUP_RC="$ros_setup_rc"
export O10_ROS_SETUP_ELAPSED_MS="$((ros_setup_finished_ms - ros_setup_started_ms))"
export O10_WORKSPACE_SETUP_EXISTS="$workspace_setup_exists"
export O10_WORKSPACE_SETUP_SOURCED="$workspace_setup_sourced"
export O10_WORKSPACE_SETUP_SKIPPED="$workspace_setup_skipped"
export O10_WORKSPACE_SETUP_RC="$workspace_setup_rc"
export O10_WORKSPACE_SETUP_ELAPSED_MS="$((workspace_setup_finished_ms - workspace_setup_started_ms))"
export O10_CD_OK="$cd_ok"
python3 - <<'PY'
import json
import os
import subprocess
import sys
import time

SCHEMA = __SCHEMA_JSON__
PATH_TIMEOUT_S = __PATH_TIMEOUT_JSON__
LIGHTWEIGHT_TIMEOUT_S = __LIGHTWEIGHT_TIMEOUT_JSON__
LIGHTWEIGHT_NODE_LIST_TIMEOUT_S = __LIGHTWEIGHT_NODE_LIST_TIMEOUT_JSON__
INVOCATION_TIMEOUT_S = __INVOCATION_TIMEOUT_JSON__
RCLPY_TIMEOUT_S = __RCLPY_TIMEOUT_JSON__

RCLPY_IMPORT_CODE = r'''
import json
import sys

payload = {
    "python_executable": sys.executable,
    "python_version": sys.version.split()[0],
    "sys_path_head": sys.path[:8],
    "rclpy_import_ok": False,
    "rclpy_file": None,
    "error": None,
}

try:
    import rclpy
    payload["rclpy_import_ok"] = True
    payload["rclpy_file"] = getattr(rclpy, "__file__", None)
except Exception as exc:
    payload["error"] = {
        "type": type(exc).__name__,
        "message": str(exc)[:240],
    }

print(json.dumps(payload, ensure_ascii=False))
'''.strip()

def now_ms():
    return int(time.time() * 1000)

def compact(text, limit):
    return str(text or "")[-limit:]

def flag(name):
    return os.environ.get(name) == "true"

def number(name):
    try:
        return int(os.environ.get(name, "0"))
    except ValueError:
        return 0

def source_stage_payload():
    stage = {
        "started_at_ms": number("O10_STARTED_MS"),
        "finished_at_ms": number("O10_FINISHED_MS"),
        "elapsed_ms": max(0, number("O10_FINISHED_MS") - number("O10_STARTED_MS")),
        "ros_setup": {
            "path": __ROS_SETUP_JSON__,
            "exists": flag("O10_ROS_SETUP_EXISTS"),
            "sourced": flag("O10_ROS_SETUP_SOURCED"),
            "returncode": number("O10_ROS_SETUP_RC"),
            "elapsed_ms": number("O10_ROS_SETUP_ELAPSED_MS"),
        },
        "workspace_setup": {
            "path": __ONBOARD_SETUP_JSON__,
            "exists": flag("O10_WORKSPACE_SETUP_EXISTS"),
            "sourced": flag("O10_WORKSPACE_SETUP_SOURCED"),
            "skipped": flag("O10_WORKSPACE_SETUP_SKIPPED"),
            "returncode": number("O10_WORKSPACE_SETUP_RC"),
            "elapsed_ms": number("O10_WORKSPACE_SETUP_ELAPSED_MS"),
            "failure_tolerated": flag("O10_WORKSPACE_SETUP_EXISTS") and not flag("O10_WORKSPACE_SETUP_SOURCED"),
        },
        "workdir": __WORKDIR_JSON__,
        "cd_ok": flag("O10_CD_OK"),
    }
    stage["ok"] = bool(stage["ros_setup"]["sourced"] and stage["cd_ok"])
    return stage

def run_layer(label, command, timeout_s):
    # 这里不再 source；子命令继承本 Python 进程从父 shell 得到的同一个 ROS/workspace 环境。
    started_ms = now_ms()
    try:
        completed = subprocess.run(
            ["bash", "-lc", command],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=float(timeout_s),
        )
        return {
            "label": label,
            "command": command,
            "executed": True,
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "started_at_ms": started_ms,
            "finished_at_ms": now_ms(),
            "timeout_s": float(timeout_s),
            "timed_out": False,
            "elapsed_ms": now_ms() - started_ms,
            "stdout": compact(completed.stdout, 2000),
            "stderr": compact(completed.stderr, 1000),
            "source_amortized": True,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return {
            "label": label,
            "command": command,
            "executed": True,
            "ok": False,
            "returncode": None,
            "started_at_ms": started_ms,
            "finished_at_ms": now_ms(),
            "timeout_s": float(timeout_s),
            "timed_out": True,
            "elapsed_ms": now_ms() - started_ms,
            "stdout": compact(stdout, 2000),
            "stderr": compact(stderr, 1000),
            "error": {"type": "TimeoutExpired", "message": f"{label} timed out after {timeout_s}s"},
            "source_amortized": True,
        }

def skipped_layer(label, command, timeout_s, boundary):
    return {
        "label": label,
        "command": command,
        "executed": False,
        "ok": False,
        "returncode": None,
        "timeout_s": float(timeout_s),
        "timed_out": False,
        "boundary": boundary,
        "stdout": "",
        "stderr": "",
        "source_amortized": True,
    }

def parse_json(text):
    try:
        parsed = json.loads(str(text or "").strip())
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None

def summarize_lightweight_readiness(results):
    # 这里的轻量 gate 只回答 CLI 是否可用，不提前声明 graph/lifecycle/TF 已 ready。
    ordered_labels = ("ros2_daemon_status", "ros2_node_list")
    executed = [results[label] for label in ordered_labels if isinstance(results.get(label), dict) and results[label].get("executed")]
    successful = [entry for entry in executed if entry.get("ok")]
    timed_out = [entry for entry in executed if entry.get("timed_out")]
    primary = successful[0] if successful else executed[0] if executed else None
    return {
        "ok": bool(successful),
        "executed": bool(executed),
        "command_count": len(executed),
        "successful_labels": [str(entry.get("label") or "") for entry in successful],
        "timed_out_labels": [str(entry.get("label") or "") for entry in timed_out],
        "primary_label": None if primary is None else primary.get("label"),
        "primary_command": None if primary is None else primary.get("command"),
        "primary_boundary": None if primary is None else (
            "lightweight_cli_ready"
            if primary.get("ok")
            else "lightweight_cli_timeout"
            if primary.get("timed_out")
            else "lightweight_cli_failed"
        ),
        "results": results,
    }

def run_rclpy_import():
    # rclpy 仍单独用 child Python 设 timeout，但它继承同一个 source 后环境，不再重复 source。
    started_ms = now_ms()
    try:
        completed = subprocess.run(
            [sys.executable, "-c", RCLPY_IMPORT_CODE],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=float(RCLPY_TIMEOUT_S),
        )
        result = {
            "label": "rclpy_import",
            "command": "python3 -c <rclpy import probe>",
            "executed": True,
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "started_at_ms": started_ms,
            "finished_at_ms": now_ms(),
            "timeout_s": float(RCLPY_TIMEOUT_S),
            "timed_out": False,
            "elapsed_ms": now_ms() - started_ms,
            "stdout": compact(completed.stdout, 2000),
            "stderr": compact(completed.stderr, 1000),
            "source_amortized": True,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        result = {
            "label": "rclpy_import",
            "command": "python3 -c <rclpy import probe>",
            "executed": True,
            "ok": False,
            "returncode": None,
            "started_at_ms": started_ms,
            "finished_at_ms": now_ms(),
            "timeout_s": float(RCLPY_TIMEOUT_S),
            "timed_out": True,
            "elapsed_ms": now_ms() - started_ms,
            "stdout": compact(stdout, 2000),
            "stderr": compact(stderr, 1000),
            "error": {"type": "TimeoutExpired", "message": f"rclpy import timed out after {RCLPY_TIMEOUT_S}s"},
            "source_amortized": True,
        }
    payload = parse_json(result.get("stdout")) or {
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "sys_path_head": sys.path[:8],
        "rclpy_import_ok": False,
        "rclpy_file": None,
        "error": result.get("error") or {"type": "ProbeParseFailed", "message": compact(result.get("stderr"), 240)},
    }
    return result, payload

source_stage = source_stage_payload()
source_ok = bool(source_stage["ok"])
if source_ok:
    path_lookup = {
        "command_v": run_layer("command_v", "command -v ros2", PATH_TIMEOUT_S),
        "type_a": run_layer("type_a", "type -a ros2", PATH_TIMEOUT_S),
        "which": run_layer("which", "which ros2", PATH_TIMEOUT_S),
    }
else:
    path_lookup = {
        "command_v": skipped_layer("command_v", "command -v ros2", PATH_TIMEOUT_S, "source_stage_failed_skip_cli_path_lookup"),
        "type_a": skipped_layer("type_a", "type -a ros2", PATH_TIMEOUT_S, "source_stage_failed_skip_cli_path_lookup"),
        "which": skipped_layer("which", "which ros2", PATH_TIMEOUT_S, "source_stage_failed_skip_cli_path_lookup"),
    }

ros2_path = ""
for key in ("command_v", "which"):
    candidate = str(path_lookup[key].get("stdout") or "").strip().splitlines()
    if candidate:
        ros2_path = candidate[0].strip()
        break
if source_ok and ros2_path:
    lightweight_results = {
        "ros2_daemon_status": run_layer("ros2_daemon_status", "ros2 daemon status", LIGHTWEIGHT_TIMEOUT_S),
        "ros2_node_list": run_layer("ros2_node_list", "ros2 node list", LIGHTWEIGHT_NODE_LIST_TIMEOUT_S),
    }
    lightweight_readiness = summarize_lightweight_readiness(lightweight_results)
    cli_invocation = run_layer("ros2_help", "ros2 --help >/dev/null", INVOCATION_TIMEOUT_S)
elif source_ok:
    lightweight_results = {
        "ros2_daemon_status": skipped_layer(
            "ros2_daemon_status",
            "ros2 daemon status",
            LIGHTWEIGHT_TIMEOUT_S,
            "ros2_path_missing_skip_lightweight_readiness",
        ),
        "ros2_node_list": skipped_layer(
            "ros2_node_list",
            "ros2 node list",
            LIGHTWEIGHT_NODE_LIST_TIMEOUT_S,
            "ros2_path_missing_skip_lightweight_readiness",
        ),
    }
    lightweight_readiness = summarize_lightweight_readiness(lightweight_results)
    cli_invocation = skipped_layer("ros2_help", "ros2 --help >/dev/null", INVOCATION_TIMEOUT_S, "ros2_path_missing_skip_cli_invocation")
else:
    lightweight_results = {
        "ros2_daemon_status": skipped_layer(
            "ros2_daemon_status",
            "ros2 daemon status",
            LIGHTWEIGHT_TIMEOUT_S,
            "source_stage_failed_skip_lightweight_readiness",
        ),
        "ros2_node_list": skipped_layer(
            "ros2_node_list",
            "ros2 node list",
            LIGHTWEIGHT_NODE_LIST_TIMEOUT_S,
            "source_stage_failed_skip_lightweight_readiness",
        ),
    }
    lightweight_readiness = summarize_lightweight_readiness(lightweight_results)
    cli_invocation = skipped_layer("ros2_help", "ros2 --help >/dev/null", INVOCATION_TIMEOUT_S, "source_stage_failed_skip_cli_invocation")

if source_ok:
    rclpy_command, python_rclpy = run_rclpy_import()
else:
    rclpy_command = skipped_layer(
        "rclpy_import",
        "python3 -c <rclpy import probe>",
        RCLPY_TIMEOUT_S,
        "source_stage_failed_skip_rclpy_import",
    )
    python_rclpy = {
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "sys_path_head": sys.path[:8],
        "rclpy_import_ok": False,
        "rclpy_file": None,
        "error": None,
    }

payload = {
    "kind": "source_amortized_cli_preflight_final",
    "schema": SCHEMA,
    "source_amortized_cli_preflight": True,
    "source_amortized": True,
    "source_and_cli_in_one_shell": True,
    "per_command_source_overhead_eliminated": bool(source_ok),
    "per_command_source_overhead_excluded": bool(source_ok),
    "source_stage": source_stage,
    "path_lookup": path_lookup,
    "ros2_cli_path": ros2_path or None,
    "lightweight_readiness": lightweight_readiness,
    "cli_invocation": cli_invocation,
    "python_rclpy": python_rclpy,
    "python_rclpy_command": rclpy_command,
    "environment": {
        "ROS_DISTRO": os.environ.get("ROS_DISTRO"),
        "ROS_DOMAIN_ID": os.environ.get("ROS_DOMAIN_ID"),
        "RMW_IMPLEMENTATION": os.environ.get("RMW_IMPLEMENTATION"),
        "PATH_entry_count": len([item for item in os.environ.get("PATH", "").split(os.pathsep) if item]),
        "AMENT_PREFIX_PATH_entry_count": len([item for item in os.environ.get("AMENT_PREFIX_PATH", "").split(os.pathsep) if item]),
        "PYTHONPATH_entry_count": len([item for item in os.environ.get("PYTHONPATH", "").split(os.pathsep) if item]),
        "LD_LIBRARY_PATH_entry_count": len([item for item in os.environ.get("LD_LIBRARY_PATH", "").split(os.pathsep) if item]),
    },
    "commands_executed_after_single_source": [
        label
        for label, result in {
            "command_v": path_lookup["command_v"],
            "type_a": path_lookup["type_a"],
            "which": path_lookup["which"],
            "ros2_daemon_status": lightweight_results["ros2_daemon_status"],
            "ros2_node_list": lightweight_results["ros2_node_list"],
            "ros2_help": cli_invocation,
            "rclpy_import": rclpy_command,
        }.items()
        if result.get("executed")
    ],
    "ok": bool(source_ok),
    "boundary": "source_amortized_cli_preflight_completed" if source_ok else "source_amortized_cli_preflight_source_stage_failed",
}
print(json.dumps(payload, ensure_ascii=False))
sys.exit(0 if source_ok else 3)
PY
""".strip()
    return (
        template.replace("__ROS_SETUP_SH__", ros_setup)
        .replace("__ONBOARD_SETUP_SH__", onboard_setup)
        .replace("__WORKDIR_SH__", workdir)
        .replace("__SCHEMA_JSON__", json.dumps(SOURCE_AMORTIZED_CLI_PREFLIGHT_SCHEMA, ensure_ascii=False))
        .replace("__PATH_TIMEOUT_JSON__", json.dumps(ROS2_LAYER_COMMAND_TIMEOUT_S, ensure_ascii=False))
        .replace("__LIGHTWEIGHT_TIMEOUT_JSON__", json.dumps(ROS2_LIGHTWEIGHT_READINESS_TIMEOUT_S, ensure_ascii=False))
        .replace("__LIGHTWEIGHT_NODE_LIST_TIMEOUT_JSON__", json.dumps(ROS2_LIGHTWEIGHT_NODE_LIST_TIMEOUT_S, ensure_ascii=False))
        .replace("__INVOCATION_TIMEOUT_JSON__", json.dumps(ROS2_LAYER_INVOCATION_TIMEOUT_S, ensure_ascii=False))
        .replace("__RCLPY_TIMEOUT_JSON__", json.dumps(RCLPY_PREFLIGHT_TIMEOUT_S, ensure_ascii=False))
        .replace("__ROS_SETUP_JSON__", json.dumps(args.ros_setup, ensure_ascii=False))
        .replace("__ONBOARD_SETUP_JSON__", json.dumps(args.onboard_setup, ensure_ascii=False))
        .replace("__WORKDIR_JSON__", json.dumps(args.workdir, ensure_ascii=False))
    )


def board_source_preflight(args: argparse.Namespace) -> dict[str, Any]:
    """拆分 sourced shell 中 ros2 CLI 与 Python rclpy runtime，可直接写回 artifact。"""
    phase_writer = getattr(args, "_phase_writer", None)
    preflight_check = run_bash(
        board_source_amortized_cli_preflight_command(args),
        timeout_s=SOURCE_AMORTIZED_CLI_PREFLIGHT_TIMEOUT_S,
        artifact_command="source_amortized_cli_preflight",
        phase_writer=phase_writer,
    )
    preflight_payload = parse_json_stdout(preflight_check) or {}
    source_stage = preflight_payload.get("source_stage") if isinstance(preflight_payload.get("source_stage"), dict) else {}
    source_ok = bool(
        preflight_payload
        and not preflight_check.get("timed_out")
        and (source_stage.get("ros_setup") or {}).get("sourced")
        and source_stage.get("cd_ok")
    )

    cli_layer_check = {
        "command": "source_amortized_cli_preflight",
        "executed": bool(preflight_check.get("executed")),
        "ok": bool(preflight_payload and source_ok),
        "returncode": preflight_check.get("returncode"),
        "timed_out": bool(preflight_check.get("timed_out")),
        "timeout_s": preflight_check.get("timeout_s"),
        "elapsed_ms": preflight_check.get("elapsed_ms"),
        "boundary": preflight_payload.get("boundary") or "source_amortized_cli_preflight_missing_payload",
        "schema": preflight_payload.get("schema"),
        "source_amortized": True,
    }
    cli_layer_payload = preflight_payload if isinstance(preflight_payload, dict) else {}
    path_lookup = cli_layer_payload.get("path_lookup") if isinstance(cli_layer_payload.get("path_lookup"), dict) else {}
    ros2_check = path_lookup.get("command_v") if isinstance(path_lookup.get("command_v"), dict) else cli_layer_check
    which_check = path_lookup.get("which") if isinstance(path_lookup.get("which"), dict) else {}
    type_check = path_lookup.get("type_a") if isinstance(path_lookup.get("type_a"), dict) else {}
    cli_invocation = (
        cli_layer_payload.get("cli_invocation")
        if isinstance(cli_layer_payload.get("cli_invocation"), dict)
        else {"executed": False, "ok": False, "boundary": "cli_layer_probe_missing_invocation"}
    )
    lightweight_readiness = (
        cli_layer_payload.get("lightweight_readiness")
        if isinstance(cli_layer_payload.get("lightweight_readiness"), dict)
        else {}
    )
    lightweight_results = (
        lightweight_readiness.get("results")
        if isinstance(lightweight_readiness.get("results"), dict)
        else {}
    )
    lightweight_daemon_status = (
        lightweight_results.get("ros2_daemon_status")
        if isinstance(lightweight_results.get("ros2_daemon_status"), dict)
        else {}
    )
    lightweight_node_list = (
        lightweight_results.get("ros2_node_list")
        if isinstance(lightweight_results.get("ros2_node_list"), dict)
        else {}
    )
    ros2_cli_path = str(cli_layer_payload.get("ros2_cli_path") or "").strip() or None
    if not ros2_cli_path:
        for candidate_result in (ros2_check, which_check):
            candidate_lines = str(candidate_result.get("stdout") or "").strip().splitlines()
            if candidate_lines:
                ros2_cli_path = candidate_lines[0].strip()
                break
    ros2_cli_path_ok = bool(ros2_cli_path)
    lightweight_cli_ready = bool(lightweight_readiness.get("ok"))
    lightweight_cli_executed = bool(lightweight_readiness.get("executed"))
    lightweight_cli_timed_out = any(
        bool(result.get("timed_out"))
        for result in (lightweight_daemon_status, lightweight_node_list)
        if isinstance(result, dict) and result.get("executed")
    )
    ros2_cli_invocation_ok = bool(cli_invocation.get("ok"))
    ros2_cli_ok = bool(ros2_cli_path_ok and lightweight_cli_ready)

    rclpy_check = (
        cli_layer_payload.get("python_rclpy_command")
        if isinstance(cli_layer_payload.get("python_rclpy_command"), dict)
        else {
            "command": "python3 -c <rclpy import probe>",
            "executed": False,
            "ok": False,
            "boundary": "source_amortized_cli_preflight_missing_rclpy_result",
            "timed_out": False,
        }
    )
    rclpy_payload = (
        cli_layer_payload.get("python_rclpy")
        if isinstance(cli_layer_payload.get("python_rclpy"), dict)
        else {}
    )
    rclpy_import_ok = bool(rclpy_check.get("ok")) and bool(rclpy_payload.get("rclpy_import_ok"))
    rclpy_error = rclpy_payload.get("error") if isinstance(rclpy_payload.get("error"), dict) else None
    rclpy_error_message = str((rclpy_error or {}).get("message") or "")

    path_timed_out = any(bool(result.get("timed_out")) for result in (ros2_check, which_check, type_check))
    if preflight_check.get("timed_out") and not source_stage:
        classification = "board_source_preflight_source_timeout"
    elif not source_ok:
        classification = (
            "board_source_preflight_source_timeout"
            if preflight_check.get("timed_out")
            else "board_source_preflight_source_failed"
        )
    elif path_timed_out:
        classification = "board_source_preflight_ros2_cli_which_timeout"
    elif not ros2_cli_path_ok:
        classification = "board_source_preflight_ros2_cli_path_missing"
    elif not lightweight_cli_ready:
        classification = (
            "board_source_preflight_lightweight_cli_timeout"
            if lightweight_cli_timed_out
            else "board_source_preflight_lightweight_cli_failed"
            if lightweight_cli_executed
            else "board_source_preflight_lightweight_cli_not_executed"
        )
    elif rclpy_check.get("timed_out"):
        classification = "board_source_preflight_rclpy_import_timeout"
    elif not rclpy_import_ok:
        classification = (
            "board_source_preflight_rclpy_import_failed_"
            + classify_rclpy_import_failure(
                rclpy_error_message,
                {
                    "PYTHONPATH": "\n".join(str(item) for item in (rclpy_payload.get("sys_path_head") or [])),
                    "python_executable": rclpy_payload.get("python_executable"),
                },
            )
        )
    else:
        classification = "board_source_preflight_ready"

    cli_ready = bool(source_ok and ros2_cli_ok)
    runtime_ready = bool(cli_ready and rclpy_import_ok)

    return {
        "executed": True,
        "source_stage_ok": source_ok,
        "source_stage_timeout_s": SOURCE_PREFLIGHT_TIMEOUT_S,
        "source_stage": source_stage,
        "ros2_cli_ok": ros2_cli_ok,
        "ros2_cli_path_ok": ros2_cli_path_ok,
        "ros2_cli_invocation_ok": ros2_cli_invocation_ok,
        "ros2_cli_path": ros2_cli_path,
        "ros2_cli_timeout_s": ROS2_PREFLIGHT_TIMEOUT_S,
        "path_lookup_timeout_s": ROS2_LAYER_COMMAND_TIMEOUT_S,
        "path_lookup": path_lookup,
        "lightweight_readiness_timeout_s": ROS2_LIGHTWEIGHT_READINESS_TIMEOUT_S,
        "lightweight_cli_ready": lightweight_cli_ready,
        "lightweight_readiness": lightweight_readiness,
        "cli_invocation_timeout_s": ROS2_LAYER_INVOCATION_TIMEOUT_S,
        "cli_invocation": cli_invocation,
        "rclpy_import_ok": rclpy_import_ok,
        "rclpy_import_timeout_s": RCLPY_PREFLIGHT_TIMEOUT_S,
        "source_amortized_cli_preflight": True,
        "source_amortized_cli_preflight_schema": SOURCE_AMORTIZED_CLI_PREFLIGHT_SCHEMA,
        "source_amortized_cli_preflight_timeout_s": SOURCE_AMORTIZED_CLI_PREFLIGHT_TIMEOUT_S,
        "source_and_cli_in_one_shell": bool(preflight_payload.get("source_and_cli_in_one_shell")),
        "per_command_source_overhead_eliminated": bool(preflight_payload.get("per_command_source_overhead_eliminated")),
        "per_command_source_overhead_excluded": bool(preflight_payload.get("per_command_source_overhead_excluded")),
        "commands_executed_after_single_source": (
            preflight_payload.get("commands_executed_after_single_source")
            if isinstance(preflight_payload.get("commands_executed_after_single_source"), list)
            else []
        ),
        "amortized_shell": {
            "schema": preflight_payload.get("schema"),
            "boundary": preflight_payload.get("boundary"),
            "ok": bool(preflight_payload.get("ok")),
            "source_amortized": bool(preflight_payload.get("source_amortized")),
            "source_and_cli_in_one_shell": bool(preflight_payload.get("source_and_cli_in_one_shell")),
            "per_command_source_overhead_eliminated": bool(preflight_payload.get("per_command_source_overhead_eliminated")),
            "environment": preflight_payload.get("environment") if isinstance(preflight_payload.get("environment"), dict) else {},
        },
        "python_executable": rclpy_payload.get("python_executable"),
        "python_version": rclpy_payload.get("python_version"),
        "rclpy_file": rclpy_payload.get("rclpy_file"),
        "sys_path_head": rclpy_payload.get("sys_path_head") if isinstance(rclpy_payload.get("sys_path_head"), list) else [],
        "classification": classification,
        "cli_ready": cli_ready,
        "runtime_ready": runtime_ready,
        "ready": runtime_ready,
        "python_rclpy": rclpy_payload,
        "rclpy_error": rclpy_error,
        "commands": {
            "source_stage": cli_layer_check,
            "source_amortized_cli_preflight": preflight_check,
            "ros2_cli_layer": cli_layer_check,
            "ros2_cli": ros2_check,
            "ros2_type": type_check,
            "ros2_which": which_check,
            "ros2_lightweight_daemon_status": lightweight_daemon_status,
            "ros2_lightweight_node_list": lightweight_node_list,
            "ros2_lightweight_readiness": lightweight_readiness,
            "ros2_cli_invocation": cli_invocation,
            "rclpy_import": rclpy_check,
        },
    }


def compact_text(text: Any, limit: int = 600) -> str:
    """artifact 摘要只留尾部短文本，避免 stderr/stdout 把现场 JSON 撑爆。"""
    return str(text or "")[-limit:]


def graph_probe_command_summary(result: dict[str, Any], *, boundary: str | None = None) -> dict[str, Any]:
    """把每条 graph probe 压成固定短格式，便于 Product 直接读分类证据。"""
    return {
        "command": result.get("command"),
        "timeout_s": result.get("timeout_s"),
        "returncode": result.get("returncode"),
        "ok": bool(result.get("ok")),
        "timed_out": bool(result.get("timed_out")),
        "elapsed_ms": result.get("elapsed_ms"),
        "stdout_summary": compact_text(result.get("stdout"), 800),
        "stderr_summary": compact_text(result.get("stderr"), 800),
        "error": result.get("error") if isinstance(result.get("error"), dict) else None,
        "boundary": boundary or str(result.get("boundary") or "probe_boundary_unclassified"),
    }


def ros2_no_daemon_unsupported(result: dict[str, Any]) -> bool:
    """Humble 的 node list 可能没有 `--no-daemon`；unsupported 是能力边界，不是运行失败。"""
    text = f"{result.get('stdout') or ''}\n{result.get('stderr') or ''}".lower()
    return any(
        marker in text
        for marker in (
            "unrecognized arguments: --no-daemon",
            "no such option: --no-daemon",
            "unknown option --no-daemon",
            "invalid choice: '--no-daemon'",
        )
    )


def graph_command_boundary(label: str, result: dict[str, Any]) -> str:
    """按命令语义给 probe 命名，避免所有非零退出都变成泛化 failed。"""
    stdout_lines = [line.strip() for line in str(result.get("stdout") or "").splitlines() if line.strip()]
    if label == "ros2_node_list_no_daemon" and ros2_no_daemon_unsupported(result):
        return "unsupported_option"
    if result.get("timed_out"):
        return f"{label}_timeout"
    if result.get("ok"):
        if label in {"ros2_node_list", "ros2_node_list_no_daemon", "ros2_node_list_after_daemon_reset"}:
            return f"{label}_observed" if stdout_lines else f"{label}_empty"
        return f"{label}_ok"
    return f"{label}_failed"


def selected_path_matches(entries: list[str], markers: tuple[str, ...]) -> list[str]:
    """只返回 ROS/workspace 相关路径片段，不把完整环境变量复制进 artifact。"""
    matches: list[str] = []
    for entry in entries:
        if any(marker in entry for marker in markers):
            matches.append(entry)
    return matches[:8]


def path_env_summary(value: str, *, workspace_markers: tuple[str, ...]) -> dict[str, Any]:
    """环境变量只做 presence 摘要，防止凭证或无关路径进入证据文件。"""
    entries = [item for item in str(value or "").split(os.pathsep) if item]
    ros_matches = selected_path_matches(entries, ("/opt/ros/", "/opt/ros"))
    workspace_matches = selected_path_matches(entries, workspace_markers)
    return {
        "entry_count": len(entries),
        "contains_ros": bool(ros_matches),
        "contains_onboard_workspace": bool(workspace_matches),
        "ros_matches": ros_matches,
        "workspace_matches": workspace_matches,
    }


def workspace_environment_summary_command(args: argparse.Namespace) -> str:
    """在 sourced shell 内只打印 ROS 相关环境摘要，不输出全量 env。"""
    workspace_markers = (
        str(args.workdir),
        "/root/rober/onboard",
        "/ws",
        "ros2_trashbot",
    )
    code = f"""
import json
import os
import shutil

def split_paths(value):
    return [item for item in str(value or "").split(os.pathsep) if item]

def matches(entries, markers):
    return [entry for entry in entries if any(marker in entry for marker in markers)][:8]

def summarize_path(name, workspace_markers):
    entries = split_paths(os.environ.get(name, ""))
    ros_matches = matches(entries, ("/opt/ros/", "/opt/ros"))
    workspace_matches = matches(entries, workspace_markers)
    return {{
        "entry_count": len(entries),
        "contains_ros": bool(ros_matches),
        "contains_onboard_workspace": bool(workspace_matches),
        "ros_matches": ros_matches,
        "workspace_matches": workspace_matches,
    }}

workspace_markers = tuple({json.dumps(workspace_markers, ensure_ascii=False)})
payload = {{
    "ROS_DISTRO": os.environ.get("ROS_DISTRO"),
    "ROS_DOMAIN_ID": os.environ.get("ROS_DOMAIN_ID"),
    "RMW_IMPLEMENTATION": os.environ.get("RMW_IMPLEMENTATION"),
    "AMENT_PREFIX_PATH": summarize_path("AMENT_PREFIX_PATH", workspace_markers),
    "PYTHONPATH": summarize_path("PYTHONPATH", workspace_markers),
    "LD_LIBRARY_PATH": summarize_path("LD_LIBRARY_PATH", workspace_markers),
    "which_ros2": shutil.which("ros2"),
}}
print(json.dumps(payload, ensure_ascii=False))
""".strip()
    return f"python3 -c {shlex.quote(code)}"


def rclpy_graph_segment_probe_command(probe_timeout_s: float = 1.1) -> str:
    """child Python 内分段量测 import/init/create_node/graph wait，定位是否卡在 rclpy 层。"""
    code = f"""
import json
import time

payload = {{
    "executed": True,
    "ok": False,
    "node_names": [],
    "segments": [],
    "boundary": "rclpy_graph_segments_not_started",
    "error": None,
}}
node = None
rclpy_initialized = False
started = time.monotonic()

def mark(name, start):
    payload["segments"].append({{"name": name, "elapsed_ms": int((time.monotonic() - start) * 1000)}})

try:
    segment_started = time.monotonic()
    import rclpy
    mark("import_rclpy", segment_started)

    segment_started = time.monotonic()
    if not rclpy.ok():
        rclpy.init(args=None)
    rclpy_initialized = True
    mark("rclpy_init", segment_started)

    segment_started = time.monotonic()
    node = rclpy.create_node("o10_graph_timeout_segment_probe")
    mark("create_node", segment_started)

    segment_started = time.monotonic()
    deadline = time.monotonic() + {max(float(probe_timeout_s), 0.2)!r}
    names = []
    while time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.05)
        names = sorted({{name for name in node.get_node_names() if name}})
        if names:
            break
    mark("graph_wait", segment_started)
    payload["node_names"] = names
    payload["ok"] = bool(names)
    payload["boundary"] = "rclpy_graph_nodes_observed" if names else "rclpy_graph_empty_after_segment_wait"
except Exception as exc:
    payload["error"] = {{"type": type(exc).__name__, "message": str(exc)[:240]}}
    payload["boundary"] = "rclpy_graph_segment_probe_failed"
finally:
    payload["elapsed_ms"] = int((time.monotonic() - started) * 1000)
    if node is not None:
        try:
            node.destroy_node()
        except Exception:
            pass
    if rclpy_initialized:
        try:
            if rclpy.ok():
                rclpy.shutdown()
        except Exception:
            pass

print(json.dumps(payload, ensure_ascii=False))
""".strip()
    return f"python3 -c {shlex.quote(code)}"


def source_amortized_graph_probe_batch_command(args: argparse.Namespace) -> str:
    """单次 source 后批量执行 graph probes，避免每条命令重复 source 污染 timeout。"""
    ros_setup = shlex.quote(args.ros_setup)
    onboard_setup = shlex.quote(args.onboard_setup)
    workdir = shlex.quote(args.workdir)
    command_specs = [
        {"label": label, "command": command, "timeout_s": timeout_s}
        for label, (command, timeout_s) in ROS2_GRAPH_SOURCE_AMORTIZED_COMMANDS.items()
    ]
    daemon_retry_specs = [
        {"label": label, "command": command, "timeout_s": timeout_s}
        for label, (command, timeout_s) in ROS2_GRAPH_DAEMON_SAFE_RETRY_COMMANDS.items()
    ]
    workspace_markers = (
        str(args.workdir),
        "/root/rober/onboard",
        "/ws",
        "ros2_trashbot",
    )
    template = """
set +e
o10_now_ms() {
  python3 -c 'import time; print(int(time.time() * 1000))'
}
started_ms=$(o10_now_ms)
ros_setup_exists=false
ros_setup_sourced=false
ros_setup_rc=127
ros_setup_started_ms=$(o10_now_ms)
ros_setup_finished_ms=$ros_setup_started_ms
workspace_setup_exists=false
workspace_setup_sourced=false
workspace_setup_skipped=false
workspace_setup_rc=0
workspace_setup_started_ms=$(o10_now_ms)
workspace_setup_finished_ms=$workspace_setup_started_ms
cd_ok=false
if [ -f __ROS_SETUP_SH__ ]; then
  ros_setup_exists=true
  ros_setup_started_ms=$(o10_now_ms)
  source __ROS_SETUP_SH__
  ros_setup_rc=$?
  ros_setup_finished_ms=$(o10_now_ms)
  if [ "$ros_setup_rc" -eq 0 ]; then
    ros_setup_sourced=true
  fi
fi
if [ "$ros_setup_sourced" = "true" ]; then
  if [ -f __ONBOARD_SETUP_SH__ ]; then
    workspace_setup_exists=true
    workspace_setup_started_ms=$(o10_now_ms)
    source __ONBOARD_SETUP_SH__
    workspace_setup_rc=$?
    workspace_setup_finished_ms=$(o10_now_ms)
    if [ "$workspace_setup_rc" -eq 0 ]; then
      workspace_setup_sourced=true
    fi
  else
    workspace_setup_skipped=true
  fi
  cd __WORKDIR_SH__
  if [ "$?" -eq 0 ]; then
    cd_ok=true
  fi
fi
finished_ms=$(o10_now_ms)
export O10_STARTED_MS="$started_ms"
export O10_FINISHED_MS="$finished_ms"
export O10_ROS_SETUP_EXISTS="$ros_setup_exists"
export O10_ROS_SETUP_SOURCED="$ros_setup_sourced"
export O10_ROS_SETUP_RC="$ros_setup_rc"
export O10_ROS_SETUP_ELAPSED_MS="$((ros_setup_finished_ms - ros_setup_started_ms))"
export O10_WORKSPACE_SETUP_EXISTS="$workspace_setup_exists"
export O10_WORKSPACE_SETUP_SOURCED="$workspace_setup_sourced"
export O10_WORKSPACE_SETUP_SKIPPED="$workspace_setup_skipped"
export O10_WORKSPACE_SETUP_RC="$workspace_setup_rc"
export O10_WORKSPACE_SETUP_ELAPSED_MS="$((workspace_setup_finished_ms - workspace_setup_started_ms))"
export O10_CD_OK="$cd_ok"
python3 - <<'PY'
import json
import os
import shutil
import subprocess
import sys
import time

COMMAND_SPECS = __COMMAND_SPECS_JSON__
DAEMON_RETRY_SPECS = __DAEMON_RETRY_SPECS_JSON__
WORKSPACE_MARKERS = tuple(__WORKSPACE_MARKERS_JSON__)
RCLPY_WAIT_S = __RCLPY_WAIT_S_JSON__

def now_ms():
    return int(time.time() * 1000)

def compact(text, limit):
    return str(text or "")[-limit:]

def flag(name):
    return os.environ.get(name) == "true"

def number(name):
    try:
        return int(os.environ.get(name, "0"))
    except ValueError:
        return 0

def emit(kind, **payload):
    print(json.dumps({"kind": kind, **payload}, ensure_ascii=False), flush=True)

def source_stage_payload():
    stage = {
        "started_at_ms": number("O10_STARTED_MS"),
        "finished_at_ms": number("O10_FINISHED_MS"),
        "elapsed_ms": max(0, number("O10_FINISHED_MS") - number("O10_STARTED_MS")),
        "ros_setup": {
            "path": __ROS_SETUP_JSON__,
            "exists": flag("O10_ROS_SETUP_EXISTS"),
            "sourced": flag("O10_ROS_SETUP_SOURCED"),
            "returncode": number("O10_ROS_SETUP_RC"),
            "elapsed_ms": number("O10_ROS_SETUP_ELAPSED_MS"),
        },
        "workspace_setup": {
            "path": __ONBOARD_SETUP_JSON__,
            "exists": flag("O10_WORKSPACE_SETUP_EXISTS"),
            "sourced": flag("O10_WORKSPACE_SETUP_SOURCED"),
            "skipped": flag("O10_WORKSPACE_SETUP_SKIPPED"),
            "returncode": number("O10_WORKSPACE_SETUP_RC"),
            "elapsed_ms": number("O10_WORKSPACE_SETUP_ELAPSED_MS"),
            "failure_tolerated": flag("O10_WORKSPACE_SETUP_EXISTS") and not flag("O10_WORKSPACE_SETUP_SOURCED"),
        },
        "workdir": __WORKDIR_JSON__,
        "cd_ok": flag("O10_CD_OK"),
    }
    stage["ok"] = bool(stage["ros_setup"]["sourced"] and stage["cd_ok"])
    return stage

def run_command(label, command, timeout_s):
    started_ms = now_ms()
    try:
        completed = subprocess.run(
            ["bash", "-lc", command],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=float(timeout_s),
        )
        result = {
            "command": command,
            "executed": True,
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "started_at_ms": started_ms,
            "finished_at_ms": now_ms(),
            "timeout_s": float(timeout_s),
            "timed_out": False,
            "elapsed_ms": now_ms() - started_ms,
            "stdout": compact(completed.stdout, 4000),
            "stderr": compact(completed.stderr, 2000),
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        result = {
            "command": command,
            "executed": True,
            "ok": False,
            "returncode": None,
            "started_at_ms": started_ms,
            "finished_at_ms": now_ms(),
            "timeout_s": float(timeout_s),
            "timed_out": True,
            "elapsed_ms": now_ms() - started_ms,
            "stdout": compact(stdout, 4000),
            "stderr": compact(stderr, 2000),
            "error": {"type": "TimeoutExpired", "message": f"{label} timed out after {timeout_s}s"},
        }
    emit("command_result", label=label, result=result)
    return result

def command_boundary(label, result):
    stdout_lines = [line.strip() for line in str(result.get("stdout") or "").splitlines() if line.strip()]
    if result.get("timed_out"):
        return f"{label}_timeout"
    if result.get("ok"):
        if label in {"ros2_node_list", "ros2_node_list_no_daemon", "ros2_node_list_after_daemon_reset"}:
            return f"{label}_observed" if stdout_lines else f"{label}_empty"
        return f"{label}_ok"
    return f"{label}_failed"

def bounded_command_summary(result, boundary):
    return {
        "command": result.get("command"),
        "timeout_s": result.get("timeout_s"),
        "returncode": result.get("returncode"),
        "ok": bool(result.get("ok")),
        "timed_out": bool(result.get("timed_out")),
        "elapsed_ms": result.get("elapsed_ms"),
        "stdout_summary": compact(result.get("stdout"), 800),
        "stderr_summary": compact(result.get("stderr"), 800),
        "error": result.get("error") if isinstance(result.get("error"), dict) else None,
        "boundary": boundary,
    }

def daemon_safe_retry_probe(source_stage, commands):
    summary = {
        "schema": "trashbot.o10.daemon_safe_graph_retry.v1",
        "attempted": False,
        "skipped": True,
        "skip_reason": None,
        "motion_boundary": {
            "publishes_cmd_vel": False,
            "calls_base_manual": False,
            "sends_navigate_to_pose": False,
            "uses_base_uart": False,
            "safe_to_control": False,
        },
        "pre_reset_graph_blocked_labels": [],
        "commands": {},
        "reset_completed": False,
        "graph_retry_observed": False,
        "graph_retry_boundaries": {},
    }
    if not source_stage.get("ok"):
        summary["skip_reason"] = "source_stage_not_ok"
        emit("daemon_safe_retry", summary=summary)
        return summary
    # 本轮目标是执行上一轮 next_live_command 等价的 daemon-safe stop/start + 8s readback。
    # 因此不再把 `ros2 node list --help` 当成 reset 前置门槛，只要 graph 层已有 timeout/
    # blocked 事实，就继续做 daemon-safe 复验，把结果留给后续 split 合同判读。
    graph_labels = (
        "ros2_node_list",
        "ros2_topic_list",
        "ros2_daemon_status",
        "ros2_node_list_no_daemon",
        "ros2_node_list_help",
    )
    blocked = [
        label
        for label in graph_labels
        if isinstance(commands.get(label), dict) and commands[label].get("timed_out")
    ]
    summary["pre_reset_graph_blocked_labels"] = blocked
    if not blocked:
        summary["skip_reason"] = "graph_commands_not_blocked"
        emit("daemon_safe_retry", summary=summary)
        return summary
    summary["attempted"] = True
    summary["skipped"] = False
    summary["skip_reason"] = None
    for spec in DAEMON_RETRY_SPECS:
        label = spec["label"]
        result = run_command(label, spec["command"], spec["timeout_s"])
        boundary = command_boundary(label, result)
        summary["commands"][label] = bounded_command_summary(result, boundary)
    stop_ok = bool(summary["commands"].get("ros2_daemon_stop", {}).get("ok"))
    start_ok = bool(summary["commands"].get("ros2_daemon_start", {}).get("ok"))
    status_after_ok = bool(summary["commands"].get("ros2_daemon_status_after_reset", {}).get("ok"))
    summary["reset_completed"] = bool(stop_ok and start_ok and status_after_ok)
    retry_labels = ("ros2_node_list_after_daemon_reset", "ros2_topic_list_after_daemon_reset")
    summary["graph_retry_boundaries"] = {
        label: summary["commands"].get(label, {}).get("boundary")
        for label in retry_labels
    }
    summary["graph_retry_observed"] = any(
        str(summary["graph_retry_boundaries"].get(label) or "").endswith(("_observed", "_ok"))
        for label in retry_labels
    )
    emit("daemon_safe_retry", summary=summary)
    return summary

def split_paths(value):
    return [item for item in str(value or "").split(os.pathsep) if item]

def matches(entries, markers):
    return [entry for entry in entries if any(marker in entry for marker in markers)][:8]

def summarize_path(name):
    entries = split_paths(os.environ.get(name, ""))
    ros_matches = matches(entries, ("/opt/ros/", "/opt/ros"))
    workspace_matches = matches(entries, WORKSPACE_MARKERS)
    return {
        "entry_count": len(entries),
        "contains_ros": bool(ros_matches),
        "contains_onboard_workspace": bool(workspace_matches),
        "ros_matches": ros_matches,
        "workspace_matches": workspace_matches,
    }

def workspace_environment_summary():
    return {
        "ROS_DISTRO": os.environ.get("ROS_DISTRO"),
        "ROS_DOMAIN_ID": os.environ.get("ROS_DOMAIN_ID"),
        "RMW_IMPLEMENTATION": os.environ.get("RMW_IMPLEMENTATION"),
        "AMENT_PREFIX_PATH": summarize_path("AMENT_PREFIX_PATH"),
        "PYTHONPATH": summarize_path("PYTHONPATH"),
        "LD_LIBRARY_PATH": summarize_path("LD_LIBRARY_PATH"),
        "which_ros2": shutil.which("ros2"),
    }

def rclpy_stage_stream_probe():
    events = []
    segments = []
    node = None
    rclpy_initialized = False
    started = time.monotonic()

    def stage_event(stage, event, **extra):
        payload = {"stage": stage, "event": event, "at_ms": now_ms(), **extra}
        events.append(payload)
        emit("rclpy_stage", **payload)

    def run_stage(stage, callback):
        stage_started = time.monotonic()
        stage_event(stage, "started")
        value = callback()
        elapsed_ms = int((time.monotonic() - stage_started) * 1000)
        segments.append({"name": stage, "elapsed_ms": elapsed_ms})
        stage_event(stage, "completed", elapsed_ms=elapsed_ms)
        return value

    payload = {
        "executed": True,
        "ok": False,
        "node_names": [],
        "segments": segments,
        "events": events,
        "boundary": "rclpy_graph_stage_stream_not_started",
        "error": None,
        "timeout_s": float(RCLPY_WAIT_S),
    }
    try:
        rclpy = run_stage("import_rclpy", lambda: __import__("rclpy"))

        def init_rclpy():
            if not rclpy.ok():
                rclpy.init(args=None)

        run_stage("rclpy_init", init_rclpy)
        rclpy_initialized = True
        node = run_stage("create_node", lambda: rclpy.create_node("o10_source_amortized_graph_probe"))

        def wait_graph():
            deadline = time.monotonic() + max(float(RCLPY_WAIT_S), 0.2)
            names = []
            while time.monotonic() < deadline:
                rclpy.spin_once(node, timeout_sec=0.05)
                names = sorted({name for name in node.get_node_names() if name})
                if names:
                    break
            return names

        names = run_stage("graph_wait", wait_graph)
        payload["node_names"] = names
        payload["ok"] = bool(names)
        payload["boundary"] = "rclpy_graph_nodes_observed" if names else "rclpy_graph_empty_after_stage_wait"
    except Exception as exc:
        stage_event("exception", "raised", error_type=type(exc).__name__, message=str(exc)[:240])
        payload["error"] = {"type": type(exc).__name__, "message": str(exc)[:240]}
        payload["boundary"] = "rclpy_graph_stage_stream_failed"
    finally:
        if node is not None:
            try:
                run_stage("destroy_node", lambda: node.destroy_node())
            except Exception:
                pass
        if rclpy_initialized:
            try:
                import rclpy
                if rclpy.ok():
                    run_stage("rclpy_shutdown", lambda: rclpy.shutdown())
            except Exception:
                pass
        payload["elapsed_ms"] = int((time.monotonic() - started) * 1000)
    emit("rclpy_stage_summary", summary=payload)
    return payload

source_stage = source_stage_payload()
emit("source_stage", source_stage=source_stage)
commands = {}
workspace_environment = {}
daemon_safe_retry = {
    "schema": "trashbot.o10.daemon_safe_graph_retry.v1",
    "attempted": False,
    "skipped": True,
    "skip_reason": "source_stage_not_evaluated",
}
rclpy_summary = {
    "executed": False,
    "ok": False,
    "timed_out": False,
    "boundary": "rclpy_graph_stage_stream_skipped_source_stage_failed",
    "events": [],
    "segments": [],
    "node_names": [],
}
if source_stage["ok"]:
    for spec in COMMAND_SPECS:
        commands[spec["label"]] = run_command(spec["label"], spec["command"], spec["timeout_s"])
    workspace_environment = {"summary": workspace_environment_summary(), "observed": True}
    emit("workspace_environment", **workspace_environment)
    daemon_safe_retry = daemon_safe_retry_probe(source_stage, commands)
    rclpy_summary = rclpy_stage_stream_probe()
else:
    workspace_environment = {"summary": {}, "observed": False, "boundary": "workspace_environment_skipped_source_stage_failed"}
    emit("workspace_environment", **workspace_environment)
    daemon_safe_retry = daemon_safe_retry_probe(source_stage, commands)

payload = {
    "kind": "source_amortized_batch_final",
    "schema": "trashbot.o10.source_amortized_ros2_graph_probe.v1",
    "source_stage": source_stage,
    "commands": commands,
    "workspace_environment": workspace_environment,
    "daemon_safe_retry": daemon_safe_retry,
    "rclpy_graph_stage_stream": rclpy_summary,
    "source_amortized": True,
    "per_command_source_overhead_excluded": bool(source_stage["ok"]),
    "ok": bool(source_stage["ok"]),
    "boundary": "source_amortized_batch_completed" if source_stage["ok"] else "source_amortized_source_stage_failed",
}
print(json.dumps(payload, ensure_ascii=False), flush=True)
sys.exit(0 if source_stage["ok"] else 3)
PY
""".strip()
    return (
        template.replace("__ROS_SETUP_SH__", ros_setup)
        .replace("__ONBOARD_SETUP_SH__", onboard_setup)
        .replace("__WORKDIR_SH__", workdir)
        .replace("__COMMAND_SPECS_JSON__", json.dumps(command_specs, ensure_ascii=False))
        .replace("__DAEMON_RETRY_SPECS_JSON__", json.dumps(daemon_retry_specs, ensure_ascii=False))
        .replace("__WORKSPACE_MARKERS_JSON__", json.dumps(workspace_markers, ensure_ascii=False))
        .replace("__RCLPY_WAIT_S_JSON__", json.dumps(ROS2_GRAPH_SOURCE_AMORTIZED_RCLPY_WAIT_S, ensure_ascii=False))
        .replace("__ROS_SETUP_JSON__", json.dumps(args.ros_setup, ensure_ascii=False))
        .replace("__ONBOARD_SETUP_JSON__", json.dumps(args.onboard_setup, ensure_ascii=False))
        .replace("__WORKDIR_JSON__", json.dumps(args.workdir, ensure_ascii=False))
    )


def parse_jsonl_objects(text: str) -> list[dict[str, Any]]:
    """stage-stream 以 JSONL 输出；解析失败的 ROS 提示行直接跳过。"""
    objects: list[dict[str, Any]] = []
    for line in str(text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            objects.append(parsed)
    return objects


def rclpy_stage_stream_summary_from_events(
    events: list[dict[str, Any]],
    *,
    timed_out: bool,
    timeout_s: float | None,
) -> dict[str, Any]:
    """外层 batch timeout 时，用已 flush 的 stage JSONL 还原卡住的 rclpy 阶段。"""
    rclpy_events = [event for event in events if event.get("kind") == "rclpy_stage"]
    started = [str(event.get("stage")) for event in rclpy_events if event.get("event") == "started"]
    completed = [str(event.get("stage")) for event in rclpy_events if event.get("event") == "completed"]
    last_started = started[-1] if started else None
    last_completed = completed[-1] if completed else None
    return {
        "executed": bool(rclpy_events),
        "ok": False,
        "timed_out": bool(timed_out),
        "timeout_s": timeout_s,
        "boundary": "rclpy_graph_stage_stream_timeout" if timed_out else "rclpy_graph_stage_stream_incomplete",
        "events": rclpy_events[-20:],
        "segments": [
            {"name": event.get("stage"), "elapsed_ms": event.get("elapsed_ms")}
            for event in rclpy_events
            if event.get("event") == "completed"
        ],
        "node_names": [],
        "last_started_stage": last_started,
        "last_completed_stage": last_completed,
    }


def parse_source_amortized_batch_result(result: dict[str, Any]) -> dict[str, Any]:
    """把 source-amortized batch 的 final JSON 或 timeout 前 JSONL 转成稳定 artifact。"""
    stdout_text = str(result.get("stdout") or "")
    events = parse_jsonl_objects(stdout_text)
    # 真板上偶发只回一整块 final JSON，而不是逐行 JSONL。这里先兜底整块解析，避免把
    # 已执行的 daemon-safe readback 误判成 `daemon_safe_retry_summary_missing_from_batch`。
    if not events:
        stripped = stdout_text.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, dict):
                events = [parsed]
    final_payload: dict[str, Any] | None = None
    for event in events:
        if event.get("kind") == "source_amortized_batch_final":
            final_payload = event
    if final_payload is None:
        source_stage = {}
        commands: dict[str, Any] = {}
        workspace_environment: dict[str, Any] = {"summary": {}, "observed": False}
        daemon_safe_retry: dict[str, Any] = {
            "schema": "trashbot.o10.daemon_safe_graph_retry.v1",
            "attempted": False,
            "skipped": True,
            "skip_reason": "daemon_safe_retry_summary_missing_from_batch",
        }
        for event in events:
            if event.get("kind") == "source_stage" and isinstance(event.get("source_stage"), dict):
                source_stage = event["source_stage"]
            elif event.get("kind") == "command_result" and isinstance(event.get("result"), dict):
                commands[str(event.get("label") or "")] = event["result"]
            elif event.get("kind") == "workspace_environment":
                workspace_environment = {
                    "summary": event.get("summary") if isinstance(event.get("summary"), dict) else {},
                    "observed": bool(event.get("observed")),
                    "boundary": event.get("boundary"),
                }
            elif event.get("kind") == "daemon_safe_retry" and isinstance(event.get("summary"), dict):
                daemon_safe_retry = event["summary"]
            elif event.get("kind") == "rclpy_stage_summary" and isinstance(event.get("summary"), dict):
                final_payload = {
                    "kind": "source_amortized_batch_final",
                    "schema": "trashbot.o10.source_amortized_ros2_graph_probe.v1",
                    "source_stage": source_stage,
                    "commands": commands,
                    "workspace_environment": workspace_environment,
                    "daemon_safe_retry": daemon_safe_retry,
                    "rclpy_graph_stage_stream": event["summary"],
                    "source_amortized": True,
                    "per_command_source_overhead_excluded": bool(source_stage.get("ok")),
                    "ok": bool(source_stage.get("ok")),
                    "boundary": "source_amortized_batch_completed_from_stage_summary",
                }
        if final_payload is None:
            final_payload = {
                "kind": "source_amortized_batch_final",
                "schema": "trashbot.o10.source_amortized_ros2_graph_probe.v1",
                "source_stage": source_stage,
                "commands": commands,
                "workspace_environment": workspace_environment,
                "daemon_safe_retry": daemon_safe_retry,
                "rclpy_graph_stage_stream": rclpy_stage_stream_summary_from_events(
                    events,
                    timed_out=bool(result.get("timed_out")),
                    timeout_s=result.get("timeout_s"),
                ),
                "source_amortized": True,
                "per_command_source_overhead_excluded": bool(source_stage.get("ok")),
                "ok": False,
                "boundary": "source_amortized_batch_timeout" if result.get("timed_out") else "source_amortized_batch_parse_failed",
            }
    final_payload["batch_command"] = graph_probe_command_summary(
        result,
        boundary=str(final_payload.get("boundary") or "source_amortized_batch_unclassified"),
    )
    # final payload 本身也来自 JSONL；不能把它再塞回 events_observed，否则会形成循环引用。
    final_payload["events_observed"] = [
        event for event in events if event is not final_payload and event.get("kind") != "source_amortized_batch_final"
    ][-30:]
    return final_payload


def collect_source_amortized_graph_probe_batch(args: argparse.Namespace) -> dict[str, Any]:
    """运行 source-amortized batch；外层 timeout 足够覆盖一次 source 和所有子命令预算。"""
    result = run_bash(
        source_amortized_graph_probe_batch_command(args),
        timeout_s=ROS2_GRAPH_SOURCE_AMORTIZED_BATCH_TIMEOUT_S,
        artifact_command="source_amortized_ros2_graph_probe_batch",
        phase_writer=getattr(args, "_phase_writer", None),
    )
    return parse_source_amortized_batch_result(result)


def source_amortized_batch_to_legacy_probes(batch: dict[str, Any]) -> dict[str, Any]:
    """用 batch 结果回填旧 probe 字段，旧 consumer 不需要理解新 schema 也能读。"""
    probes: dict[str, Any] = {}
    commands = batch.get("commands") if isinstance(batch.get("commands"), dict) else {}
    for label in ROS2_GRAPH_SOURCE_AMORTIZED_COMMANDS:
        command_result = commands.get(label) if isinstance(commands.get(label), dict) else {}
        if command_result:
            probes[label] = {
                **graph_probe_command_summary(
                    command_result,
                    boundary=graph_command_boundary(label, command_result),
                ),
                "source": "source_amortized_batch",
                "source_amortized": True,
            }
        else:
            probes[label] = {
                "executed": False,
                "ok": False,
                "timed_out": False,
                "boundary": "source_amortized_batch_missing_command_result",
                "source": "source_amortized_batch",
                "source_amortized": True,
            }

    workspace = batch.get("workspace_environment") if isinstance(batch.get("workspace_environment"), dict) else {}
    workspace_summary = workspace.get("summary") if isinstance(workspace.get("summary"), dict) else {}
    probes["workspace_environment"] = {
        "command": "workspace_environment_summary_in_source_amortized_batch",
        "ok": bool(workspace_summary),
        "timed_out": False,
        "timeout_s": None,
        "returncode": 0 if workspace_summary else None,
        "elapsed_ms": None,
        "stdout_summary": "",
        "stderr_summary": "",
        "error": None,
        "boundary": "workspace_environment_observed" if workspace_summary else str(workspace.get("boundary") or "workspace_environment_missing_from_source_amortized_batch"),
        "summary": workspace_summary,
        "source": "source_amortized_batch",
        "source_amortized": True,
    }

    rclpy_stream = batch.get("rclpy_graph_stage_stream") if isinstance(batch.get("rclpy_graph_stage_stream"), dict) else {}
    rclpy_boundary = str(rclpy_stream.get("boundary") or "rclpy_graph_stage_stream_missing")
    probes["rclpy_graph_segments"] = {
        "command": "rclpy_graph_stage_stream_in_source_amortized_batch",
        "ok": bool(rclpy_stream.get("ok")),
        "timed_out": bool(rclpy_stream.get("timed_out")),
        "timeout_s": rclpy_stream.get("timeout_s"),
        "returncode": 0 if rclpy_stream.get("ok") else None,
        "elapsed_ms": rclpy_stream.get("elapsed_ms"),
        "stdout_summary": "",
        "stderr_summary": "",
        "error": rclpy_stream.get("error") if isinstance(rclpy_stream.get("error"), dict) else None,
        "boundary": rclpy_boundary,
        "payload": rclpy_stream,
        "source": "source_amortized_batch",
        "source_amortized": True,
    }
    daemon_safe_retry = batch.get("daemon_safe_retry") if isinstance(batch.get("daemon_safe_retry"), dict) else {}
    probes["daemon_safe_retry"] = {
        "command": "daemon_safe_retry_in_source_amortized_batch",
        "ok": bool(daemon_safe_retry.get("graph_retry_observed") or daemon_safe_retry.get("reset_completed")),
        "timed_out": False,
        "timeout_s": None,
        "returncode": 0 if daemon_safe_retry else None,
        "elapsed_ms": None,
        "stdout_summary": "",
        "stderr_summary": "",
        "error": None,
        "boundary": (
            "daemon_safe_retry_skipped"
            if daemon_safe_retry.get("skipped")
            else "daemon_safe_retry_graph_observed"
            if daemon_safe_retry.get("graph_retry_observed")
            else "daemon_safe_retry_completed_graph_still_blocked"
            if daemon_safe_retry.get("reset_completed")
            else "daemon_safe_retry_attempted_but_reset_not_confirmed"
        ),
        "summary": daemon_safe_retry,
        "source": "source_amortized_batch",
        "source_amortized": True,
    }
    probes["source_amortized_batch"] = batch
    return probes


def collect_ros2_graph_timeout_probes(
    args: argparse.Namespace,
    *,
    board_source_preflight: dict[str, Any],
) -> dict[str, Any]:
    """执行低预算、只读 graph probes；所有命令都在 sourced shell 内运行。"""
    if not board_source_preflight.get("cli_ready"):
        skipped = {
            "executed": False,
            "boundary": "skipped_without_sourced_ros2_cli_ready",
            "reason": board_source_preflight.get("classification"),
        }
        return {
            "ros2_node_list": skipped,
            "ros2_node_list_no_daemon": skipped,
            "ros2_daemon_status": skipped,
            "ros2_node_list_help": skipped,
            "ros2_topic_list": skipped,
            "rclpy_graph_segments": skipped,
            "workspace_environment": skipped,
            "source_amortized_batch": {
                "executed": False,
                "boundary": "skipped_without_sourced_ros2_cli_ready",
                "reason": board_source_preflight.get("classification"),
            },
        }
    batch = collect_source_amortized_graph_probe_batch(args)
    return source_amortized_batch_to_legacy_probes(batch)


def graph_probe_has_boundary(probes: dict[str, Any], probe_name: str, boundaries: set[str]) -> bool:
    """分类器只看稳定 boundary，不解析 CLI 原文。"""
    probe = probes.get(probe_name) if isinstance(probes.get(probe_name), dict) else {}
    return str(probe.get("boundary") or "") in boundaries


def graph_probe_boundary(probes: dict[str, Any], probe_name: str) -> str:
    """统一读取 probe boundary，避免分类 reason 回退到泛化 preflight 状态。"""
    probe = probes.get(probe_name) if isinstance(probes.get(probe_name), dict) else {}
    return str(probe.get("boundary") or "")


def workspace_environment_ready(probes: dict[str, Any], board_source_preflight: dict[str, Any]) -> bool:
    """source/env ready 要同时看到 ROS distro、ros2 path 和 workspace/ROS 路径摘要。"""
    env_probe = probes.get("workspace_environment") if isinstance(probes.get("workspace_environment"), dict) else {}
    summary = env_probe.get("summary") if isinstance(env_probe.get("summary"), dict) else {}
    ament = summary.get("AMENT_PREFIX_PATH") if isinstance(summary.get("AMENT_PREFIX_PATH"), dict) else {}
    pythonpath = summary.get("PYTHONPATH") if isinstance(summary.get("PYTHONPATH"), dict) else {}
    ld_path = summary.get("LD_LIBRARY_PATH") if isinstance(summary.get("LD_LIBRARY_PATH"), dict) else {}
    return bool(
        board_source_preflight.get("cli_ready")
        and summary.get("ROS_DISTRO")
        and summary.get("which_ros2")
        and ament.get("contains_ros")
        and ament.get("contains_onboard_workspace")
        and pythonpath.get("contains_ros")
        and ld_path.get("contains_ros")
    )


def source_amortized_batch_active(probes: dict[str, Any]) -> bool:
    """分类器优先使用 batch 证据；legacy 字段只是由 batch 回填给旧 reader。"""
    batch = probes.get("source_amortized_batch") if isinstance(probes.get("source_amortized_batch"), dict) else {}
    return bool(batch.get("source_amortized") and batch.get("source_stage"))


def rclpy_stage_stream_payload(probes: dict[str, Any]) -> dict[str, Any]:
    """读取 batch stage-stream payload；缺失时回退到旧 rclpy graph segment payload。"""
    rclpy_probe = probes.get("rclpy_graph_segments") if isinstance(probes.get("rclpy_graph_segments"), dict) else {}
    payload = rclpy_probe.get("payload") if isinstance(rclpy_probe.get("payload"), dict) else {}
    return payload


def rclpy_source_amortized_startup_blocked(probes: dict[str, Any]) -> bool:
    """只有 rclpy 卡在 import/init/create_node 前段时，才把 batch 归到 CLI/plugin/import 层。"""
    payload = rclpy_stage_stream_payload(probes)
    if not source_amortized_batch_active(probes):
        return False
    boundary = str(payload.get("boundary") or "")
    if boundary == "rclpy_graph_stage_stream_failed":
        segments = payload.get("segments") if isinstance(payload.get("segments"), list) else []
        segment_names = {str(segment.get("name")) for segment in segments if isinstance(segment, dict)}
        return "create_node" not in segment_names
    if boundary != "rclpy_graph_stage_stream_timeout":
        return False
    last_started = str(payload.get("last_started_stage") or "")
    last_completed = str(payload.get("last_completed_stage") or "")
    return bool(last_started in {"import_rclpy", "rclpy_init", "create_node"} and last_completed != last_started)


def rclpy_source_amortized_stage_reason(probes: dict[str, Any]) -> str:
    """primary reason 要落到具体 stage，不能再写泛化 rclpy_graph_segment_probe_timeout。"""
    payload = rclpy_stage_stream_payload(probes)
    last_started = str(payload.get("last_started_stage") or "")
    if last_started:
        return f"source_amortized_rclpy_stage_timeout_at_{last_started}"
    boundary = str(payload.get("boundary") or "rclpy_graph_stage_stream_blocked")
    return f"source_amortized_{boundary}"


def managed_process_graph_block_summary(
    *,
    managed_runtime: dict[str, Any],
    graph_wait_blocked: bool,
    require_planner_server: bool,
) -> dict[str, Any]:
    """graph blocked 时把 process/lifecycle 证据写清，不把 skipped lifecycle 当 inactive。"""
    process = managed_runtime.get("process")
    poll_value = process.poll() if hasattr(process, "poll") else None
    expected_nodes = ["/map_server", "/amcl"]
    if require_planner_server:
        expected_nodes.append("/planner_server")
    wait_result = managed_runtime.get("wait_result") if isinstance(managed_runtime.get("wait_result"), dict) else {}
    observed_nodes = sorted(
        {
            f"/{str(name).lstrip('/')}"
            for name in (wait_result.get("observed_node_names") or [])
            if isinstance(name, str) and name
        }
    )
    lifecycle_results = wait_result.get("lifecycle_results") if isinstance(wait_result.get("lifecycle_results"), dict) else {}
    lifecycle_probe_skipped = {
        key: lifecycle_result_is_skipped(result)
        for key, result in lifecycle_results.items()
        if isinstance(result, dict)
    }
    return {
        "managed_runtime_started": bool(managed_runtime.get("started")),
        "process_group": managed_runtime.get("process_group"),
        "process_alive": bool(managed_runtime.get("started") and poll_value is None),
        "process_returncode": poll_value,
        "expected_nodes": expected_nodes,
        "observed_nodes": observed_nodes,
        "missing_expected_nodes": [node for node in expected_nodes if node not in observed_nodes],
        "graph_wait_blocked": bool(graph_wait_blocked),
        "wait_reason": wait_result.get("reason") or wait_result.get("boundary"),
        "lifecycle_probe_status": (
            "skipped_after_ros2_graph_timeout"
            if graph_wait_blocked and not observed_nodes
            else "executed_or_partially_observed"
            if lifecycle_results
            else "not_requested"
        ),
        "lifecycle_probe_skipped": lifecycle_probe_skipped,
        "lifecycle_results": lifecycle_results,
        "log_tail": preview_file(str(managed_runtime.get("log_path") or "")),
    }


DAEMON_DDS_SPLIT_CANDIDATES = (
    "ros2_daemon_state_timeout",
    "dds_discovery_or_domain_mismatch",
    "workspace_source_or_env_mismatch",
    "managed_process_lifecycle_visibility_blocked",
    "graph_command_budget_insufficient",
    "ros2_cli_no_daemon_unsupported",
)


def candidate_record(candidate: str, reason: str, *, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    """daemon/DDS split 候选使用稳定 candidate 名称，避免继续复用泛化 classification。"""
    return {
        "candidate": candidate,
        "reason": reason,
        "evidence": evidence or {},
    }


def daemon_safe_retry_summary_from_probes(probes: dict[str, Any]) -> dict[str, Any]:
    """兼容 batch final 与 legacy probe 两种位置读取 daemon-safe retry 摘要。"""
    retry_probe = probes.get("daemon_safe_retry") if isinstance(probes.get("daemon_safe_retry"), dict) else {}
    retry_summary = retry_probe.get("summary") if isinstance(retry_probe.get("summary"), dict) else {}
    if retry_summary:
        return retry_summary
    batch = probes.get("source_amortized_batch") if isinstance(probes.get("source_amortized_batch"), dict) else {}
    if isinstance(batch.get("daemon_safe_retry"), dict):
        return batch["daemon_safe_retry"]
    return {
        "schema": "trashbot.o10.daemon_safe_graph_retry.v1",
        "attempted": False,
        "skipped": True,
        "skip_reason": str(batch.get("boundary") or "daemon_safe_retry_summary_missing"),
        "reset_completed": False,
        "graph_retry_observed": False,
        "commands": {},
    }


def retry_command_boundary(daemon_retry: dict[str, Any], label: str) -> str:
    """daemon reset 后的 retry command 已经在 batch 内写了 boundary，这里只做安全读取。"""
    commands = daemon_retry.get("commands") if isinstance(daemon_retry.get("commands"), dict) else {}
    result = commands.get(label) if isinstance(commands.get(label), dict) else {}
    return str(result.get("boundary") or "")


def retry_command_ok(daemon_retry: dict[str, Any], label: str) -> bool:
    """按 label 读取 daemon-safe retry 子命令是否成功，避免解析 stdout 原文。"""
    commands = daemon_retry.get("commands") if isinstance(daemon_retry.get("commands"), dict) else {}
    result = commands.get(label) if isinstance(commands.get(label), dict) else {}
    return bool(result.get("ok"))


def safe_workspace_env_summary(probes: dict[str, Any], board_source_preflight: dict[str, Any]) -> dict[str, Any]:
    """只回显 ROS/DDS/domain 和路径 presence 摘要，不 dump 完整环境变量。"""
    env_probe = probes.get("workspace_environment") if isinstance(probes.get("workspace_environment"), dict) else {}
    summary = env_probe.get("summary") if isinstance(env_probe.get("summary"), dict) else {}
    safe_summary: dict[str, Any] = {
        "ROS_DISTRO": summary.get("ROS_DISTRO"),
        "ROS_DOMAIN_ID": summary.get("ROS_DOMAIN_ID"),
        "RMW_IMPLEMENTATION": summary.get("RMW_IMPLEMENTATION"),
        "which_ros2": summary.get("which_ros2"),
        "workspace_environment_boundary": env_probe.get("boundary"),
        "board_source_preflight": {
            "classification": board_source_preflight.get("classification"),
            "cli_ready": bool(board_source_preflight.get("cli_ready")),
            "runtime_ready": bool(board_source_preflight.get("runtime_ready")),
            "ros2_cli_invocation_ok": bool(board_source_preflight.get("ros2_cli_invocation_ok")),
            "rclpy_import_ok": bool(board_source_preflight.get("rclpy_import_ok")),
        },
    }
    for name in ("AMENT_PREFIX_PATH", "PYTHONPATH", "LD_LIBRARY_PATH"):
        value = summary.get(name) if isinstance(summary.get(name), dict) else {}
        safe_summary[name] = {
            "entry_count": value.get("entry_count"),
            "contains_ros": bool(value.get("contains_ros")),
            "contains_onboard_workspace": bool(value.get("contains_onboard_workspace")),
            "ros_match_count": len(value.get("ros_matches") or []) if isinstance(value.get("ros_matches"), list) else 0,
            "workspace_match_count": len(value.get("workspace_matches") or []) if isinstance(value.get("workspace_matches"), list) else 0,
        }
    return safe_summary


def graph_budget_summary(probes: dict[str, Any], daemon_retry: dict[str, Any]) -> dict[str, Any]:
    """把各 graph 命令预算压缩到一处，用来判断 timeout 是预算问题还是 discovery 问题。"""
    command_labels = (
        "ros2_node_list",
        "ros2_node_list_no_daemon",
        "ros2_daemon_status",
        "ros2_node_list_help",
        "ros2_topic_list",
    )
    commands = {
        label: {
            "boundary": graph_probe_boundary(probes, label),
            "timeout_s": (probes.get(label) or {}).get("timeout_s") if isinstance(probes.get(label), dict) else None,
            "elapsed_ms": (probes.get(label) or {}).get("elapsed_ms") if isinstance(probes.get(label), dict) else None,
            "timed_out": bool((probes.get(label) or {}).get("timed_out")) if isinstance(probes.get(label), dict) else False,
        }
        for label in command_labels
    }
    retry_commands = daemon_retry.get("commands") if isinstance(daemon_retry.get("commands"), dict) else {}
    retry = {
        label: {
            "boundary": result.get("boundary"),
            "timeout_s": result.get("timeout_s"),
            "elapsed_ms": result.get("elapsed_ms"),
            "timed_out": bool(result.get("timed_out")),
        }
        for label, result in retry_commands.items()
        if isinstance(result, dict)
    }
    batch = probes.get("source_amortized_batch") if isinstance(probes.get("source_amortized_batch"), dict) else {}
    return {
        "schema": "trashbot.o10.graph_command_budget_summary.v1",
        "batch_timeout_s": ROS2_GRAPH_SOURCE_AMORTIZED_BATCH_TIMEOUT_S,
        "batch_boundary": batch.get("boundary"),
        "source_stage_elapsed_ms": (
            batch.get("source_stage", {}).get("elapsed_ms")
            if isinstance(batch.get("source_stage"), dict)
            else None
        ),
        "commands": commands,
        "daemon_retry_commands": retry,
    }


def daemon_safe_graph_readback_contract(
    probes: dict[str, Any],
    daemon_retry: dict[str, Any],
    *,
    process_summary: dict[str, Any],
) -> dict[str, Any]:
    """把 stop/start + 8s node/topic 复验整理成单独合同，供 sprint 和下一轮直接读取。"""
    pre_status = probes.get("ros2_daemon_status") if isinstance(probes.get("ros2_daemon_status"), dict) else {}
    commands = daemon_retry.get("commands") if isinstance(daemon_retry.get("commands"), dict) else {}

    def read_command(label: str) -> dict[str, Any]:
        result = commands.get(label) if isinstance(commands.get(label), dict) else {}
        if result:
            return result
        return {
            "boundary": f"{label}_missing",
            "ok": False,
            "timed_out": False,
            "timeout_s": None,
            "elapsed_ms": None,
            "returncode": None,
            "stdout_summary": "",
            "stderr_summary": "",
            "error": None,
        }

    stop_result = read_command("ros2_daemon_stop")
    start_result = read_command("ros2_daemon_start")
    status_after_result = read_command("ros2_daemon_status_after_reset")
    node_after_result = read_command("ros2_node_list_after_daemon_reset")
    topic_after_result = read_command("ros2_topic_list_after_daemon_reset")

    node_boundary = str(node_after_result.get("boundary") or "")
    topic_boundary = str(topic_after_result.get("boundary") or "")
    status_after_boundary = str(status_after_result.get("boundary") or "")

    node_outcome = (
        "observed"
        if node_boundary.endswith("_observed")
        else "empty"
        if node_boundary.endswith("_empty")
        else "timeout"
        if node_boundary.endswith("_timeout")
        else "failed"
        if node_boundary
        else "not_run"
    )
    topic_outcome = (
        "observed"
        if topic_boundary.endswith("_ok") or topic_boundary.endswith("_observed")
        else "timeout"
        if topic_boundary.endswith("_timeout")
        else "failed"
        if topic_boundary
        else "not_run"
    )

    reset_attempted = bool(daemon_retry.get("attempted"))
    reset_completed = bool(daemon_retry.get("reset_completed"))
    reset_skipped = bool(daemon_retry.get("skipped"))
    skip_reason = str(daemon_retry.get("skip_reason") or "")

    if reset_skipped:
        primary_conclusion = "daemon_reset_not_executed"
        next_step = "continue_daemon_or_cli_budget_split_before_lifecycle_gate"
    elif reset_completed and node_outcome == "observed" and topic_outcome == "observed":
        primary_conclusion = "graph_readback_recovered_after_daemon_reset"
        next_step = "return_to_lifecycle_localization_gate_without_motion"
    elif reset_completed and node_outcome == "empty" and topic_outcome == "observed":
        primary_conclusion = "topic_graph_visible_but_node_graph_empty_after_daemon_reset"
        next_step = "narrow_to_managed_lifecycle_visibility_or_graph_budget"
    elif reset_completed and node_outcome == "timeout" and topic_outcome == "timeout":
        primary_conclusion = "node_and_topic_graph_timeout_after_daemon_reset"
        next_step = "narrow_to_dds_domain_or_graph_budget"
    elif reset_completed and node_outcome == "timeout":
        primary_conclusion = "node_graph_timeout_after_daemon_reset"
        next_step = "narrow_to_dds_domain_or_managed_lifecycle_visibility"
    elif reset_completed and topic_outcome == "timeout":
        primary_conclusion = "topic_graph_timeout_after_daemon_reset"
        next_step = "narrow_to_dds_domain_or_graph_budget"
    elif reset_attempted:
        primary_conclusion = "daemon_reset_attempted_but_not_confirmed"
        next_step = "verify_daemon_status_completion_before_graph_or_lifecycle_gate"
    else:
        primary_conclusion = "daemon_safe_readback_not_attempted"
        next_step = "continue_daemon_or_cli_budget_split_before_lifecycle_gate"

    return {
        "schema": "trashbot.o10.daemon_safe_graph_readback.v1",
        "strict_no_motion": True,
        "pre_reset_daemon_status": {
            "boundary": pre_status.get("boundary"),
            "ok": bool(pre_status.get("ok")),
            "timed_out": bool(pre_status.get("timed_out")),
            "timeout_s": pre_status.get("timeout_s"),
            "elapsed_ms": pre_status.get("elapsed_ms"),
            "returncode": pre_status.get("returncode"),
            "stdout_summary": pre_status.get("stdout_summary", ""),
            "stderr_summary": pre_status.get("stderr_summary", ""),
            "error": pre_status.get("error") if isinstance(pre_status.get("error"), dict) else None,
        },
        "reset_attempted": reset_attempted,
        "reset_skipped": reset_skipped,
        "reset_skip_reason": skip_reason or None,
        "reset_completed": reset_completed,
        "commands": {
            "ros2_daemon_stop": stop_result,
            "ros2_daemon_start": start_result,
            "ros2_daemon_status_after_reset": status_after_result,
            "ros2_node_list_after_daemon_reset": node_after_result,
            "ros2_topic_list_after_daemon_reset": topic_after_result,
        },
        "graph_readback": {
            "node_list_outcome": node_outcome,
            "node_list_boundary": node_boundary,
            "topic_list_outcome": topic_outcome,
            "topic_list_boundary": topic_boundary,
            "status_after_reset_boundary": status_after_boundary,
            "graph_retry_observed": bool(daemon_retry.get("graph_retry_observed")),
        },
        "managed_lifecycle_context": {
            "managed_runtime_started": bool(process_summary.get("managed_runtime_started")),
            "process_alive": bool(process_summary.get("process_alive")),
            "missing_expected_nodes": process_summary.get("missing_expected_nodes"),
            "lifecycle_probe_status": process_summary.get("lifecycle_probe_status"),
            "wait_reason": process_summary.get("wait_reason"),
        },
        "primary_conclusion": primary_conclusion,
        "next_step": next_step,
        "evidence_boundary": {
            "path_generation_attempted": False,
            "path_generated": False,
            "safe_to_control": False,
            "publishes_cmd_vel": False,
            "calls_base_manual": False,
            "robot_control_executed": False,
            "route_execution_success": False,
            "delivery_success": False,
            "hil_pass": False,
            "uses_base_uart": False,
            "sends_navigate_to_pose": False,
        },
    }


def next_live_command_for_split(candidate: str) -> str:
    """下一条 live 命令必须继续 no-motion，只做 graph/env/lifecycle 只读或 daemon-safe retry。"""
    if candidate == "ros2_daemon_state_timeout":
        return (
            "ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && "
            "source /opt/ros/humble/setup.bash && [ -f install/setup.bash ] && source install/setup.bash || true; "
            "ros2 daemon status; ros2 daemon stop; ros2 daemon start; timeout 8 ros2 node list; timeout 8 ros2 topic list'"
        )
    if candidate == "workspace_source_or_env_mismatch":
        return (
            "ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && "
            "source /opt/ros/humble/setup.bash && [ -f install/setup.bash ] && source install/setup.bash || true; "
            "env | egrep \"^(ROS_DISTRO|ROS_DOMAIN_ID|RMW_IMPLEMENTATION|AMENT_PREFIX_PATH|PYTHONPATH|LD_LIBRARY_PATH)=\"; "
            "command -v ros2; python3 -c \"import rclpy; print(rclpy.__file__)\"'"
        )
    if candidate == "managed_process_lifecycle_visibility_blocked":
        return (
            "ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && "
            "source /opt/ros/humble/setup.bash && [ -f install/setup.bash ] && source install/setup.bash || true; "
            "timeout 8 ros2 lifecycle get /map_server; timeout 8 ros2 lifecycle get /amcl; "
            "timeout 8 ros2 node list'"
        )
    if candidate == "graph_command_budget_insufficient":
        return (
            "ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && "
            "source /opt/ros/humble/setup.bash && [ -f install/setup.bash ] && source install/setup.bash || true; "
            "timeout 12 ros2 node list; timeout 12 ros2 topic list; timeout 12 ros2 daemon status'"
        )
    if candidate == "ros2_cli_no_daemon_unsupported":
        return (
            "ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && "
            "source /opt/ros/humble/setup.bash && ros2 node list --help | head -80'"
        )
    return (
        "ssh -p 37878 root@192.168.1.11 'cd /root/rober/onboard && "
        "source /opt/ros/humble/setup.bash && [ -f install/setup.bash ] && source install/setup.bash || true; "
        "env | egrep \"^(ROS_DOMAIN_ID|RMW_IMPLEMENTATION|ROS_DISTRO)=\"; "
        "ros2 daemon status; timeout 8 ros2 node list; timeout 8 ros2 topic list'"
    )


def build_daemon_dds_split_contract(
    *,
    board_source_preflight: dict[str, Any],
    process_summary: dict[str, Any],
    probes: dict[str, Any],
    env_ready: bool,
    board_cli_ready: bool,
    help_ok: bool,
    graph_discovery_timeout: bool,
    node_list_timeout: bool,
    topic_list_timeout: bool,
    daemon_status_timeout: bool,
    no_daemon_timeout: bool,
    no_daemon_unsupported: bool,
) -> dict[str, Any]:
    """把泛化 daemon/DDS timeout 拆成 Product 可执行的候选层。"""
    excluded: list[dict[str, Any]] = []
    remaining: list[dict[str, Any]] = []
    candidate_status: dict[str, str] = {candidate: "not_evaluated" for candidate in DAEMON_DDS_SPLIT_CANDIDATES}
    daemon_retry = daemon_safe_retry_summary_from_probes(probes)
    reset_attempted = bool(daemon_retry.get("attempted"))
    reset_skipped = bool(daemon_retry.get("skipped"))
    reset_completed = bool(daemon_retry.get("reset_completed"))
    retry_node_boundary = retry_command_boundary(daemon_retry, "ros2_node_list_after_daemon_reset")
    retry_topic_boundary = retry_command_boundary(daemon_retry, "ros2_topic_list_after_daemon_reset")
    retry_status_after_boundary = retry_command_boundary(daemon_retry, "ros2_daemon_status_after_reset")
    retry_graph_timeout = bool(
        retry_node_boundary == "ros2_node_list_after_daemon_reset_timeout"
        or retry_topic_boundary == "ros2_topic_list_after_daemon_reset_timeout"
    )
    retry_graph_observed = bool(daemon_retry.get("graph_retry_observed"))
    retry_status_after_ok = retry_command_ok(daemon_retry, "ros2_daemon_status_after_reset")
    batch = probes.get("source_amortized_batch") if isinstance(probes.get("source_amortized_batch"), dict) else {}
    batch_timeout = str(batch.get("boundary") or "") == "source_amortized_batch_timeout"
    daemon_safe_graph_readback = daemon_safe_graph_readback_contract(
        probes,
        daemon_retry,
        process_summary=process_summary,
    )

    primary = candidate_record("dds_discovery_or_domain_mismatch", "graph_timeout_after_source_env_split")

    def set_primary(candidate: str, reason: str, *, evidence: dict[str, Any] | None = None) -> None:
        nonlocal primary
        previous_candidate = str(primary.get("candidate") or "")
        if previous_candidate in candidate_status and candidate_status.get(previous_candidate) == "primary":
            candidate_status[previous_candidate] = "remaining"
        primary = candidate_record(candidate, reason, evidence=evidence)
        candidate_status[candidate] = "primary"

    def add_excluded(candidate: str, reason: str, *, evidence: dict[str, Any] | None = None) -> None:
        if candidate_status.get(candidate) == "primary":
            return
        candidate_status[candidate] = "excluded"
        excluded.append(candidate_record(candidate, reason, evidence=evidence))

    def add_remaining(candidate: str, reason: str, *, evidence: dict[str, Any] | None = None) -> None:
        if candidate_status.get(candidate) in {"primary", "excluded"}:
            return
        candidate_status[candidate] = "remaining"
        remaining.append(candidate_record(candidate, reason, evidence=evidence))

    if env_ready:
        add_excluded("workspace_source_or_env_mismatch", "safe_env_summary_contains_ros_and_onboard_workspace")
    elif board_cli_ready:
        add_remaining("workspace_source_or_env_mismatch", "safe_env_summary_missing_or_incomplete_after_cli_ready")
    else:
        set_primary("workspace_source_or_env_mismatch", "board_source_preflight_cli_not_ready")

    if no_daemon_unsupported:
        add_remaining("ros2_cli_no_daemon_unsupported", "current_ros2_cli_rejected_node_list_no_daemon")
    elif no_daemon_timeout:
        add_remaining("ros2_cli_no_daemon_unsupported", "node_list_no_daemon_probe_timed_out_capability_unknown")
    elif graph_probe_boundary(probes, "ros2_node_list_no_daemon") in {
        "ros2_node_list_no_daemon_observed",
        "ros2_node_list_no_daemon_empty",
    }:
        add_excluded("ros2_cli_no_daemon_unsupported", "node_list_no_daemon_command_completed")

    if daemon_status_timeout and (not reset_attempted or not reset_completed):
        set_primary(
            "ros2_daemon_state_timeout",
            "daemon_status_timed_out_and_daemon_reset_not_confirmed",
            evidence={
                "reset_attempted": reset_attempted,
                "reset_skipped": reset_skipped,
                "skip_reason": daemon_retry.get("skip_reason"),
            },
        )
    elif reset_attempted and reset_completed and retry_graph_observed:
        set_primary(
            "ros2_daemon_state_timeout",
            "daemon_reset_recovered_graph_visibility",
            evidence={"retry_node_boundary": retry_node_boundary, "retry_topic_boundary": retry_topic_boundary},
        )
    elif reset_attempted and (reset_completed or retry_status_after_ok) and retry_graph_timeout:
        add_excluded(
            "ros2_daemon_state_timeout",
            "daemon_reset_completed_or_status_ok_but_graph_retry_still_timed_out",
            evidence={"retry_status_after_boundary": retry_status_after_boundary},
        )
        set_primary(
            "dds_discovery_or_domain_mismatch",
            "daemon_reset_did_not_restore_node_or_topic_graph_visibility",
            evidence={"retry_node_boundary": retry_node_boundary, "retry_topic_boundary": retry_topic_boundary},
        )
    elif not daemon_status_timeout and graph_probe_boundary(probes, "ros2_daemon_status") == "ros2_daemon_status_ok":
        add_excluded("ros2_daemon_state_timeout", "daemon_status_completed_before_reset")
    else:
        add_remaining(
            "ros2_daemon_state_timeout",
            "daemon_state_not_fully_excluded",
            evidence={"reset_attempted": reset_attempted, "skip_reason": daemon_retry.get("skip_reason")},
        )

    if process_summary.get("managed_runtime_started") and process_summary.get("missing_expected_nodes"):
        add_remaining(
            "managed_process_lifecycle_visibility_blocked",
            "managed_runtime_started_but_expected_nodes_or_lifecycle_not_visible_after_graph_block",
            evidence={
                "missing_expected_nodes": process_summary.get("missing_expected_nodes"),
                "lifecycle_probe_status": process_summary.get("lifecycle_probe_status"),
            },
        )
    elif process_summary.get("managed_runtime_started"):
        add_excluded("managed_process_lifecycle_visibility_blocked", "managed_runtime_expected_nodes_visible_or_not_missing")
    else:
        add_remaining("managed_process_lifecycle_visibility_blocked", "managed_runtime_not_started_or_not_observable_in_split")

    if batch_timeout:
        set_primary(
            "graph_command_budget_insufficient",
            "source_amortized_batch_timed_out_before_final_graph_split",
            evidence={"batch_boundary": batch.get("boundary")},
        )
    elif graph_discovery_timeout:
        add_remaining(
            "graph_command_budget_insufficient",
            "bounded_graph_commands_reached_configured_timeouts",
            evidence={"node_list_timeout": node_list_timeout, "topic_list_timeout": topic_list_timeout},
        )
    else:
        add_excluded("graph_command_budget_insufficient", "graph_commands_completed_within_configured_budgets")

    if graph_discovery_timeout and env_ready and help_ok and board_source_preflight.get("rclpy_import_ok"):
        if primary["candidate"] not in {"ros2_daemon_state_timeout", "graph_command_budget_insufficient"}:
            set_primary(
                "dds_discovery_or_domain_mismatch",
                "source_env_help_and_rclpy_ready_but_ros2_node_topic_graph_timed_out",
                evidence={
                    "ROS_DOMAIN_ID": safe_workspace_env_summary(probes, board_source_preflight).get("ROS_DOMAIN_ID"),
                    "RMW_IMPLEMENTATION": safe_workspace_env_summary(probes, board_source_preflight).get("RMW_IMPLEMENTATION"),
                },
            )
    elif graph_discovery_timeout:
        add_remaining("dds_discovery_or_domain_mismatch", "graph_timeout_present_but_env_or_cli_readiness_not_fully_excluded")
    else:
        add_excluded("dds_discovery_or_domain_mismatch", "node_and_topic_graph_commands_not_timed_out")

    # primary 可能先由 env/daemon/budget 设置；最后再把未触达候选补成 remaining，便于读者看到全量枚举。
    for candidate, status in list(candidate_status.items()):
        if status == "not_evaluated":
            add_remaining(candidate, "candidate_not_fully_evaluated_in_current_no_motion_window")

    return {
        "schema": "trashbot.o10.daemon_dds_graph_split.v1",
        "candidate_names": list(DAEMON_DDS_SPLIT_CANDIDATES),
        "primary_candidate": primary,
        "excluded_candidates": excluded,
        "remaining_candidates": remaining,
        "candidate_status": candidate_status,
        "safe_environment_summary": safe_workspace_env_summary(probes, board_source_preflight),
        "daemon_command_summaries": {
            "pre_reset_daemon_status": probes.get("ros2_daemon_status") if isinstance(probes.get("ros2_daemon_status"), dict) else {},
            "daemon_safe_retry": daemon_retry,
            "reset_attempted": reset_attempted,
            "reset_skipped": reset_skipped,
            "reset_skip_reason": daemon_retry.get("skip_reason"),
            "reset_completed": reset_completed,
            "retry_node_boundary": retry_node_boundary,
            "retry_topic_boundary": retry_topic_boundary,
        },
        "graph_budget_summary": graph_budget_summary(probes, daemon_retry),
        "managed_lifecycle_visibility_summary": {
            "managed_runtime_started": process_summary.get("managed_runtime_started"),
            "process_alive": process_summary.get("process_alive"),
            "missing_expected_nodes": process_summary.get("missing_expected_nodes"),
            "lifecycle_probe_status": process_summary.get("lifecycle_probe_status"),
            "wait_reason": process_summary.get("wait_reason"),
        },
        "daemon_safe_graph_readback": daemon_safe_graph_readback,
        "next_live_command": next_live_command_for_split(str(primary.get("candidate") or "")),
        "evidence_boundary": {
            "scope": "strict_no_motion_daemon_dds_graph_split",
            "path_generation_attempted": False,
            "path_generated": False,
            "safe_to_control": False,
            "publishes_cmd_vel": False,
            "calls_base_manual": False,
            "robot_control_executed": False,
            "route_execution_success": False,
            "delivery_success": False,
            "hil_pass": False,
            "uses_base_uart": False,
            "sends_navigate_to_pose": False,
        },
    }


def build_ros2_graph_timeout_root_cause(
    *,
    board_source_preflight: dict[str, Any],
    managed_runtime: dict[str, Any],
    managed_runtime_wait_graph_blocked: bool,
    probes: dict[str, Any],
    tf_source_root_cause_detail: dict[str, Any] | None,
    require_planner_server: bool,
) -> dict[str, Any]:
    """把 `ros2_node_list_timeout` 拆成 additive root-cause contract。"""
    excluded: list[dict[str, Any]] = []
    remaining: list[dict[str, Any]] = []
    process_summary = managed_process_graph_block_summary(
        managed_runtime=managed_runtime,
        graph_wait_blocked=managed_runtime_wait_graph_blocked,
        require_planner_server=require_planner_server,
    )
    source_amortized_active = source_amortized_batch_active(probes)
    env_ready = workspace_environment_ready(probes, board_source_preflight)
    board_cli_ready = bool(board_source_preflight.get("cli_ready"))
    help_ok = graph_probe_has_boundary(probes, "ros2_node_list_help", {"ros2_node_list_help_ok"})
    topic_list_timeout = graph_probe_has_boundary(probes, "ros2_topic_list", {"ros2_topic_list_timeout"})
    node_list_timeout = graph_probe_has_boundary(probes, "ros2_node_list", {"ros2_node_list_timeout"})
    no_daemon_timeout = graph_probe_has_boundary(probes, "ros2_node_list_no_daemon", {"ros2_node_list_no_daemon_timeout"})
    daemon_status_timeout = graph_probe_has_boundary(probes, "ros2_daemon_status", {"ros2_daemon_status_timeout"})
    no_daemon_unsupported = graph_probe_has_boundary(probes, "ros2_node_list_no_daemon", {"unsupported_option"})
    graph_discovery_timeout = bool(node_list_timeout or no_daemon_timeout or daemon_status_timeout or topic_list_timeout)
    graph_cli_import_ready = bool(board_source_preflight.get("rclpy_import_ok") and help_ok)
    rclpy_payload = rclpy_stage_stream_payload(probes)
    rclpy_segments = rclpy_payload.get("segments") if isinstance(rclpy_payload.get("segments"), list) else []
    rclpy_segment_names = {
        str(segment.get("name"))
        for segment in rclpy_segments
        if isinstance(segment, dict) and segment.get("name")
    }
    rclpy_import_stage_failed = bool(
        str(rclpy_payload.get("boundary") or "").startswith("rclpy_graph_segment_probe_failed")
        and "import_rclpy" not in rclpy_segment_names
    )
    rclpy_segment_probe_timeout = graph_probe_has_boundary(
        probes,
        "rclpy_graph_segments",
        {"rclpy_graph_segment_probe_timeout", "rclpy_graph_stage_stream_timeout"},
    )
    rclpy_startup_blocked = rclpy_source_amortized_startup_blocked(probes)
    if source_amortized_active:
        cli_plugin_suspect = bool(
            not board_source_preflight.get("rclpy_import_ok")
            or rclpy_import_stage_failed
            or rclpy_startup_blocked
        )
    else:
        cli_plugin_suspect = bool(
            graph_probe_has_boundary(probes, "ros2_node_list_help", {"ros2_node_list_help_timeout", "ros2_node_list_help_failed"})
            or not board_source_preflight.get("rclpy_import_ok")
            or rclpy_import_stage_failed
            or rclpy_segment_probe_timeout
        )
    cli_plugin_reason_boundaries: list[str] = []
    help_boundary = graph_probe_boundary(probes, "ros2_node_list_help")
    if help_boundary in {"ros2_node_list_help_timeout", "ros2_node_list_help_failed"} and (
        not source_amortized_active or rclpy_startup_blocked
    ):
        cli_plugin_reason_boundaries.append(help_boundary)
    rclpy_probe_boundary = graph_probe_boundary(probes, "rclpy_graph_segments")
    if source_amortized_active and rclpy_startup_blocked:
        cli_plugin_reason_boundaries.append(rclpy_source_amortized_stage_reason(probes))
    elif rclpy_probe_boundary == "rclpy_graph_segment_probe_timeout" or rclpy_import_stage_failed:
        cli_plugin_reason_boundaries.append(rclpy_probe_boundary or str(rclpy_payload.get("boundary") or "rclpy_graph_segment_probe_failed"))
    if not board_source_preflight.get("rclpy_import_ok"):
        preflight_reason = str(board_source_preflight.get("classification") or "")
        # `board_source_preflight_ready` 是通过状态，不是 CLI/plugin timeout 的根因。
        if preflight_reason and preflight_reason != "board_source_preflight_ready":
            cli_plugin_reason_boundaries.append(preflight_reason)
    cli_plugin_reason_boundaries = list(dict.fromkeys(cli_plugin_reason_boundaries))

    if env_ready:
        excluded.append(
            {
                "classification": "workspace_source_or_env_mismatch",
                "reason": (
                    "source_amortized_sourced_shell_env_contains_ros_and_onboard_workspace"
                    if source_amortized_active
                    else "sourced_shell_env_contains_ros_and_onboard_workspace"
                ),
            }
        )
    elif board_cli_ready:
        remaining.append(
            {
                "classification": "workspace_source_or_env_mismatch",
                "reason": "workspace_environment_summary_not_observed_but_board_source_preflight_cli_ready",
            }
        )
    if help_ok and board_source_preflight.get("rclpy_import_ok"):
        excluded.append(
            {
                "classification": "ros2_cli_plugin_or_import_timeout",
                "reason": "ros2_node_list_help_and_rclpy_import_completed",
            }
        )
    if no_daemon_unsupported:
        remaining.append(
            {
                "classification": "ros2_daemon_or_dds_graph_discovery_timeout",
                "reason": "ros2_node_list_no_daemon_unsupported_in_current_cli",
            }
        )

    if not board_cli_ready:
        classification = "workspace_source_or_env_mismatch"
        reason = str(board_source_preflight.get("classification") or "workspace_environment_summary_missing_ros_or_workspace")
    elif managed_runtime_wait_graph_blocked and graph_cli_import_ready and graph_discovery_timeout:
        # help/import 已通过时，node/topic/daemon graph 超时是 DDS/daemon discovery blocker；
        # 即使 workspace env 摘要自己超时，也只能作为 remaining candidate，不能反推成 source mismatch。
        classification = "ros2_daemon_or_dds_graph_discovery_timeout"
        reason = str(process_summary.get("wait_reason") or "ros2_graph_discovery_timeout_after_managed_runtime_started")
    elif cli_plugin_suspect:
        classification = "ros2_cli_plugin_or_import_timeout"
        reason = "_and_".join(cli_plugin_reason_boundaries) or "ros2_cli_help_or_import_probe_failed"
    elif managed_runtime_wait_graph_blocked and graph_discovery_timeout:
        classification = "ros2_daemon_or_dds_graph_discovery_timeout"
        reason = str(process_summary.get("wait_reason") or "ros2_graph_discovery_timeout_after_managed_runtime_started")
    elif process_summary["managed_runtime_started"] and process_summary["missing_expected_nodes"]:
        classification = "managed_process_lifecycle_not_ready"
        reason = "managed_runtime_process_alive_but_expected_nodes_not_observed"
    else:
        classification = "root_cause_unclassified_after_probe"
        reason = "graph_timeout_not_uniquely_explained_by_low_budget_probes"

    if process_summary["managed_runtime_started"] and process_summary["missing_expected_nodes"]:
        remaining.append(
            {
                "classification": "managed_process_lifecycle_not_ready",
                "reason": "process_started_but_lifecycle_or_expected_nodes_not_proven_ready",
            }
        )
    tf_detail = tf_source_root_cause_detail or {}
    if managed_runtime_wait_graph_blocked and str(tf_detail.get("reason") or "") == "/tf_topic_missing":
        remaining.append(
            {
                "classification": "tf_runtime_secondary_after_graph_blocked",
                "reason": "/tf_topic_missing_recorded_as_secondary_readback_after_graph_blocked",
            }
        )
    daemon_dds_split = build_daemon_dds_split_contract(
        board_source_preflight=board_source_preflight,
        process_summary=process_summary,
        probes=probes,
        env_ready=env_ready,
        board_cli_ready=board_cli_ready,
        help_ok=help_ok,
        graph_discovery_timeout=graph_discovery_timeout,
        node_list_timeout=node_list_timeout,
        topic_list_timeout=topic_list_timeout,
        daemon_status_timeout=daemon_status_timeout,
        no_daemon_timeout=no_daemon_timeout,
        no_daemon_unsupported=no_daemon_unsupported,
    )

    return {
        "classification": classification,
        "primary_candidate": {
            "classification": classification,
            "reason": reason,
        },
        "excluded_candidates": excluded,
        "remaining_candidates": remaining,
        "evidence_priority": "source_amortized_batch" if source_amortized_active else "legacy_per_command_probes",
        "probes": {
            **probes,
            "managed_process": process_summary,
        },
        "daemon_dds_split": daemon_dds_split,
        "evidence_boundary": {
            "scope": "strict_no_motion_read_only_ros2_graph_timeout_probe",
            "evidence_priority": "source_amortized_batch" if source_amortized_active else "legacy_per_command_probes",
            "source_amortized_batch_used": bool(source_amortized_active),
            "graph_wait_blocked": bool(managed_runtime_wait_graph_blocked),
            "safe_to_control": False,
            "publishes_cmd_vel": False,
            "calls_base_manual": False,
            "robot_control_executed": False,
            "route_execution_success": False,
            "delivery_success": False,
            "hil_pass": False,
            "uses_base_uart": False,
            "path_generation_attempted_when_gate_blocked": False,
            "path_generated": False,
        },
    }


def write_json_atomic(path: str, payload: dict[str, Any]) -> None:
    """latest artifact 必须原子替换，避免 GET route 读到半截 JSON。"""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp_path, output_path)


def read_json(path: str) -> tuple[dict[str, Any] | None, dict[str, str] | None]:
    """读取上轮 canonical map proof；读失败必须进入 root cause，而不是继续猜。"""
    try:
        parsed = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, {"layer": "canonical map proof", "reason": "map_lifecycle_latest_missing"}
    except json.JSONDecodeError:
        return None, {"layer": "canonical map proof", "reason": "map_lifecycle_latest_bad_json"}
    except OSError:
        return None, {"layer": "canonical map proof", "reason": "map_lifecycle_latest_read_failed"}
    if not isinstance(parsed, dict):
        return None, {"layer": "canonical map proof", "reason": "map_lifecycle_latest_json_not_object"}
    return parsed, None


def successful_files(map_files: Any, suffix: str) -> list[dict[str, Any]]:
    """只接受 proof 中 stat 成功且本地仍存在的地图文件，避免消费陈旧 artifact。"""
    result: list[dict[str, Any]] = []
    if not isinstance(map_files, list):
        return result
    for item in map_files:
        if not isinstance(item, dict) or item.get("ok") is False:
            continue
        path = str(item.get("path") or "")
        item_suffix = str(item.get("suffix") or Path(path).suffix)
        if item_suffix == suffix and Path(path).exists():
            result.append(dict(item))
    return result


def map_input_summary(args: argparse.Namespace) -> dict[str, Any]:
    """把 canonical map proof 转成 Nav2 collector 输入；默认路径不拉起新 runtime。"""
    latest, read_error = read_json(args.map_proof)
    proof = latest.get("proof") if isinstance(latest, dict) and isinstance(latest.get("proof"), dict) else {}
    yaml_files = successful_files(proof.get("map_files"), ".yaml")
    pgm_files = successful_files(proof.get("map_files"), ".pgm")
    expected_map_dir = str(Path(args.map_dir))
    observed_map_dir = proof.get("map_artifact_dir") if isinstance(proof.get("map_artifact_dir"), str) else None
    root_causes: list[dict[str, str]] = []
    if read_error:
        root_causes.append(read_error)
    else:
        if proof.get("status") != "map_once_artifact_metadata_observed":
            root_causes.append({"layer": "canonical map proof", "reason": "map_lifecycle_proof_not_clean"})
        if proof.get("map_once_observed") is not True:
            root_causes.append({"layer": "canonical map proof", "reason": "map_once_not_observed"})
        if proof.get("map_file_observed") is not True:
            root_causes.append({"layer": "map artifact", "reason": "map_file_not_observed"})
        if proof.get("map_metadata_observed") is not True:
            root_causes.append({"layer": "map metadata", "reason": "map_metadata_not_observed"})
        if observed_map_dir != expected_map_dir:
            root_causes.append({"layer": "map artifact contract", "reason": "canonical_map_artifact_dir_mismatch"})
        if not yaml_files:
            root_causes.append({"layer": "map artifact", "reason": "map_yaml_missing_or_stale"})
        if not pgm_files:
            root_causes.append({"layer": "map artifact", "reason": "map_pgm_missing_or_stale"})
    return {
        "map_proof_path": args.map_proof,
        "map_artifact_dir": expected_map_dir,
        "source_evidence_type": latest.get("evidence_type") if isinstance(latest, dict) else None,
        "source_evidence_ref": proof.get("evidence_ref"),
        "source_proof_status": proof.get("status"),
        "map_metadata": proof.get("map_metadata") if isinstance(proof.get("map_metadata"), dict) else {},
        "map_yaml_candidates": yaml_files,
        "map_image_candidates": pgm_files,
        "root_causes": root_causes,
        "inputs_ready": not root_causes,
    }


def effective_map_inputs_for_runtime(
    map_inputs: dict[str, Any],
    *,
    managed_runtime_requested: bool,
    managed_runtime_started: bool,
    managed_map_analysis: dict[str, Any],
    map_once_observed: bool,
) -> dict[str, Any]:
    """managed runtime 已实测消费可用地图时，用本轮证据覆盖陈旧 canonical proof blocker。"""
    runtime_map_ready = bool(
        managed_runtime_requested
        and managed_runtime_started
        and map_once_observed
        and map_has_free_cells_for_path_proof(managed_map_analysis)
    )
    if not runtime_map_ready:
        return map_inputs
    effective = dict(map_inputs)
    # canonical map proof 可能是上一轮坏地图状态；本轮 /map 已来自 managed runtime 加载的可用地图。
    effective["root_causes"] = []
    effective["inputs_ready"] = True
    effective["managed_runtime_map_inputs_ready"] = True
    return effective


def resolve_managed_map_yaml(args: argparse.Namespace, map_inputs: dict[str, Any]) -> tuple[str | None, str]:
    """managed runtime 优先用显式 map yaml；缺省时才回退到 canonical artifact。"""
    explicit = str(args.managed_map_yaml or "").strip()
    if explicit:
        path = Path(explicit)
        if path.exists():
            return str(path), "explicit_cli_managed_map_yaml"
        return None, "explicit_cli_managed_map_yaml_missing"
    usable_candidates: list[tuple[int, int, str]] = []
    fallback_candidate: str | None = None
    for candidate in map_inputs.get("map_yaml_candidates") or []:
        path = str(candidate.get("path") or "").strip()
        if not path or not Path(path).exists():
            continue
        if fallback_candidate is None:
            fallback_candidate = path
        analysis = map_yaml_runtime_analysis(path)
        if map_has_free_cells_for_path_proof(analysis):
            cell_counts = analysis.get("cell_counts") if isinstance(analysis.get("cell_counts"), dict) else {}
            usable_candidates.append((int(cell_counts.get("free") or 0), int(candidate.get("mtime_ms") or 0), path))
    if usable_candidates:
        usable_candidates.sort(reverse=True)
        return usable_candidates[0][2], "canonical_map_proof_usable_yaml_candidate"
    if fallback_candidate:
        return fallback_candidate, "canonical_map_proof_yaml_candidate_without_free_cells"
    return None, "canonical_map_yaml_candidate_missing"


def initialpose_request(args: argparse.Namespace) -> dict[str, Any]:
    """把 opt-in 位姿参数固化进 artifact，默认缺省时必须能证明没有发布。"""
    yaw = float(args.initialpose_yaw)
    return {
        "enabled": bool(args.initialpose_opt_in),
        "frame_id": str(args.initialpose_frame_id),
        "x": float(args.initialpose_x),
        "y": float(args.initialpose_y),
        "yaw": yaw,
        # AMCL 初始位姿只需要平面朝向，四元数在这里集中计算以避免 shell 拼错。
        "orientation_z": math.sin(yaw / 2.0),
        "orientation_w": math.cos(yaw / 2.0),
    }


def initialpose_payload(request: dict[str, Any]) -> str:
    """生成 PoseWithCovarianceStamped YAML；协方差保守放宽，只用于定位 proof。"""
    covariance = [0.0] * 36
    covariance[0] = 0.25
    covariance[7] = 0.25
    covariance[35] = 0.06853891945200942
    payload = {
        # stamp=0 让 AMCL/TF 使用最新 transform，避免现场 TF buffer 刚启动时把 initialpose 判成 past extrapolation。
        "header": {"frame_id": request["frame_id"], "stamp": {"sec": 0, "nanosec": 0}},
        "pose": {
            "pose": {
                "position": {"x": request["x"], "y": request["y"], "z": 0.0},
                "orientation": {
                    "x": 0.0,
                    "y": 0.0,
                    "z": request["orientation_z"],
                    "w": request["orientation_w"],
                },
            },
            "covariance": covariance,
        },
    }
    return json.dumps(payload, ensure_ascii=False)


def _ros_python_import_paths() -> list[str]:
    """裸 python 进程在板端启动时补 ROS Python 路径，避免 source 只恢复动态库但漏掉 site-packages。"""
    return [
        "/opt/ros/humble/lib/python3.10/site-packages",
        "/opt/ros/humble/local/lib/python3.10/dist-packages",
        "/root/rober/onboard/install/ros2_trashbot_interfaces/local/lib/python3.10/dist-packages",
    ]


def publish_initialpose_inprocess_burst(
    request: dict[str, Any],
    *,
    wait_subscription_s: float = 2.0,
    publish_attempt_limit: int = 5,
    publish_period_s: float = 0.12,
) -> dict[str, Any]:
    """用进程内 transient-local publisher 稳定发布 `/initialpose`，避免 CLI 冷启动与 QoS 抖动。"""
    result: dict[str, Any] = {
        "command": "rclpy in-process /initialpose burst",
        "executed": True,
        "ok": False,
        "publish_method": "rclpy_inprocess_burst",
        "boundary": "rclpy_initialpose_publish_not_attempted",
        "subscriber_count": None,
        "subscription_match_proven": False,
        "publish_attempts": 0,
        "elapsed_ms": 0,
        "rmw_fastrtps_use_shm": "",
        "fastdds_builtin_transports": "",
        "error": None,
    }
    started_ms = now_ms()
    node = None
    rclpy = None
    rclpy_initialized = False
    for path in _ros_python_import_paths():
        if path not in sys.path:
            sys.path.append(path)
    # Orange Pi / FastDDS SHM 锁文件会让短命 publisher 容易卡死；这里固定走更稳的 UDP 发现。
    for key, value in DDS_NO_SHM_ENV.items():
        os.environ.setdefault(key, value)
    result["rmw_fastrtps_use_shm"] = os.environ.get("RMW_FASTRTPS_USE_SHM", "")
    result["fastdds_builtin_transports"] = os.environ.get("FASTDDS_BUILTIN_TRANSPORTS", "")
    try:
        import rclpy as rclpy_module  # type: ignore[import-not-found]
        from geometry_msgs.msg import PoseWithCovarianceStamped  # type: ignore[import-not-found]
        from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy  # type: ignore[import-not-found]

        rclpy = rclpy_module
    except Exception as exc:  # noqa: BLE001 - ROS Python 环境缺失时必须回退 CLI。
        result["boundary"] = "rclpy_initialpose_import_failed"
        result["error"] = compact_error(exc)
        result["elapsed_ms"] = now_ms() - started_ms
        return result
    try:
        if not rclpy.ok():
            rclpy.init(args=None)
            rclpy_initialized = True
        node = rclpy.create_node("o10_initialpose_publisher")
        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=3,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        publisher = node.create_publisher(PoseWithCovarianceStamped, "/initialpose", qos)
        wait_started = time.monotonic()
        subscriber_count = int(publisher.get_subscription_count())
        while subscriber_count <= 0 and time.monotonic() - wait_started < max(wait_subscription_s, 0.1):
            # graph discovery 需要 spin_once 推进；否则刚起的 AMCL 订阅匹配可能一直看不到。
            rclpy.spin_once(node, timeout_sec=0.05)
            subscriber_count = int(publisher.get_subscription_count())

        message = PoseWithCovarianceStamped()
        message.header.frame_id = str(request["frame_id"])
        # stamp=0 让 AMCL 按 latest TF 处理，避免 proof runtime 刚启动时被过去时间戳卡住。
        message.header.stamp.sec = 0
        message.header.stamp.nanosec = 0
        message.pose.pose.position.x = float(request["x"])
        message.pose.pose.position.y = float(request["y"])
        message.pose.pose.position.z = 0.0
        message.pose.pose.orientation.x = 0.0
        message.pose.pose.orientation.y = 0.0
        message.pose.pose.orientation.z = float(request["orientation_z"])
        message.pose.pose.orientation.w = float(request["orientation_w"])
        covariance = [0.0] * 36
        covariance[0] = 0.25
        covariance[7] = 0.25
        covariance[35] = 0.06853891945200942
        message.pose.covariance = covariance

        publish_attempts = max(int(publish_attempt_limit), 1)
        for index in range(publish_attempts):
            publisher.publish(message)
            result["publish_attempts"] = index + 1
            rclpy.spin_once(node, timeout_sec=0.0)
            subscriber_count = max(subscriber_count, int(publisher.get_subscription_count()))
            if index < publish_attempts - 1:
                time.sleep(max(publish_period_s, 0.02))

        result["subscriber_count"] = subscriber_count
        result["subscription_match_proven"] = subscriber_count > 0
        result["ok"] = bool(result["subscription_match_proven"] and result["publish_attempts"] > 0)
        result["boundary"] = (
            "rclpy_initialpose_publish_observed"
            if result["ok"]
            else "rclpy_initialpose_subscriber_missing_after_wait"
        )
        result["elapsed_ms"] = now_ms() - started_ms
        if not result["ok"]:
            result["error"] = {
                "type": "subscriber_missing",
                "message": "publisher burst completed but /initialpose subscriber match was not proven",
            }
        return result
    except Exception as exc:  # noqa: BLE001 - 现场 ROS graph 异常要结构化返回给 artifact。
        result["boundary"] = "rclpy_initialpose_publish_failed"
        result["error"] = compact_error(exc)
        result["elapsed_ms"] = now_ms() - started_ms
        return result
    finally:
        if node is not None:
            try:
                node.destroy_node()
            except Exception:
                pass
        if rclpy_initialized and rclpy is not None:
            try:
                if rclpy.ok():
                    rclpy.shutdown()
            except Exception:
                pass


def map_yaml_runtime_analysis(map_yaml: str | None) -> dict[str, Any]:
    """轻量解析当前 map yaml/PGM；用于判断 proof 目标是否落在地图范围内。"""
    result: dict[str, Any] = {
        "executed": bool(map_yaml),
        "ok": False,
        "map_yaml": map_yaml,
        "image": None,
        "resolution": None,
        "origin": None,
        "width": None,
        "height": None,
        "bounds": None,
        "cell_counts": {},
        "error": None,
    }
    if not map_yaml:
        result["error"] = {"type": "map_yaml_missing", "message": "managed map yaml is not resolved"}
        return result
    try:
        yaml_path = Path(map_yaml)
        text = yaml_path.read_text(encoding="utf-8", errors="replace")
        image_name = ""
        origin_values: list[float] = []
        resolution: float | None = None
        lines = text.splitlines()
        for index, raw_line in enumerate(lines):
            line = raw_line.strip()
            if line.startswith("image:"):
                image_name = line.split(":", 1)[1].strip().strip("'\"")
            elif line.startswith("resolution:"):
                resolution = float(line.split(":", 1)[1].strip())
            elif line.startswith("origin:"):
                inline = line.split(":", 1)[1].strip()
                if inline.startswith("[") and inline.endswith("]"):
                    origin_values = [float(part.strip()) for part in inline.strip("[]").split(",") if part.strip()]
                else:
                    for offset in range(1, 4):
                        if index + offset < len(lines):
                            value_text = lines[index + offset].strip()
                            if value_text.startswith("-"):
                                value_text = value_text[1:].strip()
                            origin_values.append(float(value_text))
        if resolution is None or len(origin_values) < 2:
            raise ValueError("map yaml missing resolution or origin")
        image_path = (yaml_path.parent / image_name) if image_name else yaml_path.with_suffix(".pgm")
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
        bounds = {
            "min_x": origin_values[0],
            "min_y": origin_values[1],
            "max_x": origin_values[0] + (width * resolution),
            "max_y": origin_values[1] + (height * resolution),
        }
        result.update(
            {
                "ok": True,
                "image": str(image_path),
                "resolution": resolution,
                "origin": origin_values[:3],
                "width": width,
                "height": height,
                "bounds": bounds,
                "cell_counts": {
                    "free": free_cells,
                    "unknown": unknown_cells,
                    "occupied": occupied_cells,
                    "other": len(data) - free_cells - unknown_cells - occupied_cells,
                },
            }
        )
        return result
    except Exception as exc:  # noqa: BLE001 - map 诊断失败不能阻塞已有 proof 主路径。
        result["error"] = compact_error(exc)
        return result


def point_in_map_bounds(x: float, y: float, map_analysis: dict[str, Any]) -> bool:
    """只用 map metadata 判断点是否在地图矩形内；不把 unknown/free 混成安全可行驶。"""
    bounds = map_analysis.get("bounds") if isinstance(map_analysis.get("bounds"), dict) else {}
    return bool(
        map_analysis.get("ok")
        and float(bounds.get("min_x", 0.0)) <= x <= float(bounds.get("max_x", 0.0))
        and float(bounds.get("min_y", 0.0)) <= y <= float(bounds.get("max_y", 0.0))
    )


def map_has_free_cells_for_path_proof(map_analysis: dict[str, Any] | None) -> bool:
    """Nav2 proof 至少要看到 free cell；unknown-only 地图不能被包装成可规划地图。"""
    if not isinstance(map_analysis, dict) or not map_analysis.get("ok"):
        return True
    cell_counts = map_analysis.get("cell_counts") if isinstance(map_analysis.get("cell_counts"), dict) else {}
    return int(cell_counts.get("free") or 0) > 0


def clamp_point_to_map_bounds(x: float, y: float, map_analysis: dict[str, Any]) -> tuple[float, float]:
    """no-motion planner proof 允许把测试点夹到地图内侧，避免固定点因新地图裁剪失效。"""
    bounds = map_analysis.get("bounds") if isinstance(map_analysis.get("bounds"), dict) else {}
    resolution = float(map_analysis.get("resolution") or 0.05)
    margin = max(resolution * 5.0, 0.25)
    min_x = float(bounds["min_x"]) + margin
    max_x = float(bounds["max_x"]) - margin
    min_y = float(bounds["min_y"]) + margin
    max_y = float(bounds["max_y"]) - margin
    if min_x > max_x:
        min_x = max_x = (float(bounds["min_x"]) + float(bounds["max_x"])) / 2.0
    if min_y > max_y:
        min_y = max_y = (float(bounds["min_y"]) + float(bounds["max_y"])) / 2.0
    return min(max(x, min_x), max_x), min(max(y, min_y), max_y)


def adapt_path_request_to_map_bounds(
    request: dict[str, Any],
    *,
    map_analysis: dict[str, Any],
    initialpose_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    """当固定 no-motion 起终点越界时，生成地图内的 planner-only 测试请求。"""
    if not map_analysis.get("ok"):
        request["map_goal_diagnostics"] = {"map_analysis_ok": False, "adapted": False}
        return request
    start_x = float(request.get("start_x", (initialpose_payload or {}).get("x", 0.0)))
    start_y = float(request.get("start_y", (initialpose_payload or {}).get("y", 0.0)))
    goal_x = float(request["x"])
    goal_y = float(request["y"])
    start_in_bounds = point_in_map_bounds(start_x, start_y, map_analysis)
    goal_in_bounds = point_in_map_bounds(goal_x, goal_y, map_analysis)
    diagnostics = {
        "map_analysis_ok": True,
        "adapted": False,
        "start_in_bounds": start_in_bounds,
        "goal_in_bounds": goal_in_bounds,
        "bounds": map_analysis.get("bounds"),
        "cell_counts": map_analysis.get("cell_counts"),
        "original_start": {"x": start_x, "y": start_y},
        "original_goal": {"x": goal_x, "y": goal_y},
    }
    if start_in_bounds and goal_in_bounds:
        request["start_x"] = start_x
        request["start_y"] = start_y
        request["map_goal_diagnostics"] = diagnostics
        return request
    adapted_start_x, adapted_start_y = clamp_point_to_map_bounds(start_x, start_y, map_analysis)
    adapted_goal_x, adapted_goal_y = clamp_point_to_map_bounds(goal_x, goal_y, map_analysis)
    if math.hypot(adapted_goal_x - adapted_start_x, adapted_goal_y - adapted_start_y) < 0.25:
        # 如果起终点被夹到同一小片区域，优先沿 x 方向制造一段仍在地图内的 planner-only 目标。
        bounds = map_analysis.get("bounds") if isinstance(map_analysis.get("bounds"), dict) else {}
        candidate_x = adapted_start_x + 0.8
        if candidate_x > float(bounds.get("max_x", candidate_x)):
            candidate_x = adapted_start_x - 0.8
        adapted_goal_x, adapted_goal_y = clamp_point_to_map_bounds(candidate_x, adapted_start_y, map_analysis)
    request.update(
        {
            "x": adapted_goal_x,
            "y": adapted_goal_y,
            "start_x": adapted_start_x,
            "start_y": adapted_start_y,
            "use_start": True,
            "adapted_from_map_bounds": True,
            "adaptation_boundary": "map_bounds_adapted_no_motion_planner_probe",
            "original_goal": {"x": goal_x, "y": goal_y, "yaw": request["yaw"]},
        }
    )
    diagnostics.update(
        {
            "adapted": True,
            "adaptation_boundary": request["adaptation_boundary"],
            "adapted_start": {"x": adapted_start_x, "y": adapted_start_y},
            "adapted_goal": {"x": adapted_goal_x, "y": adapted_goal_y},
        }
    )
    request["map_goal_diagnostics"] = diagnostics
    return request


def path_generation_request(
    args: argparse.Namespace,
    *,
    map_analysis: dict[str, Any] | None = None,
    initialpose_payload: dict[str, Any] | None = None,
    observed_start_pose: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """路径生成只接受显式 opt-in 的单次目标请求，默认不会进入 planner。"""
    yaw = float(args.path_goal_yaw)
    request = {
        "enabled": bool(args.path_generation_opt_in),
        "frame_id": str(args.path_goal_frame_id),
        "x": float(args.path_goal_x),
        "y": float(args.path_goal_y),
        "yaw": yaw,
        # ComputePathToPose 允许显式 start，但 no-motion proof 优先依赖当前 TF/定位结果。
        "use_start": False,
        "start_x": float(getattr(args, "initialpose_x", 0.0)),
        "start_y": float(getattr(args, "initialpose_y", 0.0)),
        "start_yaw": yaw,
        "start_orientation_z": math.sin(yaw / 2.0),
        "start_orientation_w": math.cos(yaw / 2.0),
        "start_source": "implicit_current_robot_pose_via_tf",
        "planner_id": "",
        "orientation_z": math.sin(yaw / 2.0),
        "orientation_w": math.cos(yaw / 2.0),
    }
    if isinstance(observed_start_pose, dict) and observed_start_pose.get("frame_id") == request["frame_id"]:
        # 板端 TF buffer 窗口较短时，`use_start=false` 会让 planner 在 action 时刻回查
        # base_link->map 并触发 extrapolation；AMCL pose 已是同一 run 的定位证据，可作为
        # ComputePathToPose 的显式起点，仍然只做规划不做控制。
        start_yaw = float(observed_start_pose.get("yaw") or 0.0)
        request.update(
            {
                "use_start": True,
                "start_x": float(observed_start_pose["x"]),
                "start_y": float(observed_start_pose["y"]),
                "start_yaw": start_yaw,
                "start_orientation_z": math.sin(start_yaw / 2.0),
                "start_orientation_w": math.cos(start_yaw / 2.0),
                "start_source": "amcl_pose_observed_for_planner_only_start",
            }
        )
    elif isinstance(observed_start_pose, dict):
        request["start_source"] = "amcl_pose_ignored_frame_mismatch"
    if map_analysis is not None:
        request = adapt_path_request_to_map_bounds(
            request,
            map_analysis=map_analysis,
            initialpose_payload=initialpose_payload,
        )
        cell_counts = map_analysis.get("cell_counts") if isinstance(map_analysis.get("cell_counts"), dict) else {}
        request["map_free_cell_count"] = int(cell_counts.get("free") or 0)
        request["map_has_free_cells_for_path_proof"] = map_has_free_cells_for_path_proof(map_analysis)
    return request


def path_goal_pose(request: dict[str, Any]) -> dict[str, Any]:
    """把 planner 目标整理成 artifact 里的稳定结构，便于远端回放请求内容。"""
    return {
        "frame_id": request["frame_id"],
        "position": {"x": request["x"], "y": request["y"], "z": 0.0},
        "orientation": {
            "x": 0.0,
            "y": 0.0,
            "z": request["orientation_z"],
            "w": request["orientation_w"],
        },
    }


def compact_path_preview_points(path: Any, poses: list[Any], *, limit: int = 64) -> list[dict[str, Any]]:
    """把 Nav2 path 压成可视化预览点，避免 artifact 因完整路线过长而拖慢 PC 首屏。"""
    if not poses or limit <= 0:
        return []
    if len(poses) <= limit:
        indexes = list(range(len(poses)))
    else:
        # 等距抽样并强制保留首尾，PC 端能看到完整路线方向但不会接收超大数组。
        indexes = sorted({round(i * (len(poses) - 1) / (limit - 1)) for i in range(limit)})
    frame_id = getattr(getattr(path, "header", None), "frame_id", None) if path is not None else None
    points: list[dict[str, Any]] = []
    for index in indexes:
        pose_stamped = poses[index]
        pose = getattr(pose_stamped, "pose", None)
        position = getattr(pose, "position", None)
        if position is None:
            continue
        try:
            x = float(getattr(position, "x"))
            y = float(getattr(position, "y"))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(x) or not math.isfinite(y):
            continue
        points.append(
            {
                "x": round(x, 4),
                "y": round(y, 4),
                "frame_id": str(frame_id or ""),
                "source_index": int(index),
            }
        )
    return points


def build_planner_readiness_summary(
    *,
    managed_runtime: dict[str, Any],
    localization_ready: bool,
    planner_server_active: bool,
    planner_server_observed: bool,
    controller_server_requested: bool,
    controller_server_active: bool,
    controller_server_observed: bool,
    path_generation_request: dict[str, Any],
    path_generation_attempted: bool,
    path_generation_succeeded: bool,
    path_point_count: int,
) -> dict[str, Any]:
    """把 planner readiness 压成一份可读摘要，避免下游从顶层布尔值误判可控状态。"""
    return {
        "managed_runtime_requested": bool(managed_runtime.get("requested")),
        "managed_runtime_started": bool(managed_runtime.get("started")),
        "managed_runtime_boundary": managed_runtime.get("boundary"),
        "localization_ready": bool(localization_ready),
        "path_generation_requested": bool(path_generation_request["enabled"]),
        "path_generation_attempted": bool(path_generation_attempted),
        "planner_server_active": bool(planner_server_active),
        "planner_server_observed": bool(planner_server_observed),
        "controller_server_requested": bool(controller_server_requested),
        "controller_server_active": bool(controller_server_active),
        "controller_server_observed": bool(controller_server_observed),
        "path_generation_succeeded": bool(path_generation_succeeded),
        "path_generated": bool(path_generation_succeeded and path_point_count > 0),
        "path_point_count": int(path_point_count),
    }


def normalize_ros_node_name(name: str) -> str:
    """ROS graph 有时带斜杠、有时不带；统一成 `/node` 便于 proof 稳定比较。"""
    stripped = str(name or "").strip()
    if not stripped:
        return ""
    return f"/{stripped.lstrip('/')}"


def node_names_from_graph_result(result: dict[str, Any]) -> set[str]:
    """从 `ros2 node list` 或 rclpy probe 结果里提取规范化节点名。"""
    names: set[str] = set()
    for raw_name in result.get("node_names") or []:
        normalized = normalize_ros_node_name(str(raw_name))
        if normalized:
            names.add(normalized)
    for raw_line in str(result.get("stdout") or "").splitlines():
        normalized = normalize_ros_node_name(raw_line)
        if normalized:
            names.add(normalized)
    return names


def managed_runtime_observed_node_names(managed_runtime: dict[str, Any]) -> set[str]:
    """managed wait 的 history 是最早证据源；即使最终 CLI 超时，也不能丢掉曾观测到的节点。"""
    observed: set[str] = set()
    wait_result = managed_runtime.get("wait_result") or {}
    observed.update(node_names_from_graph_result(wait_result.get("node_list") or {}))
    observed.update(node_names_from_graph_result({"node_names": wait_result.get("observed_node_names") or []}))
    for snapshot in wait_result.get("history") or []:
        if not isinstance(snapshot, dict):
            continue
        observed.update(node_names_from_graph_result({"node_names": snapshot.get("cumulative_node_names") or []}))
        observed.update(node_names_from_graph_result(snapshot.get("node_list_command") or {}))
    return observed


def lifecycle_recheck_observed_node_names(lifecycle_results: dict[str, Any]) -> set[str]:
    """lifecycle retry 自带 graph visibility；planner proof 不能丢掉这条只读节点证据。"""
    observed: set[str] = set()
    for result in lifecycle_results.values():
        if not isinstance(result, dict):
            continue
        containers = [
            result,
            result.get("command_summary") if isinstance(result.get("command_summary"), dict) else {},
            result.get("lifecycle_cli_budget_recovery") if isinstance(result.get("lifecycle_cli_budget_recovery"), dict) else {},
        ]
        for container in containers:
            graph_visibility = container.get("graph_visibility") if isinstance(container.get("graph_visibility"), dict) else {}
            observed.update(node_names_from_graph_result({"node_names": graph_visibility.get("observed_node_names") or []}))
    return observed


def parse_pose_stamped(request: dict[str, Any]) -> str:
    """把 path goal 转成 ROS2 CLI 可读的 PoseStamped JSON，便于 action / CLI 双路径调试。"""
    payload = {
        "header": {"frame_id": request["frame_id"]},
        "pose": {
            "position": {"x": request["x"], "y": request["y"], "z": 0.0},
            "orientation": {
                "x": 0.0,
                "y": 0.0,
                "z": request["orientation_z"],
                "w": request["orientation_w"],
            },
        },
    }
    return json.dumps(payload, ensure_ascii=False)


def maybe_publish_initialpose(args: argparse.Namespace, ros2_ok: bool) -> tuple[dict[str, Any], dict[str, Any]]:
    """显式 opt-in 时只发布一次 /initialpose；默认路径不产生任何额外 ROS 写动作。"""
    request = initialpose_request(args)
    if not request["enabled"]:
        return request, {
            "command": "initialpose opt-in disabled",
            "executed": False,
            "ok": False,
            "publish_method": "disabled",
            "subscriber_count": None,
            "publish_attempts": 0,
            "boundary": "default_read_only_no_initialpose_publish",
        }
    if not ros2_ok:
        return request, {
            "command": "initialpose opt-in requested but ros2 unavailable",
            "executed": False,
            "ok": False,
            "publish_method": "ros2_unavailable",
            "subscriber_count": None,
            "publish_attempts": 0,
            "boundary": "ros2_unavailable_no_initialpose_publish",
        }
    rclpy_publish = publish_initialpose_inprocess_burst(request)
    if rclpy_publish.get("ok"):
        return request, rclpy_publish
    # 唯一允许的写 topic 是 /initialpose；它只给 AMCL 定位种子，不会触发运动执行。
    payload = initialpose_payload(request)
    command = (
        "ros2 topic pub --once /initialpose "
        f"geometry_msgs/msg/PoseWithCovarianceStamped {shlex.quote(payload)}"
    )
    cli_publish = run_ros(args, command, timeout_s=8.0)
    cli_publish.update(
        {
            "publish_method": "ros2_topic_pub_once_cli_fallback",
            "boundary": (
                "cli_initialpose_publish_observed"
                if cli_publish.get("ok")
                else "cli_initialpose_publish_failed"
            ),
            "subscriber_count": rclpy_publish.get("subscriber_count"),
            "subscription_match_proven": bool(rclpy_publish.get("subscription_match_proven")),
            "publish_attempts": int(rclpy_publish.get("publish_attempts") or 0) + 1,
            "elapsed_ms": int(rclpy_publish.get("elapsed_ms") or 0) + int(cli_publish.get("elapsed_ms") or 0),
            "fallback_after_method": rclpy_publish.get("publish_method"),
            "rclpy_attempt": {
                "boundary": rclpy_publish.get("boundary"),
                "subscriber_count": rclpy_publish.get("subscriber_count"),
                "publish_attempts": rclpy_publish.get("publish_attempts"),
                "elapsed_ms": rclpy_publish.get("elapsed_ms"),
                "error": rclpy_publish.get("error"),
            },
        }
    )
    return request, cli_publish


def maybe_compute_path_generation(
    args: argparse.Namespace,
    *,
    ros2_ok: bool,
    localization_ready: bool,
    planner_server_active: bool,
    map_analysis: dict[str, Any] | None = None,
    initialpose_payload: dict[str, Any] | None = None,
    observed_start_pose: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, str]]]:
    """显式 opt-in 时只尝试一次 ComputePathToPose；默认路径不进入 planner/action。"""
    request = path_generation_request(
        args,
        map_analysis=map_analysis,
        initialpose_payload=initialpose_payload,
        observed_start_pose=observed_start_pose,
    )
    if not request["enabled"]:
        return request, {
            "attempted": False,
            "ok": False,
            "boundary": "default_read_only_no_path_generation_attempt",
        }, {
            "attempted": False,
            "ok": False,
            "boundary": "path_generation_opt_in_disabled_no_compute_path_call",
        }, []
    if not ros2_ok:
        return request, {
            "attempted": False,
            "ok": False,
            "boundary": "path_generation_requested_but_ros2_unavailable",
        }, {
            "attempted": False,
            "ok": False,
            "boundary": "path_generation_requested_but_ros2_unavailable",
        }, [{"layer": "ROS install/source", "reason": "ros2_cli_not_ready_for_path_generation"}]
    if not localization_ready:
        return request, {
            "attempted": False,
            "ok": False,
            "boundary": "path_generation_blocked_by_localization_not_ready",
        }, {
            "attempted": False,
            "ok": False,
            "boundary": "path_generation_blocked_by_localization_not_ready",
        }, [{"layer": "planner readiness", "reason": "localization_not_ready_for_path_generation"}]
    if not planner_server_active:
        return request, {
            "attempted": False,
            "ok": False,
            "boundary": "path_generation_blocked_by_planner_server_inactive",
        }, {
            "attempted": False,
            "ok": False,
            "boundary": "path_generation_blocked_by_planner_server_inactive",
        }, [{"layer": "planner readiness", "reason": "planner_server_not_active"}]
    if map_analysis is not None and not map_has_free_cells_for_path_proof(map_analysis):
        # 当前板端 no-motion 地图可能只有 unknown/occupied，没有任何 free cell。
        # 这种地图即使偶发返回 path，也不能代表可导航地图质量；这里在 action 前稳定挡住。
        return request, {
            "attempted": False,
            "ok": False,
            "boundary": "path_generation_blocked_by_map_has_no_free_cells",
            "service_name": None,
            "service_available": False,
            "path_generated": False,
            "path_point_count": 0,
            "path_goal_request": {
                "goal_frame_id": request["frame_id"],
                "goal_x": request["x"],
                "goal_y": request["y"],
                "goal_yaw": request["yaw"],
                "planner_id": request["planner_id"],
                "use_start": request["use_start"],
                "start_x": request.get("start_x"),
                "start_y": request.get("start_y"),
                "start_yaw": request.get("start_yaw"),
                "start_source": request.get("start_source"),
                "adapted_from_map_bounds": bool(request.get("adapted_from_map_bounds")),
                "adaptation_boundary": request.get("adaptation_boundary"),
                "original_goal": request.get("original_goal"),
                "map_goal_diagnostics": request.get("map_goal_diagnostics"),
                "map_free_cell_count": request.get("map_free_cell_count"),
                "map_has_free_cells_for_path_proof": request.get("map_has_free_cells_for_path_proof"),
            },
            "path_goal_response": {
                "accepted": False,
                "result_received": False,
                "blocked_before_action": True,
            },
        }, {
            "attempted": False,
            "ok": False,
            "boundary": "path_generation_blocked_by_map_has_no_free_cells",
        }, [{"layer": "map quality", "reason": "map_has_no_free_cells_for_nav2_path_proof"}]
    try:
        import rclpy
        from geometry_msgs.msg import PoseStamped  # type: ignore[import-not-found]
        from nav2_msgs.action import ComputePathToPose  # type: ignore[import-not-found]
        from rclpy.action import ActionClient  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001 - 现场若缺 ROS Python 依赖，必须把 blocker 写回 artifact。
        error = compact_error(exc)
        boundary = "path_generation_python_runtime_unavailable"
        fallback_result, fallback_causes = compute_path_generation_cli_fallback(
            args,
            request,
            python_import_error=error,
        )
        if fallback_result.get("attempted"):
            return request, fallback_result, {
                "attempted": True,
                "ok": bool(fallback_result.get("ok")),
                "boundary": fallback_result.get("boundary"),
                "fallback_used": True,
                "fallback_after_boundary": boundary,
            }, fallback_causes
        return request, {
            "attempted": True,
            "ok": False,
            "boundary": boundary,
            "error": error,
            "fallback_used": False,
        }, {
            "attempted": True,
            "ok": False,
            "boundary": boundary,
            "error": error,
        }, [{"layer": "ROS python runtime", "reason": f"{error['type']}:{error['message']}"}]

    started_ms = now_ms()
    action_name = ""
    result_payload: dict[str, Any] = {
        "attempted": True,
        "ok": False,
        "boundary": "path_generation_attempt_started",
        "service_name": None,
        "service_available": False,
        "goal_accepted": False,
        "result_received": False,
        "result_ok": False,
        "path_generated": False,
        "path_point_count": 0,
        "path_structured_poses": [],
        "path_structured_pose_count": 0,
        "path_preview_points": [],
        "path_preview_point_count": 0,
        "path_preview_source_point_count": 0,
        "path_preview_frame_id": None,
        "path_goal_request": {
            "goal_frame_id": request["frame_id"],
            "goal_x": request["x"],
            "goal_y": request["y"],
            "goal_yaw": request["yaw"],
            "planner_id": request["planner_id"],
            "use_start": request["use_start"],
            "start_x": request.get("start_x"),
            "start_y": request.get("start_y"),
            "start_yaw": request.get("start_yaw"),
            "start_source": request.get("start_source"),
            "adapted_from_map_bounds": bool(request.get("adapted_from_map_bounds")),
            "adaptation_boundary": request.get("adaptation_boundary"),
            "original_goal": request.get("original_goal"),
            "map_goal_diagnostics": request.get("map_goal_diagnostics"),
        },
        "path_goal_response": {},
        "planning_time_ms": None,
        "elapsed_ms": 0,
        "error": None,
    }

    node = None
    rclpy_initialized = False
    try:
        rclpy.init(args=[])
        rclpy_initialized = True
        node = rclpy.create_node("o10_path_generation_probe")

        def build_goal() -> Any:
            goal_msg = ComputePathToPose.Goal()
            goal_msg.goal = PoseStamped()
            goal_msg.goal.header.frame_id = request["frame_id"]
            goal_msg.goal.pose.position.x = request["x"]
            goal_msg.goal.pose.position.y = request["y"]
            goal_msg.goal.pose.position.z = 0.0
            goal_msg.goal.pose.orientation.x = 0.0
            goal_msg.goal.pose.orientation.y = 0.0
            goal_msg.goal.pose.orientation.z = request["orientation_z"]
            goal_msg.goal.pose.orientation.w = request["orientation_w"]
            goal_msg.start = PoseStamped()
            goal_msg.start.header.frame_id = request["frame_id"]
            goal_msg.start.pose.position.x = float(request.get("start_x", request["x"]))
            goal_msg.start.pose.position.y = float(request.get("start_y", request["y"]))
            goal_msg.start.pose.orientation.z = float(request.get("start_orientation_z", request["orientation_z"]))
            goal_msg.start.pose.orientation.w = float(request.get("start_orientation_w", request["orientation_w"]))
            goal_msg.planner_id = request["planner_id"]
            goal_msg.use_start = bool(request["use_start"])
            return goal_msg

        for candidate in PATH_GENERATION_ACTION_CANDIDATES:
            client = ActionClient(node, ComputePathToPose, candidate)
            if client.wait_for_server(timeout_sec=min(max(float(args.path_generation_timeout_s), 1.0), 5.0)):
                action_name = candidate
                result_payload["service_name"] = candidate
                result_payload["service_available"] = True
                goal_future = client.send_goal_async(build_goal())
                rclpy.spin_until_future_complete(node, goal_future, timeout_sec=max(float(args.path_generation_timeout_s), 5.0))
                goal_handle = goal_future.result()
                if goal_handle is None:
                    result_payload["boundary"] = "path_generation_goal_handle_missing"
                    result_payload["error"] = {"type": "goal_handle_missing", "message": "action goal handle is None"}
                    break
                result_payload["goal_accepted"] = bool(getattr(goal_handle, "accepted", False))
                if not result_payload["goal_accepted"]:
                    result_payload["boundary"] = "path_generation_goal_rejected"
                    result_payload["path_goal_response"] = {"accepted": False}
                    break
                result_future = goal_handle.get_result_async()
                rclpy.spin_until_future_complete(
                    node,
                    result_future,
                    timeout_sec=max(float(args.path_generation_timeout_s), 5.0),
                )
                result = result_future.result()
                if result is None:
                    result_payload["boundary"] = "path_generation_result_missing"
                    result_payload["path_goal_response"] = {"accepted": True, "result_received": False}
                    break
                path = getattr(result.result, "path", None)
                poses = list(getattr(path, "poses", []) or []) if path is not None else []
                planning_time = getattr(result.result, "planning_time", None)
                error_code = getattr(result.result, "error_code", None)
                error_msg = getattr(result.result, "error_msg", None)
                path_preview_points = compact_path_preview_points(path, poses)
                path_frame_id = getattr(path.header, "frame_id", None) if path is not None else None
                planning_time_ms = None
                if planning_time is not None:
                    planning_time_ms = int((float(getattr(planning_time, "sec", 0)) * 1000) + (float(getattr(planning_time, "nanosec", 0)) / 1_000_000.0))
                result_payload.update(
                    {
                        "result_received": True,
                        "result_ok": True,
                        "path_generated": bool(poses),
                        "path_point_count": len(poses),
                        "path_preview_points": path_preview_points,
                        "path_preview_point_count": len(path_preview_points),
                        "path_preview_source_point_count": len(poses),
                        "path_preview_frame_id": path_frame_id,
                        "planning_time_ms": planning_time_ms,
                        "path_goal_response": {
                            "accepted": True,
                            "result_received": True,
                            "path_frame_id": path_frame_id,
                            "path_point_count": len(poses),
                            "path_preview_point_count": len(path_preview_points),
                            "planning_time_ms": planning_time_ms,
                            "error_code": error_code,
                            "error_msg": error_msg,
                        },
                        "planner_error_code": error_code,
                        "planner_error_msg": error_msg,
                    }
                )
                result_payload["boundary"] = "explicit_opt_in_compute_path_to_pose_action_no_motion"
                break
        else:
            result_payload["boundary"] = "path_generation_action_unavailable"
            result_payload["path_goal_response"] = {"accepted": False, "result_received": False}
    except Exception as exc:  # noqa: BLE001 - action/client 失败必须回写结构化 blocker。
        result_payload["boundary"] = "path_generation_attempt_failed"
        result_payload["error"] = compact_error(exc)
    finally:
        result_payload["elapsed_ms"] = now_ms() - started_ms
        result_payload["action_name"] = action_name
        if node is not None:
            try:
                node.destroy_node()
            except Exception:
                pass
        if rclpy_initialized:
            try:
                if rclpy.ok():
                    rclpy.shutdown()
            except Exception:
                pass

    path_generation_causes: list[dict[str, str]] = []
    if not result_payload["service_available"]:
        path_generation_causes.append({"layer": "planner action", "reason": "compute_path_to_pose_action_unavailable"})
    if result_payload["service_available"] and not result_payload["goal_accepted"]:
        path_generation_causes.append({"layer": "planner action", "reason": "compute_path_to_pose_goal_rejected"})
    if result_payload["service_available"] and result_payload["goal_accepted"] and not result_payload["result_received"]:
        path_generation_causes.append({"layer": "planner action", "reason": "compute_path_to_pose_result_missing"})
    if result_payload["service_available"] and result_payload["result_received"] and not result_payload["path_generated"]:
        path_generation_causes.append({"layer": "planner action", "reason": "compute_path_to_pose_empty_path"})
    result_payload["ok"] = bool(result_payload["path_generated"])
    return request, result_payload, {
        "attempted": bool(result_payload["attempted"]),
        "ok": bool(result_payload["ok"]),
        "boundary": result_payload["boundary"],
    }, path_generation_causes


def cli_compute_path_goal_payload(request: dict[str, Any]) -> str:
    """生成 ROS2 CLI 可接受的 ComputePathToPose goal；只包含 planner action 字段。"""
    payload = {
        "goal": {
            "header": {"frame_id": request["frame_id"]},
            "pose": {
                "position": {"x": request["x"], "y": request["y"], "z": 0.0},
                "orientation": {"x": 0.0, "y": 0.0, "z": request["orientation_z"], "w": request["orientation_w"]},
            },
        },
        "start": {
            "header": {"frame_id": request["frame_id"]},
            "pose": {
                "position": {
                    "x": float(request.get("start_x", request["x"])),
                    "y": float(request.get("start_y", request["y"])),
                    "z": 0.0,
                },
                "orientation": {
                    "x": 0.0,
                    "y": 0.0,
                    "z": float(request.get("start_orientation_z", request["orientation_z"])),
                    "w": float(request.get("start_orientation_w", request["orientation_w"])),
                },
            },
        },
        "planner_id": request["planner_id"],
        "use_start": bool(request["use_start"]),
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def compute_path_action_names_from_cli(stdout: str) -> list[str]:
    """解析 `ros2 action list -t`，优先使用现场实际暴露的 ComputePathToPose 名称。"""
    names: list[str] = []
    for raw_line in str(stdout or "").splitlines():
        line = raw_line.strip()
        if "nav2_msgs/action/ComputePathToPose" not in line:
            continue
        name = line.split("[", 1)[0].strip()
        if name and name not in names:
            names.append(name)
    return names


def ordered_compute_path_action_candidates(action_list_result: dict[str, Any]) -> list[str]:
    """现场 action list 成功时按真实 action 名称优先，避免无谓等待不存在的 candidate。"""
    observed = compute_path_action_names_from_cli(str(action_list_result.get("stdout") or ""))
    ordered = [name for name in observed if name]
    for candidate in PATH_GENERATION_ACTION_CANDIDATES:
        if candidate not in ordered:
            ordered.append(candidate)
    return ordered


def cli_path_pose_count(stdout: str) -> int:
    """从 `ros2 action send_goal` 输出里估算 Path.poses 数量；只用于 proof 摘要。"""
    scoped = cli_compute_path_poses_text(stdout)
    count = len(re.findall(r"(?m)^\s*-\s+header\s*:", scoped))
    if count:
        return count
    return len(re.findall(r"(?m)^\s*-\s+pose\s*:", scoped))


def cli_compute_path_poses_text(stdout: str) -> str:
    """只截取 CLI result.path.poses 区段，避免 planning_time/status 被当成 pose 字段。"""
    text = str(stdout or "")
    path_index = text.lower().find("path:")
    scoped = text[path_index:] if path_index >= 0 else text
    poses_index = scoped.lower().find("poses:")
    if poses_index >= 0:
        scoped = scoped[poses_index:]
    end_candidates = [
        index
        for marker in ("\n  planning_time:", "\n  error_code:", "\n  error_msg:", "\nstatus:", "\ngoal finished")
        for index in [scoped.lower().find(marker)]
        if index >= 0
    ]
    if end_candidates:
        scoped = scoped[: min(end_candidates)]
    return scoped


def cli_yamlish_scalar(value: str) -> str:
    """ROS2 CLI 输出接近 YAML；这里只清理标量引号和尾逗号，不引入外部 YAML 依赖。"""
    cleaned = str(value or "").strip().rstrip(",")
    if cleaned in {"''", '""'}:
        return ""
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {"'", '"'}:
        return cleaned[1:-1]
    return cleaned


def cli_yamlish_section(block: str, section_name: str) -> str:
    """按缩进抽取 position/orientation/stamp 小节，兼容 CLI 的 YAML-ish 文本。"""
    lines = str(block or "").splitlines()
    for index, line in enumerate(lines):
        match = re.match(rf"^(\s*){re.escape(section_name)}\s*:\s*(.*)$", line)
        if not match:
            continue
        indent = len(match.group(1).replace("\t", "    "))
        body: list[str] = []
        inline_value = match.group(2).strip()
        if inline_value:
            body.append(inline_value)
        for next_line in lines[index + 1 :]:
            if not next_line.strip():
                continue
            next_indent = len(re.match(r"^(\s*)", next_line).group(1).replace("\t", "    "))
            if next_indent <= indent and not next_line.lstrip().startswith("- "):
                break
            body.append(next_line)
        return "\n".join(body)
    return ""


def cli_yamlish_field(block: str, field_name: str) -> str | None:
    """读取 YAML-ish 小节里的单个标量字段。"""
    pattern = rf"(?m)^\s*{re.escape(field_name)}\s*:\s*(.*?)\s*$"
    match = re.search(pattern, str(block or ""))
    if not match:
        return None
    return cli_yamlish_scalar(match.group(1))


def cli_yamlish_float(block: str, field_name: str) -> float | None:
    """读取浮点字段；非法值返回 None，让调用方保持 fail-closed。"""
    value = cli_yamlish_field(block, field_name)
    if value is None:
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if math.isfinite(parsed) else None


def cli_yamlish_int(block: str, field_name: str) -> int | None:
    """读取整数 stamp 字段，兼容 CLI 输出把数字转成字符串的情况。"""
    value = cli_yamlish_field(block, field_name)
    if value is None:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def cli_path_frame_id(stdout: str) -> str | None:
    """优先读取 path.header.frame_id；单个 pose 缺 frame 时用它补齐来源 frame。"""
    text = str(stdout or "")
    path_index = text.lower().find("path:")
    scoped = text[path_index:] if path_index >= 0 else text
    poses_index = scoped.lower().find("poses:")
    if poses_index >= 0:
        scoped = scoped[:poses_index]
    return cli_yamlish_field(scoped, "frame_id")


def cli_path_pose_blocks(stdout: str) -> list[str]:
    """把 result.path.poses 拆成完整 pose block；截断开头的半个 pose 不会被补造。"""
    lines = cli_compute_path_poses_text(stdout).splitlines()
    starts = [index for index, line in enumerate(lines) if re.match(r"^\s*-\s+(header|pose)\s*:", line)]
    blocks: list[str] = []
    for offset, start in enumerate(starts):
        end = starts[offset + 1] if offset + 1 < len(starts) else len(lines)
        block = "\n".join(lines[start:end]).strip()
        if block:
            blocks.append(block)
    return blocks


def parse_cli_path_structured_poses(stdout: str) -> list[dict[str, Any]]:
    """从完整 CLI path 输出解析结构化 pose；不能从截断 tail 里推测缺失点。"""
    default_frame_id = cli_path_frame_id(stdout)
    poses: list[dict[str, Any]] = []
    for source_index, block in enumerate(cli_path_pose_blocks(stdout)):
        position = cli_yamlish_section(block, "position")
        orientation = cli_yamlish_section(block, "orientation")
        stamp_block = cli_yamlish_section(block, "stamp")
        x = cli_yamlish_float(position, "x")
        y = cli_yamlish_float(position, "y")
        if x is None or y is None:
            continue
        z = cli_yamlish_float(position, "z")
        qx = cli_yamlish_float(orientation, "x")
        qy = cli_yamlish_float(orientation, "y")
        qz = cli_yamlish_float(orientation, "z")
        qw = cli_yamlish_float(orientation, "w")
        sec = cli_yamlish_int(stamp_block, "sec")
        nanosec = cli_yamlish_int(stamp_block, "nanosec")
        pose: dict[str, Any] = {
            "source_index": int(source_index),
            "frame_id": cli_yamlish_field(block, "frame_id") or default_frame_id,
            "x": float(x),
            "y": float(y),
            "z": float(z) if z is not None else 0.0,
            "qx": float(qx) if qx is not None else 0.0,
            "qy": float(qy) if qy is not None else 0.0,
            "qz": float(qz) if qz is not None else 0.0,
            "qw": float(qw) if qw is not None else 1.0,
        }
        if sec is not None or nanosec is not None:
            pose["stamp"] = {"sec": int(sec or 0), "nanosec": int(nanosec or 0)}
        poses.append(pose)
    return poses


def compact_cli_structured_path_preview_points(
    structured_poses: list[dict[str, Any]],
    *,
    limit: int = 64,
) -> list[dict[str, Any]]:
    """从结构化 pose 生成轻量 preview；preview 不能比真实解析出的 pose 更多。"""
    if not structured_poses or limit <= 0:
        return []
    if len(structured_poses) <= limit:
        indexes = list(range(len(structured_poses)))
    else:
        indexes = sorted({round(i * (len(structured_poses) - 1) / (limit - 1)) for i in range(limit)})
    preview: list[dict[str, Any]] = []
    for index in indexes:
        pose = structured_poses[index]
        x = pose.get("x")
        y = pose.get("y")
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            continue
        preview.append(
            {
                "x": round(float(x), 4),
                "y": round(float(y), 4),
                "frame_id": str(pose.get("frame_id") or ""),
                "source_index": int(pose.get("source_index") or index),
            }
        )
    return preview


def parse_cli_compute_path_result(command_result: dict[str, Any], *, action_name: str) -> dict[str, Any]:
    """把 CLI action 输出压缩成和 Python ActionClient 兼容的 path proof 字段。"""
    stdout = str(command_result.get("stdout") or "")
    stderr = str(command_result.get("stderr") or "")
    combined = f"{stdout}\n{stderr}"
    lower = combined.lower()
    structured_poses = parse_cli_path_structured_poses(stdout)
    path_point_count = max(cli_path_pose_count(stdout), len(structured_poses))
    path_preview_points = compact_cli_structured_path_preview_points(structured_poses)
    path_preview_frame_id = None
    if structured_poses:
        path_preview_frame_id = structured_poses[0].get("frame_id")
    goal_rejected = "goal rejected" in lower or "rejected" in lower and "goal accepted" not in lower
    goal_accepted = ("goal accepted" in lower or "accepted: true" in lower or path_point_count > 0) and not goal_rejected
    result_received = path_point_count > 0 or "result:" in lower or "\nresult:" in lower
    runtime_unavailable = any(token in combined for token in ("librcl_action.so", "_rclpy_pybind11", "ImportError"))
    timed_out = bool(command_result.get("timed_out")) or int(command_result.get("returncode") or 0) == 124
    error_code_match = re.search(r"(?m)^\s*error_code:\s*([0-9]+)", stdout)
    error_msg_match = re.search(r"(?m)^\s*error_msg:\s*['\"]?([^'\"\n]*)", stdout)
    status_match = re.search(r"(?m)^\s*status:\s*([A-Z_0-9]+)", stdout)
    if runtime_unavailable:
        boundary = "path_generation_cli_action_runtime_unavailable"
    elif goal_rejected:
        boundary = "path_generation_cli_action_goal_rejected"
    elif path_point_count > 0:
        boundary = "explicit_opt_in_compute_path_to_pose_cli_action_no_motion"
    elif timed_out:
        boundary = "path_generation_cli_action_timeout"
    elif result_received:
        boundary = "path_generation_cli_action_empty_path"
    elif not command_result.get("ok"):
        boundary = "path_generation_cli_action_command_failed"
    else:
        boundary = "path_generation_cli_action_result_missing"
    return {
        "action_name": action_name,
        "command": command_result.get("command"),
        "returncode": command_result.get("returncode"),
        "timed_out": timed_out,
        "elapsed_ms": command_result.get("elapsed_ms"),
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-2000:],
        "boundary": boundary,
        "runtime_unavailable": runtime_unavailable,
        "goal_accepted": goal_accepted,
        "goal_rejected": goal_rejected,
        "result_received": result_received,
        "path_generated": path_point_count > 0,
        "path_point_count": path_point_count,
        "path_structured_poses": structured_poses,
        "path_structured_pose_count": len(structured_poses),
        "path_preview_points": path_preview_points,
        "path_preview_point_count": len(path_preview_points),
        "path_preview_source_point_count": len(structured_poses),
        "path_preview_frame_id": path_preview_frame_id,
        "status": status_match.group(1) if status_match else None,
        "planner_error_code": int(error_code_match.group(1)) if error_code_match else None,
        "planner_error_msg": error_msg_match.group(1).strip() if error_msg_match else None,
    }


def compute_path_generation_cli_fallback(
    args: argparse.Namespace,
    request: dict[str, Any],
    *,
    python_import_error: dict[str, str],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Python ActionClient import 失败时，改走 sourced ROS2 CLI action；仍只调用 ComputePathToPose。"""
    started_ms = now_ms()
    cli_timeout_s = max(float(args.path_generation_timeout_s), 5.0)
    # 每条 CLI 用 GNU timeout 做内层硬边界，外层 run_ros 留清理余量，避免 action client 残留。
    command_timeout_s = cli_timeout_s + 4.0
    action_list = run_ros(args, "ros2 action list -t", timeout_s=min(command_timeout_s, 10.0))
    observed_actions = compute_path_action_names_from_cli(str(action_list.get("stdout") or ""))
    attempts: list[dict[str, Any]] = []
    result_payload: dict[str, Any] = {
        "attempted": True,
        "ok": False,
        "boundary": "path_generation_cli_action_fallback_started",
        "service_name": None,
        "service_available": False,
        "goal_accepted": False,
        "result_received": False,
        "result_ok": False,
        "path_generated": False,
        "path_point_count": 0,
        "path_structured_poses": [],
        "path_structured_pose_count": 0,
        "path_preview_points": [],
        "path_preview_point_count": 0,
        "path_preview_source_point_count": 0,
        "path_preview_frame_id": request["frame_id"],
        "path_goal_request": {
            "goal_frame_id": request["frame_id"],
            "goal_x": request["x"],
            "goal_y": request["y"],
            "goal_yaw": request["yaw"],
            "planner_id": request["planner_id"],
            "use_start": request["use_start"],
            "start_x": request.get("start_x"),
            "start_y": request.get("start_y"),
            "start_yaw": request.get("start_yaw"),
            "start_source": request.get("start_source"),
            "adapted_from_map_bounds": bool(request.get("adapted_from_map_bounds")),
            "adaptation_boundary": request.get("adaptation_boundary"),
            "original_goal": request.get("original_goal"),
            "map_goal_diagnostics": request.get("map_goal_diagnostics"),
        },
        "path_goal_response": {},
        "planning_time_ms": None,
        "elapsed_ms": 0,
        "error": python_import_error,
        "fallback_used": True,
        "fallback_mode": "ros2_cli_action_send_goal",
        "fallback_after_boundary": "path_generation_python_runtime_unavailable",
        "python_import_error": python_import_error,
        "action_list": {
            "ok": bool(action_list.get("ok")),
            "timed_out": bool(action_list.get("timed_out")),
            "returncode": action_list.get("returncode"),
            "observed_compute_path_actions": observed_actions,
            "stdout_tail": str(action_list.get("stdout") or "")[-2000:],
            "stderr_tail": str(action_list.get("stderr") or "")[-1000:],
        },
        "fallback_attempts": attempts,
    }
    if action_list.get("ok") and not observed_actions:
        result_payload["boundary"] = "path_generation_cli_action_unavailable"
        result_payload["elapsed_ms"] = now_ms() - started_ms
        return result_payload, [{"layer": "planner action", "reason": "compute_path_to_pose_action_unavailable"}]

    goal_payload = cli_compute_path_goal_payload(request)
    for action_name in ordered_compute_path_action_candidates(action_list):
        command = (
            f"timeout {cli_timeout_s:g} "
            f"ros2 action send_goal {shlex.quote(action_name)} "
            f"nav2_msgs/action/ComputePathToPose {shlex.quote(goal_payload)}"
        )
        command_result = run_ros(args, command, timeout_s=command_timeout_s)
        parsed = parse_cli_compute_path_result(command_result, action_name=action_name)
        attempts.append(parsed)
        result_payload["service_name"] = action_name
        result_payload["service_available"] = bool(
            parsed["goal_accepted"]
            or parsed["result_received"]
            or parsed["path_generated"]
            or action_name in observed_actions
        )
        result_payload["goal_accepted"] = bool(parsed["goal_accepted"])
        result_payload["result_received"] = bool(parsed["result_received"])
        result_payload["result_ok"] = bool(parsed["path_generated"])
        result_payload["path_generated"] = bool(parsed["path_generated"])
        result_payload["path_point_count"] = int(parsed["path_point_count"])
        result_payload["path_structured_poses"] = parsed["path_structured_poses"]
        result_payload["path_structured_pose_count"] = int(parsed["path_structured_pose_count"])
        result_payload["path_preview_points"] = parsed["path_preview_points"]
        result_payload["path_preview_point_count"] = int(parsed["path_preview_point_count"])
        result_payload["path_preview_source_point_count"] = int(parsed["path_preview_source_point_count"])
        result_payload["path_preview_frame_id"] = parsed["path_preview_frame_id"] or request["frame_id"]
        result_payload["path_goal_response"] = {
            "accepted": bool(parsed["goal_accepted"]),
            "result_received": bool(parsed["result_received"]),
            "path_frame_id": result_payload["path_preview_frame_id"] if parsed["path_generated"] else None,
            "path_point_count": int(parsed["path_point_count"]),
            "path_structured_pose_count": int(parsed["path_structured_pose_count"]),
            "path_structured_poses": parsed["path_structured_poses"],
            "path_preview_points": parsed["path_preview_points"],
            "path_preview_point_count": int(parsed["path_preview_point_count"]),
            "path_preview_source_point_count": int(parsed["path_preview_source_point_count"]),
            "planner_error_code": parsed["planner_error_code"],
            "planner_error_msg": parsed["planner_error_msg"],
            "status": parsed["status"],
            "runtime_unavailable": bool(parsed["runtime_unavailable"]),
        }
        result_payload["boundary"] = str(parsed["boundary"])
        result_payload["planner_error_code"] = parsed["planner_error_code"]
        result_payload["planner_error_msg"] = parsed["planner_error_msg"]
        if parsed["path_generated"]:
            break
        if parsed["runtime_unavailable"]:
            break
        if action_name in observed_actions:
            # action list 已确认该 server；失败已足够具体，不再让后续别名重复超时。
            break

    result_payload["elapsed_ms"] = now_ms() - started_ms
    result_payload["ok"] = bool(result_payload["path_generated"])
    if result_payload["ok"]:
        result_payload["boundary"] = "explicit_opt_in_compute_path_to_pose_cli_action_no_motion"
        return result_payload, []
    boundary = str(result_payload.get("boundary") or "")
    if boundary == "path_generation_cli_action_runtime_unavailable":
        return result_payload, [{"layer": "planner CLI action runtime", "reason": "compute_path_to_pose_cli_action_runtime_unavailable"}]
    if boundary == "path_generation_cli_action_unavailable" or not result_payload.get("service_available"):
        return result_payload, [{"layer": "planner action", "reason": "compute_path_to_pose_action_unavailable"}]
    if boundary == "path_generation_cli_action_goal_rejected":
        return result_payload, [{"layer": "planner action", "reason": "compute_path_to_pose_goal_rejected"}]
    if boundary == "path_generation_cli_action_timeout":
        return result_payload, [{"layer": "planner CLI action", "reason": "compute_path_to_pose_cli_action_timeout"}]
    if boundary == "path_generation_cli_action_empty_path":
        return result_payload, [{"layer": "planner action", "reason": "compute_path_to_pose_empty_path"}]
    return result_payload, [{"layer": "planner CLI action", "reason": "compute_path_to_pose_cli_action_result_missing"}]


def text_contains_any(text: str, needles: list[str]) -> bool:
    """字符串匹配统一转小写，避免 ROS2 CLI 输出大小写差异带来误判。"""
    lowered = text.lower()
    return any(needle.lower() in lowered for needle in needles)


def topic_once_observed(result: dict[str, Any]) -> bool:
    """topic echo 成功且有正文才算 observed，timeout 空结果不能默认为真。"""
    return bool(result.get("ok") and str(result.get("stdout") or "").strip())


def probe_attempt_artifact(
    result: dict[str, Any],
    *,
    label: str,
    source: str,
    qos_profile: str | None = None,
) -> dict[str, Any]:
    """把单次 probe 封成稳定摘要，便于 artifact 区分 QoS、来源与 timeout。"""
    artifact = {
        "label": label,
        "source": source,
        "qos_profile": qos_profile,
        "command": result.get("command"),
        "executed": bool(result.get("executed")),
        "ok": bool(result.get("ok")),
        "observed": topic_once_observed(result),
        "returncode": result.get("returncode"),
        "elapsed_ms": result.get("elapsed_ms"),
        "timeout_s": result.get("timeout_s"),
        "timed_out": bool(result.get("timed_out") or result.get("returncode") == 124),
        "boundary": result.get("boundary"),
        "error": result.get("error") if isinstance(result.get("error"), dict) else None,
    }
    for optional_key in (
        "runtime",
        "runtime_diagnostics",
        "import_check",
        "environment_check",
        "fallback_boundary",
        "frame_observed",
        "frame_stamp",
        "endpoint_inventory",
        "child_runtime",
        "requested_qos_profile",
        "sample_timing",
    ):
        if result.get(optional_key) is not None:
            artifact[optional_key] = result.get(optional_key)
    return artifact


def build_scan_probe_attempts(args: argparse.Namespace) -> list[dict[str, Any]]:
    """`/scan` 优先保留 child rclpy 的 BEST_EFFORT/RELIABLE 对照，再回退 CLI。"""
    cli_timeout_s = max(float(args.timeout_s), 6.0)
    child_timeout_s = max(float(args.timeout_s), 2.2)
    return [
        {
            "label": "rclpy_best_effort_once",
            "source": "rclpy_subscription",
            "qos_profile": "best_effort",
            "runtime": "ros_sourced_child_python",
            "timeout_s": child_timeout_s,
            "profile_label": "sensor_data_best_effort",
            "reliability": "BEST_EFFORT",
            "durability": "VOLATILE",
        },
        {
            "label": "rclpy_reliable_once",
            "source": "rclpy_subscription",
            "qos_profile": "reliable",
            "runtime": "ros_sourced_child_python",
            "timeout_s": child_timeout_s,
            "profile_label": "reliable_volatile",
            "reliability": "RELIABLE",
            "durability": "VOLATILE",
        },
        {
            "label": "cli_sensor_data_echo_once",
            "source": "ros2_topic_echo_cli",
            "qos_profile": "sensor_data",
            "command": "timeout 6 ros2 topic echo /scan --qos-profile sensor_data --once",
            "timeout_s": cli_timeout_s,
        },
        {
            "label": "cli_default_echo_once",
            "source": "ros2_topic_echo_cli",
            "qos_profile": "default",
            "command": "timeout 6 ros2 topic echo --once /scan",
            "timeout_s": cli_timeout_s,
        },
    ]


def tf_echo_transform_observed(result: dict[str, Any]) -> bool:
    """tf2_echo 会被 timeout 结束；只要已有完整 transform 且无 lookup 失败即可采信。"""
    text = f"{result.get('stdout') or ''}\n{result.get('stderr') or ''}".strip()
    if not text:
        return False
    lowered = text.lower()
    # tf2_echo 常见模式是先打印 waiting，再在同一窗口内输出真正的 transform。
    # 只要已经出现完整平移/旋转，就应认定本轮观测成功，不能被早期等待日志覆盖。
    has_translation = "translation:" in lowered or "transform.translation" in lowered
    has_rotation = "rotation:" in lowered or "transform.rotation" in lowered
    if has_translation and has_rotation:
        return True
    failure_needles = [
        "could not transform",
        "lookup would require extrapolation",
        "lookup exception",
        "connectivity exception",
        "extrapolation exception",
        "invalid frame id",
        "frame does not exist",
        "does not exist",
        "unable to transform",
        "waiting for transform",
        "failure at",
    ]
    if text_contains_any(lowered, failure_needles):
        return False
    return bool(has_translation and has_rotation)


def parse_tf_echo_transform(result: dict[str, Any], *, parent_frame_id: str, child_frame_id: str) -> dict[str, Any] | None:
    """从 tf2_echo 文本提取 2D 外参；没有完整数值时不返回默认偏移。"""
    if not tf_echo_transform_observed(result):
        return None
    text = str(result.get("stdout") or "")
    translation_match = re.search(r"Translation:\s*\[([^\]]+)\]", text)
    rotation_match = re.search(r"Rotation:[^\[]*\[([^\]]+)\]", text)
    if not translation_match or not rotation_match:
        return None
    try:
        translation_values = [float(value.strip()) for value in translation_match.group(1).split(",")]
        rotation_values = [float(value.strip()) for value in rotation_match.group(1).split(",")]
    except ValueError:
        return None
    if len(translation_values) < 2 or len(rotation_values) < 4:
        return None
    qx, qy, qz, qw = rotation_values[:4]
    yaw = math.atan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz))
    return {
        "parent_frame_id": parent_frame_id,
        "child_frame_id": child_frame_id,
        "translation": {"x": translation_values[0], "y": translation_values[1], "z": translation_values[2] if len(translation_values) > 2 else 0.0},
        "rotation": {"yaw": yaw, "quaternion": {"x": qx, "y": qy, "z": qz, "w": qw}},
        "source": "tf2_echo",
    }


def default_tf_chain_observed() -> dict[str, bool]:
    """TF 链字段必须稳定，partial/final/upper readback 都使用同一组键。"""
    return {key: False for key in TF_CHAIN_KEYS}


def tf_probe_result_reason(result: dict[str, Any]) -> str:
    """把 tf2_echo 失败压成下一层原因，避免所有失败都落成同一个 unknown。"""
    text = f"{result.get('stdout') or ''}\n{result.get('stderr') or ''}".lower()
    if tf_echo_transform_observed(result):
        return "observed"
    # 命名或发布源不一致时，tf2_echo 会明确提示 frame 不存在；这类问题优先于 timeout。
    if any(needle in text for needle in ("invalid frame id", "frame does not exist", "does not exist")):
        return "frame_missing_or_name_mismatch"
    if "lookup would require extrapolation" in text or "extrapolation exception" in text:
        return "tf2_extrapolation_or_clock_timing"
    if "connectivity exception" in text or "could not transform" in text or "unable to transform" in text:
        return "tf2_connectivity_gap"
    if result.get("returncode") == 124 or result.get("error"):
        return "tf2_timeout_or_timing"
    if not str(result.get("stdout") or result.get("stderr") or "").strip():
        return "tf2_empty_output_or_timing"
    return "tf2_unclassified_failure"


def tf_chain_frame_contract(args: argparse.Namespace) -> dict[str, Any]:
    """记录 helper 实际使用的 frame，便于区分链路缺失和 frame 命名不一致。"""
    map_frame = "map"
    odom_frame = str(args.managed_odom_frame_id)
    base_frame = str(args.managed_base_frame_id)
    laser_frame = str(args.managed_laser_frame_id)
    expected = {
        "map": "map",
        "odom": DEFAULT_MANAGED_ODOM_FRAME_ID,
        "base": DEFAULT_MANAGED_BASE_FRAME_ID,
        "laser": DEFAULT_MANAGED_LASER_FRAME_ID,
    }
    actual = {"map": map_frame, "odom": odom_frame, "base": base_frame, "laser": laser_frame}
    return {
        "expected": expected,
        "actual": actual,
        "consistent_with_defaults": actual == expected,
    }


def extract_section(text: str, marker: str) -> str:
    """组合诊断命令用 marker 分段；解析失败返回空串，避免误用相邻段内容。"""
    token = f"__{marker}__"
    start = text.find(token)
    if start < 0:
        return ""
    rest = text[start + len(token) :]
    # `__PARAM__` 是参数行前缀，不是段 marker；这里只识别固定的大段分隔符。
    next_positions = [
        position
        for section in ("TOPIC_LIST_T", "AMCL_NODE_INFO", "AMCL_PARAMS", "TF_ONCE", "TF_STATIC_ONCE")
        if section != marker
        for position in [rest.find(f"\n__{section}__")]
        if position >= 0
    ]
    if next_positions:
        rest = rest[: min(next_positions)]
    return rest.strip()


def parse_topic_list_with_types(text: str) -> dict[str, str]:
    """解析 `ros2 topic list -t`，只用于确认 /tf 与 /tf_static 是否在 graph 中。"""
    topics: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("/"):
            continue
        if "[" in line and "]" in line:
            topic, type_text = line.split("[", 1)
            topics[topic.strip()] = type_text.split("]", 1)[0].strip()
        else:
            topics[line] = ""
    return topics


def qos_policy_to_artifact(value: Any) -> Any:
    """QoS policy 只保留可读枚举名，避免不同 rclpy 版本的对象 repr 污染 artifact。"""
    if value is None:
        return None
    name = getattr(value, "name", None)
    if name is not None:
        return str(name)
    try:
        return int(value)
    except (TypeError, ValueError):
        return str(value)


def qos_profile_to_artifact(qos_profile: Any) -> dict[str, Any] | None:
    """端点 QoS 是本轮分类依据；字段缺失时保守返回 None，而不是伪造默认值。"""
    if qos_profile is None:
        return None
    artifact: dict[str, Any] = {}
    for key in ("reliability", "durability", "history", "liveliness"):
        if hasattr(qos_profile, key):
            artifact[key] = qos_policy_to_artifact(getattr(qos_profile, key))
    for key in ("depth", "deadline", "lifespan", "liveliness_lease_duration"):
        if hasattr(qos_profile, key):
            artifact[key] = qos_policy_to_artifact(getattr(qos_profile, key))
    return artifact or None


def endpoint_info_to_artifact(endpoint: Any) -> dict[str, Any]:
    """ROS endpoint 只保留节点名、命名空间、类型和最小 QoS，避免泄露 GID 等低价值细节。"""
    return {
        "node_name": str(getattr(endpoint, "node_name", "") or ""),
        "node_namespace": str(getattr(endpoint, "node_namespace", "") or ""),
        "topic_type": str(getattr(endpoint, "topic_type", "") or ""),
        "qos_profile": qos_profile_to_artifact(getattr(endpoint, "qos_profile", None)),
    }


def topic_endpoint_summary(node: Any, topic: str) -> dict[str, Any]:
    """同一 rclpy graph pass 内读取 topic 端点，给 freshness root-cause 区分无 topic 与无 publisher。"""
    summary: dict[str, Any] = {
        "publishers": [],
        "subscribers": [],
        "publisher_count": 0,
        "subscriber_count": 0,
        "inventory_observed": False,
        "error": None,
    }
    try:
        publishers = [endpoint_info_to_artifact(endpoint) for endpoint in node.get_publishers_info_by_topic(topic)]
        subscribers = [endpoint_info_to_artifact(endpoint) for endpoint in node.get_subscriptions_info_by_topic(topic)]
        summary.update(
            {
                "publishers": publishers,
                "subscribers": subscribers,
                "publisher_count": len(publishers),
                "subscriber_count": len(subscribers),
                "inventory_observed": True,
            }
        )
    except Exception as exc:  # noqa: BLE001 - graph API 失败不能阻断 TF/source 采样。
        summary["error"] = compact_error(exc)
    return summary


def signal_topic_endpoint_summaries(node: Any) -> dict[str, Any]:
    """只采本轮关心的定位信号，避免把整张 ROS graph 泄进 artifact。"""
    return {topic: topic_endpoint_summary(node, topic) for topic in LOCALIZATION_SIGNAL_TOPICS}


def endpoint_node_full_name(endpoint: dict[str, Any]) -> str:
    """把 graph endpoint 的 namespace/name 规范成 ROS 全名，避免根命名空间出现双斜杠。"""
    namespace = str(endpoint.get("node_namespace") or "/").strip()
    node_name = str(endpoint.get("node_name") or "").strip().strip("/")
    if not node_name:
        return ""
    if namespace in {"", "/"}:
        return f"/{node_name}"
    return f"/{namespace.strip('/')}/{node_name}"


def endpoint_identity(endpoint: dict[str, Any]) -> tuple[str, str, str, str]:
    """端点去重只比较可审计字段；QoS 纳入身份可保留同节点异常重复端点。"""
    qos = endpoint.get("qos_profile") if isinstance(endpoint.get("qos_profile"), dict) else {}
    return (
        endpoint_node_full_name(endpoint),
        str(endpoint.get("topic_type") or ""),
        str(qos.get("reliability") or ""),
        str(qos.get("durability") or ""),
    )


def normalize_publisher_endpoint(endpoint: dict[str, Any], *, source_topic: str) -> dict[str, Any]:
    """publisher endpoint 补 source topic/full name，供 artifact 直接建立 edge-to-source 关联。"""
    normalized = {
        "node_name": str(endpoint.get("node_name") or ""),
        "node_namespace": str(endpoint.get("node_namespace") or ""),
        "node_full_name": endpoint_node_full_name(endpoint),
        "topic_type": str(endpoint.get("topic_type") or ""),
        "qos_profile": endpoint.get("qos_profile") if isinstance(endpoint.get("qos_profile"), dict) else None,
        "source_topic": source_topic,
    }
    return normalized


def tf_map_to_odom_publisher_attribution(
    *,
    dynamic_source_observed: bool,
    tf_endpoint_summary: dict[str, Any],
    amcl_publishers: list[dict[str, Any]],
) -> dict[str, Any]:
    """用 `/amcl` node graph 与 `/tf` endpoint 的交集归因，绝不把其他 TF publisher 冒充 AMCL。"""
    raw_publishers = tf_endpoint_summary.get("publishers") if isinstance(tf_endpoint_summary.get("publishers"), list) else []
    endpoints: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for raw_endpoint in raw_publishers:
        if not isinstance(raw_endpoint, dict):
            continue
        endpoint = normalize_publisher_endpoint(raw_endpoint, source_topic="/tf")
        identity = endpoint_identity(endpoint)
        if identity in seen:
            continue
        seen.add(identity)
        endpoints.append(endpoint)
    # `/amcl` node info 明确列出 `/tf` 才能建立交集；只看 endpoint 节点名会把同名残留误归因。
    amcl_tf_publishers = [
        publisher
        for publisher in amcl_publishers
        if isinstance(publisher, dict)
        and str(publisher.get("topic") or "") == "/tf"
        and str(publisher.get("type") or "") in {"", "tf2_msgs/msg/TFMessage"}
    ]
    matching = [endpoint for endpoint in endpoints if endpoint.get("node_full_name") == "/amcl"]
    base = {
        "source_topic": "/tf" if dynamic_source_observed else None,
        "dynamic_source_observed": bool(dynamic_source_observed),
        "publisher_endpoint_inventory_observed": bool(tf_endpoint_summary.get("inventory_observed")),
        "publisher_endpoint_count": int(tf_endpoint_summary.get("publisher_count") or len(endpoints)),
        "publisher_endpoint_candidates": endpoints,
        "amcl_node_tf_publisher_observed": bool(amcl_tf_publishers),
        "amcl_node_tf_publishers": amcl_tf_publishers,
        "publisher_endpoint": None,
    }
    if not dynamic_source_observed:
        return {
            **base,
            "publisher_attribution_status": "not_attributed_dynamic_map_to_odom_not_observed",
            "publisher_attribution_reason": "dynamic_map_to_odom_edge_missing_from_current_tf_sample",
        }
    if not tf_endpoint_summary.get("inventory_observed"):
        return {
            **base,
            "publisher_attribution_status": "unavailable_tf_publisher_endpoint_inventory_not_observed",
            "publisher_attribution_reason": "tf_graph_endpoint_inventory_not_observed_in_current_window",
        }
    if not amcl_tf_publishers:
        return {
            **base,
            "publisher_attribution_status": "unavailable_amcl_tf_publisher_not_observed_in_node_graph",
            "publisher_attribution_reason": "amcl_node_graph_did_not_list_tf_publisher",
        }
    if len(matching) == 1:
        return {
            **base,
            "publisher_attribution_status": "attributed_to_amcl_graph_endpoint",
            "publisher_attribution_reason": "unique_amcl_tf_endpoint_matches_amcl_node_publisher_inventory",
            "publisher_endpoint": matching[0],
        }
    if len(matching) > 1:
        return {
            **base,
            "publisher_attribution_status": "ambiguous_multiple_amcl_tf_publisher_endpoints",
            "publisher_attribution_reason": "multiple_amcl_named_tf_endpoints_prevent_unique_attribution",
            "publisher_endpoint_candidates": matching,
        }
    return {
        **base,
        "publisher_attribution_status": "unmatched_amcl_endpoint_not_present_in_tf_inventory",
        "publisher_attribution_reason": "amcl_lists_tf_but_tf_endpoint_inventory_has_no_amcl_identity",
    }


def parse_tf_edges(text: str, *, source_topic: str) -> list[dict[str, str]]:
    """从 TFMessage echo 文本中提取 parent->child；只看 frame_id/child_frame_id。"""
    edges: list[dict[str, str]] = []
    for block in text.split("- header:"):
        parent_match = None
        child_match = None
        for line in block.splitlines():
            stripped = line.strip().strip("'\"")
            if stripped.startswith("frame_id:"):
                parent_match = stripped.split(":", 1)[1].strip().strip("'\"")
            if stripped.startswith("child_frame_id:"):
                child_match = stripped.split(":", 1)[1].strip().strip("'\"")
        if parent_match and child_match:
            edges.append({"parent": parent_match, "child": child_match, "topic": source_topic})
    return edges


def ros_stamp_parts_to_artifact(sec: int, nanosec: int, *, source: str) -> dict[str, Any]:
    """把 ROS stamp 统一转成 JSON 字段；freshness 判断再单独处理墙钟/仿真时钟。"""
    epoch_ms = int(sec * 1000 + nanosec / 1_000_000)
    return {
        "parsed": True,
        "sec": sec,
        "nanosec": nanosec,
        "epoch_ms": epoch_ms,
        "source": source,
    }


def ros_message_stamp_to_artifact(stamp: Any, *, source: str) -> dict[str, Any]:
    """从 rclpy message header.stamp 提取秒/纳秒；缺字段时保持 unknown。"""
    try:
        sec = int(getattr(stamp, "sec"))
        nanosec = int(getattr(stamp, "nanosec"))
    except (TypeError, ValueError, AttributeError):
        return {"parsed": False, "reason": "stamp_fields_missing", "source": source}
    return ros_stamp_parts_to_artifact(sec, nanosec, source=source)


def parse_first_ros_stamp(text: str, *, source: str) -> dict[str, Any]:
    """从 ROS2 YAML echo 中提取第一组 header.stamp，解析失败不猜时间。"""
    stripped_text = text.strip()
    if stripped_text.startswith("{"):
        try:
            parsed = json.loads(stripped_text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            stamp = parsed.get("stamp")
            if isinstance(stamp, dict):
                try:
                    sec = int(stamp.get("sec"))
                    nanosec = int(stamp.get("nanosec"))
                except (TypeError, ValueError):
                    return {"parsed": False, "reason": "json_stamp_parse_failed", "source": source}
                return ros_stamp_parts_to_artifact(sec, nanosec, source=source)
    inline = re.search(r"stamp:\s*\{[^}]*sec:\s*(-?\d+)[^}]*nanosec:\s*(-?\d+)[^}]*\}", text)
    if inline:
        return ros_stamp_parts_to_artifact(int(inline.group(1)), int(inline.group(2)), source=source)
    capture = False
    sec: int | None = None
    nanosec: int | None = None
    for raw_line in text.splitlines():
        stripped = raw_line.strip().strip("'\"")
        if stripped.startswith("stamp:"):
            capture = True
            sec = None
            nanosec = None
            continue
        if not capture:
            continue
        if stripped.startswith("sec:"):
            try:
                sec = int(stripped.split(":", 1)[1].strip())
            except ValueError:
                return {"parsed": False, "reason": "stamp_sec_parse_failed", "source": source}
        elif stripped.startswith("nanosec:"):
            try:
                nanosec = int(stripped.split(":", 1)[1].strip())
            except ValueError:
                return {"parsed": False, "reason": "stamp_nanosec_parse_failed", "source": source}
        elif stripped and not raw_line.startswith((" ", "\t", "-")) and (sec is not None or nanosec is not None):
            break
        if sec is not None and nanosec is not None:
            return ros_stamp_parts_to_artifact(sec, nanosec, source=source)
    return {"parsed": False, "reason": "stamp_not_found", "source": source}


def freshness_from_stamp(
    stamp: dict[str, Any],
    *,
    observed: bool,
    source_class: str,
    reference_ms: int,
    stale_after_ms: int = FRESHNESS_STALE_AFTER_MS,
) -> dict[str, Any]:
    """只对动态墙钟 stamp 做 freshness；static TF 和仿真/零时间戳必须明确 unknown。"""
    if not observed:
        return {"status": "not_observed", "reason": "probe_or_source_not_observed", "age_ms": None}
    if source_class == "static":
        return {"status": "static_source_observed_not_age_gated", "reason": "static_tf_is_latched", "age_ms": None}
    if not stamp.get("parsed"):
        return {"status": "unknown", "reason": str(stamp.get("reason") or "stamp_not_parseable"), "age_ms": None}
    epoch_ms = int(stamp.get("epoch_ms") or 0)
    if epoch_ms <= 0:
        return {"status": "unknown", "reason": "zero_or_unset_stamp", "age_ms": None}
    if epoch_ms < FRESHNESS_WALL_CLOCK_MIN_MS:
        return {"status": "unknown", "reason": "stamp_not_wall_clock", "age_ms": None, "stamp_epoch_ms": epoch_ms}
    age_ms = int(reference_ms - epoch_ms)
    if age_ms < -stale_after_ms:
        return {
            "status": "unknown",
            "reason": "stamp_is_in_future_relative_to_probe_clock",
            "age_ms": age_ms,
            "threshold_ms": stale_after_ms,
        }
    return {
        "status": "fresh" if age_ms <= stale_after_ms else "stale",
        "reason": "within_threshold" if age_ms <= stale_after_ms else "older_than_threshold",
        "age_ms": age_ms,
        "threshold_ms": stale_after_ms,
    }


def parse_tf_topic_transforms(text: str, *, source_topic: str) -> list[dict[str, Any]]:
    """从 `/tf(_static)` echo 的 YAML 文本提取 transform 数值，超时时也能保留雷达外参。"""
    transforms: list[dict[str, Any]] = []
    for block in text.split("- header:"):
        parent_match = None
        child_match = None
        section = None
        translation: dict[str, float] = {}
        rotation: dict[str, float] = {}
        for line in block.splitlines():
            stripped = line.strip().strip("'\"")
            if stripped.startswith("frame_id:"):
                parent_match = stripped.split(":", 1)[1].strip().strip("'\"")
            elif stripped.startswith("child_frame_id:"):
                child_match = stripped.split(":", 1)[1].strip().strip("'\"")
            elif stripped == "translation:":
                section = "translation"
            elif stripped == "rotation:":
                section = "rotation"
            elif section in {"translation", "rotation"} and ":" in stripped:
                name, raw_value = stripped.split(":", 1)
                name = name.strip()
                if name not in {"x", "y", "z", "w"}:
                    continue
                try:
                    value = float(raw_value.strip())
                except ValueError:
                    continue
                if section == "translation":
                    translation[name] = value
                else:
                    rotation[name] = value
        if not parent_match or not child_match:
            continue
        if not all(axis in translation for axis in ("x", "y", "z")):
            continue
        if not all(axis in rotation for axis in ("x", "y", "z", "w")):
            continue
        qx = rotation["x"]
        qy = rotation["y"]
        qz = rotation["z"]
        qw = rotation["w"]
        yaw = math.atan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz))
        transforms.append(
            {
                "parent_frame_id": parent_match,
                "child_frame_id": child_match,
                "stamp": parse_first_ros_stamp(block, source=f"{source_topic}.header.stamp"),
                "translation": {"x": translation["x"], "y": translation["y"], "z": translation["z"]},
                "rotation": {"yaw": yaw, "quaternion": {"x": qx, "y": qy, "z": qz, "w": qw}},
                "source": source_topic,
            }
        )
    return transforms


def find_tf_topic_transform(
    transforms: list[dict[str, Any]],
    *,
    parent_frame_id: str,
    child_frame_id: str,
) -> dict[str, Any] | None:
    """按 parent/child 精确取当前窗口最新 transform，避免首个旧 stamp 污染 freshness。"""
    matches = [
        transform
        for transform in transforms
        if transform.get("parent_frame_id") == parent_frame_id
        and transform.get("child_frame_id") == child_frame_id
    ]
    if not matches:
        return None
    # callback 追加顺序本身可作为兜底；stamp 可解析时优先取 epoch 最大项。
    return max(
        enumerate(matches),
        key=lambda item: (
            int((item[1].get("stamp") or {}).get("epoch_ms") or 0)
            if isinstance(item[1].get("stamp"), dict)
            else 0,
            item[0],
        ),
    )[1]


def parse_pose_frame_id(text: str) -> str | None:
    """提取 `/amcl_pose` header.frame_id，用于区分 pose 有了但 map frame 未进 TF。"""
    for line in text.splitlines():
        stripped = line.strip().strip("'\"")
        if stripped.startswith("frame_id:"):
            value = stripped.split(":", 1)[1].strip().strip("'\"")
            return value or None
    return None


def parse_amcl_pose(text: str) -> dict[str, Any] | None:
    """从 `/amcl_pose` YAML 输出提取 map-frame 位姿；解析失败时不伪造坐标。"""
    frame_id = parse_pose_frame_id(text)
    section: str | None = None
    position: dict[str, float] = {}
    orientation: dict[str, float] = {}
    for line in text.splitlines():
        stripped = line.strip().strip("'\"")
        if stripped == "position:":
            section = "position"
            continue
        if stripped == "orientation:":
            section = "orientation"
            continue
        if ":" not in stripped or section not in {"position", "orientation"}:
            continue
        key, raw_value = stripped.split(":", 1)
        if key not in {"x", "y", "z", "w"}:
            continue
        try:
            value = float(raw_value.strip().strip("'\""))
        except ValueError:
            continue
        if section == "position":
            position[key] = value
        else:
            orientation[key] = value
    if "x" not in position or "y" not in position:
        return None
    z = orientation.get("z")
    w = orientation.get("w")
    yaw = math.atan2(2.0 * (w or 0.0) * (z or 0.0), 1.0 - 2.0 * (z or 0.0) * (z or 0.0)) if z is not None and w is not None else None
    return {
        "frame_id": frame_id or "not_loaded",
        "x": position["x"],
        "y": position["y"],
        "z": position.get("z", 0.0),
        "yaw": yaw,
        "source": "/amcl_pose",
    }


def parse_node_info_topics(text: str, section_name: str) -> list[dict[str, str]]:
    """解析 `ros2 node info` 的 Publishers/Subscribers，保留 topic/type 便于远端复盘。"""
    capture = False
    topics: list[dict[str, str]] = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped == f"{section_name}:":
            capture = True
            continue
        if capture and stripped.endswith(":") and not stripped.startswith("*"):
            break
        if not capture or not stripped.startswith("* "):
            continue
        item = stripped[2:].strip()
        topic = item
        topic_type = ""
        if "[" in item and "]" in item:
            topic, topic_type = item.split("[", 1)
            topic_type = topic_type.split("]", 1)[0].strip()
        topics.append({"topic": topic.strip(), "type": topic_type})
    return topics


def parse_param_probe(text: str) -> dict[str, str]:
    """解析组合命令中的 AMCL 参数 readback；保留字符串形态避免 ROS CLI 文案差异。"""
    params: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("__PARAM__") or "=" not in line:
            continue
        name, value = line.removeprefix("__PARAM__").split("=", 1)
        normalized = value.strip()
        for prefix in ("String value is:", "Boolean value is:"):
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix) :].strip()
        params[name.strip()] = normalized.strip("'\"")
    return params


def parameter_value_to_artifact(value: Any) -> Any:
    """把 rcl_interfaces/ParameterValue 转为 JSON 友好值，避免依赖 ros2 param CLI 文案。"""
    # ROS2 ParameterType 常量值：1 bool、2 int、3 double、4 string；只读取本轮需要的类型。
    value_type = int(getattr(value, "type", 0) or 0)
    if value_type == 1:
        return bool(getattr(value, "bool_value", False))
    if value_type == 2:
        return int(getattr(value, "integer_value", 0))
    if value_type == 3:
        return float(getattr(value, "double_value", 0.0))
    if value_type == 4:
        return str(getattr(value, "string_value", ""))
    return None


def normalize_param_artifact_value(value: Any) -> str | None:
    """参数比较统一走字符串，兼容 ROS CLI 和 rclpy 两种 probe 来源。"""
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip().strip("'\"")


def graph_topics_to_artifact(topics: list[tuple[str, list[str]]]) -> list[dict[str, str]]:
    """rclpy graph API 返回类型数组；artifact 保持和 ros2 node info 解析后的形状一致。"""
    return [{"topic": topic, "type": ",".join(types)} for topic, types in topics]


def tf_message_edges(message: Any, *, source_topic: str) -> list[dict[str, str]]:
    """从 rclpy 订阅到的 TFMessage 提取边，避免再跑慢 `ros2 topic echo`。"""
    edges: list[dict[str, str]] = []
    for transform in getattr(message, "transforms", []) or []:
        header = getattr(transform, "header", None)
        parent = str(getattr(header, "frame_id", "") or "")
        child = str(getattr(transform, "child_frame_id", "") or "")
        if parent and child:
            edges.append({"parent": parent, "child": child, "topic": source_topic})
    return edges


def tf_message_transforms(message: Any, *, source_topic: str) -> list[dict[str, Any]]:
    """从 rclpy TFMessage 直接提取 transform 数值，避免 partial artifact 缺少雷达外参。"""
    transforms: list[dict[str, Any]] = []
    for transform in getattr(message, "transforms", []) or []:
        header = getattr(transform, "header", None)
        parent = str(getattr(header, "frame_id", "") or "")
        child = str(getattr(transform, "child_frame_id", "") or "")
        value = getattr(transform, "transform", None)
        translation = getattr(value, "translation", None)
        rotation = getattr(value, "rotation", None)
        if not parent or not child or translation is None or rotation is None:
            continue
        qx = float(getattr(rotation, "x", 0.0))
        qy = float(getattr(rotation, "y", 0.0))
        qz = float(getattr(rotation, "z", 0.0))
        qw = float(getattr(rotation, "w", 1.0))
        yaw = math.atan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz))
        transforms.append(
            {
                "parent_frame_id": parent,
                "child_frame_id": child,
                "stamp": ros_message_stamp_to_artifact(getattr(header, "stamp", None), source=f"{source_topic}.header.stamp"),
                "translation": {
                    "x": float(getattr(translation, "x", 0.0)),
                    "y": float(getattr(translation, "y", 0.0)),
                    "z": float(getattr(translation, "z", 0.0)),
                },
                "rotation": {"yaw": yaw, "quaternion": {"x": qx, "y": qy, "z": qz, "w": qw}},
                "source": source_topic,
            }
        )
    return transforms


def merge_amcl_cli_fallback_probe(rclpy_result: dict[str, Any], cli_fallback: dict[str, Any]) -> dict[str, Any]:
    """合并 rclpy 快速采样和 CLI closeout，避免任一层失败时丢掉另一层证据。"""
    combined = dict(rclpy_result)
    # rclpy 可能拿到 TF 边但参数服务没返回；CLI 可能只拿到 topic/node info，两层互补。
    cli_topic_types = cli_fallback.get("topic_types") if isinstance(cli_fallback.get("topic_types"), dict) else {}
    rclpy_topic_types = rclpy_result.get("topic_types") if isinstance(rclpy_result.get("topic_types"), dict) else {}
    combined["topic_types"] = {**{str(k): str(v) for k, v in cli_topic_types.items()}, **{str(k): str(v) for k, v in rclpy_topic_types.items()}}
    cli_endpoints = cli_fallback.get("topic_endpoint_summaries") if isinstance(cli_fallback.get("topic_endpoint_summaries"), dict) else {}
    rclpy_endpoints = rclpy_result.get("topic_endpoint_summaries") if isinstance(rclpy_result.get("topic_endpoint_summaries"), dict) else {}
    combined["topic_endpoint_summaries"] = {**cli_endpoints, **rclpy_endpoints}
    rclpy_params = rclpy_result.get("params") if isinstance(rclpy_result.get("params"), dict) else {}
    cli_params = cli_fallback.get("params") if isinstance(cli_fallback.get("params"), dict) else {}
    combined["params"] = rclpy_params or cli_params
    combined["param_probe_ok"] = bool(rclpy_result.get("param_probe_ok") or cli_fallback.get("param_probe_ok"))
    combined["node_info_observed"] = bool(rclpy_result.get("node_info_observed") or cli_fallback.get("node_info_observed"))
    combined["tf_inventory_observed"] = bool(rclpy_result.get("tf_inventory_observed") or cli_fallback.get("tf_inventory_observed"))
    for key in ("publishers", "subscribers", "dynamic_edges", "static_edges", "dynamic_transforms", "static_transforms"):
        value = rclpy_result.get(key)
        if not (isinstance(value, list) and value):
            value = cli_fallback.get(key)
        combined[key] = value if isinstance(value, list) else []
    rclpy_statuses = rclpy_result.get("command_statuses") if isinstance(rclpy_result.get("command_statuses"), dict) else {}
    cli_statuses = cli_fallback.get("command_statuses") if isinstance(cli_fallback.get("command_statuses"), dict) else {}
    combined["command_statuses"] = {**cli_statuses, **rclpy_statuses}
    combined["ok"] = bool(rclpy_result.get("ok") or cli_fallback.get("ok"))
    combined["fallback_used"] = True
    combined["fallback_boundary"] = cli_fallback.get("boundary")
    combined["param_probe_boundary"] = rclpy_result.get("param_probe_boundary") or cli_fallback.get("param_probe_boundary")
    combined["probe_mode"] = "ros2_cli_fallback"
    combined["rclpy_boundary"] = rclpy_result.get("boundary")
    combined["cli_fallback"] = cli_fallback
    combined["boundary"] = f"{rclpy_result.get('boundary') or 'rclpy_amcl_probe_incomplete'}_with_{cli_fallback.get('boundary') or 'cli_amcl_inventory_unavailable'}"
    return combined


def collect_amcl_rclpy_probe(args: argparse.Namespace | None = None, timeout_s: float = 2.0) -> dict[str, Any]:
    """用 rclpy 一次性取 /amcl 参数、graph 和 TF 样本，替代多条串行 ROS CLI。"""
    result: dict[str, Any] = {
        "executed": False,
        "ok": False,
        "param_probe_ok": False,
        "node_info_observed": False,
        "tf_inventory_observed": False,
        "params": {},
        "publishers": [],
        "subscribers": [],
        "topic_types": {},
        "topic_endpoint_summaries": {},
        "dynamic_edges": [],
        "static_edges": [],
        "dynamic_transforms": [],
        "static_transforms": [],
        "amcl_pose_sample": {
            "observed": False,
            "sample_count": 0,
            "received_at_ms": None,
            "frame_id": None,
            "stamp": {"parsed": False, "reason": "sample_not_observed", "source": "/amcl_pose.header.stamp"},
        },
        "command_statuses": {"rclpy_graph": None, "tf": None, "tf_static": None},
        "error": None,
        "elapsed_ms": 0,
        "boundary": "rclpy_amcl_probe_not_started",
        "fallback_used": False,
        "fallback_boundary": None,
        "param_probe_boundary": None,
        "probe_mode": "rclpy",
    }
    started_ms = now_ms()
    node = None
    rclpy_initialized = False
    try:
        import rclpy
        from rcl_interfaces.srv import GetParameters  # type: ignore[import-not-found]
        from geometry_msgs.msg import PoseWithCovarianceStamped  # type: ignore[import-not-found]
        from rclpy.qos import DurabilityPolicy, QoSProfile  # type: ignore[import-not-found]
        from tf2_msgs.msg import TFMessage  # type: ignore[import-not-found]

        result["executed"] = True
        rclpy.init(args=[])
        rclpy_initialized = True
        node = rclpy.create_node("o10_amcl_param_graph_probe")
        client = node.create_client(GetParameters, "/amcl/get_parameters")
        publishers: list[tuple[str, list[str]]] = []
        subscribers: list[tuple[str, list[str]]] = []
        graph_deadline = time.time() + max(min(timeout_s, 2.5), 1.2)
        service_ready = False
        while time.time() < graph_deadline:
            # ROS graph 在节点刚启动后有发现延迟；持续刷新可避免把瞬态空 graph 误判为 /tf 缺失。
            rclpy.spin_once(node, timeout_sec=0.08)
            topic_pairs = node.get_topic_names_and_types()
            result["topic_types"] = {topic: ",".join(types) for topic, types in topic_pairs}
            result["topic_endpoint_summaries"] = signal_topic_endpoint_summaries(node)
            result["command_statuses"]["rclpy_graph"] = 0
            try:
                publishers = node.get_publisher_names_and_types_by_node("amcl", "/")
                subscribers = node.get_subscriber_names_and_types_by_node("amcl", "/")
                if publishers or subscribers:
                    result["node_info_observed"] = True
            except Exception as graph_exc:  # noqa: BLE001 - AMCL graph 名称瞬态不可见时仍继续查参数服务。
                result["node_info_error"] = compact_error(graph_exc)
            service_ready = client.service_is_ready()
            graph_has_tf = "/tf" in result["topic_types"] or "/tf_static" in result["topic_types"]
            if service_ready and result["node_info_observed"] and graph_has_tf:
                break
        result["publishers"] = graph_topics_to_artifact(publishers)
        result["subscribers"] = graph_topics_to_artifact(subscribers)
        names = ["tf_broadcast", "global_frame_id", "odom_frame_id", "base_frame_id"]
        params: dict[str, Any] = {}
        param_future: Any = None
        param_boundary = "amcl_parameter_service_unavailable"
        if service_ready or client.wait_for_service(timeout_sec=0.4):
            request = GetParameters.Request()
            request.names = names
            param_future = client.call_async(request)
            param_boundary = "amcl_parameter_response_pending"
        dynamic_edges: list[dict[str, str]] = []
        static_edges: list[dict[str, str]] = []
        dynamic_transforms: list[dict[str, Any]] = []
        static_transforms: list[dict[str, Any]] = []
        amcl_pose_samples: list[dict[str, Any]] = []

        def on_dynamic_tf(message: Any) -> None:
            dynamic_edges.extend(tf_message_edges(message, source_topic="/tf"))
            dynamic_transforms.extend(tf_message_transforms(message, source_topic="/tf"))

        def on_static_tf(message: Any) -> None:
            static_edges.extend(tf_message_edges(message, source_topic="/tf_static"))
            static_transforms.extend(tf_message_transforms(message, source_topic="/tf_static"))

        def on_amcl_pose(message: Any) -> None:
            """只读采样 pose；本轮禁止 initialpose，所以必须直接记录当前 runtime 是否自行出样本。"""
            stamp = getattr(getattr(message, "header", None), "stamp", None)
            amcl_pose_samples.append(
                {
                    "received_at_ms": now_ms(),
                    "frame_id": str(getattr(getattr(message, "header", None), "frame_id", "") or ""),
                    "stamp": ros_stamp_parts_to_artifact(
                        int(getattr(stamp, "sec", 0) or 0),
                        int(getattr(stamp, "nanosec", 0) or 0),
                        source="/amcl_pose.header.stamp",
                    ),
                }
            )

        # transient local QoS 是读取 /tf_static 的关键，避免 CLI echo 的启动成本和时序抖动。
        node.create_subscription(TFMessage, "/tf", on_dynamic_tf, QoSProfile(depth=10))
        node.create_subscription(
            TFMessage,
            "/tf_static",
            on_static_tf,
            QoSProfile(depth=10, durability=DurabilityPolicy.TRANSIENT_LOCAL),
        )
        # 订阅本身不发布位姿、不触发运动；它只把 `/amcl_pose` 同窗 timestamp/freshness 带回 artifact。
        node.create_subscription(PoseWithCovarianceStamped, "/amcl_pose", on_amcl_pose, QoSProfile(depth=10))
        end_time = time.time() + max(min(timeout_s, 3.0), 0.8)
        while time.time() < end_time:
            # 参数服务偶发晚于 /amcl 节点出现在 graph；不要因此跳过 TF/static TF 采样。
            rclpy.spin_once(node, timeout_sec=0.1)
            topic_pairs = node.get_topic_names_and_types()
            result["topic_types"] = {topic: ",".join(types) for topic, types in topic_pairs}
            result["topic_endpoint_summaries"] = signal_topic_endpoint_summaries(node)
            result["command_statuses"]["rclpy_graph"] = 0
            try:
                publishers = node.get_publisher_names_and_types_by_node("amcl", "/")
                subscribers = node.get_subscriber_names_and_types_by_node("amcl", "/")
                if publishers or subscribers:
                    result["node_info_observed"] = True
                    result["publishers"] = graph_topics_to_artifact(publishers)
                    result["subscribers"] = graph_topics_to_artifact(subscribers)
            except Exception as graph_exc:  # noqa: BLE001 - graph 继续发现，错误只留给 artifact。
                result["node_info_error"] = compact_error(graph_exc)
            if param_future is None and client.service_is_ready():
                request = GetParameters.Request()
                request.names = names
                param_future = client.call_async(request)
                param_boundary = "amcl_parameter_response_pending"
            if param_future is not None and param_future.done() and not params:
                response = param_future.result()
                if response is None:
                    param_boundary = "amcl_parameter_response_missing"
                else:
                    values = getattr(response, "values", []) or []
                    params = {
                        name: parameter_value_to_artifact(value)
                        for name, value in zip(names, values)
                    }
                    param_boundary = "amcl_parameter_response_observed"
            # `/tf` 上先出现 odom->base_link 很常见；只有目标 map->odom 已采到才可提前结束，
            # 否则必须用完有界窗口，避免把 AMCL 的较低频广播误判为 current-window 缺失。
            expected_odom_frame = str(getattr(args, "managed_odom_frame_id", DEFAULT_MANAGED_ODOM_FRAME_ID))
            map_to_odom_observed = edge_observed(dynamic_edges, "map", expected_odom_frame)
            if map_to_odom_observed and static_edges and params and result["node_info_observed"] and amcl_pose_samples:
                break
        result["dynamic_edges"] = dynamic_edges
        result["static_edges"] = static_edges
        result["dynamic_transforms"] = dynamic_transforms
        result["static_transforms"] = static_transforms
        latest_pose = amcl_pose_samples[-1] if amcl_pose_samples else {}
        result["amcl_pose_sample"] = {
            "observed": bool(amcl_pose_samples),
            "sample_count": len(amcl_pose_samples),
            "received_at_ms": latest_pose.get("received_at_ms"),
            "frame_id": latest_pose.get("frame_id"),
            "stamp": latest_pose.get("stamp")
            if isinstance(latest_pose.get("stamp"), dict)
            else {"parsed": False, "reason": "sample_not_observed", "source": "/amcl_pose.header.stamp"},
        }
        result["command_statuses"]["tf"] = 0 if dynamic_edges else 124
        result["command_statuses"]["tf_static"] = 0 if static_edges else 124
        result["tf_inventory_observed"] = bool(dynamic_edges or static_edges or result["topic_types"])
        result.update(
            {
                "ok": bool(result["node_info_observed"] and params and result["tf_inventory_observed"]),
                "param_probe_ok": bool(params),
                "params": params,
                "param_probe_boundary": param_boundary,
                "boundary": (
                    "rclpy_amcl_params_graph_tf_probe_observed"
                    if params
                    else f"{param_boundary}_after_tf_probe"
                ),
            }
        )
        if args is not None and not result["ok"]:
            cli_fallback = collect_amcl_cli_probe(args, timeout_s=timeout_s)
            return merge_amcl_cli_fallback_probe(result, cli_fallback)
        return result
    except Exception as exc:  # noqa: BLE001 - 现场缺 rclpy/服务超时都要结构化回写。
        result["error"] = compact_error(exc)
        result["boundary"] = "rclpy_amcl_probe_failed"
        result["probe_mode"] = "rclpy_failed_before_inventory_complete"
        result["rclpy_import_failure_classification"] = classify_rclpy_import_failure(str(exc), dict(os.environ))
        if args is not None:
            cli_fallback = collect_amcl_cli_probe(args, timeout_s=timeout_s)
            cli_fallback["error"] = result["error"]
            cli_fallback["rclpy_boundary"] = result["boundary"]
            cli_fallback["rclpy_import_failure_classification"] = result["rclpy_import_failure_classification"]
            return cli_fallback
        return result
    finally:
        result["elapsed_ms"] = now_ms() - started_ms
        if node is not None:
            try:
                node.destroy_node()
            except Exception:
                pass
        if rclpy_initialized:
            try:
                if rclpy.ok():
                    rclpy.shutdown()
            except Exception:
                pass


def collect_amcl_sourced_rclpy_probe(args: argparse.Namespace, timeout_s: float = 4.0) -> dict[str, Any]:
    """在已 source 的 child Python 运行 rclpy probe，避免 SSH parent 缺 PYTHONPATH 后退成十条慢 CLI。"""
    child_timeout_s = max(min(float(timeout_s), 5.0), 1.0)
    command = (
        f"python3 {shlex.quote(str(Path(__file__).resolve()))} "
        f"--tf-source-child-probe --timeout-s {child_timeout_s:g}"
    )
    command_result = run_ros(args, command, timeout_s=child_timeout_s + 8.0)
    stdout = str(command_result.get("stdout") or "").strip()
    try:
        payload = json.loads(stdout.splitlines()[-1]) if stdout else None
    except json.JSONDecodeError as exc:
        payload = None
        parse_error = compact_error(exc)
    else:
        parse_error = None
    if not isinstance(payload, dict):
        return {
            "executed": bool(command_result.get("executed")),
            "ok": False,
            "param_probe_ok": False,
            "node_info_observed": False,
            "tf_inventory_observed": False,
            "params": {},
            "publishers": [],
            "subscribers": [],
            "topic_types": {},
            "topic_endpoint_summaries": {},
            "dynamic_edges": [],
            "static_edges": [],
            "dynamic_transforms": [],
            "static_transforms": [],
            "command_statuses": {"rclpy_graph": None, "tf": None, "tf_static": None},
            "error": parse_error or command_result.get("error") or {
                "type": "sourced_rclpy_child_output_missing",
                "message": str(command_result.get("stderr") or "child returned no JSON")[-400:],
            },
            "elapsed_ms": command_result.get("elapsed_ms"),
            "boundary": "sourced_rclpy_child_probe_failed",
            "probe_mode": "sourced_rclpy_child",
            "child_command": command_result,
        }
    payload["probe_mode"] = "sourced_rclpy_child"
    payload["child_command"] = {
        "executed": bool(command_result.get("executed")),
        "ok": bool(command_result.get("ok")),
        "returncode": command_result.get("returncode"),
        "elapsed_ms": command_result.get("elapsed_ms"),
        "timed_out": bool(command_result.get("timed_out")),
    }
    return payload


def compact_tf_source_child_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """压缩 child JSON 到 run_bash 8KB 上限内；只保留 attribution 所需 endpoint/edge/stamp。"""
    compact = {
        key: payload.get(key)
        for key in (
            "executed",
            "ok",
            "param_probe_ok",
            "node_info_observed",
            "tf_inventory_observed",
            "params",
            "publishers",
            "subscribers",
            "command_statuses",
            "error",
            "elapsed_ms",
            "boundary",
            "fallback_used",
            "fallback_boundary",
            "param_probe_boundary",
            "probe_mode",
            "node_info_error",
        )
    }
    topic_types = payload.get("topic_types") if isinstance(payload.get("topic_types"), dict) else {}
    compact["topic_types"] = {
        topic: topic_types.get(topic)
        for topic in LOCALIZATION_SIGNAL_TOPICS
        if topic in topic_types
    }
    endpoint_summaries = payload.get("topic_endpoint_summaries") if isinstance(payload.get("topic_endpoint_summaries"), dict) else {}
    compact_endpoints: dict[str, Any] = {}
    for topic in ("/tf", "/tf_static", "/amcl_pose"):
        summary = endpoint_summaries.get(topic) if isinstance(endpoint_summaries.get(topic), dict) else {}
        compact_summary = {
            "publisher_count": int(summary.get("publisher_count") or 0),
            "subscriber_count": int(summary.get("subscriber_count") or 0),
            "inventory_observed": bool(summary.get("inventory_observed")),
            "error": summary.get("error"),
        }
        for endpoint_kind in ("publishers", "subscribers"):
            endpoints = summary.get(endpoint_kind) if isinstance(summary.get(endpoint_kind), list) else []
            compact_summary[endpoint_kind] = []
            for endpoint in endpoints[:8]:
                if not isinstance(endpoint, dict):
                    continue
                qos = endpoint.get("qos_profile") if isinstance(endpoint.get("qos_profile"), dict) else {}
                compact_summary[endpoint_kind].append(
                    {
                        "node_name": endpoint.get("node_name"),
                        "node_namespace": endpoint.get("node_namespace"),
                        "topic_type": endpoint.get("topic_type"),
                        "qos_profile": {
                            key: qos.get(key)
                            for key in ("reliability", "durability", "history", "depth")
                            if key in qos
                        },
                    }
                )
        compact_endpoints[topic] = compact_summary
    compact["topic_endpoint_summaries"] = compact_endpoints
    compact["amcl_pose_sample"] = (
        dict(payload["amcl_pose_sample"])
        if isinstance(payload.get("amcl_pose_sample"), dict)
        else {
            "observed": False,
            "sample_count": 0,
            "received_at_ms": None,
            "frame_id": None,
            "stamp": {"parsed": False, "reason": "sample_not_observed", "source": "/amcl_pose.header.stamp"},
        }
    )

    # 同一 broadcaster 在窗口内会产生大量重复 edge；只保留唯一 edge 与该 edge 最新 stamp。
    for edge_key, transform_key in (("dynamic_edges", "dynamic_transforms"), ("static_edges", "static_transforms")):
        raw_edges = payload.get(edge_key) if isinstance(payload.get(edge_key), list) else []
        edge_map: dict[tuple[str, str, str], dict[str, Any]] = {}
        for edge in raw_edges:
            if not isinstance(edge, dict):
                continue
            identity = (str(edge.get("parent") or ""), str(edge.get("child") or ""), str(edge.get("topic") or ""))
            edge_map[identity] = edge
        compact[edge_key] = list(edge_map.values())[:16]
        raw_transforms = payload.get(transform_key) if isinstance(payload.get(transform_key), list) else []
        transform_map: dict[tuple[str, str], dict[str, Any]] = {}
        for transform in raw_transforms:
            if not isinstance(transform, dict):
                continue
            identity = (str(transform.get("parent_frame_id") or ""), str(transform.get("child_frame_id") or ""))
            previous = transform_map.get(identity)
            current_epoch = int((transform.get("stamp") or {}).get("epoch_ms") or 0) if isinstance(transform.get("stamp"), dict) else 0
            previous_epoch = int((previous.get("stamp") or {}).get("epoch_ms") or 0) if isinstance(previous, dict) and isinstance(previous.get("stamp"), dict) else 0
            if previous is None or current_epoch >= previous_epoch:
                transform_map[identity] = transform
        compact[transform_key] = list(transform_map.values())[:16]
    return compact


def parse_section_status(text: str, marker: str) -> int | None:
    """读取 source probe 中每段命令退出码；缺失时返回 None 代表旧 artifact。"""
    token = f"__{marker}__"
    start = text.find(token)
    if start < 0:
        return None
    tail = text[start + len(token) :].strip().splitlines()
    if not tail:
        return None
    try:
        return int(tail[0].strip())
    except ValueError:
        return None


def topic_info_count(result: dict[str, Any], label: str) -> int | None:
    """从 `ros2 topic info --verbose` 提取 publisher/subscription count，供 publish 诊断兜底。"""
    text = f"{result.get('stdout') or ''}\n{result.get('stderr') or ''}"
    match = re.search(rf"{label}\s+count:\s*(\d+)", text, flags=re.IGNORECASE)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def cli_topic_endpoint_summary(result: dict[str, Any]) -> dict[str, Any]:
    """把 `ros2 topic info --verbose` 收口成稳定摘要，rclpy graph 失败时仍保留 topic inventory。"""
    publisher_count = topic_info_count(result, "publisher")
    subscriber_count = topic_info_count(result, "subscription")
    inventory_observed = bool(result.get("ok")) or publisher_count is not None or subscriber_count is not None
    return {
        "publishers": [],
        "subscribers": [],
        "publisher_count": int(publisher_count or 0),
        "subscriber_count": int(subscriber_count or 0),
        "inventory_observed": inventory_observed,
        "error": None if inventory_observed else result.get("error"),
    }


def cli_amcl_param_probe(args: argparse.Namespace, timeout_s: float = AMCL_CLI_FALLBACK_TIMEOUT_S) -> tuple[dict[str, Any], str]:
    """CLI 参数兜底只读读取关键 AMCL 参数；逐个查询避免单条组合命令掩盖哪项失败。"""
    params: dict[str, Any] = {}
    boundaries: list[str] = []
    command_timeout_s = max(min(float(timeout_s), AMCL_CLI_FALLBACK_TIMEOUT_S), 1.0)
    for name in ("tf_broadcast", "global_frame_id", "odom_frame_id", "base_frame_id"):
        result = run_ros(args, f"ros2 param get /amcl {shlex.quote(name)}", timeout_s=command_timeout_s)
        parsed = parse_param_probe(f"__PARAM__{name}={str(result.get('stdout') or '').strip()}")
        if name in parsed:
            params[name] = parsed[name]
            boundaries.append(f"{name}_observed")
        elif result.get("timed_out"):
            boundaries.append(f"{name}_timeout")
        elif result.get("ok"):
            boundaries.append(f"{name}_empty")
        else:
            boundaries.append(f"{name}_failed")
    if params and len(params) == 4:
        return params, "cli_amcl_param_probe_observed"
    if params:
        return params, "cli_amcl_param_probe_partial"
    return params, "cli_amcl_param_probe_unavailable_" + "_".join(boundaries[:4])


def collect_amcl_cli_probe(args: argparse.Namespace, timeout_s: float = 2.0) -> dict[str, Any]:
    """rclpy 不可用时退回 ROS CLI，只读保留 `/tf`、`/tf_static` 与 `/amcl` inventory 事实。"""
    # 现场上一轮卡在 graph wait；fallback 必须短而有边界，避免 AMCL closeout 自己吃掉 final artifact。
    command_timeout_s = max(min(float(timeout_s), AMCL_CLI_FALLBACK_TIMEOUT_S), 1.0)
    topic_list = run_ros(args, "ros2 topic list -t", timeout_s=command_timeout_s)
    amcl_node_info = run_ros(args, "ros2 node info /amcl", timeout_s=command_timeout_s)
    scan_info = run_ros(args, "ros2 topic info /scan --verbose", timeout_s=command_timeout_s)
    map_info = run_ros(args, "ros2 topic info /map --verbose", timeout_s=command_timeout_s)
    tf_info = run_ros(args, "ros2 topic info /tf --verbose", timeout_s=command_timeout_s)
    tf_static_info = run_ros(args, "ros2 topic info /tf_static --verbose", timeout_s=command_timeout_s)
    params, param_boundary = cli_amcl_param_probe(args, timeout_s=command_timeout_s)
    topic_types = parse_topic_list_with_types(str(topic_list.get("stdout") or ""))
    publishers = parse_node_info_topics(str(amcl_node_info.get("stdout") or ""), "Publishers")
    subscribers = parse_node_info_topics(str(amcl_node_info.get("stdout") or ""), "Subscribers")
    topic_endpoint_summaries = {
        topic: {
            "publishers": [],
            "subscribers": [],
            "publisher_count": 0,
            "subscriber_count": 0,
            "inventory_observed": False,
            "error": None,
        }
        for topic in LOCALIZATION_SIGNAL_TOPICS
    }
    topic_endpoint_summaries["/scan"] = cli_topic_endpoint_summary(scan_info)
    topic_endpoint_summaries["/map"] = cli_topic_endpoint_summary(map_info)
    topic_endpoint_summaries["/tf"] = cli_topic_endpoint_summary(tf_info)
    topic_endpoint_summaries["/tf_static"] = cli_topic_endpoint_summary(tf_static_info)
    boundary_parts = []
    if topic_types:
        boundary_parts.append("topic_list")
    if publishers or subscribers:
        boundary_parts.append("amcl_node_info")
    if topic_endpoint_summaries["/scan"]["inventory_observed"]:
        boundary_parts.append("scan_info")
    if topic_endpoint_summaries["/map"]["inventory_observed"]:
        boundary_parts.append("map_info")
    if topic_endpoint_summaries["/tf"]["inventory_observed"]:
        boundary_parts.append("tf_info")
    if topic_endpoint_summaries["/tf_static"]["inventory_observed"]:
        boundary_parts.append("tf_static_info")
    if params:
        boundary_parts.append("amcl_params")
    boundary = "cli_amcl_inventory_observed_" + "_".join(boundary_parts) if boundary_parts else "cli_amcl_inventory_unavailable"
    return {
        "executed": True,
        "ok": bool(topic_types or publishers or subscribers),
        "param_probe_ok": bool(params),
        "node_info_observed": bool(publishers or subscribers),
        "tf_inventory_observed": bool(topic_types or topic_endpoint_summaries["/tf"]["inventory_observed"] or topic_endpoint_summaries["/tf_static"]["inventory_observed"]),
        "params": params,
        "publishers": publishers,
        "subscribers": subscribers,
        "topic_types": topic_types,
        "topic_endpoint_summaries": topic_endpoint_summaries,
        "dynamic_edges": [],
        "static_edges": [],
        "dynamic_transforms": [],
        "static_transforms": [],
        "command_statuses": {
            "rclpy_graph": topic_list.get("returncode"),
            "scan_topic_info": scan_info.get("returncode"),
            "map_topic_info": map_info.get("returncode"),
            "tf": tf_info.get("returncode"),
            "tf_static": tf_static_info.get("returncode"),
        },
        "commands": {
            "topic_list": topic_list,
            "amcl_node_info": amcl_node_info,
            "scan_info": scan_info,
            "map_info": map_info,
            "tf_info": tf_info,
            "tf_static_info": tf_static_info,
        },
        "command_timeout_s": command_timeout_s,
        "error": None,
        "elapsed_ms": int(
            sum(
                int(command.get("elapsed_ms") or 0)
                for command in (topic_list, amcl_node_info, scan_info, map_info, tf_info, tf_static_info)
            )
        ),
        "boundary": boundary,
        "fallback_used": True,
        "fallback_boundary": boundary,
        "param_probe_boundary": param_boundary,
        "probe_mode": "ros2_cli_fallback",
    }


def edge_observed(edges: list[dict[str, str]], parent: str, child: str) -> bool:
    """frame inventory 里的边用精确 parent/child 匹配，避免子串误判 frame 名。"""
    return any(edge.get("parent") == parent and edge.get("child") == child for edge in edges)


def collect_tf_source_diagnostics(
    args: argparse.Namespace,
    *,
    ros2_cli_ready: bool,
    rclpy_runtime_ready: bool,
    board_source_preflight_result: dict[str, Any] | None,
    amcl_pose_result: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """轻量采集 AMCL/TF source；放在 tf2_echo 前，避免慢查询掩盖 root cause。"""
    if not ros2_cli_ready:
        return {
            "executed": False,
            "ok": False,
            "boundary": "ros2_cli_unavailable_tf_source_probe_skipped",
        }, default_tf_source_diagnostics(
            args,
            amcl_pose_result=amcl_pose_result,
            root_cause_reason="tf_source_probe_skipped_without_ros2_cli",
            probe_boundary="ros2_cli_unavailable_tf_source_probe_skipped",
        )
    if not rclpy_runtime_ready:
        classification = str((board_source_preflight_result or {}).get("classification") or "board_source_preflight_rclpy_runtime_not_ready")
        cli_probe = collect_amcl_cli_probe(args, timeout_s=AMCL_CLI_FALLBACK_TIMEOUT_S)
        cli_probe["rclpy_boundary"] = "rclpy_runtime_unavailable_after_board_preflight"
        cli_probe["blocked_by_board_source_classification"] = classification
        result = {
            "executed": True,
            "ok": bool(cli_probe.get("ok")),
            "boundary": cli_probe.get("boundary") or "tf_source_probe_rclpy_runtime_unavailable_after_board_preflight",
            "elapsed_ms": cli_probe.get("elapsed_ms"),
            "stdout": "",
            "stderr": "",
            "rclpy_runtime_ready": False,
            "blocked_by_board_source_classification": classification,
            "amcl_rclpy_probe": cli_probe,
        }
        diagnostics = build_tf_source_diagnostics(args, result, amcl_pose_result=amcl_pose_result, amcl_probe=cli_probe)
        diagnostics["tf_source_root_cause_detail"]["blocked_by_board_source_classification"] = classification
        diagnostics["tf_source_root_cause_detail"]["probe_boundary"] = classification
        if diagnostics["amcl_tf_root_cause"] == "/tf_topic_missing":
            diagnostics["amcl_tf_root_cause"] = "tf_source_probe_rclpy_runtime_unavailable_after_board_preflight"
            diagnostics["tf_source_root_cause_detail"]["reason"] = diagnostics["amcl_tf_root_cause"]
        return result, diagnostics
    amcl_probe = collect_amcl_sourced_rclpy_probe(args, timeout_s=4.0)
    result = {
        "executed": True,
        "ok": bool(amcl_probe.get("ok")),
        "boundary": amcl_probe.get("boundary"),
        "elapsed_ms": amcl_probe.get("elapsed_ms"),
        "stdout": "",
        "stderr": "",
    }
    result["amcl_rclpy_probe"] = amcl_probe
    return result, build_tf_source_diagnostics(args, result, amcl_pose_result=amcl_pose_result, amcl_probe=amcl_probe)


def default_tf_source_diagnostics(
    args: argparse.Namespace,
    *,
    amcl_pose_result: dict[str, Any],
    root_cause_reason: str = "tf_source_probe_not_executed",
    probe_boundary: str = "tf_source_probe_not_executed",
) -> dict[str, Any]:
    """source probe 未执行时仍输出稳定字段，保证 upper/readback 不需要猜 key。"""
    frame_ids = tf_chain_frame_contract(args)["actual"]
    amcl_pose_frame_id = parse_pose_frame_id(str(amcl_pose_result.get("stdout") or ""))
    return {
        "tf_topics_observed": {"/tf": False, "/tf_static": False},
        "tf_static_observed": False,
        "tf_frame_inventory": {"frames": [], "edges": [], "dynamic_edges": [], "static_edges": [], "transforms": []},
        "topic_endpoint_summaries": {
            topic: {
                "publishers": [],
                "subscribers": [],
                "publisher_count": 0,
                "subscriber_count": 0,
                "error": None,
            }
            for topic in LOCALIZATION_SIGNAL_TOPICS
        },
        "amcl_pose_frame_id": amcl_pose_frame_id,
        "amcl_pose_sample": {
            "observed": False,
            "sample_count": 0,
            "received_at_ms": None,
            "frame_id": amcl_pose_frame_id or None,
            "stamp": {"parsed": False, "reason": "sample_not_observed", "source": "/amcl_pose.header.stamp"},
        },
        "amcl_node_publishers": [],
        "amcl_node_subscribers": [],
        "amcl_param_probe_ok": False,
        "amcl_node_info_observed": False,
        "amcl_tf_broadcast_param": None,
        "amcl_frame_params": {},
        "tf_source_root_cause_detail": {"reason": root_cause_reason, "probe_boundary": probe_boundary},
        "amcl_broadcast_conditions": {},
        "map_frame_observed": False,
        "odom_frame_observed": False,
        "base_frame_observed": False,
        "laser_frame_observed": False,
        "map_to_odom_source_observed": False,
        "map_to_odom_publisher_attribution": {
            "source_topic": None,
            "dynamic_source_observed": False,
            "publisher_attribution_status": "not_attributed_dynamic_map_to_odom_not_observed",
            "publisher_attribution_reason": root_cause_reason,
            "publisher_endpoint_inventory_observed": False,
            "publisher_endpoint_count": 0,
            "publisher_endpoint": None,
            "publisher_endpoint_candidates": [],
            "amcl_node_tf_publisher_observed": False,
            "amcl_node_tf_publishers": [],
        },
        "odom_to_base_link_source_observed": False,
        "base_link_to_laser_frame_source_observed": False,
        "base_link_to_laser_frame_source_transform": None,
        "amcl_tf_root_cause": root_cause_reason,
        "frame_contract": {"actual": frame_ids},
    }


def build_tf_source_diagnostics(
    args: argparse.Namespace,
    result: dict[str, Any],
    *,
    amcl_pose_result: dict[str, Any],
    amcl_probe: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """把 `/tf`、`/tf_static`、AMCL node info/params 汇总成稳定 source/timing 字段。"""
    stdout = str(result.get("stdout") or "")
    topic_types = parse_topic_list_with_types(extract_section(stdout, "TOPIC_LIST_T"))
    amcl_info = extract_section(stdout, "AMCL_NODE_INFO")
    params = parse_param_probe(extract_section(stdout, "AMCL_PARAMS"))
    probe = amcl_probe if isinstance(amcl_probe, dict) else {}
    probe_topic_types = probe.get("topic_types") if isinstance(probe.get("topic_types"), dict) else {}
    if probe_topic_types:
        topic_types = {str(topic): str(topic_type) for topic, topic_type in probe_topic_types.items()}
    topic_endpoints = probe.get("topic_endpoint_summaries") if isinstance(probe.get("topic_endpoint_summaries"), dict) else {}
    rclpy_params = probe.get("params") if isinstance(probe.get("params"), dict) else {}
    for name, value in rclpy_params.items():
        normalized = normalize_param_artifact_value(value)
        if normalized is not None:
            params[name] = normalized
    dynamic_text = extract_section(stdout, "TF_ONCE")
    static_text = extract_section(stdout, "TF_STATIC_ONCE")
    probe_command_statuses = probe.get("command_statuses") if isinstance(probe.get("command_statuses"), dict) else {}
    command_statuses = {
        "topic_list": parse_section_status(stdout, "TOPIC_LIST_STATUS"),
        "tf_static": parse_section_status(stdout, "TF_STATIC_STATUS"),
        "tf": parse_section_status(stdout, "TF_STATUS"),
    }
    if probe_command_statuses:
        command_statuses = {
            "topic_list": probe_command_statuses.get("rclpy_graph"),
            "tf_static": probe_command_statuses.get("tf_static"),
            "tf": probe_command_statuses.get("tf"),
        }
    dynamic_edges = parse_tf_edges(dynamic_text, source_topic="/tf")
    static_edges = parse_tf_edges(static_text, source_topic="/tf_static")
    dynamic_transforms = parse_tf_topic_transforms(dynamic_text, source_topic="/tf")
    static_transforms = parse_tf_topic_transforms(static_text, source_topic="/tf_static")
    if isinstance(probe.get("dynamic_edges"), list):
        dynamic_edges = [edge for edge in probe["dynamic_edges"] if isinstance(edge, dict)]
    if isinstance(probe.get("static_edges"), list):
        static_edges = [edge for edge in probe["static_edges"] if isinstance(edge, dict)]
    if isinstance(probe.get("dynamic_transforms"), list):
        dynamic_transforms = [transform for transform in probe["dynamic_transforms"] if isinstance(transform, dict)]
    if isinstance(probe.get("static_transforms"), list):
        static_transforms = [transform for transform in probe["static_transforms"] if isinstance(transform, dict)]
    edges = [*dynamic_edges, *static_edges]
    transforms = [*dynamic_transforms, *static_transforms]
    frames = sorted({value for edge in edges for value in (edge.get("parent"), edge.get("child")) if value})
    frame_ids = tf_chain_frame_contract(args)["actual"]
    map_to_odom_source_observed = edge_observed(dynamic_edges, "map", frame_ids["odom"])
    # 真实底盘里程计通常在 /tf 动态发布 odom->base_link；no-motion smoke 才可能使用 /tf_static 兜底。
    odom_to_base_dynamic_observed = edge_observed(dynamic_edges, frame_ids["odom"], frame_ids["base"])
    odom_to_base_static_observed = edge_observed(static_edges, frame_ids["odom"], frame_ids["base"])
    odom_to_base_source_observed = bool(odom_to_base_dynamic_observed or odom_to_base_static_observed)
    base_to_laser_source_observed = edge_observed(static_edges, frame_ids["base"], frame_ids["laser"])
    base_to_laser_source_transform = find_tf_topic_transform(
        static_transforms,
        parent_frame_id=frame_ids["base"],
        child_frame_id=frame_ids["laser"],
    )
    param_probe_ok = bool(probe.get("param_probe_ok") or all(params.get(name) is not None for name in ("tf_broadcast", "global_frame_id", "odom_frame_id", "base_frame_id")))
    amcl_publishers = (
        probe.get("publishers")
        if isinstance(probe.get("publishers"), list) and probe.get("publishers")
        else parse_node_info_topics(amcl_info, "Publishers")
    )
    amcl_subscribers = (
        probe.get("subscribers")
        if isinstance(probe.get("subscribers"), list) and probe.get("subscribers")
        else parse_node_info_topics(amcl_info, "Subscribers")
    )
    tf_endpoint_summary = (
        topic_endpoints.get("/tf")
        if isinstance(topic_endpoints.get("/tf"), dict)
        else {
            "publishers": [],
            "subscribers": [],
            "publisher_count": 0,
            "subscriber_count": 0,
            "inventory_observed": False,
            "error": {"type": "tf_endpoint_inventory_missing", "message": "current probe did not return /tf endpoints"},
        }
    )
    publisher_attribution = tf_map_to_odom_publisher_attribution(
        dynamic_source_observed=map_to_odom_source_observed,
        tf_endpoint_summary=tf_endpoint_summary,
        amcl_publishers=amcl_publishers,
    )
    node_info_observed = bool(probe.get("node_info_observed") or amcl_publishers or amcl_subscribers)
    amcl_pose_sample = (
        dict(probe["amcl_pose_sample"])
        if isinstance(probe.get("amcl_pose_sample"), dict)
        else {
            "observed": False,
            "sample_count": 0,
            "received_at_ms": None,
            "frame_id": None,
            "stamp": {"parsed": False, "reason": "sample_not_observed", "source": "/amcl_pose.header.stamp"},
        }
    )
    amcl_pose_frame_id = str(amcl_pose_sample.get("frame_id") or "") or parse_pose_frame_id(
        str(amcl_pose_result.get("stdout") or "")
    )
    root_cause = "source_inventory_observed"
    if "/tf" not in topic_types and command_statuses["topic_list"] not in (0, None):
        root_cause = "tf_topic_list_timeout_or_unavailable"
    elif "/tf" not in topic_types:
        root_cause = "/tf_topic_missing"
    elif not node_info_observed:
        root_cause = "amcl_node_info_not_observed"
    elif not param_probe_ok:
        root_cause = "amcl_param_probe_failed"
    elif params.get("tf_broadcast", "").lower() in {"false", "0"}:
        root_cause = "amcl_tf_broadcast_disabled"
    elif params.get("global_frame_id") and params.get("global_frame_id") != "map":
        root_cause = "amcl_global_frame_id_mismatch"
    elif params.get("odom_frame_id") and params.get("odom_frame_id") != frame_ids["odom"]:
        root_cause = "amcl_odom_frame_id_mismatch"
    elif params.get("base_frame_id") and params.get("base_frame_id") != frame_ids["base"]:
        root_cause = "amcl_base_frame_id_mismatch"
    elif not map_to_odom_source_observed:
        root_cause = "amcl_map_to_odom_tf_not_observed_on_tf"
    elif publisher_attribution["publisher_attribution_status"] != "attributed_to_amcl_graph_endpoint":
        root_cause = str(publisher_attribution["publisher_attribution_status"])
    elif not odom_to_base_source_observed:
        root_cause = "odom_to_base_link_tf_not_observed"
    elif not base_to_laser_source_observed:
        root_cause = "base_link_to_laser_frame_static_tf_not_observed"
    detail = {
        "reason": root_cause,
        "amcl_param_probe_boundary": probe.get("boundary"),
        "amcl_param_probe_error": probe.get("error") if isinstance(probe.get("error"), dict) else None,
        "tf_command_statuses": command_statuses,
        "amcl_node_info_observed": node_info_observed,
        "amcl_param_probe_ok": param_probe_ok,
        "expected_params": {
            "tf_broadcast": "true",
            "global_frame_id": "map",
            "odom_frame_id": frame_ids["odom"],
            "base_frame_id": frame_ids["base"],
        },
        "observed_params": {
            "tf_broadcast": params.get("tf_broadcast"),
            "global_frame_id": params.get("global_frame_id"),
            "odom_frame_id": params.get("odom_frame_id"),
            "base_frame_id": params.get("base_frame_id"),
        },
        "amcl_pose_frame_id": amcl_pose_frame_id,
        "amcl_pose_sample": amcl_pose_sample,
        "map_to_odom_source_observed": map_to_odom_source_observed,
        "map_to_odom_publisher_attribution": publisher_attribution,
        "odom_to_base_link_source_observed": odom_to_base_source_observed,
        "odom_to_base_link_dynamic_source_observed": odom_to_base_dynamic_observed,
        "odom_to_base_link_static_source_observed": odom_to_base_static_observed,
        "base_link_to_laser_frame_source_observed": base_to_laser_source_observed,
        "base_link_to_laser_frame_source_transform": base_to_laser_source_transform,
    }
    conditions = {
        "initialpose_published": None,
        "amcl_pose_observed": bool(amcl_pose_frame_id),
        "amcl_pose_frame_id_is_map": amcl_pose_frame_id == "map",
        "tf_broadcast_enabled": params.get("tf_broadcast", "").lower() not in {"false", "0", ""},
        "amcl_frame_params_match_helper": bool(
            params.get("global_frame_id") == "map"
            and params.get("odom_frame_id") == frame_ids["odom"]
            and params.get("base_frame_id") == frame_ids["base"]
        ),
        "map_to_odom_source_observed": map_to_odom_source_observed,
        "map_to_odom_publisher_attribution": publisher_attribution,
        "odom_to_base_link_source_observed": odom_to_base_source_observed,
        "odom_to_base_link_dynamic_source_observed": odom_to_base_dynamic_observed,
        "odom_to_base_link_static_source_observed": odom_to_base_static_observed,
        "base_link_to_laser_frame_source_observed": base_to_laser_source_observed,
        "scan_once_observed": None,
        "map_once_observed": None,
    }
    return {
        "tf_topics_observed": {"/tf": "/tf" in topic_types, "/tf_static": "/tf_static" in topic_types},
        "tf_static_observed": bool(static_edges),
        "tf_frame_inventory": {
            "frames": frames,
            "edges": edges,
            "dynamic_edges": dynamic_edges,
            "static_edges": static_edges,
            "dynamic_transforms": dynamic_transforms,
            "static_transforms": static_transforms,
            "transforms": transforms,
            "topic_types": topic_types,
            "command_statuses": command_statuses,
        },
        "topic_endpoint_summaries": {
            topic: topic_endpoints.get(
                topic,
                {"publishers": [], "subscribers": [], "publisher_count": 0, "subscriber_count": 0, "error": None},
            )
            for topic in LOCALIZATION_SIGNAL_TOPICS
        },
        "amcl_pose_frame_id": amcl_pose_frame_id,
        "amcl_pose_sample": amcl_pose_sample,
        "amcl_node_publishers": amcl_publishers,
        "amcl_node_subscribers": amcl_subscribers,
        "amcl_param_probe_ok": param_probe_ok,
        "amcl_node_info_observed": node_info_observed,
        "amcl_tf_broadcast_param": params.get("tf_broadcast"),
        "amcl_frame_params": {
            "global_frame_id": params.get("global_frame_id"),
            "odom_frame_id": params.get("odom_frame_id"),
            "base_frame_id": params.get("base_frame_id"),
        },
        "map_frame_observed": "map" in frames,
        "odom_frame_observed": frame_ids["odom"] in frames,
        "base_frame_observed": frame_ids["base"] in frames,
        "laser_frame_observed": frame_ids["laser"] in frames,
        "map_to_odom_source_observed": map_to_odom_source_observed,
        "map_to_odom_publisher_attribution": publisher_attribution,
        "odom_to_base_link_source_observed": odom_to_base_source_observed,
        "odom_to_base_link_dynamic_source_observed": odom_to_base_dynamic_observed,
        "odom_to_base_link_static_source_observed": odom_to_base_static_observed,
        "base_link_to_laser_frame_source_observed": base_to_laser_source_observed,
        "base_link_to_laser_frame_source_transform": base_to_laser_source_transform,
        "amcl_tf_root_cause": root_cause,
        "tf_source_root_cause_detail": detail,
        "amcl_broadcast_conditions": conditions,
        "frame_contract": tf_chain_frame_contract(args),
    }


def build_tf_chain_diagnostics(
    *,
    args: argparse.Namespace,
    results: dict[str, dict[str, Any]],
    observed: dict[str, bool],
    tf_source_diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """保存每段 TF 的 source/target/原因；命令正文留在 commands，摘要留在顶层。"""
    frame_contract = tf_chain_frame_contract(args)
    frames = frame_contract["actual"]
    pairs = {
        "map_to_odom": ("map", frames["odom"]),
        "odom_to_base_link": (frames["odom"], frames["base"]),
        "base_link_to_laser_frame": (frames["base"], frames["laser"]),
        "map_to_base_link": ("map", frames["base"]),
    }
    diagnostics: dict[str, Any] = {
        "frame_contract": frame_contract,
        "pairs": {},
        "source_diagnostics": tf_source_diagnostics or {},
    }
    for key, (source, target) in pairs.items():
        result = results.get(key, {"executed": False, "ok": False})
        diagnostics["pairs"][key] = {
            "source_frame": source,
            "target_frame": target,
            "observed": bool(observed.get(key)),
            "executed": bool(result.get("executed")),
            "returncode": result.get("returncode"),
            "elapsed_ms": result.get("elapsed_ms"),
            "failure_reason": tf_probe_result_reason(result),
            "boundary": result.get("boundary"),
            "error": result.get("error") if isinstance(result.get("error"), dict) else None,
            "stdout_preview": str(result.get("stdout") or "")[-400:],
            "stderr_preview": str(result.get("stderr") or "")[-400:],
        }
    return diagnostics


def tf_segment_root_cause(
    diagnostics: dict[str, Any],
    segment: str,
    *,
    layer: str = "Localization TF",
) -> dict[str, str]:
    """每段 TF 失败都写 source/detail，避免 timeout 时只知道最后卡在哪条命令。"""
    pairs = diagnostics.get("pairs") if isinstance(diagnostics.get("pairs"), dict) else {}
    detail = pairs.get(segment) if isinstance(pairs.get(segment), dict) else {}
    return {
        "layer": layer,
        "reason": f"{segment}_not_observed",
        "source": segment,
        "detail": str(detail.get("failure_reason") or "not_observed"),
    }


def classify_tf_chain_failure(
    *,
    args: argparse.Namespace,
    observed: dict[str, bool],
    diagnostics: dict[str, Any],
) -> dict[str, Any]:
    """把 `map->base_link` 失败下钻到缺 map、缺 odom/base、命名或 timing。"""
    frame_contract = diagnostics.get("frame_contract") if isinstance(diagnostics.get("frame_contract"), dict) else tf_chain_frame_contract(args)
    pairs = diagnostics.get("pairs") if isinstance(diagnostics.get("pairs"), dict) else {}
    source_diagnostics = diagnostics.get("source_diagnostics") if isinstance(diagnostics.get("source_diagnostics"), dict) else {}
    classification: dict[str, Any] = {
        "map_to_base_link": "observed" if observed.get("map_to_base_link") else "not_observed",
        "frame_naming_consistent": bool(frame_contract.get("consistent_with_defaults")),
        "blocking_segment": None,
        "reason": None,
        "amcl_tf_root_cause": source_diagnostics.get("amcl_tf_root_cause"),
    }
    if not classification["frame_naming_consistent"]:
        classification.update(
            {
                "map_to_base_link": "frame_naming_mismatch",
                "blocking_segment": "frame_contract",
                "reason": "managed_frame_ids_differ_from_expected_defaults",
            }
        )
        return classification
    if observed.get("map_to_base_link"):
        classification["reason"] = "complete_chain_observed"
        return classification
    if not observed.get("map_to_odom"):
        source_reason = source_diagnostics.get("amcl_tf_root_cause")
        classification.update(
            {
                "map_to_base_link": "blocked_by_missing_map_to_odom",
                "blocking_segment": "map_to_odom",
                "reason": source_reason or pairs.get("map_to_odom", {}).get("failure_reason", "map_to_odom_not_observed"),
            }
        )
        return classification
    if not observed.get("odom_to_base_link"):
        classification.update(
            {
                "map_to_base_link": "blocked_by_missing_odom_to_base_link",
                "blocking_segment": "odom_to_base_link",
                "reason": pairs.get("odom_to_base_link", {}).get("failure_reason", "odom_to_base_link_not_observed"),
            }
        )
        return classification
    classification.update(
        {
            "map_to_base_link": "tf2_timeout_or_chain_timing",
            "blocking_segment": "map_to_base_link",
            "reason": pairs.get("map_to_base_link", {}).get("failure_reason", "tf2_timeout_or_timing"),
        }
    )
    return classification


def tf_chain_root_causes(classification: dict[str, Any], observed: dict[str, bool]) -> list[dict[str, str]]:
    """root_causes 只写会阻塞定位 reset 的链路段，laser 静态 TF 作为独立诊断。"""
    causes: list[dict[str, str]] = []
    state = str(classification.get("map_to_base_link") or "")
    blocking_segment = str(classification.get("blocking_segment") or "")
    reason = str(classification.get("reason") or state)
    if state not in {"", "observed"}:
        causes.append(
            {
                "layer": "Localization TF",
                "reason": f"map_to_base_link_{state}",
                "source": blocking_segment or "map_to_base_link",
                "detail": reason,
            }
        )
    if not observed.get("base_link_to_laser_frame"):
        causes.append(
            {
                "layer": "Managed static TF",
                "reason": "base_link_to_laser_frame_not_observed",
                "source": "base_link_to_laser_frame",
                "detail": "static_lidar_tf_missing_or_not_yet_observed",
            }
        )
    return causes


def package_checks(args: argparse.Namespace) -> tuple[dict[str, bool], dict[str, dict[str, Any]], dict[str, Any]]:
    """Nav2 包检查只做单次 source 的批量诊断，避免 preflight 吃掉定位主路径预算。"""
    available: dict[str, bool] = {}
    results: dict[str, dict[str, Any]] = {}
    command = "ros2 pkg list"
    batch_result = run_ros(args, command, timeout_s=PACKAGE_CHECK_BATCH_TIMEOUT_S)
    installed_packages = {
        line.strip()
        for line in str(batch_result.get("stdout") or "").splitlines()
        if line.strip()
    }
    for package in EXPECTED_PACKAGES:
        ok = bool(batch_result.get("ok") and package in installed_packages)
        available[package] = ok
        results[package] = {
            "command": f"ros2 pkg list contains {package}",
            "executed": bool(batch_result.get("executed")),
            "ok": ok,
            "returncode": batch_result.get("returncode"),
            "elapsed_ms": batch_result.get("elapsed_ms"),
            "stdout": package if ok else "",
            "stderr": "" if ok else f"{package} not found in ros2 pkg list",
            "diagnostic_mode": "single_sourced_pkg_list_package_check",
            "batch_command": command,
        }
    return available, results, batch_result


def parse_lifecycle_active(result: dict[str, Any]) -> bool:
    """ROS2 lifecycle get 的 stdout 若已出现 active，就按 active stdout 采信。"""
    text = f"{result.get('stdout') or ''}\n{result.get('stderr') or ''}".lower()
    for line in text.splitlines():
        normalized = line.strip()
        if normalized == "active" or normalized.startswith("active "):
            return True
        if normalized.endswith(": active") or normalized.endswith(" state active"):
            return True
    return False


def lifecycle_result_is_skipped(result: dict[str, Any]) -> bool:
    """未执行的 lifecycle probe 只能算 skipped，不能被写成已证明 inactive。"""
    if result.get("executed") is True:
        return False
    boundary = str(result.get("boundary") or "")
    return bool(
        result.get("executed") is False
        or "not_run" in boundary
        or "skipped" in boundary
        or "graph_wait_blocked" in boundary
    )


def lifecycle_retry_timeout_s(args: argparse.Namespace) -> float:
    """retry 预算复用现场 `--timeout-s`，但限制上限，避免单条 CLI 无限拖住 proof。"""
    requested = float(getattr(args, "timeout_s", LIFECYCLE_CLI_RETRY_MIN_TIMEOUT_S))
    return min(max(requested, LIFECYCLE_CLI_RETRY_MIN_TIMEOUT_S), LIFECYCLE_CLI_RETRY_MAX_TIMEOUT_S)


def lifecycle_graph_visibility_snapshot(
    args: argparse.Namespace,
    nodes: dict[str, str],
    *,
    graph_probe_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """给 lifecycle readback 旁路记录 graph 可见性，避免把 RPC timeout 误判成节点缺失。"""
    if graph_probe_result is None:
        graph_probe_result = run_ros(args, "ros2 node list", timeout_s=LIFECYCLE_GRAPH_VISIBILITY_TIMEOUT_S)
    observed = sorted(node_names_from_graph_result(graph_probe_result))
    target_nodes = {
        key: {
            "node": normalize_ros_node_name(node),
            "visible": normalize_ros_node_name(node) in set(observed),
        }
        for key, node in nodes.items()
    }
    return {
        "schema": "trashbot.o10.lifecycle_cli_graph_visibility.v1",
        "command": graph_probe_result.get("command", "ros2 node list"),
        "executed": bool(graph_probe_result.get("executed")),
        "ok": bool(graph_probe_result.get("ok")),
        "returncode": graph_probe_result.get("returncode"),
        "timed_out": bool(graph_probe_result.get("timed_out")),
        "timeout_s": graph_probe_result.get("timeout_s"),
        "elapsed_ms": graph_probe_result.get("elapsed_ms"),
        "boundary": graph_probe_result.get("boundary"),
        "observed_node_names": observed,
        "target_nodes": target_nodes,
    }


def lifecycle_attempt_classification(
    result: dict[str, Any],
    *,
    active: bool,
    graph_node_visible: bool,
) -> str:
    """把单次 lifecycle get 归入本轮要求的 active/inactive/timeout 分层。"""
    if lifecycle_result_is_skipped(result):
        return "lifecycle probe skipped"
    stdout = str(result.get("stdout") or "")
    stderr = str(result.get("stderr") or "")
    text = f"{stdout}\n{stderr}".lower()
    if active:
        return "active"
    if result.get("timed_out") or result.get("returncode") == 124:
        return "graph ok but lifecycle timeout" if graph_node_visible else "lifecycle_command_timeout"
    if "inactive" in text or "unconfigured" in text:
        return "inactive stdout"
    if result.get("executed"):
        return "lifecycle command failed"
    return "lifecycle not active"


def lifecycle_attempt_summary(
    *,
    label: str,
    node_key: str,
    node_name: str,
    result: dict[str, Any],
    graph_node_visible: bool,
) -> dict[str, Any]:
    """保留 lifecycle CLI 原始读数；stdout/stderr 截断但不丢 command、预算和返回码。"""
    active = parse_lifecycle_active(result)
    return {
        "label": label,
        "node_key": node_key,
        "node": node_name,
        "command": result.get("command") or f"ros2 lifecycle get {node_name}",
        "executed": bool(result.get("executed")),
        "ok": bool(result.get("ok")),
        "active": active,
        "classification": lifecycle_attempt_classification(
            result,
            active=active,
            graph_node_visible=graph_node_visible,
        ),
        "timeout_s": result.get("timeout_s"),
        "elapsed_ms": result.get("elapsed_ms"),
        "returncode": result.get("returncode"),
        "timed_out": bool(result.get("timed_out") or result.get("returncode") == 124),
        "stdout": str(result.get("stdout") or "")[-8000:],
        "stderr": str(result.get("stderr") or "")[-4000:],
        "error": result.get("error") if isinstance(result.get("error"), dict) else None,
    }


def lifecycle_recovery_result(
    args: argparse.Namespace,
    *,
    node_key: str,
    node_name: str,
    graph_visibility: dict[str, Any],
) -> dict[str, Any]:
    """执行 first/retry lifecycle readback，并把最终结果保持成 legacy result 兼容形状。"""
    normalized_node = normalize_ros_node_name(node_name)
    target = (graph_visibility.get("target_nodes") or {}).get(node_key)
    graph_node_visible = bool(target.get("visible")) if isinstance(target, dict) else normalized_node in set(graph_visibility.get("observed_node_names") or [])
    command = f"ros2 lifecycle get {shlex.quote(node_name)}"
    first = run_ros(args, command, timeout_s=LIFECYCLE_CLI_FIRST_ATTEMPT_TIMEOUT_S)
    first_summary = lifecycle_attempt_summary(
        label="first_attempt",
        node_key=node_key,
        node_name=node_name,
        result=first,
        graph_node_visible=graph_node_visible,
    )
    retry: dict[str, Any] | None = None
    retry_summary: dict[str, Any] | None = None
    final = first
    final_summary = first_summary
    if not first_summary["active"]:
        # 非 active 才 retry；active 已经是 clean readback，继续重复只会浪费现场窗口。
        retry = run_ros(args, command, timeout_s=lifecycle_retry_timeout_s(args))
        retry_summary = lifecycle_attempt_summary(
            label="retry_attempt",
            node_key=node_key,
            node_name=node_name,
            result=retry,
            graph_node_visible=graph_node_visible,
        )
        final = retry
        final_summary = retry_summary
    else:
        retry_summary = {
            "label": "retry_attempt",
            "node_key": node_key,
            "node": node_name,
            "command": command,
            "executed": False,
            "ok": True,
            "active": True,
            "classification": "retry skipped after active first attempt",
            "timeout_s": lifecycle_retry_timeout_s(args),
            "elapsed_ms": 0,
            "returncode": None,
            "timed_out": False,
            "stdout": "",
            "stderr": "",
            "error": None,
        }
    summary = {
        "schema": "trashbot.o10.lifecycle_cli_budget_recovery.v1",
        "strategy": "lifecycle_cli_budget_recovery",
        "node_key": node_key,
        "node": node_name,
        "command": command,
        "graph_visibility": graph_visibility,
        "graph_node_visible": graph_node_visible,
        "first_attempt": first_summary,
        "retry_attempt": retry_summary,
        "attempts": [first_summary] + ([retry_summary] if retry_summary and retry_summary.get("executed") else []),
        "final_attempt_label": str(final_summary.get("label") or "first_attempt"),
        "classification": final_summary["classification"],
        "clean": bool(final_summary["active"]),
        "timeout_budget_s": {
            "first_attempt": LIFECYCLE_CLI_FIRST_ATTEMPT_TIMEOUT_S,
            "retry_attempt": lifecycle_retry_timeout_s(args),
        },
        "next_step": (
            "lifecycle_readback_clean_continue_downstream_no_motion"
            if final_summary["active"]
            else "inspect_lifecycle_manager_or_node_state_after_graph_visible_timeout"
            if graph_node_visible and final_summary["classification"] == "graph ok but lifecycle timeout"
            else "inspect_lifecycle_node_state_or_activation"
            if final_summary["classification"] == "inactive stdout"
            else "inspect_ros2_cli_budget_daemon_or_process_graph"
        ),
    }
    result = dict(final)
    result["active"] = bool(final_summary["active"])
    result["classification"] = summary["classification"]
    result["graph_node_visible"] = graph_node_visible
    result["first_attempt"] = first_summary
    result["retry_attempt"] = retry_summary
    result["attempts"] = summary["attempts"]
    result["command_summary"] = summary
    result["lifecycle_cli_budget_recovery"] = summary
    return result


def lifecycle_node_blocked_reason(name: str, active: bool, result: dict[str, Any]) -> str | None:
    """把 lifecycle 失败拆成 timeout、inactive stdout 和命令失败三类，方便下一轮直接派工。"""
    if active:
        return None
    if lifecycle_result_is_skipped(result):
        return f"{name}_lifecycle_probe_skipped"
    classification = str((result.get("command_summary") or {}).get("classification") or result.get("classification") or "")
    if classification in {"lifecycle_command_timeout", "graph ok but lifecycle timeout"}:
        return f"{name}_lifecycle_command_timeout"
    if classification == "inactive stdout":
        return f"{name}_lifecycle_inactive_stdout"
    stdout = str(result.get("stdout") or "").strip()
    stderr = str(result.get("stderr") or "").strip()
    text = f"{stdout}\n{stderr}".lower()
    if result.get("timed_out") or result.get("returncode") == 124:
        return f"{name}_lifecycle_command_timeout"
    if "inactive" in text:
        return f"{name}_lifecycle_inactive_stdout"
    if "unconfigured" in text:
        return f"{name}_lifecycle_unconfigured_stdout"
    if "active" in text:
        return f"{name}_lifecycle_active_parse_failed"
    if result.get("executed"):
        return f"{name}_lifecycle_command_failed"
    return f"{name}_lifecycle_not_active"


def lifecycle_node_summary(name: str, active: bool, result: dict[str, Any]) -> dict[str, Any]:
    """压缩单个 lifecycle probe，stdout 只保留尾部，避免 artifact 被 CLI 原文淹没。"""
    blocked_reason = lifecycle_node_blocked_reason(name, active, result)
    if active:
        failure_mode = None
    elif blocked_reason and blocked_reason.endswith("_command_timeout"):
        failure_mode = "command_timeout"
    elif blocked_reason and ("inactive_stdout" in blocked_reason or "unconfigured_stdout" in blocked_reason):
        failure_mode = "inactive_stdout"
    elif blocked_reason and blocked_reason.endswith("_probe_skipped"):
        failure_mode = "probe_skipped"
    elif blocked_reason and blocked_reason.endswith("_command_failed"):
        failure_mode = "command_failed"
    else:
        failure_mode = "not_active"
    return {
        "node": name,
        "active": bool(active),
        "executed": bool(result.get("executed")),
        "ok": bool(result.get("ok")),
        "returncode": result.get("returncode"),
        "timed_out": bool(result.get("timed_out") or result.get("returncode") == 124),
        "stdout_tail": str(result.get("stdout") or "")[-240:],
        "stderr_tail": str(result.get("stderr") or "")[-240:],
        "boundary": result.get("boundary"),
        "failure_mode": failure_mode,
        "blocked_reason": blocked_reason,
        "legacy_blocked_reason": None if active else f"{name}_lifecycle_not_active",
        "command_summary": result.get("command_summary") if isinstance(result.get("command_summary"), dict) else None,
        "lifecycle_cli_budget_recovery": (
            result.get("lifecycle_cli_budget_recovery")
            if isinstance(result.get("lifecycle_cli_budget_recovery"), dict)
            else None
        ),
    }


def build_map_lifecycle_preflight(
    *,
    ros2_cli_ok: bool,
    lifecycle_active: dict[str, bool],
    lifecycle_results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """把 map_server/amcl lifecycle 压成短摘要，避免现场只剩泛化 source blocker。"""
    node_summaries = {
        name: lifecycle_node_summary(
            name,
            bool(lifecycle_active.get(name)),
            lifecycle_results.get(name) if isinstance(lifecycle_results.get(name), dict) else {},
        )
        for name in ("map_server", "amcl")
    }
    blocking_reasons = {
        name: summary.get("blocked_reason")
        for name, summary in node_summaries.items()
        if summary.get("blocked_reason")
    }
    if not ros2_cli_ok:
        skipped_result = {
            "executed": False,
            "ok": False,
            "boundary": "map_lifecycle_preflight_skipped_without_ros2_cli",
        }
        node_summaries = {
            name: lifecycle_node_summary(name, False, skipped_result)
            for name in ("map_server", "amcl")
        }
        blocking_reasons = {
            name: summary.get("blocked_reason")
            for name, summary in node_summaries.items()
            if summary.get("blocked_reason")
        }
        return {
            "executed": False,
            "map_server_active": False,
            "amcl_active": False,
            "classification": "map_lifecycle_preflight_skipped_without_ros2_cli",
            "root_causes": [],
            "node_summaries": node_summaries,
            "blocking_reasons": blocking_reasons,
            "lifecycle_cli_budget_recovery": {},
            "command_summaries": {},
            "results": {},
        }
    map_server_active = bool(lifecycle_active.get("map_server"))
    amcl_active = bool(lifecycle_active.get("amcl"))
    skipped_nodes = [
        name
        for name in ("map_server", "amcl")
        if not lifecycle_active.get(name)
        and lifecycle_result_is_skipped(lifecycle_results.get(name) if isinstance(lifecycle_results.get(name), dict) else {})
    ]
    if map_server_active and amcl_active:
        classification = "map_lifecycle_preflight_all_active"
        root_causes: list[dict[str, str]] = []
    elif skipped_nodes and len(skipped_nodes) == len([name for name in ("map_server", "amcl") if not lifecycle_active.get(name)]):
        classification = "map_lifecycle_preflight_lifecycle_probe_skipped_after_graph_blocked"
        root_causes = []
    else:
        failed = [name for name in ("map_server", "amcl") if not lifecycle_active.get(name) and name not in skipped_nodes]
        classification = "map_lifecycle_preflight_" + "_and_".join(failed) + "_inactive"
        root_causes = [
            {"layer": "Nav2 lifecycle", "reason": f"{name}_lifecycle_not_active_during_preflight"}
            for name in failed
        ]
    return {
        "executed": True,
        "map_server_active": map_server_active,
        "amcl_active": amcl_active,
        "classification": classification,
        "root_causes": root_causes,
        "skipped_nodes": skipped_nodes,
        "node_summaries": node_summaries,
        "blocking_reasons": blocking_reasons,
        "lifecycle_cli_budget_recovery": {
            name: summary.get("lifecycle_cli_budget_recovery")
            for name, summary in node_summaries.items()
            if summary.get("lifecycle_cli_budget_recovery")
        },
        "command_summaries": {
            name: summary.get("command_summary")
            for name, summary in node_summaries.items()
            if summary.get("command_summary")
        },
        "results": lifecycle_results,
    }


def command_result_evidence(result: dict[str, Any]) -> dict[str, Any]:
    """保留命令可验收字段；stdout/stderr 截尾但不丢预算、耗时和返回码。"""
    return {
        "command": result.get("command"),
        "executed": bool(result.get("executed")),
        "ok": bool(result.get("ok")),
        "returncode": result.get("returncode"),
        "timed_out": bool(result.get("timed_out") or result.get("returncode") == 124),
        "timeout_s": result.get("timeout_s"),
        "elapsed_ms": result.get("elapsed_ms"),
        "boundary": result.get("boundary"),
        "stdout": str(result.get("stdout") or "")[-4000:],
        "stderr": str(result.get("stderr") or "")[-4000:],
        "error": result.get("error") if isinstance(result.get("error"), dict) else None,
    }


def lifecycle_summary_for_node(map_lifecycle_preflight: dict[str, Any], node_key: str) -> dict[str, Any]:
    """优先使用新 command_summary；缺失时从 legacy lifecycle result 回填最小可读形状。"""
    command_summaries = (
        map_lifecycle_preflight.get("command_summaries")
        if isinstance(map_lifecycle_preflight.get("command_summaries"), dict)
        else {}
    )
    summary = command_summaries.get(node_key) if isinstance(command_summaries.get(node_key), dict) else {}
    if summary:
        return summary
    results = map_lifecycle_preflight.get("results") if isinstance(map_lifecycle_preflight.get("results"), dict) else {}
    result = results.get(node_key) if isinstance(results.get(node_key), dict) else {}
    if not result:
        return {}
    node_name = LOCALIZATION_LIFECYCLE_NODES.get(node_key, f"/{node_key}")
    # 旧 artifact 没有 first/retry 分层时，也要暴露同名字段，避免 consumer 需要猜结构版本。
    attempt = lifecycle_attempt_summary(
        label="legacy_single_attempt",
        node_key=node_key,
        node_name=node_name,
        result=result,
        graph_node_visible=bool(result.get("graph_node_visible")),
    )
    return {
        "schema": "trashbot.o10.lifecycle_cli_budget_recovery.v1",
        "strategy": "legacy_lifecycle_result_backfill",
        "node_key": node_key,
        "node": node_name,
        "command": result.get("command") or f"ros2 lifecycle get {node_name}",
        "graph_visibility": {},
        "graph_node_visible": bool(result.get("graph_node_visible")),
        "first_attempt": attempt,
        "retry_attempt": {
            "label": "retry_attempt",
            "node_key": node_key,
            "node": node_name,
            "command": result.get("command") or f"ros2 lifecycle get {node_name}",
            "executed": False,
            "ok": False,
            "active": False,
            "classification": "retry_not_recorded_in_legacy_result",
            "timeout_s": None,
            "elapsed_ms": 0,
            "returncode": None,
            "timed_out": False,
            "stdout": "",
            "stderr": "",
            "error": None,
        },
        "attempts": [attempt],
        "final_attempt_label": "legacy_single_attempt",
        "classification": attempt["classification"],
        "clean": bool(attempt["active"]),
        "timeout_budget_s": {"first_attempt": attempt.get("timeout_s"), "retry_attempt": None},
        "next_step": "inspect_lifecycle_node_state_or_activation",
    }


def command_probe_brief(probes: dict[str, Any], key: str) -> dict[str, Any]:
    """daemon/DDS summary 只摘稳定 probe 字段，避免复制完整 batch 造成 artifact 过大。"""
    probe = probes.get(key) if isinstance(probes.get(key), dict) else {}
    if not probe:
        return {}
    return {
        "command": probe.get("command"),
        "executed": bool(probe.get("executed")),
        "ok": bool(probe.get("ok")),
        "returncode": probe.get("returncode"),
        "timed_out": bool(probe.get("timed_out") or probe.get("returncode") == 124),
        "timeout_s": probe.get("timeout_s"),
        "elapsed_ms": probe.get("elapsed_ms"),
        "boundary": probe.get("boundary"),
        "stdout_tail": str(probe.get("stdout") or "")[-800:],
        "stderr_tail": str(probe.get("stderr") or "")[-800:],
    }


def map_server_visibility_observed_nodes(
    *,
    graph_visibility: dict[str, Any],
    managed_wait: dict[str, Any],
    graph_probes: dict[str, Any],
) -> list[str]:
    """合并 lifecycle、managed wait 和 daemon-safe probes 的 graph inventory。"""
    observed: set[str] = set()
    observed.update(node_names_from_graph_result({"node_names": graph_visibility.get("observed_node_names") or []}))
    observed.update(node_names_from_graph_result({"node_names": managed_wait.get("observed_node_names") or []}))
    observed.update(node_names_from_graph_result(graph_probes.get("ros2_node_list") or {}))
    daemon_split = graph_probes.get("daemon_dds_split") if isinstance(graph_probes.get("daemon_dds_split"), dict) else {}
    readback = daemon_split.get("daemon_safe_graph_readback") if isinstance(daemon_split.get("daemon_safe_graph_readback"), dict) else {}
    graph_readback = readback.get("graph_readback") if isinstance(readback.get("graph_readback"), dict) else {}
    observed.update(node_names_from_graph_result({"node_names": graph_readback.get("node_names") or []}))
    return sorted(observed)


def lifecycle_summary_attempts_text(summary: dict[str, Any]) -> str:
    """把 first/retry stdout/stderr 合并成短文本，用来识别 `Node not found` 等稳定错误。"""
    chunks: list[str] = []
    for key in ("first_attempt", "retry_attempt"):
        attempt = summary.get(key) if isinstance(summary.get(key), dict) else {}
        chunks.append(str(attempt.get("stdout") or ""))
        chunks.append(str(attempt.get("stderr") or ""))
    chunks.append(str(summary.get("classification") or ""))
    chunks.append(str(summary.get("next_step") or ""))
    return "\n".join(chunks).lower()


def classify_map_server_graph_lifecycle_visibility(
    *,
    graph_visible: bool,
    observed_node_names: list[str],
    lifecycle_summary: dict[str, Any],
    managed_runtime_context: dict[str, Any],
    daemon_dds_visibility: dict[str, Any],
) -> tuple[str, str]:
    """输出本轮 canonical classification，并保留更细 failure_detail 供下一轮派工。"""
    if bool(lifecycle_summary.get("clean")) or bool((lifecycle_summary.get("first_attempt") or {}).get("active")):
        return "map_server_lifecycle_active", "map_server_lifecycle_readback_active"

    text = lifecycle_summary_attempts_text(lifecycle_summary)
    lifecycle_timed_out = any(
        bool((lifecycle_summary.get(key) or {}).get("timed_out"))
        for key in ("first_attempt", "retry_attempt")
        if isinstance(lifecycle_summary.get(key), dict)
    )
    if "node not found" in text:
        return "map_server_node_absent", "lifecycle_retry_node_not_found"
    if not graph_visible and "/map_server" not in observed_node_names and observed_node_names:
        return "map_server_node_absent", "node_graph_inventory_readable_without_map_server"

    graph_root_classification = str(daemon_dds_visibility.get("root_cause_classification") or "")
    daemon_primary = daemon_dds_visibility.get("daemon_dds_primary_candidate")
    daemon_candidate = str((daemon_primary or {}).get("candidate") or "")
    graph_probe_timed_out = any(
        bool((daemon_dds_visibility.get("probe_boundaries") or {}).get(key, {}).get("timed_out"))
        for key in ("ros2_node_list", "ros2_node_list_no_daemon", "ros2_daemon_status", "ros2_topic_list")
    )
    if (
        graph_root_classification == "ros2_daemon_or_dds_graph_discovery_timeout"
        or daemon_candidate in {"ros2_daemon_state_timeout", "dds_discovery_or_domain_mismatch"}
        or (graph_probe_timed_out and not observed_node_names)
    ):
        return "daemon_or_dds_graph_visibility_failed", "daemon_or_dds_graph_inventory_unreadable"

    startup_error = managed_runtime_context.get("startup_error")
    wait_reason = str(managed_runtime_context.get("wait_reason") or "")
    managed_runtime_claimed = bool(
        managed_runtime_context.get("requested")
        or managed_runtime_context.get("started")
        or startup_error
    )
    if (
        startup_error
        or (
            managed_runtime_claimed
            and (
                managed_runtime_context.get("process_alive") is False
                or wait_reason in {"managed_runtime_required_nodes_not_observed", "ros2_node_list_empty_after_wait"}
            )
        )
    ):
        return "lifecycle_manager_or_process_startup_missing", "managed_runtime_or_lifecycle_process_not_ready"

    if lifecycle_timed_out:
        if graph_visible:
            return "helper_budget_or_timing_exhausted", "graph_visible_lifecycle_command_timeout"
        return "helper_budget_or_timing_exhausted", "lifecycle_command_budget_or_observation_window_exhausted"

    if not graph_visible and "/map_server" not in observed_node_names:
        return "lifecycle_manager_or_process_startup_missing", "map_server_not_visible_without_daemon_timeout"

    return "helper_budget_or_timing_exhausted", "map_server_visibility_unclassified_after_bounded_readback"


def build_map_server_graph_lifecycle_visibility_summary(proof: dict[str, Any]) -> dict[str, Any]:
    """09-54 主 artifact：只读解释 `/map_server` graph/lifecycle visibility 的失败层级。"""
    board = proof.get("board_source_preflight") if isinstance(proof.get("board_source_preflight"), dict) else {}
    map_lifecycle = proof.get("map_lifecycle_preflight") if isinstance(proof.get("map_lifecycle_preflight"), dict) else {}
    lifecycle_summary = lifecycle_summary_for_node(map_lifecycle, "map_server")
    graph_visibility = lifecycle_summary.get("graph_visibility") if isinstance(lifecycle_summary.get("graph_visibility"), dict) else {}
    graph_target = (graph_visibility.get("target_nodes") or {}).get("map_server") if isinstance(graph_visibility.get("target_nodes"), dict) else {}
    commands = proof.get("commands") if isinstance(proof.get("commands"), dict) else {}
    managed_runtime = commands.get("managed_runtime") if isinstance(commands.get("managed_runtime"), dict) else {}
    managed_wait = proof.get("managed_runtime_wait_result") if isinstance(proof.get("managed_runtime_wait_result"), dict) else {}
    graph_root = proof.get("ros2_graph_timeout_root_cause") if isinstance(proof.get("ros2_graph_timeout_root_cause"), dict) else {}
    graph_root_probes = graph_root.get("probes") if isinstance(graph_root.get("probes"), dict) else {}
    graph_probes = {**graph_root_probes, "daemon_dds_split": graph_root.get("daemon_dds_split")}
    observed_node_names = map_server_visibility_observed_nodes(
        graph_visibility=graph_visibility,
        managed_wait=managed_wait,
        graph_probes=graph_probes,
    )
    graph_visible = bool(
        proof.get("map_server_active")
        or lifecycle_summary.get("graph_node_visible")
        or (isinstance(graph_target, dict) and graph_target.get("visible"))
        or "/map_server" in observed_node_names
    )
    process_summary = graph_root_probes.get("managed_process") if isinstance(graph_root_probes.get("managed_process"), dict) else {}
    managed_runtime_context = {
        "requested": bool(proof.get("managed_runtime_requested") or managed_runtime.get("requested")),
        "started": bool(proof.get("managed_runtime_started") or managed_runtime.get("started")),
        "boundary": proof.get("managed_runtime_boundary") or managed_runtime.get("boundary"),
        "process_group": proof.get("managed_runtime_process_group") or managed_runtime.get("process_group"),
        "process_alive": process_summary.get("process_alive"),
        "process_returncode": process_summary.get("process_returncode"),
        "startup_error": managed_runtime.get("startup_error"),
        "wait_reason": managed_wait.get("reason") or managed_wait.get("boundary"),
        "wait_ok": bool(managed_wait.get("ok")),
        "observed_nodes": observed_node_names,
        "missing_expected_nodes": process_summary.get("missing_expected_nodes") or [],
        "lifecycle_probe_status": process_summary.get("lifecycle_probe_status"),
        "lifecycle_probe_skipped": process_summary.get("lifecycle_probe_skipped") or {},
        "expected_process_names": ["nav2_map_server", "nav2_lifecycle_manager"],
        "log_tail": process_summary.get("log_tail") or managed_runtime.get("log_tail") or "",
    }
    daemon_dds_split = graph_root.get("daemon_dds_split") if isinstance(graph_root.get("daemon_dds_split"), dict) else {}
    daemon_dds_visibility = {
        "root_cause_classification": graph_root.get("classification"),
        "primary_candidate": graph_root.get("primary_candidate") if isinstance(graph_root.get("primary_candidate"), dict) else {},
        "daemon_dds_primary_candidate": daemon_dds_split.get("primary_candidate") if isinstance(daemon_dds_split.get("primary_candidate"), dict) else {},
        "daemon_safe_graph_readback": (
            daemon_dds_split.get("daemon_safe_graph_readback")
            if isinstance(daemon_dds_split.get("daemon_safe_graph_readback"), dict)
            else {}
        ),
        "probe_boundaries": {
            key: command_probe_brief(graph_root_probes, key)
            for key in ("ros2_node_list", "ros2_node_list_no_daemon", "ros2_daemon_status", "ros2_topic_list", "source_amortized_batch")
        },
    }
    classification, failure_detail = classify_map_server_graph_lifecycle_visibility(
        graph_visible=graph_visible,
        observed_node_names=observed_node_names,
        lifecycle_summary=lifecycle_summary,
        managed_runtime_context=managed_runtime_context,
        daemon_dds_visibility=daemon_dds_visibility,
    )
    amcl_summary = lifecycle_summary_for_node(map_lifecycle, "amcl")
    amcl_active = bool(proof.get("amcl_active") or amcl_summary.get("clean"))
    amcl_text = lifecycle_summary_attempts_text(amcl_summary)
    amcl_live_state_regression = bool(not amcl_active and "active [3]" not in amcl_text)
    return {
        "schema": "trashbot.o10.map_server_graph_lifecycle_visibility.v1",
        "proof_boundary": "software_proof_o3_o1_strict_no_motion_map_server_graph_lifecycle_visibility_only",
        "node": "/map_server",
        "canonical_classification": classification,
        "classification": classification,
        "failure_detail": failure_detail,
        "classification_set": sorted(MAP_SERVER_GRAPH_LIFECYCLE_CLASSIFICATIONS),
        "readiness_inputs": {
            "board_source_preflight_ready": board.get("classification") == "board_source_preflight_ready",
            "lightweight_cli_ready": bool(board.get("lightweight_cli_ready")),
            "cli_ready": bool(board.get("cli_ready")),
            "runtime_ready": bool(board.get("runtime_ready")),
        },
        "node_graph_inventory": {
            "node": "/map_server",
            "visible": graph_visible,
            "observed_node_names": observed_node_names,
            "lifecycle_graph_visibility": graph_visibility,
            "managed_wait_observed_node_names": managed_wait.get("observed_node_names") or [],
            "target_node": graph_target if isinstance(graph_target, dict) else {},
        },
        "daemon_dds_visibility": daemon_dds_visibility,
        "lifecycle_readback": {
            "schema": lifecycle_summary.get("schema"),
            "strategy": lifecycle_summary.get("strategy"),
            "command": lifecycle_summary.get("command") or "ros2 lifecycle get /map_server",
            "graph_node_visible": graph_visible,
            "first_attempt": lifecycle_summary.get("first_attempt") if isinstance(lifecycle_summary.get("first_attempt"), dict) else {},
            "retry_attempt": lifecycle_summary.get("retry_attempt") if isinstance(lifecycle_summary.get("retry_attempt"), dict) else {},
            "attempts": lifecycle_summary.get("attempts") if isinstance(lifecycle_summary.get("attempts"), list) else [],
            "final_attempt_label": lifecycle_summary.get("final_attempt_label"),
            "classification": lifecycle_summary.get("classification"),
            "clean": bool(lifecycle_summary.get("clean")),
            "timeout_budget_s": lifecycle_summary.get("timeout_budget_s") if isinstance(lifecycle_summary.get("timeout_budget_s"), dict) else {},
            "next_step": lifecycle_summary.get("next_step"),
        },
        "managed_runtime_context": managed_runtime_context,
        "lifecycle_manager_or_process_startup_context": {
            "expected_process_names": managed_runtime_context["expected_process_names"],
            "started": managed_runtime_context["started"],
            "process_alive": managed_runtime_context["process_alive"],
            "startup_error": managed_runtime_context["startup_error"],
            "missing_expected_nodes": managed_runtime_context["missing_expected_nodes"],
            "wait_reason": managed_runtime_context["wait_reason"],
        },
        "amcl_lifecycle_reference": {
            "previous_accepted_fact": "08-55 /amcl retry stdout contains active [3]",
            "current_active": amcl_active,
            "live_state_regression": amcl_live_state_regression,
            "current_summary": amcl_summary,
        },
        "guarded_downstream_context": {
            "downstream_primary_target": False,
            "scan_map_tf_consumed_only_after_lifecycle_clean": bool(
                (proof.get("downstream_recovery_summary") or {}).get("downstream_probes_allowed")
            ),
        },
        "no_motion_invariants": {
            **safety_flags(),
            "path_generation_attempted": False,
            "path_generated": False,
        },
    }


def map_yaml_presence_policy(proof: dict[str, Any]) -> dict[str, Any]:
    """把 managed map yaml 压成安全摘要；消费者默认看 basename，不依赖板端绝对路径。"""
    commands = proof.get("commands") if isinstance(proof.get("commands"), dict) else {}
    managed = commands.get("managed_runtime") if isinstance(commands.get("managed_runtime"), dict) else {}
    path_text = str(
        proof.get("managed_runtime_map_yaml")
        or proof.get("managed_runtime_requested_map_yaml")
        or managed.get("map_yaml")
        or managed.get("requested_map_yaml")
        or ""
    ).strip()
    source = str(proof.get("managed_runtime_map_yaml_source") or managed.get("map_yaml_source") or "")
    analysis = proof.get("managed_runtime_map_analysis")
    if not isinstance(analysis, dict):
        analysis = managed.get("map_analysis") if isinstance(managed.get("map_analysis"), dict) else {}
    policy: dict[str, Any] = {
        "provided": bool(path_text),
        "source": source or None,
        "configured_basename": Path(path_text).name if path_text else None,
        "basename": Path(path_text).name if path_text else None,
        "path_policy": "internal_artifact_keeps_board_path_summary_consumers_use_basename",
        "full_path_recorded_elsewhere": bool(path_text),
        "exists": None,
        "size_bytes": None,
        "sha256_prefix": None,
        "analysis_ok": bool(analysis.get("ok")),
        "image_basename": Path(str(analysis.get("image"))).name if analysis.get("image") else None,
        "error": analysis.get("error") if isinstance(analysis.get("error"), dict) else None,
    }
    if not path_text:
        return policy
    try:
        yaml_path = Path(path_text)
        stat = yaml_path.stat()
        policy["exists"] = True
        policy["size_bytes"] = stat.st_size
        # hash 只取 yaml 本身的短前缀，便于比较地图版本，又避免 artifact 过大。
        policy["sha256_prefix"] = hashlib.sha256(yaml_path.read_bytes()).hexdigest()[:16]
    except OSError:
        policy["exists"] = False
    return policy


def lifecycle_attempts_contain_node_not_found(lifecycle_summary: dict[str, Any]) -> bool:
    """`Node not found` 是 presence recovery 的专门分支，不能再只归成泛化 absent。"""
    return "node not found" in lifecycle_summary_attempts_text(lifecycle_summary)


def classify_map_server_presence_recovery(
    *,
    visibility_summary: dict[str, Any],
    map_yaml_policy: dict[str, Any],
) -> tuple[str, str, str]:
    """10-54 主分类：把 read-only absent 升级为 managed-runtime recovery 结果。"""
    managed_context = (
        visibility_summary.get("managed_runtime_context")
        if isinstance(visibility_summary.get("managed_runtime_context"), dict)
        else {}
    )
    lifecycle_summary = (
        visibility_summary.get("lifecycle_readback")
        if isinstance(visibility_summary.get("lifecycle_readback"), dict)
        else {}
    )
    node_inventory = (
        visibility_summary.get("node_graph_inventory")
        if isinstance(visibility_summary.get("node_graph_inventory"), dict)
        else {}
    )
    observed_nodes = {
        normalize_ros_node_name(str(name))
        for name in (node_inventory.get("observed_node_names") or managed_context.get("observed_nodes") or [])
        if str(name or "").strip()
    }
    requested = bool(managed_context.get("requested"))
    started = bool(managed_context.get("started"))
    wait_reason = str(managed_context.get("wait_reason") or "")
    process_alive = managed_context.get("process_alive")
    startup_error = managed_context.get("startup_error")
    log_tail = str(managed_context.get("log_tail") or "")
    log_tail_lower = log_tail.lower()

    if not requested:
        return (
            "presence_recovery_not_requested_read_only_existing_graph",
            "managed_runtime_opt_in_not_requested",
            "rerun_with_managed_runtime_opt_in_and_managed_map_yaml",
        )
    map_error = map_yaml_policy.get("error") if isinstance(map_yaml_policy.get("error"), dict) else {}
    map_error_type = str(map_error.get("type") or "")
    if not map_yaml_policy.get("provided") or map_error_type in {"map_yaml_missing", "FileNotFoundError"}:
        return "managed_map_yaml_missing", "managed_map_yaml_missing_or_not_resolved", "provide_existing_managed_map_yaml"
    if map_yaml_policy.get("analysis_ok") is False and map_error:
        return "managed_map_yaml_unreadable", "managed_map_yaml_analysis_failed", "repair_or_regenerate_managed_map_yaml"
    if startup_error or not started:
        return "managed_runtime_start_failed", "managed_runtime_process_not_started", "inspect_managed_runtime_startup_log"
    if lifecycle_summary.get("clean") or visibility_summary.get("canonical_classification") == "map_server_lifecycle_active":
        return "map_server_lifecycle_active", "map_server_lifecycle_readback_active_after_recovery", "continue_map_topic_tf_planner_readiness_no_motion"
    if "failed to change state for node: map_server" in log_tail_lower:
        return (
            "map_server_lifecycle_not_active_after_recovery",
            "lifecycle_manager_failed_to_change_state_for_map_server",
            "inspect_map_server_configure_error_and_map_yaml_runtime_log",
        )
    if "configuring map_server" in log_tail_lower or "[map_server]: configuring" in log_tail_lower:
        return (
            "map_server_lifecycle_not_active_after_recovery",
            "map_server_configure_started_but_active_not_observed",
            "inspect_map_server_lifecycle_transition_and_graph_readback",
        )
    if process_alive is False:
        return (
            "managed_runtime_process_exited_before_map_server_presence",
            "managed_runtime_process_not_alive_after_start",
            "inspect_nav2_map_server_startup_log_and_process_exit",
        )
    if wait_reason in {"ros2_node_list_timeout", "ros2_node_list_empty_after_wait", "ros2_node_list_failed", "rclpy_node_names_failed"}:
        return "managed_runtime_graph_unreadable_after_start", wait_reason, "repair_ros2_graph_or_daemon_after_managed_start"
    if lifecycle_attempts_contain_node_not_found(lifecycle_summary):
        if "/amcl" in observed_nodes or "/lifecycle_manager" in observed_nodes:
            return (
                "lifecycle_manager_not_serving_map_server",
                "managed_runtime_started_but_map_server_lifecycle_node_not_found",
                "inspect_lifecycle_manager_node_names_and_map_server_startup",
            )
        return (
            "managed_runtime_started_map_server_not_observed",
            "map_server_node_not_found_after_managed_runtime_start",
            "inspect_nav2_map_server_process_and_ros_node_name",
        )
    retry = lifecycle_summary.get("retry_attempt") if isinstance(lifecycle_summary.get("retry_attempt"), dict) else {}
    first = lifecycle_summary.get("first_attempt") if isinstance(lifecycle_summary.get("first_attempt"), dict) else {}
    if bool(first.get("timed_out")) or bool(retry.get("timed_out")):
        return (
            "map_server_lifecycle_rpc_timeout_after_recovery",
            "map_server_lifecycle_command_timeout_after_managed_start",
            "increase_lifecycle_cli_budget_or_inspect_lifecycle_service",
        )
    if str(lifecycle_summary.get("classification") or "") in {"inactive stdout", "lifecycle not active"}:
        return (
            "map_server_lifecycle_not_active_after_recovery",
            "map_server_lifecycle_visible_but_not_active",
            "inspect_map_yaml_and_lifecycle_transition_errors",
        )
    return (
        "map_server_lifecycle_command_failed_after_recovery",
        str(lifecycle_summary.get("classification") or "map_server_lifecycle_unclassified_after_recovery"),
        "inspect_map_server_lifecycle_stderr_stdout",
    )


def build_map_server_presence_recovery_summary(
    proof: dict[str, Any],
    *,
    visibility_summary: dict[str, Any],
) -> dict[str, Any]:
    """10-54 主 artifact：证明 managed runtime recovery 是否真的执行，并给出下一修复点。"""
    managed_context = (
        visibility_summary.get("managed_runtime_context")
        if isinstance(visibility_summary.get("managed_runtime_context"), dict)
        else {}
    )
    node_inventory = (
        visibility_summary.get("node_graph_inventory")
        if isinstance(visibility_summary.get("node_graph_inventory"), dict)
        else {}
    )
    lifecycle_summary = (
        visibility_summary.get("lifecycle_readback")
        if isinstance(visibility_summary.get("lifecycle_readback"), dict)
        else {}
    )
    map_yaml_policy = map_yaml_presence_policy(proof)
    classification, failure_detail, next_step = classify_map_server_presence_recovery(
        visibility_summary=visibility_summary,
        map_yaml_policy=map_yaml_policy,
    )
    observed_nodes = [
        normalize_ros_node_name(str(name))
        for name in (node_inventory.get("observed_node_names") or managed_context.get("observed_nodes") or [])
        if str(name or "").strip()
    ]
    log_tail = str(managed_context.get("log_tail") or "")
    log_tail_lower = log_tail.lower()
    requested = bool(managed_context.get("requested"))
    started = bool(managed_context.get("started"))
    return {
        "schema": "trashbot.o10.map_server_presence_recovery.v1",
        "proof_boundary": "software_proof_o3_o1_strict_no_motion_map_server_presence_recovery_only",
        "recovery_attempted": requested,
        "canonical_classification": classification,
        "classification": classification,
        "failure_detail": failure_detail,
        "classification_set": sorted(MAP_SERVER_PRESENCE_RECOVERY_CLASSIFICATIONS),
        "next_step": next_step,
        "recovery_path": {
            "method": "helper_managed_runtime_opt_in" if requested else "read_only_existing_graph",
            "managed_runtime_requested": requested,
            "managed_runtime_started": started,
            "managed_runtime_boundary": managed_context.get("boundary"),
            "command_family": "build_managed_runtime_shell" if requested else None,
            "starts_required_nodes": ["map_server", "amcl", "lifecycle_manager"] if requested else [],
            "starts_planner_server": bool(proof.get("path_generation_requested") and requested),
            "starts_controller_server": False,
            "sends_navigate_to_pose": False,
            "publishes_cmd_vel": False,
            "calls_base_manual": False,
            "uses_base_uart": False,
        },
        "managed_map_yaml": map_yaml_policy,
        "process_presence": {
            "process_group": managed_context.get("process_group"),
            "process_alive_before_cleanup": managed_context.get("process_alive"),
            "process_returncode": managed_context.get("process_returncode"),
            "startup_error": managed_context.get("startup_error"),
            "expected_process_names": managed_context.get("expected_process_names") or ["nav2_map_server", "nav2_lifecycle_manager"],
            "log_tail": managed_context.get("log_tail") or "",
        },
        "node_presence": {
            "target_node": "/map_server",
            "target_visible": bool((node_inventory.get("target_node") or {}).get("visible") or node_inventory.get("visible")),
            "observed_node_names": sorted(set(observed_nodes)),
            "lifecycle_manager_visible": "/lifecycle_manager" in set(observed_nodes),
            "amcl_visible": "/amcl" in set(observed_nodes),
            "log_inferred_map_server_configure_started": "configuring map_server" in log_tail_lower or "[map_server]: configuring" in log_tail_lower,
            "log_inferred_map_server_state_change_failed": "failed to change state for node: map_server" in log_tail_lower,
            "log_inferred_map_yaml_loaded": "loading yaml file:" in log_tail_lower and "trashbot_map.yaml" in log_tail_lower,
            "wait_reason": managed_context.get("wait_reason"),
            "missing_expected_nodes": managed_context.get("missing_expected_nodes") or [],
        },
        "lifecycle_readback": {
            "command": lifecycle_summary.get("command") or "ros2 lifecycle get /map_server",
            "clean": bool(lifecycle_summary.get("clean")),
            "classification": lifecycle_summary.get("classification"),
            "first_attempt": lifecycle_summary.get("first_attempt") if isinstance(lifecycle_summary.get("first_attempt"), dict) else {},
            "retry_attempt": lifecycle_summary.get("retry_attempt") if isinstance(lifecycle_summary.get("retry_attempt"), dict) else {},
            "node_not_found_observed": lifecycle_attempts_contain_node_not_found(lifecycle_summary),
            "timeout_budget_s": lifecycle_summary.get("timeout_budget_s") if isinstance(lifecycle_summary.get("timeout_budget_s"), dict) else {},
        },
        "previous_read_only_visibility": {
            "canonical_classification": visibility_summary.get("canonical_classification"),
            "failure_detail": visibility_summary.get("failure_detail"),
            "managed_runtime_requested": requested,
            "managed_runtime_started": started,
        },
        "no_motion_invariants": {
            **safety_flags(),
            "path_generation_attempted": False,
            "path_generated": False,
            "sends_navigate_to_pose": False,
        },
    }


def strip_ansi(text: str) -> str:
    """ROS/FastDDS 日志带 ANSI 颜色码；分类前先去掉，避免字符串匹配漂移。"""
    return re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", str(text or ""))


def file_readback(path_text: str | None) -> dict[str, Any]:
    """统一记录文件存在、可读、hash 和 basename；失败也要结构化输出。"""
    path_text = str(path_text or "").strip()
    result: dict[str, Any] = {
        "path": path_text or None,
        "basename": Path(path_text).name if path_text else None,
        "exists": False,
        "readable": False,
        "size_bytes": None,
        "sha256_prefix": None,
        "error": None,
    }
    if not path_text:
        result["error"] = {"type": "path_missing", "message": "path is empty"}
        return result
    try:
        path = Path(path_text)
        result["exists"] = path.exists()
        if not result["exists"]:
            result["error"] = {"type": "FileNotFoundError", "message": path_text}
            return result
        data = path.read_bytes()
        result["readable"] = True
        result["size_bytes"] = len(data)
        result["sha256_prefix"] = hashlib.sha256(data).hexdigest()[:16]
        return result
    except OSError as exc:
        result["error"] = compact_error(exc)
        return result


def parse_float_field(value: str) -> float | None:
    """map yaml 字段需要转成数值；失败时保留 None，让 classifier 给出 invalid_fields。"""
    try:
        return float(str(value).strip().strip("'\""))
    except (TypeError, ValueError):
        return None


def parse_map_yaml_fields(text: str, *, yaml_dir: Path | None = None) -> dict[str, Any]:
    """只解析 map_server 关心的稳定字段，不引入额外 YAML 依赖。"""
    fields: dict[str, Any] = {
        "image": None,
        "image_path": None,
        "resolution": None,
        "origin": None,
        "occupied_thresh": None,
        "free_thresh": None,
        "mode": None,
        "negate": None,
    }
    lines = str(text or "").splitlines()
    for index, raw_line in enumerate(lines):
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key == "image":
            fields["image"] = value
            image_path = Path(value)
            if not image_path.is_absolute() and yaml_dir is not None:
                image_path = yaml_dir / value
            fields["image_path"] = str(image_path)
        elif key == "resolution":
            fields["resolution"] = parse_float_field(value)
        elif key == "origin":
            origin_values: list[float] = []
            if value.startswith("[") and value.endswith("]"):
                raw_values = [part.strip() for part in value.strip("[]").split(",") if part.strip()]
            else:
                raw_values = []
                for offset in range(1, 4):
                    if index + offset >= len(lines):
                        break
                    candidate = lines[index + offset].split("#", 1)[0].strip()
                    if not candidate.startswith("-"):
                        break
                    raw_values.append(candidate[1:].strip())
            for item in raw_values:
                parsed = parse_float_field(item)
                if parsed is not None:
                    origin_values.append(parsed)
            fields["origin"] = origin_values if origin_values else None
        elif key == "occupied_thresh":
            fields["occupied_thresh"] = parse_float_field(value)
        elif key == "free_thresh":
            fields["free_thresh"] = parse_float_field(value)
        elif key == "mode":
            fields["mode"] = value or None
        elif key == "negate":
            try:
                fields["negate"] = int(value)
            except (TypeError, ValueError):
                fields["negate"] = value or None
    required_missing = [
        key
        for key in ("image", "resolution", "origin")
        if fields.get(key) in (None, "", [])
    ]
    optional_missing = [
        key
        for key in ("occupied_thresh", "free_thresh", "mode")
        if fields.get(key) in (None, "", [])
    ]
    fields["required_missing"] = required_missing
    fields["optional_missing"] = optional_missing
    fields["valid_for_map_server"] = not required_missing
    return fields


def map_yaml_activation_readback(proof: dict[str, Any]) -> dict[str, Any]:
    """本轮 activation proof 要把 yaml/pgm 字段和 hash 放到同一块里。"""
    commands = proof.get("commands") if isinstance(proof.get("commands"), dict) else {}
    managed = commands.get("managed_runtime") if isinstance(commands.get("managed_runtime"), dict) else {}
    map_yaml = str(
        proof.get("managed_runtime_map_yaml")
        or proof.get("managed_runtime_requested_map_yaml")
        or managed.get("map_yaml")
        or managed.get("requested_map_yaml")
        or ""
    ).strip()
    analysis = proof.get("managed_runtime_map_analysis")
    if not isinstance(analysis, dict):
        analysis = managed.get("map_analysis") if isinstance(managed.get("map_analysis"), dict) else {}
    yaml_file = file_readback(map_yaml)
    fields: dict[str, Any] = {
        "image": Path(str(analysis.get("image"))).name if analysis.get("image") else None,
        "image_path": str(analysis.get("image") or ""),
        "resolution": analysis.get("resolution"),
        "origin": analysis.get("origin"),
        "occupied_thresh": None,
        "free_thresh": None,
        "mode": None,
        "negate": None,
        "required_missing": [],
        "optional_missing": ["occupied_thresh", "free_thresh", "mode"],
        "valid_for_map_server": bool(analysis.get("ok")),
    }
    if yaml_file["readable"]:
        try:
            yaml_path = Path(map_yaml)
            fields = parse_map_yaml_fields(
                yaml_path.read_text(encoding="utf-8", errors="replace"),
                yaml_dir=yaml_path.parent,
            )
        except OSError as exc:
            fields["read_error"] = compact_error(exc)
            fields["valid_for_map_server"] = False
    image_path = str(fields.get("image_path") or analysis.get("image") or "")
    image_file = file_readback(image_path)
    validation = {
        "yaml_readable": bool(yaml_file["readable"]),
        "image_readable": bool(image_file["readable"]),
        "yaml_fields_valid": bool(fields.get("valid_for_map_server")),
        "analysis_ok": bool(analysis.get("ok")),
        "cell_counts": analysis.get("cell_counts") if isinstance(analysis.get("cell_counts"), dict) else {},
        "width": analysis.get("width"),
        "height": analysis.get("height"),
    }
    return {
        "schema": "trashbot.o10.map_server_activation_map_readback.v1",
        "yaml": yaml_file,
        "pgm": image_file,
        "fields": fields,
        "validation": validation,
    }


def managed_runtime_log_for_activation(proof: dict[str, Any]) -> str:
    """activation summary 只读 artifact 中已保存的 managed runtime log tail。"""
    commands = proof.get("commands") if isinstance(proof.get("commands"), dict) else {}
    managed = commands.get("managed_runtime") if isinstance(commands.get("managed_runtime"), dict) else {}
    wait_result = proof.get("managed_runtime_wait_result") if isinstance(proof.get("managed_runtime_wait_result"), dict) else {}
    process_presence = (
        (proof.get("map_server_presence_recovery") or {}).get("process_presence")
        if isinstance(proof.get("map_server_presence_recovery"), dict)
        else {}
    )
    candidates = [
        str((process_presence or {}).get("log_tail") or ""),
        str(wait_result.get("log_tail") or ""),
        str(managed.get("log_tail") or ""),
        str(proof.get("amcl_log_tail") or ""),
    ]
    return select_map_server_transition_log(candidates)


def ros_log_timestamp_s(line: str) -> float | None:
    """解析 ROS 日志头里的秒/纳秒时间戳，用来避免 stdout flush 顺序误导分类。"""
    match = re.search(r"\[(\d+)\.(\d{1,9})\]", str(line or ""))
    if not match:
        return None
    seconds = int(match.group(1))
    nanos = int(match.group(2).ljust(9, "0")[:9])
    return seconds + nanos / 1_000_000_000.0


def first_ros_timestamp(lines: list[str], index: int | None) -> float | None:
    """line index 可能为空；统一返回 None，artifact 中就能明确区分未观测。"""
    if index is None or index < 0 or index >= len(lines):
        return None
    return ros_log_timestamp_s(lines[index])


def map_server_transition_log_score(log_text: str) -> int:
    """优先保留真正包含 configure/ChangeState/map IO 的窗口，而不是 cleanup tail。"""
    summary = map_server_activation_log_summary(log_text)
    events = summary.get("events") if isinstance(summary.get("events"), dict) else {}
    line_indices = summary.get("line_indices") if isinstance(summary.get("line_indices"), dict) else {}
    score = 0
    for key in (
        "lifecycle_manager_configure_requested",
        "map_server_configure_callback_entered",
        "state_change_failed",
        "yaml_load_started",
        "image_load_started",
        "map_read_completed",
    ):
        if events.get(key):
            score += 8
    for value in line_indices.values():
        if value is not None:
            score += 1
    if events.get("state_change_failed_before_map_server_configure_callback"):
        score += 12
    if "running nav2 lifecyclenode rcl preshutdown" in strip_ansi(log_text).lower():
        score -= 4
    return score


def select_map_server_transition_log(candidates: list[str]) -> str:
    """从多个 artifact log 字段中选择证据最强的一段，避免 preserved evidence 只能给布尔值。"""
    non_empty = [candidate for candidate in candidates if candidate]
    if not non_empty:
        return ""
    return max(non_empty, key=map_server_transition_log_score)


def first_line_index(lines: list[str], *needles: str) -> int | None:
    """返回第一个包含任一 needle 的行号，供日志顺序判断使用。"""
    lowered_needles = [needle.lower() for needle in needles]
    for index, line in enumerate(lines):
        lower = line.lower()
        if any(needle in lower for needle in lowered_needles):
            return index
    return None


def map_server_activation_log_summary(log_text: str) -> dict[str, Any]:
    """从 runtime log 提取 configure/activate 顺序，不把后续 LiDAR 异常当 map_server 根因。"""
    clean = strip_ansi(log_text)
    lines = [line.strip() for line in clean.splitlines() if line.strip()]
    lifecycle_configure_index = first_line_index(lines, "[lifecycle_manager]: configuring map_server", "configuring map_server")
    map_server_configure_index = first_line_index(lines, "[map_server]: configuring")
    configure_index = map_server_configure_index if map_server_configure_index is not None else lifecycle_configure_index
    activate_index = first_line_index(lines, "activating map_server", "[map_server]: activating")
    yaml_index = first_line_index(lines, "loading yaml file:")
    image_index = first_line_index(lines, "loading image_file:")
    read_map_index = first_line_index(lines, "read map ")
    state_failed_index = first_line_index(lines, "failed to change state for node: map_server")
    bringup_failed_index = first_line_index(lines, "failed to bring up all requested nodes")
    service_timeout_index = first_line_index(
        lines,
        "timed out waiting for service",
        "service call failed",
        "failed to call service",
        "change_state service",
    )
    bond_created_index = first_line_index(
        lines,
        "creating bond (map_server)",
        "created bond (map_server)",
        "bond connection to lifecycle manager",
    )
    bond_timeout_index = first_line_index(
        lines,
        "timed out waiting for bond",
        "bond timeout",
        "failed to create bond",
    )
    bond_destroyed_index = first_line_index(lines, "destroying bond (map_server)")
    amcl_configure_request_index = first_line_index(lines, "[lifecycle_manager]: configuring amcl", "configuring amcl")
    amcl_configure_callback_index = first_line_index(lines, "[amcl]: configuring")
    amcl_state_failed_index = first_line_index(lines, "failed to change state for node: amcl")
    amcl_init_transforms_index = first_line_index(lines, "[amcl]: inittransforms")
    amcl_init_pubsub_index = first_line_index(lines, "[amcl]: initpubsub")
    amcl_received_map_index = first_line_index(lines, "[amcl]: received a", "received a 261 x 113 map")
    map_server_error_lines = [
        line for line in lines if "[map_server]" in line.lower() and ("error" in line.lower() or "exception" in line.lower())
    ]
    dds_transport_error_lines = [
        line
        for line in lines[-200:]
        if (
            "rtps_transport_shm" in line.lower()
            or "failed init_port" in line.lower()
            or "open_and_lock_file failed" in line.lower()
        )
    ]
    traceback_blocks: list[str] = []
    for index, line in enumerate(lines):
        if "traceback (most recent call last)" not in line.lower():
            continue
        traceback_blocks.append("\n".join(lines[index:index + 24])[-3000:])
    return {
        "recent_log_lines": lines[-80:],
        "map_server_stdout_stderr_tail": "\n".join(
            line for line in lines[-120:] if any(token in line.lower() for token in ("map_server", "map_io", "lifecycle_manager"))
        )[-5000:],
        "lifecycle_manager_log_tail": "\n".join(
            line for line in lines[-120:] if "lifecycle_manager" in line.lower()
        )[-3000:],
        "exception_text": "\n\n".join(traceback_blocks)[-4000:],
        "map_server_exception_text": "\n".join(map_server_error_lines)[-2000:],
        "dds_transport_error_text": "\n".join(dds_transport_error_lines)[-3000:],
        "process_exit_lines": [line for line in lines[-120:] if "[ros2run]: process exited" in line.lower()],
        "line_indices": {
            "configure_started": configure_index,
            "lifecycle_manager_configure_requested": lifecycle_configure_index,
            "map_server_configure_callback_entered": map_server_configure_index,
            "activate_started": activate_index,
            "yaml_load_started": yaml_index,
            "image_load_started": image_index,
            "map_read_completed": read_map_index,
            "state_change_failed": state_failed_index,
            "bringup_failed": bringup_failed_index,
            "service_timeout": service_timeout_index,
            "bond_created": bond_created_index,
            "bond_timeout": bond_timeout_index,
            "bond_destroyed": bond_destroyed_index,
            "amcl_configure_requested": amcl_configure_request_index,
            "amcl_configure_callback_entered": amcl_configure_callback_index,
            "amcl_state_change_failed": amcl_state_failed_index,
            "amcl_init_transforms": amcl_init_transforms_index,
            "amcl_init_pub_sub": amcl_init_pubsub_index,
            "amcl_map_received": amcl_received_map_index,
        },
        "event_timestamps_s": {
            "configure_started": first_ros_timestamp(lines, configure_index),
            "lifecycle_manager_configure_requested": first_ros_timestamp(lines, lifecycle_configure_index),
            "map_server_configure_callback_entered": first_ros_timestamp(lines, map_server_configure_index),
            "activate_started": first_ros_timestamp(lines, activate_index),
            "yaml_load_started": first_ros_timestamp(lines, yaml_index),
            "image_load_started": first_ros_timestamp(lines, image_index),
            "map_read_completed": first_ros_timestamp(lines, read_map_index),
            "state_change_failed": first_ros_timestamp(lines, state_failed_index),
            "bringup_failed": first_ros_timestamp(lines, bringup_failed_index),
            "service_timeout": first_ros_timestamp(lines, service_timeout_index),
            "bond_created": first_ros_timestamp(lines, bond_created_index),
            "bond_timeout": first_ros_timestamp(lines, bond_timeout_index),
            "bond_destroyed": first_ros_timestamp(lines, bond_destroyed_index),
            "amcl_configure_requested": first_ros_timestamp(lines, amcl_configure_request_index),
            "amcl_configure_callback_entered": first_ros_timestamp(lines, amcl_configure_callback_index),
            "amcl_state_change_failed": first_ros_timestamp(lines, amcl_state_failed_index),
            "amcl_init_transforms": first_ros_timestamp(lines, amcl_init_transforms_index),
            "amcl_init_pub_sub": first_ros_timestamp(lines, amcl_init_pubsub_index),
            "amcl_map_received": first_ros_timestamp(lines, amcl_received_map_index),
        },
        "events": {
            "lifecycle_manager_started": any("starting role=lifecycle_manager" in line.lower() or "[lifecycle_manager]" in line.lower() for line in lines),
            "map_server_process_started": any("starting role=map_server" in line.lower() or "[map_server]" in line.lower() for line in lines),
            "configure_started": configure_index is not None,
            "lifecycle_manager_configure_requested": lifecycle_configure_index is not None,
            "map_server_configure_callback_entered": map_server_configure_index is not None,
            "activate_started": activate_index is not None,
            "yaml_load_started": yaml_index is not None,
            "image_load_started": image_index is not None,
            "map_read_completed": read_map_index is not None,
            "state_change_failed": state_failed_index is not None,
            "bringup_failed": bringup_failed_index is not None,
            "service_timeout_or_rpc_error": service_timeout_index is not None,
            "bond_created": bond_created_index is not None,
            "bond_timeout": bond_timeout_index is not None,
            "bond_destroyed": bond_destroyed_index is not None,
            "amcl_configure_requested": amcl_configure_request_index is not None,
            "amcl_configure_callback_entered": amcl_configure_callback_index is not None,
            "amcl_state_change_failed": amcl_state_failed_index is not None,
            "amcl_init_transforms": amcl_init_transforms_index is not None,
            "amcl_init_pub_sub": amcl_init_pubsub_index is not None,
            "amcl_map_received": amcl_received_map_index is not None,
            "amcl_state_change_failed_after_map_server_configure_success": bool(
                read_map_index is not None
                and amcl_state_failed_index is not None
                and read_map_index < amcl_state_failed_index
            ),
            "dds_shm_transport_error": bool(dds_transport_error_lines),
            "map_read_after_state_change_failure": bool(
                state_failed_index is not None
                and read_map_index is not None
                and read_map_index > state_failed_index
            ),
            "state_change_failed_after_image_load_before_map_read_completed": bool(
                state_failed_index is not None
                and image_index is not None
                and image_index < state_failed_index
                and (read_map_index is None or state_failed_index < read_map_index)
            ),
            "changestate_response_false_before_map_io_completion": bool(
                state_failed_index is not None
                and read_map_index is not None
                and state_failed_index < read_map_index
            ),
            "state_change_failed_before_map_server_configure_callback": bool(
                state_failed_index is not None
                and lifecycle_configure_index is not None
                and (
                    (
                        map_server_configure_index is None
                        and yaml_index is None
                        and image_index is None
                        and read_map_index is None
                    )
                    or (
                        map_server_configure_index is not None
                        and state_failed_index < map_server_configure_index
                    )
                )
            ),
        },
    }


def managed_runtime_launch_parameter_summary(proof: dict[str, Any]) -> dict[str, Any]:
    """记录 helper 生成的 no-motion launch/param 边界，方便区分 name/namespace mismatch。"""
    include_planner_server = bool(proof.get("path_generation_requested"))
    managed_node_list = ["map_server", "amcl"] + (["planner_server"] if include_planner_server else [])
    map_yaml = str(proof.get("managed_runtime_map_yaml") or proof.get("managed_runtime_requested_map_yaml") or "")
    return {
        "map_server": {
            "node_name": "map_server",
            "namespace": "/",
            "parameters": {
                "yaml_filename_basename": Path(map_yaml).name if map_yaml else None,
                "frame_id": "map",
                "use_sim_time": False,
            },
        },
        "lifecycle_manager": {
            "node_name": "lifecycle_manager",
            "namespace": "/",
            "managed_node_list": managed_node_list,
            "autostart": True,
            "bond_timeout_s": 8.0,
            "service_timeout_s": 12.0,
        },
        "runtime_environment": {
            "RMW_FASTRTPS_USE_SHM": "0",
            "FASTDDS_BUILTIN_TRANSPORTS": "UDPv4",
            "strict_no_motion": True,
            "opens_base_uart": False,
        },
        "name_namespace_check": {
            "map_server_name_in_managed_node_list": "map_server" in managed_node_list,
            "map_server_namespace_matches_manager": True,
            "expected_map_server_fqn": "/map_server",
        },
    }


def event_delta_ms(event_timestamps: dict[str, Any], start_key: str, end_key: str) -> float | None:
    """两个 ROS 日志时间戳都存在时才计算差值，避免用缺省 0 伪造 timing 证据。"""
    try:
        start = float(event_timestamps.get(start_key))
        end = float(event_timestamps.get(end_key))
    except (TypeError, ValueError):
        return None
    return round((end - start) * 1000.0, 3)


def map_io_changestate_timing(log_summary: dict[str, Any]) -> dict[str, Any]:
    """把 ChangeState response 与 map IO 的先后关系写成可复核 timing，而不只给字符串分类。"""
    events = log_summary.get("events") if isinstance(log_summary.get("events"), dict) else {}
    event_timestamps = log_summary.get("event_timestamps_s") if isinstance(log_summary.get("event_timestamps_s"), dict) else {}
    return {
        "configure_to_state_failure_ms": event_delta_ms(event_timestamps, "configure_started", "state_change_failed"),
        "yaml_load_to_state_failure_ms": event_delta_ms(event_timestamps, "yaml_load_started", "state_change_failed"),
        "image_load_to_state_failure_ms": event_delta_ms(event_timestamps, "image_load_started", "state_change_failed"),
        "state_failure_to_map_read_completed_ms": event_delta_ms(event_timestamps, "state_change_failed", "map_read_completed"),
        "configure_to_map_read_completed_ms": event_delta_ms(event_timestamps, "configure_started", "map_read_completed"),
        "map_read_completed_after_state_failure": bool(events.get("map_read_after_state_change_failure")),
        "change_state_response_false_while_map_io_incomplete": bool(
            events.get("state_change_failed")
            and events.get("changestate_response_false_before_map_io_completion")
        ),
        "state_failure_after_image_before_map_read": bool(
            events.get("state_change_failed_after_image_load_before_map_read_completed")
        ),
    }


def managed_runtime_log_lifecycle_active_readback(log_text: str) -> dict[str, Any]:
    """从 managed runtime 日志回读 lifecycle active，补足 ROS graph probe 偶发 timeout 的盲区。"""
    clean = strip_ansi(log_text)
    lowered = clean.lower()
    managed_nodes_active = "managed nodes are active" in lowered
    map_server_active = bool(
        managed_nodes_active
        or (
            "activating map_server" in lowered
            and "[map_server]: activating" in lowered
            and "server map_server connected with bond" in lowered
        )
    )
    amcl_active = bool(
        managed_nodes_active
        or (
            "activating amcl" in lowered
            and "[amcl]: activating" in lowered
            and "server amcl connected with bond" in lowered
        )
    )
    active = {"map_server": map_server_active, "amcl": amcl_active}
    results = {
        key: {
            "executed": False,
            "ok": bool(value),
            "active": bool(value),
            "boundary": (
                "managed_runtime_log_lifecycle_active_observed"
                if value
                else "managed_runtime_log_lifecycle_active_not_observed"
            ),
            "stdout": "active [3]\n" if value else "",
            "source": "managed_runtime_log",
        }
        for key, value in active.items()
    }
    return {
        "schema": "trashbot.o10.managed_runtime_log_lifecycle_readback.v1",
        "executed": bool(clean),
        "clean": bool(map_server_active and amcl_active),
        "managed_nodes_active_logged": managed_nodes_active,
        "active": active,
        "results": results,
        "evidence": {
            "map_server_activating_logged": "activating map_server" in lowered and "[map_server]: activating" in lowered,
            "map_server_bond_connected_logged": "server map_server connected with bond" in lowered,
            "amcl_activating_logged": "activating amcl" in lowered and "[amcl]: activating" in lowered,
            "amcl_bond_connected_logged": "server amcl connected with bond" in lowered,
            "managed_nodes_active_logged": managed_nodes_active,
        },
        "log_tail": clean[-2400:],
    }


def classify_map_server_lifecycle_activation(
    *,
    proof: dict[str, Any],
    map_readback: dict[str, Any],
    log_summary: dict[str, Any],
    launch_parameters: dict[str, Any],
    presence_summary: dict[str, Any],
) -> tuple[str, str, str]:
    """把本轮 lifecycle failure 收窄到 map/input、命名、进程、configure 或 activate。"""
    requested = bool(proof.get("managed_runtime_requested"))
    started = bool(proof.get("managed_runtime_started"))
    if not requested:
        return (
            "map_server_lifecycle_activation_not_requested",
            "managed_runtime_opt_in_not_requested",
            "rerun_with_managed_runtime_opt_in",
        )
    lifecycle_readback = presence_summary.get("lifecycle_readback") if isinstance(presence_summary.get("lifecycle_readback"), dict) else {}
    if lifecycle_readback.get("clean") or presence_summary.get("canonical_classification") == "map_server_lifecycle_active":
        return "map_server_lifecycle_active", "map_server_active_after_activation_repair", "continue_map_topic_tf_planner_readiness_no_motion"
    validation = map_readback.get("validation") if isinstance(map_readback.get("validation"), dict) else {}
    yaml_file = map_readback.get("yaml") if isinstance(map_readback.get("yaml"), dict) else {}
    pgm_file = map_readback.get("pgm") if isinstance(map_readback.get("pgm"), dict) else {}
    fields = map_readback.get("fields") if isinstance(map_readback.get("fields"), dict) else {}
    if not yaml_file.get("readable"):
        return "map_server_yaml_image_unreadable", "map_yaml_file_missing_or_unreadable", "repair_managed_map_yaml_path"
    if not validation.get("yaml_fields_valid"):
        return "map_server_yaml_invalid_fields", "map_yaml_required_fields_missing_or_invalid", "repair_map_yaml_required_fields"
    if not pgm_file.get("readable"):
        return "map_server_yaml_image_unreadable", "map_yaml_image_file_missing_or_unreadable", "repair_map_yaml_image_path"
    frame_id = str((((launch_parameters.get("map_server") or {}).get("parameters") or {}).get("frame_id") or ""))
    if not frame_id or frame_id.startswith("/"):
        return "map_server_frame_id_missing_or_invalid", "map_server_frame_id_not_valid", "set_map_server_frame_id_to_map"
    name_check = launch_parameters.get("name_namespace_check") if isinstance(launch_parameters.get("name_namespace_check"), dict) else {}
    if not name_check.get("map_server_name_in_managed_node_list"):
        return "lifecycle_manager_map_server_name_mismatch", "lifecycle_manager_node_names_missing_map_server", "align_lifecycle_manager_node_names"
    if not name_check.get("map_server_namespace_matches_manager"):
        return "lifecycle_manager_map_server_namespace_mismatch", "lifecycle_manager_namespace_does_not_match_map_server", "align_lifecycle_manager_namespace"
    process_alive = proof.get("managed_runtime_process_group") is not None
    process_returncode = None
    commands = proof.get("commands") if isinstance(proof.get("commands"), dict) else {}
    managed = commands.get("managed_runtime") if isinstance(commands.get("managed_runtime"), dict) else {}
    if isinstance(managed.get("cleanup_result"), dict):
        process_returncode = managed["cleanup_result"].get("process_returncode")
    events = log_summary.get("events") if isinstance(log_summary.get("events"), dict) else {}
    if started and process_returncode not in (None, 0) and events.get("configure_started"):
        return "map_server_process_exited_during_configure", "managed_runtime_process_exited_after_configure_started", "inspect_map_server_process_exit_status"
    if log_summary.get("map_server_exception_text"):
        return "map_server_configure_exception", "map_server_exception_observed_in_configure_log", "inspect_map_server_exception_text"
    if events.get("amcl_state_change_failed_after_map_server_configure_success"):
        return (
            "map_server_configure_completed_lifecycle_blocked_by_amcl_configure_failure",
            "lifecycle_manager_advanced_to_amcl_after_map_server_configure_then_amcl_changestate_failed",
            "inspect_amcl_on_configure_return_path_after_map_server_configure_success",
        )
    if events.get("state_change_failed"):
        return (
            "map_server_activate_callback_failed",
            "lifecycle_manager_failed_to_change_state_for_map_server_after_valid_map_readback",
            "inspect_nav2_lifecycle_manager_service_timeout_or_map_server_transition_callback",
        )
    if process_alive and (presence_summary.get("canonical_classification") == "map_server_lifecycle_rpc_timeout_after_recovery"):
        return (
            "map_server_lifecycle_service_timeout_with_process_alive",
            "lifecycle_service_timeout_process_still_alive",
            "increase_lifecycle_service_budget_or_inspect_dds_rpc",
        )
    return "map_server_configure_exception", "map_server_lifecycle_activation_unclassified_after_readback", "inspect_runtime_log_and_lifecycle_cli"


def build_map_server_lifecycle_activation_summary(
    proof: dict[str, Any],
    *,
    presence_summary: dict[str, Any],
) -> dict[str, Any]:
    """11-54 主 artifact：输出 map_server configure/activate 的可执行窄分类。"""
    map_readback = map_yaml_activation_readback(proof)
    log_summary = map_server_activation_log_summary(managed_runtime_log_for_activation(proof))
    root_filter = proof.get("root_cause_filtering") if isinstance(proof.get("root_cause_filtering"), dict) else {}
    preserved_log_evidence = root_filter.get("evidence") if isinstance(root_filter.get("evidence"), dict) else {}
    if preserved_log_evidence:
        # cleanup 后 log tail 可能被 SIGINT/traceback 覆盖；保留 pre-cleanup 证据避免分类回退。
        events = log_summary.setdefault("events", {})
        if isinstance(events, dict):
            event_aliases = {
                "lifecycle_manager_started": "lifecycle_manager_started",
                "map_server_process_started": "map_server_process_started",
                "configure_started": "map_server_configure_started",
                "lifecycle_manager_configure_requested": "lifecycle_manager_configure_requested",
                "map_server_configure_callback_entered": "map_server_configure_callback_entered",
                "yaml_load_started": "map_yaml_loaded",
                "image_load_started": "map_pgm_loaded",
                "state_change_failed": "map_server_state_change_failed",
                "map_read_completed": "map_read_completed",
                "map_read_after_state_change_failure": "map_read_after_state_change_failure",
                "state_change_failed_after_image_load_before_map_read_completed": "state_change_failed_after_image_load_before_map_read_completed",
                "state_change_failed_before_map_server_configure_callback": "state_change_failed_before_map_server_configure_callback",
            }
            for event_key, evidence_key in event_aliases.items():
                events[event_key] = bool(events.get(event_key) or preserved_log_evidence.get(evidence_key))
        log_summary["preserved_pre_cleanup_evidence"] = preserved_log_evidence
    launch_parameters = managed_runtime_launch_parameter_summary(proof)
    classification, failure_detail, next_step = classify_map_server_lifecycle_activation(
        proof=proof,
        map_readback=map_readback,
        log_summary=log_summary,
        launch_parameters=launch_parameters,
        presence_summary=presence_summary,
    )
    commands = proof.get("commands") if isinstance(proof.get("commands"), dict) else {}
    managed = commands.get("managed_runtime") if isinstance(commands.get("managed_runtime"), dict) else {}
    wait_result = proof.get("managed_runtime_wait_result") if isinstance(proof.get("managed_runtime_wait_result"), dict) else {}
    return {
        "schema": "trashbot.o10.map_server_lifecycle_activation.v1",
        "proof_boundary": "software_proof_o3_o1_strict_no_motion_map_server_lifecycle_activation_only",
        "canonical_classification": classification,
        "classification": classification,
        "failure_detail": failure_detail,
        "classification_set": sorted(MAP_SERVER_LIFECYCLE_ACTIVATION_CLASSIFICATIONS),
        "next_step": next_step,
        "map_yaml_pgm_readback": map_readback,
        "runtime_log": log_summary,
        "lifecycle_manager_state_change_result": {
            "failed_to_change_state_for_map_server": bool((log_summary.get("events") or {}).get("state_change_failed")),
            "bringup_failed": bool((log_summary.get("events") or {}).get("bringup_failed")),
            "map_read_after_state_change_failure": bool((log_summary.get("events") or {}).get("map_read_after_state_change_failure")),
            "dds_shm_transport_error": bool((log_summary.get("events") or {}).get("dds_shm_transport_error")),
            "failure_detail": failure_detail,
        },
        "launch_parameters": launch_parameters,
        "node_identity": {
            "map_server_node_name": "map_server",
            "map_server_namespace": "/",
            "map_server_fqn": "/map_server",
            "lifecycle_manager_node_name": "lifecycle_manager",
            "lifecycle_manager_namespace": "/",
        },
        "process_status": {
            "managed_runtime_started": bool(proof.get("managed_runtime_started")),
            "process_group": proof.get("managed_runtime_process_group"),
            "process_alive_before_cleanup": bool(proof.get("managed_runtime_started")),
            "process_returncode": managed.get("process_returncode"),
            "startup_error": managed.get("startup_error"),
            "wait_reason": wait_result.get("reason") or wait_result.get("boundary"),
            "wait_returncode": wait_result.get("returncode"),
        },
        "lifecycle_readback": presence_summary.get("lifecycle_readback") if isinstance(presence_summary.get("lifecycle_readback"), dict) else {},
        "no_motion_invariants": {
            **safety_flags(),
            "path_generation_attempted": False,
            "path_generated": False,
            "sends_navigate_to_pose": False,
        },
    }


def lifecycle_readback_has_timeout(lifecycle_readback: dict[str, Any]) -> bool:
    """service/RPC 层只看真实执行过的 lifecycle attempt，跳过 legacy/skipped 噪音。"""
    for key in ("first_attempt", "retry_attempt"):
        attempt = lifecycle_readback.get(key) if isinstance(lifecycle_readback.get(key), dict) else {}
        if attempt.get("executed") and (attempt.get("timed_out") or attempt.get("returncode") == 124):
            return True
    return False


def managed_runtime_graph_timeout_observed(proof: dict[str, Any]) -> bool:
    """graph timeout 会连带阻断 lifecycle CLI，需和 map_server callback 返回失败分开。"""
    wait_result = proof.get("managed_runtime_wait_result") if isinstance(proof.get("managed_runtime_wait_result"), dict) else {}
    wait_reason = str(wait_result.get("reason") or wait_result.get("boundary") or "")
    graph_summary = wait_result.get("graph_wait_summary") if isinstance(wait_result.get("graph_wait_summary"), dict) else {}
    return bool(
        wait_reason in MANAGED_RUNTIME_GRAPH_BLOCKED_REASONS
        or graph_summary.get("latest_ros2_node_list_timed_out")
        or str(graph_summary.get("latest_ros2_node_list_boundary") or "").endswith("_timeout")
    )


def map_server_transition_stage(log_summary: dict[str, Any]) -> str:
    """用日志顺序判断当前失败停在 configure 还是 activate，避免误报 activation。"""
    events = log_summary.get("events") if isinstance(log_summary.get("events"), dict) else {}
    if events.get("activate_started"):
        return "activate"
    if events.get("configure_started") or events.get("yaml_load_started") or events.get("image_load_started"):
        return "configure"
    return "unknown"


def map_server_activation_map_readback_valid(activation_summary: dict[str, Any]) -> bool:
    """只在 yaml 字段、image 文件和 runtime 分析都通过时，才排除参数/文件类 root cause。"""
    readback = (
        activation_summary.get("map_yaml_pgm_readback")
        if isinstance(activation_summary.get("map_yaml_pgm_readback"), dict)
        else {}
    )
    validation = readback.get("validation") if isinstance(readback.get("validation"), dict) else {}
    return bool(
        validation.get("yaml_readable")
        and validation.get("image_readable")
        and validation.get("yaml_fields_valid")
        and validation.get("analysis_ok")
    )


def map_server_load_map_response_from_yaml_summary(
    *,
    activation_summary: dict[str, Any],
    log_summary: dict[str, Any],
    lifecycle_readback: dict[str, Any],
    classification: str,
    failure_detail: str,
) -> dict[str, Any]:
    """把 LoadMap response 观测边界写清楚：直接返回码缺失时，只能采信 runtime 等价证据。"""
    events = log_summary.get("events") if isinstance(log_summary.get("events"), dict) else {}
    timing = map_io_changestate_timing(log_summary)
    exception_text = str(log_summary.get("map_server_exception_text") or "")
    map_inputs_valid = map_server_activation_map_readback_valid(activation_summary)
    map_read_after_failure = bool(events.get("map_read_after_state_change_failure"))
    image_before_failure = bool(events.get("state_change_failed_after_image_load_before_map_read_completed"))
    change_state_before_completion = bool(events.get("changestate_response_false_before_map_io_completion"))
    success_equivalent = bool(map_inputs_valid and map_read_after_failure)
    if success_equivalent and change_state_before_completion:
        response_status = "success_equivalent_logged_after_lifecycle_changestate_failure"
        on_configure_return_path = "return_failure_before_deferred_loadmap_response_completion_log"
    elif exception_text:
        response_status = "error_string_logged_by_map_server"
        on_configure_return_path = "return_failure_with_map_server_exception_text"
    elif not map_inputs_valid:
        response_status = "not_validated_due_to_map_input_readback_failure"
        on_configure_return_path = "return_failure_before_valid_map_input_readback"
    elif events.get("map_read_completed"):
        response_status = "success_equivalent_map_read_completed_before_failure"
        on_configure_return_path = "return_failure_after_loadmap_response_completion_log"
    else:
        response_status = "not_observed"
        on_configure_return_path = "return_failure_with_loadmap_response_not_observed"
    return {
        "schema": "trashbot.o10.map_server_load_map_response_from_yaml.v1",
        "probe_source": "runtime_log_equivalent_evidence",
        "direct_return_code_observed": False,
        "return_code": "not_logged_by_nav2_map_server_runtime",
        "error_string_observed": bool(exception_text),
        "error_string": exception_text[-800:],
        "response_status": response_status,
        "response_status_evidence": {
            "map_input_validation_valid": map_inputs_valid,
            "yaml_load_started": bool(events.get("yaml_load_started")),
            "image_load_started": bool(events.get("image_load_started")),
            "map_read_completed": bool(events.get("map_read_completed")),
            "map_read_completed_after_state_failure": map_read_after_failure,
            "state_change_failed_after_image_load_before_map_read_completed": image_before_failure,
            "change_state_response_false_before_map_io_completion": change_state_before_completion,
        },
        "on_configure_return_path": on_configure_return_path,
        "load_map_response_status_at_changestate_failure": (
            "pending_or_not_logged"
            if change_state_before_completion
            else "completed_or_not_ordered_before_failure"
            if events.get("map_read_completed")
            else "not_observed"
        ),
        "lifecycle_changestate_response_handling": {
            "change_state_response_observed": bool(events.get("state_change_failed")),
            "inferred_response_status": "failure" if events.get("state_change_failed") else "not_observed",
            "service_timeout_or_rpc_error_observed": bool(
                events.get("service_timeout_or_rpc_error") or lifecycle_readback_has_timeout(lifecycle_readback)
            ),
            "response_before_loadmap_completion": change_state_before_completion,
            "failure_detail": failure_detail,
        },
        "executor_log_ordering_summary": {
            "classification": classification,
            "state_failure_before_map_server_configure_callback": bool(
                events.get("state_change_failed_before_map_server_configure_callback")
            ),
            "state_failure_after_image_before_map_read": image_before_failure,
            "map_io_timing": timing,
        },
        "evidence_quality": (
            "equivalent_runtime_evidence_no_direct_return_code"
            if success_equivalent
            else "runtime_log_boundary_without_direct_return_code"
        ),
    }


def map_server_on_configure_return_source_summary(
    *,
    activation_summary: dict[str, Any],
    log_summary: dict[str, Any],
    lifecycle_readback: dict[str, Any],
    classification: str,
    failure_detail: str,
    load_map_response_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """把 on_configure 失败来源落到可验收字段，避免只重复 ChangeState timing 现象。"""
    events = log_summary.get("events") if isinstance(log_summary.get("events"), dict) else {}
    readback = (
        activation_summary.get("map_yaml_pgm_readback")
        if isinstance(activation_summary.get("map_yaml_pgm_readback"), dict)
        else {}
    )
    validation = readback.get("validation") if isinstance(readback.get("validation"), dict) else {}
    timing = map_io_changestate_timing(log_summary)
    exception_text = str(log_summary.get("map_server_exception_text") or "")
    service_timeout = bool(events.get("service_timeout_or_rpc_error") or lifecycle_readback_has_timeout(lifecycle_readback))
    map_inputs_valid = map_server_activation_map_readback_valid(activation_summary)
    load_map_response = load_map_response_summary or map_server_load_map_response_from_yaml_summary(
        activation_summary=activation_summary,
        log_summary=log_summary,
        lifecycle_readback=lifecycle_readback,
        classification=classification,
        failure_detail=failure_detail,
    )
    if classification == "map_server_lifecycle_active":
        primary_source = "map_server_lifecycle_active"
        source_family = "lifecycle_active"
    elif exception_text:
        primary_source = "map_server_on_configure_exception_text_observed"
        source_family = "exception"
    elif not map_inputs_valid:
        primary_source = "map_server_on_configure_parameter_or_map_file_validation"
        source_family = "parameter_or_map_io_input"
    elif classification == "map_server_loadmap_response_success_equivalent_after_changestate_failure":
        primary_source = "loadmap_response_success_equivalent_logged_after_on_configure_failure"
        source_family = "loadMapResponseFromYaml_response_status"
    elif classification == "map_server_on_configure_return_false_after_valid_map_io_deferred_completion":
        primary_source = "on_configure_return_false_after_valid_map_inputs_while_map_io_log_completes_later"
        source_family = "on_configure_return_false_source"
    elif service_timeout:
        primary_source = "lifecycle_change_state_service_or_future_timeout"
        source_family = "executor_service_future"
    elif events.get("dds_shm_transport_error"):
        primary_source = "lifecycle_change_state_dds_transport_error"
        source_family = "executor_service_future"
    elif events.get("changestate_response_false_before_map_io_completion"):
        primary_source = "map_io_sync_async_ordering_before_return_source_confirmed"
        source_family = "map_io_sync_async_ordering"
    else:
        primary_source = "on_configure_return_source_not_observed"
        source_family = "unclassified"
    return {
        "schema": "trashbot.o10.map_server_on_configure_return_source.v1",
        "canonical_source": primary_source,
        "primary_source": primary_source,
        "source_family": source_family,
        "canonical_classification": classification,
        "failure_detail": failure_detail,
        "narrowed_from": "map_server_changestate_response_false_before_map_io_completion",
        "baseline_repeated_without_narrowing": classification in {
            "map_server_changestate_response_false_before_map_io_completion",
            "map_server_on_configure_return_false_after_valid_map_io_deferred_completion",
        },
        "map_input_validation": {
            "valid_for_map_server": map_inputs_valid,
            "yaml_readable": bool(validation.get("yaml_readable")),
            "image_readable": bool(validation.get("image_readable")),
            "yaml_fields_valid": bool(validation.get("yaml_fields_valid")),
            "analysis_ok": bool(validation.get("analysis_ok")),
            "width": validation.get("width"),
            "height": validation.get("height"),
            "cell_counts": validation.get("cell_counts") if isinstance(validation.get("cell_counts"), dict) else {},
        },
        "excluded_sources": {
            "parameter_or_map_file_invalid_excluded_by_readback": map_inputs_valid,
            "map_server_exception_text_observed": bool(exception_text),
            "service_timeout_or_rpc_error_observed": service_timeout,
            "dds_shm_transport_error_observed": bool(events.get("dds_shm_transport_error")),
        },
        "return_path_evidence": {
            "map_server_configure_callback_entered": bool(events.get("map_server_configure_callback_entered")),
            "yaml_load_started": bool(events.get("yaml_load_started")),
            "image_load_started": bool(events.get("image_load_started")),
            "state_change_failed": bool(events.get("state_change_failed")),
            "map_read_completed_after_state_failure": bool(events.get("map_read_after_state_change_failure")),
            "change_state_response_false_before_map_io_completion": bool(
                events.get("changestate_response_false_before_map_io_completion")
            ),
            "inferred_change_state_response": "failure" if events.get("state_change_failed") else "not_observed",
            "map_io_timing": timing,
        },
        "load_map_response_from_yaml": load_map_response,
        "on_configure_return_path": load_map_response.get("on_configure_return_path"),
        "executor_log_ordering_summary": load_map_response.get("executor_log_ordering_summary"),
        "lifecycle_changestate_response_handling": load_map_response.get("lifecycle_changestate_response_handling"),
        "next_step": (
            "inspect_on_configure_return_false_or_executor_ordering_around_deferred_loadmap_response"
            if source_family == "loadMapResponseFromYaml_response_status"
            else "inspect_nav2_map_server_loadMapResponseFromYaml_return_code_or_executor_log_ordering"
            if source_family == "on_configure_return_false_source"
            else "inspect_map_server_on_configure_return_source_for_current_family"
        ),
        "no_motion_invariants": {
            **safety_flags(),
            "path_generation_attempted": False,
            "path_generated": False,
            "sends_navigate_to_pose": False,
        },
    }


def classify_map_server_transition_callback_probe(
    *,
    proof: dict[str, Any],
    activation_summary: dict[str, Any],
    log_summary: dict[str, Any],
    lifecycle_readback: dict[str, Any],
) -> tuple[str, str, str]:
    """把 12-55 主 blocker 压到 callback/service/bond/RPC 层，而不是复用旧 activation 文案。"""
    if not proof.get("managed_runtime_requested"):
        return (
            "map_server_transition_probe_not_requested",
            "managed_runtime_opt_in_not_requested",
            "rerun_with_managed_runtime_opt_in_and_managed_map_yaml",
        )
    if activation_summary.get("canonical_classification") == "map_server_lifecycle_active" or lifecycle_readback.get("clean"):
        return (
            "map_server_lifecycle_active",
            "map_server_lifecycle_readback_active_after_transition_probe",
            "continue_map_topic_tf_planner_readiness_no_motion",
        )

    events = log_summary.get("events") if isinstance(log_summary.get("events"), dict) else {}
    line_indices = log_summary.get("line_indices") if isinstance(log_summary.get("line_indices"), dict) else {}
    commands = proof.get("commands") if isinstance(proof.get("commands"), dict) else {}
    managed = commands.get("managed_runtime") if isinstance(commands.get("managed_runtime"), dict) else {}
    process_returncode = managed.get("process_returncode")
    if process_returncode is None and isinstance(managed.get("cleanup_result"), dict):
        process_returncode = managed["cleanup_result"].get("process_returncode")
    if process_returncode not in (None, 0):
        return (
            "map_server_process_exited_during_transition",
            f"managed_runtime_process_returncode_{process_returncode}",
            "inspect_map_server_process_exit_and_recent_runtime_log",
        )
    if log_summary.get("map_server_exception_text"):
        return (
            "map_server_transition_callback_exception",
            "map_server_exception_text_observed_during_transition",
            "inspect_transition_exception_text_and_stack",
        )
    if events.get("bond_timeout"):
        return (
            "map_server_bond_wait_timeout_after_active" if events.get("activate_started") else "map_server_bond_creation_timeout",
            "lifecycle_manager_bond_timeout_observed_for_map_server",
            "inspect_lifecycle_manager_bond_timeout_and_map_server_executor",
        )
    if events.get("dds_shm_transport_error") and (
        events.get("state_change_failed")
        or lifecycle_readback_has_timeout(lifecycle_readback)
        or managed_runtime_graph_timeout_observed(proof)
    ):
        return (
            "map_server_change_state_rpc_dds_shm_transport_port_lock",
            "fastdds_shm_open_and_lock_file_failed_during_configure_change_state_or_graph_readback",
            "force_udp_only_fastdds_transport_or_clear_stale_shm_ports_then_rerun",
        )
    if events.get("state_change_failed"):
        # 现场日志明确只有 Configuring，没有 Activating；因此本轮把上一轮 activation 文案
        # 收窄到 configure ChangeState response/return path，保留 map read 的先后顺序。
        stage = map_server_transition_stage(log_summary)
        if events.get("state_change_failed_before_map_server_configure_callback"):
            return (
                "map_server_changestate_response_failure_before_configure_callback_log",
                "lifecycle_manager_changestate_response_failure_logged_before_map_server_on_configure_log",
                "inspect_lifecycle_manager_change_state_future_response_order_and_map_server_executor_timing",
            )
        if (
            events.get("state_change_failed_after_image_load_before_map_read_completed")
            and events.get("changestate_response_false_before_map_io_completion")
        ):
            if map_server_activation_map_readback_valid(activation_summary):
                return (
                    "map_server_loadmap_response_success_equivalent_after_changestate_failure",
                    "loadmap_response_success_equivalent_logged_after_lifecycle_changestate_failure_without_direct_return_code",
                    "inspect_on_configure_return_false_or_executor_ordering_around_deferred_loadmap_response",
                )
            return (
                "map_server_changestate_response_false_before_map_io_completion",
                "lifecycle_manager_changestate_response_false_while_map_io_completed_later",
                "inspect_map_server_on_configure_return_false_path_while_loadMapResponseFromYaml_continues",
            )
        if events.get("state_change_failed_after_image_load_before_map_read_completed"):
            return (
                "map_server_changestate_response_failure_after_image_load_before_map_read_completed",
                "lifecycle_manager_changestate_response_failure_after_image_load_before_map_read_completed",
                "inspect_lifecycle_manager_change_state_future_timeout_vs_map_io_image_decode_completion",
            )
        detail_suffix = (
            "after_map_read_completed"
            if events.get("map_read_completed") and not events.get("map_read_after_state_change_failure")
            else "before_deferred_map_read_completed"
            if events.get("map_read_after_state_change_failure")
            else "with_map_read_not_observed"
        )
        if stage == "activate":
            return (
                "map_server_activate_callback_return_failure",
                f"lifecycle_manager_changestate_response_failure_during_activate_{detail_suffix}",
                "inspect_map_server_on_activate_return_and_bond_creation",
            )
        if stage == "configure":
            if detail_suffix == "after_map_read_completed":
                return (
                    "map_server_configure_return_failure_after_map_read_completed",
                    "lifecycle_manager_changestate_response_failure_during_configure_after_map_read_completed",
                    "inspect_map_server_on_configure_return_after_successful_map_io_readback",
                )
            if detail_suffix == "before_deferred_map_read_completed":
                return (
                    "map_server_configure_return_failure_before_deferred_map_read_completed",
                    "lifecycle_manager_changestate_response_failure_during_configure_before_deferred_map_read_completed",
                    "inspect_lifecycle_manager_service_timeout_vs_map_io_read_completion_order",
                )
            return (
                "map_server_configure_callback_return_failure",
                f"lifecycle_manager_changestate_response_failure_during_configure_{detail_suffix}",
                "inspect_map_server_on_configure_return_path_map_io_completion_order",
            )
        return (
            "map_server_lifecycle_change_state_response_error",
            "lifecycle_manager_failed_to_change_state_without_configure_or_activate_stage_marker",
            "capture_longer_runtime_log_window_around_change_state_response",
        )
    if events.get("amcl_state_change_failed_after_map_server_configure_success"):
        return (
            "map_server_configure_completed_lifecycle_blocked_by_amcl_configure_failure",
            "lifecycle_manager_advanced_to_amcl_after_map_server_configure_then_amcl_changestate_failed",
            "inspect_amcl_on_configure_return_path_after_map_server_configure_success",
        )
    if events.get("service_timeout_or_rpc_error") or lifecycle_readback_has_timeout(lifecycle_readback):
        return (
            "map_server_lifecycle_service_rpc_timeout",
            "lifecycle_changestate_or_readback_rpc_timeout",
            "inspect_lifecycle_service_server_executor_or_dds_rpc_timing",
        )
    return (
        "map_server_transition_callback_unclassified",
        str(activation_summary.get("failure_detail") or "transition_callback_probe_no_matching_event"),
        "capture_lifecycle_change_state_service_response_and_map_server_log_window",
    )


def build_map_server_transition_callback_probe_summary(
    proof: dict[str, Any],
    *,
    presence_summary: dict[str, Any],
    activation_summary: dict[str, Any],
) -> dict[str, Any]:
    """12-55 主 artifact：新增 transition/service/bond/RPC timing proof，保持 no-motion。"""
    activation_runtime_log = (
        activation_summary.get("runtime_log")
        if isinstance(activation_summary.get("runtime_log"), dict)
        else {}
    )
    if activation_runtime_log:
        # activation summary 已合并 pre-cleanup evidence；transition 层必须复用这份强证据，
        # 否则 cleanup/SIGINT tail 会把 configure failure 回退成 unclassified。
        log_summary = {
            **activation_runtime_log,
            "events": dict(activation_runtime_log.get("events") or {}),
            "line_indices": dict(activation_runtime_log.get("line_indices") or {}),
        }
    else:
        log_summary = map_server_activation_log_summary(managed_runtime_log_for_activation(proof))
    lifecycle_readback = presence_summary.get("lifecycle_readback") if isinstance(presence_summary.get("lifecycle_readback"), dict) else {}
    launch_parameters = managed_runtime_launch_parameter_summary(proof)
    classification, failure_detail, next_step = classify_map_server_transition_callback_probe(
        proof=proof,
        activation_summary=activation_summary,
        log_summary=log_summary,
        lifecycle_readback=lifecycle_readback,
    )
    events = log_summary.get("events") if isinstance(log_summary.get("events"), dict) else {}
    line_indices = log_summary.get("line_indices") if isinstance(log_summary.get("line_indices"), dict) else {}
    event_timestamps = log_summary.get("event_timestamps_s") if isinstance(log_summary.get("event_timestamps_s"), dict) else {}
    stage = map_server_transition_stage(log_summary)
    manager_params = launch_parameters.get("lifecycle_manager") if isinstance(launch_parameters.get("lifecycle_manager"), dict) else {}
    service_timeout_s = manager_params.get("service_timeout_s")
    bond_timeout_s = manager_params.get("bond_timeout_s")
    map_io_timing = map_io_changestate_timing(log_summary)
    load_map_response = map_server_load_map_response_from_yaml_summary(
        activation_summary=activation_summary,
        log_summary=log_summary,
        lifecycle_readback=lifecycle_readback,
        classification=classification,
        failure_detail=failure_detail,
    )
    on_configure_return_source = map_server_on_configure_return_source_summary(
        activation_summary=activation_summary,
        log_summary=log_summary,
        lifecycle_readback=lifecycle_readback,
        classification=classification,
        failure_detail=failure_detail,
        load_map_response_summary=load_map_response,
    )
    return {
        "schema": "trashbot.o10.map_server_transition_callback_probe.v1",
        "proof_boundary": "software_proof_o3_o1_strict_no_motion_map_server_transition_callback_probe_only",
        "canonical_classification": classification,
        "classification": classification,
        "failure_detail": failure_detail,
        "classification_set": sorted(MAP_SERVER_TRANSITION_CALLBACK_CLASSIFICATIONS),
        "next_step": next_step,
        "transition_sequence": {
            "target_node": "/map_server",
            "observed_stage": stage,
            "configure": {
                "lifecycle_manager_requested": bool(events.get("lifecycle_manager_configure_requested")),
                "map_server_callback_entered": bool(events.get("map_server_configure_callback_entered")),
                "lifecycle_manager_configure_requested": bool(events.get("lifecycle_manager_configure_requested")),
                "map_server_configure_callback_log_observed": bool(events.get("map_server_configure_callback_entered")),
                "yaml_load_started": bool(events.get("yaml_load_started")),
                "image_load_started": bool(events.get("image_load_started")),
                "map_read_completed": bool(events.get("map_read_completed")),
                "state_change_failed": bool(events.get("state_change_failed")),
                "state_change_failed_before_map_read_completed": bool(events.get("map_read_after_state_change_failure")),
                "state_change_failed_after_image_load_before_map_read_completed": bool(
                    events.get("state_change_failed_after_image_load_before_map_read_completed")
                ),
                "state_change_failed_before_map_server_configure_callback": bool(
                    events.get("state_change_failed_before_map_server_configure_callback")
                ),
            },
            "activate": {
                "lifecycle_manager_requested": bool(events.get("activate_started")),
                "map_server_callback_entered": bool(events.get("activate_started")),
                "skipped_or_not_observed_reason": None if events.get("activate_started") else "configure_transition_not_clean_or_not_reached",
            },
            "amcl": {
                "lifecycle_manager_requested": bool(events.get("amcl_configure_requested")),
                "amcl_callback_entered": bool(events.get("amcl_configure_callback_entered")),
                "init_transforms": bool(events.get("amcl_init_transforms")),
                "init_pub_sub": bool(events.get("amcl_init_pub_sub")),
                "map_received": bool(events.get("amcl_map_received")),
                "state_change_failed": bool(events.get("amcl_state_change_failed")),
                "state_change_failed_after_map_server_configure_success": bool(
                    events.get("amcl_state_change_failed_after_map_server_configure_success")
                ),
            },
            "line_indices": line_indices,
            "event_timestamps_s": event_timestamps,
        },
        "service_rpc_timing": {
            "change_state_service_family": "/map_server/change_state",
            "service_timeout_s": service_timeout_s,
            "service_timeout_or_rpc_error_observed_in_log": bool(events.get("service_timeout_or_rpc_error")),
            "lifecycle_readback_timeout_observed": lifecycle_readback_has_timeout(lifecycle_readback),
            "lifecycle_readback": lifecycle_readback,
            "map_io_timing": map_io_timing,
            "state_change_failed_after_image_load_before_map_read_completed": bool(
                events.get("state_change_failed_after_image_load_before_map_read_completed")
            ),
            "changestate_response_false_before_map_io_completion": bool(
                events.get("changestate_response_false_before_map_io_completion")
            ),
            "state_change_failed_before_map_server_configure_callback": bool(
                events.get("state_change_failed_before_map_server_configure_callback")
            ),
            "inferred_change_state_response": (
                "failure" if events.get("state_change_failed") else "not_observed"
            ),
        },
        "load_map_response_from_yaml": load_map_response,
        "on_configure_return_source": on_configure_return_source,
        "bond_timing": {
            "bond_timeout_s": bond_timeout_s,
            "bond_created_observed": bool(events.get("bond_created")),
            "bond_timeout_observed": bool(events.get("bond_timeout")),
            "bond_destroyed_observed": bool(events.get("bond_destroyed")),
            "bond_stage": (
                "wait_timeout_after_active"
                if events.get("bond_timeout") and events.get("activate_started")
                else "not_created_before_configure_return_failure"
                if stage == "configure" and events.get("state_change_failed")
                else "not_observed"
            ),
        },
        "process_status": activation_summary.get("process_status") if isinstance(activation_summary.get("process_status"), dict) else {},
        "runtime_log_window": {
            "events": events,
            "line_indices": line_indices,
            "event_timestamps_s": event_timestamps,
            "map_server_stdout_stderr_tail": log_summary.get("map_server_stdout_stderr_tail"),
            "lifecycle_manager_log_tail": log_summary.get("lifecycle_manager_log_tail"),
            "exception_text": log_summary.get("exception_text"),
            "map_server_exception_text": log_summary.get("map_server_exception_text"),
            "dds_transport_error_text": log_summary.get("dds_transport_error_text"),
            "process_exit_lines": log_summary.get("process_exit_lines") if isinstance(log_summary.get("process_exit_lines"), list) else [],
        },
        "activation_summary_reference": {
            "canonical_classification": activation_summary.get("canonical_classification"),
            "failure_detail": activation_summary.get("failure_detail"),
            "map_yaml_pgm_valid": bool(
                ((activation_summary.get("map_yaml_pgm_readback") or {}).get("validation") or {}).get("yaml_fields_valid")
            ),
        },
        "no_motion_invariants": {
            **safety_flags(),
            "path_generation_attempted": False,
            "path_generated": False,
            "sends_navigate_to_pose": False,
        },
    }


def classify_rclpy_import_failure(message: str, environment_check: dict[str, Any] | None = None) -> str:
    """把 rclpy import 错误压成可行动 blocker，避免只留下裸 ImportError。"""
    lowered = str(message or "").lower()
    env = environment_check or {}
    ld_library_path = str(env.get("LD_LIBRARY_PATH") or env.get("ld_library_path") or "")
    pythonpath = str(env.get("PYTHONPATH") or env.get("pythonpath") or "")
    ament_prefix_path = str(env.get("AMENT_PREFIX_PATH") or env.get("ament_prefix_path") or "")
    if "no module named" in lowered and ("rclpy" in lowered or "sensor_msgs" in lowered):
        return "pythonpath_missing"
    if "cannot open shared object file" in lowered or "image not found" in lowered:
        if "/opt/ros/humble" not in ld_library_path:
            return "environment_not_sourced"
        return "missing_shared_library"
    if "_rclpy_pybind11" in lowered and any(
        needle in lowered
        for needle in (
            "undefined symbol",
            "wrong elf class",
            "version",
            "abi",
            "incompatible",
            "failed to be imported while being present",
        )
    ):
        # `_rclpy_pybind11` 已存在但加载失败时，常见根因是 Python ABI、架构或 rcl/rmw 共享库不匹配。
        return "python_abi_mismatch"
    if "/opt/ros/humble" not in ld_library_path or "/opt/ros/humble" not in pythonpath + ament_prefix_path:
        return "environment_not_sourced"
    return "unknown_import_failure"


def rclpy_scan_child_python_command(
    timeout_s: float,
    *,
    attempt_label: str,
    profile_label: str,
    reliability: str,
    durability: str,
) -> str:
    """生成在 sourced ROS shell 内执行的 Python probe，隔离主进程未 source 的动态库环境。"""
    return """python3 - <<'PY'
import json
import math
import os
import sys
import time
import traceback

TIMEOUT_S = %r
ATTEMPT_LABEL = %r
PROFILE_LABEL = %r
RELIABILITY_NAME = %r
DURABILITY_NAME = %r
STARTED_MS = int(time.time() * 1000)
os.environ.setdefault("RMW_FASTRTPS_USE_SHM", "0")
os.environ.setdefault("FASTDDS_BUILTIN_TRANSPORTS", "UDPv4")


def now_ms():
    return int(time.time() * 1000)


def compact_error(exc):
    return {"type": type(exc).__name__, "message": str(exc)[:240]}


def environment_check():
    keys = [
        "LD_LIBRARY_PATH",
        "PYTHONPATH",
        "AMENT_PREFIX_PATH",
        "COLCON_PREFIX_PATH",
        "RMW_IMPLEMENTATION",
        "RMW_FASTRTPS_USE_SHM",
        "FASTDDS_BUILTIN_TRANSPORTS",
    ]
    env = {key: os.environ.get(key, "") for key in keys}
    env.update(
        {
            "python_executable": sys.executable,
            "python_version": sys.version.split()[0],
            "cwd": os.getcwd(),
            "sys_path_preview": sys.path[:8],
            "ros_setup_source_boundary": "run_ros_bash_lc_source_prefix",
        }
    )
    return env


payload = {
    "command": f"rclpy {PROFILE_LABEL} once /scan",
    "executed": True,
    "ok": False,
    "returncode": None,
    "started_at_ms": STARTED_MS,
    "finished_at_ms": None,
    "timeout_s": TIMEOUT_S,
    "timed_out": False,
    "elapsed_ms": 0,
    "stdout": "",
    "stderr": "",
    "label": ATTEMPT_LABEL,
    "runtime": "ros_sourced_child_python",
    "fallback_boundary": "cli_fallback_allowed_after_child_rclpy_probe",
    "boundary": "rclpy_scan_child_started",
    "error": None,
    "import_check": {"attempted": True, "ok": False, "classification": None, "error": None},
    "environment_check": environment_check(),
    "frame_observed": False,
    "frame_stamp": None,
    "endpoint_inventory": {
        "publishers": [],
        "subscribers": [],
        "publisher_count": 0,
        "subscriber_count": 0,
        "inventory_observed": False,
        "error": None,
    },
    "requested_qos_profile": {
        "profile": PROFILE_LABEL,
        "history": "KEEP_LAST",
        "depth": 5,
        "reliability": RELIABILITY_NAME,
        "durability": DURABILITY_NAME,
    },
    "sample_timing": {
        "probe_window_sec": TIMEOUT_S,
        "sample_wait_started_at_ms": None,
        "sample_wait_finished_at_ms": None,
        "timeout_boundary_ms": STARTED_MS + int(max(float(TIMEOUT_S), 0.4) * 1000),
        "first_sample_latency_ms": None,
        "sample_count": 0,
        "last_sample_stamp": None,
        "last_sample_received_at_ms": None,
        "timed_out": False,
    },
    "child_runtime": {
        "import_ok": False,
        "node_created": False,
        "subscription_created": False,
        "sample_wait_started": False,
        "timeout_boundary_ms": STARTED_MS + int(max(float(TIMEOUT_S), 0.4) * 1000),
    },
}


def finish(returncode):
    payload["finished_at_ms"] = now_ms()
    payload["elapsed_ms"] = payload["finished_at_ms"] - STARTED_MS
    # child probe 是一次性进程；打印 payload 后直接退出，避免 rclpy cleanup 卡住导致父进程拿不到 JSON。
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)
    os._exit(returncode)


try:
    import rclpy
    from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
    from sensor_msgs.msg import LaserScan

    payload["import_check"]["ok"] = True
    payload["import_check"]["rclpy_file"] = getattr(rclpy, "__file__", "")
    payload["child_runtime"]["import_ok"] = True
except Exception as exc:
    payload["boundary"] = "rclpy_scan_child_import_failed"
    payload["error"] = compact_error(exc)
    payload["import_check"]["error"] = payload["error"]
    payload["stderr"] = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[-4000:]
    finish(3)

node = None
rclpy_initialized = False
message_holder = {"message": None}
try:
    if not rclpy.ok():
        rclpy.init(args=None)
        rclpy_initialized = True
    node = rclpy.create_node("o10_scan_probe_child")
    payload["child_runtime"]["node_created"] = True
    qos = QoSProfile(
        history=HistoryPolicy.KEEP_LAST,
        depth=5,
        reliability=getattr(ReliabilityPolicy, RELIABILITY_NAME),
        durability=getattr(DurabilityPolicy, DURABILITY_NAME),
    )

    def stamp_payload_from_message(message):
        header = getattr(message, "header", None)
        stamp = getattr(header, "stamp", None)
        try:
            stamp_payload = {
                "parsed": True,
                "sec": int(getattr(stamp, "sec")),
                "nanosec": int(getattr(stamp, "nanosec")),
                "source": "/scan.header.stamp",
            }
            stamp_payload["epoch_ms"] = int(stamp_payload["sec"] * 1000 + stamp_payload["nanosec"] / 1000000)
            return stamp_payload
        except Exception:
            return {"parsed": False, "reason": "stamp_fields_missing", "source": "/scan.header.stamp"}

    def on_scan(message):
        message_holder["message"] = message
        received_at_ms = now_ms()
        payload["sample_timing"]["sample_count"] += 1
        if payload["sample_timing"]["first_sample_latency_ms"] is None:
            wait_started_at_ms = payload["sample_timing"]["sample_wait_started_at_ms"] or STARTED_MS
            payload["sample_timing"]["first_sample_latency_ms"] = received_at_ms - int(wait_started_at_ms)
        payload["sample_timing"]["last_sample_received_at_ms"] = received_at_ms
        payload["sample_timing"]["last_sample_stamp"] = stamp_payload_from_message(message)

    def qos_value(value):
        name = getattr(value, "name", None)
        if name is not None:
            return str(name)
        try:
            return int(value)
        except Exception:
            return str(value)

    def qos_profile_payload(qos_profile):
        if qos_profile is None:
            return None
        output = {}
        for key in ("reliability", "durability", "history", "liveliness"):
            if hasattr(qos_profile, key):
                output[key] = qos_value(getattr(qos_profile, key))
        for key in ("depth", "deadline", "lifespan", "liveliness_lease_duration"):
            if hasattr(qos_profile, key):
                output[key] = qos_value(getattr(qos_profile, key))
        return output or None

    def endpoint_payload(endpoint):
        return {
            "node_name": str(getattr(endpoint, "node_name", "") or ""),
            "node_namespace": str(getattr(endpoint, "node_namespace", "") or ""),
            "topic_type": str(getattr(endpoint, "topic_type", "") or ""),
            "qos_profile": qos_profile_payload(getattr(endpoint, "qos_profile", None)),
        }

    def refresh_endpoint_inventory():
        try:
            publishers = [endpoint_payload(endpoint) for endpoint in node.get_publishers_info_by_topic("/scan")]
            subscribers = [endpoint_payload(endpoint) for endpoint in node.get_subscriptions_info_by_topic("/scan")]
            payload["endpoint_inventory"] = {
                "publishers": publishers,
                "subscribers": subscribers,
                "publisher_count": len(publishers),
                "subscriber_count": len(subscribers),
                "inventory_observed": True,
                "error": None,
                "source": "rclpy_child_get_publishers_info_by_topic",
            }
        except Exception as exc:
            payload["endpoint_inventory"]["error"] = compact_error(exc)

    node.create_subscription(LaserScan, "/scan", on_scan, qos)
    payload["child_runtime"]["subscription_created"] = True
    refresh_endpoint_inventory()
    deadline = time.time() + max(float(TIMEOUT_S), 0.4)
    payload["sample_timing"]["sample_wait_started_at_ms"] = now_ms()
    payload["sample_timing"]["timeout_boundary_ms"] = payload["sample_timing"]["sample_wait_started_at_ms"] + int(max(float(TIMEOUT_S), 0.4) * 1000)
    payload["child_runtime"]["sample_wait_started"] = True
    payload["child_runtime"]["timeout_boundary_ms"] = payload["sample_timing"]["timeout_boundary_ms"]
    while time.time() < deadline and message_holder["message"] is None:
        refresh_endpoint_inventory()
        rclpy.spin_once(node, timeout_sec=0.08)
    message = message_holder["message"]
    payload["sample_timing"]["sample_wait_finished_at_ms"] = now_ms()
    if message is None:
        payload["timed_out"] = True
        payload["sample_timing"]["timed_out"] = True
        payload["boundary"] = "rclpy_scan_child_timeout"
        finish(4)

    header = getattr(message, "header", None)
    stamp_payload = stamp_payload_from_message(message)
    ranges = list(getattr(message, "ranges", []) or [])
    preview = []
    for value in ranges[:6]:
        try:
            numeric = float(value)
            preview.append(numeric if math.isfinite(numeric) else str(value))
        except Exception:
            preview.append(str(value))
    payload["ok"] = True
    payload["frame_observed"] = True
    payload["frame_stamp"] = stamp_payload
    payload["boundary"] = "rclpy_scan_child_observed"
    payload["stdout"] = json.dumps(
        {
            "frame_id": str(getattr(header, "frame_id", "") or ""),
            "angle_min": float(getattr(message, "angle_min", 0.0)),
            "angle_max": float(getattr(message, "angle_max", 0.0)),
            "angle_increment": float(getattr(message, "angle_increment", 0.0)),
            "range_min": float(getattr(message, "range_min", 0.0)),
            "range_max": float(getattr(message, "range_max", 0.0)),
            "ranges_count": len(ranges),
            "ranges_preview": preview,
            "stamp": stamp_payload,
        },
        ensure_ascii=False,
    )
    finish(0)
except Exception as exc:
    payload["boundary"] = "rclpy_scan_child_failed"
    payload["error"] = compact_error(exc)
    payload["stderr"] = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[-4000:]
    finish(5)
finally:
    if node is not None:
        try:
            node.destroy_node()
        except Exception:
            pass
    if rclpy_initialized:
        try:
            if rclpy.ok():
                rclpy.shutdown()
        except Exception:
            pass
PY""" % (float(timeout_s), attempt_label, profile_label, reliability, durability)


def extract_child_probe_payload(stdout: str) -> dict[str, Any] | None:
    """source 脚本偶尔会有额外输出；只采最后一行 JSON probe payload。"""
    for raw_line in reversed(str(stdout or "").splitlines()):
        line = raw_line.strip()
        if not line.startswith("{"):
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and str(parsed.get("command") or "").startswith("rclpy "):
            return parsed
    return None


def rclpy_scan_once(
    args: argparse.Namespace,
    *,
    timeout_s: float,
    attempt_label: str,
    profile_label: str,
    reliability: str,
    durability: str,
) -> dict[str, Any]:
    """在 ROS-sourced 子 Python 里订阅 `/scan`，避免主进程未 source 导致 rclpy 动态库不可见。"""
    result: dict[str, Any] = {
        "command": f"rclpy {profile_label} once /scan",
        "executed": False,
        "ok": False,
        "returncode": None,
        "started_at_ms": now_ms(),
        "finished_at_ms": None,
        "timeout_s": timeout_s,
        "timed_out": False,
        "elapsed_ms": 0,
        "stdout": "",
        "stderr": "",
        "label": attempt_label,
        "runtime": "ros_sourced_child_python",
        "runtime_diagnostics": {},
        "fallback_boundary": "cli_fallback_allowed_after_child_rclpy_probe",
        "boundary": "rclpy_scan_child_not_started",
        "error": None,
        "import_check": {"attempted": False, "ok": False, "classification": None, "error": None},
        "endpoint_inventory": {
            "publishers": [],
            "subscribers": [],
            "publisher_count": 0,
            "subscriber_count": 0,
            "inventory_observed": False,
            "error": None,
        },
        "child_runtime": {
            "import_ok": False,
            "node_created": False,
            "subscription_created": False,
            "sample_wait_started": False,
            "timeout_boundary_ms": None,
        },
        "requested_qos_profile": {
            "profile": profile_label,
            "history": "KEEP_LAST",
            "depth": 5,
            "reliability": reliability,
            "durability": durability,
        },
        "sample_timing": {
            "probe_window_sec": timeout_s,
            "sample_wait_started_at_ms": None,
            "sample_wait_finished_at_ms": None,
            "timeout_boundary_ms": None,
            "first_sample_latency_ms": None,
            "sample_count": 0,
            "last_sample_stamp": None,
            "last_sample_received_at_ms": None,
            "timed_out": False,
        },
        "environment_check": {
            "ros_setup": str(args.ros_setup),
            "onboard_setup": str(args.onboard_setup),
            "workdir": str(args.workdir),
            "ros_setup_source_boundary": "run_ros_bash_lc_source_prefix",
        },
    }
    command = rclpy_scan_child_python_command(
        timeout_s,
        attempt_label=attempt_label,
        profile_label=profile_label,
        reliability=reliability,
        durability=durability,
    )
    child_process = run_ros(args, command, timeout_s=max(float(timeout_s) + 4.0, 6.0))
    payload = extract_child_probe_payload(str(child_process.get("stdout") or ""))
    result.update(
        {
            "executed": bool(child_process.get("executed")),
            "returncode": child_process.get("returncode"),
            "started_at_ms": child_process.get("started_at_ms", result["started_at_ms"]),
            "finished_at_ms": child_process.get("finished_at_ms"),
            "timeout_s": timeout_s,
            "timed_out": bool(child_process.get("timed_out")),
            "elapsed_ms": child_process.get("elapsed_ms", 0),
            "runtime_diagnostics": {
                "child_process": {
                    "returncode": child_process.get("returncode"),
                    "timed_out": bool(child_process.get("timed_out")),
                    "elapsed_ms": child_process.get("elapsed_ms"),
                    "stderr": str(child_process.get("stderr") or "")[-1200:],
                }
            },
        }
    )
    if payload is None:
        result["boundary"] = (
            "rclpy_scan_child_ros_environment_not_sourced"
            if "setup.bash" in str(child_process.get("stderr") or "")
            else "rclpy_scan_child_payload_missing"
        )
        result["error"] = child_process.get("error") if isinstance(child_process.get("error"), dict) else None
        result["stderr"] = str(child_process.get("stderr") or "")[-4000:]
        result["import_check"] = {
            "attempted": False,
            "ok": False,
            "classification": "environment_not_sourced",
            "error": result["error"],
        }
        return result

    environment_check = payload.get("environment_check") if isinstance(payload.get("environment_check"), dict) else {}
    import_check = payload.get("import_check") if isinstance(payload.get("import_check"), dict) else {}
    outer_child_timed_out = bool(child_process.get("timed_out"))
    if not import_check.get("ok"):
        message = ""
        if isinstance(import_check.get("error"), dict):
            message = str(import_check["error"].get("message") or "")
        message = f"{message}\n{payload.get('stderr') or ''}"
        import_check["classification"] = classify_rclpy_import_failure(message, environment_check)
        result["boundary"] = f"rclpy_scan_child_import_failed_{import_check['classification']}"
    else:
        result["boundary"] = str(payload.get("boundary") or "rclpy_scan_child_finished")
    result.update(
        {
            "ok": bool(payload.get("ok")),
            "timed_out": bool(payload.get("timed_out") or outer_child_timed_out),
            "stdout": str(payload.get("stdout") or ""),
            "stderr": str(payload.get("stderr") or ""),
            "error": payload.get("error") if isinstance(payload.get("error"), dict) else None,
            "import_check": import_check,
            "environment_check": environment_check or result["environment_check"],
            "fallback_boundary": payload.get("fallback_boundary") or result["fallback_boundary"],
            "frame_observed": bool(payload.get("frame_observed")),
            "frame_stamp": payload.get("frame_stamp") if isinstance(payload.get("frame_stamp"), dict) else None,
            "endpoint_inventory": (
                payload.get("endpoint_inventory")
                if isinstance(payload.get("endpoint_inventory"), dict)
                else result["endpoint_inventory"]
            ),
            "child_runtime": payload.get("child_runtime") if isinstance(payload.get("child_runtime"), dict) else result["child_runtime"],
            "requested_qos_profile": (
                payload.get("requested_qos_profile")
                if isinstance(payload.get("requested_qos_profile"), dict)
                else result["requested_qos_profile"]
            ),
            "sample_timing": payload.get("sample_timing") if isinstance(payload.get("sample_timing"), dict) else result["sample_timing"],
        }
    )
    if isinstance(result.get("sample_timing"), dict):
        # attempt 已被 timeout 判定时，sample_timing 也必须同步置真，避免 artifact 语义分裂。
        result["sample_timing"]["timed_out"] = bool(
            result["sample_timing"].get("timed_out")
            or result.get("timed_out")
            or result.get("returncode") == 124
        )
    if outer_child_timed_out and result["boundary"] == "rclpy_scan_child_failed" and not result.get("frame_observed"):
        # 父进程外层 timeout 比 payload 更可信；若 child 还没报告 sample，就把失败收口为 timeout。
        result["boundary"] = "rclpy_scan_child_timeout_after_outer_timeout"
    result["runtime_diagnostics"]["child_payload_boundary"] = payload.get("boundary")
    result["runtime_diagnostics"]["environment_check"] = result["environment_check"]
    return result


def scan_probe(args: argparse.Namespace, *, ros2_ok: bool) -> dict[str, Any]:
    """`/scan` 采用多尝试策略，优先留下 QoS/来源/timeout 诊断而不是单个布尔值。"""
    attempts: list[dict[str, Any]] = []
    best_result: dict[str, Any] | None = None
    best_attempt: dict[str, Any] | None = None
    probe_boundary = "scan_probe_not_attempted"
    if not ros2_ok:
        return {
            "executed": False,
            "ok": False,
            "boundary": "scan_probe_skipped_without_ros2",
            "attempts": attempts,
            "best_attempt": None,
            "qos_probe_boundary": "scan_probe_skipped_without_ros2",
            "source": None,
        }
    for spec in build_scan_probe_attempts(args):
        if spec["source"] == "rclpy_subscription":
            result = rclpy_scan_once(
                args,
                timeout_s=float(spec["timeout_s"]),
                attempt_label=str(spec["label"]),
                profile_label=str(spec.get("profile_label") or spec["qos_profile"]),
                reliability=str(spec.get("reliability") or "BEST_EFFORT"),
                durability=str(spec.get("durability") or "VOLATILE"),
            )
        else:
            result = run_ros(args, str(spec["command"]), timeout_s=float(spec["timeout_s"]))
        attempt = probe_attempt_artifact(
            result,
            label=str(spec["label"]),
            source=str(spec["source"]),
            qos_profile=str(spec["qos_profile"]) if spec.get("qos_profile") is not None else None,
        )
        attempts.append(attempt)
        if best_attempt is None:
            best_attempt = attempt
            best_result = result
        if attempt["observed"]:
            best_attempt = attempt
            best_result = result
            probe_boundary = "scan_probe_observed_after_qos_attempts"
            break
        if not best_attempt.get("timed_out") and attempt.get("timed_out"):
            # 已有更具体失败时不被 timeout 覆盖；否则保留最靠后的 timeout 结论。
            pass
        else:
            best_attempt = attempt
            best_result = result
        probe_boundary = str(attempt.get("boundary") or "scan_probe_attempt_failed")
    final_result = dict(best_result or {"executed": False, "ok": False})
    final_result["attempts"] = attempts
    final_result["best_attempt"] = best_attempt
    final_result["best_effort_attempt"] = next(
        (
            attempt
            for attempt in attempts
            if isinstance(attempt, dict)
            and isinstance(attempt.get("requested_qos_profile"), dict)
            and str(attempt["requested_qos_profile"].get("reliability") or "") == "BEST_EFFORT"
        ),
        None,
    )
    final_result["reliable_attempt"] = next(
        (
            attempt
            for attempt in attempts
            if isinstance(attempt, dict)
            and isinstance(attempt.get("requested_qos_profile"), dict)
            and str(attempt["requested_qos_profile"].get("reliability") or "") == "RELIABLE"
        ),
        None,
    )
    final_result["qos_probe_boundary"] = probe_boundary
    final_result["source"] = best_attempt.get("source") if isinstance(best_attempt, dict) else None
    return final_result


def lifecycle_checks(
    args: argparse.Namespace,
    nodes: dict[str, str] | None = None,
    *,
    graph_probe_result: dict[str, Any] | None = None,
) -> tuple[dict[str, bool], dict[str, dict[str, Any]]]:
    """只读 lifecycle 状态；不调用 transition，不启动 planner/controller。"""
    target_nodes = nodes or LOCALIZATION_LIFECYCLE_NODES
    graph_visibility = lifecycle_graph_visibility_snapshot(
        args,
        target_nodes,
        graph_probe_result=graph_probe_result,
    )
    active: dict[str, bool] = {}
    results: dict[str, dict[str, Any]] = {}
    for key, node in target_nodes.items():
        result = lifecycle_recovery_result(
            args,
            node_key=key,
            node_name=node,
            graph_visibility=graph_visibility,
        )
        active[key] = parse_lifecycle_active(result)
        results[key] = result
    return active, results


def merge_lifecycle_recheck(
    lifecycle_active: dict[str, bool],
    lifecycle_results: dict[str, dict[str, Any]],
    recheck_active: dict[str, bool],
    recheck_results: dict[str, dict[str, Any]],
) -> tuple[dict[str, bool], dict[str, dict[str, Any]]]:
    """首次 lifecycle 查询抖动时，用后续 recheck 的成功结果覆盖失败快照。"""
    merged_active = dict(lifecycle_active)
    merged_results = dict(lifecycle_results)
    for key, active in recheck_active.items():
        if active:
            merged_active[key] = True
            merged_results[key] = recheck_results[key]
    return merged_active, merged_results


def managed_param_file_text(
    args: argparse.Namespace,
    map_yaml: str,
    *,
    include_planner_server: bool = False,
) -> str:
    """managed runtime 默认只覆盖 localization；路径生成 opt-in 时再追加 planner 配置。"""
    lines = [
        "map_server:",
        "  ros__parameters:",
        "    use_sim_time: false",
        f"    yaml_filename: {json.dumps(map_yaml)}",
        '    frame_id: "map"',
        "amcl:",
        "  ros__parameters:",
        "    use_sim_time: false",
        f"    base_frame_id: {json.dumps(args.managed_base_frame_id)}",
        f"    odom_frame_id: {json.dumps(args.managed_odom_frame_id)}",
        '    global_frame_id: "map"',
        '    scan_topic: "scan"',
        "    tf_broadcast: true",
        "    set_initial_pose: false",
        "    save_pose_rate: 0.5",
        "    alpha1: 0.2",
        "    alpha2: 0.2",
        "    alpha3: 0.2",
        "    alpha4: 0.2",
        "    alpha5: 0.2",
        "    beam_skip_distance: 0.5",
        "    beam_skip_error_threshold: 0.9",
        "    beam_skip_threshold: 0.3",
        "    do_beamskip: false",
        "    lambda_short: 0.1",
        "    laser_likelihood_max_dist: 2.0",
        "    laser_max_range: 100.0",
        "    laser_min_range: -1.0",
        "    laser_model_type: likelihood_field",
        "    max_beams: 60",
        "    max_particles: 2000",
        "    min_particles: 500",
        "    pf_err: 0.05",
        "    pf_z: 0.99",
        "    recovery_alpha_fast: 0.0",
        "    recovery_alpha_slow: 0.0",
        "    resample_interval: 1",
        '    robot_model_type: "nav2_amcl::DifferentialMotionModel"',
        "    sigma_hit: 0.2",
        "    transform_tolerance: 1.0",
        "    update_min_a: 0.2",
        "    update_min_d: 0.25",
        "    z_hit: 0.5",
        "    z_max: 0.05",
        "    z_rand: 0.5",
        "    z_short: 0.05",
    ]
    if include_planner_server:
        # 这里只追加 planner/costmap 的冻结配置，避免把 bt_navigator 之类的执行层一起拉起来。
        lines.extend(
            [
                "planner_server:",
                "  ros__parameters:",
                "    expected_planner_frequency: 20.0",
                '    planner_plugins: ["GridBased"]',
                "    GridBased:",
                '      plugin: "nav2_navfn_planner/NavfnPlanner"',
                "      tolerance: 0.5",
                "      use_astar: false",
                "      allow_unknown: true",
                "",
                "costmap:",
                "  ros__parameters:",
                '    global_frame: "map"',
                '    robot_base_frame: "base_link"',
                "    update_frequency: 5.0",
                "    publish_frequency: 1.0",
                "    width: 10",
                "    height: 10",
                "    resolution: 0.05",
                "    track_unknown_space: true",
                '    plugins: ["static_layer", "obstacle_layer", "inflation_layer"]',
                "    static_layer:",
                '      plugin: "nav2_costmap_2d::StaticLayer"',
                "      map_subscribe_transient_local: true",
                "    obstacle_layer:",
                '      plugin: "nav2_costmap_2d::ObstacleLayer"',
                "      enabled: true",
                "      observation_sources: scan",
                "      scan:",
                "        topic: /scan",
                "        max_obstacle_height: 2.0",
                "        clearing: true",
                "        marking: true",
                '        data_type: "LaserScan"',
                "    inflation_layer:",
                '      plugin: "nav2_costmap_2d::InflationLayer"',
                "      cost_scaling_factor: 3.0",
                "      inflation_radius: 0.55",
                "",
            ]
        )
        lines.append("lifecycle_manager:")
        lines.append("  ros__parameters:")
        lines.append("    use_sim_time: false")
        lines.append("    autostart: true")
        lines.append("    bond_timeout: 8.0")
        lines.append("    service_timeout: 12.0")
        lines.append('    node_names: ["map_server", "amcl", "planner_server"]')
    else:
        lines.append("lifecycle_manager:")
        lines.append("  ros__parameters:")
        lines.append("    use_sim_time: false")
        lines.append("    autostart: true")
        lines.append("    bond_timeout: 8.0")
        lines.append("    service_timeout: 12.0")
        lines.append('    node_names: ["map_server", "amcl"]')
    lines.append("")
    return "\n".join(lines)


def managed_static_tf_broadcaster_command(args: argparse.Namespace) -> str:
    """用一个 rclpy 节点一次性 latch 两条静态 TF，避免两个 CLI publisher 的采样竞争。"""
    base_frame = str(args.managed_base_frame_id)
    odom_frame = str(args.managed_odom_frame_id)
    laser_frame = str(args.managed_laser_frame_id)
    code = r"""
import json
import sys

import rclpy
from geometry_msgs.msg import TransformStamped
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster


def make_transform(node, parent, child):
    # 两条边都是 no-motion proof 的固定几何关系；这里显式置零，避免引入底盘里程计假设。
    transform = TransformStamped()
    transform.header.stamp = node.get_clock().now().to_msg()
    transform.header.frame_id = parent
    transform.child_frame_id = child
    transform.transform.translation.x = 0.0
    transform.transform.translation.y = 0.0
    transform.transform.translation.z = 0.0
    transform.transform.rotation.x = 0.0
    transform.transform.rotation.y = 0.0
    transform.transform.rotation.z = 0.0
    transform.transform.rotation.w = 1.0
    return transform


def main():
    frames = json.loads(sys.argv[1])
    rclpy.init(args=None)
    node = rclpy.create_node("managed_static_tf_broadcaster")
    broadcaster = StaticTransformBroadcaster(node)

    def publish_static_transforms():
        # 同一个 TFMessage 同时包含 odom->base_link 与 base_link->laser_frame。
        # transient-local late subscriber 因此不再依赖两个独立 CLI publisher 的发现时序。
        broadcaster.sendTransform(
            [
                make_transform(node, frames["odom"], frames["base"]),
                make_transform(node, frames["base"], frames["laser"]),
            ]
        )

    publish_static_transforms()
    node.create_timer(0.5, publish_static_transforms)
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
""".strip()
    frames = json.dumps({"odom": odom_frame, "base": base_frame, "laser": laser_frame}, ensure_ascii=False)
    # 额外 argv token 只用于 ps/readback 归类，不参与控制逻辑；一个进程即可证明两条 edge 的 source。
    role_tokens = "static_tf_odom_base static_tf_base_laser odom_to_base_link base_link_to_laser_frame"
    return f"python3 -c {shlex.quote(code)} {shlex.quote(frames)} {role_tokens}"


def build_managed_runtime_shell(
    args: argparse.Namespace,
    *,
    map_yaml: str,
    params_path: str,
    log_path: str,
    include_planner_server: bool = False,
) -> str:
    """用一个 bash 进程组托管 runtime，便于统一 cleanup 且避免遗留后台子进程。"""
    lidar_port = shlex.quote(args.managed_lidar_serial_port)
    lidar_baud = int(args.managed_lidar_serial_baudrate)
    params = shlex.quote(params_path)
    map_yaml_quoted = shlex.quote(map_yaml)
    log = shlex.quote(log_path)
    laser_frame = shlex.quote(args.managed_laser_frame_id)
    reuse_existing_lidar = bool(getattr(args, "reuse_existing_lidar_lifecycle", False))
    commands = []
    if not reuse_existing_lidar:
        commands.append(
            # 这里单独记录 vendor 事实边界：LiDAR 只允许 /dev/ttyACM0@230400；不允许触碰 /dev/ttyS5。
            (
                "lidar_driver",
                "ros2 run ros2_trashbot_hardware lidar_driver --ros-args "
                f"-p serial_port:={lidar_port} "
                f"-p serial_baudrate:={lidar_baud} "
                f"-p frame_id:={laser_frame} "
                "-p scan_topic:=/scan "
                "-p publish_raw_packets:=false"
            )
        )
    commands.extend([
        (
            "static_tf_broadcaster",
            managed_static_tf_broadcaster_command(args),
        ),
        (
            "map_server",
            "ros2 run nav2_map_server map_server --ros-args "
            f"--params-file {params} -r __node:=map_server"
        ),
        (
            "amcl",
            "ros2 run nav2_amcl amcl --ros-args "
            f"--params-file {params} -r __node:=amcl"
        ),
    ])
    if include_planner_server:
        commands.append(
            (
                "planner_server",
                "ros2 run nav2_planner planner_server --ros-args "
                f"--params-file {params} -r __node:=planner_server"
            )
        )
    commands.append(
        (
            "lifecycle_manager",
            "ros2 run nav2_lifecycle_manager lifecycle_manager --ros-args "
            f"--params-file {params} -r __node:=lifecycle_manager"
        ),
    )
    lifecycle_start_delay_s = max(float(args.managed_lifecycle_start_delay_s), 0.0)
    lines = [
        "set -e",
        f"{source_prefix(args)}",
        *dds_no_shm_export_lines(),
        "pids=()",
        "cleanup(){ for pid in \"${pids[@]}\"; do kill -INT \"$pid\" 2>/dev/null || true; done; wait || true; }",
        "trap cleanup EXIT INT TERM",
        f"printf '%s\\n' 'managed_map_yaml={map_yaml_quoted}' > {log}",
        (
            "printf '%s\\n' "
            f"'managed_runtime_boundary={'no_motion_path_generation_planner_only' if include_planner_server else 'no_motion_localization_only'}' "
            ">> " + log
        ),
        "printf '%s\\n' 'blocked_device=/dev/ttyS5' >> " + log,
        (
            "printf '%s\\n' "
            f"'managed_lidar_policy={'reuse_existing_lidar_lifecycle_no_driver_start' if reuse_existing_lidar else 'start_managed_lidar_driver'}' "
            ">> " + log
        ),
    ]
    if reuse_existing_lidar:
        # 本轮 Gate 2 已由 `/api/radar/status` 证明现有 150000 lifecycle；这里只记录复用事实，
        # 不再打开 `/dev/ttyACM0` 或启动第二个 LiDAR driver，避免污染 holder/readback。
        lines.append(
            "printf '%s\\n' "
            f"'reuse_existing_lidar_lifecycle serial_port={lidar_port} serial_baudrate={lidar_baud} driver_started_by_helper=false' "
            ">> " + log
        )
    for role, command in commands:
        if role == "lifecycle_manager" and lifecycle_start_delay_s > 0:
            # map_server 加载地图和 AMCL 建 service 都有 ROS graph 发现延迟；过早 autostart 会触发生命周期 race。
            lines.append(f"printf '%s\\n' 'waiting before lifecycle_manager start delay_s={lifecycle_start_delay_s:g}' >> {log}")
            lines.append(f"sleep {lifecycle_start_delay_s:g}")
        # 每个子进程都追加到同一日志，便于远端 artifact 回放每个节点的启动顺序。
        lines.append(f"printf '%s\\n' 'starting role={role}' >> {log}")
        lines.append(f"({command}) >> {log} 2>&1 & pid=$!; pids+=($pid); printf '%s\\n' 'started role={role} pid='$pid >> {log}")
    lines.append("wait")
    return "; ".join(lines)


def stale_managed_runtime_process_groups_from_ps(
    ps_text: str,
    *,
    current_process_group: int | None = None,
) -> dict[int, list[dict[str, Any]]]:
    """从 ps 输出中找出历史 helper 托管的 no-motion runtime 进程组，避免误伤系统服务。"""
    groups: dict[int, list[dict[str, Any]]] = {}
    for raw_line in str(ps_text or "").splitlines():
        parts = raw_line.strip().split(maxsplit=2)
        if len(parts) < 3 or not parts[0].isdigit() or not parts[1].isdigit():
            continue
        pid = int(parts[0])
        pgid = int(parts[1])
        command = parts[2]
        if current_process_group is not None and pgid == current_process_group:
            continue
        marker_match = any(marker in command for marker in STALE_MANAGED_RUNTIME_MARKERS)
        role_match = any(marker in command for marker in STALE_MANAGED_RUNTIME_ROLE_MARKERS)
        if not (marker_match and role_match):
            continue
        groups.setdefault(pgid, []).append({"pid": pid, "pgid": pgid, "command": command[:500]})
    return groups


def cleanup_stale_managed_runtime_processes() -> dict[str, Any]:
    """启动新 runtime 前清理旧 helper 进程组；只作用于 no-motion 托管进程，不触碰底盘 UART。"""
    result: dict[str, Any] = {
        "attempted": True,
        "schema": "trashbot.o10.stale_managed_runtime_cleanup.v1",
        "groups": [],
        "group_count": 0,
        "ok": True,
        "motion_boundary": safety_flags(),
    }
    try:
        ps_result = subprocess.run(  # noqa: S603 - 固定 ps argv；只读进程表。
            ["ps", "-eo", "pid,pgid,command"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3.0,
            check=False,
        )
    except Exception as exc:  # pragma: no cover - ps 不可用时保守记录，不阻塞主 proof。
        result.update({"ok": False, "error": compact_error(exc), "boundary": "stale_cleanup_ps_failed"})
        return result
    groups = stale_managed_runtime_process_groups_from_ps(
        ps_result.stdout,
        current_process_group=os.getpgrp(),
    )
    result["group_count"] = len(groups)
    if not groups:
        result["boundary"] = "no_stale_managed_runtime_process_groups"
        return result
    for pgid, members in sorted(groups.items()):
        group_result: dict[str, Any] = {
            "process_group": pgid,
            "member_count": len(members),
            "members": members[:12],
            "sent_sigint": False,
            "sent_sigkill": False,
            "remaining_after_cleanup": [],
            "ok": True,
        }
        try:
            os.killpg(pgid, signal.SIGINT)
            group_result["sent_sigint"] = True
        except ProcessLookupError:
            pass
        except OSError as exc:
            group_result["ok"] = False
            group_result["error"] = compact_error(exc)
        time.sleep(0.8)
        remaining = process_group_members(pgid)
        if remaining:
            try:
                os.killpg(pgid, signal.SIGKILL)
                group_result["sent_sigkill"] = True
                time.sleep(0.3)
                remaining = process_group_members(pgid)
            except ProcessLookupError:
                remaining = []
            except OSError as exc:
                group_result["ok"] = False
                group_result["error_after_sigkill"] = compact_error(exc)
        group_result["remaining_after_cleanup"] = remaining[:12]
        group_result["ok"] = bool(group_result["ok"] and not remaining)
        result["groups"].append(group_result)
    result["ok"] = all(group.get("ok") for group in result["groups"])
    result["boundary"] = (
        "stale_managed_runtime_process_groups_cleaned"
        if result["ok"]
        else "stale_managed_runtime_process_groups_remain_after_cleanup"
    )
    return result


def start_managed_runtime(args: argparse.Namespace, *, map_yaml: str) -> dict[str, Any]:
    """显式 opt-in 时短暂拉起 localization graph；默认路径完全不触发本函数。"""
    started_ms = now_ms()
    stale_cleanup = cleanup_stale_managed_runtime_processes()
    params_fd, params_path = tempfile.mkstemp(prefix="rober_nav2_localization_", suffix=".yaml")
    os.close(params_fd)
    log_fd, log_path = tempfile.mkstemp(prefix="rober_nav2_localization_", suffix=".log")
    os.close(log_fd)
    include_planner_server = bool(args.path_generation_opt_in)
    Path(params_path).write_text(
        managed_param_file_text(args, map_yaml, include_planner_server=include_planner_server),
        encoding="utf-8",
    )
    process = subprocess.Popen(  # noqa: S603 - argv 固定；runtime 内容完全由 helper 生成。
        [
            "bash",
            "-lc",
            build_managed_runtime_shell(
                args,
                map_yaml=map_yaml,
                params_path=params_path,
                log_path=log_path,
                include_planner_server=include_planner_server,
            ),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    return {
        "requested": True,
        "started": True,
        "started_at_ms": started_ms,
        "process": process,
        "process_group": process.pid,
        "params_path": params_path,
        "log_path": log_path,
        "map_yaml": map_yaml,
        "pre_start_stale_cleanup": stale_cleanup,
        "managed_lidar_policy": (
            "reuse_existing_lidar_lifecycle_no_driver_start"
            if bool(getattr(args, "reuse_existing_lidar_lifecycle", False))
            else "start_managed_lidar_driver"
        ),
        "managed_lidar_serial_port": args.managed_lidar_serial_port,
        "managed_lidar_serial_baudrate": int(args.managed_lidar_serial_baudrate),
        "managed_lidar_driver_started_by_helper": not bool(getattr(args, "reuse_existing_lidar_lifecycle", False)),
        "boundary": (
            "explicit_opt_in_managed_path_generation_runtime_no_motion"
            if include_planner_server
            else "explicit_opt_in_managed_localization_runtime_no_motion"
        ),
        "vendor_boundary": (
            "Vendor facts from docs/vendor/VENDOR_INDEX.md: WAVE ROVER base is newline-delimited "
            "UART JSON, vendor Raspberry Pi UART path is not Orange Pi fixed fact; this proof only "
            "opens LiDAR /dev/ttyACM0 and never opens /dev/ttyS5."
        ),
    }


def preview_file(path: str, limit: int = 4000) -> str:
    """日志预览只取尾部，避免 artifact 被长 launch 输出淹没。"""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")[-limit:]
    except OSError:
        return ""


def cleanup_process_group(process_group: int, process: subprocess.Popen[str] | None = None) -> dict[str, Any]:
    """清理 managed runtime 进程组，并确认没有相同 PGID 的孤儿进程残留。"""
    if process_group <= 0:
        return {"attempted": False, "ok": False, "reason": "invalid_process_group"}
    result: dict[str, Any] = {
        "attempted": True,
        "process_group": process_group,
        "sent_signal": None,
        "killed_with_sigkill": False,
        "group_present_after_cleanup": None,
        "remaining_processes": [],
        "ok": False,
    }
    try:
        os.killpg(process_group, signal.SIGINT)
        result["sent_signal"] = "SIGINT"
    except ProcessLookupError:
        result["sent_signal"] = "already_exited"
    time.sleep(1.2)
    remaining = process_group_members(process_group)
    if remaining:
        try:
            os.killpg(process_group, signal.SIGKILL)
            result["killed_with_sigkill"] = True
        except ProcessLookupError:
            pass
        time.sleep(0.5)
    # 统一 wait 子 shell，避免 defunct bash 被误记成残留进程组。
    if process is not None:
        try:
            process.communicate(timeout=5.0)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
    remaining = process_group_members(process_group)
    result["remaining_processes"] = remaining
    result["group_present_after_cleanup"] = bool(remaining)
    result["ok"] = not remaining
    return result


def process_group_members(process_group: int) -> list[dict[str, Any]]:
    """进程组残留检查只按 PGID 过滤，避免把系统上其他 ROS2 进程误算进本轮。"""
    try:
        completed = subprocess.run(
            ["ps", "-eo", "pid=,pgid=,command="],
            check=False,
            text=True,
            capture_output=True,
            timeout=5.0,
        )
    except Exception as exc:  # noqa: BLE001 - 清场失败也必须结构化写回 artifact。
        return [{"error": compact_error(exc)}]
    result: list[dict[str, Any]] = []
    for raw_line in completed.stdout.splitlines():
        parts = raw_line.strip().split(None, 2)
        if len(parts) != 3:
            continue
        pid_text, pgid_text, command = parts
        if pgid_text != str(process_group):
            continue
        result.append({"pid": int(pid_text), "pgid": int(pgid_text), "command": command})
    return result


def managed_static_tf_process_summary(args: argparse.Namespace, runtime: dict[str, Any]) -> dict[str, Any]:
    """记录 managed static TF 进程源，区分没启动、已退出和 QoS/timing 未观测。"""
    expected = [
        {
            "role": "static_tf_odom_base",
            "parent": str(args.managed_odom_frame_id),
            "child": str(args.managed_base_frame_id),
        },
        {
            "role": "static_tf_base_laser",
            "parent": str(args.managed_base_frame_id),
            "child": str(args.managed_laser_frame_id),
        },
    ]
    process_group = runtime.get("process_group")
    members = process_group_members(int(process_group)) if process_group else []
    static_processes: list[dict[str, Any]] = []
    observed_roles: list[str] = []
    for process in members:
        command = str(process.get("command") or "")
        if "static_transform_publisher" not in command and "managed_static_tf_broadcaster" not in command:
            continue
        matched_role = "unknown_static_tf"
        matched_roles: list[str] = []
        for item in expected:
            role_token = item["role"]
            # 新 runtime 用一个 rclpy broadcaster 发布两条 edge；旧 CLI 进程仍保留兼容归类。
            if role_token in command or (item["parent"] in command and item["child"] in command):
                matched_role = item["role"]
                matched_roles.append(matched_role)
                observed_roles.append(matched_role)
        static_processes.append(
            {
                **process,
                "role": matched_role,
                "roles": sorted(set(matched_roles)) or [matched_role],
                "source_type": (
                    "single_rclpy_static_transform_broadcaster"
                    if "managed_static_tf_broadcaster" in command
                    else "tf2_ros_static_transform_publisher"
                ),
            }
        )
    return {
        "expected": expected,
        "observed_roles": sorted(set(observed_roles)),
        "processes": static_processes,
        "process_group": process_group,
        "all_expected_processes_observed": all(item["role"] in observed_roles for item in expected),
        "source_strategy": "single_rclpy_static_transform_broadcaster_transient_local",
        "checked_before_cleanup": bool(runtime.get("started")),
    }


def managed_runtime_cleanup_guard(process_group: int | None) -> dict[str, Any]:
    """把清场守卫显式写成 artifact 字段，便于测试锁定 no-orphan 要求。"""
    if not process_group:
        return {"ok": True, "boundary": "no_managed_runtime_process_group_started"}
    remaining = process_group_members(process_group)
    return {
        "ok": not remaining,
        "boundary": "managed_runtime_process_group_cleanup_guard",
        "remaining_processes": remaining,
    }


def endpoint_group_summary(raw: dict[str, Any], key: str) -> dict[str, Any]:
    """端点摘要限制字段和数量，避免 graph 细节把 proof 变成不可读日志。"""
    nodes = raw.get(key) if isinstance(raw.get(key), list) else []
    clean_nodes = [
        {
            "node_name": str(node.get("node_name") or ""),
            "node_namespace": str(node.get("node_namespace") or ""),
            "topic_type": str(node.get("topic_type") or ""),
            "qos_profile": node.get("qos_profile") if isinstance(node.get("qos_profile"), dict) else None,
        }
        for node in nodes[:6]
        if isinstance(node, dict)
    ]
    count_key = "publisher_count" if key == "publishers" else "subscriber_count"
    return {"count": int(raw.get(count_key) or len(clean_nodes)), "nodes": clean_nodes}


def signal_probe_summary(result: dict[str, Any], *, observed: bool, boundary_fallback: str) -> dict[str, Any]:
    """把不同来源的 probe 统一成 observed/elapsed/timeout 结构，供 root cause 复用。"""
    summary = {
        "executed": bool(result.get("executed")),
        "observed": bool(observed),
        "returncode": result.get("returncode"),
        "elapsed_ms": result.get("elapsed_ms"),
        "timeout_s": result.get("timeout_s"),
        "timed_out": bool(result.get("timed_out") or result.get("returncode") == 124),
        "boundary": result.get("boundary") or boundary_fallback,
        "error": result.get("error") if isinstance(result.get("error"), dict) else None,
    }
    if isinstance(result.get("attempts"), list):
        summary["attempts"] = [
            dict(attempt)
            for attempt in result["attempts"][:6]
            if isinstance(attempt, dict)
        ]
    if isinstance(result.get("best_attempt"), dict):
        summary["best_attempt"] = dict(result["best_attempt"])
    if isinstance(result.get("best_effort_attempt"), dict):
        summary["best_effort_attempt"] = dict(result["best_effort_attempt"])
    if isinstance(result.get("reliable_attempt"), dict):
        summary["reliable_attempt"] = dict(result["reliable_attempt"])
    if result.get("qos_probe_boundary") is not None:
        summary["qos_probe_boundary"] = result.get("qos_probe_boundary")
    if result.get("source") is not None:
        summary["source"] = result.get("source")
    return summary


def requested_qos_profile_from_probe(probe_result: dict[str, Any]) -> dict[str, Any] | None:
    """把 probe 请求的 QoS 标准化，方便和 endpoint QoS 同屏比较。"""
    best_attempt = probe_result.get("best_attempt") if isinstance(probe_result.get("best_attempt"), dict) else {}
    attempts = probe_result.get("attempts") if isinstance(probe_result.get("attempts"), list) else []
    for attempt in attempts:
        if (
            isinstance(attempt, dict)
            and bool(attempt.get("observed"))
            and isinstance(attempt.get("requested_qos_profile"), dict)
        ):
            return dict(attempt["requested_qos_profile"])
    for attempt in attempts:
        if isinstance(attempt, dict) and isinstance(attempt.get("requested_qos_profile"), dict):
            # `/scan` 的 child rclpy 订阅是主判据；无成功样本时保留第一条 child QoS 作为默认对照。
            return dict(attempt["requested_qos_profile"])
    candidate = (
        best_attempt.get("requested_qos_profile")
        if isinstance(best_attempt.get("requested_qos_profile"), dict)
        else probe_result.get("requested_qos_profile")
        if isinstance(probe_result.get("requested_qos_profile"), dict)
        else None
    )
    if candidate:
        return dict(candidate)
    qos_profile = str(best_attempt.get("qos_profile") or probe_result.get("qos_profile") or "")
    if qos_profile == "sensor_data":
        return {
            "profile": "sensor_data",
            "history": "KEEP_LAST",
            "reliability": "BEST_EFFORT",
            "durability": "VOLATILE",
        }
    if qos_profile == "default":
        return {"profile": "ros2_cli_default"}
    return None


def sample_timing_from_probe(probe_result: dict[str, Any], *, observed: bool) -> dict[str, Any]:
    """sample timing 以 child rclpy payload 为准；CLI fallback 缺细节时保持空字段。"""
    best_attempt = probe_result.get("best_attempt") if isinstance(probe_result.get("best_attempt"), dict) else {}
    attempts = probe_result.get("attempts") if isinstance(probe_result.get("attempts"), list) else []
    observed_child_attempt = next(
        (
            attempt
            for attempt in attempts
            if isinstance(attempt, dict)
            and isinstance(attempt.get("sample_timing"), dict)
            and (
                bool(attempt.get("observed"))
                or int(((attempt.get("sample_timing") or {}).get("sample_count") or 0)) > 0
            )
        ),
        None,
    )
    child_attempt = next(
        (
            attempt
            for attempt in attempts
            if isinstance(attempt, dict) and isinstance(attempt.get("sample_timing"), dict)
        ),
        None,
    )
    raw_timing = (
        observed_child_attempt.get("sample_timing")
        if isinstance(observed_child_attempt, dict)
        else best_attempt.get("sample_timing")
        if isinstance(best_attempt.get("sample_timing"), dict)
        else child_attempt.get("sample_timing")
        if isinstance(child_attempt, dict)
        else best_attempt.get("sample_timing")
        if isinstance(best_attempt.get("sample_timing"), dict)
        else probe_result.get("sample_timing")
        if isinstance(probe_result.get("sample_timing"), dict)
        else {}
    )
    timing = {
        "probe_window_sec": raw_timing.get("probe_window_sec", probe_result.get("timeout_s")),
        "sample_wait_started_at_ms": raw_timing.get("sample_wait_started_at_ms"),
        "sample_wait_finished_at_ms": raw_timing.get("sample_wait_finished_at_ms"),
        "timeout_boundary_ms": raw_timing.get("timeout_boundary_ms"),
        "first_sample_latency_ms": raw_timing.get("first_sample_latency_ms"),
        "sample_count": int(raw_timing.get("sample_count") or (1 if observed else 0)),
        "last_sample_stamp": raw_timing.get("last_sample_stamp") if isinstance(raw_timing.get("last_sample_stamp"), dict) else None,
        "last_sample_received_at_ms": raw_timing.get("last_sample_received_at_ms"),
        "timed_out": bool(raw_timing.get("timed_out") or probe_result.get("timed_out") or probe_result.get("returncode") == 124),
    }
    if observed and timing["sample_count"] <= 0:
        # 旧 stdout-only probe 成功时没有 sample_count；这里补 1，避免 observed 与 timing 自相矛盾。
        timing["sample_count"] = 1
    return timing


def endpoint_inventory_summary(
    *,
    topic: str,
    topic_type: str | None,
    endpoint_summary: dict[str, Any],
    requested_qos_profile: dict[str, Any] | None,
) -> dict[str, Any]:
    """保留最小 endpoint 和 QoS 清单，支撑本轮 scan timeout root-cause 拆分。"""
    publishers = endpoint_group_summary(endpoint_summary, "publishers")
    subscribers = endpoint_group_summary(endpoint_summary, "subscribers")
    qos_profiles = {
        "publishers": [
            node.get("qos_profile")
            for node in publishers["nodes"]
            if isinstance(node.get("qos_profile"), dict)
        ],
        "subscribers": [
            node.get("qos_profile")
            for node in subscribers["nodes"]
            if isinstance(node.get("qos_profile"), dict)
        ],
    }
    return {
        "topic": topic,
        "topic_visible": topic_type is not None,
        "topic_type": topic_type,
        "inventory_observed": bool(endpoint_summary.get("inventory_observed")),
        "publisher_count": publishers["count"],
        "subscriber_count": subscribers["count"],
        "publishers": publishers["nodes"],
        "subscribers": subscribers["nodes"],
        "endpoint_qos_profiles": qos_profiles,
        "requested_qos_profile": requested_qos_profile,
        "error": endpoint_summary.get("error") if isinstance(endpoint_summary.get("error"), dict) else None,
    }


def endpoint_summary_from_scan_probe(scan_once: dict[str, Any]) -> dict[str, Any] | None:
    """`/scan` endpoint inventory 优先复用 sourced child probe，绕开主进程 rclpy graph 失效。"""
    attempts = scan_once.get("attempts") if isinstance(scan_once.get("attempts"), list) else []
    for attempt in attempts:
        inventory = attempt.get("endpoint_inventory") if isinstance(attempt, dict) else None
        if isinstance(inventory, dict) and inventory.get("inventory_observed"):
            return inventory
    inventory = scan_once.get("endpoint_inventory") if isinstance(scan_once.get("endpoint_inventory"), dict) else None
    if isinstance(inventory, dict) and inventory.get("inventory_observed"):
        return inventory
    return None


def scan_probe_classification(
    *,
    topic_present: bool,
    endpoint_inventory: dict[str, Any],
    probe: dict[str, Any],
    sample_timing: dict[str, Any],
    observed: bool,
    managed_runtime_started: bool | None,
) -> str:
    """把 `/scan` blocker 固定到可执行分类，避免继续把所有失败归成 child timeout。"""
    publisher_count = int(endpoint_inventory.get("publisher_count") or 0)
    inventory_observed = bool(endpoint_inventory.get("inventory_observed"))
    attempts = probe.get("attempts") if isinstance(probe.get("attempts"), list) else []
    best_attempt = probe.get("best_attempt") if isinstance(probe.get("best_attempt"), dict) else {}
    best_effort_attempt = probe.get("best_effort_attempt") if isinstance(probe.get("best_effort_attempt"), dict) else {}
    reliable_attempt = probe.get("reliable_attempt") if isinstance(probe.get("reliable_attempt"), dict) else {}
    if observed or int(sample_timing.get("sample_count") or 0) > 0:
        return "/scan_sample_observed"
    if inventory_observed and publisher_count <= 0:
        if managed_runtime_started is False:
            return "/scan_lidar_runtime_not_started"
        return "/scan_no_publisher"
    if inventory_observed and publisher_count > 0:
        if best_effort_attempt and reliable_attempt:
            if best_effort_attempt.get("timed_out") and reliable_attempt.get("timed_out"):
                return "/scan_reliable_and_best_effort_timeout"
        timed_attempts = [attempt for attempt in attempts if isinstance(attempt, dict) and attempt.get("timed_out")]
        if len(timed_attempts) >= 2 or str(best_attempt.get("qos_profile") or "") == "sensor_data":
            return "/scan_qos_or_window_timeout"
        return "/scan_publisher_visible_but_no_sample"
    import_check = best_attempt.get("import_check") if isinstance(best_attempt.get("import_check"), dict) else {}
    if best_attempt.get("source") == "rclpy_subscription" and import_check.get("ok") is True:
        child_runtime = best_attempt.get("child_runtime") if isinstance(best_attempt.get("child_runtime"), dict) else {}
        if child_runtime.get("subscription_created") or probe.get("timed_out") or best_attempt.get("timed_out"):
            return "/scan_rclpy_child_timeout_after_import"
    if probe.get("timed_out"):
        return "/scan_qos_or_window_timeout"
    if not topic_present:
        return "/scan_no_publisher"
    return "/scan_publisher_visible_but_no_sample"


def publisher_inventory_from_endpoint(
    *,
    topic_type: str | None,
    endpoint_inventory: dict[str, Any],
) -> dict[str, Any]:
    """publisher inventory 给现场排查第一眼使用：topic 是否可见、publisher 是谁。"""
    return {
        "topic_visible": topic_type is not None,
        "topic_type": topic_type,
        "inventory_observed": bool(endpoint_inventory.get("inventory_observed")),
        "publisher_count": int(endpoint_inventory.get("publisher_count") or 0),
        "publisher_nodes": endpoint_inventory.get("publishers") if isinstance(endpoint_inventory.get("publishers"), list) else [],
        "blocked_reason": None,
    }


def child_runtime_from_probe(probe_result: dict[str, Any]) -> dict[str, Any] | None:
    """child runtime 优先取 rclpy attempt，避免最后一条 CLI fallback 把关键 timing 顶掉。"""
    attempts = probe_result.get("attempts") if isinstance(probe_result.get("attempts"), list) else []
    for attempt in attempts:
        if isinstance(attempt, dict) and isinstance(attempt.get("child_runtime"), dict):
            return dict(attempt["child_runtime"])
    best_attempt = probe_result.get("best_attempt") if isinstance(probe_result.get("best_attempt"), dict) else {}
    if isinstance(best_attempt.get("child_runtime"), dict):
        return dict(best_attempt["child_runtime"])
    if isinstance(probe_result.get("child_runtime"), dict):
        return dict(probe_result["child_runtime"])
    return None


def select_amcl_pose_probe(
    amcl_pose_once: dict[str, Any],
    post_initialpose_amcl_pose_once: dict[str, Any],
) -> dict[str, Any]:
    """AMCL pose 以 post-initialpose 为主；若前置 probe 已观测，则保留最有信息的一条。"""
    if topic_once_observed(post_initialpose_amcl_pose_once) or post_initialpose_amcl_pose_once.get("executed"):
        return post_initialpose_amcl_pose_once
    return amcl_pose_once


def build_signal_entry(
    *,
    topic: str,
    topic_type: str | None,
    endpoint_summary: dict[str, Any],
    probe_result: dict[str, Any],
    observed: bool,
    stamp: dict[str, Any],
    source_class: str,
    reference_ms: int,
    managed_runtime_started: bool | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """单个 signal 的 schema 固定，后续 O6/O7 消费不用理解 ROS CLI 原文。"""
    requested_qos_profile = requested_qos_profile_from_probe(probe_result)
    endpoint_inventory = endpoint_inventory_summary(
        topic=topic,
        topic_type=topic_type,
        endpoint_summary=endpoint_summary,
        requested_qos_profile=requested_qos_profile,
    )
    entry = {
        "topic": topic,
        "expected_type": LOCALIZATION_SIGNAL_TOPICS.get(topic),
        "topic_type": topic_type,
        "topic_present": topic_type is not None,
        "source_class": source_class,
        "endpoint_inventory_observed": bool(endpoint_summary.get("inventory_observed")),
        "publishers": endpoint_group_summary(endpoint_summary, "publishers"),
        "subscribers": endpoint_group_summary(endpoint_summary, "subscribers"),
        "endpoint_error": endpoint_summary.get("error") if isinstance(endpoint_summary.get("error"), dict) else None,
        "probe": signal_probe_summary(probe_result, observed=observed, boundary_fallback=f"{topic}_probe_not_observed"),
        "timestamp": stamp,
        "freshness": freshness_from_stamp(
            stamp,
            observed=observed,
            source_class=source_class,
            reference_ms=reference_ms,
        ),
        "endpoint_inventory": endpoint_inventory,
    }
    if topic == "/scan":
        sample_timing = sample_timing_from_probe(probe_result, observed=observed)
        publisher_inventory = publisher_inventory_from_endpoint(
            topic_type=topic_type,
            endpoint_inventory=endpoint_inventory,
        )
        classification = scan_probe_classification(
            topic_present=topic_type is not None,
            endpoint_inventory=endpoint_inventory,
            probe=entry["probe"],
            sample_timing=sample_timing,
            observed=observed,
            managed_runtime_started=managed_runtime_started,
        )
        publisher_inventory["blocked_reason"] = None if classification == "/scan_sample_observed" else classification
        entry.update(
            {
                "publisher_inventory": publisher_inventory,
                "endpoint_inventory": endpoint_inventory,
                "sample_timing": sample_timing,
                "managed_runtime_scan_status": {
                    "managed_runtime_started": managed_runtime_started,
                    "topic_visible": topic_type is not None,
                    "lidar_runtime_started": bool(endpoint_inventory["inventory_observed"] and endpoint_inventory["publisher_count"] > 0),
                    "publisher_visible": bool(endpoint_inventory["publisher_count"] > 0),
                    "sample_observed": bool(observed),
                    "blocked_reason": None if classification == "/scan_sample_observed" else classification,
                },
            }
        )
        entry["probe"]["classification"] = classification
        entry["probe"]["child_runtime"] = child_runtime_from_probe(probe_result)
        entry["probe"]["requested_qos_profile"] = requested_qos_profile
    if extra:
        entry.update(extra)
    return entry


def build_localization_signal_freshness(
    *,
    generated_at_ms: int,
    tf_source_diagnostics: dict[str, Any],
    tf_source_probe_result: dict[str, Any],
    topic_list_result: dict[str, Any],
    scan_once: dict[str, Any],
    amcl_pose_once: dict[str, Any],
    post_initialpose_amcl_pose_once: dict[str, Any],
    odom_once: dict[str, Any],
    managed_runtime_started: bool | None = None,
    map_once: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """汇总 `/scan`、`/map`、`/amcl_pose`、`/odom` 与 TF topic 的 freshness/source 事实。"""
    inventory = tf_source_diagnostics.get("tf_frame_inventory") if isinstance(tf_source_diagnostics.get("tf_frame_inventory"), dict) else {}
    topic_types = inventory.get("topic_types") if isinstance(inventory.get("topic_types"), dict) else {}
    listed_topic_types = parse_topic_list_with_types(str(topic_list_result.get("stdout") or ""))
    if listed_topic_types:
        topic_types = {**listed_topic_types, **topic_types}
    endpoints = tf_source_diagnostics.get("topic_endpoint_summaries") if isinstance(tf_source_diagnostics.get("topic_endpoint_summaries"), dict) else {}
    dynamic_edges = inventory.get("dynamic_edges") if isinstance(inventory.get("dynamic_edges"), list) else []
    static_edges = inventory.get("static_edges") if isinstance(inventory.get("static_edges"), list) else []
    dynamic_transforms = inventory.get("dynamic_transforms") if isinstance(inventory.get("dynamic_transforms"), list) else []
    static_transforms = inventory.get("static_transforms") if isinstance(inventory.get("static_transforms"), list) else []
    command_statuses = inventory.get("command_statuses") if isinstance(inventory.get("command_statuses"), dict) else {}
    amcl_probe = select_amcl_pose_probe(amcl_pose_once, post_initialpose_amcl_pose_once)
    direct_amcl_pose_sample = (
        tf_source_diagnostics.get("amcl_pose_sample")
        if isinstance(tf_source_diagnostics.get("amcl_pose_sample"), dict)
        else {}
    )
    if direct_amcl_pose_sample.get("observed"):
        # strict-no-motion 不发布 initialpose；source child 的只读订阅是本轮唯一同窗 pose 样本来源。
        amcl_probe = {
            "executed": True,
            "ok": True,
            "observed": True,
            "returncode": 0,
            "finished_at_ms": direct_amcl_pose_sample.get("received_at_ms"),
            "elapsed_ms": tf_source_probe_result.get("elapsed_ms"),
            "timeout_s": None,
            "timed_out": False,
            "boundary": "amcl_pose_sample_observed_by_tf_source_child",
        }

    def endpoint(topic: str) -> dict[str, Any]:
        if topic == "/scan":
            scan_endpoint = endpoint_summary_from_scan_probe(scan_once)
            if scan_endpoint is not None:
                return scan_endpoint
        value = endpoints.get(topic)
        return (
            value
            if isinstance(value, dict)
            else {
                "publishers": [],
                "subscribers": [],
                "publisher_count": 0,
                "subscriber_count": 0,
                "inventory_observed": False,
                "error": {"type": "endpoint_inventory_missing", "message": "topic endpoint inventory not observed in current probe"},
            }
        )

    def reference(result: dict[str, Any]) -> int:
        return int(result.get("finished_at_ms") or result.get("generated_at_ms") or generated_at_ms)

    tf_reference_ms = int(tf_source_probe_result.get("finished_at_ms") or generated_at_ms)
    tf_probe = {
        "executed": bool(tf_source_probe_result.get("executed")),
        "ok": bool(dynamic_edges),
        "returncode": command_statuses.get("tf"),
        "elapsed_ms": tf_source_probe_result.get("elapsed_ms"),
        "timeout_s": None,
        "timed_out": command_statuses.get("tf") == 124,
        "boundary": tf_source_probe_result.get("boundary"),
    }
    tf_static_probe = {
        **tf_probe,
        "ok": bool(static_edges),
        "returncode": command_statuses.get("tf_static"),
        "timed_out": command_statuses.get("tf_static") == 124,
    }
    tf_stamp = (
        dynamic_transforms[0].get("stamp")
        if dynamic_transforms and isinstance(dynamic_transforms[0], dict) and isinstance(dynamic_transforms[0].get("stamp"), dict)
        else {"parsed": False, "reason": "tf_transform_stamp_not_observed", "source": "/tf.header.stamp"}
    )
    tf_static_stamp = (
        static_transforms[0].get("stamp")
        if static_transforms and isinstance(static_transforms[0], dict) and isinstance(static_transforms[0].get("stamp"), dict)
        else {"parsed": False, "reason": "tf_static_transform_stamp_not_observed", "source": "/tf_static.header.stamp"}
    )
    return {
        "/scan": build_signal_entry(
            topic="/scan",
            topic_type=topic_types.get("/scan"),
            endpoint_summary=endpoint("/scan"),
            probe_result=scan_once,
            observed=topic_once_observed(scan_once),
            stamp=parse_first_ros_stamp(str(scan_once.get("stdout") or ""), source="/scan.header.stamp"),
            source_class="message",
            reference_ms=reference(scan_once),
            managed_runtime_started=managed_runtime_started,
        ),
        "/map": build_signal_entry(
            topic="/map",
            topic_type=topic_types.get("/map"),
            endpoint_summary=endpoint("/map"),
            probe_result=map_once or {"executed": False, "ok": False, "boundary": "map_probe_not_run"},
            observed=topic_once_observed(map_once or {}),
            stamp=parse_first_ros_stamp(str((map_once or {}).get("stdout") or ""), source="/map.header.stamp"),
            source_class="message",
            reference_ms=reference(map_once or {}),
        ),
        "/amcl_pose": build_signal_entry(
            topic="/amcl_pose",
            topic_type=topic_types.get("/amcl_pose"),
            endpoint_summary=endpoint("/amcl_pose"),
            probe_result=amcl_probe,
            observed=bool(direct_amcl_pose_sample.get("observed") or topic_once_observed(amcl_probe)),
            stamp=(
                dict(direct_amcl_pose_sample["stamp"])
                if isinstance(direct_amcl_pose_sample.get("stamp"), dict)
                else parse_first_ros_stamp(str(amcl_probe.get("stdout") or ""), source="/amcl_pose.header.stamp")
            ),
            source_class="message",
            reference_ms=int(direct_amcl_pose_sample.get("received_at_ms") or reference(amcl_probe)),
            extra={"direct_read_only_sample": direct_amcl_pose_sample},
        ),
        "/odom": build_signal_entry(
            topic="/odom",
            topic_type=topic_types.get("/odom"),
            endpoint_summary=endpoint("/odom"),
            probe_result=odom_once,
            observed=topic_once_observed(odom_once),
            stamp=parse_first_ros_stamp(str(odom_once.get("stdout") or ""), source="/odom.header.stamp"),
            source_class="message",
            reference_ms=reference(odom_once),
        ),
        "/tf": build_signal_entry(
            topic="/tf",
            topic_type=topic_types.get("/tf"),
            endpoint_summary=endpoint("/tf"),
            probe_result=tf_probe,
            observed=bool(dynamic_edges),
            stamp=tf_stamp,
            source_class="dynamic",
            reference_ms=tf_reference_ms,
            extra={"dynamic_edge_count": len(dynamic_edges), "sample_edges": dynamic_edges[:8]},
        ),
        "/tf_static": build_signal_entry(
            topic="/tf_static",
            topic_type=topic_types.get("/tf_static"),
            endpoint_summary=endpoint("/tf_static"),
            probe_result=tf_static_probe,
            observed=bool(static_edges),
            stamp=tf_static_stamp,
            source_class="static",
            reference_ms=tf_reference_ms,
            extra={"static_edge_count": len(static_edges), "sample_edges": static_edges[:8]},
        ),
    }


def tf_edge_freshness_entry(
    *,
    name: str,
    parent: str,
    child: str,
    required_source_class: str | None,
    dynamic_edges: list[dict[str, Any]],
    static_edges: list[dict[str, Any]],
    dynamic_transforms: list[dict[str, Any]],
    static_transforms: list[dict[str, Any]],
    generated_at_ms: int,
    publisher_attribution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """按 edge 明确 dynamic/static source，避免把 static 兜底误当 AMCL 定位闭环。"""
    dynamic_observed = edge_observed(dynamic_edges, parent, child)
    static_observed = edge_observed(static_edges, parent, child)
    source_class = "dynamic" if dynamic_observed else "static" if static_observed else "missing"
    source_topic = "/tf" if dynamic_observed else "/tf_static" if static_observed else None
    transform = None
    if dynamic_observed:
        transform = find_tf_topic_transform(dynamic_transforms, parent_frame_id=parent, child_frame_id=child)
    elif static_observed:
        transform = find_tf_topic_transform(static_transforms, parent_frame_id=parent, child_frame_id=child)
    stamp = (
        transform.get("stamp")
        if isinstance(transform, dict) and isinstance(transform.get("stamp"), dict)
        else {"parsed": False, "reason": "transform_stamp_not_observed", "source": f"{name}.header.stamp"}
    )
    accepted_source = source_class != "missing" and (required_source_class is None or source_class == required_source_class)
    entry = {
        "edge": name,
        "parent_frame_id": parent,
        "child_frame_id": child,
        "observed": bool(accepted_source),
        "source_class": source_class,
        "source_topic": source_topic,
        "required_source_class": required_source_class,
        "dynamic_source_observed": dynamic_observed,
        "static_source_observed": static_observed,
        "timestamp": stamp,
        "freshness": freshness_from_stamp(
            stamp,
            observed=bool(source_class != "missing"),
            source_class=source_class,
            reference_ms=generated_at_ms,
        ),
    }
    # publisher attribution 只属于 dynamic map->odom；其他 edge 不复制 AMCL 身份，避免误读。
    if isinstance(publisher_attribution, dict):
        entry.update(
            {
                "publisher_attribution_status": publisher_attribution.get("publisher_attribution_status"),
                "publisher_attribution_reason": publisher_attribution.get("publisher_attribution_reason"),
                "publisher_endpoint": publisher_attribution.get("publisher_endpoint"),
                "publisher_endpoint_candidates": publisher_attribution.get("publisher_endpoint_candidates", []),
                "publisher_endpoint_inventory_observed": bool(
                    publisher_attribution.get("publisher_endpoint_inventory_observed")
                ),
                "amcl_node_tf_publisher_observed": bool(
                    publisher_attribution.get("amcl_node_tf_publisher_observed")
                ),
            }
        )
    return entry


def build_tf_source_freshness(
    *,
    args: argparse.Namespace,
    generated_at_ms: int,
    tf_source_diagnostics: dict[str, Any],
) -> dict[str, Any]:
    """把 TF source inventory 转成 edge 级 freshness 摘要，显式区分 dynamic/static。"""
    inventory = tf_source_diagnostics.get("tf_frame_inventory") if isinstance(tf_source_diagnostics.get("tf_frame_inventory"), dict) else {}
    dynamic_edges = inventory.get("dynamic_edges") if isinstance(inventory.get("dynamic_edges"), list) else []
    static_edges = inventory.get("static_edges") if isinstance(inventory.get("static_edges"), list) else []
    dynamic_transforms = inventory.get("dynamic_transforms") if isinstance(inventory.get("dynamic_transforms"), list) else []
    static_transforms = inventory.get("static_transforms") if isinstance(inventory.get("static_transforms"), list) else []
    publisher_attribution = (
        tf_source_diagnostics.get("map_to_odom_publisher_attribution")
        if isinstance(tf_source_diagnostics.get("map_to_odom_publisher_attribution"), dict)
        else {}
    )
    frames = tf_chain_frame_contract(args)["actual"]
    edges = {
        "map_to_odom": tf_edge_freshness_entry(
            name="map_to_odom",
            parent="map",
            child=frames["odom"],
            required_source_class="dynamic",
            dynamic_edges=dynamic_edges,
            static_edges=static_edges,
            dynamic_transforms=dynamic_transforms,
            static_transforms=static_transforms,
            generated_at_ms=generated_at_ms,
            publisher_attribution=publisher_attribution,
        ),
        "odom_to_base_link": tf_edge_freshness_entry(
            name="odom_to_base_link",
            parent=frames["odom"],
            child=frames["base"],
            required_source_class=None,
            dynamic_edges=dynamic_edges,
            static_edges=static_edges,
            dynamic_transforms=dynamic_transforms,
            static_transforms=static_transforms,
            generated_at_ms=generated_at_ms,
        ),
        "base_link_to_laser_frame": tf_edge_freshness_entry(
            name="base_link_to_laser_frame",
            parent=frames["base"],
            child=frames["laser"],
            required_source_class="static",
            dynamic_edges=dynamic_edges,
            static_edges=static_edges,
            dynamic_transforms=dynamic_transforms,
            static_transforms=static_transforms,
            generated_at_ms=generated_at_ms,
        ),
    }
    return {
        "edges": edges,
        "dynamic_edge_count": len(dynamic_edges),
        "static_edge_count": len(static_edges),
        "dynamic_edges": dynamic_edges[:12],
        "static_edges": static_edges[:12],
    }


def signal_root_cause_reason(summary: dict[str, Any], topic: str, fallback: str) -> str:
    """用 signal freshness 事实优先生成 blocker，事实不足才回落到旧 reason。"""
    if not summary:
        return fallback
    probe = summary.get("probe") if isinstance(summary.get("probe"), dict) else {}
    attempts = probe.get("attempts") if isinstance(probe.get("attempts"), list) else []
    best_attempt = probe.get("best_attempt") if isinstance(probe.get("best_attempt"), dict) else {}
    publishers = summary.get("publishers") if isinstance(summary.get("publishers"), dict) else {}
    freshness = summary.get("freshness") if isinstance(summary.get("freshness"), dict) else {}
    endpoint_inventory_observed = bool(summary.get("endpoint_inventory_observed"))
    normalized = topic.strip("/").replace("/", "_")
    classification = str(probe.get("classification") or "")
    if topic == "/scan" and classification.startswith("/scan_") and classification != "/scan_sample_observed":
        return classification
    if not summary.get("topic_present"):
        return f"/{normalized}_topic_missing"
    if endpoint_inventory_observed and int(publishers.get("count") or 0) <= 0:
        return f"/{normalized}_no_publisher"
    import_check = best_attempt.get("import_check") if isinstance(best_attempt.get("import_check"), dict) else {}
    if str(best_attempt.get("source") or "") == "rclpy_subscription" and import_check:
        classification = str(import_check.get("classification") or "")
        if classification == "missing_shared_library":
            return f"/{normalized}_rclpy_import_failed_missing_shared_library"
        if classification == "python_abi_mismatch":
            return f"/{normalized}_rclpy_import_failed_python_abi_mismatch"
        if classification in {"environment_not_sourced", "pythonpath_missing"}:
            return f"/{normalized}_ros_environment_not_sourced"
        if import_check.get("ok") is True:
            runtime_diagnostics = (
                best_attempt.get("runtime_diagnostics")
                if isinstance(best_attempt.get("runtime_diagnostics"), dict)
                else {}
            )
            child_process = (
                runtime_diagnostics.get("child_process")
                if isinstance(runtime_diagnostics.get("child_process"), dict)
                else {}
            )
            error = best_attempt.get("error") if isinstance(best_attempt.get("error"), dict) else {}
            if child_process.get("timed_out"):
                return f"/{normalized}_rclpy_child_timeout_after_import"
            if error.get("type") == "ExternalShutdownException":
                return f"/{normalized}_rclpy_external_shutdown_after_import"
    if str(best_attempt.get("source") or "") == "rclpy_subscription" and best_attempt.get("error"):
        return f"/{normalized}_rclpy_probe_failed"
    if probe.get("timed_out"):
        if str(best_attempt.get("qos_profile") or "") == "sensor_data":
            return f"/{normalized}_sensor_data_qos_timeout"
        if attempts and all(bool(attempt.get("timed_out")) for attempt in attempts if isinstance(attempt, dict)):
            return f"/{normalized}_all_probe_attempts_timed_out"
        return f"/{normalized}_probe_timeout"
    if freshness.get("status") == "stale":
        return f"/{normalized}_stamp_stale"
    if freshness.get("status") == "unknown" and not probe.get("observed"):
        return f"/{normalized}_freshness_unknown"
    return fallback


def tf_edge_root_cause_reason(tf_source_freshness: dict[str, Any], edge_name: str, fallback: str) -> str:
    """TF blocker 优先说明 source 类型和 edge 缺口，而不是只写泛化 not_observed。"""
    edges = tf_source_freshness.get("edges") if isinstance(tf_source_freshness.get("edges"), dict) else {}
    edge = edges.get(edge_name) if isinstance(edges.get(edge_name), dict) else {}
    if not edge:
        return fallback
    if edge.get("observed"):
        freshness = edge.get("freshness") if isinstance(edge.get("freshness"), dict) else {}
        if freshness.get("status") == "stale":
            return f"{edge_name}_{edge.get('source_class')}_source_stale"
        return fallback
    source_class = str(edge.get("source_class") or "missing")
    required_source = str(edge.get("required_source_class") or "")
    if source_class == "missing" and required_source:
        return f"{edge_name}_{required_source}_source_missing"
    if source_class == "static" and edge.get("required_source_class") == "dynamic":
        return f"{edge_name}_static_source_observed_but_dynamic_required"
    return f"{edge_name}_{source_class}_source_missing"


def select_primary_root_cause(root_causes: list[dict[str, Any]]) -> dict[str, Any] | None:
    """SIGTERM/timeout 只是收口事件；主因优先选择已观测到的 AMCL/TF/path blocker。"""
    for cause in root_causes:
        if not isinstance(cause, dict):
            continue
        if str(cause.get("layer") or "") != "helper process":
            return dict(cause)
    for cause in root_causes:
        if isinstance(cause, dict):
            return dict(cause)
    return None


def build_artifact_closeout_summary(
    *,
    status: str,
    root_causes: list[dict[str, Any]],
    last_phase: str | None,
    current_command: dict[str, Any] | None,
) -> dict[str, Any]:
    """final/partial 都输出同形 closeout，避免外层 timeout 把 root cause 读成只有 signal。"""
    signal_causes = [
        dict(cause)
        for cause in root_causes
        if isinstance(cause, dict) and str(cause.get("layer") or "") == "helper process"
    ]
    primary = select_primary_root_cause(root_causes)
    return {
        "status": status,
        "artifact_kind": "partial" if status in {"partial_runtime_in_progress", "interrupted_before_final_artifact"} else "final",
        "last_phase": last_phase,
        "primary_root_cause": primary,
        "signal_root_causes": signal_causes,
        "root_cause_count": len([cause for cause in root_causes if isinstance(cause, dict)]),
        "current_command": current_command,
        "interruption_does_not_override_primary_root_cause": bool(primary and signal_causes),
    }


def amcl_pose_sample_timing(entry: dict[str, Any]) -> dict[str, Any]:
    """AMCL pose 没有 child sample_timing 时，用 probe/timestamp 生成稳定采样摘要。"""
    probe = entry.get("probe") if isinstance(entry.get("probe"), dict) else {}
    timestamp = entry.get("timestamp") if isinstance(entry.get("timestamp"), dict) else {}
    freshness = entry.get("freshness") if isinstance(entry.get("freshness"), dict) else {}
    return {
        "sample_observed": bool(probe.get("observed")),
        "probe_executed": bool(probe.get("executed")),
        "elapsed_ms": probe.get("elapsed_ms"),
        "timeout_s": probe.get("timeout_s"),
        "timed_out": bool(probe.get("timed_out")),
        "stamp": timestamp,
        "freshness": freshness,
    }


def signal_sample_timing(entry: dict[str, Any]) -> dict[str, Any]:
    """普通 topic 没有 child timing 时，用 probe 字段生成统一 sample timeout 摘要。"""
    probe = entry.get("probe") if isinstance(entry.get("probe"), dict) else {}
    if isinstance(entry.get("sample_timing"), dict):
        return dict(entry["sample_timing"])
    return {
        "sample_observed": bool(probe.get("observed")),
        "probe_executed": bool(probe.get("executed")),
        "elapsed_ms": probe.get("elapsed_ms"),
        "timeout_s": probe.get("timeout_s"),
        "timed_out": bool(probe.get("timed_out")),
        "sample_count": 1 if probe.get("observed") else 0,
    }


def topic_readiness_summary(
    entry: dict[str, Any],
    *,
    topic: str,
    fallback_reason: str,
    lifecycle_blocker: str | None = None,
) -> dict[str, Any]:
    """把 topic 缺失、publisher=0 和 sample timeout 拆成机器可读字段。"""
    probe = entry.get("probe") if isinstance(entry.get("probe"), dict) else {}
    publishers = entry.get("publishers") if isinstance(entry.get("publishers"), dict) else {"count": 0, "nodes": []}
    subscribers = entry.get("subscribers") if isinstance(entry.get("subscribers"), dict) else {"count": 0, "nodes": []}
    endpoint_inventory = (
        entry.get("endpoint_inventory")
        if isinstance(entry.get("endpoint_inventory"), dict)
        else {}
    )
    sample_timing = signal_sample_timing(entry)
    observed = bool(probe.get("observed") or sample_timing.get("sample_count"))
    publisher_count = int(publishers.get("count") or 0)
    endpoint_observed = bool(endpoint_inventory.get("inventory_observed") or entry.get("endpoint_inventory_observed"))
    topic_present = bool(entry.get("topic_present") or (endpoint_observed and publisher_count > 0))
    normalized = topic.strip("/").replace("/", "_")
    probe_classification = str(probe.get("classification") or "")
    if observed:
        classification = f"/{normalized}_sample_observed"
    elif lifecycle_blocker:
        classification = lifecycle_blocker
    elif not topic_present:
        classification = f"/{normalized}_topic_missing"
    elif endpoint_observed and publisher_count <= 0:
        classification = f"/{normalized}_no_publisher"
    elif probe_classification:
        classification = probe_classification
    elif sample_timing.get("timed_out") or probe.get("timed_out"):
        classification = f"/{normalized}_sample_timeout"
    elif probe.get("executed"):
        classification = f"/{normalized}_sample_not_observed"
    else:
        classification = fallback_reason
    return {
        "topic": topic,
        "expected_type": entry.get("expected_type"),
        "topic_type": entry.get("topic_type"),
        "topic_present": topic_present,
        "endpoint_inventory_observed": endpoint_observed,
        "publisher_count": publisher_count,
        "subscriber_count": int(subscribers.get("count") or 0),
        "publishers": publishers.get("nodes") if isinstance(publishers.get("nodes"), list) else [],
        "subscribers": subscribers.get("nodes") if isinstance(subscribers.get("nodes"), list) else [],
        "probe_executed": bool(probe.get("executed")),
        "sample_observed": observed,
        "sample_timeout": bool(sample_timing.get("timed_out") or probe.get("timed_out")),
        "sample_timing": sample_timing,
        "classification": classification,
        "blocked_reason": None if observed else classification,
        "legacy_root_cause": None if observed else fallback_reason,
    }


def map_lifecycle_readiness_summary(proof: dict[str, Any]) -> dict[str, Any]:
    """保留 lifecycle classification，同时把每个节点 timeout/inactive stdout 拆出来。"""
    preflight = proof.get("map_lifecycle_preflight") if isinstance(proof.get("map_lifecycle_preflight"), dict) else {}
    node_summaries = preflight.get("node_summaries") if isinstance(preflight.get("node_summaries"), dict) else {}
    if not node_summaries:
        results = preflight.get("results") if isinstance(preflight.get("results"), dict) else {}
        node_summaries = {
            name: lifecycle_node_summary(
                name,
                bool(proof.get(f"{name}_active") or preflight.get(f"{name}_active")),
                results.get(name) if isinstance(results.get(name), dict) else {},
            )
            for name in ("map_server", "amcl")
        }
    return {
        "classification": preflight.get("classification"),
        "map_server": node_summaries.get("map_server", {}),
        "amcl": node_summaries.get("amcl", {}),
        "all_active": bool(preflight.get("map_server_active") and preflight.get("amcl_active")),
        "blocking_reasons": preflight.get("blocking_reasons") if isinstance(preflight.get("blocking_reasons"), dict) else {},
        "lifecycle_cli_budget_recovery": (
            preflight.get("lifecycle_cli_budget_recovery")
            if isinstance(preflight.get("lifecycle_cli_budget_recovery"), dict)
            else {}
        ),
        "command_summaries": (
            preflight.get("command_summaries")
            if isinstance(preflight.get("command_summaries"), dict)
            else {}
        ),
    }


def build_scan_readiness_summary(proof: dict[str, Any]) -> dict[str, Any]:
    """`/scan` 单独收口，第一眼区分 no publisher、QoS/window timeout 和样本已观测。"""
    signals = proof.get("localization_signal_freshness") if isinstance(proof.get("localization_signal_freshness"), dict) else {}
    entry = signals.get("/scan") if isinstance(signals.get("/scan"), dict) else {}
    summary = topic_readiness_summary(entry, topic="/scan", fallback_reason="/scan_once_not_observed")
    managed_status = entry.get("managed_runtime_scan_status") if isinstance(entry.get("managed_runtime_scan_status"), dict) else {}
    if managed_status:
        summary["managed_runtime_scan_status"] = managed_status
        if not summary["sample_observed"] and managed_status.get("blocked_reason"):
            summary["classification"] = str(managed_status["blocked_reason"])
            summary["blocked_reason"] = str(managed_status["blocked_reason"])
    return summary


def qos_reliability_value(qos_profile: dict[str, Any] | None) -> str | None:
    """QoS reliability 只比较稳定字符串，避免 ROS 枚举或 UNKNOWN 细节污染判定。"""
    if not isinstance(qos_profile, dict):
        return None
    value = str(qos_profile.get("reliability") or "").strip().upper()
    return value or None


def qos_reliability_compatible(*, offered: str | None, requested: str | None) -> bool | None:
    """按 ROS2 reliability 兼容规则判断；UNKNOWN 返回 None，表示不能据此排除 QoS 风险。"""
    offered_value = str(offered or "").upper()
    requested_value = str(requested or "").upper()
    if not offered_value or not requested_value or "UNKNOWN" in {offered_value, requested_value}:
        return None
    if requested_value == "BEST_EFFORT":
        return offered_value in {"BEST_EFFORT", "RELIABLE"}
    if requested_value == "RELIABLE":
        return offered_value == "RELIABLE"
    return None


def scan_attempt_readback_summary(attempt: dict[str, Any] | None) -> dict[str, Any]:
    """保留单次 `/scan` readback 的最小事实，供 sprint artifact 直接验收。"""
    if not isinstance(attempt, dict):
        return {
            "present": False,
            "executed": False,
            "observed": False,
            "timed_out": False,
            "sample_count": 0,
        }
    timing = attempt.get("sample_timing") if isinstance(attempt.get("sample_timing"), dict) else {}
    requested_qos = attempt.get("requested_qos_profile") if isinstance(attempt.get("requested_qos_profile"), dict) else {}
    child_runtime = attempt.get("child_runtime") if isinstance(attempt.get("child_runtime"), dict) else {}
    import_check = attempt.get("import_check") if isinstance(attempt.get("import_check"), dict) else {}
    return {
        "present": True,
        "label": attempt.get("label"),
        "source": attempt.get("source"),
        "command": attempt.get("command"),
        "qos_profile": attempt.get("qos_profile"),
        "requested_reliability": qos_reliability_value(requested_qos),
        "executed": bool(attempt.get("executed")),
        "observed": bool(attempt.get("observed") or int(timing.get("sample_count") or 0) > 0),
        "timed_out": bool(attempt.get("timed_out") or timing.get("timed_out") or attempt.get("returncode") == 124),
        "returncode": attempt.get("returncode"),
        "elapsed_ms": attempt.get("elapsed_ms"),
        "timeout_s": attempt.get("timeout_s"),
        "boundary": attempt.get("boundary"),
        "sample_count": int(timing.get("sample_count") or 0),
        "probe_window_sec": timing.get("probe_window_sec"),
        "subscription_created": bool(child_runtime.get("subscription_created")),
        "import_ok": import_check.get("ok") if "ok" in import_check else None,
        "error": attempt.get("error") if isinstance(attempt.get("error"), dict) else None,
    }


def scan_publisher_stability_from_attempts(attempts: list[dict[str, Any]]) -> dict[str, Any]:
    """endpoint 多次观测一致时，才能把 publisher 层从主嫌疑里排除。"""
    signatures: list[list[tuple[str, str, str, str | None]]] = []
    for attempt in attempts:
        if not isinstance(attempt, dict):
            continue
        inventory = attempt.get("endpoint_inventory") if isinstance(attempt.get("endpoint_inventory"), dict) else {}
        if not inventory.get("inventory_observed"):
            continue
        publishers = inventory.get("publishers") if isinstance(inventory.get("publishers"), list) else []
        signature = sorted(
            (
                str(publisher.get("node_namespace") or ""),
                str(publisher.get("node_name") or ""),
                str(publisher.get("topic_type") or ""),
                qos_reliability_value(publisher.get("qos_profile") if isinstance(publisher.get("qos_profile"), dict) else None),
            )
            for publisher in publishers
            if isinstance(publisher, dict)
        )
        signatures.append(signature)
    unique_signatures = {tuple(signature) for signature in signatures}
    return {
        "observed_attempt_count": len(signatures),
        "stable": bool(signatures and len(unique_signatures) == 1),
        "single_observation_only": len(signatures) == 1,
        "signature_count": len(unique_signatures),
    }


def build_scan_qos_endpoint_readback_split(proof: dict[str, Any]) -> dict[str, Any]:
    """把 `/scan_reliable_and_best_effort_timeout` 拆成 endpoint、QoS/readback、runtime 三层。"""
    signals = proof.get("localization_signal_freshness") if isinstance(proof.get("localization_signal_freshness"), dict) else {}
    entry = signals.get("/scan") if isinstance(signals.get("/scan"), dict) else {}
    probe = entry.get("probe") if isinstance(entry.get("probe"), dict) else {}
    endpoint_inventory = entry.get("endpoint_inventory") if isinstance(entry.get("endpoint_inventory"), dict) else {}
    attempts = probe.get("attempts") if isinstance(probe.get("attempts"), list) else []
    best_effort_attempt = probe.get("best_effort_attempt") if isinstance(probe.get("best_effort_attempt"), dict) else None
    reliable_attempt = probe.get("reliable_attempt") if isinstance(probe.get("reliable_attempt"), dict) else None
    best_effort = scan_attempt_readback_summary(best_effort_attempt)
    reliable = scan_attempt_readback_summary(reliable_attempt)
    cli_attempts = [
        scan_attempt_readback_summary(attempt)
        for attempt in attempts
        if isinstance(attempt, dict) and str(attempt.get("source") or "") == "ros2_topic_echo_cli"
    ][:4]
    publishers = endpoint_inventory.get("publishers") if isinstance(endpoint_inventory.get("publishers"), list) else []
    subscribers = endpoint_inventory.get("subscribers") if isinstance(endpoint_inventory.get("subscribers"), list) else []
    publisher_reliabilities = [
        qos_reliability_value(publisher.get("qos_profile") if isinstance(publisher.get("qos_profile"), dict) else None)
        for publisher in publishers
        if isinstance(publisher, dict)
    ]
    requested_reliabilities = {
        "best_effort": best_effort.get("requested_reliability"),
        "reliable": reliable.get("requested_reliability"),
    }
    best_effort_compatible = any(
        qos_reliability_compatible(offered=offered, requested=str(requested_reliabilities["best_effort"] or "BEST_EFFORT")) is True
        for offered in publisher_reliabilities
    )
    reliable_compatible = any(
        qos_reliability_compatible(offered=offered, requested=str(requested_reliabilities["reliable"] or "RELIABLE")) is True
        for offered in publisher_reliabilities
    )
    compatibility_unknown = any(
        qos_reliability_compatible(offered=offered, requested=str(requested_reliabilities["best_effort"] or "BEST_EFFORT")) is None
        or qos_reliability_compatible(offered=offered, requested=str(requested_reliabilities["reliable"] or "RELIABLE")) is None
        for offered in publisher_reliabilities
    )
    sample_timing = entry.get("sample_timing") if isinstance(entry.get("sample_timing"), dict) else signal_sample_timing(entry)
    sample_observed = bool((probe.get("observed") if isinstance(probe, dict) else False) or int(sample_timing.get("sample_count") or 0) > 0)
    topic_present = bool(entry.get("topic_present") or endpoint_inventory.get("topic_visible"))
    publisher_count = int(endpoint_inventory.get("publisher_count") or 0)
    endpoint_observed = bool(endpoint_inventory.get("inventory_observed") or entry.get("endpoint_inventory_observed"))
    publisher_stability = scan_publisher_stability_from_attempts(attempts)
    log_readback = proof.get("managed_runtime_log_lifecycle_readback") if isinstance(proof.get("managed_runtime_log_lifecycle_readback"), dict) else {}
    runtime_log = f"{proof.get('amcl_log_tail') or ''}\n{log_readback.get('log_tail') or ''}"
    runtime_exception_observed = "serial.serialutil.serialexception" in runtime_log.lower()
    runtime_exception_summary = {
        "observed": runtime_exception_observed,
        "type": "serial.serialutil.SerialException" if runtime_exception_observed else None,
        "source": "managed_runtime_log_lifecycle_readback.log_tail" if runtime_exception_observed else None,
        "message_hint": "device reports readiness to read but returned no data"
        if runtime_exception_observed and "returned no data" in runtime_log.lower()
        else None,
    }
    if sample_observed:
        endpoint_classification = "publisher_endpoint_sample_observed"
    elif not topic_present:
        endpoint_classification = "scan_topic_missing"
    elif endpoint_observed and publisher_count <= 0:
        endpoint_classification = "publisher_endpoint_absent"
    elif endpoint_observed and publisher_count > 0:
        endpoint_classification = "publisher_endpoint_visible"
    else:
        endpoint_classification = "publisher_endpoint_inventory_missing"
    both_qos_attempts_timed_out = bool(best_effort.get("timed_out") and reliable.get("timed_out"))
    both_qos_compatible = bool(best_effort_compatible and reliable_compatible)
    compatibility_risk = bool(not both_qos_compatible or compatibility_unknown)
    if sample_observed:
        readback_classification = "sample_observed"
    elif not endpoint_observed:
        readback_classification = "endpoint_inventory_missing_readback_not_decisive"
    elif publisher_count <= 0:
        readback_classification = "no_publisher_readback_not_qos"
    elif both_qos_attempts_timed_out and both_qos_compatible:
        readback_classification = "qos_compatible_readback_timeout_no_samples"
    elif compatibility_risk:
        readback_classification = "requested_qos_endpoint_compatibility_risk"
    elif any(attempt.get("timed_out") for attempt in cli_attempts):
        readback_classification = "cli_or_window_readback_timeout"
    else:
        readback_classification = "publisher_visible_but_sample_not_observed"
    runtime_reached = bool(
        not sample_observed
        and endpoint_classification == "publisher_endpoint_visible"
        and both_qos_attempts_timed_out
        and both_qos_compatible
    )
    if runtime_reached and runtime_exception_observed:
        runtime_classification = "lidar_runtime_exception_candidate_after_endpoint_qos_readback_split"
        primary_reason = "/scan_lidar_runtime_exception_after_endpoint_visible_qos_compatible_timeout"
        next_owner = "hardware_after_vendor_doc_review"
    elif runtime_reached:
        runtime_classification = "lidar_runtime_candidate_after_endpoint_qos_readback_split"
        primary_reason = "/scan_endpoint_visible_qos_compatible_reliable_and_best_effort_readback_timeout"
        next_owner = "robot_software_then_hardware_if_repeatable"
    elif endpoint_classification == "publisher_endpoint_absent":
        runtime_classification = "lidar_runtime_not_reached_no_publisher_endpoint"
        primary_reason = "/scan_publisher_endpoint_absent"
        next_owner = "robot_software_runtime_bringup"
    elif compatibility_risk and endpoint_classification == "publisher_endpoint_visible":
        runtime_classification = "lidar_runtime_not_reached_qos_compatibility_open"
        primary_reason = "/scan_endpoint_visible_requested_qos_compatibility_risk"
        next_owner = "robot_software_qos_readback"
    else:
        runtime_classification = "lidar_runtime_not_reached_readback_not_decisive"
        primary_reason = str(probe.get("classification") or "/scan_readback_not_decisive")
        next_owner = "robot_software_readback"
    return {
        "schema": "trashbot.o10.scan_qos_endpoint_readback_split.v1",
        "canonical_blocker": "/scan_reliable_and_best_effort_timeout",
        "sample_observed": sample_observed,
        "publisher_endpoint_classification": {
            "classification": endpoint_classification,
            "topic": "/scan",
            "topic_present": topic_present,
            "topic_type": entry.get("topic_type"),
            "expected_type": entry.get("expected_type"),
            "endpoint_inventory_observed": endpoint_observed,
            "publisher_count": publisher_count,
            "subscriber_count": int(endpoint_inventory.get("subscriber_count") or 0),
            "publisher_nodes": publishers,
            "subscriber_nodes": subscribers,
            "publisher_reliability_values": publisher_reliabilities,
            "publisher_stability": publisher_stability,
        },
        "qos_window_ros_readback_classification": {
            "classification": readback_classification,
            "best_effort_attempt": best_effort,
            "reliable_attempt": reliable,
            "cli_attempts": cli_attempts,
            "both_qos_attempts_timed_out": both_qos_attempts_timed_out,
            "requested_vs_endpoint_qos": {
                "publisher_reliability_values": publisher_reliabilities,
                "requested_reliabilities": requested_reliabilities,
                "best_effort_compatible": best_effort_compatible,
                "reliable_compatible": reliable_compatible,
                "compatibility_unknown": compatibility_unknown,
                "compatibility_risk": compatibility_risk,
            },
            "sample_timing": sample_timing,
            "ros_readback_false_timeout_still_possible": bool(
                not sample_observed
                and endpoint_classification == "publisher_endpoint_visible"
                and readback_classification != "sample_observed"
            ),
        },
        "lidar_runtime_classification": {
            "reached": runtime_reached,
            "classification": runtime_classification,
            "runtime_exception": runtime_exception_summary,
            "hardware_handoff_allowed": bool(runtime_reached),
            "hardware_handoff_requires_vendor_docs": True,
            "does_not_claim_vendor_hardware_root_cause": True,
            "handoff_conditions": {
                "endpoint_visible": endpoint_classification == "publisher_endpoint_visible",
                "qos_compatible": both_qos_compatible,
                "reliable_and_best_effort_timed_out": both_qos_attempts_timed_out,
                "sample_count": int(sample_timing.get("sample_count") or 0),
                "runtime_exception_observed": runtime_exception_observed,
            },
        },
        "primary_split": {
            "reason": primary_reason,
            "canonical_blocker": "/scan_reliable_and_best_effort_timeout",
            "classification": runtime_classification if runtime_reached else readback_classification,
            "next_owner": next_owner,
        },
        "strict_no_motion_invariants": safety_flags(),
    }


def enrich_scan_root_causes_with_split(
    root_causes: list[dict[str, Any]],
    scan_split: dict[str, Any],
) -> list[dict[str, Any]]:
    """closeout 主因要读最细 scan split；旧短语保留为 canonical blocker 方便检索。"""
    primary_split = scan_split.get("primary_split") if isinstance(scan_split.get("primary_split"), dict) else {}
    split_reason = str(primary_split.get("reason") or "")
    if not split_reason.startswith("/scan_"):
        return root_causes
    enriched: list[dict[str, Any]] = []
    for cause in root_causes:
        if not isinstance(cause, dict):
            continue
        reason = str(cause.get("reason") or "")
        if reason.startswith("/scan"):
            updated = dict(cause)
            updated.setdefault("previous_reason", reason)
            updated["reason"] = split_reason
            updated["canonical_blocker"] = str(primary_split.get("canonical_blocker") or "/scan_reliable_and_best_effort_timeout")
            updated["split_classification"] = str(primary_split.get("classification") or "")
            updated["next_owner"] = str(primary_split.get("next_owner") or "")
            updated["detail"] = "scan_qos_endpoint_readback_split_primary"
            enriched.append(updated)
        else:
            enriched.append(dict(cause))
    return enriched


def build_map_readiness_summary(proof: dict[str, Any]) -> dict[str, Any]:
    """`/map` 单独收口，避免把 map_server inactive 与 map sample timeout 混在一起。"""
    signals = proof.get("localization_signal_freshness") if isinstance(proof.get("localization_signal_freshness"), dict) else {}
    entry = signals.get("/map") if isinstance(signals.get("/map"), dict) else {}
    lifecycle = map_lifecycle_readiness_summary(proof)
    map_server = lifecycle.get("map_server") if isinstance(lifecycle.get("map_server"), dict) else {}
    lifecycle_blocker = None if map_server.get("active") else str(map_server.get("blocked_reason") or "map_server_lifecycle_not_active")
    topic_summary = topic_readiness_summary(
        entry,
        topic="/map",
        fallback_reason="/map_once_not_observed",
    )
    observed = bool(proof.get("map_once_observed") or topic_summary["sample_observed"])
    if observed:
        topic_summary["sample_observed"] = True
        topic_summary["blocked_reason"] = None
    return {
        "ready": bool(map_server.get("active") and observed),
        "map_server_lifecycle": map_server,
        "topic_sample": topic_summary,
        "blocked_reason": None if map_server.get("active") and observed else (lifecycle_blocker or topic_summary["blocked_reason"]),
        "legacy_root_cause": None if observed else "/map_once_not_observed",
    }


def build_amcl_readiness_summary(proof: dict[str, Any]) -> dict[str, Any]:
    """拆开 AMCL lifecycle 与 `/amcl_pose` sample，避免 active 被误读成定位已完成。"""
    signals = proof.get("localization_signal_freshness") if isinstance(proof.get("localization_signal_freshness"), dict) else {}
    amcl_pose = signals.get("/amcl_pose") if isinstance(signals.get("/amcl_pose"), dict) else {}
    publishers = amcl_pose.get("publishers") if isinstance(amcl_pose.get("publishers"), dict) else {"count": 0, "nodes": []}
    subscribers = amcl_pose.get("subscribers") if isinstance(amcl_pose.get("subscribers"), dict) else {"count": 0, "nodes": []}
    map_lifecycle_preflight = (
        proof.get("map_lifecycle_preflight")
        if isinstance(proof.get("map_lifecycle_preflight"), dict)
        else {}
    )
    lifecycle_results = (
        map_lifecycle_preflight.get("results")
        if isinstance(map_lifecycle_preflight.get("results"), dict)
        else {}
    )
    active = bool(proof.get("amcl_active") or map_lifecycle_preflight.get("amcl_active"))
    observed = bool(proof.get("amcl_pose_observed") or (amcl_pose.get("probe") or {}).get("observed"))
    blocked_reason = None
    if not active:
        blocked_reason = "amcl_lifecycle_not_active"
    elif proof.get("initialpose_publish_attempted") and not proof.get("initialpose_published"):
        blocked_reason = str(proof.get("initialpose_boundary") or "initialpose_not_published")
    elif not observed:
        blocked_reason = signal_root_cause_reason(amcl_pose, "/amcl_pose", "/amcl_pose_once_not_observed")
    return {
        "amcl_lifecycle": {
            "active": active,
            "map_server_active": bool(proof.get("map_server_active") or map_lifecycle_preflight.get("map_server_active")),
            "observed": bool((lifecycle_results.get("amcl") or {}).get("ok") or active),
            "classification": map_lifecycle_preflight.get("classification"),
            "result": lifecycle_results.get("amcl") if isinstance(lifecycle_results.get("amcl"), dict) else {},
        },
        "amcl_pose_sample": {
            "observed": observed,
            "topic_type": amcl_pose.get("topic_type"),
            "topic_present": bool(amcl_pose.get("topic_present")),
            "publishers": publishers,
            "subscribers": subscribers,
            "sample_timing": amcl_pose_sample_timing(amcl_pose),
            "blocked_reason": blocked_reason,
        },
        "ready": bool(active and observed),
        "blocked_reason": blocked_reason,
    }


def tf_summary_edge(
    *,
    edge_name: str,
    tf_source_freshness: dict[str, Any],
    tf_chain_diagnostics: dict[str, Any],
    observed: bool,
) -> dict[str, Any]:
    """把 TF edge 的 source/freshness/boundary 合在一处，便于 live artifact 直接验收。"""
    edges = tf_source_freshness.get("edges") if isinstance(tf_source_freshness.get("edges"), dict) else {}
    edge = edges.get(edge_name) if isinstance(edges.get(edge_name), dict) else {}
    pairs = tf_chain_diagnostics.get("pairs") if isinstance(tf_chain_diagnostics.get("pairs"), dict) else {}
    pair = pairs.get(edge_name) if isinstance(pairs.get(edge_name), dict) else {}
    required_source_default = "dynamic" if edge_name == "map_to_odom" else "static" if edge_name == "base_link_to_laser_frame" else None
    summary = {
        "observed": bool(observed or edge.get("observed")),
        "source_class": edge.get("source_class", "missing"),
        "required_source_class": edge.get("required_source_class", required_source_default),
        "source_topic": edge.get("source_topic"),
        "dynamic_source_observed": bool(edge.get("dynamic_source_observed")),
        "static_source_observed": bool(edge.get("static_source_observed")),
        "freshness": edge.get("freshness") if isinstance(edge.get("freshness"), dict) else {},
        "timestamp": edge.get("timestamp") if isinstance(edge.get("timestamp"), dict) else {},
        "boundary": pair.get("boundary"),
        "failure_reason": pair.get("failure_reason"),
    }
    for key in (
        "publisher_attribution_status",
        "publisher_attribution_reason",
        "publisher_endpoint",
        "publisher_endpoint_candidates",
        "publisher_endpoint_inventory_observed",
        "amcl_node_tf_publisher_observed",
    ):
        if key in edge:
            summary[key] = edge.get(key)
    return summary


def build_tf_readiness_summary(proof: dict[str, Any]) -> dict[str, Any]:
    """明确 dynamic `map->odom`、odom/base 输入和 downstream `map->base_link` 的边界。"""
    observed = proof.get("tf_chain_observed") if isinstance(proof.get("tf_chain_observed"), dict) else {}
    diagnostics = proof.get("tf_chain_diagnostics") if isinstance(proof.get("tf_chain_diagnostics"), dict) else {}
    freshness = proof.get("tf_source_freshness") if isinstance(proof.get("tf_source_freshness"), dict) else {}
    signals = proof.get("localization_signal_freshness") if isinstance(proof.get("localization_signal_freshness"), dict) else {}
    classification = (
        proof.get("tf_failure_classification")
        if isinstance(proof.get("tf_failure_classification"), dict)
        else {}
    )
    tf_signal = signals.get("/tf") if isinstance(signals.get("/tf"), dict) else {}
    tf_static_signal = signals.get("/tf_static") if isinstance(signals.get("/tf_static"), dict) else {}
    tf_topic = topic_readiness_summary(
        tf_signal,
        topic="/tf",
        fallback_reason="/tf_topic_missing",
    )
    tf_static_topic = topic_readiness_summary(
        tf_static_signal,
        topic="/tf_static",
        fallback_reason="/tf_static_topic_missing",
    )
    map_to_odom = tf_summary_edge(
        edge_name="map_to_odom",
        tf_source_freshness=freshness,
        tf_chain_diagnostics=diagnostics,
        observed=bool(observed.get("map_to_odom")),
    )
    odom_to_base = tf_summary_edge(
        edge_name="odom_to_base_link",
        tf_source_freshness=freshness,
        tf_chain_diagnostics=diagnostics,
        observed=bool(observed.get("odom_to_base_link")),
    )
    map_to_base_observed = bool(observed.get("map_to_base_link"))
    map_to_base_link = {
        "observed": map_to_base_observed,
        "source_class": "derived" if map_to_base_observed else "missing",
        "source_edges": ["map_to_odom", "odom_to_base_link"],
        "freshness": {
            "status": "derived_from_edges" if map_to_base_observed else "not_observed",
            "reason": "complete_chain_observed" if map_to_base_observed else str(classification.get("reason") or "map_to_base_link_not_observed"),
        },
        "boundary": classification.get("map_to_base_link"),
        "blocking_segment": classification.get("blocking_segment"),
        "blocked_reason": None if map_to_base_observed else str(classification.get("reason") or "map_to_base_link_not_observed"),
    }
    map_attribution_status = str(map_to_odom.get("publisher_attribution_status") or "")
    map_freshness = map_to_odom.get("freshness") if isinstance(map_to_odom.get("freshness"), dict) else {}
    map_source_accepted = bool(
        map_to_odom["observed"]
        and map_attribution_status == "attributed_to_amcl_graph_endpoint"
        and map_freshness.get("status") == "fresh"
    )
    if tf_signal and not tf_topic["topic_present"]:
        blocked_reason = "/tf_topic_missing"
    elif not map_to_odom["observed"]:
        blocked_reason = tf_edge_root_cause_reason(freshness, "map_to_odom", "map_to_odom_not_observed")
    elif map_attribution_status != "attributed_to_amcl_graph_endpoint":
        blocked_reason = map_attribution_status or "map_to_odom_publisher_attribution_missing"
    elif map_freshness.get("status") != "fresh":
        blocked_reason = f"map_to_odom_dynamic_timestamp_{map_freshness.get('status') or 'missing'}"
    elif not map_to_base_link["observed"]:
        blocked_reason = map_to_base_link["blocked_reason"]
    else:
        blocked_reason = None
    return {
        "tf_topic": tf_topic,
        "tf_static_topic": tf_static_topic,
        "map_to_odom_dynamic": map_to_odom,
        "odom_to_base_link": odom_to_base,
        "map_to_base_link": map_to_base_link,
        "ready": bool(map_source_accepted and odom_to_base["observed"] and map_to_base_link["observed"]),
        "blocked_reason": blocked_reason,
    }


def build_path_generation_gate_summary(proof: dict[str, Any]) -> dict[str, Any]:
    """path probe 的 gate 单独落字段；not attempted 必须说明停在哪个前置条件。"""
    commands = proof.get("commands") if isinstance(proof.get("commands"), dict) else {}
    path_command = commands.get("path_generation") if isinstance(commands.get("path_generation"), dict) else {}
    request = path_command.get("request") if isinstance(path_command.get("request"), dict) else {}
    result = path_command.get("result") if isinstance(path_command.get("result"), dict) else {}
    requested = bool(proof.get("path_generation_requested") or request.get("enabled"))
    attempted = bool(proof.get("path_generation_attempted") or result.get("attempted"))
    root_causes = [cause for cause in (proof.get("root_causes") or []) if isinstance(cause, dict)]
    localization_root_causes = [
        cause
        for cause in root_causes
        if str(cause.get("layer") or "") in {"Nav2 sensor input", "Nav2 map input", "AMCL initialpose", "AMCL localization", "Localization TF", "Managed static TF", "Nav2 lifecycle"}
    ]
    blocked_reason = None
    if not requested:
        blocked_reason = "path_generation_opt_in_disabled_no_compute_path_call"
    elif not attempted and localization_root_causes:
        blocked_reason = "path_generation_blocked_by_localization_not_ready"
    elif not attempted:
        blocked_reason = str(result.get("boundary") or "path_generation_not_attempted")
    elif not proof.get("path_generated"):
        blocked_reason = str(result.get("boundary") or "path_generation_attempted_failed")
    return {
        "requested": requested,
        "attempted": attempted,
        "generated": bool(proof.get("path_generated")),
        "point_count": int(proof.get("path_point_count") or 0),
        "localization_tf_gate_ready": bool((proof.get("tf_readiness_summary") or {}).get("ready")),
        "amcl_gate_ready": bool((proof.get("amcl_readiness_summary") or {}).get("ready")),
        "planner_server_ready_for_path_generation": bool(proof.get("planner_server_ready_for_path_generation")),
        "blocked_reason": blocked_reason,
        "localization_root_causes": localization_root_causes,
        "boundary": proof.get("path_generation_boundary") or result.get("boundary"),
    }


def build_downstream_recovery_summary(proof: dict[str, Any]) -> dict[str, Any]:
    """07-53 downstream recovery 汇总层：只读分辨 map/AMCL/scan/TF 当前 blocker。"""
    board = proof.get("board_source_preflight") if isinstance(proof.get("board_source_preflight"), dict) else {}
    map_lifecycle = map_lifecycle_readiness_summary(proof)
    scan = build_scan_readiness_summary(proof)
    map_topic = build_map_readiness_summary(proof)
    amcl = build_amcl_readiness_summary(proof)
    tf = build_tf_readiness_summary(proof)
    path_gate = build_path_generation_gate_summary(proof)
    blocking_conditions = {
        "map_lifecycle_preflight_map_server_and_amcl_inactive": (
            map_lifecycle.get("classification") == "map_lifecycle_preflight_map_server_and_amcl_inactive"
        ),
        "amcl_lifecycle_not_active": not bool((amcl.get("amcl_lifecycle") or {}).get("active")),
        "/scan_no_publisher": scan.get("blocked_reason") == "/scan_no_publisher",
        "/map_once_not_observed": not bool((map_topic.get("topic_sample") or {}).get("sample_observed")),
        "/tf_topic_missing": tf.get("blocked_reason") == "/tf_topic_missing",
        "map_to_odom_dynamic_source_missing": tf.get("blocked_reason") == "map_to_odom_dynamic_source_missing",
    }
    ready_for_planner_only = bool(
        map_topic.get("ready")
        and scan.get("sample_observed")
        and amcl.get("ready")
        and tf.get("ready")
    )
    return {
        "schema": "trashbot.o10.map_amcl_scan_tf_downstream_recovery.v1",
        "proof_boundary": "software_proof_o3_o1_strict_no_motion_map_server_graph_lifecycle_visibility_only",
        "readiness_inputs": {
            "board_source_preflight_ready": board.get("classification") == "board_source_preflight_ready",
            "lightweight_cli_ready": bool(board.get("lightweight_cli_ready")),
            "cli_ready": bool(board.get("cli_ready")),
            "runtime_ready": bool(board.get("runtime_ready")),
            "ros2_cli_invocation_diagnostic_only": True,
        },
        "map_lifecycle": map_lifecycle,
        "lifecycle_readback_clean": bool(map_lifecycle.get("all_active")),
        "downstream_probes_allowed": bool(map_lifecycle.get("all_active")),
        "scan": scan,
        "map": map_topic,
        "amcl": amcl,
        "tf": tf,
        "path_generation_gate": path_gate,
        "blocking_conditions": blocking_conditions,
        "ready_for_planner_only_path_gate": ready_for_planner_only,
        "no_motion_invariants": safety_flags(),
    }


def attach_artifact_summaries(proof: dict[str, Any], *, status: str) -> None:
    """给 final/partial proof 补齐同形摘要字段，所有调用点共享同一派生逻辑。"""
    root_causes = [cause for cause in (proof.get("root_causes") or proof.get("blockers") or []) if isinstance(cause, dict)]
    scan_split = build_scan_qos_endpoint_readback_split(proof)
    proof["scan_qos_endpoint_readback_split"] = scan_split
    root_causes = enrich_scan_root_causes_with_split(root_causes, scan_split)
    proof["root_causes"] = root_causes
    proof["blockers"] = root_causes
    proof["artifact_closeout"] = build_artifact_closeout_summary(
        status=status,
        root_causes=root_causes,
        last_phase=proof.get("last_phase"),
        current_command=proof.get("current_command") if isinstance(proof.get("current_command"), dict) else None,
    )
    proof.setdefault("amcl_readiness_summary", build_amcl_readiness_summary(proof))
    proof.setdefault("tf_readiness_summary", build_tf_readiness_summary(proof))
    proof.setdefault("path_generation_gate", build_path_generation_gate_summary(proof))
    proof["downstream_recovery_summary"] = build_downstream_recovery_summary(proof)
    map_server_visibility = build_map_server_graph_lifecycle_visibility_summary(proof)
    proof["map_server_graph_lifecycle_visibility"] = map_server_visibility
    map_server_presence = build_map_server_presence_recovery_summary(
        proof,
        visibility_summary=map_server_visibility,
    )
    proof["map_server_presence_recovery"] = map_server_presence
    map_server_activation = build_map_server_lifecycle_activation_summary(
        proof,
        presence_summary=map_server_presence,
    )
    proof["map_server_lifecycle_activation"] = map_server_activation
    proof["map_server_transition_callback_probe"] = build_map_server_transition_callback_probe_summary(
        proof,
        presence_summary=map_server_presence,
        activation_summary=map_server_activation,
    )


def rclpy_node_names(
    args: argparse.Namespace,
    timeout_s: float = 0.8,
    *,
    child_command_timeout_s: float | None = None,
    fallback_timeout_s: float | None = None,
) -> dict[str, Any]:
    """用 sourced child Python 读取节点名，避免主进程未 source 时反复误报缺 rclpy。"""
    command = f"""
python3 - <<'PY'
import json
import time

payload = {{
    "executed": False,
    "ok": False,
    "node_names": [],
    "boundary": "rclpy_node_names_not_started",
    "error": None,
}}
node = None
rclpy_initialized = False
started_ms = int(time.time() * 1000)
try:
    import rclpy

    payload["executed"] = True
    if not rclpy.ok():
        rclpy.init(args=None)
    rclpy_initialized = True
    node = rclpy.create_node("o10_managed_runtime_graph_probe")
    deadline = time.time() + {max(timeout_s, 0.2)!r}
    names = []
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.05)
        names = sorted({{name for name in node.get_node_names() if name}})
        if names:
            break
    payload.update({{
        "ok": bool(names),
        "node_names": names,
        "boundary": "rclpy_node_names_observed" if names else "rclpy_node_names_empty_after_wait",
    }})
except Exception as exc:
    payload["error"] = {{"type": type(exc).__name__, "message": str(exc)[:240]}}
    payload["boundary"] = "rclpy_node_names_failed"
finally:
    payload["elapsed_ms"] = int(time.time() * 1000) - started_ms
    if node is not None:
        try:
            node.destroy_node()
        except Exception:
            pass
    if rclpy_initialized:
        try:
            if rclpy.ok():
                rclpy.shutdown()
        except Exception:
            pass
print(json.dumps(payload, ensure_ascii=False))
PY
""".strip()
    child_timeout = max(float(child_command_timeout_s), 0.5) if child_command_timeout_s is not None else max(float(timeout_s) + 4.5, 6.0)
    fallback_timeout = max(float(fallback_timeout_s), 0.5) if fallback_timeout_s is not None else max(float(timeout_s) + 4.0, 6.0)
    result = run_ros(
        args,
        command,
        timeout_s=child_timeout,
        )
    parsed = parse_json_stdout(result) or {}
    node_names = [name for name in parsed.get("node_names", []) if isinstance(name, str)] if isinstance(parsed, dict) else []
    payload = {
        "executed": bool(result.get("executed")) and bool(parsed.get("executed")),
        "ok": bool(parsed.get("ok")),
        "node_names": node_names,
        "elapsed_ms": result.get("elapsed_ms"),
        "error": parsed.get("error") if isinstance(parsed.get("error"), dict) else result.get("error"),
        "boundary": str(parsed.get("boundary") or ("rclpy_node_names_failed" if result.get("timed_out") else "rclpy_node_names_parse_failed")),
        "stdout": result.get("stdout"),
        "stderr": result.get("stderr"),
        "fallback_used": False,
        "child_command_timeout_s": child_timeout,
        "fallback_timeout_s": fallback_timeout,
    }
    if payload["ok"]:
        return payload
    # 板端 daemon 在高频自动化窗口里可能被旧 discovery 请求拖住；managed runtime 只需要
    # 当前 DDS graph，因此 fallback 固定绕过 daemon，避免 70 秒预算被重复 CLI timeout 吃完。
    fallback = run_ros(args, "ros2 node list --no-daemon", timeout_s=fallback_timeout)
    fallback_names = sorted(node_names_from_graph_result(fallback))
    fallback_boundary = (
        "ros2_node_list_observed"
        if fallback_names
        else "ros2_node_list_timeout"
        if fallback.get("timed_out")
        else "ros2_node_list_empty_after_wait"
        if fallback.get("ok")
        else "ros2_node_list_failed"
    )
    payload["fallback"] = {
        "executed": bool(fallback.get("executed")),
        "ok": bool(fallback.get("ok")),
        "node_names": fallback_names,
        "timed_out": bool(fallback.get("timed_out")),
        "returncode": fallback.get("returncode"),
        "error": fallback.get("error"),
        "boundary": fallback_boundary,
    }
    payload["fallback_used"] = True
    if fallback_names:
        payload.update(
            {
                "ok": True,
                "node_names": fallback_names,
                "boundary": f"{payload['boundary']}_with_ros2_node_list_fallback_observed",
            }
        )
    else:
        payload["boundary"] = f"{payload['boundary']}_with_{fallback_boundary}"
    return payload


def managed_wait_node_list_entries(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """history 里 node_list 字段随阶段略有差异，统一抽出供 final closeout 使用。"""
    entries: list[dict[str, Any]] = []
    for snapshot in history:
        if not isinstance(snapshot, dict):
            continue
        node_list = snapshot.get("node_list") if isinstance(snapshot.get("node_list"), dict) else snapshot.get("node_list_command")
        if isinstance(node_list, dict):
            entries.append(node_list)
    return entries


def managed_wait_graph_summary(history: list[dict[str, Any]], observed_node_names: set[str]) -> dict[str, Any]:
    """把 managed wait 的 child/fallback graph 证据压成 final 字段，避免只剩 current_command。"""
    entries = managed_wait_node_list_entries(history)
    latest = entries[-1] if entries else {}
    fallback = latest.get("fallback") if isinstance(latest.get("fallback"), dict) else {}
    fallback_boundaries = [
        str((entry.get("fallback") or {}).get("boundary"))
        for entry in entries
        if isinstance(entry.get("fallback"), dict) and (entry.get("fallback") or {}).get("boundary")
    ]
    return {
        "history_count": len(history),
        "latest_node_list_boundary": latest.get("boundary"),
        "latest_ros2_node_list_boundary": fallback.get("boundary"),
        "latest_ros2_node_list_timed_out": bool(fallback.get("timed_out")),
        "fallback_used": any(bool(entry.get("fallback_used")) for entry in entries),
        "fallback_observed": any(bool((entry.get("fallback") or {}).get("node_names")) for entry in entries if isinstance(entry.get("fallback"), dict)),
        "observed_node_names": sorted(observed_node_names),
        "fallback_boundaries": fallback_boundaries[-MANAGED_RUNTIME_GRAPH_HISTORY_LIMIT:],
    }


def managed_wait_timeout_reason(
    *,
    history: list[dict[str, Any]],
    observed_node_names: set[str],
    nodes_observed: bool,
) -> str:
    """用最后一次 graph/fallback 事实给 wait timeout 命名，避免继续停在泛化 timeout。"""
    if nodes_observed:
        return "managed_runtime_nodes_observed_but_lifecycle_inactive"
    summary = managed_wait_graph_summary(history, observed_node_names)
    if observed_node_names:
        return "managed_runtime_required_nodes_not_observed"
    latest_fallback = str(summary.get("latest_ros2_node_list_boundary") or "")
    latest_child = str(summary.get("latest_node_list_boundary") or "")
    if latest_fallback in {"ros2_node_list_timeout", "ros2_node_list_empty_after_wait", "ros2_node_list_failed"}:
        return latest_fallback
    if latest_child in {"rclpy_node_names_empty_after_wait", "rclpy_node_names_failed", "rclpy_node_names_parse_failed"}:
        return latest_child
    if summary.get("fallback_used"):
        return "managed_runtime_process_active_graph_not_observable"
    return "managed_runtime_wait_timeout"


def append_managed_wait_history(history: list[dict[str, Any]], snapshot: dict[str, Any]) -> None:
    """wait history 只保留最近窗口，避免 board artifact 因重复 timeout 膨胀。"""
    history.append(snapshot)
    if len(history) > MANAGED_RUNTIME_GRAPH_HISTORY_LIMIT:
        del history[:-MANAGED_RUNTIME_GRAPH_HISTORY_LIMIT]


def managed_graph_probe_timeouts(remaining_s: float) -> tuple[float, float]:
    """按剩余 wait 预算分配 child/fallback 窗口，给 final closeout 留出写盘时间。"""
    usable_s = max(float(remaining_s) - MANAGED_RUNTIME_GRAPH_CLOSEOUT_RESERVE_S, 0.5)
    child_timeout = min(MANAGED_RUNTIME_GRAPH_CHILD_COMMAND_TIMEOUT_S, max(0.8, usable_s * 0.55))
    fallback_timeout = min(MANAGED_RUNTIME_GRAPH_FALLBACK_TIMEOUT_S, max(0.6, usable_s - child_timeout))
    return child_timeout, fallback_timeout


def wait_for_managed_runtime(
    args: argparse.Namespace,
    runtime: dict[str, Any],
    *,
    require_planner_server: bool = False,
) -> dict[str, Any]:
    """runtime 拉起后轮询 lifecycle，尽量在 proof 窗口内拿到 active graph。"""
    deadline = time.time() + max(float(args.managed_timeout_s), 4.0)
    history: list[dict[str, Any]] = []
    required_nodes = dict(LOCALIZATION_LIFECYCLE_NODES)
    if require_planner_server:
        required_nodes["planner_server"] = "/planner_server"
    cumulative_node_lines: set[str] = set()
    latest_lifecycle_active = {key: False for key in required_nodes}
    latest_lifecycle_results = {
        key: {
            "executed": False,
            "ok": False,
            "boundary": "managed_runtime_lifecycle_check_not_run",
        }
        for key in required_nodes
    }
    lifecycle_history: list[dict[str, Any]] = []
    nodes_observed = False
    while time.time() < deadline:
        process: subprocess.Popen[str] | None = runtime.get("process")
        if process is not None and process.poll() is not None:
            graph_summary = managed_wait_graph_summary(history, cumulative_node_lines)
            return {
                "ok": False,
                "reason": "managed_runtime_exited_early",
                "boundary": "managed_runtime_exited_early",
                "returncode": process.returncode,
                "history": history,
                "graph_wait_summary": graph_summary,
                "lifecycle_active": latest_lifecycle_active,
                "lifecycle_results": latest_lifecycle_results,
                "lifecycle_history": lifecycle_history,
                "log_tail": preview_file(runtime["log_path"]),
            }
        # runtime wait 只确认节点已出现；用 rclpy graph 避免 ROS CLI 启动成本吃掉定位预算。
        remaining_s = deadline - time.time()
        if remaining_s <= MANAGED_RUNTIME_GRAPH_CLOSEOUT_RESERVE_S:
            break
        child_timeout, fallback_timeout = managed_graph_probe_timeouts(remaining_s)
        node_list = rclpy_node_names(
            args,
            timeout_s=0.8,
            child_command_timeout_s=child_timeout,
            fallback_timeout_s=fallback_timeout,
        )
        node_lines = {f"/{line.lstrip('/')}" for line in node_list.get("node_names", []) if isinstance(line, str)}
        cumulative_node_lines.update(node_lines)
        lifecycle_active = {
            "map_server": "/map_server" in node_lines,
            "amcl": "/amcl" in node_lines,
        }
        cumulative_lifecycle_active = {
            "map_server": "/map_server" in cumulative_node_lines,
            "amcl": "/amcl" in cumulative_node_lines,
        }
        if require_planner_server:
            lifecycle_active["planner_server"] = "/planner_server" in node_lines
            cumulative_lifecycle_active["planner_server"] = "/planner_server" in cumulative_node_lines
        if not node_list.get("ok"):
            append_managed_wait_history(
                history,
                {
                    "node_list": node_list,
                    "lifecycle_active": lifecycle_active,
                    "remaining_budget_s": round(max(deadline - time.time(), 0.0), 3),
                    "probe_timeouts": {"child_command_timeout_s": child_timeout, "fallback_timeout_s": fallback_timeout},
                },
            )
            # 当前板端 graph CLI/rclpy discovery 偶发同时阻塞，但本轮自有 lifecycle manager
            # 会把两个节点 active/bond 的完整顺序写进同一进程组日志。日志 clean 后立即把
            # graph blocker 作为 secondary 返回，让后续 compact TF endpoint probe 接管验证，
            # 不能继续空转到 managed_timeout 再挤掉 final artifact 与 cleanup 预算。
            log_tail = preview_file(runtime["log_path"], limit=12000)
            lifecycle_log = managed_runtime_log_lifecycle_active_readback(log_tail)
            if lifecycle_log.get("clean"):
                graph_summary = managed_wait_graph_summary(history, cumulative_node_lines)
                reason = managed_wait_timeout_reason(
                    history=history,
                    observed_node_names=cumulative_node_lines,
                    nodes_observed=False,
                )
                return {
                    "ok": False,
                    "reason": reason,
                    "boundary": reason,
                    "history": history,
                    "graph_wait_summary": graph_summary,
                    "lifecycle_active": dict(lifecycle_log.get("active") or {}),
                    "lifecycle_results": dict(lifecycle_log.get("results") or {}),
                    "lifecycle_history": lifecycle_history,
                    "observed_node_names": sorted(cumulative_node_lines),
                    "log_tail": log_tail,
                    "early_closeout": "managed_lifecycle_log_active_graph_probe_blocked",
                    "lifecycle_log_readback": lifecycle_log,
                }
            time.sleep(0.6)
            continue
        snapshot = {
            "elapsed_ms": now_ms() - int(runtime["started_at_ms"]),
            "lifecycle_active": lifecycle_active,
            "cumulative_lifecycle_active": cumulative_lifecycle_active,
            "cumulative_node_names": sorted(cumulative_node_lines),
            "node_list_command": node_list,
        }
        append_managed_wait_history(history, snapshot)
        # 先确认节点进入 graph，再用 lifecycle get 分清 “看到节点” 与 “真正 active”。
        nodes_observed = bool(
            cumulative_lifecycle_active.get("map_server")
            and cumulative_lifecycle_active.get("amcl")
            and (not require_planner_server or cumulative_lifecycle_active.get("planner_server"))
        )
        if nodes_observed:
            lifecycle_active, lifecycle_results = lifecycle_checks(
                args,
                required_nodes,
                graph_probe_result=node_list,
            )
            latest_lifecycle_active = dict(lifecycle_active)
            latest_lifecycle_results = dict(lifecycle_results)
            lifecycle_snapshot = {
                "elapsed_ms": now_ms() - int(runtime["started_at_ms"]),
                "active": latest_lifecycle_active,
                "results": latest_lifecycle_results,
            }
            lifecycle_history.append(lifecycle_snapshot)
            snapshot["lifecycle_recheck"] = lifecycle_snapshot
            if all(latest_lifecycle_active.get(key) for key in required_nodes):
                return {
                    "ok": True,
                    "history": history,
                    "node_list": node_list,
                    "observed_node_names": sorted(cumulative_node_lines),
                    "graph_wait_summary": managed_wait_graph_summary(history, cumulative_node_lines),
                    "boundary": "managed_runtime_lifecycle_active_observed",
                    "lifecycle_active": latest_lifecycle_active,
                    "lifecycle_results": latest_lifecycle_results,
                    "lifecycle_history": lifecycle_history,
                }
        time.sleep(0.8)
    graph_summary = managed_wait_graph_summary(history, cumulative_node_lines)
    reason = managed_wait_timeout_reason(
        history=history,
        observed_node_names=cumulative_node_lines,
        nodes_observed=nodes_observed,
    )
    return {
        "ok": False,
        "reason": reason,
        "boundary": reason,
        "history": history,
        "graph_wait_summary": graph_summary,
        "lifecycle_active": latest_lifecycle_active,
        "lifecycle_results": latest_lifecycle_results,
        "lifecycle_history": lifecycle_history,
        "observed_node_names": sorted(cumulative_node_lines),
        "log_tail": preview_file(runtime["log_path"]),
    }


def classify_root_causes(
    *,
    map_inputs: dict[str, Any],
    ros2_ok: bool,
    board_source_preflight: dict[str, Any],
    map_lifecycle_preflight: dict[str, Any],
    packages: dict[str, bool],
    lifecycle_active: dict[str, bool],
    scan_once_observed: bool,
    map_once_observed: bool,
    amcl_pose_observed: bool,
    localization_tf_observed: dict[str, bool],
    tf_chain_observed: dict[str, bool],
    tf_failure_classification: dict[str, Any],
    initialpose_enabled: bool,
    initialpose_publish: dict[str, Any],
    localization_outputs_required: bool = False,
    lifecycle_results: dict[str, dict[str, Any]] | None = None,
    localization_signal_freshness: dict[str, Any] | None = None,
    tf_source_freshness: dict[str, Any] | None = None,
) -> list[dict[str, str]]:
    """root cause 按层输出，方便下一轮知道是 map、runtime 还是 localization 卡住。"""
    causes = list(map_inputs.get("root_causes") or [])
    signal_freshness = localization_signal_freshness or {}
    tf_freshness = tf_source_freshness or {}
    ros2_cli_ok = bool(board_source_preflight.get("ros2_cli_ok"))
    rclpy_import_ok = bool(board_source_preflight.get("rclpy_import_ok"))
    if not ros2_ok or not ros2_cli_ok:
        causes.append(
            {
                "layer": "ROS install/source",
                "reason": str(board_source_preflight.get("classification") or "board_source_preflight_ros2_cli_path_missing"),
            }
        )
        return causes
    if not rclpy_import_ok:
        causes.append(
            {
                "layer": "ROS Python runtime",
                "reason": str(board_source_preflight.get("classification") or "board_source_preflight_rclpy_import_failed"),
            }
        )
        causes.extend(map_lifecycle_preflight.get("root_causes") or [])
        return causes
    causes.extend(map_lifecycle_preflight.get("root_causes") or [])
    for package, available in packages.items():
        if not available:
            causes.append({"layer": "ROS install/source", "reason": f"{package}_missing"})
    for key, active in lifecycle_active.items():
        if not active:
            result = (lifecycle_results or {}).get(key) if isinstance((lifecycle_results or {}).get(key), dict) else {}
            if lifecycle_result_is_skipped(result):
                continue
            causes.append({"layer": "Nav2 lifecycle", "reason": f"{key}_lifecycle_not_active"})
    if not (bool(lifecycle_active.get("map_server")) and bool(lifecycle_active.get("amcl"))):
        # lifecycle 未 clean 时，本 sprint 明确不消费 `/scan`、`/map`、TF 下游 blocker。
        return causes
    if not scan_once_observed:
        causes.append(
            {
                "layer": "Nav2 sensor input",
                "reason": signal_root_cause_reason(signal_freshness.get("/scan", {}), "/scan", "/scan_once_not_observed"),
            }
        )
    if not map_once_observed:
        causes.append({"layer": "Nav2 map input", "reason": "/map_once_not_observed"})
    if initialpose_enabled:
        if not initialpose_publish.get("ok"):
            boundary = str(initialpose_publish.get("boundary") or "initialpose_publish_failed")
            if boundary not in {"default_read_only_no_initialpose_publish", "ros2_unavailable_no_initialpose_publish"}:
                causes.append({"layer": "AMCL initialpose", "reason": boundary})
    if initialpose_enabled or localization_outputs_required:
        if (
            localization_outputs_required
            and not initialpose_enabled
            and not amcl_pose_observed
            and not localization_tf_observed.get("map_to_odom")
        ):
            # 本轮 safety contract 禁止 initialpose；AMCL 日志若同时无 pose/map->odom，
            # 最窄根因是缺定位初值，不应继续让 graph timeout 冒充主 blocker。
            causes.append(
                {
                    "layer": "AMCL initialization",
                    "reason": "amcl_requires_initial_pose_but_initialpose_forbidden_in_current_safety_scope",
                }
            )
        if not amcl_pose_observed:
            causes.append(
                {
                    "layer": "AMCL localization",
                    "reason": signal_root_cause_reason(
                        signal_freshness.get("/amcl_pose", {}),
                        "/amcl_pose",
                        "/amcl_pose_once_not_observed",
                    ),
                }
            )
        if not localization_tf_observed.get("map_to_odom"):
            causes.append(
                {
                    "layer": "Localization TF",
                    "reason": tf_edge_root_cause_reason(tf_freshness, "map_to_odom", "map_to_odom_not_observed"),
                }
            )
        causes.extend(tf_chain_root_causes(tf_failure_classification, tf_chain_observed))
    return causes


def managed_runtime_presence_log_evidence(
    managed_runtime: dict[str, Any],
    managed_map_analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """从 managed runtime 日志中提取强证据，用来压过不稳定的 package/graph 诊断噪音。"""
    log_tail = preview_file(str(managed_runtime.get("log_path") or "")) or str(managed_runtime.get("log_tail") or "")
    lowered = log_tail.lower()
    log_summary = map_server_activation_log_summary(log_tail)
    log_events = log_summary.get("events") if isinstance(log_summary.get("events"), dict) else {}
    return {
        "managed_runtime_requested": bool(managed_runtime.get("requested")),
        "managed_runtime_started": bool(managed_runtime.get("started")),
        "map_server_lifecycle_active_logged": bool(
            log_events.get("activate_started")
            and "server map_server connected with bond" in lowered
        ),
        "amcl_lifecycle_active_logged": bool(
            "activating amcl" in lowered
            and "server amcl connected with bond" in lowered
        ),
        "managed_nodes_active_logged": "managed nodes are active" in lowered,
        "lidar_serial_exception": "serial.serialutil.serialexception" in lowered,
        "map_yaml_analysis_ok": bool((managed_map_analysis or {}).get("ok")),
        "map_server_configure_started": "configuring map_server" in lowered or "[map_server]: configuring" in lowered,
        "lifecycle_manager_configure_requested": bool(log_events.get("lifecycle_manager_configure_requested")),
        "map_server_configure_callback_entered": bool(log_events.get("map_server_configure_callback_entered")),
        "map_yaml_loaded": "loading yaml file:" in lowered and "trashbot_map.yaml" in lowered,
        "map_pgm_loaded": "loading image_file:" in lowered and "trashbot_map.pgm" in lowered,
        "map_read_completed": bool(log_events.get("map_read_completed")),
        "map_read_after_state_change_failure": bool(log_events.get("map_read_after_state_change_failure")),
        "state_change_failed_after_image_load_before_map_read_completed": bool(
            log_events.get("state_change_failed_after_image_load_before_map_read_completed")
        ),
        "changestate_response_false_before_map_io_completion": bool(
            log_events.get("changestate_response_false_before_map_io_completion")
        ),
        "state_change_failed_before_map_server_configure_callback": bool(
            log_events.get("state_change_failed_before_map_server_configure_callback")
        ),
        "map_server_state_change_failed": "failed to change state for node: map_server" in lowered,
        "amcl_configure_requested": bool(log_events.get("amcl_configure_requested")),
        "amcl_configure_callback_entered": bool(log_events.get("amcl_configure_callback_entered")),
        "amcl_state_change_failed": bool(log_events.get("amcl_state_change_failed")),
        "amcl_state_change_failed_after_map_server_configure_success": bool(
            log_events.get("amcl_state_change_failed_after_map_server_configure_success")
        ),
        "dds_shm_transport_error": bool(log_events.get("dds_shm_transport_error")),
        "dds_transport_error_text": str(log_summary.get("dds_transport_error_text") or "")[-1200:],
        "lifecycle_manager_started": "starting role=lifecycle_manager" in lowered or "[lifecycle_manager]" in lowered,
        "map_server_process_started": "starting role=map_server" in lowered or "[map_server]" in lowered,
        "log_tail_excerpt": log_tail[-1200:],
    }


def lifecycle_active_downstream_root_cause(cause: dict[str, Any]) -> bool:
    """lifecycle 已由日志证明 active 后，优先把主因落到可行动的 topic/TF/readback gate。"""
    layer = str(cause.get("layer") or "")
    reason = str(cause.get("reason") or "")
    if layer in {"Nav2 sensor input", "Nav2 map input", "AMCL localization", "Localization TF"}:
        return True
    return bool(
        reason.startswith("/scan")
        or reason.startswith("/map")
        or reason.startswith("/amcl_pose")
        or reason.startswith("/tf")
        or reason.startswith("map_to_odom")
        or reason.startswith("map_to_base_link")
        or reason.startswith("odom_to_base_link")
        or reason.startswith("base_link_to_laser_frame")
    )


def normalize_root_causes_for_presence_recovery(
    root_causes: list[dict[str, str]],
    *,
    managed_runtime: dict[str, Any],
    managed_map_analysis: dict[str, Any] | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """managed runtime 已证明 map_server 运行过时，避免把 probe timeout 写成 package missing。"""
    evidence = managed_runtime_presence_log_evidence(managed_runtime, managed_map_analysis)
    strong_presence_evidence = bool(
        evidence["managed_runtime_requested"]
        and evidence["managed_runtime_started"]
        and (
            evidence["map_server_configure_started"]
            or evidence["map_server_state_change_failed"]
            or evidence["map_yaml_loaded"]
            or evidence["map_server_process_started"]
        )
    )
    if not strong_presence_evidence:
        return root_causes, {
            "applied": False,
            "reason": "managed_runtime_presence_log_evidence_not_strong_enough",
            "evidence": evidence,
            "suppressed_root_causes": [],
        }

    if evidence.get("managed_nodes_active_logged"):
        primary = {
            "layer": "Managed runtime graph readback",
            "reason": "managed_runtime_graph_probe_timeout_after_lifecycle_active_log",
            "detail": "map_server_and_amcl_lifecycle_active_logged_but_graph_wait_or_downstream_readback_not_clean",
        }
    elif evidence["map_server_state_change_failed"] and evidence["map_yaml_analysis_ok"] and evidence.get("dds_shm_transport_error"):
        primary = {
            "layer": "Nav2 map_server ChangeState RPC / DDS transport",
            "reason": "map_server_change_state_rpc_dds_shm_transport_port_lock",
            "detail": "fastdds_shm_open_and_lock_file_failed_during_configure_change_state_or_graph_readback",
        }
    elif evidence["map_server_state_change_failed"] and evidence["map_yaml_analysis_ok"]:
        if evidence.get("state_change_failed_before_map_server_configure_callback"):
            reason = "map_server_changestate_response_failure_before_configure_callback_log"
            detail = "lifecycle_manager_changestate_response_failure_logged_before_map_server_on_configure_log"
        elif evidence.get("state_change_failed_after_image_load_before_map_read_completed"):
            if evidence.get("changestate_response_false_before_map_io_completion"):
                reason = "map_server_loadmap_response_success_equivalent_after_changestate_failure"
                detail = "loadmap_response_success_equivalent_logged_after_lifecycle_changestate_failure_without_direct_return_code"
            else:
                reason = "map_server_changestate_response_failure_after_image_load_before_map_read_completed"
                detail = "lifecycle_manager_changestate_response_failure_after_image_load_before_map_read_completed"
        else:
            map_read_order = (
                "before_deferred_map_read_completed"
                if evidence.get("map_read_after_state_change_failure")
                else "after_map_read_completed"
                if evidence.get("map_read_completed")
                else "with_map_read_not_observed"
            )
            reason = (
                "map_server_configure_return_failure_after_map_read_completed"
                if map_read_order == "after_map_read_completed"
                else "map_server_configure_return_failure_before_deferred_map_read_completed"
                if map_read_order == "before_deferred_map_read_completed"
                else "map_server_configure_callback_return_failure"
            )
            detail = f"lifecycle_manager_changestate_response_failure_during_configure_{map_read_order}"
        primary = {
            "layer": "Nav2 map_server transition callback",
            "reason": reason,
            "detail": detail,
        }
    elif evidence["map_server_state_change_failed"]:
        primary = {
            "layer": "Nav2 map_server presence recovery",
            "reason": "map_server_lifecycle_not_active_after_recovery",
            "detail": "lifecycle_manager_failed_to_change_state_for_map_server",
        }
    elif evidence.get("amcl_state_change_failed_after_map_server_configure_success"):
        primary = {
            "layer": "Nav2 lifecycle manager sequence",
            "reason": "map_server_configure_completed_lifecycle_blocked_by_amcl_configure_failure",
            "detail": "lifecycle_manager_advanced_to_amcl_after_map_server_configure_then_amcl_changestate_failed",
        }
    else:
        primary = {
            "layer": "Nav2 map_server presence recovery",
            "reason": "managed_runtime_started_map_server_presence_evidence_observed",
            "detail": "package_probe_downgraded_after_runtime_log_evidence",
        }
    package_missing_reasons = {f"{package}_missing" for package in EXPECTED_PACKAGES}
    suppressed: list[dict[str, str]] = []
    retained: list[dict[str, str]] = []
    for cause in root_causes:
        reason = str(cause.get("reason") or "")
        layer = str(cause.get("layer") or "")
        suppress = False
        if layer == "ROS install/source" and reason in package_missing_reasons:
            suppress = True
        elif layer == "Managed runtime wait" and reason in MANAGED_RUNTIME_GRAPH_BLOCKED_REASONS:
            # graph/node-list timeout 是本轮诊断噪音；runtime 日志已经证明 map_server/lifecycle_manager 到达更深层。
            suppress = True
        elif layer == "canonical map proof" and reason == "map_lifecycle_proof_not_clean" and evidence["map_yaml_loaded"]:
            # 旧 map proof 不能覆盖本轮 managed map yaml 已加载的事实。
            suppress = True
        if suppress:
            suppressed.append(dict(cause))
        else:
            retained.append(dict(cause))
    promoted_downstream: dict[str, str] | None = None
    lifecycle_active_graph_secondary: dict[str, str] | None = None
    if evidence.get("managed_nodes_active_logged"):
        downstream_candidates = [cause for cause in retained if lifecycle_active_downstream_root_cause(cause)]
        if downstream_candidates:
            # 17:55 以后 lifecycle-active 是 baseline；若本轮已经继续读到 `/scan`、
            # `/map`、`/amcl_pose` 或 TF 的具体 blocker，closeout 主因必须前移到这些 gate。
            promoted_downstream = dict(downstream_candidates[0])
            promoted_downstream.setdefault(
                "detail",
                "downstream_readback_after_map_server_and_amcl_lifecycle_active_log",
            )
            lifecycle_active_graph_secondary = dict(primary)
            retained = [
                cause
                for cause in retained
                if not (
                    cause.get("layer") == promoted_downstream.get("layer")
                    and cause.get("reason") == promoted_downstream.get("reason")
                )
            ]
            primary = promoted_downstream
    normalized = [primary]
    if lifecycle_active_graph_secondary:
        normalized.append(lifecycle_active_graph_secondary)
    normalized.extend(
        cause
        for cause in retained
        if not (
            cause.get("layer") == primary["layer"]
            and cause.get("reason") == primary["reason"]
        )
    )
    return normalized, {
        "applied": True,
        "reason": "managed_runtime_log_evidence_overrides_package_probe_missing_root_causes",
        "evidence": evidence,
        "suppressed_root_causes": suppressed,
        "retained_root_causes": retained,
        "promoted_downstream_after_lifecycle_active_log": promoted_downstream,
        "lifecycle_active_graph_secondary_root_cause": lifecycle_active_graph_secondary,
        "diagnostic_note": "package_checks remain in proof.package_availability and commands.package_checks but are not primary root causes after runtime evidence",
    }


def demote_managed_wait_after_successful_path_generation(
    root_causes: list[dict[str, str]],
    *,
    path_generation_request: dict[str, Any],
    path_generation_result: dict[str, Any],
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """ComputePathToPose 已生成 path 时，graph wait timeout 只能作为辅助诊断。"""
    path_generation_success = bool(
        path_generation_request.get("enabled")
        and path_generation_result.get("ok")
        and path_generation_result.get("path_generated")
    )
    if not path_generation_success:
        return root_causes, {
            "applied": False,
            "reason": "path_generation_success_not_observed",
            "suppressed_root_causes": [],
        }

    suppressed: list[dict[str, str]] = []
    retained: list[dict[str, str]] = []
    for cause in root_causes:
        layer = str(cause.get("layer") or "")
        reason = str(cause.get("reason") or "")
        if layer == "Managed runtime wait" and reason in MANAGED_RUNTIME_GRAPH_BLOCKED_REASONS:
            # action 已同一轮返回 path，说明 planner_server、AMCL/TF 和 map 输入已经足以
            # 完成只读规划；graph wait timeout 仍保留用于诊断，但不能覆盖更强的下游事实。
            demoted = dict(cause)
            demoted.setdefault(
                "detail",
                "compute_path_to_pose_succeeded_in_same_run_after_managed_runtime_graph_wait_timeout",
            )
            suppressed.append(demoted)
        else:
            retained.append(dict(cause))

    return retained, {
        "applied": bool(suppressed),
        "reason": (
            "compute_path_to_pose_success_demotes_managed_runtime_graph_wait"
            if suppressed
            else "path_generation_success_no_managed_wait_root_cause"
        ),
        "suppressed_root_causes": suppressed,
        "retained_root_causes": retained,
        "path_generation_boundary": path_generation_result.get("boundary"),
        "path_point_count": int(path_generation_result.get("path_point_count") or 0),
        "path_generation_fallback_used": bool(path_generation_result.get("fallback_used")),
        "path_generation_fallback_mode": path_generation_result.get("fallback_mode"),
    }


def build_proof(args: argparse.Namespace) -> dict[str, Any]:
    """执行一次 no-motion AMCL/Nav2 proof；成功或失败都写 latest artifact。"""
    started_ms = now_ms()
    phase_writer = PhaseArtifactWriter(args, started_ms)
    global ACTIVE_PHASE_WRITER
    ACTIVE_PHASE_WRITER = phase_writer
    install_phase_signal_handlers(phase_writer)
    setattr(args, "_phase_writer", phase_writer)
    phase_writer.record_phase("start", ok=True, detail={"mode": "no_motion_amcl_nav2_runtime_proof"})
    map_inputs = map_input_summary(args)
    phase_writer.update_snapshot(map_inputs_ready=bool(map_inputs.get("inputs_ready")))
    phase_writer.record_phase(
        "map_inputs",
        ok=bool(map_inputs.get("inputs_ready")),
        detail={"source_proof_status": map_inputs.get("source_proof_status")},
    )
    managed_map_yaml, managed_map_yaml_source = resolve_managed_map_yaml(args, map_inputs)
    managed_map_analysis = map_yaml_runtime_analysis(managed_map_yaml)
    managed_runtime: dict[str, Any] = {
        "requested": bool(args.managed_runtime_opt_in),
        "started": False,
        "process_group": None,
        "cleanup_ok": True,
        "boundary": "default_read_only_existing_ros_graph_no_runtime_start",
        "map_yaml": managed_map_yaml,
        "requested_map_yaml": str(args.managed_map_yaml or ""),
        "map_yaml_source": managed_map_yaml_source,
        "map_analysis": managed_map_analysis,
        "wait_result": {"executed": False, "ok": False, "boundary": "managed_runtime_not_requested"},
        "cleanup_result": {"attempted": False, "ok": True, "boundary": "managed_runtime_not_requested"},
        "startup_error": None,
    }
    managed_static_tf_processes: dict[str, Any] = {
        "expected": [],
        "observed_roles": [],
        "processes": [],
        "all_expected_processes_observed": False,
        "checked_before_cleanup": False,
    }

    phase_writer.record_phase("board_source_preflight")
    board_source = board_source_preflight(args)
    ros2_check = dict(board_source["commands"]["ros2_cli"])
    ros2_ok = bool(board_source.get("ros2_cli_ok"))
    board_source_cli_ready = bool(board_source.get("cli_ready"))
    board_source_runtime_ready = bool(board_source.get("runtime_ready"))
    # managed runtime / ros2 CLI 读操作只需要 source + ros2 可用；rclpy runtime 单独作为更细 gate。
    board_source_ready = board_source_cli_ready
    phase_writer.update_snapshot(
        board_source_preflight=board_source,
        board_source_ready=board_source_ready,
    )
    phase_writer.record_phase(
        "board_source_preflight",
        ok=board_source_ready,
        root_cause=(
            {"layer": "ROS install/source", "reason": str(board_source.get("classification"))}
            if not board_source_ready
            else None
        ),
        detail={
            "cli_ready": board_source_cli_ready,
            "runtime_ready": board_source_runtime_ready,
            "ros2_cli_ok": bool(board_source.get("ros2_cli_ok")),
            "rclpy_import_ok": bool(board_source.get("rclpy_import_ok")),
            "classification": board_source.get("classification"),
        },
    )

    if args.managed_runtime_opt_in and board_source_ready:
        phase_writer.record_phase(
            "managed_runtime",
            detail={"requested": True, "map_yaml_source": managed_map_yaml_source},
        )
        if managed_map_yaml is None:
            managed_runtime["boundary"] = "managed_runtime_requested_but_map_yaml_missing"
            managed_runtime["startup_error"] = {
                "layer": "managed runtime",
                "reason": managed_map_yaml_source,
            }
            phase_writer.record_phase(
                "managed_runtime",
                ok=False,
                root_cause={"layer": "managed runtime", "reason": managed_map_yaml_source},
            )
        else:
            try:
                managed_runtime.update(start_managed_runtime(args, map_yaml=managed_map_yaml))
                phase_writer.update_snapshot(
                    managed_runtime_started=True,
                    managed_runtime_process_group=managed_runtime.get("process_group"),
                    managed_runtime_boundary=managed_runtime.get("boundary"),
                )
                phase_writer.record_phase(
                    "managed_runtime_started",
                    ok=True,
                    detail={
                        "process_group": managed_runtime.get("process_group"),
                        "map_yaml": managed_runtime.get("map_yaml"),
                    },
                )
                # planner_server 的 active 状态依赖 map->base_link；这里只等节点入 graph。
                # 后续仍要单独复查 lifecycle，但 ComputePathToPose 本身也是 no-motion，可作为最终证据。
                managed_runtime["wait_result"] = wait_for_managed_runtime(
                    args,
                    managed_runtime,
                    require_planner_server=bool(args.path_generation_opt_in),
                )
                wait_nodes = managed_runtime_observed_node_names(managed_runtime)
                wait_lifecycle_active = (
                    managed_runtime["wait_result"].get("lifecycle_active")
                    if isinstance(managed_runtime["wait_result"].get("lifecycle_active"), dict)
                    else {
                        "map_server": "/map_server" in wait_nodes,
                        "amcl": "/amcl" in wait_nodes,
                    }
                )
                wait_lifecycle_results = (
                    managed_runtime["wait_result"].get("lifecycle_results")
                    if isinstance(managed_runtime["wait_result"].get("lifecycle_results"), dict)
                    else {
                        key: {
                            "executed": False,
                            "ok": bool(wait_lifecycle_active.get(key)),
                            "boundary": (
                                "managed_runtime_wait_node_observed"
                                if wait_lifecycle_active.get(key)
                                else "managed_runtime_wait_node_not_observed"
                            ),
                        }
                        for key in LOCALIZATION_LIFECYCLE_NODES
                    }
                )
                phase_writer.update_snapshot(
                    managed_runtime_wait_result=managed_runtime.get("wait_result"),
                    map_server_active=wait_lifecycle_active["map_server"],
                    amcl_active=wait_lifecycle_active["amcl"],
                    map_lifecycle_preflight=build_map_lifecycle_preflight(
                        ros2_cli_ok=ros2_ok,
                        lifecycle_active=wait_lifecycle_active,
                        lifecycle_results=wait_lifecycle_results,
                    ),
                )
                phase_writer.record_phase(
                    "managed_runtime_wait",
                    ok=bool(managed_runtime["wait_result"].get("ok")),
                    root_cause=(
                        {"layer": "Managed runtime wait", "reason": str(managed_runtime["wait_result"].get("reason") or managed_runtime["wait_result"].get("boundary"))}
                        if not managed_runtime["wait_result"].get("ok")
                        else None
                    ),
                    detail={"reason": managed_runtime["wait_result"].get("reason")},
                )
                managed_static_tf_processes = managed_static_tf_process_summary(args, managed_runtime)
                phase_writer.update_snapshot(
                    managed_static_tf_processes=managed_static_tf_processes,
                    static_tf_source_observed=False,
                    amcl_log_tail=preview_file(str(managed_runtime.get("log_path") or "")),
                )
            except Exception as exc:  # noqa: BLE001 - runtime 拉起失败必须结构化写回。
                managed_runtime["startup_error"] = compact_error(exc)
                managed_runtime["boundary"] = "managed_runtime_start_failed"
                phase_writer.record_phase(
                    "managed_runtime",
                    ok=False,
                    root_cause={"layer": "managed runtime", "reason": "managed_runtime_start_failed"},
                    detail={"error": managed_runtime["startup_error"]},
                )
    elif args.managed_runtime_opt_in:
        managed_runtime["boundary"] = "managed_runtime_skipped_after_board_source_preflight_failure"
        managed_runtime["startup_error"] = {
            "layer": "ROS install/source",
            "reason": str(board_source.get("classification") or "board_source_preflight_failed"),
        }
        phase_writer.record_phase(
            "managed_runtime",
            ok=False,
            root_cause={"layer": "ROS install/source", "reason": str(board_source.get("classification"))},
            detail={"requested": True, "boundary": managed_runtime["boundary"]},
        )
    else:
        phase_writer.record_phase("managed_runtime", ok=True, detail={"requested": False})

    managed_runtime_wait_snapshot = managed_runtime.get("wait_result") if isinstance(managed_runtime.get("wait_result"), dict) else {}
    managed_runtime_wait_graph_blocked = bool(
        managed_runtime.get("started")
        and managed_runtime_wait_snapshot
        and not managed_runtime_wait_snapshot.get("ok")
        and str(managed_runtime_wait_snapshot.get("reason") or managed_runtime_wait_snapshot.get("boundary"))
        in MANAGED_RUNTIME_GRAPH_BLOCKED_REASONS
    )
    managed_log_lifecycle_readback = managed_runtime_log_lifecycle_active_readback(
        preview_file(str(managed_runtime.get("log_path") or ""), limit=12000)
    )
    managed_runtime_lifecycle_log_clean = bool(managed_log_lifecycle_readback.get("clean"))
    managed_runtime_wait_graph_blocked_without_lifecycle_log = bool(
        managed_runtime_wait_graph_blocked and not managed_runtime_lifecycle_log_clean
    )
    phase_writer.record_phase(
        "ros2_graph_timeout_root_cause_probe",
        detail={
            "graph_wait_blocked": managed_runtime_wait_graph_blocked,
            "lifecycle_log_clean": managed_runtime_lifecycle_log_clean,
            "downstream_readback_allowed_after_lifecycle_log": bool(
                managed_runtime_wait_graph_blocked and managed_runtime_lifecycle_log_clean
            ),
        },
    )
    ros2_graph_timeout_probes = collect_ros2_graph_timeout_probes(
        args,
        board_source_preflight=board_source,
    )
    ros2_graph_timeout_root_cause = build_ros2_graph_timeout_root_cause(
        board_source_preflight=board_source,
        managed_runtime=managed_runtime,
        managed_runtime_wait_graph_blocked=managed_runtime_wait_graph_blocked,
        probes=ros2_graph_timeout_probes,
        tf_source_root_cause_detail=None,
        require_planner_server=bool(args.path_generation_opt_in),
    )
    phase_writer.update_snapshot(
        ros2_graph_timeout_root_cause=ros2_graph_timeout_root_cause,
        managed_runtime_log_lifecycle_readback=managed_log_lifecycle_readback,
    )
    phase_writer.record_phase(
        "ros2_graph_timeout_root_cause_probe",
        ok=ros2_graph_timeout_root_cause["classification"] != "root_cause_unclassified_after_probe",
        detail={
            "classification": ros2_graph_timeout_root_cause["classification"],
            "primary_reason": ros2_graph_timeout_root_cause["primary_candidate"]["reason"],
        },
    )

    phase_writer.record_phase("lifecycle_cli_budget_recovery")
    if ros2_ok and board_source_ready and managed_runtime_wait_graph_blocked and managed_runtime_lifecycle_log_clean:
        # graph wait timeout 不能覆盖 17:55 以后更强的 lifecycle-active 日志证据；
        # 这里直接用日志 readback 放行后续只读 topic/TF probe，并把 graph timeout 留作 secondary。
        pre_downstream_lifecycle_active = dict(managed_log_lifecycle_readback.get("active") or {})
        pre_downstream_lifecycle_results = dict(managed_log_lifecycle_readback.get("results") or {})
        phase_writer.record_phase(
            "lifecycle_cli_budget_recovery",
            detail={"mode": "managed_runtime_wait_graph_blocked_but_lifecycle_log_clean"},
        )
    elif ros2_ok and board_source_ready and not managed_runtime_wait_graph_blocked:
        pre_downstream_lifecycle_active, pre_downstream_lifecycle_results = lifecycle_checks(args)
    else:
        pre_downstream_lifecycle_active = {key: False for key in LOCALIZATION_LIFECYCLE_NODES}
        pre_downstream_lifecycle_results = {
            key: {
                "executed": False,
                "ok": False,
                "boundary": (
                    "lifecycle_cli_budget_recovery_skipped_after_managed_runtime_graph_wait_blocked"
                    if managed_runtime_wait_graph_blocked_without_lifecycle_log
                    else "lifecycle_cli_budget_recovery_skipped_without_ros2_cli"
                ),
            }
            for key in LOCALIZATION_LIFECYCLE_NODES
        }
    pre_downstream_lifecycle_preflight = build_map_lifecycle_preflight(
        ros2_cli_ok=ros2_ok and board_source_ready,
        lifecycle_active=pre_downstream_lifecycle_active,
        lifecycle_results=pre_downstream_lifecycle_results,
    )
    pre_downstream_lifecycle_clean = bool(
        pre_downstream_lifecycle_active.get("map_server")
        and pre_downstream_lifecycle_active.get("amcl")
    )
    phase_writer.update_snapshot(
        map_server_active=bool(pre_downstream_lifecycle_active.get("map_server")),
        amcl_active=bool(pre_downstream_lifecycle_active.get("amcl")),
        map_lifecycle_preflight=pre_downstream_lifecycle_preflight,
    )
    phase_writer.record_phase(
        "lifecycle_cli_budget_recovery",
        ok=pre_downstream_lifecycle_clean,
        root_cause=(
            {"layer": "Nav2 lifecycle", "reason": str(pre_downstream_lifecycle_preflight.get("blocking_reasons") or {})}
            if ros2_ok and board_source_ready and not pre_downstream_lifecycle_clean
            else None
        ),
        detail={
            "clean": pre_downstream_lifecycle_clean,
            "classification": pre_downstream_lifecycle_preflight.get("classification"),
            "blocking_reasons": pre_downstream_lifecycle_preflight.get("blocking_reasons"),
        },
    )

    phase_writer.record_phase("initialpose")
    initialpose_request_payload, initialpose_publish = maybe_publish_initialpose(
        args,
        ros2_ok
        and board_source_ready
        and pre_downstream_lifecycle_clean
        and not managed_runtime_wait_graph_blocked_without_lifecycle_log,
    )
    if initialpose_request_payload["enabled"] and managed_runtime_wait_graph_blocked_without_lifecycle_log:
        initialpose_publish.update(
            {
                "executed": False,
                "ok": False,
                "boundary": "initialpose_skipped_after_managed_runtime_graph_wait_blocked",
                "publish_method": "skipped_after_managed_runtime_graph_wait_blocked",
                "error": {
                    "type": "ManagedRuntimeGraphWaitBlocked",
                    "message": str(managed_runtime_wait_snapshot.get("reason") or managed_runtime_wait_snapshot.get("boundary"))[:240],
                },
            }
        )
    elif initialpose_request_payload["enabled"] and not board_source_ready:
        initialpose_publish.update(
            {
                "executed": False,
                "ok": False,
                "boundary": "board_source_preflight_failed_no_initialpose_publish",
                "error": {
                    "type": "BoardSourcePreflightFailed",
                    "message": str(board_source.get("classification") or "board_source_preflight_failed")[:240],
                },
            }
        )
    phase_writer.update_snapshot(
        initialpose_publish_attempted=bool(initialpose_request_payload["enabled"]),
        initialpose_published=bool(initialpose_publish.get("ok")),
        initialpose_publish_method=initialpose_publish.get("publish_method"),
        initialpose_subscriber_count=initialpose_publish.get("subscriber_count"),
        initialpose_publish_attempts=int(initialpose_publish.get("publish_attempts") or 0),
        initialpose_publish_elapsed_ms=initialpose_publish.get("elapsed_ms"),
        initialpose_publish_error=initialpose_publish.get("error"),
    )
    phase_writer.record_phase(
        "initialpose",
        ok=bool(initialpose_publish.get("ok")) if initialpose_request_payload["enabled"] else True,
        detail={
            "enabled": bool(initialpose_request_payload["enabled"]),
            "method": initialpose_publish.get("publish_method"),
            "subscriber_count": initialpose_publish.get("subscriber_count"),
            "publish_attempts": initialpose_publish.get("publish_attempts"),
        },
    )
    echo_timeout_s = min(max(float(args.timeout_s), 4.0), 18.0)
    amcl_pose_once = {
        "executed": False,
        "ok": False,
        "boundary": "pre_initialpose_amcl_pose_probe_skipped_to_prioritize_initialpose",
    }
    phase_writer.record_phase("amcl_pose_probe")
    post_initialpose_amcl_pose_once = (
        run_ros(args, "timeout 8 ros2 topic echo --once /amcl_pose", timeout_s=echo_timeout_s + 2.0)
        if ros2_ok
        and board_source_ready
        and pre_downstream_lifecycle_clean
        and initialpose_request_payload["enabled"]
        and not managed_runtime_wait_graph_blocked_without_lifecycle_log
        else {"executed": False, "ok": False, "boundary": "post_initialpose_probe_not_requested"}
    )
    amcl_pose_probe_ok = bool(topic_once_observed(amcl_pose_once) or topic_once_observed(post_initialpose_amcl_pose_once))
    early_amcl_pose_entry = build_signal_entry(
        topic="/amcl_pose",
        topic_type=None,
        endpoint_summary={
            "publishers": [],
            "subscribers": [],
            "publisher_count": 0,
            "subscriber_count": 0,
            "inventory_observed": False,
            "error": {"type": "endpoint_inventory_not_yet_collected", "message": "tf source probe has not run yet"},
        },
        probe_result=select_amcl_pose_probe(amcl_pose_once, post_initialpose_amcl_pose_once),
        observed=amcl_pose_probe_ok,
        stamp=parse_first_ros_stamp(
            str(select_amcl_pose_probe(amcl_pose_once, post_initialpose_amcl_pose_once).get("stdout") or ""),
            source="/amcl_pose.header.stamp",
        ),
        source_class="message",
        reference_ms=now_ms(),
    )
    phase_writer.update_snapshot(
        amcl_pose_observed=amcl_pose_probe_ok,
        amcl_pose_frame_id=parse_pose_frame_id(str(post_initialpose_amcl_pose_once.get("stdout") or "")),
        localization_signal_freshness={"/amcl_pose": early_amcl_pose_entry},
    )
    phase_writer.record_phase(
        "amcl_pose_probe",
        ok=amcl_pose_probe_ok,
        root_cause=(
            {"layer": "AMCL localization", "reason": "/amcl_pose_once_not_observed"}
            if initialpose_request_payload["enabled"] and not amcl_pose_probe_ok
            else None
        ),
    )
    phase_writer.record_phase("tf_source_probe")
    if board_source_ready:
        tf_source_probe_result, tf_source_diagnostics = collect_tf_source_diagnostics(
            args,
            # 本轮 source inventory 是独立只读事实；lifecycle 不 clean 也要采 endpoint/edge，
            # 但后续 readiness 仍由 lifecycle gate fail closed，不能把 source probe 当成 AMCL ready。
            ros2_cli_ready=ros2_ok and board_source_cli_ready,
            rclpy_runtime_ready=board_source_runtime_ready,
            board_source_preflight_result=board_source,
            amcl_pose_result=post_initialpose_amcl_pose_once,
        )
    else:
        tf_source_probe_result = {
            "executed": False,
            "ok": False,
            "boundary": "tf_source_probe_skipped_without_board_source_readiness",
            "board_source_ready": False,
        }
        tf_source_diagnostics = default_tf_source_diagnostics(
            args,
            amcl_pose_result=post_initialpose_amcl_pose_once,
            root_cause_reason="tf_source_probe_skipped_without_board_source_readiness",
            probe_boundary="tf_source_probe_skipped_without_board_source_readiness",
        )
    ros2_graph_timeout_root_cause = build_ros2_graph_timeout_root_cause(
        board_source_preflight=board_source,
        managed_runtime=managed_runtime,
        managed_runtime_wait_graph_blocked=managed_runtime_wait_graph_blocked,
        probes=ros2_graph_timeout_probes,
        tf_source_root_cause_detail=tf_source_diagnostics["tf_source_root_cause_detail"],
        require_planner_server=bool(args.path_generation_opt_in),
    )
    phase_writer.update_snapshot(
        ros2_graph_timeout_root_cause=ros2_graph_timeout_root_cause,
        tf_topics_observed=tf_source_diagnostics["tf_topics_observed"],
        tf_static_observed=tf_source_diagnostics["tf_static_observed"],
        tf_frame_inventory=tf_source_diagnostics["tf_frame_inventory"],
        base_link_to_laser_frame_transform=tf_source_diagnostics["base_link_to_laser_frame_source_transform"],
        amcl_pose_frame_id=tf_source_diagnostics["amcl_pose_frame_id"],
        amcl_node_publishers=tf_source_diagnostics["amcl_node_publishers"],
        amcl_node_subscribers=tf_source_diagnostics["amcl_node_subscribers"],
        amcl_param_probe_ok=tf_source_diagnostics["amcl_param_probe_ok"],
        amcl_node_info_observed=tf_source_diagnostics["amcl_node_info_observed"],
        amcl_tf_broadcast_param=tf_source_diagnostics["amcl_tf_broadcast_param"],
        amcl_frame_params=tf_source_diagnostics["amcl_frame_params"],
        tf_source_root_cause_detail=tf_source_diagnostics["tf_source_root_cause_detail"],
        amcl_broadcast_conditions=tf_source_diagnostics["amcl_broadcast_conditions"],
        managed_static_tf_processes=managed_static_tf_processes,
        static_tf_source_observed=bool(
            managed_static_tf_processes.get("all_expected_processes_observed")
            and tf_source_diagnostics["tf_static_observed"]
        ),
        amcl_log_tail=preview_file(str(managed_runtime.get("log_path") or "")),
        map_frame_observed=tf_source_diagnostics["map_frame_observed"],
        odom_frame_observed=tf_source_diagnostics["odom_frame_observed"],
        amcl_tf_root_cause=tf_source_diagnostics["amcl_tf_root_cause"],
    )
    phase_writer.record_phase(
        "tf_source_probe",
        ok=bool(tf_source_diagnostics["tf_topics_observed"].get("/tf")) if board_source_ready else False,
        detail={"amcl_tf_root_cause": tf_source_diagnostics["amcl_tf_root_cause"]},
    )
    phase_writer.record_phase("tf_probe")
    frame_contract = tf_chain_frame_contract(args)
    frame_ids = frame_contract["actual"]
    tf_not_requested = {
        "executed": False,
        "ok": False,
        "boundary": (
            "tf_probe_skipped_after_managed_runtime_graph_wait_blocked"
            if managed_runtime_wait_graph_blocked_without_lifecycle_log
            else "tf_probe_not_requested_without_initialpose_opt_in"
        ),
    }
    tf_chain_results = {
        "map_to_odom": tf_not_requested,
        "odom_to_base_link": tf_not_requested,
        "base_link_to_laser_frame": tf_not_requested,
        "map_to_base_link": tf_not_requested,
    }

    def update_tf_progress() -> tuple[dict[str, bool], dict[str, Any], dict[str, Any], dict[str, bool]]:
        """每段 TF probe 后立刻落 partial，并优先采信轻量 source inventory。"""
        observed = {
            "map_to_odom": bool(
                tf_source_diagnostics.get("map_to_odom_source_observed")
                or tf_echo_transform_observed(tf_chain_results["map_to_odom"])
            ),
            "odom_to_base_link": bool(
                tf_source_diagnostics.get("odom_to_base_link_source_observed")
                or tf_echo_transform_observed(tf_chain_results["odom_to_base_link"])
            ),
            "base_link_to_laser_frame": bool(
                tf_source_diagnostics.get("base_link_to_laser_frame_source_observed")
                or tf_echo_transform_observed(tf_chain_results["base_link_to_laser_frame"])
            ),
            "map_to_base_link": bool(
                (
                    tf_source_diagnostics.get("map_to_odom_source_observed")
                    and tf_source_diagnostics.get("odom_to_base_link_source_observed")
                )
                or tf_echo_transform_observed(tf_chain_results["map_to_base_link"])
            ),
        }
        diagnostics = build_tf_chain_diagnostics(
            args=args,
            results=tf_chain_results,
            observed=observed,
            tf_source_diagnostics=tf_source_diagnostics,
        )
        classification = classify_tf_chain_failure(
            args=args,
            observed=observed,
            diagnostics=diagnostics,
        )
        localization_observed = {
            "map_to_odom": observed["map_to_odom"],
            "map_to_base_link": observed["map_to_base_link"],
        }
        phase_writer.update_snapshot(
            localization_tf_observed=localization_observed,
            tf_chain_observed=observed,
            tf_chain_diagnostics=diagnostics,
            tf_failure_classification=classification,
        )
        return observed, diagnostics, classification, localization_observed

    map_to_odom_tf = (
        run_ros(
            args,
            f"timeout {TF_ECHO_SHELL_TIMEOUT_S:g} ros2 run tf2_ros tf2_echo map {shlex.quote(frame_ids['odom'])}",
            timeout_s=TF_ECHO_PROCESS_TIMEOUT_S,
        )
        if ros2_ok and initialpose_request_payload["enabled"] and not tf_source_diagnostics.get("map_to_odom_source_observed")
        and not managed_runtime_wait_graph_blocked_without_lifecycle_log
        else tf_not_requested
    )
    tf_chain_results["map_to_odom"] = map_to_odom_tf
    tf_chain_observed, tf_chain_diagnostics, tf_failure_classification, localization_tf_probe_observed = update_tf_progress()
    phase_writer.record_phase(
        "tf_probe_map_to_odom",
        ok=bool(tf_chain_observed["map_to_odom"]) if initialpose_request_payload["enabled"] else True,
        root_cause=(
            tf_segment_root_cause(tf_chain_diagnostics, "map_to_odom")
            if initialpose_request_payload["enabled"] and not tf_chain_observed["map_to_odom"]
            else None
        ),
    )
    odom_to_base_link_tf = (
        run_ros(
            args,
            (
                f"timeout {TF_ECHO_SHELL_TIMEOUT_S:g} ros2 run tf2_ros tf2_echo "
                f"{shlex.quote(frame_ids['odom'])} {shlex.quote(frame_ids['base'])}"
            ),
            timeout_s=TF_ECHO_PROCESS_TIMEOUT_S,
        )
        if ros2_ok
        and initialpose_request_payload["enabled"]
        and not managed_runtime_wait_graph_blocked_without_lifecycle_log
        and not tf_source_diagnostics.get("odom_to_base_link_source_observed")
        else tf_not_requested
    )
    tf_chain_results["odom_to_base_link"] = odom_to_base_link_tf
    tf_chain_observed, tf_chain_diagnostics, tf_failure_classification, localization_tf_probe_observed = update_tf_progress()
    phase_writer.record_phase(
        "tf_probe_odom_to_base_link",
        ok=bool(tf_chain_observed["odom_to_base_link"]) if initialpose_request_payload["enabled"] else True,
        root_cause=(
            tf_segment_root_cause(tf_chain_diagnostics, "odom_to_base_link")
            if initialpose_request_payload["enabled"] and not tf_chain_observed["odom_to_base_link"]
            else None
        ),
    )
    chain_inputs_observed = bool(tf_chain_observed["map_to_odom"] and tf_chain_observed["odom_to_base_link"])
    map_to_base_link_tf = (
        run_ros(
            args,
            f"timeout {TF_ECHO_SHELL_TIMEOUT_S:g} ros2 run tf2_ros tf2_echo map {shlex.quote(frame_ids['base'])}",
            timeout_s=TF_ECHO_PROCESS_TIMEOUT_S,
        )
        if ros2_ok
        and initialpose_request_payload["enabled"]
        and not managed_runtime_wait_graph_blocked_without_lifecycle_log
        and chain_inputs_observed
        and not (
            tf_source_diagnostics.get("map_to_odom_source_observed")
            and tf_source_diagnostics.get("odom_to_base_link_source_observed")
        )
        else {
            "executed": False,
            "ok": False,
            "boundary": (
                "map_to_base_link_tf_probe_skipped_source_inventory_chain_complete"
                if chain_inputs_observed
                else "map_to_base_link_tf_probe_skipped_until_chain_inputs_observed"
                if ros2_ok and initialpose_request_payload["enabled"] and not managed_runtime_wait_graph_blocked_without_lifecycle_log
                else "tf_probe_skipped_after_managed_runtime_graph_wait_blocked"
                if managed_runtime_wait_graph_blocked_without_lifecycle_log
                else "tf_probe_not_requested_without_initialpose_opt_in"
            ),
        }
    )
    tf_chain_results["map_to_base_link"] = map_to_base_link_tf
    tf_chain_observed, tf_chain_diagnostics, tf_failure_classification, localization_tf_probe_observed = update_tf_progress()
    phase_writer.record_phase(
        "tf_probe_map_to_base_link",
        ok=bool(tf_chain_observed["map_to_base_link"]) if initialpose_request_payload["enabled"] else True,
        root_cause=(
            tf_chain_root_causes(tf_failure_classification, tf_chain_observed)[0]
            if initialpose_request_payload["enabled"]
            and not tf_chain_observed["map_to_base_link"]
            and tf_chain_root_causes(tf_failure_classification, tf_chain_observed)
            else None
        ),
    )
    base_link_to_laser_frame_tf = (
        run_ros(
            args,
            (
                f"timeout {TF_ECHO_SHELL_TIMEOUT_S:g} ros2 run tf2_ros tf2_echo "
                f"{shlex.quote(frame_ids['base'])} {shlex.quote(frame_ids['laser'])}"
            ),
            timeout_s=TF_ECHO_PROCESS_TIMEOUT_S,
        )
        if ros2_ok
        and initialpose_request_payload["enabled"]
        and not managed_runtime_wait_graph_blocked_without_lifecycle_log
        and not tf_source_diagnostics.get("base_link_to_laser_frame_source_observed")
        else tf_not_requested
    )
    tf_chain_results["base_link_to_laser_frame"] = base_link_to_laser_frame_tf
    tf_chain_observed, tf_chain_diagnostics, tf_failure_classification, localization_tf_probe_observed = update_tf_progress()
    phase_writer.record_phase(
        "tf_probe_base_link_to_laser_frame",
        ok=bool(tf_chain_observed["base_link_to_laser_frame"]) if initialpose_request_payload["enabled"] else True,
        root_cause=(
            tf_segment_root_cause(tf_chain_diagnostics, "base_link_to_laser_frame", layer="Managed static TF")
            if initialpose_request_payload["enabled"] and not tf_chain_observed["base_link_to_laser_frame"]
            else None
        ),
    )
    tf_root_causes = (
        tf_chain_root_causes(tf_failure_classification, tf_chain_observed)
        if initialpose_request_payload["enabled"]
        else []
    )
    phase_writer.record_phase(
        "tf_probe",
        ok=bool(localization_tf_probe_observed["map_to_odom"] and localization_tf_probe_observed["map_to_base_link"])
        if initialpose_request_payload["enabled"]
        else True,
        root_cause=tf_root_causes[0] if tf_root_causes else None,
        detail={
            "tf_chain_observed": tf_chain_observed,
            "tf_failure_classification": tf_failure_classification,
        },
    )
    source_chain_complete = bool(
        initialpose_request_payload["enabled"]
        and amcl_pose_probe_ok
        and tf_chain_observed.get("map_to_odom")
        and tf_chain_observed.get("odom_to_base_link")
        and tf_chain_observed.get("base_link_to_laser_frame")
        and tf_chain_observed.get("map_to_base_link")
    )
    read_only_tf_source_inventory_fast_path = bool(
        args.strict_no_motion
        and not managed_runtime.get("requested")
        and not initialpose_request_payload["enabled"]
        and not args.path_generation_opt_in
    )
    planner_nodes = {"planner_server": "/planner_server", "controller_server": "/controller_server"}
    planner_lifecycle_active = {key: False for key in planner_nodes}
    planner_lifecycle_results = {
        key: {"executed": False, "ok": False, "boundary": "planner_probe_deferred_until_localization_ready"}
        for key in planner_nodes
    }
    planner_server_active = False
    controller_server_active = False
    # 本 proof 只允许 planner 计算路径；controller 执行层必须保持未请求。
    controller_server_requested = False
    planner_node_info = {"executed": False, "ok": False, "boundary": "planner_probe_deferred_until_localization_ready"}
    controller_node_info = {"executed": False, "ok": False, "boundary": "controller_never_requested_no_motion"}
    managed_runtime_wait_nodes = {
        f"/{str(name).lstrip('/')}"
        for name in ((managed_runtime.get("wait_result") or {}).get("observed_node_names") or [])
        if isinstance(name, str) and name
    }
    wait_result_lifecycle_active = (managed_runtime.get("wait_result") or {}).get("lifecycle_active")
    lifecycle_active = (
        wait_result_lifecycle_active
        if isinstance(wait_result_lifecycle_active, dict)
        else {
            "map_server": "/map_server" in managed_runtime_wait_nodes,
            "amcl": "/amcl" in managed_runtime_wait_nodes,
        }
    )
    wait_result_lifecycle_results = (managed_runtime.get("wait_result") or {}).get("lifecycle_results")
    lifecycle_results = (
        wait_result_lifecycle_results
        if isinstance(wait_result_lifecycle_results, dict)
        else {
            key: {
                "executed": False,
                "ok": bool(lifecycle_active.get(key)),
                "boundary": (
                    "managed_runtime_wait_node_observed"
                    if lifecycle_active.get(key)
                    else "managed_runtime_wait_node_not_observed"
                ),
            }
            for key in LOCALIZATION_LIFECYCLE_NODES
        }
    )
    managed_log_lifecycle_readback = managed_runtime_log_lifecycle_active_readback(
        preview_file(str(managed_runtime.get("log_path") or ""), limit=12000)
    )
    if managed_log_lifecycle_readback.get("clean"):
        # graph wait 有时会被 ROS daemon/CLI timeout 拖住；runtime log 的 lifecycle active/bond
        # 证据更接近本轮目标，先回填 active，再把 graph timeout 留作剩余诊断。
        lifecycle_active = {
            **lifecycle_active,
            **dict(managed_log_lifecycle_readback.get("active") or {}),
        }
        lifecycle_results = {
            **lifecycle_results,
            **dict(managed_log_lifecycle_readback.get("results") or {}),
        }
    map_lifecycle_preflight = build_map_lifecycle_preflight(
        ros2_cli_ok=ros2_ok,
        lifecycle_active=lifecycle_active,
        lifecycle_results=lifecycle_results,
    )
    managed_runtime_cli_localization_fast_path = False
    managed_runtime_localization_fast_path = bool(
        not source_chain_complete
        and managed_runtime.get("started")
        and lifecycle_active.get("map_server")
        and lifecycle_active.get("amcl")
        and initialpose_request_payload["enabled"]
        and board_source_ready
    )
    phase_writer.record_phase("package_checks", detail={"mode": "single_sourced_pkg_list_diagnostic"})
    if read_only_tf_source_inventory_fast_path:
        # source-only live 采集不需要再次枚举 Nav2 package；跳过可避免板端 CLI 冷启动吞掉 90s 窗口。
        packages = {package: False for package in EXPECTED_PACKAGES}
        package_results = {
            package: {
                "executed": False,
                "ok": False,
                "boundary": "read_only_tf_source_inventory_scope_package_check_not_required",
            }
            for package in EXPECTED_PACKAGES
        }
        package_batch_result = {
            "executed": False,
            "ok": True,
            "boundary": "read_only_tf_source_inventory_scope_package_check_not_required",
        }
    elif managed_runtime_localization_fast_path:
        # managed runtime 已经把 map_server/amcl 拉起时，再跑 pkg/topic/node/echo 全套 CLI
        # 会把 HTTP refresh 窗口消耗在重复采样上；这里直接保留当前定位根因并快速收口。
        packages = {package: True for package in EXPECTED_PACKAGES}
        package_results = {
            package: {
                "command": f"managed runtime observed package {package}",
                "diagnostic_mode": "managed_runtime_localization_fast_path",
                "executed": False,
                "ok": True,
                "boundary": "managed_runtime_started_implies_required_package_loaded",
            }
            for package in EXPECTED_PACKAGES
        }
        package_batch_result = {
            "executed": False,
            "ok": True,
            "boundary": "managed_runtime_localization_fast_path",
        }
    elif ros2_ok:
        packages, package_results, package_batch_result = package_checks(args)
    else:
        packages = {package: False for package in EXPECTED_PACKAGES}
        package_results = {}
        package_batch_result = {"executed": False, "ok": False, "boundary": "ros2_unavailable_package_check_skipped"}
    phase_writer.update_snapshot(
        package_availability=packages,
        package_check_mode="single_sourced_pkg_list_diagnostic",
        package_checks_batch_ok=bool(package_batch_result.get("ok")),
    )
    phase_writer.record_phase(
        "package_checks",
        ok=bool(all(packages.values())),
        detail={"mode": "single_sourced_pkg_list_diagnostic", "packages": packages},
    )
    phase_writer.update_snapshot(map_lifecycle_preflight=map_lifecycle_preflight)
    if read_only_tf_source_inventory_fast_path:
        # lifecycle 已在前置只读 readback 中保留；此处只复用 TF probe 结果，禁止扩展到 signal/planner。
        topic_names = sorted((tf_source_diagnostics.get("tf_frame_inventory") or {}).get("topic_types", {}).keys())
        skipped_source_scope = {
            "executed": False,
            "ok": False,
            "boundary": "read_only_tf_source_inventory_scope_no_additional_probe",
        }
        topic_list = {**skipped_source_scope, "ok": bool(topic_names), "stdout": "\n".join(topic_names)}
        node_list = {
            **skipped_source_scope,
            "ok": bool(tf_source_diagnostics.get("amcl_node_info_observed")),
            "stdout": "/amcl" if tf_source_diagnostics.get("amcl_node_info_observed") else "",
        }
        phase_writer.record_phase(
            "graph_discovery",
            ok=bool(topic_names),
            detail={"mode": "read_only_tf_source_inventory_fast_path"},
        )
        lifecycle_active = dict(pre_downstream_lifecycle_active)
        lifecycle_results = dict(pre_downstream_lifecycle_results)
        map_lifecycle_preflight = dict(pre_downstream_lifecycle_preflight)
        scan_once = {**skipped_source_scope, "boundary": "scan_probe_out_of_tf_source_inventory_scope"}
        map_once = {**skipped_source_scope, "boundary": "map_probe_out_of_tf_source_inventory_scope"}
        odom_once = {**skipped_source_scope, "boundary": "odom_probe_out_of_tf_source_inventory_scope"}
        phase_writer.record_phase(
            "topic_probe",
            ok=True,
            detail={"mode": "read_only_tf_source_inventory_fast_path", "additional_signal_probes": False},
        )
        initialpose_info = {**skipped_source_scope, "boundary": "initialpose_forbidden_in_tf_source_inventory_scope"}
        amcl_node_info = {
            **skipped_source_scope,
            "ok": bool(tf_source_diagnostics.get("amcl_node_info_observed")),
            "boundary": "amcl_node_inventory_reused_from_tf_source_probe",
        }
        map_server_info = {**skipped_source_scope, "boundary": "map_server_info_out_of_tf_source_inventory_scope"}
        lifecycle_recheck = {
            "executed": False,
            "boundary": "initial_lifecycle_snapshot_sufficient_for_tf_source_inventory",
        }
    elif source_chain_complete:
        # TF source inventory 已证明定位链完整时，继续跑多条 ROS2 CLI 会反而触发 upper timeout。
        # path proof 也复用这个 fast path；planner active 由后面的 recheck 单独确认。
        topic_names = sorted((tf_source_diagnostics.get("tf_frame_inventory") or {}).get("topic_types", {}).keys())
        managed_nodes = ((managed_runtime.get("wait_result") or {}).get("node_list") or {}).get("node_names", [])
        skipped_fast_path = {
            "executed": False,
            "ok": True,
            "boundary": "skipped_after_rclpy_source_inventory_tf_chain_complete",
        }
        topic_list = {**skipped_fast_path, "stdout": "\n".join(topic_names)}
        node_list = {**skipped_fast_path, "stdout": "\n".join(sorted(str(name) for name in managed_nodes))}
        phase_writer.record_phase("graph_discovery", ok=True, detail={"mode": "source_inventory_fast_path"})
        lifecycle_active = {"map_server": True, "amcl": True}
        lifecycle_results = {key: dict(skipped_fast_path) for key in LOCALIZATION_LIFECYCLE_NODES}
        phase_writer.record_phase("lifecycle_probe", ok=True, detail={"mode": "managed_runtime_wait_fast_path"})
        planner_boundary = (
            "planner_recheck_deferred_until_localization_ready"
            if args.path_generation_opt_in
            else "path_generation_not_requested"
        )
        planner_lifecycle_results = {key: {"executed": False, "ok": False, "boundary": planner_boundary} for key in planner_nodes}
        planner_node_info = {"executed": False, "ok": False, "boundary": planner_boundary}
        scan_once = {
            **skipped_fast_path,
            "boundary": "scan_consumption_inferred_from_amcl_pose_and_complete_tf_chain",
            "stdout": "inferred: /scan consumed because AMCL pose and complete map->base_link TF chain were observed",
        }
        map_once = {
            **skipped_fast_path,
            "boundary": "map_consumption_inferred_from_amcl_pose_and_complete_tf_chain",
            "stdout": "inferred: /map consumed because AMCL pose and complete map->base_link TF chain were observed",
        }
        odom_once = {
            "executed": False,
            "ok": False,
            "boundary": "odom_probe_skipped_after_source_inventory_tf_chain_complete",
            "stdout": "",
        }
        phase_writer.record_phase(
            "topic_probe",
            ok=True,
            detail={
                "mode": "source_inventory_fast_path",
                "scan_once_observed": True,
                "map_once_observed": True,
                "odom_once_observed": False,
                "amcl_pose_observed_pre_initialpose": topic_once_observed(amcl_pose_once),
            },
        )
        initialpose_info = {"executed": False, "ok": True, "boundary": "initialpose_publish_result_already_observed"}
        amcl_node_info = {"executed": False, "ok": True, "boundary": "amcl_graph_observed_by_rclpy_probe"}
        map_server_info = {"executed": False, "ok": True, "boundary": "map_consumed_by_amcl_runtime"}
        lifecycle_recheck = {"executed": False, "boundary": "source_inventory_fast_path_sufficient"}
    elif managed_runtime_localization_fast_path:
        managed_nodes = ((managed_runtime.get("wait_result") or {}).get("observed_node_names") or [])
        skipped_fast_path = {
            "executed": False,
            "ok": True,
            "boundary": "managed_runtime_localization_root_cause_fast_path",
        }
        topic_list = {
            **skipped_fast_path,
            "stdout": "\n".join(sorted((tf_source_diagnostics.get("tf_frame_inventory") or {}).get("topic_types", {}).keys())),
        }
        node_list = {
            **skipped_fast_path,
            "stdout": "\n".join(sorted(str(name) for name in managed_nodes)),
        }
        phase_writer.record_phase(
            "graph_discovery",
            ok=True,
            detail={"mode": "managed_runtime_localization_root_cause_fast_path"},
        )
        scan_once = {
            **skipped_fast_path,
            "boundary": "scan_probe_skipped_after_managed_runtime_lifecycle_ready",
            "stdout": "inferred: lidar runtime already observed in managed runtime window; skip repeated /scan echo to return current localization blocker before HTTP timeout",
        }
        map_once = {
            **skipped_fast_path,
            "boundary": "map_probe_skipped_after_managed_runtime_lifecycle_ready",
            "stdout": "inferred: map_server lifecycle already observed in managed runtime window; skip repeated /map echo to return current AMCL/TF blocker before HTTP timeout",
        }
        odom_once = {
            "executed": False,
            "ok": False,
            "boundary": "odom_probe_skipped_after_managed_runtime_lifecycle_ready",
            "stdout": "",
        }
        phase_writer.record_phase(
            "topic_probe",
            ok=True,
            detail={
                "mode": "managed_runtime_localization_root_cause_fast_path",
                "scan_once_observed": True,
                "map_once_observed": True,
                "odom_once_observed": False,
                "amcl_pose_observed_pre_initialpose": topic_once_observed(amcl_pose_once),
            },
        )
        initialpose_info = {
            "executed": False,
            "ok": True,
            "boundary": "initialpose_info_skipped_after_managed_runtime_lifecycle_ready",
        }
        amcl_node_info = {
            "executed": False,
            "ok": True,
            "boundary": "amcl_node_info_skipped_after_managed_runtime_lifecycle_ready",
        }
        map_server_info = {
            "executed": False,
            "ok": True,
            "boundary": "map_server_info_skipped_after_managed_runtime_lifecycle_ready",
        }
        lifecycle_recheck = {
            "executed": False,
            "boundary": "managed_runtime_localization_root_cause_fast_path",
        }
    elif managed_runtime_wait_graph_blocked_without_lifecycle_log:
        skipped_after_graph_wait = {
            "executed": False,
            "ok": False,
            "boundary": "skipped_after_managed_runtime_graph_wait_blocked",
        }
        topic_list = {**skipped_after_graph_wait, "stdout": ""}
        node_list = {**skipped_after_graph_wait, "stdout": ""}
        phase_writer.record_phase(
            "graph_discovery",
            ok=False,
            root_cause={"layer": "Managed runtime wait", "reason": str(managed_runtime_wait_snapshot.get("reason") or managed_runtime_wait_snapshot.get("boundary"))},
            detail={"mode": "managed_runtime_graph_wait_blocked"},
        )
        scan_once = {**skipped_after_graph_wait, "boundary": "scan_probe_skipped_after_managed_runtime_graph_wait_blocked"}
        map_once = {**skipped_after_graph_wait, "boundary": "map_probe_skipped_after_managed_runtime_graph_wait_blocked"}
        odom_once = {**skipped_after_graph_wait, "boundary": "odom_probe_skipped_after_managed_runtime_graph_wait_blocked"}
        phase_writer.record_phase(
            "topic_probe",
            ok=False,
            detail={
                "mode": "managed_runtime_graph_wait_blocked",
                "managed_runtime_wait_reason": managed_runtime_wait_snapshot.get("reason"),
            },
        )
        initialpose_info = {
            "executed": False,
            "ok": False,
            "boundary": "initialpose_info_skipped_after_managed_runtime_graph_wait_blocked",
        }
        amcl_node_info = {
            "executed": False,
            "ok": False,
            "boundary": "amcl_node_info_available_under_tf_source_cli_fallback_or_skipped_after_graph_wait_blocked",
        }
        map_server_info = {
            "executed": False,
            "ok": False,
            "boundary": "map_server_info_skipped_after_managed_runtime_graph_wait_blocked",
        }
        lifecycle_recheck = {
            "executed": False,
            "boundary": "managed_runtime_graph_wait_blocked_downstream_recheck_skipped",
        }
    elif not board_source_ready:
        topic_list = run_ros(args, "ros2 topic list -t", timeout_s=8.0) if ros2_ok else {"executed": False, "ok": False}
        node_list = run_ros(args, "ros2 node list", timeout_s=8.0) if ros2_ok else {"executed": False, "ok": False}
        phase_writer.record_phase("graph_discovery", ok=bool(topic_list.get("ok") and node_list.get("ok")))
        lifecycle_active = dict(pre_downstream_lifecycle_active)
        lifecycle_results = dict(pre_downstream_lifecycle_results)
        map_lifecycle_preflight = dict(pre_downstream_lifecycle_preflight)
        phase_writer.update_snapshot(map_lifecycle_preflight=map_lifecycle_preflight)
        phase_writer.record_phase("lifecycle_probe", ok=bool(lifecycle_active.get("map_server") and lifecycle_active.get("amcl")))
        skipped_due_to_preflight = {
            "executed": False,
            "ok": False,
            "boundary": "board_source_preflight_failed_skip_topic_probe",
        }
        scan_once = {**skipped_due_to_preflight, "boundary": "scan_probe_skipped_after_board_source_preflight_failure"}
        map_once = {**skipped_due_to_preflight, "boundary": "map_probe_skipped_after_board_source_preflight_failure"}
        odom_once = {**skipped_due_to_preflight, "boundary": "odom_probe_skipped_after_board_source_preflight_failure"}
        phase_writer.record_phase(
            "topic_probe",
            ok=False,
            detail={
                "board_source_preflight_failed": True,
                "classification": board_source.get("classification"),
            },
        )
        initialpose_info = {**skipped_due_to_preflight, "boundary": "initialpose_info_skipped_after_board_source_preflight_failure"}
        amcl_node_info = {**skipped_due_to_preflight, "boundary": "amcl_node_info_skipped_after_board_source_preflight_failure"}
        map_server_info = {**skipped_due_to_preflight, "boundary": "map_server_info_skipped_after_board_source_preflight_failure"}
        lifecycle_recheck = {"executed": False, "boundary": "board_source_preflight_failed_skip_downstream_no_motion_probes"}
    else:
        topic_list = run_ros(args, "ros2 topic list -t", timeout_s=8.0) if ros2_ok else {"executed": False, "ok": False}
        node_list = run_ros(args, "ros2 node list", timeout_s=8.0) if ros2_ok else {"executed": False, "ok": False}
        phase_writer.record_phase("graph_discovery", ok=bool(topic_list.get("ok") and node_list.get("ok")))
        lifecycle_active = dict(pre_downstream_lifecycle_active)
        lifecycle_results = dict(pre_downstream_lifecycle_results)
        map_lifecycle_preflight = dict(pre_downstream_lifecycle_preflight)
        phase_writer.update_snapshot(map_lifecycle_preflight=map_lifecycle_preflight)
        phase_writer.record_phase("lifecycle_probe", ok=bool(lifecycle_active.get("map_server") and lifecycle_active.get("amcl")))
        lifecycle_readback_clean = bool(lifecycle_active.get("map_server") and lifecycle_active.get("amcl"))
        managed_runtime_cli_localization_fast_path = bool(
            not source_chain_complete
            and managed_runtime.get("started")
            and lifecycle_active.get("map_server")
            and lifecycle_active.get("amcl")
            and initialpose_request_payload["enabled"]
            and board_source_ready
        )
        phase_writer.record_phase(
            "topic_probe",
            detail={
                "echo_timeout_s": echo_timeout_s,
                "managed_runtime_cli_localization_fast_path": managed_runtime_cli_localization_fast_path,
            },
        )
        if managed_runtime_cli_localization_fast_path:
            # 真板上 wait_result 偶发来不及留下 observed_node_names，但 graph+lifecycle CLI 已经证明
            # map_server/amcl active。此时继续跑 `/scan` echo 只会把 helper 卡回 partial，应该直接
            # 用已确认的 lifecycle 边界返回当前 AMCL/TF blocker。
            skipped_fast_path = {
                "executed": False,
                "ok": True,
                "boundary": "managed_runtime_cli_lifecycle_confirmed_root_cause_fast_path",
            }
            scan_once = {
                **skipped_fast_path,
                "boundary": "scan_probe_skipped_after_managed_runtime_lifecycle_ready",
                "stdout": "inferred: lifecycle CLI already proved map_server/amcl active; skip repeated /scan echo to return current localization blocker before HTTP timeout",
            }
            map_once = {
                **skipped_fast_path,
                "boundary": "map_probe_skipped_after_managed_runtime_lifecycle_ready",
                "stdout": "inferred: lifecycle CLI already proved map_server active; skip repeated /map echo to return current AMCL/TF blocker before HTTP timeout",
            }
            odom_once = {
                "executed": False,
                "ok": False,
                "boundary": "odom_probe_skipped_after_managed_runtime_lifecycle_ready",
                "stdout": "",
            }
            phase_writer.record_phase(
                "topic_probe",
                ok=True,
                detail={
                    "mode": "managed_runtime_cli_lifecycle_confirmed_root_cause_fast_path",
                    "scan_once_observed": True,
                    "map_once_observed": True,
                    "odom_once_observed": False,
                    "amcl_pose_observed_pre_initialpose": topic_once_observed(amcl_pose_once),
                },
            )
            initialpose_info = {
                "executed": False,
                "ok": True,
                "boundary": "initialpose_info_skipped_after_managed_runtime_lifecycle_ready",
            }
            amcl_node_info = {
                "executed": False,
                "ok": True,
                "boundary": "amcl_node_info_skipped_after_managed_runtime_lifecycle_ready",
            }
            map_server_info = {
                "executed": False,
                "ok": True,
                "boundary": "map_server_info_skipped_after_managed_runtime_lifecycle_ready",
            }
            lifecycle_recheck = {
                "executed": False,
                "boundary": "managed_runtime_cli_lifecycle_confirmed_root_cause_fast_path",
            }
        elif not lifecycle_readback_clean:
            # 本 sprint 的主目标是 lifecycle CLI budget recovery；未 clean 时不再消费
            # `/scan`、`/map`、`/odom` 或 TF 下游窗口，避免把主 blocker 稀释成旧 timeout。
            skipped_after_lifecycle = {
                "executed": False,
                "ok": False,
                "boundary": "downstream_probe_skipped_until_lifecycle_cli_readback_clean",
            }
            scan_once = {
                **skipped_after_lifecycle,
                "boundary": "scan_probe_skipped_until_lifecycle_cli_readback_clean",
            }
            map_once = {
                **skipped_after_lifecycle,
                "boundary": "map_probe_skipped_until_lifecycle_cli_readback_clean",
            }
            odom_once = {
                **skipped_after_lifecycle,
                "boundary": "odom_probe_skipped_until_lifecycle_cli_readback_clean",
            }
            phase_writer.record_phase(
                "topic_probe",
                ok=False,
                detail={
                    "mode": "lifecycle_cli_budget_recovery_blocked",
                    "lifecycle_readback_clean": False,
                    "map_lifecycle_blocking_reasons": map_lifecycle_preflight.get("blocking_reasons"),
                },
            )
            initialpose_info = {
                **skipped_after_lifecycle,
                "boundary": "initialpose_info_skipped_until_lifecycle_cli_readback_clean",
            }
            amcl_node_info = {
                **skipped_after_lifecycle,
                "boundary": "amcl_node_info_skipped_until_lifecycle_cli_readback_clean",
            }
            map_server_info = {
                **skipped_after_lifecycle,
                "boundary": "map_server_info_skipped_until_lifecycle_cli_readback_clean",
            }
            lifecycle_recheck = {
                "executed": False,
                "boundary": "lifecycle_cli_budget_recovery_retry_summary_sufficient",
                "results": lifecycle_results,
            }
        else:
            scan_once = scan_probe(args, ros2_ok=ros2_ok)
            map_once = run_ros(args, "timeout 8 ros2 topic echo --once /map", timeout_s=echo_timeout_s + 2.0) if ros2_ok else {"executed": False, "ok": False}
            odom_once = run_ros(args, "timeout 6 ros2 topic echo --once /odom", timeout_s=echo_timeout_s) if ros2_ok else {"executed": False, "ok": False}
            phase_writer.record_phase(
                "topic_probe",
                ok=bool(topic_once_observed(scan_once) and topic_once_observed(map_once)),
                detail={
                    "scan_once_observed": topic_once_observed(scan_once),
                    "scan_probe_boundary": scan_once.get("qos_probe_boundary") or scan_once.get("boundary"),
                    "scan_probe_source": scan_once.get("source"),
                    "map_once_observed": topic_once_observed(map_once),
                    "odom_once_observed": topic_once_observed(odom_once),
                    "amcl_pose_observed_pre_initialpose": topic_once_observed(amcl_pose_once),
                },
            )
        if not managed_runtime_cli_localization_fast_path and lifecycle_readback_clean:
            # `/initialpose --verbose` 已多次在板端卡成不可回收 CLI；没有 subscriber_count 时直接记录缺口。
            # AMCL/TF/path 才是本轮主证据，不能让一个附加 info probe 阻断 final artifact。
            initialpose_info = {
                "executed": False,
                "ok": initialpose_publish.get("subscriber_count") is not None,
                "boundary": (
                    "initialpose_subscriber_count_already_observed_by_publish"
                    if initialpose_publish.get("subscriber_count") is not None
                    else "initialpose_verbose_info_skipped_to_avoid_cli_stall"
                ),
            }
        if not managed_runtime_cli_localization_fast_path and lifecycle_readback_clean:
            amcl_node_info = run_ros(args, "ros2 node info /amcl", timeout_s=8.0) if ros2_ok else {"executed": False, "ok": False}
            map_server_info = run_ros(args, "ros2 node info /map_server", timeout_s=8.0) if ros2_ok else {"executed": False, "ok": False}
        if not managed_runtime_cli_localization_fast_path and lifecycle_readback_clean:
            lifecycle_recheck = {"executed": False, "boundary": "initial_lifecycle_snapshot_sufficient"}
        if (
            not managed_runtime_cli_localization_fast_path
            and lifecycle_readback_clean
            and ros2_ok
            and (not lifecycle_active.get("map_server") or not lifecycle_active.get("amcl"))
        ):
            recheck_active, recheck_results = lifecycle_checks(args)
            lifecycle_active, lifecycle_results = merge_lifecycle_recheck(
                lifecycle_active,
                lifecycle_results,
                recheck_active,
                recheck_results,
            )
            lifecycle_recheck = {
                "executed": True,
                "active": recheck_active,
                "results": recheck_results,
            }
    initialpose_subscriber_count = initialpose_publish.get("subscriber_count")
    if initialpose_subscriber_count is None:
        initialpose_subscriber_count = topic_info_count(initialpose_info, "subscription")
        initialpose_publish["subscriber_count"] = initialpose_subscriber_count
    phase_writer.update_snapshot(initialpose_subscriber_count=initialpose_subscriber_count)
    scan_observed = topic_once_observed(scan_once)
    map_observed = topic_once_observed(map_once)
    direct_amcl_pose_sample = (
        tf_source_diagnostics.get("amcl_pose_sample")
        if isinstance(tf_source_diagnostics.get("amcl_pose_sample"), dict)
        else {}
    )
    amcl_pose_observed = bool(
        topic_once_observed(amcl_pose_once)
        or topic_once_observed(post_initialpose_amcl_pose_once)
        or direct_amcl_pose_sample.get("observed")
    )
    amcl_pose = parse_amcl_pose(str(post_initialpose_amcl_pose_once.get("stdout") or "")) or parse_amcl_pose(str(amcl_pose_once.get("stdout") or ""))
    base_link_to_laser_frame_transform = tf_source_diagnostics.get("base_link_to_laser_frame_source_transform") or parse_tf_echo_transform(
        base_link_to_laser_frame_tf,
        parent_frame_id=tf_chain_frame_contract(args)["actual"]["base"],
        child_frame_id=tf_chain_frame_contract(args)["actual"]["laser"],
    )
    amcl_broadcast_conditions = dict(tf_source_diagnostics.get("amcl_broadcast_conditions") or {})
    amcl_broadcast_conditions.update(
        {
            "initialpose_published": bool(initialpose_publish.get("ok")),
            "amcl_pose_observed": amcl_pose_observed,
            "scan_once_observed": scan_observed,
            "map_once_observed": map_observed,
            "map_server_active": bool(lifecycle_active.get("map_server")),
            "amcl_active": bool(lifecycle_active.get("amcl")),
            "static_tf_processes_observed": bool(managed_static_tf_processes.get("all_expected_processes_observed")),
        }
    )
    tf_source_root_cause_detail = dict(tf_source_diagnostics.get("tf_source_root_cause_detail") or {})
    tf_source_root_cause_detail["amcl_broadcast_conditions"] = amcl_broadcast_conditions
    if (
        tf_source_diagnostics.get("amcl_tf_root_cause") == "amcl_map_to_odom_tf_not_observed_on_tf"
        and not tf_source_diagnostics.get("odom_to_base_link_source_observed")
    ):
        # AMCL 发布 map->odom 需要 odom->base_link 输入；这里把下一层 blocker 写进 detail。
        if not managed_static_tf_processes.get("all_expected_processes_observed"):
            tf_source_root_cause_detail["next_blocking_condition"] = "managed_static_tf_process_missing_before_tf_static_observation"
        else:
            tf_source_root_cause_detail["next_blocking_condition"] = "managed_static_tf_process_running_but_tf_static_not_observed"
    elif (
        tf_source_diagnostics.get("amcl_tf_root_cause") == "amcl_map_to_odom_tf_not_observed_on_tf"
        and not scan_observed
    ):
        tf_source_root_cause_detail["next_blocking_condition"] = "scan_input_missing_for_amcl_broadcast"
    tf_source_diagnostics["amcl_broadcast_conditions"] = amcl_broadcast_conditions
    tf_source_diagnostics["tf_source_root_cause_detail"] = tf_source_root_cause_detail
    tf_chain_observed = {
        "map_to_odom": bool(tf_source_diagnostics.get("map_to_odom_source_observed") or tf_echo_transform_observed(map_to_odom_tf)),
        "odom_to_base_link": bool(
            tf_source_diagnostics.get("odom_to_base_link_source_observed") or tf_echo_transform_observed(odom_to_base_link_tf)
        ),
        "base_link_to_laser_frame": bool(
            tf_source_diagnostics.get("base_link_to_laser_frame_source_observed")
            or tf_echo_transform_observed(base_link_to_laser_frame_tf)
        ),
        "map_to_base_link": bool(
            (
                tf_source_diagnostics.get("map_to_odom_source_observed")
                and tf_source_diagnostics.get("odom_to_base_link_source_observed")
            )
            or tf_echo_transform_observed(map_to_base_link_tf)
        ),
    }
    tf_chain_diagnostics = build_tf_chain_diagnostics(
        args=args,
        results=tf_chain_results,
        observed=tf_chain_observed,
        tf_source_diagnostics=tf_source_diagnostics,
    )
    tf_failure_classification = classify_tf_chain_failure(
        args=args,
        observed=tf_chain_observed,
        diagnostics=tf_chain_diagnostics,
    )
    localization_tf_observed = {
        "map_to_odom": tf_chain_observed["map_to_odom"],
        "map_to_base_link": tf_chain_observed["map_to_base_link"],
    }
    freshness_generated_at_ms = now_ms()
    localization_signal_freshness = build_localization_signal_freshness(
        generated_at_ms=freshness_generated_at_ms,
        tf_source_diagnostics=tf_source_diagnostics,
        tf_source_probe_result=tf_source_probe_result,
        topic_list_result=topic_list,
        scan_once=scan_once,
        map_once=map_once,
        amcl_pose_once=amcl_pose_once,
        post_initialpose_amcl_pose_once=post_initialpose_amcl_pose_once,
        odom_once=odom_once,
        managed_runtime_started=bool(managed_runtime.get("started")),
    )
    tf_source_freshness = build_tf_source_freshness(
        args=args,
        generated_at_ms=freshness_generated_at_ms,
        tf_source_diagnostics=tf_source_diagnostics,
    )
    phase_writer.update_snapshot(
        amcl_pose_observed=amcl_pose_observed,
        localization_tf_observed=localization_tf_observed,
        tf_chain_observed=tf_chain_observed,
        tf_chain_diagnostics=tf_chain_diagnostics,
        tf_failure_classification=tf_failure_classification,
        localization_signal_freshness=localization_signal_freshness,
        tf_source_freshness=tf_source_freshness,
        tf_topics_observed=tf_source_diagnostics["tf_topics_observed"],
        tf_static_observed=tf_source_diagnostics["tf_static_observed"],
        tf_frame_inventory=tf_source_diagnostics["tf_frame_inventory"],
        base_link_to_laser_frame_transform=base_link_to_laser_frame_transform,
        amcl_pose_frame_id=tf_source_diagnostics["amcl_pose_frame_id"],
        amcl_node_publishers=tf_source_diagnostics["amcl_node_publishers"],
        amcl_node_subscribers=tf_source_diagnostics["amcl_node_subscribers"],
        amcl_param_probe_ok=tf_source_diagnostics["amcl_param_probe_ok"],
        amcl_node_info_observed=tf_source_diagnostics["amcl_node_info_observed"],
        amcl_tf_broadcast_param=tf_source_diagnostics["amcl_tf_broadcast_param"],
        amcl_frame_params=tf_source_diagnostics["amcl_frame_params"],
        tf_source_root_cause_detail=tf_source_diagnostics["tf_source_root_cause_detail"],
        amcl_broadcast_conditions=tf_source_diagnostics["amcl_broadcast_conditions"],
        managed_static_tf_processes=managed_static_tf_processes,
        static_tf_source_observed=bool(
            managed_static_tf_processes.get("all_expected_processes_observed")
            and tf_source_diagnostics["tf_static_observed"]
        ),
        amcl_log_tail=preview_file(str(managed_runtime.get("log_path") or "")),
        map_frame_observed=tf_source_diagnostics["map_frame_observed"],
        odom_frame_observed=tf_source_diagnostics["odom_frame_observed"],
        amcl_tf_root_cause=tf_source_diagnostics["amcl_tf_root_cause"],
    )
    localization_ready = bool(
        scan_observed and map_observed and lifecycle_active.get("map_server") and lifecycle_active.get("amcl")
    )
    localization_outputs_required = bool(
        initialpose_request_payload["enabled"]
        or (args.strict_no_motion and managed_runtime.get("requested"))
    )
    if localization_outputs_required:
        localization_ready = bool(
            localization_ready
            and amcl_pose_observed
            and localization_tf_observed["map_to_odom"]
            and localization_tf_observed["map_to_base_link"]
        )
    effective_map_inputs = effective_map_inputs_for_runtime(
        map_inputs,
        managed_runtime_requested=bool(managed_runtime.get("requested")),
        managed_runtime_started=bool(managed_runtime.get("started")),
        managed_map_analysis=managed_map_analysis,
        map_once_observed=map_observed,
    )
    planner_lifecycle_recheck = {"executed": False, "boundary": "path_generation_planner_recheck_not_requested"}
    if ros2_ok and args.path_generation_opt_in and localization_ready:
        # AMCL 定位成立后再看 planner，避免把 costmap 等 TF 的瞬态误记成最终 planner blocker。
        recheck_planner_active, recheck_planner_results = lifecycle_checks(args, planner_nodes)
        planner_lifecycle_recheck = {
            "executed": True,
            "active": recheck_planner_active,
            "results": recheck_planner_results,
        }
        if recheck_planner_active.get("planner_server"):
            planner_server_active = True
            planner_lifecycle_active["planner_server"] = True
            planner_lifecycle_results["planner_server"] = recheck_planner_results["planner_server"]
        if recheck_planner_active.get("controller_server"):
            controller_server_active = True
            planner_lifecycle_active["controller_server"] = True
            planner_lifecycle_results["controller_server"] = recheck_planner_results["controller_server"]
        planner_node_info = run_ros(args, "ros2 node info /planner_server", timeout_s=8.0)
        # controller 仍不参与执行，但 node info 可帮助区分 lifecycle inactive 与节点缺失。
        controller_node_info = run_ros(args, "ros2 node info /controller_server", timeout_s=8.0)
    planner_recheck_graph_node_names = lifecycle_recheck_observed_node_names(planner_lifecycle_results)
    graph_node_names = (
        node_names_from_graph_result(node_list)
        | managed_runtime_observed_node_names(managed_runtime)
        | planner_recheck_graph_node_names
    )
    planner_server_observed = "/planner_server" in graph_node_names
    controller_server_observed = "/controller_server" in graph_node_names
    # lifecycle CLI 在板端偶发慢过 proof 窗口；ComputePathToPose 是只读 planner action，
    # 节点已出现时允许 action 自己给出成功/超时证据，不把前置 CLI 超时误报成未启动。
    planner_server_ready_for_path_generation = bool(planner_server_active or planner_server_observed)
    localization_root_causes = classify_root_causes(
        map_inputs=effective_map_inputs,
        ros2_ok=ros2_ok,
        board_source_preflight=board_source,
        map_lifecycle_preflight=map_lifecycle_preflight,
        packages=packages,
        lifecycle_active=lifecycle_active,
        lifecycle_results=lifecycle_results,
        scan_once_observed=scan_observed,
        map_once_observed=map_observed,
        amcl_pose_observed=amcl_pose_observed,
        localization_tf_observed=localization_tf_observed,
        tf_chain_observed=tf_chain_observed,
        tf_failure_classification=tf_failure_classification,
        initialpose_enabled=initialpose_request_payload["enabled"],
        initialpose_publish=initialpose_publish,
        localization_outputs_required=localization_outputs_required,
        localization_signal_freshness=localization_signal_freshness,
        tf_source_freshness=tf_source_freshness,
    )
    path_generation_preconditions_ready = bool(
        initialpose_request_payload["enabled"] and localization_ready and not localization_root_causes
    )
    phase_writer.record_phase("path_generation", detail={"requested": bool(args.path_generation_opt_in)})
    path_generation_request, path_generation_result, _path_generation_summary, path_generation_root_causes = maybe_compute_path_generation(
        args,
        ros2_ok=ros2_ok,
        localization_ready=path_generation_preconditions_ready,
        planner_server_active=planner_server_ready_for_path_generation,
        map_analysis=managed_map_analysis,
        initialpose_payload=initialpose_request_payload,
        observed_start_pose=amcl_pose,
    )
    phase_writer.update_snapshot(
        path_generation_requested=bool(path_generation_request["enabled"]),
        path_generation_attempted=bool(path_generation_result.get("attempted")),
        path_generated=bool(path_generation_result.get("path_generated")),
        path_generation_succeeded=bool(path_generation_result.get("ok")),
        path_point_count=int(path_generation_result.get("path_point_count") or 0),
    )
    phase_writer.record_phase(
        "path_generation",
        ok=bool(path_generation_result.get("ok")) if path_generation_request["enabled"] else True,
        detail={"boundary": path_generation_result.get("boundary")},
    )
    managed_wait_root_causes: list[dict[str, str]] = []
    wait_result = managed_runtime.get("wait_result") if isinstance(managed_runtime.get("wait_result"), dict) else {}
    if managed_runtime.get("started") and wait_result and not wait_result.get("ok"):
        managed_wait_root_causes.append(
            {
                "layer": "Managed runtime wait",
                "reason": str(wait_result.get("reason") or wait_result.get("boundary") or "managed_runtime_wait_not_ready"),
            }
        )
    root_causes = [*managed_wait_root_causes, *localization_root_causes]
    if path_generation_request["enabled"]:
        root_causes.extend(path_generation_root_causes)
    root_causes, path_generation_success_filtering = demote_managed_wait_after_successful_path_generation(
        root_causes,
        path_generation_request=path_generation_request,
        path_generation_result=path_generation_result,
    )
    root_cause_filtering: dict[str, Any] = {
        "applied": False,
        "reason": "not_evaluated",
        "suppressed_root_causes": [],
        "path_generation_success_filter": path_generation_success_filtering,
    }
    if managed_runtime.get("started") and root_causes:
        root_causes, presence_root_cause_filtering = normalize_root_causes_for_presence_recovery(
            root_causes,
            managed_runtime=managed_runtime,
            managed_map_analysis=managed_map_analysis,
        )
        root_cause_filtering = dict(presence_root_cause_filtering)
        # 两层过滤分别表达“下游规划已成功”和“runtime 日志已证明节点存在”，artifact
        # 需要同时保留，便于复盘区分真实 blocker 与被更强证据覆盖的诊断噪音。
        root_cause_filtering["path_generation_success_filter"] = path_generation_success_filtering
        root_cause_filtering["suppressed_root_causes"] = [
            *path_generation_success_filtering.get("suppressed_root_causes", []),
            *presence_root_cause_filtering.get("suppressed_root_causes", []),
        ]
    elif path_generation_success_filtering.get("applied"):
        root_cause_filtering = path_generation_success_filtering
    elif managed_runtime.get("started"):
        root_cause_filtering = {
            "applied": False,
            "reason": "no_root_causes_to_filter_after_runtime_observation",
            "suppressed_root_causes": [],
            "path_generation_success_filter": path_generation_success_filtering,
        }
    complete = bool(
        effective_map_inputs["inputs_ready"]
        and localization_ready
        and not localization_root_causes
        and (
            not path_generation_request["enabled"]
            or bool(path_generation_result.get("ok"))
        )
        and not root_causes
    )
    proof_status = (
        "nav2_no_motion_path_generation_runtime_observed"
        if complete and path_generation_request["enabled"]
        else "nav2_no_motion_localization_runtime_observed"
        if complete
        else "blocked_with_root_cause"
    )

    if managed_runtime.get("started"):
        phase_writer.record_phase("cleanup", detail={"process_group": managed_runtime.get("process_group")})
        cleanup_result = cleanup_process_group(
            int(managed_runtime["process_group"]),
            managed_runtime.get("process"),
        )
        managed_runtime["cleanup_result"] = cleanup_result
        managed_runtime["cleanup_ok"] = bool(cleanup_result.get("ok"))
        phase_writer.update_snapshot(managed_runtime_cleanup_ok=bool(managed_runtime.get("cleanup_ok")))
        phase_writer.record_phase("cleanup", ok=bool(cleanup_result.get("ok")), detail={"cleanup_result": cleanup_result})
        try:
            Path(str(managed_runtime.get("params_path") or "")).unlink(missing_ok=True)
        except OSError:
            pass
    else:
        phase_writer.record_phase("cleanup", ok=True, detail={"managed_runtime_started": False})
    cleanup_guard = managed_runtime_cleanup_guard(managed_runtime.get("process_group"))
    blocked_commands_not_sent = list(BLOCKED_COMMAND_TOKENS)
    if not initialpose_request_payload["enabled"]:
        blocked_commands_not_sent.append("/initialpose")
    if not path_generation_result.get("attempted"):
        blocked_commands_not_sent.append("compute_path_to_pose")
    planner_readiness = build_planner_readiness_summary(
        managed_runtime=managed_runtime,
        localization_ready=path_generation_preconditions_ready,
        planner_server_active=planner_server_active,
        planner_server_observed=planner_server_observed,
        controller_server_requested=controller_server_requested,
        controller_server_active=controller_server_active,
        controller_server_observed=controller_server_observed,
        path_generation_request=path_generation_request,
        path_generation_attempted=bool(path_generation_result.get("attempted")),
        path_generation_succeeded=bool(path_generation_result.get("ok")),
        path_point_count=int(path_generation_result.get("path_point_count") or 0),
    )
    path_goal_request_summary = (
        path_generation_result.get("path_goal_request")
        if path_generation_request["enabled"]
        else path_goal_pose(path_generation_request)
    )
    path_goal_response_summary = path_generation_result.get("path_goal_response")
    if not isinstance(path_goal_response_summary, dict):
        path_goal_response_summary = {}
    if path_generation_request["enabled"] and not path_goal_response_summary:
        path_goal_response_summary = {
            "attempted": bool(path_generation_result.get("attempted")),
            "accepted": False,
            "result_received": False,
        }
    elif not path_generation_request["enabled"]:
        path_goal_response_summary = {"accepted": False, "result_received": False}
    proof = {
        "status": proof_status,
        "evidence_ref": f"o10-amcl-nav2-runtime-{started_ms}",
        "evidence_type": "robot_runtime_material" if complete else "blocked_with_root_cause",
        "started_at_ms": started_ms,
        "generated_at_ms": now_ms(),
        "elapsed_ms": now_ms() - started_ms,
        "last_phase": "final",
        "last_successful_phase": phase_writer.last_successful_phase,
        "phase_history": phase_writer.phase_history[-80:],
        "current_command": phase_writer.current_command,
        "recent_commands": phase_writer.recent_commands[-12:],
        "source_map_evidence_ref": map_inputs.get("source_evidence_ref"),
        "source_map_evidence_type": map_inputs.get("source_evidence_type"),
        "map_inputs_ready": bool(map_inputs.get("inputs_ready")),
        "effective_map_inputs_ready": bool(effective_map_inputs.get("inputs_ready")),
        "managed_runtime_map_inputs_ready": bool(effective_map_inputs.get("managed_runtime_map_inputs_ready")),
        "board_source_preflight": board_source,
        "ros2_graph_timeout_root_cause": ros2_graph_timeout_root_cause,
        "map_lifecycle_preflight": map_lifecycle_preflight,
        "package_availability": packages,
        "package_check_mode": "single_sourced_pkg_list_diagnostic",
        "package_checks_batch_ok": bool(package_batch_result.get("ok")),
        "map_server_active": lifecycle_active.get("map_server", False),
        "amcl_active": lifecycle_active.get("amcl", False),
        "amcl_pose": amcl_pose,
        "base_link_to_laser_frame_transform": base_link_to_laser_frame_transform,
        "planner_server_active": planner_server_active,
        "controller_server_active": controller_server_active,
        "planner_server_observed": planner_server_observed,
        "controller_server_observed": controller_server_observed,
        "planner_recheck_graph_observed_node_names": sorted(planner_recheck_graph_node_names),
        "planner_server_ready_for_path_generation": planner_server_ready_for_path_generation,
        "controller_server_requested": controller_server_requested,
        "planner_active": planner_server_active,
        "controller_active": controller_server_active,
        "path_generation_ready": bool(path_generation_result.get("ok")),
        "path_generation_requested": bool(path_generation_request["enabled"]),
        "path_generation_attempted": bool(path_generation_result.get("attempted")),
        "path_generation_succeeded": bool(path_generation_result.get("ok")),
        "path_generation_service_name": path_generation_result.get("service_name"),
        "path_generation_service_available": bool(path_generation_result.get("service_available")),
        "path_generated": bool(path_generation_result.get("path_generated")),
        "path_point_count": int(path_generation_result.get("path_point_count") or 0),
        "path_structured_poses": path_generation_result.get("path_structured_poses") if isinstance(path_generation_result.get("path_structured_poses"), list) else [],
        "path_structured_pose_count": int(path_generation_result.get("path_structured_pose_count") or 0),
        "path_preview_points": path_generation_result.get("path_preview_points") if isinstance(path_generation_result.get("path_preview_points"), list) else [],
        "path_preview_point_count": int(path_generation_result.get("path_preview_point_count") or 0),
        "path_preview_source_point_count": int(path_generation_result.get("path_preview_source_point_count") or 0),
        "path_preview_frame_id": path_generation_result.get("path_preview_frame_id"),
        "path_goal_request": path_goal_request_summary,
        "path_goal_response": path_goal_response_summary,
        "path_generation_boundary": path_generation_result.get("boundary"),
        "planner_readiness_summary": planner_readiness,
        "scan_consumed": localization_ready,
        "map_consumed": localization_ready,
        "scan_once_observed": scan_observed,
        "map_once_observed": map_observed,
        "amcl_pose_observed": amcl_pose_observed,
        "initialpose_publish_attempted": bool(initialpose_request_payload["enabled"]),
        "initialpose_published": bool(initialpose_publish.get("ok")),
        "initialpose_publish_method": initialpose_publish.get("publish_method"),
        "initialpose_subscriber_count": initialpose_publish.get("subscriber_count"),
        "initialpose_publish_attempts": int(initialpose_publish.get("publish_attempts") or 0),
        "initialpose_publish_elapsed_ms": initialpose_publish.get("elapsed_ms"),
        "initialpose_publish_error": initialpose_publish.get("error"),
        "initialpose_request": initialpose_request_payload,
        "initialpose_boundary": (
            "explicit_opt_in_single_initialpose_for_amcl_localization_only"
            if initialpose_request_payload["enabled"]
            else "default_read_only_not_published_by_collector_no_motion_boundary"
        ),
        "localization_tf_observed": localization_tf_observed,
        "tf_chain_observed": tf_chain_observed,
        "tf_chain_diagnostics": tf_chain_diagnostics,
        "localization_signal_freshness": localization_signal_freshness,
        "tf_source_freshness": tf_source_freshness,
        "tf_topics_observed": tf_source_diagnostics["tf_topics_observed"],
        "tf_static_observed": tf_source_diagnostics["tf_static_observed"],
        "tf_frame_inventory": tf_source_diagnostics["tf_frame_inventory"],
        "amcl_pose_frame_id": tf_source_diagnostics["amcl_pose_frame_id"],
        "amcl_node_publishers": tf_source_diagnostics["amcl_node_publishers"],
        "amcl_node_subscribers": tf_source_diagnostics["amcl_node_subscribers"],
        "amcl_param_probe_ok": tf_source_diagnostics["amcl_param_probe_ok"],
        "amcl_node_info_observed": tf_source_diagnostics["amcl_node_info_observed"],
        "amcl_tf_broadcast_param": tf_source_diagnostics["amcl_tf_broadcast_param"],
        "amcl_frame_params": tf_source_diagnostics["amcl_frame_params"],
        "amcl_log_tail": preview_file(str(managed_runtime.get("log_path") or "")),
        "managed_static_tf_processes": managed_static_tf_processes,
        "static_tf_source_observed": bool(
            managed_static_tf_processes.get("all_expected_processes_observed")
            and tf_source_diagnostics["tf_static_observed"]
        ),
        "tf_source_root_cause_detail": tf_source_diagnostics["tf_source_root_cause_detail"],
        "amcl_broadcast_conditions": tf_source_diagnostics["amcl_broadcast_conditions"],
        "map_frame_observed": tf_source_diagnostics["map_frame_observed"],
        "odom_frame_observed": tf_source_diagnostics["odom_frame_observed"],
        "amcl_tf_root_cause": tf_source_diagnostics["amcl_tf_root_cause"],
        "tf_failure_classification": tf_failure_classification,
        "managed_runtime_requested": bool(managed_runtime["requested"]),
        "managed_runtime_started": bool(managed_runtime.get("started")),
        "managed_runtime_process_group": managed_runtime.get("process_group"),
        "managed_runtime_cleanup_ok": bool(managed_runtime.get("cleanup_ok", True)) and bool(cleanup_guard.get("ok")),
        "managed_runtime_boundary": managed_runtime.get("boundary"),
        "managed_runtime_map_yaml": managed_runtime.get("map_yaml"),
        "managed_runtime_requested_map_yaml": managed_runtime.get("requested_map_yaml"),
        "managed_runtime_map_yaml_source": managed_runtime.get("map_yaml_source"),
        "managed_lidar_policy": managed_runtime.get("managed_lidar_policy"),
        "managed_lidar_serial_port": managed_runtime.get("managed_lidar_serial_port"),
        "managed_lidar_serial_baudrate": managed_runtime.get("managed_lidar_serial_baudrate"),
        "managed_lidar_driver_started_by_helper": bool(managed_runtime.get("managed_lidar_driver_started_by_helper")),
        "managed_runtime_wait_result": managed_runtime.get("wait_result"),
        "managed_runtime_map_analysis": managed_map_analysis,
        "managed_runtime_log_lifecycle_readback": managed_log_lifecycle_readback,
        "managed_runtime_vendor_boundary": managed_runtime.get("vendor_boundary"),
        "root_cause_filtering": root_cause_filtering,
        "root_causes": root_causes,
        "blockers": root_causes,
        "map_inputs": map_inputs,
        "commands": {
            "ros2_check": ros2_check,
            "board_source_preflight": board_source,
            "package_checks_batch": package_batch_result,
            "package_checks": package_results,
            "topic_list": topic_list,
            "node_list": node_list,
            "lifecycle": lifecycle_results,
            "planner_lifecycle": planner_lifecycle_results,
            "scan_once": scan_once,
            "map_once": map_once,
            "odom_once": odom_once,
            "amcl_pose_once": amcl_pose_once,
            "initialpose_publish": initialpose_publish,
            "post_initialpose_amcl_pose_once": post_initialpose_amcl_pose_once,
            "tf_source_probe": tf_source_probe_result,
            "map_to_odom_tf": map_to_odom_tf,
            "odom_to_base_link_tf": odom_to_base_link_tf,
            "base_link_to_laser_frame_tf": base_link_to_laser_frame_tf,
            "map_to_base_link_tf": map_to_base_link_tf,
            "initialpose_info": initialpose_info,
            "amcl_node_info": amcl_node_info,
            "map_server_info": map_server_info,
            "planner_node_info": planner_node_info,
            "controller_node_info": controller_node_info,
            "lifecycle_recheck": lifecycle_recheck,
            "map_lifecycle_preflight": map_lifecycle_preflight,
            "planner_lifecycle_recheck": planner_lifecycle_recheck,
            "managed_runtime": {
                "requested": managed_runtime["requested"],
                "started": managed_runtime.get("started"),
                "process_group": managed_runtime.get("process_group"),
                "map_yaml": managed_runtime.get("map_yaml"),
                "requested_map_yaml": managed_runtime.get("requested_map_yaml"),
                "map_yaml_source": managed_runtime.get("map_yaml_source"),
                "managed_lidar_policy": managed_runtime.get("managed_lidar_policy"),
                "managed_lidar_driver_started_by_helper": bool(managed_runtime.get("managed_lidar_driver_started_by_helper")),
                "managed_lidar_serial_port": managed_runtime.get("managed_lidar_serial_port"),
                "managed_lidar_serial_baudrate": managed_runtime.get("managed_lidar_serial_baudrate"),
                "map_analysis": managed_runtime.get("map_analysis"),
                "pre_start_stale_cleanup": managed_runtime.get("pre_start_stale_cleanup"),
                "wait_result": managed_runtime.get("wait_result"),
                "cleanup_result": managed_runtime.get("cleanup_result"),
                "cleanup_guard": cleanup_guard,
                "startup_error": managed_runtime.get("startup_error"),
                "log_path": managed_runtime.get("log_path"),
                "log_tail": preview_file(managed_runtime["log_path"]) if managed_runtime.get("log_path") else "",
            },
            "path_generation": {
                "request": path_generation_request,
                "result": path_generation_result,
            },
        },
        "not_proven": [
            "nav2_goal_execution",
            "controller_cmd_vel_output",
            "fixed_route_execution",
            "delivery_success",
            "hil_pass",
            "safe_to_control_true",
        ],
        "collector_mode": (
            "managed_no_motion_path_generation_runtime"
            if managed_runtime["requested"] and path_generation_request["enabled"]
            else "managed_no_motion_localization_runtime"
            if managed_runtime["requested"]
            else "read_only_existing_ros_graph_no_motion"
        ),
        "blocked_commands_not_sent": blocked_commands_not_sent,
        "blocked_devices_not_opened": ["/dev/ttyS5"],
        **safety_flags(),
    }
    attach_artifact_summaries(proof, status=proof_status)
    phase_writer.record_phase("final", ok=complete, detail={"status": proof_status})
    proof["phase_history"] = phase_writer.phase_history[-80:]
    proof["last_successful_phase"] = phase_writer.last_successful_phase
    attach_artifact_summaries(proof, status=proof_status)
    return {
        "schema": SCHEMA,
        "generated_at_ms": now_ms(),
        "status": proof_status,
        "evidence_type": proof["evidence_type"],
        "proof": proof,
        "software_guard": True,
        "not_proven": not complete,
        **path_generation_envelope_fields(proof),
        **safety_flags(),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI 解析支持测试传 argv，避免单元测试必须 fork 子进程。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", "--output-json", dest="output", default=DEFAULT_OUTPUT)
    parser.add_argument("--map-proof", default=DEFAULT_MAP_PROOF)
    parser.add_argument("--map-dir", default=DEFAULT_MAP_DIR)
    parser.add_argument("--timeout-s", type=float, default=8.0)
    # 这两个 flag 是现场 strict no-motion 命令的显式护栏；helper 本身始终 fail-closed，
    # 接受它们是为了让 automation 命令不因兼容参数提前退出。
    parser.add_argument("--strict-no-motion", action="store_true")
    parser.add_argument("--no-base-uart", action="store_true")
    parser.add_argument("--tf-source-child-probe", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--managed-runtime-opt-in", action="store_true")
    parser.add_argument("--managed-timeout-s", type=float, default=DEFAULT_MANAGED_TIMEOUT_S)
    parser.add_argument("--managed-lifecycle-start-delay-s", type=float, default=DEFAULT_MANAGED_LIFECYCLE_START_DELAY_S)
    parser.add_argument("--managed-map-yaml", default="")
    parser.add_argument("--reuse-existing-lidar-lifecycle", action="store_true")
    parser.add_argument("--managed-lidar-serial-port", default=DEFAULT_MANAGED_LIDAR_SERIAL_PORT)
    parser.add_argument("--managed-lidar-serial-baudrate", type=int, default=DEFAULT_MANAGED_LIDAR_SERIAL_BAUDRATE)
    parser.add_argument("--managed-base-frame-id", default=DEFAULT_MANAGED_BASE_FRAME_ID)
    parser.add_argument("--managed-odom-frame-id", default=DEFAULT_MANAGED_ODOM_FRAME_ID)
    parser.add_argument("--managed-laser-frame-id", default=DEFAULT_MANAGED_LASER_FRAME_ID)
    parser.add_argument("--initialpose-opt-in", action="store_true")
    parser.add_argument("--initialpose-x", type=float, default=0.0)
    parser.add_argument("--initialpose-y", type=float, default=0.0)
    parser.add_argument("--initialpose-yaw", type=float, default=0.0)
    parser.add_argument("--initialpose-frame-id", default="map")
    parser.add_argument("--path-generation-opt-in", action="store_true")
    parser.add_argument("--path-generation-timeout-s", type=float, default=20.0)
    parser.add_argument("--path-goal-frame-id", default="map")
    parser.add_argument("--path-goal-x", type=float, default=0.8)
    parser.add_argument("--path-goal-y", type=float, default=0.0)
    parser.add_argument("--path-goal-yaw", type=float, default=0.0)
    parser.add_argument("--ros-setup", default=DEFAULT_ROS_SETUP)
    parser.add_argument("--onboard-setup", default=DEFAULT_ONBOARD_SETUP)
    parser.add_argument("--workdir", default=DEFAULT_WORKDIR)
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    if args.tf_source_child_probe:
        # 该内部模式仅在 run_ros 已 source 的 child shell 中执行，只输出 graph/TF JSON，不写 runtime artifact。
        payload = compact_tf_source_child_payload(
            collect_amcl_rclpy_probe(args=None, timeout_s=float(args.timeout_s))
        )
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0 if payload.get("executed") else 2
    try:
        payload = build_proof(args)
    except Exception as exc:  # noqa: BLE001 - 未预期异常也必须尽量落 latest，避免 live 只剩 nonzero。
        writer = ACTIVE_PHASE_WRITER
        if isinstance(writer, PhaseArtifactWriter):
            writer.record_phase(
                "exception_before_final_artifact",
                ok=False,
                root_cause={"layer": "helper process", "reason": "exception_before_final_artifact"},
                detail={"error": compact_error(exc)},
            )
            writer.write_partial(status="exception_before_final_artifact")
            try:
                payload = json.loads(Path(args.output).read_text(encoding="utf-8"))
            except Exception:
                proof = {
                    "status": "exception_before_final_artifact",
                    "root_causes": [{"layer": "helper process", "reason": "exception_before_final_artifact"}],
                    "last_phase": "exception_before_final_artifact",
                    "error": compact_error(exc),
                    **safety_flags(),
                }
                attach_artifact_summaries(proof, status="exception_before_final_artifact")
                payload = {
                    "schema": SCHEMA,
                    "generated_at_ms": now_ms(),
                    "status": "exception_before_final_artifact",
                    "evidence_type": "partial_runtime_material",
                    "proof": proof,
                    "software_guard": True,
                    "not_proven": True,
                    **path_generation_envelope_fields(proof),
                    **safety_flags(),
                }
                write_json_atomic(args.output, payload)
        else:
            proof = {
                "status": "exception_before_final_artifact",
                "root_causes": [{"layer": "helper process", "reason": "exception_before_final_artifact"}],
                "last_phase": "exception_before_final_artifact",
                "error": compact_error(exc),
                **safety_flags(),
            }
            attach_artifact_summaries(proof, status="exception_before_final_artifact")
            payload = {
                "schema": SCHEMA,
                "generated_at_ms": now_ms(),
                "status": "exception_before_final_artifact",
                "evidence_type": "partial_runtime_material",
                "proof": proof,
                "software_guard": True,
                "not_proven": True,
                **path_generation_envelope_fields(proof),
                **safety_flags(),
            }
            write_json_atomic(args.output, payload)
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 2
    write_json_atomic(args.output, payload)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if payload["proof"]["status"] in {
        "nav2_no_motion_localization_runtime_observed",
        "nav2_no_motion_path_generation_runtime_observed",
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())
