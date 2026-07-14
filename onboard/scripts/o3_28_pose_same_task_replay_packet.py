#!/usr/bin/env python3
"""消费 04:02 fixed-route 材料，生成 O3 same-task no-motion replay packet。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 本脚本只读取本地 artifact，不 import ROS2，也不提供任何会触发运动的参数。
# 05:02 的价值是证明 04:02 summary、route_csv、replay_jsonl 三份材料能被同一任务重新消费。
# packet 生成必须重新读取 CSV 和 JSONL；只复制 summary 会漏掉行级 readback 证据。
# task_id 与 route_intent_id 固定为 04:02 Product accepted identity，防止跨任务材料混入。
# 28 是本轮 accepted material 的合同计数，不是固定路线系统的长期点数上限。
# CSV 和 JSONL 会被逐行对照；任何 pose 坐标、frame、stamp 或 quaternion 漂移都会 fail closed。
# source fingerprint 写入 summary，是为了让后续 Product/O6/O7 复核能确认输入没有被替换。
# 输出 JSONL 仍然是一行一个 pose，便于 shell、consumer 和人工 review 做顺序读回。
# 所有 safety 字段在 summary 和 packet event 中都显式为 false，避免被误当成执行证据。
# 如果未来需要 archive/readback 或真实 route execution，应另开 sprint，不复用这个 offline 入口。
SOURCE_SUMMARY_SCHEMA = "trashbot.fixed_route_28_pose_consumer.v1"
SOURCE_REPLAY_SCHEMA = "trashbot.fixed_route_28_pose_replay.v1"
SOURCE_ROUTE_CSV_SCHEMA = "trashbot.fixed_route_28_pose_route_csv.v1"
SUMMARY_SCHEMA = "trashbot.o3.same_task_route_replay_packet.v1"
PACKET_EVENT_SCHEMA = "trashbot.o3.same_task_route_replay_packet_event.v1"
EXPECTED_POSE_COUNT = 28
EXPECTED_TASK_ID = "task_o3_28_pose_fixed_route_consumer_20260713_0402"
EXPECTED_ROUTE_INTENT_ID = "route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path"
SUMMARY_NAME = "same_task_replay_packet_summary.json"
PACKET_JSONL_NAME = "same_task_route_replay_packet.jsonl"
ARTIFACT_BOUNDARY = "software_proof_o3_o1_strict_no_motion_same_task_route_replay_packet_only"

SAFETY_FALSE_FIELDS = (
    "route_execution_success",
    "delivery_success",
    "hil_pass",
    "safe_to_control",
    "robot_control_executed",
    "publishes_cmd_vel",
    "calls_base_manual",
    "uses_base_uart",
)
CSV_REQUIRED_FIELDS = (
    "schema",
    "route_intent_id",
    "task_id",
    "order",
    "source_index",
    "frame_id",
    "stamp_sec",
    "stamp_nanosec",
    "x",
    "y",
    "z",
    "qx",
    "qy",
    "qz",
    "qw",
    "primary_source_artifact",
    "strict_no_motion",
)


class PacketInputError(ValueError):
    """输入材料不能组成同一 strict no-motion packet 时 fail closed。"""


def utc_now_iso() -> str:
    """统一使用 UTC，避免开发机时区影响 artifact diff 和审计。"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json_object(path: Path) -> dict[str, Any]:
    """summary 必须是 JSON object，避免误把 JSONL 或 stdout tail 当 summary。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PacketInputError(f"summary must be a JSON object: {path}")
    return data


def sha256_file(path: Path) -> str:
    """对 source artifact 做整文件 hash，后续 readback 可复核输入版本。"""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_equal(data: dict[str, Any], key: str, expected: Any, label: str) -> None:
    """集中生成字段漂移错误，让失败定位直接指向 source/CSV/JSONL。"""
    actual = data.get(key)
    if actual != expected:
        raise PacketInputError(f"{label}.{key} expected {expected!r}, got {actual!r}")


def require_true(data: dict[str, Any], key: str, label: str) -> None:
    """关键 accepted 条件必须显式为 true，缺失不能被当成通过。"""
    require_equal(data, key, True, label)


def require_false(data: dict[str, Any], key: str, label: str) -> None:
    """安全字段必须显式为 false，缺失或 None 都不能默认安全。"""
    require_equal(data, key, False, label)


def parse_int(value: Any, label: str) -> int:
    """CSV 中的索引和 timestamp 必须能无损转成整数。"""
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise PacketInputError(f"{label} must be an integer, got {value!r}") from exc


def parse_number(value: Any, label: str) -> float:
    """坐标和四元数必须是数字，不能把空字符串当 0。"""
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise PacketInputError(f"{label} must be numeric, got {value!r}") from exc


def parse_csv_bool(value: Any, label: str) -> bool:
    """CSV bool 只接受明确 true/false 字符串，避免宽松解析掩盖漂移。"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    raise PacketInputError(f"{label} must be true/false, got {value!r}")


