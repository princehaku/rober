#!/usr/bin/env python3
"""生成现场路线证据预检 JSON。

该工具只做只读探测和命令模板整理，不执行导航、建图、速度发布或底盘运动。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import platform
import re
import shlex
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.board_field_evidence_preflight.v1"
REQUIRED_PACKAGES = [
    "ros2_trashbot_bringup",
    "ros2_trashbot_nav",
    "ros2_trashbot_hardware",
    "ros2_trashbot_behavior",
]
REQUIRED_TOPICS = ["/scan", "/camera/image_raw", "/odom", "/tf", "/map"]
SMOKE_TOPICS = ["/scan", "/odom", "/camera/image_raw"]
LOCALIZATION_SMOKE_TOPICS = ["/scan", "/amcl_pose"]
LIFECYCLE_NODES = ["/map_server", "/amcl", "/planner_server"]
SETUP_CANDIDATES = [
    "/opt/ros/humble/setup.bash",
    "/root/rober/onboard/install/setup.bash",
    "/root/rober/install/setup.bash",
    "/ws/install/setup.bash",
    "~/rober/onboard/install/setup.bash",
    "~/apps/rober/onboard/install/setup.bash",
]
NAV2_PROOF_REFRESH_URL = "http://127.0.0.1:8787/api/nav2/proof/refresh"
MANAGED_MAP_YAML = "/root/rober/onboard/runtime/maps/trashbot_map.yaml"
NAV2_REFRESH_HARD_TIMEOUT_GRACE_S = 8
NAV2_REFRESH_HARD_TIMEOUT_MAX_S = 45
NAV2_REFRESH_REMOTE_PROCESS_OVERHEAD_S = 4
NAV2_REFRESH_LOCAL_PROCESS_OVERHEAD_S = 2
NAV2_PROOF_REFRESH_PAYLOAD = {
    "timeout_s": 30,
    "managed_runtime_opt_in": True,
    "managed_timeout_s": 30,
    "managed_map_yaml": MANAGED_MAP_YAML,
    "initialpose_opt_in": True,
    "initialpose_x": 0.0,
    "initialpose_y": 0.0,
    "initialpose_yaw": 0.0,
    "initialpose_frame_id": "map",
    "path_generation_opt_in": True,
    "path_generation_timeout_s": 30,
    "path_goal_frame_id": "map",
    "path_goal_x": 0.8,
    "path_goal_y": 0.0,
    "path_goal_yaw": 0.0,
}
NO_MOTION_FALSE_FLAGS = {
    "safe_to_control": False,
    "delivery_success": False,
    "primary_actions_enabled": False,
    "robot_control_executed": False,
    "route_execution_success": False,
    "hil_pass": False,
}
DANGEROUS_TRUE_FIELDS = frozenset(
    {
        "safe_to_control",
        "delivery_success",
        "primary_actions_enabled",
        "robot_control_executed",
        "route_execution_success",
        "hil_pass",
        "sends_motion_commands",
        "publishes_cmd_vel",
        "calls_base_manual",
        "sends_base_motion_commands",
        "uses_base_uart",
        "command_dispatch_enabled",
        "manual_control_enabled",
        "navigate_goal_enabled",
        "keyboard_control_enabled",
    }
)
ROS_DAEMON_FAULT_TOKENS = (
    "!rclpy.ok()",
    "xmlrpc.client.fault",
    "failed to communicate with daemon",
    "daemon is not running",
    "failed to call service of node",
)
ROS_GRAPH_READ_ONLY_PREFIXES = (
    ("ros2", "topic"),
    ("ros2", "lifecycle"),
    ("ros2", "node"),
)


def utc_now() -> str:
    # 统一使用 UTC，避免现场上位机和开发机时区不一致导致证据难以对齐。
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat()


def redact_secret(text: str) -> str:
    # 命令摘要进入 sprint 和云端 archive 前先脱敏，防止误带 token 或密码。
    home = str(Path.home())
    redacted = text.replace(home, "~") if home else text
    patterns = [
        (r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1<redacted>"),
        (r"(?i)(token|password|passwd|secret|access_key|ak|sk)(=|:)\S+", r"\1\2<redacted>"),
        (r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", "<redacted-private-key>"),
    ]
    for pattern, replacement in patterns:
        redacted = re.sub(pattern, replacement, redacted, flags=re.DOTALL)
    return redacted


def safe_text(text: str, limit: int = 1600) -> str:
    # 外部命令输出可能很长，只保留头部摘要，避免 JSON 证据包失控膨胀。
    cleaned = redact_secret(text.replace("\r\n", "\n").strip())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit] + f"\n<truncated {len(cleaned) - limit} chars>"


def ensure_text(value: Any) -> str:
    # TimeoutExpired 在不同 Python 版本里可能给 bytes；这里统一转成可脱敏字符串。
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value or "")


def command_summary(command: list[str]) -> list[str]:
    # 以 argv 数组记录命令，便于复现，同时避免 shell 拼接造成歧义。
    return [safe_text(part, 240) for part in command]


def run_command(command: list[str], timeout_s: int) -> dict[str, Any]:
    # 所有真实探测都必须有 timeout；现场命令挂住时也能产出 blocked 证据。
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        return {
            "command": command_summary(command),
            "returncode": completed.returncode,
            "stdout": safe_text(completed.stdout),
            "stderr": safe_text(completed.stderr),
            "_stdout_full": completed.stdout,
            "_stderr_full": completed.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command_summary(command),
            "returncode": None,
            "stdout": safe_text(ensure_text(exc.stdout)),
            "stderr": safe_text(ensure_text(exc.stderr)),
            "_stdout_full": ensure_text(exc.stdout),
            "_stderr_full": ensure_text(exc.stderr),
            "timed_out": True,
        }
    except OSError as exc:
        return {
            "command": command_summary(command),
            "returncode": None,
            "stdout": "",
            "stderr": safe_text(str(exc)),
            "_stdout_full": "",
            "_stderr_full": str(exc),
            "timed_out": False,
        }


def split_lines(text: str) -> list[str]:
    # ros2 输出通常是一行一个条目，先去空白再比较，减少格式差异误判。
    return [line.strip() for line in text.splitlines() if line.strip()]


def result_stdout_lines(result: dict[str, Any]) -> list[str]:
    # 逻辑判断必须看完整 stdout，不能基于已裁剪摘要做存在性判定。
    return split_lines(str(result.get("_stdout_full", "")))


def result_combined_text(result: dict[str, Any]) -> str:
    # 某些 ros2/tf2 CLI 会把关键信息写到 stderr；判定时需要合并两路输出。
    return "\n".join(
        part for part in [str(result.get("_stdout_full", "")), str(result.get("_stderr_full", ""))] if part
    )


def build_ssh_command(target: str, port: int, remote_command: str, timeout_s: int) -> list[str]:
    # SSH 使用 argv 数组承载目标、端口和远端命令，避免本地 shell 插值。
    return [
        "ssh",
        "-o",
        f"ConnectTimeout={timeout_s}",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-p",
        str(port),
        target,
        remote_command,
    ]


def build_remote_ros_command(command: str) -> str:
    # 远端 ros2 命令统一走 bash -lc 并 source ROS2 + 工作区，避免 SSH 非登录 shell 丢环境。
    setup_candidates = " ".join(shlex.quote(candidate) for candidate in SETUP_CANDIDATES[1:])
    script = f"""
source /opt/ros/humble/setup.bash
workspace_setup=""
for candidate in {setup_candidates}; do
    expanded="${{candidate/#\\~/$HOME}}"
    if [ -f "$expanded" ]; then
        source "$expanded"
        workspace_setup="$expanded"
        break
    fi
done
if [ -z "$workspace_setup" ]; then
    echo "No trashbot workspace setup.bash found" >&2
    exit 12
