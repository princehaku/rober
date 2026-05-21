#!/usr/bin/env python3
"""生成 verified_terminal_result_material_review_decision 的 PC-only 复核决策 gate。"""

from __future__ import annotations

# 设计约束 01：本 CLI 只消费上一轮 intake 的安全摘要，不读取 raw artifact。
# 设计约束 02：review decision 只表示材料复核状态，不能升级成真实 delivery success。
# 设计约束 03：所有 evidence_ref 必须是同一个 safe ref，防止拼接不同现场材料。
# 设计约束 04：terminal_result_type 只允许 delivery/dropoff/cancel，避免自造 success 类型。
# 设计约束 05：raw path、凭证、ROS/control、硬件细节和 reviewer-resolution claim 必须拒绝。
# 设计约束 06：输出 artifact/summary 始终固定 not_proven 和三个 false 控制标志。
# 设计约束 07：blocked/rejected 分支也只写脱敏原因，方便后续 owner 安全交接。
# 设计约束 08：exit code 表达是否 ready，不表达真实任务或真实外部云材料通过。

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ARTIFACT_SCHEMA = "trashbot.verified_terminal_result_material_review_decision.v1"
SUMMARY_SCHEMA = "trashbot.verified_terminal_result_material_review_decision_summary.v1"
SCHEMA_VERSION = 1
CAPABILITY = "verified_terminal_result_material_review_decision"
SOURCE_CAPABILITY = "verified_terminal_result_material_intake"
SOURCE = "software_proof"
STATUS = "not_proven"
EVIDENCE_BOUNDARY = "software_proof_docker_verified_terminal_result_material_review_decision_gate"
SOURCE_BOUNDARY = "software_proof_docker_verified_terminal_result_material_intake_gate"

SUPPORTED_INPUT_SCHEMAS = {
    "trashbot.verified_terminal_result_material_intake.v1",
    "trashbot.verified_terminal_result_material_intake_summary.v1",
    "robot_diagnostics_verified_terminal_result_material_intake_summary",
    "trashbot.robot_diagnostics_verified_terminal_result_material_intake_summary.v1",
}
WRAPPER_KEYS = (
    "verified_terminal_result_material_intake",
    "verified_terminal_result_material_intake_summary",
    "robot_diagnostics_verified_terminal_result_material_intake_summary",
    "summary",
    "artifact",
    "data",
    "payload",
    "status",
)

TERMINAL_RESULT_TYPES = ("delivery", "dropoff", "cancel")
DECISIONS = ("accepted_for_review", "needs_material_backfill", "rejected", "blocked")

SAFE_EVIDENCE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,80}$")
PATH_LIKE_RE = re.compile(r"(^/|[A-Za-z]:\\|\\\\|file://|\\b\\.\\.?/|/dev/|/Users/|/tmp/|/var/|/home/)")
LOCAL_PATH_RE = re.compile(r"(?<![A-Za-z0-9_.-])/(Users|tmp|var|etc|home|run|private|Volumes|ws|dev)\b")

# 字段名出现这些类别时，说明输入已经不是 safe summary，必须 fail closed。
FORBIDDEN_KEY_TERMS = (
    "raw_artifact",
    "raw_artifacts",
    "raw_body",
    "raw_payload",
    "artifact_path",
    "raw_path",
    "local_path",
    "file_path",
    "log_path",
    "screenshot_path",
    "complete_artifact",
    "raw_robot_response",
    "credential",
    "credentials",
    "token",
    "secret",
    "password",
    "authorization",
    "access_key",
    "api_key",
    "cookie",
    "db_url",
    "queue_url",
    "signed_url",
    "control_command",
    "cmd_vel",
    "twist",
    "motor",
    "ros_topic",
    "ros_service",
    "ros_action",
    "hardware_detail",
    "hardware_details",
    "serial_device",
    "uart",
    "wave_rover",
    "esp32",
    "orange_pi",
    "baudrate",
    "voltage",
    "pin",
    "wiring",
    "firmware",
    "reviewer_resolution",
    "review_thread_resolved",
    "github_thread_resolved",
)

UNSAFE_TEXT_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(control_enabled|hil_pass|field_pass|reviewer_resolved)\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\b(dropoff|cancel)\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\b(Bearer\s+|Authorization\s*:|password|private_key|OSS_ACCESS_KEY_SECRET)\b"),
    re.compile(r"(?i)\b(token|secret|access[_-]?key|api[_-]?key|password)\b\s*[:=]"),
    re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://"),
    re.compile(r"(?i)\b(ros2\s+topic|/cmd_vel|/odom|/tf|/trashbot/|rclpy|ros graph)\b"),
    re.compile(r"(?i)\b(WAVE ROVER|ESP32|Orange Pi|UART|baudrate|GPIO|voltage|firmware|serial device)\b"),
    re.compile(r"(?i)\b(PRRT_[A-Za-z0-9]+|reviewer.*resolved|github.*resolved)\b"),
)

