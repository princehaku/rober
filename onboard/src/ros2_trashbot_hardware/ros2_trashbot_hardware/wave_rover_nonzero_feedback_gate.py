"""WAVE ROVER nonzero feedback HIL gate。

Vendor 来源：
- docs/vendor/VENDOR_INDEX.md
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h
- docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py
- docs/hardware/wave_rover_json_bridge.md

本模块只做离线 software proof：
- 复用 wave_rover_feedback.py 的 T=1001 parser，不重复猜字段；
- 只从 mock JSON 或 feedback log 生成 fail-closed 摘要；
- 固定 source=software_proof、hil_pass=false、safe_to_control=false。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ros2_trashbot_hardware.wave_rover_feedback import parse_feedback_line


SCHEMA = "trashbot.wave_rover_nonzero_feedback_hil_gate.v1"
EVIDENCE_BOUNDARY = "software_proof_o1_wave_rover_nonzero_feedback_hil_gate_only"
PROOF_SOURCE = "software_proof"
VENDOR_SOURCES = [
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/hardware/wave_rover_json_bridge.md",
]
DEFAULT_FEEDBACK_SAMPLE = {"T": 1001, "L": 61, "R": 61, "r": 0.3, "p": 0.1, "y": 0.0, "v": 11.7}
BASE_MISSING_HIL_ARTIFACTS = [
    "real_wave_rover_feedback_log_same_run",
    "same_run_motion_command_record",
    "same_run_operator_or_external_motion_observation",
    "same_run_hil_acceptance_record",
]


def _json_line(payload: dict[str, Any]) -> str:
    """把 mock 样本编码成 vendor 同款一行 JSON。"""
    # vendor base_ctrl.py 的事实是“一行一个 JSON 帧”，离线样本也保持这个边界。
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=True) + "\n"


def _extract_candidate(line: str) -> str:
    """从原始 log 行或 wrapper JSON 中提取可交给 parser 的候选帧。"""
    stripped = line.strip()
    if not stripped:
        return ""
    try:
        decoded = json.loads(stripped)
    except json.JSONDecodeError:
        # 非 JSON 行直接原样交给 parser，统一走 fail-closed。
        return stripped

    if isinstance(decoded, dict) and "T" in decoded:
        return _json_line(decoded)

    if isinstance(decoded, dict):
        for key in ("feedback", "payload", "message", "vendor_frame"):
            candidate = decoded.get(key)
            if isinstance(candidate, dict):
                return _json_line(candidate)
            if isinstance(candidate, str):
                return candidate
    return stripped


def _direction_bucket(left_speed: float, right_speed: float) -> str:
    """把 L/R 符号模式压缩成保守摘要。"""
    # 这里仅总结符号组合，不把它命名成“前进/后退/左转/右转”之类实车方向事实。
    if left_speed > 0 and right_speed > 0:
        return "both_positive"
    if left_speed < 0 and right_speed < 0:
        return "both_negative"
    if left_speed > 0 and right_speed < 0:
        return "left_positive_right_negative"
    if left_speed < 0 and right_speed > 0:
        return "left_negative_right_positive"
    if left_speed == 0 and right_speed == 0:
        return "both_zero"
    if left_speed == 0:
        return "left_zero_right_nonzero"
    return "left_nonzero_right_zero"


def _empty_direction_summary() -> dict[str, int]:
    return {
        "both_positive": 0,
        "both_negative": 0,
        "left_positive_right_negative": 0,
        "left_negative_right_positive": 0,
        "left_zero_right_nonzero": 0,
        "left_nonzero_right_zero": 0,
        "both_zero": 0,
    }


def _evaluate_candidates(candidates: list[str]) -> dict[str, Any]:
    """评估一组候选反馈帧并输出 fail-closed gate 摘要。"""
    direction_summary = _empty_direction_summary()
    parsed_frames: list[dict[str, Any]] = []
    ignored_non_t1001_count = 0
    invalid_feedback_count = 0

    for candidate in candidates:
        stripped = candidate.strip()
        if not stripped:
            continue

        parsed = parse_feedback_line(candidate)
        if parsed is None:
            try:
                decoded = json.loads(stripped)
            except json.JSONDecodeError:
                invalid_feedback_count += 1
                continue

            # 非 T=1001 不是“坏硬件事实”，只是与本 gate 无关，因此按 ignored 统计。
            if isinstance(decoded, dict) and decoded.get("T") != 1001:
                ignored_non_t1001_count += 1
            else:
                invalid_feedback_count += 1
            continue

        parsed_frames.append(parsed)
        direction_summary[_direction_bucket(parsed["left_speed"], parsed["right_speed"])] += 1

    left_nonzero_count = 0
    right_nonzero_count = 0
    paired_nonzero_count = 0
    latest_nonzero_pair: dict[str, Any] | None = None
    for index, frame in enumerate(parsed_frames):
        left_speed = frame["left_speed"]
        right_speed = frame["right_speed"]
        if left_speed != 0:
            left_nonzero_count += 1
        if right_speed != 0:
            right_nonzero_count += 1
        if left_speed != 0 and right_speed != 0:
            paired_nonzero_count += 1
            latest_nonzero_pair = {
                "frame_index": index,
                "left_speed": left_speed,
                "right_speed": right_speed,
                "sign_pattern": _direction_bucket(left_speed, right_speed),
                "vendor_frame": frame["vendor_frame"],
            }

    valid_t1001_observed = bool(parsed_frames)
    direction_summary_available = paired_nonzero_count > 0
    missing_hil_artifacts = list(BASE_MISSING_HIL_ARTIFACTS)
    blockers: list[str] = []
    status = "software_proof_nonzero_lr_observed"

    # 任何 invalid feedback line 都必须压顶层失败，不能被其他 nonzero 样本“冲掉”。
    if invalid_feedback_count > 0:
        status = "blocked_invalid_feedback"
        blockers.append("invalid_feedback_lines_present")
        missing_hil_artifacts.insert(0, "same_run_invalid_feedback_cleanup")

    # 在没有 invalid line 时，再看是否存在合法 T=1001 与同帧 nonzero L/R。
    if not valid_t1001_observed:
        if invalid_feedback_count == 0:
            status = "blocked_missing_valid_t1001"
        blockers.append("no_valid_vendor_t1001_frame")
        missing_hil_artifacts.insert(0, "real_vendor_t1001_capture")
    elif paired_nonzero_count == 0:
        if invalid_feedback_count == 0:
            # 读到合法 T=1001 但 L/R 没有同帧同时非零时，仍然不得进入控制或 HIL pass 口径。
            status = "blocked_all_zero_or_partial_zero_lr"
        blockers.append("no_same_frame_nonzero_lr_pair")
        missing_hil_artifacts.insert(0, "same_run_nonzero_lr_frame")

    if not direction_summary_available:
        blockers.append("direction_summary_not_available")
        missing_hil_artifacts.insert(0, "same_run_direction_confirmed_nonzero_samples")

    blockers.extend(
        [
            "software_proof_cannot_claim_real_hil_pass",
            "software_proof_cannot_claim_safe_to_control",
        ]
    )

    return {
        "schema": SCHEMA,
        "source": PROOF_SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": status,
        "hil_pass": False,
        "safe_to_control": False,
        "vendor_sources": list(VENDOR_SOURCES),
        "gate": {
            "valid_t1001_observed": valid_t1001_observed,
            "left_nonzero_observed": left_nonzero_count > 0,
            "right_nonzero_observed": right_nonzero_count > 0,
            "paired_nonzero_observed": paired_nonzero_count > 0,
            "direction_summary_available": direction_summary_available,
            "ready_for_real_hil_review": False,
        },
        "counts": {
            "candidate_count": len(candidates),
            "parsed_t1001_count": len(parsed_frames),
            "ignored_non_t1001_count": ignored_non_t1001_count,
            "invalid_feedback_count": invalid_feedback_count,
            "left_nonzero_count": left_nonzero_count,
            "right_nonzero_count": right_nonzero_count,
            "paired_nonzero_count": paired_nonzero_count,
        },
        "direction_summary": direction_summary,
        "latest_nonzero_pair": latest_nonzero_pair,
        "missing_hil_artifacts": missing_hil_artifacts,
        "blockers": blockers,
    }


def build_nonzero_feedback_gate_summary(
    feedback_log: str | Path | None = None,
    feedback_sample_json: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
    """构建 WAVE ROVER nonzero feedback 的离线 HIL gate 摘要。"""
    candidates: list[str] = []

    # 默认 mock 只是 parser/gate 合同自测，不能冒充实机反馈材料。
    if feedback_log is None and feedback_sample_json is None:
        feedback_sample_json = dict(DEFAULT_FEEDBACK_SAMPLE)

    if feedback_log is not None:
        for raw_line in Path(feedback_log).read_text(encoding="utf-8").splitlines():
            candidate = _extract_candidate(raw_line)
            if candidate:
                candidates.append(candidate)

    if feedback_sample_json is not None:
        if isinstance(feedback_sample_json, dict):
            candidates.append(_json_line(feedback_sample_json))
        else:
            candidates.append(_extract_candidate(str(feedback_sample_json)))

    summary = _evaluate_candidates(candidates)
    summary["input"] = {
        "feedback_log": str(feedback_log) if feedback_log is not None else None,
        "feedback_sample_json_provided": feedback_sample_json is not None,
    }
    return summary


def _parse_feedback_sample_json(value: str | None) -> dict[str, Any] | str | None:
    if value is None:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return value
    return parsed


def main(argv: list[str] | None = None) -> int:
    """CLI 入口：只输出 software proof JSON，不触碰 UART。"""
    parser = argparse.ArgumentParser(description="Summarize WAVE ROVER T=1001 nonzero feedback gate.")
    parser.add_argument("feedback_log", nargs="?")
    parser.add_argument("--feedback-sample-json")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    summary = build_nonzero_feedback_gate_summary(
        feedback_log=args.feedback_log,
        feedback_sample_json=_parse_feedback_sample_json(args.feedback_sample_json),
    )
    payload = json.dumps(summary, indent=2, sort_keys=True) + "\n"

    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
        print(args.output)
    else:
        print(payload, end="")

    if summary["status"] == "software_proof_nonzero_lr_observed":
        return 0
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
