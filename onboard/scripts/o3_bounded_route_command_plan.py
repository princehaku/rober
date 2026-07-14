#!/usr/bin/env python3
"""从 07:07 gate record 生成 O3 bounded route command plan。"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 本脚本只生成未来受控执行前的计划参数，不 import ROS2，也不连接任何控制通道。
# 08:09 的价值是把 07:07 gate 里的“bounded command plan with abort criteria”缺口结构化。
# 即使 28-pose route CSV 完全有效，本 artifact 仍然必须 fail closed 在 live safety gate 之前。
# 这里把速度上限和超时写成 plan caps，是为了让下一轮 live sprint 有可审计输入，而不是发车命令。
# 所有 route execution、delivery、HIL、safe-to-control 和 robot control 字段必须显式 false。
# 脚本只读取本地 JSON/CSV 并写 JSON；no /cmd_vel、no /api/base/manual、no NavigateToPose、no WAVE ROVER UART。
GATE_RECORD_SCHEMA = "trashbot.o3.controlled_route_execution_gate_record.v1"
PLAN_SCHEMA = "trashbot.o3.bounded_route_command_plan.v1"
ARTIFACT_BOUNDARY = "software_proof_o3_o1_no_motion_bounded_route_command_plan_only"
OUTPUT_NAME = "bounded_route_command_plan.json"

EXPECTED_PACKET_ID = "packet_o3_28_pose_same_task_replay_7d57826142b0c79c"
EXPECTED_TASK_ID = "task_o3_28_pose_fixed_route_consumer_20260713_0402"
EXPECTED_ROUTE_INTENT_ID = "route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path"
EXPECTED_POSE_COUNT = 28
EXPECTED_SEGMENT_COUNT = EXPECTED_POSE_COUNT - 1

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

NO_MOTION_GUARDS = (
    "no /cmd_vel",
    "no /api/base/manual",
    "no NavigateToPose",
    "no WAVE ROVER UART",
)

ROUTE_CSV_REQUIRED_FIELDS = (
    "schema",
    "route_intent_id",
    "task_id",
    "order",
    "source_index",
    "frame_id",
    "x",
    "y",
    "z",
    "strict_no_motion",
)

# 这些 caps 只描述未来受控执行时的上限；当前 artifact 不会把它们发布到任何机器人接口。
COMMAND_CAPS = {
    "max_linear_speed_mps": 0.1,
    "max_angular_speed_radps": 0.3,
    "min_segment_timeout_s": 3.0,
    "route_timeout_s": 120.0,
    "route_deviation_abort_threshold_m": 0.15,
    "localization_stale_after_s": 1.0,
    "lidar_stale_after_s": 1.0,
    "tf_stale_after_s": 0.5,
    "controller_feedback_timeout_s": 2.0,
    "operator_stop_deadline_s": 0.2,
}

SEGMENT_ABORT_CHECK_IDS = (
    "operator_stop_requested",
    "control_permission_not_true",
    "localization_stale_or_missing",
    "lidar_stale_or_empty_scan",
    "tf_missing_or_stale",
    "controller_feedback_missing",
    "route_deviation_over_threshold",
    "segment_timeout",
)


class PlanInputError(ValueError):
    """gate record 或 route CSV 漂移时 fail closed，避免生成可误读的执行计划。"""


def utc_now_iso() -> str:
    """统一使用 UTC，让 artifact 在不同开发机上可比较。"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json_object(path: Path) -> dict[str, Any]:
    """gate record 必须是 JSON object，不能把 JSONL 或 stdout 当输入。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PlanInputError(f"gate record must be a JSON object: {path}")
    return data


def require_equal(data: dict[str, Any], key: str, expected: Any, label: str) -> None:
    """集中检查字段，失败信息保留 label，便于 tech-done 复盘定位。"""
    actual = data.get(key)
    if actual != expected:
        raise PlanInputError(f"{label}.{key} expected {expected!r}, got {actual!r}")


def require_false(data: dict[str, Any], key: str, label: str) -> None:
    """安全字段必须显式 false；缺失、None 或字符串 false 都不能通过。"""
    require_equal(data, key, False, label)


def resolve_ref(ref: Any, label: str) -> Path:
    """本轮只消费本地 artifact path，不能从外部或网络补材料。"""
    if not isinstance(ref, str) or not ref:
        raise PlanInputError(f"{label} must be a non-empty path string")
    path = Path(ref)
    if not path.exists() or not path.is_file():
        raise PlanInputError(f"{label} does not exist or is not a file: {ref}")
    return path


def validate_gate_record(gate_record: dict[str, Any]) -> Path:
    """复核 07:07 accepted gate record 的 identity、counts、false fields 和 no-motion guard。"""
    require_equal(gate_record, "schema", GATE_RECORD_SCHEMA, "gate_record")
    require_equal(gate_record, "packet_id", EXPECTED_PACKET_ID, "gate_record")
    require_equal(gate_record, "task_id", EXPECTED_TASK_ID, "gate_record")
    require_equal(gate_record, "route_intent_id", EXPECTED_ROUTE_INTENT_ID, "gate_record")
    require_equal(
        gate_record,
        "controlled_route_execution_gate_status",
        "fail_closed_input_packet_validated",
        "gate_record",
    )
    require_equal(gate_record, "identity_validation_status", "pass_exact_same_task_identity", "gate_record")
    require_equal(gate_record, "count_validation_status", "pass_exact_28_28_28", "gate_record")
    require_equal(gate_record, "source_hash_validation_status", "pass_exact_source_hashes", "gate_record")
    require_equal(gate_record, "route_csv_row_count", EXPECTED_POSE_COUNT, "gate_record")
    require_equal(gate_record, "replay_jsonl_event_count", EXPECTED_POSE_COUNT, "gate_record")
    require_equal(gate_record, "packet_jsonl_event_count", EXPECTED_POSE_COUNT, "gate_record")
    require_equal(gate_record, "path_structured_pose_count", EXPECTED_POSE_COUNT, "gate_record")
    for key in SAFETY_FALSE_FIELDS:
        require_false(gate_record, key, "gate_record")
        fixed_false_fields = gate_record.get("fixed_false_fields")
        if isinstance(fixed_false_fields, dict):
            require_false(fixed_false_fields, key, "gate_record.fixed_false_fields")

    guards = gate_record.get("no_motion_control_guard")
    if not isinstance(guards, list):
        raise PlanInputError("gate_record.no_motion_control_guard must be a list")
    guard_text = " ".join(str(item) for item in guards)
    for guard in NO_MOTION_GUARDS:
        if guard not in guard_text:
            raise PlanInputError(f"gate_record.no_motion_control_guard missing {guard!r}")
    return resolve_ref(gate_record.get("route_csv_ref"), "gate_record.route_csv_ref")


def parse_float(row: dict[str, str], key: str, row_number: int) -> float:
    """坐标必须可转成 float；不能把空字符串或单位文本带入距离计算。"""
    try:
        return float(row[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise PlanInputError(f"route_csv row {row_number} field {key} must be a float") from exc


def parse_int(row: dict[str, str], key: str, row_number: int) -> int:
    """order/source_index 要保持整数，后续 segment 才能被审计到原始 pose。"""
    try:
        return int(row[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise PlanInputError(f"route_csv row {row_number} field {key} must be an int") from exc


def parse_strict_no_motion(value: str, row_number: int) -> bool:
    """route CSV 的 strict_no_motion 必须逐行显式 true，防止混入执行材料。"""
    normalized = value.strip().lower()
    if normalized not in {"true", "1", "yes"}:
        raise PlanInputError(f"route_csv row {row_number} strict_no_motion expected true, got {value!r}")
    return True


def read_route_rows(route_csv_path: Path) -> list[dict[str, Any]]:
    """使用 csv.DictReader 解析 28 行 route pose，避免用字符串切片推断坐标。"""
    with route_csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        missing_fields = [field for field in ROUTE_CSV_REQUIRED_FIELDS if field not in fieldnames]
        if missing_fields:
            raise PlanInputError(f"route_csv missing required fields: {missing_fields}")

        rows: list[dict[str, Any]] = []
        for row_number, row in enumerate(reader, start=1):
            order = parse_int(row, "order", row_number)
            source_index = parse_int(row, "source_index", row_number)
            if order != len(rows):
                raise PlanInputError(f"route_csv row {row_number} order expected {len(rows)}, got {order}")
            if row.get("route_intent_id") != EXPECTED_ROUTE_INTENT_ID:
                raise PlanInputError(f"route_csv row {row_number} route_intent_id drift")
            if row.get("task_id") != EXPECTED_TASK_ID:
                raise PlanInputError(f"route_csv row {row_number} task_id drift")
            if not row.get("frame_id"):
                raise PlanInputError(f"route_csv row {row_number} frame_id must be present")
            parse_strict_no_motion(row["strict_no_motion"], row_number)
            rows.append(
                {
                    "order": order,
                    "source_index": source_index,
                    "frame_id": row["frame_id"],
                    "x": parse_float(row, "x", row_number),
                    "y": parse_float(row, "y", row_number),
                    "z": parse_float(row, "z", row_number),
                }
            )

    if len(rows) != EXPECTED_POSE_COUNT:
        raise PlanInputError(f"route_csv row count expected {EXPECTED_POSE_COUNT}, got {len(rows)}")
    return rows


def segment_timeout_s(distance_m: float) -> float:
    """短段也保留 3 秒下限，避免未来 live 执行因调度抖动被过早 abort。"""
    travel_time = distance_m / COMMAND_CAPS["max_linear_speed_mps"]
    return round(max(COMMAND_CAPS["min_segment_timeout_s"], travel_time * 3.0), 3)


def compute_segments(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按相邻 pose 计算 27 段距离；只做几何摘要，不生成控制命令序列。"""
    segments: list[dict[str, Any]] = []
    for index, (start, end) in enumerate(zip(rows, rows[1:])):
        if start["frame_id"] != end["frame_id"]:
            raise PlanInputError(f"segment {index} frame drift: {start['frame_id']} -> {end['frame_id']}")
        distance_m = math.dist((start["x"], start["y"], start["z"]), (end["x"], end["y"], end["z"]))
        segments.append(
            {
                "segment_index": index,
                "from_order": start["order"],
                "to_order": end["order"],
                "from_source_index": start["source_index"],
                "to_source_index": end["source_index"],
                "frame_id": start["frame_id"],
                "distance_m": round(distance_m, 6),
                "planned_linear_speed_cap_mps": COMMAND_CAPS["max_linear_speed_mps"],
                "segment_timeout_s": segment_timeout_s(distance_m),
                "abort_check_ids": list(SEGMENT_ABORT_CHECK_IDS),
            }
        )
    if len(segments) != EXPECTED_SEGMENT_COUNT:
        raise PlanInputError(f"segment count expected {EXPECTED_SEGMENT_COUNT}, got {len(segments)}")
    return segments


