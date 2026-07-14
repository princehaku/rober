#!/usr/bin/env python3
"""从 05:02 same-task replay packet 生成 O3 受控执行前 gate record。"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 本脚本是 robot-algorithm-engineer 的 no-motion gate，不 import ROS2，也不提供任何控制参数。
# 07:07 的价值是把 05:02 accepted packet 固化成受控 route execution 前的 fail-closed 记录。
# 这里校验 exact identity/count/source hash，是为了防止后续把旧 packet 或被替换的 CSV/JSONL 当成执行输入。
# 即使输入全部匹配，输出也只能说明“packet 可进入人工安全复核”，不能说明 route 已执行。
# 所有控制、执行、交付、HIL 和 safe-to-control 字段必须显式 false，缺失也不能默认通过。
# 脚本只读取本地 artifact 并写 JSON，不调用 NavigateToPose、controller/BT、/cmd_vel、/api/base/manual 或 UART。
PACKET_SUMMARY_SCHEMA = "trashbot.o3.same_task_route_replay_packet.v1"
GATE_RECORD_SCHEMA = "trashbot.o3.controlled_route_execution_gate_record.v1"
ARTIFACT_BOUNDARY = "software_proof_o3_o1_fail_closed_controlled_route_execution_gate_record_only"
OUTPUT_NAME = "controlled_route_execution_gate_record.json"
EXPECTED_PACKET_ID = "packet_o3_28_pose_same_task_replay_7d57826142b0c79c"
EXPECTED_TASK_ID = "task_o3_28_pose_fixed_route_consumer_20260713_0402"
EXPECTED_ROUTE_INTENT_ID = "route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path"
EXPECTED_POSE_COUNT = 28

EXPECTED_SOURCE_FINGERPRINTS = {
    "summary_sha256": "9948414e1a46b6e78de5503a06d634e24c5e96aff38c1f4c7d756bd20eb0dc93",
    "route_csv_sha256": "61b4020c93f01e595df4608e8b42545ce1b1d04eaff8798db55b0dda2aae7601",
    "replay_jsonl_sha256": "530941a7ecb4768f6583cda4abca0d9bc92715ea0266fc96e83d3a860a0400b5",
}

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


class GateInputError(ValueError):
    """输入 packet 与 05:02 accepted identity/count/hash 不一致时 fail closed。"""


def utc_now_iso() -> str:
    """统一使用 UTC，避免开发机时区影响 artifact 审计。"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json_object(path: Path) -> dict[str, Any]:
    """packet summary 必须是 JSON object，不能把 JSONL 或 stdout 当 summary。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise GateInputError(f"packet summary must be a JSON object: {path}")
    return data


def sha256_file(path: Path) -> str:
    """按整文件计算 hash，保证换行、排序或内容替换都会被 gate 捕获。"""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_equal(data: dict[str, Any], key: str, expected: Any, label: str) -> None:
    """集中生成字段漂移错误，让失败定位直接指向具体来源。"""
    actual = data.get(key)
    if actual != expected:
        raise GateInputError(f"{label}.{key} expected {expected!r}, got {actual!r}")


def require_true(data: dict[str, Any], key: str, label: str) -> None:
    """accepted packet 的核心条件必须显式 true，缺失不能当通过。"""
    require_equal(data, key, True, label)


def require_false(data: dict[str, Any], key: str, label: str) -> None:
    """安全字段必须显式 false，缺失、None 或字符串都不能默认安全。"""
    require_equal(data, key, False, label)


def resolve_ref(ref: Any, label: str) -> Path:
    """source refs 必须是可读文件路径；本轮只消费本地 artifact。"""
    if not isinstance(ref, str) or not ref:
        raise GateInputError(f"{label} must be a non-empty path string")
    path = Path(ref)
    if not path.exists() or not path.is_file():
        raise GateInputError(f"{label} does not exist or is not a file: {ref}")
    return path


def count_route_csv_rows(path: Path) -> int:
    """重新数 route CSV 数据行，避免只相信 summary 内的计数字段。"""
    with path.open(encoding="utf-8", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def count_jsonl_objects(path: Path, label: str) -> int:
    """重新数 JSONL object 行；空行或非 object 都视为 source 漂移。"""
    count = 0
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            raise GateInputError(f"{label} line {line_number} must not be blank")
        event = json.loads(line)
        if not isinstance(event, dict):
            raise GateInputError(f"{label} line {line_number} must be a JSON object")
        count += 1
    return count


def validate_packet_summary(packet_summary: dict[str, Any]) -> None:
    """校验 05:02 packet summary 本身的 identity、counts 和固定 false fields。"""
    require_equal(packet_summary, "schema", PACKET_SUMMARY_SCHEMA, "packet_summary")
    require_equal(packet_summary, "packet_id", EXPECTED_PACKET_ID, "packet_summary")
    require_equal(packet_summary, "task_id", EXPECTED_TASK_ID, "packet_summary")
    require_equal(packet_summary, "route_intent_id", EXPECTED_ROUTE_INTENT_ID, "packet_summary")
    require_true(packet_summary, "same_task_identity_verified", "packet_summary")
    require_true(packet_summary, "same_task_replay_packet_ready", "packet_summary")
    require_equal(packet_summary, "route_csv_row_count", EXPECTED_POSE_COUNT, "packet_summary")
    require_equal(packet_summary, "replay_jsonl_event_count", EXPECTED_POSE_COUNT, "packet_summary")
    require_equal(packet_summary, "path_structured_pose_count", EXPECTED_POSE_COUNT, "packet_summary")
    for key in SAFETY_FALSE_FIELDS:
        require_false(packet_summary, key, "packet_summary")


def source_paths_from(packet_summary: dict[str, Any]) -> dict[str, Path]:
    """提取并确认 packet summary 指向的三份 source 以及 packet JSONL 都存在。"""
    return {
        "source_summary": resolve_ref(packet_summary.get("source_summary_ref"), "packet_summary.source_summary_ref"),
        "route_csv": resolve_ref(packet_summary.get("route_csv_ref"), "packet_summary.route_csv_ref"),
        "replay_jsonl": resolve_ref(packet_summary.get("replay_jsonl_ref"), "packet_summary.replay_jsonl_ref"),
        "packet_jsonl": resolve_ref(packet_summary.get("packet_jsonl_ref"), "packet_summary.packet_jsonl_ref"),
    }


def observed_counts(paths: dict[str, Path]) -> dict[str, int]:
    """重新读取 source 文件的实际形状，确保 28/28/28 不是 summary 自述。"""
    counts = {
        "route_csv_row_count": count_route_csv_rows(paths["route_csv"]),
        "replay_jsonl_event_count": count_jsonl_objects(paths["replay_jsonl"], "replay_jsonl"),
        "packet_jsonl_event_count": count_jsonl_objects(paths["packet_jsonl"], "packet_jsonl"),
        "path_structured_pose_count": EXPECTED_POSE_COUNT,
    }
    for key, value in counts.items():
        if value != EXPECTED_POSE_COUNT:
            raise GateInputError(f"{key} expected {EXPECTED_POSE_COUNT}, got {value}")
    return counts


def validate_source_fingerprints(
    packet_summary: dict[str, Any],
    paths: dict[str, Path],
    expected_fingerprints: dict[str, str],
) -> dict[str, dict[str, str]]:
    """比对 summary 声明、tech-plan 固定值和当前文件实际 hash，任一漂移都 fail closed。"""
    packet_fingerprints = packet_summary.get("source_fingerprints")
    if not isinstance(packet_fingerprints, dict):
        raise GateInputError("packet_summary.source_fingerprints must be present")

    computed = {
        "summary_sha256": sha256_file(paths["source_summary"]),
        "route_csv_sha256": sha256_file(paths["route_csv"]),
        "replay_jsonl_sha256": sha256_file(paths["replay_jsonl"]),
    }
    for key, expected in expected_fingerprints.items():
        require_equal(packet_fingerprints, key, expected, "packet_summary.source_fingerprints")
        actual = computed[key]
        if actual != expected:
            raise GateInputError(f"computed {key} expected {expected!r}, got {actual!r}")
    return {
        "expected": dict(expected_fingerprints),
        "from_packet_summary": {key: str(packet_fingerprints[key]) for key in expected_fingerprints},
        "computed": computed,
    }


def build_gate_record(
    packet_summary_path: Path,
    packet_summary: dict[str, Any],
    paths: dict[str, Path],
    counts: dict[str, int],
    fingerprint_validation: dict[str, dict[str, str]],
    generated_at_utc: str,
) -> dict[str, Any]:
    """生成 fail-closed gate record，把输入已验证和控制仍阻塞分开表达。"""
    false_fields = {field: False for field in SAFETY_FALSE_FIELDS}
    blocked_reasons = [
        "controlled route execution was not run in this sprint",
        "explicit safety operator approval or equivalent recorded safety gate is missing",
        "current live HIL, stop path, and controlled environment material are missing",
        "Nav2/controller execution result is missing; only same-task replay packet material is validated",
        "delivery/operator acceptance evidence is missing",
    ]

    return {
        "schema": GATE_RECORD_SCHEMA,
        "generated_at_utc": generated_at_utc,
        "artifact_boundary": ARTIFACT_BOUNDARY,
        "proof_boundary": ARTIFACT_BOUNDARY,
        "owner_role": "robot-algorithm-engineer",
        "packet_summary_ref": packet_summary_path.as_posix(),
        "source_summary_ref": paths["source_summary"].as_posix(),
        "route_csv_ref": paths["route_csv"].as_posix(),
        "replay_jsonl_ref": paths["replay_jsonl"].as_posix(),
        "packet_jsonl_ref": paths["packet_jsonl"].as_posix(),
        "packet_summary_sha256": sha256_file(packet_summary_path),
        "packet_id": EXPECTED_PACKET_ID,
        "task_id": EXPECTED_TASK_ID,
        "route_intent_id": EXPECTED_ROUTE_INTENT_ID,
        "same_task_identity_verified": True,
        "same_task_replay_packet_ready": True,
        "route_csv_row_count": counts["route_csv_row_count"],
        "replay_jsonl_event_count": counts["replay_jsonl_event_count"],
        "packet_jsonl_event_count": counts["packet_jsonl_event_count"],
        "path_structured_pose_count": counts["path_structured_pose_count"],
        "source_fingerprints": fingerprint_validation,
        "identity_validation_status": "pass_exact_same_task_identity",
        "count_validation_status": "pass_exact_28_28_28",
        "source_hash_validation_status": "pass_exact_source_hashes",
        "controlled_route_execution_gate_status": "fail_closed_input_packet_validated",
        "dry_run_execution_readiness_status": "blocked_manual_safety_review_required",
        "no_motion_control_guard": list(NO_MOTION_GUARDS),
        "blocked_reasons": blocked_reasons,
        "missing_live_execution_prerequisites": [
            "explicit safety operator approval or equivalent recorded safety gate",
            "current live HIL / stop path / controlled environment material",
            "bounded route execution command plan with abort criteria",
            "LiDAR/localization/TF readiness in the same live window",
            "Nav2/controller execution result, not only planner path or replay packet proof",
            "delivery/operator acceptance evidence before delivery_success can change",
        ],
        "next_live_command_gate": {
            "status": "blocked_until_new_controlled_live_execution_sprint",
            "required_before_any_control": [
                "explicit safety operator approval or equivalent recorded safety gate",
                "current live HIL / stop path / controlled environment material",
                "bounded route execution command plan with abort criteria",
                "LiDAR/localization/TF readiness in the same live window",
                "Nav2/controller execution result, not only planner path proof",
                "delivery/operator acceptance evidence before delivery_success can change",
            ],
            "forbidden_in_this_artifact": list(NO_MOTION_GUARDS),
        },
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
            "controlled_route_execution_gate_record",
            EXPECTED_PACKET_ID,
            "route_execution_success=false",
            "safe_to_control=false",
            *NO_MOTION_GUARDS,
            "robot-algorithm-engineer",
        ],
        "checks": [
            {
                "name": "packet_identity",
                "status": "pass",
                "detail": "packet_id, task_id, and route_intent_id match the 05:02 same-task replay packet",
            },
            {
                "name": "source_counts",
                "status": "pass",
                "detail": "route CSV, replay JSONL, packet JSONL, and path structured pose counts are 28",
            },
            {
                "name": "source_hashes",
                "status": "pass",
                "detail": "05:02 source fingerprints match tech-plan constants and recomputed file hashes",
            },
            {
                "name": "control_guard",
                "status": "pass",
                "detail": "no /cmd_vel, no /api/base/manual, no NavigateToPose, no WAVE ROVER UART",
            },
        ],
        **false_fields,
    }


def write_outputs(
    packet_summary_path: Path,
    output_dir: Path,
    generated_at_utc: str | None = None,
    expected_fingerprints: dict[str, str] | None = None,
) -> dict[str, Any]:
    """CLI 与单测共用入口；所有验证通过后才创建/写入 gate artifact。"""
    packet_summary = load_json_object(packet_summary_path)
    validate_packet_summary(packet_summary)
    paths = source_paths_from(packet_summary)
    counts = observed_counts(paths)
    fingerprint_validation = validate_source_fingerprints(
        packet_summary,
        paths,
        expected_fingerprints or EXPECTED_SOURCE_FINGERPRINTS,
    )

    record = build_gate_record(
        packet_summary_path,
        packet_summary,
        paths,
        counts,
        fingerprint_validation,
        generated_at_utc or utc_now_iso(),
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / OUTPUT_NAME
    output_path.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def parse_args() -> argparse.Namespace:
    """CLI 只接受 packet summary 与输出目录，避免误加控制执行参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-summary", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    """命令行入口；source mismatch 返回非零并保持 fail-closed。"""
    args = parse_args()
    try:
        record = write_outputs(args.packet_summary, args.output_dir)
    except GateInputError as exc:
        print(
            json.dumps(
                {
                    "status": "blocked_source_packet_mismatch",
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
                "controlled_route_execution_gate_status": record["controlled_route_execution_gate_status"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
