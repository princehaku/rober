#!/usr/bin/env python3
"""把 manual proxy 与现场材料复核成 operator report 可用草稿。"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


# 统一输出 schema，避免后续 operator/report 草稿再出现多版本字段漂移。
SCHEMA = "trashbot.motion_evidence_material_review.v1"
# 这些来源直接对应本轮允许引用的本地事实，不扩展到在线资料。
VENDOR_SOURCES = [
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
]
# 轮速字段兼容当前 sprint 要求的几种命名，避免不同 artifact 形状漏判。
WHEEL_FIELD_PAIRS = (
    ("L", "R"),
    ("left", "right"),
    ("left_speed", "right_speed"),
    ("left_wheel_speed", "right_wheel_speed"),
    ("left_mps", "right_mps"),
)
# LiDAR delta 阈值继续保持保守，只用于“材料足够”判定，不外推成 HIL pass。
SCAN_DELTA_THRESHOLDS = {
    "min_valid_beams": 8,
    "average_abs_delta_min_m": 0.03,
    "max_abs_delta_min_m": 0.08,
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI 只接受文件输入，故参数都按路径处理。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manual-response", required=True, help="PC /api/robot-control/base/manual 响应 JSON")
    parser.add_argument("--base-feedback", help="原始 /api/base/feedback-samples/latest JSON 或 T=1001 JSONL")
    parser.add_argument("--scan-before", help="baseline 或 scan proof JSON")
    parser.add_argument("--scan-after", help="post 或 scan proof JSON")
    parser.add_argument("--output", required=True, help="输出 review JSON")
    return parser.parse_args(argv)


def load_json_file(path: str) -> Any:
    """统一读取 JSON 文件，并在上层集中处理格式错误。"""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_json_or_jsonl(path: str) -> Any:
    """反馈样本既可能是单个 JSON，也可能是逐行 JSONL。"""
    text = Path(path).read_text(encoding="utf-8")
    stripped = text.strip()
    if not stripped:
        raise ValueError("empty file")
    non_empty_lines = [line.strip() for line in text.splitlines() if line.strip()]
    # 多行且每行都是对象时优先按 JSONL 处理，避免首字符 `{` 的 JSONL 被误判成单 JSON。
    if len(non_empty_lines) > 1 and all(line.startswith("{") for line in non_empty_lines):
        items: list[Any] = []
        for line_no, line in enumerate(non_empty_lines, start=1):
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid jsonl at line {line_no}: {exc.msg}") from exc
        return items
    if stripped[0] in "[{":
        return json.loads(stripped)

    items: list[Any] = []
    for line_no, line in enumerate(non_empty_lines, start=1):
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid jsonl at line {line_no}: {exc.msg}") from exc
    return items


def as_bool(value: Any) -> bool:
    """兼容字符串布尔值，避免 artifact 来源不同导致判定偏差。"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no", ""}:
            return False
    return bool(value)


def to_number(value: Any) -> float | None:
    """所有数值判定都走同一转换，避免字符串数字被误判为缺失。"""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        if math.isfinite(float(value)):
            return float(value)
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text or text.lower() in {"nan", "null", "none"}:
            return None
        try:
            number = float(text)
        except ValueError:
            return None
        if math.isfinite(number):
            return number
    return None


def nested_get(container: Any, path: tuple[str, ...]) -> Any:
    """从嵌套对象里保守取值，取不到直接返回 None。"""
    current = container
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def collect_candidate_frames(payload: Any) -> list[dict[str, Any]]:
    """递归收集可能的反馈帧，但只保留 dict，避免把路径字符串误当样本。"""
    frames: list[dict[str, Any]] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            # 只有带 T=1001 或显式轮速字段的对象才纳入候选，避免泛滥扫描。
            if feedback_type(node) == 1001 or has_explicit_wheel_fields(node):
                frames.append(node)
            for value in node.values():
                walk(value)
            return
        if isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return frames


def feedback_type(frame: dict[str, Any]) -> int | None:
    """兼容字符串/数字 T 字段，严格只认 1001。"""
    number = to_number(frame.get("T"))
    if number is None:
        return None
    return int(number)


