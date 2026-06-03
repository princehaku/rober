#!/usr/bin/env python3
"""只读采集 O1 上位机 readiness 快照，默认 fail-closed。"""

from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable


# 版本号不从 git 读取，因为远端 stdin 运行时可能没有仓库。
SCHEMA_VERSION = "trashbot.o1.upper_computer_readiness.v1"
ROS_HUMBLE_SETUP = "/opt/ros/humble/setup.bash"
ROBER_REPO_ROOT = "/root/rober"
ROBER_ONBOARD_ROOT = "/root/rober/onboard"
ROBER_INSTALL_SETUP = "/root/rober/onboard/install/setup.bash"
O1_BOOTSTRAP_SCRIPT = "onboard/scripts/o1_ros2_humble_arm64_bootstrap.sh"
O1_SCAN_SMOKE_SCRIPT = "onboard/scripts/o1_lidar_ros2_scan_smoke.sh"
# 串口候选只允许来自这些 glob，避免把网卡、蓝牙或其他敏感设备暴露进 artifact。
SERIAL_CANDIDATE_PATTERNS = (
    "/dev/ttyUSB*",
    "/dev/ttyAMA*",
    "/dev/ttyACM*",
    "/dev/serial*",
    "/dev/serial/by-id/*",
    "/dev/serial/by-path/*",
)
# LiDAR 候选只用于 readiness 判断；真正打开哪个设备必须由现场 smoke 显式选择。
LIDAR_CANDIDATE_MARKERS = ("lidar", "STC", "stc", "ttyACM")
# vendor source 固定写入 JSON，方便后续 HIL 证据审查能回到本地资料。
VENDOR_SOURCES = (
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
    "docs/vendor/lidar_pkg_ros2-main/README.md",
    "docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp",
    "docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml",
    "docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules",
    "docs/vendor/lidar_ros/SOURCE.md",
    "docs/vendor/lidar_ros/README.md",
    "docs/vendor/lidar_ros/plot.py",
    "docs/vendor/lidar_ros/src/lidar_pkg/scripts/lidar_driver.py",
    "docs/vendor/lidar_ros/src/lidar_pkg/src/lidar_driver.cpp",
)


def _safe_run(command: str, timeout_s: float = 5.0) -> dict:
    """只运行低风险只读命令；超时和失败都结构化进入 readiness。"""
    try:
        completed = subprocess.run(
            ["bash", "-lc", command],
            check=False,
            text=True,
            capture_output=True,
            timeout=timeout_s,
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "ok": completed.returncode == 0,
            # stdout/stderr 截断，避免把远端环境噪声或路径细节无限写入 artifact。
            "stdout_preview": completed.stdout[:1600],
            "stderr_preview": completed.stderr[:1600],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": None,
            "ok": False,
            "error": {"type": "TimeoutExpired", "message": str(exc)[:300]},
        }


def summarize_serial_candidates(
    globber: Callable[[str], Iterable[str]] = glob.glob,
    patterns: Iterable[str] = SERIAL_CANDIDATE_PATTERNS,
) -> dict:
    """只做路径枚举，不 stat 权限、不打开串口，避免误触发硬件。"""
    by_pattern = {}
    total = 0
    # glob 本身不会打开字符设备，符合本轮只读上位机材料采集边界。
    for pattern in patterns:
        # 这里保留设备路径是为了后续 HIL 人工判读；不读取设备属性。
        matches = sorted(str(path) for path in globber(pattern))
        # 每个 pattern 单独计数，远端缺设备时也能看出是哪个候选族为空。
        by_pattern[pattern] = {"count": len(matches), "paths": matches}
        total += len(matches)
    return {"status": "listed_not_opened", "total_count": total, "by_pattern": by_pattern}


def _find_repo_root(start: Path) -> Path | None:
    """从脚本位置向上查找仓库根，stdin 远端执行时允许返回 None。"""
    # /root/rober 是当前上位机约定路径；stdin 从 /root 执行时父级搜索看不到它。
    explicit_candidates = [Path(ROBER_REPO_ROOT), Path("/ws"), Path.cwd()]
    for candidate in [start, *start.parents, *explicit_candidates]:
        # 用 AGENTS.md + onboard 双条件识别 rober 根，避免在 /root stdin 场景误判。
        if (candidate / "AGENTS.md").is_file() and (candidate / "onboard").is_dir():
            return candidate
    return None


