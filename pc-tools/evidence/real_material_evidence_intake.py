#!/usr/bin/env python3
"""生成 real_material_evidence_intake 的 fail-closed PC evidence gate。"""

from __future__ import annotations

# 设计约束 01：本 gate 只做 PC 侧材料摘要 intake，不连接真实硬件、真实手机或公网。
# 设计约束 02：本 gate 不读取串口、UART、ROS graph、OSS/CDN、DB/queue 或生产凭证。
# 设计约束 03：sample manifest 只能验证合同形状，不能被下游误读成真实材料到位。
# 设计约束 04：四类 material group 必须共用同一个 safe evidence_ref，否则 fail closed。
# 设计约束 05：空 evidence_ref、不安全字符、路径、token、凭证和成功/控制字段必须拒绝。
# 设计约束 06：输出只保留脱敏后的材料名、状态、短说明和 owner handoff。
# 设计约束 07：accepted 只表示材料摘要形状可进入人工复核，不代表真实验收通过。
# 设计约束 08：所有输出必须保持 software_proof、not_proven。
# 设计约束 09：所有输出必须保持 delivery_success=false。
# 设计约束 10：所有输出必须保持 primary_actions_enabled=false 和 safe_to_control=false。
# 设计约束 11：PR #5 review thread ID 必须保留，且不能声明 PR #5 可关闭。
# 设计约束 12：vendor 来源只证明本地资料边界，不证明 WAVE ROVER/UART/HIL 或传感器到位。

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.real_material_evidence_intake.v1"
SUMMARY_SCHEMA = "trashbot.real_material_evidence_intake_summary.v1"
TEMPLATE_SCHEMA = "trashbot.real_material_manifest_template.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
STATUS = "not_proven"
EVIDENCE_BOUNDARY = "software_proof_docker_real_material_evidence_intake_gate"
SAMPLE_MANIFEST_SCHEMA = "trashbot.real_material_evidence_sample_manifest.v1"
PR5_REVIEW_THREAD_ID = "PRRT_kwDOSWB9286CJ3tX"
DEFAULT_TEMPLATE_EVIDENCE_REF = "field-material-template-2026-05-19T22-23Z"

READY_STATUS = "ready_for_real_material_evidence_review_not_proven"
TEMPLATE_READY_STATUS = "ready_for_field_owner_submission_pack_not_proven"
BLOCKED_MISSING_MANIFEST = "blocked_missing_real_material_manifest"
BLOCKED_MISSING_ITEMS = "blocked_missing_real_material_items"
BLOCKED_REJECTED_ITEMS = "blocked_rejected_real_material_items"
BLOCKED_UNSAFE_MANIFEST = "blocked_unsafe_real_material_manifest"
BLOCKED_EVIDENCE_REF = "blocked_unsafe_or_inconsistent_evidence_ref"

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VENDOR_INDEX = REPO_ROOT / "docs" / "vendor" / "VENDOR_INDEX.md"

# 已读 vendor 来源；输出只引用 repo 相对路径，不复制供应商正文或本机路径。
VENDOR_SOURCE_REFS = (
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
)

# group 定义来自本 sprint tech-plan；required items 缺失时只能给下一步履约动作。
MATERIAL_GROUPS: dict[str, dict[str, Any]] = {
    "o5_external": {
        "title": "Objective 5 external real material",
        "objective_ref": "Objective 5",
        "owner_handoff": "product-okr-owner",
        "required_items": (
            "public_https_tls",
            "4g_sim",
            "oss_cdn_live_traffic",
            "production_db_queue",
            "worker_migration_cutover",
            "external_proof",
        ),
        "next_action": "collect_real_external_cloud_network_and_db_queue_materials",
    },
    "o1_pr5_hardware": {
        "title": "Objective 1 / PR #5 hardware real material",
        "objective_ref": "Objective 1",
        "owner_handoff": "hardware-engineer",
        "required_items": (
            "2d_lidar_sku_source_receipt",
            "tof_sku_source_receipt",
            "procurement_install_wiring_power_calibration",
            "hil_entry",
            "wave_rover_uart_hil_packet",
        ),
        "next_action": "collect_pr5_sensor_and_wave_rover_uart_hil_materials",
    },
    "pr4_route_elevator": {
        "title": "PR #4 route/elevator real material",
        "objective_ref": "PR #4 / Objective 2 / Objective 3",
        "owner_handoff": "autonomy-engineer",
        "required_items": (
            "nav2_fixed_route_runtime_log",
            "route_completion_signal",
            "field_task_record",
            "elevator_door_state",
            "target_floor_confirmation",
            "human_assistance_record",
            "dropoff_cancel_material",
            "delivery_result",
        ),
        "next_action": "collect_real_route_elevator_field_materials",
    },
    "o4_real_phone": {
        "title": "Objective 4 real phone material",
        "objective_ref": "Objective 4",
        "owner_handoff": "full-stack-software-engineer",
        "required_items": (
            "real_phone_browser_session",
            "production_app",
            "pwa_prompt_user_choice",
            "true_phone_browser_acceptance",
        ),
        "next_action": "collect_real_phone_device_acceptance_materials",
    },
}

