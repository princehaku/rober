#!/usr/bin/env python3
"""只读采集 O1 上位机 readiness 快照，默认 fail-closed。"""

from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable


# 版本号不从 git 读取，因为远端 stdin 运行时可能没有仓库。
SCHEMA_VERSION = "trashbot.o1.upper_computer_readiness.v1"
# 串口候选只允许来自这些 glob，避免把网卡、蓝牙或其他敏感设备暴露进 artifact。
SERIAL_CANDIDATE_PATTERNS = (
    "/dev/ttyUSB*",
    "/dev/ttyAMA*",
    "/dev/ttyACM*",
    "/dev/serial*",
    "/dev/serial/by-id/*",
    "/dev/serial/by-path/*",
)
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
    for candidate in [start, *start.parents]:
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


def build_probe_payload(
    globber: Callable[[str], Iterable[str]] = glob.glob,
    now: datetime | None = None,
    cwd: Path | None = None,
    argv: list[str] | None = None,
) -> dict:
    """构造一次性 JSON 快照；函数保持可注入，方便单元测试覆盖 contract。"""
    current_time = now or datetime.now(timezone.utc)
    current_cwd = cwd or Path.cwd()
    # stdin 远端运行时 __file__ 会是 <stdin>，因此 repo hint 必须允许降级。
    script_path = Path(__file__).resolve() if "__file__" in globals() else current_cwd
    repo_root = _find_repo_root(script_path.parent) or _find_repo_root(current_cwd)
    onboard_path = repo_root / "onboard" if repo_root else current_cwd / "onboard"

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
        "serial_candidates": summarize_serial_candidates(globber=globber),
        # pyserial 只检查 import spec，不 import Serial，也不触发任何设备访问。
        "pyserial": {
            "available": _is_pyserial_available(),
            "module_name": "serial",
            "opened": False,
        },
        # ROS 环境只检查 setup 文件存在性，不 source shell，也不启动节点。
        "ros_env_hints": {
            "humble_setup_bash": _path_hint(Path("/opt/ros/humble/setup.bash")),
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
    # payload 生成阶段不执行任何外部命令，避免 SSH 上位机采集时产生副作用。
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
