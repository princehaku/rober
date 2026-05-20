#!/usr/bin/env python3
"""生成 hardware_sensor_hil_entry_callback_review_decision fail-closed 复核决策。"""

from __future__ import annotations

# 设计约束 01：本 gate 只读上一轮 callback intake artifact/summary/wrapper。
# 设计约束 02：本 gate 不读取真实 2D LiDAR、ToF、ROS graph、Nav2、串口或 HIL。
# 设计约束 03：review decision 只消费 accepted/missing/rejected 的脱敏摘要字段。
# 设计约束 04：ready 只表示 owner handoff 可继续，不表示真实采购、安装或 HIL。
# 设计约束 05：所有输出都固定 software_proof、hardware_material_pending。
# 设计约束 06：所有输出都固定 not_proven、delivery_success=false。
# 设计约束 07：所有输出都固定 primary_actions_enabled=false、safe_to_control=false。
# 设计约束 08：任何 raw UART/serial、完整路径、凭证、checksum 都 fail closed。
# 设计约束 09：任何 HIL pass、field pass、delivery success 或控制放行文案都 fail closed。
# 设计约束 10：vendor 来源只证明本地资料边界，不证明真实传感器或上车证据。
# 设计约束 11：summary 面向 Robot/mobile/Product，只输出白名单短字段。
# 设计约束 12：CLI --help dependency-free，适合 PC/Docker-only 环境。

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "trashbot.hardware_sensor_hil_entry_callback_review_decision.v1"
SUMMARY_SCHEMA = "trashbot.hardware_sensor_hil_entry_callback_review_decision_summary.v1"
INTAKE_SCHEMA = "trashbot.hardware_sensor_hil_entry_callback_intake.v1"
INTAKE_SUMMARY_SCHEMA = "trashbot.hardware_sensor_hil_entry_callback_intake_summary.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_hardware_sensor_hil_entry_callback_review_decision_gate"
INTAKE_BOUNDARY = "software_proof_docker_hardware_sensor_hil_entry_callback_intake_gate"

# repo 相对路径进入 artifact，避免把开发机绝对路径扩散到 Robot/mobile。
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VENDOR_INDEX = REPO_ROOT / "docs" / "vendor" / "VENDOR_INDEX.md"

# required material 名称沿用 callback intake，review 不能引入新材料类别。
REQUIRED_CALLBACK_MATERIALS = (
    "2d_lidar_sku_source_receipt",
    "tof_sku_source_receipt",
    "mounting",
    "wiring",
    "power",
    "calibration",
    "hil_entry_operator_result",
)

READY_INTAKE = "ready_for_hardware_sensor_hil_entry_callback_intake_not_proven"
READY_DECISION = "ready_for_hardware_sensor_hil_entry_callback_owner_handoff_not_proven"
BACKFILL_DECISION = "needs_hardware_sensor_hil_entry_callback_material_backfill_not_proven"
REJECTED_DECISION = "blocked_rejected_hardware_sensor_hil_entry_callback_materials_not_proven"
MISMATCH_DECISION = "blocked_evidence_ref_mismatch_not_proven"
UNSUPPORTED_DECISION = "blocked_missing_or_unsupported_hardware_sensor_hil_entry_callback_intake_not_proven"
WEAK_CONTRACT_DECISION = "blocked_weak_hardware_sensor_hil_entry_callback_intake_contract_not_proven"
UNSAFE_DECISION = "blocked_unsafe_hardware_sensor_hil_entry_callback_review_decision_copy_not_proven"

# not_proven 是下游 UI/closeout 的边界清单，不代表这些事项已经发生。
NOT_PROVEN = (
    "real_2d_lidar_sku_source_receipt_accepted",
    "real_2d_lidar_mounted_wired_powered_calibrated",
    "real_tof_sku_source_receipt_accepted",
    "real_tof_mounted_wired_powered_calibrated",
    "real_hil_entry_operator_checklist_complete",
    "real_sensor_hil_entry_pass",
    "real_nav2_slam_field_pass",
    "real_near_field_safety_gate_pass",
    "real_route_or_elevator_field_pass",
    "pr5_review_thread_resolved",
    "objective5_external_proof",
    "delivery_success",
)

