#!/usr/bin/env python3
"""只读识别 WAVE ROVER 候选端口身份，默认 fail-closed。"""

from __future__ import annotations

import argparse
import glob
import json
import os
import platform
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable


# schema 固定后，automation 可以不解析 prose，直接消费机器字段。
SCHEMA_VERSION = "trashbot.o1.wave_rover_port_identity_probe.v1"
# 本 probe 只列串口候选路径；不枚举网络、摄像头或其他敏感设备。
DEVICE_PATTERNS = (
    "/dev/serial/by-id/*",
    "/dev/serial/by-path/*",
    "/dev/ttyACM*",
    "/dev/ttyUSB*",
    "/dev/lidar",
)
# vendor source 写入 JSON，确保现场判断能回到本地资料而不是靠记忆。
VENDOR_SOURCES = (
    "AGENTS.md",
    "OKR.md",
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
    "docs/vendor/lidar_pkg_ros2-main/README.md",
    "docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules",
)
# LiDAR vendor udev 规则来自 docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules。
LIDAR_VENDOR_PRODUCT = ("34bf", "ff0a")
# 这些文字只能作为风险线索，不能单独升级成硬件定论。
STC_MARKERS = ("stc", "ttyacm")
LIDAR_MARKERS = ("lidar", "laser")
WAVE_ROVER_HINT_MARKERS = ("wave_rover", "wave rover", "waveshare", "esp32", "cp210", "ch340")

# 安全边界说明：端口身份 readiness 不能打开串口，因为 open 本身会占用现场设备。
# 安全边界说明：本脚本不导入 pyserial，避免后续误把 Serial 构造器接进来。
# 安全边界说明：T=130 也不允许发送，因为本轮目标是身份识别而不是反馈请求。
# 安全边界说明：T=131 会改变下位机 feedback flow 状态，身份 probe 必须禁止。
# 安全边界说明：T=1/T=13/cmd_vel 都属于运动路径，必须只出现在 blocked 列表。
# 安全边界说明：readlink 只解析 symlink 文本，不会读取 tty 设备内容。
# 安全边界说明：stat 只看元数据，不代表串口可打开或协议可用。
# 安全边界说明：sysfs 文本只能作为线索，不能替代物理追线。
# 安全边界说明：STC 是风险线索，不是 WAVE ROVER ESP32 的充分证据。
# 安全边界说明：ttyACM 也是风险线索，因为 LiDAR 参考同样可能使用 ttyACM。
# 安全边界说明：/dev/lidar 命中时要优先怀疑错口，不能继续默认当底盘。
# 安全边界说明：possible_wave_rover_esp32 也只是可能，不是 proven。
# 安全边界说明：identity_insufficient 是正常结果，不应让 automation 失败崩溃。
# 安全边界说明：port_missing 只能提示恢复连接，不能自动 fallback 到其他端口。
# 安全边界说明：candidate inventory 用于人工对比插拔，不用于自动控制。
# 安全边界说明：by-path 稳定性也要现场确认，USB hub 拓扑变化会改变它。
# 安全边界说明：vendor_sources 是证据入口，不表示这些事实已在目标机实测。
# 安全边界说明：输出 host 只保留最小画像，不采集网络凭证或密钥。
# 安全边界说明：JSON schema 固定后，PC/automation 可直接路由风险工单。
# 安全边界说明：异常分支也必须输出 fail-closed 字段，避免审计漏判。
# 安全边界说明：本脚本不证明 T=1001，不证明 HIL，不证明 delivery success。
# 安全边界说明：真实 HIL 必须另跑 feedback probe 和现场低速测试。
# 分类说明：LiDAR vendor/product 只提高错口风险置信度，不证明雷达已可用。
# 分类说明：ESP32/Waveshare 文本只给低置信身份线索，仍需插拔和追线。
# 分类说明：多个 symlink 指向同一 realpath 是有用线索，但不是身份定论。
# 分类说明：没有 sysfs 文本时保持信息不足，比猜测硬件身份更安全。
# 分类说明：next_required_checks 保持稳定字符串，便于现场 SOP 复用。
# 分类说明：blocked_commands_not_sent 明确列 T=130，是为了区别 serial feedback probe。
# 分类说明：readonly_actions 明确列动作白名单，便于 diff review 发现越界。
# 分类说明：forbidden_actions 明确列禁止动作，便于自动验收 fail-closed。
# 分类说明：CLI 即使没有 --once-json 也只输出一次，避免长期占用会话。
# 分类说明：fake inspector 单测覆盖所有文件系统读取，不需要真实硬件。
# 分类说明：所有路径处理都用字符串和 Path，不解析 Orange Pi 引脚或电压。
# 分类说明：端口身份风险关闭后，O1 百分比仍不能因本脚本提升。
# 分类说明：如果远端 SSH 不可达，本地 probe/测试/文档仍是本轮交付。