def normalize_pose_from_csv(row: dict[str, str], order: int) -> dict[str, Any]:
    """把 route_csv 一行收敛成 packet pose，字段缺失时立即失败。"""
    missing = [field for field in CSV_REQUIRED_FIELDS if field not in row]
    if missing:
        raise PacketInputError(f"route_csv row[{order}] missing fields: {missing}")
    require_equal(row, "schema", SOURCE_ROUTE_CSV_SCHEMA, f"route_csv[{order}]")
    require_equal(row, "route_intent_id", EXPECTED_ROUTE_INTENT_ID, f"route_csv[{order}]")
    require_equal(row, "task_id", EXPECTED_TASK_ID, f"route_csv[{order}]")
    if not parse_csv_bool(row["strict_no_motion"], f"route_csv[{order}].strict_no_motion"):
        raise PacketInputError(f"route_csv[{order}].strict_no_motion must be true")

    # order 和 source_index 双重连续，防止排序漂移或补造点混入。
    row_order = parse_int(row["order"], f"route_csv[{order}].order")
    source_index = parse_int(row["source_index"], f"route_csv[{order}].source_index")
    if row_order != order or source_index != order:
        raise PacketInputError(
            f"route_csv[{order}] order/source_index expected {order}, got {row_order}/{source_index}"
        )
    frame_id = row["frame_id"]
    if not frame_id:
        raise PacketInputError(f"route_csv[{order}].frame_id must be non-empty")

    return {
        "order": order,
        "source_index": source_index,
        "frame_id": frame_id,
        "stamp": {
            "sec": parse_int(row["stamp_sec"], f"route_csv[{order}].stamp_sec"),
            "nanosec": parse_int(row["stamp_nanosec"], f"route_csv[{order}].stamp_nanosec"),
        },
        "position": {
            "x": parse_number(row["x"], f"route_csv[{order}].x"),
            "y": parse_number(row["y"], f"route_csv[{order}].y"),
            "z": parse_number(row["z"], f"route_csv[{order}].z"),
        },
        "orientation": {
            "qx": parse_number(row["qx"], f"route_csv[{order}].qx"),
            "qy": parse_number(row["qy"], f"route_csv[{order}].qy"),
            "qz": parse_number(row["qz"], f"route_csv[{order}].qz"),
            "qw": parse_number(row["qw"], f"route_csv[{order}].qw"),
        },
        "primary_source_artifact": row["primary_source_artifact"],
    }


def require_number(value: Any, label: str) -> float:
    """JSONL 中的数值要保持 int/float，不允许字符串伪装成坐标。"""
    if not isinstance(value, (int, float)):
        raise PacketInputError(f"{label} must be numeric, got {value!r}")
    return float(value)


def normalize_pose_from_event(event: dict[str, Any], order: int) -> dict[str, Any]:
    """把 replay_jsonl 一行收敛成 packet pose，并校验同一任务身份。"""
    require_equal(event, "schema", SOURCE_REPLAY_SCHEMA, f"replay_jsonl[{order}]")
    require_equal(event, "event", "structured_pose", f"replay_jsonl[{order}]")
    require_equal(event, "route_intent_id", EXPECTED_ROUTE_INTENT_ID, f"replay_jsonl[{order}]")
    require_equal(event, "task_id", EXPECTED_TASK_ID, f"replay_jsonl[{order}]")
    require_equal(event, "strict_no_motion", True, f"replay_jsonl[{order}]")
    require_false(event, "route_execution_success", f"replay_jsonl[{order}]")

    # JSONL 的 order/source_index 也必须连续，确保 packet readback 是 28 个原始事件。
    source_index = event.get("source_index")
    if event.get("order") != order or source_index != order:
        raise PacketInputError(
            f"replay_jsonl[{order}] order/source_index expected {order}, got {event.get('order')!r}/{source_index!r}"
        )
    frame_id = event.get("frame_id")
    if not isinstance(frame_id, str) or not frame_id:
        raise PacketInputError(f"replay_jsonl[{order}].frame_id must be non-empty")
    stamp = event.get("stamp")
    if not isinstance(stamp, dict) or not isinstance(stamp.get("sec"), int) or not isinstance(stamp.get("nanosec"), int):
        raise PacketInputError(f"replay_jsonl[{order}].stamp must contain integer sec/nanosec")
    position = event.get("position")
    orientation = event.get("orientation")
    if not isinstance(position, dict) or not isinstance(orientation, dict):
        raise PacketInputError(f"replay_jsonl[{order}] position/orientation must be objects")

    return {
        "order": order,
        "source_index": source_index,
        "frame_id": frame_id,
        "stamp": {"sec": stamp["sec"], "nanosec": stamp["nanosec"]},
        "position": {
            "x": require_number(position.get("x"), f"replay_jsonl[{order}].position.x"),
            "y": require_number(position.get("y"), f"replay_jsonl[{order}].position.y"),
            "z": require_number(position.get("z"), f"replay_jsonl[{order}].position.z"),
        },
        "orientation": {
            "qx": require_number(orientation.get("qx"), f"replay_jsonl[{order}].orientation.qx"),
            "qy": require_number(orientation.get("qy"), f"replay_jsonl[{order}].orientation.qy"),
            "qz": require_number(orientation.get("qz"), f"replay_jsonl[{order}].orientation.qz"),
            "qw": require_number(orientation.get("qw"), f"replay_jsonl[{order}].orientation.qw"),
        },
        "primary_source_artifact": event.get("primary_source_artifact"),
    }