def distance_summary(segments: list[dict[str, Any]]) -> dict[str, Any]:
    """汇总距离用于人工复核路线尺度；本轮不评估可通行性或避障。"""
    distances = [float(segment["distance_m"]) for segment in segments]
    total_distance_m = sum(distances)
    return {
        "segment_count": len(segments),
        "total_distance_m": round(total_distance_m, 6),
        "min_segment_distance_m": round(min(distances), 6),
        "max_segment_distance_m": round(max(distances), 6),
        "average_segment_distance_m": round(total_distance_m / len(distances), 6),
        "nonzero_segment_count": sum(1 for distance in distances if distance > 0.0),
    }


def global_abort_criteria() -> list[dict[str, Any]]:
    """列出下一轮 live execution 必须接入的 abort 条件；当前只记录，不执行。"""
    return [
        {
            "id": "operator_stop_requested",
            "abort_when": "operator stop or equivalent safety supervisor stop is requested",
            "threshold": f"must stop within {COMMAND_CAPS['operator_stop_deadline_s']}s when live control exists",
        },
        {
            "id": "control_permission_not_true",
            "abort_when": "safe_to_control, robot_control_executed guard, or operator approval is missing/false",
            "threshold": "fail before any segment; current artifact keeps safe_to_control=false",
        },
        {
            "id": "localization_stale_or_missing",
            "abort_when": "/amcl_pose or localization freshness is missing or stale",
            "threshold": f">{COMMAND_CAPS['localization_stale_after_s']}s stale",
        },
        {
            "id": "lidar_stale_or_empty_scan",
            "abort_when": "/scan has no sample, stale sample, or LiDAR runtime exception",
            "threshold": f">{COMMAND_CAPS['lidar_stale_after_s']}s stale or empty scan",
        },
        {
            "id": "tf_missing_or_stale",
            "abort_when": "map->odom or odom->base_link TF is missing or stale",
            "threshold": f">{COMMAND_CAPS['tf_stale_after_s']}s stale",
        },
        {
            "id": "controller_feedback_missing",
            "abort_when": "Nav2/controller execution result or progress feedback is missing",
            "threshold": f">{COMMAND_CAPS['controller_feedback_timeout_s']}s without feedback",
        },
        {
            "id": "route_deviation_over_threshold",
            "abort_when": "estimated robot pose deviates from bounded segment corridor",
            "threshold": f">{COMMAND_CAPS['route_deviation_abort_threshold_m']}m lateral error",
        },
        {
            "id": "segment_timeout",
            "abort_when": "segment execution exceeds planned timeout",
            "threshold": "per-segment segment_timeout_s from bounded_segment_plan",
        },
        {
            "id": "route_timeout",
            "abort_when": "whole route exceeds conservative route timeout",
            "threshold": f">{COMMAND_CAPS['route_timeout_s']}s",
        },
        {
            "id": "battery_or_imu_unknown",
            "abort_when": "battery or IMU state is unavailable in the same live window",
            "threshold": "unknown status blocks live execution",
        },
        {
            "id": "control_guard_violation",
            "abort_when": "any plan consumer attempts /cmd_vel, /api/base/manual, NavigateToPose, or WAVE ROVER UART from this artifact",
            "threshold": "forbidden in this no-motion sprint",
        },
    ]