SAFE_EVIDENCE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,80}$")
PATH_LIKE_RE = re.compile(r"(^/|[A-Za-z]:\\|\\|/|file://)")
TOKEN_LIKE_RE = re.compile(r"(?i)(token|secret|password|authorization|bearer|access[_-]?key|oss_access_key|sk=|ak=)")

# 成功、控制、凭证、绝对路径和敏感材料字段一律阻断，避免 intake 变成 proof。
FORBIDDEN_KEYS = {
    "delivery_success",
    "primary_actions_enabled",
    "safe_to_control",
    "hil_pass",
    "field_pass",
    "control_enabled",
    "credential",
    "credentials",
    "token",
    "secret",
    "password",
    "authorization",
    "access_key",
    "oss_access_key_secret",
    "db_url",
    "queue_url",
}

UNSAFE_TEXT_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(hil_pass|field_pass|control_enabled)\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(Bearer\s+|Authorization\s*:|password|private_key|OSS_ACCESS_KEY_SECRET)\b"),
    re.compile(r"(?i)\b(token|secret|access[_-]?key|password)\b\s*[:=]"),
    re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://"),
    re.compile(r"(?<![A-Za-z0-9_.-])/(Users|tmp|var|etc|home|run|private|Volumes|ws)\b"),
    re.compile(r"/dev/(ttyUSB|ttyACM|serial|cu\.|tty\.)[A-Za-z0-9._-]*"),
)


def _utc_now() -> str:
    # UTC 输出便于不同 Docker worker 的 artifact 按字面排序。
    return datetime.now(timezone.utc).isoformat()


def _repo_ref(path: Path) -> str:
    # artifact 不写入开发机绝对路径，只写 repo 相对引用。
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except (OSError, ValueError):
        return path.name