NOT_PROVEN_ITEMS = (
    "verified_terminal_delivery_result",
    "real_delivery_success",
    "real_dropoff_completion",
    "real_cancel_completion",
    "real_nav2_fixed_route_run",
    "real_elevator_field_pass",
    "real_phone_browser_or_device",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)


def _utc_now() -> str:
    # UTC 让 Docker-only evidence 在不同本地时区排序稳定。
    return datetime.now(timezone.utc).isoformat()


def _safe_flags() -> dict[str, Any]:
    # 下游可能只读取 summary，所以每层都重复 fail-closed 旗标。
    return {
        "source": SOURCE,
        "status": STATUS,
        "software_proof": True,
        "not_proven": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


def _safe_text(value: Any, default: str = "") -> str:
    # 输出文本裁剪到短摘要，避免把日志、路径或完整 JSON 带到 handoff。
    if value is None:
        text = default
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    text = text.replace("\n", " ").replace("\r", " ")
    return text[:220] or default


def _encoded(value: Any) -> str:
    # 递归扫描 dict/list，防止敏感内容藏在 wrapper 或数组里。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _read_json(path: Path) -> tuple[dict[str, Any], str]:
    # 缺输入或坏 JSON 也生成 blocked artifact，而不是抛出未处理异常。
    try:
        payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "input_missing"
    except json.JSONDecodeError:
        return {}, "input_invalid_json"
    except (OSError, UnicodeDecodeError):
        return {}, "input_read_error"
    if not isinstance(payload, dict):
        return {}, "input_not_object"
    return payload, ""


def _dict(value: Any) -> dict[str, Any]:
    # wrapper 兼容只接受 object，避免把原始文本误当安全 summary 展开。
    return value if isinstance(value, dict) else {}


def _find_source_payload(payload: dict[str, Any]) -> dict[str, Any]:
    # 常见 wrapper/nested 形态只剥一层；找不到就按顶层作为 source。
    for key in WRAPPER_KEYS:
        candidate = _dict(payload.get(key))
        if candidate:
            return candidate
    return payload


def _unsafe_key_paths(value: Any, prefix: str = "") -> list[str]:
    # 字段名命中 raw/control/credential/hardware 直接拒绝，避免值被伪装成 safe note。
    paths: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            key_path = f"{prefix}.{key_text}" if prefix else key_text
            if any(term in key_lower for term in FORBIDDEN_KEY_TERMS):
                paths.append(key_path)
            paths.extend(_unsafe_key_paths(child, key_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(_unsafe_key_paths(child, f"{prefix}[{index}]"))
    return paths


def _unsafe_text_reasons(value: Any) -> list[str]:
    # 只返回类别，不回显命中原文，避免 blocked 输出泄漏敏感片段。
    encoded = _encoded(value)
    reasons: list[str] = []
    if LOCAL_PATH_RE.search(encoded) or any(pattern.search(encoded) for pattern in UNSAFE_TEXT_PATTERNS):
        reasons.append("unsafe_raw_path_credential_ros_control_hardware_resolution_or_success_claim")
    return reasons


def _any_true_key(value: Any, key: str) -> bool:
    # true flag 可能藏在 nested summary 或字符串 note；false 是允许的 fail-closed 旗标。
    if isinstance(value, dict):
        return any((str(k) == key and v is True) or _any_true_key(v, key) for k, v in value.items())
    if isinstance(value, list):
        return any(_any_true_key(item, key) for item in value)
    if isinstance(value, str):
        return bool(re.search(rf"(?i)\b{re.escape(key)}\s*[:=]\s*true\b", value))
    return False


def _safe_evidence_ref(value: Any) -> tuple[str, str]:
    # evidence_ref 是跨材料主键，不能是路径、token 或过长自由文本。
    ref = _safe_text(value)
    if not ref:
        return "", "missing_evidence_ref"
    if not SAFE_EVIDENCE_REF_RE.fullmatch(ref):
        return "", "unsafe_evidence_ref_format"
    if PATH_LIKE_RE.search(ref):
        return "", "unsafe_evidence_ref_path"
    return ref, ""


def _collect_refs(value: Any) -> list[str]:
    # 只收集明确 ref 字段，避免 material_ref 这类安全票据被误判为 evidence_ref。
    refs: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in {"evidence_ref", "safe_evidence_ref"}:
                text = _safe_text(child)
                if text:
                    refs.append(text)
            refs.extend(_collect_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.extend(_collect_refs(child))
    return refs


def _safe_list(value: Any, limit: int = 40) -> list[Any]:
    # 上游可能传 list、tuple、字符串或缺字段；统一限制长度防止复制完整 artifact。
    if isinstance(value, list):
        return value[:limit]
    if isinstance(value, tuple):
        return list(value[:limit])
    if value in (None, ""):
        return []
    return [value]


def _safe_name_list(value: Any, limit: int = 40) -> list[str]:
    # material 对象只保留 name/status/reason，不把原始材料字段带入输出。
    names: list[str] = []
    for item in _safe_list(value, limit):
        if isinstance(item, dict):
            name = _safe_text(item.get("name") or item.get("material") or item.get("material_name"))
            reason = _safe_text(item.get("reason") or item.get("status"))
            names.append(f"{name}:{reason}" if reason and name else name or reason)
        else:
            names.append(_safe_text(item))
    return _dedupe([name for name in names if name])


def _dedupe(values: list[str]) -> list[str]:
    # 保序去重让 summary 稳定，便于 Robot/mobile 做快照对比。
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _default_next_required(decision: str, missing: list[str], rejected: list[str]) -> list[str]:
    # next_required_evidence 只描述补材料动作，不暴露控制命令或本机路径。
    if decision == "accepted_for_review":
        return [
            "Product owner reviews the sanitized material status under the same safe evidence_ref.",
            "Keep not_proven and do not mark delivery/dropoff/cancel as successful without real field proof.",
        ]
    if decision == "needs_material_backfill":
        return [f"Backfill same safe evidence_ref material: {name}" for name in missing[:8]]
    if decision == "rejected":
        return [f"Replace unsafe or rejected material summary: {name}" for name in rejected[:8]] or [
            "Replace unsafe input with sanitized intake artifact or summary.",
        ]
    return ["Provide a supported verified_terminal_result_material_intake artifact or summary with one safe evidence_ref."]


def _owners_for(decision: str, materials: list[str]) -> list[str]:
    # owner_handoff 用固定角色名，后续 sprint closeout 可以稳定分派。
    if decision == "accepted_for_review":
        return ["Product Manager / OKR Owner", "Autonomy Algorithm Engineer"]
    owners: list[str] = []
    tokens = (
        ("task_record", "Robot Platform Engineer"),
        ("delivery", "Robot Platform Engineer"),
        ("dropoff", "Robot Platform Engineer"),
        ("cancel", "Robot Platform Engineer"),
        ("nav2", "Autonomy Algorithm Engineer"),
        ("fixed_route", "Autonomy Algorithm Engineer"),
        ("route", "Autonomy Algorithm Engineer"),
        ("elevator", "Autonomy Algorithm Engineer"),
        ("phone", "User Touchpoint Full-Stack Engineer"),
        ("browser", "User Touchpoint Full-Stack Engineer"),
        ("diagnostics", "User Touchpoint Full-Stack Engineer"),
    )
    for material in materials:
        lower = material.lower()
        owner = "Product Manager / OKR Owner"
        for token, candidate in tokens:
            if token in lower:
                owner = candidate
                break
        if owner not in owners:
            owners.append(owner)
    return owners or ["Product Manager / OKR Owner"]


def _normalize_source(payload: dict[str, Any], read_state: str) -> dict[str, Any]:
    # normalized 是唯一参与决策的数据面，避免输出直接引用输入原对象。
    source = _find_source_payload(payload) if payload else {}
    schema = _safe_text(source.get("schema") or payload.get("schema"))
    source_boundary = _safe_text(source.get("evidence_boundary") or payload.get("evidence_boundary"))
    capability = _safe_text(source.get("capability") or payload.get("capability") or SOURCE_CAPABILITY)
    ref_value = source.get("safe_evidence_ref") or source.get("evidence_ref") or payload.get("safe_evidence_ref") or payload.get("evidence_ref")
    safe_ref, ref_error = _safe_evidence_ref(ref_value)
    refs = _collect_refs(source) + _collect_refs(payload)
    ref_errors: list[str] = []
    for ref in refs:
        checked_ref, error = _safe_evidence_ref(ref)
        if error:
            ref_errors.append(error)
        elif safe_ref and checked_ref != safe_ref:
            ref_errors.append("evidence_ref_mismatch")

    terminal_type = _safe_text(source.get("terminal_result_type") or payload.get("terminal_result_type"))
    accepted = _safe_name_list(source.get("accepted_materials"))
    missing = _safe_name_list(source.get("missing_materials"))
    rejected = _safe_name_list(source.get("rejected_materials")) + _safe_name_list(source.get("blocked_materials"))
    next_required = _safe_name_list(source.get("next_required_evidence")) or _safe_name_list(source.get("required_materials"))
    source_status = _safe_text(
        source.get("intake_status")
        or source.get("verified_terminal_result_material_intake")
        or source.get("status")
        or payload.get("status")
    )

    unsafe_reasons = []
    if _unsafe_key_paths(source) or _unsafe_key_paths(payload):
        unsafe_reasons.append("forbidden_raw_control_credential_ros_hardware_or_resolution_fields")
    unsafe_reasons.extend(_unsafe_text_reasons(source))
    unsafe_reasons.extend(_unsafe_text_reasons(payload))
    for key in ("delivery_success", "primary_actions_enabled", "safe_to_control", "control_enabled", "hil_pass"):
        if _any_true_key(source, key) or _any_true_key(payload, key):
            unsafe_reasons.append(f"{key}_true_overclaim")

    return {
        "read_state": read_state,
        "source": source,
        "schema": schema,
        "source_boundary": source_boundary,
        "source_capability": capability,
        "source_status": source_status,
        "safe_evidence_ref": safe_ref,
        "ref_errors": _dedupe(ref_errors + ([ref_error] if ref_error else [])),
        "same_evidence_ref_required": bool(source.get("same_evidence_ref_required", payload.get("same_evidence_ref_required", True))),
        "terminal_result_type": terminal_type,
        "accepted_materials": accepted,
        "missing_materials": missing,
        "rejected_materials": _dedupe(rejected),
        "next_required_evidence": next_required,
        "unsafe_reasons": _dedupe(unsafe_reasons),
    }


def _schema_supported(normalized: dict[str, Any]) -> bool:
    # schema 或 Robot safe alias 都要匹配，source boundary 也要停留在 intake gate。
    schema = normalized["schema"]
    boundary = normalized["source_boundary"]
    if schema in SUPPORTED_INPUT_SCHEMAS and boundary in {"", SOURCE_BOUNDARY}:
        return True
    if normalized["source_capability"] == SOURCE_CAPABILITY and boundary == SOURCE_BOUNDARY:
        return True
    return False


def _decision(normalized: dict[str, Any]) -> tuple[str, list[str]]:
    # 决策顺序：输入契约 -> 安全 -> evidence_ref -> terminal type -> material 状态。
    reasons: list[str] = []
    if normalized["read_state"]:
        return "blocked", [normalized["read_state"]]
    if not _schema_supported(normalized):
        return "blocked", ["unsupported_intake_schema_or_boundary"]
    if normalized["unsafe_reasons"]:
        return "rejected", normalized["unsafe_reasons"]
    if normalized["ref_errors"] or not normalized["safe_evidence_ref"] or not normalized["same_evidence_ref_required"]:
        reasons.extend(normalized["ref_errors"] or ["missing_or_weak_same_evidence_ref"])
        return "blocked", _dedupe(reasons)
    if normalized["terminal_result_type"] not in TERMINAL_RESULT_TYPES:
        return "blocked", ["unsupported_terminal_result_type"]
    if normalized["rejected_materials"]:
        return "rejected", ["source_intake_contains_rejected_materials"]
    if normalized["missing_materials"]:
        return "needs_material_backfill", ["source_intake_missing_required_materials"]
    if normalized["accepted_materials"]:
        return "accepted_for_review", ["source_intake_safe_material_shape_ready_for_manual_review"]
    return "needs_material_backfill", ["source_intake_has_no_accepted_materials"]


def _material_status_summary(normalized: dict[str, Any], decision: str, reasons: list[str]) -> dict[str, Any]:
    # summary 只保留材料名/原因，不复制 material body、raw refs 或本机路径。
    return {
        "source_intake_status": normalized["source_status"],
        "accepted_materials": normalized["accepted_materials"],
        "missing_materials": normalized["missing_materials"],
        "rejected_materials": normalized["rejected_materials"],
        "accepted_count": len(normalized["accepted_materials"]),
        "missing_count": len(normalized["missing_materials"]),
        "rejected_count": len(normalized["rejected_materials"]),
        "blocked_reasons": reasons if decision == "blocked" else [],
    }


def _safe_copy(decision: str, normalized: dict[str, Any]) -> str:
    # safe_copy 给 mobile/Robot 复制用，只包含短字段和固定边界。
    return (
        f"{CAPABILITY}: review_decision={decision}; "
        f"evidence_ref={normalized['safe_evidence_ref'] or 'blocked'}; "
        f"terminal_result_type={normalized['terminal_result_type'] or 'blocked'}; "
        f"evidence_boundary={EVIDENCE_BOUNDARY}; not_proven; "
        "delivery_success=false; primary_actions_enabled=false; safe_to_control=false."
    )


def build_verified_terminal_result_material_review_decision(input_path: Path) -> tuple[dict[str, Any], dict[str, Any], int]:
    """构建 review decision artifact 与 summary；ready 也不是 delivery success。"""
    payload, read_state = _read_json(input_path)
    normalized = _normalize_source(payload, read_state)
    decision, reasons = _decision(normalized)
    missing = normalized["missing_materials"] or ([] if decision == "accepted_for_review" else ["supported_safe_intake_summary"])
    rejected = normalized["rejected_materials"] + (reasons if decision == "rejected" else [])
    # 缺材料时必须逐项告诉 owner 回填什么，不能沿用 source 的泛化人工复核文案。
    if decision in {"needs_material_backfill", "rejected", "blocked"}:
        next_required = _default_next_required(decision, missing, rejected)
    else:
        next_required = normalized["next_required_evidence"] or _default_next_required(decision, missing, rejected)
    owners = _owners_for(decision, missing or rejected or normalized["accepted_materials"])
    material_summary = _material_status_summary(normalized, decision, reasons)
    generated_at = _utc_now()
    common = {
        **_safe_flags(),
        "capability": CAPABILITY,
        "source_capability": SOURCE_CAPABILITY,
        "source_schema": normalized["schema"],
        "source_evidence_boundary": normalized["source_boundary"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "review_decision": decision,
        "allowed_review_decisions": list(DECISIONS),
        "safe_evidence_ref": normalized["safe_evidence_ref"],
        "same_evidence_ref_required": True,
        "terminal_result_type": normalized["terminal_result_type"],
        "allowed_terminal_result_types": list(TERMINAL_RESULT_TYPES),
        "decision_reasons": reasons,
        "material_status_summary": material_summary,
        "next_required_evidence": next_required,
        "owner_handoff": owners,
        "safe_copy": _safe_copy(decision, normalized),
        "fail_closed_flags": {
            "software_proof": True,
            "not_proven": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
        },
        "safety_markers": [
            "software_proof",
            "not_proven",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
        ],
        "not_proven_items": list(NOT_PROVEN_ITEMS),
        "boundary_note": (
            "software_proof; not_proven; delivery_success=false; "
            "primary_actions_enabled=false; safe_to_control=false"
        ),
    }
    artifact = {
        "schema": ARTIFACT_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "verified_terminal_result_material_review_decision": decision,
        **common,
        "source_intake": {
            "schema_supported": _schema_supported(normalized),
            "read_state": read_state,
            "source_status": normalized["source_status"],
            "unsafe_reasons": normalized["unsafe_reasons"],
            "ref_errors": normalized["ref_errors"],
        },
    }
    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "summary_only": True,
        "safe_to_render_on_phone": True,
        "summary_alias": "robot_diagnostics_verified_terminal_result_material_review_decision_summary",
        **common,
    }
    return artifact, summary, 0 if decision == "accepted_for_review" else 2


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    # output-dir 由 CLI 创建，便于 sprint evidence bundle 一次落盘。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只接受上一轮 intake 输入，不新增控制、ACK、review mutation 或 raw artifact 路径。
    parser = argparse.ArgumentParser(
        description=(
            "Build trashbot.verified_terminal_result_material_review_decision.v1 software_proof artifact "
            "from --input; keeps not_proven, delivery_success=false, primary_actions_enabled=false, "
            "safe_to_control=false."
        )
    )
    parser.add_argument("--input", type=Path, required=True, help="prior intake artifact, summary, or Robot safe alias JSON")
    parser.add_argument("--output-dir", type=Path, required=True, help="directory for sanitized review decision JSON files")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_verified_terminal_result_material_review_decision(args.input)
    _write_json(args.output_dir / "verified_terminal_result_material_review_decision.json", artifact)
    _write_json(args.output_dir / "verified_terminal_result_material_review_decision_summary.json", summary)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