def build_plan(
    gate_record_path: Path,
    gate_record: dict[str, Any],
    route_csv_path: Path,
    rows: list[dict[str, Any]],
    segments: list[dict[str, Any]],
    generated_at_utc: str,
) -> dict[str, Any]:
    """构造可机器验收的 bounded route command plan，并把 no-motion 边界写成顶层字段。"""
    false_fields = {field: False for field in SAFETY_FALSE_FIELDS}
    summary = distance_summary(segments)
    estimated_duration_s = round(summary["total_distance_m"] / COMMAND_CAPS["max_linear_speed_mps"], 3)

    return {
        "schema": PLAN_SCHEMA,
        "generated_at_utc": generated_at_utc,
        "artifact_boundary": ARTIFACT_BOUNDARY,
        "proof_boundary": ARTIFACT_BOUNDARY,
        "owner_role": "robot-algorithm-engineer",
        "gate_record_ref": gate_record_path.as_posix(),
        "source_gate_schema": gate_record["schema"],
        "source_gate_status": gate_record["controlled_route_execution_gate_status"],
        "route_csv_ref": route_csv_path.as_posix(),
        "packet_id": EXPECTED_PACKET_ID,
        "task_id": EXPECTED_TASK_ID,
        "route_intent_id": EXPECTED_ROUTE_INTENT_ID,
        "route_csv_row_count": len(rows),
        "segment_count": len(segments),
        "replay_jsonl_event_count": gate_record["replay_jsonl_event_count"],
        "packet_jsonl_event_count": gate_record["packet_jsonl_event_count"],
        "path_structured_pose_count": gate_record["path_structured_pose_count"],
        "execution_plan_status": "blocked_pending_live_safety_gate",
        "command_cap_boundary": "future_bounded_execution_parameters_only_not_control_commands",
        "bounded_command_caps": dict(COMMAND_CAPS),
        "estimated_duration_s_at_cap": estimated_duration_s,
        "segment_distance_summary": summary,
        "bounded_segment_plan": segments,
        "global_abort_criteria": global_abort_criteria(),
        "missing_live_execution_prerequisites": [
            "explicit safety operator approval or equivalent recorded safety gate",
            "current live HIL / stop path / controlled environment material",
            "LiDAR/localization/TF readiness in the same live window",
            "Nav2/controller execution result, not only planner path or bounded plan proof",
            "delivery/operator acceptance evidence before delivery_success can change",
        ],
        "no_motion_control_guard": list(NO_MOTION_GUARDS),
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
            "robot_control_executed",
            "production_external_evidence",
        ],
        "fixed_false_fields": false_fields,
        "rg_acceptance_anchors": [
            "bounded_route_command_plan",
            EXPECTED_PACKET_ID,
            "blocked_pending_live_safety_gate",
            "route_execution_success=false",
            "safe_to_control=false",
            *NO_MOTION_GUARDS,
        ],
        "checks": [
            {
                "name": "source_gate_identity",
                "status": "pass",
                "detail": "07:07 gate record identity and 28-count fields match accepted same-task packet",
            },
            {
                "name": "route_csv_segments",
                "status": "pass",
                "detail": "28 route rows were parsed into 27 geometric segments without control execution",
            },
            {
                "name": "abort_criteria",
                "status": "pass",
                "detail": "operator stop, localization, LiDAR, TF, controller, deviation and timeout abort criteria are recorded",
            },
            {
                "name": "no_motion_control_guard",
                "status": "pass",
                "detail": "no /cmd_vel, no /api/base/manual, no NavigateToPose, no WAVE ROVER UART",
            },
        ],
        **false_fields,
    }


