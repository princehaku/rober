#!/usr/bin/env python3
"""生成 route/task field-run reconciliation artifact。

该工具只复账 execution pack 与 intake/review JSON 的软件材料。
它不访问 ROS graph、Nav2 runtime、serial/UART、硬件、外部云或真实机器人运行面。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# reconciliation 是 execution pack 之后的复账契约，不能和 pack/review/intake 混用。
RECONCILIATION_SCHEMA = "trashbot.route_task_field_run_reconciliation.v1"
RECONCILIATION_SCHEMA_VERSION = 1
RECONCILIATION_BOUNDARY = "software_proof_docker_route_task_field_run_reconciliation_gate"
PACK_SCHEMA = "trashbot.route_task_field_run_execution_pack.v1"
PACK_BOUNDARY = "software_proof_docker_route_task_field_run_execution_pack_gate"
INTAKE_SCHEMA = "trashbot.route_task_field_run_intake_crosscheck.v1"
INTAKE_BOUNDARY = "software_proof_docker_route_task_field_run_intake_crosscheck_gate"
REVIEW_SCHEMA = "trashbot.route_task_field_run_review_console.v1"
REVIEW_BOUNDARY = "software_proof_docker_route_task_field_run_review_console_gate"

# not_proven 是本 gate 的证据边界清单，防止复账报告被当成真实 field run。
NOT_PROVEN = (
    "real_nav2_fixed_route_run",
    "real_route_capture",
    "real_robot_base_motion",
    "real_hardware_feedback",
    "real_hil_pass",
    "dropoff_completion",
    "cancel_completion",
    "delivery_success",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# phone-safe copy 不能带凭证、控制 topic、设备路径、硬件细节、traceback 或 raw artifact。
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

# 脱敏规则覆盖常见凭证、DB/queue URL、控制 topic、设备路径、硬件名和 raw 文本。
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
    (re.compile(r"(?i)WAVE\s+ROVER"), "[REDACTED_PLATFORM]"),
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)complete artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)raw robot response"), "[REDACTED_RAW_RESPONSE]"),
)


def _utc_now() -> str:
    # UTC 时间戳让不同 PC/Docker 主机上的 artifact 可按字符串排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有自由文本先脱敏再进入输出，避免 raw support 说明扩散敏感材料。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # 本机路径不应出现在手机或复账摘要中，只保留 basename 作为同 run 线索。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_list(value: Any, limit: int = 20) -> list[str]:
    # 兼容旧 artifact 的字符串或 list 形态，并限制数量避免复制完整 artifact。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _safe_value(value: Any) -> Any:
    # 最终输出递归脱敏一次，防止新增字段绕过局部 helper。
    if isinstance(value, dict):
        return {str(_safe_text(k)): _safe_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return [_safe_value(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value


def _encoded(value: Any) -> str:
    # 安全检查需要稳定字符串；不可编码对象降级为脱敏字符串。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # forbidden 检查覆盖键和值，命中时宁可 blocked 也不让 unsafe summary 外流。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 缺文件、坏 JSON、非 object 都生成 blocked artifact，而不是让 CLI 抛异常。
    if not path:
        return {}, f"{label}_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, f"{label}_missing"
    except json.JSONDecodeError:
        return {}, f"{label}_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, f"{label}_read_error"
    if not isinstance(payload, dict):
        return {}, f"{label}_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只消费 object summary；非 dict 字段按缺失处理，避免复制 raw 字段。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # evidence_ref 和状态可来自顶层或 phone summary；只取白名单中的首个非空值。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _supported_material(schema: str, boundary: str) -> tuple[str, str]:
    # intake-json 参数兼容 intake crosscheck 与 review console 两种现场复账材料。
    if schema == INTAKE_SCHEMA:
        expected = INTAKE_BOUNDARY
        kind = "intake_crosscheck"
    elif schema == REVIEW_SCHEMA:
        expected = REVIEW_BOUNDARY
        kind = "review_console"
    else:
        return "", ""
    return kind, expected if boundary == expected else ""


def _source_state(label: str, payload: dict[str, Any], load_issue: str) -> dict[str, Any]:
    # source_state 只暴露 schema、boundary、safe ref 与状态，不复制输入 JSON。
    if load_issue:
        return {
            "name": label,
            "load_status": "blocked",
            "load_issue": load_issue,
            "schema": "",
            "schema_status": "not_loaded",
            "boundary_status": "not_loaded",
            "evidence_ref": "",
            "overall_status": "missing",
        }

    schema = _safe_text(payload.get("schema", ""))
    boundary = _safe_text(payload.get("evidence_boundary", ""))
    if label == "execution_pack":
        schema_status = "supported" if schema == PACK_SCHEMA else "unsupported"
        boundary_status = "supported" if boundary == PACK_BOUNDARY else "unsupported"
    else:
        material_kind, matched_boundary = _supported_material(schema, boundary)
        schema_status = "supported" if material_kind else "unsupported"
        boundary_status = "supported" if matched_boundary else "unsupported"

    phone = _dict(payload, "phone_safe_summary")
    return {
        "name": label,
        "load_status": "loaded",
        "load_issue": "",
        "schema": schema,
        "schema_status": schema_status,
        "boundary_status": boundary_status,
        "evidence_ref": _safe_ref(_first_text(payload.get("evidence_ref"), phone.get("evidence_ref"), default="")),
        "overall_status": _safe_text(_first_text(payload.get("overall_status"), phone.get("status"), default="missing")),
    }


def _material_status_from_intake_or_review(payload: dict[str, Any]) -> dict[str, Any]:
    # intake/review 的材料状态只保留计数和白名单列表，给 mobile/diagnostics 展示足够信息。
    schema = payload.get("schema", "")
    phone = _dict(payload, "phone_safe_summary")
    if schema == INTAKE_SCHEMA:
        return {
            "kind": "intake_crosscheck",
            "source_materials": [
                {
                    "name": _safe_text(source.get("name", "")),
                    "status": _safe_text(source.get("schema_status", "")),
                    "evidence_ref": _safe_ref(source.get("evidence_ref", "")),
                    "load_status": _safe_text(source.get("load_status", "")),
                }
                for source in payload.get("source_materials", [])
                if isinstance(source, dict)
            ],
            "missing_materials": _safe_list(payload.get("missing_materials")),
            "mismatch_reasons": _safe_list(payload.get("mismatch_reasons")),
            "missing_materials_count": len(_safe_list(payload.get("missing_materials"))),
            "mismatch_reasons_count": len(_safe_list(payload.get("mismatch_reasons"))),
            "phone_material_status": _safe_value(phone.get("material_status", {})),
            "source_phone_safe_summary": {
                "status": _safe_text(phone.get("status", "")),
                "evidence_ref": _safe_ref(phone.get("evidence_ref", "")),
                "not_proven": _safe_list(phone.get("not_proven")),
                "delivery_success": bool(phone.get("delivery_success", False)),
                "primary_actions_enabled": bool(phone.get("primary_actions_enabled", False)),
            },
        }
    return {
        "kind": "review_console",
        "missing_materials": _safe_list(payload.get("missing_materials")),
        "mismatch_reasons": _safe_list(payload.get("mismatch_reasons")),
        "missing_materials_count": len(_safe_list(payload.get("missing_materials"))),
        "mismatch_reasons_count": len(_safe_list(payload.get("mismatch_reasons"))),
        "review_decision": _safe_value(payload.get("review_decision", {})),
        "source_phone_safe_summary": {
            "status": _safe_text(phone.get("status", "")),
            "evidence_ref": _safe_ref(phone.get("evidence_ref", "")),
            "not_proven": _safe_list(phone.get("not_proven")),
            "delivery_success": bool(phone.get("delivery_success", False)),
            "primary_actions_enabled": bool(phone.get("primary_actions_enabled", False)),
        },
    }


def _missing_materials(material_status: dict[str, Any]) -> list[str]:
    # missing materials 包含显式缺失和 source_materials 未 loaded/unsupported/missing ref。
    missing = list(material_status.get("missing_materials", []))
    for source in material_status.get("source_materials", []):
        if source.get("load_status") != "loaded":
            missing.append(f"{source.get('name', 'unknown')}:not_loaded")
        if source.get("status") == "unsupported":
            missing.append(f"{source.get('name', 'unknown')}:unsupported_schema")
        if not source.get("evidence_ref"):
            missing.append(f"{source.get('name', 'unknown')}:missing_evidence_ref")
    return missing


def _source_operator_steps(pack_payload: dict[str, Any], intake_payload: dict[str, Any]) -> list[str]:
    # ready 路径优先带入源 artifact 的 operator steps，再由本 gate 补上边界提醒。
    pack_phone = _dict(pack_payload, "phone_safe_summary")
    intake_phone = _dict(intake_payload, "phone_safe_summary")
    review_decision = _dict(intake_payload, "review_decision")
    candidates = []
    candidates.extend(_safe_list(pack_payload.get("operator_next_steps") or pack_phone.get("operator_next_steps"), limit=4))
    candidates.extend(_safe_list(intake_payload.get("operator_next_steps") or intake_phone.get("operator_next_steps"), limit=4))
    if review_decision.get("operator_action"):
        candidates.append(_safe_text(review_decision.get("operator_action")))

    # 去重保持原顺序，避免 diagnostics/mobile 上重复显示同一条现场指令。
    steps: list[str] = []
    for item in candidates:
        if item and item not in steps:
            steps.append(item)
    return steps


def _merged_not_proven(pack_payload: dict[str, Any], intake_payload: dict[str, Any]) -> list[str]:
    # 固定边界为主，源 artifact 的 not_proven 只做补充，防止旧材料漏掉新边界。
    merged = list(NOT_PROVEN)
    for source in (pack_payload, intake_payload, _dict(pack_payload, "phone_safe_summary"), _dict(intake_payload, "phone_safe_summary")):
        for item in _safe_list(source.get("not_proven")):
            if item and item not in merged:
                merged.append(item)
    return merged


def _operator_steps(
    status: str,
    evidence_ref: str,
    pack_status: str,
    material_status: dict[str, Any],
    source_steps: list[str],
) -> list[str]:
    # operator_next_steps 把复账 verdict 转成现场下一步，不让操作者从 JSON 猜分支。
    ref = evidence_ref or "<same_evidence_ref>"
    if status in {"blocked_missing_execution_pack", "blocked_bad_json", "blocked_unsupported_schema", "blocked_unsupported_boundary"}:
        return [
            "Regenerate route_task_field_run_execution_pack.py from a supported review console.",
            f"Keep the regenerated execution pack on evidence_ref={ref}.",
            "Rerun this reconciliation gate after the execution pack is readable.",
        ]
    if status in {"blocked_missing_intake", "blocked_missing_materials"}:
        return [
            f"Collect or repair all field-run intake/review materials for evidence_ref={ref}.",
            "Rerun route_task_field_run_intake.py and route_task_field_run_review.py before reconciliation.",
            "Keep delivery_success=false until real route/task and HIL evidence exists.",
        ]
    if status == "blocked_evidence_ref_mismatch":
        return [
            f"Re-export execution pack and intake/review under one evidence_ref={ref}.",
            "Rerun intake, review, execution pack, then reconciliation in that order.",
            "Do not combine materials from different route/task runs.",
        ]
    if status == "blocked_unsafe_summary":
        return [
            "Remove unsafe phone/support copy from source summaries.",
            "Regenerate intake/review/execution pack after the summary passes whitelist checks.",
            "Do not share raw robot response, local paths, credentials, hardware transport, or control topics.",
        ]
    if pack_status.startswith("blocked"):
        return [
            "Repair the blocked execution pack before using it for a field-run checklist.",
            f"Keep all repaired materials under evidence_ref={ref}.",
            "Rerun this reconciliation gate before operator/mobile display.",
        ]
    if material_status.get("mismatch_reasons"):
        return [
            f"Rerun mismatched intake/review materials under evidence_ref={ref}.",
            "Confirm mismatch_reasons is empty before operator handoff.",
            "Keep this as software proof until real field evidence exists.",
        ]
    ready_steps = source_steps[:2] or ["Review the aligned software materials with support/operator."]
    ready_steps.extend(
        [
            f"Preserve evidence_ref={ref} across the next real route/task field run.",
            "Do not claim Nav2/fixed-route, HIL, dropoff/cancel completion, or delivery success from this gate.",
        ]
    )
    return ready_steps[:4] + [
        "Use the reconciliation artifact as a Docker/local software-proof handoff only.",
    ]


def _verdict(
    pack_source: dict[str, Any],
    intake_source: dict[str, Any],
    requested_ref: str,
    material_status: dict[str, Any],
    unsafe: bool,
) -> str:
    # verdict 优先级按“可读 -> schema -> boundary -> ref -> 安全 -> 材料 -> ready”保守判定。
    if pack_source["load_issue"] == "execution_pack_missing":
        return "blocked_missing_execution_pack"
    if intake_source["load_issue"] == "intake_missing":
        return "blocked_missing_intake"
    if pack_source["load_issue"] or intake_source["load_issue"]:
        if "bad_json" in {pack_source["load_issue"], intake_source["load_issue"]}:
            return "blocked_bad_json"
        return "blocked_bad_json"
    if "unsupported" in {pack_source["schema_status"], intake_source["schema_status"]}:
        return "blocked_unsupported_schema"
    if "unsupported" in {pack_source["boundary_status"], intake_source["boundary_status"]}:
        return "blocked_unsupported_boundary"
    if not requested_ref or not pack_source["evidence_ref"] or not intake_source["evidence_ref"]:
        return "blocked_missing_evidence_ref"
    if pack_source["evidence_ref"] != requested_ref or intake_source["evidence_ref"] != requested_ref:
        return "blocked_evidence_ref_mismatch"
    if unsafe:
        return "blocked_unsafe_summary"
    if _missing_materials(material_status):
        return "blocked_missing_materials"
    if material_status.get("mismatch_reasons"):
        return "blocked_evidence_ref_mismatch"
    if pack_source["overall_status"].startswith("blocked") or intake_source["overall_status"].startswith("blocked"):
        return "blocked_missing_materials"
    return "ready_for_route_task_field_run_reconciliation"


def _phone_summary(verdict: str, evidence_ref: str, materials_status: dict[str, Any], steps: list[str]) -> dict[str, Any]:
    # phone_safe_summary 只输出白名单摘要，不包含 raw artifact、完整路径或底层控制细节。
    return {
        "schema": RECONCILIATION_SCHEMA,
        "evidence_boundary": RECONCILIATION_BOUNDARY,
        "status": verdict,
        "reconciliation_verdict": verdict,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "materials_status": {
            "kind": materials_status.get("kind", ""),
            "missing_materials_count": materials_status.get("missing_materials_count", 0),
            "mismatch_reasons_count": materials_status.get("mismatch_reasons_count", 0),
        },
        "operator_next_steps": steps[:3],
        "not_proven": list(NOT_PROVEN),
        "ack_semantics": "reconciliation_metadata_only_not_delivery_success",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_reconciliation(execution_pack_json: str, intake_json: str, evidence_ref: str = "") -> tuple[dict[str, Any], int]:
    pack_payload, pack_issue = _load_json(execution_pack_json, "execution_pack")
    intake_payload, intake_issue = _load_json(intake_json, "intake")

    pack_source = _source_state("execution_pack", pack_payload, pack_issue)
    intake_source = _source_state("intake_or_review", intake_payload, intake_issue)
    material_status = _material_status_from_intake_or_review(intake_payload) if intake_payload else {
        "kind": "missing",
        "missing_materials": ["intake_or_review:not_loaded"],
        "mismatch_reasons": [],
        "missing_materials_count": 1,
        "mismatch_reasons_count": 0,
    }
    requested_ref = _safe_ref(evidence_ref) or _first_text(
        pack_source.get("evidence_ref"),
        intake_source.get("evidence_ref"),
        default="",
    )

    # 原文和输出摘要双层检查；source 命中敏感词时 verdict 必须 blocked。
    unsafe = bool((pack_payload and _has_forbidden_copy(pack_payload)) or (intake_payload and _has_forbidden_copy(intake_payload)))
    verdict = _verdict(pack_source, intake_source, requested_ref, material_status, unsafe)
    source_steps = _source_operator_steps(pack_payload, intake_payload) if pack_payload or intake_payload else []
    steps = _operator_steps(verdict, requested_ref, pack_source.get("overall_status", ""), material_status, source_steps)
    phone_summary = _phone_summary(verdict, requested_ref, material_status, steps)
    if _has_forbidden_copy(phone_summary):
        verdict = "blocked_unsafe_summary"
        steps = _operator_steps(verdict, requested_ref, pack_source.get("overall_status", ""), material_status, [])
        phone_summary = _phone_summary(verdict, requested_ref, material_status, steps)
    merged_not_proven = _merged_not_proven(pack_payload, intake_payload)

    artifact = {
        "schema": RECONCILIATION_SCHEMA,
        "schema_version": RECONCILIATION_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": RECONCILIATION_BOUNDARY,
        "same_evidence_ref_required": True,
        "reconciliation_verdict": verdict,
        "evidence_ref": requested_ref,
        "source_materials": {
            "execution_pack": pack_source,
            "intake_or_review": intake_source,
        },
        "materials_status": material_status,
        "operator_next_steps": steps,
        "phone_safe_summary": phone_summary,
        "not_proven": merged_not_proven,
        "non_access_scope": [
            "ros_graph",
            "nav2_runtime",
            "hardware_transport",
            "robot_base_runtime",
            "hardware_runtime",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
        ],
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    if _has_forbidden_copy(artifact):
        # 最终防线只降级状态，不试图把 unsafe artifact 伪装成 ready。
        artifact["reconciliation_verdict"] = "blocked_unsafe_summary"
        artifact["phone_safe_summary"]["status"] = "blocked_unsafe_summary"
        artifact["phone_safe_summary"]["reconciliation_verdict"] = "blocked_unsafe_summary"
    return artifact, 0


def write_reconciliation(artifact: dict[str, Any], output: str) -> None:
    # output 为空时只打印 stdout；指定路径时自动建父目录方便 /tmp 验收。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 只读 execution pack 和 intake/review JSON；--once-json 便于围栏验证直接消费。
    parser = argparse.ArgumentParser(description="Generate a route/task field-run reconciliation artifact")
    parser.add_argument("--execution-pack-json", required=True, help="route_task_field_run_execution_pack JSON path")
    parser.add_argument("--intake-json", required=True, help="route_task_field_run_intake or review JSON path")
    parser.add_argument("--output", default="", help="optional reconciliation JSON path")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for both source materials")
    parser.add_argument("--once-json", action="store_true", help="print reconciliation JSON to stdout and exit")
    args = parser.parse_args()

    artifact, exit_code = build_reconciliation(args.execution_pack_json, args.intake_json, args.evidence_ref)
    write_reconciliation(artifact, args.output)
    if args.once_json or not args.output:
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route/task field-run reconciliation: reconciliation_file:{_safe_ref(args.output)}")
        print(f"reconciliation_verdict: {artifact['reconciliation_verdict']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
