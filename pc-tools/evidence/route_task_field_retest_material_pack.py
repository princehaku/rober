#!/usr/bin/env python3
"""打包并校验 route/task field retest material directory。

该 gate 只读取 PC 侧材料目录中的八类现场复测材料摘要，生成 sanitized
artifact 与 summary，供后续 result_intake / result_reconciliation 消费。它不访问
ROS graph、Nav2 runtime、serial/UART、硬件、外部云、真实手机/browser 或真实上车
环境；即使八类材料齐全，也只能证明 Docker/local software proof。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# material pack 是 result intake/reconciliation 前的 PC 侧目录入口契约。
PACK_SCHEMA = "trashbot.route_task_field_retest_material_pack.v1"
PACK_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_material_pack_summary.v1"
SCHEMA_VERSION = 1
PACK_BOUNDARY = "software_proof_docker_route_task_field_retest_material_pack_gate"

# rg 验收会检查这些 literal；也作为人工复盘时的证据边界提示。
BOUNDARY_NOTE = (
    "software_proof_docker only; not_proven; delivery_success=false; "
    "primary_actions_enabled=false; fixture_materials_do_not_equal_field_pass=true"
)

# 八类材料是下游 result_intake / result_reconciliation 的固定清单。
REQUIRED_MATERIALS = (
    "nav2_or_fixed_route_runtime_log",
    "route_completion_signal",
    "task_record",
    "door_state",
    "target_floor_confirmation",
    "human_assistance_note",
    "dropoff_or_cancel_completion",
    "delivery_result",
)

# 每类材料允许 JSON 或文本文件；别名只影响发现，不进入 summary 的 raw path。
MATERIAL_ALIASES: dict[str, tuple[str, ...]] = {
    "nav2_or_fixed_route_runtime_log": (
        "nav2_or_fixed_route_runtime_log.json",
        "nav2_or_fixed_route_runtime_log.log",
        "nav2_or_fixed_route_runtime_log.txt",
        "runtime_log.json",
        "runtime_log.log",
    ),
    "route_completion_signal": ("route_completion_signal.json", "completion_signal.json"),
    "task_record": ("task_record.json",),
    "door_state": ("door_state.json",),
    "target_floor_confirmation": ("target_floor_confirmation.json", "floor_confirmation.json"),
    "human_assistance_note": ("human_assistance_note.json", "human_assistance_note.md", "operator_note.md"),
    "dropoff_or_cancel_completion": (
        "dropoff_or_cancel_completion.json",
        "dropoff_completion.json",
        "cancel_completion.json",
    ),
    "delivery_result": ("delivery_result.json", "delivery_result.md"),
}

# not_proven 固定列出真实能力缺口，避免材料目录被误解为现场通过。
NOT_PROVEN = (
    "real_nav2_fixed_route_runtime",
    "real_route_completion_pass",
    "real_task_record_runtime",
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_field_note",
    "real_dropoff_or_cancel_completion",
    "real_delivery_result_reviewed_success",
    "real_delivery_success",
    "real_hil_pass",
    "real_phone_device_or_browser",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# 输入命中这些字样时必须 fail closed，不能进入 phone/diagnostics 消费面。
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

# 成功文案必须阻断；本 gate 只能说材料可复账，不能说 delivery/field 已成功。
SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfield\s+pass(ed)?\b"),
    re.compile(r"(?i)\bhil\s+pass(ed)?\b"),
    re.compile(r"(?i)\bnav2\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfixed[-_ ]route\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bdropoff\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bcancel\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
)

# 绝对路径不能进入 summary，也不允许作为材料正文的一部分。
RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

# placeholder 只能算 rejected，不允许被当成现场回填材料。
PLACEHOLDER_PATTERNS = (
    re.compile(r"(?i)\b(tbd|todo|placeholder|example|sample|dummy|not_collected|fill me)\b"),
    re.compile(r"^<[^>]+>$"),
)

# 输出前统一脱敏；artifact/summary 不回显 raw 材料正文。
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
    (re.compile(r"(?i)\bWAVE\s+ROVER\b"), "[REDACTED_PLATFORM]"),
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
    (re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"), r"\1[REDACTED_PATH]"),
    (re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"), "[REDACTED_PATH]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)complete artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)raw robot response"), "[REDACTED_RAW_RESPONSE]"),
)


def _utc_now() -> str:
    # UTC 时间让不同 PC/Docker 产物可以按时间线审计。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有输出文本走同一脱敏链，避免新增字段绕过安全边界。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref 可能来自路径形态输入；输出只保留 basename 防止泄漏本机路径。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 递归脱敏是最终防线，artifact 和 summary 都不复制敏感原文。
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
    # 安全扫描使用稳定 JSON 文本，覆盖键名和值。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _has_forbidden_copy(value: Any) -> bool:
    # 禁词必须在脱敏前检查，命中后 fail closed。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _has_raw_path_copy(value: Any) -> bool:
    # 现场材料包只允许相对文件名；正文里的绝对路径会泄漏 PC 环境。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _has_success_or_control_claim(value: Any) -> bool:
    # 布尔字段和自由文本都检查，防止材料包越界启用动作或宣称成功。
    if isinstance(value, dict):
        if value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _read_material(path: Path) -> tuple[str, Any, str]:
    # 坏 JSON 不抛异常；转成 rejected reason，便于现场修复单个材料。
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return "", {}, "read_error"
    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return text, {}, "bad_json"
        if not isinstance(payload, dict):
            return text, payload, "json_not_object"
        return text, payload, ""
    return text, {"note": text}, ""


def _first_text(*values: Any, default: str = "") -> str:
    # 兼容现场手写 JSON 的不同字段名，取第一个非空值。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _material_ref(payload: Any, text: str, fallback_ref: str) -> str:
    # JSON 优先读 evidence_ref；Markdown/log 只解析固定 evidence_ref 行。
    if isinstance(payload, dict):
        return _safe_ref(_first_text(payload.get("evidence_ref"), payload.get("ref"), default=fallback_ref))
    match = re.search(r"(?im)^\s*-?\s*evidence_ref\s*:\s*(.+?)\s*$", text)
    return _safe_ref(match.group(1).strip()) if match else fallback_ref


def _material_status(payload: Any) -> str:
    # status 只用于判断是否 placeholder，不当作现场成功结论。
    if isinstance(payload, dict):
        return _safe_text(
            _first_text(
                payload.get("status"),
                payload.get("material_status"),
                payload.get("collection_status"),
                payload.get("state"),
                default="provided",
            )
        )
    return "provided"


def _placeholder_material(text: str, payload: Any, read_issue: str) -> bool:
    # 空文件、模板词和 placeholder 状态都不能算有效现场材料。
    if read_issue:
        return False
    encoded = _encoded(payload) + "\n" + text
    if not text.strip():
        return True
    if any(pattern.search(encoded.strip()) for pattern in PLACEHOLDER_PATTERNS):
        return True
    status = _material_status(payload).lower().replace("-", "_")
    return status in {"placeholder", "not_collected", "missing", "required_not_collected"}


def _find_material_file(material_dir: Path, material_name: str) -> Path | None:
    # 只按白名单文件名查找，避免任意目录文件被包装进 artifact。
    for alias in MATERIAL_ALIASES[material_name]:
        candidate = material_dir / alias
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _metadata_summary(payload: Any, text: str) -> dict[str, Any]:
    # 输出只保留短状态字段，不复制 raw log / note / ROS topic / 文件路径。
    if not isinstance(payload, dict):
        return {"summary_status": "text_material_detected", "text_length": len(text)}
    metadata: dict[str, Any] = {}
    for key in (
        "schema",
        "status",
        "material_status",
        "collection_status",
        "state",
        "review_note",
        "failure_reason",
        "observer_note",
        "source",
    ):
        if key in payload:
            metadata[key] = _safe_text(payload[key])
    return metadata


def _scan_material(material_dir: Path, material_name: str, expected_ref: str) -> tuple[dict[str, Any], list[str]]:
    # 单类材料扫描只返回状态和拒绝原因，绝不把正文写入输出。
    path = _find_material_file(material_dir, material_name)
    if path is None:
        return {
            "name": material_name,
            "status": "missing",
            "accepted": False,
            "same_evidence_ref_required": True,
            "rejected_reasons": ["missing_material"],
        }, ["missing_material"]
    text, payload, read_issue = _read_material(path)
    evidence_ref = _material_ref(payload, text, expected_ref)
    reasons: list[str] = []
    if read_issue:
        reasons.append(read_issue)
    if _placeholder_material(text, payload, read_issue):
        reasons.append("placeholder_only")
    if expected_ref and evidence_ref and evidence_ref != expected_ref:
        reasons.append("evidence_ref_mismatch")
    if not evidence_ref:
        reasons.append("missing_evidence_ref")
    if _has_forbidden_copy(text) or _has_forbidden_copy(payload):
        reasons.append("unsafe_copy")
    if _has_raw_path_copy(text) or _has_raw_path_copy(payload):
        reasons.append("raw_path_copy")
    if _has_success_or_control_claim(text) or _has_success_or_control_claim(payload):
        reasons.append("success_or_control_claim")
    entry = {
        "name": material_name,
        "status": "accepted" if not reasons else "rejected",
        "accepted": not reasons,
        "file_ref": f"file:{path.name}",
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "metadata": _metadata_summary(payload, text),
        "rejected_reasons": reasons,
    }
    return entry, reasons


def _source_dir_status(material_dir: str) -> tuple[Path | None, dict[str, Any]]:
    # CLI 必须显式收到 material-dir；缺目录不能猜测现场材料存在。
    if not material_dir:
        return None, {"directory_status": "missing_argument", "material_dir_ref": "", "load_issue": "material_dir_not_provided"}
    path = Path(material_dir).expanduser()
    if not path.exists() or not path.is_dir():
        return None, {
            "directory_status": "missing",
            "material_dir_ref": _safe_ref(str(path)),
            "load_issue": "material_dir_missing",
        }
    return path, {"directory_status": "scanned", "material_dir_ref": _safe_ref(str(path)), "load_issue": ""}


def _pack_status(dir_status: dict[str, Any], missing: list[str], rejected: dict[str, list[str]], mismatched: list[str]) -> str:
    # fail closed 优先级固定，便于 Robot/mobile 只读消费同一状态语义。
    if dir_status["load_issue"]:
        return "blocked_missing_material_dir"
    if any("unsafe_copy" in reasons or "raw_path_copy" in reasons for reasons in rejected.values()):
        return "blocked_unsafe_material_copy"
    if any("success_or_control_claim" in reasons for reasons in rejected.values()):
        return "blocked_success_or_control_claim"
    if mismatched:
        return "blocked_same_evidence_ref_mismatch"
    if missing:
        return "blocked_missing_materials"
    if any("placeholder_only" in reasons for reasons in rejected.values()):
        return "blocked_placeholder_only_materials"
    if rejected:
        return "blocked_rejected_materials"
    return "ready_for_field_retest_material_pack_not_proven"


def _operator_next_steps(status: str, evidence_ref: str, missing: list[str], rejected: dict[str, list[str]]) -> list[str]:
    # next steps 只要求补齐和重跑 PC gate，不允许引导现场成功或启用动作。
    ref = evidence_ref or "<same_evidence_ref>"
    if status == "ready_for_field_retest_material_pack_not_proven":
        return [
            f"Run route_task_field_retest_result_intake.py with this material pack summary for evidence_ref={ref}.",
            "Then run route_task_field_retest_result_reconciliation.py before any terminal review decision.",
            "Keep delivery_success=false and primary_actions_enabled=false until real review closes.",
        ]
    steps = [f"Keep every material on evidence_ref={ref} before rerun."]
    if missing:
        steps.append("Collect missing retest materials: " + ", ".join(missing))
    if rejected:
        rejected_names = ", ".join(f"{name}({'+'.join(reasons[:2])})" for name, reasons in rejected.items())
        steps.append("Repair rejected retest materials: " + rejected_names)
    steps.append("Rerun route_task_field_retest_material_pack.py --material-dir <material_dir> --once-json.")
    return [_safe_text(step) for step in steps[:5]]


def _material_completeness(materials: list[dict[str, Any]], missing: list[str]) -> dict[str, Any]:
    # completeness 是目录材料状态，不是 field pass 或 delivery success。
    accepted = [entry["name"] for entry in materials if entry["accepted"]]
    rejected = [entry["name"] for entry in materials if entry["status"] == "rejected"]
    return {
        "required_count": len(REQUIRED_MATERIALS),
        "accepted_count": len(accepted),
        "accepted_materials": accepted,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "is_complete": len(accepted) == len(REQUIRED_MATERIALS),
    }


def _summary_payload(
    status: str,
    evidence_ref: str,
    materials: list[dict[str, Any]],
    completeness: dict[str, Any],
    rejected: dict[str, list[str]],
    operator_next_steps: list[str],
) -> dict[str, Any]:
    # summary 是下游首选消费面，字段保持白名单且不包含完整 artifact。
    safe_materials = [
        {
            "name": entry["name"],
            "status": entry["status"],
            "accepted": entry["accepted"],
            "evidence_ref": entry.get("evidence_ref", ""),
            "rejected_reasons": entry.get("rejected_reasons", []),
        }
        for entry in materials
    ]
    return {
        "schema": PACK_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": PACK_BOUNDARY,
        "boundary": PACK_BOUNDARY,
        "status": status,
        "material_pack_verdict": status,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "required_materials": list(REQUIRED_MATERIALS),
        "materials": safe_materials,
        "material_completeness": completeness,
        "missing_materials": completeness["missing_materials"],
        "rejected_materials": rejected,
        "operator_next_steps": operator_next_steps,
        "safe_copy": {
            "schema": f"{PACK_SUMMARY_SCHEMA}.safe_copy",
            "status": status,
            "evidence_boundary": PACK_BOUNDARY,
            "evidence_ref": evidence_ref,
            "not_proven": "not_proven",
            "delivery_success": False,
            "primary_actions_enabled": False,
        },
        "not_proven": list(NOT_PROVEN),
        "primary_actions_enabled": False,
        "delivery_success": False,
    }


def build_route_task_field_retest_material_pack(
    material_dir: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    # 主构建函数保持 dependency-free，便于 unittest 和 CLI 共用同一逻辑。
    requested_ref = _safe_ref(evidence_ref)
    material_path, dir_status = _source_dir_status(material_dir)
    materials: list[dict[str, Any]] = []
    rejected: dict[str, list[str]] = {}
    missing: list[str] = []
    mismatched: list[str] = []
    if material_path is None:
        for name in REQUIRED_MATERIALS:
            materials.append({"name": name, "status": "missing", "accepted": False, "rejected_reasons": ["missing_material"]})
            missing.append(name)
    else:
        for name in REQUIRED_MATERIALS:
            entry, reasons = _scan_material(material_path, name, requested_ref)
            materials.append(entry)
            if "missing_material" in reasons:
                missing.append(name)
            elif reasons:
                rejected[name] = reasons
            if "evidence_ref_mismatch" in reasons:
                mismatched.append(name)
            if not requested_ref and entry.get("evidence_ref"):
                requested_ref = entry["evidence_ref"]
    completeness = _material_completeness(materials, missing)
    status = _pack_status(dir_status, missing, rejected, mismatched)
    next_steps = _operator_next_steps(status, requested_ref, missing, rejected)
    summary = _summary_payload(status, requested_ref, materials, completeness, rejected, next_steps)
    artifact = {
        "schema": PACK_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": PACK_BOUNDARY,
        "boundary": PACK_BOUNDARY,
        "same_evidence_ref_required": True,
        "evidence_ref": requested_ref,
        "material_pack_verdict": status,
        "source_material_dir": dir_status,
        "material_manifest": materials,
        "material_pack_summary": summary,
        "operator_next_steps": next_steps,
        "result_intake_hint": {
            "schema": "trashbot.route_task_field_retest_result_intake.v1",
            "command": "run route_task_field_retest_result_intake.py with this material pack summary",
        },
        "result_reconciliation_hint": {
            "schema": "trashbot.route_task_field_retest_result_reconciliation.v1",
            "command": "run route_task_field_retest_result_reconciliation.py after intake",
        },
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "ros_graph",
            "nav2_runtime",
            "hardware_transport",
            "hardware",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
            "phone_device_or_browser",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "primary_actions_enabled": False,
        "delivery_success": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _has_forbidden_copy(summary) or _has_raw_path_copy(summary) or _has_success_or_control_claim(summary):
        # 最终防线：summary 仍不安全时只保留 blocked 状态，不输出原始内容。
        summary["status"] = "blocked_unsafe_summary"
        summary["material_pack_verdict"] = "blocked_unsafe_summary"
        artifact["material_pack_verdict"] = "blocked_unsafe_summary"
        artifact["material_pack_summary"] = summary
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # output 为空时只打 stdout；指定路径时创建父目录方便 sprint evidence 归档。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 只读 PC 材料目录；--once-json 便于围栏验证和 downstream fixture 消费。
    parser = argparse.ArgumentParser(description="Build sanitized route/task field retest material pack artifact")
    parser.add_argument("--material-dir", required=True, help="directory containing eight route/task field retest materials")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for every material")
    parser.add_argument("--output", default="", help="optional material pack artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional material pack summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print material pack artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_material_pack(args.material_dir, args.evidence_ref)
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not args.output:
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route_task_field_retest_material_pack: artifact_file:{_safe_ref(args.output)}")
        print(f"material_pack_verdict: {artifact['material_pack_verdict']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
