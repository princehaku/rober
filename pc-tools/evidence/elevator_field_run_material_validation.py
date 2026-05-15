#!/usr/bin/env python3
"""校验 elevator assisted delivery 现场材料目录是否具备复盘条件。

该 gate 只读取 PC/Docker 本地材料目录，不访问 ROS graph、Nav2 runtime、
serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue 或 4G。
输出只能作为 Docker/local software proof，不能写成 delivery success。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# validation schema 是 Robot diagnostics/mobile 后续只读消费的稳定契约。
VALIDATION_SCHEMA = "trashbot.elevator_field_run_material_validation.v1"
VALIDATION_SUMMARY_SCHEMA = "trashbot.elevator_field_run_material_validation_summary.v1"
VALIDATION_SCHEMA_VERSION = 1
VALIDATION_BOUNDARY = "software_proof_docker_elevator_field_material_validation_gate"

# 电梯现场材料必须覆盖门、楼层、人协助、路线运行、任务、完成和安全摘要。
MATERIAL_SPECS = (
    {"name": "door_state.json", "category": "door_state", "kind": "json"},
    {"name": "target_floor_confirmation.json", "category": "target_floor_confirmation", "kind": "json"},
    {"name": "human_assistance_operator_note.md", "category": "human_assistance", "kind": "text"},
    {"name": "nav2_fixed_route_runtime_log.json", "category": "nav2_fixed_route_runtime", "kind": "json"},
    {"name": "task_record.json", "category": "task_record", "kind": "json"},
    {"name": "completion_signal.json", "category": "completion_signal", "kind": "json"},
    {"name": "diagnostics_mobile_safe_summary.json", "category": "diagnostics_mobile_safe_summary", "kind": "json"},
)

# not_proven 明确列出这轮没有证明的真实能力，防止材料 gate 被误读。
NOT_PROVEN = (
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance现场记录",
    "real_nav2_fixed_route_run",
    "real_robot_motion",
    "real_wave_rover_or_uart_feedback",
    "real_hil_pass",
    "real_dropoff_completion",
    "real_cancel_completion",
    "delivery_success",
    "real_phone_device_or_browser",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# 验收命令会检索这两个 fail-closed 字符串；也作为人工复盘边界。
BOUNDARY_NOTE = (
    "Docker/local software proof only; delivery_success=false; "
    "primary_actions_enabled=false; elevator_field_material_status_not_real_delivery=true"
)

# 这些词不允许进入 diagnostics/mobile safe summary 或最终 artifact。
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

# 输出前统一做脱敏，最终 artifact 不复制 raw 现场材料正文。
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
    # UTC 时间方便不同 PC 生成的材料按时间排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有对外文本都走同一脱敏链，避免新字段绕过。
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
    # 命中敏感词代表现场材料不适合进入 phone/diagnostics 摘要。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _any_true_key(value: Any, key: str) -> bool:
    # 嵌套字段也可能越界声明成功或放行动作，必须递归检查。
    if isinstance(value, dict):
        return any((k == key and v is True) or _any_true_key(v, key) for k, v in value.items())
    if isinstance(value, list):
        return any(_any_true_key(item, key) for item in value)
    if isinstance(value, str):
        return bool(re.search(rf"(?i)\b{re.escape(key)}\s*[:=]\s*true\b", value))
    return False


def _looks_like_unfilled_json_template(payload: dict[str, Any]) -> bool:
    # 模板材料不能被当作现场回填；这些字段是本 repo 常用模板信号。
    schema = _safe_text(payload.get("schema", ""))
    if schema.endswith("_template.v1") or schema.endswith("_material_template.v1"):
        return True
    if payload.get("filled_by", None) == "" and payload.get("filled_at", None) == "":
        return True
    if payload.get("summary_status") == "placeholder":
        return True
    if payload.get("status") in {"placeholder", "template", "todo"}:
        return True
    return False


def _text_note_ref(text: str) -> str:
    # operator note 只解析固定 evidence_ref 行，不依赖自由文本格式。
    match = re.search(r"(?im)^\s*-?\s*evidence_ref\s*:\s*(.+?)\s*$", text)
    return _safe_ref(match.group(1).strip()) if match else ""


def _looks_like_unfilled_notes(text: str) -> bool:
    # 默认 notes 模板有空 operator/observed/help 字段，空值表示未回填。
    lowered = text.lower()
    template_markers = (
        "elevator field run operator note",
        "human assistance operator note",
        "todo",
        "placeholder",
    )
    empty_patterns = (
        r"(?im)^\s*-?\s*operator\s*:\s*$",
        r"(?im)^\s*-?\s*observed door state\s*:\s*$",
        r"(?im)^\s*-?\s*target floor confirmation\s*:\s*$",
        r"(?im)^\s*-?\s*human assistance note\s*:\s*$",
        r"(?im)^\s*-?\s*failure or recovery reason\s*:\s*$",
    )
    return any(marker in lowered for marker in template_markers) and any(re.search(pattern, text) for pattern in empty_patterns)


def _load_json_file(path: Path) -> tuple[dict[str, Any], str]:
    # 坏 JSON 要形成 blocked artifact，而不是抛未处理异常。
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}, "bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "read_error"
    if not isinstance(payload, dict):
        return {}, "not_object"
    return payload, ""


def _material_json_status(path: Path, category: str, expected_ref: str) -> tuple[dict[str, Any], list[str], bool, bool]:
    # JSON 材料只输出状态和白名单字段，不复制现场正文。
    payload, load_issue = _load_json_file(path)
    if load_issue:
        return {"status": load_issue, "ref": _safe_ref(str(path)), "category": category}, [], False, False
    evidence_ref = _safe_ref(payload.get("evidence_ref", ""))
    mismatches: list[str] = []
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
    }, mismatches, _any_true_key(payload, "primary_actions_enabled"), _any_true_key(payload, "delivery_success")


def _material_text_status(path: Path, category: str, expected_ref: str) -> tuple[dict[str, Any], list[str], bool, bool]:
    # Markdown notes 只判断是否回填、是否同 ref、是否越界声明成功。
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {"status": "read_error", "ref": _safe_ref(str(path)), "category": category}, [], False, False
    evidence_ref = _text_note_ref(text)
    mismatches: list[str] = []
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
    }, mismatches, _any_true_key(text, "primary_actions_enabled"), _any_true_key(text, "delivery_success")


def _scan_material_file(material_dir: Path, spec: dict[str, str], expected_ref: str) -> tuple[dict[str, Any], list[str], bool, bool, bool]:
    # 单文件扫描返回状态、错配、安全和越界声明，供总 verdict 聚合。
    target = material_dir / spec["name"]
    if not target.exists():
        return {
            "name": spec["name"],
            "category": spec["category"],
            "status": "missing",
            "same_evidence_ref_required": True,
        }, [], False, False, False
    try:
        raw_text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        raw_text = ""
    unsafe = _has_forbidden_copy(raw_text)
    if spec["kind"] == "json":
        entry, mismatches, action_claim, delivery_claim = _material_json_status(target, spec["category"], expected_ref)
    else:
        entry, mismatches, action_claim, delivery_claim = _material_text_status(target, spec["category"], expected_ref)
    entry["name"] = spec["name"]
    entry["unsafe_copy_detected"] = unsafe
    return entry, mismatches, unsafe, action_claim, delivery_claim


def _infer_evidence_ref(material_dir: Path) -> str:
    # CLI 允许不传 evidence_ref；此时从第一个已回填 ref 推导期望 ref。
    for spec in MATERIAL_SPECS:
        target = material_dir / spec["name"]
        if not target.exists():
            continue
        if spec["kind"] == "json":
            payload, load_issue = _load_json_file(target)
            if not load_issue:
                ref = _safe_ref(payload.get("evidence_ref", ""))
                if ref:
                    return ref
        else:
            try:
                ref = _text_note_ref(target.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError):
                ref = ""
            if ref:
                return ref
    return ""


def _scan_material_dir(material_dir: str, evidence_ref: str) -> tuple[dict[str, Any], list[str], dict[str, bool]]:
    # 没有 material-dir 时必须 fail closed，不能猜测现场材料存在。
    path = Path(material_dir).expanduser() if material_dir else Path("")
    flags = {
        "unsafe": False,
        "has_missing": False,
        "has_placeholder": False,
        "primary_actions_claim": False,
        "delivery_success_claim": False,
    }
    if not material_dir or not path.exists() or not path.is_dir():
        entries = [
            {"name": spec["name"], "category": spec["category"], "status": "missing", "same_evidence_ref_required": True}
            for spec in MATERIAL_SPECS
        ]
        flags["has_missing"] = True
        return {
            "material_dir_ref": _safe_ref(str(path)) if material_dir else "",
            "directory_status": "missing",
            "material_files": entries,
            "same_evidence_ref_required": True,
        }, [], flags
    expected_ref = _safe_ref(evidence_ref) or _infer_evidence_ref(path)
    entries: list[dict[str, Any]] = []
    mismatches: list[str] = []
    seen_refs: set[str] = set()
    for spec in MATERIAL_SPECS:
        entry, file_mismatches, file_unsafe, action_claim, delivery_claim = _scan_material_file(path, spec, expected_ref)
        entries.append(entry)
        mismatches.extend(file_mismatches)
        ref = entry.get("evidence_ref", "")
        if isinstance(ref, str) and ref:
            seen_refs.add(ref)
        flags["unsafe"] = flags["unsafe"] or file_unsafe
        flags["has_missing"] = flags["has_missing"] or entry["status"] in {"missing", "bad_json", "not_object", "read_error"}
        flags["has_placeholder"] = flags["has_placeholder"] or entry["status"] == "placeholder_template"
        flags["primary_actions_claim"] = flags["primary_actions_claim"] or action_claim
        flags["delivery_success_claim"] = flags["delivery_success_claim"] or delivery_claim
    if expected_ref:
        for ref in sorted(seen_refs):
            if ref != expected_ref:
                mismatches.append(f"material_dir:evidence_ref_mismatch:{ref}!={expected_ref}")
    elif len(seen_refs) > 1:
        mismatches.append("material_dir:evidence_ref_fields_do_not_share_same_ref")
    return {
        "material_dir_ref": _safe_ref(str(path)),
        "directory_status": "scanned",
        "material_files": entries,
        "same_evidence_ref_required": True,
    }, mismatches, flags


def _validation_verdict(material_status: dict[str, Any], mismatches: list[str], flags: dict[str, bool]) -> str:
    # verdict 优先级从输入可读性到安全边界，任何成功声明都 fail closed。
    if material_status["directory_status"] == "missing":
        return "blocked_missing_material_dir"
    if flags["delivery_success_claim"]:
        return "blocked_delivery_success_claim"
    if flags["primary_actions_claim"]:
        return "blocked_primary_actions_claim"
    if flags["unsafe"]:
        return "blocked_unsafe_summary"
    if mismatches:
        return "blocked_mismatch_evidence_ref"
    if flags["has_missing"]:
        return "blocked_missing_materials"
    if flags["has_placeholder"]:
        return "blocked_placeholder_materials"
    return "elevator_field_material_validation_ready_not_proven"


def _operator_next_steps(verdict: str, evidence_ref: str, material_status: dict[str, Any], mismatches: list[str]) -> list[str]:
    # next steps 只给现场补材料方向，不给机器人控制或硬件细节。
    ref = evidence_ref or "<same_evidence_ref>"
    files = material_status["material_files"]
    if verdict == "elevator_field_material_validation_ready_not_proven":
        steps = [
            f"Keep all elevator field materials under evidence_ref={ref}.",
            "Run Robot diagnostics/mobile read-only gates before any controlled field review.",
        ]
    elif verdict == "blocked_placeholder_materials":
        names = [entry["name"] for entry in files if entry["status"] == "placeholder_template"]
        steps = [f"Replace placeholder elevator materials for evidence_ref={ref}.", f"Placeholder files: {', '.join(names[:4])}"]
    elif verdict == "blocked_missing_materials":
        names = [entry["name"] for entry in files if entry["status"] in {"missing", "bad_json", "not_object", "read_error"}]
        steps = [f"Collect or repair elevator field materials for evidence_ref={ref}.", f"Missing or invalid files: {', '.join(names[:4])}"]
    elif verdict == "blocked_mismatch_evidence_ref":
        steps = [f"Regenerate materials so every file uses evidence_ref={ref}.", "Do not combine elevator, route, task, or completion files from different runs."]
    elif verdict in {"blocked_delivery_success_claim", "blocked_primary_actions_claim"}:
        steps = ["Remove success/control claims from the field material package.", f"Keep delivery_success=false and primary_actions_enabled=false for evidence_ref={ref}."]
    elif verdict == "blocked_unsafe_summary":
        steps = ["Remove raw credentials, ROS control topics, device paths, transport details, tracebacks, and raw robot responses.", f"Regenerate phone-safe summaries for evidence_ref={ref}."]
    else:
        steps = [f"Create a complete elevator field material directory for evidence_ref={ref}.", "Keep the result as software proof until real controlled field evidence is reviewed."]
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
    files = material_status["material_files"]
    return {
        "schema": VALIDATION_SUMMARY_SCHEMA,
        "schema_version": VALIDATION_SCHEMA_VERSION,
        "evidence_boundary": VALIDATION_BOUNDARY,
        "status": verdict,
        "material_validation_verdict": verdict,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "material_dir_ref": material_status["material_dir_ref"],
        "material_files": files,
        "missing_materials": [entry["name"] for entry in files if entry["status"] in {"missing", "bad_json", "not_object", "read_error"}],
        "placeholder_materials": [entry["name"] for entry in files if entry["status"] == "placeholder_template"],
        "mismatch_reasons": mismatches[:10],
        "operator_next_steps": next_steps[:5],
        "not_proven": list(NOT_PROVEN),
        "primary_actions_enabled": False,
        "delivery_success": False,
    }


def build_material_validation(material_dir: str, evidence_ref: str = "") -> tuple[dict[str, Any], int]:
    # 这是测试和 CLI 共用入口，保持无 ROS2/硬件/网络依赖。
    path = Path(material_dir).expanduser() if material_dir else Path("")
    requested_ref = _safe_ref(evidence_ref) or (_infer_evidence_ref(path) if material_dir and path.exists() else "")
    material_status, mismatches, flags = _scan_material_dir(material_dir, requested_ref)
    verdict = _validation_verdict(material_status, mismatches, flags)
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
        "material_directory_status": material_status,
        "material_validation_summary": summary,
        "operator_next_steps": next_steps,
        "mismatch_reasons": mismatches,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "ros_graph",
            "nav2_runtime",
            "hardware_transport",
            "wave_rover",
            "real_elevator",
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
    # CLI 只读 PC 侧材料目录；不会触发机器人动作或外部网络访问。
    parser = argparse.ArgumentParser(description="Validate elevator assisted delivery field-run material directory status")
    parser.add_argument("--material-dir", required=True, help="directory containing elevator field-run materials")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for validation")
    parser.add_argument("--output", default="", help="optional material validation JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print material validation JSON to stdout and exit")
    args = parser.parse_args()

    artifact, exit_code = build_material_validation(args.material_dir, args.evidence_ref)
    write_material_validation(artifact, args.output)
    if args.once_json or not args.output:
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"elevator field-run material validation: validation_file:{_safe_ref(args.output)}")
        print(f"material_validation_verdict: {artifact['material_validation_verdict']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