def load_route_csv(path: Path) -> list[dict[str, Any]]:
    """实际读取 route_csv，并返回 28 行规范化 pose。"""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    if len(rows) != EXPECTED_POSE_COUNT:
        raise PacketInputError(f"route_csv expected {EXPECTED_POSE_COUNT} rows, got {len(rows)}")
    return [normalize_pose_from_csv(row, order) for order, row in enumerate(rows)]


def load_replay_jsonl(path: Path) -> list[dict[str, Any]]:
    """实际读取 replay_jsonl，并返回 28 个规范化 replay events。"""
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            raise PacketInputError(f"replay_jsonl line {line_number} must not be blank")
        event = json.loads(line)
        if not isinstance(event, dict):
            raise PacketInputError(f"replay_jsonl line {line_number} must be a JSON object")
        events.append(event)
    if len(events) != EXPECTED_POSE_COUNT:
        raise PacketInputError(f"replay_jsonl expected {EXPECTED_POSE_COUNT} events, got {len(events)}")
    return [normalize_pose_from_event(event, order) for order, event in enumerate(events)]


def validate_source_summary(summary: dict[str, Any], route_csv: Path, replay_jsonl: Path) -> None:
    """校验 04:02 summary 的 accepted 条件和 source refs。"""
    require_equal(summary, "schema", SOURCE_SUMMARY_SCHEMA, "summary")
    require_equal(summary, "route_intent_id", EXPECTED_ROUTE_INTENT_ID, "summary")
    require_equal(summary, "task_id", EXPECTED_TASK_ID, "summary")
    require_true(summary, "fresh_28_pose_structured_material_consumed", "summary")
    require_false(summary, "historic_21_57_artifact_primary_source", "summary")
    require_equal(summary, "path_structured_pose_count", EXPECTED_POSE_COUNT, "summary")
    require_equal(summary, "validation_status", "pass_fresh_28_pose_structured_material", "summary")
    for key in SAFETY_FALSE_FIELDS:
        require_false(summary, key, "summary")

    refs = summary.get("route_material_refs")
    if not isinstance(refs, dict):
        raise PacketInputError("summary.route_material_refs must be present")
    require_equal(refs, "route_csv_ref", route_csv.as_posix(), "summary.route_material_refs")
    require_equal(refs, "route_replay_jsonl_ref", replay_jsonl.as_posix(), "summary.route_material_refs")

    shape = summary.get("material_shape")
    if not isinstance(shape, dict):
        raise PacketInputError("summary.material_shape must be present")
    require_equal(shape, "csv_material_row_count", EXPECTED_POSE_COUNT, "summary.material_shape")
    require_equal(shape, "replay_event_count", EXPECTED_POSE_COUNT, "summary.material_shape")


def compare_pose_pair(csv_pose: dict[str, Any], event_pose: dict[str, Any], order: int) -> None:
    """CSV 与 JSONL 同一 order 的 pose 必须逐字段一致。"""
    comparable_fields = ("order", "source_index", "frame_id", "stamp", "position", "orientation")
    for field in comparable_fields:
        if csv_pose[field] != event_pose[field]:
            raise PacketInputError(
                f"pose[{order}] mismatch for {field}: csv={csv_pose[field]!r}, jsonl={event_pose[field]!r}"
            )
    if csv_pose["primary_source_artifact"] != event_pose["primary_source_artifact"]:
        raise PacketInputError(
            f"pose[{order}] primary_source_artifact mismatch: "
            f"csv={csv_pose['primary_source_artifact']!r}, jsonl={event_pose['primary_source_artifact']!r}"
        )