def _path_hint(path: Path) -> dict:
    """只返回存在性与路径提示，不读取凭证类文件内容。"""
    # exists/is_dir 足够判断环境 readiness，不需要读取目标文件内容。
    return {"path": str(path), "exists": path.exists(), "is_dir": path.is_dir()}


def _is_pyserial_available() -> bool:
    """安全检测 pyserial；测试 stub 的 __spec__ 异常也按不可用处理。"""
    try:
        return importlib.util.find_spec("serial") is not None
    except Exception:
        # readiness probe 必须 fail-closed，不能因为半初始化模块让整份 JSON 崩掉。
        return False


def _flatten_serial_paths(serial_summary: dict) -> list[str]:
    """把按 pattern 分组的串口候选摊平，方便后续 readiness 规则复用。"""
    paths: list[str] = []
    # readiness JSON 允许未来扩展字段，所以这里按 dict 防御式读取。
    for item in serial_summary.get("by_pattern", {}).values():
        paths.extend(str(path) for path in item.get("paths", []))
    # 去重后排序，保证 artifact diff 稳定，便于 hourly automation 比较漂移。
    return sorted(set(paths))


def _lidar_candidate_paths(serial_summary: dict) -> list[str]:
    """基于路径名字推导 LiDAR 候选，不打开设备也不读取 USB 属性。"""
    candidates = []
    for path in _flatten_serial_paths(serial_summary):
        # /dev/lidar 是 vendor udev 目标；STC/ttyACM 是当前现场观察到的候选线索。
        if any(marker in path for marker in LIDAR_CANDIDATE_MARKERS):
            candidates.append(path)
    return sorted(set(candidates))


def _docker_arm64_runtime_status(command_runner: Callable[[str, float], dict]) -> dict:
    """检查本机是否已有可用 arm64 ROS2 容器后备，不拉镜像、不联网。"""
    docker_version = command_runner("command -v docker >/dev/null && docker version --format '{{.Server.Arch}}'", 4.0)
    images: list[dict] = []
    # 只 inspect 本地镜像，避免 readiness probe 变成网络下载或构建动作。
    for image in ("ros-rbs-humble:dev", "osrf/ros:humble-desktop"):
        result = command_runner(f"docker image inspect --format '{{{{.Architecture}}}}' {image}", 4.0)
        architecture = result.get("stdout_preview", "").strip()
        images.append(
            {
                "image": image,
                "present": bool(result.get("ok")),
                "architecture": architecture if result.get("ok") else "",
                "usable_arm64": bool(result.get("ok")) and architecture in {"arm64", "aarch64"},
            }
        )
    return {
        "docker_available": bool(docker_version.get("ok")),
        "server_arch": docker_version.get("stdout_preview", "").strip() if docker_version.get("ok") else "",
        "checks": {
            "docker_version": docker_version,
            # 镜像 inspect 结果保留摘要，方便现场判断是缺镜像还是架构不对。
            "images": images,
        },
        "local_arm64_ros_image_available": any(item["usable_arm64"] for item in images),
    }


def _ros2_topic_status(command_runner: Callable[[str, float], dict], runtime_ready: bool) -> dict:
    """runtime 就绪后才列 ROS2 topic；该动作只读，不 launch、不发布。"""
    command = f"source {ROS_HUMBLE_SETUP} && source {ROBER_INSTALL_SETUP} && timeout 5 ros2 topic list"
    if not runtime_ready:
        return {"attempted": False, "reason": "runtime_or_install_missing", "command": command, "topics": []}
    result = command_runner(command, 7.0)
    topics = [line.strip() for line in result.get("stdout_preview", "").splitlines() if line.strip().startswith("/")]
    return {"attempted": True, "result": result, "command": command, "topics": topics}


