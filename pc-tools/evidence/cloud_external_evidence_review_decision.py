#!/usr/bin/env python3
"""生成 cloud external evidence review-decision artifact。

该工具只复核既有 `trashbot.external_evidence_intake` 安全摘要，把未来
公网入口、OSS/CDN、生产 DB/queue、4G/SIM、worker/cutover、真实手机和
terminal result 材料分成 accepted / needs backfill / unsafe / missing / ref
mismatch 五种稳定状态。它不访问公网、不读取 raw artifact、不触发机器人控制。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# schema/boundary 是 Robot diagnostics、mobile/web 和 sprint closeout 的稳定锚点。
REVIEW_SCHEMA = "trashbot.cloud_external_evidence_review_decision.v1"
REVIEW_SUMMARY_SCHEMA = "trashbot.cloud_external_evidence_review_decision_summary.v1"
REVIEW_SCHEMA_VERSION = 1
REVIEW_BOUNDARY = "software_proof_docker_cloud_external_evidence_review_decision_gate"
SOURCE_CAPABILITY = "trashbot.external_evidence_intake"
SOURCE_BOUNDARY = "software_proof_docker_external_evidence_intake_gate"
SOURCE_SCHEMA = "trashbot.external_evidence_intake"
SOURCE_SUMMARY_SCHEMA = "trashbot.external_evidence_intake_summary.v1"
SOURCE = "software_proof"

# 五种输出状态都带 not_proven，避免后续手机面板把 review 误解为真实外部证明。
ACCEPTED = "accepted_external_evidence_not_proven"
NEEDS_BACKFILL = "needs_external_evidence_backfill_not_proven"
REJECTED_UNSAFE = "rejected_unsafe_external_evidence_not_proven"
BLOCKED_MISSING = "blocked_missing_external_evidence_intake_not_proven"
REF_MISMATCH = "external_evidence_ref_mismatch_not_proven"
DECISION_STATES = (ACCEPTED, NEEDS_BACKFILL, REJECTED_UNSAFE, BLOCKED_MISSING, REF_MISMATCH)

# intake 旧能力只有四类材料；review-decision 额外显式要求 worker、真手机和 terminal result 后续补证。
REQUIRED_MATERIALS = (
    "public_ingress_tls",
    "oss_cdn",
    "production_db_queue",
    "four_g_sim",
    "worker_cutover",
    "true_phone_browser_proof",
    "verified_terminal_result",
)
ACCEPTED_STATUSES = {
    "accepted_not_proven",
    "present_not_proven",
    "safe_summary_present_not_proven",
    "redacted_external_material_present_not_proven",
}
MISSING_STATUSES = {
    "",
    "missing",
    "missing_not_proven",
    "blocked_missing_external_material_not_proven",
    "needs_backfill_not_proven",
}
UNSAFE_STATUSES = {
    "unsafe",
    "unsafe_not_proven",
    "rejected_unsafe_not_proven",
    "credential_bearing_rejected_not_proven",
}

# not_proven 列表是给移动端和 product closeout 的防误读合同。
NOT_PROVEN = (
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
    "not_delivery_success",
    "no OKR percentage lift",
)

# 这些词只能用于输入安全扫描，不允许原样出现在输出 artifact 的 safe fields。
FORBIDDEN_OUTPUT_MARKERS = (
    "authorization",
    "bearer",
    "token",
    "oss ak",
    "oss sk",
    "access_key",
    "secret",
    "credential",
    "database url",
    "db url",
    "queue url",
    "postgres://",
    "postgresql://",
    "mysql://",
    "redis://",
    "amqp://",
    "mongodb://",
    "signed url",
    "http://",
    "https://",
    "/users/",
    "/private/",
    "/tmp/",
    "/ws/",
    "traceback",
    "response body",
    "raw artifact",
    "raw diagnostics",
    "raw payload",
    "raw pr payload",
    "github mutation",
    "checksum",
    "complete artifact",
    "hardware detail",
    "delivery_success=true",
    "primary_actions_enabled=true",
    "safe_to_control=true",
)

# 输入里出现这些敏感模式时直接判 unsafe；输出侧只落 rejected 状态和安全原因枚举。
UNSAFE_INPUT_PATTERNS = (
    re.compile(r"(?i)\bAuthorization\s*:"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)\b(OSS_)?(ACCESS|SECRET)[A-Z_]*\b\s*[:=]"),
    re.compile(r"(?i)\b(access[_-]?key|secret|token|password)\b\s*[:=]"),
    re.compile(r"(?i)\b(db|database|queue)[_-]?url\b\s*[:=]"),
    re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://"),
    re.compile(r"(?i)\bhttps?://"),
    re.compile(r"/cmd_vel\b"),
    re.compile(r"/dev/(ttyUSB|ttyACM|cu\.|tty\.)"),
    re.compile(r"(?i)\b(serial|uart|baudrate|wave rover)\b"),
    re.compile(r"(?i)Traceback \(most recent call last\):"),
    re.compile(r"(?i)\b(checksum|response body|raw artifact|raw diagnostics|raw pr payload|github mutation)\b"),
    re.compile(r"(?i)\b(delivery_success|primary_actions_enabled|safe_to_control)\s*[:=]\s*true\b"),
)


def _utc_now() -> str:
    # UTC 字符串让本地和 Docker 生成结果可排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any, fallback: str = "") -> str:
    # 自由文本只允许短摘要，避免把 URL、凭证或路径从上游带到手机端。
    text = str(value if value not in (None, "") else fallback).strip()
    text = re.sub(r"(?i)\bhttps?://\S+", "[redacted_url]", text)
    text = re.sub(r"(?i)\bBearer\s+\S+", "Bearer [redacted]", text)
    text = re.sub(r"(?i)\b(authorization|token|secret|password)\b\s*[:=]\s*\S+", r"\1=[redacted]", text)
    text = re.sub(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://\S+", "[redacted_endpoint]", text)
    text = re.sub(r"/(?:Users|private|tmp|ws|var)/[^\s,]+", "[redacted_path]", text)
    text = re.sub(r"(?i)\b(authorization|bearer|token|secret|credential)\b", "[redacted]", text)
    return text[:220]


def _safe_ref(value: Any) -> str:
    # evidence_ref / command_ref 只能是稳定短引用；路径只保留 basename。
    text = _safe_text(value)
    if not text:
        return "not_proven"
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_list(value: Any, fallback: str, limit: int = 12) -> list[str]:
    # 列表字段兼容字符串、数组和缺失，统一输出有限安全文本。
    if isinstance(value, list):
        items = [_safe_text(item) for item in value[:limit]]
    elif value in (None, ""):
        items = []
    else:
        items = [_safe_text(value)]
    return [item for item in items if item] or [fallback]


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 读失败不抛异常给操作者；后续会转成 blocked missing intake 状态。
    if not path:
        return {}, "intake_path_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "intake_file_missing"
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}, "intake_file_unreadable"
    if not isinstance(payload, dict):
        return {}, "intake_not_object"
    return payload, ""


def _json_text(value: Any) -> str:
    # 安全扫描需要覆盖 key/value；编码失败时退回脱敏字符串。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_unsafe_input(value: Any) -> bool:
    # 任意层级出现 raw endpoint、credential、机器人控制或成功声明都拒绝。
    text = _json_text(value)
    return any(pattern.search(text) for pattern in UNSAFE_INPUT_PATTERNS)


def _source_summary(payload: dict[str, Any]) -> dict[str, Any]:
    # 支持 full artifact、summary 和 Robot safe alias 三种常见输入形态。
    for key in (
        "external_evidence_intake_summary",
        "trashbot.external_evidence_intake",
        "summary",
        "robot_diagnostics_external_evidence_intake_summary",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return payload


def _material_items(value: Any) -> list[dict[str, Any]]:
    # 上游 material_statuses 可能是 list 或 dict；这里归一到 name/status 列表。
    if isinstance(value, dict):
        items = []
        for name, raw in value.items():
            if isinstance(raw, dict):
                item = dict(raw)
                item.setdefault("name", name)
                items.append(item)
            else:
                items.append({"name": name, "status": raw})
        return items
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _normalize_material_statuses(source: dict[str, Any]) -> tuple[dict[str, dict[str, str]], list[str], list[str]]:
    # 只保留 material family、状态和安全摘要，不复制 raw material 内容。
    statuses: dict[str, dict[str, str]] = {}
    missing: list[str] = []
    unsafe: list[str] = []
    source_items = _material_items(source.get("material_statuses"))
    source_by_name = {_safe_text(item.get("name")): item for item in source_items if _safe_text(item.get("name"))}
    for name in REQUIRED_MATERIALS:
        item = source_by_name.get(name, {})
        raw_status = _safe_text(item.get("status") or item.get("material_status"), "missing_not_proven")
        if raw_status in MISSING_STATUSES:
            status = "missing_not_proven"
            missing.append(name)
        elif raw_status in UNSAFE_STATUSES:
            status = "unsafe_not_proven"
            unsafe.append(name)
        elif raw_status in ACCEPTED_STATUSES:
            status = "accepted_not_proven"
        else:
            status = "needs_review_not_proven"
            missing.append(name)
        statuses[name] = {
            "status": status,
            "safe_summary": _safe_text(item.get("safe_summary") or item.get("summary"), f"{name}=not_proven"),
            "evidence_ref": _safe_ref(item.get("evidence_ref") or source.get("evidence_ref")),
        }
    return statuses, missing, unsafe


def _schema_supported(source: dict[str, Any]) -> bool:
    # 只接受既有 intake schema/boundary；任意其它 JSON 都不能升级成 review 结果。
    schema = _safe_text(source.get("schema"))
    boundary = _safe_text(source.get("evidence_boundary"))
    return schema in {SOURCE_SCHEMA, SOURCE_SUMMARY_SCHEMA} and boundary == SOURCE_BOUNDARY


def _redaction_passed(source: dict[str, Any]) -> bool:
    # redaction_status 兼容字符串或对象；缺失按 not passed 处理。
    status = source.get("redaction_status")
    if isinstance(status, dict):
        return _safe_text(status.get("status")) == "passed"
    return _safe_text(status) == "passed"


def _expected_ref_mismatch(source_ref: str, expected_ref: str) -> bool:
    # same evidence_ref 是跨 PC/Robot/mobile 对齐的最小证据链，不一致直接分流。
    expected = _safe_ref(expected_ref) if expected_ref else ""
    if not expected:
        return False
    return source_ref not in {"", "not_proven", expected}


def _decide(
    *,
    load_issue: str,
    source: dict[str, Any],
    expected_ref: str,
    missing: list[str],
    unsafe: list[str],
) -> str:
    # 决策优先级固定：输入缺失 -> schema/unsafe -> ref mismatch -> backfill -> accepted。
    if load_issue or not source or not _schema_supported(source):
        return BLOCKED_MISSING
    if _has_unsafe_input(source) or not _redaction_passed(source) or unsafe:
        return REJECTED_UNSAFE
    source_ref = _safe_ref(source.get("evidence_ref"))
    if _expected_ref_mismatch(source_ref, expected_ref):
        return REF_MISMATCH
    if missing:
        return NEEDS_BACKFILL
    return ACCEPTED


def _next_required_evidence(decision: str, missing: list[str], evidence_ref: str) -> list[str]:
    # 下一步只说明补材料，不给上传端点、控制命令或 raw artifact 路径。
    ref = evidence_ref or "not_proven"
    if decision == ACCEPTED:
        return [
            f"product_closeout_review_safe_summary_for_evidence_ref={ref}",
            "keep_not_proven_until_real_external_probe_and_field_materials_are_reviewed",
        ]
    if decision == NEEDS_BACKFILL:
        return [f"backfill_{name}_safe_summary_for_evidence_ref={ref}" for name in missing[:7]]
    if decision == REF_MISMATCH:
        return [f"rerun_trashbot.external_evidence_intake_with_same_safe_evidence_ref={ref}"]
    if decision == REJECTED_UNSAFE:
        return ["remove_unsafe_raw_fields_paths_control_or_success_claims_then_regenerate_intake"]
    return ["generate_trashbot.external_evidence_intake_safe_artifact_before_review_decision"]


def _safe_copy(
    decision: str,
    evidence_ref: str,
    command_ref: str,
    material_statuses: dict[str, dict[str, str]],
    next_required: list[str],
) -> dict[str, Any]:
    # safe_copy 是 mobile 复制和 Robot alias 的最小白名单，不包含 raw artifact 内容。
    return {
        "capability": "cloud_external_evidence_review_decision",
        "source_capability": SOURCE_CAPABILITY,
        "review_decision": decision,
        "safe_evidence_ref": evidence_ref,
        "safe_command_ref": command_ref,
        "material_statuses": material_statuses,
        "next_required_evidence": next_required,
        "source": SOURCE,
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "not_true_phone_browser_proof": True,
        "no_okr_percentage_lift": True,
        "evidence_boundary": REVIEW_BOUNDARY,
    }


def _assert_no_forbidden_output(payload: dict[str, Any]) -> None:
    # 输出层最后检查一次，防止后续字段新增时泄漏敏感信息。
    text = _json_text(payload).lower()
    leaked = [marker for marker in FORBIDDEN_OUTPUT_MARKERS if marker in text]
    if leaked:
        raise ValueError(f"unsafe output marker detected: {leaked[0]}")


def build_review_decision(intake_json: str = "", expected_evidence_ref: str = "") -> tuple[dict[str, Any], dict[str, Any], int]:
    """从 external evidence intake 安全 artifact/summary 生成 review decision。"""

    payload, load_issue = _load_json(intake_json)
    source = _source_summary(payload) if payload else {}
    material_statuses, missing, unsafe = _normalize_material_statuses(source) if source else ({}, list(REQUIRED_MATERIALS), [])
    source_ref = _safe_ref(source.get("evidence_ref") or expected_evidence_ref)
    command_ref = _safe_ref(source.get("command_ref") or source.get("safe_command_ref") or "cloud_external_evidence_review_decision_not_proven")
    decision = _decide(
        load_issue=load_issue,
        source=source,
        expected_ref=expected_evidence_ref,
        missing=missing,
        unsafe=unsafe,
    )
    next_required = _next_required_evidence(decision, missing, source_ref)
    generated_at = _utc_now()
    copy = _safe_copy(decision, source_ref, command_ref, material_statuses, next_required)
    summary = {
        "schema": REVIEW_SUMMARY_SCHEMA,
        "schema_version": REVIEW_SCHEMA_VERSION,
        "capability": "cloud_external_evidence_review_decision",
        "source_capability": SOURCE_CAPABILITY,
        "source": SOURCE,
        "generated_at": generated_at,
        "evidence_boundary": REVIEW_BOUNDARY,
        "review_decision": decision,
        "safe_evidence_ref": source_ref,
        "safe_command_ref": command_ref,
        "material_statuses": material_statuses,
        "missing_materials": missing,
        "unsafe_materials": unsafe,
        "next_required_evidence": next_required,
        "safe_copy": copy,
        "safe_phone_copy": (
            f"cloud_external_evidence_review_decision={decision}; "
            "source=software_proof; not_proven; delivery_success=false; "
            "primary_actions_enabled=false; safe_to_control=false; "
            "not true phone/browser proof; no OKR percentage lift"
        ),
        "pr5_review_context": {
            "thread": "PRRT_kwDOSWB9286CJ3tX",
            "status": "hardware_material_pending",
        },
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "not_proven": list(NOT_PROVEN),
    }
    artifact = {
        "schema": REVIEW_SCHEMA,
        "schema_version": REVIEW_SCHEMA_VERSION,
        "capability": "cloud_external_evidence_review_decision",
        "source_capability": SOURCE_CAPABILITY,
        "source": SOURCE,
        "generated_at": generated_at,
        "evidence_boundary": REVIEW_BOUNDARY,
        "review_decision": decision,
        "decision_states": list(DECISION_STATES),
        "source_intake": {
            "schema": _safe_text(source.get("schema"), "missing"),
            "evidence_boundary": _safe_text(source.get("evidence_boundary"), "missing"),
            "load_issue": load_issue or "loaded",
            "redaction_status": "passed" if _redaction_passed(source) else "not_passed",
            "external_evidence_complete": False,
            "production_ready": False,
        },
        "safe_evidence_ref": source_ref,
        "safe_command_ref": command_ref,
        "material_statuses": material_statuses,
        "missing_materials": missing,
        "unsafe_materials": unsafe,
        "next_required_evidence": next_required,
        "summary": summary,
        "safe_copy": copy,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "not_proven": list(NOT_PROVEN),
    }
    _assert_no_forbidden_output(artifact)
    return artifact, summary, 0 if decision == ACCEPTED else 2


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 写入时创建父目录，方便 sprint artifact bundle 直接指定新路径。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只有 intake 输入和 review 输出，不提供上传、提交、复演或控制参数。
    parser = argparse.ArgumentParser(description="Generate cloud external evidence review-decision artifact.")
    parser.add_argument("--intake-json", default="", help="Existing trashbot.external_evidence_intake JSON.")
    parser.add_argument("--expected-evidence-ref", default="", help="Expected same safe evidence_ref.")
    parser.add_argument("--output", default="", help="Write full review-decision artifact JSON.")
    parser.add_argument("--summary-output", default="", help="Write safe review-decision summary JSON.")
    parser.add_argument("--once-json", action="store_true", help="Print full artifact JSON to stdout.")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_review_decision(args.intake_json, args.expected_evidence_ref)
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"cloud_external_evidence_review_decision={artifact['review_decision']}")
        print("delivery_success=false primary_actions_enabled=false safe_to_control=false")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
