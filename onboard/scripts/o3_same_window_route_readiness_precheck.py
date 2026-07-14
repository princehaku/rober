#!/usr/bin/env python3
"""汇总 O3/O1 same-window route readiness blocker，生成严格 no-motion precheck artifact。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 本脚本只读取既有 route material 并写出 readiness blocker summary。
# 它不 import ROS2、不创建 action client、不发布 topic，也不调用任何 HTTP 控制接口。
# 13:38 sprint 的目标是把 07:07 gate、08:09 bounded plan、23:23 mock execution 统一成下一轮 live capture 门槛。
# 即使所有输入都匹配，本 artifact 也必须保持 blocked，因为缺的是 same-window live evidence。
# 这里反复校验 false 字段，是为了避免把 mock completed progress 误读成真实 route execution。
# literal guard 必须保留，方便 Product 和后续 owner 用 rg 直接验证 no /cmd_vel、no /api/base/manual、no NavigateToPose、no WAVE ROVER UART。
GATE_RECORD_SCHEMA = "trashbot.o3.controlled_route_execution_gate_record.v1"
BOUNDED_PLAN_SCHEMA = "trashbot.o3.bounded_route_command_plan.v1"
MOCK_SUMMARY_SCHEMA = "trashbot.o3.bounded_route_mock_execution.v1"
PROGRESS_SCHEMA = "trashbot.o3.bounded_route_mock_execution.progress.v1"
SUMMARY_SCHEMA = "trashbot.o3.same_window_route_readiness_precheck.v1"

SOURCE_GATE_STATUS = "fail_closed_input_packet_validated"
SOURCE_PLAN_STATUS = "blocked_pending_live_safety_gate"
SOURCE_MOCK_STATUS = "mock_route_execution_completed_not_live_route_execution"
READINESS_STATUS = "blocked_missing_same_window_live_evidence"
PROOF_BOUNDARY = "software_proof_o3_o1_same_window_route_readiness_precheck_only"
SUMMARY_OUTPUT_NAME = "same_window_route_readiness_precheck_summary.json"

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

MISSING_EVIDENCE = (
    "explicit_operator_approval",
    "current_live_stop_hil",
    "same_window_scan_readiness",
    "same_window_amcl_pose_readiness",
    "same_window_map_to_odom_tf_readiness",
    "nav2_controller_result",
    "delivery_or_operator_acceptance",
)

REJECTED_CLAIMS = (
    "live route execution",
    "fixed-route movement",
    "Nav2 controller/BT execution",
    "/cmd_vel publish",
    "/api/base/manual call",
    "NavigateToPose goal",
    "WAVE ROVER UART command",
    "current live HIL pass",
    "delivery success",
    "operator delivery acceptance",
    "safe-to-control",
    "O5 production/cloud evidence",
)


class ReadinessPrecheckInputError(ValueError):
    """输入 artifact 漂移时 fail closed，避免写出可误读的 readiness summary。"""


def utc_now_iso() -> str:
    """统一使用 UTC 秒级时间，避免开发机时区影响 artifact 对照。"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    """每个 source summary 都必须是 JSON object，不能把 JSONL 或 stdout 当输入。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ReadinessPrecheckInputError(f"{label} must be a JSON object: {path}")
    return data


def load_jsonl_objects(path: Path, label: str) -> list[dict[str, Any]]:
    """progress JSONL 必须逐行 object；空行会让后续审计无法稳定计数。"""
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            raise ReadinessPrecheckInputError(f"{label} line {line_number} must not be blank")
        event = json.loads(line)
        if not isinstance(event, dict):
            raise ReadinessPrecheckInputError(f"{label} line {line_number} must be a JSON object")
        events.append(event)
    return events


def require_equal(data: dict[str, Any], key: str, expected: Any, label: str) -> None:
    """集中生成字段漂移错误，让 tech-done 能直接记录失败根因。"""
    actual = data.get(key)
    if actual != expected:
        raise ReadinessPrecheckInputError(f"{label}.{key} expected {expected!r}, got {actual!r}")