def _ros2_command_status(command_runner: Callable[[str, float], dict], humble_setup_exists: bool) -> dict:
    """只检查 ros2 CLI 是否可解析，不启动节点也不访问 ROS graph。"""
    command = f"source {ROS_HUMBLE_SETUP} && command -v ros2"
    if not humble_setup_exists:
        # setup 文件缺失时不 source，避免 stderr 噪声掩盖真正 blocker。
        return {"attempted": False, "reason": "ros_humble_setup_missing", "command": command, "available": False}
    result = command_runner(command, 4.0)
    return {"attempted": True, "result": result, "command": command, "available": bool(result.get("ok"))}


def _driver_evidence(onboard_path: Path, install_setup_exists: bool) -> dict:
    """检查 repo/install 中 LiDAR driver 入口迹象；只读文件元数据和 setup.py 文本。"""
    package_root = onboard_path / "src" / "ros2_trashbot_hardware"
    driver_path = package_root / "ros2_trashbot_hardware" / "lidar_driver.py"
    setup_path = package_root / "setup.py"
    setup_text = ""
    try:
        # 只读取 setup.py 是为了确认 console_scripts 入口，避免 install 缺失时误报 ready。
        setup_text = setup_path.read_text(encoding="utf-8") if setup_path.is_file() else ""
    except UnicodeDecodeError:
        setup_text = ""
    source_entrypoint_present = "lidar_driver = ros2_trashbot_hardware.lidar_driver:main" in setup_text

    installed_candidates = [
        onboard_path / "install" / "ros2_trashbot_hardware" / "lib" / "ros2_trashbot_hardware" / "lidar_driver",
        onboard_path / "install" / "ros2_trashbot_hardware" / "lib" / "python3.10" / "site-packages"
        / "ros2_trashbot_hardware"
        / "lidar_driver.py",
    ]
    install_entrypoint_present = install_setup_exists and any(path.exists() for path in installed_candidates)
    return {
        "source_driver": {"path": str(driver_path), "exists": driver_path.is_file()},
        "source_setup_entrypoint": {"path": str(setup_path), "present": source_entrypoint_present},
        "install_entrypoint": {
            "present": install_entrypoint_present,
            "candidate_paths": [str(path) for path in installed_candidates],
        },
        # source 入口足够进入 build/install 阶段；真实运行仍要求 install setup 存在。
        "repo_driver_ready": driver_path.is_file() and source_entrypoint_present,
        "install_driver_ready": install_entrypoint_present,
    }


