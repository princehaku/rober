#!/usr/bin/env python3
"""生成 verified_terminal_result_material_intake 的 fail-closed PC evidence gate。"""

from __future__ import annotations

# 设计约束 01：本 gate 只在 PC 侧读取 JSON bundle，不连接 ROS graph、Nav2 runtime 或硬件。
# 设计约束 02：terminal result 只能进入人工复核队列，不能升级成 delivery success。
# 设计约束 03：顶层 evidence_ref 与每个 nested material ref 必须完全一致，避免拼接不同现场证据。
# 设计约束 04：delivery/dropoff/cancel 三类终态分别有 required materials，缺失时必须 fail closed。
# 设计约束 05：raw artifact、本机路径、凭证、ROS/control details、hardware details 和成功 overclaim 一律拒绝。
# 设计约束 06：输出只保留脱敏摘要、材料名和 safe evidence_ref，不复制输入里的原始路径或敏感字段。
# 设计约束 07：所有 artifact 都固定保持 software_proof、not_proven 和三个 false flag。
# 设计约束 08：blocked 输出仍生成 summary，方便 sprint 证据链说明还缺什么材料。
# 设计约束 09：exit code 只表达 gate 是否遇到不安全/不一致输入，不代表真实任务终态。
# 设计约束 10：技术注释使用中文，说明为什么这些保守边界不能放松。

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.verified_terminal_result_material_intake.v1"
SUMMARY_SCHEMA = "trashbot.verified_terminal_result_material_intake_summary.v1"
SCHEMA_VERSION = 1
CAPABILITY = "verified_terminal_result_material_intake"
SOURCE = "software_proof"
STATUS = "not_proven"
EVIDENCE_BOUNDARY = "software_proof_docker_verified_terminal_result_material_intake_gate"

READY_STATUS = "ready_for_terminal_result_manual_review_not_proven"
MISSING_STATUS = "blocked_missing_terminal_result_required_materials_not_proven"
UNSAFE_STATUS = "blocked_unsafe_terminal_result_material_bundle_not_proven"
REF_STATUS = "blocked_evidence_ref_mismatch_terminal_result_materials_not_proven"
TYPE_STATUS = "blocked_unsupported_terminal_result_type_not_proven"
READ_STATUS = "blocked_missing_or_unreadable_terminal_result_bundle_not_proven"

TERMINAL_RESULT_TYPES = ("delivery", "dropoff", "cancel")
REQUIRED_MATERIALS: dict[str, tuple[str, ...]] = {
    "delivery": (
        "task_record",
        "nav2_fixed_route_runtime_log",
        "route_completion_signal",
        "elevator_door_floor_evidence",
        "human_assistance_note",
        "delivery_result",
        "true_phone_browser_evidence",
        "diagnostics_mobile_safe_summary",
    ),
    "dropoff": (
        "task_record",
        "nav2_fixed_route_runtime_log",
        "route_completion_signal",
        "elevator_door_floor_evidence",
        "human_assistance_note",
        "dropoff_cancel_completion",
        "true_phone_browser_evidence",
        "diagnostics_mobile_safe_summary",
    ),
    "cancel": (
        "task_record",
        "dropoff_cancel_completion",
        "true_phone_browser_evidence",
        "diagnostics_mobile_safe_summary",
    ),
}

SAFE_EVIDENCE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,80}$")
PATH_LIKE_RE = re.compile(r"(^/|[A-Za-z]:\\|\\\\|file://|\\b\\.\\.?/|/dev/|/Users/|/tmp/|/var/|/home/)")
TOKEN_LIKE_RE = re.compile(r"(?i)(token|secret|password|authorization|bearer|access[_-]?key|api[_-]?key|credential)")

# 禁止字段即使命中 false 也拒绝，因为本 gate 的输入合同不允许携带控制/凭证/硬件细节。
FORBIDDEN_KEY_TERMS = (
    "raw_artifact",
    "raw_artifacts",
    "artifact_path",
    "raw_path",
    "local_path",
    "file_path",
    "log_path",
    "screenshot_path",
    "delivery_success",
    "primary_actions_enabled",
    "safe_to_control",
    "control_enabled",
    "control_command",
    "cmd_vel",
    "twist",
    "motor",
    "ros_topic",
    "ros_service",
    "ros_action",
    "odom_topic",
    "credential",
    "credentials",
    "token",
    "secret",
    "password",
    "authorization",
    "access_key",
    "api_key",
    "cookie",
    "db_url",
    "queue_url",
    "hardware_detail",
    "hardware_details",
    "serial_device",
    "uart",
    "wave_rover",
    "esp32",
    "orange_pi",
    "baudrate",
    "voltage",
    "pin",
    "wiring",
    "firmware",
)

