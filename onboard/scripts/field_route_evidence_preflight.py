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
SETUP_CANDIDATES = [
    "/opt/ros/humble/setup.bash",
    "/root/rober/onboard/install/setup.bash",
    "/root/rober/install/setup.bash",
    "/ws/install/setup.bash",
    "~/rober/onboard/install/setup.bash",
    "~/apps/rober/onboard/install/setup.bash",
]


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
            "stdout": safe_text(exc.stdout or ""),
            "stderr": safe_text(exc.stderr or ""),
            "_stdout_full": exc.stdout or "",
            "_stderr_full": exc.stderr or "",
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
    if remote:
        command = build_ssh_command(
            args.ssh_target,
            args.ssh_port,
            build_remote_ros_command("ros2 topic list"),
            args.timeout_s,
        )
        result = run_command(command, args.timeout_s + 2)
    else:
        result = run_command(["ros2", "topic", "list"], args.timeout_s)
    found = set(result_stdout_lines(result)) if result["returncode"] == 0 else set()
    missing = [topic for topic in REQUIRED_TOPICS if topic not in found]
    check = {"ok": result["returncode"] == 0 and not missing, "required": REQUIRED_TOPICS, "missing": missing, "result": result}
    return check, (None if check["ok"] else "blocked_required_topics_missing")


def check_topic_smoke(args: argparse.Namespace, remote: bool) -> tuple[dict[str, Any], str | None]:
    # smoke 采样用进程 timeout 兜底，避免 ros2 topic hz 长时间阻塞现场收口。
    results = []
    for topic in SMOKE_TOPICS:
        local_command = ["ros2", "topic", "hz", topic, "--window", "2"]
        if remote:
            remote_command = build_remote_ros_command(" ".join(local_command))
            command = build_ssh_command(args.ssh_target, args.ssh_port, remote_command, args.timeout_s)
            result = run_command(command, args.timeout_s + 2)
        else:
            result = run_command(local_command, args.timeout_s)
        results.append({"topic": topic, "kind": "hz", "ok": result["returncode"] == 0, "result": result})

    tf_command = ["ros2", "topic", "echo", "--once", "/tf"]
    if remote:
        result = run_command(
            build_ssh_command(
                args.ssh_target,
                args.ssh_port,
                build_remote_ros_command(" ".join(tf_command)),
                args.timeout_s,
            ),
            args.timeout_s + 2,
        )
    else:
        result = run_command(tf_command, args.timeout_s)
    results.append({"topic": "/tf", "kind": "echo_once", "ok": result["returncode"] == 0, "result": result})

    ok = all(item["ok"] for item in results)
    return {
        "ok": ok,
        "results": results,
        "templates": topic_smoke_templates(args.ssh_target if remote else "local", args.ssh_port if remote else None),
    }, (
        None if ok else "blocked_topic_smoke_failed"
    )


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
    checks["topics"], status = check_topics(args, remote=False)
    if status:
        return checks, status
    checks["topic_smoke_commands"], status = check_topic_smoke(args, remote=False)
    if status:
        return checks, status
    checks["learning_commands"] = {"ok": True, "templates": learning_command_templates("local")}
    checks["output_contract"] = output_contract()
    return checks, "ready_for_live_route_capture_not_proven"


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
    checks["topics"], status = check_topics(args, remote=True)
    if status:
        return checks, status
    checks["topic_smoke_commands"], status = check_topic_smoke(args, remote=True)
    if status:
        return checks, status
    checks["learning_commands"] = {"ok": True, "templates": learning_command_templates(args.ssh_target, args.ssh_port)}
    checks["output_contract"] = output_contract()
    return checks, "ready_for_live_route_capture_not_proven"


def output_contract() -> dict[str, Any]:
    # RUN_ID/OUT_DIR 固化为模板，避免现场多次运行覆盖 map、route、keyframe 等材料。
    return {
        "ok": True,
        "run_id_template": "field_route_$(date +%Y%m%d_%H%M%S)",
        "out_dir_template": "$HOME/.ros/trashbot_runs/${RUN_ID}",
        "required_artifacts": [
            "field_preflight.json",
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
    if status == "ready_for_live_route_capture_not_proven":
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
        "learning": learning_command_templates(
            args.ssh_target if args.mode == "ssh" else "local",
            args.ssh_port if args.mode == "ssh" else None,
        ),
    }
    return {
        "schema": SCHEMA,
        "status": status,
        "source": "software_preflight",
        "mode": args.mode,
        "dry_run": args.dry_run,
        "generated_at": utc_now(),
        "target": target,
        "checks": checks,
        "commands": commands,
        "next_required_evidence": [
            "真实上位机 SSH 可达证据",
            "ROS2 setup.bash 和 trashbot package 可用证据",
            "/scan、/camera/image_raw、/odom、/tf、/map topic 与 smoke 输出",
            "map.yaml、route.csv、keyframes、rosbag 或 replay JSONL",
        ],
        "blocked_reason": blocked_reason_for(status),
        "not_proven": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
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