def build_lidar_ros2_bootstrap_readiness(
    *,
    repo_root: Path | None,
    onboard_path: Path,
    humble_setup_exists: bool,
    install_setup_exists: bool,
    serial_summary: dict,
    command_runner: Callable[[str, float], dict] = _safe_run,
) -> dict:
    """输出 LiDAR ROS2 bootstrap 六类状态，供现场按 blocker 精准补齐。"""
    repo_present = repo_root is not None and onboard_path.is_dir()
    lidar_candidates = _lidar_candidate_paths(serial_summary)
    ros2_cli = _ros2_command_status(command_runner, humble_setup_exists)
    driver_evidence = _driver_evidence(onboard_path, install_setup_exists) if repo_present else {
        "source_driver": {"path": str(onboard_path / "src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py"), "exists": False},
        "source_setup_entrypoint": {"path": str(onboard_path / "src/ros2_trashbot_hardware/setup.py"), "present": False},
        "install_entrypoint": {"present": False, "candidate_paths": []},
        "repo_driver_ready": False,
        "install_driver_ready": False,
    }

    blocker_codes: list[str] = []
    if not humble_setup_exists or not ros2_cli["available"]:
        blocker_codes.append("runtime_missing")
    if not repo_present:
        blocker_codes.append("repo_missing")
    if repo_present and not install_setup_exists:
        blocker_codes.append("install_missing")
    if repo_present and not driver_evidence["repo_driver_ready"]:
        blocker_codes.append("driver_missing")
    if repo_present and install_setup_exists and not driver_evidence["install_driver_ready"]:
        blocker_codes.append("driver_missing")
    if not lidar_candidates:
        blocker_codes.append("lidar_device_missing")

    status_priority = (
        "runtime_missing",
        "repo_missing",
        "install_missing",
        "driver_missing",
        "lidar_device_missing",
    )
    status = next((code for code in status_priority if code in blocker_codes), "ready_for_scan_bootstrap")
    candidate_port = lidar_candidates[0] if lidar_candidates else "<lidar_serial_port>"
    workspace = str(onboard_path) if repo_present else ROBER_ONBOARD_ROOT
    commands_if_ready = [
        f"source {ROS_HUMBLE_SETUP}",
        f"cd {workspace} && source install/setup.bash",
        "timeout 10 ros2 topic echo --once /scan",
        "timeout 10 ros2 topic hz /scan",
        "timeout 10 ros2 topic echo --once /lidar/raw_packet",
        (
            "ros2 run ros2_trashbot_hardware lidar_driver --ros-args "
            f"-p serial_port:={candidate_port} -p serial_baudrate:=150000 "
            "-p frame_id:=laser_frame -p publish_raw_packets:=true"
        ),
    ]
    remediation_plan = {
        "runtime_missing": (
            f"Run {O1_BOOTSTRAP_SCRIPT} on the upper computer or install/source ROS2 Humble so "
            f"{ROS_HUMBLE_SETUP} and ros2 CLI are both available."
        ),
        "repo_missing": f"Sync the rober checkout with onboard/ to {ROBER_REPO_ROOT} or run from a valid checkout.",
        "install_missing": (
            f"Run {O1_BOOTSTRAP_SCRIPT} after source sync, or build onboard workspace: cd {ROBER_ONBOARD_ROOT} "
            f"&& source {ROS_HUMBLE_SETUP} && colcon build --symlink-install."
        ),
        "driver_missing": "Restore ros2_trashbot_hardware/lidar_driver.py and the setup.py lidar_driver console_scripts entry, then rebuild install.",
        "lidar_device_missing": "Attach/install STC LiDAR udev rule so /dev/lidar, STC by-id, or ttyACM candidate is visible.",
        "ready_for_scan_bootstrap": (
            f"Run {O1_SCAN_SMOKE_SCRIPT} for LiDAR-only /scan proof; it starts only the LiDAR driver and static TF."
        ),
    }
    return {
        "status": status,
        "blocker_codes": blocker_codes,
        "remediation_plan": [remediation_plan[code] for code in blocker_codes] or [remediation_plan["ready_for_scan_bootstrap"]],
        "commands_if_ready": commands_if_ready if status == "ready_for_scan_bootstrap" else [],
        "candidate_ports": lidar_candidates,
        "selected_candidate_hint": candidate_port,
        "ros2_cli": ros2_cli,
        "driver_evidence": driver_evidence,
        "vendor_sources": [
            "docs/vendor/VENDOR_INDEX.md",
            "docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp",
            "docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml",
            "docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules",
        ],
        # fail-closed 安全字段是给 UI/API 消费的硬边界，不随 readiness 变成 true。
        "safe_to_control": False,
        "sends_commands": False,
        "sends_motion_commands": False,
        "sends_wave_rover_t_commands": False,
        "calls_base_manual": False,
        "publishes_cmd_vel": False,
        "opens_serial_devices": False,
        "starts_ros2_driver": False,
        "hil_pass": False,
        "scan_proven": False,
        "tf_proven": False,
        "slam_nav2_proven": False,
    }