# forbidden token 代表输入不是 sanitized summary/ref，必须在 review 前阻断。
FORBIDDEN_COPY = (
    "Authorization",
    "Bearer ",
    "access_key",
    "accessKey",
    "secret",
    "token",
    "password",
    "AK=",
    "SK=",
    "oss://",
    "postgres://",
    "postgresql://",
    "mysql://",
    "redis://",
    "amqp://",
    "mongodb://",
    "queue_url",
    "/cmd_vel",
    "/dev/ttyUSB",
    "/dev/ttyACM",
    "/dev/cu.",
    "/dev/tty.",
    "raw UART",
    "raw serial",
    "raw JSON",
    "raw_json",
    "complete artifact",
    "complete_artifact",
    "Traceback",
    "checksum",
)

# 这些正则避免用户把“通过/完成”文案藏在 summary 中。
SUCCESS_OR_CONTROL_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bhil_pass\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bHIL\s+(passed|pass|success|complete|completed)\b"),
    re.compile(r"(?i)\bfield\s+(pass|passed|success|complete|completed)\b"),
    re.compile(r"(?i)\b(delivery|installed|wired|powered|calibrated)\s+(pass|passed|success|complete|completed|done)\b"),
    re.compile(r"(送达|交付|安装|接线|上电|电源|标定|HIL|现场).{0,16}(完成|通过|成功|已验证)"),
)

# blocked artifact 也要脱敏，避免失败路径泄漏凭证或 raw device 信息。
SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\bAuthorization\s*:\s*[^,\s]+"), "Authorization: [REDACTED]"),
    (re.compile(r"(?i)\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://[^,\s]+"), "[REDACTED_URL]"),
    (re.compile(r"/cmd_vel\b"), "[REDACTED_ROS_TOPIC]"),
    (re.compile(r"/dev/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*"), "/dev/[REDACTED_DEVICE]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)raw[_ -]?(UART|serial|JSON)"), "[REDACTED_RAW_MATERIAL]"),
    (re.compile(r"(?i)complete[_ -]?artifact"), "[REDACTED_ARTIFACT]"),
)


def _utc_now() -> str:
    # UTC 时间让 macOS 与 Docker-only evidence 输出可稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any, default: str = "") -> str:
    # 所有自由文本先脱敏，再进入 artifact/summary。
    if value is None:
        text = default
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text or default


def _repo_ref(path: Path | None, fallback: str = "missing") -> str:
    # 输入文件引用只保留 repo 相对路径或 basename，不泄漏本机目录。
    if path is None:
        return fallback
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except (OSError, ValueError):
        return path.name or fallback


def _safe_ref(value: Any, fallback: str = "missing") -> str:
    # evidence_ref 不能像路径；像路径时降级 file:name 并由合同检查阻断。
    text = _safe_text(value)
    if not text:
        return fallback
    path = Path(text)
    if path.is_absolute() or "/" in text or "\\" in text:
        return f"file:{path.name}"
    return text


def _is_safe_ref(value: str) -> bool:
    # safe evidence_ref 要短、无路径、无 shell 空白，方便现场按号回填。
    if not value or value.startswith("file:") or value == "missing":
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:@-]{2,120}", value))


def _read_json(path: Path | None) -> tuple[dict[str, Any], str]:
    # 缺输入是 blocked 状态，不能抛 traceback 给用户或自动化。
    if path is None:
        return {}, "missing"
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


def _dict(value: Any) -> dict[str, Any]:
    # 只接受 object，避免弱类型 wrapper 绕过 schema/boundary。
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    # 上游可能缺字段；统一列表化，方便白名单截断。
    return list(value) if isinstance(value, (list, tuple)) else []


def _encoded(value: Any) -> str:
    # JSON 编码用于统一扫描 key/value；不可编码时退回脱敏文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _without_not_proven(value: Any) -> Any:
    # not_proven 会含 pass/success 目标名，成功扫描必须排除这个安全字段。
    if isinstance(value, dict):
        return {key: _without_not_proven(item) for key, item in value.items() if key != "not_proven"}
    if isinstance(value, list):
        return [_without_not_proven(item) for item in value]
    return value


def _has_success_or_control_claim(value: Any) -> bool:
    # 控制放行或成功文案只能来自真实验收；本 gate 看到即 blocked。
    encoded = _encoded(_without_not_proven(value))
    return any(pattern.search(encoded) for pattern in SUCCESS_OR_CONTROL_PATTERNS)