def _safe_flags() -> dict[str, Any]:
    # 每层重复 fail-closed 字段，防止下游只读取局部对象时误启控制。
    return {
        "source": SOURCE,
        "status": STATUS,
        "not_proven": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


def _safe_text(value: Any, default: str = "") -> str:
    # 文本进入输出前先裁剪，避免长材料、凭证或日志全文流入 summary。
    if value is None:
        text = default
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    text = text.replace("\n", " ").replace("\r", " ")
    return text[:160] or default


def _encoded(value: Any) -> str:
    # 统一扫描嵌套 dict/list 的键和值，捕获伪装 success/control 字段。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_unsafe_text(value: Any) -> bool:
    # 正则用于捕获字符串里的成功/凭证/路径信号，字段名由另一个函数检查。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in UNSAFE_TEXT_PATTERNS)


def _unsafe_key_paths(value: Any, prefix: str = "") -> list[str]:
    # 禁止字段即使命中 false 也拒绝，因为 intake contract 不允许这些字段出现。
    paths: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            key_path = f"{prefix}.{key_text}" if prefix else key_text
            if key_text.lower() in FORBIDDEN_KEYS:
                paths.append(key_path)
            paths.extend(_unsafe_key_paths(child, key_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(_unsafe_key_paths(child, f"{prefix}[{index}]"))
    return paths


def _read_json(path: Path | None) -> tuple[dict[str, Any], str]:
    # CLI 缺 manifest 时使用内置 sample；显式传入但不可读时 fail closed。
    if path is None:
        return _sample_manifest(), "sample_manifest"
    try:
        payload = json.loads(path.expanduser().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "missing"
    except json.JSONDecodeError:
        return {}, "invalid_json"
    except (OSError, UnicodeDecodeError):
        return {}, "read_error"
    if not isinstance(payload, dict):
        return {}, "invalid_json"
    return payload, ""


def _sample_manifest() -> dict[str, Any]:
    # sample 只提供安全 evidence_ref 和 group 结构，不包含真实材料条目。
    return {
        "schema": SAMPLE_MANIFEST_SCHEMA,
        "evidence_ref": "sample-real-material-evidence-2026-05-19",
        "material_groups": [
            {"material_group": group_id, "evidence_ref": "sample-real-material-evidence-2026-05-19", "items": []}
            for group_id in MATERIAL_GROUPS
        ],
    }


def _template_item(group_id: str, item_name: str, group_spec: dict[str, Any], evidence_ref: str) -> dict[str, Any]:
    # template item 是给现场 owner 填写的安全提示，不携带真实路径、凭证或成功结论。
    return {
        **_safe_flags(),
        "name": item_name,
        "required": True,
        "safe_evidence_ref": evidence_ref,
        "summary_hint": (
            f"fill redacted {item_name} material summary for manual review only; "
            "state what was collected, source owner, time window, and any missing fields"
        ),
        "material_ref_hint": (
            f"fill redacted handoff reference for {group_id}.{item_name}; "
            "use a packet id, ticket id, or checksum label, not a raw local path"
        ),
        "owner_handoff": group_spec["owner_handoff"],
        "objective_ref": group_spec["objective_ref"],
        "next_action": group_spec["next_action"],
        "safety_markers": [
            "software_proof",
            "not_proven",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
        ],
    }


def build_real_material_manifest_template(evidence_ref: str = DEFAULT_TEMPLATE_EVIDENCE_REF) -> dict[str, Any]:
    """生成 field owner 可交付的真实材料 manifest template；不制造 proof claim。"""
    safe_ref, ref_error = _safe_evidence_ref(evidence_ref)
    if ref_error:
        raise ValueError(f"unsafe template evidence_ref: {ref_error}")

    material_groups: list[dict[str, Any]] = []
    for group_id, group_spec in MATERIAL_GROUPS.items():
        # 每个 group 直接展开 required item，现场 owner 不需要再查脚本常量。
        material_groups.append(
            {
                **_safe_flags(),
                "material_group": group_id,
                "title": group_spec["title"],
                "safe_evidence_ref": safe_ref,
                "same_evidence_ref_required": True,
                "objective_ref": group_spec["objective_ref"],
                "owner_handoff": group_spec["owner_handoff"],
                "next_action": group_spec["next_action"],
                "required_items": [
                    _template_item(group_id, item_name, group_spec, safe_ref)
                    for item_name in group_spec["required_items"]
                ],
                "safety_markers": [
                    "software_proof",
                    "not_proven",
                    "delivery_success=false",
                    "primary_actions_enabled=false",
                    "safe_to_control=false",
                ],
            }
        )

    return {
        "schema": TEMPLATE_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        **_safe_flags(),
        "real_material_manifest_template": TEMPLATE_READY_STATUS,
        "template_status": TEMPLATE_READY_STATUS,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": safe_ref,
        "same_evidence_ref_required": True,
        "submission_pack": {
            **_safe_flags(),
            "purpose": "field_owner_manifest_submission_pack",
            "instructions": [
                "keep the same safe_evidence_ref on every group and item",
                "replace summary_hint and material_ref_hint with redacted material metadata before intake",
                "do not paste local paths, serial devices, DB URLs, OSS keys, passwords, tokens, or success/control claims",
                "rerun real_material_evidence_intake after the field owner fills the manifest",
            ],
            "owner_handoff": "product-okr-owner",
            "next_action": "fill_real_material_manifest_and_rerun_intake",
        },
        "material_groups": material_groups,
        "review_refs": {
            "objective_5": "Objective 5 remains blocked pending real external proof",
            "objective_1": "Objective 1 / PR #5 remains blocked pending real hardware materials",
            "pr5_thread_id": PR5_REVIEW_THREAD_ID,
            "pr5_state": "blocked_pending_real_materials_not_closed",
        },
        "vendor_source_boundary": {
            "vendor_index": _repo_ref(DEFAULT_VENDOR_INDEX),
            "vendor_index_exists": DEFAULT_VENDOR_INDEX.exists(),
            "source_refs": list(VENDOR_SOURCE_REFS),
            "hardware_conclusion": (
                "template cites local vendor boundaries only; it does not prove WAVE ROVER UART, HIL, "
                "real sensor procurement, phone acceptance, route/elevator completion, or cloud readiness"
            ),
        },
        "boundary_note": (
            "software_proof; not_proven; delivery_success=false; "
            "primary_actions_enabled=false; safe_to_control=false"
        ),
    }


def _manifest_groups(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    # 同时兼容 list 和 dict 形态，方便 field owner 手工编辑 manifest。
    raw_groups = manifest.get("material_groups", {})
    groups: dict[str, dict[str, Any]] = {}
    if isinstance(raw_groups, dict):
        for group_id, payload in raw_groups.items():
            if isinstance(payload, dict):
                groups[str(group_id)] = {"material_group": str(group_id), **payload}
    elif isinstance(raw_groups, list):
        for payload in raw_groups:
            if isinstance(payload, dict):
                group_id = _safe_text(payload.get("material_group") or payload.get("group_id"))
                if group_id:
                    groups[group_id] = payload
    return groups


def _safe_evidence_ref(value: Any) -> tuple[str, str]:
    # evidence_ref 是跨组归档键，不能为空、路径化或含 token 语义。
    ref = _safe_text(value)
    if not ref:
        return "", "missing_evidence_ref"
    if not SAFE_EVIDENCE_REF_RE.fullmatch(ref):
        return "", "unsafe_evidence_ref_format"
    if PATH_LIKE_RE.search(ref) or TOKEN_LIKE_RE.search(ref):
        return "", "unsafe_evidence_ref_token_or_path"
    return ref, ""


def _items_by_name(group_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    # items 支持 list/dict；只接收 object，弱类型条目会在 rejected_items 中体现。
    raw_items = group_payload.get("items", {})
    items: dict[str, dict[str, Any]] = {}
    if isinstance(raw_items, dict):
        for item_name, item_payload in raw_items.items():
            if isinstance(item_payload, dict):
                items[str(item_name)] = {"name": str(item_name), **item_payload}
            else:
                items[str(item_name)] = {"name": str(item_name), "value": item_payload}
    elif isinstance(raw_items, list):
        for item_payload in raw_items:
            if isinstance(item_payload, dict):
                item_name = _safe_text(item_payload.get("name") or item_payload.get("item"))
                if item_name:
                    items[item_name] = item_payload
    return items


def _accepted_item(item_name: str, item_payload: dict[str, Any]) -> dict[str, Any]:
    # accepted item 仍是待人工复核材料，不携带 raw path/checksum/credential。
    return {
        "name": item_name,
        "status": "accepted_for_manual_review_not_proven",
        "summary": _safe_text(item_payload.get("summary") or item_payload.get("description"), "metadata_shape_present"),
        "material_ref": _safe_text(item_payload.get("material_ref") or item_payload.get("ref"), "metadata_ref_present"),
    }


def _rejected_item(name: str, reason: str) -> dict[str, str]:
    # rejected 只给原因，避免复制问题材料。
    return {"name": name, "reason": reason}


def _scan_item(item_name: str, item_payload: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, str] | None]:
    # 单项材料只校验合同形状；真实内容仍必须由 owner 后续线下复核。
    if _unsafe_key_paths(item_payload) or _has_unsafe_text(item_payload):
        return None, _rejected_item(item_name, "unsafe_success_control_credential_path_or_token_field")
    if not _safe_text(item_payload.get("summary") or item_payload.get("description") or item_payload.get("material_ref") or item_payload.get("ref")):
        return None, _rejected_item(item_name, "missing_safe_material_summary_or_ref")
    return _accepted_item(item_name, item_payload), None


def _evaluate_group(
    group_id: str,
    group_payload: dict[str, Any],
    manifest_ref: str,
    group_ref_error: str,
    global_blockers: list[str],
) -> dict[str, Any]:
    # group 级别输出保持固定字段，方便 Robot/mobile 后续白名单消费。
    group_spec = MATERIAL_GROUPS[group_id]
    group_ref, local_ref_error = _safe_evidence_ref(group_payload.get("evidence_ref") or manifest_ref)
    ref_error = group_ref_error or local_ref_error
    items = _items_by_name(group_payload)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []

    for item_name, item_payload in sorted(items.items()):
        if item_name not in group_spec["required_items"]:
            rejected.append(_rejected_item(item_name, "unsupported_material_item_for_group"))
            continue
        accepted_item, rejected_item = _scan_item(item_name, item_payload)
        if accepted_item:
            accepted.append(accepted_item)
        if rejected_item:
            rejected.append(rejected_item)

    accepted_names = {item["name"] for item in accepted}
    missing = [name for name in group_spec["required_items"] if name not in accepted_names]
    if ref_error:
        rejected.insert(0, _rejected_item("evidence_ref", ref_error))
    if global_blockers:
        rejected.extend(_rejected_item("manifest", blocker) for blocker in global_blockers)

    if rejected:
        intake_status = BLOCKED_REJECTED_ITEMS
    elif missing:
        intake_status = BLOCKED_MISSING_ITEMS
    else:
        intake_status = READY_STATUS

    return {
        **_safe_flags(),
        "material_group": group_id,
        "title": group_spec["title"],
        "objective_ref": group_spec["objective_ref"],
        "intake_status": intake_status,
        "safe_evidence_ref": group_ref if not ref_error else "",
        "same_evidence_ref_required": True,
        "accepted_items": accepted,
        "missing_items": missing,
        "rejected_items": rejected,
        "next_action": group_spec["next_action"] if intake_status != READY_STATUS else "route_to_owner_manual_review_not_proven",
        "owner_handoff": group_spec["owner_handoff"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safety_markers": [
            "software_proof",
            "not_proven",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
        ],
    }


def _global_manifest_blockers(manifest: dict[str, Any], read_state: str, groups_payload: dict[str, dict[str, Any]]) -> list[str]:
    # 全局 blocker 会写入每个 group，保证缺陷在 summary 面也可见。
    blockers: list[str] = []
    if read_state in {"missing", "invalid_json", "read_error"}:
        blockers.append(f"manifest_{read_state}")
    unsafe_paths = _unsafe_key_paths(manifest)
    if unsafe_paths:
        blockers.append("manifest_contains_forbidden_fields")
    if _has_unsafe_text(manifest):
        blockers.append("manifest_contains_unsafe_success_control_credential_path_or_token_copy")
    if any(group_id not in MATERIAL_GROUPS for group_id in groups_payload):
        blockers.append("manifest_contains_unsupported_material_group")
    return blockers


def build_real_material_evidence_intake(
    manifest_path: Path | None = None,
    *,
    vendor_index: Path = DEFAULT_VENDOR_INDEX,
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """构建 artifact 与 summary；返回码 0 只表示 gate 成功生成 fail-closed 输出。"""
    manifest, read_state = _read_json(manifest_path)
    manifest_ref, manifest_ref_error = _safe_evidence_ref(manifest.get("evidence_ref"))
    groups_payload = _manifest_groups(manifest)
    global_blockers = _global_manifest_blockers(manifest, read_state, groups_payload)

    group_refs: set[str] = set()
    for payload in groups_payload.values():
        group_ref, error = _safe_evidence_ref(payload.get("evidence_ref") or manifest_ref)
        if group_ref and not error:
            group_refs.add(group_ref)
    group_ref_error = ""
    if len(group_refs) > 1:
        group_ref_error = "cross_group_evidence_ref_mismatch"
    elif manifest_ref_error:
        group_ref_error = manifest_ref_error

    material_groups = [
        _evaluate_group(
            group_id,
            groups_payload.get(group_id, {"evidence_ref": manifest_ref, "items": []}),
            manifest_ref,
            group_ref_error,
            global_blockers,
        )
        for group_id in MATERIAL_GROUPS
    ]

    rejected_count = sum(len(group["rejected_items"]) for group in material_groups)
    missing_count = sum(len(group["missing_items"]) for group in material_groups)
    accepted_count = sum(len(group["accepted_items"]) for group in material_groups)
    if global_blockers or group_ref_error:
        intake_status = BLOCKED_UNSAFE_MANIFEST if global_blockers else BLOCKED_EVIDENCE_REF
        exit_code = 2
    elif rejected_count:
        intake_status = BLOCKED_REJECTED_ITEMS
        exit_code = 2
    elif missing_count:
        intake_status = BLOCKED_MISSING_ITEMS
        exit_code = 0
    elif read_state == "missing":
        intake_status = BLOCKED_MISSING_MANIFEST
        exit_code = 2
    else:
        intake_status = READY_STATUS
        exit_code = 0

    safe_ref = manifest_ref if manifest_ref and not group_ref_error else ""
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        **_safe_flags(),
        "real_material_evidence_intake": intake_status,
        "intake_status": intake_status,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": safe_ref,
        "same_evidence_ref_required": True,
        "manifest_source": read_state or _repo_ref(manifest_path or Path("embedded_sample_manifest")),
        "material_groups": material_groups,
        "accepted_count": accepted_count,
        "missing_count": missing_count,
        "rejected_count": rejected_count,
        "vendor_source_boundary": {
            "vendor_index": _repo_ref(vendor_index),
            "vendor_index_exists": vendor_index.exists(),
            "source_refs": list(VENDOR_SOURCE_REFS),
            "hardware_conclusion": (
                "vendor coverage bounds WAVE ROVER/UART/Orange Pi source facts only; "
                "it does not prove real 2D LiDAR/ToF procurement, WAVE ROVER UART/HIL, or PR #5 closure"
            ),
        },
        "review_refs": {
            "objective_5": "Objective 5 remains blocked pending real external proof",
            "objective_1": "Objective 1 / PR #5 remains blocked pending real hardware materials",
            "pr5_thread_id": PR5_REVIEW_THREAD_ID,
            "pr5_state": "blocked_pending_real_materials_not_closed",
        },
        "not_proven_items": [
            "real_public_https_tls",
            "real_4g_sim",
            "real_oss_cdn_live_traffic",
            "real_production_db_queue",
            "real_2d_lidar_or_tof_procurement_install_calibration",
            "real_wave_rover_uart_hil",
            "real_route_elevator_field_run",
            "real_phone_browser_acceptance",
            "delivery_success",
        ],
    }
    summary_groups = [
        {
            **_safe_flags(),
            "material_group": group["material_group"],
            "intake_status": group["intake_status"],
            "safe_evidence_ref": group["safe_evidence_ref"],
            "accepted_items": [item["name"] for item in group["accepted_items"]],
            "missing_items": group["missing_items"],
            "rejected_items": group["rejected_items"],
            "next_action": group["next_action"],
            "owner_handoff": group["owner_handoff"],
            "evidence_boundary": EVIDENCE_BOUNDARY,
        }
        for group in material_groups
    ]
    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": artifact["generated_at"],
        **_safe_flags(),
        "real_material_evidence_intake": intake_status,
        "intake_status": intake_status,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": safe_ref,
        "same_evidence_ref_required": True,
        "summary_only": True,
        "safe_to_render_on_phone": True,
        "material_groups": summary_groups,
        "group_count": len(summary_groups),
        "accepted_count": accepted_count,
        "missing_count": missing_count,
        "rejected_count": rejected_count,
        "next_action": "collect_missing_real_materials_and_rerun_intake" if intake_status != READY_STATUS else "route_to_owner_manual_review_not_proven",
        "owner_handoff": "product-okr-owner",
        "review_refs": artifact["review_refs"],
        "boundary_note": (
            "software_proof; not_proven; delivery_success=false; "
            "primary_actions_enabled=false; safe_to_control=false"
        ),
    }
    if _has_unsafe_text(artifact) or _has_unsafe_text(summary):
        # 理论上不会到这里；保留最后一道闸，避免输出被未来字段污染。
        artifact["real_material_evidence_intake"] = BLOCKED_UNSAFE_MANIFEST
        artifact["intake_status"] = BLOCKED_UNSAFE_MANIFEST
        summary["real_material_evidence_intake"] = BLOCKED_UNSAFE_MANIFEST
        summary["intake_status"] = BLOCKED_UNSAFE_MANIFEST
        exit_code = 2
    return artifact, summary, exit_code


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    # mkdir 让 sprint evidence 目录可由 gate 自行创建，但不写范围外路径内容。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build trashbot.real_material_evidence_intake.v1 software_proof artifact; "
            "keeps not_proven, delivery_success=false, primary_actions_enabled=false, safe_to_control=false."
        )
    )
    parser.add_argument("--manifest", type=Path, default=None, help="material manifest JSON; omitted uses an embedded safe sample manifest")
    parser.add_argument("--sample-manifest", type=Path, default=None, help="alias for --manifest when validating a sample manifest file")
    parser.add_argument("--output", type=Path, default=Path("real_material_evidence_intake.json"))
    parser.add_argument("--summary-output", type=Path, default=Path("real_material_evidence_intake_summary.json"))
    parser.add_argument("--template-output", type=Path, default=None, help="write a field-owner manifest template JSON without changing intake exit code")
    parser.add_argument(
        "--template-evidence-ref",
        default=DEFAULT_TEMPLATE_EVIDENCE_REF,
        help="safe evidence_ref shared by every material group in the generated template",
    )
    args = parser.parse_args(argv)

    # sample-manifest 是显式别名；两者同时给出时优先 manifest，避免隐式覆盖。
    manifest_path = args.manifest or args.sample_manifest
    artifact, summary, exit_code = build_real_material_evidence_intake(manifest_path)
    _write_json(args.output, artifact)
    _write_json(args.summary_output, summary)
    if args.template_output:
        try:
            template = build_real_material_manifest_template(args.template_evidence_ref)
        except ValueError as exc:
            parser.error(str(exc))
        _write_json(args.template_output, template)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