def build_ros2_runtime_remediation_plan(
    *,
    repo_root: Path | None,
    onboard_path: Path,
    humble_setup_exists: bool,
    install_setup_exists: bool,
    lidar_candidates: list[str],
    command_runner: Callable[[str, float], dict] = _safe_run,
) -> dict:
    """把 `/scan` blocker 分类成下一条可执行动作，而不是只回放旧 artifact。"""
    repo_present = repo_root is not None and onboard_path.exists()
    docker_status = _docker_arm64_runtime_status(command_runner)
    runtime_ready = bool(humble_setup_exists and install_setup_exists)
    topic_status = _ros2_topic_status(command_runner, runtime_ready)
    topics = set(topic_status.get("topics", []))

    classifications: list[dict[str, str]] = []
    if not repo_present:
        classifications.append({"code": "repo_missing", "detail": f"{ROBER_ONBOARD_ROOT} or rober checkout not detected"})
    if not humble_setup_exists:
        classifications.append({"code": "runtime_missing", "detail": f"{ROS_HUMBLE_SETUP} not found"})
    if repo_present and not install_setup_exists:
        classifications.append({"code": "install_missing", "detail": f"{ROBER_INSTALL_SETUP} not found"})
    if (not humble_setup_exists or not install_setup_exists) and not docker_status["local_arm64_ros_image_available"]:
        classifications.append(
            {
                "code": "docker_arm64_unavailable",
                "detail": "no local arm64 ROS2/Humble image was confirmed by docker image inspect",
            }
        )
    if runtime_ready and ("/scan" not in topics or "/lidar/raw_packet" not in topics):
        classifications.append(
            {
                "code": "topics_not_running",
                "detail": "ROS2 runtime exists but /scan and/or /lidar/raw_packet are not currently listed",
            }
        )
    if not lidar_candidates:
        classifications.append({"code": "lidar_device_candidate_missing", "detail": "no read-only LiDAR serial candidate listed"})

    if any(item["code"] == "repo_missing" for item in classifications):
        next_action = "sync_rober_repo_to_upper_computer"
        next_command = "rsync/scp the rober checkout to /root/rober, then rerun this readiness probe"
    elif any(item["code"] == "runtime_missing" for item in classifications):
        next_action = "install_or_provide_ros2_humble_runtime"
        next_command = f"bash {ROBER_ONBOARD_ROOT}/scripts/o1_ros2_humble_arm64_bootstrap.sh"
    elif any(item["code"] == "install_missing" for item in classifications):
        next_action = "build_current_onboard_workspace"
        next_command = f"bash {ROBER_ONBOARD_ROOT}/scripts/o1_ros2_humble_arm64_bootstrap.sh --skip-apt-install"
    elif any(item["code"] == "docker_arm64_unavailable" for item in classifications):
        next_action = "prepare_arm64_docker_runtime"
        next_command = "load/build ros-rbs-humble:dev for arm64, then rerun readiness before /scan proof"
    elif any(item["code"] == "topics_not_running" for item in classifications):
        next_action = "start_lidar_driver_no_motion"
        port = lidar_candidates[0] if lidar_candidates else "<lidar_serial_port>"
        next_command = f"bash {ROBER_ONBOARD_ROOT}/scripts/o1_lidar_ros2_scan_smoke.sh --serial-port {port}"
    else:
        next_action = "collect_scan_proof_read_only_topics"
        next_command = (
            f"cd {ROBER_ONBOARD_ROOT} && source {ROS_HUMBLE_SETUP} && source install/setup.bash && "
            "timeout 10 ros2 topic echo --once /scan && timeout 10 ros2 topic echo --once /lidar/raw_packet"
        )

    return {
        "status": "ready_to_collect_scan_topics" if not classifications else "blocked",
        "primary_blocker": classifications[0]["code"] if classifications else "",
        "classifications": classifications,
        "next_action": next_action,
        "next_command": next_command,
        "docker_runtime": docker_status,
        "ros2_topics": topic_status,
        # 再次固定安全边界：分类 probe 只读，不启动 driver、不发底盘命令。
        "probe_sends_base_commands": False,
        "probe_starts_lidar_driver": False,
        "probe_publishes_cmd_vel": False,
    }


