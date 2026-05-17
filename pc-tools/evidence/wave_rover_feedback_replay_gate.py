#!/usr/bin/env python3
"""WAVE ROVER T=1001 feedback replay / interval / topic-alignment gate.

该工具只读取文件，不打开串口、不 import ROS2、不访问硬件。它用于真实
HIL 材料回填后的离线复账，也允许本机用 synthetic fixture 验证解析逻辑。
vendor 来源见 docs/vendor/VENDOR_INDEX.md 与 WAVE_ROVER_V0.9/json_cmd.h。
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# schema/boundary 是 Robot diagnostics 与 mobile/web 只读消费的稳定契约。
SCHEMA = "trashbot.wave_rover_feedback_replay.v1"
SCHEMA_VERSION = 1
EVIDENCE_BOUNDARY = "software_proof_docker_wave_rover_feedback_replay_gate"
SOURCE = "software_proof"
SAME_EVIDENCE_REF_REQUIRED = True

# T=1001 与字段来自 docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h。
FEEDBACK_TYPE = 1001
REQUIRED_FEEDBACK_FIELDS = ("T", "L", "R", "r", "p", "y", "v")
WRAPPER_PAYLOAD_KEYS = ("feedback", "payload", "message")
TIMESTAMP_KEYS = ("timestamp", "t", "time", "monotonic_time")

# 同一 evidence_ref 只能使用安全字符，避免把本机路径、串口名或凭证塞进摘要。
SAFE_EVIDENCE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}$")

# topic once snapshot 只检查最小字段存在；真实数值可信性必须留给 HIL。
TOPIC_REQUIREMENTS = {
    "odom": ("pose", "twist", "position", "orientation", "linear", "angular"),
    "imu": ("orientation", "angular_velocity", "linear_acceleration", "rpy", "yaw"),
    "battery": ("voltage", "percentage", "power_supply_status", "current"),
}

# not_proven 明确阻止下游把本 gate 当成实车通过。
NOT_PROVEN = (
    "real_wave_rover_feedback",
    "real_uart_session",
    "real_hil_pass",
    "real_odom",
    "real_imu",
    "real_battery",
    "real_delivery_success",
)

NEXT_REQUIRED_EVIDENCE = (
    "real_hil_feedback_T1001.log_with_timestamps",
    "real_hil_odom_once.jsonl",
    "real_hil_imu_once.jsonl",
    "real_hil_battery_once.jsonl",
    "same_safe_evidence_ref_across_packet",
    "operator_hil_report_declaring_source_hil_pass_separately",
)


def _utc_now() -> str:
    # UTC 时间只用于 artifact 排序，不参与硬件事实判断。
    return datetime.now(timezone.utc).isoformat()


def _read_json_object(value: Any) -> dict[str, Any] | None:
    # wrapper 的 message/payload 可能是 JSON 字符串，坏 JSON 必须 fail closed。
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            payload = json.loads(value)
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None
    return None


def _parse_timestamp(value: Any) -> float | None:
    # 支持 epoch 秒、毫秒级大整数、以及 ISO8601；无法解析时不猜单位。
    if isinstance(value, (int, float)):
        number = float(value)
        if number > 1_000_000_000_000:
            return number / 1000.0
        return number
    if isinstance(value, str) and value.strip():
        text = value.strip()
        try:
            return _parse_timestamp(float(text))
        except ValueError:
            pass
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    return None


def _first_timestamp(record: dict[str, Any]) -> float | None:
    # timestamp 可在 wrapper 或 feedback payload 内；任一合法值都可用于 interval。
    for key in TIMESTAMP_KEYS:
        if key in record:
            parsed = _parse_timestamp(record.get(key))
            if parsed is not None:
                return parsed
    return None


def _extract_feedback(line_payload: dict[str, Any]) -> tuple[dict[str, Any] | None, float | None, str]:
    # 直接 T=1001 是最短路径；wrapper 只从白名单字段拆 payload。
    wrapper_timestamp = _first_timestamp(line_payload)
    direct_t = line_payload.get("T")
    if direct_t == FEEDBACK_TYPE:
        return line_payload, wrapper_timestamp, ""

    for key in WRAPPER_PAYLOAD_KEYS:
        nested = _read_json_object(line_payload.get(key))
        if nested is None:
            continue
        if nested.get("T") == FEEDBACK_TYPE:
            return nested, wrapper_timestamp if wrapper_timestamp is not None else _first_timestamp(nested), ""

    # 非 T=1001 不作为噪声跳过，因为本 gate 专门复账 T=1001 feedback packet。
    return None, wrapper_timestamp, "missing_T1001_feedback"


def _load_feedback_log(path: str) -> tuple[list[dict[str, Any]], list[str]]:
    # 文件级错误必须变成 blocked，而不是给出半真半假的 replay pass。
    errors: list[str] = []
    records: list[dict[str, Any]] = []
    try:
        lines = Path(path).expanduser().read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return [], ["feedback_T1001_missing"]
    except (OSError, UnicodeDecodeError):
        return [], ["feedback_T1001_read_error"]

    for index, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"line_{index}:bad_json")
            continue
        if not isinstance(payload, dict):
            errors.append(f"line_{index}:not_object")
            continue
        feedback, timestamp, issue = _extract_feedback(payload)
        if issue:
            errors.append(f"line_{index}:{issue}")
            continue
        assert feedback is not None
        missing = [field for field in REQUIRED_FEEDBACK_FIELDS if field not in feedback]
        if missing:
            errors.append(f"line_{index}:missing_fields:{','.join(missing)}")
            continue
        records.append(
            {
                "line": index,
                "timestamp": timestamp,
                "feedback": {field: feedback.get(field) for field in REQUIRED_FEEDBACK_FIELDS},
            }
        )

    if not records:
        errors.append("feedback_T1001_no_valid_records")
    return records, errors


def _interval_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    # 少于两个 timestamp 只能证明可解析，不能证明频率或 HIL interval。
    timestamps = [record["timestamp"] for record in records if isinstance(record.get("timestamp"), (int, float))]
    if len(timestamps) < 2:
        return {
            "status": "blocked_missing_timestamps",
            "record_count": len(records),
            "timestamp_count": len(timestamps),
            "interval_count": 0,
            "min_s": None,
            "max_s": None,
            "median_s": None,
            "large_gap_count": 0,
            "large_gap_threshold_s": None,
        }

    intervals = [round(timestamps[i] - timestamps[i - 1], 6) for i in range(1, len(timestamps))]
    unordered = [gap for gap in intervals if gap < 0]
    positive = [gap for gap in intervals if gap >= 0]
    median = statistics.median(positive) if positive else 0.0
    baseline = min((gap for gap in positive if gap > 0), default=median)
    # 阈值以最小正间隔为基准，避免两帧样本时异常大 gap 把自身抬成正常。
    threshold = max(baseline * 2.5, 1.0)
    large_gaps = [gap for gap in positive if gap > threshold]
    status = "pass"
    if unordered:
        status = "blocked_unordered_timestamps"
    elif large_gaps:
        status = "blocked_large_gap"

    return {
        "status": status,
        "record_count": len(records),
        "timestamp_count": len(timestamps),
        "interval_count": len(intervals),
        "min_s": min(intervals) if intervals else None,
        "max_s": max(intervals) if intervals else None,
        "median_s": median,
        "large_gap_count": len(large_gaps),
        "large_gap_threshold_s": round(threshold, 6),
    }


def _load_first_jsonl(path: str, label: str) -> tuple[dict[str, Any], str]:
    # once JSONL 至少要有一条 object；多行时第一条代表该 topic 的 snapshot。
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    return {}, f"{label}_line_{line_number}_bad_json"
                if not isinstance(payload, dict):
                    return {}, f"{label}_line_{line_number}_not_object"
                return payload, ""
    except FileNotFoundError:
        return {}, f"{label}_missing"
    except (OSError, UnicodeDecodeError):
        return {}, f"{label}_read_error"
    return {}, f"{label}_empty"


def _nested_dict(value: Any) -> dict[str, Any]:
    # 上游 header/evidence/route_progress 可能缺失或类型不稳，统一按空对象处理。
    return value if isinstance(value, dict) else {}


def _extract_evidence_ref(payload: dict[str, Any]) -> str:
    # evidence_ref 的位置按需求白名单查找，避免深层任意字段误匹配。
    candidates = (
        payload.get("evidence_ref"),
        _nested_dict(payload.get("header")).get("evidence_ref"),
        _nested_dict(payload.get("evidence")).get("evidence_ref"),
        _nested_dict(payload.get("route_progress")).get("evidence_ref"),
    )
    for candidate in candidates:
        text = str(candidate or "").strip()
        if text:
            return text
    return ""


def _has_minimum_topic_fields(label: str, payload: dict[str, Any]) -> bool:
    # 检查存在性而非真实性；真实性必须由实车 HIL packet 单独证明。
    requirements = TOPIC_REQUIREMENTS[label]
    return any(field in payload for field in requirements)


def _topic_alignment(paths: dict[str, str], requested_ref: str) -> dict[str, Any]:
    # 逐 topic fail-closed，任何缺失或 ref mismatch 都让整体 blocked。
    topics: dict[str, Any] = {}
    refs: dict[str, str] = {}
    issues: list[str] = []

    for label, path in paths.items():
        payload, load_issue = _load_first_jsonl(path, label)
        if load_issue:
            topics[label] = {"status": "blocked", "issue": load_issue, "evidence_ref": ""}
            issues.append(load_issue)
            continue

        evidence_ref = _extract_evidence_ref(payload)
        fields_ok = _has_minimum_topic_fields(label, payload)
        ref_ok = bool(evidence_ref and SAFE_EVIDENCE_REF.match(evidence_ref))
        if not ref_ok:
            issues.append(f"{label}_missing_or_unsafe_evidence_ref")
        if not fields_ok:
            issues.append(f"{label}_missing_minimum_fields")
        refs[label] = evidence_ref
        topics[label] = {
            "status": "pass" if ref_ok and fields_ok else "blocked",
            "evidence_ref": evidence_ref if ref_ok else "",
            "minimum_fields_status": "pass" if fields_ok else "blocked",
        }

    observed_refs = {ref for ref in refs.values() if ref}
    expected_ref = requested_ref.strip()
    if expected_ref and not SAFE_EVIDENCE_REF.match(expected_ref):
        issues.append("requested_evidence_ref_unsafe")
    if expected_ref and any(ref != expected_ref for ref in observed_refs):
        issues.append("evidence_ref_mismatch")
    if not expected_ref and len(observed_refs) == 1:
        expected_ref = next(iter(observed_refs))
    elif not expected_ref:
        issues.append("evidence_ref_missing_or_ambiguous")
    if len(observed_refs) > 1:
        issues.append("topic_evidence_ref_mismatch")

    return {
        "status": "pass" if not issues else "blocked",
        "evidence_ref": expected_ref if expected_ref and SAFE_EVIDENCE_REF.match(expected_ref) else "",
        "topics": topics,
        "issues": sorted(set(issues)),
    }


def build_summary(
    feedback_log: str,
    odom_once: str,
    imu_once: str,
    battery_once: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], int]:
    # summary 始终生成，失败通过 status 表达，便于自动化收集 blocked artifact。
    records, feedback_errors = _load_feedback_log(feedback_log)
    interval = _interval_summary(records)
    alignment = _topic_alignment(
        {"odom": odom_once, "imu": imu_once, "battery": battery_once},
        evidence_ref,
    )

    feedback_status = "pass" if records and not feedback_errors else "blocked"
    interval_status = interval["status"]
    topic_status = alignment["status"]
    overall_status = "ready_for_hil_review_not_proven"
    if feedback_status != "pass" or interval_status != "pass" or topic_status != "pass":
        overall_status = "blocked_not_proven"

    summary = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "overall_status": overall_status,
        "feedback_replay_status": feedback_status,
        "interval_status": interval_status,
        "topic_alignment_status": topic_status,
        "same_evidence_ref_required": SAME_EVIDENCE_REF_REQUIRED,
        "evidence_ref": alignment["evidence_ref"],
        "feedback_replay": {
            "record_count": len(records),
            "first_line": records[0]["line"] if records else None,
            "last_line": records[-1]["line"] if records else None,
            "errors": feedback_errors,
            "required_fields": list(REQUIRED_FEEDBACK_FIELDS),
            "vendor_feedback_type": "T=1001",
        },
        "interval": interval,
        "topic_alignment": alignment,
        "vendor_sources": [
            "docs/vendor/VENDOR_INDEX.md",
            "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
            "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
            "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
        ],
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
        "next_required_evidence": list(NEXT_REQUIRED_EVIDENCE),
    }
    # blocked exit code 帮 CI/脚本感知失败；artifact 仍可被 Product/Robot 消费。
    return summary, 0 if overall_status == "ready_for_hil_review_not_proven" else 2


def write_json(payload: dict[str, Any], output: str) -> None:
    # 输出目录按需创建，便于 sprint artifact 写到临时 evidence packet。
    path = Path(output).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay WAVE ROVER T=1001 feedback logs and align odom/imu/battery once JSONL snapshots.",
    )
    parser.add_argument("feedback_log", help="Path to feedback_T1001.log")
    parser.add_argument("odom_once", help="Path to odom_once.jsonl")
    parser.add_argument("imu_once", help="Path to imu_once.jsonl")
    parser.add_argument("battery_once", help="Path to battery_once.jsonl")
    parser.add_argument("--evidence-ref", default="", help="Expected safe evidence_ref shared by all once JSONL files")
    parser.add_argument("--summary-output", default="", help="Optional path for full JSON summary artifact")
    parser.add_argument("--once-json", action="store_true", help="Print compact one-line JSON summary to stdout")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary, exit_code = build_summary(
        args.feedback_log,
        args.odom_once,
        args.imu_once,
        args.battery_once,
        args.evidence_ref,
    )
    if args.summary_output:
        write_json(summary, args.summary_output)
    if args.once_json or not args.summary_output:
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
