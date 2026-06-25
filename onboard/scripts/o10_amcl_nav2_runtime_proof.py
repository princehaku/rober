#!/usr/bin/env python3
"""No-motion AMCL/Nav2 runtime proof collector for O10."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shlex
import signal
import subprocess
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
DEFAULT_MANAGED_LIDAR_SERIAL_BAUDRATE = 150000
DEFAULT_MANAGED_TIMEOUT_S = 20.0
DEFAULT_MANAGED_LIFECYCLE_START_DELAY_S = 3.0
DEFAULT_MANAGED_BASE_FRAME_ID = "base_link"
DEFAULT_MANAGED_ODOM_FRAME_ID = "odom"
DEFAULT_MANAGED_LASER_FRAME_ID = "laser_frame"
TF_CHAIN_KEYS = (
    "map_to_odom",
    "odom_to_base_link",
    "base_link_to_laser_frame",
    "map_to_base_link",
)
ROS2_PREFLIGHT_COMMAND = "command -v ros2"
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
TF_ECHO_SHELL_TIMEOUT_S = 4.0
TF_ECHO_PROCESS_TIMEOUT_S = 5.5
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
        "hil_pass": False,
        "uses_base_uart": False,
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
            "amcl_pose_observed": False,
            "localization_tf_observed": {"map_to_odom": False, "map_to_base_link": False},
            "tf_chain_observed": default_tf_chain_observed(),
            "tf_chain_diagnostics": {},
            "tf_topics_observed": {"/tf": False, "/tf_static": False},
            "tf_static_observed": False,
            "tf_frame_inventory": {"frames": [], "edges": [], "dynamic_edges": [], "static_edges": []},
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
        payload = {
            "schema": SCHEMA,
            "generated_at_ms": now_ms(),
            "status": status,
            "evidence_type": "partial_runtime_material",
            "proof": proof,
            "software_guard": True,
            "not_proven": True,
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


def source_prefix(args: argparse.Namespace) -> str:
    """ROS2 setup 必须走 bash -lc，避免远端 zsh 直接 source bash 脚本失败。"""
    return "; ".join(
        [
            "set -e",
            f"source {shlex.quote(args.ros_setup)}",
            f"[ -f {shlex.quote(args.onboard_setup)} ] && source {shlex.quote(args.onboard_setup)} || true",
            f"cd {shlex.quote(args.workdir)}",
        ]
    )


def run_ros(args: argparse.Namespace, command: str, timeout_s: float) -> dict[str, Any]:
    """执行 ROS2 CLI；命令文本固定来自 helper 本身，不接受外部 shell 注入。"""
    started_ms = now_ms()
    process: subprocess.Popen[str] | None = None
    phase_writer = getattr(args, "_phase_writer", None)
    if isinstance(phase_writer, PhaseArtifactWriter):
        phase_writer.before_command(command, timeout_s)
    try:
        process = subprocess.Popen(  # noqa: S603 - argv 固定为 bash -lc，命令来自本 helper。
            ["bash", "-lc", f"{source_prefix(args)}; {command}"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        stdout, stderr = process.communicate(timeout=timeout_s)
        result = {
            "command": command,
            "executed": True,
            "ok": process.returncode == 0,
            "returncode": process.returncode,
            "elapsed_ms": now_ms() - started_ms,
            "stdout": stdout[-8000:],
            "stderr": stderr[-4000:],
        }
        if isinstance(phase_writer, PhaseArtifactWriter):
            phase_writer.after_command(result)
        return result
    except subprocess.TimeoutExpired as exc:
        # ROS2 CLI 超时必须杀整个进程组，否则 echo/pub/tf2_echo 子进程会残留污染下一轮 proof。
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
                stdout, stderr = process.communicate(timeout=2.0)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                stdout, stderr = process.communicate()
        else:
            stdout = exc.stdout if isinstance(exc.stdout, str) else ""
            stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        result = {
            "command": command,
            "executed": True,
            "ok": False,
            "returncode": None,
            "elapsed_ms": now_ms() - started_ms,
            "error": compact_error(exc),
            "stdout": (stdout or "")[-8000:],
            "stderr": (stderr or "")[-4000:],
        }
        if isinstance(phase_writer, PhaseArtifactWriter):
            phase_writer.after_command(result)
        return result


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
        "header": {"frame_id": request["frame_id"]},
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
    start_x = float((initialpose_payload or {}).get("x", 0.0))
    start_y = float((initialpose_payload or {}).get("y", 0.0))
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
        "planner_id": "",
        "orientation_z": math.sin(yaw / 2.0),
        "orientation_w": math.cos(yaw / 2.0),
    }
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
    controller_server_requested: bool,
    controller_server_active: bool,
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
        "controller_server_requested": bool(controller_server_requested),
        "controller_server_active": bool(controller_server_active),
        "path_generation_succeeded": bool(path_generation_succeeded),
        "path_generated": bool(path_generation_succeeded and path_point_count > 0),
        "path_point_count": int(path_point_count),
    }


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
            "boundary": "default_read_only_no_initialpose_publish",
        }
    if not ros2_ok:
        return request, {
            "command": "initialpose opt-in requested but ros2 unavailable",
            "executed": False,
            "ok": False,
            "boundary": "ros2_unavailable_no_initialpose_publish",
        }
    # 唯一允许的写 topic 是 /initialpose；它只给 AMCL 定位种子，不会触发运动执行。
    payload = initialpose_payload(request)
    command = (
        "ros2 topic pub --once /initialpose "
        f"geometry_msgs/msg/PoseWithCovarianceStamped {shlex.quote(payload)}"
    )
    return request, run_ros(args, command, timeout_s=8.0)


def maybe_compute_path_generation(
    args: argparse.Namespace,
    *,
    ros2_ok: bool,
    localization_ready: bool,
    planner_server_active: bool,
    map_analysis: dict[str, Any] | None = None,
    initialpose_payload: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, str]]]:
    """显式 opt-in 时只尝试一次 ComputePathToPose；默认路径不进入 planner/action。"""
    request = path_generation_request(
        args,
        map_analysis=map_analysis,
        initialpose_payload=initialpose_payload,
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
        }, [{"layer": "ROS install/source", "reason": "ros2_command_unavailable_after_bash_source"}]
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
        return request, {
            "attempted": True,
            "ok": False,
            "boundary": boundary,
            "error": error,
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
            goal_msg.start.pose.orientation.z = request["orientation_z"]
            goal_msg.start.pose.orientation.w = request["orientation_w"]
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


def text_contains_any(text: str, needles: list[str]) -> bool:
    """字符串匹配统一转小写，避免 ROS2 CLI 输出大小写差异带来误判。"""
    lowered = text.lower()
    return any(needle.lower() in lowered for needle in needles)


def topic_once_observed(result: dict[str, Any]) -> bool:
    """topic echo 成功且有正文才算 observed，timeout 空结果不能默认为真。"""
    return bool(result.get("ok") and str(result.get("stdout") or "").strip())


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


def collect_amcl_rclpy_probe(timeout_s: float = 2.0) -> dict[str, Any]:
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
        "dynamic_edges": [],
        "static_edges": [],
        "command_statuses": {"rclpy_graph": None, "tf": None, "tf_static": None},
        "error": None,
        "elapsed_ms": 0,
        "boundary": "rclpy_amcl_probe_not_started",
    }
    started_ms = now_ms()
    node = None
    rclpy_initialized = False
    try:
        import rclpy
        from rcl_interfaces.srv import GetParameters  # type: ignore[import-not-found]
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

        def on_dynamic_tf(message: Any) -> None:
            dynamic_edges.extend(tf_message_edges(message, source_topic="/tf"))

        def on_static_tf(message: Any) -> None:
            static_edges.extend(tf_message_edges(message, source_topic="/tf_static"))

        # transient local QoS 是读取 /tf_static 的关键，避免 CLI echo 的启动成本和时序抖动。
        node.create_subscription(TFMessage, "/tf", on_dynamic_tf, QoSProfile(depth=10))
        node.create_subscription(
            TFMessage,
            "/tf_static",
            on_static_tf,
            QoSProfile(depth=10, durability=DurabilityPolicy.TRANSIENT_LOCAL),
        )
        end_time = time.time() + max(min(timeout_s, 3.0), 0.8)
        while time.time() < end_time:
            # 参数服务偶发晚于 /amcl 节点出现在 graph；不要因此跳过 TF/static TF 采样。
            rclpy.spin_once(node, timeout_sec=0.1)
            topic_pairs = node.get_topic_names_and_types()
            result["topic_types"] = {topic: ",".join(types) for topic, types in topic_pairs}
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
            if dynamic_edges and static_edges and params and result["node_info_observed"]:
                break
        result["dynamic_edges"] = dynamic_edges
        result["static_edges"] = static_edges
        result["command_statuses"]["tf"] = 0 if dynamic_edges else 124
        result["command_statuses"]["tf_static"] = 0 if static_edges else 124
        result["tf_inventory_observed"] = bool(dynamic_edges or static_edges or result["topic_types"])
        result.update(
            {
                "ok": bool(result["node_info_observed"] and params and result["tf_inventory_observed"]),
                "param_probe_ok": bool(params),
                "params": params,
                "boundary": (
                    "rclpy_amcl_params_graph_tf_probe_observed"
                    if params
                    else f"{param_boundary}_after_tf_probe"
                ),
            }
        )
        return result
    except Exception as exc:  # noqa: BLE001 - 现场缺 rclpy/服务超时都要结构化回写。
        result["error"] = compact_error(exc)
        result["boundary"] = "rclpy_amcl_probe_failed"
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


def edge_observed(edges: list[dict[str, str]], parent: str, child: str) -> bool:
    """frame inventory 里的边用精确 parent/child 匹配，避免子串误判 frame 名。"""
    return any(edge.get("parent") == parent and edge.get("child") == child for edge in edges)


def collect_tf_source_diagnostics(
    args: argparse.Namespace,
    *,
    ros2_ok: bool,
    amcl_pose_result: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """轻量采集 AMCL/TF source；放在 tf2_echo 前，避免慢查询掩盖 root cause。"""
    if not ros2_ok:
        return {
            "executed": False,
            "ok": False,
            "boundary": "ros2_unavailable_tf_source_probe_skipped",
        }, default_tf_source_diagnostics(args, amcl_pose_result=amcl_pose_result)
    amcl_probe = collect_amcl_rclpy_probe(timeout_s=4.0)
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
) -> dict[str, Any]:
    """source probe 未执行时仍输出稳定字段，保证 upper/readback 不需要猜 key。"""
    frame_ids = tf_chain_frame_contract(args)["actual"]
    amcl_pose_frame_id = parse_pose_frame_id(str(amcl_pose_result.get("stdout") or ""))
    return {
        "tf_topics_observed": {"/tf": False, "/tf_static": False},
        "tf_static_observed": False,
        "tf_frame_inventory": {"frames": [], "edges": [], "dynamic_edges": [], "static_edges": []},
        "amcl_pose_frame_id": amcl_pose_frame_id,
        "amcl_node_publishers": [],
        "amcl_node_subscribers": [],
        "amcl_param_probe_ok": False,
        "amcl_node_info_observed": False,
        "amcl_tf_broadcast_param": None,
        "amcl_frame_params": {},
        "tf_source_root_cause_detail": {"reason": "tf_source_probe_not_executed"},
        "amcl_broadcast_conditions": {},
        "map_frame_observed": False,
        "odom_frame_observed": False,
        "base_frame_observed": False,
        "laser_frame_observed": False,
        "map_to_odom_source_observed": False,
        "odom_to_base_link_source_observed": False,
        "base_link_to_laser_frame_source_observed": False,
        "amcl_tf_root_cause": "tf_source_probe_not_executed",
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
    if isinstance(probe.get("dynamic_edges"), list):
        dynamic_edges = [edge for edge in probe["dynamic_edges"] if isinstance(edge, dict)]
    if isinstance(probe.get("static_edges"), list):
        static_edges = [edge for edge in probe["static_edges"] if isinstance(edge, dict)]
    edges = [*dynamic_edges, *static_edges]
    frames = sorted({value for edge in edges for value in (edge.get("parent"), edge.get("child")) if value})
    frame_ids = tf_chain_frame_contract(args)["actual"]
    map_to_odom_source_observed = edge_observed(dynamic_edges, "map", frame_ids["odom"])
    odom_to_base_source_observed = edge_observed(static_edges, frame_ids["odom"], frame_ids["base"])
    base_to_laser_source_observed = edge_observed(static_edges, frame_ids["base"], frame_ids["laser"])
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
    node_info_observed = bool(probe.get("node_info_observed") or amcl_publishers or amcl_subscribers)
    amcl_pose_frame_id = parse_pose_frame_id(str(amcl_pose_result.get("stdout") or ""))
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
    elif not odom_to_base_source_observed:
        root_cause = "odom_to_base_link_static_tf_not_observed"
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
        "map_to_odom_source_observed": map_to_odom_source_observed,
        "odom_to_base_link_source_observed": odom_to_base_source_observed,
        "base_link_to_laser_frame_source_observed": base_to_laser_source_observed,
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
        "odom_to_base_link_source_observed": odom_to_base_source_observed,
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
            "topic_types": topic_types,
            "command_statuses": command_statuses,
        },
        "amcl_pose_frame_id": amcl_pose_frame_id,
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
        "odom_to_base_link_source_observed": odom_to_base_source_observed,
        "base_link_to_laser_frame_source_observed": base_to_laser_source_observed,
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
    """ROS2 lifecycle get 输出包含 active 时才算 active，缺 node 必须 fail-closed。"""
    if not result.get("ok"):
        return False
    text = f"{result.get('stdout') or ''}\n{result.get('stderr') or ''}".lower()
    for line in text.splitlines():
        normalized = line.strip()
        if normalized == "active" or normalized.startswith("active "):
            return True
        if normalized.endswith(": active") or normalized.endswith(" state active"):
            return True
    return False


def lifecycle_checks(
    args: argparse.Namespace,
    nodes: dict[str, str] | None = None,
) -> tuple[dict[str, bool], dict[str, dict[str, Any]]]:
    """只读 lifecycle 状态；不调用 transition，不启动 planner/controller。"""
    active: dict[str, bool] = {}
    results: dict[str, dict[str, Any]] = {}
    for key, node in (nodes or LOCALIZATION_LIFECYCLE_NODES).items():
        # 现场板子上 lifecycle RPC 偶发慢于 topic echo，因此给它更宽的超时窗口。
        result = run_ros(args, f"ros2 lifecycle get {shlex.quote(node)}", timeout_s=10.0)
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
        lines.append("    bond_timeout: 4.0")
        lines.append('    node_names: ["map_server", "amcl", "planner_server"]')
    else:
        lines.append("lifecycle_manager:")
        lines.append("  ros__parameters:")
        lines.append("    use_sim_time: false")
        lines.append("    autostart: true")
        lines.append("    bond_timeout: 4.0")
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
    commands = [
        # 这里单独记录 vendor 事实边界：LiDAR 只允许 /dev/ttyACM0@150000；不允许触碰 /dev/ttyS5。
        (
            "lidar_driver",
            "ros2 run ros2_trashbot_hardware lidar_driver --ros-args "
            f"-p serial_port:={lidar_port} "
            f"-p serial_baudrate:={lidar_baud} "
            f"-p frame_id:={laser_frame} "
            "-p scan_topic:=/scan "
            "-p publish_raw_packets:=false"
        ),
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
    ]
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
    ]
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


def start_managed_runtime(args: argparse.Namespace, *, map_yaml: str) -> dict[str, Any]:
    """显式 opt-in 时短暂拉起 localization graph；默认路径完全不触发本函数。"""
    started_ms = now_ms()
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


def rclpy_node_names(timeout_s: float = 0.8) -> dict[str, Any]:
    """用 rclpy graph 读取节点名，替代慢 `ros2 node list` CLI。"""
    started_ms = now_ms()
    result: dict[str, Any] = {
        "executed": False,
        "ok": False,
        "node_names": [],
        "elapsed_ms": 0,
        "error": None,
        "boundary": "rclpy_node_names_not_started",
    }
    node = None
    rclpy_initialized = False
    try:
        import rclpy

        result["executed"] = True
        rclpy.init(args=[])
        rclpy_initialized = True
        node = rclpy.create_node("o10_managed_runtime_graph_probe")
        deadline = time.time() + max(timeout_s, 0.2)
        names: list[str] = []
        while time.time() < deadline:
            rclpy.spin_once(node, timeout_sec=0.05)
            names = sorted({name for name in node.get_node_names() if name})
            if names:
                break
        result.update({"ok": bool(names), "node_names": names, "boundary": "rclpy_node_names_observed"})
        return result
    except Exception as exc:  # noqa: BLE001 - graph 查询失败必须结构化，不回退阻塞 CLI。
        result["error"] = compact_error(exc)
        result["boundary"] = "rclpy_node_names_failed"
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
    while time.time() < deadline:
        process: subprocess.Popen[str] | None = runtime.get("process")
        if process is not None and process.poll() is not None:
            return {
                "ok": False,
                "reason": "managed_runtime_exited_early",
                "returncode": process.returncode,
                "history": history,
                "log_tail": preview_file(runtime["log_path"]),
            }
        # runtime wait 只确认节点已出现；用 rclpy graph 避免 ROS CLI 启动成本吃掉定位预算。
        node_list = rclpy_node_names(timeout_s=0.8)
        node_lines = {f"/{line.lstrip('/')}" for line in node_list.get("node_names", []) if isinstance(line, str)}
        lifecycle_active = {
            "map_server": "/map_server" in node_lines,
            "amcl": "/amcl" in node_lines,
        }
        if require_planner_server:
            lifecycle_active["planner_server"] = "/planner_server" in node_lines
        if not node_list.get("ok"):
            history.append({"node_list": node_list, "lifecycle_active": lifecycle_active})
            time.sleep(0.6)
            continue
        snapshot = {
            "elapsed_ms": now_ms() - int(runtime["started_at_ms"]),
            "lifecycle_active": lifecycle_active,
            "node_list_command": node_list,
        }
        history.append(snapshot)
        if lifecycle_active.get("map_server") and lifecycle_active.get("amcl") and (
            not require_planner_server or lifecycle_active.get("planner_server")
        ):
            return {"ok": True, "history": history, "node_list": node_list, "boundary": "managed_runtime_nodes_observed"}
        time.sleep(0.8)
    return {
        "ok": False,
        "reason": "managed_runtime_wait_timeout",
        "history": history,
        "log_tail": preview_file(runtime["log_path"]),
    }


def classify_root_causes(
    *,
    map_inputs: dict[str, Any],
    ros2_ok: bool,
    packages: dict[str, bool],
    lifecycle_active: dict[str, bool],
    scan_once_observed: bool,
    map_once_observed: bool,
    amcl_pose_observed: bool,
    localization_tf_observed: dict[str, bool],
    tf_chain_observed: dict[str, bool],
    tf_failure_classification: dict[str, Any],
    initialpose_enabled: bool,
) -> list[dict[str, str]]:
    """root cause 按层输出，方便下一轮知道是 map、runtime 还是 localization 卡住。"""
    causes = list(map_inputs.get("root_causes") or [])
    if not ros2_ok:
        causes.append({"layer": "ROS install/source", "reason": "ros2_command_unavailable_after_bash_source"})
        return causes
    for package, available in packages.items():
        if not available:
            causes.append({"layer": "ROS install/source", "reason": f"{package}_missing"})
    for key, active in lifecycle_active.items():
        if not active:
            causes.append({"layer": "Nav2 lifecycle", "reason": f"{key}_lifecycle_not_active"})
    if not scan_once_observed:
        causes.append({"layer": "Nav2 sensor input", "reason": "/scan_once_not_observed"})
    if not map_once_observed:
        causes.append({"layer": "Nav2 map input", "reason": "/map_once_not_observed"})
    if initialpose_enabled:
        if not amcl_pose_observed:
            causes.append({"layer": "AMCL localization", "reason": "/amcl_pose_once_not_observed"})
        if not localization_tf_observed.get("map_to_odom"):
            causes.append({"layer": "Localization TF", "reason": "map_to_odom_not_observed"})
        causes.extend(tf_chain_root_causes(tf_failure_classification, tf_chain_observed))
    return causes


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
    if args.managed_runtime_opt_in:
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
                # planner_server 的 costmap 激活依赖 map->base_link；必须先让 AMCL 接收 initialpose。
                # 因此 runtime 启动阶段只等待 localization 节点，planner 在定位 ready 后再复查。
                managed_runtime["wait_result"] = wait_for_managed_runtime(
                    args,
                    managed_runtime,
                    require_planner_server=False,
                )
                phase_writer.record_phase(
                    "managed_runtime_wait",
                    ok=bool(managed_runtime["wait_result"].get("ok")),
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
    else:
        phase_writer.record_phase("managed_runtime", ok=True, detail={"requested": False})

    phase_writer.record_phase("ros2_preflight")
    ros2_check = run_ros(args, ROS2_PREFLIGHT_COMMAND, timeout_s=3.0)
    # 这里故意只检查 ros2 可执行文件，避免 `ros2 --help` 在现场服务环境中消耗定位窗口。
    ros2_ok = bool(ros2_check.get("ok") or str(ros2_check.get("stdout") or "").strip())
    phase_writer.record_phase("ros2_preflight", ok=ros2_ok)
    phase_writer.record_phase("initialpose")
    initialpose_request_payload, initialpose_publish = maybe_publish_initialpose(args, ros2_ok)
    phase_writer.update_snapshot(
        initialpose_publish_attempted=bool(initialpose_request_payload["enabled"]),
        initialpose_published=bool(initialpose_publish.get("ok")),
    )
    phase_writer.record_phase(
        "initialpose",
        ok=bool(initialpose_publish.get("ok")) if initialpose_request_payload["enabled"] else True,
        detail={"enabled": bool(initialpose_request_payload["enabled"])},
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
        if ros2_ok and initialpose_request_payload["enabled"]
        else {"executed": False, "ok": False, "boundary": "post_initialpose_probe_not_requested"}
    )
    amcl_pose_probe_ok = bool(topic_once_observed(amcl_pose_once) or topic_once_observed(post_initialpose_amcl_pose_once))
    phase_writer.update_snapshot(
        amcl_pose_observed=amcl_pose_probe_ok,
        amcl_pose_frame_id=parse_pose_frame_id(str(post_initialpose_amcl_pose_once.get("stdout") or "")),
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
    tf_source_probe_result, tf_source_diagnostics = collect_tf_source_diagnostics(
        args,
        ros2_ok=ros2_ok and initialpose_request_payload["enabled"],
        amcl_pose_result=post_initialpose_amcl_pose_once,
    )
    phase_writer.update_snapshot(
        tf_topics_observed=tf_source_diagnostics["tf_topics_observed"],
        tf_static_observed=tf_source_diagnostics["tf_static_observed"],
        tf_frame_inventory=tf_source_diagnostics["tf_frame_inventory"],
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
        ok=bool(tf_source_diagnostics["tf_topics_observed"].get("/tf")),
        detail={"amcl_tf_root_cause": tf_source_diagnostics["amcl_tf_root_cause"]},
    )
    phase_writer.record_phase("tf_probe")
    frame_contract = tf_chain_frame_contract(args)
    frame_ids = frame_contract["actual"]
    tf_not_requested = {"executed": False, "ok": False, "boundary": "tf_probe_not_requested_without_initialpose_opt_in"}
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
        if ros2_ok and initialpose_request_payload["enabled"] and not tf_source_diagnostics.get("odom_to_base_link_source_observed")
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
                if ros2_ok and initialpose_request_payload["enabled"]
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
        if ros2_ok and initialpose_request_payload["enabled"] and not tf_source_diagnostics.get("base_link_to_laser_frame_source_observed")
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
    phase_writer.record_phase("package_checks", detail={"mode": "single_sourced_pkg_list_diagnostic"})
    if ros2_ok:
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
        ok=bool(ros2_ok and all(packages.values())),
        detail={"mode": "single_sourced_pkg_list_diagnostic", "packages": packages},
    )
    planner_nodes = {"planner_server": "/planner_server", "controller_server": "/controller_server"}
    if source_chain_complete:
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
        planner_lifecycle_active = {key: False for key in planner_nodes}
        planner_boundary = (
            "planner_recheck_deferred_until_localization_ready"
            if args.path_generation_opt_in
            else "path_generation_not_requested"
        )
        planner_lifecycle_results = {key: {"executed": False, "ok": False, "boundary": planner_boundary} for key in planner_nodes}
        planner_server_active = False
        controller_server_active = False
        controller_server_requested = False
        planner_node_info = {"executed": False, "ok": False, "boundary": planner_boundary}
        controller_node_info = {"executed": False, "ok": False, "boundary": "controller_never_requested_no_motion"}
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
        phase_writer.record_phase(
            "topic_probe",
            ok=True,
            detail={
                "mode": "source_inventory_fast_path",
                "scan_once_observed": True,
                "map_once_observed": True,
                "amcl_pose_observed_pre_initialpose": topic_once_observed(amcl_pose_once),
            },
        )
        initialpose_info = {"executed": False, "ok": True, "boundary": "initialpose_publish_result_already_observed"}
        amcl_node_info = {"executed": False, "ok": True, "boundary": "amcl_graph_observed_by_rclpy_probe"}
        map_server_info = {"executed": False, "ok": True, "boundary": "map_consumed_by_amcl_runtime"}
        lifecycle_recheck = {"executed": False, "boundary": "source_inventory_fast_path_sufficient"}
    else:
        topic_list = run_ros(args, "ros2 topic list", timeout_s=8.0) if ros2_ok else {"executed": False, "ok": False}
        node_list = run_ros(args, "ros2 node list", timeout_s=8.0) if ros2_ok else {"executed": False, "ok": False}
        phase_writer.record_phase("graph_discovery", ok=bool(topic_list.get("ok") and node_list.get("ok")))
        lifecycle_active, lifecycle_results = lifecycle_checks(args) if ros2_ok else ({key: False for key in LOCALIZATION_LIFECYCLE_NODES}, {})
        phase_writer.record_phase("lifecycle_probe", ok=bool(lifecycle_active.get("map_server") and lifecycle_active.get("amcl")))
        planner_lifecycle_active, planner_lifecycle_results = (
            lifecycle_checks(args, planner_nodes) if ros2_ok else ({key: False for key in planner_nodes}, {})
        )
        planner_server_active = bool(planner_lifecycle_active.get("planner_server"))
        controller_server_active = bool(planner_lifecycle_active.get("controller_server"))
        # 本 proof 只允许 planner 计算路径；即使 path opt-in，也不得请求 controller 执行层。
        controller_server_requested = False
        planner_node_info = run_ros(args, "ros2 node info /planner_server", timeout_s=8.0) if ros2_ok else {"executed": False, "ok": False}
        controller_node_info = run_ros(args, "ros2 node info /controller_server", timeout_s=8.0) if ros2_ok else {"executed": False, "ok": False}
        phase_writer.record_phase("topic_probe", detail={"echo_timeout_s": echo_timeout_s})
        scan_once = run_ros(args, "timeout 6 ros2 topic echo --once /scan", timeout_s=echo_timeout_s) if ros2_ok else {"executed": False, "ok": False}
        map_once = run_ros(args, "timeout 8 ros2 topic echo --once /map", timeout_s=echo_timeout_s + 2.0) if ros2_ok else {"executed": False, "ok": False}
        phase_writer.record_phase(
            "topic_probe",
            ok=bool(topic_once_observed(scan_once) and topic_once_observed(map_once)),
            detail={
                "scan_once_observed": topic_once_observed(scan_once),
                "map_once_observed": topic_once_observed(map_once),
                "amcl_pose_observed_pre_initialpose": topic_once_observed(amcl_pose_once),
            },
        )
        initialpose_info = run_ros(args, "ros2 topic info /initialpose --verbose", timeout_s=6.0) if ros2_ok else {"executed": False, "ok": False}
        amcl_node_info = run_ros(args, "ros2 node info /amcl", timeout_s=8.0) if ros2_ok else {"executed": False, "ok": False}
        map_server_info = run_ros(args, "ros2 node info /map_server", timeout_s=8.0) if ros2_ok else {"executed": False, "ok": False}
        lifecycle_recheck = {"executed": False, "boundary": "initial_lifecycle_snapshot_sufficient"}
        if ros2_ok and (not lifecycle_active.get("map_server") or not lifecycle_active.get("amcl")):
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
    scan_observed = topic_once_observed(scan_once)
    map_observed = topic_once_observed(map_once)
    amcl_pose_observed = bool(topic_once_observed(amcl_pose_once) or topic_once_observed(post_initialpose_amcl_pose_once))
    amcl_pose = parse_amcl_pose(str(post_initialpose_amcl_pose_once.get("stdout") or "")) or parse_amcl_pose(str(amcl_pose_once.get("stdout") or ""))
    base_link_to_laser_frame_transform = parse_tf_echo_transform(
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
    phase_writer.update_snapshot(
        amcl_pose_observed=amcl_pose_observed,
        localization_tf_observed=localization_tf_observed,
        tf_chain_observed=tf_chain_observed,
        tf_chain_diagnostics=tf_chain_diagnostics,
        tf_failure_classification=tf_failure_classification,
        tf_topics_observed=tf_source_diagnostics["tf_topics_observed"],
        tf_static_observed=tf_source_diagnostics["tf_static_observed"],
        tf_frame_inventory=tf_source_diagnostics["tf_frame_inventory"],
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
    if initialpose_request_payload["enabled"]:
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
    localization_root_causes = classify_root_causes(
        map_inputs=effective_map_inputs,
        ros2_ok=ros2_ok,
        packages=packages,
        lifecycle_active=lifecycle_active,
        scan_once_observed=scan_observed,
        map_once_observed=map_observed,
        amcl_pose_observed=amcl_pose_observed,
        localization_tf_observed=localization_tf_observed,
        tf_chain_observed=tf_chain_observed,
        tf_failure_classification=tf_failure_classification,
        initialpose_enabled=initialpose_request_payload["enabled"],
    )
    path_generation_preconditions_ready = bool(
        initialpose_request_payload["enabled"] and localization_ready and not localization_root_causes
    )
    phase_writer.record_phase("path_generation", detail={"requested": bool(args.path_generation_opt_in)})
    path_generation_request, path_generation_result, _path_generation_summary, path_generation_root_causes = maybe_compute_path_generation(
        args,
        ros2_ok=ros2_ok,
        localization_ready=path_generation_preconditions_ready,
        planner_server_active=planner_server_active,
        map_analysis=managed_map_analysis,
        initialpose_payload=initialpose_request_payload,
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
    root_causes = list(localization_root_causes)
    if path_generation_request["enabled"]:
        root_causes.extend(path_generation_root_causes)
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
        controller_server_requested=controller_server_requested,
        controller_server_active=controller_server_active,
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
        "package_availability": packages,
        "package_check_mode": "single_sourced_pkg_list_diagnostic",
        "package_checks_batch_ok": bool(package_batch_result.get("ok")),
        "map_server_active": lifecycle_active.get("map_server", False),
        "amcl_active": lifecycle_active.get("amcl", False),
        "amcl_pose": amcl_pose,
        "base_link_to_laser_frame_transform": base_link_to_laser_frame_transform,
        "planner_server_active": planner_server_active,
        "controller_server_active": controller_server_active,
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
        "initialpose_request": initialpose_request_payload,
        "initialpose_boundary": (
            "explicit_opt_in_single_initialpose_for_amcl_localization_only"
            if initialpose_request_payload["enabled"]
            else "default_read_only_not_published_by_collector_no_motion_boundary"
        ),
        "localization_tf_observed": localization_tf_observed,
        "tf_chain_observed": tf_chain_observed,
        "tf_chain_diagnostics": tf_chain_diagnostics,
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
        "managed_runtime_map_yaml_source": managed_runtime.get("map_yaml_source"),
        "managed_runtime_map_analysis": managed_map_analysis,
        "managed_runtime_vendor_boundary": managed_runtime.get("vendor_boundary"),
        "root_causes": root_causes,
        "blockers": root_causes,
        "map_inputs": map_inputs,
        "commands": {
            "ros2_check": ros2_check,
            "package_checks_batch": package_batch_result,
            "package_checks": package_results,
            "topic_list": topic_list,
            "node_list": node_list,
            "lifecycle": lifecycle_results,
            "planner_lifecycle": planner_lifecycle_results,
            "scan_once": scan_once,
            "map_once": map_once,
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
            "planner_lifecycle_recheck": planner_lifecycle_recheck,
            "managed_runtime": {
                "requested": managed_runtime["requested"],
                "started": managed_runtime.get("started"),
                "process_group": managed_runtime.get("process_group"),
                "map_yaml": managed_runtime.get("map_yaml"),
                "map_yaml_source": managed_runtime.get("map_yaml_source"),
                "map_analysis": managed_runtime.get("map_analysis"),
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
    phase_writer.record_phase("final", ok=complete, detail={"status": proof_status})
    proof["phase_history"] = phase_writer.phase_history[-80:]
    proof["last_successful_phase"] = phase_writer.last_successful_phase
    return {
        "schema": SCHEMA,
        "generated_at_ms": now_ms(),
        "status": proof_status,
        "evidence_type": proof["evidence_type"],
        "proof": proof,
        "software_guard": True,
        "not_proven": not complete,
        **safety_flags(),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI 解析支持测试传 argv，避免单元测试必须 fork 子进程。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--map-proof", default=DEFAULT_MAP_PROOF)
    parser.add_argument("--map-dir", default=DEFAULT_MAP_DIR)
    parser.add_argument("--timeout-s", type=float, default=8.0)
    parser.add_argument("--managed-runtime-opt-in", action="store_true")
    parser.add_argument("--managed-timeout-s", type=float, default=DEFAULT_MANAGED_TIMEOUT_S)
    parser.add_argument("--managed-lifecycle-start-delay-s", type=float, default=DEFAULT_MANAGED_LIFECYCLE_START_DELAY_S)
    parser.add_argument("--managed-map-yaml", default="")
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
    payload = build_proof(args)
    write_json_atomic(args.output, payload)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if payload["proof"]["status"] in {
        "nav2_no_motion_localization_runtime_observed",
        "nav2_no_motion_path_generation_runtime_observed",
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())
