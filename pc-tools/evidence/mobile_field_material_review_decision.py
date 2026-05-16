#!/usr/bin/env python3
"""生成 mobile field material review decision artifact。

该 CLI 只读取上一轮 mobile_field_material_intake artifact/summary，把 intake
状态整理成 owner handoff、next-required-evidence 和 fail-closed 复核决策。
它不访问 ROS graph、Nav2 runtime、serial/UART、真实手机、真实电梯、外部云、
OSS/CDN、DB/queue 或 4G。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# schema 名称是 pc-tools、Robot diagnostics、mobile/web 和 Product closeout 的稳定锚点。
REVIEW_SCHEMA = "trashbot.mobile_field_material_review_decision.v1"
REVIEW_SUMMARY_SCHEMA = "trashbot.mobile_field_material_review_decision_summary.v1"
REVIEW_SCHEMA_VERSION = 1
REVIEW_BOUNDARY = "software_proof_docker_mobile_field_material_review_decision_gate"
SOURCE = "software_proof"

# 只接上一轮 intake artifact 或 summary；其他 JSON 不能被误当作现场材料。
INTAKE_SCHEMA = "trashbot.mobile_field_material_intake.v1"
INTAKE_SUMMARY_SCHEMA = "trashbot.mobile_field_material_intake_summary.v1"
INTAKE_BOUNDARY = "software_proof_docker_mobile_field_material_intake_gate"
READY_INTAKE_VERDICTS = {
    "ready_for_mobile_field_material_review_not_proven",
    "validated_mobile_field_material_intake_not_proven",
}

# 决策枚举按阻塞优先级排列；ready 也保持 not_proven，不放行控制动作。
READY_DECISION = "ready_for_owner_handoff_not_proven"
DECISION_ORDER = (
    "blocked_invalid_intake",
    "blocked_missing_real_phone_or_pwa_observation",
    "blocked_missing_route_elevator_field_materials",
    "blocked_missing_nav2_or_fixed_route_runtime_log",
    "blocked_missing_same_evidence_ref_task_record_or_completion_signal",
    "blocked_missing_dropoff_or_cancel_completion",
    READY_DECISION,
)

# intake 的 material_statuses name 到复核决策和 owner handoff 的白名单映射。
MATERIAL_DECISION_MAP = {
    "device_pwa_observation": (
        "blocked_missing_real_phone_or_pwa_observation",
        "Full-stack",
        "Capture real phone/browser or PWA observation for the same evidence_ref.",
    ),
    "route_elevator_field_materials": (
        "blocked_missing_route_elevator_field_materials",
        "Product closeout",
        "Collect route/elevator field materials before Product closeout.",
    ),
    "nav2_fixed_route_runtime_log": (
        "blocked_missing_nav2_or_fixed_route_runtime_log",
        "Autonomy",
        "Provide Nav2 or fixed-route runtime log under the same evidence_ref.",
    ),
    "task_record": (
        "blocked_missing_same_evidence_ref_task_record_or_completion_signal",
        "Robot",
        "Provide task_record with the same evidence_ref.",
    ),
    "completion_signal": (
        "blocked_missing_same_evidence_ref_task_record_or_completion_signal",
        "Robot",
        "Provide completion_signal with the same evidence_ref.",
    ),
    "dropoff_cancel_material_status": (
        "blocked_missing_dropoff_or_cancel_completion",
        "Robot",
        "Provide dropoff or cancel completion material without success claims.",
    ),
}

# not_proven 明确列出不能由本 gate 证明的能力，供 mobile/support 防误读。
NOT_PROVEN = (
    "real_phone_device_or_browser",
    "real_pwa_install_prompt_user_choice",
    "real_route_elevator_field_pass",
    "real_nav2_fixed_route_run",
    "real_fixed_route_completion",
    "real_task_record_acceptance",
    "real_dropoff_completion",
    "real_cancel_completion",
    "delivery_success",
    "real_hil_pass",
    "real_wave_rover_or_uart_feedback",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# 输出与检测都禁止这些敏感或容易越界的片段进入 phone-safe review 面。
FORBIDDEN_COPY = (
    "Authorization",
    "OSS_ACCESS_KEY",
    "OSS_SECRET",
    "access_key",
    "secret",
    "token",
    "password",
    "postgres://",
    "postgresql://",
    "mysql://",
    "redis://",
    "amqp://",
    "mongodb://",
    "/cmd_vel",
    "/dev/ttyUSB",
    "/dev/ttyACM",
    "serial",
    "UART",
    "baudrate",
    "baud_rate",
    "WAVE ROVER",
    "Traceback",
    "checksum",
    "complete artifact",
    "raw robot response",
)

# placeholder 会让同一证据链看似完整但不可复核，因此直接阻断。
PLACEHOLDER_PATTERNS = (
    re.compile(r"(?i)<[^>]*(todo|placeholder|same_evidence_ref|fill|tbd)[^>]*>"),
    re.compile(r"(?i)\b(todo|tbd|placeholder|replace_me|sample_only|example_only)\b"),
)

# 成功文案或 true 旗标会把 software proof 误读为真实送达，必须 fail closed。
SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\broute/elevator\s+field\s+pass(ed)?\b"),
    re.compile(r"(?i)\bnav2\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bfixed[-_ ]route\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bdropoff\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bcancel\s+(completed|complete|success|succeeded)\b"),
    re.compile(r"(?i)\bhil_pass\s*[:=]\s*true\b"),
)

# 先脱敏再输出，避免 operator note 或 summary 污染下游 mobile copy。
SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\bAuthorization\s*:\s*[^,\s]+"), "Authorization: [REDACTED]"),
    (re.compile(r"(?i)\bOSS_[A-Z_]*(ACCESS|SECRET)[A-Z_]*\b\s*[:=]\s*[^,\s]+"), "OSS_KEY=[REDACTED]"),
    (re.compile(r"(?i)\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\b(db|database|queue)[_-]?url\b\s*[:=]\s*[^,\s]+"), r"\1_url=[REDACTED]"),
    (re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://[^,\s]+"), "[REDACTED_URL]"),
    (re.compile(r"/cmd_vel\b"), "[REDACTED_ROS_TOPIC]"),
    (re.compile(r"/dev/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*"), "/dev/[REDACTED_DEVICE]"),
    (re.compile(r"(?i)\b(baud|baudrate|baud_rate)\b\s*[:=]\s*\d+"), r"\1=[REDACTED_RATE]"),
    (re.compile(r"(?i)\bserial\b"), "[REDACTED_TRANSPORT]"),
    (re.compile(r"(?i)\bUART\b"), "[REDACTED_TRANSPORT]"),
    (re.compile(r"(?i)\bWAVE ROVER\b"), "[REDACTED_ROBOT_BASE]"),
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)complete artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)raw robot response"), "[REDACTED_RAW_RESPONSE]"),
)


def _utc_now() -> str:
    # UTC 让不同 PC/Docker 主机生成的复核结果可按字符串排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 自由文本统一脱敏；新增字段也能通过递归输出层复用这套规则。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref 若是本机路径，只保留 basename，避免 phone/export 泄漏目录结构。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # artifact 写盘前递归脱敏，保证嵌套 summary 不绕过过滤。
    if isinstance(value, dict):
        return {str(_safe_text(key)): _safe_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return [_safe_value(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value


def _encoded(value: Any) -> str:
    # 安全扫描覆盖 key/value；不可编码对象退回脱敏文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺文件、坏 JSON、非 object 都转成 blocked artifact，不抛未处理异常。
    if not path:
        return {}, "intake_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "intake_missing"
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}, "intake_read_error"
    if not isinstance(payload, dict):
        return {}, "intake_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 嵌套 summary 缺失时按空对象处理，避免复制 raw artifact 细节。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any, limit: int = 30) -> list[str]:
    # intake 旧字段可能是字符串、缺失或 list；统一成有限白名单文本。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _has_forbidden_copy(value: Any) -> bool:
    # 检查键和值，确保 review 输出不会携带控制、凭证、硬件或 raw artifact 细节。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _has_placeholder(value: Any) -> bool:
    # placeholder 代表材料不可复核，不能进入 owner handoff ready。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in PLACEHOLDER_PATTERNS)


def _any_true_key(value: Any, key: str) -> bool:
    # true 旗标可能藏在 nested summary 或字符串 note 中，递归阻断。
    if isinstance(value, dict):
        return any((k == key and v is True) or _any_true_key(v, key) for k, v in value.items())
    if isinstance(value, list):
        return any(_any_true_key(item, key) for item in value)
    if isinstance(value, str):
        return bool(re.search(rf"(?i)\b{re.escape(key)}\s*[:=]\s*true\b", value))
    return False


def _has_success_claim(value: Any) -> bool:
    # 文案和 bool 都检查，因为现场手写摘要常把成功写在 notes 中。
    encoded = _encoded(value)
    if any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS):
        return True
    return any(
        _any_true_key(value, key)
        for key in (
            "delivery_success",
            "primary_actions_enabled",
            "real_device_observed",
            "pwa_install_prompt_observed",
            "route_elevator_field_pass",
            "nav2_fixed_route_completed",
            "dropoff_completion",
            "cancel_completion",
            "hil_pass",
        )
    )


def _source_payload(payload: dict[str, Any]) -> dict[str, Any]:
    # full intake artifact 与 summary 均支持；full artifact 内没有 raw material，直接取顶层即可。
    nested = _dict(payload, "mobile_field_material_intake_summary")
    return nested or payload


def _material_statuses(source: dict[str, Any]) -> list[dict[str, Any]]:
    # 只保留白名单字段；不复制上游可能新增的 raw operator note。
    statuses = source.get("material_statuses")
    if not isinstance(statuses, list):
        return []
    safe_statuses: list[dict[str, Any]] = []
    for item in statuses:
        if not isinstance(item, dict):
            continue
        name = _safe_text(item.get("name")).strip()
        if name not in MATERIAL_DECISION_MAP:
            continue
        safe_statuses.append(
            {
                "name": name,
                "status": _safe_text(item.get("status", "missing_or_unreadable")),
                "present": bool(item.get("present", False)),
                "evidence_ref": _safe_ref(item.get("evidence_ref")),
                "same_evidence_ref_required": bool(item.get("same_evidence_ref_required", True)),
                "missing_or_blocked": _safe_list(item.get("missing_or_blocked"), limit=10),
            }
        )
    return safe_statuses


def _normalize_intake(payload: dict[str, Any], expected_ref: str) -> dict[str, Any]:
    # 下游决策只看 contract 字段、材料状态和固定 fail-closed 旗标。
    source = _source_payload(payload)
    schema = _safe_text(source.get("schema", payload.get("schema", "")))
    boundary = _safe_text(source.get("evidence_boundary", payload.get("evidence_boundary", "")))
    evidence_ref = _safe_ref(expected_ref or source.get("evidence_ref") or payload.get("evidence_ref"))
    intake_verdict = _safe_text(source.get("intake_verdict") or source.get("status") or payload.get("intake_verdict", "missing"))
    same_ref_status = _safe_text(source.get("same_evidence_ref_status", payload.get("same_evidence_ref_status", "")))
    return {
        "schema": schema,
        "evidence_boundary": boundary,
        "evidence_ref": evidence_ref,
        "source_evidence_ref": _safe_ref(source.get("evidence_ref") or payload.get("evidence_ref")),
        "same_evidence_ref_required": bool(source.get("same_evidence_ref_required", True)),
        "same_evidence_ref_status": same_ref_status,
        "intake_verdict": intake_verdict,
        "material_statuses": _material_statuses(source),
        "missing_or_blocked": _safe_list(source.get("missing_or_blocked") or payload.get("missing_or_blocked"), limit=40),
        "not_proven": _safe_list(source.get("not_proven") or payload.get("not_proven"), limit=30),
        "unsafe_copy_detected": _has_forbidden_copy(source) or _has_forbidden_copy(payload),
        "placeholder_detected": _has_placeholder(source) or _has_placeholder(payload),
        "success_claim_detected": _has_success_claim(source) or _has_success_claim(payload),
    }


def _schema_status(load_issue: str, normalized: dict[str, Any]) -> str:
    # schema/boundary 是防止任意 JSON 被当成 review source 的第一道围栏。
    if load_issue:
        return "not_loaded"
    if normalized["schema"] in {INTAKE_SCHEMA, INTAKE_SUMMARY_SCHEMA} and normalized["evidence_boundary"] == INTAKE_BOUNDARY:
        return "supported"
    return "unsupported"


def _blocked_materials(normalized: dict[str, Any]) -> list[dict[str, Any]]:
    # present_not_proven 是唯一可进入 handoff 的材料状态；其它状态都保留原原因。
    blocked: list[dict[str, Any]] = []
    seen = {item["name"] for item in normalized["material_statuses"]}
    for name, (_decision, owner, reason) in MATERIAL_DECISION_MAP.items():
        found = next((item for item in normalized["material_statuses"] if item["name"] == name), None)
        if not found:
            blocked.append({"name": name, "status": "missing", "owner": owner, "reason": reason})
            continue
        if found.get("status") != "present_not_proven":
            blocked.append(
                {
                    "name": name,
                    "status": found.get("status", "blocked"),
                    "owner": owner,
                    "reason": ", ".join(found.get("missing_or_blocked", [])) or reason,
                }
            )
    if not seen:
        # 缺 material_statuses 时给出紧凑原因，方便 operator 知道要重跑 intake。
        blocked.append({"name": "material_statuses", "status": "missing", "owner": "Product closeout", "reason": "rerun intake"})
    return blocked


def _review_decision(
    load_issue: str,
    schema_status: str,
    normalized: dict[str, Any],
    expected_ref: str,
) -> str:
    # 决策优先级：输入有效性/安全 -> same evidence_ref -> 具体材料缺口 -> ready。
    if load_issue or schema_status != "supported":
        return "blocked_invalid_intake"
    if normalized["placeholder_detected"] or normalized["unsafe_copy_detected"] or normalized["success_claim_detected"]:
        return "blocked_invalid_intake"
    if not normalized["evidence_ref"] or normalized["evidence_ref"] == "<same_evidence_ref>":
        return "blocked_invalid_intake"
    if expected_ref and normalized["source_evidence_ref"] and normalized["source_evidence_ref"] != normalized["evidence_ref"]:
        return "blocked_invalid_intake"
    if normalized["same_evidence_ref_status"] != "matched_same_evidence_ref":
        return "blocked_invalid_intake"
    for blocked in _blocked_materials(normalized):
        if blocked["name"] in MATERIAL_DECISION_MAP:
            return MATERIAL_DECISION_MAP[blocked["name"]][0]
    if normalized["intake_verdict"] in READY_INTAKE_VERDICTS:
        return READY_DECISION
    return "blocked_invalid_intake"


def _owner_handoff(decision: str) -> str:
    # owner handoff 固定四类，便于 sprint closeout 和 mobile 面板直接展示。
    if decision == "blocked_missing_real_phone_or_pwa_observation":
        return "Full-stack"
    if decision in {
        "blocked_missing_same_evidence_ref_task_record_or_completion_signal",
        "blocked_missing_dropoff_or_cancel_completion",
    }:
        return "Robot"
    if decision == "blocked_missing_nav2_or_fixed_route_runtime_log":
        return "Autonomy"
    return "Product closeout"


def _next_required_evidence(decision: str, evidence_ref: str, blocked: list[dict[str, Any]]) -> list[str]:
    # next-required-evidence 只描述补证据，不给机器人控制命令。
    ref = evidence_ref or "<same_evidence_ref>"
    if decision == READY_DECISION:
        return [
            f"Product closeout reviews mobile_field_material_review_decision for evidence_ref={ref}.",
            "Keep delivery_success=false and primary_actions_enabled=false until real field completion exists.",
        ]
    if decision == "blocked_invalid_intake":
        return [
            f"Regenerate mobile_field_material_intake under evidence_ref={ref}.",
            "Use supported schema/boundary, remove placeholder, unsafe copy, mismatch, and success wording.",
        ]
    if blocked:
        names = ", ".join(item["name"] for item in blocked[:4])
        return [
            f"Collect or repair {names} for evidence_ref={ref}.",
            "Rerun mobile_field_material_intake.py, then rerun mobile_field_material_review_decision.py.",
        ]
    return [f"Collect missing mobile field materials for evidence_ref={ref}."]


def _review_summary(
    decision: str,
    evidence_ref: str,
    owner: str,
    blocked: list[dict[str, Any]],
    next_evidence: list[str],
) -> dict[str, Any]:
    # summary 是 Robot diagnostics/mobile 只读消费面，字段短且白名单。
    return {
        "schema": REVIEW_SUMMARY_SCHEMA,
        "schema_version": REVIEW_SCHEMA_VERSION,
        "source": SOURCE,
        "evidence_boundary": REVIEW_BOUNDARY,
        "status": decision,
        "review_decision": decision,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "owner_handoff": owner,
        "owner handoff": owner,
        "blocked_materials": blocked,
        "next_required_evidence": next_evidence,
        "next-required-evidence": next_evidence,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_review_decision(intake_json: str, evidence_ref: str = "") -> tuple[dict[str, Any], dict[str, Any], int]:
    """从 mobile_field_material_intake artifact/summary 生成 review decision。"""

    payload, load_issue = _load_json(intake_json)
    normalized = _normalize_intake(payload, evidence_ref) if payload else {
        "schema": "",
        "evidence_boundary": "",
        "evidence_ref": _safe_ref(evidence_ref),
        "source_evidence_ref": "",
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": "not_proven",
        "intake_verdict": "missing",
        "material_statuses": [],
        "missing_or_blocked": [],
        "not_proven": [],
        "unsafe_copy_detected": False,
        "placeholder_detected": False,
        "success_claim_detected": False,
    }
    schema_status = _schema_status(load_issue, normalized)
    decision = _review_decision(load_issue, schema_status, normalized, _safe_ref(evidence_ref))
    blocked = _blocked_materials(normalized) if decision != READY_DECISION else []
    owner = _owner_handoff(decision)
    next_evidence = _next_required_evidence(decision, normalized["evidence_ref"], blocked)
    generated_at = _utc_now()
    summary = _review_summary(decision, normalized["evidence_ref"], owner, blocked, next_evidence)
    artifact = {
        "schema": REVIEW_SCHEMA,
        "schema_version": REVIEW_SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": generated_at,
        "evidence_boundary": REVIEW_BOUNDARY,
        "review_decision": decision,
        "decision_order": list(DECISION_ORDER),
        "evidence_ref": normalized["evidence_ref"],
        "same_evidence_ref_required": True,
        "same_evidence_ref_status": "matched_same_evidence_ref" if decision == READY_DECISION else "not_proven",
        "owner_handoff": owner,
        "owner handoff": owner,
        "next_required_evidence": next_evidence,
        "next-required-evidence": next_evidence,
        "blocked_materials": blocked,
        "source_intake": {
            "ref": _safe_ref(intake_json),
            "load_issue": load_issue,
            "schema_status": schema_status,
            "schema": normalized["schema"],
            "evidence_boundary": normalized["evidence_boundary"],
            "intake_verdict": normalized["intake_verdict"],
            "same_evidence_ref_status": normalized["same_evidence_ref_status"],
            "unsafe_copy_detected": normalized["unsafe_copy_detected"],
            "placeholder_detected": normalized["placeholder_detected"],
            "success_claim_detected": normalized["success_claim_detected"],
        },
        "material_statuses": normalized["material_statuses"],
        "missing_or_blocked": normalized["missing_or_blocked"],
        "review_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "real_phone_device_or_browser",
            "real_route_elevator_field_pass",
            "real_nav2_or_fixed_route_runtime",
            "dropoff_or_cancel_completion",
            "hardware_hil_wave_rover_uart",
            "objective_5_external_proof",
        ],
        "boundary_note": "software proof only; delivery_success=false; primary_actions_enabled=false; not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    safe_artifact = _safe_value(artifact)
    safe_summary = _safe_value(summary)
    if _has_forbidden_copy(safe_artifact):
        # 最后一层保险：输出已脱敏后仍命中禁词时，只返回 blocked invalid contract。
        safe_artifact["review_decision"] = "blocked_invalid_intake"
        safe_artifact["owner_handoff"] = "Product closeout"
        safe_artifact["review_summary"]["review_decision"] = "blocked_invalid_intake"
        safe_artifact["review_summary"]["status"] = "blocked_invalid_intake"
        safe_summary = safe_artifact["review_summary"]
    return safe_artifact, safe_summary, 0 if decision == READY_DECISION else 2


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 指定输出路径时自动创建父目录，方便 sprint evidence bundle 落盘。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只接 intake 一个输入，避免把 review gate 变成新的材料采集入口。
    parser = argparse.ArgumentParser(
        description="Generate mobile_field_material_review_decision software-proof artifact."
    )
    parser.add_argument("--intake-json", required=True, help="mobile_field_material_intake artifact/summary JSON.")
    parser.add_argument("--evidence-ref", default="", help="Expected same evidence_ref for this review decision.")
    parser.add_argument("--output", default="", help="Write full review decision artifact JSON to this path.")
    parser.add_argument("--summary-output", default="", help="Write review decision summary JSON to this path.")
    parser.add_argument("--once-json", action="store_true", help="Print review decision artifact JSON to stdout.")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_review_decision(args.intake_json, args.evidence_ref)
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"mobile field material review decision: review_file:{_safe_ref(args.output)}")
        print(f"review_decision: {artifact['review_decision']}")
        print(f"owner handoff: {artifact['owner_handoff']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