def _has_forbidden_copy(value: Any) -> bool:
    # raw material、凭证、完整路径、checksum 都不该进入 review decision。
    encoded = _encoded(value)
    if any(token in encoded for token in FORBIDDEN_COPY):
        return True
    return bool(re.search(r'(?i)"[^"]*(/Users/|/home/|/tmp/|/var/folders/)[^"]*"', encoded))


def _any_true_key(value: Any, key: str) -> bool:
    # 嵌套 true 字段同样会误导下游，必须递归阻断。
    if isinstance(value, dict):
        return any((k == key and item is True) or _any_true_key(item, key) for k, item in value.items())
    if isinstance(value, list):
        return any(_any_true_key(item, key) for item in value)
    if isinstance(value, str):
        return bool(re.search(rf"(?i)\b{re.escape(key)}\s*[:=]\s*true\b", value))
    return False


def _source_intake(payload: dict[str, Any]) -> dict[str, Any]:
    # 支持 artifact、summary，以及 Robot/mobile/automation wrapper 内嵌 summary。
    if payload.get("schema") in {INTAKE_SCHEMA, INTAKE_SUMMARY_SCHEMA}:
        return payload
    for key in (
        "callback_intake_summary",
        "hardware_sensor_hil_entry_callback_intake_summary",
        "robot_diagnostics_hardware_sensor_hil_entry_callback_intake_summary",
        "summary",
        "safe_copy",
    ):
        nested = _dict(payload.get(key))
        if nested.get("schema") == INTAKE_SUMMARY_SCHEMA:
            return nested
    return payload


def _schema_status(load_issue: str, payload: dict[str, Any], intake: dict[str, Any]) -> str:
    # 只接受上一轮 callback intake gate 的 artifact/summary，避免误吃其他 evidence。
    if load_issue:
        return "not_loaded"
    top_schema = _safe_text(payload.get("schema"))
    schema = _safe_text(intake.get("schema") or top_schema)
    boundary = _safe_text(intake.get("evidence_boundary") or payload.get("evidence_boundary"))
    source_boundary = _safe_text(intake.get("source_evidence_boundary") or payload.get("source_evidence_boundary"))
    if top_schema and top_schema not in {INTAKE_SCHEMA, INTAKE_SUMMARY_SCHEMA}:
        return "unsupported_schema"
    if schema not in {INTAKE_SCHEMA, INTAKE_SUMMARY_SCHEMA}:
        return "unsupported_schema"
    if boundary != INTAKE_BOUNDARY and source_boundary != INTAKE_BOUNDARY:
        return "unsupported_boundary"
    return "supported"


def _status(intake: dict[str, Any], payload: dict[str, Any]) -> str:
    # summary 与 artifact 字段名不同，这里统一成 source status。
    return _safe_text(
        intake.get("status")
        or intake.get("callback_intake_status")
        or intake.get("hardware_sensor_hil_entry_callback_intake")
        or payload.get("callback_intake_status")
        or payload.get("hardware_sensor_hil_entry_callback_intake"),
        "missing_source_status",
    )


def _material_names(value: Any) -> list[str]:
    # summary 可能只给 string list；artifact 可能给 object list。
    names: list[str] = []
    for item in _list(value):
        if isinstance(item, dict):
            name = _safe_text(item.get("material") or item.get("name"))
        else:
            name = _safe_text(item)
        if name:
            names.append(name)
    return names


def _material_entries(value: Any, names: list[str]) -> list[dict[str, str]]:
    # review artifact 只保留 material/ref/summary/review_status，不复制完整材料。
    entries: list[dict[str, str]] = []
    if _list(value) and all(isinstance(item, dict) for item in _list(value)):
        for item in _list(value)[:12]:
            data = _dict(item)
            name = _safe_text(data.get("material") or data.get("name"))
            if not name:
                continue
            entries.append(
                {
                    "material": name,
                    "review_status": "accepted_for_owner_review_not_proven",
                    "summary": _safe_text(data.get("summary"), "sanitized callback reference accepted for review")[:220],
                    "ref": _safe_ref(data.get("ref") or data.get("reference"), f"{name}_callback_ref"),
                }
            )
    else:
        for name in names[:12]:
            entries.append(
                {
                    "material": name,
                    "review_status": "accepted_for_owner_review_not_proven",
                    "summary": "sanitized callback reference accepted for review",
                    "ref": f"{name}_callback_ref",
                }
            )
    return entries