def validate_materials(summary: dict[str, Any], route_csv: Path, replay_jsonl: Path) -> list[dict[str, Any]]:
    """三方材料同时通过后，才返回可写入 packet 的 pose 列表。"""
    validate_source_summary(summary, route_csv, replay_jsonl)
    csv_poses = load_route_csv(route_csv)
    event_poses = load_replay_jsonl(replay_jsonl)
    for order, (csv_pose, event_pose) in enumerate(zip(csv_poses, event_poses)):
        compare_pose_pair(csv_pose, event_pose, order)
    return csv_poses


def packet_id_for(fingerprints: dict[str, str]) -> str:
    """packet_id 基于输入 hash 生成，重复运行不会因时间不同而漂移。"""
    basis = "|".join(
        (
            EXPECTED_TASK_ID,
            EXPECTED_ROUTE_INTENT_ID,
            fingerprints["summary_sha256"],
            fingerprints["route_csv_sha256"],
            fingerprints["replay_jsonl_sha256"],
        )
    )
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]
    return f"packet_o3_28_pose_same_task_replay_{digest}"


def packet_event_for_pose(
    pose: dict[str, Any],
    packet_id: str,
    summary_ref: str,
    route_csv_ref: str,
    replay_jsonl_ref: str,
    fingerprints: dict[str, str],
) -> dict[str, Any]:
    """输出 packet JSONL 的单条 pose readback event。"""
    return {
        "schema": PACKET_EVENT_SCHEMA,
        "event": "same_task_structured_pose_readback",
        "packet_id": packet_id,
        "route_intent_id": EXPECTED_ROUTE_INTENT_ID,
        "task_id": EXPECTED_TASK_ID,
        "order": pose["order"],
        "source_index": pose["source_index"],
        "frame_id": pose["frame_id"],
        "stamp": pose["stamp"],
        "position": pose["position"],
        "orientation": pose["orientation"],
        "source_summary_ref": summary_ref,
        "route_csv_ref": route_csv_ref,
        "replay_jsonl_ref": replay_jsonl_ref,
        "source_fingerprints": fingerprints,
        "same_task_identity_verified": True,
        "strict_no_motion": True,
        # 行级 safety false 让 JSONL 脱离 summary 被消费时也不会越界。
        "route_execution_success": False,
        "delivery_success": False,
        "hil_pass": False,
        "safe_to_control": False,
        "robot_control_executed": False,
        "publishes_cmd_vel": False,
        "calls_base_manual": False,
        "uses_base_uart": False,
    }