class ReadOnlyDeviceInspector:
    """把文件系统操作集中封装，便于单测注入 fake /dev 和 fake sysfs。"""

    def glob(self, pattern: str) -> list[str]:
        """glob 只返回路径名，不打开字符设备。"""
        return sorted(glob.glob(pattern))

    def lexists(self, path: str) -> bool:
        """lexists 能看见坏 symlink，便于报告 by-id 漂移。"""
        return os.path.lexists(path)

    def exists(self, path: str) -> bool:
        """exists 只检查路径存在，不读取设备内容。"""
        return os.path.exists(path)

    def islink(self, path: str) -> bool:
        """symlink 信息用于暴露 by-id/by-path 到 ttyACM/ttyUSB 的关系。"""
        return os.path.islink(path)

    def realpath(self, path: str) -> str:
        """realpath 不打开目标设备，只解析路径。"""
        return os.path.realpath(path)

    def stat(self, path: str) -> os.stat_result:
        """stat 只读元数据；不调用 open/read/write 串口。"""
        return os.stat(path)

    def readlink(self, path: str) -> str:
        """readlink 只读 symlink 文本，避免误触 /dev 节点。"""
        return os.readlink(path)

    def read_text(self, path: str, max_bytes: int = 4096) -> str:
        """只读取 sysfs 小文本；调用方负责禁止读取 /dev/*。"""
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read(max_bytes)


