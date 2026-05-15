#!/usr/bin/env python3
"""校验 route/task field-run material bundle 目录是否具备现场回填材料。

该 gate 只读取上一轮 material bundle JSON 和 PC 侧材料目录。它不访问 ROS graph、
Nav2 runtime、serial/UART、硬件、外部云、OSS/CDN、DB/queue 或 4G；所有输出
都保持 Docker/local software proof 边界。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# validation 是 material bundle 之后的现场材料状态契约，供 Robot/mobile 只读消费。
VALIDATION_SCHEMA = "trashbot.route_task_field_run_material_validation.v1"
VALIDATION_SUMMARY_SCHEMA = "trashbot.route_task_field_run_material_validation_summary.v1"
VALIDATION_SCHEMA_VERSION = 1
VALIDATION_BOUNDARY = "software_proof_docker_route_task_field_run_material_validation_gate"
BUNDLE_SCHEMA = "trashbot.route_task_field_run_material_bundle.v1"
BUNDLE_SUMMARY_SCHEMA = "trashbot.route_task_field_run_material_bundle_summary.v1"
BUNDLE_BOUNDARY = "software_proof_docker_route_task_field_run_material_bundle_gate"

# material bundle 生成的固定模板名也是 validation 的最小材料清单。
MATERIAL_SPECS = (
    {"name": "route_status_template.json", "category": "route", "kind": "json"},
    {"name": "task_record_template.json", "category": "task", "kind": "json"},
    {"name": "completion_material_template.json", "category": "completion", "kind": "json"},
    {"name": "operator_notes.md", "category": "operator_notes", "kind": "text"},
    {"name": "robot_diagnostics_summary_template.json", "category": "diagnostics", "kind": "json"},
    {"name": "mobile_readonly_summary_template.json", "category": "mobile_summary", "kind": "json"},
)

# not_proven 固定列出真实能力缺口，防止材料校验被误写成上车成功。
NOT_PROVEN = (
    "real_nav2_fixed_route_run",
    "real_route_capture",
    "real_robot_motion",
    "real_uart_feedback",
    "real_hil_pass",
    "real_dropoff_completion",
    "real_cancel_completion",
    "delivery_success",
    "real_phone_device_or_browser",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# rg 验收会检查 delivery_success=false；这里同时作为人工复盘边界说明。
BOUNDARY_NOTE = (
    "Docker/local software proof only; delivery_success=false; "
    "primary_actions_enabled=false; material_status_not_real_field_run=true"
)

# 这些词一旦出现在输入材料中，说明现场材料不适合进入 phone/diagnostics 摘要。
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

# 输出前统一脱敏；validation artifact 不复制 raw 材料正文。
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
    # UTC 时间让不同 PC 生成的 validation artifact 可按时间排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有输出文本走同一脱敏链，避免新增字段绕过安全边界。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # 对外只暴露 basename，避免泄露本机绝对路径。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 递归脱敏保证 artifact、summary 和 next steps 都 phone-safe。
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
    # forbidden 检查使用稳定 JSON 文本；不可编码对象退回脱敏字符串。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # validation 是对外状态入口，命中敏感词必须 fail closed。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 坏文件输出 blocked artifact，而不是让 CLI 抛未处理异常。
    if not path:
        return {}, "material_bundle_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "material_bundle_missing"
    except json.JSONDecodeError:
        return {}, "material_bundle_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "material_bundle_read_error"
    if not isinstance(payload, dict):
        return {}, "material_bundle_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只把 object 当稳定接口，避免 list/string raw payload 泄入 summary。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _source_bundle_status(bundle: dict[str, Any], load_issue: str, bundle_path: str) -> dict[str, Any]:
    # source_bundle 只暴露支持判定，不复制 material bundle 全量正文。
    schema = _safe_text(bundle.get("schema", "")) if bundle else ""
    boundary = _safe_text(bundle.get("evidence_boundary", "")) if bundle else ""
    summary = _dict(bundle, "material_bundle_summary")
    if load_issue:
        schema_status = "not_loaded"
    elif schema == BUNDLE_SCHEMA and boundary == BUNDLE_BOUNDARY:
        schema_status = "supported"
    else:
        schema_status = "unsupported"
    return {
        "ref": _safe_ref(bundle_path),
        "load_status": "blocked" if load_issue else "loaded",
        "load_issue": load_issue,
        "schema": schema,
        "schema_status": schema_status,
        "evidence_boundary": boundary,
        "material_bundle_verdict": _safe_text(bundle.get("material_bundle_verdict", "")) if bundle else "",
        "summary_schema": _safe_text(summary.get("schema", "")),
        "summary_schema_supported": summary.get("schema", "") in ("", BUNDLE_SUMMARY_SCHEMA),
        "evidence_ref": _extract_bundle_ref(bundle) if bundle else "",
    }


def _extract_bundle_ref(bundle: dict[str, Any]) -> str:
    # bundle 顶层和 summary 都可能承载同一 evidence_ref，validation 需要兼容两者。
    summary = _dict(bundle, "material_bundle_summary")
    for value in (bundle.get("evidence_ref"), summary.get("evidence_ref")):
        ref = _safe_ref(value)
        if ref:
            return ref
    return ""


def _refs_from_bundle(bundle: dict[str, Any]) -> dict[str, str]:
    # mismatch 诊断保留来源标签，便于现场只修错配文件。
    summary = _dict(bundle, "material_bundle_summary")
    return {
        "material_bundle": _safe_ref(bundle.get("evidence_ref", "")),
        "material_bundle_summary": _safe_ref(summary.get("evidence_ref", "")),
    }


def _any_true_key(value: Any, key: str) -> bool:
    # 递归检查让 nested diagnostics/mobile 越界声明也会 fail closed。
    if isinstance(value, dict):
        return any((k == key and v is True) or _any_true_key(v, key) for k, v in value.items())
    if isinstance(value, list):
        return any(_any_true_key(item, key) for item in value)
    return False


def _looks_like_unfilled_json_template(payload: dict[str, Any]) -> bool:
    # material bundle 模板的 schema/空字段是强占位信号，不能当现场材料。
    schema = _safe_text(payload.get("schema", ""))
    if schema.endswith("_material_template.v1"):
        return True
    if payload.get("filled_by", None) == "" and payload.get("filled_at", None) == "":
        return True
    if payload.get("summary_status") == "placeholder":
        return True
    return False


def _text_note_ref(text: str) -> str:
    # operator notes 是 Markdown，只解析固定 evidence_ref 行，不依赖自由文本格式。
    match = re.search(r"(?im)^\s*-?\s*evidence_ref\s*:\s*(.+?)\s*$", text)
    return _safe_ref(match.group(1).strip()) if match else ""


def _looks_like_unfilled_notes(text: str) -> bool:
    # 默认 notes 模板有空 operator/observed 字段；这些空值表示未回填。
    lowered = text.lower()
    if "route task field run operator notes" not in lowered:
        return False
    empty_markers = ("- operator:", "- observed route/task state:", "- failure or recovery reason:", "- materials collected:")
    return any(marker in lowered for marker in empty_markers)


def _material_json_status(path: Path, category: str, expected_ref: str) -> tuple[dict[str, Any], list[str]]:
    # JSON 材料只返回状态和白名单字段，不把现场正文带入 artifact。
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"status": "bad_json", "ref": _safe_ref(str(path))}, []
    except (OSError, UnicodeDecodeError):
        return {"status": "read_error", "ref": _safe_ref(str(path))}, []
    if not isinstance(payload, dict):
        return {"status": "not_object", "ref": _safe_ref(str(path))}, []
    evidence_ref = _safe_ref(payload.get("evidence_ref", ""))
    mismatches = []
    if expected_ref and evidence_ref and evidence_ref != expected_ref:
        mismatches.append(f"{category}:evidence_ref_mismatch:{evidence_ref}!={expected_ref}")
    status = "placeholder_template" if _looks_like_unfilled_json_template(payload) else "filled_material"
    return {
        "status": status,
        "ref": _safe_ref(str(path)),
        "category": category,
        "schema": _safe_text(payload.get("schema", "")),
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "primary_actions_enabled": bool(payload.get("primary_actions_enabled", False)),
        "delivery_success": bool(payload.get("delivery_success", False)),
    }, mismatches


def _material_text_status(path: Path, category: str, expected_ref: str) -> tuple[dict[str, Any], list[str]]:
    # Markdown notes 只判断是否回填和是否同 ref，不输出正文。
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {"status": "read_error", "ref": _safe_ref(str(path))}, []
    evidence_ref = _text_note_ref(text)
    mismatches = []
    if expected_ref and evidence_ref and evidence_ref != expected_ref:
        mismatches.append(f"{category}:evidence_ref_mismatch:{evidence_ref}!={expected_ref}")
    status = "placeholder_template" if _looks_like_unfilled_notes(text) else "filled_material"
    return {
        "status": status,
        "ref": _safe_ref(str(path)),
        "category": category,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "primary_actions_enabled": False,
        "delivery_success": False,
    }, mismatches


def _scan_material_file(material_dir: Path, spec: dict[str, str], expected_ref: str) -> tuple[dict[str, Any], list[str], bool]:
    # 单文件扫描返回状态、ref mismatch 和 unsafe 判定，供总 verdict 聚合。
    target = material_dir / spec["name"]
    if not target.exists():
        return {
            "name": spec["name"],
            "category": spec["category"],
            "status": "missing",
            "same_evidence_ref_required": True,
        }, [], False
    try:
        raw_text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        raw_text = ""
    unsafe = _has_forbidden_copy(raw_text)
    if spec["kind"] == "json":
        entry, mismatches = _material_json_status(target, spec["category"], expected_ref)
    else:
        entry, mismatches = _material_text_status(target, spec["category"], expected_ref)
    entry["name"] = spec["name"]
    entry["unsafe_copy_detected"] = unsafe
    return entry, mismatches, unsafe


def _scan_material_dir(material_dir: str, expected_ref: str) -> tuple[dict[str, Any], list[str], bool, bool, bool]:
    # validation 要求显式 material-dir；没有目录时不能假装材料齐全。
    if not material_dir:
        entries = [
            {"name": spec["name"], "category": spec["category"], "status": "not_requested", "same_evidence_ref_required": True}
            for spec in MATERIAL_SPECS
        ]
        return {
            "material_dir_ref": "",
            "directory_status": "not_requested",
            "material_files": entries,
            "same_evidence_ref_required": True,
        }, [], False, True, False
    path = Path(material_dir).expanduser()
    if not path.exists() or not path.is_dir():
        entries = [
            {"name": spec["name"], "category": spec["category"], "status": "missing", "same_evidence_ref_required": True}
            for spec in MATERIAL_SPECS
        ]
        return {
            "material_dir_ref": _safe_ref(str(path)),
            "directory_status": "missing",
            "material_files": entries,
            "same_evidence_ref_required": True,
        }, [], False, True, False
    entries: list[dict[str, Any]] = []
    mismatches: list[str] = []
    unsafe = False
    has_missing = False
    has_placeholder = False
    for spec in MATERIAL_SPECS:
        entry, file_mismatches, file_unsafe = _scan_material_file(path, spec, expected_ref)
        entries.append(entry)
        mismatches.extend(file_mismatches)
        unsafe = unsafe or file_unsafe
        has_missing = has_missing or entry["status"] in {"missing", "bad_json", "not_object", "read_error"}
        has_placeholder = has_placeholder or entry["status"] == "placeholder_template"
    return {
        "material_dir_ref": _safe_ref(str(path)),
        "directory_status": "scanned",
        "material_files": entries,
        "same_evidence_ref_required": True,
    }, mismatches, unsafe, has_missing, has_placeholder


def _bundle_mismatches(bundle: dict[str, Any], expected_ref: str) -> list[str]:
    # bundle 顶层与 summary 必须共享 same evidence_ref，防止拼接不同 run。
    mismatches: list[str] = []
    refs = _refs_from_bundle(bundle)
    loaded_refs = {ref for ref in refs.values() if ref}
    for label, ref in refs.items():
        if expected_ref and ref and ref != expected_ref:
            mismatches.append(f"{label}:evidence_ref_mismatch:{ref}!={expected_ref}")
    if len(loaded_refs) > 1:
        mismatches.append("material_bundle:evidence_ref_fields_do_not_share_same_ref")
    return mismatches


def _validation_verdict(
    source: dict[str, Any],
    bundle: dict[str, Any],
    mismatches: list[str],
    unsafe: bool,
    has_missing: bool,
    has_placeholder: bool,
) -> str:
    # verdict 优先级从输入可读性到现场材料状态，任何越界都 fail closed。
    if source["load_issue"] in {"material_bundle_bad_json", "material_bundle_not_object", "material_bundle_read_error"}:
        return "blocked_bad_material_bundle"
    if source["load_status"] != "loaded":
        return "blocked_missing_material_bundle"
    if source["schema_status"] == "unsupported" or not source["summary_schema_supported"]:
        return "blocked_unsupported_material_bundle"
    if mismatches:
        return "blocked_mismatch_evidence_ref"
    if unsafe or _has_forbidden_copy(bundle):
        return "blocked_unsafe_summary"
    if _any_true_key(bundle, "delivery_success"):
        return "blocked_delivery_success_claim"
    if _any_true_key(bundle, "primary_actions_enabled"):
        return "blocked_primary_actions_claim"
    if source["material_bundle_verdict"].startswith("blocked"):
        return "blocked_source_material_bundle"
    if has_missing:
        return "blocked_missing_materials"
    if has_placeholder:
        return "blocked_placeholder_materials"
    return "field_run_material_validation_ready_not_proven"


def _operator_next_steps(verdict: str, evidence_ref: str, material_status: dict[str, Any], mismatches: list[str]) -> list[str]:
    # next steps 只给现场补材料方向，不给硬件/控制细节。
    ref = evidence_ref or "<same_evidence_ref>"
    if verdict == "field_run_material_validation_ready_not_proven":
        steps = [
            f"Keep the validated material directory under evidence_ref={ref}.",
            "Run intake/review gates before any route/task completion or delivery claim.",
        ]
    elif verdict == "blocked_placeholder_materials":
        placeholders = [entry["name"] for entry in material_status["material_files"] if entry["status"] == "placeholder_template"]
        steps = [
            f"Replace or fill placeholder material files for evidence_ref={ref}.",
            f"Placeholder files: {', '.join(placeholders[:4])}",
        ]
    elif verdict == "blocked_missing_materials":
        missing = [entry["name"] for entry in material_status["material_files"] if entry["status"] in {"missing", "bad_json", "not_object", "read_error"}]
        steps = [
            f"Collect or repair missing material files for evidence_ref={ref}.",
            f"Missing or invalid files: {', '.join(missing[:4])}",
        ]
    elif verdict == "blocked_mismatch_evidence_ref":
        steps = [
            f"Regenerate or rename materials so every file uses evidence_ref={ref}.",
            "Do not combine route/task files from different field runs.",
        ]
    else:
        steps = [
            "Regenerate a supported material bundle and rerun validation.",
            f"Keep delivery_success=false and same evidence_ref={ref}.",
        ]
    if mismatches:
        steps.append(f"Evidence mismatch: {', '.join(mismatches[:3])}")
    return [_safe_text(step) for step in steps[:5]]


def _validation_summary(
    verdict: str,
    evidence_ref: str,
    material_status: dict[str, Any],
    next_steps: list[str],
    mismatches: list[str],
) -> dict[str, Any]:
    # summary 是 Robot/Full-stack 消费面，只暴露聚合状态和安全文件状态。
    return {
        "schema": VALIDATION_SUMMARY_SCHEMA,
        "schema_version": VALIDATION_SCHEMA_VERSION,
        "evidence_boundary": VALIDATION_BOUNDARY,
        "status": verdict,
        "material_validation_verdict": verdict,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "material_dir_ref": material_status["material_dir_ref"],
        "material_files": material_status["material_files"],
        "missing_materials": [
            entry["name"]
            for entry in material_status["material_files"]
            if entry["status"] in {"missing", "bad_json", "not_object", "read_error"}
        ],
        "placeholder_materials": [
            entry["name"] for entry in material_status["material_files"] if entry["status"] == "placeholder_template"
        ],
        "mismatch_reasons": mismatches[:10],
        "operator_next_steps": next_steps[:5],
        "not_proven": list(NOT_PROVEN),
        "primary_actions_enabled": False,
        "delivery_success": False,
    }


def build_material_validation(
    material_bundle_json: str,
    material_dir: str = "",
    evidence_ref: str = "",
) -> tuple[dict[str, Any], int]:
    bundle, load_issue = _load_json(material_bundle_json)
    source = _source_bundle_status(bundle, load_issue, material_bundle_json)
    requested_ref = _safe_ref(evidence_ref) or source.get("evidence_ref", "")
    material_status, material_mismatches, material_unsafe, has_missing, has_placeholder = _scan_material_dir(
        material_dir, requested_ref
    )
    mismatches = (_bundle_mismatches(bundle, requested_ref) if bundle else []) + material_mismatches
    unsafe = material_unsafe
    verdict = _validation_verdict(source, bundle, mismatches, unsafe, has_missing, has_placeholder)
    next_steps = _operator_next_steps(verdict, requested_ref, material_status, mismatches)
    summary = _validation_summary(verdict, requested_ref, material_status, next_steps, mismatches)
    artifact = {
        "schema": VALIDATION_SCHEMA,
        "schema_version": VALIDATION_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": VALIDATION_BOUNDARY,
        "same_evidence_ref_required": True,
        "evidence_ref": requested_ref,
        "material_validation_verdict": verdict,
        "source_material_bundle": source,
        "material_directory_status": material_status,
        "material_validation_summary": summary,
        "operator_next_steps": next_steps,
        "mismatch_reasons": mismatches,
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
        ],
        "boundary_note": BOUNDARY_NOTE,
        "primary_actions_enabled": False,
        "delivery_success": False,
    }
    artifact = _safe_value(artifact)
    if _has_forbidden_copy(artifact):
        # 最终防线：输出仍命中敏感词时降级，但不抛 raw 内容。
        artifact["material_validation_verdict"] = "blocked_unsafe_summary"
        artifact["material_validation_summary"]["status"] = "blocked_unsafe_summary"
        artifact["material_validation_summary"]["material_validation_verdict"] = "blocked_unsafe_summary"
    return artifact, 0


def write_material_validation(artifact: dict[str, Any], output: str) -> None:
    # output 为空时只打 stdout；指定路径时创建父目录便于 sprint 证据归档。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 只读 bundle 和 PC 目录；不会触发机器人动作或外部网络访问。
    parser = argparse.ArgumentParser(description="Validate route/task field-run material directory status")
    parser.add_argument("--material-bundle-json", required=True, help="route_task_field_run_material_bundle JSON path")
    parser.add_argument("--material-dir", required=True, help="material directory created from the material bundle")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for validation")
    parser.add_argument("--output", default="", help="optional material validation JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print material validation JSON to stdout and exit")
    args = parser.parse_args()

    artifact, exit_code = build_material_validation(args.material_bundle_json, args.material_dir, args.evidence_ref)
    write_material_validation(artifact, args.output)
    if args.once_json or not args.output:
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route/task field-run material validation: validation_file:{_safe_ref(args.output)}")
        print(f"material_validation_verdict: {artifact['material_validation_verdict']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