def require_int(data: dict[str, Any], key: str, expected: int, label: str) -> None:
    """计数字段必须是真 int，不能接受字符串或 bool 伪装的数字。"""
    actual = data.get(key)
    if type(actual) is not int or actual != expected:
        raise ReadinessPrecheckInputError(f"{label}.{key} expected int {expected!r}, got {actual!r}")


def require_false(data: dict[str, Any], key: str, label: str) -> None:
    """安全字段必须显式为布尔 false；缺失、None、字符串 false 都不能通过。"""
    require_equal(data, key, False, label)


def validate_identity_and_counts(data: dict[str, Any], label: str, *, expect_segment_count: bool) -> None:
    """复用 identity/count 校验，确保三个 source 仍指向同一 28-pose route chain。"""
    require_equal(data, "packet_id", EXPECTED_PACKET_ID, label)
    require_equal(data, "task_id", EXPECTED_TASK_ID, label)
    require_equal(data, "route_intent_id", EXPECTED_ROUTE_INTENT_ID, label)
    require_int(data, "route_csv_row_count", EXPECTED_ROUTE_ROW_COUNT, label)
    if "replay_jsonl_event_count" in data:
        require_int(data, "replay_jsonl_event_count", EXPECTED_ROUTE_ROW_COUNT, label)
    if "packet_jsonl_event_count" in data:
        require_int(data, "packet_jsonl_event_count", EXPECTED_ROUTE_ROW_COUNT, label)
    if "path_structured_pose_count" in data:
        require_int(data, "path_structured_pose_count", EXPECTED_ROUTE_ROW_COUNT, label)
    if expect_segment_count:
        require_int(data, "segment_count", EXPECTED_SEGMENT_COUNT, label)


def validate_false_fields(data: dict[str, Any], label: str) -> dict[str, bool]:
    """同时校验顶层与 fixed_false_fields，避免消费者只读其中一处时误判。"""
    fixed_false_fields = data.get("fixed_false_fields")
    if not isinstance(fixed_false_fields, dict):
        raise ReadinessPrecheckInputError(f"{label}.fixed_false_fields must be an object")
    for key in SAFETY_FALSE_FIELDS:
        require_false(data, key, label)
        require_false(fixed_false_fields, key, f"{label}.fixed_false_fields")
    return {key: False for key in SAFETY_FALSE_FIELDS}


def validate_no_motion_guards(data: dict[str, Any], label: str) -> list[str]:
    """四类 forbidden control literal 必须可检索，证明本轮不暴露控制入口。"""
    guards = data.get("no_motion_control_guard")
    if not isinstance(guards, list):
        raise ReadinessPrecheckInputError(f"{label}.no_motion_control_guard must be a list")
    guard_text = " ".join(str(item) for item in guards)
    for guard in NO_MOTION_GUARDS:
        if guard not in guard_text:
            raise ReadinessPrecheckInputError(f"{label}.no_motion_control_guard missing {guard!r}")
    return [str(item) for item in guards]


def validate_gate_record(gate_record: dict[str, Any]) -> dict[str, Any]:
    """校验 07:07 gate 仍是 fail-closed gate record，不是 execution proof。"""
    require_equal(gate_record, "schema", GATE_RECORD_SCHEMA, "gate_record")
    require_equal(gate_record, "controlled_route_execution_gate_status", SOURCE_GATE_STATUS, "gate_record")
    validate_identity_and_counts(gate_record, "gate_record", expect_segment_count=False)
    require_equal(gate_record, "identity_validation_status", "pass_exact_same_task_identity", "gate_record")
    require_equal(gate_record, "count_validation_status", "pass_exact_28_28_28", "gate_record")
    require_equal(gate_record, "source_hash_validation_status", "pass_exact_source_hashes", "gate_record")
    false_fields = validate_false_fields(gate_record, "gate_record")
    guards = validate_no_motion_guards(gate_record, "gate_record")
    return {
        "schema": gate_record["schema"],
        "status": gate_record["controlled_route_execution_gate_status"],
        "proof_boundary": gate_record.get("proof_boundary"),
        "no_motion_control_guard": guards,
        "fixed_false_fields": false_fields,
    }


