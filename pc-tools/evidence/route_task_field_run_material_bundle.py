#!/usr/bin/env python3
"""生成 route/task field-run material bundle summary 和现场材料目录脚手架。

该工具只读取上一轮 route_task_field_run_evidence_kit JSON。指定 --material-dir
时，它会在 PC 侧创建现场回填模板；它不访问 ROS graph、Nav2 runtime、
serial/UART、硬件、外部云、OSS/CDN、DB/queue 或 4G。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# material bundle 是 evidence kit 之后的现场材料履约契约，供 diagnostics/mobile 只读消费。
BUNDLE_SCHEMA = "trashbot.route_task_field_run_material_bundle.v1"
BUNDLE_SUMMARY_SCHEMA = "trashbot.route_task_field_run_material_bundle_summary.v1"
BUNDLE_SCHEMA_VERSION = 1
BUNDLE_BOUNDARY = "software_proof_docker_route_task_field_run_material_bundle_gate"
KIT_SCHEMA = "trashbot.route_task_field_run_evidence_kit.v1"
KIT_BOUNDARY = "software_proof_docker_route_task_field_run_evidence_kit_gate"

# 模板文件只表达现场要回填什么，不把占位内容当作真实 route/task 运行结果。
MATERIAL_TEMPLATES = (
    {
        "name": "route_status_template.json",
        "category": "route",
        "description": "fixed-route/Nav2 status placeholder",
    },
    {
        "name": "task_record_template.json",
        "category": "task",
        "description": "task state transition placeholder",
    },
    {
        "name": "completion_material_template.json",
        "category": "completion",
        "description": "dropoff/cancel completion placeholder",
    },
    {
        "name": "operator_notes.md",
        "category": "operator_notes",
        "description": "phone-safe operator notes placeholder",
    },
    {
        "name": "robot_diagnostics_summary_template.json",
        "category": "diagnostics",
        "description": "metadata-only robot diagnostics placeholder",
    },
    {
        "name": "mobile_readonly_summary_template.json",
        "category": "mobile_summary",
        "description": "read-only mobile summary placeholder",
    },
)

# not_proven 固定保留真实能力缺口，避免材料包被误读成现场执行成功。
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

# rg 验收会查这些边界字样；同时给人工读者一个直接防误读口径。
BOUNDARY_NOTE = (
    "Docker/local software proof only; delivery_success=false; "
    "primary_actions_enabled=false; same_evidence_ref_required=true"
)

# material bundle 面向现场人员，不能把凭证、控制 topic、硬件链路或 raw 调试材料带出去。
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

# 先脱敏再输出；命中禁词仍 fail closed，避免模板或摘要成为泄露渠道。
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
    # UTC 时间戳让不同 PC/Docker 主机生成的材料包可以稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有自由文本共用脱敏链，避免新增字段绕过 phone-safe 边界。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # 面向 diagnostics/mobile 的 ref 只保留 basename，避免暴露本机完整路径。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_list(value: Any, limit: int = 30) -> list[str]:
    # 上游可能给字符串或 list；限制条数避免复制完整 artifact。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _safe_value(value: Any) -> Any:
    # 最终输出递归脱敏，保证 scaffold summary 不泄露 raw 字段。
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
    # forbidden copy 检查需要稳定字符串，异常对象按脱敏文本处理。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # 命中禁词时保持 blocked，防止材料包被当成可分享现场材料。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺文件、坏 JSON、非 object 都输出 blocked bundle，而不是抛未处理异常。
    if not path:
        return {}, "evidence_kit_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "evidence_kit_missing"
    except json.JSONDecodeError:
        return {}, "evidence_kit_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "evidence_kit_read_error"
    if not isinstance(payload, dict):
        return {}, "evidence_kit_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只消费 object summary，避免 raw list/string 成为稳定接口。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # evidence_ref 允许从顶层和 nested summary 回退读取，兼容上一轮 artifact 形态。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _extract_kit_ref(kit: dict[str, Any]) -> str:
    # 同一 evidence_ref 是材料目录和后续 intake/review 的主键。
    robot = _dict(kit, "robot_diagnostics_summary")
    mobile = _dict(kit, "mobile_readonly_summary")
    handoff = _dict(kit, "operator_handoff")
    return _safe_ref(
        _first_text(
            kit.get("evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("evidence_ref"),
            handoff.get("evidence_ref"),
            default="",
        )
    )


def _source_kit_status(kit: dict[str, Any], load_issue: str, kit_path: str) -> dict[str, Any]:
    # source_kit 只暴露白名单元数据，不复制上一轮完整 evidence kit。
    schema = _safe_text(kit.get("schema", "")) if kit else ""
    boundary = _safe_text(kit.get("evidence_boundary", "")) if kit else ""
    if load_issue:
        schema_status = "not_loaded"
    elif schema == KIT_SCHEMA and boundary == KIT_BOUNDARY:
        schema_status = "supported"
    else:
        schema_status = "unsupported"
    return {
        "ref": _safe_ref(kit_path),
        "load_status": "blocked" if load_issue else "loaded",
        "load_issue": load_issue,
        "schema": schema,
        "schema_status": schema_status,
        "evidence_boundary": boundary,
        "evidence_kit_verdict": _safe_text(kit.get("evidence_kit_verdict", "")) if kit else "",
        "evidence_ref": _extract_kit_ref(kit) if kit else "",
    }


def _input_claims_delivery_success(kit: dict[str, Any]) -> bool:
    # 上游若声称 delivery_success=true，材料包必须阻断该成功口径。
    robot = _dict(kit, "robot_diagnostics_summary")
    mobile = _dict(kit, "mobile_readonly_summary")
    return kit.get("delivery_success") is True or robot.get("delivery_success") is True or mobile.get("delivery_success") is True


def _input_enables_primary_actions(kit: dict[str, Any]) -> bool:
    # material bundle 是只读材料准备，不继承 Start/Confirm/Cancel 放行状态。
    robot = _dict(kit, "robot_diagnostics_summary")
    mobile = _dict(kit, "mobile_readonly_summary")
    return kit.get("primary_actions_enabled") is True or robot.get("primary_actions_enabled") is True or mobile.get("primary_actions_enabled") is True


def _kit_mismatches(kit: dict[str, Any], expected_ref: str) -> list[str]:
    # 同一 ref 检查覆盖顶层、diagnostics、mobile 和 operator handoff。
    refs = {
        "evidence_kit": _extract_kit_ref(kit),
        "robot_diagnostics": _safe_ref(_dict(kit, "robot_diagnostics_summary").get("evidence_ref", "")),
        "mobile_readonly": _safe_ref(_dict(kit, "mobile_readonly_summary").get("evidence_ref", "")),
        "operator_handoff": _safe_ref(_dict(kit, "operator_handoff").get("evidence_ref", "")),
    }
    mismatches: list[str] = []
    for label, ref in refs.items():
        if expected_ref and ref and ref != expected_ref:
            mismatches.append(f"{label}:evidence_ref_mismatch:{ref}!={expected_ref}")
    loaded_refs = {ref for ref in refs.values() if ref}
    if len(loaded_refs) > 1:
        mismatches.append("evidence_ref:evidence_kit_summaries_do_not_share_same_ref")
    return mismatches


def _json_template(category: str, evidence_ref: str) -> dict[str, Any]:
    # JSON 模板只给现场回填字段，不预填任何成功结论。
    common = {
        "schema": f"trashbot.route_task_field_run_{category}_material_template.v1",
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "filled_by": "",
        "filled_at": "",
        "notes": "",
        "primary_actions_enabled": False,
        "delivery_success": False,
        "not_proven": list(NOT_PROVEN),
    }
    if category == "route":
        common.update({"route_state": "", "checkpoint_id": "", "failure_code": "", "failure_reason": ""})
    elif category == "task":
        common.update({"task_id": "", "state_transition_history": [], "recovery_reason": ""})
    elif category == "completion":
        common.update({"dropoff_completion": {"present": False}, "cancel_completion": {"present": False}})
    elif category == "diagnostics":
        common.update({"summary_status": "placeholder", "material_bundle_status": ""})
    elif category == "mobile_summary":
        common.update({"summary_status": "placeholder", "operator_next_steps": []})
    return common


def _operator_notes_template(evidence_ref: str) -> str:
    # Markdown 模板提醒现场同学只写 phone-safe 观察，不写硬件链路或 raw 响应。
    return "\n".join(
        [
            "# Route Task Field Run Operator Notes",
            "",
            f"- evidence_ref: {evidence_ref}",
            "- same_evidence_ref_required: true",
            "- delivery_success=false",
            "- primary_actions_enabled=false",
            "",
            "## Observations",
            "",
            "- operator:",
            "- observed route/task state:",
            "- failure or recovery reason:",
            "- materials collected:",
            "",
            "## Phone-safe constraints",
            "",
            "- Do not paste credentials, local device paths, control topics, raw robot responses, or complete artifacts.",
            "- Keep this note as Docker/local material support until a separate real field gate passes.",
            "",
        ]
    )


def _template_content(template: dict[str, str], evidence_ref: str) -> str:
    # 不同文件类型保持轻量文本，便于现场直接编辑和版本比较。
    category = template["category"]
    if category == "operator_notes":
        return _operator_notes_template(evidence_ref)
    payload = _json_template(category, evidence_ref)
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _write_material_scaffold(material_dir: str, evidence_ref: str) -> tuple[dict[str, Any], str]:
    # 指定 material-dir 时才创建目录；已有文件保留，避免覆盖现场手写材料。
    if not material_dir:
        entries = [
            {
                "name": template["name"],
                "category": template["category"],
                "description": template["description"],
                "status": "not_requested",
                "same_evidence_ref_required": True,
            }
            for template in MATERIAL_TEMPLATES
        ]
        return {
            "material_dir_ref": "",
            "directory_status": "not_requested",
            "template_files": entries,
            "same_evidence_ref_required": True,
        }, ""
    try:
        path = Path(material_dir).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        entries: list[dict[str, Any]] = []
        for template in MATERIAL_TEMPLATES:
            target = path / template["name"]
            if target.exists():
                status = "preserved_existing"
            else:
                target.write_text(_template_content(template, evidence_ref), encoding="utf-8")
                status = "created"
            entries.append(
                {
                    "name": template["name"],
                    "category": template["category"],
                    "description": template["description"],
                    "status": status,
                    "ref": _safe_ref(str(target)),
                    "same_evidence_ref_required": True,
                }
            )
    except OSError as exc:
        return {
            "material_dir_ref": _safe_ref(material_dir),
            "directory_status": "write_error",
            "write_error": _safe_text(exc),
            "template_files": [],
            "same_evidence_ref_required": True,
        }, "material_dir_write_error"
    return {
        "material_dir_ref": _safe_ref(str(path)),
        "directory_status": "scaffold_ready",
        "template_files": entries,
        "same_evidence_ref_required": True,
    }, ""


def _bundle_verdict(
    source: dict[str, Any],
    mismatches: list[str],
    unsafe: bool,
    delivery_success_claimed: bool,
    primary_actions_enabled: bool,
    scaffold_issue: str,
) -> str:
    # verdict 优先级保持 fail-closed：输入、schema、同 ref、安全、越界成功、写目录。
    if source["load_issue"] in {"evidence_kit_bad_json", "evidence_kit_not_object", "evidence_kit_read_error"}:
        return "blocked_bad_evidence_kit"
    if source["load_status"] != "loaded":
        return "blocked_missing_evidence_kit"
    if source["schema_status"] == "unsupported":
        return "blocked_unsupported_evidence_kit"
    if mismatches:
        return "blocked_mismatch_evidence_ref"
    if unsafe or primary_actions_enabled:
        return "blocked_unsafe_summary"
    if delivery_success_claimed:
        return "blocked_delivery_success_claim"
    if source["evidence_kit_verdict"].startswith("blocked"):
        return "blocked_source_evidence_kit"
    if scaffold_issue:
        return "blocked_material_scaffold_write"
    return "field_run_material_bundle_ready_not_proven"


def _operator_next_steps(verdict: str, evidence_ref: str, mismatches: list[str], scaffold_issue: str) -> list[str]:
    # next steps 是现场操作说明，不包含 raw path 或控制细节。
    ref = evidence_ref or "<same_evidence_ref>"
    if verdict == "field_run_material_bundle_ready_not_proven":
        steps = [
            f"Use the material bundle templates under evidence_ref={ref}.",
            "Fill route, task, completion, diagnostics, mobile summary, and operator notes before review.",
            "Run intake/review gates before any delivery success claim.",
        ]
    elif verdict == "blocked_mismatch_evidence_ref":
        steps = [
            f"Regenerate the evidence kit summaries under one evidence_ref={ref}.",
            "Do not combine material files from different route/task runs.",
        ]
    elif verdict == "blocked_material_scaffold_write":
        steps = [
            "Choose a writable material directory and rerun the material bundle CLI.",
            f"Keep every regenerated template on evidence_ref={ref}.",
        ]
    else:
        steps = [
            "Regenerate a supported route_task_field_run_evidence_kit first.",
            f"Keep delivery_success=false and same evidence_ref={ref}.",
        ]
    if mismatches:
        steps.append(f"Evidence mismatch: {', '.join(mismatches[:3])}")
    if scaffold_issue:
        steps.append(f"Scaffold issue: {scaffold_issue}")
    return [_safe_text(step) for step in steps[:5]]


def _material_bundle_summary(
    verdict: str,
    evidence_ref: str,
    scaffold: dict[str, Any],
    next_steps: list[str],
    mismatches: list[str],
) -> dict[str, Any]:
    # summary 是 Robot/Full-stack 的消费面，字段保持小而稳定。
    return {
        "schema": BUNDLE_SUMMARY_SCHEMA,
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "evidence_boundary": BUNDLE_BOUNDARY,
        "status": verdict,
        "material_bundle_verdict": verdict,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "material_dir_ref": scaffold["material_dir_ref"],
        "template_files": scaffold["template_files"],
        "mismatch_reasons": mismatches[:10],
        "operator_next_steps": next_steps[:5],
        "not_proven": list(NOT_PROVEN),
        "primary_actions_enabled": False,
        "delivery_success": False,
    }


def build_material_bundle(
    evidence_kit_json: str,
    material_dir: str = "",
    evidence_ref: str = "",
) -> tuple[dict[str, Any], int]:
    kit, load_issue = _load_json(evidence_kit_json)
    source = _source_kit_status(kit, load_issue, evidence_kit_json)
    requested_ref = _safe_ref(evidence_ref) or source.get("evidence_ref", "")
    scaffold, scaffold_issue = _write_material_scaffold(material_dir, requested_ref or "<same_evidence_ref>")
    mismatches = _kit_mismatches(kit, requested_ref) if kit else []
    unsafe = bool(kit and _has_forbidden_copy(kit))
    delivery_success_claimed = bool(kit and _input_claims_delivery_success(kit))
    primary_actions_enabled = bool(kit and _input_enables_primary_actions(kit))
    verdict = _bundle_verdict(
        source,
        mismatches,
        unsafe,
        delivery_success_claimed,
        primary_actions_enabled,
        scaffold_issue,
    )
    next_steps = _operator_next_steps(verdict, requested_ref, mismatches, scaffold_issue)
    summary = _material_bundle_summary(verdict, requested_ref, scaffold, next_steps, mismatches)
    artifact = {
        "schema": BUNDLE_SCHEMA,
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": BUNDLE_BOUNDARY,
        "same_evidence_ref_required": True,
        "evidence_ref": requested_ref,
        "material_bundle_verdict": verdict,
        "source_evidence_kit": source,
        "material_directory_scaffold": scaffold,
        "material_bundle_summary": summary,
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
        # 最终防线保证输出不带敏感 copy；状态也同步回落到 blocked。
        artifact["material_bundle_verdict"] = "blocked_unsafe_summary"
        artifact["material_bundle_summary"]["status"] = "blocked_unsafe_summary"
        artifact["material_bundle_summary"]["material_bundle_verdict"] = "blocked_unsafe_summary"
        artifact["operator_next_steps"] = _operator_next_steps("blocked_unsafe_summary", requested_ref, mismatches, scaffold_issue)
    return artifact, 0


def write_material_bundle(artifact: dict[str, Any], output: str) -> None:
    # output 为空时只打印 stdout；指定路径时自动创建父目录。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 只读 evidence kit；--material-dir 是 PC 侧模板写入，不触发机器人动作。
    parser = argparse.ArgumentParser(description="Generate a route/task field-run material bundle summary")
    parser.add_argument("--evidence-kit-json", required=True, help="route_task_field_run_evidence_kit JSON path")
    parser.add_argument("--material-dir", default="", help="optional directory where material templates are created")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for the material bundle")
    parser.add_argument("--output", default="", help="optional material bundle JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print material bundle JSON to stdout and exit")
    args = parser.parse_args()

    artifact, exit_code = build_material_bundle(args.evidence_kit_json, args.material_dir, args.evidence_ref)
    write_material_bundle(artifact, args.output)
    if args.once_json or not args.output:
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route/task field-run material bundle: bundle_file:{_safe_ref(args.output)}")
        print(f"material_bundle_verdict: {artifact['material_bundle_verdict']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