UNSAFE_TEXT_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(control_enabled|hil_pass|field_pass)\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(Bearer\s+|Authorization\s*:|password|private_key|OSS_ACCESS_KEY_SECRET)\b"),
    re.compile(r"(?i)\b(token|secret|access[_-]?key|api[_-]?key|password)\b\s*[:=]"),
    re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://"),
    re.compile(r"(?i)\b(ros2\s+topic|/cmd_vel|/odom|/tf|/trashbot/|rclpy|ros graph)\b"),
    re.compile(r"(?i)\b(WAVE ROVER|ESP32|Orange Pi|UART|baudrate|GPIO|voltage|firmware|serial device)\b"),
    re.compile(r"(?<![A-Za-z0-9_.-])/(Users|tmp|var|etc|home|run|private|Volumes|ws)\b"),
    re.compile(r"/dev/(ttyUSB|ttyACM|serial|cu\.|tty\.)[A-Za-z0-9._-]*"),
)


def _utc_now() -> str:
    # UTC 时间避免不同 worker 时区影响 artifact 排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_flags() -> dict[str, Any]:
    # 每个输出层都重复 false flags，防止下游只读 summary 时误启主操作。
    return {
        "source": SOURCE,
        "status": STATUS,
        "software_proof": True,
        "not_proven": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


def _safe_text(value: Any, default: str = "") -> str:
    # 输出文本统一裁剪成短摘要，避免把原始日志、路径或凭证搬进 summary。
    if value is None:
        text = default
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    text = text.replace("\n", " ").replace("\r", " ")
    return text[:180] or default


def _encoded(value: Any) -> str:
    # 统一扫描嵌套 dict/list，避免敏感字段藏在数组或 wrapper 里。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _read_json(path: Path) -> tuple[dict[str, Any], str]:
    # 显式 --input 是合同入口；不可读或非 object 时只输出 blocked 状态。
    try:
        payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "input_missing"
    except json.JSONDecodeError:
        return {}, "input_invalid_json"
    except (OSError, UnicodeDecodeError):
        return {}, "input_read_error"
    if not isinstance(payload, dict):
        return {}, "input_not_object"
    return payload, ""


def _safe_evidence_ref(value: Any) -> tuple[str, str]:
    # evidence_ref 是跨材料归档主键，路径化或 token 化都可能泄露环境信息。
    ref = _safe_text(value)
    if not ref:
        return "", "missing_evidence_ref"
    if not SAFE_EVIDENCE_REF_RE.fullmatch(ref):
        return "", "unsafe_evidence_ref_format"
    if PATH_LIKE_RE.search(ref) or TOKEN_LIKE_RE.search(ref):
        return "", "unsafe_evidence_ref_token_or_path"
    return ref, ""


def _unsafe_key_paths(value: Any, prefix: str = "") -> list[str]:
    # 字段名比字段值更可靠；一旦出现 raw/control/credential/hardware key 就拒绝整包。
    paths: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            key_path = f"{prefix}.{key_text}" if prefix else key_text
            if any(term in key_lower for term in FORBIDDEN_KEY_TERMS):
                paths.append(key_path)
            paths.extend(_unsafe_key_paths(child, key_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(_unsafe_key_paths(child, f"{prefix}[{index}]"))
    return paths


def _unsafe_text_reasons(value: Any) -> list[str]:
    # 正则只返回类别，不回显命中的原文，避免泄露本机路径或凭证片段。
    encoded = _encoded(value)
    reasons: list[str] = []
    if any(pattern.search(encoded) for pattern in UNSAFE_TEXT_PATTERNS):
        reasons.append("unsafe_success_control_credential_ros_hardware_or_path_text")
    return reasons


def _global_blockers(bundle: dict[str, Any], read_state: str) -> list[str]:
    # 全局 blocker 写入 artifact 顶层，方便 PM/Robot worker 判断不可消费原因。
    blockers: list[str] = []
    if read_state:
        blockers.append(read_state)
    if _unsafe_key_paths(bundle):
        blockers.append("bundle_contains_forbidden_raw_control_credential_ros_or_hardware_fields")
    blockers.extend(_unsafe_text_reasons(bundle))
    return sorted(set(blockers))


def _terminal_result_type(bundle: dict[str, Any]) -> tuple[str, str]:
    # 只允许三种终态，避免 field owner 自创 success 类 result 绕过材料要求。
    result_type = _safe_text(bundle.get("terminal_result_type"))
    if result_type not in TERMINAL_RESULT_TYPES:
        return "", "unsupported_terminal_result_type"
    return result_type, ""


def _material_entries(bundle: dict[str, Any]) -> dict[str, dict[str, Any]]:
    # 支持 dict/list 两种手工 JSON 形态，但只接受 object material 条目。
    raw = bundle.get("materials", bundle.get("material_refs", {}))
    entries: dict[str, dict[str, Any]] = {}
    if isinstance(raw, dict):
        for name, payload in raw.items():
            if isinstance(payload, dict):
                entries[str(name)] = {"name": str(name), **payload}
            else:
                entries[str(name)] = {"name": str(name), "summary": payload}
    elif isinstance(raw, list):
        for payload in raw:
            if isinstance(payload, dict):
                name = _safe_text(payload.get("name") or payload.get("material") or payload.get("material_name"))
                if name:
                    entries[name] = payload
    return entries


def _material_ref(material: dict[str, Any], top_ref: str) -> tuple[str, str]:
    # material 可省略 evidence_ref，此时继承顶层 ref；显式 ref 必须完全一致。
    ref_value = material.get("evidence_ref", material.get("safe_evidence_ref", top_ref))
    return _safe_evidence_ref(ref_value)


def _accepted_material(name: str, material: dict[str, Any], safe_ref: str) -> dict[str, Any]:
    # accepted 只是“可人工复核的脱敏材料形状”，不是终态验证通过。
    return {
        **_safe_flags(),
        "name": name,
        "status": "accepted_for_terminal_result_manual_review_not_proven",
        "safe_evidence_ref": safe_ref,
        "summary": _safe_text(material.get("summary") or material.get("description"), "metadata_shape_present"),
        "material_ref": _safe_text(material.get("material_ref") or material.get("ref"), "metadata_ref_present"),
    }


def _rejected_material(name: str, reason: str) -> dict[str, str]:
    # rejected 只记录原因，不复制原始字段值，避免二次泄露。
    return {"name": name, "reason": reason}


def _scan_material(name: str, material: dict[str, Any], top_ref: str) -> tuple[dict[str, Any] | None, dict[str, str] | None]:
    # 单项材料同时满足 ref、安全字段和短摘要，才进入 accepted_materials。
    material_ref, ref_error = _material_ref(material, top_ref)
    if ref_error:
        return None, _rejected_material(name, ref_error)
    if material_ref != top_ref:
        return None, _rejected_material(name, "nested_material_evidence_ref_mismatch")
    if _unsafe_key_paths(material) or _unsafe_text_reasons(material):
        return None, _rejected_material(name, "unsafe_raw_control_credential_ros_hardware_or_path_material")
    if not _safe_text(material.get("summary") or material.get("description") or material.get("material_ref") or material.get("ref")):
        return None, _rejected_material(name, "missing_safe_material_summary_or_ref")
    return _accepted_material(name, material, material_ref), None


def build_verified_terminal_result_material_intake(input_path: Path) -> tuple[dict[str, Any], dict[str, Any], int]:
    """构建 artifact 与 summary；返回码不代表真实 delivery/dropoff/cancel 成功。"""
    bundle, read_state = _read_json(input_path)
    blockers = _global_blockers(bundle, read_state)
    top_ref, ref_error = _safe_evidence_ref(bundle.get("evidence_ref"))
    result_type, type_error = _terminal_result_type(bundle)
    materials = _material_entries(bundle)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []

    if ref_error:
        rejected.append(_rejected_material("evidence_ref", ref_error))
    if type_error:
        rejected.append(_rejected_material("terminal_result_type", type_error))

    required = REQUIRED_MATERIALS.get(result_type, ())
    for name, material in sorted(materials.items()):
        if result_type and name not in required:
            rejected.append(_rejected_material(name, "unsupported_material_for_terminal_result_type"))
            continue
        if top_ref and not ref_error:
            accepted_item, rejected_item = _scan_material(name, material, top_ref)
            if accepted_item:
                accepted.append(accepted_item)
            if rejected_item:
                rejected.append(rejected_item)

    accepted_names = {item["name"] for item in accepted}
    missing = [name for name in required if name not in accepted_names]
    rejected.extend(_rejected_material("bundle", blocker) for blocker in blockers)

    if read_state:
        intake_status = READ_STATUS
        exit_code = 2
    elif blockers:
        intake_status = UNSAFE_STATUS
        exit_code = 2
    elif type_error:
        intake_status = TYPE_STATUS
        exit_code = 2
    elif ref_error or any(item["reason"] == "nested_material_evidence_ref_mismatch" for item in rejected):
        intake_status = REF_STATUS
        exit_code = 2
    elif rejected:
        intake_status = UNSAFE_STATUS
        exit_code = 2
    elif missing:
        intake_status = MISSING_STATUS
        exit_code = 0
    else:
        intake_status = READY_STATUS
        exit_code = 0

    safe_ref = top_ref if not ref_error and intake_status not in {REF_STATUS, READ_STATUS} else ""
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        **_safe_flags(),
        "capability": CAPABILITY,
        "verified_terminal_result_material_intake": intake_status,
        "intake_status": intake_status,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": safe_ref,
        "same_evidence_ref_required": True,
        "terminal_result_type": result_type,
        "allowed_terminal_result_types": list(TERMINAL_RESULT_TYPES),
        "required_materials": list(required),
        "accepted_materials": accepted,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "accepted_count": len(accepted),
        "missing_count": len(missing),
        "rejected_count": len(rejected),
        "next_action": (
            "route_to_terminal_result_manual_review_not_proven"
            if intake_status == READY_STATUS
            else "collect_safe_terminal_result_materials_and_rerun_intake"
        ),
        "owner_handoff": ""robot-algorithm-engineer"",
        "not_proven_items": [
            "real_nav2_fixed_route_pass",
            "real_elevator_field_pass",
            "real_dropoff_or_cancel_completion",
            "verified_terminal_delivery_result",
            "delivery_success",
        ],
        "safety_markers": [
            "software_proof",
            "not_proven",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
        ],
        "boundary_note": (
            "software_proof; not_proven; delivery_success=false; "
            "primary_actions_enabled=false; safe_to_control=false"
        ),
    }
    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": artifact["generated_at"],
        **_safe_flags(),
        "capability": CAPABILITY,
        "verified_terminal_result_material_intake": intake_status,
        "intake_status": intake_status,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": safe_ref,
        "same_evidence_ref_required": True,
        "summary_only": True,
        "safe_to_render_on_phone": True,
        "terminal_result_type": result_type,
        "required_materials": list(required),
        "accepted_materials": [item["name"] for item in accepted],
        "missing_materials": missing,
        "rejected_materials": rejected,
        "accepted_count": len(accepted),
        "missing_count": len(missing),
        "rejected_count": len(rejected),
        "next_action": artifact["next_action"],
        "owner_handoff": artifact["owner_handoff"],
        "boundary_note": artifact["boundary_note"],
    }
    return artifact, summary, exit_code


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    # output-dir 由 CLI 创建，便于 sprint evidence 目录由 worker 一次生成。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build trashbot.verified_terminal_result_material_intake.v1 software_proof artifact from --input; "
            "keeps not_proven, delivery_success=false, primary_actions_enabled=false, safe_to_control=false."
        )
    )
    parser.add_argument("--input", type=Path, required=True, help="terminal result evidence bundle JSON")
    parser.add_argument("--output-dir", type=Path, required=True, help="directory for sanitized artifact and summary JSON")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_verified_terminal_result_material_intake(args.input)
    _write_json(args.output_dir / "verified_terminal_result_material_intake.json", artifact)
    _write_json(args.output_dir / "verified_terminal_result_material_intake_summary.json", summary)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