def has_explicit_wheel_fields(frame: dict[str, Any]) -> bool:
    """没有 T=1001 时，只接受明确轮速字段的对象参与 wheel 复核。"""
    for left_key, right_key in WHEEL_FIELD_PAIRS:
        if left_key in frame or right_key in frame:
            return True
    return False


def frame_wheel_pair(frame: dict[str, Any]) -> tuple[float | None, float | None]:
    """按优先顺序提取左右轮，保持同一对象内配对。"""
    for left_key, right_key in WHEEL_FIELD_PAIRS:
        if left_key in frame or right_key in frame:
            return to_number(frame.get(left_key)), to_number(frame.get(right_key))
    return None, None


def review_wheel_feedback(payload: Any) -> tuple[bool, list[str], list[str], dict[str, Any]]:
    """左右轮必须在同一帧或同一候选对象内同时非零，单侧非零不能算通过。"""
    failure_reasons: list[str] = []
    warnings: list[str] = []
    frames = collect_candidate_frames(payload)
    details = {
        "candidate_frame_count": len(frames),
        "matched_frame_count": 0,
        "matched_field_pairs": [],
    }
    if not frames:
        failure_reasons.append("base_feedback_missing_parseable_t1001_or_explicit_wheel_fields")
        return False, failure_reasons, warnings, details

    saw_any_pair = False
    saw_single_side_nonzero = False
    for frame in frames:
        left_value, right_value = frame_wheel_pair(frame)
        if left_value is None and right_value is None:
            continue
        saw_any_pair = True
        details["matched_frame_count"] += 1
        details["matched_field_pairs"].append(
            {
                "feedback_type": feedback_type(frame),
                "left": left_value,
                "right": right_value,
            }
        )
        # 只有左右两侧都可解析且同一对象都非零，才能写成 wheel proof。
        if left_value is not None and right_value is not None:
            if abs(left_value) > 0.0 and abs(right_value) > 0.0:
                return True, failure_reasons, warnings, details
            if (abs(left_value) > 0.0) ^ (abs(right_value) > 0.0):
                saw_single_side_nonzero = True

    if not saw_any_pair:
        failure_reasons.append("base_feedback_missing_left_right_wheel_pair")
    elif saw_single_side_nonzero:
        failure_reasons.append("wheel_feedback_single_side_nonzero_only")
    else:
        failure_reasons.append("wheel_feedback_lr_nonzero_not_observed")
    return False, failure_reasons, warnings, details


def extract_ranges(payload: Any) -> list[float | None] | None:
    """raw ranges 可能在根对象，也可能包在 scan proof / latest 结构里。"""
    if isinstance(payload, dict):
        direct_ranges = payload.get("ranges")
        if isinstance(direct_ranges, list):
            return [to_number(item) for item in direct_ranges]
        for value in payload.values():
            ranges = extract_ranges(value)
            if ranges is not None:
                return ranges
    elif isinstance(payload, list):
        return [to_number(item) for item in payload]
    return None


def extract_scan_summary(payload: Any) -> dict[str, float] | None:
    """当没有 raw ranges 时，只接受可比较 summary，不伪造 true。"""
    summary_keys = ("average_abs_delta_m", "max_abs_delta_m", "valid_beam_count")
    if isinstance(payload, dict):
        values = {key: to_number(payload.get(key)) for key in summary_keys}
        if all(values[key] is not None for key in summary_keys):
            return {
                "average_abs_delta_m": float(values["average_abs_delta_m"]),
                "max_abs_delta_m": float(values["max_abs_delta_m"]),
                "valid_beam_count": float(values["valid_beam_count"]),
            }
        for value in payload.values():
            nested = extract_scan_summary(value)
            if nested is not None:
                return nested
    return None


