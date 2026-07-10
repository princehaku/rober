#!/usr/bin/env python3
"""生成现场路线 evidence manifest。

该工具只读扫描 map、route、keyframe、rosbag 和 replay 材料，不启动导航、不发布运动命令。
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import math
import re
import shlex
import sqlite3
import subprocess
import sys
import struct
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.field_evidence_manifest.v1"
READY_PREFLIGHT_STATUS = "ready_for_live_route_capture_not_proven"
KEYFRAME_SUFFIXES = {".jpg", ".jpeg", ".png", ".json"}
ROUTE_ROOT_DIR_NAMES = {"route", "route_data"}
OPTIONAL_ROUTE_BAG_REASON = "route_bag_missing_optional_for_route_root_seed"
ROUTE_ROOT_SEED_SCHEMA = "trashbot.route_root_seed_gate.v1"
FIELD_MOTION_PACKET_SCHEMA = "trashbot.field_motion_evidence_packet.v1"
FIELD_MOTION_PACKET_PROOF_SCOPE = "software_proof_field_motion_evidence_packet_only"
O11_NAV2_GOAL_PROOF_SCHEMA = "trashbot.upper_robot_api.v1.nav2_goal_execution_proof"
NAV2_GOAL_EXECUTION_EVIDENCE_SCHEMA = "trashbot.nav2_goal_execution_evidence.v1"
NAV2_GOAL_EXECUTION_EVIDENCE_PROOF_SCOPE = "software_proof_nav2_goal_execution_evidence_only"
DELIVERY_RESULT_SOURCE_SCHEMA = "trashbot.delivery_result.v1"
DELIVERY_RESULT_EVIDENCE_SCHEMA = "trashbot.delivery_result_evidence.v1"
DELIVERY_RESULT_EVIDENCE_PROOF_SCOPE = "software_proof_delivery_result_evidence_only"
CLOUD_COMMAND_TERMINAL_RESULT_SCHEMA = "trashbot.cloud_command_terminal_result.v1"
CLOUD_COMMAND_RESULT_RECONCILIATION_SCHEMA = "trashbot.cloud_command_result_reconciliation.v2"
ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_SCHEMA = "trashbot.route_execution_result_delivery_readiness.v1"
ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_PROOF_SCOPE = "software_proof_route_execution_result_delivery_readiness_only"
ROUTE_DELIVERY_CLOSURE_PACKET_SCHEMA = "trashbot.route_delivery_closure_packet.v1"
ROUTE_DELIVERY_CLOSURE_PACKET_PROOF_SCOPE = "software_proof_route_delivery_closure_packet_only"
SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA = "trashbot.same_task_mission_evidence_gate.v1"
SAME_TASK_MISSION_EVIDENCE_GATE_PROOF_SCOPE = "software_proof_same_task_mission_evidence_gate_only"
SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA = "trashbot.same_task_field_material_packet.v1"
SAME_TASK_FIELD_MATERIAL_PACKET_PROOF_SCOPE = "software_proof_same_task_field_material_packet_only"
ROUTE_BAG_EVIDENCE_SCHEMA = "trashbot.route_bag_evidence.v1"
ROUTE_BAG_EVIDENCE_PROOF_SCOPE = "software_proof_route_bag_evidence_intake_only"
ROUTE_BAG_PAYLOAD_REPLAY_SCHEMA = "trashbot.route_bag_payload_replay.v1"
ROUTE_BAG_PAYLOAD_REPLAY_PROOF_SCOPE = "software_proof_route_bag_payload_replay_only"
ROUTE_BAG_SEMANTIC_REPLAY_SCHEMA = "trashbot.route_bag_semantic_replay.v1"
ROUTE_BAG_SEMANTIC_REPLAY_PROOF_SCOPE = "software_proof_route_bag_semantic_replay_only"
ROUTE_BAG_POSE_PROGRESS_REPLAY_SCHEMA = "trashbot.route_bag_pose_progress_replay.v1"
ROUTE_BAG_POSE_PROGRESS_REPLAY_PROOF_SCOPE = "software_proof_route_bag_pose_progress_replay_only"
ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_SCHEMA = "trashbot.route_bag_full_semantic_decode_matrix.v1"
ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_PROOF_SCOPE = "software_proof_route_bag_full_semantic_decode_matrix_only"
CONTROL_TOPIC_CMD_VEL = "/" + "cmd_vel"
ROUTE_BAG_SEMANTIC_REPLAY_TOPIC_TYPES = {
    "sensor_msgs/msg/LaserScan": "laser_scan",
    "sensor_msgs/msg/Image": "image",
    "tf2_msgs/msg/TFMessage": "tf_message",
    "nav_msgs/msg/Odometry": "odometry",
    "diagnostic_msgs/msg/DiagnosticArray": "diagnostic_array",
}
ROUTE_BAG_SEMANTIC_REPLAY_DECODE_SAMPLE_LIMIT = 8
ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_SAMPLE_LIMIT = 8
ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_DECODERS = {
    "sensor_msgs/msg/LaserScan": "decode_laserscan_payload",
    "sensor_msgs/msg/Image": "decode_image_payload",
    "tf2_msgs/msg/TFMessage": "decode_tf_message_payload",
    "nav_msgs/msg/Odometry": "decode_odometry_payload",
    "diagnostic_msgs/msg/DiagnosticArray": "decode_diagnostic_array_payload",
}
DIAGNOSTIC_ARRAY_STATUS_SAMPLE_LIMIT = 3
DIAGNOSTIC_ARRAY_MAX_STATUS_COUNT = 256
DIAGNOSTIC_ARRAY_MAX_KEY_VALUE_COUNT = 1024
DIAGNOSTIC_ARRAY_MAX_STRING_BYTES = 8192
DIAGNOSTIC_ARRAY_SAMPLE_TEXT_MAX_CHARS = 48
ROUTE_BAG_POSE_PROGRESS_REPLAY_TOPIC_TYPES = {
    "tf2_msgs/msg/TFMessage": "tf_message",
    "nav_msgs/msg/Odometry": "odom",
}
ARTIFACT_CANDIDATES = {
    "map_yaml": ["map.yaml", "map/map.yaml", "map/*.yaml", "route_data/map.yaml"],
    "map_pgm": ["map.pgm", "map/*.pgm", "route_data/map.pgm"],
    "route_csv": ["route.csv", "route/route.csv", "route_data/route.csv"],
    "source_manifest": ["manifest.json", "route/manifest.json", "route_data/manifest.json"],
    "keyframes": ["keyframes", "route/keyframes", "route_data/keyframes"],
    "rosbag": ["rosbag", "route_bag", "route_data/rosbag", "route_data/route_bag"],
    "replay_jsonl": ["replay.jsonl", "fixed_route_replay.jsonl", "route/replay.jsonl", "route/fixed_route_replay.jsonl", "route_data/fixed_route_replay.jsonl"],
}
EXISTING_MANIFEST_CANDIDATES = [
    "field_evidence_manifest.json",
    "trashbot_field_evidence_manifest.json",
    "trashbot.field_evidence_manifest.v1.json",
    "route_data/field_evidence_manifest.json",
    "route_data/trashbot_field_evidence_manifest.json",
]
UNSAFE_EXISTING_MANIFEST_FIELDS = ["delivery_success", "safe_to_control", "primary_actions_enabled"]
NAV2_GOAL_DANGEROUS_TRUE_FIELDS = {"delivery_success", "safe_to_control", "primary_actions_enabled"}
NAV2_GOAL_UNSAFE_MARKERS = ("path", "root", "token", "raw", "base64")
DELIVERY_RESULT_DANGEROUS_TRUE_FIELDS = {"delivery_success", "safe_to_control", "primary_actions_enabled", "robot_control_executed", "real_world_delivery_proven"}
DELIVERY_RESULT_UNSAFE_MARKERS = ("path", "root", "token", "raw", "base64", "credential")
CLOUD_TERMINAL_DELIVERY_TYPES = {"delivery_terminal", "dropoff_terminal"}
CLOUD_TERMINAL_COMPLETED_VALUES = {
    "completed",
    "delivered",
    "delivery_completed",
    "dropoff_completed",
    "dropoff_terminal_completed",
    "operator_confirmed_dropoff",
    "success",
    "succeeded",
    "task_terminal_completed",
    "terminal_result_recorded",
}
ROUTE_BAG_DANGEROUS_TRUE_FIELDS = {"delivery_success", "safe_to_control", "primary_actions_enabled", "robot_control_executed"}
UTC_TEXT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|\+00:00)$")
DELIVERY_RESULT_CREDENTIAL_URL_RE = re.compile(r"https?://[^/\s:@]+:[^/\s@]+@")
CLOUD_TERMINAL_URL_RE = re.compile(r"[a-z][a-z0-9+.-]*://", re.IGNORECASE)
ROUTE_BAG_CREDENTIAL_URL_RE = re.compile(r"https?://[^/\s:@]+:[^/\s@]+@")
SUMMARY_UNSAFE_CREDENTIAL_URL_RE = re.compile(r"https?://[^/\s:@]+:[^/\s@]+@")
SAME_TASK_FIELD_MATERIAL_DANGEROUS_TRUE_FIELDS = {
    "delivery_success",
    "safe_to_control",
    "primary_actions_enabled",
    "robot_control_executed",
    "route_execution_success",
}
SAME_TASK_FIELD_MATERIAL_UNSAFE_MARKERS = ("path", "root", "token", "raw", "base64", "credential", "secret")


def utc_now() -> str:
    # 统一 UTC 让本地 fixture、上位机和后续云端 archive 能按同一时间轴对齐。
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat()


def mtime_utc(timestamp: float) -> str:
    # manifest 进入审计时不依赖本机时区，避免 CST/UTC 混用造成误判。
    return _dt.datetime.fromtimestamp(timestamp, tz=_dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str:
    # 使用分块读取，现场 rosbag 可能较大，避免一次性读入内存。
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(path: Path) -> list[Path]:
    # 固定排序后再摘要，确保同一目录在不同机器上生成稳定 digest。
    if path.is_file():
        return [path]
    return sorted((item for item in path.rglob("*") if item.is_file()), key=lambda item: item.relative_to(path).as_posix())


def digest_directory(path: Path, allowed_suffixes: set[str] | None = None) -> tuple[str | None, int, int, str | None, list[dict[str, Any]]]:
    # 目录摘要包含相对路径、大小和子文件 sha256，既可复核又不会把原始图像写进 JSON。
    files = []
    digest = hashlib.sha256()
    latest_mtime = 0.0
    total_size = 0
    for file_path in iter_files(path):
        if allowed_suffixes and file_path.suffix.lower() not in allowed_suffixes:
            continue
        size = file_path.stat().st_size
        relative = file_path.relative_to(path).as_posix()
        file_hash = sha256_file(file_path)
        total_size += size
        latest_mtime = max(latest_mtime, file_path.stat().st_mtime)
        digest.update(relative.encode("utf-8"))
        digest.update(str(size).encode("ascii"))
        digest.update(file_hash.encode("ascii"))
        files.append({"path": relative, "size_bytes": size, "sha256": file_hash})
    if not files:
        return None, 0, 0, None, []
    return digest.hexdigest(), total_size, len(files), mtime_utc(latest_mtime), files


def artifact_path(root: Path, name: str) -> Path | None:
    # 支持 route_data 子目录是为了兼容 preflight 模板中的默认采集输出结构。
    for candidate in ARTIFACT_CANDIDATES[name]:
        if "*" in candidate:
            matches = sorted(root.glob(candidate))
            if matches:
                return matches[0]
            continue
        path = root / candidate
        if path.exists():
            return path
    if name == "replay_jsonl":
        matches = sorted(root.rglob("*replay*.jsonl"))
        return matches[0] if matches else None
    if name == "rosbag":
        matches = sorted([item for item in root.rglob("*.db3") if item.is_file()])
        return matches[0] if matches else None
    return None


def missing_artifact(root: Path, name: str, reason: str, *, required: bool = True, expected_path: Path | None = None) -> dict[str, Any]:
    # 缺失项保留期望路径，现场排查时不用回查代码就能知道该补哪个文件。
    return {
        "required": required,
        "present": False,
        "path": str(expected_path or root / ARTIFACT_CANDIDATES[name][0]),
        "size_bytes": 0,
        "mtime_utc": None,
        "sha256": None,
        "reason": reason,
    }


def scan_file_artifact(root: Path, name: str, *, explicit_path: Path | None = None, required: bool = True) -> dict[str, Any]:
    # map、route、replay 都必须是非空文件；空模板不能进入现场证据链。
    path = explicit_path if explicit_path is not None else artifact_path(root, name)
    if path is None:
        reason = "missing" if required else "missing_optional"
        return missing_artifact(root, name, reason, required=required)
    if not path.is_file():
        return missing_artifact(root, name, "not_file", required=required, expected_path=path)
    size = path.stat().st_size
    if size <= 0:
        return missing_artifact(root, name, "empty", required=required, expected_path=path)
    return {
        "required": required,
        "present": True,
        "path": str(path),
        "size_bytes": size,
        "mtime_utc": mtime_utc(path.stat().st_mtime),
        "sha256": sha256_file(path),
        "reason": None,
    }


def scan_explicit_file_artifact(path: Path, fallback_root: Path, name: str) -> dict[str, Any]:
    # derive replay 产物可以写到当前 sprint artifacts；这里显式接入，避免 discovery 误判为缺失。
    required = True
    if not path.exists():
        reason = "missing" if required else "missing_optional"
        return missing_artifact(fallback_root, name, reason, required=required, expected_path=path)
    if not path.is_file():
        return missing_artifact(fallback_root, name, "not_file", required=required, expected_path=path)
    size = path.stat().st_size
    if size <= 0:
        return missing_artifact(fallback_root, name, "empty", required=required, expected_path=path)
    return {
        "required": required,
        "present": True,
        "path": str(path),
        "size_bytes": size,
        "mtime_utc": mtime_utc(path.stat().st_mtime),
        "sha256": sha256_file(path),
        "reason": None,
    }


def scan_directory_artifact(root: Path, name: str, allowed_suffixes: set[str] | None = None, *, required: bool = True) -> dict[str, Any]:
    # keyframes 只认可图片或 JSON，rosbag 则认可目录或单个非空 bag 文件。
    path = artifact_path(root, name)
    if path is None:
        reason = "missing" if required else "missing_optional"
        return missing_artifact(root, name, reason, required=required)
    if path.is_file():
        size = path.stat().st_size
        if size <= 0:
            return missing_artifact(root, name, "empty", required=required, expected_path=path)
        return {
            "required": required,
            "present": True,
            "path": str(path),
            "size_bytes": size,
            "mtime_utc": mtime_utc(path.stat().st_mtime),
            "sha256": sha256_file(path),
            "reason": None,
            "file_count": 1,
        }
    if not path.is_dir():
        return missing_artifact(root, name, "not_directory", required=required, expected_path=path)
    digest, total_size, file_count, latest_mtime, files = digest_directory(path, allowed_suffixes)
    if not files:
        reason = "no_keyframe_file" if allowed_suffixes else "empty"
        return missing_artifact(root, name, reason, required=required, expected_path=path)
    if total_size <= 0:
        return missing_artifact(root, name, "empty", required=required, expected_path=path)
    return {
        "required": required,
        "present": True,
        "path": str(path),
        "size_bytes": total_size,
        "mtime_utc": latest_mtime,
        "sha256": digest,
        "reason": None,
        "file_count": file_count,
        "files": files[:20],
    }


def scan_local_artifacts(root: Path, *, map_yaml: Path | None = None, map_pgm: Path | None = None) -> dict[str, Any]:
    # artifact gate 与 ROS2 运行解耦，缺真实硬件时也能用 fixture 验证 fail-closed 语义。
    return {
        "map_yaml": scan_file_artifact(root, "map_yaml", explicit_path=map_yaml),
        "map_pgm": scan_file_artifact(root, "map_pgm", explicit_path=map_pgm),
        "route_csv": scan_file_artifact(root, "route_csv"),
        "source_manifest": scan_file_artifact(root, "source_manifest"),
        "keyframes": scan_directory_artifact(root, "keyframes", KEYFRAME_SUFFIXES),
        "rosbag": scan_directory_artifact(root, "rosbag"),
        "replay_jsonl": scan_file_artifact(root, "replay_jsonl"),
    }


def artifact_present(artifact: dict[str, Any] | None) -> bool:
    # route-root seed 只信“存在且无扫描原因”的材料，避免空文件或坏目录被误当作可用证据。
    return bool(artifact and artifact.get("present") and not artifact.get("reason"))


def route_root_explicit(args: argparse.Namespace) -> bool:
    # 只有显式 route/route_data 目录或显式拆分 map 输入才进入 route-root 语义，普通 bundle 仍按完整材料 gate。
    root = Path(args.artifact_root).expanduser()
    has_split_map = bool(args.map_yaml and args.map_pgm)
    return root.name in ROUTE_ROOT_DIR_NAMES or has_split_map


def replay_enabled_or_present(args: argparse.Namespace, artifacts: dict[str, Any], derived_replay: dict[str, Any] | None) -> bool:
    # 派生 replay 请求本身就说明本轮在构造 O7-safe 回放材料；已有 replay 文件也满足 seed 条件。
    return bool(args.derive_replay_jsonl) or artifact_present(artifacts.get("replay_jsonl")) or bool(
        derived_replay and derived_replay.get("generated") is True
    )


def apply_route_root_seed_semantics(
    args: argparse.Namespace,
    artifacts: dict[str, Any],
    derived_replay: dict[str, Any] | None,
) -> None:
    # route-root seed 证明的是路线材料可被 O6/O7 消费，不证明真实运动；route_bag 因此降级为增强证据。
    if not (route_root_explicit(args) and replay_enabled_or_present(args, artifacts, derived_replay)):
        return
    rosbag = dict(artifacts.get("rosbag") or missing_artifact(Path(args.artifact_root).expanduser(), "rosbag", "missing"))
    rosbag["required"] = False
    if not artifact_present(rosbag):
        rosbag["present"] = False
        rosbag["reason"] = OPTIONAL_ROUTE_BAG_REASON
    artifacts["rosbag"] = rosbag


def route_root_seed_gate_summary(
    args: argparse.Namespace,
    artifacts: dict[str, Any],
    derived_replay: dict[str, Any] | None,
    source_manifest: dict[str, Any],
) -> dict[str, Any]:
    # 摘要面向 O6/O7，只暴露布尔、计数和 basename 级别事实，不泄露原始媒体或控制能力。
    explicit = route_root_explicit(args)
    replay_seed = replay_enabled_or_present(args, artifacts, derived_replay)
    route_bag_artifact = artifacts.get("rosbag", {})
    route_bag_required = bool(route_bag_artifact.get("required", True))
    route_bag_present = artifact_present(route_bag_artifact)
    route_csv_present = artifact_present(artifacts.get("route_csv"))
    source_manifest_present = artifact_present(artifacts.get("source_manifest"))
    replay_present = artifact_present(artifacts.get("replay_jsonl"))
    keyframes = artifacts.get("keyframes", {})
    blocked_reasons = [
        str(item.get("reason"))
        for item in artifacts.values()
        if item.get("required", True) and item.get("reason")
    ]
    if not route_bag_required and not route_bag_present:
        blocked_reasons.append(OPTIONAL_ROUTE_BAG_REASON)
    if source_manifest.get("blocked_reason"):
        blocked_reasons.append(str(source_manifest["blocked_reason"]))
    next_required_evidence = []
    if not route_bag_present:
        next_required_evidence.append("route_bag_or_live_nav2_log_for_motion_proof")
    if not replay_present:
        next_required_evidence.append("derive_or_attach_fixed_route_replay_jsonl")
    if not route_csv_present:
        next_required_evidence.append("attach_route_csv")
    if not source_manifest_present:
        next_required_evidence.append("attach_route_manifest_json")
    return {
        "schema": ROUTE_ROOT_SEED_SCHEMA,
        "enabled": explicit and replay_seed,
        "route_root_explicit": explicit,
        "replay_enabled_or_present": replay_seed,
        "status": "route_root_seed_gated_not_delivery_proof" if artifacts_pass(artifacts) else "route_root_seed_blocked_not_proven",
        "route_bag_required": route_bag_required,
        "route_bag_present": route_bag_present,
        "route_csv_present": route_csv_present,
        "source_manifest_present": source_manifest_present,
        "replay_jsonl_present": replay_present,
        "derived_replay_frame_count": int((derived_replay or {}).get("frame_count") or 0),
        "keyframe_count": int(keyframes.get("file_count") or 0),
        "blocked_reasons": sorted(set(blocked_reasons)),
        "next_required_evidence": next_required_evidence,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
    }


def safe_route_reference(path: Path) -> str:
    # replay JSONL 会被 O7/PC consumer 长期消费，因此只允许稳定逻辑引用，不泄露本机绝对路径。
    return "field_route://" + path.as_posix().lstrip("/")


def route_relative_reference(route_csv_path: Path, target_name: str) -> str:
    # 同一个 route bundle 内部的帧引用保持相对关系，便于后续 archive/解压后复用。
    route_dir_name = route_csv_path.parent.name
    if route_dir_name in {"route", "route_data"}:
        return safe_route_reference(Path(route_dir_name) / "keyframes" / target_name)
    return safe_route_reference(Path("keyframes") / target_name)


def safe_basename(value: str | None) -> str | None:
    # packet 面向 O6/O7 consumer，只暴露 basename 级别引用，避免把开发机路径带进后续归档。
    if not value:
        return None
    return Path(value).name


def quaternion_to_yaw_rad(qx: float, qy: float, qz: float, qw: float) -> float:
    # route.csv 当前记录完整 quaternion；这里显式转 yaw，避免 consumer 再各自重复推导。
    siny_cosp = 2.0 * (qw * qz + qx * qy)
    cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
    return math.atan2(siny_cosp, cosy_cosp)


def parse_timestamp_ms(row: dict[str, str]) -> int:
    # 现场 CSV 由 sec/nanosec 组成；统一落成毫秒整数，保证 JSONL 在不同 Python 版本下仍然稳定。
    sec = int(row.get("sec") or 0)
    nanosec = int(row.get("nanosec") or 0)
    return sec * 1000 + nanosec // 1_000_000


def read_route_rows(route_csv_path: Path) -> list[dict[str, str]]:
    # route.csv 后续既用于 derive replay，也用于 packet 位移统计，因此统一走一份 CSV 解析。
    with route_csv_path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def derive_replay_events(route_csv_path: Path) -> list[dict[str, Any]]:
    # 派生 replay 只复用 route.csv 的位姿事实，不猜测速度、控制命令或 delivery 成功状态。
    events: list[dict[str, Any]] = []
    for row in read_route_rows(route_csv_path):
        frame_name = str(row.get("frame") or "").strip()
        frame_index = int(row.get("index") or len(events))
        event = {
            "schema": "trashbot.fixed_route_replay.v1",
            "event": "route_frame",
            "frame_index": frame_index,
            "timestamp_ms": parse_timestamp_ms(row),
            "frame_id": str(row.get("frame_id") or "map"),
            "x_m": float(row.get("x") or 0.0),
            "y_m": float(row.get("y") or 0.0),
            "yaw_rad": quaternion_to_yaw_rad(
                float(row.get("qx") or 0.0),
                float(row.get("qy") or 0.0),
                float(row.get("qz") or 0.0),
                float(row.get("qw") or 1.0),
            ),
            "state": "not_proven_route_replay_only",
            "evidence_ref": route_relative_reference(route_csv_path, frame_name) if frame_name else safe_route_reference(Path(route_csv_path.name)),
            "source_route_csv": safe_route_reference(Path(route_csv_path.name)),
        }
        events.append(event)
    return events


def derive_replay_jsonl(route_csv_path: Path, output_path: Path) -> dict[str, Any]:
    # 先生成 deterministic JSONL，再让常规 artifact scan 读取同一输出文件，避免派生逻辑与 gate 视图分叉。
    events = derive_replay_events(route_csv_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return {
        "generated": True,
        "frame_count": len(events),
        "output": str(output_path),
        "source_route_csv": str(route_csv_path),
        "blocked_reason": None,
    }


def build_derived_replay_summary(args: argparse.Namespace, route_csv_path: Path | None) -> dict[str, Any]:
    # derive 是可选能力；未启用时明确标成 not_requested，避免 consumer 猜测 replay 来源。
    if not args.derive_replay_jsonl:
        return {
            "generated": False,
            "frame_count": 0,
            "output": None,
            "source_route_csv": str(route_csv_path) if route_csv_path else None,
            "blocked_reason": "not_requested",
        }
    if route_csv_path is None or not route_csv_path.is_file():
        return {
            "generated": False,
            "frame_count": 0,
            "output": args.derive_replay_jsonl,
            "source_route_csv": None,
            "blocked_reason": "missing_route_csv",
        }
    return derive_replay_jsonl(route_csv_path, Path(args.derive_replay_jsonl).expanduser())


def find_existing_manifest(root: Path, output: Path | None) -> Path | None:
    # 离线 packet 可能已经带 manifest；先按固定候选找，避免递归误吃大目录里的历史 JSON。
    for candidate in EXISTING_MANIFEST_CANDIDATES:
        path = root / candidate
        if path.exists() and path.is_file() and (output is None or path.resolve() != output.resolve()):
            return path
    return None


def existing_manifest_summary(root: Path, output: Path | None) -> dict[str, Any]:
    # 只有 field-evidence manifest 才按复用安全检查；route/manifest.json 另作为 source manifest 读取。
    path = find_existing_manifest(root, output)
    if path is None:
        return {
            "present": False,
            "path": None,
            "status": "not_found",
            "schema": None,
            "gate_pass": None,
            "dangerous_true_fields": [],
            "blocked_reason": None,
            "safe_for_reuse": True,
        }
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "present": True,
            "path": str(path),
            "status": "invalid_json",
            "schema": None,
            "gate_pass": None,
            "dangerous_true_fields": [],
            "blocked_reason": f"invalid_existing_manifest_json:{exc}",
            "safe_for_reuse": False,
        }
    if not isinstance(loaded, dict):
        return {
            "present": True,
            "path": str(path),
            "status": "invalid_root",
            "schema": None,
            "gate_pass": None,
            "dangerous_true_fields": [],
            "blocked_reason": "invalid_existing_manifest_root",
            "safe_for_reuse": False,
        }
    dangerous_true_fields = [field for field in UNSAFE_EXISTING_MANIFEST_FIELDS if loaded.get(field) is True]
    if loaded.get("schema") != SCHEMA:
        status = "schema_mismatch"
        blocked_reason = "existing_manifest_schema_mismatch"
    elif dangerous_true_fields:
        status = "unsafe_claim"
        blocked_reason = "unsafe_existing_manifest_claim"
    else:
        status = "schema_match_safe"
        blocked_reason = None
    return {
        "present": True,
        "path": str(path),
        "status": status,
        "schema": loaded.get("schema"),
        "gate_pass": loaded.get("gate_pass") if isinstance(loaded.get("gate_pass"), bool) else None,
        "dangerous_true_fields": dangerous_true_fields,
        "blocked_reason": blocked_reason,
        "safe_for_reuse": blocked_reason is None,
    }


def source_manifest_summary(artifact: dict[str, Any]) -> dict[str, Any]:
    # route_recorder 写出的 manifest.json 可能是 vision_samples schema；它是上游证据，不是本工具旧版输出。
    if not artifact.get("present"):
        return {
            "present": False,
            "path": artifact.get("path"),
            "status": "not_found",
            "schema": None,
            "sample_count": None,
            "blocked_reason": artifact.get("reason"),
        }
    path = Path(str(artifact["path"]))
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "present": True,
            "path": str(path),
            "status": "invalid_json",
            "schema": None,
            "sample_count": None,
            "blocked_reason": f"invalid_source_manifest_json:{exc}",
        }
    if not isinstance(loaded, dict):
        return {
            "present": True,
            "path": str(path),
            "status": "invalid_root",
            "schema": None,
            "sample_count": None,
            "blocked_reason": "invalid_source_manifest_root",
        }
    samples = loaded.get("samples")
    return {
        "present": True,
        "path": str(path),
        "status": "source_manifest",
        "schema": loaded.get("schema"),
        "sample_count": len(samples) if isinstance(samples, list) else None,
        "loaded": loaded,
        "blocked_reason": None,
    }


def route_summary(artifact: dict[str, Any]) -> dict[str, Any]:
    # route 摘要只暴露 frame/位移/时间窗口，供 packet 和 consumer 复用，不暴露任何控制语义。
    if not artifact.get("present"):
        return {
            "present": False,
            "path": artifact.get("path"),
            "frame_count": 0,
            "nonzero_displacement_observed": False,
            "distance_m": 0.0,
            "start_pose": None,
            "end_pose": None,
            "duration_ms": 0,
            "blocked_reason": artifact.get("reason"),
        }
    path = Path(str(artifact["path"]))
    rows = read_route_rows(path)
    if not rows:
        return {
            "present": True,
            "path": str(path),
            "frame_count": 0,
            "nonzero_displacement_observed": False,
            "distance_m": 0.0,
            "start_pose": None,
            "end_pose": None,
            "duration_ms": 0,
            "blocked_reason": "empty_route_csv",
        }
    start_row = rows[0]
    end_row = rows[-1]
    start_x = float(start_row.get("x") or 0.0)
    start_y = float(start_row.get("y") or 0.0)
    end_x = float(end_row.get("x") or 0.0)
    end_y = float(end_row.get("y") or 0.0)
    distance_m = math.hypot(end_x - start_x, end_y - start_y)
    return {
        "present": True,
        "path": str(path),
        "basename": path.name,
        "frame_count": len(rows),
        "nonzero_displacement_observed": distance_m > 1e-6,
        "distance_m": round(distance_m, 6),
        "start_pose": {"x_m": start_x, "y_m": start_y, "frame_id": str(start_row.get("frame_id") or "map")},
        "end_pose": {"x_m": end_x, "y_m": end_y, "frame_id": str(end_row.get("frame_id") or "map")},
        "duration_ms": max(0, parse_timestamp_ms(end_row) - parse_timestamp_ms(start_row)),
        "blocked_reason": None,
    }


def keyframe_summary(artifact: dict[str, Any]) -> dict[str, Any]:
    # keyframe 摘要只输出计数和样本名，避免把原始图片路径直接暴露给上层 UI。
    files = artifact.get("files") or []
    sample_refs = [safe_basename(str(item.get("path"))) for item in files[:5] if item.get("path")]
    return {
        "present": bool(artifact.get("present")),
        "path": artifact.get("path"),
        "count": int(artifact.get("file_count") or 0),
        "sample_refs": [item for item in sample_refs if item],
        "blocked_reason": artifact.get("reason"),
    }


def map_summary(artifacts: dict[str, Any]) -> dict[str, Any]:
    # map.yaml 和 map.pgm 必须成对出现，packet 只关心是否可复用和各自 basename。
    map_yaml = artifacts.get("map_yaml", {})
    map_pgm = artifacts.get("map_pgm", {})
    return {
        "map_yaml_present": artifact_present(map_yaml),
        "map_yaml_ref": safe_basename(str(map_yaml.get("path") or "")),
        "map_pgm_present": artifact_present(map_pgm),
        "map_pgm_ref": safe_basename(str(map_pgm.get("path") or "")),
        "blocked_reasons": [reason for reason in [map_yaml.get("reason"), map_pgm.get("reason")] if reason],
    }


def safe_sha256_prefix(value: Any, *, length: int = 12) -> str | None:
    # O6/O7 只需要短 hash 前缀做材料对照；完整 digest 没必要在 packet 里重复暴露。
    if not isinstance(value, str):
        return None
    lowered = value.strip().lower()
    if not re.fullmatch(r"[0-9a-f]{12,64}", lowered):
        return None
    return lowered[:length]


def count_replay_lines(path_value: Any) -> int:
    # replay 只统计 JSONL 行数，避免把原始事件内容继续带进摘要。
    if not isinstance(path_value, str) or not path_value:
        return 0
    path = Path(path_value)
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return sum(1 for line in handle if line.strip())
    except OSError:
        return 0


def sample_material_refs(artifact: dict[str, Any], *, limit: int = 3) -> list[str]:
    # sample ref 只允许 basename 粒度，既能复核文件存在，也不会泄露开发机路径。
    if not artifact_present(artifact):
        return []
    files = artifact.get("files")
    if isinstance(files, list) and files:
        refs = [safe_basename(str(item.get("path") or "")) for item in files[:limit] if isinstance(item, dict)]
        return [item for item in refs if item]
    basename = safe_basename(str(artifact.get("path") or ""))
    return [basename] if basename else []


def material_item_summary(name: str, artifact: dict[str, Any], *, count: int | None = None) -> dict[str, Any]:
    # material item 固定输出 basename/size/hash/count，不把绝对路径或文件内容回传给上游。
    summary = {
        "present": artifact_present(artifact),
        "required": bool(artifact.get("required", True)),
        "basename": safe_basename(str(artifact.get("path") or "")),
        "size_bytes": int(artifact.get("size_bytes") or 0),
        "sha256_prefix": safe_sha256_prefix(artifact.get("sha256")),
        "sample_refs": sample_material_refs(artifact),
        "count": int(count if count is not None else artifact.get("file_count") or (1 if artifact_present(artifact) else 0)),
        "reason": artifact.get("reason"),
    }
    if name == "replay_jsonl":
        summary["count"] = count_replay_lines(artifact.get("path")) if summary["present"] else 0
    return summary


def collect_same_task_field_material_safety_issues(value: Any, parent: str = "") -> tuple[list[str], list[str], list[str]]:
    # source manifest 可能来自历史材料包；这里先全树扫描，再决定 packet 是否需要 fail-closed。
    dangerous_true_fields: list[str] = []
    unsafe_fields: list[str] = []
    unsafe_text_fields: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{parent}.{key_text}" if parent else key_text
            key_lower = key_text.lower()
            if key_lower in SAME_TASK_FIELD_MATERIAL_DANGEROUS_TRUE_FIELDS and child is True:
                dangerous_true_fields.append(child_path)
            if any(marker in key_lower for marker in SAME_TASK_FIELD_MATERIAL_UNSAFE_MARKERS):
                unsafe_fields.append(child_path)
            child_dangerous, child_unsafe, child_unsafe_text = collect_same_task_field_material_safety_issues(child, child_path)
            dangerous_true_fields.extend(child_dangerous)
            unsafe_fields.extend(child_unsafe)
            unsafe_text_fields.extend(child_unsafe_text)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{parent}[{index}]" if parent else f"[{index}]"
            child_dangerous, child_unsafe, child_unsafe_text = collect_same_task_field_material_safety_issues(child, child_path)
            dangerous_true_fields.extend(child_dangerous)
            unsafe_fields.extend(child_unsafe)
            unsafe_text_fields.extend(child_unsafe_text)
    elif isinstance(value, str) and summary_contains_unsafe_text(value):
        unsafe_text_fields.append(parent or "text")
    return sorted(set(dangerous_true_fields)), sorted(set(unsafe_fields)), sorted(set(unsafe_text_fields))


def build_same_task_field_material_packet(
    packet: dict[str, Any],
    artifacts: dict[str, Any],
    source_manifest: dict[str, Any],
) -> dict[str, Any]:
    # 这份 packet 只证明“同 task 的准现场路线材料已被安全消费”，不证明 live Nav2 或 delivery 成功。
    task_id = str(packet.get("task_id") or "")
    task_id_source = str(packet.get("task_id_source") or "field_motion_evidence_packet")
    material_items = {
        "map_yaml": material_item_summary("map_yaml", artifacts.get("map_yaml", {})),
        "route_csv": material_item_summary("route_csv", artifacts.get("route_csv", {})),
        "keyframes": material_item_summary("keyframes", artifacts.get("keyframes", {})),
        "route_bag_or_rosbag": material_item_summary("route_bag_or_rosbag", artifacts.get("rosbag", {})),
        "replay_jsonl": material_item_summary("replay_jsonl", artifacts.get("replay_jsonl", {})),
    }
    present_materials = [name for name, item in material_items.items() if item["present"]]
    missing_materials = [name for name in material_items if name not in present_materials]
    dangerous_true_fields, unsafe_fields, unsafe_text_fields = collect_same_task_field_material_safety_issues(source_manifest.get("loaded"))
    blocked_reasons: list[str] = []
    next_required_evidence: list[str] = []
    if not task_id:
        blocked_reasons.append("same_task_field_material_task_id_missing")
        next_required_evidence.append("stable_same_task_id_for_route_materials")
    if len(present_materials) < 2:
        blocked_reasons.append("same_task_field_material_insufficient_present_materials")
        next_required_evidence.append("at_least_two_same_task_route_material_categories")
    if not material_items["map_yaml"]["present"]:
        blocked_reasons.append("same_task_field_material_map_yaml_missing_optional")
        next_required_evidence.append("attach_map_yaml_for_navigation_context")
    if not material_items["route_csv"]["present"]:
        next_required_evidence.append("attach_same_task_route_csv")
    if not material_items["keyframes"]["present"]:
        next_required_evidence.append("attach_same_task_keyframes")
    if not material_items["route_bag_or_rosbag"]["present"]:
        next_required_evidence.append("attach_same_task_route_bag_or_rosbag")
    if not material_items["replay_jsonl"]["present"]:
        next_required_evidence.append("attach_same_task_replay_jsonl")
    if dangerous_true_fields:
        blocked_reasons.append("same_task_field_material_dangerous_true_claim")
    if unsafe_fields:
        blocked_reasons.append("same_task_field_material_unsafe_field")
    if unsafe_text_fields:
        blocked_reasons.append("same_task_field_material_unsafe_text")
    ready = len(present_materials) >= 2 and not dangerous_true_fields and not unsafe_fields and not unsafe_text_fields and bool(task_id)
    sample_refs = []
    for item in material_items.values():
        sample_refs.extend(item.get("sample_refs") or [])
    return {
        "schema": SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA,
        "proof_scope": SAME_TASK_FIELD_MATERIAL_PACKET_PROOF_SCOPE,
        "status": "ready_not_delivery_proof" if ready else "blocked_not_proven",
        "source": "field_motion_evidence_packet.material_artifacts",
        "task_id": task_id,
        "task_id_source": task_id_source,
        "same_task_id_consumed": bool(task_id),
        "live_or_field_material_consumed": len(present_materials) >= 2,
        "present_materials": present_materials,
        "missing_materials": missing_materials,
        "present_material_count": len(present_materials),
        "missing_material_count": len(missing_materials),
        "map_yaml_present": material_items["map_yaml"]["present"],
        "route_csv_present": material_items["route_csv"]["present"],
        "keyframes_present": material_items["keyframes"]["present"],
        "route_bag_or_rosbag_present": material_items["route_bag_or_rosbag"]["present"],
        "replay_jsonl_present": material_items["replay_jsonl"]["present"],
        "material_flags": {
            "map_yaml_present": material_items["map_yaml"]["present"],
            "route_csv_present": material_items["route_csv"]["present"],
            "keyframes_present": material_items["keyframes"]["present"],
            "route_bag_or_rosbag_present": material_items["route_bag_or_rosbag"]["present"],
            "replay_jsonl_present": material_items["replay_jsonl"]["present"],
        },
        "material_summaries": material_items,
        "sample_refs": sample_refs[:8],
        "blocked_reasons": sorted(set(blocked_reasons)),
        "dangerous_true_fields": dangerous_true_fields,
        "unsafe_field_count": len(unsafe_fields),
        "unsafe_text_field_count": len(unsafe_text_fields),
        "next_required_evidence": sorted(
            set(
                next_required_evidence
                + (
                    [
                        "same_task_delivery_record_or_operator_confirmation",
                        "live_route_execution_or_production_cloud_acceptance",
                    ]
                    if ready
                    else []
                )
            )
        ),
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "route_execution_success": False,
    }


def nav2_goal_path(parent: str, key: str) -> str:
    # fail-closed 报告只给字段名，不回显字段值，避免路径、token 或 raw payload 进入 manifest。
    return f"{parent}.{key}" if parent else key


def delivery_result_path(parent: str, key: str) -> str:
    # delivery result 摘要也只暴露字段路径，防止人工备注或 URL 被回显到 O6/O7 读链路。
    return f"{parent}.{key}" if parent else key


def collect_nav2_goal_proof_safety_issues(value: Any, parent: str = "") -> tuple[list[str], list[str], list[str]]:
    # O11 proof 原文可能含运行日志路径或 raw 字段；这里先全树扫描，命中后只输出字段名级别阻断。
    dangerous_true_fields: list[str] = []
    unsafe_fields: list[str] = []
    unsafe_text_fields: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            child_path = nav2_goal_path(parent, key_text)
            key_lower = key_text.lower()
            if key_lower in NAV2_GOAL_DANGEROUS_TRUE_FIELDS and child is True:
                dangerous_true_fields.append(child_path)
            if any(marker in key_lower for marker in NAV2_GOAL_UNSAFE_MARKERS):
                unsafe_fields.append(child_path)
            child_dangerous, child_unsafe, child_unsafe_text = collect_nav2_goal_proof_safety_issues(child, child_path)
            dangerous_true_fields.extend(child_dangerous)
            unsafe_fields.extend(child_unsafe)
            unsafe_text_fields.extend(child_unsafe_text)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{parent}[{index}]" if parent else f"[{index}]"
            child_dangerous, child_unsafe, child_unsafe_text = collect_nav2_goal_proof_safety_issues(child, child_path)
            dangerous_true_fields.extend(child_dangerous)
            unsafe_fields.extend(child_unsafe)
            unsafe_text_fields.extend(child_unsafe_text)
    elif isinstance(value, str):
        lowered = value.lower()
        # 字符串值只按高风险片段阻断，避免把普通 status 文案误判成敏感字段。
        if any(marker in lowered for marker in ("/root", "/users/", "token", "base64", "raw_payload", " raw ", "path=")):
            unsafe_text_fields.append(parent or "<root>")
    return sorted(set(dangerous_true_fields)), sorted(set(unsafe_fields)), sorted(set(unsafe_text_fields))


def safe_nav2_goal_text(value: Any) -> str | None:
    # 只接收短字符串；复杂对象、空值或非字符串不进入 O6/O7 白名单摘要。
    if not isinstance(value, str):
        return None
    return value[:160]


def safe_nav2_goal_bool(value: Any) -> bool:
    # 严格要求 JSON boolean，避免 "true" 字符串被误当作真控制证据。
    return value is True


def safe_nav2_goal_int(value: Any) -> int | None:
    # result_status_code 是 action status 数字；bool 在 Python 里是 int 子类，必须显式排除。
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and math.isfinite(value) and value.is_integer():
        return int(value)
    return None


def safe_nav2_goal_float(value: Any) -> float | None:
    # goal pose 只保留有限浮点数，不做坐标系或路径推导。
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return float(value)
    return None


def collect_delivery_result_safety_issues(value: Any, parent: str = "") -> tuple[list[str], list[str], list[str]]:
    # delivery result 常来自人工/mock JSON，先做全树安全扫描，再决定是否允许白名单摘要进入 manifest。
    dangerous_true_fields: list[str] = []
    unsafe_fields: list[str] = []
    unsafe_text_fields: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            child_path = delivery_result_path(parent, key_text)
            key_lower = key_text.lower()
            if key_lower in DELIVERY_RESULT_DANGEROUS_TRUE_FIELDS and child is True:
                dangerous_true_fields.append(child_path)
            if any(marker in key_lower for marker in DELIVERY_RESULT_UNSAFE_MARKERS):
                unsafe_fields.append(child_path)
            child_dangerous, child_unsafe, child_unsafe_text = collect_delivery_result_safety_issues(child, child_path)
            dangerous_true_fields.extend(child_dangerous)
            unsafe_fields.extend(child_unsafe)
            unsafe_text_fields.extend(child_unsafe_text)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{parent}[{index}]" if parent else f"[{index}]"
            child_dangerous, child_unsafe, child_unsafe_text = collect_delivery_result_safety_issues(child, child_path)
            dangerous_true_fields.extend(child_dangerous)
            unsafe_fields.extend(child_unsafe)
            unsafe_text_fields.extend(child_unsafe_text)
    elif isinstance(value, str):
        lowered = value.lower()
        # 这里同时阻断绝对路径、token/raw/base64 痕迹和带凭证 URL，避免人工备注泄露敏感上下文。
        if (
            any(marker in lowered for marker in ("/root", "/users/", "token", "base64", "raw_payload", " raw ", "path="))
            or DELIVERY_RESULT_CREDENTIAL_URL_RE.search(value)
        ):
            unsafe_text_fields.append(parent or "<root>")
    return sorted(set(dangerous_true_fields)), sorted(set(unsafe_fields)), sorted(set(unsafe_text_fields))


def safe_delivery_result_text(value: Any) -> str | None:
    # delivery result 只接受短文本字段，避免长备注、原始日志或 HTML 进入归档摘要。
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text[:160] if text else None


def safe_delivery_result_bool(value: Any) -> bool:
    # 只认真正的 JSON boolean，字符串 true/false 不应被视为送达证据。
    return value is True


def safe_delivery_result_completed_at(value: Any) -> str | None:
    # 时间戳只允许短 UTC 文本，避免把本地路径、时区噪音或非标准字符串写进 additive。
    text = safe_delivery_result_text(value)
    if not text or not UTC_TEXT_RE.fullmatch(text):
        return None
    return text


def safe_delivery_result_claimed(value: Any) -> bool:
    # 允许 bool 或有限状态字符串表达“输入里有人声称已完成”，但它绝不能推高 delivery_success。
    if value is True:
        return True
    if not isinstance(value, str):
        return False
    lowered = value.strip().lower()
    return lowered in {
        "delivered",
        "delivery_recorded",
        "dropoff_completed",
        "operator_confirmed_dropoff",
        "completed",
        "succeeded",
        "success",
    }


def safe_cloud_terminal_completed_at(value: Any) -> str | None:
    # O5 终态写入口可能带本地时区；manifest 统一输出 UTC，避免 O6/O7 按时区误读顺序。
    text = safe_delivery_result_text(value)
    if not text:
        return None
    try:
        parsed = _dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(_dt.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_cloud_terminal_ref(value: Any) -> tuple[str | None, bool]:
    # terminal result 的 ref 只允许短逻辑标识；路径、URL、token、raw/base64 都不能进入 manifest。
    if not isinstance(value, str):
        return None, False
    text = value.strip()
    if not text:
        return None, False
    lowered = text.lower()
    if (
        len(text) > 160
        or text.startswith(("/", "~"))
        or "\\" in text
        or "/" in text
        or CLOUD_TERMINAL_URL_RE.search(text)
        or DELIVERY_RESULT_CREDENTIAL_URL_RE.search(text)
        or any(marker in lowered for marker in ("token", "base64", "raw_payload", " raw ", "path=", "/root", "/users/"))
    ):
        return None, True
    return text, False


def cloud_terminal_completion_claimed(terminal_type: str | None, result_code: str | None, task_terminal_state: str | None) -> bool:
    # 只有 delivery/dropoff 终态可以转成 delivery_result_claimed；cancel/failure/timeout 继续 fail-closed。
    if terminal_type not in CLOUD_TERMINAL_DELIVERY_TYPES:
        return False
    normalized_values = {str(item or "").strip().lower() for item in (result_code, task_terminal_state)}
    return any(value in CLOUD_TERMINAL_COMPLETED_VALUES or value.endswith("_terminal_completed") for value in normalized_values if value)


def delivery_result_blocked_summary(
    task_id: str,
    task_id_source: str,
    linked_nav2_goal_execution_proven: bool,
    blocked_reasons: list[str],
    *,
    record_present: bool,
    record_read_ok: bool,
    source: str = "delivery_result_json",
    source_schema: str | None = None,
    dangerous_true_fields: list[str] | None = None,
    unsafe_fields: list[str] | None = None,
    unsafe_text_fields: list[str] | None = None,
    next_required_evidence: list[str] | None = None,
) -> dict[str, Any]:
    # 同形 blocked 摘要保证 O6/O7 缺输入或命中危险字段时仍有稳定 additive 可读。
    reasons = sorted(set(reason for reason in blocked_reasons if reason))
    next_required_evidence_values = list(next_required_evidence or ["safe_delivery_result_json_for_selected_task", "delivery_record_or_operator_dropoff_confirmation"])
    if not linked_nav2_goal_execution_proven:
        next_required_evidence_values.insert(0, "linked_nav2_goal_execution_evidence")
    return {
        "schema": DELIVERY_RESULT_EVIDENCE_SCHEMA,
        "proof_scope": DELIVERY_RESULT_EVIDENCE_PROOF_SCOPE,
        "source": source,
        "source_schema": source_schema,
        "status": "blocked_not_proven",
        "task_id": task_id,
        "task_id_source": task_id_source,
        "record_present": record_present,
        "record_read_ok": record_read_ok,
        "record_status": None,
        "delivery_result_claimed": False,
        "operator_confirmation_present": False,
        "dropoff_confirmation_type": None,
        "completed_at_utc": None,
        "linked_nav2_goal_execution_proven": linked_nav2_goal_execution_proven,
        "blocked_reasons": reasons,
        "dangerous_true_fields": sorted(set(dangerous_true_fields or [])),
        "unsafe_field_count": len(set(unsafe_fields or [])),
        "unsafe_text_field_count": len(set(unsafe_text_fields or [])),
        "next_required_evidence": sorted(set(next_required_evidence_values)),
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
    }


def build_cloud_terminal_delivery_result_evidence(args: argparse.Namespace, packet: dict[str, Any]) -> dict[str, Any]:
    # O5 terminal result 是 delivery_result_evidence 的一个安全来源，不改变 field packet 的主 task lineage。
    task_id = str(packet.get("task_id") or args.run_id)
    task_id_source = str(packet.get("task_id_source") or "field_motion_evidence_packet")
    linked_nav2 = bool(((packet.get("nav2_goal_execution_evidence") or {}).get("nav2_goal_execution_proven")))
    terminal_result_path_value = getattr(args, "cloud_terminal_result_json", None)
    try:
        loaded = json.loads(Path(terminal_result_path_value).expanduser().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return delivery_result_blocked_summary(
            task_id,
            task_id_source,
            linked_nav2,
            ["cloud_terminal_result_json_unreadable"],
            record_present=True,
            record_read_ok=False,
            source="cloud_command_terminal_result",
        )
    if not isinstance(loaded, dict):
        return delivery_result_blocked_summary(
            task_id,
            task_id_source,
            linked_nav2,
            ["cloud_terminal_result_json_root_not_object"],
            record_present=True,
            record_read_ok=True,
            source="cloud_command_terminal_result",
        )

    source_schema = safe_delivery_result_text(loaded.get("schema"))
    dangerous_true_fields, unsafe_fields, unsafe_text_fields = collect_delivery_result_safety_issues(loaded)
    normalized_loaded = loaded
    if source_schema == CLOUD_COMMAND_RESULT_RECONCILIATION_SCHEMA:
        # reconciliation wrapper 只能在 recorded 且 nested terminal_result 合法时下钻；否则必须维持 fail-closed。
        result_state = safe_delivery_result_text(loaded.get("result_state"))
        nested_terminal_result = loaded.get("terminal_result")
        blocked_reasons = []
        next_required_evidence = ["same_task_delivery_record_review"]
        if result_state != "terminal_result_recorded":
            blocked_reasons.append("cloud_terminal_result_reconciliation_result_state_not_recorded")
            next_required_evidence.append("recorded_reconciliation_terminal_result")
        if nested_terminal_result is None:
            blocked_reasons.append("cloud_terminal_result_reconciliation_terminal_result_missing")
            next_required_evidence.append("nested_cloud_terminal_result")
        elif not isinstance(nested_terminal_result, dict):
            blocked_reasons.append("cloud_terminal_result_reconciliation_terminal_result_not_object")
            next_required_evidence.append("nested_cloud_terminal_result")
        else:
            nested_schema = safe_delivery_result_text(nested_terminal_result.get("schema"))
            if nested_schema != CLOUD_COMMAND_TERMINAL_RESULT_SCHEMA:
                blocked_reasons.append("cloud_terminal_result_reconciliation_terminal_result_schema_mismatch")
                next_required_evidence.append("nested_cloud_terminal_result_v1")
            wrapper_task_id = safe_delivery_result_text(loaded.get("task_id"))
            nested_task_id = safe_delivery_result_text(nested_terminal_result.get("task_id"))
            if wrapper_task_id and wrapper_task_id != task_id:
                blocked_reasons.append("cloud_terminal_result_reconciliation_task_id_mismatch")
            if nested_task_id and nested_task_id != task_id:
                blocked_reasons.append("cloud_terminal_result_task_id_mismatch")
            if wrapper_task_id and nested_task_id and wrapper_task_id != nested_task_id:
                blocked_reasons.append("cloud_terminal_result_reconciliation_nested_task_id_mismatch")
                next_required_evidence.append("same_task_terminal_result_alignment")
            if not blocked_reasons:
                # 输出合同继续维持 direct terminal result 语义，wrapper 只负责 gate 和补齐安全 ref。
                normalized_loaded = dict(nested_terminal_result)
                for ref_key in ("command_id", "task_record_ref", "evidence_ref", "task_id"):
                    if normalized_loaded.get(ref_key) in (None, "") and loaded.get(ref_key) not in (None, ""):
                        normalized_loaded[ref_key] = loaded.get(ref_key)
        if blocked_reasons:
            return delivery_result_blocked_summary(
                task_id,
                task_id_source,
                linked_nav2,
                blocked_reasons,
                record_present=True,
                record_read_ok=True,
                source="cloud_command_terminal_result",
                source_schema=CLOUD_COMMAND_TERMINAL_RESULT_SCHEMA,
                next_required_evidence=next_required_evidence,
            )

    command_id_ref, command_id_ref_unsafe = safe_cloud_terminal_ref(normalized_loaded.get("command_id"))
    task_record_ref, task_record_ref_unsafe = safe_cloud_terminal_ref(normalized_loaded.get("task_record_ref"))
    evidence_ref, evidence_ref_unsafe = safe_cloud_terminal_ref(normalized_loaded.get("evidence_ref"))
    if command_id_ref_unsafe:
        unsafe_text_fields.append("command_id")
    if task_record_ref_unsafe:
        unsafe_text_fields.append("task_record_ref")
    if evidence_ref_unsafe:
        unsafe_text_fields.append("evidence_ref")
    normalized_source_schema = safe_delivery_result_text(normalized_loaded.get("schema"))
    if "schema" in unsafe_text_fields:
        normalized_source_schema = None
    if dangerous_true_fields or unsafe_fields or unsafe_text_fields:
        reasons = []
        if dangerous_true_fields:
            reasons.append("cloud_terminal_result_dangerous_true_claim")
        if unsafe_fields or unsafe_text_fields:
            reasons.append("cloud_terminal_result_unsafe_field_or_text")
        return delivery_result_blocked_summary(
            task_id,
            task_id_source,
            linked_nav2,
            reasons,
            record_present=True,
            record_read_ok=True,
            source="cloud_command_terminal_result",
            source_schema=normalized_source_schema,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_fields=unsafe_fields,
            unsafe_text_fields=unsafe_text_fields,
        )
    if normalized_loaded.get("schema") != CLOUD_COMMAND_TERMINAL_RESULT_SCHEMA:
        return delivery_result_blocked_summary(
            task_id,
            task_id_source,
            linked_nav2,
            ["cloud_terminal_result_schema_mismatch"],
            record_present=True,
            record_read_ok=True,
            source="cloud_command_terminal_result",
            source_schema=normalized_source_schema,
        )

    source_task_id = safe_delivery_result_text(normalized_loaded.get("task_id"))
    terminal_type = safe_delivery_result_text(normalized_loaded.get("terminal_result_type"))
    task_terminal_state = safe_delivery_result_text(normalized_loaded.get("task_terminal_state") or normalized_loaded.get("terminal_result_state"))
    result_code = safe_delivery_result_text(normalized_loaded.get("result_code"))
    completed_at_utc = safe_cloud_terminal_completed_at(normalized_loaded.get("completed_at") or normalized_loaded.get("completed_at_utc"))
    delivery_result_claimed = cloud_terminal_completion_claimed(terminal_type, result_code, task_terminal_state)
    dropoff_confirmation_type = f"cloud_{terminal_type}" if delivery_result_claimed and terminal_type else None
    evidence = {
        "schema": DELIVERY_RESULT_EVIDENCE_SCHEMA,
        "proof_scope": DELIVERY_RESULT_EVIDENCE_PROOF_SCOPE,
        "source": "cloud_command_terminal_result",
        "source_schema": CLOUD_COMMAND_TERMINAL_RESULT_SCHEMA,
        "status": "blocked_not_proven",
        "task_id": task_id,
        "task_id_source": task_id_source,
        "record_present": True,
        "record_read_ok": True,
        "record_status": task_terminal_state or result_code,
        "delivery_result_claimed": delivery_result_claimed,
        "operator_confirmation_present": delivery_result_claimed,
        "dropoff_confirmation_type": dropoff_confirmation_type,
        "completed_at_utc": completed_at_utc,
        "command_id_ref": command_id_ref,
        "task_record_ref": task_record_ref,
        "evidence_ref": evidence_ref,
        "linked_nav2_goal_execution_proven": linked_nav2,
        "dangerous_true_fields": [],
        "unsafe_field_count": 0,
        "unsafe_text_field_count": 0,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
    }
    blocked_reasons = []
    if source_task_id and source_task_id != task_id:
        blocked_reasons.append("cloud_terminal_result_task_id_mismatch")
    if terminal_type not in CLOUD_TERMINAL_DELIVERY_TYPES:
        blocked_reasons.append("cloud_terminal_result_type_not_delivery_or_dropoff")
    if not task_terminal_state:
        blocked_reasons.append("cloud_terminal_result_state_missing")
    if not result_code:
        blocked_reasons.append("cloud_terminal_result_code_missing")
    if not delivery_result_claimed:
        blocked_reasons.append("cloud_terminal_result_completion_claim_missing")
    if completed_at_utc is None:
        blocked_reasons.append("completed_at_utc_missing_or_invalid")
    if not linked_nav2:
        blocked_reasons.append("linked_nav2_goal_execution_not_proven")
    next_required_evidence = []
    if not linked_nav2:
        next_required_evidence.append("linked_nav2_goal_execution_evidence")
    if terminal_type not in CLOUD_TERMINAL_DELIVERY_TYPES:
        next_required_evidence.append("cloud_delivery_or_dropoff_terminal_result")
    if not delivery_result_claimed:
        next_required_evidence.append("completed_cloud_terminal_result")
    if completed_at_utc is None:
        next_required_evidence.append("completed_at_utc_utc_text")
    next_required_evidence.append("same_task_delivery_record_review")
    evidence["blocked_reasons"] = sorted(set(blocked_reasons))
    evidence["next_required_evidence"] = sorted(set(next_required_evidence))
    if not evidence["blocked_reasons"]:
        evidence["status"] = "ready_not_delivery_proof"
    return evidence


def build_delivery_result_evidence(args: argparse.Namespace, packet: dict[str, Any]) -> dict[str, Any]:
    # delivery result additive 只复用 packet lineage 和安全白名单字段，不采信输入里的“成功”声明。
    task_id = str(packet.get("task_id") or args.run_id)
    task_id_source = str(packet.get("task_id_source") or "field_motion_evidence_packet")
    linked_nav2 = bool(((packet.get("nav2_goal_execution_evidence") or {}).get("nav2_goal_execution_proven")))
    delivery_result_path_value = getattr(args, "delivery_result_json", None)
    if not delivery_result_path_value:
        if getattr(args, "cloud_terminal_result_json", None):
            return build_cloud_terminal_delivery_result_evidence(args, packet)
        return delivery_result_blocked_summary(
            task_id,
            task_id_source,
            linked_nav2,
            ["delivery_result_json_missing"],
            record_present=False,
            record_read_ok=False,
        )
    try:
        loaded = json.loads(Path(delivery_result_path_value).expanduser().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return delivery_result_blocked_summary(
            task_id,
            task_id_source,
            linked_nav2,
            ["delivery_result_json_unreadable"],
            record_present=True,
            record_read_ok=False,
        )
    if not isinstance(loaded, dict):
        return delivery_result_blocked_summary(
            task_id,
            task_id_source,
            linked_nav2,
            ["delivery_result_json_root_not_object"],
            record_present=True,
            record_read_ok=True,
        )

    source_schema = safe_delivery_result_text(loaded.get("schema"))
    dangerous_true_fields, unsafe_fields, unsafe_text_fields = collect_delivery_result_safety_issues(loaded)
    if "schema" in unsafe_text_fields:
        source_schema = None
    if dangerous_true_fields or unsafe_fields or unsafe_text_fields:
        reasons = []
        if dangerous_true_fields:
            reasons.append("delivery_result_dangerous_true_claim")
        if unsafe_fields or unsafe_text_fields:
            reasons.append("delivery_result_unsafe_field_or_text")
        return delivery_result_blocked_summary(
            task_id,
            task_id_source,
            linked_nav2,
            reasons,
            record_present=True,
            record_read_ok=True,
            source_schema=source_schema,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_fields=unsafe_fields,
            unsafe_text_fields=unsafe_text_fields,
        )
    if loaded.get("schema") != DELIVERY_RESULT_SOURCE_SCHEMA:
        return delivery_result_blocked_summary(
            task_id,
            task_id_source,
            linked_nav2,
            ["delivery_result_schema_mismatch"],
            record_present=True,
            record_read_ok=True,
            source_schema=source_schema,
        )

    source_task_id = safe_delivery_result_text(loaded.get("task_id"))
    record_status = safe_delivery_result_text(loaded.get("record_status") or loaded.get("status"))
    completed_at_utc = safe_delivery_result_completed_at(loaded.get("completed_at_utc"))
    evidence = {
        "schema": DELIVERY_RESULT_EVIDENCE_SCHEMA,
        "proof_scope": DELIVERY_RESULT_EVIDENCE_PROOF_SCOPE,
        "source": "delivery_result_json",
        "source_schema": DELIVERY_RESULT_SOURCE_SCHEMA,
        "status": "blocked_not_proven",
        "task_id": task_id,
        "task_id_source": task_id_source,
        "record_present": True,
        "record_read_ok": True,
        "record_status": record_status,
        "delivery_result_claimed": safe_delivery_result_claimed(loaded.get("delivery_result_claimed") or record_status),
        "operator_confirmation_present": safe_delivery_result_bool(loaded.get("operator_confirmation_present")),
        "dropoff_confirmation_type": safe_delivery_result_text(loaded.get("dropoff_confirmation_type")),
        "completed_at_utc": completed_at_utc,
        "linked_nav2_goal_execution_proven": linked_nav2,
        "dangerous_true_fields": [],
        "unsafe_field_count": 0,
        "unsafe_text_field_count": 0,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
    }
    blocked_reasons = []
    if source_task_id and source_task_id != task_id:
        blocked_reasons.append("delivery_result_task_id_mismatch")
    if not record_status:
        blocked_reasons.append("delivery_result_status_missing")
    if not evidence["delivery_result_claimed"]:
        blocked_reasons.append("delivery_result_claim_missing")
    if not evidence["operator_confirmation_present"]:
        blocked_reasons.append("operator_confirmation_missing")
    if not evidence["dropoff_confirmation_type"]:
        blocked_reasons.append("dropoff_confirmation_type_missing")
    if completed_at_utc is None:
        blocked_reasons.append("completed_at_utc_missing_or_invalid")
    if not linked_nav2:
        blocked_reasons.append("linked_nav2_goal_execution_not_proven")
    next_required_evidence = []
    if not linked_nav2:
        next_required_evidence.append("linked_nav2_goal_execution_evidence")
    if not evidence["operator_confirmation_present"]:
        next_required_evidence.append("operator_dropoff_confirmation")
    if not evidence["dropoff_confirmation_type"]:
        next_required_evidence.append("dropoff_confirmation_type")
    if completed_at_utc is None:
        next_required_evidence.append("completed_at_utc_utc_text")
    next_required_evidence.append("same_task_delivery_record_review")
    evidence["blocked_reasons"] = sorted(set(blocked_reasons))
    evidence["next_required_evidence"] = sorted(set(next_required_evidence))
    if not evidence["blocked_reasons"]:
        evidence["status"] = "ready_not_delivery_proof"
    return evidence


def route_execution_result_delivery_readiness_blocked_summary(
    task_id: str,
    task_id_source: str,
    blocked_reasons: list[str],
    *,
    route_execution_result_status: str | None,
    route_execution_source: str | None,
    route_execution_result_ready: bool,
    delivery_result_readiness_status: str | None,
    delivery_result_source: str | None,
    delivery_result_readiness_ready: bool,
    operator_confirmation_readiness_status: str | None,
    operator_confirmation_source: str | None,
    operator_confirmation_readiness_ready: bool,
    linked_nav2_goal_execution_proven: bool,
    linked_delivery_result_claimed: bool,
    linked_operator_confirmation_present: bool,
    next_required_evidence: list[str],
) -> dict[str, Any]:
    # 结果链 readiness 必须稳定 fail-closed，哪怕下游只拿到部分 additive 也能安全回读。
    return {
        "schema": ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_SCHEMA,
        "proof_scope": ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_PROOF_SCOPE,
        "status": "blocked_not_proven",
        "source": "field_motion_evidence_packet",
        "task_id": task_id,
        "task_id_source": task_id_source,
        "route_execution_result_status": route_execution_result_status,
        "route_execution_source": route_execution_source,
        "route_execution_result_ready": route_execution_result_ready,
        "route_execution_success": False,
        "delivery_result_readiness_status": delivery_result_readiness_status,
        "delivery_result_source": delivery_result_source,
        "delivery_result_readiness_ready": delivery_result_readiness_ready,
        "operator_confirmation_readiness_status": operator_confirmation_readiness_status,
        "operator_confirmation_source": operator_confirmation_source,
        "operator_confirmation_readiness_ready": operator_confirmation_readiness_ready,
        "linked_nav2_goal_execution_proven": linked_nav2_goal_execution_proven,
        "linked_delivery_result_claimed": linked_delivery_result_claimed,
        "linked_operator_confirmation_present": linked_operator_confirmation_present,
        "blocked_reasons": sorted(set(reason for reason in blocked_reasons if reason)),
        "next_required_evidence": sorted(set(item for item in next_required_evidence if item)),
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
    }


def build_route_execution_result_delivery_readiness(packet: dict[str, Any]) -> dict[str, Any]:
    # 这里把 route execution、delivery result 和 operator confirmation 收束到同一 task_id 的保守摘要。
    task_id = str(packet.get("task_id") or "")
    task_id_source = str(packet.get("task_id_source") or "field_motion_evidence_packet")
    nav2_evidence = packet.get("nav2_goal_execution_evidence") if isinstance(packet.get("nav2_goal_execution_evidence"), dict) else {}
    delivery_evidence = packet.get("delivery_result_evidence") if isinstance(packet.get("delivery_result_evidence"), dict) else {}
    pose_progress = packet.get("route_bag_pose_progress_replay") if isinstance(packet.get("route_bag_pose_progress_replay"), dict) else {}
    route_bag_live = packet.get("route_bag_or_live_nav2_log") if isinstance(packet.get("route_bag_or_live_nav2_log"), dict) else {}

    linked_nav2_goal_execution_proven = bool(nav2_evidence.get("nav2_goal_execution_proven"))
    linked_delivery_result_claimed = bool(delivery_evidence.get("delivery_result_claimed"))
    linked_operator_confirmation_present = bool(delivery_evidence.get("operator_confirmation_present"))
    pose_progress_ready = pose_progress.get("status") == "ready_not_live_nav2_proof" and bool(pose_progress.get("nonzero_pose_progress_observed"))

    route_execution_result_ready = linked_nav2_goal_execution_proven and pose_progress_ready
    delivery_result_readiness_ready = delivery_evidence.get("status") == "ready_not_delivery_proof" and linked_delivery_result_claimed
    operator_confirmation_readiness_ready = delivery_evidence.get("status") == "ready_not_delivery_proof" and linked_operator_confirmation_present

    route_execution_source_parts = []
    if linked_nav2_goal_execution_proven:
        route_execution_source_parts.append("nav2_goal_execution_evidence")
    if pose_progress_ready:
        route_execution_source_parts.append("route_bag_pose_progress_replay")
    route_execution_source = "+".join(route_execution_source_parts) if route_execution_source_parts else "field_motion_evidence_packet"
    route_execution_result_status = "ready_not_delivery_proof" if route_execution_result_ready else "blocked_not_proven"
    delivery_result_source = "delivery_result_evidence"
    delivery_result_readiness_status = "ready_not_delivery_proof" if delivery_result_readiness_ready else "blocked_not_proven"
    operator_confirmation_source = "delivery_result_evidence"
    operator_confirmation_readiness_status = "ready_not_delivery_proof" if operator_confirmation_readiness_ready else "blocked_not_proven"

    blocked_reasons = []
    next_required_evidence = []
    if nav2_evidence.get("schema") != NAV2_GOAL_EXECUTION_EVIDENCE_SCHEMA:
        blocked_reasons.append("linked_nav2_goal_execution_evidence_schema_mismatch")
    if nav2_evidence.get("status") != "ready_not_delivery_proof":
        blocked_reasons.append("linked_nav2_goal_execution_evidence_not_ready")
        next_required_evidence.extend(nav2_evidence.get("next_required_evidence") or [])
    if not linked_nav2_goal_execution_proven:
        blocked_reasons.append("linked_nav2_goal_execution_not_proven")
        next_required_evidence.append("linked_nav2_goal_execution_evidence")
    if pose_progress.get("schema") != ROUTE_BAG_POSE_PROGRESS_REPLAY_SCHEMA:
        blocked_reasons.append("linked_route_bag_pose_progress_replay_schema_mismatch")
    if pose_progress.get("status") != "ready_not_live_nav2_proof":
        blocked_reasons.append("linked_route_bag_pose_progress_replay_not_ready")
        next_required_evidence.extend(pose_progress.get("next_required_evidence") or [])
    if not pose_progress_ready:
        blocked_reasons.append("route_execution_pose_progress_missing")
        next_required_evidence.append("linked_route_bag_pose_progress_replay")
    if route_bag_live.get("present") is not True:
        blocked_reasons.append("route_bag_or_live_nav2_log_missing")
    if delivery_evidence.get("schema") != DELIVERY_RESULT_EVIDENCE_SCHEMA:
        blocked_reasons.append("linked_delivery_result_evidence_schema_mismatch")
    if delivery_evidence.get("status") != "ready_not_delivery_proof":
        blocked_reasons.append("linked_delivery_result_evidence_not_ready")
        next_required_evidence.extend(delivery_evidence.get("next_required_evidence") or [])
    if not delivery_result_readiness_ready:
        blocked_reasons.append("delivery_result_readiness_not_ready")
        next_required_evidence.append("same_task_delivery_result_record")
    if not operator_confirmation_readiness_ready:
        blocked_reasons.append("operator_confirmation_readiness_not_ready")
        next_required_evidence.append("same_task_operator_confirmation")
    if linked_delivery_result_claimed and not route_execution_result_ready:
        blocked_reasons.append("delivery_result_claim_without_route_execution_readiness")
    if linked_operator_confirmation_present and not linked_delivery_result_claimed:
        blocked_reasons.append("operator_confirmation_present_without_delivery_result_claim")
    if (delivery_evidence.get("unsafe_field_count") or 0) > 0 or (delivery_evidence.get("unsafe_text_field_count") or 0) > 0:
        blocked_reasons.append("linked_delivery_result_evidence_unsafe")
    if delivery_evidence.get("dangerous_true_fields"):
        blocked_reasons.append("linked_delivery_result_evidence_dangerous_true_claim")
    if (nav2_evidence.get("unsafe_field_count") or 0) > 0 or (nav2_evidence.get("unsafe_text_field_count") or 0) > 0:
        blocked_reasons.append("linked_nav2_goal_execution_evidence_unsafe")
    if nav2_evidence.get("dangerous_true_fields"):
        blocked_reasons.append("linked_nav2_goal_execution_evidence_dangerous_true_claim")
    if delivery_evidence.get("completed_at_utc") is None:
        next_required_evidence.append("completed_at_utc_utc_text")

    if not blocked_reasons:
        return {
            "schema": ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_SCHEMA,
            "proof_scope": ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_PROOF_SCOPE,
            "status": "route_execution_result_delivery_readiness_ready_not_delivery_proof",
            "source": "field_motion_evidence_packet",
            "task_id": task_id,
            "task_id_source": task_id_source,
            "route_execution_result_status": route_execution_result_status,
            "route_execution_source": route_execution_source,
            "route_execution_result_ready": True,
            "route_execution_success": False,
            "delivery_result_readiness_status": delivery_result_readiness_status,
            "delivery_result_source": delivery_result_source,
            "delivery_result_readiness_ready": True,
            "operator_confirmation_readiness_status": operator_confirmation_readiness_status,
            "operator_confirmation_source": operator_confirmation_source,
            "operator_confirmation_readiness_ready": True,
            "linked_nav2_goal_execution_proven": True,
            "linked_delivery_result_claimed": True,
            "linked_operator_confirmation_present": True,
            "blocked_reasons": [],
            "next_required_evidence": ["real_route_execution_result_delivery_acceptance"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
        }
    return route_execution_result_delivery_readiness_blocked_summary(
        task_id,
        task_id_source,
        blocked_reasons,
        route_execution_result_status=route_execution_result_status,
        route_execution_source=route_execution_source,
        route_execution_result_ready=route_execution_result_ready,
        delivery_result_readiness_status=delivery_result_readiness_status,
        delivery_result_source=delivery_result_source,
        delivery_result_readiness_ready=delivery_result_readiness_ready,
        operator_confirmation_readiness_status=operator_confirmation_readiness_status,
        operator_confirmation_source=operator_confirmation_source,
        operator_confirmation_readiness_ready=operator_confirmation_readiness_ready,
        linked_nav2_goal_execution_proven=linked_nav2_goal_execution_proven,
        linked_delivery_result_claimed=linked_delivery_result_claimed,
        linked_operator_confirmation_present=linked_operator_confirmation_present,
        next_required_evidence=next_required_evidence,
    )


def summary_contains_unsafe_text(value: Any) -> bool:
    # closure packet 只允许消费安全摘要；一旦 linked summary 里混入路径、token 或凭证 URL，必须继续 fail-closed。
    if isinstance(value, dict):
        return any(summary_contains_unsafe_text(child) for child in value.values())
    if isinstance(value, list):
        return any(summary_contains_unsafe_text(child) for child in value)
    if isinstance(value, str):
        lowered = value.lower()
        if SUMMARY_UNSAFE_CREDENTIAL_URL_RE.search(value):
            return True
        return any(marker in lowered for marker in ("/root", "/users/", "token", "base64", "raw_payload", " raw ", "path="))
    return False


def summary_has_dangerous_true(summary: dict[str, Any]) -> bool:
    # linked additive 已经固定所有危险 true 为 false；这里再次兜底，防止上游 drift 被闭合包误收为 ready。
    return any(
        summary.get(field) is True
        for field in (
            "safe_to_control",
            "delivery_success",
            "primary_actions_enabled",
            "robot_control_executed",
            "route_execution_success",
        )
    )


def safe_summary_text(value: Any) -> str | None:
    # blocked 摘要只允许回显安全短文本；命中 unsafe marker 时直接抹掉，避免把上游泄漏继续带下去。
    if not isinstance(value, str):
        return None
    if summary_contains_unsafe_text(value):
        return None
    return value[:160]


def route_delivery_closure_packet_blocked_summary(
    task_id: str,
    task_id_source: str,
    *,
    closure_ready: bool,
    linked_nav2_goal_status: str | None,
    linked_delivery_result_status: str | None,
    linked_route_execution_result_status: str | None,
    linked_pose_progress_status: str | None,
    linked_route_execution_source: str | None,
    linked_nav2_goal_execution_proven: bool,
    linked_delivery_result_claimed: bool,
    linked_operator_confirmation_present: bool,
    linked_nonzero_pose_progress_observed: bool,
    linked_route_execution_result_ready: bool,
    linked_delivery_result_readiness_ready: bool,
    linked_operator_confirmation_readiness_ready: bool,
    blocked_reasons: list[str],
    next_required_evidence: list[str],
) -> dict[str, Any]:
    # closure blocked 摘要保持和其他 additive 同形，方便 O6/O7 只读消费且不把部分 ready 误报为闭合成功。
    return {
        "schema": ROUTE_DELIVERY_CLOSURE_PACKET_SCHEMA,
        "proof_scope": ROUTE_DELIVERY_CLOSURE_PACKET_PROOF_SCOPE,
        "status": "blocked_not_proven",
        "source": "field_motion_evidence_packet",
        "task_id": task_id,
        "task_id_source": task_id_source,
        "closure_ready": closure_ready,
        "linked_nav2_goal_status": linked_nav2_goal_status,
        "linked_delivery_result_status": linked_delivery_result_status,
        "linked_route_execution_result_status": linked_route_execution_result_status,
        "linked_pose_progress_status": linked_pose_progress_status,
        "linked_route_execution_source": linked_route_execution_source,
        "linked_nav2_goal_execution_proven": linked_nav2_goal_execution_proven,
        "linked_delivery_result_claimed": linked_delivery_result_claimed,
        "linked_operator_confirmation_present": linked_operator_confirmation_present,
        "linked_nonzero_pose_progress_observed": linked_nonzero_pose_progress_observed,
        "linked_route_execution_result_ready": linked_route_execution_result_ready,
        "linked_delivery_result_readiness_ready": linked_delivery_result_readiness_ready,
        "linked_operator_confirmation_readiness_ready": linked_operator_confirmation_readiness_ready,
        "blocked_reasons": sorted(set(reason for reason in blocked_reasons if reason)),
        "next_required_evidence": sorted(set(item for item in next_required_evidence if item)),
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "route_execution_success": False,
    }


def build_route_delivery_closure_packet(packet: dict[str, Any]) -> dict[str, Any]:
    # closure packet 只表达“同一 task_id 的软件证据闭合”，绝不表达真实送达成功或可控制。
    task_id = str(packet.get("task_id") or "")
    task_id_source = str(packet.get("task_id_source") or "field_motion_evidence_packet")
    nav2_evidence = packet.get("nav2_goal_execution_evidence") if isinstance(packet.get("nav2_goal_execution_evidence"), dict) else {}
    delivery_evidence = packet.get("delivery_result_evidence") if isinstance(packet.get("delivery_result_evidence"), dict) else {}
    readiness = (
        packet.get("route_execution_result_delivery_readiness")
        if isinstance(packet.get("route_execution_result_delivery_readiness"), dict)
        else {}
    )
    pose_progress = packet.get("route_bag_pose_progress_replay") if isinstance(packet.get("route_bag_pose_progress_replay"), dict) else {}
    linked_nav2_goal_execution_proven = bool(nav2_evidence.get("nav2_goal_execution_proven"))
    linked_delivery_result_claimed = bool(delivery_evidence.get("delivery_result_claimed"))
    linked_operator_confirmation_present = bool(delivery_evidence.get("operator_confirmation_present"))
    linked_nonzero_pose_progress_observed = bool(pose_progress.get("nonzero_pose_progress_observed"))
    linked_route_execution_result_ready = bool(readiness.get("route_execution_result_ready"))
    linked_delivery_result_readiness_ready = bool(readiness.get("delivery_result_readiness_ready"))
    linked_operator_confirmation_readiness_ready = bool(readiness.get("operator_confirmation_readiness_ready"))
    linked_ready_without_integrity_blockers = (
        readiness.get("status") == "route_execution_result_delivery_readiness_ready_not_delivery_proof"
        and linked_route_execution_result_ready
        and linked_delivery_result_readiness_ready
        and linked_operator_confirmation_readiness_ready
        and nav2_evidence.get("status") == "ready_not_delivery_proof"
        and linked_nav2_goal_execution_proven
        and delivery_evidence.get("status") == "ready_not_delivery_proof"
        and linked_delivery_result_claimed
        and linked_operator_confirmation_present
        and pose_progress.get("status") == "ready_not_live_nav2_proof"
        and linked_nonzero_pose_progress_observed
    )
    blocked_reasons: list[str] = []
    next_required_evidence: list[str] = []
    linked_specs = [
        (
            "nav2_goal_execution_evidence",
            nav2_evidence,
            NAV2_GOAL_EXECUTION_EVIDENCE_SCHEMA,
            "ready_not_delivery_proof",
            "linked_nav2_goal_execution_evidence",
        ),
        (
            "delivery_result_evidence",
            delivery_evidence,
            DELIVERY_RESULT_EVIDENCE_SCHEMA,
            "ready_not_delivery_proof",
            "linked_delivery_result_evidence",
        ),
        (
            "route_execution_result_delivery_readiness",
            readiness,
            ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_SCHEMA,
            "route_execution_result_delivery_readiness_ready_not_delivery_proof",
            "linked_route_execution_result_delivery_readiness",
        ),
        (
            "route_bag_pose_progress_replay",
            pose_progress,
            ROUTE_BAG_POSE_PROGRESS_REPLAY_SCHEMA,
            "ready_not_live_nav2_proof",
            "linked_route_bag_pose_progress_replay",
        ),
    ]
    for summary_name, summary, expected_schema, expected_status, next_evidence in linked_specs:
        if summary.get("schema") != expected_schema:
            blocked_reasons.append(f"{summary_name}_schema_mismatch")
        if summary.get("status") != expected_status:
            blocked_reasons.append(f"{summary_name}_not_ready")
            next_required_evidence.extend(summary.get("next_required_evidence") or [])
        if summary.get("task_id") != task_id:
            blocked_reasons.append(f"{summary_name}_task_id_mismatch")
        if summary_has_dangerous_true(summary):
            blocked_reasons.append(f"{summary_name}_dangerous_true_claim")
        if summary_contains_unsafe_text(summary):
            blocked_reasons.append(f"{summary_name}_unsafe_text")
        if (summary.get("unsafe_field_count") or 0) > 0 or (summary.get("unsafe_text_field_count") or 0) > 0:
            blocked_reasons.append(f"{summary_name}_unsafe_summary")
        if summary.get("dangerous_true_fields"):
            blocked_reasons.append(f"{summary_name}_dangerous_true_fields")
        next_required_evidence.append(next_evidence)
    if not linked_nav2_goal_execution_proven:
        blocked_reasons.append("linked_nav2_goal_execution_not_proven")
    if not linked_delivery_result_claimed:
        blocked_reasons.append("linked_delivery_result_claim_missing")
    if not linked_operator_confirmation_present:
        blocked_reasons.append("linked_operator_confirmation_missing")
    if not linked_nonzero_pose_progress_observed:
        blocked_reasons.append("linked_route_bag_pose_progress_missing")
    if not linked_route_execution_result_ready:
        blocked_reasons.append("linked_route_execution_result_not_ready")
    if not linked_delivery_result_readiness_ready:
        blocked_reasons.append("linked_delivery_result_readiness_not_ready")
    if not linked_operator_confirmation_readiness_ready:
        blocked_reasons.append("linked_operator_confirmation_readiness_not_ready")
    if not linked_ready_without_integrity_blockers:
        next_required_evidence.append("same_task_route_delivery_closure_inputs")
    if blocked_reasons:
        next_required_evidence.append("same_task_route_delivery_closure_inputs")
    if not blocked_reasons:
        return {
            "schema": ROUTE_DELIVERY_CLOSURE_PACKET_SCHEMA,
            "proof_scope": ROUTE_DELIVERY_CLOSURE_PACKET_PROOF_SCOPE,
            "status": "route_delivery_closure_ready_not_success_proof",
            "source": "field_motion_evidence_packet",
            "task_id": task_id,
            "task_id_source": task_id_source,
            "closure_ready": True,
            "linked_nav2_goal_status": "ready_not_delivery_proof",
            "linked_delivery_result_status": "ready_not_delivery_proof",
            "linked_route_execution_result_status": "route_execution_result_delivery_readiness_ready_not_delivery_proof",
            "linked_pose_progress_status": "ready_not_live_nav2_proof",
            "linked_route_execution_source": readiness.get("route_execution_source"),
            "linked_nav2_goal_execution_proven": True,
            "linked_delivery_result_claimed": True,
            "linked_operator_confirmation_present": True,
            "linked_nonzero_pose_progress_observed": True,
            "linked_route_execution_result_ready": True,
            "linked_delivery_result_readiness_ready": True,
            "linked_operator_confirmation_readiness_ready": True,
            "blocked_reasons": [],
            "next_required_evidence": ["real_route_delivery_success_proof"],
            "safe_to_control": False,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "robot_control_executed": False,
            "route_execution_success": False,
        }
    return route_delivery_closure_packet_blocked_summary(
        task_id,
        task_id_source,
        closure_ready=False,
        linked_nav2_goal_status=str(nav2_evidence.get("status") or "") or None,
        linked_delivery_result_status=str(delivery_evidence.get("status") or "") or None,
        linked_route_execution_result_status=str(readiness.get("status") or "") or None,
        linked_pose_progress_status=str(pose_progress.get("status") or "") or None,
        linked_route_execution_source=safe_summary_text(readiness.get("route_execution_source")),
        linked_nav2_goal_execution_proven=linked_nav2_goal_execution_proven,
        linked_delivery_result_claimed=linked_delivery_result_claimed,
        linked_operator_confirmation_present=linked_operator_confirmation_present,
        linked_nonzero_pose_progress_observed=linked_nonzero_pose_progress_observed,
        linked_route_execution_result_ready=linked_route_execution_result_ready,
        linked_delivery_result_readiness_ready=linked_delivery_result_readiness_ready,
        linked_operator_confirmation_readiness_ready=linked_operator_confirmation_readiness_ready,
        blocked_reasons=blocked_reasons,
        next_required_evidence=next_required_evidence,
    )


def same_task_mission_gate_terminal_refs(delivery_evidence: dict[str, Any]) -> dict[str, Any]:
    # gate 只回显 delivery_result_evidence 里已经脱敏过的短引用，绝不重新读取 cloud 原始 payload。
    return {
        "source": safe_summary_text(delivery_evidence.get("source")),
        "source_schema": safe_summary_text(delivery_evidence.get("source_schema")),
        "command_id_ref": safe_summary_text(delivery_evidence.get("command_id_ref")),
        "task_record_ref": safe_summary_text(delivery_evidence.get("task_record_ref")),
        "evidence_ref": safe_summary_text(delivery_evidence.get("evidence_ref")),
        "completed_at_utc": safe_summary_text(delivery_evidence.get("completed_at_utc")),
    }


def same_task_mission_gate_linked_flags(
    delivery_evidence: dict[str, Any],
    readiness: dict[str, Any],
    closure: dict[str, Any],
    pose_progress: dict[str, Any],
    *,
    same_task_id_matched: bool,
) -> dict[str, Any]:
    # flags 面向 O6/O7 展示，只表达 linked additive 是否满足 gate 条件，不把 ready 提升成成功证明。
    return {
        "same_task_id_matched": same_task_id_matched,
        "delivery_result_evidence_ready": delivery_evidence.get("status") == "ready_not_delivery_proof",
        "delivery_result_source": safe_summary_text(delivery_evidence.get("source")),
        "delivery_result_source_schema": safe_summary_text(delivery_evidence.get("source_schema")),
        "cloud_terminal_result_source_consumed": delivery_evidence.get("source_schema") == CLOUD_COMMAND_TERMINAL_RESULT_SCHEMA,
        "route_execution_result_delivery_readiness_ready": (
            readiness.get("status") == "route_execution_result_delivery_readiness_ready_not_delivery_proof"
        ),
        "route_execution_source": safe_summary_text(readiness.get("route_execution_source")),
        "route_delivery_closure_ready": closure.get("status") == "route_delivery_closure_ready_not_success_proof",
        "route_bag_pose_progress_ready": pose_progress.get("status") == "ready_not_live_nav2_proof",
        "nonzero_pose_progress_observed": bool(pose_progress.get("nonzero_pose_progress_observed")),
    }


def same_task_mission_gate_context_markers(packet: dict[str, Any]) -> list[str]:
    # support-only 分类只读取现成安全摘要字段，避免为判定 OKR credit 再引入 raw payload 依赖。
    route_bag_live = packet.get("route_bag_or_live_nav2_log") if isinstance(packet.get("route_bag_or_live_nav2_log"), dict) else {}
    motion_logs = packet.get("motion_log_summary") if isinstance(packet.get("motion_log_summary"), dict) else {}
    route_bag_evidence = packet.get("route_bag_evidence") if isinstance(packet.get("route_bag_evidence"), dict) else {}
    readiness = (
        packet.get("route_execution_result_delivery_readiness")
        if isinstance(packet.get("route_execution_result_delivery_readiness"), dict)
        else {}
    )
    delivery_evidence = packet.get("delivery_result_evidence") if isinstance(packet.get("delivery_result_evidence"), dict) else {}
    candidates = [
        route_bag_live.get("source"),
        route_bag_live.get("status"),
        route_bag_evidence.get("source_label"),
        route_bag_evidence.get("status"),
        readiness.get("route_execution_source"),
        readiness.get("source"),
        delivery_evidence.get("source"),
        delivery_evidence.get("source_schema"),
        motion_logs.get("path"),
    ]
    markers: list[str] = []
    for candidate in candidates:
        safe_text = safe_summary_text(candidate)
        if safe_text:
            markers.append(safe_text.lower())
    return markers


def same_task_mission_gate_live_or_field_command_executed(packet: dict[str, Any], linked_flags: dict[str, Any], *, ready: bool) -> bool:
    # 只有明确消费 live/field command 证据时才允许主 OKR credit；route/terminal readback ready 本身不够。
    if not ready or not bool(linked_flags.get("same_task_id_matched")):
        return False
    motion_logs = packet.get("motion_log_summary") if isinstance(packet.get("motion_log_summary"), dict) else {}
    route_bag_live = packet.get("route_bag_or_live_nav2_log") if isinstance(packet.get("route_bag_or_live_nav2_log"), dict) else {}
    if bool(motion_logs.get("live_motion_evidence_present")):
        return True
    if bool(motion_logs.get("live_nav2_log_present")):
        return True
    return str(route_bag_live.get("source") or "") == "live_motion_log"


def same_task_mission_gate_support_only_reason(
    packet: dict[str, Any],
    linked_flags: dict[str, Any],
    *,
    ready: bool,
    live_or_field_command_executed: bool,
) -> str | None:
    # support-only reason 需要给 Product/O6/O7 一个稳定合同，明确为什么这轮不能计入主 OKR 进度。
    if live_or_field_command_executed:
        return None
    if not bool(linked_flags.get("same_task_id_matched")):
        return "same_task_id_mismatch_or_missing"
    context_markers = same_task_mission_gate_context_markers(packet)
    if any("probe" in marker for marker in context_markers):
        return "probe_only_same_task_artifacts"
    if any("checklist" in marker for marker in context_markers):
        return "checklist_only_same_task_artifacts"
    if any("readback" in marker for marker in context_markers):
        return "readback_only_same_task_artifacts"
    if any(any(keyword in marker for keyword in ("local", "mock", "unit", "fixture")) for marker in context_markers):
        return "local_or_mock_same_task_artifacts_only"
    if not ready:
        return "same_task_mission_gate_not_ready"
    return "live_or_field_mission_artifact_delta_missing"


def same_task_mission_gate_artifact_delta(
    packet: dict[str, Any],
    linked_flags: dict[str, Any],
    *,
    ready: bool,
) -> dict[str, Any]:
    # mission delta 明确本轮消费了哪些同 task 任务材料，同时把 credit 判定和 support-only 原因固化成合同。
    live_or_field_command_executed = same_task_mission_gate_live_or_field_command_executed(packet, linked_flags, ready=ready)
    field_material_packet = (
        packet.get("same_task_field_material_packet")
        if isinstance(packet.get("same_task_field_material_packet"), dict)
        else {}
    )
    same_task_field_material_consumed = (
        ready
        and field_material_packet.get("schema") == SAME_TASK_FIELD_MATERIAL_PACKET_SCHEMA
        and field_material_packet.get("status") == "ready_not_delivery_proof"
        and field_material_packet.get("task_id") == packet.get("task_id")
        and not summary_has_dangerous_true(field_material_packet)
        and not summary_contains_unsafe_text(field_material_packet)
        and int(field_material_packet.get("unsafe_field_count") or 0) == 0
        and int(field_material_packet.get("unsafe_text_field_count") or 0) == 0
    )
    okr_credit_allowed = ready and bool(linked_flags.get("same_task_id_matched")) and live_or_field_command_executed
    support_only_reason = same_task_mission_gate_support_only_reason(
        packet,
        linked_flags,
        ready=ready,
        live_or_field_command_executed=live_or_field_command_executed,
    )
    return {
        "same_task_id_consumed": bool(linked_flags.get("same_task_id_matched")),
        "cloud_terminal_result_source_consumed": bool(linked_flags.get("cloud_terminal_result_source_consumed")),
        "route_execution_readiness_consumed": bool(linked_flags.get("route_execution_result_delivery_readiness_ready")),
        "route_delivery_closure_consumed": bool(linked_flags.get("route_delivery_closure_ready")),
        "nonzero_pose_progress_consumed": bool(linked_flags.get("nonzero_pose_progress_observed")),
        "same_task_field_material_consumed": same_task_field_material_consumed,
        "same_task_terminal_result_linked_to_route_execution": ready,
        "delivery_success_delta": False,
        "production_cloud_evidence_delta": False,
        "live_or_field_command_executed": live_or_field_command_executed,
        "support_only_reason": support_only_reason,
        "okr_credit_allowed": okr_credit_allowed,
        "mission_gate_status": "same_task_mission_gate_ready_not_success_proof" if ready else "blocked_not_proven",
    }


def build_same_task_mission_evidence_gate(packet: dict[str, Any]) -> dict[str, Any]:
    # same-task gate 是现有 additive 的只读合页，不新增 raw cloud/route payload 入口。
    task_id = str(packet.get("task_id") or "")
    task_id_source = str(packet.get("task_id_source") or "field_motion_evidence_packet")
    delivery_evidence = packet.get("delivery_result_evidence") if isinstance(packet.get("delivery_result_evidence"), dict) else {}
    readiness = (
        packet.get("route_execution_result_delivery_readiness")
        if isinstance(packet.get("route_execution_result_delivery_readiness"), dict)
        else {}
    )
    closure = packet.get("route_delivery_closure_packet") if isinstance(packet.get("route_delivery_closure_packet"), dict) else {}
    pose_progress = packet.get("route_bag_pose_progress_replay") if isinstance(packet.get("route_bag_pose_progress_replay"), dict) else {}
    linked_specs = [
        (
            "delivery_result_evidence",
            delivery_evidence,
            DELIVERY_RESULT_EVIDENCE_SCHEMA,
            DELIVERY_RESULT_EVIDENCE_PROOF_SCOPE,
            "ready_not_delivery_proof",
            "linked_delivery_result_evidence",
        ),
        (
            "route_execution_result_delivery_readiness",
            readiness,
            ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_SCHEMA,
            ROUTE_EXECUTION_RESULT_DELIVERY_READINESS_PROOF_SCOPE,
            "route_execution_result_delivery_readiness_ready_not_delivery_proof",
            "linked_route_execution_result_delivery_readiness",
        ),
        (
            "route_delivery_closure_packet",
            closure,
            ROUTE_DELIVERY_CLOSURE_PACKET_SCHEMA,
            ROUTE_DELIVERY_CLOSURE_PACKET_PROOF_SCOPE,
            "route_delivery_closure_ready_not_success_proof",
            "linked_route_delivery_closure_packet",
        ),
        (
            "route_bag_pose_progress_replay",
            pose_progress,
            ROUTE_BAG_POSE_PROGRESS_REPLAY_SCHEMA,
            ROUTE_BAG_POSE_PROGRESS_REPLAY_PROOF_SCOPE,
            "ready_not_live_nav2_proof",
            "linked_route_bag_pose_progress_replay",
        ),
    ]
    blocked_reasons: list[str] = []
    next_required_evidence: list[str] = []
    same_task_id_matched = True
    for summary_name, summary, expected_schema, expected_proof_scope, expected_status, next_evidence in linked_specs:
        if summary.get("schema") != expected_schema:
            blocked_reasons.append(f"{summary_name}_schema_mismatch")
        if summary.get("proof_scope") != expected_proof_scope:
            blocked_reasons.append(f"{summary_name}_proof_scope_mismatch")
        if summary.get("status") != expected_status:
            blocked_reasons.append(f"{summary_name}_not_ready")
            next_required_evidence.extend(summary.get("next_required_evidence") or [])
        if summary.get("task_id") != task_id:
            same_task_id_matched = False
            blocked_reasons.append(f"{summary_name}_task_id_mismatch")
        if summary_has_dangerous_true(summary) or summary.get("dangerous_true_fields"):
            blocked_reasons.append(f"{summary_name}_dangerous_true_claim")
        if summary_contains_unsafe_text(summary):
            blocked_reasons.append(f"{summary_name}_unsafe_text")
        if (summary.get("unsafe_field_count") or 0) > 0 or (summary.get("unsafe_text_field_count") or 0) > 0:
            blocked_reasons.append(f"{summary_name}_unsafe_summary")
        next_required_evidence.append(next_evidence)
    if delivery_evidence.get("source_schema") != CLOUD_COMMAND_TERMINAL_RESULT_SCHEMA:
        blocked_reasons.append("delivery_result_evidence_source_schema_mismatch")
        next_required_evidence.append("same_task_cloud_terminal_result_source")
    if not bool(pose_progress.get("nonzero_pose_progress_observed")):
        blocked_reasons.append("route_bag_pose_progress_nonzero_missing")
        next_required_evidence.append("nonzero_route_bag_pose_progress_replay")
    if not same_task_id_matched:
        next_required_evidence.append("same_task_terminal_route_delivery_task_id_alignment")
    ready = not blocked_reasons
    linked_flags = same_task_mission_gate_linked_flags(
        delivery_evidence,
        readiness,
        closure,
        pose_progress,
        same_task_id_matched=same_task_id_matched,
    )
    mission_artifact_delta = same_task_mission_gate_artifact_delta(packet, linked_flags, ready=ready)
    return {
        "schema": SAME_TASK_MISSION_EVIDENCE_GATE_SCHEMA,
        "proof_scope": SAME_TASK_MISSION_EVIDENCE_GATE_PROOF_SCOPE,
        "status": "same_task_mission_gate_ready_not_success_proof" if ready else "blocked_not_proven",
        "source": "field_motion_evidence_packet.linked_additive_summaries",
        "task_id": task_id,
        "task_id_source": task_id_source,
        "same_task_mission_gate_ready": ready,
        "terminal_refs": same_task_mission_gate_terminal_refs(delivery_evidence),
        "linked_readiness_flags": linked_flags,
        "same_task_id_consumed": mission_artifact_delta["same_task_id_consumed"],
        "live_or_field_command_executed": mission_artifact_delta["live_or_field_command_executed"],
        "support_only_reason": mission_artifact_delta["support_only_reason"],
        "okr_credit_allowed": mission_artifact_delta["okr_credit_allowed"],
        "mission_artifact_delta": mission_artifact_delta,
        "blocked_reasons": sorted(set(reason for reason in blocked_reasons if reason)),
        "next_required_evidence": (
            ["real_same_task_mission_success_proof", "production_cloud_or_live_route_execution_acceptance"]
            if ready
            else sorted(set(item for item in next_required_evidence if item))
        ),
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "route_execution_success": False,
    }


def route_bag_blocked_summary(
    task_id: str,
    task_id_source: str,
    source_label: str | None,
    blocked_reasons: list[str],
    *,
    metadata_summary: dict[str, Any] | None = None,
    db3_basename: str | None = None,
    db3_present: bool = False,
    db3_read_ok: bool = False,
    sqlite_schema_ok: bool = False,
    db3_size_bytes: int = 0,
    db3_sha256_prefix: str | None = None,
    topic_count: int = 0,
    message_count: int = 0,
    timestamp_first_ns: int | None = None,
    timestamp_last_ns: int | None = None,
    sample_topic_names: list[str] | None = None,
    dangerous_true_fields: list[str] | None = None,
    unsafe_field_count: int = 0,
    unsafe_text_field_count: int = 0,
) -> dict[str, Any]:
    # 同形 blocked 摘要让 O6/O7 可以稳定展示缺口，同时不回显 DB3 绝对路径或 payload。
    metadata = metadata_summary or route_bag_metadata_absent_summary()
    return {
        "schema": ROUTE_BAG_EVIDENCE_SCHEMA,
        "proof_scope": ROUTE_BAG_EVIDENCE_PROOF_SCOPE,
        "source": "route_bag_db3_sqlite_summary",
        "source_label": source_label,
        "status": "blocked_not_proven",
        "task_id": task_id,
        "task_id_source": task_id_source,
        "metadata_present": bool(metadata.get("metadata_present")),
        "metadata_read_ok": bool(metadata.get("metadata_read_ok")),
        "metadata_basename": metadata.get("metadata_basename"),
        "metadata_size_bytes": int(metadata.get("metadata_size_bytes") or 0),
        "metadata_sha256_prefix": metadata.get("metadata_sha256_prefix"),
        "db3_present": db3_present,
        "db3_read_ok": db3_read_ok,
        "sqlite_schema_ok": sqlite_schema_ok,
        "db3_basename": db3_basename,
        "db3_size_bytes": db3_size_bytes,
        "db3_sha256_prefix": db3_sha256_prefix,
        "topic_count": topic_count,
        "message_count": message_count,
        "timestamp_first_ns": timestamp_first_ns,
        "timestamp_last_ns": timestamp_last_ns,
        "sample_topic_names": sample_topic_names or [],
        "blocked_reasons": sorted(set(reason for reason in blocked_reasons if reason)),
        "dangerous_true_fields": sorted(set(dangerous_true_fields or [])),
        "unsafe_field_count": int(unsafe_field_count),
        "unsafe_text_field_count": int(unsafe_text_field_count),
        "next_required_evidence": [
            "safe_route_bag_db3_with_topics_and_messages",
            "same_task_route_bag_metadata_yaml",
            "live_nav2_pose_progress_or_route_execution_log",
            "delivery_record_or_operator_dropoff_confirmation",
        ],
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "live_nav2_run_proven": False,
        "route_execution_success": False,
        "connects_cloud_production": False,
    }


def route_bag_payload_replay_absent_summary() -> dict[str, Any]:
    # payload replay 的 absent 状态必须显式保留，避免 O6/O7 把缺输入误读成 ready。
    return {
        "payload_sample_count": 0,
        "payload_size_min_bytes": 0,
        "payload_size_max_bytes": 0,
        "payload_size_avg_bytes": 0.0,
        "payload_sha256_prefix_samples": [],
    }


def route_bag_payload_replay_blocked_summary(
    task_id: str,
    task_id_source: str,
    source_label: str | None,
    blocked_reasons: list[str],
    *,
    metadata_summary: dict[str, Any] | None = None,
    db3_basename: str | None = None,
    db3_present: bool = False,
    db3_read_ok: bool = False,
    sqlite_schema_ok: bool = False,
    db3_size_bytes: int = 0,
    db3_sha256_prefix: str | None = None,
    topic_count: int = 0,
    message_count: int = 0,
    timestamp_first_ns: int | None = None,
    timestamp_last_ns: int | None = None,
    sample_topic_names: list[str] | None = None,
    payload_sample_count: int = 0,
    payload_size_min_bytes: int = 0,
    payload_size_max_bytes: int = 0,
    payload_size_avg_bytes: float = 0.0,
    payload_sha256_prefix_samples: list[str] | None = None,
    dangerous_true_fields: list[str] | None = None,
    unsafe_field_count: int = 0,
    unsafe_text_field_count: int = 0,
) -> dict[str, Any]:
    # 同形 blocked 摘要让 payload replay 的缺口和 ready 形状一致，但不会暴露 raw payload。
    metadata = metadata_summary or route_bag_metadata_absent_summary()
    return {
        "schema": ROUTE_BAG_PAYLOAD_REPLAY_SCHEMA,
        "proof_scope": ROUTE_BAG_PAYLOAD_REPLAY_PROOF_SCOPE,
        "source": "route_bag_db3_payload_replay",
        "source_label": source_label,
        "status": "blocked_not_proven",
        "task_id": task_id,
        "task_id_source": task_id_source,
        "metadata_present": bool(metadata.get("metadata_present")),
        "metadata_read_ok": bool(metadata.get("metadata_read_ok")),
        "metadata_basename": metadata.get("metadata_basename"),
        "metadata_size_bytes": int(metadata.get("metadata_size_bytes") or 0),
        "metadata_sha256_prefix": metadata.get("metadata_sha256_prefix"),
        "db3_present": db3_present,
        "db3_read_ok": db3_read_ok,
        "sqlite_schema_ok": sqlite_schema_ok,
        "db3_basename": db3_basename,
        "db3_size_bytes": db3_size_bytes,
        "db3_sha256_prefix": db3_sha256_prefix,
        "topic_count": topic_count,
        "message_count": message_count,
        "timestamp_first_ns": timestamp_first_ns,
        "timestamp_last_ns": timestamp_last_ns,
        "sample_topic_names": sample_topic_names or [],
        "payload_sample_count": payload_sample_count,
        "payload_size_min_bytes": payload_size_min_bytes,
        "payload_size_max_bytes": payload_size_max_bytes,
        "payload_size_avg_bytes": payload_size_avg_bytes,
        "payload_sha256_prefix_samples": payload_sha256_prefix_samples or [],
        "blocked_reasons": sorted(set(reason for reason in blocked_reasons if reason)),
        "dangerous_true_fields": sorted(set(dangerous_true_fields or [])),
        "unsafe_field_count": int(unsafe_field_count),
        "unsafe_text_field_count": int(unsafe_text_field_count),
        "next_required_evidence": [
            "safe_route_bag_payload_replay_db3_with_nonempty_payloads",
            "same_task_route_bag_metadata_yaml",
            "live_nav2_pose_progress_or_route_execution_log",
            "delivery_record_or_operator_dropoff_confirmation",
        ],
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "live_nav2_run_proven": False,
        "route_execution_success": False,
        "connects_cloud_production": False,
    }


def route_bag_metadata_absent_summary() -> dict[str, Any]:
    # metadata 是增强输入；未显式提供时不阻断 DB3 摘要，但必须显式写出 absent 状态。
    return {
        "metadata_present": False,
        "metadata_read_ok": False,
        "metadata_basename": None,
        "metadata_size_bytes": 0,
        "metadata_sha256_prefix": None,
        "blocked_reasons": [],
        "dangerous_true_fields": [],
        "unsafe_text_field_count": 0,
    }


def route_bag_short_hash(path: Path) -> str:
    # DB3 可能比普通 JSON 大，复用分块 sha256 后只输出短前缀，避免 manifest 变成长 artifact 索引。
    return sha256_file(path)[:16]


class CdrReader:
    """小规模 CDR 只读器，用于白名单语义消息解码，目标是统计而非重建消息对象。"""

    def __init__(self, payload: bytes, *, little_endian: bool = True):
        self.payload = payload
        self.little_endian = little_endian
        self.offset = 0

    def _endian(self) -> str:
        return "<" if self.little_endian else ">"

    def align(self, alignment: int) -> None:
        # CDR 的对齐要求必须先对齐再读取字段，否则长度会错位，进而触发解析失败。
        if alignment <= 1:
            return
        pad = (alignment - (self.offset % alignment)) % alignment
        self.offset += pad

    def _read(self, fmt: str, size: int) -> tuple[int, Any]:
        # 统一在每次读取前做边界保护，失败时抛 ValueError 触发 fail-closed。
        if self.offset + size > len(self.payload):
            raise ValueError("cdr_buffer_underrun")
        raw = self.payload[self.offset : self.offset + size]
        self.offset += size
        value = struct.unpack(self._endian() + fmt, raw)[0]
        return self.offset, value

    def read_u8(self) -> int:
        self.align(1)
        _, value = self._read("B", 1)
        return int(value)

    def read_u32(self) -> int:
        self.align(4)
        _, value = self._read("I", 4)
        return int(value)

    def read_u64(self) -> int:
        self.align(8)
        _, value = self._read("Q", 8)
        return int(value)

    def read_float32(self) -> float:
        self.align(4)
        _, value = self._read("f", 4)
        return float(value)

    def read_float64(self) -> float:
        self.align(8)
        _, value = self._read("d", 8)
        return float(value)

    def read_bytes(self, size: int) -> bytes:
        self.align(1)
        if size < 0 or self.offset + size > len(self.payload):
            raise ValueError("cdr_buffer_underrun")
        start = self.offset
        self.offset += size
        return self.payload[start:self.offset]

    def read_string(self) -> str:
        # CDR string 为先长度再 UTF-8 字节，长度包含结尾空字符；这里忽略尾 0 仅做去空格处理。
        length = self.read_u32()
        if length <= 0:
            return ""
        text = self.read_bytes(length)
        return text[:-1].decode("utf-8", errors="replace").strip() if text.endswith(b"\x00") else text.decode("utf-8", errors="replace").strip()

    def skip_u8(self, count: int) -> None:
        if count <= 0:
            return
        self.align(1)
        if self.offset + count > len(self.payload):
            raise ValueError("cdr_buffer_underrun")
        self.offset += count


def cdr_reader_variants(payload: bytes) -> list[CdrReader]:
    # strict 与 permissive 两套读取器都尝试一遍：优先完整 CDR 对齐语义，失败后回退到无对齐模式。
    prepared_payload = decode_cdr_payload(payload)
    strict = CdrReader(prepared_payload, little_endian=True)
    permissive = CdrReader(prepared_payload, little_endian=True)

    # permissive 仅在局部 payload 样本结构缺少标准对齐时开启，优先级低于 strict。
    def _no_align(_: int) -> None:
        return None

    permissive.align = _no_align  # type: ignore[attr-defined]
    return [strict, permissive]


def decode_cdr_payload(payload: bytes) -> bytes:
    # rosbag CDR 一般不带封装头，但也要能处理带头的样本，不然后续 decode 会误把封装头当字段。
    # 小端 CDR 封装头常见为 0x00 0x01 0x00 0x00；避免误删正常 payload（比如首字段也可能为 1）。
    if len(payload) >= 4 and payload[:4] == b"\x00\x01\x00\x00":
        return payload[4:]
    return payload


def decode_laserscan_payload(payload: bytes) -> dict[str, Any]:
    # LaserScan 摘要只提 range 统计和角度采样元数据，不泄露每一帧原始 range 内容。
    for reader in cdr_reader_variants(payload):
        try:
            reader.read_u32()
            reader.read_u32()
            reader.read_u32()
            _ = reader.read_string()
            angle_min = reader.read_float32()
            angle_max = reader.read_float32()
            angle_increment = reader.read_float32()
            reader.read_float32()
            reader.read_float32()
            range_min = reader.read_float32()
            range_max = reader.read_float32()
            range_count = reader.read_u32()
            finite_range_count = 0
            finite_range_min = None
            finite_range_max = None
            for _ in range(range_count):
                value = reader.read_float32()
                if math.isfinite(value):
                    finite_range_count += 1
                    finite_range_min = value if finite_range_min is None else min(finite_range_min, value)
                    finite_range_max = value if finite_range_max is None else max(finite_range_max, value)
            # intensity 维度不用于本轮摘要，直接按长度跳过。
            intensity_count = reader.read_u32()
            reader.skip_u8(4 * int(intensity_count))
            return {
                "angle_min": angle_min,
                "angle_max": angle_max,
                "angle_increment": angle_increment,
                "range_min": range_min,
                "range_max": range_max,
                "range_sample_count": range_count,
                "finite_range_count": finite_range_count,
                "finite_range_min": finite_range_min,
                "finite_range_max": finite_range_max,
                "intensity_count": intensity_count,
            }
        except Exception:
            continue
    raise ValueError("cdr_buffer_underrun")


def decode_image_payload(payload: bytes) -> dict[str, Any]:
    # Image 摘要只保留尺寸/编码/步长和 data 大小，避免把原始像素 bytes 变成 manifest 内容。
    for reader in cdr_reader_variants(payload):
        try:
            reader.read_u32()
            reader.read_u32()
            reader.read_u32()
            _ = reader.read_string()
            width = reader.read_u32()
            height = reader.read_u32()
            encoding = reader.read_string()
            _ = reader.read_u8()
            step = reader.read_u32()
            # permissive 变体可能没做 4 字节对齐，故这里不额外强加对齐前提，避免把合法样本误判为失败。
            data_size = reader.read_u32()
            if data_size < 0:
                raise ValueError("negative_image_data_size")
            reader.skip_u8(data_size)
            return {
                "width": width,
                "height": height,
                "encoding": encoding,
                "step": step,
                "data_size": data_size,
            }
        except Exception:
            continue
    raise ValueError("cdr_buffer_underrun")


def _safe_frame_id(value: str) -> str | None:
    # frame id 里只能保留结构化坐标名，避免把 token、路径文本或 raw 字符串带到 manifest。
    text = value.strip()
    if not text:
        return None
    if len(text) > 64:
        return None
    lowered = text.lower()
    if any(marker in lowered for marker in ("/users/", "/root/", "token", "credential", "base64", "raw_payload", "path=")):
        return None
    if ROUTE_BAG_CREDENTIAL_URL_RE.search(text):
        return None
    if not re.fullmatch(r"[A-Za-z0-9_:/+\-.]+", text):
        return None
    return text


def _cdr_read_string_bytes(reader: CdrReader, max_bytes: int) -> bytes:
    # DiagnosticArray 会携带自由文本；先按长度做上限保护，再决定是否解码或仅跳过。
    length = reader.read_u32()
    if length <= 0:
        return b""
    if length > max_bytes:
        raise ValueError("cdr_string_too_large")
    return reader.read_bytes(length)


def _cdr_skip_string(reader: CdrReader, max_bytes: int = DIAGNOSTIC_ARRAY_MAX_STRING_BYTES) -> None:
    # message/key/value 可能包含路径、token 或现场原文，只推进 offset，不把内容放进 Python 字符串。
    length = reader.read_u32()
    if length <= 0:
        return
    if length > max_bytes:
        raise ValueError("cdr_string_too_large")
    reader.skip_u8(length)


def _safe_diagnostic_sample_text(value: str) -> str | None:
    # name/hardware_id 只允许短标识符样本；正文、路径、URL、traceback 和 secret 直接丢弃。
    text = value.strip()
    if not text or len(text) > DIAGNOSTIC_ARRAY_SAMPLE_TEXT_MAX_CHARS:
        return None
    lowered = text.lower()
    unsafe_markers = (
        "token",
        "credential",
        "secret",
        "base64",
        "raw",
        "traceback",
        "exception",
        "password",
        "http://",
        "https://",
        "/users/",
        "/root/",
        "/tmp/",
        "path=",
    )
    if any(marker in lowered for marker in unsafe_markers):
        return None
    if "\\" in text or text.startswith("/"):
        return None
    if ROUTE_BAG_CREDENTIAL_URL_RE.search(text):
        return None
    if not re.fullmatch(r"[A-Za-z0-9_.:+ -]+", text):
        return None
    return text


def _cdr_read_diagnostic_sample_text(reader: CdrReader) -> str | None:
    # 样本文本必须先经过安全过滤；不合规文本不会让 decoder 失败，只是不进入摘要。
    raw = _cdr_read_string_bytes(reader, DIAGNOSTIC_ARRAY_MAX_STRING_BYTES)
    if not raw:
        return None
    text_bytes = raw[:-1] if raw.endswith(b"\x00") else raw
    decoded = text_bytes.decode("utf-8", errors="replace")
    return _safe_diagnostic_sample_text(decoded)


def _append_unique_limited_sample(samples: list[str], value: str | None) -> None:
    # samples 面向 UI/报告，只保留少量去重短样本，避免长数组成为隐式原始数据通道。
    if value and value not in samples and len(samples) < DIAGNOSTIC_ARRAY_STATUS_SAMPLE_LIMIT:
        samples.append(value)


def decode_tf_message_payload(payload: bytes) -> dict[str, Any]:
    # TFMessage summary 聚焦 transforms 数量和 frame 采样，不读取完整位姿链路。
    for reader in cdr_reader_variants(payload):
        try:
            reader.read_u32()
            reader.read_u32()
            reader.read_u32()
            _ = reader.read_string()
            transform_count = reader.read_u32()
            frame_pairs: list[tuple[str, str]] = []
            for _ in range(int(transform_count)):
                # TransformStamped.header
                reader.read_u32()
                reader.read_u32()
                reader.read_u32()
                parent_frame_id = _safe_frame_id(reader.read_string())
                child_frame_id = _safe_frame_id(reader.read_string())
                # permissive 样本里 transform 区段可能跳过了标准对齐；先尝试 strict，再允许 no-align 作为后备。
                try:
                    _ = reader.read_float64()
                    _ = reader.read_float64()
                    _ = reader.read_float64()
                    _ = reader.read_float64()
                    _ = reader.read_float64()
                    _ = reader.read_float64()
                    _ = reader.read_float64()
                except ValueError:
                    # permissive reader 已禁用 align，这里只做一次整体回退，由上层循环重新切换 reader。
                    raise
                frame_pairs.append((parent_frame_id or "", child_frame_id or ""))
            return {"transform_count": int(transform_count), "frame_pairs": frame_pairs[:3]}
        except Exception:
            continue
    raise ValueError("cdr_buffer_underrun")


def decode_route_bag_pose_progress_tf_payload(payload: bytes) -> list[dict[str, Any]]:
    # 只读 TFMessage 位姿摘要时，必须把每个 transform 的平移和 frame pair 都筛成安全样本。
    for reader in cdr_reader_variants(payload):
        try:
            reader.read_u32()
            reader.read_u32()
            reader.read_u32()
            _ = reader.read_string()
            transform_count = reader.read_u32()
            samples: list[dict[str, Any]] = []
            for _ in range(int(transform_count)):
                # TransformStamped.header
                reader.read_u32()
                reader.read_u32()
                reader.read_u32()
                parent_frame_id = _safe_frame_id(reader.read_string())
                child_frame_id = _safe_frame_id(reader.read_string())
                if not parent_frame_id or not child_frame_id:
                    raise ValueError("unsafe_tf_frame_id")
                x_m = reader.read_float64()
                y_m = reader.read_float64()
                z_m = reader.read_float64()
                reader.read_float64()
                reader.read_float64()
                reader.read_float64()
                reader.read_float64()
                if not all(math.isfinite(value) for value in (x_m, y_m, z_m)):
                    raise ValueError("non_finite_tf_translation")
                samples.append(
                    {
                        "frame_id": parent_frame_id,
                        "child_frame_id": child_frame_id,
                        "x_m": x_m,
                        "y_m": y_m,
                        "z_m": z_m,
                    }
                )
            if not samples:
                raise ValueError("empty_tf_pose_progress")
            return samples
        except Exception:
            continue
    raise ValueError("cdr_buffer_underrun")


def decode_route_bag_pose_progress_odom_payload(payload: bytes) -> list[dict[str, Any]]:
    # Odometry 只读位姿与 frame pair；covariance 和 twist 不进入摘要，避免把控制信息带出。
    for reader in cdr_reader_variants(payload):
        try:
            reader.read_u32()
            reader.read_u32()
            reader.read_u32()
            frame_id = _safe_frame_id(reader.read_string())
            child_frame_id = _safe_frame_id(reader.read_string())
            if not frame_id or not child_frame_id:
                raise ValueError("unsafe_odom_frame_id")
            x_m = reader.read_float64()
            y_m = reader.read_float64()
            z_m = reader.read_float64()
            reader.read_float64()
            reader.read_float64()
            reader.read_float64()
            reader.read_float64()
            if not all(math.isfinite(value) for value in (x_m, y_m, z_m)):
                raise ValueError("non_finite_odom_translation")
            return [
                {
                    "frame_id": frame_id,
                    "child_frame_id": child_frame_id,
                    "x_m": x_m,
                    "y_m": y_m,
                    "z_m": z_m,
                }
            ]
        except Exception:
            continue
    raise ValueError("cdr_buffer_underrun")


def decode_route_bag_pose_progress_message(topic_type: str, payload: bytes) -> list[dict[str, Any]]:
    # 只对白名单位姿消息做有限 CDR 解码；任何未知类型都视作失败，而不是“跳过即成功”。
    if topic_type == "tf2_msgs/msg/TFMessage":
        return decode_route_bag_pose_progress_tf_payload(payload)
    if topic_type == "nav_msgs/msg/Odometry":
        return decode_route_bag_pose_progress_odom_payload(payload)
    raise ValueError("unsupported_pose_progress_type")


def decode_odometry_payload(payload: bytes) -> dict[str, Any]:
    # semantic replay 复用已验证的位姿解析，只输出 frame pair 与平移摘要，避免扩散 twist/covariance。
    samples = decode_route_bag_pose_progress_odom_payload(payload)
    sample = samples[0] if samples else None
    if not sample:
        raise ValueError("empty_odometry_sample")
    translation_norm_m = round(
        math.sqrt(
            float(sample["x_m"]) * float(sample["x_m"])
            + float(sample["y_m"]) * float(sample["y_m"])
            + float(sample["z_m"]) * float(sample["z_m"])
        ),
        6,
    )
    return {
        "frame_id": str(sample["frame_id"]),
        "child_frame_id": str(sample["child_frame_id"]),
        "x_m": round(float(sample["x_m"]), 6),
        "y_m": round(float(sample["y_m"]), 6),
        "z_m": round(float(sample["z_m"]), 6),
        "translation_norm_m": translation_norm_m,
        "nonzero_translation_observed": translation_norm_m > 1e-6,
    }


def decode_diagnostic_array_payload(payload: bytes) -> dict[str, Any]:
    # DiagnosticArray 只输出健康状态计数和短标识符样本，不输出 message、key、value 或原始 payload。
    for reader in cdr_reader_variants(payload):
        try:
            reader.read_u32()
            reader.read_u32()
            reader.read_u32()
            _cdr_skip_string(reader)
            status_count = reader.read_u32()
            if status_count > DIAGNOSTIC_ARRAY_MAX_STATUS_COUNT:
                raise ValueError("diagnostic_status_count_too_large")
            highest_level: int | None = None
            level_counts: dict[int, int] = {}
            status_name_samples: list[str] = []
            hardware_id_samples: list[str] = []
            key_value_pair_count = 0
            for _ in range(int(status_count)):
                level = reader.read_u8()
                highest_level = level if highest_level is None else max(highest_level, level)
                level_counts[level] = int(level_counts.get(level, 0)) + 1
                _append_unique_limited_sample(status_name_samples, _cdr_read_diagnostic_sample_text(reader))
                _cdr_skip_string(reader)
                _append_unique_limited_sample(hardware_id_samples, _cdr_read_diagnostic_sample_text(reader))
                value_count = reader.read_u32()
                if value_count > DIAGNOSTIC_ARRAY_MAX_KEY_VALUE_COUNT:
                    raise ValueError("diagnostic_key_value_count_too_large")
                key_value_pair_count += int(value_count)
                for _ in range(int(value_count)):
                    _cdr_skip_string(reader)
                    _cdr_skip_string(reader)
            return {
                "status_count": int(status_count),
                "highest_level": highest_level,
                "level_distribution": {str(level): level_counts[level] for level in sorted(level_counts)},
                "status_name_samples": status_name_samples,
                "hardware_id_samples": hardware_id_samples,
                "key_value_pair_count": key_value_pair_count,
            }
        except Exception:
            continue
    raise ValueError("cdr_buffer_underrun")


def decode_semantic_message(topic_type: str, payload: bytes) -> tuple[str, dict[str, Any]]:
    # 路由到白名单解码器，命中错误或未知 schema 都返回 failed。
    if topic_type == "sensor_msgs/msg/LaserScan":
        return "laser_scan", decode_laserscan_payload(payload)
    if topic_type == "sensor_msgs/msg/Image":
        return "image", decode_image_payload(payload)
    if topic_type == "tf2_msgs/msg/TFMessage":
        return "tf_message", decode_tf_message_payload(payload)
    if topic_type == "nav_msgs/msg/Odometry":
        return "odometry", decode_odometry_payload(payload)
    if topic_type == "diagnostic_msgs/msg/DiagnosticArray":
        return "diagnostic_array", decode_diagnostic_array_payload(payload)
    raise ValueError("unsupported_semantic_type")


def _semantic_empty_summary() -> dict[str, Any]:
    # 空语义摘要先固定完整字段集，确保 consumer 不会在 blocked/ready 之间遇到 schema 形状变化。
    return {
        "sample_count": 0,
        "range_sample_count": 0,
        "finite_range_count": 0,
        "finite_range_min": None,
        "finite_range_max": None,
        "angle_min": None,
        "angle_max": None,
        "angle_increment": None,
        "range_min": None,
        "range_max": None,
        "intensity_count": 0,
        "image_sample_count": 0,
        "width_min": None,
        "width_max": None,
        "height_min": None,
        "height_max": None,
        "step_min": None,
        "step_max": None,
        "data_size_min": None,
        "data_size_max": None,
        "data_size_total": 0,
        "encodings": [],
        "tf_sample_count": 0,
        "transform_count_total": 0,
        "frame_pairs": [],
    }


def _odometry_semantic_empty_summary() -> dict[str, Any]:
    # Odometry 语义层只保留 frame pair 与平移聚合，避免把控制相关字段透传给 O6/O7。
    return {
        "sample_count": 0,
        "nonzero_translation_sample_count": 0,
        "translation_norm_min": None,
        "translation_norm_max": None,
        "frame_pairs": [],
        "start_translation": None,
        "end_translation": None,
    }


def _diagnostic_array_semantic_empty_summary() -> dict[str, Any]:
    # DiagnosticArray 摘要固定为计数与短样本，不承载原始 status message 或 key/value 内容。
    return {
        "sample_count": 0,
        "status_count": 0,
        "highest_level": None,
        "level_distribution": {},
        "status_name_samples": [],
        "hardware_id_samples": [],
        "key_value_pair_count": 0,
    }


def _semantic_update_laser_scan_summary(summary: dict[str, Any], value: dict[str, Any]) -> None:
    # LaserScan 聚合不回放每帧原始 range，只做 min/max/count，便于 O6/O7 判定语义提取是否完整。
    summary["sample_count"] += 1
    summary["range_sample_count"] += int(value.get("range_sample_count") or 0)
    summary["finite_range_count"] += int(value.get("finite_range_count") or 0)
    summary["intensity_count"] += int(value.get("intensity_count") or 0)
    if value.get("finite_range_min") is not None:
        current = summary["finite_range_min"]
        summary["finite_range_min"] = float(value["finite_range_min"]) if current is None else min(current, float(value["finite_range_min"]))
    if value.get("finite_range_max") is not None:
        current = summary["finite_range_max"]
        summary["finite_range_max"] = float(value["finite_range_max"]) if current is None else max(current, float(value["finite_range_max"]))
    if value.get("angle_min") is not None:
        current = summary["angle_min"]
        summary["angle_min"] = float(value["angle_min"]) if current is None else min(current, float(value["angle_min"]))
    if value.get("angle_max") is not None:
        current = summary["angle_max"]
        summary["angle_max"] = float(value["angle_max"]) if current is None else max(current, float(value["angle_max"]))
    if value.get("angle_increment") is not None:
        current = summary["angle_increment"]
        increment = float(value["angle_increment"])
        summary["angle_increment"] = increment if current is None else min(current, increment)
    if value.get("range_min") is not None:
        range_min = float(value["range_min"])
        if range_min == range_min:
            current = summary.get("range_min")
            summary["range_min"] = range_min if current is None else min(current, range_min)
    if value.get("range_max") is not None:
        range_max = float(value["range_max"])
        if range_max == range_max:
            current = summary.get("range_max")
            summary["range_max"] = range_max if current is None else max(current, range_max)


def _semantic_update_image_summary(summary: dict[str, Any], value: dict[str, Any]) -> None:
    # Image 聚合仅保留尺寸、编码和 data_size 统计，避免像素与时间序列进入 manifest。
    summary["sample_count"] += 1
    summary["image_sample_count"] += 1
    width = value.get("width")
    height = value.get("height")
    step = value.get("step")
    data_size = value.get("data_size")
    summary["width_min"] = width if summary["width_min"] is None else min(summary["width_min"], int(width))
    summary["width_max"] = width if summary["width_max"] is None else max(summary["width_max"], int(width))
    summary["height_min"] = height if summary["height_min"] is None else min(summary["height_min"], int(height))
    summary["height_max"] = height if summary["height_max"] is None else max(summary["height_max"], int(height))
    summary["step_min"] = step if summary["step_min"] is None else min(summary["step_min"], int(step))
    summary["step_max"] = step if summary["step_max"] is None else max(summary["step_max"], int(step))
    summary["data_size_min"] = data_size if summary["data_size_min"] is None else min(summary["data_size_min"], int(data_size))
    summary["data_size_max"] = data_size if summary["data_size_max"] is None else max(summary["data_size_max"], int(data_size))
    encoding = value.get("encoding")
    if isinstance(encoding, str):
        encoding = encoding.strip()
        if encoding and encoding not in summary["encodings"]:
            summary["encodings"].append(encoding)
    summary["data_size_total"] = int(summary.get("data_size_total") or 0) + int(data_size or 0)


def _semantic_update_tf_summary(summary: dict[str, Any], value: dict[str, Any]) -> None:
    # TF 聚合只保留 transforms count 与少量 frame pair 示例，不解析位姿值。
    summary["sample_count"] += 1
    summary["tf_sample_count"] += 1
    summary["transform_count_total"] += int(value.get("transform_count") or 0)
    for parent_frame_id, child_frame_id in value.get("frame_pairs") or []:
        if parent_frame_id or child_frame_id:
            summary["frame_pairs"].append((parent_frame_id, child_frame_id))
    summary["frame_pairs"] = summary["frame_pairs"][:6]


def _odometry_translation_summary(value: dict[str, Any]) -> dict[str, Any]:
    # 只输出安全平移值，让 consumer 可见位姿变化但拿不到原始 payload。
    return {
        "x_m": round(float(value["x_m"]), 6),
        "y_m": round(float(value["y_m"]), 6),
        "z_m": round(float(value["z_m"]), 6),
    }


def _semantic_update_odometry_summary(summary: dict[str, Any], value: dict[str, Any]) -> None:
    # Odometry 聚合按样本更新起止位姿与位移范数，不进入 twist/covariance 语义。
    summary["sample_count"] += 1
    if bool(value.get("nonzero_translation_observed")):
        summary["nonzero_translation_sample_count"] += 1
    translation_norm_m = value.get("translation_norm_m")
    if translation_norm_m is not None:
        numeric_norm = float(translation_norm_m)
        current_min = summary["translation_norm_min"]
        current_max = summary["translation_norm_max"]
        summary["translation_norm_min"] = numeric_norm if current_min is None else min(current_min, numeric_norm)
        summary["translation_norm_max"] = numeric_norm if current_max is None else max(current_max, numeric_norm)
    pair_list = [str(value["frame_id"]), str(value["child_frame_id"])]
    if pair_list not in summary["frame_pairs"]:
        summary["frame_pairs"].append(pair_list)
    if summary["start_translation"] is None:
        summary["start_translation"] = _odometry_translation_summary(value)
    summary["end_translation"] = _odometry_translation_summary(value)


def _semantic_update_diagnostic_array_summary(summary: dict[str, Any], value: dict[str, Any]) -> None:
    # DiagnosticArray 可能含诊断正文和具体值；聚合只累加安全计数和短标识符样本。
    summary["sample_count"] += 1
    summary["status_count"] += int(value.get("status_count") or 0)
    value_highest_level = value.get("highest_level")
    if value_highest_level is not None:
        current = summary["highest_level"]
        level = int(value_highest_level)
        summary["highest_level"] = level if current is None else max(int(current), level)
    for level, count in (value.get("level_distribution") or {}).items():
        level_key = str(level)
        summary["level_distribution"][level_key] = int(summary["level_distribution"].get(level_key, 0)) + int(count or 0)
    for sample in value.get("status_name_samples") or []:
        _append_unique_limited_sample(summary["status_name_samples"], _safe_diagnostic_sample_text(str(sample)))
    for sample in value.get("hardware_id_samples") or []:
        _append_unique_limited_sample(summary["hardware_id_samples"], _safe_diagnostic_sample_text(str(sample)))
    summary["key_value_pair_count"] += int(value.get("key_value_pair_count") or 0)


def _pose_progress_empty_summary() -> dict[str, Any]:
    # 位姿进度摘要固定字段骨架，方便 blocked 与 ready 两种状态保持同形。
    return {
        "sample_count": 0,
        "pose_sample_count": 0,
        "pose_decode_ok_count": 0,
        "pose_decode_failed_count": 0,
        "pose_topic_types": [],
        "pose_frame_pairs": [],
        "pose_time_span_ns": 0,
        "start_pose": None,
        "end_pose": None,
        "displacement_m": 0.0,
        "nonzero_pose_progress_observed": False,
    }


def _pose_progress_build_pose(sample: dict[str, Any], timestamp_ns: int) -> dict[str, Any]:
    # start/end pose 只保留 frame pair 与平移值，不把 orientation 或原始 payload 再向上游扩散。
    return {
        "frame_id": sample["frame_id"],
        "child_frame_id": sample["child_frame_id"],
        "x_m": round(float(sample["x_m"]), 6),
        "y_m": round(float(sample["y_m"]), 6),
        "z_m": round(float(sample["z_m"]), 6),
        "timestamp_ns": int(timestamp_ns),
    }


def _pose_progress_select_pair(samples_by_pair: dict[tuple[str, str], list[dict[str, Any]]]) -> tuple[tuple[str, str] | None, list[dict[str, Any]]]:
    # 多个 frame pair 同时出现时，优先选择样本最多且起始最早的那一组来计算位移。
    candidates = []
    for pair, samples in samples_by_pair.items():
        ordered = sorted(samples, key=lambda item: (int(item["timestamp_ns"]), int(item["sequence_index"])))
        if len(ordered) < 2:
            continue
        candidates.append((pair, ordered))
    if not candidates:
        return None, []
    candidates.sort(key=lambda item: (-len(item[1]), int(item[1][0]["timestamp_ns"]), item[0][0], item[0][1]))
    return candidates[0]


def summarize_route_bag_pose_progress_replay(path: Path) -> tuple[dict[str, Any], list[str], int]:
    # 位姿进度摘要只读 DB3 中白名单消息类型，失败时必须保留 blocked reason，而不是猜测进度。
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        tables = {str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        missing_tables = {"topics", "messages"} - tables
        topics_columns = sqlite_table_columns(connection, "topics") if "topics" in tables else set()
        messages_columns = sqlite_table_columns(connection, "messages") if "messages" in tables else set()
        missing_topic_columns = {"id", "name", "type"} - topics_columns
        missing_message_columns = {"id", "topic_id", "timestamp", "data"} - messages_columns
        if missing_tables or missing_topic_columns or missing_message_columns:
            return (
                {
                    "sqlite_schema_ok": False,
                    "topic_count": 0,
                    "message_count": 0,
                    "timestamp_first_ns": None,
                    "timestamp_last_ns": None,
                    "sample_topic_names": [],
                    **_pose_progress_empty_summary(),
                },
                ["route_bag_pose_progress_sqlite_schema_mismatch"],
                0,
            )

        topic_count = int(connection.execute("SELECT COUNT(*) FROM topics").fetchone()[0])
        message_count = int(connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0])
        timestamp_row = connection.execute("SELECT MIN(timestamp), MAX(timestamp) FROM messages").fetchone()
        sample_topic_names = []
        unsafe_topic_count = 0
        for row in connection.execute("SELECT name FROM topics ORDER BY id LIMIT 8").fetchall():
            safe_name, unsafe = safe_route_bag_topic_name(row[0])
            if unsafe:
                unsafe_topic_count += 1
                continue
            sample_topic_names.append(safe_name)

        blocked_reasons: list[str] = []
        if topic_count <= 0:
            blocked_reasons.append("route_bag_pose_progress_topics_empty")
        if message_count <= 0:
            blocked_reasons.append("route_bag_pose_progress_messages_empty")
        if unsafe_topic_count:
            blocked_reasons.append("route_bag_pose_progress_unsafe_topic_name")

        pose_samples: list[dict[str, Any]] = []
        pose_decode_ok_count = 0
        pose_decode_failed_count = 0
        pose_topic_types: set[str] = set()
        sample_rows = connection.execute(
            """
            SELECT t.name, t.type, m.timestamp, m.data, m.id
            FROM messages AS m
            LEFT JOIN topics AS t ON t.id = m.topic_id
            ORDER BY m.timestamp, m.id
            """
        ).fetchall()
        for topic_name, topic_type, timestamp_ns, payload, message_id in sample_rows:
            safe_topic_name, topic_unsafe = safe_route_bag_topic_name(topic_name)
            if topic_unsafe:
                continue
            if not isinstance(topic_type, str) or topic_type not in ROUTE_BAG_POSE_PROGRESS_REPLAY_TOPIC_TYPES:
                continue
            pose_topic_types.add(topic_type)
            try:
                decoded_samples = decode_route_bag_pose_progress_message(topic_type, bytes(payload or b""))
            except Exception:
                pose_decode_failed_count += 1
                blocked_reasons.append("route_bag_pose_progress_decode_failed")
                continue
            pose_decode_ok_count += 1
            for sequence_index, sample in enumerate(decoded_samples):
                pose_samples.append(
                    {
                        "frame_id": sample["frame_id"],
                        "child_frame_id": sample["child_frame_id"],
                        "x_m": sample["x_m"],
                        "y_m": sample["y_m"],
                        "z_m": sample["z_m"],
                        "timestamp_ns": int(timestamp_ns or 0),
                        "sequence_index": int(sequence_index),
                        "message_id": int(message_id or 0),
                        "topic_name": safe_topic_name,
                        "topic_type": topic_type,
                    }
                )

        if not pose_topic_types:
            blocked_reasons.append("route_bag_pose_progress_supported_topic_missing")
        if not pose_samples:
            blocked_reasons.append("route_bag_pose_progress_pose_samples_missing")

        pose_frame_pairs: list[list[str]] = []
        samples_by_pair: dict[tuple[str, str], list[dict[str, Any]]] = {}
        pair_seen: set[tuple[str, str]] = set()
        for sample in pose_samples:
            pair = (str(sample["frame_id"]), str(sample["child_frame_id"]))
            samples_by_pair.setdefault(pair, []).append(sample)
            if pair not in pair_seen:
                pair_seen.add(pair)
                pose_frame_pairs.append([pair[0], pair[1]])

        selected_pair, selected_samples = _pose_progress_select_pair(samples_by_pair)
        if not selected_pair:
            blocked_reasons.append("route_bag_pose_progress_same_frame_pair_missing")
        pose_time_span_ns = 0
        displacement_m = 0.0
        start_pose = None
        end_pose = None
        nonzero_pose_progress_observed = False
        if selected_pair:
            start_sample = selected_samples[0]
            end_sample = selected_samples[-1]
            pose_time_span_ns = int(end_sample["timestamp_ns"]) - int(start_sample["timestamp_ns"])
            displacement_m = round(
                math.hypot(
                    float(end_sample["x_m"]) - float(start_sample["x_m"]),
                    float(end_sample["y_m"]) - float(start_sample["y_m"]),
                ),
                6,
            )
            start_pose = _pose_progress_build_pose(start_sample, int(start_sample["timestamp_ns"]))
            end_pose = _pose_progress_build_pose(end_sample, int(end_sample["timestamp_ns"]))
            nonzero_pose_progress_observed = displacement_m > 1e-6
            if not nonzero_pose_progress_observed:
                blocked_reasons.append("route_bag_pose_progress_zero_displacement")
        if not selected_pair:
            blocked_reasons.append("route_bag_pose_progress_insufficient_same_frame_pair_samples")

        return (
            {
                "sqlite_schema_ok": True,
                "topic_count": topic_count,
                "message_count": message_count,
                "timestamp_first_ns": timestamp_row[0] if timestamp_row else None,
                "timestamp_last_ns": timestamp_row[1] if timestamp_row else None,
                "sample_topic_names": sample_topic_names,
                "sample_count": len(pose_samples),
                "pose_sample_count": len(pose_samples),
                "pose_decode_ok_count": pose_decode_ok_count,
                "pose_decode_failed_count": pose_decode_failed_count,
                "pose_topic_types": sorted(pose_topic_types),
                "pose_frame_pairs": pose_frame_pairs,
                "pose_time_span_ns": pose_time_span_ns,
                "start_pose": start_pose,
                "end_pose": end_pose,
                "displacement_m": displacement_m,
                "nonzero_pose_progress_observed": nonzero_pose_progress_observed,
            },
            blocked_reasons,
            unsafe_topic_count,
        )
    finally:
        connection.close()


def summarize_route_bag_semantic_replay(path: Path) -> tuple[dict[str, Any], list[str], int]:
    # 只在 whitelist topic type 上做 limited CDR 反序列，失败必须返回 blocked reason 而不抛错。
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        tables = {str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        missing_tables = {"topics", "messages"} - tables
        topics_columns = sqlite_table_columns(connection, "topics") if "topics" in tables else set()
        messages_columns = sqlite_table_columns(connection, "messages") if "messages" in tables else set()
        missing_topic_columns = {"id", "name", "type"} - topics_columns
        missing_message_columns = {"id", "topic_id", "timestamp", "data"} - messages_columns
        if missing_tables or missing_topic_columns or missing_message_columns:
            return (
                {
                    "sqlite_schema_ok": False,
                    "topic_count": 0,
                    "message_count": 0,
                    "timestamp_first_ns": None,
                    "timestamp_last_ns": None,
                    "sample_topic_names": [],
                    "semantic_sample_count": 0,
                    "semantic_decode_ok_count": 0,
                    "semantic_decode_failed_count": 0,
                    "semantic_topic_types": [],
                    "laser_scan_summary": _semantic_empty_summary(),
                    "image_summary": _semantic_empty_summary(),
                    "tf_summary": _semantic_empty_summary(),
                    "odometry_summary": _odometry_semantic_empty_summary(),
                    "diagnostic_array_summary": _diagnostic_array_semantic_empty_summary(),
                },
                ["route_bag_semantic_replay_sqlite_schema_mismatch"],
                0,
            )

        topic_count = int(connection.execute("SELECT COUNT(*) FROM topics").fetchone()[0])
        message_count = int(connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0])
        timestamp_row = connection.execute("SELECT MIN(timestamp), MAX(timestamp) FROM messages").fetchone()
        sample_topic_names = []
        unsafe_topic_count = 0
        for row in connection.execute("SELECT name FROM topics ORDER BY id LIMIT 8").fetchall():
            safe_name, unsafe = safe_route_bag_topic_name(row[0])
            if unsafe:
                unsafe_topic_count += 1
                continue
            sample_topic_names.append(safe_name)

        blocked_reasons: list[str] = []
        if topic_count <= 0:
            blocked_reasons.append("route_bag_topics_empty")
        if message_count <= 0:
            blocked_reasons.append("route_bag_messages_empty")
        if unsafe_topic_count:
            blocked_reasons.append("route_bag_semantic_unsafe_topic_name")

        sample_rows = connection.execute(
            """
            SELECT t.name, t.type, m.timestamp, m.data
            FROM messages AS m
            LEFT JOIN topics AS t ON t.id = m.topic_id
            ORDER BY m.timestamp, m.id
            LIMIT ?
            """,
            (ROUTE_BAG_SEMANTIC_REPLAY_DECODE_SAMPLE_LIMIT,),
        ).fetchall()

        semantic_sample_count = 0
        semantic_decode_ok_count = 0
        semantic_decode_failed_count = 0
        semantic_topic_types: set[str] = set()
        laser_scan_summary = _semantic_empty_summary()
        image_summary = _semantic_empty_summary()
        tf_summary = _semantic_empty_summary()
        odometry_summary = _odometry_semantic_empty_summary()
        diagnostic_array_summary = _diagnostic_array_semantic_empty_summary()
        for topic_name, topic_type, _timestamp, payload in sample_rows:
            safe_topic_name, topic_unsafe = safe_route_bag_topic_name(topic_name)
            if topic_unsafe:
                continue
            if not isinstance(topic_type, str) or topic_type not in ROUTE_BAG_SEMANTIC_REPLAY_TOPIC_TYPES:
                continue
            semantic_topic_types.add(topic_type)
            blob = bytes(payload or b"")
            semantic_sample_count += 1
            try:
                semantic_key, semantic_value = decode_semantic_message(topic_type, blob)
            except Exception:
                semantic_decode_failed_count += 1
                blocked_reasons.append("route_bag_semantic_decode_failed")
                continue
            semantic_decode_ok_count += 1
            if semantic_key == "laser_scan":
                _semantic_update_laser_scan_summary(laser_scan_summary, semantic_value)
            elif semantic_key == "image":
                _semantic_update_image_summary(image_summary, semantic_value)
            elif semantic_key == "tf_message":
                _semantic_update_tf_summary(tf_summary, semantic_value)
            elif semantic_key == "odometry":
                _semantic_update_odometry_summary(odometry_summary, semantic_value)
            elif semantic_key == "diagnostic_array":
                _semantic_update_diagnostic_array_summary(diagnostic_array_summary, semantic_value)

        if semantic_sample_count == 0:
            blocked_reasons.append("route_bag_semantic_supported_topic_missing")
        if semantic_decode_failed_count:
            blocked_reasons.append("route_bag_semantic_decode_failed")

        return (
            {
                "sqlite_schema_ok": True,
                "topic_count": topic_count,
                "message_count": message_count,
                "timestamp_first_ns": timestamp_row[0] if timestamp_row else None,
                "timestamp_last_ns": timestamp_row[1] if timestamp_row else None,
                "sample_topic_names": sample_topic_names,
                "semantic_sample_count": semantic_sample_count,
                "semantic_decode_ok_count": semantic_decode_ok_count,
                "semantic_decode_failed_count": semantic_decode_failed_count,
                "semantic_topic_types": sorted(semantic_topic_types),
                "laser_scan_summary": laser_scan_summary,
                "image_summary": image_summary,
                "tf_summary": tf_summary,
                "odometry_summary": odometry_summary,
                "diagnostic_array_summary": diagnostic_array_summary,
            },
            blocked_reasons,
            unsafe_topic_count,
        )
    finally:
        connection.close()


def route_bag_semantic_replay_blocked_summary(
    task_id: str,
    task_id_source: str,
    source_label: str | None,
    blocked_reasons: list[str],
    *,
    metadata_summary: dict[str, Any] | None = None,
    db3_basename: str | None = None,
    db3_present: bool = False,
    db3_read_ok: bool = False,
    sqlite_schema_ok: bool = False,
    db3_size_bytes: int = 0,
    db3_sha256_prefix: str | None = None,
    topic_count: int = 0,
    message_count: int = 0,
    timestamp_first_ns: int | None = None,
    timestamp_last_ns: int | None = None,
    sample_topic_names: list[str] | None = None,
    semantic_sample_count: int = 0,
    semantic_decode_ok_count: int = 0,
    semantic_decode_failed_count: int = 0,
    semantic_topic_types: list[str] | None = None,
    laser_scan_summary: dict[str, Any] | None = None,
    image_summary: dict[str, Any] | None = None,
    tf_summary: dict[str, Any] | None = None,
    odometry_summary: dict[str, Any] | None = None,
    diagnostic_array_summary: dict[str, Any] | None = None,
    dangerous_true_fields: list[str] | None = None,
    unsafe_field_count: int = 0,
    unsafe_text_field_count: int = 0,
) -> dict[str, Any]:
    # fail-closed 摘要必须保留同形字段，让 O6/O7 对 route-bag cdr 解码失败保持可观测。
    metadata = metadata_summary or route_bag_metadata_absent_summary()
    return {
        "schema": ROUTE_BAG_SEMANTIC_REPLAY_SCHEMA,
        "proof_scope": ROUTE_BAG_SEMANTIC_REPLAY_PROOF_SCOPE,
        "source": "route_bag_db3_semantic_replay",
        "source_label": source_label,
        "status": "blocked_not_proven",
        "task_id": task_id,
        "task_id_source": task_id_source,
        "metadata_present": bool(metadata.get("metadata_present")),
        "metadata_read_ok": bool(metadata.get("metadata_read_ok")),
        "metadata_basename": metadata.get("metadata_basename"),
        "metadata_size_bytes": int(metadata.get("metadata_size_bytes") or 0),
        "metadata_sha256_prefix": metadata.get("metadata_sha256_prefix"),
        "db3_present": db3_present,
        "db3_read_ok": db3_read_ok,
        "sqlite_schema_ok": sqlite_schema_ok,
        "db3_basename": db3_basename,
        "db3_size_bytes": db3_size_bytes,
        "db3_sha256_prefix": db3_sha256_prefix,
        "topic_count": topic_count,
        "message_count": message_count,
        "timestamp_first_ns": timestamp_first_ns,
        "timestamp_last_ns": timestamp_last_ns,
        "sample_topic_names": sample_topic_names or [],
        "semantic_sample_count": semantic_sample_count,
        "semantic_decode_ok_count": semantic_decode_ok_count,
        "semantic_decode_failed_count": semantic_decode_failed_count,
        "semantic_topic_types": semantic_topic_types or [],
        "laser_scan_summary": laser_scan_summary or _semantic_empty_summary(),
        "image_summary": image_summary or _semantic_empty_summary(),
        "tf_summary": tf_summary or _semantic_empty_summary(),
        "odometry_summary": odometry_summary or _odometry_semantic_empty_summary(),
        "diagnostic_array_summary": diagnostic_array_summary or _diagnostic_array_semantic_empty_summary(),
        "blocked_reasons": sorted(set(reason for reason in blocked_reasons if reason)),
        "dangerous_true_fields": sorted(set(dangerous_true_fields or [])),
        "unsafe_field_count": int(unsafe_field_count),
        "unsafe_text_field_count": int(unsafe_text_field_count),
        "next_required_evidence": [
            "safe_route_bag_db3_with_safe_whitelist_semantic_messages",
            "same_task_route_bag_metadata_yaml",
            "live_nav2_pose_progress_or_route_execution_log",
            "delivery_record_or_operator_dropoff_confirmation",
        ],
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "live_nav2_run_proven": False,
        "route_execution_success": False,
        "connects_cloud_production": False,
    }


def _full_semantic_decode_matrix_empty_summary() -> dict[str, Any]:
    # 覆盖矩阵 blocked/ready 都固定字段集，避免 O6/O7 因缺字段把缺口误判为成功。
    return {
        "topic_type_count": 0,
        "decoded_topic_type_count": 0,
        "unsupported_topic_type_count": 0,
        "failed_topic_type_count": 0,
        "decoded_message_sample_count": 0,
        "decode_failed_message_sample_count": 0,
        "unsupported_message_sample_count": 0,
        "coverage_ratio": 0.0,
        "topic_type_matrix": [],
    }


def route_bag_full_semantic_decode_matrix_blocked_summary(
    task_id: str,
    task_id_source: str,
    source_label: str | None,
    blocked_reasons: list[str],
    *,
    metadata_summary: dict[str, Any] | None = None,
    db3_basename: str | None = None,
    db3_present: bool = False,
    db3_read_ok: bool = False,
    sqlite_schema_ok: bool = False,
    db3_size_bytes: int = 0,
    db3_sha256_prefix: str | None = None,
    topic_count: int = 0,
    message_count: int = 0,
    timestamp_first_ns: int | None = None,
    timestamp_last_ns: int | None = None,
    sample_topic_names: list[str] | None = None,
    topic_type_count: int = 0,
    decoded_topic_type_count: int = 0,
    unsupported_topic_type_count: int = 0,
    failed_topic_type_count: int = 0,
    decoded_message_sample_count: int = 0,
    decode_failed_message_sample_count: int = 0,
    unsupported_message_sample_count: int = 0,
    coverage_ratio: float = 0.0,
    topic_type_matrix: list[dict[str, Any]] | None = None,
    dangerous_true_fields: list[str] | None = None,
    unsafe_field_count: int = 0,
    unsafe_text_field_count: int = 0,
) -> dict[str, Any]:
    # fail-closed 摘要只保留安全矩阵和计数；路径、payload、完整 hash 只能留在本地 DB3。
    metadata = metadata_summary or route_bag_metadata_absent_summary()
    return {
        "schema": ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_SCHEMA,
        "proof_scope": ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_PROOF_SCOPE,
        "source": "route_bag_db3_full_semantic_decode_matrix",
        "source_label": source_label,
        "status": "blocked_not_proven",
        "task_id": task_id,
        "task_id_source": task_id_source,
        "metadata_present": bool(metadata.get("metadata_present")),
        "metadata_read_ok": bool(metadata.get("metadata_read_ok")),
        "metadata_basename": metadata.get("metadata_basename"),
        "metadata_size_bytes": int(metadata.get("metadata_size_bytes") or 0),
        "metadata_sha256_prefix": metadata.get("metadata_sha256_prefix"),
        "db3_present": db3_present,
        "db3_read_ok": db3_read_ok,
        "sqlite_schema_ok": sqlite_schema_ok,
        "db3_basename": db3_basename,
        "db3_size_bytes": db3_size_bytes,
        "db3_sha256_prefix": db3_sha256_prefix,
        "topic_count": topic_count,
        "message_count": message_count,
        "timestamp_first_ns": timestamp_first_ns,
        "timestamp_last_ns": timestamp_last_ns,
        "sample_topic_names": sample_topic_names or [],
        "topic_type_count": int(topic_type_count),
        "decoded_topic_type_count": int(decoded_topic_type_count),
        "unsupported_topic_type_count": int(unsupported_topic_type_count),
        "failed_topic_type_count": int(failed_topic_type_count),
        "decoded_message_sample_count": int(decoded_message_sample_count),
        "decode_failed_message_sample_count": int(decode_failed_message_sample_count),
        "unsupported_message_sample_count": int(unsupported_message_sample_count),
        "coverage_ratio": float(coverage_ratio),
        "topic_type_matrix": topic_type_matrix or [],
        "blocked_reasons": sorted(set(reason for reason in blocked_reasons if reason)),
        "dangerous_true_fields": sorted(set(dangerous_true_fields or [])),
        "unsafe_field_count": int(unsafe_field_count),
        "unsafe_text_field_count": int(unsafe_text_field_count),
        "next_required_evidence": [
            "safe_route_bag_db3_with_decodable_semantic_topic_types",
            "decoder_for_unsupported_route_bag_topic_types",
            "clean_route_bag_payload_samples_without_decode_failures",
            "live_nav2_pose_progress_or_route_execution_log",
            "delivery_record_or_operator_dropoff_confirmation",
        ],
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "live_nav2_run_proven": False,
        "route_execution_success": False,
        "connects_cloud_production": False,
    }


def _decode_matrix_item_status(item: dict[str, Any]) -> tuple[str, str | None]:
    # topic/type 级状态按最严重样本归类，让 failed 和 unsupported 不会被少量 decoded 洗白。
    if int(item["unsupported_message_sample_count"]):
        return "unsupported", "unsupported_semantic_type"
    if int(item["decode_failed_message_sample_count"]):
        return "failed", "route_bag_full_semantic_decode_matrix_decode_failed"
    if int(item["decoded_message_sample_count"]):
        return "decoded", None
    return "failed", "route_bag_full_semantic_decode_matrix_sample_missing"


def summarize_route_bag_full_semantic_decode_matrix(path: Path) -> tuple[dict[str, Any], list[str], int]:
    # 覆盖矩阵只读 rosbag2 DB3，按 topic/type 聚合有限样本解码，不引入 ROS2 runtime。
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        tables = {str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        missing_tables = {"topics", "messages"} - tables
        topics_columns = sqlite_table_columns(connection, "topics") if "topics" in tables else set()
        messages_columns = sqlite_table_columns(connection, "messages") if "messages" in tables else set()
        missing_topic_columns = {"id", "name", "type"} - topics_columns
        missing_message_columns = {"id", "topic_id", "timestamp", "data"} - messages_columns
        if missing_tables or missing_topic_columns or missing_message_columns:
            return (
                {
                    "sqlite_schema_ok": False,
                    "topic_count": 0,
                    "message_count": 0,
                    "timestamp_first_ns": None,
                    "timestamp_last_ns": None,
                    "sample_topic_names": [],
                    **_full_semantic_decode_matrix_empty_summary(),
                },
                ["route_bag_full_semantic_decode_matrix_sqlite_schema_mismatch"],
                0,
            )

        topic_rows = connection.execute("SELECT id, name, type FROM topics ORDER BY id").fetchall()
        topic_count = len(topic_rows)
        message_count = int(connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0])
        timestamp_row = connection.execute("SELECT MIN(timestamp), MAX(timestamp) FROM messages").fetchone()
        sample_topic_names = []
        safe_topics_by_id: dict[int, tuple[str, str] | None] = {}
        unsafe_topic_count = 0
        unsafe_type_count = 0
        for topic_id, topic_name, topic_type in topic_rows:
            safe_name, topic_unsafe = safe_route_bag_topic_name(topic_name)
            safe_type, type_unsafe = safe_route_bag_topic_type(topic_type)
            if topic_unsafe:
                unsafe_topic_count += 1
            if type_unsafe:
                unsafe_type_count += 1
            if topic_unsafe or type_unsafe:
                safe_topics_by_id[int(topic_id)] = None
                continue
            safe_topics_by_id[int(topic_id)] = (str(safe_name), str(safe_type))
            if len(sample_topic_names) < 8:
                sample_topic_names.append(str(safe_name))

        matrix_by_key: dict[tuple[str, str], dict[str, Any]] = {}
        for topic_id, timestamp_ns, payload in connection.execute(
            """
            SELECT topic_id, timestamp, data
            FROM messages
            ORDER BY timestamp, id
            """
        ):
            topic_info = safe_topics_by_id.get(int(topic_id or 0))
            if topic_info is None:
                continue
            topic_name, topic_type = topic_info
            key = (topic_name, topic_type)
            decoder_name = ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_DECODERS.get(topic_type)
            item = matrix_by_key.setdefault(
                key,
                {
                    "topic_name": topic_name,
                    "topic_type": topic_type,
                    "message_count": 0,
                    "sampled_message_count": 0,
                    "decoded_message_sample_count": 0,
                    "decode_failed_message_sample_count": 0,
                    "unsupported_message_sample_count": 0,
                    "status": "blocked_not_proven",
                    "blocked_reason": None,
                    "decoder_name": decoder_name,
                    "sample_sha256_prefixes": [],
                },
            )
            item["message_count"] = int(item["message_count"]) + 1
            if int(item["sampled_message_count"]) >= ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_SAMPLE_LIMIT:
                continue
            blob = bytes(payload or b"")
            item["sampled_message_count"] = int(item["sampled_message_count"]) + 1
            item["sample_sha256_prefixes"].append(hashlib.sha256(blob).hexdigest()[:12])
            if decoder_name is None:
                item["unsupported_message_sample_count"] = int(item["unsupported_message_sample_count"]) + 1
                continue
            try:
                decode_semantic_message(topic_type, blob)
            except Exception:
                item["decode_failed_message_sample_count"] = int(item["decode_failed_message_sample_count"]) + 1
                continue
            item["decoded_message_sample_count"] = int(item["decoded_message_sample_count"]) + 1

        topic_type_matrix = []
        decoded_topic_type_count = 0
        unsupported_topic_type_count = 0
        failed_topic_type_count = 0
        decoded_message_sample_count = 0
        decode_failed_message_sample_count = 0
        unsupported_message_sample_count = 0
        for item in sorted(matrix_by_key.values(), key=lambda value: (str(value["topic_name"]), str(value["topic_type"]))):
            status, blocked_reason = _decode_matrix_item_status(item)
            item["status"] = status
            item["blocked_reason"] = blocked_reason
            item["sample_sha256_prefixes"] = list(item["sample_sha256_prefixes"])[:3]
            decoded_message_sample_count += int(item["decoded_message_sample_count"])
            decode_failed_message_sample_count += int(item["decode_failed_message_sample_count"])
            unsupported_message_sample_count += int(item["unsupported_message_sample_count"])
            if status == "decoded":
                decoded_topic_type_count += 1
            elif status == "unsupported":
                unsupported_topic_type_count += 1
            else:
                failed_topic_type_count += 1
            topic_type_matrix.append(item)

        considered_sample_count = decoded_message_sample_count + decode_failed_message_sample_count + unsupported_message_sample_count
        coverage_ratio = round(decoded_message_sample_count / considered_sample_count, 3) if considered_sample_count else 0.0
        blocked_reasons: list[str] = []
        if topic_count <= 0:
            blocked_reasons.append("route_bag_full_semantic_decode_matrix_topics_empty")
        if message_count <= 0:
            blocked_reasons.append("route_bag_full_semantic_decode_matrix_messages_empty")
        if unsafe_topic_count:
            blocked_reasons.append("route_bag_full_semantic_decode_matrix_unsafe_topic_name")
        if unsafe_type_count:
            blocked_reasons.append("route_bag_full_semantic_decode_matrix_unsafe_topic_type")
        if not topic_type_matrix:
            blocked_reasons.append("route_bag_full_semantic_decode_matrix_safe_topic_type_missing")
        if decoded_topic_type_count <= 0:
            blocked_reasons.append("route_bag_full_semantic_decode_matrix_decoded_topic_type_missing")
        if unsupported_topic_type_count:
            blocked_reasons.append("route_bag_full_semantic_decode_matrix_unsupported_topic_type")
        if failed_topic_type_count:
            blocked_reasons.append("route_bag_full_semantic_decode_matrix_decode_failed")

        return (
            {
                "sqlite_schema_ok": True,
                "topic_count": topic_count,
                "message_count": message_count,
                "timestamp_first_ns": timestamp_row[0] if timestamp_row else None,
                "timestamp_last_ns": timestamp_row[1] if timestamp_row else None,
                "sample_topic_names": sample_topic_names,
                "topic_type_count": len(topic_type_matrix),
                "decoded_topic_type_count": decoded_topic_type_count,
                "unsupported_topic_type_count": unsupported_topic_type_count,
                "failed_topic_type_count": failed_topic_type_count,
                "decoded_message_sample_count": decoded_message_sample_count,
                "decode_failed_message_sample_count": decode_failed_message_sample_count,
                "unsupported_message_sample_count": unsupported_message_sample_count,
                "coverage_ratio": coverage_ratio,
                "topic_type_matrix": topic_type_matrix,
            },
            blocked_reasons,
            unsafe_topic_count + unsafe_type_count,
        )
    finally:
        connection.close()


def route_bag_pose_progress_replay_blocked_summary(
    task_id: str,
    task_id_source: str,
    source_label: str | None,
    blocked_reasons: list[str],
    *,
    metadata_summary: dict[str, Any] | None = None,
    db3_basename: str | None = None,
    db3_present: bool = False,
    db3_read_ok: bool = False,
    sqlite_schema_ok: bool = False,
    db3_size_bytes: int = 0,
    db3_sha256_prefix: str | None = None,
    topic_count: int = 0,
    message_count: int = 0,
    timestamp_first_ns: int | None = None,
    timestamp_last_ns: int | None = None,
    sample_topic_names: list[str] | None = None,
    pose_sample_count: int = 0,
    pose_decode_ok_count: int = 0,
    pose_decode_failed_count: int = 0,
    pose_topic_types: list[str] | None = None,
    pose_frame_pairs: list[list[str]] | None = None,
    pose_time_span_ns: int = 0,
    start_pose: dict[str, Any] | None = None,
    end_pose: dict[str, Any] | None = None,
    displacement_m: float = 0.0,
    nonzero_pose_progress_observed: bool = False,
    dangerous_true_fields: list[str] | None = None,
    unsafe_field_count: int = 0,
    unsafe_text_field_count: int = 0,
) -> dict[str, Any]:
    # fail-closed 摘要必须保留同形字段，让 O6/O7 对位姿进度解码失败保持可观测。
    metadata = metadata_summary or route_bag_metadata_absent_summary()
    return {
        "schema": ROUTE_BAG_POSE_PROGRESS_REPLAY_SCHEMA,
        "proof_scope": ROUTE_BAG_POSE_PROGRESS_REPLAY_PROOF_SCOPE,
        "source": "route_bag_db3_pose_progress_replay",
        "source_label": source_label,
        "status": "blocked_not_proven",
        "task_id": task_id,
        "task_id_source": task_id_source,
        "metadata_present": bool(metadata.get("metadata_present")),
        "metadata_read_ok": bool(metadata.get("metadata_read_ok")),
        "metadata_basename": metadata.get("metadata_basename"),
        "metadata_size_bytes": int(metadata.get("metadata_size_bytes") or 0),
        "metadata_sha256_prefix": metadata.get("metadata_sha256_prefix"),
        "db3_present": db3_present,
        "db3_read_ok": db3_read_ok,
        "sqlite_schema_ok": sqlite_schema_ok,
        "db3_basename": db3_basename,
        "db3_size_bytes": db3_size_bytes,
        "db3_sha256_prefix": db3_sha256_prefix,
        "topic_count": topic_count,
        "message_count": message_count,
        "timestamp_first_ns": timestamp_first_ns,
        "timestamp_last_ns": timestamp_last_ns,
        "sample_topic_names": sample_topic_names or [],
        "sample_count": pose_sample_count,
        "pose_sample_count": pose_sample_count,
        "pose_decode_ok_count": pose_decode_ok_count,
        "pose_decode_failed_count": pose_decode_failed_count,
        "pose_topic_types": pose_topic_types or [],
        "pose_frame_pairs": pose_frame_pairs or [],
        "pose_time_span_ns": pose_time_span_ns,
        "start_pose": start_pose,
        "end_pose": end_pose,
        "displacement_m": displacement_m,
        "nonzero_pose_progress_observed": nonzero_pose_progress_observed,
        "blocked_reasons": sorted(set(reason for reason in blocked_reasons if reason)),
        "dangerous_true_fields": sorted(set(dangerous_true_fields or [])),
        "unsafe_field_count": int(unsafe_field_count),
        "unsafe_text_field_count": int(unsafe_text_field_count),
        "next_required_evidence": [
            "safe_route_bag_db3_with_pose_progress_messages",
            "same_task_route_bag_metadata_yaml",
            "live_nav2_pose_progress_or_route_execution_log",
            "delivery_record_or_operator_dropoff_confirmation",
        ],
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "live_nav2_run_proven": False,
        "route_execution_success": False,
        "connects_cloud_production": False,
    }


def route_bag_text_issues(text: str) -> tuple[list[str], int]:
    # metadata/source label 只做安全扫描，不把原文带入输出；相对 route_bag_0.db3 文件名不视为路径泄露。
    dangerous_true_fields = []
    for field in ROUTE_BAG_DANGEROUS_TRUE_FIELDS:
        if re.search(rf"\b{re.escape(field)}\b\s*[:=]\s*true\b", text, flags=re.IGNORECASE):
            dangerous_true_fields.append(field)
    lowered = text.lower()
    unsafe_text_count = 0
    unsafe_markers = (
        "/users/",
        "/root/",
        "token",
        "credential",
        "base64",
        "raw_payload",
        "path=",
        "secret",
        "access_key",
    )
    if any(marker in lowered for marker in unsafe_markers) or ROUTE_BAG_CREDENTIAL_URL_RE.search(text):
        unsafe_text_count += 1
    return sorted(set(dangerous_true_fields)), unsafe_text_count


def safe_route_bag_source_label(value: str | None, fallback: str) -> tuple[str | None, list[str], int]:
    # source_label 是跨系统可见字段，只允许短 label；绝对路径和 URL 由 basename/hash 摘要替代。
    raw = (value if value is not None else fallback).strip()
    dangerous, unsafe_text_count = route_bag_text_issues(raw)
    if not raw or len(raw) > 120 or not re.fullmatch(r"[A-Za-z0-9_.:-]+", raw):
        unsafe_text_count += 1
    if dangerous or unsafe_text_count:
        return None, dangerous, unsafe_text_count
    return raw, [], 0


def safe_route_bag_topic_name(value: Any) -> tuple[str | None, bool]:
    # topic 名允许 ROS 常见的 /scan、/tf_static、/camera/image_raw；但不允许控制 topic 或敏感文本进入样本。
    if not isinstance(value, str):
        return None, True
    text = value.strip()
    lowered = text.lower()
    if not text or len(text) > 120:
        return None, True
    if text == CONTROL_TOPIC_CMD_VEL or text.endswith(CONTROL_TOPIC_CMD_VEL):
        return None, True
    if any(marker in lowered for marker in ("/users/", "/root/", "token", "credential", "base64", "raw_payload", "secret")):
        return None, True
    if ROUTE_BAG_CREDENTIAL_URL_RE.search(text):
        return None, True
    if not re.fullmatch(r"/?[A-Za-z0-9_~/]+", text):
        return None, True
    return text, False


def safe_route_bag_topic_type(value: Any) -> tuple[str | None, bool]:
    # type 会进入覆盖矩阵，必须像 topic 一样先筛掉路径、凭证和任意控制/原始文本。
    if not isinstance(value, str):
        return None, True
    text = value.strip()
    lowered = text.lower()
    if not text or len(text) > 120:
        return None, True
    if text.startswith("/") or "\\" in text or ".." in text:
        return None, True
    if any(marker in lowered for marker in ("/users/", "/root/", "token", "credential", "base64", "raw_payload", "secret")):
        return None, True
    if ROUTE_BAG_CREDENTIAL_URL_RE.search(text):
        return None, True
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*/(?:msg|srv|action)/[A-Za-z][A-Za-z0-9_]*", text):
        return None, True
    return text, False


def read_route_bag_metadata(path_value: str | None) -> dict[str, Any]:
    # metadata.yaml 只提取 basename/size/hash 和安全状态，不解析或输出 relative_file_paths/raw 内容。
    if not path_value:
        return route_bag_metadata_absent_summary()
    path = Path(path_value).expanduser()
    if not path.is_file():
        return {
            **route_bag_metadata_absent_summary(),
            "blocked_reasons": ["route_bag_metadata_yaml_missing_or_not_file"],
        }
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        size = path.stat().st_size
        digest = route_bag_short_hash(path)
    except OSError:
        return {
            **route_bag_metadata_absent_summary(),
            "metadata_present": True,
            "metadata_basename": path.name,
            "blocked_reasons": ["route_bag_metadata_yaml_unreadable"],
        }
    dangerous, unsafe_text_count = route_bag_text_issues(text)
    blocked_reasons = []
    if size <= 0:
        blocked_reasons.append("route_bag_metadata_yaml_empty")
    if dangerous:
        blocked_reasons.append("route_bag_metadata_dangerous_true_claim")
    if unsafe_text_count:
        blocked_reasons.append("route_bag_metadata_unsafe_text")
    return {
        "metadata_present": True,
        "metadata_read_ok": not blocked_reasons,
        "metadata_basename": path.name,
        "metadata_size_bytes": size,
        "metadata_sha256_prefix": digest,
        "blocked_reasons": blocked_reasons,
        "dangerous_true_fields": dangerous,
        "unsafe_text_field_count": unsafe_text_count,
    }


def sqlite_table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    # PRAGMA table_info 是 SQLite 自带 schema introspection，不需要 rosbag2 或 ROS2 runtime。
    return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}


def summarize_route_bag_db3(path: Path) -> tuple[dict[str, Any], list[str], int]:
    # 只查询 topics/messages 元数据，绝不读取 messages.data BLOB，避免 raw ROS payload 进入内存摘要。
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        tables = {str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        missing_tables = {"topics", "messages"} - tables
        topics_columns = sqlite_table_columns(connection, "topics") if "topics" in tables else set()
        messages_columns = sqlite_table_columns(connection, "messages") if "messages" in tables else set()
        missing_topic_columns = {"id", "name"} - topics_columns
        missing_message_columns = {"id", "topic_id", "timestamp"} - messages_columns
        if missing_tables or missing_topic_columns or missing_message_columns:
            return (
                {
                    "sqlite_schema_ok": False,
                    "topic_count": 0,
                    "message_count": 0,
                    "timestamp_first_ns": None,
                    "timestamp_last_ns": None,
                    "sample_topic_names": [],
                },
                ["route_bag_sqlite_schema_mismatch"],
                0,
            )
        topic_count = int(connection.execute("SELECT COUNT(*) FROM topics").fetchone()[0])
        message_count = int(connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0])
        timestamp_row = connection.execute("SELECT MIN(timestamp), MAX(timestamp) FROM messages").fetchone()
        sample_topic_names = []
        unsafe_topic_count = 0
        for row in connection.execute("SELECT name FROM topics ORDER BY id LIMIT 8").fetchall():
            safe_name, unsafe = safe_route_bag_topic_name(row[0])
            if unsafe:
                unsafe_topic_count += 1
                continue
            sample_topic_names.append(safe_name)
        blocked_reasons = []
        if topic_count <= 0:
            blocked_reasons.append("route_bag_topics_empty")
        if message_count <= 0:
            blocked_reasons.append("route_bag_messages_empty")
        if unsafe_topic_count:
            blocked_reasons.append("route_bag_unsafe_topic_name")
        return (
            {
                "sqlite_schema_ok": True,
                "topic_count": topic_count,
                "message_count": message_count,
                "timestamp_first_ns": timestamp_row[0] if timestamp_row else None,
                "timestamp_last_ns": timestamp_row[1] if timestamp_row else None,
                "sample_topic_names": sample_topic_names,
            },
            blocked_reasons,
            unsafe_topic_count,
        )
    finally:
        connection.close()


def summarize_route_bag_payload_replay(path: Path) -> tuple[dict[str, Any], list[str], int]:
    # payload replay 只读取 BLOB 长度、摘要 hash 和少量样本，避免把整包消息内容搬进内存或 JSON。
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        tables = {str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        missing_tables = {"topics", "messages"} - tables
        topics_columns = sqlite_table_columns(connection, "topics") if "topics" in tables else set()
        messages_columns = sqlite_table_columns(connection, "messages") if "messages" in tables else set()
        missing_topic_columns = {"id", "name"} - topics_columns
        missing_message_columns = {"id", "topic_id", "timestamp", "data"} - messages_columns
        if missing_tables or missing_topic_columns or missing_message_columns:
            return (
                {
                    "sqlite_schema_ok": False,
                    "topic_count": 0,
                    "message_count": 0,
                    "timestamp_first_ns": None,
                    "timestamp_last_ns": None,
                    "sample_topic_names": [],
                    "payload_sample_count": 0,
                    "payload_size_min_bytes": 0,
                    "payload_size_max_bytes": 0,
                    "payload_size_avg_bytes": 0.0,
                    "payload_sha256_prefix_samples": [],
                },
                ["route_bag_payload_sqlite_schema_mismatch"],
                0,
            )

        topic_count = int(connection.execute("SELECT COUNT(*) FROM topics").fetchone()[0])
        message_count = int(connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0])
        timestamp_row = connection.execute("SELECT MIN(timestamp), MAX(timestamp) FROM messages").fetchone()
        payload_row = connection.execute(
            "SELECT MIN(length(data)), MAX(length(data)), AVG(CAST(length(data) AS REAL)) FROM messages"
        ).fetchone()
        sample_topic_names = []
        unsafe_topic_count = 0
        for row in connection.execute("SELECT name FROM topics ORDER BY id LIMIT 8").fetchall():
            safe_name, unsafe = safe_route_bag_topic_name(row[0])
            if unsafe:
                unsafe_topic_count += 1
                continue
            sample_topic_names.append(safe_name)

        payload_samples: list[str] = []
        payload_size_min_bytes = int(payload_row[0] or 0) if payload_row else 0
        payload_size_max_bytes = int(payload_row[1] or 0) if payload_row else 0
        payload_size_avg_bytes = round(float(payload_row[2] or 0.0), 3) if payload_row else 0.0
        sample_rows = connection.execute(
            """
            SELECT t.name, m.timestamp, length(m.data), m.data
            FROM messages AS m
            LEFT JOIN topics AS t ON t.id = m.topic_id
            ORDER BY m.timestamp, m.id
            LIMIT 8
            """
        ).fetchall()
        payload_unsafe_topic_count = 0
        payload_unsafe_text_count = 0
        for topic_name, timestamp_ns, payload_size, payload_blob in sample_rows:
            safe_topic_name, unsafe_topic = safe_route_bag_topic_name(topic_name)
            if unsafe_topic:
                payload_unsafe_topic_count += 1
            blob = bytes(payload_blob or b"")
            payload_size = int(payload_size or 0)
            payload_text = blob.decode("utf-8", errors="replace")
            payload_dangerous, payload_unsafe_text = route_bag_text_issues(payload_text)
            if payload_dangerous:
                payload_unsafe_text_count += 1
            if payload_unsafe_text:
                payload_unsafe_text_count += payload_unsafe_text
            payload_samples.append(hashlib.sha256(blob).hexdigest()[:12])

        blocked_reasons = []
        if topic_count <= 0:
            blocked_reasons.append("route_bag_payload_topics_empty")
        if message_count <= 0:
            blocked_reasons.append("route_bag_payload_messages_empty")
        if unsafe_topic_count or payload_unsafe_topic_count:
            blocked_reasons.append("route_bag_payload_unsafe_topic_name")
        if payload_size_min_bytes <= 0:
            blocked_reasons.append("route_bag_payload_empty")
        if payload_unsafe_text_count:
            blocked_reasons.append("route_bag_payload_unsafe_text")
        return (
            {
                "sqlite_schema_ok": True,
                "topic_count": topic_count,
                "message_count": message_count,
                "timestamp_first_ns": timestamp_row[0] if timestamp_row else None,
                "timestamp_last_ns": timestamp_row[1] if timestamp_row else None,
                "sample_topic_names": sample_topic_names,
                "payload_sample_count": len(payload_samples),
                "payload_size_min_bytes": payload_size_min_bytes,
                "payload_size_max_bytes": payload_size_max_bytes,
                "payload_size_avg_bytes": payload_size_avg_bytes,
                "payload_sha256_prefix_samples": payload_samples,
            },
            blocked_reasons,
            unsafe_topic_count + payload_unsafe_topic_count,
        )
    finally:
        connection.close()


def build_route_bag_evidence(args: argparse.Namespace, packet: dict[str, Any]) -> dict[str, Any]:
    # route_bag_evidence 是 DB3 intake 证据，不证明 route execution、live Nav2 或 delivery 成功。
    task_id = str(packet.get("task_id") or args.run_id)
    task_id_source = str(packet.get("task_id_source") or "field_motion_evidence_packet")
    db3_path_value = getattr(args, "route_bag_db3", None)
    fallback_label = Path(db3_path_value).name if db3_path_value else "missing_route_bag_db3"
    source_label, label_dangerous, label_unsafe_count = safe_route_bag_source_label(getattr(args, "route_bag_source_label", None), fallback_label)
    metadata_summary = read_route_bag_metadata(getattr(args, "route_bag_metadata_yaml", None))
    dangerous_true_fields = sorted(set(label_dangerous + list(metadata_summary.get("dangerous_true_fields") or [])))
    unsafe_text_count = int(label_unsafe_count) + int(metadata_summary.get("unsafe_text_field_count") or 0)
    blocked_reasons = list(metadata_summary.get("blocked_reasons") or [])
    if label_dangerous:
        blocked_reasons.append("route_bag_source_label_dangerous_true_claim")
    if label_unsafe_count:
        blocked_reasons.append("route_bag_source_label_unsafe_text")
    if not db3_path_value:
        return route_bag_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_db3_missing"],
            metadata_summary=metadata_summary,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )

    db3_path = Path(db3_path_value).expanduser()
    db3_basename = db3_path.name
    if not db3_path.is_file():
        return route_bag_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_db3_missing_or_not_file"],
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )
    try:
        db3_size_bytes = db3_path.stat().st_size
        db3_sha256_prefix = route_bag_short_hash(db3_path)
    except OSError:
        return route_bag_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_db3_stat_or_hash_failed"],
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            db3_present=True,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )
    if db3_size_bytes <= 0:
        return route_bag_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_db3_empty"],
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            db3_present=True,
            db3_size_bytes=db3_size_bytes,
            db3_sha256_prefix=db3_sha256_prefix,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )
    try:
        db3_summary, db3_blocked_reasons, unsafe_topic_count = summarize_route_bag_db3(db3_path)
    except sqlite3.DatabaseError:
        return route_bag_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_db3_unreadable"],
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            db3_present=True,
            db3_read_ok=False,
            db3_size_bytes=db3_size_bytes,
            db3_sha256_prefix=db3_sha256_prefix,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )
    blocked_reasons.extend(db3_blocked_reasons)
    unsafe_field_count = int(unsafe_topic_count)
    if blocked_reasons or dangerous_true_fields or unsafe_text_count:
        return route_bag_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons,
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            db3_present=True,
            db3_read_ok=True,
            sqlite_schema_ok=bool(db3_summary["sqlite_schema_ok"]),
            db3_size_bytes=db3_size_bytes,
            db3_sha256_prefix=db3_sha256_prefix,
            topic_count=int(db3_summary["topic_count"]),
            message_count=int(db3_summary["message_count"]),
            timestamp_first_ns=db3_summary["timestamp_first_ns"],
            timestamp_last_ns=db3_summary["timestamp_last_ns"],
            sample_topic_names=list(db3_summary["sample_topic_names"]),
            dangerous_true_fields=dangerous_true_fields,
            unsafe_field_count=unsafe_field_count,
            unsafe_text_field_count=unsafe_text_count,
        )
    return {
        "schema": ROUTE_BAG_EVIDENCE_SCHEMA,
        "proof_scope": ROUTE_BAG_EVIDENCE_PROOF_SCOPE,
        "source": "route_bag_db3_sqlite_summary",
        "source_label": source_label,
        "status": "ready_not_route_execution_proof",
        "task_id": task_id,
        "task_id_source": task_id_source,
        "metadata_present": bool(metadata_summary.get("metadata_present")),
        "metadata_read_ok": bool(metadata_summary.get("metadata_read_ok")),
        "metadata_basename": metadata_summary.get("metadata_basename"),
        "metadata_size_bytes": int(metadata_summary.get("metadata_size_bytes") or 0),
        "metadata_sha256_prefix": metadata_summary.get("metadata_sha256_prefix"),
        "db3_present": True,
        "db3_read_ok": True,
        "sqlite_schema_ok": True,
        "db3_basename": db3_basename,
        "db3_size_bytes": db3_size_bytes,
        "db3_sha256_prefix": db3_sha256_prefix,
        "topic_count": int(db3_summary["topic_count"]),
        "message_count": int(db3_summary["message_count"]),
        "timestamp_first_ns": db3_summary["timestamp_first_ns"],
        "timestamp_last_ns": db3_summary["timestamp_last_ns"],
        "sample_topic_names": list(db3_summary["sample_topic_names"]),
        "blocked_reasons": [],
        "dangerous_true_fields": [],
        "unsafe_field_count": 0,
        "unsafe_text_field_count": 0,
        "next_required_evidence": [
            "live_nav2_pose_progress_or_route_execution_log",
            "delivery_record_or_operator_dropoff_confirmation",
        ],
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "live_nav2_run_proven": False,
        "route_execution_success": False,
        "connects_cloud_production": False,
    }


def build_route_bag_semantic_replay(args: argparse.Namespace, packet: dict[str, Any]) -> dict[str, Any]:
    # semantic replay 是 route bag 的可解释语义层，仍只读、可复现，并且不能升级为真实执行成功声明。
    task_id = str(packet.get("task_id") or args.run_id)
    task_id_source = str(packet.get("task_id_source") or "field_motion_evidence_packet")
    db3_path_value = getattr(args, "route_bag_db3", None)
    fallback_label = Path(db3_path_value).name if db3_path_value else "missing_route_bag_db3"
    source_label, label_dangerous, label_unsafe_count = safe_route_bag_source_label(getattr(args, "route_bag_source_label", None), fallback_label)
    metadata_summary = read_route_bag_metadata(getattr(args, "route_bag_metadata_yaml", None))
    dangerous_true_fields = sorted(set(label_dangerous + list(metadata_summary.get("dangerous_true_fields") or [])))
    unsafe_text_count = int(label_unsafe_count) + int(metadata_summary.get("unsafe_text_field_count") or 0)
    blocked_reasons = list(metadata_summary.get("blocked_reasons") or [])
    if label_dangerous:
        blocked_reasons.append("route_bag_semantic_source_label_dangerous_true_claim")
    if label_unsafe_count:
        blocked_reasons.append("route_bag_semantic_source_label_unsafe_text")
    if not db3_path_value:
        return route_bag_semantic_replay_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_semantic_db3_missing"],
            metadata_summary=metadata_summary,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )

    db3_path = Path(db3_path_value).expanduser()
    db3_basename = db3_path.name
    if not db3_path.is_file():
        return route_bag_semantic_replay_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_semantic_db3_missing_or_not_file"],
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )
    try:
        db3_size_bytes = db3_path.stat().st_size
        db3_sha256_prefix = route_bag_short_hash(db3_path)
    except OSError:
        return route_bag_semantic_replay_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_semantic_db3_stat_or_hash_failed"],
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            db3_present=True,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )
    if db3_size_bytes <= 0:
        return route_bag_semantic_replay_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_semantic_db3_empty"],
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            db3_present=True,
            db3_size_bytes=db3_size_bytes,
            db3_sha256_prefix=db3_sha256_prefix,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )
    try:
        db3_summary, db3_blocked_reasons, unsafe_topic_count = summarize_route_bag_semantic_replay(db3_path)
    except sqlite3.DatabaseError:
        return route_bag_semantic_replay_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_semantic_db3_unreadable"],
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            db3_present=True,
            db3_read_ok=False,
            db3_size_bytes=db3_size_bytes,
            db3_sha256_prefix=db3_sha256_prefix,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )

    blocked_reasons.extend(db3_blocked_reasons)
    unsafe_field_count = int(unsafe_topic_count)
    if blocked_reasons or dangerous_true_fields or unsafe_text_count:
        return route_bag_semantic_replay_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons,
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            db3_present=True,
            db3_read_ok=True,
            sqlite_schema_ok=bool(db3_summary["sqlite_schema_ok"]),
            db3_size_bytes=db3_size_bytes,
            db3_sha256_prefix=db3_sha256_prefix,
            topic_count=int(db3_summary["topic_count"]),
            message_count=int(db3_summary["message_count"]),
            timestamp_first_ns=db3_summary["timestamp_first_ns"],
            timestamp_last_ns=db3_summary["timestamp_last_ns"],
            sample_topic_names=list(db3_summary["sample_topic_names"]),
            semantic_sample_count=int(db3_summary["semantic_sample_count"]),
            semantic_decode_ok_count=int(db3_summary["semantic_decode_ok_count"]),
            semantic_decode_failed_count=int(db3_summary["semantic_decode_failed_count"]),
            semantic_topic_types=list(db3_summary["semantic_topic_types"]),
            laser_scan_summary=dict(db3_summary["laser_scan_summary"]),
            image_summary=dict(db3_summary["image_summary"]),
            tf_summary=dict(db3_summary["tf_summary"]),
            odometry_summary=dict(db3_summary["odometry_summary"]),
            diagnostic_array_summary=dict(db3_summary["diagnostic_array_summary"]),
            dangerous_true_fields=dangerous_true_fields,
            unsafe_field_count=unsafe_field_count,
            unsafe_text_field_count=unsafe_text_count,
        )
    return {
        "schema": ROUTE_BAG_SEMANTIC_REPLAY_SCHEMA,
        "proof_scope": ROUTE_BAG_SEMANTIC_REPLAY_PROOF_SCOPE,
        "source": "route_bag_db3_semantic_replay",
        "source_label": source_label,
        "status": "ready_not_route_execution_proof",
        "task_id": task_id,
        "task_id_source": task_id_source,
        "metadata_present": bool(metadata_summary.get("metadata_present")),
        "metadata_read_ok": bool(metadata_summary.get("metadata_read_ok")),
        "metadata_basename": metadata_summary.get("metadata_basename"),
        "metadata_size_bytes": int(metadata_summary.get("metadata_size_bytes") or 0),
        "metadata_sha256_prefix": metadata_summary.get("metadata_sha256_prefix"),
        "db3_present": True,
        "db3_read_ok": True,
        "sqlite_schema_ok": True,
        "db3_basename": db3_basename,
        "db3_size_bytes": db3_size_bytes,
        "db3_sha256_prefix": db3_sha256_prefix,
        "topic_count": int(db3_summary["topic_count"]),
        "message_count": int(db3_summary["message_count"]),
        "timestamp_first_ns": db3_summary["timestamp_first_ns"],
        "timestamp_last_ns": db3_summary["timestamp_last_ns"],
        "sample_topic_names": list(db3_summary["sample_topic_names"]),
        "semantic_sample_count": int(db3_summary["semantic_sample_count"]),
        "semantic_decode_ok_count": int(db3_summary["semantic_decode_ok_count"]),
        "semantic_decode_failed_count": int(db3_summary["semantic_decode_failed_count"]),
        "semantic_topic_types": list(db3_summary["semantic_topic_types"]),
        "laser_scan_summary": db3_summary["laser_scan_summary"],
        "image_summary": db3_summary["image_summary"],
        "tf_summary": db3_summary["tf_summary"],
        "odometry_summary": db3_summary["odometry_summary"],
        "diagnostic_array_summary": db3_summary["diagnostic_array_summary"],
        "blocked_reasons": [],
        "dangerous_true_fields": [],
        "unsafe_field_count": 0,
        "unsafe_text_field_count": 0,
        "next_required_evidence": [
            "live_nav2_pose_progress_or_route_execution_log",
            "delivery_record_or_operator_dropoff_confirmation",
        ],
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "live_nav2_run_proven": False,
        "route_execution_success": False,
        "connects_cloud_production": False,
    }


def build_route_bag_full_semantic_decode_matrix(args: argparse.Namespace, packet: dict[str, Any]) -> dict[str, Any]:
    # full semantic matrix 证明“哪些 topic/type 可解码”，但不证明 route execution 或 delivery 成功。
    task_id = str(packet.get("task_id") or args.run_id)
    task_id_source = str(packet.get("task_id_source") or "field_motion_evidence_packet")
    db3_path_value = getattr(args, "route_bag_db3", None)
    fallback_label = Path(db3_path_value).name if db3_path_value else "missing_route_bag_db3"
    source_label, label_dangerous, label_unsafe_count = safe_route_bag_source_label(getattr(args, "route_bag_source_label", None), fallback_label)
    metadata_summary = read_route_bag_metadata(getattr(args, "route_bag_metadata_yaml", None))
    dangerous_true_fields = sorted(set(label_dangerous + list(metadata_summary.get("dangerous_true_fields") or [])))
    unsafe_text_count = int(label_unsafe_count) + int(metadata_summary.get("unsafe_text_field_count") or 0)
    blocked_reasons = list(metadata_summary.get("blocked_reasons") or [])
    if label_dangerous:
        blocked_reasons.append("route_bag_full_semantic_decode_matrix_source_label_dangerous_true_claim")
    if label_unsafe_count:
        blocked_reasons.append("route_bag_full_semantic_decode_matrix_source_label_unsafe_text")
    if not db3_path_value:
        return route_bag_full_semantic_decode_matrix_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_full_semantic_decode_matrix_db3_missing"],
            metadata_summary=metadata_summary,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )

    db3_path = Path(db3_path_value).expanduser()
    db3_basename = db3_path.name
    if not db3_path.is_file():
        return route_bag_full_semantic_decode_matrix_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_full_semantic_decode_matrix_db3_missing_or_not_file"],
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )
    try:
        db3_size_bytes = db3_path.stat().st_size
        db3_sha256_prefix = route_bag_short_hash(db3_path)
    except OSError:
        return route_bag_full_semantic_decode_matrix_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_full_semantic_decode_matrix_db3_stat_or_hash_failed"],
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            db3_present=True,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )
    if db3_size_bytes <= 0:
        return route_bag_full_semantic_decode_matrix_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_full_semantic_decode_matrix_db3_empty"],
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            db3_present=True,
            db3_size_bytes=db3_size_bytes,
            db3_sha256_prefix=db3_sha256_prefix,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )
    try:
        db3_summary, db3_blocked_reasons, unsafe_topic_or_type_count = summarize_route_bag_full_semantic_decode_matrix(db3_path)
    except sqlite3.DatabaseError:
        return route_bag_full_semantic_decode_matrix_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_full_semantic_decode_matrix_db3_unreadable"],
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            db3_present=True,
            db3_read_ok=False,
            db3_size_bytes=db3_size_bytes,
            db3_sha256_prefix=db3_sha256_prefix,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )

    blocked_reasons.extend(db3_blocked_reasons)
    unsafe_field_count = int(unsafe_topic_or_type_count)
    summary_kwargs = {
        "metadata_summary": metadata_summary,
        "db3_basename": db3_basename,
        "db3_present": True,
        "db3_read_ok": True,
        "sqlite_schema_ok": bool(db3_summary["sqlite_schema_ok"]),
        "db3_size_bytes": db3_size_bytes,
        "db3_sha256_prefix": db3_sha256_prefix,
        "topic_count": int(db3_summary["topic_count"]),
        "message_count": int(db3_summary["message_count"]),
        "timestamp_first_ns": db3_summary["timestamp_first_ns"],
        "timestamp_last_ns": db3_summary["timestamp_last_ns"],
        "sample_topic_names": list(db3_summary["sample_topic_names"]),
        "topic_type_count": int(db3_summary["topic_type_count"]),
        "decoded_topic_type_count": int(db3_summary["decoded_topic_type_count"]),
        "unsupported_topic_type_count": int(db3_summary["unsupported_topic_type_count"]),
        "failed_topic_type_count": int(db3_summary["failed_topic_type_count"]),
        "decoded_message_sample_count": int(db3_summary["decoded_message_sample_count"]),
        "decode_failed_message_sample_count": int(db3_summary["decode_failed_message_sample_count"]),
        "unsupported_message_sample_count": int(db3_summary["unsupported_message_sample_count"]),
        "coverage_ratio": float(db3_summary["coverage_ratio"]),
        "topic_type_matrix": list(db3_summary["topic_type_matrix"]),
        "dangerous_true_fields": dangerous_true_fields,
        "unsafe_field_count": unsafe_field_count,
        "unsafe_text_field_count": unsafe_text_count,
    }
    ready = (
        bool(db3_summary["sqlite_schema_ok"])
        and int(db3_summary["decoded_topic_type_count"]) > 0
        and unsafe_field_count == 0
        and not dangerous_true_fields
        and unsafe_text_count == 0
    )
    if not ready:
        return route_bag_full_semantic_decode_matrix_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons,
            **summary_kwargs,
        )
    return {
        "schema": ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_SCHEMA,
        "proof_scope": ROUTE_BAG_FULL_SEMANTIC_DECODE_MATRIX_PROOF_SCOPE,
        "source": "route_bag_db3_full_semantic_decode_matrix",
        "source_label": source_label,
        "status": "ready_not_route_execution_proof",
        "task_id": task_id,
        "task_id_source": task_id_source,
        "metadata_present": bool(metadata_summary.get("metadata_present")),
        "metadata_read_ok": bool(metadata_summary.get("metadata_read_ok")),
        "metadata_basename": metadata_summary.get("metadata_basename"),
        "metadata_size_bytes": int(metadata_summary.get("metadata_size_bytes") or 0),
        "metadata_sha256_prefix": metadata_summary.get("metadata_sha256_prefix"),
        "db3_present": True,
        "db3_read_ok": True,
        "sqlite_schema_ok": True,
        "db3_basename": db3_basename,
        "db3_size_bytes": db3_size_bytes,
        "db3_sha256_prefix": db3_sha256_prefix,
        "topic_count": int(db3_summary["topic_count"]),
        "message_count": int(db3_summary["message_count"]),
        "timestamp_first_ns": db3_summary["timestamp_first_ns"],
        "timestamp_last_ns": db3_summary["timestamp_last_ns"],
        "sample_topic_names": list(db3_summary["sample_topic_names"]),
        "topic_type_count": int(db3_summary["topic_type_count"]),
        "decoded_topic_type_count": int(db3_summary["decoded_topic_type_count"]),
        "unsupported_topic_type_count": int(db3_summary["unsupported_topic_type_count"]),
        "failed_topic_type_count": int(db3_summary["failed_topic_type_count"]),
        "decoded_message_sample_count": int(db3_summary["decoded_message_sample_count"]),
        "decode_failed_message_sample_count": int(db3_summary["decode_failed_message_sample_count"]),
        "unsupported_message_sample_count": int(db3_summary["unsupported_message_sample_count"]),
        "coverage_ratio": float(db3_summary["coverage_ratio"]),
        "topic_type_matrix": list(db3_summary["topic_type_matrix"]),
        "blocked_reasons": sorted(set(reason for reason in blocked_reasons if reason)),
        "dangerous_true_fields": [],
        "unsafe_field_count": 0,
        "unsafe_text_field_count": 0,
        "next_required_evidence": [
            "decoder_for_unsupported_route_bag_topic_types",
            "clean_route_bag_payload_samples_without_decode_failures",
            "live_nav2_pose_progress_or_route_execution_log",
            "delivery_record_or_operator_dropoff_confirmation",
        ],
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "live_nav2_run_proven": False,
        "route_execution_success": False,
        "connects_cloud_production": False,
    }


def build_route_bag_pose_progress_replay(args: argparse.Namespace, packet: dict[str, Any]) -> dict[str, Any]:
    # pose progress replay 仍然只读 DB3 摘要；它证明的是位姿样本可复核，不是 live Nav2 或 delivery 成功。
    task_id = str(packet.get("task_id") or args.run_id)
    task_id_source = str(packet.get("task_id_source") or "field_motion_evidence_packet")
    db3_path_value = getattr(args, "route_bag_db3", None)
    fallback_label = Path(db3_path_value).name if db3_path_value else "missing_route_bag_db3"
    source_label, label_dangerous, label_unsafe_count = safe_route_bag_source_label(getattr(args, "route_bag_source_label", None), fallback_label)
    metadata_summary = read_route_bag_metadata(getattr(args, "route_bag_metadata_yaml", None))
    dangerous_true_fields = sorted(set(label_dangerous + list(metadata_summary.get("dangerous_true_fields") or [])))
    unsafe_text_count = int(label_unsafe_count) + int(metadata_summary.get("unsafe_text_field_count") or 0)
    blocked_reasons = list(metadata_summary.get("blocked_reasons") or [])
    if label_dangerous:
        blocked_reasons.append("route_bag_pose_progress_source_label_dangerous_true_claim")
    if label_unsafe_count:
        blocked_reasons.append("route_bag_pose_progress_source_label_unsafe_text")
    if not db3_path_value:
        return route_bag_pose_progress_replay_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_pose_progress_db3_missing"],
            metadata_summary=metadata_summary,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )

    db3_path = Path(db3_path_value).expanduser()
    db3_basename = db3_path.name
    if not db3_path.is_file():
        return route_bag_pose_progress_replay_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_pose_progress_db3_missing_or_not_file"],
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )
    try:
        db3_size_bytes = db3_path.stat().st_size
        db3_sha256_prefix = route_bag_short_hash(db3_path)
    except OSError:
        return route_bag_pose_progress_replay_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_pose_progress_db3_stat_or_hash_failed"],
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            db3_present=True,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )
    if db3_size_bytes <= 0:
        return route_bag_pose_progress_replay_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_pose_progress_db3_empty"],
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            db3_present=True,
            db3_size_bytes=db3_size_bytes,
            db3_sha256_prefix=db3_sha256_prefix,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )
    try:
        db3_summary, db3_blocked_reasons, unsafe_topic_count = summarize_route_bag_pose_progress_replay(db3_path)
    except sqlite3.DatabaseError:
        return route_bag_pose_progress_replay_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_pose_progress_db3_unreadable"],
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            db3_present=True,
            db3_read_ok=False,
            db3_size_bytes=db3_size_bytes,
            db3_sha256_prefix=db3_sha256_prefix,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )

    blocked_reasons.extend(db3_blocked_reasons)
    unsafe_field_count = int(unsafe_topic_count)
    if blocked_reasons or dangerous_true_fields or unsafe_text_count:
        return route_bag_pose_progress_replay_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons,
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            db3_present=True,
            db3_read_ok=True,
            sqlite_schema_ok=bool(db3_summary["sqlite_schema_ok"]),
            db3_size_bytes=db3_size_bytes,
            db3_sha256_prefix=db3_sha256_prefix,
            topic_count=int(db3_summary["topic_count"]),
            message_count=int(db3_summary["message_count"]),
            timestamp_first_ns=db3_summary["timestamp_first_ns"],
            timestamp_last_ns=db3_summary["timestamp_last_ns"],
            sample_topic_names=list(db3_summary["sample_topic_names"]),
            pose_sample_count=int(db3_summary["pose_sample_count"]),
            pose_decode_ok_count=int(db3_summary["pose_decode_ok_count"]),
            pose_decode_failed_count=int(db3_summary["pose_decode_failed_count"]),
            pose_topic_types=list(db3_summary["pose_topic_types"]),
            pose_frame_pairs=[list(pair) for pair in db3_summary["pose_frame_pairs"]],
            pose_time_span_ns=int(db3_summary["pose_time_span_ns"]),
            start_pose=db3_summary["start_pose"],
            end_pose=db3_summary["end_pose"],
            displacement_m=float(db3_summary["displacement_m"]),
            nonzero_pose_progress_observed=bool(db3_summary["nonzero_pose_progress_observed"]),
            dangerous_true_fields=dangerous_true_fields,
            unsafe_field_count=unsafe_field_count,
            unsafe_text_field_count=unsafe_text_count,
        )
    return {
        "schema": ROUTE_BAG_POSE_PROGRESS_REPLAY_SCHEMA,
        "proof_scope": ROUTE_BAG_POSE_PROGRESS_REPLAY_PROOF_SCOPE,
        "source": "route_bag_db3_pose_progress_replay",
        "source_label": source_label,
        "status": "ready_not_live_nav2_proof",
        "task_id": task_id,
        "task_id_source": task_id_source,
        "metadata_present": bool(metadata_summary.get("metadata_present")),
        "metadata_read_ok": bool(metadata_summary.get("metadata_read_ok")),
        "metadata_basename": metadata_summary.get("metadata_basename"),
        "metadata_size_bytes": int(metadata_summary.get("metadata_size_bytes") or 0),
        "metadata_sha256_prefix": metadata_summary.get("metadata_sha256_prefix"),
        "db3_present": True,
        "db3_read_ok": True,
        "sqlite_schema_ok": True,
        "db3_basename": db3_basename,
        "db3_size_bytes": db3_size_bytes,
        "db3_sha256_prefix": db3_sha256_prefix,
        "topic_count": int(db3_summary["topic_count"]),
        "message_count": int(db3_summary["message_count"]),
        "timestamp_first_ns": db3_summary["timestamp_first_ns"],
        "timestamp_last_ns": db3_summary["timestamp_last_ns"],
        "sample_topic_names": list(db3_summary["sample_topic_names"]),
        "sample_count": int(db3_summary["pose_sample_count"]),
        "pose_sample_count": int(db3_summary["pose_sample_count"]),
        "pose_decode_ok_count": int(db3_summary["pose_decode_ok_count"]),
        "pose_decode_failed_count": int(db3_summary["pose_decode_failed_count"]),
        "pose_topic_types": list(db3_summary["pose_topic_types"]),
        "pose_frame_pairs": [list(pair) for pair in db3_summary["pose_frame_pairs"]],
        "pose_time_span_ns": int(db3_summary["pose_time_span_ns"]),
        "start_pose": db3_summary["start_pose"],
        "end_pose": db3_summary["end_pose"],
        "displacement_m": float(db3_summary["displacement_m"]),
        "nonzero_pose_progress_observed": bool(db3_summary["nonzero_pose_progress_observed"]),
        "blocked_reasons": [],
        "dangerous_true_fields": [],
        "unsafe_field_count": 0,
        "unsafe_text_field_count": 0,
        "next_required_evidence": [
            "safe_route_bag_db3_with_pose_progress_messages",
            "same_task_route_bag_metadata_yaml",
            "live_nav2_pose_progress_or_route_execution_log",
            "delivery_record_or_operator_dropoff_confirmation",
        ],
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "live_nav2_run_proven": False,
        "route_execution_success": False,
        "connects_cloud_production": False,
    }


def build_route_bag_payload_replay(args: argparse.Namespace, packet: dict[str, Any]) -> dict[str, Any]:
    # payload replay 是 route bag 的更深一层只读摘要，但仍然不能被上层读链路误认为路线成功。
    task_id = str(packet.get("task_id") or args.run_id)
    task_id_source = str(packet.get("task_id_source") or "field_motion_evidence_packet")
    db3_path_value = getattr(args, "route_bag_db3", None)
    fallback_label = Path(db3_path_value).name if db3_path_value else "missing_route_bag_db3"
    source_label, label_dangerous, label_unsafe_count = safe_route_bag_source_label(getattr(args, "route_bag_source_label", None), fallback_label)
    metadata_summary = read_route_bag_metadata(getattr(args, "route_bag_metadata_yaml", None))
    dangerous_true_fields = sorted(set(label_dangerous + list(metadata_summary.get("dangerous_true_fields") or [])))
    unsafe_text_count = int(label_unsafe_count) + int(metadata_summary.get("unsafe_text_field_count") or 0)
    blocked_reasons = list(metadata_summary.get("blocked_reasons") or [])
    if label_dangerous:
        blocked_reasons.append("route_bag_payload_source_label_dangerous_true_claim")
    if label_unsafe_count:
        blocked_reasons.append("route_bag_payload_source_label_unsafe_text")
    if not db3_path_value:
        return route_bag_payload_replay_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_payload_db3_missing"],
            metadata_summary=metadata_summary,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )

    db3_path = Path(db3_path_value).expanduser()
    db3_basename = db3_path.name
    if not db3_path.is_file():
        return route_bag_payload_replay_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_payload_db3_missing_or_not_file"],
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )
    try:
        db3_size_bytes = db3_path.stat().st_size
        db3_sha256_prefix = route_bag_short_hash(db3_path)
    except OSError:
        return route_bag_payload_replay_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_payload_db3_stat_or_hash_failed"],
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            db3_present=True,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )
    if db3_size_bytes <= 0:
        return route_bag_payload_replay_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_payload_db3_empty"],
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            db3_present=True,
            db3_size_bytes=db3_size_bytes,
            db3_sha256_prefix=db3_sha256_prefix,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )
    try:
        db3_summary, db3_blocked_reasons, unsafe_topic_count = summarize_route_bag_payload_replay(db3_path)
    except sqlite3.DatabaseError:
        return route_bag_payload_replay_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons + ["route_bag_payload_db3_unreadable"],
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            db3_present=True,
            db3_read_ok=False,
            db3_size_bytes=db3_size_bytes,
            db3_sha256_prefix=db3_sha256_prefix,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_text_field_count=unsafe_text_count,
        )
    blocked_reasons.extend(db3_blocked_reasons)
    unsafe_field_count = int(unsafe_topic_count)
    if blocked_reasons or dangerous_true_fields or unsafe_text_count:
        return route_bag_payload_replay_blocked_summary(
            task_id,
            task_id_source,
            source_label,
            blocked_reasons,
            metadata_summary=metadata_summary,
            db3_basename=db3_basename,
            db3_present=True,
            db3_read_ok=True,
            sqlite_schema_ok=bool(db3_summary["sqlite_schema_ok"]),
            db3_size_bytes=db3_size_bytes,
            db3_sha256_prefix=db3_sha256_prefix,
            topic_count=int(db3_summary["topic_count"]),
            message_count=int(db3_summary["message_count"]),
            timestamp_first_ns=db3_summary["timestamp_first_ns"],
            timestamp_last_ns=db3_summary["timestamp_last_ns"],
            sample_topic_names=list(db3_summary["sample_topic_names"]),
            payload_sample_count=int(db3_summary["payload_sample_count"]),
            payload_size_min_bytes=int(db3_summary["payload_size_min_bytes"]),
            payload_size_max_bytes=int(db3_summary["payload_size_max_bytes"]),
            payload_size_avg_bytes=float(db3_summary["payload_size_avg_bytes"]),
            payload_sha256_prefix_samples=list(db3_summary["payload_sha256_prefix_samples"]),
            dangerous_true_fields=dangerous_true_fields,
            unsafe_field_count=unsafe_field_count,
            unsafe_text_field_count=unsafe_text_count,
        )
    return {
        "schema": ROUTE_BAG_PAYLOAD_REPLAY_SCHEMA,
        "proof_scope": ROUTE_BAG_PAYLOAD_REPLAY_PROOF_SCOPE,
        "source": "route_bag_db3_payload_replay",
        "source_label": source_label,
        "status": "ready_not_route_execution_proof",
        "task_id": task_id,
        "task_id_source": task_id_source,
        "metadata_present": bool(metadata_summary.get("metadata_present")),
        "metadata_read_ok": bool(metadata_summary.get("metadata_read_ok")),
        "metadata_basename": metadata_summary.get("metadata_basename"),
        "metadata_size_bytes": int(metadata_summary.get("metadata_size_bytes") or 0),
        "metadata_sha256_prefix": metadata_summary.get("metadata_sha256_prefix"),
        "db3_present": True,
        "db3_read_ok": True,
        "sqlite_schema_ok": True,
        "db3_basename": db3_basename,
        "db3_size_bytes": db3_size_bytes,
        "db3_sha256_prefix": db3_sha256_prefix,
        "topic_count": int(db3_summary["topic_count"]),
        "message_count": int(db3_summary["message_count"]),
        "timestamp_first_ns": db3_summary["timestamp_first_ns"],
        "timestamp_last_ns": db3_summary["timestamp_last_ns"],
        "sample_topic_names": list(db3_summary["sample_topic_names"]),
        "payload_sample_count": int(db3_summary["payload_sample_count"]),
        "payload_size_min_bytes": int(db3_summary["payload_size_min_bytes"]),
        "payload_size_max_bytes": int(db3_summary["payload_size_max_bytes"]),
        "payload_size_avg_bytes": float(db3_summary["payload_size_avg_bytes"]),
        "payload_sha256_prefix_samples": list(db3_summary["payload_sha256_prefix_samples"]),
        "blocked_reasons": [],
        "dangerous_true_fields": [],
        "unsafe_field_count": 0,
        "unsafe_text_field_count": 0,
        "next_required_evidence": [
            "safe_route_bag_payload_replay_db3_with_nonempty_payloads",
            "live_nav2_pose_progress_or_route_execution_log",
            "delivery_record_or_operator_dropoff_confirmation",
        ],
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "live_nav2_run_proven": False,
        "route_execution_success": False,
        "connects_cloud_production": False,
    }


def nav2_goal_blocked_summary(
    task_id: str,
    task_id_source: str,
    blocked_reasons: list[str],
    *,
    proof_json_present: bool,
    proof_json_read_ok: bool,
    source_schema: str | None = None,
    dangerous_true_fields: list[str] | None = None,
    unsafe_fields: list[str] | None = None,
    unsafe_text_fields: list[str] | None = None,
) -> dict[str, Any]:
    # 缺失、schema mismatch 或安全阻断时仍输出同形摘要，方便 O6/O7 fail-closed 回读。
    reasons = sorted(set(reason for reason in blocked_reasons if reason))
    return {
        "schema": NAV2_GOAL_EXECUTION_EVIDENCE_SCHEMA,
        "proof_scope": NAV2_GOAL_EXECUTION_EVIDENCE_PROOF_SCOPE,
        "source": "o11_nav2_goal_execution_proof_json",
        "source_schema": source_schema,
        "status": "blocked_not_proven",
        "task_id": task_id,
        "task_id_source": task_id_source,
        "proof_json_present": proof_json_present,
        "proof_json_read_ok": proof_json_read_ok,
        "source_status": None,
        "proof_status": None,
        "result_status": None,
        "result_status_code": None,
        "goal_sent": False,
        "goal_accepted": False,
        "result_received": False,
        "nav2_goal_execution_proven": False,
        "base_motion_command_nonzero_proven": False,
        "base_command_mode": None,
        "requested_base_command_mode": None,
        "feedback_sample_count": 0,
        "goal_request": {"frame_id": None, "x": None, "y": None, "yaw": None},
        "base_feedback_summary": {
            "wheel_feedback_lr_nonzero_proven": False,
            "nonzero_sample_count": 0,
            "imu_attitude_delta_observed": False,
        },
        "base_command_summary": {
            "nonzero_command_observed": False,
            "nonzero_command_count": 0,
            "latest_nonzero_command_mode": None,
        },
        "blocked_reasons": reasons,
        "dangerous_true_fields": sorted(set(dangerous_true_fields or [])),
        "unsafe_field_count": len(set(unsafe_fields or [])),
        "unsafe_text_field_count": len(set(unsafe_text_fields or [])),
        "next_required_evidence": [
            "o11_nav2_goal_execution_proof_json_with_safe_schema",
            "nav2_goal_execution_proven_true",
            "delivery_record_or_operator_dropoff_confirmation",
        ],
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
    }


def nav2_goal_execution_next_evidence(evidence: dict[str, Any], source_robot_control_executed: bool) -> list[str]:
    # next evidence 说明还缺什么，不把 O11 的执行字段升级成 field packet 主动作。
    next_required = []
    if not evidence.get("goal_sent"):
        next_required.append("nav2_goal_sent")
    if not evidence.get("goal_accepted"):
        next_required.append("nav2_goal_accepted")
    if not evidence.get("result_received"):
        next_required.append("nav2_goal_result_received")
    if evidence.get("result_status") != "succeeded":
        next_required.append("nav2_goal_succeeded")
    if not evidence.get("base_motion_command_nonzero_proven"):
        next_required.append("nonzero_base_motion_command")
    if not (evidence.get("base_feedback_summary") or {}).get("wheel_feedback_lr_nonzero_proven"):
        next_required.append("same_window_wheel_feedback_lr_nonzero")
    if not evidence.get("nav2_goal_execution_proven"):
        next_required.append("nav2_goal_execution_proven_true")
    if source_robot_control_executed:
        next_required.append("delivery_record_required_after_o11_execution_claim")
    next_required.append("delivery_record_or_operator_dropoff_confirmation")
    return sorted(set(next_required))


def build_nav2_goal_execution_evidence(args: argparse.Namespace, packet: dict[str, Any]) -> dict[str, Any]:
    # O11 proof 是可选上游证据；本摘要只消费白名单字段，并且不能覆盖 field packet lineage。
    task_id = str(packet.get("task_id") or args.run_id)
    task_id_source = str(packet.get("task_id_source") or "field_motion_evidence_packet")
    proof_path = getattr(args, "nav2_goal_proof_json", None)
    if not proof_path:
        return nav2_goal_blocked_summary(
            task_id,
            task_id_source,
            ["nav2_goal_proof_json_missing"],
            proof_json_present=False,
            proof_json_read_ok=False,
        )
    try:
        loaded = json.loads(Path(proof_path).expanduser().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return nav2_goal_blocked_summary(
            task_id,
            task_id_source,
            ["nav2_goal_proof_json_unreadable"],
            proof_json_present=True,
            proof_json_read_ok=False,
        )
    if not isinstance(loaded, dict):
        return nav2_goal_blocked_summary(
            task_id,
            task_id_source,
            ["nav2_goal_proof_json_root_not_object"],
            proof_json_present=True,
            proof_json_read_ok=True,
        )

    source_schema = safe_nav2_goal_text(loaded.get("schema"))
    dangerous_true_fields, unsafe_fields, unsafe_text_fields = collect_nav2_goal_proof_safety_issues(loaded)
    if "schema" in unsafe_text_fields:
        source_schema = None
    if dangerous_true_fields or unsafe_fields or unsafe_text_fields:
        reasons = []
        if dangerous_true_fields:
            reasons.append("nav2_goal_proof_dangerous_true_claim")
        if unsafe_fields or unsafe_text_fields:
            reasons.append("nav2_goal_proof_unsafe_field_or_text")
        return nav2_goal_blocked_summary(
            task_id,
            task_id_source,
            reasons,
            proof_json_present=True,
            proof_json_read_ok=True,
            source_schema=source_schema,
            dangerous_true_fields=dangerous_true_fields,
            unsafe_fields=unsafe_fields,
            unsafe_text_fields=unsafe_text_fields,
        )
    if loaded.get("schema") != O11_NAV2_GOAL_PROOF_SCHEMA:
        return nav2_goal_blocked_summary(
            task_id,
            task_id_source,
            ["nav2_goal_proof_schema_mismatch"],
            proof_json_present=True,
            proof_json_read_ok=True,
            source_schema=source_schema,
        )

    goal_request = loaded.get("goal_request") if isinstance(loaded.get("goal_request"), dict) else {}
    base_feedback = loaded.get("base_feedback_summary") if isinstance(loaded.get("base_feedback_summary"), dict) else {}
    base_command = loaded.get("base_command_summary") if isinstance(loaded.get("base_command_summary"), dict) else {}
    evidence = {
        "schema": NAV2_GOAL_EXECUTION_EVIDENCE_SCHEMA,
        "proof_scope": NAV2_GOAL_EXECUTION_EVIDENCE_PROOF_SCOPE,
        "source": "o11_nav2_goal_execution_proof_json",
        "source_schema": O11_NAV2_GOAL_PROOF_SCHEMA,
        "status": "blocked_not_proven",
        "task_id": task_id,
        "task_id_source": task_id_source,
        "proof_json_present": True,
        "proof_json_read_ok": True,
        "source_status": safe_nav2_goal_text(loaded.get("status")),
        "proof_status": safe_nav2_goal_text(loaded.get("proof_status")),
        "result_status": safe_nav2_goal_text(loaded.get("result_status")),
        "result_status_code": safe_nav2_goal_int(loaded.get("result_status_code")),
        "goal_sent": safe_nav2_goal_bool(loaded.get("goal_sent")),
        "goal_accepted": safe_nav2_goal_bool(loaded.get("goal_accepted")),
        "result_received": safe_nav2_goal_bool(loaded.get("result_received")),
        "nav2_goal_execution_proven": safe_nav2_goal_bool(loaded.get("nav2_goal_execution_proven")),
        "base_motion_command_nonzero_proven": safe_nav2_goal_bool(loaded.get("base_motion_command_nonzero_proven")),
        "base_command_mode": safe_nav2_goal_text(loaded.get("base_command_mode")),
        "requested_base_command_mode": safe_nav2_goal_text(loaded.get("requested_base_command_mode")),
        "feedback_sample_count": safe_nav2_goal_int(loaded.get("feedback_sample_count")) or 0,
        "goal_request": {
            "frame_id": safe_nav2_goal_text(goal_request.get("frame_id")),
            "x": safe_nav2_goal_float(goal_request.get("x")),
            "y": safe_nav2_goal_float(goal_request.get("y")),
            "yaw": safe_nav2_goal_float(goal_request.get("yaw")),
        },
        "base_feedback_summary": {
            "wheel_feedback_lr_nonzero_proven": safe_nav2_goal_bool(base_feedback.get("wheel_feedback_lr_nonzero_proven")),
            "nonzero_sample_count": safe_nav2_goal_int(base_feedback.get("nonzero_sample_count")) or 0,
            "imu_attitude_delta_observed": safe_nav2_goal_bool(base_feedback.get("imu_attitude_delta_observed")),
        },
        "base_command_summary": {
            "nonzero_command_observed": safe_nav2_goal_bool(base_command.get("nonzero_command_observed")),
            "nonzero_command_count": safe_nav2_goal_int(base_command.get("nonzero_command_count")) or 0,
            "latest_nonzero_command_mode": safe_nav2_goal_text(base_command.get("latest_nonzero_command_mode")),
        },
        "dangerous_true_fields": [],
        "unsafe_field_count": 0,
        "unsafe_text_field_count": 0,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
    }
    blocked_reasons = []
    if not evidence["nav2_goal_execution_proven"]:
        blocked_reasons.append("nav2_goal_execution_not_proven")
    if evidence["goal_request"]["frame_id"] is None:
        blocked_reasons.append("nav2_goal_request_missing")
    if evidence["result_status"] != "succeeded":
        blocked_reasons.append("nav2_goal_result_not_succeeded")
    if not evidence["base_motion_command_nonzero_proven"]:
        blocked_reasons.append("base_motion_command_nonzero_missing")
    if not evidence["base_feedback_summary"]["wheel_feedback_lr_nonzero_proven"]:
        blocked_reasons.append("wheel_feedback_lr_nonzero_missing")
    evidence["blocked_reasons"] = sorted(set(blocked_reasons))
    evidence["next_required_evidence"] = nav2_goal_execution_next_evidence(
        evidence,
        source_robot_control_executed=safe_nav2_goal_bool(loaded.get("robot_control_executed")),
    )
    if not evidence["blocked_reasons"]:
        evidence["status"] = "ready_not_delivery_proof"
    return evidence


def extract_packet_lineage(source_manifest: dict[str, Any], run_id: str) -> dict[str, Any]:
    # 6 月现场 material 的 task_id 为空时，packet 需要稳定 fallback，方便 O6/O7 用同一键归档与读取。
    loaded = source_manifest.get("loaded")
    route_id = None
    source_task_id = None
    if isinstance(loaded, dict):
        samples = loaded.get("samples")
        if isinstance(samples, list):
            for sample in samples:
                if not isinstance(sample, dict):
                    continue
                context = sample.get("context")
                if isinstance(context, dict):
                    if not source_task_id and context.get("task_id"):
                        source_task_id = str(context.get("task_id"))
                    if not route_id and context.get("route_id"):
                        route_id = str(context.get("route_id"))
                if source_task_id and route_id:
                    break
    if source_task_id:
        return {
            "task_id": source_task_id,
            "task_id_source": "source_manifest.context.task_id",
            "route_id": route_id,
            "lineage_blocked_reason": None,
        }
    return {
        "task_id": run_id,
        "task_id_source": "run_id_fallback_due_missing_source_task_id",
        "route_id": route_id,
        "lineage_blocked_reason": "source_manifest_task_id_missing",
    }


def read_text_if_file(path: Path) -> str:
    # motion log 都是小文本，统一按 UTF-8 容错读取，避免一处 decode 失败拖垮整个 packet。
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def parse_named_float(text: str, label: str) -> float | None:
    # odom/tf 文本没有结构化 schema，这里只做最小正则提取，不把任意数字误当作 pose。
    match = re.search(rf"{re.escape(label)}:\s*([-+]?\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else None


def parse_motion_log_summary(root: Path | None, route_info: dict[str, Any]) -> dict[str, Any]:
    # remote_capture 只作为“现场 motion evidence”补强；没有 rosbag 时也不能把它升级成 delivery proof。
    if root is None:
        return {
            "present": False,
            "path": None,
            "live_motion_evidence_present": False,
            "live_nav2_log_present": False,
            "motion_log_present": False,
            "nonzero_cmd_vel_log_present": False,
            "nonzero_odom_evidence_present": bool(route_info.get("nonzero_displacement_observed")),
            "nonzero_tf_evidence_present": False,
            "direct_odom_capture_nonzero": False,
            "direct_tf_capture_nonzero": False,
            "route_pose_nonzero": bool(route_info.get("nonzero_displacement_observed")),
            "evidence_sources": [],
            "blocked_reasons": ["motion_log_root_missing"],
        }
    present_files = sorted(item.name for item in root.iterdir() if item.is_file()) if root.is_dir() else []
    if not root.is_dir():
        return {
            "present": False,
            "path": str(root),
            "live_motion_evidence_present": False,
            "live_nav2_log_present": False,
            "motion_log_present": False,
            "nonzero_cmd_vel_log_present": False,
            "nonzero_odom_evidence_present": bool(route_info.get("nonzero_displacement_observed")),
            "nonzero_tf_evidence_present": False,
            "direct_odom_capture_nonzero": False,
            "direct_tf_capture_nonzero": False,
            "route_pose_nonzero": bool(route_info.get("nonzero_displacement_observed")),
            "evidence_sources": [],
            "blocked_reasons": ["motion_log_root_not_directory"],
        }
    pulse_sources = []
    nonzero_cmd_vel_log_present = False
    for name in ("pulse_and_stop.log", "pulse_and_stop2.log"):
        path = root / name
        text = read_text_if_file(path)
        if not text:
            continue
        match = re.search(r"linear=geometry_msgs\.msg\.Vector3\(x=([-+]?\d+(?:\.\d+)?)", text)
        if match and abs(float(match.group(1))) > 1e-6:
            nonzero_cmd_vel_log_present = True
            pulse_sources.append(f"{name}:nonzero_cmd_vel")
    learn_log = read_text_if_file(root / "learn_launch.log")
    live_nav2_log_present = "route_data_recorder" in learn_log or "slam_toolbox" in learn_log
    learn_waypoint_nonzero = False
    if learn_log:
        for match in re.finditer(r"Saved waypoint #\d+ at \(([-+]?\d+(?:\.\d+)?),\s*([-+]?\d+(?:\.\d+)?)\)", learn_log):
            x_value = float(match.group(1))
            y_value = float(match.group(2))
            if abs(x_value) > 1e-6 or abs(y_value) > 1e-6:
                learn_waypoint_nonzero = True
                break
    odom_sources = []
    direct_odom_capture_nonzero = False
    for path in sorted(root.glob("odom_after_motion*.txt")):
        text = read_text_if_file(path)
        x_value = parse_named_float(text, "x")
        y_value = parse_named_float(text, "y")
        if (x_value is not None and abs(x_value) > 1e-6) or (y_value is not None and abs(y_value) > 1e-6):
            direct_odom_capture_nonzero = True
            odom_sources.append(f"{path.name}:nonzero_pose")
    tf_sources = []
    direct_tf_capture_nonzero = False
    for path in sorted(root.glob("tf_after_motion*.txt")):
        text = read_text_if_file(path)
        if re.search(r"translation:\s*\n\s*x:\s*([-+]?\d+(?:\.\d+)?)", text):
            for match in re.finditer(r"translation:\s*\n\s*x:\s*([-+]?\d+(?:\.\d+)?)\n\s*y:\s*([-+]?\d+(?:\.\d+)?)", text):
                if abs(float(match.group(1))) > 1e-6 or abs(float(match.group(2))) > 1e-6:
                    direct_tf_capture_nonzero = True
                    tf_sources.append(f"{path.name}:nonzero_translation")
                    break
    route_pose_nonzero = bool(route_info.get("nonzero_displacement_observed"))
    evidence_sources = []
    if learn_waypoint_nonzero:
        evidence_sources.append("learn_launch.log:nonzero_waypoints")
    evidence_sources.extend(pulse_sources)
    evidence_sources.extend(odom_sources)
    evidence_sources.extend(tf_sources)
    if route_pose_nonzero:
        evidence_sources.append("route.csv:nonzero_displacement")
    blocked_reasons = []
    if not present_files:
        blocked_reasons.append("motion_log_files_missing")
    if not nonzero_cmd_vel_log_present:
        blocked_reasons.append("nonzero_cmd_vel_log_missing")
    if not (learn_waypoint_nonzero or direct_odom_capture_nonzero or direct_tf_capture_nonzero or route_pose_nonzero):
        blocked_reasons.append("nonzero_odom_tf_evidence_missing")
    if not direct_odom_capture_nonzero:
        blocked_reasons.append("direct_odom_capture_zero_or_missing")
    if not direct_tf_capture_nonzero:
        blocked_reasons.append("direct_tf_capture_zero_or_missing")
    return {
        "present": True,
        "path": str(root),
        "file_count": len(present_files),
        "sample_files": present_files[:8],
        "motion_log_present": bool(present_files),
        "live_motion_evidence_present": bool(nonzero_cmd_vel_log_present or learn_waypoint_nonzero or route_pose_nonzero),
        "live_nav2_log_present": live_nav2_log_present,
        "nonzero_cmd_vel_log_present": nonzero_cmd_vel_log_present,
        "nonzero_odom_evidence_present": bool(learn_waypoint_nonzero or direct_odom_capture_nonzero or route_pose_nonzero),
        "nonzero_tf_evidence_present": bool(direct_tf_capture_nonzero or route_pose_nonzero),
        "direct_odom_capture_nonzero": direct_odom_capture_nonzero,
        "direct_tf_capture_nonzero": direct_tf_capture_nonzero,
        "route_pose_nonzero": route_pose_nonzero,
        "evidence_sources": evidence_sources,
        "blocked_reasons": blocked_reasons,
    }


def field_motion_packet_status(route_info: dict[str, Any], motion_logs: dict[str, Any], route_bag_live: dict[str, Any]) -> tuple[str, list[str], list[str]]:
    # packet 状态强调“可消费的现场运动证据”，但仍然严格保持 not-delivery proof。
    blocked_reasons = []
    if not route_info.get("present"):
        blocked_reasons.append("route_csv_missing")
    if not route_info.get("nonzero_displacement_observed"):
        blocked_reasons.append("route_nonzero_displacement_missing")
    if not motion_logs.get("motion_log_present"):
        blocked_reasons.append("motion_log_missing")
    if not motion_logs.get("live_motion_evidence_present"):
        blocked_reasons.append("live_motion_evidence_missing")
    if not route_bag_live.get("present"):
        blocked_reasons.append("route_bag_or_live_nav2_log_missing")
    next_required_evidence = []
    if not motion_logs.get("direct_odom_capture_nonzero"):
        next_required_evidence.append("nonzero_odom_capture_or_bag_replay")
    if not motion_logs.get("direct_tf_capture_nonzero"):
        next_required_evidence.append("nonzero_tf_capture_or_bag_replay")
    if route_bag_live.get("source") != "route_bag":
        next_required_evidence.append("route_bag_or_live_nav2_log_with_pose_progress")
    next_required_evidence.append("nav2_goal_result_or_delivery_record")
    status = "field_motion_evidence_packet_ready_not_delivery_proof" if not blocked_reasons else "field_motion_evidence_packet_blocked_not_proven"
    return status, sorted(set(blocked_reasons)), next_required_evidence


def build_field_motion_evidence_packet(
    args: argparse.Namespace,
    artifacts: dict[str, Any],
    source_manifest: dict[str, Any],
    derived_replay: dict[str, Any] | None,
) -> dict[str, Any]:
    # 这份 packet 专门给 O6/O7 消费现场运动材料摘要，不回写控制能力，也不宣称 Nav2 或 delivery 成功。
    route_info = route_summary(artifacts.get("route_csv", {}))
    keyframes = keyframe_summary(artifacts.get("keyframes", {}))
    lineage = extract_packet_lineage(source_manifest, args.run_id)
    motion_logs = parse_motion_log_summary(
        Path(args.motion_log_root).expanduser() if getattr(args, "motion_log_root", None) else None,
        route_info,
    )
    rosbag_artifact = artifacts.get("rosbag", {})
    rosbag_present = artifact_present(rosbag_artifact)
    live_log_present = bool(motion_logs.get("live_motion_evidence_present") or motion_logs.get("live_nav2_log_present"))
    route_bag_or_live_nav2_log = {
        "present": bool(rosbag_present or live_log_present),
        "source": "route_bag" if rosbag_present else ("live_motion_log" if live_log_present else "missing"),
        "route_bag_present": rosbag_present,
        "live_motion_log_present": live_log_present,
        "status": (
            "route_bag_present_not_delivery_proof"
            if rosbag_present
            else "live_motion_log_present_not_delivery_proof"
            if live_log_present
            else "missing_not_proven"
        ),
        "blocked_reasons": [] if (rosbag_present or live_log_present) else ["route_bag_and_live_motion_log_missing"],
    }
    status, blocked_reasons, next_required_evidence = field_motion_packet_status(route_info, motion_logs, route_bag_or_live_nav2_log)
    if lineage.get("lineage_blocked_reason"):
        blocked_reasons.append(str(lineage["lineage_blocked_reason"]))
    return {
        "schema": FIELD_MOTION_PACKET_SCHEMA,
        "proof_scope": FIELD_MOTION_PACKET_PROOF_SCOPE,
        "status": status,
        "task_id": lineage["task_id"],
        "task_id_source": lineage["task_id_source"],
        "route_id": lineage["route_id"],
        "map_summary": map_summary(artifacts),
        "route_summary": route_info,
        "keyframe_summary": keyframes,
        "motion_log_summary": motion_logs,
        "derived_replay_summary": {
            "generated": bool((derived_replay or {}).get("generated")),
            "frame_count": int((derived_replay or {}).get("frame_count") or 0),
            "output_ref": safe_basename((derived_replay or {}).get("output")),
            "blocked_reason": (derived_replay or {}).get("blocked_reason"),
        },
        "route_bag_or_live_nav2_log": route_bag_or_live_nav2_log,
        "blocked_reasons": sorted(set(blocked_reasons + route_bag_or_live_nav2_log["blocked_reasons"])),
        "next_required_evidence": next_required_evidence,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
    }


def read_preflight(path: Path | None) -> dict[str, Any]:
    # preflight 缺失也必须 fail closed；不能因为 artifact 完整就跳过现场 ready 条件。
    if path is None:
        return {"status": "missing_preflight_json", "dry_run": None, "blocked_reason": "missing_preflight_json", "read_ok": False}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "invalid_preflight_json", "dry_run": None, "blocked_reason": str(exc), "read_ok": False}
    if not isinstance(loaded, dict):
        return {"status": "invalid_preflight_json", "dry_run": None, "blocked_reason": "root_not_object", "read_ok": False}
    return {
        "schema": loaded.get("schema"),
        "status": str(loaded.get("status") or "missing_status"),
        "dry_run": bool(loaded.get("dry_run", False)),
        "blocked_reason": loaded.get("blocked_reason"),
        "mode": loaded.get("mode"),
        "read_ok": True,
    }


def artifacts_pass(artifacts: dict[str, Any]) -> bool:
    # gate_pass 只表示必需材料完整，delivery_success 仍由真实任务验收单独证明。
    return all(
        item.get("present") and not item.get("reason")
        for item in artifacts.values()
        if item.get("required", True)
    )


def artifact_blocked_reason(artifacts: dict[str, Any]) -> str | None:
    # 缺失优先于空文件上报，方便现场先补目录/文件，再处理内容质量。
    reasons = [
        str(item.get("reason"))
        for item in artifacts.values()
        if item.get("required", True) and item.get("reason")
    ]
    if not reasons:
        return None
    if "missing" in reasons:
        return "missing_required_artifact"
    if "empty" in reasons or "no_keyframe_file" in reasons:
        return "empty_required_artifact"
    return reasons[0]


def artifact_status(artifacts: dict[str, Any], ssh_status: str | None) -> str:
    # artifact_status 只描述材料健康，不把 preflight 是否 ready 混进 gate 语义。
    if ssh_status:
        return "blocked"
    if artifacts_pass(artifacts):
        return "gated"
    if artifact_blocked_reason(artifacts) in {"missing_required_artifact", "empty_required_artifact"}:
        return "missing"
    return "blocked"


def artifact_health(artifacts: dict[str, Any], ssh_status: str | None) -> dict[str, Any]:
    # artifact_health 保留计数与摘要，便于 consumer detail 直接解释“为什么还不能当成功证据”。
    required_artifacts = {name: item for name, item in artifacts.items() if item.get("required", True)}
    optional_artifacts = {name: item for name, item in artifacts.items() if not item.get("required", True)}
    required_count = len(required_artifacts)
    present_artifacts = [name for name, item in required_artifacts.items() if item.get("present") and not item.get("reason")]
    missing_artifacts = [name for name, item in required_artifacts.items() if not item.get("present")]
    blocked_artifacts = [name for name, item in required_artifacts.items() if item.get("reason") and str(item.get("reason")) not in {"missing", "empty", "no_keyframe_file"}]
    empty_artifacts = [name for name, item in required_artifacts.items() if str(item.get("reason")) in {"empty", "no_keyframe_file"}]
    optional_present_artifacts = [name for name, item in optional_artifacts.items() if item.get("present") and not item.get("reason")]
    optional_missing_artifacts = [name for name, item in optional_artifacts.items() if not item.get("present")]
    status = artifact_status(artifacts, ssh_status)
    if status == "gated":
        summary = "all_required_artifacts_present"
    elif status == "missing":
        summary = "missing_required_artifacts"
    elif ssh_status:
        summary = "blocked_ssh_scan_unavailable"
    elif empty_artifacts:
        summary = "empty_required_artifacts"
    else:
        summary = "blocked_artifact_scan_unavailable"
    return {
        "status": status,
        "required_count": required_count,
        "present_count": len(present_artifacts),
        "missing_count": len(missing_artifacts),
        "blocked_count": len(blocked_artifacts),
        "empty_count": len(empty_artifacts),
        "present_artifacts": present_artifacts,
        "missing_artifacts": missing_artifacts,
        "blocked_artifacts": blocked_artifacts,
        "optional_present_artifacts": optional_present_artifacts,
        "optional_missing_artifacts": optional_missing_artifacts,
        "summary": summary,
    }


def preflight_ready(preflight: dict[str, Any]) -> bool:
    # 只有非 dry-run 且 ready 的 preflight 才能解除 manifest 的 not_proven 标记。
    return (
        preflight.get("read_ok") is True
        and preflight.get("status") == READY_PREFLIGHT_STATUS
        and preflight.get("dry_run") is False
        and not preflight.get("blocked_reason")
    )


def build_status(
    artifact_gate_pass: bool,
    artifacts: dict[str, Any],
    preflight: dict[str, Any],
    ssh_status: str | None,
    input_manifest: dict[str, Any],
) -> tuple[str, str | None]:
    # SSH 不可达先报网络入口；本地模式再表达 artifact gate 和 preflight 边界。
    if ssh_status:
        # SSH 模式连只读扫描都不可用时，根因是远端入口，不再把派生的 artifact 缺失当主因。
        return ssh_status, ssh_status
    if input_manifest.get("blocked_reason"):
        # packet 内已有 manifest 不可信时，不能用同目录其它 artifact 把它“洗白”成通过。
        return "blocked_existing_manifest_reuse", str(input_manifest["blocked_reason"])
    artifact_reason = artifact_blocked_reason(artifacts)
    if not artifact_gate_pass:
        if artifact_reason == "empty_required_artifact":
            return "blocked_artifacts_empty", artifact_reason
        return "blocked_artifacts_missing", artifact_reason
    if preflight_ready(preflight):
        return "field_evidence_manifest_ready_not_delivery_proof", None
    reason = str(preflight.get("blocked_reason") or preflight.get("status") or "blocked_preflight_not_ready")
    return "field_evidence_manifest_ready_not_delivery_proof", reason


def build_manifest(
    args: argparse.Namespace,
    artifacts: dict[str, Any],
    preflight: dict[str, Any],
    ssh_status: str | None = None,
    input_manifest: dict[str, Any] | None = None,
    derived_replay: dict[str, Any] | None = None,
    source_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    input_manifest = input_manifest or {
        "present": False,
        "status": "not_scanned",
        "blocked_reason": None,
        "safe_for_reuse": True,
        "dangerous_true_fields": [],
    }
    source_manifest = source_manifest or source_manifest_summary(artifacts.get("source_manifest", {}))
    artifact_gate_pass = artifacts_pass(artifacts)
    input_manifest_safe = input_manifest.get("safe_for_reuse") is True
    gate_pass = artifact_gate_pass and input_manifest_safe
    status, blocked_reason = build_status(artifact_gate_pass, artifacts, preflight, ssh_status, input_manifest)
    proven_material = gate_pass and preflight_ready(preflight) and ssh_status is None
    source = "ssh_remote" if args.mode == "ssh" else "local_fixture"
    health = artifact_health(artifacts, ssh_status)
    if input_manifest.get("blocked_reason"):
        health = {
            **health,
            "status": "blocked",
            "blocked_artifacts": sorted(set(health["blocked_artifacts"] + ["input_manifest"])),
            "summary": "blocked_existing_manifest_reuse",
        }
    manifest_gate = {
        "schema": SCHEMA,
        "status": "gated" if gate_pass else "blocked_not_proven",
        "gate_pass": gate_pass,
        "blocked_reason": blocked_reason,
        "source": source,
    }
    packet = build_field_motion_evidence_packet(args, artifacts, source_manifest, derived_replay)
    nav2_goal_execution_evidence = build_nav2_goal_execution_evidence(args, packet)
    packet["nav2_goal_execution_evidence"] = nav2_goal_execution_evidence
    delivery_result_evidence = build_delivery_result_evidence(args, packet)
    packet["delivery_result_evidence"] = delivery_result_evidence
    route_bag_evidence = build_route_bag_evidence(args, packet)
    packet["route_bag_evidence"] = route_bag_evidence
    route_bag_pose_progress_replay = build_route_bag_pose_progress_replay(args, packet)
    packet["route_bag_pose_progress_replay"] = route_bag_pose_progress_replay
    route_bag_semantic_replay = build_route_bag_semantic_replay(args, packet)
    packet["route_bag_semantic_replay"] = route_bag_semantic_replay
    route_bag_full_semantic_decode_matrix = build_route_bag_full_semantic_decode_matrix(args, packet)
    packet["route_bag_full_semantic_decode_matrix"] = route_bag_full_semantic_decode_matrix
    route_bag_payload_replay = build_route_bag_payload_replay(args, packet)
    packet["route_bag_payload_replay"] = route_bag_payload_replay
    route_execution_result_delivery_readiness = build_route_execution_result_delivery_readiness(packet)
    packet["route_execution_result_delivery_readiness"] = route_execution_result_delivery_readiness
    route_delivery_closure_packet = build_route_delivery_closure_packet(packet)
    packet["route_delivery_closure_packet"] = route_delivery_closure_packet
    same_task_field_material_packet = build_same_task_field_material_packet(packet, artifacts, source_manifest)
    packet["same_task_field_material_packet"] = same_task_field_material_packet
    same_task_mission_evidence_gate = build_same_task_mission_evidence_gate(packet)
    packet["same_task_mission_evidence_gate"] = same_task_mission_evidence_gate
    return {
        "schema": SCHEMA,
        "run_id": args.run_id,
        "generated_at": utc_now(),
        "source": source,
        "mode": args.mode,
        "artifact_root": args.artifact_root,
        "preflight_json": args.preflight_json,
        "preflight_status": preflight.get("status"),
        "preflight": preflight,
        "gate_pass": gate_pass,
        "artifact_status": health["status"],
        "artifact_health": health,
        "input_manifest": input_manifest,
        "source_manifest": source_manifest,
        "route_root_seed_gate": route_root_seed_gate_summary(args, artifacts, derived_replay, source_manifest),
        "field_motion_evidence_packet": packet,
        "nav2_goal_execution_evidence": nav2_goal_execution_evidence,
        "delivery_result_evidence": delivery_result_evidence,
        "route_bag_evidence": route_bag_evidence,
        "route_bag_pose_progress_replay": route_bag_pose_progress_replay,
        "route_bag_semantic_replay": route_bag_semantic_replay,
        "route_bag_full_semantic_decode_matrix": route_bag_full_semantic_decode_matrix,
        "route_bag_payload_replay": route_bag_payload_replay,
        "route_execution_result_delivery_readiness": route_execution_result_delivery_readiness,
        "route_delivery_closure_packet": route_delivery_closure_packet,
        "same_task_field_material_packet": same_task_field_material_packet,
        "same_task_mission_evidence_gate": same_task_mission_evidence_gate,
        "manifest_gate": manifest_gate,
        "status": status,
        "blocked_reason": blocked_reason,
        "not_proven": not proven_material,
        "safe_to_control": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "robot_control_executed": False,
        "derived_replay": derived_replay
        or {
            "generated": False,
            "frame_count": 0,
            "output": None,
            "source_route_csv": None,
            "blocked_reason": "not_requested",
        },
        "artifacts": artifacts,
    }


def remote_scanner_code() -> str:
    # SSH 模式把同一份本地扫描逻辑上传为 python -c，只读远端文件系统，不复制或删除材料。
    script_path = Path(__file__)
    text = script_path.read_text(encoding="utf-8")
    marker = "\nif __name__ == \"__main__\":"
    prefix = text.split(marker, 1)[0]
    return (
        prefix
        + "\nimport json as _json, sys as _sys\n"
        + "_root = Path(_sys.argv[1]).expanduser()\n"
        + "print(_json.dumps(scan_local_artifacts(_root), ensure_ascii=False, sort_keys=True))\n"
    )


def build_ssh_command(target: str, port: int, artifact_root: str, timeout_s: int) -> list[str]:
    # 远端命令使用 python3 -c 和 argv 参数，避免把 artifact_root 作为 shell 片段执行。
    remote = "python3 -c " + shlex.quote(remote_scanner_code()) + " " + shlex.quote(artifact_root)
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
        remote,
    ]


def run_ssh_scan(args: argparse.Namespace) -> tuple[dict[str, Any], str | None, dict[str, Any]]:
    # SSH manifest 只执行远端只读扫描；不可达时仍写 JSON，避免现场证据链断档。
    command = build_ssh_command(args.ssh_target, args.ssh_port, args.artifact_root, args.timeout_s)
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=args.timeout_s + 3)
    except subprocess.TimeoutExpired as exc:
        result = {"command": command, "returncode": None, "stdout": exc.stdout or "", "stderr": exc.stderr or "", "timed_out": True}
        return {}, "blocked_ssh_unreachable", result
    except OSError as exc:
        result = {"command": command, "returncode": None, "stdout": "", "stderr": str(exc), "timed_out": False}
        return {}, "blocked_ssh_unreachable", result
    result = {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout[:1600],
        "stderr": completed.stderr[:1600],
        "timed_out": False,
    }
    if completed.returncode != 0:
        return {}, "blocked_ssh_unreachable", result
    try:
        artifacts = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {}, "blocked_artifact_digest_failed", result
    return artifacts, None, result


def write_manifest(manifest: dict[str, Any], output: Path) -> None:
    # 父目录自动创建，便于 automation 和现场脚本统一写入 /tmp 或 run 目录。
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a trashbot field evidence manifest.")
    parser.add_argument("--mode", choices=["local", "ssh"], required=True)
    parser.add_argument("--artifact-root", dest="artifact_root")
    parser.add_argument("--input", dest="input_dir", help="Alias for --artifact-root when importing a local offline evidence packet.")
    parser.add_argument("--map-yaml", help="Explicit map YAML path when route artifacts and map artifacts are stored in separate directories.")
    parser.add_argument("--map-pgm", help="Explicit map PGM path when route artifacts and map artifacts are stored in separate directories.")
    parser.add_argument("--preflight-json")
    parser.add_argument("--motion-log-root", help="Remote capture directory used to summarize live field motion evidence without claiming delivery success.")
    parser.add_argument("--derive-replay-jsonl", help="Derive a replay JSONL from route.csv without enabling control or delivery claims.")
    parser.add_argument("--nav2-goal-proof-json", help="Optional O11 Nav2 goal execution proof JSON; only safe whitelist fields are summarized.")
    parser.add_argument("--delivery-result-json", help="Optional delivery result JSON; only safe whitelist fields are summarized into additive evidence.")
    parser.add_argument("--cloud-terminal-result-json", help="Optional O5 cloud command terminal result JSON; used as delivery_result_evidence only when --delivery-result-json is absent.")
    parser.add_argument("--route-bag-db3", help="Optional rosbag2 SQLite DB3; only topics/messages metadata is summarized without ROS2 runtime.")
    parser.add_argument("--route-bag-metadata-yaml", help="Optional rosbag2 metadata.yaml; only basename, size, hash prefix and safety status are summarized.")
    parser.add_argument("--route-bag-source-label", help="Safe short source label for route_bag_evidence; paths and credential-like text are rejected.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--ssh-target", default="root@192.168.1.11")
    parser.add_argument("--ssh-port", type=int, default=37878)
    parser.add_argument("--timeout-s", type=int, default=8)
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args(argv)
    if args.timeout_s < 1:
        parser.error("--timeout-s must be >= 1")
    if args.artifact_root and args.input_dir and Path(args.artifact_root).expanduser() != Path(args.input_dir).expanduser():
        parser.error("--artifact-root and --input must point to the same directory when both are provided")
    args.artifact_root = args.artifact_root or args.input_dir
    if not args.artifact_root:
        parser.error("one of --artifact-root or --input is required")
    # run_id 默认来自 UTC 时间，保证每份 manifest 能被后续 archive 稳定索引。
    args.run_id = args.run_id or "field_evidence_" + _dt.datetime.now(tz=_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    preflight = read_preflight(Path(args.preflight_json).expanduser() if args.preflight_json else None)
    ssh_status = None
    ssh_result = None
    derived_replay = None
    if args.mode == "ssh":
        artifacts, ssh_status, ssh_result = run_ssh_scan(args)
        if not artifacts:
            artifacts = {
                name: missing_artifact(
                    Path(args.artifact_root),
                    name,
                    "missing_optional" if name in {"map_pgm", "source_manifest"} else "ssh_scan_unavailable",
                    required=name not in {"map_pgm", "source_manifest"},
                )
                for name in ARTIFACT_CANDIDATES
            }
        input_manifest = existing_manifest_summary(Path(args.artifact_root).expanduser(), Path(args.output).expanduser())
        source_manifest = source_manifest_summary(artifacts.get("source_manifest", {}))
    else:
        artifact_root = Path(args.artifact_root).expanduser()
        map_yaml = Path(args.map_yaml).expanduser() if args.map_yaml else None
        map_pgm = Path(args.map_pgm).expanduser() if args.map_pgm else None
        route_csv_path = artifact_path(artifact_root, "route_csv")
        derived_replay = build_derived_replay_summary(args, route_csv_path)
        artifacts = scan_local_artifacts(artifact_root, map_yaml=map_yaml, map_pgm=map_pgm)
        if derived_replay and derived_replay.get("generated") is True and args.derive_replay_jsonl:
            artifacts["replay_jsonl"] = scan_explicit_file_artifact(Path(args.derive_replay_jsonl).expanduser(), artifact_root, "replay_jsonl")
        input_manifest = existing_manifest_summary(artifact_root, Path(args.output).expanduser())
        source_manifest = source_manifest_summary(artifacts.get("source_manifest", {}))
    apply_route_root_seed_semantics(args, artifacts, derived_replay)
    manifest = build_manifest(args, artifacts, preflight, ssh_status, input_manifest, derived_replay, source_manifest)
    if ssh_result is not None:
        manifest["ssh_scan"] = ssh_result
    write_manifest(manifest, Path(args.output))
    print(json.dumps({"schema": SCHEMA, "status": manifest["status"], "gate_pass": manifest["gate_pass"], "output": args.output}, ensure_ascii=False, sort_keys=True))
    return 0 if manifest["gate_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
