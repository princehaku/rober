#!/usr/bin/env python3
"""生成 cloud external evidence review handoff follow-up escalation status gate。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.cloud_external_evidence_review_handoff_followup_escalation_status.v1"
SUMMARY_SCHEMA = "trashbot.cloud_external_evidence_review_handoff_followup_escalation_status_summary.v1"
ROBOT_ALIAS_SCHEMA = (
    "trashbot.robot_diagnostics_cloud_external_evidence_review_handoff_followup_escalation_status_summary.v1"
)
ROBOT_ALIAS = "robot_diagnostics_cloud_external_evidence_review_handoff_followup_escalation_status_summary"
CAPABILITY = "cloud_external_evidence_review_handoff_followup_escalation_status"
SOURCE_CAPABILITY = "cloud_external_evidence_review_handoff"
UPSTREAM_CAPABILITY = "cloud_external_evidence_review_decision"
SOURCE = "software_proof"
STATUS = "not_proven"
EVIDENCE_BOUNDARY = "software_proof_docker_cloud_external_evidence_review_handoff_followup_escalation_status_gate"
SOURCE_BOUNDARY = "software_proof_docker_cloud_external_evidence_review_handoff_gate"
PR5_THREAD_ID = "PRRT_kwDOSWB9286CJ3tX"
NO_OKR_LIFT = "no OKR percentage lift"

PENDING = "pending_followup_not_proven"
DUE = "due_followup_not_proven"
OVERDUE = "overdue_followup_not_proven"
ESCALATED = "escalated_hardware_material_pending_not_proven"
BLOCKED = "blocked_missing_external_evidence_review_handoff_not_proven"
FOLLOWUP_STATUSES = (PENDING, DUE, OVERDUE, ESCALATED, BLOCKED)

SUPPORTED_SOURCE_SCHEMAS = {
    "trashbot.cloud_external_evidence_review_handoff.v1",
    "trashbot.cloud_external_evidence_review_handoff_summary.v1",
    "trashbot.robot_diagnostics_cloud_external_evidence_review_handoff_summary.v1",
}
WRAPPER_KEYS = (
    "robot_diagnostics_cloud_external_evidence_review_handoff_summary",
    "cloud_external_evidence_review_handoff_summary",
    "cloud_external_evidence_review_handoff",
    "summary",
    "safe_copy",
    "phone_readiness",
    "diagnostics",
    "data",
    "payload",
)

# 本 gate 只处理上一跳脱敏摘要；这些模式出现时必须 fail closed。
UNSAFE_TEXT_PATTERNS = (
    re.compile(r"(?i)\bAuthorization\s*:|\bBearer\s+"),
    re.compile(r"(?i)\b(token|secret|password|access[_-]?key|credential)\b\s*[:=]"),
    re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://|https?://|oss://|s3://"),
    re.compile(r"(?i)\b(raw artifact|raw diagnostics|raw json|raw payload|response body|traceback)\b"),
    re.compile(r"(?i)\b(github mutation|review mutation|handoff mutation|ack mutation|material upload)\b"),
    re.compile(r"(?i)\b(/cmd_vel|ros2 topic|/trashbot/|serial|uart|wave rover|esp32|orange pi)\b"),
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bPRRT_kwDOSWB9286CJ3tX\b.*\b(resolved|closed)\b"),
)
UNSAFE_KEY_TERMS = (
    "raw",
    "token",
    "secret",
    "password",
    "credential",
    "authorization",
    "access_key",
    "api_key",
    "db_url",
    "queue_url",
    "signed_url",
    "artifact_path",
    "local_path",
    "file_path",
    "cmd_vel",
    "ros_topic",
    "serial",
    "uart",
    "github_mutation",
    "material_upload",
    "control_command",
)

NOT_PROVEN_ITEMS = (
    "software_proof",
    "not_proven",
    "not_o5_external_proof",
    "not_public_https_tls_proof",
    "not_4g_sim_proof",
    "not_oss_cdn_live_traffic",
    "not_production_db_queue_proof",
    "not_worker_cutover_proof",
    "not_verified_terminal_result",
    "not true phone/browser proof",
    "not_hil",
    "not_delivery_success",
    "no OKR percentage lift",
)
FALSE_STATE_FLAGS = (
    "delivery_success=false",
    "primary_actions_enabled=false",
    "safe_to_control=false",
)
DEFAULT_NEXT_REQUIRED_EVIDENCE = (
    "next_required_evidence=real_public_https_tls_or_4g_or_oss_cdn_or_db_queue_safe_summary",
    "next_required_evidence=true_phone_browser_or_verified_terminal_result_safe_summary",
    "next_required_evidence=PRRT_kwDOSWB9286CJ3tX_real_material_resolution_before_reviewer_closeout",
)
BOUNDARY_NOTE = (
    f"{CAPABILITY}; {SOURCE_CAPABILITY}; {EVIDENCE_BOUNDARY}; source=software_proof; "
    "software_proof; not_proven; delivery_success=false; primary_actions_enabled=false; "
    "safe_to_control=false; not true phone/browser proof; no OKR percentage lift; "
    f"{PR5_THREAD_ID}; hardware_material_pending"
)


def _utc_now() -> str:
    # UTC 时间只用于审计排序，不参与 proof 结论。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any, default: str = "") -> str:
    # 输出文本保持短单行，避免把日志、路径或 raw JSON 带入 phone/support 面。
    if value is None:
        text = default
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    text = text.replace("\n", " ").replace("\r", " ")
    return text[:260] or default


def _safe_list(value: Any, fallback: str, limit: int = 16) -> list[str]:
    # route/evidence 字段兼容数组、map 和字符串，但每个元素都必须是安全短文本。
    if value in (None, ""):
        return [fallback]
    items = value if isinstance(value, list) else list(value.items()) if isinstance(value, dict) else [value]
    result: list[str] = []
    for item in list(items)[:limit]:
        if isinstance(item, tuple):
            key = _safe_text(item[0])
            raw = item[1]
            detail = _safe_text(raw.get("status") or raw.get("route") or raw.get("safe_summary")) if isinstance(raw, dict) else _safe_text(raw)
            text = f"{key}={detail}" if key and detail else key or detail
        elif isinstance(item, dict):
            text = _safe_text(item.get("name") or item.get("route") or item.get("status") or item.get("safe_summary"))
        else:
            text = _safe_text(item)
        if text and not _is_unsafe_text(text):
            result.append(text)
    return list(dict.fromkeys(result)) or [fallback]


def _encoded(value: Any) -> str:
    # 递归扫描使用稳定 JSON，确保嵌套字段里的越界 claim 也会被挡住。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _is_unsafe_text(value: Any) -> bool:
    text = _safe_text(value)
    return any(pattern.search(text) for pattern in UNSAFE_TEXT_PATTERNS)


def _read_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺文件或坏 JSON 是 blocked 输入，不把 traceback 交给用户界面。
    if not path:
        return {}, "handoff_json_not_provided"
    try:
        payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "handoff_json_missing"
    except json.JSONDecodeError:
        return {}, "handoff_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "handoff_json_read_error"
    if not isinstance(payload, dict):
        return {}, "handoff_json_not_object"
    return payload, ""


def _dict(value: Any) -> dict[str, Any]:
    # 只把 object 视为 wrapper；字符串化 JSON 不展开，避免绕过安全摘要边界。
    return value if isinstance(value, dict) else {}


def _candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 递归白名单 wrapper key，支持 artifact、summary、Robot alias 和 phone_readiness。
    result = [payload]
    for key in WRAPPER_KEYS:
        child = _dict(payload.get(key))
        if child:
            result.extend(_candidates(child))
    return result


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # source 必须看起来像 cloud_external_evidence_review_handoff safe summary。
    for candidate in _candidates(payload):
        if (
            _safe_text(candidate.get("schema")) in SUPPORTED_SOURCE_SCHEMAS
            or _safe_text(candidate.get("capability")) == SOURCE_CAPABILITY
        ):
            return candidate
    return payload


def _unsafe_reasons(value: Any) -> list[str]:
    # unsafe 原值不回显，只输出类别，避免 rejected artifact 二次泄漏。
    reasons: list[str] = []
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key, child in current.items():
                key_text = str(key).lower()
                if key not in {"delivery_success", "primary_actions_enabled", "safe_to_control"} and any(
                    term in key_text for term in UNSAFE_KEY_TERMS
                ):
                    reasons.append("forbidden_raw_control_credential_or_mutation_key")
                if key in {"delivery_success", "primary_actions_enabled", "safe_to_control"} and child is True:
                    reasons.append(f"{key}_true_overclaim")
                stack.append(child)
        elif isinstance(current, list):
            stack.extend(current)
        elif _is_unsafe_text(current):
            reasons.append("unsafe_text_or_success_control_claim")
    if _is_unsafe_text(_encoded(value)):
        reasons.append("unsafe_nested_payload")
    return list(dict.fromkeys(reasons))


def _source_view(payload: dict[str, Any], load_issue: str) -> dict[str, Any]:
    # normalized view 是后续状态计算唯一输入，避免 UI/CLI 自行解释 source。
    source = _find_source(payload) if payload else {}
    pr5_context = _dict(source.get("pr5_review_context") or source.get("pr5_thread") or source.get("pr5_context"))
    return {
        "load_issue": load_issue,
        "schema": _safe_text(source.get("schema")),
        "capability": _safe_text(source.get("capability")),
        "source_capability": _safe_text(source.get("source_capability")),
        "source": _safe_text(source.get("source"), SOURCE),
        "evidence_boundary": _safe_text(source.get("evidence_boundary") or source.get("proof_boundary")),
        "source_handoff_status": _safe_text(source.get("handoff_status") or source.get("status"), BLOCKED),
        "source_review_decision": _safe_text(source.get("source_review_decision") or source.get("review_decision")),
        "safe_evidence_ref": _safe_text(source.get("safe_evidence_ref") or source.get("evidence_ref"), "evidence_ref=not_proven"),
        "safe_command_ref": _safe_text(source.get("safe_command_ref") or source.get("command_ref") or source.get("command_id"), "command_ref=not_proven"),
        "owner_route": _safe_list(source.get("owner_route") or source.get("owner_handoff"), "owner_action=waiting_for_external_evidence_owner_followup"),
        "support_route": _safe_list(source.get("support_route") or source.get("support_handoff"), "support_action=keep_PRRT_kwDOSWB9286CJ3tX_hardware_material_pending_visible"),
        "reviewer_route": _safe_list(source.get("reviewer_route") or source.get("reviewer_handoff"), "reviewer_action=do_not_resolve_before_real_external_evidence"),
        "next_required_evidence": _safe_list(source.get("next_required_evidence"), DEFAULT_NEXT_REQUIRED_EVIDENCE[0]),
        "pr5_material_state": _safe_text(pr5_context.get(PR5_THREAD_ID) or pr5_context.get("material_state"), "hardware_material_pending"),
        "delivery_success": source.get("delivery_success"),
        "primary_actions_enabled": source.get("primary_actions_enabled"),
        "safe_to_control": source.get("safe_to_control"),
        "unsafe_reasons": _unsafe_reasons(source) if source else [],
    }


def _source_block_reasons(source: dict[str, Any]) -> list[str]:
    # source 合同错误必须先 blocked，再谈 due/escalation。
    reasons: list[str] = []
    if source["load_issue"]:
        reasons.append(source["load_issue"])
    if source["schema"] not in SUPPORTED_SOURCE_SCHEMAS and source["capability"] != SOURCE_CAPABILITY:
        reasons.append("unsupported_cloud_external_evidence_review_handoff_schema")
    if source["source_capability"] and source["source_capability"] != UPSTREAM_CAPABILITY:
        reasons.append("wrong_source_capability")
    if source["source"] != SOURCE:
        reasons.append("source_not_software_proof")
    if source["evidence_boundary"] != SOURCE_BOUNDARY:
        reasons.append("missing_or_wrong_cloud_external_evidence_review_handoff_boundary")
    if source["delivery_success"] is not False:
        reasons.append("delivery_success_false_flag_missing_or_changed")
    if source["primary_actions_enabled"] is not False:
        reasons.append("primary_actions_enabled_false_flag_missing_or_changed")
    if source["safe_to_control"] is not False:
        reasons.append("safe_to_control_false_flag_missing_or_changed")
    if source["pr5_material_state"] != "hardware_material_pending":
        reasons.append("pr5_hardware_material_pending_not_preserved")
    reasons.extend(source["unsafe_reasons"])
    return list(dict.fromkeys(reasons))


def _normalize_followup_status(value: str) -> str:
    # CLI 和库函数都只接受固定枚举；未知状态保守 blocked。
    text = _safe_text(value or PENDING).lower().replace("-", "_")
    return text if text in FOLLOWUP_STATUSES else BLOCKED


def _status_for_source(source: dict[str, Any], followup_status: str) -> tuple[str, list[str], int]:
    # follow-up escalation 只表达人工跟进时效，不改变 source handoff 的 proof 边界。
    reasons = _source_block_reasons(source)
    status = _normalize_followup_status(followup_status)
    if reasons or status == BLOCKED:
        if status == BLOCKED and followup_status not in {"", BLOCKED}:
            reasons.append("unsupported_followup_status")
        return BLOCKED, list(dict.fromkeys(reasons or ["blocked_missing_external_evidence_review_handoff"])), 2
    if status == PENDING:
        return status, ["owner_support_reviewer_followup_pending_not_proven"], 0
    if status == DUE:
        return status, ["owner_support_reviewer_followup_due_not_proven"], 0
    if status == OVERDUE:
        return status, ["owner_support_reviewer_followup_overdue_not_proven"], 0
    return status, ["ceo_escalation_recommended_for_hardware_material_pending_not_proven"], 0


def _due_status(status: str) -> dict[str, bool | str]:
    # 布尔派生给 mobile/web 渲染；不由手机端重新解析字符串。
    return {
        "status": status,
        "is_pending": status == PENDING,
        "is_due": status == DUE,
        "is_overdue": status == OVERDUE,
        "is_escalated": status == ESCALATED,
        "is_blocked": status == BLOCKED,
    }


def _ceo_escalation_recommendation(status: str) -> str:
    # CEO 升级建议只用于人工决策，不触发 GitHub 或机器人动作。
    if status == ESCALATED:
        return "ceo_escalation_recommended=escalate_PRRT_kwDOSWB9286CJ3tX_hardware_material_pending"
    if status == OVERDUE:
        return "ceo_escalation_recommended=prepare_escalation_if_owner_support_reviewer_do_not_backfill"
    if status == DUE:
        return "ceo_escalation_recommended=not_yet_escalated_due_followup_required"
    if status == PENDING:
        return "ceo_escalation_recommended=false_pending_followup"
    return "ceo_escalation_recommended=blocked_missing_safe_handoff"


def _summary(source: dict[str, Any], followup_status: str, reasons: list[str]) -> dict[str, Any]:
    # summary 是手机和 Robot alias 共用的最小安全面，所有 false flags 在这里重复。
    blocked_reason = "blocked_reason=" + ";".join(reasons)
    owner_action = _safe_list(source["owner_route"], "owner_action=backfill_same_safe_evidence_ref_external_materials")
    support_action = _safe_list(source["support_route"], "support_action=keep_PRRT_kwDOSWB9286CJ3tX_hardware_material_pending_visible")
    reviewer_action = _safe_list(source["reviewer_route"], "reviewer_action=wait_for_real_external_evidence_before_resolution")
    next_required = list(dict.fromkeys([*source["next_required_evidence"], *DEFAULT_NEXT_REQUIRED_EVIDENCE]))
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": 1,
        "summary_alias": ROBOT_ALIAS,
        "robot_alias_schema": ROBOT_ALIAS_SCHEMA,
        "capability": CAPABILITY,
        "source_capability": SOURCE_CAPABILITY,
        "upstream_capability": UPSTREAM_CAPABILITY,
        "source": SOURCE,
        "status": STATUS,
        "followup_status": followup_status,
        "source_handoff_status": source["source_handoff_status"],
        "source_review_decision": source["source_review_decision"] or "blocked_missing_external_evidence_intake_not_proven",
        "due_status": _due_status(followup_status),
        "blocked_reason": blocked_reason,
        "owner_action": owner_action,
        "support_action": support_action,
        "reviewer_action": reviewer_action,
        "ceo_escalation_recommendation": _ceo_escalation_recommendation(followup_status),
        "next_required_evidence": next_required[:12],
        "pr5_review_thread": PR5_THREAD_ID,
        "pr5_material_state": "hardware_material_pending",
        "safe_evidence_ref": source["safe_evidence_ref"],
        "safe_command_ref": source["safe_command_ref"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "source_evidence_boundary": SOURCE_BOUNDARY,
        "safe_phone_copy": (
            f"{CAPABILITY}={followup_status}; source={SOURCE}; {blocked_reason}; "
            f"{PR5_THREAD_ID}=hardware_material_pending; delivery_success=false; "
            "primary_actions_enabled=false; safe_to_control=false; not true phone/browser proof; "
            "no OKR percentage lift"
        ),
        "recovery_hint": "等待同一 safe evidence_ref 的真实外部材料或 reviewer resolution；手机端只读展示，不提交控制动作。",
        "false_state_flags": list(FALSE_STATE_FLAGS),
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "not_proven": list(NOT_PROVEN_ITEMS),
        "boundary_note": BOUNDARY_NOTE,
        "safe_copy": {
            "capability": CAPABILITY,
            "followup_status": followup_status,
            "source_handoff_status": source["source_handoff_status"],
            "blocked_reason": blocked_reason,
            "ceo_escalation_recommendation": _ceo_escalation_recommendation(followup_status),
            "pr5_review_thread": PR5_THREAD_ID,
            "pr5_material_state": "hardware_material_pending",
            "delivery_success": False,
            "primary_actions_enabled": False,
            "safe_to_control": False,
        },
    }


def build_cloud_external_evidence_review_handoff_followup_escalation_status(
    handoff_json: str,
    followup_status: str,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    payload, load_issue = _read_json(handoff_json)
    source = _source_view(payload, load_issue)
    status, reasons, exit_code = _status_for_source(source, followup_status)
    summary = _summary(source, status, reasons)
    artifact = {
        "schema": SCHEMA,
        "schema_version": 1,
        "generated_at": _utc_now(),
        "capability": CAPABILITY,
        "cloud_external_evidence_review_handoff_followup_escalation_status": status,
        "followup_status": status,
        "followup_reasons": reasons,
        "summary": summary,
        f"{CAPABILITY}_summary": summary,
        ROBOT_ALIAS: summary,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "source_boundary": SOURCE_BOUNDARY,
        "source": SOURCE,
        "status": STATUS,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }
    return artifact, summary, exit_code


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 输出只写调用方指定文件，不扫描或修改任何并行 worker 产物。
    if not path:
        return
    Path(path).expanduser().write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate cloud_external_evidence_review_handoff_followup_escalation_status "
            "software_proof Docker/local gate."
        )
    )
    parser.add_argument("--handoff-json", required=True, help="sanitized cloud_external_evidence_review_handoff JSON")
    parser.add_argument("--followup-status", choices=FOLLOWUP_STATUSES, default=PENDING)
    parser.add_argument("--output")
    parser.add_argument("--summary-output")
    parser.add_argument("--once-json", action="store_true")
    args = parser.parse_args()

    artifact, summary, exit_code = build_cloud_external_evidence_review_handoff_followup_escalation_status(
        args.handoff_json,
        args.followup_status,
    )
    _write_json(args.output, artifact)
    _write_json(args.summary_output, summary)
    if args.once_json or not args.output:
        print(json.dumps(artifact, ensure_ascii=False, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