def compare_ranges(before_ranges: list[float | None], after_ranges: list[float | None]) -> dict[str, Any]:
    """逐 beam 做绝对差，直接输出保守统计量，方便 operator 后续复核。"""
    deltas: list[float] = []
    valid_pairs = min(len(before_ranges), len(after_ranges))
    for before_value, after_value in zip(before_ranges[:valid_pairs], after_ranges[:valid_pairs]):
        if before_value is None or after_value is None:
            continue
        deltas.append(abs(after_value - before_value))

    average_delta = sum(deltas) / len(deltas) if deltas else 0.0
    max_delta = max(deltas) if deltas else 0.0
    return {
        "valid_beam_count": len(deltas),
        "average_abs_delta_m": average_delta,
        "max_abs_delta_m": max_delta,
        "paired_beam_window_size": valid_pairs,
    }


def review_scan_delta(before_payload: Any, after_payload: Any) -> tuple[bool, list[str], list[str], dict[str, Any]]:
    """支持 raw ranges 和 summary 两种材料，但两者都必须可比较。"""
    failure_reasons: list[str] = []
    warnings: list[str] = []

    before_ranges = extract_ranges(before_payload)
    after_ranges = extract_ranges(after_payload)
    if before_ranges is not None and after_ranges is not None:
        metrics = compare_ranges(before_ranges, after_ranges)
        proven = (
            metrics["valid_beam_count"] >= SCAN_DELTA_THRESHOLDS["min_valid_beams"]
            and metrics["average_abs_delta_m"] >= SCAN_DELTA_THRESHOLDS["average_abs_delta_min_m"]
            and metrics["max_abs_delta_m"] >= SCAN_DELTA_THRESHOLDS["max_abs_delta_min_m"]
        )
        if not proven:
            failure_reasons.append("scan_delta_below_conservative_threshold")
        metrics["source"] = "raw_ranges"
        return proven, failure_reasons, warnings, metrics

    before_summary = extract_scan_summary(before_payload)
    after_summary = extract_scan_summary(after_payload)
    if before_summary is not None and after_summary is not None:
        # summary 模式要求 after 自带 delta 汇总，before 只用来确认确实是成对材料输入。
        metrics = {
            "valid_beam_count": int(after_summary["valid_beam_count"]),
            "average_abs_delta_m": after_summary["average_abs_delta_m"],
            "max_abs_delta_m": after_summary["max_abs_delta_m"],
            "paired_beam_window_size": int(before_summary["valid_beam_count"]),
            "source": "summary_fields",
        }
        proven = (
            metrics["valid_beam_count"] >= SCAN_DELTA_THRESHOLDS["min_valid_beams"]
            and metrics["average_abs_delta_m"] >= SCAN_DELTA_THRESHOLDS["average_abs_delta_min_m"]
            and metrics["max_abs_delta_m"] >= SCAN_DELTA_THRESHOLDS["max_abs_delta_min_m"]
        )
        if not proven:
            failure_reasons.append("scan_delta_summary_below_conservative_threshold")
        return proven, failure_reasons, warnings, metrics

    failure_reasons.append("scan_delta_missing_comparable_ranges_or_summary")
    return False, failure_reasons, warnings, {"source": "missing"}


def manual_response_is_valid(payload: Any) -> tuple[bool, list[str]]:
    """只校验本轮明确依赖的 readback 入口，避免把别的 proxy 文件误塞进来。"""
    failure_reasons: list[str] = []
    if not isinstance(payload, dict):
        return False, ["manual_response_not_json_object"]

    required_fields = (
        "before_readback",
        "after_readback",
        "evidence_capture_endpoints",
        "motion_evidence_summary",
    )
    for field in required_fields:
        if field not in payload:
            failure_reasons.append(f"manual_response_missing_{field}")

    if not isinstance(payload.get("before_readback"), dict):
        failure_reasons.append("manual_response_before_readback_not_object")
    if not isinstance(payload.get("after_readback"), dict):
        failure_reasons.append("manual_response_after_readback_not_object")
    if not isinstance(payload.get("evidence_capture_endpoints"), list):
        failure_reasons.append("manual_response_evidence_capture_endpoints_not_list")
    if not isinstance(payload.get("motion_evidence_summary"), str):
        failure_reasons.append("manual_response_motion_evidence_summary_not_string")
    return not failure_reasons, failure_reasons


