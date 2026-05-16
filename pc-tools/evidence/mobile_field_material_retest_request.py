#!/usr/bin/env python3
"""生成 mobile field material route/elevator retest request artifact。

该 CLI 只读取上一轮 mobile_field_material_review_decision artifact/summary，
把 owner handoff 和 next-required-evidence 转成下一轮 route/elevator field
retest request。它不访问 ROS graph、Nav2 runtime、serial/UART、真实手机、
真实电梯、WAVE ROVER、外部云、OSS/CDN、DB/queue 或 4G。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# retest request 是 mobile review decision 之后的新证据请求层，schema 单独命名避免下游误读。
REQUEST_SCHEMA = "trashbot.mobile_field_material_retest_request.v1"
REQUEST_SUMMARY_SCHEMA = "trashbot.mobile_field_material_retest_request_summary.v1"
REQUEST_SCHEMA_VERSION = 1
REQUEST_BOUNDARY = "software_proof_docker_mobile_field_material_retest_request_gate"
SOURCE = "software_proof"

# 只支持上一轮 mobile review artifact/summary；任意其它 JSON 都必须 fail closed。
REVIEW_SCHEMA = "trashbot.mobile_field_material_review_decision.v1"
REVIEW_SUMMARY_SCHEMA = "trashbot.mobile_field_material_review_decision_summary.v1"
REVIEW_BOUNDARY = "software_proof_docker_mobile_field_material_review_decision_gate"
READY_REVIEW_DECISION = "ready_for_owner_handoff_not_proven"

# 输出枚举保持短字符串，便于 Robot diagnostics、mobile 和 Product closeout 白名单消费。
READY_REQUEST = "ready_for_route_elevator_field_retest_request_not_proven"
BLOCKED_REVIEW_NOT_READY = "blocked_mobile_field_material_review_not_ready"
BLOCKED_INVALID_REVIEW = "blocked_invalid_mobile_field_material_review"
BLOCKED_UNSAFE_COPY = "blocked_unsafe_copy"
BLOCKED_SUCCESS_OR_CONTROL_CLAIM = "blocked_success_or_control_claim"

# route/elevator retest request 只要求下一轮收集材料，不证明这些材料已经真实通过。
RETEST_MATERIALS = (
    ("device_pwa_observation.json", "device_pwa_observation", "Full-stack"),
    ("route_elevator_field_materials.json", "route_elevator_field_materials", "Product closeout"),
    ("nav2_fixed_route_runtime_log.json", "nav2_fixed_route_runtime_log", "Autonomy"),
    ("task_record.json", "task_record", "Robot"),
    ("completion_signal.json", "completion_signal", "Robot"),
    ("dropoff_cancel_material_status.json", "dropoff_cancel_material_status", "Robot"),
)

# not_proven 明确列出本 gate 不能证明的能力，避免 O2/O3 retest request 被误读成成功证据。
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

# 验收命令会检索这些边界语句；人工读 artifact 时也能直接看到不能启用动作。
BOUNDARY_NOTE = (
    "mobile_field_material_retest_request is a Docker/local software proof retest request; "
    "delivery_success=false; primary_actions_enabled=false; not_proven"
)

# 输出不能携带凭证、控制 topic、硬件传输、原始机器人响应或完整本机材料。
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

# 成功类自由文本必须阻断；但字段 delivery_success=false 是 contract 必需项，所以只拦 true/成功文案。
SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\broute/elevator\s+field\s+pass(ed)?\b"),
    re.compile(r"(?i)\bnav2\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bfixed[-_ ]route\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bdropoff\s+(success|succeeded|completed|complete)\b"),
    re.compile(r"(?i)\bcancel\s+(completed|complete|success|succeeded)\b"),
    re.compile(r"(?i)\bhil_pass\s*[:=]\s*true\b"),
)

# 先脱敏再扫描 forbidden copy，保证 review 中的自由文本不会污染 retest request。
SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\bAuthorization\s*:\s*[^,\s]+"), "[REDACTED_AUTH_HEADER]"),
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
    # UTC 让不同 PC/Docker 主机生成的 request 可以按字符串排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有进入 request 的文本统一脱敏，避免自由文本绕过输出白名单。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref 或输入路径只保留 basename，避免把本机绝对路径交给手机/支持面。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_list(value: Any, limit: int = 20) -> list[str]:
    # 上游字段可能是字符串或数组；这里限制数量，避免复制完整 artifact。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _safe_value(value: Any) -> Any:
    # 最终写盘前递归脱敏一次，防止新增嵌套字段绕过局部 helper。
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
    # forbidden/success 扫描使用稳定 JSON 字符串；不可编码时退回脱敏文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # 同时扫描 key/value，防止 summary 字段名或自由文本带出敏感边界。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _has_success_claim_copy(value: Any) -> bool:
    # 自由文本成功文案和 true 旗标都必须拦截，避免 request 被当作现场通过。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _any_true_key(value: Any, key: str) -> bool:
    # 成功或放行动作可能藏在嵌套字段或字符串里，因此必须递归检查。
    if isinstance(value, dict):
        return any((k == key and v is True) or _any_true_key(v, key) for k, v in value.items())
    if isinstance(value, list):
        return any(_any_true_key(item, key) for item in value)
    if isinstance(value, str):
        return bool(re.search(rf"(?i)\b{re.escape(key)}\s*[:=]\s*true\b", value))
    return False


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺文件、坏 JSON、非 object 都生成 blocked request，不抛未处理异常。
    if not path:
        return {}, "review_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "review_missing"
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}, "review_read_error"
    if not isinstance(payload, dict):
        return {}, "review_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只接受 object summary；其它形态不参与白名单消费。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _source_payload(payload: dict[str, Any]) -> dict[str, Any]:
    # 支持 full review artifact、summary，以及 diagnostics 嵌套的只读 summary。
    if "schema" in payload:
        # 外层 schema 一旦存在就必须受支持，不能让 unsupported wrapper 借 nested summary 混入。
        return payload
    nested_summary = _dict(payload, "review_summary") or _dict(payload, "mobile_field_material_review_decision_summary")
    if nested_summary:
        return nested_summary
    nested_artifact = _dict(payload, "mobile_field_material_review_decision")
    if nested_artifact:
        return nested_artifact
    return payload


def _normalize_review(payload: dict[str, Any]) -> dict[str, Any]:
    # request 只消费 review 的白名单字段，不复制 intake raw materials 或本机路径。
    source = _source_payload(payload)
    summary = _dict(source, "review_summary")
    effective = summary if summary.get("schema") == REVIEW_SUMMARY_SCHEMA else source
    same_required = effective.get("same_evidence_ref_required", source.get("same_evidence_ref_required", True))
    return {
        "schema": _safe_text(effective.get("schema", source.get("schema", ""))),
        "full_schema": _safe_text(source.get("schema", "")),
        "evidence_boundary": _safe_text(effective.get("evidence_boundary", source.get("evidence_boundary", ""))),
        "status": _safe_text(effective.get("status", source.get("review_decision", "missing_review"))),
        "review_decision": _safe_text(
            effective.get("review_decision") or source.get("review_decision") or "missing_review_decision"
        ),
        "evidence_ref": _safe_ref(effective.get("evidence_ref", source.get("evidence_ref", ""))),
        "same_evidence_ref_required": same_required,
        "owner_handoff": _safe_text(effective.get("owner_handoff", source.get("owner_handoff", ""))),
        "blocked_materials": _blocked_materials(effective.get("blocked_materials", source.get("blocked_materials", []))),
        "next_required_evidence": _safe_list(
            effective.get("next_required_evidence", source.get("next_required_evidence", [])), limit=10
        ),
        "next-required-evidence": _safe_list(
            effective.get("next-required-evidence", source.get("next-required-evidence", [])), limit=10
        ),
        "not_proven": _safe_list(effective.get("not_proven", source.get("not_proven", [])), limit=20),
        "delivery_success": _any_true_key(source, "delivery_success") or _any_true_key(effective, "delivery_success"),
        "primary_actions_enabled": _any_true_key(source, "primary_actions_enabled")
        or _any_true_key(effective, "primary_actions_enabled"),
        "success_claim_copy": _has_success_claim_copy(source) or _has_success_claim_copy(effective),
    }


def _blocked_materials(value: Any) -> list[dict[str, Any]]:
    # review 的 blocked_materials 只保留 name/status/owner/reason，避免复制 raw material。
    if not isinstance(value, list):
        return []
    materials: list[dict[str, Any]] = []
    for item in value[:20]:
        if not isinstance(item, dict):
            continue
        materials.append(
            {
                "name": _safe_text(item.get("name", "")),
                "status": _safe_text(item.get("status", "")),
                "owner": _safe_text(item.get("owner", "")),
                "reason": _safe_text(item.get("reason", "")),
            }
        )
    return materials


def _schema_status(load_issue: str, review: dict[str, Any]) -> str:
    # artifact 和 summary 都支持，但 schema、boundary、same_evidence_ref_required 必须严格匹配。
    if load_issue:
        return "not_loaded"
    schema_supported = review["schema"] in {REVIEW_SCHEMA, REVIEW_SUMMARY_SCHEMA}
    full_schema_supported = review["full_schema"] in {"", REVIEW_SCHEMA, REVIEW_SUMMARY_SCHEMA}
    boundary_supported = review["evidence_boundary"] == REVIEW_BOUNDARY
    same_ref_supported = review["same_evidence_ref_required"] is True
    return "supported" if schema_supported and full_schema_supported and boundary_supported and same_ref_supported else "unsupported"


def _request_verdict(load_issue: str, schema_status: str, review: dict[str, Any], unsafe: bool) -> str:
    # 决策顺序先看输入有效性和安全，再看 review 是否允许生成 retest request。
    if load_issue or schema_status != "supported" or not review["evidence_ref"]:
        return BLOCKED_INVALID_REVIEW
    if review["delivery_success"] or review["primary_actions_enabled"] or review["success_claim_copy"]:
        return BLOCKED_SUCCESS_OR_CONTROL_CLAIM
    if unsafe:
        return BLOCKED_UNSAFE_COPY
    if review["review_decision"] == READY_REVIEW_DECISION:
        return READY_REQUEST
    return BLOCKED_REVIEW_NOT_READY


def _material_checklist(evidence_ref: str, review: dict[str, Any]) -> list[dict[str, Any]]:
    # route/elevator material checklist 是下一轮补证据清单，不生成任何真实现场材料。
    ref = evidence_ref or "<same_evidence_ref>"
    blocked_names = {item["name"] for item in review["blocked_materials"] if item.get("name")}
    checklist: list[dict[str, Any]] = []
    for filename, category, owner in RETEST_MATERIALS:
        blocked = category in blocked_names or filename in blocked_names
        checklist.append(
            {
                "name": filename,
                "category": category,
                "owner": owner,
                "required": True,
                "same_evidence_ref_required": True,
                "request_status": "repair_from_review_gap" if blocked else "request_for_retest_capture",
                "capture_note": f"Collect {category} for route/elevator material checklist under evidence_ref={ref}.",
            }
        )
    return checklist


def _next_required_evidence(review: dict[str, Any], verdict: str) -> list[str]:
    # next_required_evidence 只描述补材料和重跑 gate，不给机器人控制命令。
    ref = review["evidence_ref"] or "<same_evidence_ref>"
    upstream = review["next_required_evidence"] or review["next-required-evidence"]
    if verdict == READY_REQUEST:
        return [
            f"Create route/elevator material checklist for field retest under evidence_ref={ref}.",
            "Collect all retest materials with the same evidence_ref before rerunning intake/review.",
            "Keep delivery_success=false and primary_actions_enabled=false until separate real field evidence exists.",
        ]
    if verdict == BLOCKED_REVIEW_NOT_READY and upstream:
        return upstream[:4] + [
            f"After repairing the review gap, rerun mobile_field_material_retest_request.py for evidence_ref={ref}."
        ]
    return [
        f"Regenerate mobile_field_material_review_decision for evidence_ref={ref}.",
        "Use supported schema/boundary, JSON boolean same_evidence_ref_required=true, and no success/control wording.",
    ]


def _retest_commands(evidence_ref: str) -> list[str]:
    # 命令都是 PC 材料整理步骤，不包含 ROS control、串口、云凭证或本机绝对路径。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"assign one route/elevator field retest evidence_ref={ref}",
        f"collect device_pwa_observation.json under evidence_ref={ref}",
        f"collect route_elevator_field_materials.json under evidence_ref={ref}",
        f"collect nav2_fixed_route_runtime_log.json under evidence_ref={ref}",
        f"collect task_record.json and completion_signal.json under evidence_ref={ref}",
        f"collect dropoff_cancel_material_status.json under evidence_ref={ref}",
        "rerun mobile_field_material_intake.py, then mobile_field_material_review_decision.py, then mobile_field_material_retest_request.py --once-json",
    ]


def _request_summary(verdict: str, review: dict[str, Any], checklist: list[dict[str, Any]]) -> dict[str, Any]:
    # summary 是 Robot diagnostics/mobile 的只读消费面，只放短字段和 fail-closed 标记。
    next_evidence = _next_required_evidence(review, verdict)
    return {
        "schema": REQUEST_SUMMARY_SCHEMA,
        "schema_version": REQUEST_SCHEMA_VERSION,
        "source": SOURCE,
        "evidence_boundary": REQUEST_BOUNDARY,
        "status": verdict,
        "request_verdict": verdict,
        "review_decision": review["review_decision"],
        "evidence_ref": review["evidence_ref"],
        "same_evidence_ref_required": True,
        "route/elevator material checklist": [item["name"] for item in checklist],
        "route_elevator_material_checklist": [item["name"] for item in checklist],
        "owner_handoff": review["owner_handoff"] or "Product closeout",
        "next_required_evidence": next_evidence,
        "next-required-evidence": next_evidence,
        "retest_commands": _retest_commands(review["evidence_ref"])[:4],
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_retest_request(review_json: str) -> tuple[dict[str, Any], dict[str, Any], int]:
    """从 mobile_field_material_review_decision artifact/summary 生成 retest request。"""

    payload, load_issue = _load_json(review_json)
    review = _normalize_review(payload) if payload else {
        "schema": "",
        "full_schema": "",
        "evidence_boundary": "",
        "status": "missing",
        "review_decision": "missing_review",
        "evidence_ref": "",
        "same_evidence_ref_required": True,
        "owner_handoff": "Product closeout",
        "blocked_materials": [],
        "next_required_evidence": [],
        "next-required-evidence": [],
        "not_proven": [],
        "delivery_success": False,
        "primary_actions_enabled": False,
        "success_claim_copy": False,
    }
    schema_status = _schema_status(load_issue, review)
    unsafe = bool(payload and _has_forbidden_copy(payload))
    verdict = _request_verdict(load_issue, schema_status, review, unsafe)
    checklist = _material_checklist(review["evidence_ref"], review)
    next_evidence = _next_required_evidence(review, verdict)
    summary = _request_summary(verdict, review, checklist)
    artifact = {
        "schema": REQUEST_SCHEMA,
        "schema_version": REQUEST_SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": _utc_now(),
        "evidence_boundary": REQUEST_BOUNDARY,
        "request_verdict": verdict,
        "overall_status": verdict,
        "evidence_ref": review["evidence_ref"],
        "same_evidence_ref_required": True,
        "source_review": {
            "ref": _safe_ref(review_json),
            "load_issue": load_issue,
            "schema_status": schema_status,
            "schema": review["schema"],
            "full_schema": review["full_schema"],
            "evidence_boundary": review["evidence_boundary"],
            "review_decision": review["review_decision"],
            "same_evidence_ref_required": review["same_evidence_ref_required"],
        },
        "route/elevator material checklist": checklist,
        "route_elevator_material_checklist": checklist,
        "next_required_evidence": next_evidence,
        "next-required-evidence": next_evidence,
        "retest_commands": _retest_commands(review["evidence_ref"]),
        "owner_handoff": review["owner_handoff"] or "Product closeout",
        "blocked_materials": review["blocked_materials"],
        "retest_request_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "ros_graph",
            "nav2_runtime",
            "fixed_route_runtime",
            "real_elevator",
            "dropoff_or_cancel_completion",
            "hardware_hil_wave_rover_uart",
            "objective_5_external_proof",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _has_forbidden_copy(artifact):
        # 最后一层保险：输出脱敏后仍命中禁词时，改成 blocked unsafe 且保持 fail-closed。
        artifact["request_verdict"] = BLOCKED_UNSAFE_COPY
        artifact["overall_status"] = BLOCKED_UNSAFE_COPY
        artifact["retest_request_summary"]["status"] = BLOCKED_UNSAFE_COPY
        artifact["retest_request_summary"]["request_verdict"] = BLOCKED_UNSAFE_COPY
        summary = artifact["retest_request_summary"]
        verdict = BLOCKED_UNSAFE_COPY
    return artifact, summary, 0 if verdict == READY_REQUEST else 2


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 指定输出路径时自动创建父目录，方便 sprint evidence bundle 落盘。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 单输入单输出，避免把 request gate 变成新的现场材料采集入口。
    parser = argparse.ArgumentParser(
        description="Generate mobile_field_material_retest_request software-proof retest request artifact."
    )
    parser.add_argument("--review-json", required=True, help="mobile_field_material_review_decision artifact/summary JSON.")
    parser.add_argument("--output", default="", help="Write full retest request artifact JSON to this path.")
    parser.add_argument("--summary-output", default="", help="Write retest request summary JSON to this path.")
    parser.add_argument("--once-json", action="store_true", help="Print retest request artifact JSON to stdout.")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_retest_request(args.review_json)
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"mobile field material retest request: request_file:{_safe_ref(args.output)}")
        print(f"request_verdict: {artifact['request_verdict']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