def validate_bounded_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """校验 08:09 bounded plan 仍 blocked 在 live safety gate 前。"""
    require_equal(plan, "schema", BOUNDED_PLAN_SCHEMA, "bounded_plan")
    require_equal(plan, "execution_plan_status", SOURCE_PLAN_STATUS, "bounded_plan")
    validate_identity_and_counts(plan, "bounded_plan", expect_segment_count=True)
    false_fields = validate_false_fields(plan, "bounded_plan")
    guards = validate_no_motion_guards(plan, "bounded_plan")
    segments = plan.get("bounded_segment_plan")
    if not isinstance(segments, list) or len(segments) != EXPECTED_SEGMENT_COUNT:
        raise ReadinessPrecheckInputError(
            f"bounded_plan.bounded_segment_plan expected {EXPECTED_SEGMENT_COUNT} segments"
        )
    return {
        "schema": plan["schema"],
        "status": plan["execution_plan_status"],
        "proof_boundary": plan.get("proof_boundary"),
        "no_motion_control_guard": guards,
        "fixed_false_fields": false_fields,
    }


def validate_mock_summary(mock_summary: dict[str, Any]) -> dict[str, Any]:
    """校验 23:23 summary 是 mock completion，不是 live route execution。"""
    require_equal(mock_summary, "schema", MOCK_SUMMARY_SCHEMA, "mock_summary")
    require_equal(mock_summary, "mock_execution_status", SOURCE_MOCK_STATUS, "mock_summary")
    validate_identity_and_counts(mock_summary, "mock_summary", expect_segment_count=True)
    require_int(mock_summary, "mock_segment_progress_count", EXPECTED_SEGMENT_COUNT, "mock_summary")
    require_int(mock_summary, "progress_jsonl_event_count", EXPECTED_SEGMENT_COUNT, "mock_summary")
    false_fields = validate_false_fields(mock_summary, "mock_summary")
    guards = validate_no_motion_guards(mock_summary, "mock_summary")
    return {
        "schema": mock_summary["schema"],
        "status": mock_summary["mock_execution_status"],
        "proof_boundary": mock_summary.get("proof_boundary"),
        "no_motion_control_guard": guards,
        "fixed_false_fields": false_fields,
    }


def validate_progress_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    """复核 27 条 mock progress 都是 segment_completed_in_software_only，不含控制成功语义。"""
    if len(events) != EXPECTED_SEGMENT_COUNT:
        raise ReadinessPrecheckInputError(
            f"mock_progress expected {EXPECTED_SEGMENT_COUNT} events, got {len(events)}"
        )
    for expected_index, event in enumerate(events):
        label = f"mock_progress[{expected_index}]"
        require_equal(event, "schema", PROGRESS_SCHEMA, label)
        require_equal(event, "event_type", "mock_segment_completed_not_live_control", label)
        require_equal(event, "proof_boundary", "software_proof_o3_o1_bounded_route_mock_execution_only", label)
        require_equal(event, "packet_id", EXPECTED_PACKET_ID, label)
        require_equal(event, "task_id", EXPECTED_TASK_ID, label)
        require_equal(event, "route_intent_id", EXPECTED_ROUTE_INTENT_ID, label)
        require_int(event, "segment_index", expected_index, label)
        require_int(event, "from_order", expected_index, label)
        require_int(event, "to_order", expected_index + 1, label)
        for key in SAFETY_FALSE_FIELDS:
            require_false(event, key, label)
    return {
        "schema": PROGRESS_SCHEMA,
        "event_type": "mock_segment_completed_not_live_control",
        "event_count": len(events),
        "segment_index_min": 0,
        "segment_index_max": EXPECTED_SEGMENT_COUNT - 1,
    }


def source_artifact_summary(
    gate_path: Path,
    plan_path: Path,
    mock_summary_path: Path,
    progress_path: Path,
    gate_status: dict[str, Any],
    plan_status: dict[str, Any],
    mock_status: dict[str, Any],
    progress_status: dict[str, Any],
) -> list[dict[str, Any]]:
    """保留四个 input artifact 的最小状态，方便下一轮追溯 source chain。"""
    return [
        {
            "name": "controlled_route_execution_gate_record",
            "ref": gate_path.as_posix(),
            "schema": gate_status["schema"],
            "status": gate_status["status"],
            "proof_boundary": gate_status["proof_boundary"],
        },
        {
            "name": "bounded_route_command_plan",
            "ref": plan_path.as_posix(),
            "schema": plan_status["schema"],
            "status": plan_status["status"],
            "proof_boundary": plan_status["proof_boundary"],
        },
        {
            "name": "bounded_route_mock_execution_summary",
            "ref": mock_summary_path.as_posix(),
            "schema": mock_status["schema"],
            "status": mock_status["status"],
            "proof_boundary": mock_status["proof_boundary"],
        },
        {
            "name": "bounded_route_mock_execution_progress",
            "ref": progress_path.as_posix(),
            "schema": progress_status["schema"],
            "status": progress_status["event_type"],
            "event_count": progress_status["event_count"],
        },
    ]


