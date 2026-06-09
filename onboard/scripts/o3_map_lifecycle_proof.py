#!/usr/bin/env python3
"""no-motion LiDAR + SLAM `/map` lifecycle proof 采集器。

这个 helper 是 `/api/map/proof/refresh` 的内置入口，只证明传感器和 SLAM
生命周期材料，不发布 `/cmd_vel`，不调用底盘 manual API，也不打开 WAVE ROVER
UART。保存地图前必须先观测到 `/map`，避免把旧 YAML/PGM 误当成本轮地图。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import signal
import subprocess
import time
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.upper_robot_api.v1.map_lifecycle_runtime_proof"
DEFAULT_ROS_SETUP = "/opt/ros/humble/setup.bash"
DEFAULT_ONBOARD_SETUP = "/root/rober/onboard/install/setup.bash"
DEFAULT_WORKDIR = "/root/rober/onboard"
DEFAULT_OUTPUT = "/root/rober/onboard/runtime/map_lifecycle_latest.json"
DEFAULT_MAP_DIR = "/root/rober/onboard/runtime/maps"
VENDOR_SOURCES = [
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/lidar_pkg_ros2-main/README.md",
    "docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp",
    "docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml",
    "docs/vendor/lidar_pkg_ros2-main/launch/lidar.launch.py",
]


def now_ms() -> int:
    """统一使用毫秒时间戳，方便和 upper API/readback 对齐。"""
    return int(time.time() * 1000)


def safety_flags() -> dict[str, Any]:
    """本 proof 只允许传感器和 SLAM，不允许把任何结果外推成可控车。"""
    return {
        "safe_to_control": False,
        "sends_base_motion_commands": False,
        "sends_motion_commands": False,
        "robot_control_executed": False,
        "publishes_cmd_vel": False,
        "calls_base_manual": False,
        "uses_base_uart": False,
        "delivery_success": False,
        "hil_pass": False,
    }


def compact_error(error: BaseException) -> dict[str, str]:
    """错误只保留类型和短文本，避免 artifact 混入大量环境噪声。"""
    return {"type": type(error).__name__, "message": str(error)[:240]}


def source_prefix(args: argparse.Namespace) -> str:
    """ROS setup 必须在 bash 里 source；不要在 zsh 里直接 source bash 脚本。"""
    pieces = [
        "set -e",
        f"source {shlex.quote(args.ros_setup)}",
        f"[ -f {shlex.quote(args.onboard_setup)} ] && source {shlex.quote(args.onboard_setup)} || true",
        f"cd {shlex.quote(args.workdir)}",
    ]
    return "; ".join(pieces)


def run_ros(args: argparse.Namespace, command: str, timeout_s: float) -> dict[str, Any]:
    """通过 bash -lc 执行 ROS2 命令，避免远端默认 shell 破坏 setup.bash。"""
    started_ms = now_ms()
    try:
        completed = subprocess.run(
            ["bash", "-lc", f"{source_prefix(args)}; {command}"],
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout_s,
        )
        return {
            "command": command,
            "executed": True,
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "elapsed_ms": now_ms() - started_ms,
            "stdout": completed.stdout[-8000:],
            "stderr": completed.stderr[-4000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "executed": True,
            "ok": False,
            "returncode": None,
            "elapsed_ms": now_ms() - started_ms,
            "error": compact_error(exc),
            "stdout": (exc.stdout or "")[-8000:] if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
        }


def package_available(args: argparse.Namespace, package: str) -> tuple[bool, dict[str, Any]]:
    """用 ros2 pkg prefix 判定包是否安装，避免从 topic 缺失反猜依赖。"""
    result = run_ros(args, f"ros2 pkg prefix {shlex.quote(package)}", timeout_s=6.0)
    return bool(result.get("ok")), result


def start_runtime(args: argparse.Namespace) -> dict[str, Any]:
    """启动 learn.launch.py 的 LiDAR+SLAM 窗口；该 launch 不发布 /cmd_vel。"""
    map_dir = shlex.quote(args.map_dir)
    launch_command = " ".join(
        [
            "ros2 launch ros2_trashbot_bringup learn.launch.py",
            "lidar_enabled:=true",
            f"lidar_serial_port:={shlex.quote(args.serial_port)}",
            f"lidar_serial_baudrate:={int(args.serial_baudrate)}",
            f"lidar_frame_id:={shlex.quote(args.frame_id)}",
            "lidar_publish_raw_packets:=true",
            # slam_toolbox 订阅 laser_frame 的 /scan，no-motion proof 必须补齐 base_link -> laser_frame。
            "static_laser_tf_enabled:=true",
            "no_motion_static_odom_tf:=true",
            "waypoint_manager:=false",
            f"map_dir:={map_dir}",
            f"default_map_name:={shlex.quote(args.map_name)}",
        ]
    )
    log_path = f"/tmp/rober_map_lifecycle_runtime_{now_ms()}.log"
    started_ms = now_ms()
    try:
        log_handle = open(log_path, "ab", buffering=0)
        process = subprocess.Popen(
            ["bash", "-lc", f"{source_prefix(args)}; {launch_command}"],
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
        log_handle.close()
        time.sleep(max(args.startup_s, 0.0))
        return {
            "mode": "learn_launch_lidar_slam_no_motion",
            "executed": True,
            "ok": process.poll() is None,
            "pid": process.pid,
            "returncode_after_startup": process.poll(),
            "elapsed_ms": now_ms() - started_ms,
            "log_path": log_path,
            "log_tail": read_text(log_path)[-4000:],
            "command": launch_command,
            **safety_flags(),
        }
    except Exception as exc:  # noqa: BLE001 - 现场权限/launch 缺口要进入 proof。
        return {
            "mode": "learn_launch_lidar_slam_no_motion",
            "executed": False,
            "ok": False,
            "elapsed_ms": now_ms() - started_ms,
            "error": compact_error(exc),
            "command": launch_command,
            **safety_flags(),
        }


def stop_runtime(runtime: dict[str, Any]) -> dict[str, Any]:
    """结束本 helper 启动的 launch 进程组，避免短窗口 proof 变成常驻服务。"""
    pid = runtime.get("pid")
    if not isinstance(pid, int):
        return {"attempted": False, "reason": "runtime_pid_missing", **safety_flags()}
    try:
        os.killpg(pid, signal.SIGINT)
        time.sleep(2.0)
        return {"attempted": True, "ok": True, "signal": "SIGINT", "pid": pid, **safety_flags()}
    except ProcessLookupError:
        return {"attempted": True, "ok": True, "reason": "process_already_exited", "pid": pid, **safety_flags()}
    except Exception as exc:  # noqa: BLE001 - 停止失败要留痕，后续由 operator 排查进程。
        return {"attempted": True, "ok": False, "pid": pid, "error": compact_error(exc), **safety_flags()}


def read_text(path: str, max_bytes: int = 8000) -> str:
    """读取日志尾部；失败返回空串，不阻塞 proof artifact 写入。"""
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")[-max_bytes:]
    except OSError:
        return ""


def parse_map_metadata(map_stdout: str) -> dict[str, Any]:
    """从 ros2 topic echo 文本里抽取最小地图元数据，质量评估另走独立工具。"""
    metadata: dict[str, Any] = {}
    patterns = {
        "frame_id": r"frame_id:\s*['\"]?([^'\"\n]+)",
        "resolution": r"resolution:\s*([0-9.eE+-]+)",
        "width": r"width:\s*([0-9]+)",
        "height": r"height:\s*([0-9]+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, map_stdout)
        if not match:
            continue
        raw = match.group(1).strip()
        if key in {"width", "height"}:
            metadata[key] = int(raw)
        elif key == "resolution":
            metadata[key] = float(raw)
        else:
            metadata[key] = raw
    return metadata


def list_map_files(map_dir: str) -> list[dict[str, Any]]:
    """列出保存出的 YAML/PGM/PBStream；存在也不代表可导航。"""
    root = Path(map_dir)
    files: list[dict[str, Any]] = []
    for pattern in ("*.yaml", "*.pgm", "*.pbstream"):
        for path in sorted(root.glob(pattern)):
            try:
                stat_result = path.stat()
            except OSError as exc:
                files.append({"path": str(path), "ok": False, "error": compact_error(exc)})
                continue
            files.append(
                {
                    "path": str(path),
                    "name": path.name,
                    "suffix": path.suffix,
                    "size_bytes": stat_result.st_size,
                    "mtime_ms": int(stat_result.st_mtime_ns / 1_000_000),
                }
            )
    return files


def workdir_path(args: argparse.Namespace, path: str) -> str:
    """相对路径统一按 onboard workdir 解析，避免 systemd cwd 让 artifact 误判。"""
    candidate = Path(path)
    if candidate.is_absolute():
        return str(candidate)
    return str(Path(args.workdir) / candidate)


def classify_root_causes(
    *,
    ros2_ok: bool,
    packages: dict[str, bool],
    scan_observed: bool,
    map_observed: bool,
    save_ok: bool,
    map_files: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """按 sprint 要求把失败收敛到具体层，而不是只写 map missing。"""
    causes: list[dict[str, str]] = []
    if not ros2_ok:
        causes.append({"layer": "ROS install/source", "reason": "ros2_command_unavailable_after_bash_source"})
        return causes
    for package, available in packages.items():
        if not available:
            causes.append({"layer": "ROS install/source", "reason": f"{package}_missing"})
    if not scan_observed:
        causes.append({"layer": "LiDAR/launch/topic remap", "reason": "/scan_once_not_observed"})
    if scan_observed and not map_observed:
        causes.append({"layer": "SLAM/TF/topic remap", "reason": "/map_once_not_observed"})
    if map_observed and not save_ok:
        causes.append({"layer": "map saver", "reason": "trashbot_save_map_service_failed_or_missing"})
    if map_observed and save_ok and not map_files:
        causes.append({"layer": "file path/permissions", "reason": "map_save_reported_success_but_no_artifact_files_found"})
    return causes


def write_json_atomic(path: str, payload: dict[str, Any]) -> None:
    """原子写 latest artifact，避免 PC/API 读到半截 JSON。"""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp_path, output_path)


def build_proof(args: argparse.Namespace) -> dict[str, Any]:
    """执行一次 no-motion lifecycle proof，成功或失败都写清证据边界。"""
    started_ms = now_ms()
    ros2_check = run_ros(args, "command -v ros2", timeout_s=6.0)
    ros2_ok = bool(ros2_check.get("ok"))
    package_names = ["ros2_trashbot_bringup", "ros2_trashbot_nav", "ros2_trashbot_hardware", "slam_toolbox"]
    package_results: dict[str, dict[str, Any]] = {}
    packages: dict[str, bool] = {}
    if ros2_ok:
        for package in package_names:
            available, result = package_available(args, package)
            packages[package] = available
            package_results[package] = result
    else:
        packages = {package: False for package in package_names}

    runtime: dict[str, Any] | None = None
    if ros2_ok and all(packages.values()):
        runtime = start_runtime(args)

    topic_list = run_ros(args, "ros2 topic list", timeout_s=8.0) if ros2_ok else {"executed": False, "ok": False}
    scan_once = run_ros(args, "timeout 8 ros2 topic echo --once /scan", timeout_s=10.0) if runtime else {"executed": False, "ok": False}
    map_once = run_ros(args, "timeout 12 ros2 topic echo --once /map", timeout_s=14.0) if runtime else {"executed": False, "ok": False}
    save_map = (
        run_ros(args, "timeout 8 ros2 service call /trashbot/save_map std_srvs/srv/Trigger '{}'", timeout_s=10.0)
        if map_once.get("ok")
        else {"executed": False, "ok": False, "reason": "skipped_until_map_once_observed"}
    )
    stop_result = stop_runtime(runtime) if runtime else {"attempted": False, "reason": "runtime_not_started", **safety_flags()}

    map_artifact_dir = workdir_path(args, args.map_dir)
    map_files = list_map_files(map_artifact_dir)
    scan_observed = bool(scan_once.get("ok") and str(scan_once.get("stdout") or "").strip())
    map_observed = bool(map_once.get("ok") and str(map_once.get("stdout") or "").strip())
    save_ok = bool(save_map.get("ok") and "success=True" in str(save_map.get("stdout") or ""))
    metadata = parse_map_metadata(str(map_once.get("stdout") or ""))
    root_causes = classify_root_causes(
        ros2_ok=ros2_ok,
        packages=packages,
        scan_observed=scan_observed,
        map_observed=map_observed,
        save_ok=save_ok,
        map_files=map_files,
    )
    complete = bool(scan_observed and map_observed and metadata and map_files and not root_causes)
    proof_status = "map_once_artifact_metadata_observed" if complete else "blocked_with_root_cause"
    proof = {
        "status": proof_status,
        "evidence_ref": f"o3-map-lifecycle-{started_ms}",
        "evidence_type": "robot_runtime_material" if complete else "blocked_with_root_cause",
        "started_at_ms": started_ms,
        "generated_at_ms": now_ms(),
        "elapsed_ms": now_ms() - started_ms,
        "map_once_observed": map_observed,
        "scan_once_observed": scan_observed,
        "map_file_observed": bool(map_files),
        "map_metadata_observed": bool(metadata),
        "slam_toolbox_state": "package_missing" if not packages.get("slam_toolbox") else ("runtime_attempted" if runtime else "not_started"),
        "root_causes": root_causes,
        "blockers": root_causes,
        "map_metadata": metadata,
        "map_files": map_files,
        "map_artifact_dir": map_artifact_dir,
        "commands": {
            "ros2_check": ros2_check,
            "package_checks": package_results,
            "runtime": runtime,
            "topic_list": topic_list,
            "scan_once": scan_once,
            "map_once": map_once,
            "save_map": save_map,
            "stop_runtime": stop_result,
        },
        "algorithm_boundary": {
            "slam_map_quality_evaluated": False,
            "map_usable_for_navigation": False,
            "amcl_ready": False,
            "nav2_ready": False,
            "fixed_route_ready": False,
        },
        **safety_flags(),
    }
    return {
        "schema": SCHEMA,
        "generated_at_ms": now_ms(),
        "vendor_sources": VENDOR_SOURCES,
        "proof": proof,
        "status": proof_status,
        "evidence_type": proof["evidence_type"],
        "not_proven": not complete,
        "software_guard": True,
        **safety_flags(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--map-dir", default=DEFAULT_MAP_DIR)
    parser.add_argument("--map-name", default="trashbot_map")
    parser.add_argument("--serial-port", default="/dev/ttyACM0")
    parser.add_argument("--serial-baudrate", type=int, default=150000)
    parser.add_argument("--frame-id", default="laser_frame")
    parser.add_argument("--startup-s", type=float, default=8.0)
    parser.add_argument("--timeout-s", type=float, default=45.0)
    parser.add_argument("--ros-setup", default=DEFAULT_ROS_SETUP)
    parser.add_argument("--onboard-setup", default=DEFAULT_ONBOARD_SETUP)
    parser.add_argument("--workdir", default=DEFAULT_WORKDIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_proof(args)
    write_json_atomic(args.output, payload)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if payload["proof"]["status"] == "map_once_artifact_metadata_observed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
