#!/usr/bin/env python3
"""Bounded Nav2 NavigateToPose execution proof collector."""

from __future__ import annotations

import argparse
import json
import math
import os
import shlex
import signal
import subprocess
import time
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.upper_robot_api.v1.nav2_goal_execution_proof"
NAVIGATE_ACTION_CANDIDATES = ("/navigate_to_pose", "navigate_to_pose")
DEFAULT_ONBOARD_SETUP = "/root/rober/onboard/install/setup.bash"
DEFAULT_WORKDIR = "/root/rober/onboard"
DEFAULT_NAV2_PARAMS = "/root/rober/onboard/src/ros2_trashbot_nav/config/nav2_params.yaml"
DEFAULT_BASE_COMMAND_MODE = "ros"
ALLOWED_BASE_COMMAND_MODES = frozenset({"ros", "speed", "pwm"})
DEFAULT_PWM_MIN_ABS = 164
DEFAULT_PWM_MAX_ABS = 164


def now_ms() -> int:
    """统一毫秒时间，便于和 PC proxy、上位机 latest artifact 对齐。"""
    return int(time.time() * 1000)


def safe_flags(*, executed: bool) -> dict[str, Any]:
    """执行证明仍不等于交付成功，安全与主动作字段保持关闭。"""
    return {
        "safe_to_control": False,
        "primary_actions_enabled": False,
        "delivery_success": False,
        "hil_pass": False,
        "robot_control_executed": executed,
        "sends_motion_commands": executed,
        "publishes_cmd_vel": "nav2_controller_may_publish_cmd_vel_when_goal_is_active" if executed else False,
        "sends_base_motion_commands": False,
        "calls_base_manual": False,
        "uses_base_uart": False,
    }


def compact_error(exc: BaseException) -> dict[str, str]:
    """异常只保留短类型和消息，避免 artifact 被 traceback 淹没。"""
    return {"type": type(exc).__name__, "message": str(exc)[:500]}


def normalize_base_command_mode(value: str) -> str:
    """Nav2 执行只允许厂商已定义的三种底盘控制面，避免请求体拼任意 ROS 参数。"""
    mode = str(value or DEFAULT_BASE_COMMAND_MODE).strip().lower()
    return mode if mode in ALLOWED_BASE_COMMAND_MODES else DEFAULT_BASE_COMMAND_MODE


def wheel_zero_proof_status_for_mode(base_command_mode: str) -> str:
    """按真实底盘控制模式标记缺口，避免 ROS 重跑后仍被误诊断成 PWM 问题。"""
    command_mode = normalize_base_command_mode(base_command_mode)
    return f"nav2_goal_succeeded_with_{command_mode}_commands_but_wheel_lr_zero"


def managed_esp32_bridge_command(
    feedback_log_path: str,
    command_log_path: str = "",
    base_command_mode: str = DEFAULT_BASE_COMMAND_MODE,
) -> str:
    """O11 托管 Nav2 默认走 vendor T=13 ROS 控制；现场可切回 speed/pwm 做 A/B 复验。"""
    command_mode = normalize_base_command_mode(base_command_mode)
    command_debug_arg = (
        f" -p command_debug_log_path:={shlex.quote(command_log_path)}" if command_log_path else ""
    )
    return (
        "ros2 run ros2_trashbot_hardware esp32_bridge --ros-args "
        "-p serial_port:=/dev/ttyS5 -p serial_baudrate:=115200 "
        f"-p command_mode:={command_mode} "
        "-p track_width_m:=0.172 -p max_wheel_speed_mps:=1.3 "
        f"-p pwm_min_abs:={DEFAULT_PWM_MIN_ABS} -p pwm_max_abs:={DEFAULT_PWM_MAX_ABS} "
        f"-p feedback_debug_log_path:={shlex.quote(feedback_log_path)}"
        f"{command_debug_arg}"
    )