def build_lidar_runtime_readiness(
    *,
    serial_summary: dict,
    pyserial_available: bool,
    humble_setup_exists: bool,
    repo_root: Path | None,
) -> dict:
    """给现场同学一个机器可读的 no-motion LiDAR smoke gate。"""
    lidar_candidates = _lidar_candidate_paths(serial_summary)
    blockers: list[dict[str, str]] = []
    # ROS2 runtime 是 /scan 证据的硬前置；缺它只能做脚本级 readiness。
    if not humble_setup_exists:
        blockers.append(
            {
                "code": "ros2_humble_setup_missing",
                "detail": "/opt/ros/humble/setup.bash not found; cannot run ros2 topic or driver smoke",
            }
        )
    # pyserial 缺失时 Python driver 无法打开 LiDAR 串口，必须先补依赖。
    if not pyserial_available:
        blockers.append(
            {
                "code": "pyserial_missing",
                "detail": "python module 'serial' is unavailable; install pyserial before driver smoke",
            }
        )
    # 没有 repo/workspace 时无法 source install 或运行项目 driver。
    if repo_root is None:
        blockers.append(
            {
                "code": "workspace_not_found",
                "detail": "rober checkout with onboard/ was not detected from probe cwd or script path",
            }
        )
    # 没有候选路径时不能盲开 /dev/ttyUSB0，避免打开错误设备。
    if not lidar_candidates:
        blockers.append(
            {
                "code": "lidar_serial_candidate_missing",
                "detail": "no /dev/lidar, STC by-id, or ttyACM candidate was listed by the read-only probe",
            }
        )

    candidate_port = lidar_candidates[0] if lidar_candidates else "<lidar_serial_port>"
    workspace = str(repo_root / "onboard") if repo_root else "<rober>/onboard"
    return {
        "status": "ready_for_no_motion_lidar_smoke" if not blockers else "blocked_by_readiness",
        # 该 smoke 只允许触发 LiDAR 电机/串口读取，不允许触碰 WAVE ROVER 底盘控制。
        "sends_base_motion_commands": False,
        "sends_cmd_vel": False,
        "writes_wave_rover_uart": False,
        "opens_lidar_serial_when_run_manually": True,
        "probe_ran_driver": False,
        "candidate_ports": lidar_candidates,
        "selected_candidate_hint": candidate_port,
        "blockers": blockers,
        "commands_if_ready": [
            "source /opt/ros/humble/setup.bash",
            f"source {workspace}/install/setup.bash",
            (
                "ros2 run ros2_trashbot_hardware lidar_driver --ros-args "
                f"-p serial_port:={candidate_port} -p serial_baudrate:=150000 "
                "-p frame_id:=laser_frame -p publish_raw_packets:=true"
            ),
            "timeout 10 ros2 topic echo --once /scan",
            "timeout 10 ros2 topic echo --once /lidar/raw_packet",
        ],
    }


