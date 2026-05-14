#!/usr/bin/env python3
"""生成 route/task field-run evidence kit artifact。

该工具只读取上一轮 route_task_field_run_console JSON，并可选检查 PC 侧材料目录。
它把 console 转成现场同学可执行、可回填的证据包，但不访问 ROS graph、Nav2
runtime、serial/UART、WAVE ROVER、硬件、外部云、OSS/CDN、DB/queue 或 4G。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# evidence kit 是 console 之后的交付包契约，供 Robot diagnostics 和 mobile 只读消费。
KIT_SCHEMA = "trashbot.route_task_field_run_evidence_kit.v1"
KIT_SCHEMA_VERSION = 1
KIT_BOUNDARY = "software_proof_docker_route_task_field_run_evidence_kit_gate"
CONSOLE_SCHEMA = "trashbot.route_task_field_run_console.v1"
CONSOLE_BOUNDARY = "software_proof_docker_route_task_field_run_console_gate"

# material directory 只描述现场要交接的文件名，不读取硬件或运行时系统。
MATERIAL_FILES = (
    "route_task_field_run_console.json",
    "route_status.json",
    "task_record.json",
    "completion_signal.json",
    "operator_notes.md",
    "robot_diagnostics_summary.json",
    "mobile_readonly_summary.json",
)

# not_proven 固定列出真实能力缺口，避免 evidence kit 被误读成现场成功。
NOT_PROVEN = (
    "real_nav2_fixed_route_run",
    "real_route_capture",
    "wave_rover_motion",
    "real_uart_feedback",
    "real_hil_pass",
    "real_dropoff_completion",
    "real_cancel_completion",
    "delivery_success",
    "real_phone_device_or_browser",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# rg 验收会查 delivery_success=false；这里也给人工读者一个直接边界。
BOUNDARY_NOTE = "Docker/local software proof only; delivery_success=false; primary_actions_enabled=false"

# operator/mobile 摘要不能扩散凭证、控制 topic、硬件链路或 raw 调试材料。
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

# 先脱敏再检查禁词，既减少泄露，也能把可疑摘要 fail closed。
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
    # UTC 时间戳让不同 PC/Docker 主机生成的 kit 可以按字符串排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有自由文本都经过同一脱敏链，防止 console 文案绕过白名单。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # 本机完整路径不进手机/diagnostics，只保留 basename 作为交接线索。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_list(value: Any, limit: int = 30) -> list[str]:
    # 上游字段可能是字符串或 list；限制条数避免复制完整 artifact。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _safe_value(value: Any) -> Any:
    # 最终输出递归脱敏，防止新增字段遗漏局部 helper。
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
    # 命中禁词时不继续宣称 ready，避免 unsafe 摘要进入现场包。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺文件、坏 JSON、非 object 都输出 blocked kit，而不是抛未处理异常。
    if not path:
        return {}, "console_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "console_missing"
    except json.JSONDecodeError:
        return {}, "console_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "console_read_error"
    if not isinstance(payload, dict):
        return {}, "console_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只消费 object summary，避免把 raw list/string 当成稳定契约。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # evidence_ref、verdict 等字段允许从顶层或 nested summary 回退读取。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _extract_console_ref(console: dict[str, Any]) -> str:
    # 同一 evidence_ref 是 kit 的核心主键，兼容 diagnostics/mobile nested 形态。
    robot = _dict(console, "robot_diagnostics_summary")
    mobile = _dict(console, "mobile_readonly_summary")
    pack = _dict(console, "execution_pack_summary")
    route = _dict(console, "route_status_summary")
    task = _dict(console, "task_record_summary")
    completion = _dict(console, "completion_signal_summary")
    return _safe_ref(
        _first_text(
            console.get("evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("evidence_ref"),
            pack.get("evidence_ref"),
            route.get("evidence_ref"),
            task.get("evidence_ref"),
            completion.get("evidence_ref"),
            default="",
        )
    )


def _source_console_status(console: dict[str, Any], load_issue: str, console_path: str) -> dict[str, Any]:
    # source_console 只暴露白名单元数据，不复制上一轮完整 artifact。
    schema = _safe_text(console.get("schema", "")) if console else ""
    boundary = _safe_text(console.get("evidence_boundary", "")) if console else ""
    if load_issue:
        schema_status = "not_loaded"
    elif schema == CONSOLE_SCHEMA and boundary == CONSOLE_BOUNDARY:
        schema_status = "supported"
    else:
        schema_status = "unsupported"
    return {
        "ref": _safe_ref(console_path),
        "load_status": "blocked" if load_issue else "loaded",
        "load_issue": load_issue,
        "schema": schema,
        "schema_status": schema_status,
        "evidence_boundary": boundary,
        "console_verdict": _safe_text(console.get("console_verdict", "")) if console else "",
        "evidence_ref": _extract_console_ref(console) if console else "",
    }


def _material_directory_manifest(material_dir: str, evidence_ref: str) -> dict[str, Any]:
    # material dir manifest 是现场交接目录，不把缺目录猜成已采齐。
    path = Path(material_dir).expanduser() if material_dir else None
    dir_exists = bool(path and path.is_dir())
    entries: list[dict[str, Any]] = []
    for name in MATERIAL_FILES:
        present = bool(dir_exists and (path / name).exists())
        entries.append(
            {
                "name": name,
                "required": True,
                "present": present,
                "same_evidence_ref_required": True,
                "capture_template": f"Fill {name} for evidence_ref={evidence_ref or '<same_evidence_ref>'}; keep delivery_success=false.",
            }
        )
    missing = [entry["name"] for entry in entries if not entry["present"]]
    return {
        "material_dir_ref": _safe_ref(str(path)) if path else "",
        "directory_status": "present" if dir_exists else "not_provided",
        "expected_files": entries,
        "missing_files": missing,
        "same_evidence_ref_required": True,
    }


def _capture_templates(evidence_ref: str) -> list[dict[str, Any]]:
    # capture_templates 给现场同学回填字段，不创建真实运行结论。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        {
            "name": "route_status_json",
            "required_fields": ["schema_or_state", "evidence_ref", "route_progress", "failure_code"],
            "same_evidence_ref_required": True,
            "template_note": f"Capture fixed-route/Nav2 status for evidence_ref={ref}; do not set delivery_success=true.",
        },
        {
            "name": "task_record_json",
            "required_fields": ["task_id", "evidence_ref", "state_transition_history", "failure_reason", "recovery_reason"],
            "same_evidence_ref_required": True,
            "template_note": f"Capture task state transitions for evidence_ref={ref}.",
        },
        {
            "name": "completion_signal_json",
            "required_fields": ["schema", "evidence_ref", "dropoff_completion", "cancel_completion", "not_proven"],
            "same_evidence_ref_required": True,
            "template_note": f"Record completion materials for evidence_ref={ref}; completion remains not_proven in this kit.",
        },
        {
            "name": "operator_notes",
            "required_fields": ["operator", "time", "observed_failure_or_recovery", "materials_collected"],
            "same_evidence_ref_required": True,
            "template_note": "Use phone-safe notes only; omit credentials, local devices, raw robot response, ROS topics, and complete artifacts.",
        },
    ]


def _commands_to_run(evidence_ref: str, console_path: str, material_dir: str) -> list[str]:
    # commands 只生成 PC 侧回填/重跑说明，不触发机器人动作。
    ref = evidence_ref or "<same_evidence_ref>"
    kit_output = f"{material_dir.rstrip('/')}/route_task_field_run_evidence_kit.json" if material_dir else "/tmp/route_task_field_run_evidence_kit.json"
    return [
        f"mkdir -p {material_dir or '/tmp/route_task_field_run_materials'}",
        f"Copy route_status.json, task_record.json, completion_signal.json, operator_notes.md, robot_diagnostics_summary.json, and mobile_readonly_summary.json under evidence_ref={ref}.",
        f"python3 pc-tools/evidence/route_task_field_run_evidence_kit.py --console-json {console_path or '/tmp/route_task_field_run_console.json'} --material-dir {material_dir or '/tmp/route_task_field_run_materials'} --evidence-ref {ref} --output {kit_output}",
    ]


def _commands_to_rerun(evidence_ref: str, console_path: str, material_dir: str) -> list[str]:
    # rerun 命令强调同一 ref 复账，防止把不同 run 拼成成功证据。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"Regenerate route_task_field_run_console.json with evidence_ref={ref}.",
        f"Rebuild the material directory with only files from evidence_ref={ref}.",
        f"python3 pc-tools/evidence/route_task_field_run_evidence_kit.py --console-json {console_path or '/tmp/route_task_field_run_console.json'} --material-dir {material_dir or '/tmp/route_task_field_run_materials'} --evidence-ref {ref} --once-json",
    ]


def _console_missing_materials(console: dict[str, Any]) -> list[str]:
    # console 的 blocked/missing 直接进入 kit，避免 evidence kit 掩盖上一层问题。
    materials = _dict(console, "materials_status")
    missing = _safe_list(materials.get("missing_materials"))
    missing.extend(_safe_list(console.get("missing_materials")))
    return list(dict.fromkeys(item for item in missing if item))


def _console_mismatches(console: dict[str, Any], expected_ref: str) -> list[str]:
    # 同一 ref 检查覆盖顶层和四个 summary，任何漂移都保持 blocked。
    refs = {
        "console": _extract_console_ref(console),
        "execution_pack": _safe_ref(_dict(console, "execution_pack_summary").get("evidence_ref", "")),
        "route_status": _safe_ref(_dict(console, "route_status_summary").get("evidence_ref", "")),
        "task_record": _safe_ref(_dict(console, "task_record_summary").get("evidence_ref", "")),
        "completion_signal": _safe_ref(_dict(console, "completion_signal_summary").get("evidence_ref", "")),
    }
    mismatches: list[str] = []
    for label, ref in refs.items():
        if expected_ref and ref and ref != expected_ref:
            mismatches.append(f"{label}:evidence_ref_mismatch:{ref}!={expected_ref}")
    loaded_refs = {ref for ref in refs.values() if ref}
    if len(loaded_refs) > 1:
        mismatches.append("evidence_ref:console_summaries_do_not_share_same_ref")
    return mismatches


def _input_claims_delivery_success(console: dict[str, Any]) -> bool:
    # 上游如果已经声称 delivery_success=true，kit 必须阻断该成功口径。
    robot = _dict(console, "robot_diagnostics_summary")
    mobile = _dict(console, "mobile_readonly_summary")
    return console.get("delivery_success") is True or robot.get("delivery_success") is True or mobile.get("delivery_success") is True


def _input_enables_primary_actions(console: dict[str, Any]) -> bool:
    # evidence kit 是只读证据包，不能继承任何 Start/Confirm/Cancel 放行状态。
    robot = _dict(console, "robot_diagnostics_summary")
    mobile = _dict(console, "mobile_readonly_summary")
    return console.get("primary_actions_enabled") is True or robot.get("primary_actions_enabled") is True or mobile.get("primary_actions_enabled") is True


def _kit_verdict(
    source: dict[str, Any],
    directory_manifest: dict[str, Any],
    missing_materials: list[str],
    mismatches: list[str],
    unsafe: bool,
    delivery_success_claimed: bool,
    primary_actions_enabled: bool,
) -> str:
    # verdict 优先级保持 fail-closed：输入、schema、同 ref、安全、越界成功、材料目录。
    if source["load_issue"] in {"console_bad_json", "console_not_object", "console_read_error"}:
        return "blocked_bad_console"
    if source["load_status"] != "loaded":
        return "blocked_missing_console"
    if source["schema_status"] == "unsupported":
        return "blocked_unsupported_console"
    if mismatches:
        return "blocked_mismatch_evidence_ref"
    if unsafe or primary_actions_enabled:
        return "blocked_unsafe_summary"
    if delivery_success_claimed:
        return "blocked_delivery_success_claim"
    if source["console_verdict"].startswith("blocked"):
        return "blocked_source_console"
    if missing_materials or directory_manifest["missing_files"]:
        return "blocked_missing_materials"
    return "field_run_evidence_kit_ready_not_proven"


def _operator_handoff(verdict: str, evidence_ref: str, missing: list[str], mismatches: list[str]) -> dict[str, Any]:
    # handoff 是人读的下一步，不包含 raw artifact 或控制细节。
    ref = evidence_ref or "<same_evidence_ref>"
    if verdict == "field_run_evidence_kit_ready_not_proven":
        next_steps = [
            f"Hand this evidence kit to the field operator for evidence_ref={ref}.",
            "Use the material directory manifest and capture templates during the run.",
            "Return filled materials for PC review before any delivery success claim.",
        ]
    elif verdict == "blocked_mismatch_evidence_ref":
        next_steps = [
            f"Regenerate console and material files under one evidence_ref={ref}.",
            "Do not combine material files from different route/task runs.",
        ]
    elif verdict == "blocked_unsafe_summary":
        next_steps = [
            "Remove unsafe support/mobile copy from the source console or material notes.",
            "Regenerate the evidence kit before sharing it with field operators.",
        ]
    else:
        next_steps = [
            f"Complete the missing console/material files under evidence_ref={ref}.",
            "Rerun this evidence kit gate before a field handoff.",
            "Keep delivery_success=false until a separate real field evidence gate passes.",
        ]
    if missing:
        next_steps.append(f"Missing materials: {', '.join(missing[:6])}")
    if mismatches:
        next_steps.append(f"Evidence mismatch: {', '.join(mismatches[:3])}")
    return {
        "status": verdict,
        "evidence_ref": evidence_ref,
        "next_steps": [_safe_text(step) for step in next_steps[:5]],
        "same_evidence_ref_required": True,
        "delivery_success": False,
    }


def _robot_diagnostics_summary(verdict: str, evidence_ref: str, missing: list[str], mismatches: list[str]) -> dict[str, Any]:
    # diagnostics summary 是 metadata-only，不是 command/status/ACK 控制面。
    return {
        "schema": KIT_SCHEMA,
        "evidence_boundary": KIT_BOUNDARY,
        "status": verdict,
        "evidence_kit_verdict": verdict,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "missing_materials": missing[:10],
        "mismatch_reasons": mismatches[:10],
        "not_proven": list(NOT_PROVEN),
        "ack_semantics": "route_task_field_run_evidence_kit_metadata_only_not_delivery_success",
        "primary_actions_enabled": False,
        "delivery_success": False,
    }


def _mobile_readonly_summary(verdict: str, evidence_ref: str, handoff: dict[str, Any]) -> dict[str, Any]:
    # mobile 只显示白名单摘要，不能带本机路径或控制动作。
    return {
        "schema": KIT_SCHEMA,
        "evidence_boundary": KIT_BOUNDARY,
        "status": verdict,
        "evidence_kit_verdict": verdict,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "operator_next_steps": handoff["next_steps"][:3],
        "not_proven": list(NOT_PROVEN),
        "primary_actions_enabled": False,
        "delivery_success": False,
    }


def build_evidence_kit(
    console_json: str,
    material_dir: str = "",
    evidence_ref: str = "",
) -> tuple[dict[str, Any], int]:
    console, load_issue = _load_json(console_json)
    source = _source_console_status(console, load_issue, console_json)
    requested_ref = _safe_ref(evidence_ref) or source.get("evidence_ref", "")
    directory_manifest = _material_directory_manifest(material_dir, requested_ref)
    console_missing = _console_missing_materials(console) if console else []
    missing_materials = list(dict.fromkeys(console_missing + directory_manifest["missing_files"]))
    mismatches = _console_mismatches(console, requested_ref) if console else []
    unsafe = bool(console and _has_forbidden_copy(console))
    delivery_success_claimed = bool(console and _input_claims_delivery_success(console))
    primary_actions_enabled = bool(console and _input_enables_primary_actions(console))
    verdict = _kit_verdict(
        source,
        directory_manifest,
        missing_materials,
        mismatches,
        unsafe,
        delivery_success_claimed,
        primary_actions_enabled,
    )
    handoff = _operator_handoff(verdict, requested_ref, missing_materials, mismatches)
    robot_summary = _robot_diagnostics_summary(verdict, requested_ref, missing_materials, mismatches)
    mobile_summary = _mobile_readonly_summary(verdict, requested_ref, handoff)
    artifact = {
        "schema": KIT_SCHEMA,
        "schema_version": KIT_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": KIT_BOUNDARY,
        "same_evidence_ref_required": True,
        "evidence_ref": requested_ref,
        "evidence_kit_verdict": verdict,
        "source_console": source,
        "material_directory_manifest": directory_manifest,
        "capture_templates": _capture_templates(requested_ref),
        "commands_to_run": _commands_to_run(requested_ref, _safe_ref(console_json), directory_manifest["material_dir_ref"]),
        "commands_to_rerun": _commands_to_rerun(requested_ref, _safe_ref(console_json), directory_manifest["material_dir_ref"]),
        "missing_materials": missing_materials,
        "mismatch_reasons": mismatches,
        "operator_handoff": handoff,
        "robot_diagnostics_summary": robot_summary,
        "mobile_readonly_summary": mobile_summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "ros_graph",
            "nav2_runtime",
            "hardware_transport",
            "wave_rover",
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
        # 最终防线保证输出不带敏感 copy；状态也必须回落到 blocked。
        artifact["evidence_kit_verdict"] = "blocked_unsafe_summary"
        artifact["operator_handoff"]["status"] = "blocked_unsafe_summary"
        artifact["robot_diagnostics_summary"]["status"] = "blocked_unsafe_summary"
        artifact["robot_diagnostics_summary"]["evidence_kit_verdict"] = "blocked_unsafe_summary"
        artifact["mobile_readonly_summary"]["status"] = "blocked_unsafe_summary"
        artifact["mobile_readonly_summary"]["evidence_kit_verdict"] = "blocked_unsafe_summary"
    return artifact, 0


def write_evidence_kit(artifact: dict[str, Any], output: str) -> None:
    # output 为空时只打印 stdout；指定路径时自动创建父目录。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 只读 console 和材料目录；--once-json 用于验收或 downstream fixture。
    parser = argparse.ArgumentParser(description="Generate a route/task field-run evidence kit artifact")
    parser.add_argument("--console-json", required=True, help="route_task_field_run_console JSON path")
    parser.add_argument("--material-dir", default="", help="optional field-run material directory to manifest-check")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for console and material handoff")
    parser.add_argument("--output", default="", help="optional evidence kit JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print evidence kit JSON to stdout and exit")
    args = parser.parse_args()

    artifact, exit_code = build_evidence_kit(args.console_json, args.material_dir, args.evidence_ref)
    write_evidence_kit(artifact, args.output)
    if args.once_json or not args.output:
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route/task field-run evidence kit: kit_file:{_safe_ref(args.output)}")
        print(f"evidence_kit_verdict: {artifact['evidence_kit_verdict']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