def derive_wheel_feedback_ref(
    manual_response: dict[str, Any],
    manual_response_path: str,
    base_feedback_path: str | None,
) -> str | None:
    """优先引用显式输入文件，其次回退到 manual readback 里已有 artifact 路径。"""
    if base_feedback_path:
        return base_feedback_path
    for path in (
        ("after_readback", "base_feedback_samples_latest", "artifact", "path"),
        ("before_readback", "base_feedback_samples_latest", "artifact", "path"),
    ):
        candidate = nested_get(manual_response, path)
        if isinstance(candidate, str) and candidate:
            return candidate
    # 保底保留 manual 响应路径，方便 operator 追溯本次 review 依据。
    return manual_response_path


def derive_scan_delta_ref(
    manual_response: dict[str, Any],
    scan_before_path: str | None,
    scan_after_path: str | None,
) -> str | None:
    """scan 引用优先指向本次 before/after 文件对，避免引用 unrelated radar proof。"""
    if scan_before_path and scan_after_path:
        return f"{scan_before_path} -> {scan_after_path}"
    for path in (
        ("after_readback", "radar_scan_proof_latest", "artifact", "path"),
        ("before_readback", "radar_scan_proof_latest", "artifact", "path"),
    ):
        candidate = nested_get(manual_response, path)
        if isinstance(candidate, str) and candidate:
            return candidate
    return None


def build_operator_report_claims(
    wheel_proven: bool,
    wheel_ref: str | None,
    scan_proven: bool,
    scan_ref: str | None,
) -> dict[str, Any]:
    """只生成结构化草稿字段，不把结果包装成 HIL pass 或 delivery。"""
    return {
        "wheel_feedback_lr_nonzero_proven": wheel_proven,
        "wheel_feedback_ref": wheel_ref,
        "physical_motion_lidar_delta_proven": scan_proven,
        "scan_delta_ref": scan_ref,
        "real_route_map_proven": False,
        "route_map_ref": None,
        "delivery_success": False,
    }


def build_result(
    manual_response: dict[str, Any],
    manual_response_path: str,
    base_feedback_path: str | None,
    base_feedback_payload: Any | None,
    scan_before_path: str | None,
    scan_before_payload: Any | None,
    scan_after_path: str | None,
    scan_after_payload: Any | None,
) -> dict[str, Any]:
    """统一组装输出，确保所有顶层安全字段始终 fail-closed。"""
    warnings: list[str] = []
    failure_reasons: list[str] = []

    wheel_proven = False
    wheel_details: dict[str, Any] = {"source": "missing"}
    if base_feedback_payload is None:
        failure_reasons.append("base_feedback_file_not_provided")
    else:
        wheel_proven, wheel_failures, wheel_warnings, wheel_details = review_wheel_feedback(base_feedback_payload)
        failure_reasons.extend(wheel_failures)
        warnings.extend(wheel_warnings)

    scan_proven = False
    scan_details: dict[str, Any] = {"source": "missing"}
    if scan_before_payload is None or scan_after_payload is None:
        failure_reasons.append("scan_before_or_after_file_not_provided")
    else:
        scan_proven, scan_failures, scan_warnings, scan_details = review_scan_delta(scan_before_payload, scan_after_payload)
        failure_reasons.extend(scan_failures)
        warnings.extend(scan_warnings)

    review_status = "ready_for_operator_report_material" if wheel_proven and scan_proven else "insufficient_material"
    wheel_ref = derive_wheel_feedback_ref(manual_response, manual_response_path, base_feedback_path)
    scan_ref = derive_scan_delta_ref(manual_response, scan_before_path, scan_after_path)

    # motion summary 只作为来源说明，绝不把 forwarded/path/no-motion 文本当 proof。
    motion_summary = manual_response.get("motion_evidence_summary", "")
    if isinstance(motion_summary, str) and motion_summary:
        warnings.append("manual_response_motion_evidence_summary_treated_as_context_only_not_motion_proof")

    return {
        "schema": SCHEMA,
        "vendor_sources": VENDOR_SOURCES,
        "manual_response_ref": manual_response_path,
        "motion_evidence_summary": motion_summary,
        "review_status": review_status,
        "wheel_feedback_lr_nonzero_proven": wheel_proven,
        "wheel_feedback_ref": wheel_ref,
        "physical_motion_lidar_delta_proven": scan_proven,
        "scan_delta_ref": scan_ref,
        "operator_report_claims": build_operator_report_claims(wheel_proven, wheel_ref, scan_proven, scan_ref),
        "failure_reasons": sorted(set(failure_reasons)),
        "warnings": sorted(set(warnings)),
        "scan_delta_thresholds": SCAN_DELTA_THRESHOLDS,
        "details": {
            "wheel_review": wheel_details,
            "scan_review": scan_details,
            "manual_response_keys": sorted(manual_response.keys()),
            "evidence_capture_endpoint_count": len(manual_response.get("evidence_capture_endpoints", [])),
        },
        # 这些字段是本轮最重要的 fail-closed 护栏，顶层必须全部保持 false。
        "safe_to_control": False,
        "delivery_success": False,
        "hil_pass": False,
        "robot_control_executed": False,
        "sends_motion_commands": False,
    }


