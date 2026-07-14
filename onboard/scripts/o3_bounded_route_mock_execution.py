#!/usr/bin/env python3
"""消费 bounded route command plan，生成严格 no-motion 的 mock route execution 进度材料。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 本脚本只做本地软件仿真，不 import ROS2，也不调用任何机器人控制接口。
# 输入必须是 08:09 已接受的 bounded route command plan，避免把旧材料误接成新执行证据。
# 输出的 progress JSONL 是“每段 mock completed”的可审计日志，不代表底盘移动。
# 所有 route execution、delivery、HIL、safe-to-control 和 robot control 字段必须保持 false。
# 这里保留 /cmd_vel、/api/base/manual、NavigateToPose、WAVE ROVER UART 的 literal guard，
# 是为了让后续消费者可以用简单 rg/JSON 断言确认本 artifact 仍是 no-motion 材料。
SOURCE_PLAN_SCHEMA = "trashbot.o3.bounded_route_command_plan.v1"
SUMMARY_SCHEMA = "trashbot.o3.bounded_route_mock_execution.v1"
MOCK_EXECUTION_STATUS = "mock_route_execution_completed_not_live_route_execution"
PROOF_BOUNDARY = "software_proof_o3_o1_bounded_route_mock_execution_only"
SOURCE_EXECUTION_PLAN_STATUS = "blocked_pending_live_safety_gate"
SUMMARY_OUTPUT_NAME = "bounded_route_mock_execution_summary.json"
PROGRESS_OUTPUT_NAME = "bounded_route_mock_execution_progress.jsonl"

EXPECTED_PACKET_ID = "packet_o3_28_pose_same_task_replay_7d57826142b0c79c"
EXPECTED_TASK_ID = "task_o3_28_pose_fixed_route_consumer_20260713_0402"
EXPECTED_ROUTE_INTENT_ID = "route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path"
EXPECTED_ROUTE_ROW_COUNT = 28
EXPECTED_SEGMENT_COUNT = EXPECTED_ROUTE_ROW_COUNT - 1

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

REJECTED_CLAIMS = (
    "live route execution",
    "fixed-route movement",
    "controller/BT execution",
    "/cmd_vel publish",
    "/api/base/manual call",
    "NavigateToPose goal",
    "WAVE ROVER UART command",
    "HIL pass",
    "delivery success",
    "safe-to-control",
    "O5 production external evidence",
)


class MockExecutionInputError(ValueError):
    """输入计划漂移时 fail closed，避免生成会被误读的执行完成材料。"""


def utc_now_iso() -> str:
    """统一使用 UTC 秒级时间，便于不同主机生成的 artifact 对照。"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json_object(path: Path) -> dict[str, Any]:
    """bounded plan 必须是 JSON object，不能把 JSONL 或命令 stdout 当输入。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise MockExecutionInputError(f"bounded plan must be a JSON object: {path}")
    return data


def require_equal(data: dict[str, Any], key: str, expected: Any, label: str) -> None:
    """集中校验关键字段；错误消息携带 label，方便 sprint 复盘定位。"""
    actual = data.get(key)
    if actual != expected:
        raise MockExecutionInputError(f"{label}.{key} expected {expected!r}, got {actual!r}")


def require_false(data: dict[str, Any], key: str, label: str) -> None:
    """安全字段必须是布尔 false；缺失、None 或字符串 false 都不能通过。"""
    require_equal(data, key, False, label)


def require_int(data: dict[str, Any], key: str, expected: int, label: str) -> None:
    """count 字段必须精确匹配，不能接受字符串或浮点伪装的数字。"""
    actual = data.get(key)
    if type(actual) is not int or actual != expected:
        raise MockExecutionInputError(f"{label}.{key} expected int {expected!r}, got {actual!r}")


def validate_no_motion_guards(plan: dict[str, Any]) -> list[str]:
    """要求 plan 顶层 guard 覆盖四类禁止控制入口，保持 proof boundary 可机读。"""
    guards = plan.get("no_motion_control_guard")
    if not isinstance(guards, list):
        raise MockExecutionInputError("bounded_plan.no_motion_control_guard must be a list")
    guard_text = " ".join(str(item) for item in guards)
    for guard in NO_MOTION_GUARDS:
        if guard not in guard_text:
            raise MockExecutionInputError(f"bounded_plan.no_motion_control_guard missing {guard!r}")
    return [str(item) for item in guards]


def validate_false_fields(plan: dict[str, Any]) -> dict[str, bool]:
    """同时校验顶层和 fixed_false_fields，防止消费者只读其中一个字段时误判。"""
    fixed_false_fields = plan.get("fixed_false_fields")
    if not isinstance(fixed_false_fields, dict):
        raise MockExecutionInputError("bounded_plan.fixed_false_fields must be an object")
    for key in SAFETY_FALSE_FIELDS:
        require_false(plan, key, "bounded_plan")
        require_false(fixed_false_fields, key, "bounded_plan.fixed_false_fields")
    return {key: False for key in SAFETY_FALSE_FIELDS}


def parse_non_negative_float(value: Any, label: str) -> float:
    """segment distance/timeout 来自上游 plan，这里只允许非负数进入 mock 计算。"""
    if isinstance(value, bool):
        raise MockExecutionInputError(f"{label} must be a non-negative number, got {value!r}")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise MockExecutionInputError(f"{label} must be a non-negative number, got {value!r}") from exc
    if number < 0:
        raise MockExecutionInputError(f"{label} must be non-negative, got {value!r}")
    return number


def parse_order(value: Any, label: str) -> int:
    """order/index 必须是真整数，mock progress 才能追溯到原始 28 pose。"""
    if type(value) is not int:
        raise MockExecutionInputError(f"{label} must be an int, got {value!r}")
    return value


def validate_segment(segment: Any, expected_index: int) -> dict[str, Any]:
    """逐段校验 bounded_segment_plan，避免只信 segment_count 顶层字段。"""
    if not isinstance(segment, dict):
        raise MockExecutionInputError(f"bounded_segment_plan[{expected_index}] must be an object")

    segment_index = parse_order(segment.get("segment_index"), f"bounded_segment_plan[{expected_index}].segment_index")
    if segment_index != expected_index:
        raise MockExecutionInputError(
            f"bounded_segment_plan[{expected_index}].segment_index expected {expected_index}, got {segment_index}"
        )

    from_order = parse_order(segment.get("from_order"), f"bounded_segment_plan[{expected_index}].from_order")
    to_order = parse_order(segment.get("to_order"), f"bounded_segment_plan[{expected_index}].to_order")
    if from_order != expected_index or to_order != expected_index + 1:
        raise MockExecutionInputError(
            f"bounded_segment_plan[{expected_index}] expected orders {expected_index}->{expected_index + 1}, "
            f"got {from_order}->{to_order}"
        )

    # frame_id 不参与控制，只用于人工核对这些 progress event 仍来自同一个 map frame。
    frame_id = segment.get("frame_id")
    if not isinstance(frame_id, str) or not frame_id:
        raise MockExecutionInputError(f"bounded_segment_plan[{expected_index}].frame_id must be present")

    return {
        "segment_index": segment_index,
        "from_order": from_order,
        "to_order": to_order,
        "from_source_index": segment.get("from_source_index"),
        "to_source_index": segment.get("to_source_index"),
        "frame_id": frame_id,
        "distance_m": round(parse_non_negative_float(segment.get("distance_m"), f"segment {expected_index}.distance_m"), 6),
        "planned_linear_speed_cap_mps": parse_non_negative_float(
            segment.get("planned_linear_speed_cap_mps", 0.0),
            f"segment {expected_index}.planned_linear_speed_cap_mps",
        ),
        "segment_timeout_s": round(
            parse_non_negative_float(segment.get("segment_timeout_s", 0.0), f"segment {expected_index}.segment_timeout_s"),
            3,
        ),
    }


def validate_segments(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """顶层 segment_count 和实际 27 段列表必须同时成立，才允许写 mock progress。"""
    require_int(plan, "segment_count", EXPECTED_SEGMENT_COUNT, "bounded_plan")
    segments = plan.get("bounded_segment_plan")
    if not isinstance(segments, list):
        raise MockExecutionInputError("bounded_plan.bounded_segment_plan must be a list")
    if len(segments) != EXPECTED_SEGMENT_COUNT:
        raise MockExecutionInputError(
            f"bounded_plan.bounded_segment_plan expected {EXPECTED_SEGMENT_COUNT} segments, got {len(segments)}"
        )
    return [validate_segment(segment, index) for index, segment in enumerate(segments)]


def validate_source_plan(plan: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], dict[str, bool]]:
    """校验 08:09 bounded plan 的身份、计数、状态和 no-motion 安全边界。"""
    require_equal(plan, "schema", SOURCE_PLAN_SCHEMA, "bounded_plan")
    require_equal(plan, "execution_plan_status", SOURCE_EXECUTION_PLAN_STATUS, "bounded_plan")
    require_equal(plan, "packet_id", EXPECTED_PACKET_ID, "bounded_plan")
    require_equal(plan, "task_id", EXPECTED_TASK_ID, "bounded_plan")
    require_equal(plan, "route_intent_id", EXPECTED_ROUTE_INTENT_ID, "bounded_plan")
    require_int(plan, "route_csv_row_count", EXPECTED_ROUTE_ROW_COUNT, "bounded_plan")
    require_int(plan, "replay_jsonl_event_count", EXPECTED_ROUTE_ROW_COUNT, "bounded_plan")
    require_int(plan, "packet_jsonl_event_count", EXPECTED_ROUTE_ROW_COUNT, "bounded_plan")
    require_int(plan, "path_structured_pose_count", EXPECTED_ROUTE_ROW_COUNT, "bounded_plan")
    guards = validate_no_motion_guards(plan)
    false_fields = validate_false_fields(plan)
    segments = validate_segments(plan)
    return segments, guards, false_fields


def mock_elapsed_s(segment: dict[str, Any]) -> float:
    """elapsed_s 是 deterministic mock 值，不是墙钟、不来自控制器 feedback。"""
    speed_cap = segment["planned_linear_speed_cap_mps"]
    if speed_cap <= 0:
        return 0.0
    return round(segment["distance_m"] / speed_cap, 3)


def build_progress_events(
    plan: dict[str, Any],
    segments: list[dict[str, Any]],
    false_fields: dict[str, bool],
) -> list[dict[str, Any]]:
    """把 27 个几何 segment 转成 27 条 mock completion event，严格不携带控制成功语义。"""
    events: list[dict[str, Any]] = []
    cumulative_distance_m = 0.0
    cumulative_elapsed_s = 0.0

    for segment in segments:
        elapsed_s = mock_elapsed_s(segment)
        cumulative_distance_m += segment["distance_m"]
        cumulative_elapsed_s += elapsed_s
        event = {
            "schema": "trashbot.o3.bounded_route_mock_execution.progress.v1",
            "event_type": "mock_segment_completed_not_live_control",
            "proof_boundary": PROOF_BOUNDARY,
            "source_schema": plan["schema"],
            "source_execution_plan_status": plan["execution_plan_status"],
            "packet_id": plan["packet_id"],
            "task_id": plan["task_id"],
            "route_intent_id": plan["route_intent_id"],
            "segment_index": segment["segment_index"],
            "from_order": segment["from_order"],
            "to_order": segment["to_order"],
            "from_source_index": segment["from_source_index"],
            "to_source_index": segment["to_source_index"],
            "frame_id": segment["frame_id"],
            "distance_m": segment["distance_m"],
            "elapsed_s": elapsed_s,
            "cumulative_distance_m": round(cumulative_distance_m, 6),
            "cumulative_elapsed_s": round(cumulative_elapsed_s, 3),
            "mock_progress_status": "segment_completed_in_software_only_not_robot_motion",
            "elapsed_source": "distance_over_plan_speed_cap_not_wall_clock_control",
            **false_fields,
        }
        events.append(event)

    return events


def build_summary(
    bounded_plan_path: Path,
    plan: dict[str, Any],
    segments: list[dict[str, Any]],
    guards: list[str],
    false_fields: dict[str, bool],
    events: list[dict[str, Any]],
    generated_at_utc: str,
) -> dict[str, Any]:
    """构造 summary；顶层重复写入身份、计数和 false fields，方便下游最小读取。"""
    total_distance_m = round(sum(float(event["distance_m"]) for event in events), 6)
    total_elapsed_s = round(sum(float(event["elapsed_s"]) for event in events), 3)
    return {
        "schema": SUMMARY_SCHEMA,
        "generated_at_utc": generated_at_utc,
        "mock_execution_status": MOCK_EXECUTION_STATUS,
        "proof_boundary": PROOF_BOUNDARY,
        "owner_role": "robot-algorithm-engineer",
        "bounded_plan_ref": bounded_plan_path.as_posix(),
        "progress_jsonl_ref": PROGRESS_OUTPUT_NAME,
        "source_schema": plan["schema"],
        "source_execution_plan_status": plan["execution_plan_status"],
        "source_proof_boundary": plan.get("proof_boundary"),
        "packet_id": plan["packet_id"],
        "task_id": plan["task_id"],
        "route_intent_id": plan["route_intent_id"],
        "route_csv_row_count": plan["route_csv_row_count"],
        "segment_count": plan["segment_count"],
        "replay_jsonl_event_count": plan["replay_jsonl_event_count"],
        "packet_jsonl_event_count": plan["packet_jsonl_event_count"],
        "path_structured_pose_count": plan["path_structured_pose_count"],
        "source_identity_verified": True,
        "source_counts_verified": True,
        "source_no_motion_guard_verified": True,
        "source_fixed_false_fields_verified": True,
        "mock_execution_completed": True,
        "mock_segment_progress_count": len(segments),
        "progress_jsonl_event_count": len(events),
        "mock_total_distance_m": total_distance_m,
        "mock_total_elapsed_s": total_elapsed_s,
        "mock_elapsed_source": "deterministic_distance_over_plan_speed_cap_not_wall_clock_control",
        "no_motion_control_guard": guards,
        "rejected_claims": list(REJECTED_CLAIMS),
        "fixed_false_fields": false_fields,
        "checks": [
            {
                "name": "source_plan_identity",
                "status": "pass",
                "detail": "bounded plan schema/status/packet/task/route identity matched accepted 28-pose source",
            },
            {
                "name": "source_counts",
                "status": "pass",
                "detail": "28 route rows and 27 bounded segments were verified before writing progress JSONL",
            },
            {
                "name": "no_motion_guard",
                "status": "pass",
                "detail": "no /cmd_vel, no /api/base/manual, no NavigateToPose, no WAVE ROVER UART",
            },
            {
                "name": "fixed_false_fields",
                "status": "pass",
                "detail": "route_execution_success=false and safe_to_control=false remain fixed with all control fields false",
            },
        ],
        "rg_acceptance_anchors": [
            "bounded_route_mock_execution",
            MOCK_EXECUTION_STATUS,
            PROOF_BOUNDARY,
            "route_execution_success=false",
            "safe_to_control=false",
        ],
        **false_fields,
    }


def write_progress_jsonl(path: Path, events: list[dict[str, Any]]) -> None:
    """JSONL 一行一 event，便于后续 tail/stream 消费，但仍是离线 artifact。"""
    content = "".join(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n" for event in events)
    path.write_text(content, encoding="utf-8")


def write_outputs(
    bounded_plan_path: Path,
    output_dir: Path,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """CLI 与单测共用入口；所有输入校验通过后才写 summary 和 progress JSONL。"""
    plan = load_json_object(bounded_plan_path)
    segments, guards, false_fields = validate_source_plan(plan)
    events = build_progress_events(plan, segments, false_fields)
    summary = build_summary(
        bounded_plan_path,
        plan,
        segments,
        guards,
        false_fields,
        events,
        generated_at_utc or utc_now_iso(),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    progress_path = output_dir / PROGRESS_OUTPUT_NAME
    write_progress_jsonl(progress_path, events)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    """CLI 只接受 bounded plan 和输出目录，避免暴露任何控制执行参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bounded-plan", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    """命令行入口；输入漂移时 fail closed，并在 stderr 保留 false safety 字段。"""
    args = parse_args()
    try:
        summary = write_outputs(args.bounded_plan, args.output_dir)
    except MockExecutionInputError as exc:
        print(
            json.dumps(
                {
                    "status": "blocked_bounded_route_mock_execution_input_mismatch",
                    "error": str(exc),
                    "route_execution_success": False,
                    "delivery_success": False,
                    "hil_pass": False,
                    "safe_to_control": False,
                    "robot_control_executed": False,
                    "publishes_cmd_vel": False,
                    "calls_base_manual": False,
                    "uses_base_uart": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2

    print(
        json.dumps(
            {
                "status": "ok",
                "summary": (args.output_dir / SUMMARY_OUTPUT_NAME).as_posix(),
                "progress": (args.output_dir / PROGRESS_OUTPUT_NAME).as_posix(),
                "mock_execution_status": summary["mock_execution_status"],
                "mock_segment_progress_count": summary["mock_segment_progress_count"],
                "route_execution_success": False,
                "safe_to_control": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
