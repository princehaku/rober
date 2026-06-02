#!/usr/bin/env python3
"""只读枚举 USB/串口 inventory，帮助现场区分 LiDAR 与底盘控制器。"""

from __future__ import annotations

import argparse
import glob
import json
import os
import platform
import stat
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


# schema 固定后，PC/automation 可以直接消费 inventory 和风险字段。
SCHEMA_VERSION = "trashbot.o1.usb_serial_inventory.v1"
# 这些路径只做 glob/readlink/stat，不打开字符设备，也不读取串口内容。
DEVICE_PATTERNS = (
    "/dev/ttyUSB*",
    "/dev/ttyACM*",
    "/dev/serial/by-id/*",
    "/dev/serial/by-path/*",
    "/dev/lidar",
)
# vendor_sources 写进 payload，避免现场报告变成“凭记忆判断 STC”。
VENDOR_SOURCES = (
    "AGENTS.md",
    "OKR.md",
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules",
    "docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml",
    "docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp",
)
# LiDAR udev 规则明确把 STC 34bf:ff0a 映射为 /dev/lidar。
LIDAR_VENDOR_PRODUCT = ("34bf", "ff0a")
# STC/ttyACM 只能是身份风险线索，不能证明 WAVE ROVER ESP32。
STC_MARKERS = ("stc", "34bf", "ff0a", "ttyacm")
# Waveshare/ESP32 文本出现时也只给候选提示，仍需插拔和追线确认。
BASE_CONTROLLER_MARKERS = ("wave_rover", "wave rover", "waveshare", "esp32", "ch340", "cp210", "cp210x")

# 安全边界说明：inventory probe 不 import pyserial，避免误接 Serial open。
# 安全边界说明：glob 只枚举路径名，不会触发串口协议或设备动作。
# 安全边界说明：readlink 只读 symlink 文本，不读取 /dev/tty* 内容。
# 安全边界说明：stat 只读取 inode 元数据，不代表设备可打开或可控。
# 安全边界说明：sysfs 文本读取只发生在 /sys/class/tty 上游小文件。
# 安全边界说明：/dev/lidar 命中时优先暴露错口风险，而不是继续控制。
# 安全边界说明：STC vendor/product 与 LiDAR udev 一致时必须 fail-closed。
# 安全边界说明：多个 alias 同 realpath 是现场插拔对比材料，不是身份定论。
# 安全边界说明：推荐检查项用稳定字符串，方便现场按步骤复跑。
# 安全边界说明：本脚本不发送 T=130，因为本轮目标不是请求反馈。
# 安全边界说明：本脚本不发送 T=131，因为 feedback flow 会改变下位机状态。
# 安全边界说明：本脚本不发送 T=1/T=13/cmd_vel，因为它们属于运动路径。
# 安全边界说明：本脚本不证明 T=1001、HIL、真实 /odom 或 delivery success。
# 安全边界说明：远端 SSH 只运行本脚本时，也不应打开任何串口设备。
# 安全边界说明：异常分支仍输出安全 false 字段，避免审计漏判。
# 安全边界说明：没有 LiDAR alias 不等于没有 LiDAR，只能提示继续物理对比。
# 安全边界说明：没有 by-id 不等于设备不可用，只说明 udev 身份不足。
# 安全边界说明：by-path 稳定性受 USB 拓扑影响，必须结合插拔记录判断。
# 安全边界说明：vendor_sources 是证据入口，不代表本轮完成真实 HIL。
# 安全边界说明：hostname 只用于区分 artifact，不采集凭证或网络配置。


class ReadOnlyInventoryInspector:
    """集中封装只读文件系统操作，便于单测替换 fake /dev 和 fake sysfs。"""

    def glob(self, pattern: str) -> list[str]:
        """glob 只返回路径名；不会打开字符设备。"""
        return sorted(glob.glob(pattern))

    def lexists(self, path: str) -> bool:
        """lexists 能报告坏 symlink，便于发现 udev 漂移。"""
        return os.path.lexists(path)

    def exists(self, path: str) -> bool:
        """exists 只看路径存在性，不读取串口内容。"""
        return os.path.exists(path)

    def islink(self, path: str) -> bool:
        """islink 用于记录 by-id/by-path alias 关系。"""
        return os.path.islink(path)

    def readlink(self, path: str) -> str:
        """readlink 只读 symlink 文本，避免触碰目标设备。"""
        return os.readlink(path)

    def realpath(self, path: str) -> str:
        """realpath 只解析路径，帮助把 alias 聚合到同一 tty。"""
        return os.path.realpath(path)

    def stat(self, path: str) -> os.stat_result:
        """stat 只读元数据；不做串口 open/read/write。"""
        return os.stat(path)

    def read_text(self, path: str, max_bytes: int = 4096) -> str:
        """只允许调用方传入 sysfs 小文本路径。"""
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read(max_bytes)