def build_invalid_result(manual_response_path: str, failure_reasons: list[str], warnings: list[str]) -> dict[str, Any]:
    """即使输入无效也输出结构化结果，方便 sprint artifact 固化失败原因。"""
    return {
        "schema": SCHEMA,
        "vendor_sources": VENDOR_SOURCES,
        "manual_response_ref": manual_response_path,
        "review_status": "invalid_input",
        "wheel_feedback_lr_nonzero_proven": False,
        "wheel_feedback_ref": None,
        "physical_motion_lidar_delta_proven": False,
        "scan_delta_ref": None,
        "operator_report_claims": build_operator_report_claims(False, None, False, None),
        "failure_reasons": sorted(set(failure_reasons)),
        "warnings": sorted(set(warnings)),
        "scan_delta_thresholds": SCAN_DELTA_THRESHOLDS,
        "details": {},
        "safe_to_control": False,
        "delivery_success": False,
        "hil_pass": False,
        "robot_control_executed": False,
        "sends_motion_commands": False,
    }


def main(argv: list[str] | None = None) -> int:
    """主流程只读文件并写输出，不连接任何机器人接口。"""
    args = parse_args(argv)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = []
    try:
        manual_response = load_json_file(args.manual_response)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = build_invalid_result(args.manual_response, [f"manual_response_load_failed:{exc}"], warnings)
        output_path.write_text(json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        return 0

    valid_manual_response, validation_failures = manual_response_is_valid(manual_response)
    if not valid_manual_response:
        result = build_invalid_result(args.manual_response, validation_failures, warnings)
        output_path.write_text(json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        return 0

    base_feedback_payload = None
    if args.base_feedback:
        try:
            base_feedback_payload = load_json_or_jsonl(args.base_feedback)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            validation_failures.append(f"base_feedback_load_failed:{exc}")

    scan_before_payload = None
    if args.scan_before:
        try:
            scan_before_payload = load_json_file(args.scan_before)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            validation_failures.append(f"scan_before_load_failed:{exc}")

    scan_after_payload = None
    if args.scan_after:
        try:
            scan_after_payload = load_json_file(args.scan_after)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            validation_failures.append(f"scan_after_load_failed:{exc}")

    if validation_failures:
        result = build_invalid_result(args.manual_response, validation_failures, warnings)
        output_path.write_text(json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        return 0

    result = build_result(
        manual_response=manual_response,
        manual_response_path=args.manual_response,
        base_feedback_path=args.base_feedback,
        base_feedback_payload=base_feedback_payload,
        scan_before_path=args.scan_before,
        scan_before_payload=scan_before_payload,
        scan_after_path=args.scan_after,
        scan_after_payload=scan_after_payload,
    )
    output_path.write_text(json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
