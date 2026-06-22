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


def start_managed_autonomous_runtime(args: argparse.Namespace) -> dict[str, Any]:
    """短暂启动 Nav2 执行 runtime，让 NavigateToPose action server 可用。"""
    if not args.managed_runtime_opt_in:
        return {"requested": False, "started": False, "cleanup": {"ok": True, "boundary": "not_requested"}}
    if not args.managed_map_yaml:
        return {"requested": True, "started": False, "error": {"type": "ValueError", "message": "managed_map_yaml is required"}}
    log_path = f"/tmp/o11_nav2_goal_execution_{now_ms()}.log"
    initialpose_payload = json.dumps(
        {
            # stamp=0 让 AMCL 用最新 TF，避免初始位姿刚发布时因为 odom->base_link 时间略早而外推失败。
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
            "ros2 run ros2_trashbot_hardware esp32_bridge --ros-args "
            "-p serial_port:=/dev/ttyS5 -p serial_baudrate:=115200 -p command_mode:=speed "
            "-p track_width_m:=0.172 -p max_wheel_speed_mps:=1.3",
        ),
        (
            "lidar_driver",
            "ros2 run ros2_trashbot_hardware lidar_driver --ros-args "
            "-p serial_port:=/dev/ttyACM0 -p serial_baudrate:=150000 -p frame_id:=laser_frame "
            "-p scan_topic:=/scan -p publish_raw_packets:=false",
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
        (
            "amcl",
            f"ros2 run nav2_amcl amcl --ros-args --params-file {DEFAULT_NAV2_PARAMS} -r __node:=amcl",
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
            "-p node_names:=\"[map_server, amcl]\" "
            "-r __node:=lifecycle_manager_localization",
        ),
        (
            "initialpose_seed",
            "ros2 topic pub --once /initialpose geometry_msgs/msg/PoseWithCovarianceStamped "
            f"{shlex.quote(initialpose_payload)}",
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
    ]
    for role, role_command in localization_commands:
        launch_lines.append(f"printf '%s\\n' 'starting role={role}' >> {shlex.quote(log_path)}")
        launch_lines.append(f"({role_command}) >> {shlex.quote(log_path)} 2>&1 & pids+=($!)")
    # map_server/AMCL 先进入 active，并在执行层启动前发布 initialpose，避免 planner costmap 等不到 map->base_link。
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
        "startup_s": float(args.managed_startup_s),
        "initialpose": {
            "frame_id": str(args.initialpose_frame_id),
            "x": float(args.initialpose_x),
            "y": float(args.initialpose_y),
            "yaw": float(args.initialpose_yaw),
        },
        "log_path": log_path,
        "command": command,
        "process": process,
    }


def wait_for_nav2_lifecycle_active(timeout_s: float, *, log_path: str = "") -> dict[str, Any]:
    """等待执行层 lifecycle 全部 active；优先消费本 helper 的 lifecycle 日志，避免 ros2 CLI discovery 抖动。"""
    required_nodes = ("planner_server", "controller_server", "bt_navigator", "behavior_server")
    deadline = time.monotonic() + max(float(timeout_s), 1.0)
    history: list[dict[str, Any]] = []
    latest_states: dict[str, str] = {}
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
        latest_states = {}
        all_active = True
        for node_name in required_nodes:
            command = ["ros2", "lifecycle", "get", f"/{node_name}"]
            try:
                completed = subprocess.run(command, check=False, text=True, capture_output=True, timeout=3.0)
                output = f"{completed.stdout}\n{completed.stderr}".strip()
                state = output.splitlines()[0].strip() if output else f"returncode_{completed.returncode}"
            except Exception as exc:  # noqa: BLE001
                state = compact_error(exc)["message"] or type(exc).__name__
            latest_states[node_name] = state
            if "active [3]" not in state:
                all_active = False
        history.append({"at_ms": now_ms(), "states": dict(latest_states), "all_active": all_active})
        if all_active:
            return {
                "ok": True,
                "states": latest_states,
                "history": history[-12:],
                "timeout_s": float(timeout_s),
            }
        time.sleep(1.0)
    return {
        "ok": False,
        "states": latest_states,
        "history": history[-12:],
        "timeout_s": float(timeout_s),
        "reason": "nav2_lifecycle_active_timeout",
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
    parser.add_argument("--server-timeout-s", type=float, default=5.0)
    parser.add_argument("--result-timeout-s", type=float, default=8.0)
    parser.add_argument("--max-feedback-samples", type=int, default=8)
    parser.add_argument("--managed-runtime-opt-in", action="store_true")
    parser.add_argument("--managed-map-yaml", default="")
    parser.add_argument("--managed-startup-s", type=float, default=2.0)
    parser.add_argument("--managed-ready-timeout-s", type=float, default=45.0)
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