def _rejected_entries(value: Any) -> list[dict[str, str]]:
    # rejected 只保留材料名和原因；原因也要脱敏。
    rejected: list[dict[str, str]] = []
    for item in _list(value)[:12]:
        data = _dict(item)
        if data:
            material = _safe_text(data.get("material") or data.get("name"), "unknown")
            reason = _safe_text(data.get("reason"), "rejected_or_unsafe_callback_material")
        else:
            material = _safe_text(item, "unknown")
            reason = "rejected_or_unsafe_callback_material"
        rejected.append({"material": material, "reason": reason[:160]})
    return rejected


def _normalize_intake(payload: dict[str, Any], intake: dict[str, Any]) -> dict[str, Any]:
    # 归一化只提取白名单字段，避免把原 callback material 复制到决策层。
    accepted_source = intake.get("accepted_callback_materials", payload.get("accepted_callback_materials"))
    accepted_names = _material_names(accepted_source)
    missing = [_safe_text(item) for item in _list(intake.get("missing_required_materials", payload.get("missing_required_materials"))) if _safe_text(item)]
    rejected = _rejected_entries(intake.get("rejected_callback_materials", payload.get("rejected_callback_materials")))
    return {
        "schema": _safe_text(intake.get("schema") or payload.get("schema")),
        "source_schema": _safe_text(intake.get("source_schema") or payload.get("schema")),
        "evidence_boundary": _safe_text(intake.get("evidence_boundary") or payload.get("evidence_boundary")),
        "source": _safe_text(intake.get("source") or payload.get("source"), "missing"),
        "status": _status(intake, payload),
        "evidence_ref": _safe_ref(intake.get("evidence_ref") or payload.get("evidence_ref")),
        "accepted_names": accepted_names,
        "accepted_entries": _material_entries(accepted_source, accepted_names),
        "missing": missing,
        "rejected": rejected,
        "operator_result_summary": _dict(intake.get("operator_result_summary") or payload.get("operator_result_summary")),
        "owner_handoff": _owner_handoff(intake.get("owner_handoff") or payload.get("owner_handoff")),
        "next_required_evidence": _safe_list(intake.get("next_required_evidence") or payload.get("next_required_evidence"), 12),
        "hardware_material_status": _safe_text(intake.get("hardware_material_status") or payload.get("hardware_material_status"), "hardware_material_pending"),
        "hardware_material_pending": intake.get("hardware_material_pending", payload.get("hardware_material_pending")),
        "evidence_status": _safe_text(intake.get("evidence_status") or payload.get("evidence_status"), "not_proven"),
        "delivery_success": intake.get("delivery_success", payload.get("delivery_success")),
        "primary_actions_enabled": intake.get("primary_actions_enabled", payload.get("primary_actions_enabled")),
        "safe_to_control": intake.get("safe_to_control", payload.get("safe_to_control", False)),
    }


def _safe_list(value: Any, limit: int = 12) -> list[str]:
    # 下游列表统一截断，避免 summary 变成材料搬运层。
    items: list[str] = []
    for item in _list(value)[:limit]:
        text = _safe_text(item)
        if text:
            items.append(text[:240])
    return items


def _owner_handoff(value: Any) -> list[dict[str, str]]:
    # handoff 只保留 owner/action，不给 Robot 开任何控制动作。
    handoff: list[dict[str, str]] = []
    for item in _list(value)[:8]:
        data = _dict(item)
        owner = _safe_text(data.get("owner"), "Hardware Infra Engineer")
        action = _safe_text(data.get("action"), "Keep hardware_material_pending until reviewed real evidence lands.")
        handoff.append({"owner": owner[:80], "action": action[:260]})
    return handoff


def _weak_contract(normalized: dict[str, Any], evidence_ref: str) -> str:
    # 上游 bool 必须是真 bool；字符串 false 在消费侧可能被当成 truthy。
    if normalized["source"] != SOURCE:
        return "source"
    if not _is_safe_ref(evidence_ref):
        return "evidence_ref"
    if normalized["hardware_material_status"] != "hardware_material_pending":
        return "hardware_material_status"
    if normalized["evidence_status"] != "not_proven":
        return "evidence_status"
    for field in ("hardware_material_pending", "delivery_success", "primary_actions_enabled", "safe_to_control"):
        if not isinstance(normalized.get(field), bool):
            return field
    if normalized["hardware_material_pending"] is not True:
        return "hardware_material_pending_false"
    if normalized["delivery_success"] or normalized["primary_actions_enabled"] or normalized["safe_to_control"]:
        return "unsafe_true_boolean"
    return ""


