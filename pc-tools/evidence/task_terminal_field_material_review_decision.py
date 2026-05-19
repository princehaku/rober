#!/usr/bin/env python3
"""生成 task terminal field material review decision artifact。

该 CLI 只读取上一轮 task_terminal_field_material_intake artifact/summary，
把 returned/missing materials 转成只读复核决策、owner handoff 和 rerun guidance。
它不访问 ROS graph、Nav2 runtime、serial/UART、真实电梯、真实硬件、外部云、
OSS/CDN、DB/queue、4G 或真实手机/browser。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# schema 是 PC gate、Robot diagnostics、mobile/web 和 Product closeout 的稳定契约。
ARTIFACT_SCHEMA = "trashbot.task_terminal_field_material_review_decision.v1"
SUMMARY_SCHEMA = "trashbot.task_terminal_field_material_review_decision_summary.v1"
SCHEMA_VERSION = 1
BOUNDARY = "software_proof_docker_task_terminal_field_material_review_decision_gate"
SOURCE = "software_proof"

# 只接受上一轮 task_terminal_field_material_intake 的 artifact/summary/safe alias。
INTAKE_SCHEMAS = {
    "trashbot.task_terminal_field_material_intake.v1",
    "trashbot.task_terminal_field_material_intake_summary.v1",
    "trashbot.robot_diagnostics_task_terminal_field_material_intake_summary.v1",
}
INTAKE_BOUNDARY = "software_proof_docker_task_terminal_field_material_intake_gate"

# 决策枚举保持 fail-closed；ready 也只是 owner handoff，不代表现场通过。
READY_DECISION = "ready_for_owner_handoff_not_proven"
BACKFILL_DECISION = "needs_required_material_backfill_not_proven"
UNSAFE_DECISION = "blocked_rejected_or_unsafe_materials_not_proven"
MISMATCH_DECISION = "blocked_evidence_ref_mismatch_not_proven"
UNSUPPORTED_DECISION = "blocked_missing_or_unsupported_intake_not_proven"
DECISION_ORDER = (
    UNSUPPORTED_DECISION,
    UNSAFE_DECISION,
    MISMATCH_DECISION,
    BACKFILL_DECISION,
    READY_DECISION,
)

# 缺口清单故意覆盖 route/elevator、terminal、phone 三类 owner，避免 happy path 误收口。
DEFAULT_MISSING_MATERIALS = (
    "real_task_record",
    "real_dropoff_or_cancel_terminal_material",
    "real_route_elevator_field_material",
    "real_phone_browser_evidence",
)

# not_proven 明确告诉下游：review decision 不是 field pass 或 delivery success。
NOT_PROVEN = (
    "real_task_record_acceptance",
    "real_dropoff_completion",
    "real_cancel_completion",
    "real_nav2_fixed_route_run",
    "real_route_completion_signal",
    "real_route_elevator_field_pass",
    "real_phone_device_or_browser",
    "real_hil_pass",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# owner handoff 用固定短标签，Product closeout 可以稳定聚合。
OWNER_HINTS = (
    ("task_record", "Robot Platform Engineer"),
    ("dropoff", "Robot Platform Engineer"),
    ("cancel", "Robot Platform Engineer"),
    ("route", "Autonomy Algorithm Engineer"),
    ("elevator", "Autonomy Algorithm Engineer"),
    ("nav2", "Autonomy Algorithm Engineer"),
    ("fixed_route", "Autonomy Algorithm Engineer"),
    ("phone", "User Touchpoint Full-Stack Engineer"),
    ("browser", "User Touchpoint Full-Stack Engineer"),
)

# 这些片段一旦进入输入，说明不是 phone-safe/sprint-safe 摘要，必须 blocked。
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
    "Traceback",
    "checksum",
    "complete artifact",
    "raw robot response",
)

# 本机路径和 placeholder 会让 evidence_ref 或材料无法复核，因此不进入 ready。
RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)
PLACEHOLDER_PATTERNS = (
    re.compile(r"(?i)<[^>]*(todo|placeholder|same_evidence_ref|fill|tbd)[^>]*>"),
    re.compile(r"(?i)\b(todo|tbd|placeholder|replace_me|sample_only|example_only)\b"),
)

# 成功和控制授权只能来自真实现场验收；本 gate 看到就强制 unsafe blocked。
SUCCESS_OR_CONTROL_PATTERNS = (
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\broute/elevator\s+field\s+pass(ed)?\b"),
    re.compile(r"(?i)\bnav2\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bfixed[-_ ]route\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bdropoff\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bcancel\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
)

# blocked artifact 也必须脱敏，避免失败证据泄漏 credential 或 raw runtime 细节。
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
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)complete artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)raw robot response"), "[REDACTED_RAW_RESPONSE]"),
)


def _utc_now() -> str:
    # UTC 让 Docker/local evidence bundle 在不同主机上仍可排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有自由文本先脱敏再参与输出或扫描，防止 blocked 分支泄漏原文。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text.strip()


def _safe_ref(value: Any) -> str:
    # evidence_ref 不允许把本机目录传播给 Robot/mobile，只保留 basename。
    text = _safe_text(value)
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 递归脱敏让未来新增嵌套字段默认继承同一安全边界。
    if isinstance(value, dict):
        return {str(_safe_text(key)): _safe_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return [_safe_value(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value


def _safe_list(value: Any, limit: int = 40) -> list[str]:
    # 上游可能传字符串、list 或缺失；统一成有限列表避免复制完整 artifact。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit] if _safe_text(item)]
    if value in (None, ""):
        return []
    text = _safe_text(value)
    return [text] if text else []


def _dedupe(values: list[str]) -> list[str]:
    # 保序去重，方便 owner 看到紧凑缺口而不丢优先级。
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _encoded(value: Any) -> str:
    # JSON 扫描覆盖 key/value；不可编码时退回脱敏文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 嵌套 summary 缺失时按空对象处理，避免展开 raw artifact。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都输出 blocked artifact，而不是抛未处理异常。
    if not path:
        return {}, "intake_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "intake_missing"
    except json.JSONDecodeError:
        return {}, "intake_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "intake_read_error"
    if not isinstance(payload, dict):
        return {}, "intake_not_object"
    return payload, ""


def _source_payload(payload: dict[str, Any]) -> dict[str, Any]:
    # 支持 artifact、summary、Robot safe alias 和自动化 wrapper，仍只取白名单字段。
    for key in (
        "task_terminal_field_material_intake",
        "task_terminal_field_material_intake_summary",
        "robot_diagnostics_task_terminal_field_material_intake_summary",
        "summary",
    ):
        candidate = _dict(payload, key)
        if candidate:
            return candidate
    return payload


def _has_forbidden_copy(value: Any) -> bool:
    # forbidden token 代表输入不适合进入 owner handoff。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _has_raw_path(value: Any) -> bool:
    # raw path 只会暴露本机 evidence bundle 位置，不是可交接材料。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _has_placeholder(value: Any) -> bool:
    # placeholder 让 material 看似齐全但实际不可复核，必须 fail closed。
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


def _has_success_or_control_claim(value: Any) -> bool:
    # success/control claim 会把 review decision 误读为真实现场通过。
    encoded = _encoded(value)
    if any(pattern.search(encoded) for pattern in SUCCESS_OR_CONTROL_PATTERNS):
        return True
    return any(
        _any_true_key(value, key)
        for key in ("delivery_success", "primary_actions_enabled", "safe_to_control", "control_grant", "hil_pass")
    )


def _default_next_required(missing_materials: list[str]) -> list[str]:
    # next_required_evidence 只描述补证据，不提供机器人控制命令。
    if not missing_materials:
        return ["保持同一 safe evidence_ref，交给 Product/owner 做人工复核。"]
    return [f"补齐同一 safe evidence_ref 下的 {item}" for item in missing_materials[:8]]


def _normalize_intake(payload: dict[str, Any], expected_ref: str) -> dict[str, Any]:
    # normalized 只保留 contract 字段；review gate 不复制 raw material body。
    source = _source_payload(payload)
    schema = _safe_text(source.get("schema") or payload.get("schema"))
    boundary = _safe_text(source.get("evidence_boundary") or source.get("source_evidence_boundary") or payload.get("evidence_boundary"))
    source_ref = _safe_ref(
        source.get("safe_evidence_ref")
        or source.get("evidence_ref")
        or payload.get("safe_evidence_ref")
        or payload.get("evidence_ref")
    )
    evidence_ref = _safe_ref(expected_ref) or source_ref
    accepted = _dedupe(
        _safe_list(source.get("accepted_materials"))
        + _safe_list(source.get("returned_materials"))
        + _safe_list(source.get("accepted_safe_refs"))
        + _safe_list(source.get("returned_safe_refs"))
    )
    # missing_materials 显式为空代表 intake 已声明无缺口；只有缺字段才回退默认缺口。
    missing = _dedupe(
        _safe_list(source.get("missing_materials"))
        if "missing_materials" in source
        else list(DEFAULT_MISSING_MATERIALS)
    )
    rejected = _dedupe(_safe_list(source.get("rejected_materials")) + _safe_list(source.get("blocked_materials")))
    return {
        "schema": schema,
        "evidence_boundary": boundary,
        "status": _safe_text(source.get("status") or payload.get("status") or "missing"),
        "safe_evidence_ref": evidence_ref,
        "source_evidence_ref": source_ref,
        "same_evidence_ref_required": bool(source.get("same_evidence_ref_required", True)),
        "accepted_materials": accepted,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "next_required_evidence": _safe_list(source.get("next_required_evidence")) or _default_next_required(missing),
        "phone_safe_copy": _safe_text(
            source.get("phone_safe_copy")
            or _dict(source, "phone_safe_summary").get("safe_copy")
            or "现场材料仍需复核；software_proof；not_proven；delivery_success=false；primary_actions_enabled=false；safe_to_control=false。"
        ),
        "unsafe_copy_detected": (
            _has_forbidden_copy(source)
            or _has_forbidden_copy(payload)
            or _has_raw_path(source)
            or _has_raw_path(payload)
        ),
        "placeholder_detected": _has_placeholder(source) or _has_placeholder(payload),
        "success_claim_detected": _has_success_or_control_claim(source) or _has_success_or_control_claim(payload),
    }


def _schema_status(load_issue: str, normalized: dict[str, Any]) -> str:
    # schema 与 boundary 同时白名单化，避免任意 JSON 被当成 terminal intake。
    if load_issue:
        return "not_loaded"
    if normalized["schema"] in INTAKE_SCHEMAS and normalized["evidence_boundary"] == INTAKE_BOUNDARY:
        return "supported"
    return "unsupported"


def _owners_for_materials(materials: list[str]) -> list[str]:
    # owner 从材料名推导为固定角色，缺口多时保序输出，便于分工。
    owners: list[str] = []
    for material in materials:
        lower = material.lower()
        owner = "Product Manager / OKR Owner"
        for token, candidate in OWNER_HINTS:
            if token in lower:
                owner = candidate
                break
        if owner not in owners:
            owners.append(owner)
    return owners or ["Product Manager / OKR Owner"]


def _blocked_materials(normalized: dict[str, Any], decision: str) -> list[str]:
    # blocked_materials 汇总 missing/rejected/unsafe，给 Robot/mobile 同一字段消费。
    if decision == READY_DECISION:
        return []
    if decision == UNSAFE_DECISION:
        return _dedupe(normalized["rejected_materials"] + ["unsafe_or_success_copy"])
    if decision == MISMATCH_DECISION:
        return ["evidence_ref_mismatch"]
    if decision == UNSUPPORTED_DECISION:
        return ["missing_or_unsupported_intake"]
    return _dedupe(normalized["missing_materials"])


def _review_decision(load_issue: str, schema_status: str, normalized: dict[str, Any], expected_ref: str) -> str:
    # 决策顺序：输入契约 -> 安全 -> evidence_ref -> 材料缺口 -> ready。
    if load_issue or schema_status != "supported":
        return UNSUPPORTED_DECISION
    if normalized["unsafe_copy_detected"] or normalized["placeholder_detected"] or normalized["success_claim_detected"]:
        return UNSAFE_DECISION
    if not normalized["safe_evidence_ref"] or normalized["safe_evidence_ref"].startswith("file:"):
        return MISMATCH_DECISION
    if expected_ref and normalized["source_evidence_ref"] and normalized["source_evidence_ref"] != normalized["safe_evidence_ref"]:
        return MISMATCH_DECISION
    if not normalized["same_evidence_ref_required"]:
        return MISMATCH_DECISION
    if normalized["rejected_materials"]:
        return UNSAFE_DECISION
    if normalized["missing_materials"]:
        return BACKFILL_DECISION
    if normalized["accepted_materials"]:
        return READY_DECISION
    return BACKFILL_DECISION


def _summary(decision: str, normalized: dict[str, Any], blocked: list[str]) -> dict[str, Any]:
    # summary 是 Robot diagnostics/mobile 的只读消费面，不包含 raw artifact。
    owners = _owners_for_materials(blocked or normalized["accepted_materials"])
    next_required = normalized["next_required_evidence"] if decision != READY_DECISION else [
        f"Product owner reviews accepted_materials for safe_evidence_ref={normalized['safe_evidence_ref']}.",
        "Keep delivery_success=false, primary_actions_enabled=false, and safe_to_control=false until real field proof exists.",
    ]
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "summary_alias": "robot_diagnostics_task_terminal_field_material_review_decision_summary",
        "source": SOURCE,
        "evidence_boundary": BOUNDARY,
        "status": decision,
        "review_decision": decision,
        "safe_evidence_ref": normalized["safe_evidence_ref"],
        "same_evidence_ref_required": True,
        "accepted_materials": normalized["accepted_materials"],
        "missing_materials": normalized["missing_materials"] if decision != READY_DECISION else [],
        "rejected_materials": normalized["rejected_materials"],
        "blocked_materials": blocked,
        "owner_handoff": owners,
        "next_required_evidence": next_required,
        "rerun_guidance": [
            "补齐缺失材料后重新运行 task_terminal_field_material_intake",
            "保持同一 safe evidence_ref 后再运行 task_terminal_field_material_review_decision",
        ],
        "phone_safe_copy": "现场材料复核仍是 software_proof/not_proven；只能查看复核决策和下一步证据要求。",
        "evidence_boundary_flags": [
            "software_proof",
            "not_proven",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
        ],
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


def build_review_decision(intake_json: str, evidence_ref: str = "") -> tuple[dict[str, Any], dict[str, Any], int]:
    """从 task_terminal_field_material_intake artifact/summary 生成 review decision。"""

    payload, load_issue = _load_json(intake_json)
    normalized = (
        _normalize_intake(payload, evidence_ref)
        if payload
        else {
            "schema": "",
            "evidence_boundary": "",
            "status": "missing",
            "safe_evidence_ref": _safe_ref(evidence_ref),
            "source_evidence_ref": "",
            "same_evidence_ref_required": True,
            "accepted_materials": [],
            "missing_materials": list(DEFAULT_MISSING_MATERIALS),
            "rejected_materials": [],
            "next_required_evidence": _default_next_required(list(DEFAULT_MISSING_MATERIALS)),
            "phone_safe_copy": "",
            "unsafe_copy_detected": False,
            "placeholder_detected": False,
            "success_claim_detected": False,
        }
    )
    expected_ref = _safe_ref(evidence_ref)
    schema_status = _schema_status(load_issue, normalized)
    decision = _review_decision(load_issue, schema_status, normalized, expected_ref)
    blocked = _blocked_materials(normalized, decision)
    summary = _summary(decision, normalized, blocked)
    artifact = {
        "schema": ARTIFACT_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": _utc_now(),
        "evidence_boundary": BOUNDARY,
        "review_decision": decision,
        "decision_order": list(DECISION_ORDER),
        "safe_evidence_ref": normalized["safe_evidence_ref"],
        "same_evidence_ref_required": True,
        "accepted_materials": summary["accepted_materials"],
        "missing_materials": summary["missing_materials"],
        "rejected_materials": summary["rejected_materials"],
        "blocked_materials": blocked,
        "owner_handoff": summary["owner_handoff"],
        "next_required_evidence": summary["next_required_evidence"],
        "rerun_guidance": summary["rerun_guidance"],
        "source_intake": {
            "ref": _safe_ref(intake_json),
            "load_issue": load_issue,
            "schema_status": schema_status,
            "schema": normalized["schema"],
            "evidence_boundary": normalized["evidence_boundary"],
            "status": normalized["status"],
            "unsafe_copy_detected": normalized["unsafe_copy_detected"],
            "placeholder_detected": normalized["placeholder_detected"],
            "success_claim_detected": normalized["success_claim_detected"],
        },
        "review_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "ros_graph",
            "nav2_runtime",
            "field_elevator_runtime",
            "external_cloud_or_db_queue",
            "real_phone_browser",
        ],
        "boundary_note": "software_proof; not_proven; delivery_success=false; primary_actions_enabled=false; safe_to_control=false",
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }
    safe_artifact = _safe_value(artifact)
    safe_summary = _safe_value(summary)
    return safe_artifact, safe_summary, 0 if decision == READY_DECISION else 2


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 指定输出路径时创建父目录，便于 evidence bundle 自动落盘。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只接上一轮 intake 输入；不新增真实材料目录、runtime 或控制入口。
    parser = argparse.ArgumentParser(
        description="Generate task_terminal_field_material_review_decision software-proof artifact."
    )
    parser.add_argument("--intake-json", required=True, help="task_terminal_field_material_intake artifact/summary JSON.")
    parser.add_argument("--evidence-ref", default="", help="Expected same safe evidence_ref for this review.")
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
        print(f"task terminal field material review decision: review_file:{_safe_ref(args.output)}")
        print(f"review_decision: {artifact['review_decision']}")
        print(f"owner_handoff: {', '.join(artifact['owner_handoff'])}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