def _utc_now() -> str:
    """统一 UTC 时间，便于现场多次插拔 artifact 对齐。"""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _base_payload(argv: list[str]) -> dict[str, Any]:
    """所有输出路径共享 fail-closed 字段，防止异常分支漏安全口径。"""
    return {
        "schema": SCHEMA_VERSION,
        "version": 1,
        "generated_at": _utc_now(),
        "source": {"probe": "o1_usb_serial_inventory_probe", "mode": "read_only_once", "argv": argv},
        "vendor_sources": list(VENDOR_SOURCES),
        "evidence_boundary": "usb_serial_inventory_read_only_not_hil",
        "safe_to_control": False,
        "sends_commands": False,
        "opens_serial_devices": False,
        "robot_control_executed": False,
        "delivery_success": False,
        "readonly_actions": ["glob", "readlink", "stat", "sysfs_text_read"],
        "forbidden_actions": [
            "import_pyserial",
            "open_serial_device",
            "read_serial_device",
            "write_serial_device",
            "send_T130",
            "send_T131",
            "send_T1",
            "send_T13",
            "send_cmd_vel",
        ],
        "blocked_commands_not_sent": [
            {"command": {"T": 130}, "reason": "feedback request is outside no-motion inventory"},
            {"command": {"T": 131}, "reason": "feedback flow state change is forbidden"},
            {"command": {"T": 1}, "reason": "wheel speed command is forbidden"},
            {"command": {"T": 13}, "reason": "ROS velocity command is forbidden"},
            {"command": "cmd_vel", "reason": "ROS motion path is outside this inventory"},
        ],
        "host": {
            "hostname": platform.node(),
            "os": platform.system(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
        },
    }


def _alias_kind(path: str) -> str:
    """把候选路径归类，方便现场先看 by-id/by-path/lidar/tty。"""
    if path.startswith("/dev/serial/by-id/"):
        return "by_id"
    if path.startswith("/dev/serial/by-path/"):
        return "by_path"
    if path == "/dev/lidar":
        return "lidar_alias"
    if path.startswith("/dev/ttyACM"):
        return "tty_acm"
    if path.startswith("/dev/ttyUSB"):
        return "tty_usb"
    return "other"


def _tty_name_from_realpath(path: str | None) -> str | None:
    """只从 /dev/tty* 路径提取 tty 名，不猜 USB 物理身份。"""
    if not path:
        return None
    name = Path(path).name
    if name.startswith("tty"):
        return name
    return None


def _safe_stat(path: str, inspector: ReadOnlyInventoryInspector) -> dict[str, Any]:
    """描述一个候选路径；坏 symlink 和异常都转成机器字段。"""
    entry: dict[str, Any] = {
        "path": path,
        "alias_kind": _alias_kind(path),
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


def _read_sysfs_tty(tty_name: str | None, inspector: ReadOnlyInventoryInspector) -> dict[str, Any]:
    """读取 tty 上游 sysfs USB 文本；不访问 /dev/tty* 数据流。"""
    if not tty_name:
        return {"tty_name": None, "status": "no_tty_realpath", "nodes": []}

    base = Path("/sys/class/tty") / tty_name / "device"
    nodes: list[dict[str, Any]] = []
    for depth in range(0, 6):
        # USB 属性常在 tty device 父级；向上有限层级即可覆盖常见拓扑。
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


def _collect_paths(patterns: Iterable[str], inspector: ReadOnlyInventoryInspector) -> dict[str, Any]:
    """枚举全部候选路径，并保留每个 glob pattern 的原始命中。"""
    paths: set[str] = set()
    by_pattern: dict[str, Any] = {}
    for pattern in patterns:
        try:
            matches = inspector.glob(pattern)
            by_pattern[pattern] = {"count": len(matches), "paths": matches}
            paths.update(matches)
        except Exception as exc:
            by_pattern[pattern] = {"count": 0, "paths": [], "error": {"type": exc.__class__.__name__, "message": str(exc)}}
    return {"paths": sorted(paths), "by_pattern": by_pattern}


def _sysfs_vendor_product(sysfs: dict[str, Any]) -> set[tuple[str, str]]:
    """提取 vendor/product 组合，用于匹配 LiDAR udev 线索。"""
    pairs: set[tuple[str, str]] = set()
    for node in sysfs.get("nodes", []):
        attrs = node.get("attributes", {})
        vendor = str(attrs.get("idVendor", "")).lower()
        product = str(attrs.get("idProduct", "")).lower()
        if vendor and product:
            pairs.add((vendor, product))
    return pairs


def _text_blob(*items: Any) -> str:
    """合并小写 JSON 文本，只用于保守风险分类。"""
    return "\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True).lower() for item in items)


def _summarize_inventory(entries: list[dict[str, Any]], sysfs_by_realpath: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """生成机器可读摘要，让现场快速看哪些 alias 指向同一 realpath。"""
    realpath_to_aliases: dict[str, list[str]] = defaultdict(list)
    alias_counts: dict[str, int] = defaultdict(int)
    tty_realpaths: list[str] = []
    stc_realpaths: list[str] = []
    lidar_alias_realpaths: list[str] = []

    for entry in entries:
        alias_counts[entry["alias_kind"]] += 1
        realpath = entry.get("realpath")
        if realpath:
            realpath_to_aliases[realpath].append(entry["path"])
            if Path(realpath).name.startswith("tty"):
                tty_realpaths.append(realpath)
        if entry["alias_kind"] == "lidar_alias" and realpath:
            lidar_alias_realpaths.append(realpath)

    for realpath, sysfs in sysfs_by_realpath.items():
        text = _text_blob(realpath, sysfs, realpath_to_aliases.get(realpath, []))
        if any(marker in text for marker in STC_MARKERS):
            stc_realpaths.append(realpath)

    return {
        "total_candidate_paths": len(entries),
        "alias_counts": dict(sorted(alias_counts.items())),
        "tty_realpaths": sorted(set(tty_realpaths)),
        "realpath_to_aliases": {key: sorted(value) for key, value in sorted(realpath_to_aliases.items())},
        "stc_or_ttyacm_realpaths": sorted(set(stc_realpaths)),
        "lidar_alias_realpaths": sorted(set(lidar_alias_realpaths)),
        "candidate_realpath_count": len(realpath_to_aliases),
    }


def _build_identity_risks(
    entries: list[dict[str, Any]],
    sysfs_by_realpath: dict[str, dict[str, Any]],
    summary: dict[str, Any],
) -> list[dict[str, Any]]:
    """把错口风险机器化输出；风险字段不等于硬件身份结论。"""
    risks: list[dict[str, Any]] = []
    for realpath, sysfs in sorted(sysfs_by_realpath.items()):
        aliases = summary["realpath_to_aliases"].get(realpath, [])
        text = _text_blob(realpath, aliases, sysfs)
        vendor_products = sorted(_sysfs_vendor_product(sysfs))
        if LIDAR_VENDOR_PRODUCT in vendor_products or "/dev/lidar" in aliases or "lidar" in text or "laser" in text:
            risks.append(
                {
                    "risk_id": "possible_lidar_or_other_stc",
                    "severity": "high",
                    "affected_realpath": realpath,
                    "evidence": {
                        "aliases": aliases,
                        "usb_vendor_products": vendor_products,
                        "reason": "LiDAR alias/text or vendor udev 34bf:ff0a clue observed",
                    },
                    "recommended_check": "unplug_lidar_then_rerun_inventory_and_compare_changed_aliases",
                }
            )
        elif any(marker in text for marker in STC_MARKERS):
            risks.append(
                {
                    "risk_id": "stc_or_ttyacm_is_not_unique",
                    "severity": "medium",
                    "affected_realpath": realpath,
                    "evidence": {"aliases": aliases, "usb_vendor_products": vendor_products},
                    "recommended_check": "unplug_lidar_and_base_controller_separately_then_compare_by_id_by_path",
                }
            )
        elif any(marker in text for marker in BASE_CONTROLLER_MARKERS):
            risks.append(
                {
                    "risk_id": "possible_base_controller_not_proven",
                    "severity": "low",
                    "affected_realpath": realpath,
                    "evidence": {"aliases": aliases, "reason": "ESP32/Waveshare-style text clue observed"},
                    "recommended_check": "physically_trace_cable_to_wave_rover_esp32_before_feedback_probe",
                }
            )

    if not entries:
        risks.append(
            {
                "risk_id": "no_serial_candidates_visible",
                "severity": "high",
                "affected_realpath": None,
                "evidence": {"patterns": list(DEVICE_PATTERNS)},
                "recommended_check": "confirm_usb_devices_are_plugged_and_rerun_inventory",
            }
        )
    return risks


def _recommended_physical_checks() -> list[dict[str, str]]:
    """输出稳定现场 SOP，强调分别插拔而不是继续盲发 T=130。"""
    return [
        {
            "check_id": "baseline_inventory",
            "action": "run this inventory once with all current devices connected and save the JSON",
            "expected_observation": "record current ttyUSB/ttyACM/by-id/by-path/lidar aliases and realpaths",
        },
        {
            "check_id": "unplug_lidar_only",
            "action": "power-safe unplug LiDAR USB only, rerun inventory, then compare changed aliases and realpaths",
            "expected_observation": "the LiDAR alias or STC 34bf:ff0a realpath should disappear or change",
        },
        {
            "check_id": "replug_lidar_unplug_base_controller_only",
            "action": "restore LiDAR, unplug WAVE ROVER ESP32/base controller USB/UART adapter only, rerun inventory",
            "expected_observation": "base-controller candidate aliases should disappear while /dev/lidar should remain",
        },
        {
            "check_id": "trace_cables_before_feedback_probe",
            "action": "physically trace the selected realpath cable to the WAVE ROVER ESP32 before any feedback probe",
            "expected_observation": "only confirmed base-controller port may be used for explicit T=130 feedback probe",
        },
    ]


def build_inventory_payload(
    argv: list[str] | None = None,
    inspector: ReadOnlyInventoryInspector | None = None,
    patterns: Iterable[str] = DEVICE_PATTERNS,
) -> dict[str, Any]:
    """构造一次 inventory JSON；全程不打开串口、不发送命令。"""
    device_inspector = inspector or ReadOnlyInventoryInspector()
    payload = _base_payload(argv or [])
    collected = _collect_paths(patterns, device_inspector)
    entries = [_safe_stat(path, device_inspector) for path in collected["paths"]]

    sysfs_by_realpath: dict[str, dict[str, Any]] = {}
    for entry in entries:
        realpath = entry.get("realpath")
        tty_name = _tty_name_from_realpath(realpath)
        if realpath and tty_name and realpath not in sysfs_by_realpath:
            sysfs_by_realpath[realpath] = _read_sysfs_tty(tty_name, device_inspector)

    summary = _summarize_inventory(entries, sysfs_by_realpath)
    payload.update(
        {
            "scan_patterns": list(patterns),
            "glob_results": collected["by_pattern"],
            "serial_devices": entries,
            "sysfs_usb_tty_descriptions_by_realpath": sysfs_by_realpath,
            "inventory_summary": summary,
            "identity_risks": _build_identity_risks(entries, sysfs_by_realpath, summary),
            "recommended_physical_checks": _recommended_physical_checks(),
        }
    )
    return payload


def _parse_args(argv: list[str]) -> argparse.Namespace:
    """CLI 保持一次性 JSON 输出，适配 ssh 'python3 -s - --once-json'。"""
    parser = argparse.ArgumentParser(description="Read-only USB/serial inventory probe for O1")
    parser.add_argument("--once-json", action="store_true", help="emit one JSON payload and exit")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """入口即使没有 --once-json 也只跑一次，避免长期占用现场会话。"""
    actual_argv = list(sys.argv[1:] if argv is None else argv)
    args = _parse_args(actual_argv)
    payload = build_inventory_payload(argv=actual_argv)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