def write_outputs(
    gate_record_path: Path,
    output_dir: Path,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """CLI 与单测共用入口；所有校验通过后才写出 bounded plan artifact。"""
    gate_record = load_json_object(gate_record_path)
    route_csv_path = validate_gate_record(gate_record)
    rows = read_route_rows(route_csv_path)
    segments = compute_segments(rows)
    plan = build_plan(
        gate_record_path,
        gate_record,
        route_csv_path,
        rows,
        segments,
        generated_at_utc or utc_now_iso(),
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / OUTPUT_NAME
    output_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return plan


def parse_args() -> argparse.Namespace:
    """CLI 只接受 gate record 和输出目录，避免误加任何控制执行参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate-record", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    """命令行入口；输入漂移返回非零并明确保持 safe_to_control=false。"""
    args = parse_args()
    try:
        plan = write_outputs(args.gate_record, args.output_dir)
    except PlanInputError as exc:
        print(
            json.dumps(
                {
                    "status": "blocked_bounded_route_command_plan_input_mismatch",
                    "error": str(exc),
                    "route_execution_success": False,
                    "safe_to_control": False,
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    print(
        json.dumps(
            {
                "status": "ok",
                "artifact": (args.output_dir / OUTPUT_NAME).as_posix(),
                "execution_plan_status": plan["execution_plan_status"],
                "segment_count": plan["segment_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
