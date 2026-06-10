#!/usr/bin/env python3
"""No-motion AMCL/Nav2 runtime proof collector for O10."""

from __future__ import annotations

import argparse
import json
import math
import os
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
DEFAULT_MANAGED_BASE_FRAME_ID = "base_link"
DEFAULT_MANAGED_ODOM_FRAME_ID = "odom"
DEFAULT_MANAGED_LASER_FRAME_ID = "laser_frame"
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
    "compute_path_to_pose",
    "navigate_to_pose",
]


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
    try:
        process = subprocess.Popen(  # noqa: S603 - argv 固定为 bash -lc，命令来自本 helper。
            ["bash", "-lc", f"{source_prefix(args)}; {command}"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        stdout, stderr = process.communicate(timeout=timeout_s)
        return {
            "command": command,
            "executed": True,
            "ok": process.returncode == 0,
            "returncode": process.returncode,
            "elapsed_ms": now_ms() - started_ms,
            "stdout": stdout[-8000:],
            "stderr": stderr[-4000:],
        }
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
        return {
            "command": command,
            "executed": True,
            "ok": False,
            "returncode": None,
            "elapsed_ms": now_ms() - started_ms,
            "error": compact_error(exc),
            "stdout": (stdout or "")[-8000:],
            "stderr": (stderr or "")[-4000:],
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


def resolve_managed_map_yaml(args: argparse.Namespace, map_inputs: dict[str, Any]) -> tuple[str | None, str]:
    """managed runtime 优先用显式 map yaml；缺省时才回退到 canonical artifact。"""
    explicit = str(args.managed_map_yaml or "").strip()
    if explicit:
        path = Path(explicit)
        if path.exists():
            return str(path), "explicit_cli_managed_map_yaml"
        return None, "explicit_cli_managed_map_yaml_missing"
    for candidate in map_inputs.get("map_yaml_candidates") or []:
        path = str(candidate.get("path") or "").strip()
        if path and Path(path).exists():
            return path, "canonical_map_proof_yaml_candidate"
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


def package_checks(args: argparse.Namespace) -> tuple[dict[str, bool], dict[str, dict[str, Any]]]:
    """Nav2 包是否安装要单独记录，不能从 lifecycle node 缺失反推依赖。"""
    available: dict[str, bool] = {}
    results: dict[str, dict[str, Any]] = {}
    for package in EXPECTED_PACKAGES:
        result = run_ros(args, f"ros2 pkg prefix {shlex.quote(package)}", timeout_s=6.0)
        available[package] = bool(result.get("ok"))
        results[package] = result
    return available, results


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


def lifecycle_checks(args: argparse.Namespace) -> tuple[dict[str, bool], dict[str, dict[str, Any]]]:
    """只读 lifecycle 状态；不调用 transition，不启动 planner/controller。"""
    active: dict[str, bool] = {}
    results: dict[str, dict[str, Any]] = {}
    for key, node in LOCALIZATION_LIFECYCLE_NODES.items():
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


def managed_param_file_text(args: argparse.Namespace, map_yaml: str) -> str:
    """managed runtime 参数文件只覆盖 localization proof 所需字段，避免拉起运动能力。"""
    return "\n".join(
        [
            "map_server:",
            "  ros__parameters:",
            f"    use_sim_time: false",
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
            "lifecycle_manager:",
            "  ros__parameters:",
            "    use_sim_time: false",
            "    autostart: true",
            "    bond_timeout: 4.0",
            '    node_names: ["map_server", "amcl"]',
            "",
        ]
    )


def build_managed_runtime_shell(args: argparse.Namespace, *, map_yaml: str, params_path: str, log_path: str) -> str:
    """用一个 bash 进程组托管 runtime，便于统一 cleanup 且避免遗留后台子进程。"""
    lidar_port = shlex.quote(args.managed_lidar_serial_port)
    lidar_baud = int(args.managed_lidar_serial_baudrate)
    params = shlex.quote(params_path)
    map_yaml_quoted = shlex.quote(map_yaml)
    log = shlex.quote(log_path)
    base_frame = shlex.quote(args.managed_base_frame_id)
    odom_frame = shlex.quote(args.managed_odom_frame_id)
    laser_frame = shlex.quote(args.managed_laser_frame_id)
    commands = [
        # 这里单独记录 vendor 事实边界：LiDAR 只允许 /dev/ttyACM0@150000；不允许触碰 /dev/ttyS5。
        "pids=()",
        "cleanup(){ for pid in \"${pids[@]}\"; do kill -INT \"$pid\" 2>/dev/null || true; done; wait || true; }",
        "trap cleanup EXIT INT TERM",
        (
            "ros2 run ros2_trashbot_hardware lidar_driver --ros-args "
            f"-p serial_port:={lidar_port} "
            f"-p serial_baudrate:={lidar_baud} "
            f"-p frame_id:={laser_frame} "
            "-p scan_topic:=/scan "
            "-p publish_raw_packets:=false"
        ),
        (
            "ros2 run tf2_ros static_transform_publisher "
            f"0.0 0.0 0.0 0.0 0.0 0.0 {odom_frame} {base_frame}"
        ),
        (
            "ros2 run tf2_ros static_transform_publisher "
            f"0.0 0.0 0.0 0.0 0.0 0.0 {base_frame} {laser_frame}"
        ),
        (
            "ros2 run nav2_map_server map_server --ros-args "
            f"--params-file {params} -r __node:=map_server"
        ),
        (
            "ros2 run nav2_amcl amcl --ros-args "
            f"--params-file {params} -r __node:=amcl"
        ),
        (
            "ros2 run nav2_lifecycle_manager lifecycle_manager --ros-args "
            f"--params-file {params} -r __node:=lifecycle_manager"
        ),
    ]
    lines = [
        "set -e",
        f"{source_prefix(args)}",
        f"printf '%s\\n' 'managed_map_yaml={map_yaml_quoted}' > {log}",
        "printf '%s\\n' 'managed_runtime_boundary=no_motion_localization_only' >> " + log,
        "printf '%s\\n' 'blocked_device=/dev/ttyS5' >> " + log,
    ]
    for command in commands[3:]:
        # 每个子进程都追加到同一日志，便于远端 artifact 回放每个节点的启动顺序。
        lines.append(f"({command}) >> {log} 2>&1 & pids+=($!)")
    lines.append("wait")
    return "; ".join(lines)


def start_managed_runtime(args: argparse.Namespace, *, map_yaml: str) -> dict[str, Any]:
    """显式 opt-in 时短暂拉起 localization graph；默认路径完全不触发本函数。"""
    started_ms = now_ms()
    params_fd, params_path = tempfile.mkstemp(prefix="rober_nav2_localization_", suffix=".yaml")
    os.close(params_fd)
    log_fd, log_path = tempfile.mkstemp(prefix="rober_nav2_localization_", suffix=".log")
    os.close(log_fd)
    Path(params_path).write_text(managed_param_file_text(args, map_yaml), encoding="utf-8")
    process = subprocess.Popen(  # noqa: S603 - argv 固定；runtime 内容完全由 helper 生成。
        ["bash", "-lc", build_managed_runtime_shell(args, map_yaml=map_yaml, params_path=params_path, log_path=log_path)],
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
        "boundary": "explicit_opt_in_managed_localization_runtime_no_motion",
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


def wait_for_managed_runtime(args: argparse.Namespace, runtime: dict[str, Any]) -> dict[str, Any]:
    """runtime 拉起后轮询 lifecycle，尽量在 proof 窗口内拿到 active graph。"""
    deadline = time.time() + max(float(args.managed_timeout_s), 4.0)
    history: list[dict[str, Any]] = []
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
        ros2_check = run_ros(args, "command -v ros2 && ros2 --help >/dev/null", timeout_s=6.0)
        if not ros2_check.get("ok"):
            history.append({"ros2_check": ros2_check})
            time.sleep(1.0)
            continue
        lifecycle_active, lifecycle_results = lifecycle_checks(args)
        snapshot = {
            "elapsed_ms": now_ms() - int(runtime["started_at_ms"]),
            "lifecycle_active": lifecycle_active,
        }
        history.append(snapshot)
        if lifecycle_active.get("map_server") and lifecycle_active.get("amcl"):
            return {"ok": True, "history": history, "lifecycle": lifecycle_results}
        time.sleep(1.2)
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
        if not localization_tf_observed.get("map_to_base_link"):
            causes.append({"layer": "Localization TF", "reason": "map_to_base_link_not_observed"})
    return causes


def build_proof(args: argparse.Namespace) -> dict[str, Any]:
    """执行一次 no-motion AMCL/Nav2 localization proof；成功或失败都写 latest artifact。"""
    started_ms = now_ms()
    map_inputs = map_input_summary(args)
    managed_map_yaml, managed_map_yaml_source = resolve_managed_map_yaml(args, map_inputs)
    managed_runtime: dict[str, Any] = {
        "requested": bool(args.managed_runtime_opt_in),
        "started": False,
        "process_group": None,
        "cleanup_ok": True,
        "boundary": "default_read_only_existing_ros_graph_no_runtime_start",
        "map_yaml": managed_map_yaml,
        "map_yaml_source": managed_map_yaml_source,
        "wait_result": {"executed": False, "ok": False, "boundary": "managed_runtime_not_requested"},
        "cleanup_result": {"attempted": False, "ok": True, "boundary": "managed_runtime_not_requested"},
        "startup_error": None,
    }
    if args.managed_runtime_opt_in:
        if managed_map_yaml is None:
            managed_runtime["boundary"] = "managed_runtime_requested_but_map_yaml_missing"
            managed_runtime["startup_error"] = {
                "layer": "managed runtime",
                "reason": managed_map_yaml_source,
            }
        else:
            try:
                managed_runtime.update(start_managed_runtime(args, map_yaml=managed_map_yaml))
                managed_runtime["wait_result"] = wait_for_managed_runtime(args, managed_runtime)
            except Exception as exc:  # noqa: BLE001 - runtime 拉起失败必须结构化写回。
                managed_runtime["startup_error"] = compact_error(exc)
                managed_runtime["boundary"] = "managed_runtime_start_failed"

    ros2_check = run_ros(args, "command -v ros2 && ros2 --help >/dev/null", timeout_s=6.0)
    ros2_ok = bool(ros2_check.get("ok"))
    packages, package_results = package_checks(args) if ros2_ok else ({package: False for package in EXPECTED_PACKAGES}, {})
    topic_list = run_ros(args, "ros2 topic list", timeout_s=8.0) if ros2_ok else {"executed": False, "ok": False}
    node_list = run_ros(args, "ros2 node list", timeout_s=8.0) if ros2_ok else {"executed": False, "ok": False}
    lifecycle_active, lifecycle_results = lifecycle_checks(args) if ros2_ok else ({key: False for key in LOCALIZATION_LIFECYCLE_NODES}, {})
    echo_timeout_s = min(max(float(args.timeout_s), 4.0), 18.0)
    scan_once = run_ros(args, "timeout 6 ros2 topic echo --once /scan", timeout_s=echo_timeout_s) if ros2_ok else {"executed": False, "ok": False}
    map_once = run_ros(args, "timeout 8 ros2 topic echo --once /map", timeout_s=echo_timeout_s + 2.0) if ros2_ok else {"executed": False, "ok": False}
    amcl_pose_once = (
        run_ros(args, "timeout 8 ros2 topic echo --once /amcl_pose", timeout_s=echo_timeout_s + 2.0)
        if ros2_ok
        else {"executed": False, "ok": False}
    )
    initialpose_request_payload, initialpose_publish = maybe_publish_initialpose(args, ros2_ok)
    post_initialpose_amcl_pose_once = (
        run_ros(args, "timeout 8 ros2 topic echo --once /amcl_pose", timeout_s=echo_timeout_s + 2.0)
        if ros2_ok and initialpose_request_payload["enabled"]
        else {"executed": False, "ok": False, "boundary": "post_initialpose_probe_not_requested"}
    )
    map_to_odom_tf = (
        run_ros(args, "timeout 8 ros2 run tf2_ros tf2_echo map odom", timeout_s=echo_timeout_s + 2.0)
        if ros2_ok and initialpose_request_payload["enabled"]
        else {"executed": False, "ok": False, "boundary": "tf_probe_not_requested_without_initialpose_opt_in"}
    )
    map_to_base_link_tf = (
        run_ros(args, "timeout 8 ros2 run tf2_ros tf2_echo map base_link", timeout_s=echo_timeout_s + 2.0)
        if ros2_ok and initialpose_request_payload["enabled"]
        else {"executed": False, "ok": False, "boundary": "tf_probe_not_requested_without_initialpose_opt_in"}
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
    localization_tf_observed = {
        "map_to_odom": tf_echo_transform_observed(map_to_odom_tf),
        "map_to_base_link": tf_echo_transform_observed(map_to_base_link_tf),
    }
    localization_ready = True
    if initialpose_request_payload["enabled"]:
        localization_ready = bool(
            amcl_pose_observed
            and localization_tf_observed["map_to_odom"]
            and localization_tf_observed["map_to_base_link"]
        )
    runtime_ready = bool(scan_observed and map_observed and lifecycle_active.get("map_server") and lifecycle_active.get("amcl"))
    root_causes = classify_root_causes(
        map_inputs=map_inputs,
        ros2_ok=ros2_ok,
        packages=packages,
        lifecycle_active=lifecycle_active,
        scan_once_observed=scan_observed,
        map_once_observed=map_observed,
        amcl_pose_observed=amcl_pose_observed,
        localization_tf_observed=localization_tf_observed,
        initialpose_enabled=initialpose_request_payload["enabled"],
    )
    complete = bool(map_inputs["inputs_ready"] and runtime_ready and localization_ready and not root_causes)
    proof_status = "nav2_no_motion_localization_runtime_observed" if complete else "blocked_with_root_cause"

    if managed_runtime.get("started"):
        cleanup_result = cleanup_process_group(
            int(managed_runtime["process_group"]),
            managed_runtime.get("process"),
        )
        managed_runtime["cleanup_result"] = cleanup_result
        managed_runtime["cleanup_ok"] = bool(cleanup_result.get("ok"))
        try:
            Path(str(managed_runtime.get("params_path") or "")).unlink(missing_ok=True)
        except OSError:
            pass
    cleanup_guard = managed_runtime_cleanup_guard(managed_runtime.get("process_group"))
    blocked_commands_not_sent = list(BLOCKED_COMMAND_TOKENS)
    if not initialpose_request_payload["enabled"]:
        blocked_commands_not_sent.append("/initialpose")
    proof = {
        "status": proof_status,
        "evidence_ref": f"o10-amcl-nav2-runtime-{started_ms}",
        "evidence_type": "robot_runtime_material" if complete else "blocked_with_root_cause",
        "started_at_ms": started_ms,
        "generated_at_ms": now_ms(),
        "elapsed_ms": now_ms() - started_ms,
        "source_map_evidence_ref": map_inputs.get("source_evidence_ref"),
        "source_map_evidence_type": map_inputs.get("source_evidence_type"),
        "map_server_active": lifecycle_active.get("map_server", False),
        "amcl_active": lifecycle_active.get("amcl", False),
        # planner/controller 明确保持未启动，防止下游把 proof 错解成可发 goal 的 Nav2 graph。
        "planner_active": False,
        "controller_active": False,
        "path_generation_ready": False,
        "path_generated": False,
        "path_generation_boundary": "localization_only_no_planner_no_controller_no_goal_no_compute_path",
        "scan_consumed": runtime_ready,
        "map_consumed": runtime_ready,
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
        "managed_runtime_requested": bool(managed_runtime["requested"]),
        "managed_runtime_started": bool(managed_runtime.get("started")),
        "managed_runtime_process_group": managed_runtime.get("process_group"),
        "managed_runtime_cleanup_ok": bool(managed_runtime.get("cleanup_ok", True)) and bool(cleanup_guard.get("ok")),
        "managed_runtime_boundary": managed_runtime.get("boundary"),
        "managed_runtime_map_yaml": managed_runtime.get("map_yaml"),
        "managed_runtime_map_yaml_source": managed_runtime.get("map_yaml_source"),
        "managed_runtime_vendor_boundary": managed_runtime.get("vendor_boundary"),
        "root_causes": root_causes,
        "blockers": root_causes,
        "map_inputs": map_inputs,
        "commands": {
            "ros2_check": ros2_check,
            "package_checks": package_results,
            "topic_list": topic_list,
            "node_list": node_list,
            "lifecycle": lifecycle_results,
            "scan_once": scan_once,
            "map_once": map_once,
            "amcl_pose_once": amcl_pose_once,
            "initialpose_publish": initialpose_publish,
            "post_initialpose_amcl_pose_once": post_initialpose_amcl_pose_once,
            "map_to_odom_tf": map_to_odom_tf,
            "map_to_base_link_tf": map_to_base_link_tf,
            "initialpose_info": initialpose_info,
            "amcl_node_info": amcl_node_info,
            "map_server_info": map_server_info,
            "lifecycle_recheck": lifecycle_recheck,
            "managed_runtime": {
                "requested": managed_runtime["requested"],
                "started": managed_runtime.get("started"),
                "process_group": managed_runtime.get("process_group"),
                "map_yaml": managed_runtime.get("map_yaml"),
                "map_yaml_source": managed_runtime.get("map_yaml_source"),
                "wait_result": managed_runtime.get("wait_result"),
                "cleanup_result": managed_runtime.get("cleanup_result"),
                "cleanup_guard": cleanup_guard,
                "startup_error": managed_runtime.get("startup_error"),
                "log_path": managed_runtime.get("log_path"),
                "log_tail": preview_file(managed_runtime["log_path"]) if managed_runtime.get("log_path") else "",
            },
        },
        "not_proven": [
            "planner_server_runtime",
            "controller_server_runtime",
            "compute_path_call",
            "nav2_goal_execution",
            "controller_cmd_vel_output",
            "fixed_route_execution",
            "delivery_success",
            "hil_pass",
            "safe_to_control_true",
        ],
        "collector_mode": (
            "managed_no_motion_localization_runtime"
            if managed_runtime["requested"]
            else "read_only_existing_ros_graph_no_motion"
        ),
        "blocked_commands_not_sent": blocked_commands_not_sent,
        "blocked_devices_not_opened": ["/dev/ttyS5"],
        **safety_flags(),
    }
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
    parser.add_argument("--ros-setup", default=DEFAULT_ROS_SETUP)
    parser.add_argument("--onboard-setup", default=DEFAULT_ONBOARD_SETUP)
    parser.add_argument("--workdir", default=DEFAULT_WORKDIR)
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    payload = build_proof(args)
    write_json_atomic(args.output, payload)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if payload["proof"]["status"] == "nav2_no_motion_localization_runtime_observed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