def build_probe_payload(
    globber: Callable[[str], Iterable[str]] = glob.glob,
    now: datetime | None = None,
    cwd: Path | None = None,
    argv: list[str] | None = None,
    command_runner: Callable[[str, float], dict] = _safe_run,
) -> dict:
    """构造一次性 JSON 快照；函数保持可注入，方便单元测试覆盖 contract。"""
    current_time = now or datetime.now(timezone.utc)
    current_cwd = cwd or Path.cwd()
    # stdin 远端运行时 __file__ 会是 <stdin>，因此 repo hint 必须允许降级。
    script_path = Path(__file__).resolve() if "__file__" in globals() else current_cwd
    repo_root = _find_repo_root(script_path.parent) or _find_repo_root(current_cwd)
    onboard_path = repo_root / "onboard" if repo_root else current_cwd / "onboard"
    serial_summary = summarize_serial_candidates(globber=globber)
    pyserial_available = _is_pyserial_available()
    humble_setup_hint = _path_hint(Path(ROS_HUMBLE_SETUP))
    install_setup_hint = _path_hint(Path(ROBER_INSTALL_SETUP))

    # WAVE ROVER 控制命令只进入禁止列表，不会被发送到串口或 ROS2。
    blocked_commands = [
        # T=1 是左右轮速度命令，任何自动发送都可能导致底盘运动。
        {"command": {"T": 1}, "reason": "wheel speed command; requires HIL and explicit control run"},
        # T=13 是 ROS velocity 命令，vendor 注释要求带编码器产品才适用。
        {"command": {"T": 13}, "reason": "ROS velocity command; firmware support must be verified on chassis"},
        # T=131 会改变反馈流状态，本轮 readiness 不改变下位机状态。
        {"command": {"T": 131}, "reason": "feedback stream command; not sent by readiness probe"},
    ]

    # safe command list 只包含编译、单测和只读探测，刻意不含 move/turn/control 字样。
    next_safe_commands = [
        # 第一条命令用于重复生成同 schema 快照，便于比较环境漂移。
        "python3 onboard/scripts/o1_upper_computer_readiness_probe.py --once-json",
        # 编译检查能发现语法错误，不需要 ROS2 或真实硬件。
        "python3 -m py_compile onboard/scripts/o1_upper_computer_readiness_probe.py",
        # 单测验证 fail-closed contract，避免未来改动误放开控制字段。
        "PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_o1_upper_computer_readiness_probe.py",
        # ROS setup 只检查存在性，避免 source 后污染当前 shell 环境。
        "test -f /opt/ros/humble/setup.bash && printf ros_humble_setup_present",
        # ls 只列候选设备名；后续 HIL 才能决定是否打开其中某个设备。
        "ls -1 /dev/ttyUSB* /dev/ttyAMA* /dev/ttyACM* /dev/serial* 2>/dev/null",
    ]

    return {
        # schema/version 固定，方便云端或人工脚本稳定解析 readiness artifact。
        "schema": SCHEMA_VERSION,
        "version": 1,
        "generated_at": current_time.isoformat().replace("+00:00", "Z"),
        # source 只记录 probe 自身和参数，不记录 SSH host key、密码或 token。
        "source": {
            "probe": "o1_upper_computer_readiness_probe",
            "mode": "read_only_once",
            "argv": argv or sys.argv[1:],
        },
        # boundary 是本脚本最重要的安全 contract，任何环境下都必须 fail-closed。
        "boundary": {
            "safe_to_control": False,
            "sends_commands": False,
            "robot_control_executed": False,
            "delivery_success": False,
            # 显式声明未打开串口，避免把候选路径列表误读成串口可用证明。
            "opens_serial_devices": False,
            "writes_dev_nodes": False,
            "starts_ros2_control": False,
            "sends_cmd_vel": False,
            "raw_credentials_redacted": True,
        },
        # vendor_sources 是审查入口，不代表这些事实已经在远端机器实测通过。
        "vendor_sources": list(VENDOR_SOURCES),
        # host 只给最小 OS 画像，不输出完整 IP/MAC 列表，降低 artifact 敏感度。
        "host": {
            "hostname": platform.node(),
            "os": platform.system(),
            "os_release": platform.release(),
            "kernel": platform.version(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
        },
        # 串口只做 glob 摘要；是否是 WAVE ROVER 或 LiDAR 必须后续 HIL 证明。
        "serial_candidates": serial_summary,
        # pyserial 只检查 import spec，不 import Serial，也不触发任何设备访问。
        "pyserial": {
            "available": pyserial_available,
            "module_name": "serial",
            "opened": False,
        },
        # ROS 环境只检查 setup 文件存在性，不 source shell，也不启动节点。
        "ros_env_hints": {
            "humble_setup_bash": humble_setup_hint,
            "rober_install_setup_bash": install_setup_hint,
            "ROS_DISTRO": os.environ.get("ROS_DISTRO", ""),
        },
        # repo_hints 帮助判断远端是否已有代码 checkout；stdin 采集允许 repo_root=None。
        "repo_hints": {
            "cwd": str(current_cwd),
            "repo_root": str(repo_root) if repo_root else None,
            "onboard": _path_hint(onboard_path),
            "script_path": str(script_path),
        },
        # LiDAR 当前以 ROS2/STC vendor snapshot 为准；ROS1 snapshot 只保留协议对照价值。
        "lidar_reference_readiness": {
            "status": "software_reference_not_hil",
            "source_of_truth": "docs/vendor/lidar_pkg_ros2-main/",
            "historical_protocol_reference": "docs/vendor/lidar_ros/",
            "reference_baudrate": 150000,
            "reference_start_command_hex": "A5 60",
            "reference_stop_command_hex": "A5 00 A5 65 A5 65",
            "reference_header": "0xAA 0x55",
            "reference_config_port_name": "/dev/lidar",
            "reference_raw_topic": "/lidar/raw_packet",
            "reference_scan_topic": "/scan",
            "reference_frame_id": "laser",
            "project_frame_id_override_allowed": "laser_frame",
            "reference_udev": {"idVendor": "34bf", "idProduct": "ff0a", "symlink": "lidar"},
            "not_proven": [
                "real LiDAR USB path on this upper computer",
                # 150000 是 vendor reference，真实 USB-UART 是否稳定必须另跑。
                "150000 baud stability on target hardware",
                "ROS2 /scan output from real LiDAR",
                "TF/Nav2/SLAM consumption with real sensor data",
            ],
        },
        # 该字段把“能不能试 /scan”变成机器可读 gate，避免 SSH/ROS 缺口只停留在口头报告。
        "lidar_runtime_readiness": build_lidar_runtime_readiness(
            serial_summary=serial_summary,
            pyserial_available=pyserial_available,
            humble_setup_exists=humble_setup_hint["exists"],
            repo_root=repo_root,
        ),
        # 新字段按 runtime/repo/install/driver/device/ready 六类输出，供 20 分钟内本地判断下一步。
        "lidar_ros2_bootstrap": build_lidar_ros2_bootstrap_readiness(
            repo_root=repo_root,
            onboard_path=onboard_path,
            humble_setup_exists=humble_setup_hint["exists"],
            install_setup_exists=install_setup_hint["exists"],
            serial_summary=serial_summary,
            command_runner=command_runner,
        ),
        "ros2_runtime_remediation_plan": build_ros2_runtime_remediation_plan(
            repo_root=repo_root,
            onboard_path=onboard_path,
            humble_setup_exists=humble_setup_hint["exists"],
            install_setup_exists=install_setup_hint["exists"],
            lidar_candidates=_lidar_candidate_paths(serial_summary),
            command_runner=command_runner,
        ),
        # WAVE ROVER readiness 刻意保持 not_ready_for_control，避免被 launch 默认误用。
        "wave_rover_readiness": {
            "status": "not_ready_for_control",
            "uart_json_reference": "UTF-8 newline-delimited JSON",
            # Raspberry Pi reference 只能作为 vendor 样例，不能当 Orange Pi 实测路径。
            "vendor_raspberry_pi_reference": {"serial_port": "/dev/ttyAMA0", "baudrate": 115200},
            "orange_pi_serial_status": "candidate_paths_listed_only_not_confirmed",
            "blocked_commands_not_sent": blocked_commands,
            "hil_readiness_blockers": [
                "real WAVE ROVER UART device path not confirmed in this probe",
                # pyserial 缺失或存在都不是 HIL 证据，因为 probe 不打开串口。
                "pyserial open/read/write intentionally not attempted",
                "T=1001 feedback packet not captured from real chassis",
                "T=13 ROS velocity behavior not confirmed on loaded firmware",
                "IMU/battery/odom calibration and units not validated on target",
            ],
        },
        # 下一步命令保持安全，只允许重复采集、编译和单测，不包含运动或控制词。
        "next_safe_commands": next_safe_commands,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    # --once-json 显式表达一次性快照；默认也输出 JSON 以兼容 stdin 远端运行。
    parser.add_argument("--once-json", action="store_true", help="print one read-only JSON snapshot")
    # --output 只写调用方指定路径；脚本自身不选择仓库内 artifact 位置。
    parser.add_argument("--output", help="write the same sanitized JSON snapshot to this path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    # payload 只允许执行本地只读命令；不启动 ROS2 driver、不打开串口、不发布控制 topic。
    payload = build_probe_payload(argv=sys.argv[1:] if argv is None else argv)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)

    # --once-json 和默认行为都只输出 JSON，方便 SSH stdin 方式无依赖运行。
    if args.once_json or not args.output:
        print(text)
    if args.output:
        output_path = Path(args.output)
        # 创建父目录只影响用户指定 artifact 路径，不触碰 /dev 或 ROS runtime。
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