fi
{command}
""".strip()
    return f"bash -lc {shlex.quote(script)}"


def local_environment() -> dict[str, Any]:
    # 环境检查只记录可公开的上下文，不枚举环境变量或 home 目录。
    return {
        "ok": True,
        "hostname": socket.gethostname(),
        "time_utc": utc_now(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cwd": str(Path.cwd()),
    }


def dry_run_checks(args: argparse.Namespace) -> dict[str, Any]:
    # dry-run 是模板证明，不依赖 ROS2/SSH，避免开发机缺环境时阻塞软件交付。
    target = args.ssh_target if args.mode == "ssh" else "local"
    return {
        "environment": local_environment(),
        "ssh_reachability": {
            "ok": None,
            "target": args.ssh_target,
            "port": args.ssh_port,
            "command_template": command_summary(build_ssh_command(args.ssh_target, args.ssh_port, "true", args.timeout_s)),
            "note": "dry-run skips network access",
        },
        "ros2_cli": {
            "ok": None,
            "command_template": ["command", "-v", "ros2"],
            "note": "dry-run skips local ROS2 detection",
        },
        "setup_candidates": {
            "ok": None,
            "candidates": SETUP_CANDIDATES,
            "note": "dry-run records candidates only",
        },
        "trashbot_packages": {
            "ok": None,
            "required": REQUIRED_PACKAGES,
            "command_template": ["ros2", "pkg", "list"],
        },
        "topics": {
            "ok": None,
            "required": REQUIRED_TOPICS,
            "command_template": ["ros2", "topic", "list"],
        },
        "topic_smoke_commands": {
            "ok": None,
            "templates": topic_smoke_templates(target, args.ssh_port if args.mode == "ssh" else None),
        },
        "localization_smoke": {
            "ok": None,
            "templates": localization_smoke_templates(target, args.ssh_port if args.mode == "ssh" else None),
            "note": "dry-run skips live localization smoke",
        },
        "nav2_proof_refresh": {
            "ok": None,
            "template": nav2_refresh_template(target, args.ssh_port if args.mode == "ssh" else None),
            "note": "dry-run skips refresh readback",
        },
        "learning_commands": {
            "ok": None,
            "templates": learning_command_templates(target, args.ssh_port if args.mode == "ssh" else None),
        },
        "output_contract": output_contract(),
    }


def check_local_setup_candidates() -> dict[str, Any]:
    # setup.bash 是否存在是 ROS2 工作区可启动的前置信号，不在 dry-run 中强制。
    candidates = []
    for raw_path in SETUP_CANDIDATES:
        expanded = Path(raw_path).expanduser()
        candidates.append({"path": raw_path, "expanded": str(expanded), "exists": expanded.is_file()})
    return {"ok": any(item["exists"] for item in candidates), "candidates": candidates}


def check_remote_setup_candidates(args: argparse.Namespace) -> dict[str, Any]:
    # 远端检查只执行 test -f，不读取文件内容，避免泄露安装细节或凭证。
    results = []
    for raw_path in SETUP_CANDIDATES[1:]:
        remote = f"test -f {raw_path}"
        result = run_command(build_ssh_command(args.ssh_target, args.ssh_port, remote, args.timeout_s), args.timeout_s + 2)
        results.append({"path": raw_path, "exists": result["returncode"] == 0, "result": result})
    return {"ok": any(item["exists"] for item in results), "candidates": results}


def check_local_ros2(args: argparse.Namespace) -> tuple[dict[str, Any], str | None]:
    # command -v 的语义用 shell 内建完成；该命令不含用户输入，风险面可控。
    result = run_command(["/bin/sh", "-lc", "command -v ros2"], args.timeout_s)
    ok = result["returncode"] == 0 and bool(result["stdout"])
    return {"ok": ok, "result": result}, (None if ok else "blocked_ros2_cli_missing")


def check_remote_ros2(args: argparse.Namespace) -> tuple[dict[str, Any], str | None]:
    # SSH 可达后再查 ros2，确保网络 blocker 和环境 blocker 能分层。
    result = run_command(
        build_ssh_command(args.ssh_target, args.ssh_port, build_remote_ros_command("command -v ros2"), args.timeout_s),
        args.timeout_s + 2,
    )
    ok = result["returncode"] == 0 and bool(result["stdout"])
    return {"ok": ok, "result": result}, (None if ok else "blocked_ros2_cli_missing")


def check_packages(args: argparse.Namespace, remote: bool) -> tuple[dict[str, Any], str | None]:
    # 包列表是能否进入 learn/fixed route 命令链的最小软件边界。
    if remote:
        command = build_ssh_command(
            args.ssh_target,
            args.ssh_port,
            build_remote_ros_command("ros2 pkg list"),
            args.timeout_s,
        )
        result = run_command(command, args.timeout_s + 2)
    else:
        result = run_command(["ros2", "pkg", "list"], args.timeout_s)
    found = set(result_stdout_lines(result)) if result["returncode"] == 0 else set()
    missing = [pkg for pkg in REQUIRED_PACKAGES if pkg not in found]
    check = {"ok": result["returncode"] == 0 and not missing, "required": REQUIRED_PACKAGES, "missing": missing, "result": result}
    return check, (None if check["ok"] else "blocked_trashbot_packages_missing")


def check_topics(args: argparse.Namespace, remote: bool) -> tuple[dict[str, Any], str | None]:
    # topic list 只证明当前 ROS graph 暴露了必要输入，不证明数据质量。
    result = run_ros_command(args, remote, ["ros2", "topic", "list"])
    found = set(result_stdout_lines(result)) if result["returncode"] == 0 else set()
    missing = [topic for topic in REQUIRED_TOPICS if topic not in found]
    check = {"ok": result["returncode"] == 0 and not missing, "required": REQUIRED_TOPICS, "missing": missing, "result": result}
    return check, (None if check["ok"] else "blocked_required_topics_missing")


def check_topic_smoke(args: argparse.Namespace, remote: bool) -> tuple[dict[str, Any], str | None]:
    # smoke 采样用进程 timeout 兜底，避免 ros2 topic hz 长时间阻塞现场收口。
    results = []
    for topic in SMOKE_TOPICS:
        local_command = ["ros2", "topic", "hz", topic, "--window", "2"]
        result = run_ros_command(args, remote, local_command)
        results.append({"topic": topic, "kind": "hz", "ok": result["returncode"] == 0, "result": result})

    tf_command = ["ros2", "topic", "echo", "--once", "/tf"]
    result = run_ros_command(args, remote, tf_command)
    results.append({"topic": "/tf", "kind": "echo_once", "ok": result["returncode"] == 0, "result": result})

    ok = all(item["ok"] for item in results)
    return {
        "ok": ok,
        "results": results,
        "templates": topic_smoke_templates(args.ssh_target if remote else "local", args.ssh_port if remote else None),
    }, (
        None if ok else "blocked_topic_smoke_failed"
    )


def ros2_once_echo_command(topic: str) -> list[str]:
    # once echo 用于 no-motion 只读采样；它不会向图里写控制命令。
    return ["ros2", "topic", "echo", "--once", topic]


def ros2_tf_echo_command(parent_frame: str, child_frame: str) -> list[str]:
    # tf2_echo 只读检查 frame 连通性，输出由进程超时截断即可。
    return ["ros2", "run", "tf2_ros", "tf2_echo", parent_frame, child_frame]


def execute_ros_command_once(args: argparse.Namespace, remote: bool, command: list[str]) -> dict[str, Any]:
    # 单次 ROS2 CLI 执行入口；daemon-safe retry 逻辑在外层统一处理。
    if remote:
        remote_command = build_remote_ros_command(" ".join(shlex.quote(part) for part in command))
        return run_command(
            build_ssh_command(args.ssh_target, args.ssh_port, remote_command, args.timeout_s),
            args.timeout_s + 2,
        )
    return run_command(command, args.timeout_s)


def ros_graph_query_command(command: list[str]) -> bool:
    # 仅对 ROS graph 只读查询启用 daemon reset/retry，避免把普通 shell 命令误送进维护路径。
    if tuple(command[:4]) == ("ros2", "run", "tf2_ros", "tf2_echo"):
        return True
    return any(tuple(command[: len(prefix)]) == prefix for prefix in ROS_GRAPH_READ_ONLY_PREFIXES)


def ros_daemon_fault_detected(result: dict[str, Any]) -> bool:
    # `!rclpy.ok()` 和 XMLRPC fault 都表明 CLI/daemon graph 层异常，不能当成普通 topic 缺失。
    combined = result_combined_text(result).lower()
    return any(token in combined for token in ROS_DAEMON_FAULT_TOKENS)


def ros_command_label(command: list[str]) -> str:
    # 摘要里优先暴露被观测的 topic/node/frame，方便 sprint 直接引用恢复点。
    if not command:
        return "unknown"
    if tuple(command[:4]) == ("ros2", "run", "tf2_ros", "tf2_echo") and len(command) >= 6:
        return f"{command[4]}->{command[5]}"
    if tuple(command[:3]) == ("ros2", "topic", "hz") and len(command) >= 4:
        return command[3]
    if tuple(command[:3]) == ("ros2", "topic", "echo") and command:
        return command[-1]
    if tuple(command[:3]) == ("ros2", "topic", "type") and command:
        return command[-1]
    if tuple(command[:3]) == ("ros2", "topic", "info") and command:
        return command[-1]
    if tuple(command[:3]) == ("ros2", "lifecycle", "get") and command:
        return command[-1]
    if tuple(command[:3]) == ("ros2", "topic", "list"):
        return "topic_list"
    if tuple(command[:3]) == ("ros2", "node", "list"):
        return "node_list"
    return command[-1]


def ros_daemon_control_command(action: str) -> list[str]:
    # daemon stop/start 是官方维护入口；这里只用于修复只读查询层坏状态。
    return ["ros2", "daemon", action]


def recover_ros_daemon(args: argparse.Namespace, remote: bool) -> dict[str, Any]:
    # 维护动作本身也要留证据，便于区分 reset 失败和 graph 仍不可用。
    stop_result = execute_ros_command_once(args, remote, ros_daemon_control_command("stop"))
    start_result = execute_ros_command_once(args, remote, ros_daemon_control_command("start"))
    health_command = ["ros2", "node", "list"]
    health_result = execute_ros_command_once(args, remote, health_command)
    health_ok = health_result.get("returncode") == 0 and not ros_daemon_fault_detected(health_result)
    return {
        "stop_result": stop_result,
        "start_result": start_result,
        "health_result": health_result,
        "health_ok": health_ok,
        "reset_failed": bool(start_result.get("returncode") not in {0, None}) or ros_daemon_fault_detected(start_result),
    }


def run_ros_command(args: argparse.Namespace, remote: bool, command: list[str]) -> dict[str, Any]:
    # ROS graph 读命令一旦撞上 daemon fault，要先 reset/retry，再决定是否真是定位链 blocker。
    initial = execute_ros_command_once(args, remote, command)
    if not ros_graph_query_command(command):
        initial["daemon_fault_detected"] = False
        initial["daemon_recovered"] = False
        initial["retry_attempts"] = 0
        initial["ros_cli_retry"] = {"eligible": False, "attempted": False, "target": ros_command_label(command)}
        return initial
    if not ros_daemon_fault_detected(initial):
        initial["daemon_fault_detected"] = False
        initial["daemon_recovered"] = False
        initial["retry_attempts"] = 0
        initial["ros_cli_retry"] = {"eligible": True, "attempted": False, "target": ros_command_label(command)}
        return initial

    recovery = recover_ros_daemon(args, remote)
    retried = execute_ros_command_once(args, remote, command)
    daemon_recovered = bool(recovery.get("health_ok")) and not ros_daemon_fault_detected(retried)
    retried["daemon_fault_detected"] = True
    retried["daemon_recovered"] = daemon_recovered
    retried["retry_attempts"] = 1
    retried["ros_daemon_health"] = recovery
    retried["ros_cli_retry"] = {
        "eligible": True,
        "attempted": True,
        "target": ros_command_label(command),
        "initial_failure_summary": summarize_failure_text(initial),
        "retry_failure_summary": summarize_failure_text(retried),
        "health_ok": recovery.get("health_ok"),
        "reset_failed": recovery.get("reset_failed"),
    }
    return retried


def command_observed_once(result: dict[str, Any], required_markers: list[str] | None = None) -> bool:
    # observed 必须是命令成功、未超时且输出命中结构 marker；warning/error 不算健康观测。
    if result.get("timed_out"):
        return False
    if result.get("returncode") != 0:
        return False
    combined = result_combined_text(result)
    if required_markers:
        return all(marker in combined for marker in required_markers)
    return bool(split_lines(combined))


def summarize_live_result(
    *,
    name: str,
    observed: bool,
    blocked_reason: str,
    command: list[str],
    result: dict[str, Any],
) -> dict[str, Any]:
    # 每个观测项都写成独立摘要，便于后续 sprint/consumer 直接引用单项 blocker。
    return {
        "name": name,
        "observed": observed,
        "ok": observed,
        "blocked_reason": None if observed else blocked_reason,
        "command": command_summary(command),
        "result": result,
    }


def check_localization_smoke(args: argparse.Namespace, remote: bool) -> tuple[dict[str, Any], str | None]:
    # 这一段是本轮新增主目标：真实 no-motion 下直接确认 /scan、/amcl_pose 与 map 相关 TF。
    results: list[dict[str, Any]] = []
    scan_command = ros2_once_echo_command("/scan")
    scan_result = run_ros_command(args, remote, scan_command)
    results.append(
        summarize_live_result(
            name="/scan",
            observed=command_observed_once(scan_result, ["header:", "ranges:"]),
            blocked_reason="blocked_scan_not_observed",
            command=scan_command,
            result=scan_result,
        )
    )

    amcl_command = ros2_once_echo_command("/amcl_pose")
    amcl_result = run_ros_command(args, remote, amcl_command)
    results.append(
        summarize_live_result(
            name="/amcl_pose",
            observed=command_observed_once(amcl_result, ["header:", "pose:"]),
            blocked_reason="blocked_amcl_pose_not_observed",
            command=amcl_command,
            result=amcl_result,
        )
    )

    map_odom_command = ros2_tf_echo_command("map", "odom")
    map_odom_result = run_ros_command(args, remote, map_odom_command)
    map_odom_summary = summarize_live_result(
        name="map->odom",
        observed=command_observed_once(map_odom_result, ["Frame: odom", "Frame: map"]),
        blocked_reason="blocked_map_to_odom_not_observed",
        command=map_odom_command,
        result=map_odom_result,
    )
    map_odom_summary["failure_summary"] = summarize_failure_text(map_odom_result)
    results.append(map_odom_summary)

    map_base_command = ros2_tf_echo_command("map", "base_link")
    map_base_result = run_ros_command(args, remote, map_base_command)
    map_base_summary = summarize_live_result(
        name="map->base_link",
        observed=command_observed_once(map_base_result, ["Frame: base_link", "Frame: map"]),
        blocked_reason="blocked_map_to_base_link_not_observed",
        command=map_base_command,
        result=map_base_result,
    )
    map_base_summary["failure_summary"] = summarize_failure_text(map_base_result)
    results.append(map_base_summary)

    missing = [item["blocked_reason"] for item in results if not item["observed"]]
    return {
        "ok": not missing,
        "results": results,
        "templates": localization_smoke_templates(args.ssh_target if remote else "local", args.ssh_port if remote else None),
        "localization_ready_for_no_motion_refresh": not missing,
        "blocked_reasons": missing,
    }, (None if not missing else "blocked_live_localization_chain_not_ready")


def topic_info_command(topic: str, verbose: bool = False) -> list[str]:
    # topic info/type 都是 ROS graph 只读命令，用来区分“topic 名字存在”和“真正有发布者”。
    command = ["ros2", "topic", "info"]
    if verbose:
        command.append("-v")
    command.append(topic)
    return command


def topic_type_command(topic: str) -> list[str]:
    # topic type 可帮助区分未发布、未知类型和类型正确但无样本三类根因。
    return ["ros2", "topic", "type", topic]


def lifecycle_get_command(node_name: str) -> list[str]:
    # lifecycle get 只读查询节点状态，不会触发 transition。
    return ["ros2", "lifecycle", "get", node_name]


def extract_int(pattern: str, text: str) -> int | None:
    # 发布者/订阅者数量只保留整数，避免把完整 ros2 输出直接扩散到摘要字段。
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    try:
        return int(match.group(1))
    except (TypeError, ValueError):
        return None


def summarize_failure_text(result: dict[str, Any]) -> str | None:
    # 失败摘要优先给出第一条有效错误，方便 sprint 文档直接引用根因短句。
    combined = result_combined_text(result)
    for line in split_lines(combined):
        lowered = line.lower()
        if any(
            token in lowered
            for token in ["invalid frame", "could not", "warning", "error", "failed", "unknown topic", "does not appear"]
        ):
            return safe_text(line, 240)
    return safe_text(combined, 240) if combined else None


def probe_topic_metadata(args: argparse.Namespace, remote: bool, topic: str, required_type: str | None = None) -> dict[str, Any]:
    # topic metadata 负责把“有无 publisher/type”压成安全摘要，避免只靠 echo 现象猜根因。
    type_result = run_ros_command(args, remote, topic_type_command(topic))
    info_result = run_ros_command(args, remote, topic_info_command(topic, verbose=True))
    combined_type = result_combined_text(type_result)
    combined_info = result_combined_text(info_result)
    topic_type = split_lines(combined_type)[0] if combined_type and type_result.get("returncode") == 0 else None
    publisher_count = extract_int(r"publisher count:\s*(\d+)", combined_info)
    subscription_count = extract_int(r"subscription count:\s*(\d+)", combined_info)
    blocked_reasons: list[str] = []
    if not topic_type:
        blocked_reasons.append(f"blocked_{topic.strip('/').replace('/', '_')}_topic_type_missing")
    elif required_type and topic_type != required_type:
        blocked_reasons.append(f"blocked_{topic.strip('/').replace('/', '_')}_topic_type_unexpected")
    if publisher_count == 0:
        blocked_reasons.append(f"blocked_{topic.strip('/').replace('/', '_')}_publisher_missing")
    return {
        "topic": topic,
        "ok": not blocked_reasons,
        "topic_type": topic_type,
        "required_type": required_type,
        "publisher_count": publisher_count,
        "subscription_count": subscription_count,
        "blocked_reasons": blocked_reasons,
        "type_result": type_result,
        "info_result": info_result,
        "failure_summary": summarize_failure_text(type_result) or summarize_failure_text(info_result),
    }


def summarize_lifecycle_state(result: dict[str, Any]) -> str | None:
    # lifecycle 输出格式可能带 label；这里只收敛到主状态词，便于横向比对。
    combined = result_combined_text(result)
    for line in split_lines(combined):
        match = re.search(r"state:\s*([A-Za-z_]+)", line, flags=re.IGNORECASE)
        if match:
            return match.group(1).lower()
        if line.lower() in {"active", "inactive", "unconfigured", "finalized"}:
            return line.lower()
    return None


def probe_lifecycle_states(args: argparse.Namespace, remote: bool) -> dict[str, Any]:
    # lifecycle probe 用于分层 map_server/amcl/planner_server 是否活着、是否 active。
    results = []
    blocked_reasons: list[str] = []
    for node_name in LIFECYCLE_NODES:
        result = run_ros_command(args, remote, lifecycle_get_command(node_name))
        state = summarize_lifecycle_state(result)
        item_blocked: list[str] = []
        if result.get("returncode") != 0 or not state:
            item_blocked.append(f"blocked_{node_name.strip('/').replace('/', '_')}_lifecycle_unavailable")
        elif state != "active":
            item_blocked.append(f"blocked_{node_name.strip('/').replace('/', '_')}_lifecycle_not_active")
        blocked_reasons.extend(item_blocked)
        results.append(
            {
                "node": node_name,
                "ok": not item_blocked,
                "state": state,
                "blocked_reasons": item_blocked,
                "result": result,
                "failure_summary": summarize_failure_text(result),
            }
        )
    return {"ok": not blocked_reasons, "results": results, "blocked_reasons": blocked_reasons}


def managed_map_yaml_probe_command(map_yaml: str) -> str:
    # 只读 map yaml 存在性与 sha256 前缀，不输出完整路径以外的敏感上下文。
    quoted = json.dumps(map_yaml, ensure_ascii=False)
    return (
        "python3 - <<'PY'\n"
        "from pathlib import Path\n"
        "import hashlib, json\n"
        f"path = Path({quoted})\n"
        "payload = {'exists': path.is_file(), 'basename': path.name}\n"
        "if path.is_file():\n"
        "    data = path.read_bytes()\n"
        "    payload['size_bytes'] = len(data)\n"
        "    payload['sha256_prefix'] = hashlib.sha256(data).hexdigest()[:12]\n"
        "print(json.dumps(payload, ensure_ascii=False))\n"
        "PY"
    )


def probe_managed_map_yaml(args: argparse.Namespace, remote: bool) -> dict[str, Any]:
    # managed map yaml 是本轮定位链的关键前置，缺文件时要与 AMCL/TF blocker 分开记录。
    map_yaml = args.managed_map_yaml
    if remote:
        result = run_command(
            build_ssh_command(args.ssh_target, args.ssh_port, managed_map_yaml_probe_command(map_yaml), args.timeout_s),
            args.timeout_s + 2,
        )
    else:
        result = run_command(["/bin/sh", "-lc", managed_map_yaml_probe_command(map_yaml)], args.timeout_s + 2)
    payload: dict[str, Any] = {"exists": False, "basename": Path(map_yaml).name}
    if result.get("returncode") == 0:
        try:
            parsed = json.loads(result.get("_stdout_full") or result.get("stdout") or "{}")
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            pass
    blocked_reasons = [] if payload.get("exists") else ["blocked_managed_map_yaml_missing"]
    return {
        "ok": not blocked_reasons,
        "configured_basename": Path(map_yaml).name,
        "summary": payload,
        "blocked_reasons": blocked_reasons,
        "result": result,
        "failure_summary": summarize_failure_text(result),
    }


def probe_amcl_map_root_cause(args: argparse.Namespace, remote: bool) -> dict[str, Any]:
    # root-cause probe 聚合同轮 map topic、amcl topic、lifecycle、map yaml 与 TF 失败摘要。
    scan_topic = probe_topic_metadata(args, remote, "/scan", "sensor_msgs/msg/LaserScan")
    map_topic = probe_topic_metadata(args, remote, "/map", "nav_msgs/msg/OccupancyGrid")
    amcl_topic = probe_topic_metadata(args, remote, "/amcl_pose", "geometry_msgs/msg/PoseWithCovarianceStamped")
    lifecycle = probe_lifecycle_states(args, remote)
    map_yaml = probe_managed_map_yaml(args, remote)
    blocked_reasons = (
        list(scan_topic["blocked_reasons"])
        + list(map_topic["blocked_reasons"])
        + list(amcl_topic["blocked_reasons"])
        + list(lifecycle["blocked_reasons"])
        + list(map_yaml["blocked_reasons"])
    )
    return {
        "ok": not blocked_reasons,
        "scan_topic": scan_topic,
        "map_topic": map_topic,
        "amcl_pose_topic": amcl_topic,
        "lifecycle_states": lifecycle,
        "managed_map_yaml": map_yaml,
        "blocked_reasons": blocked_reasons,
    }


def nav2_refresh_command(timeout_s: int, url: str) -> list[str]:
    # refresh body 固定为 no-motion readback 合同，避免现场手输参数漂移。
    return [
        "curl",
        "--max-time",
        str(nav2_refresh_hard_timeout_s(timeout_s)),
        "-sS",
        "-X",
        "POST",
        "-H",
        "Content-Type: application/json",
        "--data",
        json.dumps(NAV2_PROOF_REFRESH_PAYLOAD, separators=(",", ":")),
        url,
    ]


def nav2_refresh_requested_budget_s(base_timeout_s: int) -> int:
    # 请求体里的 timeout 是远端 helper 的工作预算；外层 hard timeout 必须从它们推导。
    candidates = [
        max(base_timeout_s, 1),
        NAV2_PROOF_REFRESH_PAYLOAD.get("timeout_s"),
        NAV2_PROOF_REFRESH_PAYLOAD.get("managed_timeout_s"),
        NAV2_PROOF_REFRESH_PAYLOAD.get("path_generation_timeout_s"),
    ]
    numeric = [int(value) for value in candidates if isinstance(value, (int, float))]
    return max(numeric) if numeric else max(base_timeout_s, 1)


def nav2_refresh_hard_timeout_s(base_timeout_s: int) -> int:
    # 现场 refresh 允许短暂拉起 runtime，但绝不能无限吃掉整轮 automation。
    derived = nav2_refresh_requested_budget_s(base_timeout_s) + NAV2_REFRESH_HARD_TIMEOUT_GRACE_S
    return min(max(derived, max(base_timeout_s, 1)), NAV2_REFRESH_HARD_TIMEOUT_MAX_S)


def nav2_refresh_process_timeout_s(base_timeout_s: int, remote: bool) -> int:
    # SSH 远端额外给极小运输余量；真正的工作预算仍由 hard timeout 控制。
    overhead = NAV2_REFRESH_REMOTE_PROCESS_OVERHEAD_S if remote else NAV2_REFRESH_LOCAL_PROCESS_OVERHEAD_S
    return nav2_refresh_hard_timeout_s(base_timeout_s) + overhead


def find_dangerous_true_fields(value: Any, path: str = "") -> list[str]:
    # refresh 返回里只要出现硬危险 true，就必须把整轮 readback fail-closed。
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            item_path = f"{path}.{key}" if path else key
            if key in DANGEROUS_TRUE_FIELDS and item is True:
                found.append(item_path)
            found.extend(find_dangerous_true_fields(item, item_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(find_dangerous_true_fields(item, f"{path}[{index}]"))
    return found


def summarize_nav2_refresh_payload(
    payload: dict[str, Any],
    *,
    result: dict[str, Any],
    hard_timeout_s: int,
    process_timeout_s: int,
) -> dict[str, Any]:
    # refresh summary 只保留当前 sprint 真正关心的 no-motion readback 字段。
    proof = payload.get("proof")
    proof_dict = proof if isinstance(proof, dict) else {}
    root_causes = proof_dict.get("root_causes")
    blockers = proof_dict.get("blockers")
    root_cause_list = root_causes if isinstance(root_causes, list) else []
    blocker_list = blockers if isinstance(blockers, list) else []
    summary = {
        "endpoint": payload.get("endpoint"),
        "status": payload.get("status"),
        "proof_state": payload.get("proof_state"),
        "path_generated": proof_dict.get("path_generated", payload.get("path_generated")),
        "path_generation_succeeded": proof_dict.get("path_generation_succeeded", payload.get("path_generation_succeeded")),
        "path_point_count": proof_dict.get("path_point_count", payload.get("path_point_count")),
        "planner_server_active": proof_dict.get("planner_server_active", payload.get("planner_server_active")),
        "scan_once_observed": proof_dict.get("scan_once_observed"),
        "amcl_pose_once_observed": proof_dict.get("amcl_pose_once_observed"),
        "map_to_odom_observed": proof_dict.get("map_to_odom_observed"),
        "map_to_base_link_observed": proof_dict.get("map_to_base_link_observed"),
        "root_causes": root_cause_list,
        "blocked_reasons": blocker_list,
        "proof_blocked_reason_count": len(root_cause_list) or len(blocker_list),
        "dangerous_true_fields": find_dangerous_true_fields(payload),
        "timed_out": bool(result.get("timed_out")),
        "naturally_returned": not bool(result.get("timed_out")),
        "returncode": result.get("returncode"),
        "curl_max_time_s": hard_timeout_s,
        "process_timeout_s": process_timeout_s,
        **NO_MOTION_FALSE_FLAGS,
    }
    return summary


def failed_nav2_refresh_summary(
    *,
    endpoint: str,
    status: str,
    result: dict[str, Any],
    hard_timeout_s: int,
    process_timeout_s: int,
) -> dict[str, Any]:
    # timeout / 非零返回 / JSON 解析失败都要写成统一的 fail-closed summary，供主 packet 直接落盘。
    return {
        "endpoint": endpoint,
        "status": status,
        "timed_out": bool(result.get("timed_out")),
        "naturally_returned": not bool(result.get("timed_out")),
        "returncode": result.get("returncode"),
        "failure_summary": summarize_failure_text(result),
        "dangerous_true_fields": [],
        "curl_max_time_s": hard_timeout_s,
        "process_timeout_s": process_timeout_s,
        **NO_MOTION_FALSE_FLAGS,
    }


def collect_ros_cli_retry_events(value: Any) -> list[dict[str, Any]]:
    # 递归扫描 checks，把各层 ROS CLI retry 结果压成一个统一列表，方便顶层收口。
    events: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if "ros_cli_retry" in value or "daemon_fault_detected" in value:
            retry = value.get("ros_cli_retry") if isinstance(value.get("ros_cli_retry"), dict) else {}
            daemon_health = value.get("ros_daemon_health") if isinstance(value.get("ros_daemon_health"), dict) else {}
            event = {
                "target": retry.get("target"),
                "eligible": retry.get("eligible"),
                "attempted": retry.get("attempted"),
                "daemon_fault_detected": bool(value.get("daemon_fault_detected")),
                "daemon_recovered": bool(value.get("daemon_recovered")),
                "retry_attempts": int(value.get("retry_attempts") or 0),
                "health_ok": daemon_health.get("health_ok"),
                "reset_failed": daemon_health.get("reset_failed"),
                "initial_failure_summary": retry.get("initial_failure_summary"),
                "retry_failure_summary": retry.get("retry_failure_summary"),
            }
            if event["attempted"] or event["daemon_fault_detected"]:
                events.append(event)
        for item in value.values():
            events.extend(collect_ros_cli_retry_events(item))
    elif isinstance(value, list):
        for item in value:
            events.extend(collect_ros_cli_retry_events(item))
    return events


def summarize_ros_cli_retry(checks: dict[str, Any]) -> dict[str, Any]:
    # 顶层摘要要回答：是否撞到 daemon fault、是否恢复、恢复了哪些观测点、还卡在哪层。
    events = collect_ros_cli_retry_events(checks)
    daemon_fault_detected = any(event.get("daemon_fault_detected") for event in events)
    recovered_targets = sorted(
        {
            str(event.get("target"))
            for event in events
            if event.get("daemon_fault_detected") and event.get("daemon_recovered") and event.get("target")
        }
    )
    unrecovered_blockers: list[str] = []
    for event in events:
        if not event.get("daemon_fault_detected") or event.get("daemon_recovered"):
            continue
        if event.get("reset_failed"):
            unrecovered_blockers.append("daemon_reset_failed")
        else:
            unrecovered_blockers.append("ros_graph_unavailable")
    first_health = next(
        (
            {
                "target": event.get("target"),
                "health_ok": event.get("health_ok"),
                "reset_failed": event.get("reset_failed"),
                "initial_failure_summary": event.get("initial_failure_summary"),
                "retry_failure_summary": event.get("retry_failure_summary"),
            }
            for event in events
            if event.get("daemon_fault_detected")
        ),
        None,
    )
    return {
        "daemon_fault_detected": daemon_fault_detected,
        "daemon_recovered": bool(recovered_targets) and not unrecovered_blockers,
        "retry_attempts": sum(int(event.get("retry_attempts") or 0) for event in events),
        "recovered_targets": recovered_targets,
        "unrecovered_blockers": unrecovered_blockers,
        "ros_daemon_health": first_health,
        "events": events,
    }


def classify_root_cause_layers(
    *,
    daemon_summary: dict[str, Any],
    scan_topic: dict[str, Any],
    amcl_pose_topic: dict[str, Any],
    lifecycle_states: list[dict[str, Any]],
    tf_failures: list[dict[str, Any]],
    localization_blocked_reasons: list[str],
) -> list[str]:
    # 现场收口需要层级化 blocker，而不是重复堆原始 blocked_reason。
    layers: list[str] = []
    unrecovered = list(daemon_summary.get("unrecovered_blockers") or [])
    layers.extend(unrecovered)
    if any(reason in (scan_topic.get("blocked_reasons") or []) for reason in ["blocked_scan_topic_type_missing", "blocked_scan_publisher_missing"]):
        layers.append("lidar_missing")
    lifecycle_map = {item.get("node"): item for item in lifecycle_states if isinstance(item, dict)}
    map_server_state = lifecycle_map.get("/map_server") or {}
    amcl_state = lifecycle_map.get("/amcl") or {}
    if "blocked_map_server_lifecycle_unavailable" in (map_server_state.get("blocked_reasons") or []):
        layers.append("map_server_not_active")
    elif "blocked_map_server_lifecycle_not_active" in (map_server_state.get("blocked_reasons") or []):
        layers.append("map_server_not_active")
    if "blocked_amcl_lifecycle_unavailable" in (amcl_state.get("blocked_reasons") or []):
        layers.append("amcl_not_active")
    elif "blocked_amcl_lifecycle_not_active" in (amcl_state.get("blocked_reasons") or []):
        layers.append("amcl_not_active")
    elif "blocked_amcl_pose_not_observed" in localization_blocked_reasons or "blocked_amcl_pose_publisher_missing" in (amcl_pose_topic.get("blocked_reasons") or []):
        layers.append("amcl_no_pose")
    if any(not item.get("observed") for item in tf_failures):
        layers.append("tf_missing")
    return list(dict.fromkeys(layers))


def root_cause_from_checks(checks: dict[str, Any]) -> dict[str, Any]:
    # 顶层 root-cause summary 只抽高价值字段，供 sprint 收口和 O6/O7 后续 intake 直接消费。
    localization = checks.get("localization_smoke") or {}
    root_cause = checks.get("amcl_map_tf_root_cause") or {}
    refresh = checks.get("nav2_proof_refresh") or {}
    daemon_summary = summarize_ros_cli_retry(checks)
    refresh_summary = refresh.get("summary") if isinstance(refresh, dict) else {}
    if not isinstance(refresh_summary, dict):
        refresh_summary = {}
    tf_failures = []
    for item in localization.get("results", []):
        if isinstance(item, dict) and item.get("name") in {"map->odom", "map->base_link"}:
            tf_failures.append(
                {
                    "name": item.get("name"),
                    "observed": item.get("observed"),
                    "blocked_reason": item.get("blocked_reason"),
                    "failure_summary": item.get("failure_summary"),
                }
            )
    return {
        "localization_blocked_reasons": localization.get("blocked_reasons", []),
        "ros_daemon_health": daemon_summary.get("ros_daemon_health"),
        "ros_cli_retry_summary": daemon_summary.get("events", []),
        "daemon_fault_detected": daemon_summary.get("daemon_fault_detected"),
        "daemon_recovered": daemon_summary.get("daemon_recovered"),
        "retry_attempts": daemon_summary.get("retry_attempts"),
        "recovered_targets": daemon_summary.get("recovered_targets", []),
        "unrecovered_blockers": daemon_summary.get("unrecovered_blockers", []),
        "scan_topic": {
            "topic_type": ((root_cause.get("scan_topic") or {}).get("topic_type")),
            "publisher_count": ((root_cause.get("scan_topic") or {}).get("publisher_count")),
            "blocked_reasons": ((root_cause.get("scan_topic") or {}).get("blocked_reasons", [])),
        },
        "map_topic": {
            "topic_type": ((root_cause.get("map_topic") or {}).get("topic_type")),
            "publisher_count": ((root_cause.get("map_topic") or {}).get("publisher_count")),
            "blocked_reasons": ((root_cause.get("map_topic") or {}).get("blocked_reasons", [])),
        },
        "amcl_pose_topic": {
            "topic_type": ((root_cause.get("amcl_pose_topic") or {}).get("topic_type")),
            "publisher_count": ((root_cause.get("amcl_pose_topic") or {}).get("publisher_count")),
            "blocked_reasons": ((root_cause.get("amcl_pose_topic") or {}).get("blocked_reasons", [])),
        },
        "managed_map_yaml": {
            "configured_basename": ((root_cause.get("managed_map_yaml") or {}).get("configured_basename")),
            "summary": ((root_cause.get("managed_map_yaml") or {}).get("summary")),
            "blocked_reasons": ((root_cause.get("managed_map_yaml") or {}).get("blocked_reasons", [])),
        },
        "lifecycle_states": [
            {
                "node": item.get("node"),
                "state": item.get("state"),
                "blocked_reasons": item.get("blocked_reasons", []),
            }
            for item in ((root_cause.get("lifecycle_states") or {}).get("results", []))
        ],
        "tf_failures": tf_failures,
        "nav2_refresh": {
            "status": refresh_summary.get("status"),
            "timed_out": refresh_summary.get("timed_out"),
            "naturally_returned": refresh_summary.get("naturally_returned"),
            "returncode": refresh_summary.get("returncode"),
            "root_causes": refresh_summary.get("root_causes", []),
            "blocked_reasons": refresh_summary.get("blocked_reasons", []),
            "path_generated": refresh_summary.get("path_generated"),
            "path_generation_succeeded": refresh_summary.get("path_generation_succeeded"),
            "path_point_count": refresh_summary.get("path_point_count"),
            "curl_max_time_s": refresh_summary.get("curl_max_time_s"),
            "process_timeout_s": refresh_summary.get("process_timeout_s"),
        },
        "root_cause_layers": classify_root_cause_layers(
            daemon_summary=daemon_summary,
            scan_topic=(root_cause.get("scan_topic") or {}),
            amcl_pose_topic=(root_cause.get("amcl_pose_topic") or {}),
            lifecycle_states=[
                {
                    "node": item.get("node"),
                    "state": item.get("state"),
                    "blocked_reasons": item.get("blocked_reasons", []),
                }
                for item in ((root_cause.get("lifecycle_states") or {}).get("results", []))
            ],
            tf_failures=tf_failures,
            localization_blocked_reasons=localization.get("blocked_reasons", []),
        ),
    }


def check_nav2_proof_refresh(args: argparse.Namespace, remote: bool) -> tuple[dict[str, Any], str | None]:
    # refresh 只在 live localization smoke 之后执行，用来确认 blocker 是否仍卡在定位链。
    command = nav2_refresh_command(args.timeout_s, args.nav2_refresh_url)
    hard_timeout_s = nav2_refresh_hard_timeout_s(args.timeout_s)
    process_timeout_s = nav2_refresh_process_timeout_s(args.timeout_s, remote)
    if remote:
        result = run_command(
            build_ssh_command(
                args.ssh_target,
                args.ssh_port,
                build_remote_ros_command(" ".join(shlex.quote(part) for part in command)),
                args.timeout_s,
            ),
            process_timeout_s,
        )
    else:
        result = run_command(command, process_timeout_s)

    if result.get("timed_out"):
        return {
            "ok": False,
            "command": command_summary(command),
            "result": result,
            "summary": failed_nav2_refresh_summary(
                endpoint=args.nav2_refresh_url,
                status="refresh_readback_timed_out",
                result=result,
                hard_timeout_s=hard_timeout_s,
                process_timeout_s=process_timeout_s,
            ),
            "template": nav2_refresh_template(args.ssh_target if remote else "local", args.ssh_port if remote else None),
        }, "blocked_refresh_readback_failed"

    if result["returncode"] != 0:
        return {
            "ok": False,
            "command": command_summary(command),
            "result": result,
            "summary": failed_nav2_refresh_summary(
                endpoint=args.nav2_refresh_url,
                status="refresh_command_failed",
                result=result,
                hard_timeout_s=hard_timeout_s,
                process_timeout_s=process_timeout_s,
            ),
            "template": nav2_refresh_template(args.ssh_target if remote else "local", args.ssh_port if remote else None),
        }, "blocked_refresh_readback_failed"

    try:
        payload = json.loads(result.get("_stdout_full") or result.get("stdout") or "{}")
    except json.JSONDecodeError:
        return {
            "ok": False,
            "command": command_summary(command),
            "result": result,
            "summary": failed_nav2_refresh_summary(
                endpoint=args.nav2_refresh_url,
                status="refresh_json_parse_failed",
                result=result,
                hard_timeout_s=hard_timeout_s,
                process_timeout_s=process_timeout_s,
            ),
            "template": nav2_refresh_template(args.ssh_target if remote else "local", args.ssh_port if remote else None),
        }, "blocked_refresh_readback_failed"

    summary = summarize_nav2_refresh_payload(
        payload,
        result=result,
        hard_timeout_s=hard_timeout_s,
        process_timeout_s=process_timeout_s,
    )
    dangerous_true_fields = summary["dangerous_true_fields"]
    if dangerous_true_fields:
        return {
            "ok": False,
            "command": command_summary(command),
            "result": result,
            "payload": payload,
            "summary": summary,
        }, "blocked_refresh_invokes_motion_or_goal_execution"

    return {
        "ok": True,
        "command": command_summary(command),
        "result": result,
        "payload": payload,
        "summary": summary,
        "template": nav2_refresh_template(args.ssh_target if remote else "local", args.ssh_port if remote else None),
    }, None


def check_ssh_reachability(args: argparse.Namespace) -> tuple[dict[str, Any], str | None]:
    # SSH 阶段先跑 true，失败时停止远端 ROS2 检查，但仍输出完整 JSON packet。
    result = run_command(build_ssh_command(args.ssh_target, args.ssh_port, "true", args.timeout_s), args.timeout_s + 2)
    ok = result["returncode"] == 0
    return {
        "ok": ok,
        "target": args.ssh_target,
        "port": args.ssh_port,
        "result": result,
    }, (None if ok else "blocked_ssh_unreachable")


def local_real_checks(args: argparse.Namespace) -> tuple[dict[str, Any], str]:
    checks: dict[str, Any] = {"environment": local_environment()}
    checks["ssh_reachability"] = {"ok": None, "note": "mode=local skips ssh", "target": None}
    checks["setup_candidates"] = check_local_setup_candidates()
    if not checks["setup_candidates"]["ok"]:
        return checks, "blocked_setup_missing"

    checks["ros2_cli"], status = check_local_ros2(args)
    if status:
        return checks, status
    checks["trashbot_packages"], status = check_packages(args, remote=False)
    if status:
        return checks, status
    checks["topics"], _ = check_topics(args, remote=False)
    checks["topic_smoke_commands"], _ = check_topic_smoke(args, remote=False)
    checks["localization_smoke"], localization_status = check_localization_smoke(args, remote=False)
    checks["amcl_map_tf_root_cause"] = probe_amcl_map_root_cause(args, remote=False)
    checks["nav2_proof_refresh"], refresh_status = check_nav2_proof_refresh(args, remote=False)
    if refresh_status:
        return checks, refresh_status
    checks["learning_commands"] = {"ok": True, "templates": learning_command_templates("local")}
    checks["output_contract"] = output_contract()
    if localization_status:
        return checks, localization_status
    return checks, "live_localization_smoke_refresh_readback_not_proven"


def ssh_real_checks(args: argparse.Namespace) -> tuple[dict[str, Any], str]:
    checks: dict[str, Any] = {"environment": local_environment()}
    checks["ssh_reachability"], status = check_ssh_reachability(args)
    if status:
        # SSH 不可达不是纯口头 blocker；这里仍交付可归档 JSON 和后续命令模板。
        checks["ros2_cli"] = {"ok": None, "note": "skipped because ssh is unreachable"}
        checks["setup_candidates"] = {"ok": None, "note": "skipped because ssh is unreachable", "candidates": SETUP_CANDIDATES}
        checks["trashbot_packages"] = {"ok": None, "required": REQUIRED_PACKAGES}
        checks["topics"] = {"ok": None, "required": REQUIRED_TOPICS}
        checks["topic_smoke_commands"] = {"ok": None, "templates": topic_smoke_templates(args.ssh_target, args.ssh_port)}
        checks["localization_smoke"] = {
            "ok": None,
            "templates": localization_smoke_templates(args.ssh_target, args.ssh_port),
            "note": "skipped because ssh is unreachable",
        }
        checks["amcl_map_tf_root_cause"] = {
            "ok": None,
            "note": "skipped because ssh is unreachable",
        }
        checks["nav2_proof_refresh"] = {
            "ok": None,
            "template": nav2_refresh_template(args.ssh_target, args.ssh_port),
            "note": "skipped because ssh is unreachable",
        }
        checks["learning_commands"] = {"ok": None, "templates": learning_command_templates(args.ssh_target, args.ssh_port)}
        checks["output_contract"] = output_contract()
        return checks, status

    checks["setup_candidates"] = check_remote_setup_candidates(args)
    if not checks["setup_candidates"]["ok"]:
        return checks, "blocked_setup_missing"
    checks["ros2_cli"], status = check_remote_ros2(args)
    if status:
        return checks, status
    checks["trashbot_packages"], status = check_packages(args, remote=True)
    if status:
        return checks, status
    checks["topics"], _ = check_topics(args, remote=True)
    checks["topic_smoke_commands"], _ = check_topic_smoke(args, remote=True)
    checks["localization_smoke"], localization_status = check_localization_smoke(args, remote=True)
    checks["amcl_map_tf_root_cause"] = probe_amcl_map_root_cause(args, remote=True)
    checks["nav2_proof_refresh"], refresh_status = check_nav2_proof_refresh(args, remote=True)
    if refresh_status:
        return checks, refresh_status
    checks["learning_commands"] = {"ok": True, "templates": learning_command_templates(args.ssh_target, args.ssh_port)}
    checks["output_contract"] = output_contract()
    if localization_status:
        return checks, localization_status
    return checks, "live_localization_smoke_refresh_readback_not_proven"


def output_contract() -> dict[str, Any]:
    # RUN_ID/OUT_DIR 固化为模板，避免现场多次运行覆盖 map、route、keyframe 等材料。
    return {
        "ok": True,
        "run_id_template": "field_route_$(date +%Y%m%d_%H%M%S)",
        "out_dir_template": "$HOME/.ros/trashbot_runs/${RUN_ID}",
        "required_artifacts": [
            "field_preflight.json",
            "live_localization_preflight.pretty.json",
            "live_localization_preflight.summary.json",
            "map.yaml",
            "route.csv",
            "keyframes/",
            "route_bag/",
            "fixed_route_replay.jsonl",
        ],
    }


def ssh_prefix(target: str, port: int | None) -> str:
    # SSH 模板显式包含端口，避免现场复制命令时落回默认 22 端口。
    return "" if target == "local" else f"ssh -p {port} {target} "


def remote_template_shell(command: str) -> str:
    # 人工执行模板保持可读，同时显式列出主工作区和候选工作区回退顺序。
    return (
        'bash -lc "source /opt/ros/humble/setup.bash; '
        'source /root/rober/onboard/install/setup.bash '
        '|| source /root/rober/install/setup.bash '
        '|| source /ws/install/setup.bash '
        '|| source ~/rober/onboard/install/setup.bash '
        '|| source ~/apps/rober/onboard/install/setup.bash; '
        f'{command}"'
    )


def topic_smoke_templates(target: str, port: int | None = None) -> list[dict[str, str]]:
    # 模板写入 JSON，让 SSH 恢复后的现场动作不依赖聊天记录。
    prefix = ssh_prefix(target, port)
    if target == "local":
        return [
            {"topic": "/scan", "command": "ros2 topic hz /scan --window 2"},
            {"topic": "/odom", "command": "ros2 topic hz /odom --window 2"},
            {"topic": "/camera/image_raw", "command": "ros2 topic hz /camera/image_raw --window 2"},
            {"topic": "/tf", "command": "ros2 topic echo --once /tf"},
        ]
    return [
        {"topic": "/scan", "command": f"{prefix}{remote_template_shell('ros2 topic hz /scan --window 2')}"},
        {"topic": "/odom", "command": f"{prefix}{remote_template_shell('ros2 topic hz /odom --window 2')}"},
        {"topic": "/camera/image_raw", "command": f"{prefix}{remote_template_shell('ros2 topic hz /camera/image_raw --window 2')}"},
        {"topic": "/tf", "command": f"{prefix}{remote_template_shell('ros2 topic echo --once /tf')}"},
    ]


def localization_smoke_templates(target: str, port: int | None = None) -> list[dict[str, str]]:
    # 当前同窗 localization smoke 模板固定为只读命令，不允许包含 manual/cmd_vel。
    prefix = ssh_prefix(target, port)
    if target == "local":
        return [
            {"name": "scan_once", "command": "ros2 topic echo --once /scan"},
            {"name": "amcl_pose_once", "command": "ros2 topic echo --once /amcl_pose"},
            {"name": "tf_map_odom", "command": "ros2 run tf2_ros tf2_echo map odom"},
            {"name": "tf_map_base_link", "command": "ros2 run tf2_ros tf2_echo map base_link"},
        ]
    return [
        {"name": "scan_once", "command": f"{prefix}{remote_template_shell('ros2 topic echo --once /scan')}"},
        {"name": "amcl_pose_once", "command": f"{prefix}{remote_template_shell('ros2 topic echo --once /amcl_pose')}"},
        {"name": "tf_map_odom", "command": f"{prefix}{remote_template_shell('ros2 run tf2_ros tf2_echo map odom')}"},
        {"name": "tf_map_base_link", "command": f"{prefix}{remote_template_shell('ros2 run tf2_ros tf2_echo map base_link')}"},
    ]


def nav2_refresh_template(target: str, port: int | None = None) -> str:
    # refresh 模板固定请求体，明确它只是 no-motion readback，不接受现场任意 body。
    command = " ".join(shlex.quote(part) for part in nav2_refresh_command(8, NAV2_PROOF_REFRESH_URL))
    if target == "local":
        return command
    return f"{ssh_prefix(target, port)}{remote_template_shell(command)}"


def learning_command_templates(target: str, port: int | None = None) -> list[dict[str, str]]:
    # learn/save/replay 全部是模板；工具本身不启动会导致运动的 launch。
    prefix = ssh_prefix(target, port)
    out_dir = "$HOME/.ros/trashbot_runs/${RUN_ID}"
    return [
        {
            "name": "prepare_output_dir",
            "command": f"RUN_ID=field_route_$(date +%Y%m%d_%H%M%S); OUT_DIR={out_dir}; mkdir -p $OUT_DIR",
        },
        {
            "name": "learn_launch_route_record",
            "command": (
                (
                    "ros2 launch ros2_trashbot_bringup learn.launch.py "
                    f"route_recorder:=true route_output_dir:={out_dir}/route_data route_id:=board_field_route"
                )
                if target == "local"
                else f"{prefix}{remote_template_shell('ros2 launch ros2_trashbot_bringup learn.launch.py ' + 'route_recorder:=true route_output_dir:=' + out_dir + '/route_data route_id:=board_field_route')}"
            ),
        },
        {
            "name": "save_map",
            "command": (
                "ros2 service call /trashbot/save_map std_srvs/srv/Trigger"
                if target == "local"
                else f"{prefix}{remote_template_shell('ros2 service call /trashbot/save_map std_srvs/srv/Trigger')}"
            ),
        },
        {
            "name": "route_csv_to_yaml",
            "command": (
                (
                    "ros2 run ros2_trashbot_nav route_csv_to_yaml --ros-args "
                    f"-p input_csv:={out_dir}/route_data/route.csv -p output_yaml:={out_dir}/route_data/fixed_route.yaml"
                )
                if target == "local"
                else f"{prefix}{remote_template_shell('ros2 run ros2_trashbot_nav route_csv_to_yaml --ros-args ' + '-p input_csv:=' + out_dir + '/route_data/route.csv -p output_yaml:=' + out_dir + '/route_data/fixed_route.yaml')}"
            ),
        },
        {
            "name": "fixed_route_autonomy_dry_run",
            "command": (
                (
                    "ros2 run ros2_trashbot_nav fixed_route_autonomy --ros-args "
                    f"-p route_file:={out_dir}/route_data/fixed_route.yaml -p keyframe_dir:={out_dir}/route_data/keyframes "
                    "-p dry_run:=true -p enable_visual_gate:=false"
                )
                if target == "local"
                else f"{prefix}{remote_template_shell('ros2 run ros2_trashbot_nav fixed_route_autonomy --ros-args ' + '-p route_file:=' + out_dir + '/route_data/fixed_route.yaml -p keyframe_dir:=' + out_dir + '/route_data/keyframes -p dry_run:=true -p enable_visual_gate:=false')}"
            ),
        },
        {
            "name": "optional_rosbag_record",
            "command": (
                f"ros2 bag record -o {out_dir}/route_bag /scan /camera/image_raw /odom /tf /map"
                if target == "local"
                else f"{prefix}{remote_template_shell('ros2 bag record -o ' + out_dir + '/route_bag /scan /camera/image_raw /odom /tf /map')}"
            ),
        },
    ]


def blocked_reason_for(status: str) -> str | None:
    # ready 仍然 not_proven，因为 preflight 不等于真实 route/map 验收。
    if status in {"ready_for_live_route_capture_not_proven", "live_localization_smoke_refresh_readback_not_proven"}:
        return None
    return status


def build_packet(args: argparse.Namespace) -> dict[str, Any]:
    if args.dry_run:
        checks = dry_run_checks(args)
        status = "dry_run_template_only_not_proven"
    elif args.mode == "local":
        checks, status = local_real_checks(args)
    else:
        checks, status = ssh_real_checks(args)

    target = {
        "mode": args.mode,
        "ssh_target": args.ssh_target if args.mode == "ssh" else None,
        "ssh_port": args.ssh_port if args.mode == "ssh" else None,
        "timeout_s": args.timeout_s,
    }
    commands = {
        "topic_smoke": topic_smoke_templates(
            args.ssh_target if args.mode == "ssh" else "local",
            args.ssh_port if args.mode == "ssh" else None,
        ),
        "localization_smoke": localization_smoke_templates(
            args.ssh_target if args.mode == "ssh" else "local",
            args.ssh_port if args.mode == "ssh" else None,
        ),
        "nav2_proof_refresh": nav2_refresh_template(
            args.ssh_target if args.mode == "ssh" else "local",
            args.ssh_port if args.mode == "ssh" else None,
        ),
        "learning": learning_command_templates(
            args.ssh_target if args.mode == "ssh" else "local",
            args.ssh_port if args.mode == "ssh" else None,
        ),
    }
    daemon_summary = summarize_ros_cli_retry(checks)
    return {
        "schema": SCHEMA,
        "status": status,
        "source": "software_preflight",
        "mode": args.mode,
        "dry_run": args.dry_run,
        "generated_at": utc_now(),
        "target": target,
        "checks": checks,
        "root_cause_summary": root_cause_from_checks(checks),
        "daemon_fault_detected": daemon_summary.get("daemon_fault_detected"),
        "daemon_recovered": daemon_summary.get("daemon_recovered"),
        "retry_attempts": daemon_summary.get("retry_attempts"),
        "recovered_topics": daemon_summary.get("recovered_targets", []),
        "unrecovered_blockers": daemon_summary.get("unrecovered_blockers", []),
        "ros_daemon_health": daemon_summary.get("ros_daemon_health"),
        "ros_cli_retry_summary": daemon_summary.get("events", []),
        "commands": commands,
        "next_required_evidence": [
            "真实上位机 SSH 可达证据",
            "ROS2 setup.bash 和 trashbot package 可用证据",
            "/scan、/amcl_pose、map->odom、map->base_link live localization smoke 输出",
            "/api/nav2/proof/refresh no-motion readback",
            "/scan、/camera/image_raw、/odom、/tf、/map topic 与 smoke 输出",
            "map.yaml、route.csv、keyframes、rosbag 或 replay JSONL",
        ],
        "blocked_reason": blocked_reason_for(status),
        "not_proven": True,
        **NO_MOTION_FALSE_FLAGS,
    }


def write_packet(packet: dict[str, Any], output: Path) -> None:
    # 父目录由工具创建，现场只需要指定目标文件即可稳定落盘。
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(strip_private_fields(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def strip_private_fields(value: Any) -> Any:
    # 内部完整 stdout/stderr 只供本次进程判断，不写进 artifact，避免 JSON 过大。
    if isinstance(value, dict):
        return {
            key: strip_private_fields(item)
            for key, item in value.items()
            if not key.startswith("_")
        }
    if isinstance(value, list):
        return [strip_private_fields(item) for item in value]
    return value


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a board field route evidence preflight packet.")
    parser.add_argument("--mode", choices=["local", "ssh"], required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--ssh-target", default="root@192.168.1.11")
    parser.add_argument("--ssh-port", type=int, default=37878)
    parser.add_argument("--timeout-s", type=int, default=8)
    parser.add_argument("--nav2-refresh-url", default=NAV2_PROOF_REFRESH_URL)
    parser.add_argument("--managed-map-yaml", default=MANAGED_MAP_YAML)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    if args.timeout_s < 1:
        parser.error("--timeout-s must be >= 1")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    packet = build_packet(args)
    write_packet(packet, Path(args.output))
    # stdout 只输出短摘要，完整证据写入 JSON，便于 automation 捕捉关键状态。
    print(json.dumps({"schema": SCHEMA, "status": packet["status"], "output": args.output}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