def build_summary(
    gate_record_path: Path,
    bounded_plan_path: Path,
    mock_summary_path: Path,
    progress_path: Path,
    gate_record: dict[str, Any],
    bounded_plan: dict[str, Any],
    mock_summary: dict[str, Any],
    gate_status: dict[str, Any],
    plan_status: dict[str, Any],
    mock_status: dict[str, Any],
    progress_status: dict[str, Any],
    generated_at_utc: str,
) -> dict[str, Any]:
    """构造 precheck summary；顶层重复写入 blockers 和 false fields，便于机器验收。"""
    false_fields = {key: False for key in SAFETY_FALSE_FIELDS}
    return {
        "schema": SUMMARY_SCHEMA,
        "generated_at_utc": generated_at_utc,
        "same_window_route_readiness_status": READINESS_STATUS,
        "proof_boundary": PROOF_BOUNDARY,
        "owner_role": "robot-algorithm-engineer",
        "packet_id": EXPECTED_PACKET_ID,
        "task_id": EXPECTED_TASK_ID,
        "route_intent_id": EXPECTED_ROUTE_INTENT_ID,
        "route_csv_row_count": EXPECTED_ROUTE_ROW_COUNT,
        "segment_count": EXPECTED_SEGMENT_COUNT,
        "replay_jsonl_event_count": EXPECTED_ROUTE_ROW_COUNT,
        "packet_jsonl_event_count": EXPECTED_ROUTE_ROW_COUNT,
        "path_structured_pose_count": EXPECTED_ROUTE_ROW_COUNT,
        "source_identity_verified": True,
        "source_counts_verified": True,
        "source_no_motion_guard_verified": True,
        "source_fixed_false_fields_verified": True,
        "mock_progress_verified": True,
        "source_artifacts": source_artifact_summary(
            gate_record_path,
            bounded_plan_path,
            mock_summary_path,
            progress_path,
            gate_status,
            plan_status,
            mock_status,
            progress_status,
        ),
        "source_status_summary": {
            "controlled_route_execution_gate_status": gate_record["controlled_route_execution_gate_status"],
            "execution_plan_status": bounded_plan["execution_plan_status"],
            "mock_execution_status": mock_summary["mock_execution_status"],
            "mock_progress_event_count": progress_status["event_count"],
            "mock_total_distance_m": mock_summary.get("mock_total_distance_m"),
            "mock_total_elapsed_s": mock_summary.get("mock_total_elapsed_s"),
        },
        "missing_evidence": list(MISSING_EVIDENCE),
        "missing_evidence_detail": {
            "explicit_operator_approval": "same-window live route/HIL capture has not been operator approved",
            "current_live_stop_hil": "current live stop path and HIL material are missing; mock stop/HIL gates do not count",
            "same_window_scan_readiness": "no same-window /scan readiness artifact was consumed by this precheck",
            "same_window_amcl_pose_readiness": "no same-window /amcl_pose readiness artifact was consumed by this precheck",
            "same_window_map_to_odom_tf_readiness": "no same-window dynamic map_to_odom TF readiness artifact was consumed",
            "nav2_controller_result": "bounded plan and mock progress do not include Nav2 controller/BT result",
            "delivery_or_operator_acceptance": "no delivery, dropoff, or operator acceptance evidence was consumed",
        },
        "next_live_capture_allowed": False,
        "next_live_capture_gate": {
            "status": READINESS_STATUS,
            "required_before_capture": list(MISSING_EVIDENCE),
            "forbidden_in_this_artifact": list(NO_MOTION_GUARDS),
        },
        "no_motion_control_guard": list(NO_MOTION_GUARDS),
        "rejected_claims": list(REJECTED_CLAIMS),
        "fixed_false_fields": false_fields,
        "checks": [
            {
                "name": "source_route_identity",
                "status": "pass",
                "detail": "gate record, bounded plan, mock summary, and progress JSONL share the accepted packet/task/route identity",
            },
            {
                "name": "source_counts",
                "status": "pass",
                "detail": "28 route rows and 27 bounded/mock segments were verified before writing precheck summary",
            },
            {
                "name": "same_window_live_evidence",
                "status": "blocked",
                "detail": "explicit operator approval, current live stop/HIL, /scan, AMCL, map_to_odom TF, Nav2/controller result, and delivery/operator acceptance are missing",
            },
            {
                "name": "no_motion_guard",
                "status": "pass",
                "detail": "no /cmd_vel, no /api/base/manual, no NavigateToPose, no WAVE ROVER UART",
            },
            {
                "name": "fixed_false_fields",
                "status": "pass",
                "detail": "route_execution_success=false, delivery_success=false, hil_pass=false, safe_to_control=false",
            },
        ],
        "rg_acceptance_anchors": [
            "same_window_route_readiness_precheck",
            READINESS_STATUS,
            PROOF_BOUNDARY,
            "route_execution_success=false",
            "delivery_success=false",
            "hil_pass=false",
            "safe_to_control=false",
            "no /cmd_vel",
            "no /api/base/manual",
            "no NavigateToPose",
            "no WAVE ROVER UART",
        ],
        **false_fields,
    }