def _decision(
    load_issue: str,
    schema_status: str,
    weak_contract: str,
    unsafe_copy: bool,
    success_or_control: bool,
    evidence_ref_mismatch: bool,
    normalized: dict[str, Any],
) -> str:
    # 决策顺序先挡输入合同，再挡危险复制，最后根据材料三类映射 owner 动作。
    if load_issue or schema_status != "supported":
        return UNSUPPORTED_DECISION
    if weak_contract:
        return WEAK_CONTRACT_DECISION
    if unsafe_copy or success_or_control:
        return UNSAFE_DECISION
    if evidence_ref_mismatch:
        return MISMATCH_DECISION
    if normalized["rejected"]:
        return REJECTED_DECISION
    if normalized["missing"] or normalized["status"] != READY_INTAKE:
        return BACKFILL_DECISION
    accepted = set(normalized["accepted_names"])
    if any(item not in accepted for item in REQUIRED_CALLBACK_MATERIALS):
        return BACKFILL_DECISION
    return READY_DECISION


def _decision_reasons(decision: str, normalized: dict[str, Any], details: dict[str, str]) -> list[str]:
    # reason 只说明复核依据，不扩大成真实硬件结论。
    if decision == READY_DECISION:
        return [
            "accepted_callback_materials cover all required sanitized categories",
            "callback intake source remains software_proof, hardware_material_pending, not_proven",
            "owner handoff can review the sanitized materials without control release",
        ]
    if decision == BACKFILL_DECISION:
        missing = normalized["missing"] or [item for item in REQUIRED_CALLBACK_MATERIALS if item not in set(normalized["accepted_names"])]
        return [f"missing_or_not_ready_callback_materials: {', '.join(missing)}"]
    if decision == REJECTED_DECISION:
        return [f"rejected_or_unsafe_callback_materials: {', '.join(item['material'] for item in normalized['rejected'])}"]
    if decision == MISMATCH_DECISION:
        return ["input evidence_ref does not match requested evidence_ref"]
    if decision == WEAK_CONTRACT_DECISION:
        return [f"weak callback intake contract: {details.get('weak_contract', 'unknown')}"]
    if decision == UNSAFE_DECISION:
        return ["input contains raw copy, credential/path/checksum, success claim, or control claim"]
    return [f"missing_or_unsupported_callback_intake: {details.get('schema_status', 'not_loaded')}"]


def _next_required_evidence(decision: str, normalized: dict[str, Any]) -> list[str]:
    # 下一步只要求人类补证据或复核，不触发 ROS、串口、HIL 或控制动作。
    if decision == READY_DECISION:
        return [
            "Hardware Infra Engineer reviews the sanitized SKU/source/receipt, mounting, wiring, power, calibration, and operator-result references.",
            "If review accepts them, collect separate real HIL-entry evidence before any HIL, field, PR #5, O5, or delivery claim.",
        ]
    if decision == BACKFILL_DECISION:
        missing = normalized["missing"] or [item for item in REQUIRED_CALLBACK_MATERIALS if item not in set(normalized["accepted_names"])]
        return [f"Backfill sanitized {item} callback summary/ref under the same evidence_ref." for item in missing]
    if decision == REJECTED_DECISION:
        return [f"Replace rejected {item['material']} material with a sanitized summary/ref only." for item in normalized["rejected"]]
    return [
        "Regenerate a supported hardware_sensor_hil_entry_callback_intake summary.",
        "Remove raw credentials, full paths, serial/UART details, checksums, complete artifacts, success wording, and control claims.",
    ]


def _owner_handoff_for_decision(decision: str, normalized: dict[str, Any]) -> list[dict[str, str]]:
    # handoff 保留上游 owner，再追加本轮复核动作。
    handoff = normalized["owner_handoff"][:5]
    if decision == READY_DECISION:
        handoff.extend(
            [
                {
                    "owner": "Hardware Infra Engineer",
                    "action": "Review sanitized callback materials and decide whether real HIL-entry evidence collection can be scheduled.",
                },
                {
                    "owner": "Product Manager / OKR Owner",
                    "action": "Keep PRRT_kwDOSWB9286CJ3tX unresolved until reviewer accepts real materials; do not mark delivery or O5 proof.",
                },
            ]
        )
    elif decision in {BACKFILL_DECISION, REJECTED_DECISION}:
        handoff.append(
            {
                "owner": "Hardware Infra Engineer",
                "action": "Request corrected sanitized callback material from field owner under the same evidence_ref.",
            }
        )
    elif not handoff:
        handoff.append(
            {
                "owner": "Hardware Infra Engineer",
                "action": "Repair callback intake schema, boundary, evidence_ref, or safety contract before review.",
            }
        )
    return handoff[:8]