def build_summary(
    poses: list[dict[str, Any]],
    summary_ref: str,
    route_csv_ref: str,
    replay_jsonl_ref: str,
    output_dir: Path,
    generated_at_utc: str,
    fingerprints: dict[str, str],
) -> dict[str, Any]:
    """生成顶层 summary，把可接受事实和拒绝声明分开写清楚。"""
    packet_id = packet_id_for(fingerprints)
    first_pose = poses[0]
    last_pose = poses[-1]
    output_prefix = output_dir.as_posix()

    return {
        "schema": SUMMARY_SCHEMA,
        "generated_at_utc": generated_at_utc,
        "packet_id": packet_id,
        "task_id": EXPECTED_TASK_ID,
        "route_intent_id": EXPECTED_ROUTE_INTENT_ID,
        "source_summary_ref": summary_ref,
        "route_csv_ref": route_csv_ref,
        "replay_jsonl_ref": replay_jsonl_ref,
        "packet_jsonl_ref": f"{output_prefix}/{PACKET_JSONL_NAME}",
        "source_fingerprints": fingerprints,
        "route_csv_row_count": len(poses),
        "replay_jsonl_event_count": len(poses),
        "path_structured_pose_count": len(poses),
        "same_task_identity_verified": True,
        "same_task_replay_packet_ready": True,
        "consumer_integration_status": "pass_strict_no_motion_same_task_replay_packet",
        "artifact_boundary": ARTIFACT_BOUNDARY,
        "pose_readback": {
            # 首尾 pose 是最小可读摘要，证明不是只复制 summary。
            "first_pose": first_pose,
            "last_pose": last_pose,
            "source_index_min": first_pose["source_index"],
            "source_index_max": last_pose["source_index"],
            "frame_ids": sorted({pose["frame_id"] for pose in poses}),
        },
        "checks": [
            {
                "name": "summary_route_csv_replay_jsonl_consumed",
                "status": "pass",
                "detail": "04:02 summary, route_csv, and replay_jsonl were all read and cross-checked",
            },
            {
                "name": "same_task_identity",
                "status": "pass",
                "detail": "task_id and route_intent_id match across summary, CSV, JSONL, and output packet",
            },
            {
                "name": "twenty_eight_pose_readback",
                "status": "pass",
                "detail": "28 route CSV rows and 28 replay JSONL events matched order/source_index/pose fields",
            },
            {
                "name": "strict_no_motion_safety_fields",
                "status": "pass",
                "detail": "route/control/delivery/HIL/safe-to-control fields remain false",
            },
        ],
        "strict_no_motion": True,
        "strict_no_motion_boundary": (
            "offline same-task replay packet only; no NavigateToPose, controller/BT, /cmd_vel, "
            "/api/base/manual, WAVE ROVER UART, route execution, delivery, HIL, or safe-to-control path was used"
        ),
        "route_execution_success": False,
        "delivery_success": False,
        "hil_pass": False,
        "safe_to_control": False,
        "robot_control_executed": False,
        "publishes_cmd_vel": False,
        "calls_base_manual": False,
        "uses_base_uart": False,
        "rejected_claims": [
            "route_execution_success",
            "fixed_route_movement",
            "NavigateToPose",
            "controller_bt_execution",
            "publishes_cmd_vel",
            "calls_base_manual",
            "uses_base_uart",
            "delivery_success",
            "hil_pass",
            "safe_to_control",
            "production_external_evidence",
        ],
        "next_evidence_required": [
            "controlled route execution record before route_execution_success can change",
            "delivery/operator acceptance evidence before delivery_success can change",
            "current live HIL evidence before hil_pass or safe_to_control can change",
            "O6/O7 archive/readback should be a separate cross-owner sprint if needed",
        ],
        "rg_acceptance_anchors": [
            "same-task",
            "28-pose",
            "route_csv",
            "replay_jsonl",
            "route_execution_success=false",
            "delivery_success=false",
            "hil_pass=false",
            "safe_to_control=false",
            "robot-algorithm-engineer",
        ],
    }


def write_outputs(
    summary_path: Path,
    route_csv: Path,
    replay_jsonl: Path,
    output_dir: Path,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """主写入入口；CLI 和单测共用，避免验证逻辑分叉。"""
    # 先读完并校验所有输入，再创建输出目录，避免失败时留下半成品。
    source_summary = load_json_object(summary_path)
    poses = validate_materials(source_summary, route_csv, replay_jsonl)
    fingerprints = {
        "summary_sha256": sha256_file(summary_path),
        "route_csv_sha256": sha256_file(route_csv),
        "replay_jsonl_sha256": sha256_file(replay_jsonl),
    }
    timestamp = generated_at_utc or utc_now_iso()
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_ref = summary_path.as_posix()
    route_csv_ref = route_csv.as_posix()
    replay_jsonl_ref = replay_jsonl.as_posix()
    packet_summary = build_summary(
        poses,
        summary_ref,
        route_csv_ref,
        replay_jsonl_ref,
        output_dir,
        timestamp,
        fingerprints,
    )

    # JSONL 先写，summary 后写；summary 的 packet_jsonl_ref 因此指向已存在文件。
    packet_jsonl_path = output_dir / PACKET_JSONL_NAME
    with packet_jsonl_path.open("w", encoding="utf-8") as handle:
        for pose in poses:
            handle.write(
                json.dumps(
                    packet_event_for_pose(
                        pose,
                        packet_summary["packet_id"],
                        summary_ref,
                        route_csv_ref,
                        replay_jsonl_ref,
                        fingerprints,
                    ),
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            handle.write("\n")

    summary_output_path = output_dir / SUMMARY_NAME
    summary_output_path.write_text(
        json.dumps(packet_summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return packet_summary


def parse_args() -> argparse.Namespace:
    """CLI 只接受 artifact 输入输出路径，避免误加运动控制参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--route-csv", required=True, type=Path)
    parser.add_argument("--replay-jsonl", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    """命令行入口；异常冒泡为非零退出，代表 packet fail closed。"""
    args = parse_args()
    summary = write_outputs(args.summary, args.route_csv, args.replay_jsonl, args.output_dir)
    print(json.dumps({"status": "ok", "summary": f"{args.output_dir.as_posix()}/{SUMMARY_NAME}"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