def _utc_now() -> str:
    """统一 UTC 时间，方便 hourly artifact 跨主机对比。"""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _base_payload(port: str, argv: list[str]) -> dict[str, Any]:
    """所有路径共享 fail-closed 字段，防止错误分支漏安全口径。"""
    return {
        "schema": SCHEMA_VERSION,
        "version": 1,
        "generated_at": _utc_now(),
        "source": {"probe": "o1_wave_rover_port_identity_probe", "mode": "read_only_once", "argv": argv},
        "vendor_sources": list(VENDOR_SOURCES),
        "evidence_boundary": "port_identity_read_only_not_hil",
        "safe_to_control": False,
        "sends_commands": False,
        "opens_serial_devices": False,
        "robot_control_executed": False,
        "delivery_success": False,
        "blocked_commands_not_sent": [
            {"command": {"T": 130}, "reason": "feedback request is not part of no-motion identity readiness"},
            {"command": {"T": 131}, "reason": "feedback flow state change is forbidden in identity readiness"},
            {"command": {"T": 1}, "reason": "wheel speed command is forbidden in identity readiness"},
            {"command": {"T": 13}, "reason": "ROS velocity command is forbidden in identity readiness"},
            {"command": "cmd_vel", "reason": "ROS motion path is outside this no-motion probe"},
        ],
        "host": {
            "hostname": platform.node(),
            "os": platform.system(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
        },
        "target_port": port,
    }


def _safe_stat(path: str, inspector: ReadOnlyDeviceInspector) -> dict[str, Any]:
    """返回设备元数据；异常转 JSON，避免现场坏 symlink 中断 probe。"""
    entry: dict[str, Any] = {
        "path": path,
        "lexists": False,
        "exists": False,
        "is_symlink": False,
        "symlink_target": None,
        "realpath": None,
        "realpath_exists": False,
        "is_character_device": False,
        "mode_octal": None,
        "uid": None,
        "gid": None,
        "error": None,
    }
    try:
        entry["lexists"] = inspector.lexists(path)
        entry["exists"] = inspector.exists(path)
        entry["is_symlink"] = inspector.islink(path)
        if entry["is_symlink"]:
            entry["symlink_target"] = inspector.readlink(path)
        if entry["lexists"]:
            realpath = inspector.realpath(path)
            entry["realpath"] = realpath
            entry["realpath_exists"] = inspector.exists(realpath)
            stat_result = inspector.stat(path)
            entry["is_character_device"] = stat.S_ISCHR(stat_result.st_mode)
            entry["mode_octal"] = oct(stat_result.st_mode & 0o7777)
            entry["uid"] = stat_result.st_uid
            entry["gid"] = stat_result.st_gid
    except Exception as exc:
        entry["error"] = {"type": exc.__class__.__name__, "message": str(exc)}
    return entry


def _tty_name_from_realpath(path: str | None) -> str | None:
    """从 /dev/ttyACM0 这类 realpath 提取 tty 名，不猜 Orange Pi 物理口。"""
    if not path:
        return None
    name = Path(path).name
    if name.startswith("tty"):
        return name
    return None


def _read_sysfs_chain(tty_name: str | None, inspector: ReadOnlyDeviceInspector) -> dict[str, Any]:
    """只读取 tty 对应 sysfs 文本，避免打开 /dev 串口。"""
    if not tty_name:
        return {"tty_name": None, "status": "no_tty_realpath", "nodes": []}

    base = Path("/sys/class/tty") / tty_name / "device"
    nodes: list[dict[str, Any]] = []
    # USB 属性可能挂在 tty device 的父级，最多向上 5 层即可覆盖常见拓扑。
    for depth in range(0, 6):
        node_path = base if depth == 0 else base.joinpath(*([".."] * depth))
        node: dict[str, Any] = {"path": str(node_path), "depth": depth, "attributes": {}, "uevent": None, "error": None}
        try:
            for attr in ("idVendor", "idProduct", "manufacturer", "product", "serial", "interface"):
                attr_path = str(node_path / attr)
                if inspector.exists(attr_path):
                    node["attributes"][attr] = inspector.read_text(attr_path).strip()
            uevent_path = str(node_path / "uevent")
            if inspector.exists(uevent_path):
                node["uevent"] = inspector.read_text(uevent_path).strip()
        except Exception as exc:
            node["error"] = {"type": exc.__class__.__name__, "message": str(exc)}
        if node["attributes"] or node["uevent"] or node["error"]:
            nodes.append(node)
    return {"tty_name": tty_name, "status": "read_sysfs_text_only", "nodes": nodes}


def _collect_candidates(
    target_port: str,
    inspector: ReadOnlyDeviceInspector,
    patterns: Iterable[str] = DEVICE_PATTERNS,
) -> dict[str, Any]:
    """枚举目标端口和候选 symlink，帮助现场识别错口风险。"""
    paths: set[str] = {target_port}
    by_pattern: dict[str, Any] = {}
    for pattern in patterns:
        try:
            matches = inspector.glob(pattern)
            by_pattern[pattern] = {"count": len(matches), "paths": matches}
            paths.update(matches)
        except Exception as exc:
            by_pattern[pattern] = {"count": 0, "paths": [], "error": {"type": exc.__class__.__name__, "message": str(exc)}}
    described = [_safe_stat(path, inspector) for path in sorted(paths)]
    target_realpath = inspector.realpath(target_port) if inspector.lexists(target_port) else None
    related = [
        item
        for item in described
        if item.get("path") == target_port or (target_realpath and item.get("realpath") == target_realpath)
    ]
    return {"patterns": list(patterns), "by_pattern": by_pattern, "all": described, "related_to_target_realpath": related}


def _text_blob(*items: Any) -> str:
    """把路径、by-id、sysfs 属性合成小写文本，只用于保守分类。"""
    chunks: list[str] = []
    for item in items:
        chunks.append(json.dumps(item, ensure_ascii=False, sort_keys=True).lower())
    return "\n".join(chunks)


def _sysfs_vendor_product(sysfs: dict[str, Any]) -> set[tuple[str, str]]:
    """提取 USB vendor/product 组合，用于识别 LiDAR udev 规则线索。"""
    pairs: set[tuple[str, str]] = set()
    for node in sysfs.get("nodes", []):
        attrs = node.get("attributes", {})
        vendor = str(attrs.get("idVendor", "")).lower()
        product = str(attrs.get("idProduct", "")).lower()
        if vendor and product:
            pairs.add((vendor, product))
    return pairs


def classify_identity(target: dict[str, Any], candidates: dict[str, Any], sysfs: dict[str, Any]) -> dict[str, Any]:
    """保守分类端口身份；输出可能性，不输出硬件定论。"""
    risks: list[str] = []
    evidence: list[str] = []
    next_checks: list[str] = []
    text = _text_blob(target, candidates.get("related_to_target_realpath", []), sysfs)

    if not target.get("lexists"):
        return {
            "status": "port_missing",
            "possible_role": "port_absent",
            "confidence": "none",
            "risk_flags": ["target_port_missing"],
            "evidence": ["target port path does not exist or broken symlink was not present"],
            "next_required_checks": [
                "confirm_upper_computer_usb_connection",
                "rerun_read_only_port_identity_probe_after_replug",
                "compare /dev/serial/by-id and /dev/serial/by-path inventories",
            ],
        }

    if any(marker in text for marker in STC_MARKERS):
        risks.append("stc_or_ttyacm_is_not_unique")
        evidence.append("STC/ttyACM clue observed; vendor LiDAR reference also uses ttyUSB/ttyACM discovery")
    if LIDAR_VENDOR_PRODUCT in _sysfs_vendor_product(sysfs) or any(marker in text for marker in LIDAR_MARKERS):
        risks.append("lidar_clue_present")
        evidence.append("LiDAR clue observed from path/sysfs/vendor udev reference")
    if any(marker in text for marker in WAVE_ROVER_HINT_MARKERS):
        evidence.append("ESP32/Waveshare-style text clue observed in path or sysfs")
    if target.get("is_symlink"):
        evidence.append("target is a symlink; realpath must remain stable across replug")
    if target.get("is_character_device"):
        evidence.append("target resolves to a character device; this is metadata only, not serial-open proof")

    next_checks.extend(
        [
            "physically trace USB/UART cable from target port to WAVE ROVER ESP32",
            "compare by-id/by-path before and after unplugging LiDAR and base controller separately",
            "check whether /dev/lidar or LiDAR udev vendor/product points to the same realpath",
            "only after identity is confirmed, run explicit serial feedback probe or vendor terminal T=130",
        ]
    )

    if "lidar_clue_present" in risks:
        status = "possible_lidar_or_other_stc"
        possible_role = "possible_lidar_or_other_stc_not_wave_rover_proven"
        confidence = "medium_for_risk_only"
    elif any("ESP32/Waveshare-style" in item for item in evidence) and "stc_or_ttyacm_is_not_unique" not in risks:
        status = "possible_wave_rover_esp32"
        possible_role = "possible_wave_rover_esp32_not_proven"
        confidence = "low"
    else:
        status = "identity_insufficient"
        possible_role = "unknown_serial_device"
        confidence = "insufficient"
        if not risks:
            risks.append("no_distinctive_usb_identity_clue")

    return {
        "status": status,
        "possible_role": possible_role,
        "confidence": confidence,
        "risk_flags": risks,
        "evidence": evidence or ["target exists but no distinctive identity text was available"],
        "next_required_checks": next_checks,
    }


def build_probe_payload(
    port: str,
    argv: list[str] | None = None,
    inspector: ReadOnlyDeviceInspector | None = None,
) -> dict[str, Any]:
    """构造一次 probe JSON；不打开串口，也不发送任何命令。"""
    device_inspector = inspector or ReadOnlyDeviceInspector()
    payload = _base_payload(port, argv or [])
    target = _safe_stat(port, device_inspector)
    tty_name = _tty_name_from_realpath(target.get("realpath"))
    sysfs = _read_sysfs_chain(tty_name, device_inspector)
    candidates = _collect_candidates(port, device_inspector)
    classification = classify_identity(target, candidates, sysfs)
    payload.update(
        {
            "readonly_actions": ["glob", "readlink", "stat", "sysfs_text_read"],
            "forbidden_actions": ["open_serial_device", "write_serial_device", "send_T130", "send_T131", "send_T1", "send_T13", "send_cmd_vel"],
            "target": target,
            "sysfs_usb_tty_description": sysfs,
            "serial_candidates": candidates,
            "identity_assessment": classification,
        }
    )
    return payload


def _parse_args(argv: list[str]) -> argparse.Namespace:
    """CLI 保持一次性 JSON 输出，方便 SSH stdin 执行。"""
    parser = argparse.ArgumentParser(description="Read-only WAVE ROVER port identity readiness probe")
    parser.add_argument("--once-json", action="store_true", help="emit one JSON payload and exit")
    parser.add_argument("--port", default="/dev/serial/by-id/usb-STC_STC_USB_Serial-if00", help="target serial path to inspect without opening it")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """入口只输出 JSON；即使用户忘记 --once-json 也不进入循环。"""
    actual_argv = list(sys.argv[1:] if argv is None else argv)
    args = _parse_args(actual_argv)
    payload = build_probe_payload(args.port, argv=actual_argv)
    indent = 2 if args.pretty else None
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