def start_managed_autonomous_runtime(args: argparse.Namespace) -> dict[str, Any]:
    """短暂启动 Nav2 执行 runtime，让 NavigateToPose action server 可用。"""
    if not args.managed_runtime_opt_in:
        return {"requested": False, "started": False, "cleanup": {"ok": True, "boundary": "not_requested"}}
    if not args.managed_map_yaml:
        return {"requested": True, "started": False, "error": {"type": "ValueError", "message": "managed_map_yaml is required"}}
    runtime_ms = now_ms()
    log_path = f"/tmp/o11_nav2_goal_execution_{runtime_ms}.log"
    base_feedback_log_path = f"/tmp/o11_wave_rover_feedback_{runtime_ms}.jsonl"
    base_command_log_path = f"/tmp/o11_wave_rover_command_{runtime_ms}.jsonl"
    base_command_mode = normalize_base_command_mode(args.base_command_mode)
    initialpose_payload = json.dumps(
        {
            # stamp=0 保留旧 initialpose 兼容；当前 O11 使用静态 map->odom，不依赖 AMCL 或雷达。
            "header": {"stamp": {"sec": 0, "nanosec": 0}, "frame_id": str(args.initialpose_frame_id)},
            "pose": {
                "pose": {
                    "position": {"x": float(args.initialpose_x), "y": float(args.initialpose_y), "z": 0.0},
                    "orientation": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": math.sin(float(args.initialpose_yaw) / 2.0),
                        "w": math.cos(float(args.initialpose_yaw) / 2.0),
                    },
                },
                "covariance": [0.0] * 36,
            },
        },
        ensure_ascii=False,
    )
    localization_commands = [
        (
            "esp32_bridge",
            managed_esp32_bridge_command(base_feedback_log_path, base_command_log_path, base_command_mode),
        ),
        (
            "static_tf_map_odom",
            "ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 map odom",
        ),
        (
            "static_tf_base_laser",
            "ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 base_link laser_frame",
        ),
        (
            "map_server",
            f"ros2 run nav2_map_server map_server --ros-args --params-file {DEFAULT_NAV2_PARAMS} "
            f"-p yaml_filename:={args.managed_map_yaml} -r __node:=map_server",
        ),
    ]
    navigation_commands = [
        (
            "planner_server",
            f"ros2 run nav2_planner planner_server --ros-args --params-file {DEFAULT_NAV2_PARAMS} -r __node:=planner_server",
        ),
        (
            "controller_server",
            f"ros2 run nav2_controller controller_server --ros-args --params-file {DEFAULT_NAV2_PARAMS} -r __node:=controller_server",
        ),
        (
            "bt_navigator",
            f"ros2 run nav2_bt_navigator bt_navigator --ros-args --params-file {DEFAULT_NAV2_PARAMS} -r __node:=bt_navigator",
        ),
        (
            "behavior_server",
            f"ros2 run nav2_behaviors behavior_server --ros-args --params-file {DEFAULT_NAV2_PARAMS} -r __node:=behavior_server",
        ),
    ]
    lifecycle_commands = [
        (
            "lifecycle_manager_localization",
            "ros2 run nav2_lifecycle_manager lifecycle_manager --ros-args "
            "-p autostart:=true "
            "-p node_names:=\"[map_server]\" "
            "-r __node:=lifecycle_manager_localization",
        ),
        (
            "initialpose_seed",
            "true",
        ),
        (
            "lifecycle_manager_navigation",
            "ros2 run nav2_lifecycle_manager lifecycle_manager --ros-args "
            "-p autostart:=true "
            "-p node_names:=\"[planner_server, controller_server, bt_navigator, behavior_server]\" "
            "-r __node:=lifecycle_manager_navigation",
        ),
    ]
    launch_lines = [
        "set -e",
        "source /opt/ros/humble/setup.bash",
        f"if [ -f {DEFAULT_ONBOARD_SETUP} ]; then source {DEFAULT_ONBOARD_SETUP}; fi",
        "pids=()",
        "cleanup(){ for pid in \"${pids[@]}\"; do kill -INT \"$pid\" 2>/dev/null || true; done; wait || true; }",
        "trap cleanup EXIT INT TERM",
        f"printf '%s\\n' 'log_path={log_path}' > {shlex.quote(log_path)}",
        f"printf '%s\\n' 'managed_map_yaml={args.managed_map_yaml}' >> {shlex.quote(log_path)}",
        f"printf '%s\\n' 'base_command_mode={base_command_mode}' >> {shlex.quote(log_path)}",
        f"printf '%s\\n' 'base_feedback_log_path={base_feedback_log_path}' >> {shlex.quote(log_path)}",
        f"printf '%s\\n' 'base_command_log_path={base_command_log_path}' >> {shlex.quote(log_path)}",
    ]
    for role, role_command in localization_commands:
        launch_lines.append(f"printf '%s\\n' 'starting role={role}' >> {shlex.quote(log_path)}")
        launch_lines.append(f"({role_command}) >> {shlex.quote(log_path)} 2>&1 & pids+=($!)")
    # map_server 与静态 map->odom 先就绪，避免 planner/controller 等不到 map->base_link。
    launch_lines.append("sleep 4")
    role, role_command = lifecycle_commands[0]
    launch_lines.append(f"printf '%s\\n' 'starting role={role}' >> {shlex.quote(log_path)}")
    launch_lines.append(f"({role_command}) >> {shlex.quote(log_path)} 2>&1 & pids+=($!)")
    launch_lines.append("sleep 5")
    role, role_command = lifecycle_commands[1]
    launch_lines.append(f"printf '%s\\n' 'starting role={role}' >> {shlex.quote(log_path)}")
    launch_lines.append(f"({role_command}) >> {shlex.quote(log_path)} 2>&1 || true")
    launch_lines.append("sleep 4")
    for role, role_command in navigation_commands:
        launch_lines.append(f"printf '%s\\n' 'starting role={role}' >> {shlex.quote(log_path)}")
        launch_lines.append(f"({role_command}) >> {shlex.quote(log_path)} 2>&1 & pids+=($!)")
    launch_lines.append("sleep 3")
    role, role_command = lifecycle_commands[2]
    launch_lines.append(f"printf '%s\\n' 'starting role={role}' >> {shlex.quote(log_path)}")
    launch_lines.append(f"({role_command}) >> {shlex.quote(log_path)} 2>&1 & pids+=($!)")
    launch_lines.append("wait")
    command = "; ".join(launch_lines)
    process = subprocess.Popen(
        ["bash", "-lc", command],
        cwd=DEFAULT_WORKDIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    # shell 内部已经按定位/执行两段 sleep；这里仅给进程组一点启动余量，真正 readiness 由 lifecycle 轮询判断。
    time.sleep(min(max(float(args.managed_startup_s), 0.0), 2.0))
    return {
        "requested": True,
        "started": True,
        "process_group": process.pid,
        "pid": process.pid,
        "map_yaml": args.managed_map_yaml,
        "runtime_ms": runtime_ms,
        "startup_s": float(args.managed_startup_s),
        "initialpose": {
            "frame_id": str(args.initialpose_frame_id),
            "x": float(args.initialpose_x),
            "y": float(args.initialpose_y),
            "yaw": float(args.initialpose_yaw),
        },
        "base_command_mode": base_command_mode,
        "base_pwm_min_abs": DEFAULT_PWM_MIN_ABS,
        "base_pwm_max_abs": DEFAULT_PWM_MAX_ABS,
        "base_feedback_log_path": base_feedback_log_path,
        "base_command_log_path": base_command_log_path,
        "log_path": log_path,
        "command": command,
        "process": process,
    }


def wait_for_nav2_lifecycle_active(timeout_s: float, *, log_path: str = "") -> dict[str, Any]:
    """等待执行层 lifecycle 全部 active；只消费本 helper 日志，避免 ros2 CLI 服务轮询拖慢 lifecycle。"""
    required_nodes = ("planner_server", "controller_server", "bt_navigator", "behavior_server")
    deadline = time.monotonic() + max(float(timeout_s), 1.0)
    history: list[dict[str, Any]] = []
    while time.monotonic() < deadline:
        log_tail = preview_text_file(log_path, max_chars=12000)
        navigation_active_observed = any(
            "lifecycle_manager_navigation" in line and "Managed nodes are active" in line
            for line in log_tail.splitlines()
        )
        if navigation_active_observed:
            active_states = {node_name: "active [3] (observed_in_lifecycle_manager_log)" for node_name in required_nodes}
            history.append({"at_ms": now_ms(), "states": active_states, "all_active": True, "source": "lifecycle_manager_log"})
            return {
                "ok": True,
                "states": active_states,
                "history": history[-12:],
                "timeout_s": float(timeout_s),
                "source": "lifecycle_manager_log",
            }
        history.append(
            {
                "at_ms": now_ms(),
                "states": {node_name: "waiting_for_lifecycle_manager_log" for node_name in required_nodes},
                "all_active": False,
                "source": "lifecycle_manager_log_tail",
            }
        )
        time.sleep(1.0)
    return {
        "ok": False,
        "states": {node_name: "not_observed_in_lifecycle_manager_log" for node_name in required_nodes},
        "history": history[-12:],
        "timeout_s": float(timeout_s),
        "reason": "nav2_lifecycle_active_timeout",
        "source": "lifecycle_manager_log_tail",
    }


def cleanup_managed_runtime(runtime: dict[str, Any]) -> dict[str, Any]:
    """清理 O11 托管的 autonomous runtime，避免 Nav2/bridge 后台遗留。"""
    process = runtime.get("process")
    pgid = runtime.get("process_group")
    if not process or not pgid:
        return {"ok": True, "boundary": "no_process_started"}
    try:
        os.killpg(int(pgid), signal.SIGINT)
        try:
            process.wait(timeout=4.0)
        except subprocess.TimeoutExpired:
            os.killpg(int(pgid), signal.SIGKILL)
            process.wait(timeout=4.0)
        stdout, stderr = process.communicate(timeout=1.0)
        return {
            "ok": True,
            "returncode": process.returncode,
            "stdout_preview": (stdout or "")[-2000:],
            "stderr_preview": (stderr or "")[-2000:],
            "log_path": runtime.get("log_path"),
            "log_tail": preview_text_file(str(runtime.get("log_path") or ""), max_chars=3000),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": compact_error(exc)}


def preview_text_file(path: str, *, max_chars: int) -> str:
    """读取短日志尾部；日志只用于定位 Nav2 lifecycle，不进入安全结论。"""
    if not path:
        return ""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")[-max_chars:]
    except OSError:
        return ""


def summarize_feedback_debug_log(path: str) -> dict[str, Any]:
    """汇总 bridge 写出的 T=1001 反馈，作为 Nav2 是否真正触底盘的材料。"""
    attitude_pairs: list[dict[str, float]] = []
    summary: dict[str, Any] = {
        "path": path,
        "exists": False,
        "sample_count": 0,
        "nonzero_sample_count": 0,
        "wheel_feedback_lr_nonzero_proven": False,
        "imu_attitude_delta_observed": False,
        "imu_attitude_delta_summary": {
            "source": "wave_rover_t1001_roll_pitch",
            "matched_sample_count": 0,
            "max_abs_roll_delta": 0.0,
            "max_abs_pitch_delta": 0.0,
            "threshold_degrees": 1.0,
        },
        "latest_pair": None,
        "latest_nonzero_pair": None,
        "malformed_line_count": 0,
        "source": "wave_rover_uart_t1001_feedback_debug_log",
    }
    if not path:
        summary["reason"] = "feedback_debug_log_path_empty"
        return summary
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        summary["reason"] = "feedback_debug_log_unreadable"
        summary["error"] = compact_error(exc)
        return summary

    summary["exists"] = True
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            summary["malformed_line_count"] += 1
            continue
        left_speed = record.get("left_speed")
        right_speed = record.get("right_speed")
        if not isinstance(left_speed, (int, float)) or not isinstance(right_speed, (int, float)):
            summary["malformed_line_count"] += 1
            continue
        pair = {
            "left_speed": float(left_speed),
            "right_speed": float(right_speed),
            "observed_at_unix_s": record.get("observed_at_unix_s"),
        }
        summary["sample_count"] += 1
        summary["latest_pair"] = pair
        if abs(float(left_speed)) > 1e-6 or abs(float(right_speed)) > 1e-6:
            summary["nonzero_sample_count"] += 1
            summary["latest_nonzero_pair"] = pair
        roll = record.get("roll")
        pitch = record.get("pitch")
        if isinstance(roll, (int, float)) and isinstance(pitch, (int, float)):
            attitude_pairs.append({"roll": float(roll), "pitch": float(pitch)})

    summary["wheel_feedback_lr_nonzero_proven"] = summary["nonzero_sample_count"] > 0
    if attitude_pairs:
        base_roll = attitude_pairs[0]["roll"]
        base_pitch = attitude_pairs[0]["pitch"]
        max_roll_delta = max(abs(item["roll"] - base_roll) for item in attitude_pairs)
        max_pitch_delta = max(abs(item["pitch"] - base_pitch) for item in attitude_pairs)
        threshold = float(summary["imu_attitude_delta_summary"]["threshold_degrees"])
        summary["imu_attitude_delta_summary"].update(
            {
                "matched_sample_count": len(attitude_pairs),
                "max_abs_roll_delta": round(max_roll_delta, 6),
                "max_abs_pitch_delta": round(max_pitch_delta, 6),
            }
        )
        # 姿态变化只能作为“车身有运动迹象”，不能替代 L/R 轮速闭环或交付成功。
        summary["imu_attitude_delta_observed"] = max(max_roll_delta, max_pitch_delta) >= threshold
    if summary["sample_count"] == 0 and "reason" not in summary:
        summary["reason"] = "feedback_debug_log_has_no_valid_samples"
    return summary


def summarize_command_debug_log(path: str) -> dict[str, Any]:
    """汇总 /cmd_vel 转 vendor JSON 的命令日志，定位 Nav2 是否真的发了非零底盘命令。"""
    summary: dict[str, Any] = {
        "path": path,
        "exists": False,
        "sample_count": 0,
        "nonzero_command_count": 0,
        "nonzero_command_observed": False,
        "command_mode_counts": {},
        "latest_nonzero_command_mode": "not_loaded",
        "latest_command": None,
        "latest_nonzero_command": None,
        "malformed_line_count": 0,
        "source": "esp32_bridge_cmd_vel_command_debug_log",
    }
    if not path:
        summary["reason"] = "command_debug_log_path_empty"
        return summary
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        summary["reason"] = "command_debug_log_unreadable"
        summary["error"] = compact_error(exc)
        return summary

    summary["exists"] = True
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            summary["malformed_line_count"] += 1
            continue
        command = record.get("vendor_command")
        if not isinstance(command, dict):
            summary["malformed_line_count"] += 1
            continue
        left = command.get("L")
        right = command.get("R")
        ros_x = command.get("X")
        ros_z = command.get("Z")
        values = [value for value in (left, right, ros_x, ros_z) if isinstance(value, (int, float))]
        is_nonzero = any(abs(float(value)) > 1e-6 for value in values)
        command_mode = str(record.get("command_mode") or "").strip().lower()
        if not command_mode:
            # 历史日志可能没有 command_mode；按 vendor T 值补一个诊断口径，便于现场区分 ROS/T=13 与 PWM/T=11。
            command_mode = {13: "ros", 1: "speed", 11: "pwm"}.get(command.get("T"), "unknown")
        short_record = {
            "observed_at_unix_s": record.get("observed_at_unix_s"),
            "linear_x": record.get("linear_x"),
            "angular_z": record.get("angular_z"),
            "command_mode": command_mode,
            "vendor_command": command,
        }
        summary["sample_count"] += 1
        summary["command_mode_counts"][command_mode] = summary["command_mode_counts"].get(command_mode, 0) + 1
        summary["latest_command"] = short_record
        if is_nonzero:
            summary["nonzero_command_count"] += 1
            summary["latest_nonzero_command_mode"] = command_mode
            summary["latest_nonzero_command"] = short_record

    summary["nonzero_command_observed"] = summary["nonzero_command_count"] > 0
    if summary["sample_count"] == 0 and "reason" not in summary:
        summary["reason"] = "command_debug_log_has_no_valid_samples"
    return summary


def write_json_atomic(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    """latest artifact 原子落盘，确保 PC 读到的是完整 JSON。"""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(target)
    return {"ok": True, "path": str(target), "bytes_written": target.stat().st_size}


def yaw_to_quaternion(yaw: float) -> tuple[float, float]:
    """Nav2 目标只需要平面 yaw；转成 z/w 四元数。"""
    return math.sin(yaw / 2.0), math.cos(yaw / 2.0)


def status_label(status_code: int | None) -> str:
    """action_msgs/GoalStatus 数字转短标签，缺包时也能稳定回读。"""
    labels = {
        0: "unknown",
        1: "accepted",
        2: "executing",
        3: "canceling",
        4: "succeeded",
        5: "canceled",
        6: "aborted",
    }
    return labels.get(status_code, "not_received")


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    """发送 NavigateToPose，等待短窗口，超时则 cancel 并记录结果。"""
    started_ms = now_ms()
    feedback_samples: list[dict[str, Any]] = []
    goal_z, goal_w = yaw_to_quaternion(float(args.goal_yaw))
    goal_request = {
        "frame_id": str(args.goal_frame_id),
        "x": float(args.goal_x),
        "y": float(args.goal_y),
        "yaw": float(args.goal_yaw),
        "orientation_z": goal_z,
        "orientation_w": goal_w,
        "server_timeout_s": float(args.server_timeout_s),
        "result_timeout_s": float(args.result_timeout_s),
    }
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "generated_at_ms": started_ms,
        "status": "blocked",
        "evidence_ref": f"o11-nav2-goal-execution-{started_ms}",
        "goal_request": goal_request,
        "managed_runtime": {"requested": bool(args.managed_runtime_opt_in), "started": False},
        "action_name": None,
        "action_server_available": False,
        "goal_sent": False,
        "goal_accepted": False,
        "result_received": False,
        "result_status_code": None,
        "result_status": "not_received",
        "cancel_requested": False,
        "cancel_response": None,
        "feedback_sample_count": 0,
        "feedback_samples": feedback_samples,
        "elapsed_ms": 0,
        "error": None,
        "not_proven": ["delivery_success", "operator_dropoff_confirmation"],
        **safe_flags(executed=False),
    }
    try:
        import rclpy
        from action_msgs.msg import GoalStatus
        from action_msgs.srv import CancelGoal
        from geometry_msgs.msg import PoseStamped
        from nav2_msgs.action import NavigateToPose
        from rclpy.action import ActionClient
    except Exception as exc:  # noqa: BLE001
        result.update({"status": "ros_python_import_failed", "error": compact_error(exc), "elapsed_ms": now_ms() - started_ms})
        return result

    node = None
    initialized = False
    managed_runtime: dict[str, Any] = {"requested": bool(args.managed_runtime_opt_in), "started": False}
    try:
        managed_runtime = start_managed_autonomous_runtime(args)
        result["managed_runtime"] = {key: value for key, value in managed_runtime.items() if key != "process"}
        if args.managed_runtime_opt_in:
            lifecycle_ready = wait_for_nav2_lifecycle_active(
                float(args.managed_ready_timeout_s),
                log_path=str(managed_runtime.get("log_path") or ""),
            )
            managed_runtime["lifecycle_ready"] = lifecycle_ready
            result["managed_runtime"]["lifecycle_ready"] = lifecycle_ready
            if not lifecycle_ready.get("ok"):
                result.update(
                    {
                        "status": "nav2_lifecycle_not_active",
                        "elapsed_ms": now_ms() - started_ms,
                        "not_proven": ["nav2_lifecycle_active", "nav2_goal_execution", "delivery_success"],
                    }
                )
                return result
        rclpy.init(args=[])
        initialized = True
        node = rclpy.create_node("o11_nav2_goal_execution_probe")

        def build_goal() -> Any:
            goal_msg = NavigateToPose.Goal()
            goal_msg.pose = PoseStamped()
            goal_msg.pose.header.frame_id = str(args.goal_frame_id)
            goal_msg.pose.header.stamp = node.get_clock().now().to_msg()
            goal_msg.pose.pose.position.x = float(args.goal_x)
            goal_msg.pose.pose.position.y = float(args.goal_y)
            goal_msg.pose.pose.position.z = 0.0
            goal_msg.pose.pose.orientation.z = goal_z
            goal_msg.pose.pose.orientation.w = goal_w
            return goal_msg

        def on_feedback(feedback_msg: Any) -> None:
            feedback = getattr(feedback_msg, "feedback", None)
            if feedback is None or len(feedback_samples) >= int(args.max_feedback_samples):
                return
            distance_remaining = getattr(feedback, "distance_remaining", None)
            navigation_time = getattr(feedback, "navigation_time", None)
            feedback_samples.append(
                {
                    "distance_remaining": float(distance_remaining) if distance_remaining is not None else None,
                    "navigation_time_sec": int(getattr(navigation_time, "sec", 0)) if navigation_time is not None else None,
                    "navigation_time_nanosec": int(getattr(navigation_time, "nanosec", 0)) if navigation_time is not None else None,
                }
            )

        goal_handle = None
        action_client = None
        for action_name in NAVIGATE_ACTION_CANDIDATES:
            candidate = ActionClient(node, NavigateToPose, action_name)
            if candidate.wait_for_server(timeout_sec=float(args.server_timeout_s)):
                action_client = candidate
                result["action_name"] = action_name
                result["action_server_available"] = True
                break
        if action_client is None:
            result.update({"status": "navigate_to_pose_action_unavailable", "elapsed_ms": now_ms() - started_ms})
            return result

        goal_future = action_client.send_goal_async(build_goal(), feedback_callback=on_feedback)
        rclpy.spin_until_future_complete(node, goal_future, timeout_sec=max(float(args.server_timeout_s), 1.0))
        goal_handle = goal_future.result()
        if goal_handle is None:
            result.update({"status": "goal_handle_missing", "elapsed_ms": now_ms() - started_ms})
            return result
        result["goal_sent"] = True
        result["goal_accepted"] = bool(getattr(goal_handle, "accepted", False))
        result.update(safe_flags(executed=result["goal_accepted"]))
        if not result["goal_accepted"]:
            result.update({"status": "goal_rejected", "elapsed_ms": now_ms() - started_ms})
            return result

        result_future = goal_handle.get_result_async()
        deadline = time.monotonic() + float(args.result_timeout_s)
        while time.monotonic() < deadline and not result_future.done():
            rclpy.spin_once(node, timeout_sec=0.1)
        if result_future.done():
            action_result = result_future.result()
            status_code = int(getattr(action_result, "status", GoalStatus.STATUS_UNKNOWN))
            result.update(
                {
                    "status": "goal_succeeded" if status_code == GoalStatus.STATUS_SUCCEEDED else f"goal_{status_label(status_code)}",
                    "result_received": True,
                    "result_status_code": status_code,
                    "result_status": status_label(status_code),
                    "delivery_success": False,
                    "not_proven": ["delivery_success", "operator_dropoff_confirmation"],
                }
            )
        else:
            result["cancel_requested"] = True
            cancel_future = goal_handle.cancel_goal_async()
            rclpy.spin_until_future_complete(node, cancel_future, timeout_sec=2.0)
            cancel_result = cancel_future.result()
            result["cancel_response"] = {
                "return_code": int(getattr(cancel_result, "return_code", -1)) if cancel_result is not None else None,
                "goals_canceling": len(getattr(cancel_result, "goals_canceling", []) or []) if cancel_result is not None else 0,
                "accepted": (
                    int(getattr(cancel_result, "return_code", -1)) == CancelGoal.Response.ERROR_NONE
                    if cancel_result is not None
                    else False
                ),
            }
            result["status"] = "goal_timeout_cancel_requested"
            result["not_proven"] = ["nav2_goal_result", "delivery_success", "operator_dropoff_confirmation"]
    except Exception as exc:  # noqa: BLE001
        result.update({"status": "goal_execution_exception", "error": compact_error(exc)})
    finally:
        cleanup = cleanup_managed_runtime(managed_runtime)
        base_feedback_summary = summarize_feedback_debug_log(str(managed_runtime.get("base_feedback_log_path") or ""))
        base_command_summary = summarize_command_debug_log(str(managed_runtime.get("base_command_log_path") or ""))
        result["base_feedback_summary"] = base_feedback_summary
        result["base_command_summary"] = base_command_summary
        result["base_command_mode"] = managed_runtime.get("base_command_mode") or normalize_base_command_mode(args.base_command_mode)
        result_base_command_mode = str(result["base_command_mode"])
        base_feedback_nonzero = bool(base_feedback_summary.get("wheel_feedback_lr_nonzero_proven"))
        base_command_nonzero = bool(base_command_summary.get("nonzero_command_observed"))
        result["base_motion_command_nonzero_proven"] = base_command_nonzero
        if result.get("goal_accepted"):
            # 只有 goal 被 Nav2 接受后，才把底盘 UART 和运动命令标记为本轮执行材料。
            result["uses_base_uart"] = bool(managed_runtime.get("base_feedback_log_path"))
            result["sends_base_motion_commands"] = True
        if result.get("status") == "goal_succeeded" and base_feedback_nonzero:
            result["hil_pass"] = True
            result["nav2_goal_execution_proven"] = True
            result["proof_status"] = "nav2_goal_succeeded_with_nonzero_base_feedback"
            result["not_proven"] = ["delivery_success", "operator_dropoff_confirmation"]
        else:
            result["nav2_goal_execution_proven"] = False
            if result.get("status") == "goal_succeeded" and base_command_nonzero and not base_feedback_nonzero:
                # 非零命令已到达 bridge，但完整路线仍必须等待同窗口 T=1001 L/R 非零复验。
                result["proof_status"] = wheel_zero_proof_status_for_mode(result_base_command_mode)
                result["not_proven"] = [
                    "wheel_feedback_lr_nonzero",
                    "delivery_success",
                    "operator_dropoff_confirmation",
                ]
            elif result.get("status") == "goal_succeeded":
                result["proof_status"] = "nav2_goal_succeeded_without_base_feedback_nonzero"
        result["managed_runtime"] = {
            **{key: value for key, value in managed_runtime.items() if key != "process"},
            "cleanup": cleanup,
        }
        result["feedback_sample_count"] = len(feedback_samples)
        result["elapsed_ms"] = now_ms() - started_ms
        if node is not None:
            node.destroy_node()
        if initialized:
            rclpy.shutdown()
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="/root/rober/onboard/runtime/nav2_goal_execution_latest.json")
    parser.add_argument("--goal-frame-id", default="map")
    parser.add_argument("--goal-x", type=float, required=True)
    parser.add_argument("--goal-y", type=float, required=True)
    parser.add_argument("--goal-yaw", type=float, default=0.0)
    parser.add_argument("--server-timeout-s", type=float, default=12.0)
    parser.add_argument("--result-timeout-s", type=float, default=8.0)
    parser.add_argument("--max-feedback-samples", type=int, default=8)
    parser.add_argument("--managed-runtime-opt-in", action="store_true")
    parser.add_argument("--managed-map-yaml", default="")
    parser.add_argument("--managed-startup-s", type=float, default=2.0)
    parser.add_argument("--managed-ready-timeout-s", type=float, default=90.0)
    parser.add_argument("--base-command-mode", choices=sorted(ALLOWED_BASE_COMMAND_MODES), default=DEFAULT_BASE_COMMAND_MODE)
    parser.add_argument("--initialpose-frame-id", default="map")
    parser.add_argument("--initialpose-x", type=float, default=0.0)
    parser.add_argument("--initialpose-y", type=float, default=0.0)
    parser.add_argument("--initialpose-yaw", type=float, default=0.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_payload(args)
    payload["artifact"] = {"path": args.output, "write": write_json_atomic(args.output, payload)}
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if payload["status"] == "goal_succeeded" else 2


if __name__ == "__main__":
    raise SystemExit(main())
