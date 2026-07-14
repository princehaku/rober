#!/usr/bin/env python3
"""O5 外部证据安全复核决策工具。

该工具只消费 `trashbot.external_evidence_intake` 的脱敏输出，并生成
可被 cutover readiness packet 消费的本地软件 proof；它不连接生产云、
不访问 OSS/CDN、不触发机器人控制，也不证明真实送达。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

# 复核层是 external evidence intake 之后的独立 gate，不把材料存在升级为生产就绪。
SCHEMA = "trashbot.cloud_external_evidence_review_decision.v1"
SCHEMA_VERSION = 1
SUMMARY_SCHEMA = "trashbot.cloud_external_evidence_review_decision_summary.v1"
SUMMARY_SCHEMA_VERSION = 1
SOURCE_SCHEMA = "trashbot.external_evidence_intake"
SOURCE_SCHEMA_VERSION = 1
SOURCE_BOUNDARY = "software_proof_docker_external_evidence_intake_gate"
EVIDENCE_BOUNDARY = "software_proof_docker_cloud_external_evidence_review_decision_gate"

# 这 7 类材料是产品文档要求的 review-decision 覆盖面，缺一类就只能 backfill。
MATERIAL_FAMILIES = (
    "public_ingress_tls",
    "oss_cdn",
    "production_db_queue",
    "four_g_sim",
    "worker_cutover",
    "true_phone_browser_proof",
    "verified_terminal_result",
)

# 所有状态都保留 not_proven 后缀，避免 UI 或 packet 把 review accepted 读成生产成功。
ACCEPTED_DECISION = "accepted_external_evidence_not_proven"
BACKFILL_DECISION = "needs_external_evidence_backfill_not_proven"
UNSAFE_DECISION = "rejected_unsafe_external_evidence_not_proven"
MISSING_DECISION = "blocked_missing_external_evidence_intake_not_proven"
MISMATCH_DECISION = "external_evidence_ref_mismatch_not_proven"

# 摘要只允许安全枚举、引用和布尔 false；这些 marker 一旦出现在输入就必须拒绝。
FORBIDDEN_PATTERNS = (
    re.compile(r"(?i)\bAuthorization\b"),
    re.compile(r"(?i)\bBearer\s+"),
    re.compile(r"(?i)\btoken\b"),
    re.compile(r"(?i)\bsecret\b"),
    re.compile(r"(?i)\bpassword\b"),
    re.compile(r"(?i)\baccess[_-]?key\b"),
    re.compile(r"(?i)\bAK/SK\b"),
    re.compile(r"(?i)https?://"),
    re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://"),
    re.compile(r"(?i)\b(database|queue)[ _-]?url\b"),
    re.compile(r"(?i)\bresponse body\b"),
    re.compile(r"(?i)\braw response\b"),
    re.compile(r"(?i)Traceback \(most recent call last\):"),
    re.compile(r"(?i)/dev/(ttyUSB|ttyACM|cu\.|tty\.)"),
    re.compile(r"(?i)\bserial\b"),
    re.compile(r"(?i)\buart\b"),
    re.compile(r"(?i)\bwave rover\b"),
    re.compile(r"(?i)\bROS topic\b"),
    re.compile(r"(?i)/cmd_vel\b"),
    re.compile(r"(?i)/api/base/manual\b"),
    re.compile(r"(?i)/tmp/"),
)

# 这些缺口必须留在 output 中，确保后续 packet 和产品文案不会越界。
NOT_PROVEN = (
    "software_proof",
    "not_proven",
    "public_https_tls_success",
    "oss_cdn_live_traffic",
    "production_db_queue_external_success",
    "production_worker_cutover",
    "real_4g_sim",
    "true_phone_browser_proof",
    "verified_terminal_result",
    "route_execution",
    "delivery_success",
    "hil",
    "safe_to_control",
    "no OKR percentage lift",
)


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _sha256_checksum(payload: Any) -> str:
    # checksum 只覆盖输出 artifact，summary 不暴露完整 checksum。
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_json(path: str) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as stream:
        payload = json.load(stream)
    if not isinstance(payload, dict):
        raise ValueError("external evidence intake must be a JSON object")
    return payload


def _safe_ref(value: Any, *, limit: int = 128) -> str:
    # 引用字段只保留短 label，防止路径、URL 或凭证片段进入 artifact。
    text = str(value or "").strip()[:limit]
    if not text:
        return ""
    if any(pattern.search(text) for pattern in FORBIDDEN_PATTERNS):
        return ""
    if text.startswith(("/", "~/")) or "\\" in text:
        return ""
    if not re.fullmatch(r"[A-Za-z0-9_.:-]+", text):
        return ""
    return text


def _intake_is_unsafe(payload: dict[str, Any]) -> bool:
    # 对完整输入做安全扫描；命中后输出只写 rejection，不回显原文。
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return any(pattern.search(encoded) for pattern in FORBIDDEN_PATTERNS)


def _redaction_passed(value: Any) -> bool:
    if isinstance(value, dict):
        return str(value.get("status") or "").strip().lower() in {"pass", "passed"}
    return str(value or "").strip().lower() in {"pass", "passed"}


def _material_index(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    statuses = payload.get("material_statuses")
    if not isinstance(statuses, list):
        return {}
    output: dict[str, dict[str, Any]] = {}
    for item in statuses:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if name:
            output[name] = item
    return output


def _material_family_statuses(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 不复制 safe_summary 原文，只保留 family/status，避免 fixture 或真实材料里混入敏感文字。
    by_name = _material_index(payload)
    rows: list[dict[str, Any]] = []
    for name in MATERIAL_FAMILIES:
        item = by_name.get(name) or {}
        status = str(item.get("status") or "missing_not_proven").strip()
        accepted = status == "accepted_not_proven"
        rows.append(
            {
                "name": name,
                "status": status if status else "missing_not_proven",
                "review_status": "accepted_not_proven" if accepted else "needs_backfill_not_proven",
                "not_proven": True,
            }
        )
    return rows


def _decide(payload: dict[str, Any], expected_ref: str) -> tuple[str, list[str]]:
    # 决策顺序必须 fail-closed：先安全，再 schema/ref，最后才看材料覆盖。
    if payload.get("schema") != SOURCE_SCHEMA or int(payload.get("schema_version", 0) or 0) != SOURCE_SCHEMA_VERSION:
        return MISSING_DECISION, ["external_evidence_intake_schema"]
    if payload.get("evidence_boundary") != SOURCE_BOUNDARY:
        return MISSING_DECISION, ["external_evidence_intake_boundary"]
    if payload.get("production_ready") is not False or payload.get("overall_status") != "blocked":
        return UNSAFE_DECISION, ["external_evidence_intake_claims_production_ready"]
    if payload.get("external_evidence_complete") is not False:
        return UNSAFE_DECISION, ["external_evidence_intake_claims_complete"]
    if not _redaction_passed(payload.get("redaction_status")):
        return UNSAFE_DECISION, ["external_evidence_intake_redaction_not_passed"]
    if _intake_is_unsafe(payload):
        return UNSAFE_DECISION, ["external_evidence_intake_contains_phone_unsafe_markers"]

    expected = _safe_ref(expected_ref)
    actual = _safe_ref(payload.get("evidence_ref"))
    if expected and actual != expected:
        return MISMATCH_DECISION, ["external_evidence_ref_mismatch"]

    rows = _material_family_statuses(payload)
    missing = [row["name"] for row in rows if row["status"] != "accepted_not_proven"]
    if missing:
        return BACKFILL_DECISION, [f"{name}_backfill_required" for name in missing]
    return ACCEPTED_DECISION, []


def _next_required_evidence(decision: str, blocked_reasons: list[str]) -> list[str]:
    if decision == ACCEPTED_DECISION:
        return [
            "real_public_https_tls_success_class",
            "oss_cdn_live_traffic_evidence",
            "production_db_queue_external_probe",
            "production_worker_cutover_log",
            "real_4g_sim_network_trace",
            "true_phone_browser_acceptance",
            "verified_terminal_result",
        ]
    if decision == BACKFILL_DECISION:
        return blocked_reasons or ["complete_all_external_evidence_material_families"]
    if decision == MISMATCH_DECISION:
        return ["match_expected_external_evidence_ref_before_review"]
    if decision == UNSAFE_DECISION:
        return ["resubmit_redacted_external_evidence_without_urls_credentials_paths_or_bodies"]
    return ["provide_valid_external_evidence_intake_artifact"]


def _safe_summary(decision: str) -> str:
    if decision == ACCEPTED_DECISION:
        return "Cloud external evidence review decision accepted local software material; production proof remains not proven."
    if decision == BACKFILL_DECISION:
        return "Cloud external evidence review decision needs material-family backfill; production proof remains not proven."
    if decision == MISMATCH_DECISION:
        return "Cloud external evidence review decision blocked by evidence-ref mismatch; production proof remains not proven."
    if decision == UNSAFE_DECISION:
        return "Cloud external evidence review decision rejected unsafe intake; source details omitted."
    return "Cloud external evidence review decision blocked because intake artifact is missing or invalid."


def _build_payload_from_intake(
    payload: dict[str, Any],
    expected_ref: str,
    *,
    generated_at: str | None = None,
    forced_decision: str | None = None,
    forced_reasons: list[str] | None = None,
) -> dict[str, Any]:
    decision, blocked_reasons = (
        (forced_decision, list(forced_reasons or []))
        if forced_decision
        else _decide(payload, expected_ref)
    )
    rows = _material_family_statuses(payload)
    accepted_count = sum(1 for row in rows if row["status"] == "accepted_not_proven")
    missing_count = len(rows) - accepted_count
    evidence_ref = _safe_ref(expected_ref) or _safe_ref(payload.get("evidence_ref"))
    body = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "summary_schema": SUMMARY_SCHEMA,
        "summary_schema_version": SUMMARY_SCHEMA_VERSION,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "proof_boundary": EVIDENCE_BOUNDARY,
        "source_schema": SOURCE_SCHEMA,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "source_evidence_boundary": SOURCE_BOUNDARY,
        "generated_at": generated_at or _utc_now(),
        "source": "software_proof",
        "evidence_ref": evidence_ref,
        "command_ref": _safe_ref(payload.get("command_ref")),
        "review_decision": decision,
        "status": decision,
        "production_ready": False,
        "overall_status": "blocked",
        "external_evidence_complete": False,
        "external_evidence_proven": False,
        "connects_cloud_production": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "robot_control_executed": False,
        "route_execution_success": False,
        "hil_pass": False,
        "true_phone_browser_proof": False,
        "okr_credit_allowed": False,
        "support_only_reason": "no_real_production_external_evidence",
        "proof_scope_class": "software_proof_support_only",
        "material_family_statuses": rows,
        "material_family_counts": {
            "material_family_count": len(rows),
            "accepted_material_family_count": accepted_count,
            "missing_or_backfill_material_family_count": missing_count,
        },
        "blocked_reasons": blocked_reasons,
        "next_required_evidence": _next_required_evidence(decision, blocked_reasons),
        "pr_context": {
            "pr_id": "PRRT_kwDOSWB9286CJ3tX",
            "status": "hardware_material_pending",
        },
        "readiness_details": {
            "review_decision": decision,
            "material_family_count": len(rows),
            "accepted_material_family_count": accepted_count,
            "missing_or_backfill_material_family_count": missing_count,
            "production_ready": False,
            "delivery_success": False,
            "safe_to_control": False,
            "robot_control_executed": False,
            "route_execution_success": False,
            "hil_pass": False,
            "okr_credit_allowed": False,
        },
        "safe_summary": _safe_summary(decision),
        "retry_hint": "collect_real_external_evidence_then_submit_redacted_intake_and_review_again",
        "redaction_status": {
            "status": "pass",
            "urls_recorded": False,
            "credential_headers_recorded": False,
            "opaque_auth_values_recorded": False,
            "raw_bodies_recorded": False,
            "local_paths_recorded": False,
            "robot_control_paths_recorded": False,
        },
        "not_proven": list(NOT_PROVEN),
    }
    body["checksum"] = _sha256_checksum(body)
    return body


def _missing_payload(reason: str, expected_ref: str) -> dict[str, Any]:
    # 缺失或不可解析也写出标准 artifact，让下游 packet 有稳定的 fail-closed 状态。
    return _build_payload_from_intake(
        {
            "schema": SOURCE_SCHEMA,
            "schema_version": SOURCE_SCHEMA_VERSION,
            "evidence_boundary": SOURCE_BOUNDARY,
            "evidence_ref": _safe_ref(expected_ref),
            "redaction_status": "passed",
            "production_ready": False,
            "overall_status": "blocked",
            "external_evidence_complete": False,
            "material_statuses": [],
            "blocked_reason": reason,
        },
        expected_ref,
        forced_decision=MISSING_DECISION,
        forced_reasons=[reason],
    )


def build_review_decision_payload(intake_json: str, evidence_ref: str) -> dict[str, Any]:
    try:
        payload = _load_json(intake_json)
    except (OSError, ValueError, json.JSONDecodeError):
        return _missing_payload("external_evidence_intake_missing_or_invalid", evidence_ref)
    return _build_payload_from_intake(payload, evidence_ref)


def build_summary_payload(artifact: dict[str, Any]) -> dict[str, Any]:
    # Summary 是给手机/packet 的窄视图，不输出 checksum 或源 artifact 全量内容。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "artifact_schema": SCHEMA,
        "artifact_schema_version": SCHEMA_VERSION,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "source_schema": SOURCE_SCHEMA,
        "source_evidence_boundary": SOURCE_BOUNDARY,
        "source": "software_proof",
        "evidence_ref": artifact.get("evidence_ref", ""),
        "command_ref": artifact.get("command_ref", ""),
        "review_decision": artifact.get("review_decision", MISSING_DECISION),
        "status": artifact.get("status", MISSING_DECISION),
        "production_ready": False,
        "overall_status": "blocked",
        "external_evidence_complete": False,
        "external_evidence_proven": False,
        "connects_cloud_production": False,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "robot_control_executed": False,
        "route_execution_success": False,
        "hil_pass": False,
        "true_phone_browser_proof": False,
        "okr_credit_allowed": False,
        "support_only_reason": "no_real_production_external_evidence",
        "proof_scope_class": "software_proof_support_only",
        "material_family_counts": artifact.get("material_family_counts", {}),
        "material_family_statuses": artifact.get("material_family_statuses", []),
        "blocked_reasons": artifact.get("blocked_reasons", []),
        "next_required_evidence": artifact.get("next_required_evidence", []),
        "pr_context": artifact.get("pr_context", {}),
        "readiness_details": artifact.get("readiness_details", {}),
        "safe_summary": artifact.get("safe_summary", _safe_summary(MISSING_DECISION)),
        "retry_hint": artifact.get("retry_hint", ""),
        "redaction_status": artifact.get("redaction_status", {"status": "pass"}),
        "not_proven": list(NOT_PROVEN),
    }


def _write_json(path: str, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build O5 cloud external evidence review-decision artifact")
    parser.add_argument("--intake-json", required=True, help="sanitized trashbot.external_evidence_intake JSON")
    parser.add_argument(
        "--evidence-ref",
        "--expected-evidence-ref",
        dest="evidence_ref",
        required=True,
        help="expected safe evidence_ref label",
    )
    parser.add_argument("--output", required=True, help="artifact JSON output path")
    parser.add_argument("--summary-output", required=True, help="summary JSON output path")
    args = parser.parse_args(argv)

    artifact = build_review_decision_payload(args.intake_json, args.evidence_ref)
    summary = build_summary_payload(artifact)
    _write_json(args.output, artifact)
    _write_json(args.summary_output, summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