def _rerun_commands(source_ref: str, evidence_ref: str) -> list[str]:
    # rerun command 只包含 PC evidence gate，不包含真实串口、ROS 或 HIL 操作。
    intake_arg = source_ref or "<hardware_sensor_hil_entry_callback_intake_json>"
    evidence_arg = f" --evidence-ref {evidence_ref}" if evidence_ref and evidence_ref != "missing" else ""
    return [
        f"python3 pc-tools/evidence/hardware_sensor_hil_entry_callback_review_decision_gate.py --callback-intake-json {intake_arg}{evidence_arg} --summary-output <callback_review_decision_summary_json>",
        "python3 -m unittest pc-tools/evidence/test_hardware_sensor_hil_entry_callback_review_decision_gate.py",
        'rg -n "hardware_sensor_hil_entry_callback_review_decision|software_proof_docker_hardware_sensor_hil_entry_callback_review_decision_gate|hardware_material_pending|not_proven" pc-tools/evidence docs/product',
    ]


def _safe_copy(artifact: dict[str, Any]) -> dict[str, Any]:
    # safe_copy 是给 Robot/mobile/Product 的短摘要，不包含完整 callback material。
    return {
        "schema": SUMMARY_SCHEMA,
        "status": artifact["review_decision"],
        "hardware_sensor_hil_entry_callback_review_decision": artifact["review_decision"],
        "evidence_ref": artifact["evidence_ref"],
        "accepted_materials": [item["material"] for item in artifact["accepted_materials"]],
        "missing_materials": artifact["missing_materials"],
        "rejected_materials": artifact["rejected_materials"],
        "decision_reasons": artifact["decision_reasons"],
        "source": SOURCE,
        "evidence_status": "not_proven",
        "hardware_material_status": "hardware_material_pending",
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


def _summary(artifact: dict[str, Any]) -> dict[str, Any]:
    # summary 字段保持稳定短小，便于 Robot diagnostics 和 mobile 只读展示。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source_schema": SCHEMA,
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": artifact["review_decision"],
        "hardware_sensor_hil_entry_callback_review_decision": artifact["review_decision"],
        "source_callback_intake_schema": artifact["source_callback_intake_schema"],
        "source_callback_intake_status": artifact["source_callback_intake_status"],
        "evidence_ref": artifact["evidence_ref"],
        "decision_reasons": artifact["decision_reasons"],
        "accepted_materials": [item["material"] for item in artifact["accepted_materials"]],
        "missing_materials": artifact["missing_materials"],
        "rejected_materials": artifact["rejected_materials"],
        "owner_handoff": artifact["owner_handoff"],
        "next_required_evidence": artifact["next_required_evidence"],
        "rerun_commands": artifact["rerun_commands"],
        "safe_copy": artifact["safe_copy"],
        "hardware_material_status": "hardware_material_pending",
        "hardware_material_pending": True,
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "boundary_note": "software_proof_docker_hardware_sensor_hil_entry_callback_review_decision_gate; delivery_success=false; primary_actions_enabled=false; safe_to_control=false; not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }


def build_hardware_sensor_hil_entry_callback_review_decision(
    callback_intake_json: str | Path | None = None,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 callback intake，生成 fail-closed review decision。"""

    intake_path = Path(callback_intake_json) if callback_intake_json else None
    payload, load_issue = _read_json(intake_path)
    intake_payload = _source_intake(payload) if payload else {}
    normalized = _normalize_intake(payload, intake_payload)
    safe_ref = _safe_ref(evidence_ref or normalized["evidence_ref"])
    schema_status = _schema_status(load_issue, payload, intake_payload)
    weak_contract = "" if load_issue or schema_status != "supported" else _weak_contract(normalized, safe_ref)
    evidence_ref_mismatch = bool(evidence_ref and normalized["evidence_ref"] not in {"missing", safe_ref} and normalized["evidence_ref"] != safe_ref)
    unsafe_copy = bool(payload and _has_forbidden_copy(payload))
    success_or_control = bool(
        payload
        and (
            _has_success_or_control_claim(payload)
            or _any_true_key(payload, "delivery_success")
            or _any_true_key(payload, "primary_actions_enabled")
            or _any_true_key(payload, "safe_to_control")
        )
    )
    decision = _decision(load_issue, schema_status, weak_contract, unsafe_copy, success_or_control, evidence_ref_mismatch, normalized)
    source_ref = _repo_ref(intake_path) if intake_path and intake_path.exists() else _safe_ref(intake_path, "missing")
    details = {"schema_status": schema_status, "weak_contract": weak_contract}

    artifact: dict[str, Any] = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": _utc_now(),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "evidence_ref": safe_ref,
        "source_callback_intake_ref": source_ref,
        "source_callback_intake_schema": normalized["schema"] or "missing",
        "source_callback_intake_boundary": normalized["evidence_boundary"] or "missing",
        "source_callback_intake_status": normalized["status"],
        "schema_status": schema_status,
        "weak_contract": weak_contract,
        "review_decision": decision,
        "hardware_sensor_hil_entry_callback_review_decision": decision,
        "decision_reasons": _decision_reasons(decision, normalized, details),
        "accepted_materials": normalized["accepted_entries"],
        "missing_materials": normalized["missing"],
        "rejected_materials": normalized["rejected"],
        "operator_result_summary": {
            "status": _safe_text(normalized["operator_result_summary"].get("status"), "missing_hil_entry_operator_result"),
            "summary": _safe_text(normalized["operator_result_summary"].get("summary"), "No sanitized operator result summary.")[:240],
        },
        "owner_handoff": _owner_handoff_for_decision(decision, normalized),
        "next_required_evidence": _next_required_evidence(decision, normalized),
        "rerun_commands": _rerun_commands(source_ref, safe_ref),
        "vendor_source_boundary": {
            "source": _repo_ref(DEFAULT_VENDOR_INDEX),
            "checked_readable_local_sources": [
                "docs/vendor/VENDOR_INDEX.md",
                "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
                "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
                "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
                "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
            ],
            "review_thread_context": "PRRT_kwDOSWB9286CJ3tX",
            "vendor_boundary": "Orange Pi Zero 3 / WAVE ROVER / UART JSON / firmware/vendor app source boundary only",
            "project_2d_lidar_tof_mounting_wiring_power_calibration_hil_proof": "not_proven",
        },
        "non_access_scope": [
            "physical_2d_lidar",
            "physical_tof",
            "wave_rover_runtime",
            "serial_uart",
            "ros_graph",
            "sensor_driver_runtime",
            "nav2_runtime",
            "hil_rig",
            "field_run",
            "delivery_execution",
            "objective5_external_cloud",
        ],
        "hardware_material_status": "hardware_material_pending",
        "hardware_material_pending": True,
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
    }
    artifact["safe_copy"] = _safe_copy(artifact)
    summary = _summary(artifact)
    artifact["callback_review_decision_summary"] = summary
    return artifact, summary, 0 if decision == READY_DECISION else 2


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 输出目录自动创建，便于 sprint evidence bundle 收集。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只生成 software-proof metadata，不访问真实硬件、串口或 HIL。
    parser = argparse.ArgumentParser(
        description="Generate trashbot.hardware_sensor_hil_entry_callback_review_decision.v1 from a sanitized callback intake artifact or summary."
    )
    parser.add_argument("--callback-intake-json", default="", help="Previous hardware_sensor_hil_entry_callback_intake artifact/summary/wrapper JSON.")
    parser.add_argument("--evidence-ref", default="", help="Optional safe evidence_ref override; mismatches fail closed.")
    parser.add_argument("--output", default="", help="Write full HIL-entry callback review decision artifact JSON.")
    parser.add_argument("--summary-output", default="", help="Write compact HIL-entry callback review decision summary JSON.")
    parser.add_argument("--once-json", action="store_true", help="Print full artifact JSON to stdout.")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_hardware_sensor_hil_entry_callback_review_decision(
        args.callback_intake_json or None,
        evidence_ref=args.evidence_ref,
    )
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"hardware_sensor_hil_entry_callback_review_decision: artifact_file:{Path(args.output).name if args.output else ''}")
        print(f"review_decision: {artifact['review_decision']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