def write_outputs(
    gate_record_path: Path,
    bounded_plan_path: Path,
    mock_summary_path: Path,
    progress_path: Path,
    output_dir: Path,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """CLI 与单测共用入口；所有 source 校验通过后才创建输出目录和写 JSON。"""
    gate_record = load_json_object(gate_record_path, "gate_record")
    bounded_plan = load_json_object(bounded_plan_path, "bounded_plan")
    mock_summary = load_json_object(mock_summary_path, "mock_summary")
    progress_events = load_jsonl_objects(progress_path, "mock_progress")

    gate_status = validate_gate_record(gate_record)
    plan_status = validate_bounded_plan(bounded_plan)
    mock_status = validate_mock_summary(mock_summary)
    progress_status = validate_progress_events(progress_events)

    summary = build_summary(
        gate_record_path,
        bounded_plan_path,
        mock_summary_path,
        progress_path,
        gate_record,
        bounded_plan,
        mock_summary,
        gate_status,
        plan_status,
        mock_status,
        progress_status,
        generated_at_utc or utc_now_iso(),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / SUMMARY_OUTPUT_NAME
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def parse_args() -> argparse.Namespace:
    """CLI 只暴露 artifact 输入和输出目录，不提供任何控制或 live runtime 参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate-record", required=True, type=Path)
    parser.add_argument("--bounded-plan", required=True, type=Path)
    parser.add_argument("--mock-execution-summary", required=True, type=Path)
    parser.add_argument("--mock-execution-progress", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    """命令行入口；失败时 stderr 仍固定安全字段 false，避免外层脚本误判。"""
    args = parse_args()
    try:
        summary = write_outputs(
            args.gate_record,
            args.bounded_plan,
            args.mock_execution_summary,
            args.mock_execution_progress,
            args.output_dir,
        )
    except ReadinessPrecheckInputError as exc:
        print(
            json.dumps(
                {
                    "status": "blocked_same_window_route_readiness_precheck_input_mismatch",
                    "error": str(exc),
                    "route_execution_success": False,
                    "delivery_success": False,
                    "hil_pass": False,
                    "safe_to_control": False,
                    "robot_control_executed": False,
                    "publishes_cmd_vel": False,
                    "calls_base_manual": False,
                    "uses_base_uart": False,
                    "next_live_capture_allowed": False,
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
                "same_window_route_readiness_status": summary["same_window_route_readiness_status"],
                "proof_boundary": summary["proof_boundary"],
                "route_execution_success": False,
                "delivery_success": False,
                "hil_pass": False,
                "safe_to_control": False,
                "next_live_capture_allowed": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
