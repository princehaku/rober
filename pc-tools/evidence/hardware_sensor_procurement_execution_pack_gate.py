#!/usr/bin/env python3
"""生成 hardware_sensor_procurement_execution_pack fail-closed 采购执行包。"""

from __future__ import annotations

# 设计约束 01：本文件只做 PC metadata gate，不连接真实采购系统。
# 设计约束 02：本文件只做 PC metadata gate，不读取真实传感器驱动。
# 设计约束 03：本文件只做 PC metadata gate，不读取 ROS graph。
# 设计约束 04：本文件只做 PC metadata gate，不打开任何串口设备。
# 设计约束 05：本文件只做 PC metadata gate，不访问 WAVE ROVER 下位机。
# 设计约束 06：本文件只做 PC metadata gate，不发 `/cmd_vel`。
# 设计约束 07：本文件只做 PC metadata gate，不发 JSON 控制指令。
# 设计约束 08：本文件只做 PC metadata gate，不检查真实电源。
# 设计约束 09：本文件只做 PC metadata gate，不检查真实安装孔位。
# 设计约束 10：本文件只做 PC metadata gate，不检查真实标定结果。
# 设计约束 11：采购执行包只是把 review decision 变成待填模板。
# 设计约束 12：待填模板不是采购订单，也不是发货证明。
# 设计约束 13：待填模板不是安装验收，也不是 HIL 准入证明。
# 设计约束 14：ready 状态只表示可以进入人工材料履约。
# 设计约束 15：ready 状态仍必须保持 not_proven。
# 设计约束 16：ready 状态仍必须保持 hardware_material_pending。
# 设计约束 17：ready 状态仍必须保持 delivery_success=false。
# 设计约束 18：ready 状态仍必须保持 primary_actions_enabled=false。
# 设计约束 19：缺 review decision 时必须 fail closed。
# 设计约束 20：坏 JSON 输入时必须 fail closed。
# 设计约束 21：非 object JSON 输入时必须 fail closed。
# 设计约束 22：unsupported schema 输入时必须 fail closed。
# 设计约束 23：unsupported boundary 输入时必须 fail closed。
# 设计约束 24：顶层 unsupported schema 不能被内嵌 summary 绕过。
# 设计约束 25：diagnostics wrapper 只有在没有顶层 schema 时才按 summary 解析。
# 设计约束 26：内嵌 summary 仍要校验 schema。
# 设计约束 27：内嵌 summary 仍要校验证据边界。
# 设计约束 28：delivery_success=true 必须阻断。
# 设计约束 29：primary_actions_enabled=true 必须阻断。
# 设计约束 30：hil_pass=true 必须阻断。
# 设计约束 31：自由文本里的已采购断言必须阻断。
# 设计约束 32：自由文本里的已安装断言必须阻断。
# 设计约束 33：自由文本里的已标定断言必须阻断。
# 设计约束 34：自由文本里的 field pass 断言必须阻断。
# 设计约束 35：自由文本里的 HIL pass 断言必须阻断。
# 设计约束 36：字符串形式的 false 不当成 bool false。
# 设计约束 37：字符串形式的 true 不当成 bool true 后继续放行。
# 设计约束 38：hardware_material_pending 必须是 bool true。
# 设计约束 39：delivery_success 必须是 bool false。
# 设计约束 40：primary_actions_enabled 必须是 bool false。
# 设计约束 41：hardware_material_status 必须保持 hardware_material_pending。
# 设计约束 42：输入里出现本机绝对设备路径必须阻断。
# 设计约束 43：输入里出现控制 topic 必须阻断。
# 设计约束 44：输入里出现凭证字段必须阻断。
# 设计约束 45：输入里出现数据库连接串必须阻断。
# 设计约束 46：输入里出现队列连接串必须阻断。
# 设计约束 47：输入里出现 checksum 必须阻断，避免复制 raw artifact。
# 设计约束 48：输入里出现 traceback 必须阻断，避免把错误栈给手机端。
# 设计约束 49：输出 evidence_ref 不能泄漏本机绝对路径。
# 设计约束 50：输出 source_review_ref 不能泄漏本机绝对路径。
# 设计约束 51：输出 owner_handoff 只保留 owner/action。
# 设计约束 52：输出 blockers 只保留 category/status/fields/owner。
# 设计约束 53：输出 rerun_commands 只保留 PC gate 命令。
# 设计约束 54：rerun_commands 不允许包含串口调试命令。
# 设计约束 55：rerun_commands 不允许包含 ROS 控制命令。
# 设计约束 56：rerun_commands 不允许包含真实采购系统命令。
# 设计约束 57：material_templates 只描述应补字段。
# 设计约束 58：material_templates 不填充任何真实 SKU。
# 设计约束 59：material_templates 不填充任何真实 purchase order。
# 设计约束 60：material_templates 不填充任何真实安装结论。
# 设计约束 61：material_templates 不填充任何真实标定结论。
# 设计约束 62：material_templates 不填充任何真实 HIL 结论。
# 设计约束 63：2D LiDAR 模板必须保留 source document 字段。
# 设计约束 64：2D LiDAR 模板必须保留采购状态字段。
# 设计约束 65：2D LiDAR 模板必须保留安装走线字段。
# 设计约束 66：2D LiDAR 模板必须保留 power budget 字段。
# 设计约束 67：2D LiDAR 模板必须保留 calibration 字段。
# 设计约束 68：2D LiDAR 模板必须保留 HIL entry 字段。
# 设计约束 69：ToF 模板必须保留 channel count source 字段。
# 设计约束 70：ToF 模板必须保留采购状态字段。
# 设计约束 71：ToF 模板必须保留安装走线字段。
# 设计约束 72：ToF 模板必须保留 power budget 字段。
# 设计约束 73：ToF 模板必须保留 calibration 字段。
# 设计约束 74：ToF 模板必须保留 HIL entry 字段。
# 设计约束 75：summary 是 Robot/mobile 的消费面，不能复制完整 artifact。
# 设计约束 76：summary 必须保留 source_schema。
# 设计约束 77：summary 必须保留 evidence_boundary。
# 设计约束 78：summary 必须保留 execution_pack_status。
# 设计约束 79：summary 必须保留 hardware_material_pending。
# 设计约束 80：summary 必须保留 not_proven。
# 设计约束 81：summary 必须保留 delivery_success=false。
# 设计约束 82：summary 必须保留 primary_actions_enabled=false。
# 设计约束 83：vendor_source_boundary 只记录资料边界，不扩大成采购证据。
# 设计约束 84：vendor_source_boundary 必须引用 docs/vendor/VENDOR_INDEX.md。
# 设计约束 85：Orange Pi 手册/电路图只证明资料来源存在。
# 设计约束 86：WAVE ROVER wiki/firmware/app 只证明底盘资料来源存在。
# 设计约束 87：vendor 资料不证明项目 2D LiDAR 已采购。
# 设计约束 88：vendor 资料不证明项目 ToF 已采购。
# 设计约束 89：vendor 资料不证明项目 2D LiDAR 已安装。
# 设计约束 90：vendor 资料不证明项目 ToF 已安装。
# 设计约束 91：vendor 资料不证明项目传感器已标定。
# 设计约束 92：vendor 资料不证明项目传感器已通过 HIL。
# 设计约束 93：non_access_scope 必须列出采购系统不访问。
# 设计约束 94：non_access_scope 必须列出物理安装不访问。
# 设计约束 95：non_access_scope 必须列出 sensor driver 不访问。
# 设计约束 96：non_access_scope 必须列出 ROS graph 不访问。
# 设计约束 97：non_access_scope 必须列出 serial_uart 不访问。
# 设计约束 98：non_access_scope 必须列出 hardware_bus 不访问。
# 设计约束 99：non_access_scope 必须列出 nav2_runtime 不访问。
# 设计约束 100：non_access_scope 必须列出 hil 不访问。
# 设计约束 101：blocked_reason 要短，方便 Product closeout 引用。
# 设计约束 102：blocked_reason 不能包含 raw JSON。
# 设计约束 103：blocked_reason 不能包含凭证。
# 设计约束 104：blocked_reason 不能包含本机路径。
# 设计约束 105：blocked_reason 不能包含串口设备名。
# 设计约束 106：next_required_evidence 是履约动作，不是控制建议。
# 设计约束 107：owner_handoff 是人类分工，不是机器人动作。
# 设计约束 108：测试必须覆盖 ready review。
# 设计约束 109：测试必须覆盖 missing review。
# 设计约束 110：测试必须覆盖 summary-only 输入。
# 设计约束 111：测试必须覆盖 wrapper summary 输入。
# 设计约束 112：测试必须覆盖 blocked review。
# 设计约束 113：测试必须覆盖 unsupported schema。
# 设计约束 114：测试必须覆盖 unsupported boundary。
# 设计约束 115：测试必须覆盖 success/control claim。
# 设计约束 116：测试必须覆盖 weak boolean contract。
# 设计约束 117：测试必须覆盖 raw path/credential copy。
# 设计约束 118：本 gate 的 exit code ready 为 0，blocked 为 2。
# 设计约束 119：exit code 不能被当成真实硬件证明。
# 设计约束 120：所有输出字段都服务于可审查的软件证明。
# 设计约束 121：本 gate 不更新 OKR 完成度。
# 设计约束 122：本 gate 不替代 Product final closeout。
# 设计约束 123：本 gate 不替代真实采购审核。
# 设计约束 124：本 gate 不替代真实 bench check。
# 设计约束 125：本 gate 不替代真实 HIL entry check。
# 设计约束 126：本 gate 不替代真实 route/elevator field run。
# 设计约束 127：本 gate 不替代真实 delivery result。
# 设计约束 128：本 gate 的边界字符串必须便于 rg 验收。
# 设计约束 129：本 gate 的状态枚举必须便于 Robot fail-closed 消费。
# 设计约束 130：本 gate 的 summary 必须便于 mobile read-only 展示。

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# execution pack 是 review decision 之后的采购履约目录，不代表真实采购完成。
SCHEMA = "trashbot.hardware_sensor_procurement_execution_pack.v1"
SUMMARY_SCHEMA = "trashbot.hardware_sensor_procurement_execution_pack_summary.v1"
REVIEW_SCHEMA = "trashbot.hardware_sensor_procurement_review_decision.v1"
REVIEW_SUMMARY_SCHEMA = "trashbot.hardware_sensor_procurement_review_decision_summary.v1"
SCHEMA_VERSION = 1
SOURCE = "software_proof"
EVIDENCE_BOUNDARY = "software_proof_docker_hardware_sensor_procurement_execution_pack_gate"
REVIEW_BOUNDARY = "software_proof_docker_hardware_sensor_procurement_review_decision_gate"

# repo 相对引用避免把开发机绝对路径扩散到 Robot diagnostics 或 mobile/web。
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VENDOR_INDEX = REPO_ROOT / "docs" / "vendor" / "VENDOR_INDEX.md"

READY_REVIEW_DECISION = "ready_for_procurement_review_not_proven"
READY_EXECUTION_PACK = "ready_for_hardware_sensor_procurement_execution_pack_not_proven"
BLOCKED_MISSING_REVIEW = "blocked_missing_hardware_sensor_procurement_review_decision"
BLOCKED_UNSUPPORTED_REVIEW = "blocked_unsupported_hardware_sensor_procurement_review_decision"
BLOCKED_REVIEW_NOT_READY = "blocked_hardware_sensor_procurement_review_not_ready"
BLOCKED_UNSAFE_COPY = "blocked_unsafe_hardware_sensor_procurement_execution_pack_copy"
BLOCKED_WEAK_CONTRACT = "blocked_weak_hardware_sensor_procurement_review_contract"

# 采购执行包仍只准备材料模板，不能声明采购、安装、标定、HIL 或送达成功。
NOT_PROVEN = (
    "real_2d_lidar_procured",
    "real_2d_lidar_vendor_source_accepted",
    "real_2d_lidar_mounted_wired_calibrated",
    "real_tof_procured",
    "real_tof_channel_count_source_accepted",
    "real_tof_mounted_wired_calibrated",
    "real_sensor_hil_entry_pass",
    "real_nav2_slam_field_pass",
    "real_near_field_safety_gate_pass",
    "real_route_or_elevator_field_pass",
    "real_hardware_installation",
    "delivery_success",
)

# 执行包模板是下一步人工采购履约清单，不生成或假造真实 SKU/source。
MATERIAL_TEMPLATES = (
    {
        "name": "2d_lidar_procurement_order.md",
        "category": "procurement_source_material",
        "required_fields": [
            "sku",
            "vendor_source_document",
            "quote_or_purchase_order_ref",
            "procurement_status",
        ],
    },
    {
        "name": "2d_lidar_mounting_wiring_plan.md",
        "category": "mounting_wiring_power_calibration_hil_entry",
        "required_fields": [
            "mounting_plan",
            "wiring_plan",
            "power_budget",
            "calibration_plan",
            "hil_entry_material",
        ],
    },
    {
        "name": "tof_ring_procurement_order.md",
        "category": "procurement_source_material",
        "required_fields": [
            "sku",
            "vendor_source_document",
            "channel_count_source",
            "quote_or_purchase_order_ref",
            "procurement_status",
        ],
    },
    {
        "name": "tof_ring_mounting_wiring_plan.md",
        "category": "mounting_wiring_power_calibration_hil_entry",
        "required_fields": [
            "mounting_plan",
            "wiring_plan",
            "power_budget",
            "calibration_plan",
            "hil_entry_material",
        ],
    },
    {
        "name": "hardware_sensor_hil_entry_checklist.md",
        "category": "hil_entry_material",
        "required_fields": [
            "accepted_source_refs",
            "bench_check_result",
            "install_check_result",
            "calibration_check_result",
            "hil_entry_owner",
        ],
    },
    {
        "name": "diagnostics_mobile_safe_summary.json",
        "category": "metadata_only_summary",
        "required_fields": [
            "status",
            "evidence_ref",
            "hardware_material_status",
            "not_proven",
            "delivery_success",
            "primary_actions_enabled",
        ],
    },
)

# 这些片段属于 raw 控制、凭证、本机路径或成功断言，不能进入执行包输出面。
FORBIDDEN_COPY = (
    "Authorization",
    "Bearer ",
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
    "/dev/cu.",
    "/dev/tty.",
    "checksum",
    "raw robot response",
    "complete artifact",
    "Traceback",
)

# 文案中出现采购/标定/HIL/送达成功，就必须 fail closed。
UNSAFE_SUCCESS_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bhil_pass\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(procured|purchased|installed|calibrated|hil|field)\s+(pass|passed|complete|completed|success)\b"),
    re.compile(r"(?i)\b(lidar|tof).{0,32}(procured|purchased|installed|calibrated|hil_pass|field_pass)\b"),
)

# 脱敏先于输出白名单，避免上游自由文本把路径或凭证带入 artifact。
SENSITIVE_PATTERNS = (
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"), "Bearer [REDACTED]"),
    (re.compile(r"(?i)\bAuthorization\s*:\s*[^,\s]+"), "[REDACTED_AUTH_HEADER]"),
    (re.compile(r"(?i)\b(access[_-]?key|secret|token|password)\b\s*[:=]\s*[^,\s]+"), r"\1=[REDACTED]"),
    (re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://[^,\s]+"), "[REDACTED_URL]"),
    (re.compile(r"/cmd_vel\b"), "[REDACTED_ROS_TOPIC]"),
    (re.compile(r"/dev/(ttyUSB|ttyACM|cu\.|tty\.)[A-Za-z0-9._-]*"), "/dev/[REDACTED_DEVICE]"),
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)complete artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)raw robot response"), "[REDACTED_RAW_RESPONSE]"),
)


def _utc_now() -> str:
    # UTC 时间让 Docker 和 macOS 生成的证据可以稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any, default: str = "") -> str:
    # 所有外发文本都先脱敏，防止上游 review note 泄漏本机环境。
    if value is None:
        text = default
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text or default


def _safe_ref(value: Any, fallback: str = "missing") -> str:
    # evidence_ref 允许业务引用，但本机绝对路径只保留文件名。
    text = _safe_text(value)
    if not text:
        return fallback
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _repo_ref(path: Path) -> str:
    # vendor/source boundary 输出 repo 相对路径，便于审查来源。
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except (OSError, ValueError):
        return path.name


def _read_json(path: Path | None) -> tuple[dict[str, Any], str]:
    # 缺 review decision 是预期 blocked 状态，不把异常直接抛给调用方。
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
    # 只接受 object summary，避免弱类型绕过 schema/boundary 校验。
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    # 上游可能缺数组字段；统一成 list 便于白名单截断。
    return list(value) if isinstance(value, (list, tuple)) else []


def _safe_list(value: Any, limit: int = 12) -> list[str]:
    # 执行包只保留短列表，不复制完整 artifact 或 raw 现场说明。
    return [_safe_text(item) for item in _list(value)[:limit] if _safe_text(item)]


def _encoded(value: Any) -> str:
    # JSON 编码让 forbidden/success 扫描同时覆盖键和值。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # 先扫描原始输入，拦截 raw 控制、凭证和本机设备路径。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _has_success_claim(value: Any) -> bool:
    # 字段和自由文本都扫描，避免 procurement pack 被误读成真实完成。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in UNSAFE_SUCCESS_PATTERNS)


def _any_true_key(value: Any, key: str) -> bool:
    # 成功或放行字段可能嵌套在 summary 中，必须递归处理。
    if isinstance(value, dict):
        return any((k == key and v is True) or _any_true_key(v, key) for k, v in value.items())
    if isinstance(value, list):
        return any(_any_true_key(item, key) for item in value)
    if isinstance(value, str):
        return bool(re.search(rf"(?i)\b{re.escape(key)}\s*[:=]\s*true\b", value))
    return False


def _source_payload(payload: dict[str, Any]) -> dict[str, Any]:
    # 支持直接 artifact、直接 summary，以及 diagnostics wrapper 内嵌 summary。
    if payload.get("schema") in {REVIEW_SCHEMA, REVIEW_SUMMARY_SCHEMA}:
        return payload
    if payload.get("schema"):
        return payload
    for key in ("review_summary", "hardware_sensor_procurement_review_decision_summary", "summary"):
        nested = _dict(payload.get(key))
        if nested.get("schema") == REVIEW_SUMMARY_SCHEMA:
            return nested
    return payload


def _normalize_review(payload: dict[str, Any]) -> dict[str, Any]:
    # 只消费上一轮 review 的白名单字段，不把 raw intake 或完整 artifact 下传。
    source = _source_payload(payload)
    nested_summary = _dict(source.get("review_summary"))
    effective = nested_summary if nested_summary.get("schema") == REVIEW_SUMMARY_SCHEMA else source
    status = _safe_text(
        effective.get("status")
        or effective.get("review_decision")
        or effective.get("hardware_sensor_procurement_review_decision")
        or source.get("review_decision")
        or source.get("hardware_sensor_procurement_review_decision"),
        "missing_review_decision",
    )
    return {
        "schema": _safe_text(effective.get("schema") or source.get("schema")),
        "full_schema": _safe_text(source.get("schema")),
        "evidence_boundary": _safe_text(effective.get("evidence_boundary") or source.get("evidence_boundary")),
        "status": status,
        "review_decision": status,
        "source_intake_schema": _safe_text(effective.get("source_intake_schema") or source.get("source_intake_schema"), "missing"),
        "source_intake_status": _safe_text(effective.get("source_intake_status") or source.get("source_intake_status"), "missing"),
        "evidence_ref": _safe_ref(effective.get("evidence_ref") or source.get("evidence_ref"), "missing_review_decision"),
        "blockers": _blockers(effective.get("blockers") or source.get("blockers")),
        "next_required_evidence": _safe_list(effective.get("next_required_evidence") or source.get("next_required_evidence"), limit=12),
        "owner_handoff": _owner_handoff(effective.get("owner_handoff") or source.get("owner_handoff")),
        "rerun_commands": _safe_list(effective.get("rerun_commands") or source.get("rerun_commands"), limit=8),
        "not_proven": _safe_list(effective.get("not_proven") or source.get("not_proven"), limit=20),
        "hardware_material_status": _safe_text(
            effective.get("hardware_material_status") or source.get("hardware_material_status"),
            "hardware_material_pending",
        ),
        "hardware_material_pending": effective.get("hardware_material_pending", source.get("hardware_material_pending")),
        "delivery_success": effective.get("delivery_success", source.get("delivery_success")),
        "primary_actions_enabled": effective.get("primary_actions_enabled", source.get("primary_actions_enabled")),
    }


def _blockers(value: Any) -> list[dict[str, Any]]:
    # blocker 只保留 category/status/fields/owner，避免复制上游自由文本。
    blockers: list[dict[str, Any]] = []
    for item in _list(value)[:10]:
        if not isinstance(item, dict):
            continue
        blockers.append(
            {
                "category": _safe_text(item.get("category"), "unknown"),
                "status": _safe_text(item.get("status"), "hardware_material_pending"),
                "fields": _safe_list(item.get("fields"), limit=16),
                "owner": _safe_text(item.get("owner"), "Hardware Infra Engineer"),
            }
        )
    return blockers


def _owner_handoff(value: Any) -> list[dict[str, str]]:
    # handoff 白名单化，确保下游只看到 owner/action 级别的执行建议。
    handoff: list[dict[str, str]] = []
    for item in _list(value)[:8]:
        if not isinstance(item, dict):
            continue
        handoff.append(
            {
                "owner": _safe_text(item.get("owner"), "Hardware Infra Engineer"),
                "action": _safe_text(item.get("action"), "Keep hardware_material_pending until real evidence lands."),
            }
        )
    return handoff


def _schema_status(load_issue: str, review: dict[str, Any]) -> str:
    # 顶层 schema 和内嵌 summary schema 都要受支持，避免 wrapper schema bypass。
    if load_issue:
        return "not_loaded"
    schema_supported = review["schema"] in {REVIEW_SCHEMA, REVIEW_SUMMARY_SCHEMA}
    full_schema_supported = review["full_schema"] in {"", REVIEW_SCHEMA, REVIEW_SUMMARY_SCHEMA}
    boundary_supported = review["evidence_boundary"] == REVIEW_BOUNDARY
    return "supported" if schema_supported and full_schema_supported and boundary_supported else "unsupported"


def _weak_contract_status(review: dict[str, Any]) -> str:
    # bool contract 用弱类型时阻断，避免字符串 false/true 被消费方误判。
    bool_fields = ("hardware_material_pending", "delivery_success", "primary_actions_enabled")
    for field in bool_fields:
        if not isinstance(review.get(field), bool):
            return field
    if review["delivery_success"] or review["primary_actions_enabled"]:
        return "unsafe_true_boolean"
    if review["hardware_material_pending"] is not True:
        return "hardware_material_pending_false"
    if review["hardware_material_status"] != "hardware_material_pending":
        return "hardware_material_status"
    return ""


def _execution_pack_status(
    load_issue: str,
    schema_status: str,
    weak_contract: str,
    unsafe_copy: bool,
    success_claim: bool,
    review: dict[str, Any],
) -> str:
    # 决策顺序先挡输入和安全，再看 review decision 是否 ready。
    if load_issue:
        return BLOCKED_MISSING_REVIEW if load_issue == "missing" else BLOCKED_UNSUPPORTED_REVIEW
    if schema_status != "supported":
        return BLOCKED_UNSUPPORTED_REVIEW
    if unsafe_copy:
        return BLOCKED_UNSAFE_COPY
    if success_claim:
        return BLOCKED_UNSUPPORTED_REVIEW
    if weak_contract:
        return BLOCKED_WEAK_CONTRACT
    if review["review_decision"] == READY_REVIEW_DECISION:
        return READY_EXECUTION_PACK
    return BLOCKED_REVIEW_NOT_READY


def _blocked_reason(status: str, load_issue: str, schema_status: str, weak_contract: str, review: dict[str, Any]) -> str:
    # blocked_reason 给 Product/Hardware 快速定位，不引入 raw artifact。
    if status == READY_EXECUTION_PACK:
        return ""
    if status == BLOCKED_MISSING_REVIEW:
        return "missing hardware_sensor_procurement_review_decision artifact or summary"
    if status == BLOCKED_UNSUPPORTED_REVIEW:
        return f"unsupported review contract: load_issue={load_issue or 'none'} schema_status={schema_status}"
    if status == BLOCKED_WEAK_CONTRACT:
        return f"weak or unsafe boolean/source contract: {weak_contract}"
    if status == BLOCKED_UNSAFE_COPY:
        return "source review contains raw path, credential, control topic, checksum, traceback, or complete artifact copy"
    return f"source review decision is not ready: {review['review_decision']}"


def _material_templates(evidence_ref: str) -> list[dict[str, Any]]:
    # 模板强制继承同一 evidence_ref，但不生成任何真实采购材料。
    templates: list[dict[str, Any]] = []
    for item in MATERIAL_TEMPLATES:
        templates.append(
            {
                "name": item["name"],
                "category": item["category"],
                "required_fields": list(item["required_fields"]),
                "evidence_ref": evidence_ref,
                "status": "template_pending_real_material",
            }
        )
    return templates


def _next_required_evidence(status: str, review: dict[str, Any]) -> list[str]:
    # 下一步材料清单来自 review；ready 时补齐 execution-pack 专属履约动作。
    if status == BLOCKED_MISSING_REVIEW:
        return [
            "Generate hardware_sensor_procurement_review decision artifact or summary first.",
            "Keep hardware_material_pending until a supported review decision exists.",
        ]
    if status in {BLOCKED_UNSUPPORTED_REVIEW, BLOCKED_UNSAFE_COPY, BLOCKED_WEAK_CONTRACT}:
        return [
            "Regenerate a supported review decision summary without success/control claims, raw paths, credentials, or weak boolean fields.",
            "Use schema trashbot.hardware_sensor_procurement_review_decision.v1 or trashbot.hardware_sensor_procurement_review_decision_summary.v1.",
        ]
    if status == BLOCKED_REVIEW_NOT_READY:
        return review["next_required_evidence"] or [
            "Resolve review_decision blockers before preparing a procurement execution package.",
        ]
    return [
        "Fill procurement order refs and source documents for 2D LiDAR and ToF under the same evidence_ref.",
        "Fill mounting, wiring, power budget, calibration, and HIL-entry checklist templates before any install/HIL claim.",
        "Re-run intake, review decision, and execution pack gates after real material changes.",
    ]


def _owner_handoff_for_status(status: str, review: dict[str, Any]) -> list[dict[str, str]]:
    # owner_handoff 明确这是材料履约，不允许 mobile/Robot 放行动作。
    base = review["owner_handoff"][:6]
    if status == READY_EXECUTION_PACK:
        return base + [
            {
                "owner": "Hardware Infra Engineer",
                "action": "Fill procurement/source, mounting/wiring/power, calibration, and HIL-entry templates with real evidence.",
            },
            {
                "owner": "Product Manager / OKR Owner",
                "action": "Keep OKR wording at software_proof / not_proven until procurement, install, calibration, and HIL evidence lands.",
            },
        ]
    return base or [
        {
            "owner": "Hardware Infra Engineer",
            "action": "Repair the review decision source before using this execution pack.",
        },
        {
            "owner": "Product Manager / OKR Owner",
            "action": "Do not count this blocked pack as procurement, installation, calibration, HIL, or delivery progress.",
        },
    ]


def _rerun_commands(review_ref: str, review_commands: list[str]) -> list[str]:
    # 命令只重跑 PC gate，不包含串口、ROS 控制、真实硬件或采购系统操作。
    review_arg = review_ref or "<hardware_sensor_procurement_review_decision_json>"
    commands = list(review_commands[:4])
    commands.extend(
        [
            "python3 pc-tools/evidence/hardware_sensor_procurement_review_decision_gate.py --intake-json <hardware_sensor_procurement_intake_json> --summary-output <review_summary_json>",
            f"python3 pc-tools/evidence/hardware_sensor_procurement_execution_pack_gate.py --review-json {review_arg} --summary-output <execution_pack_summary_json>",
            "python3 pc-tools/evidence/test_hardware_sensor_procurement_execution_pack_gate.py",
            'rg -n "hardware_sensor_procurement_execution_pack|hardware_material_pending|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence docs/product',
        ]
    )
    return [_safe_text(command) for command in commands[:8]]


def _summary(artifact: dict[str, Any]) -> dict[str, Any]:
    # summary 是 Robot/mobile 的只读消费面，字段保持短且 fail-closed。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source_schema": SCHEMA,
        "source": SOURCE,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "status": artifact["execution_pack_status"],
        "execution_pack_status": artifact["execution_pack_status"],
        "hardware_sensor_procurement_execution_pack": artifact["execution_pack_status"],
        "source_review_decision": artifact["source_review_decision"],
        "source_review_schema": artifact["source_review_schema"],
        "source_review_status": artifact["source_review_status"],
        "evidence_ref": artifact["evidence_ref"],
        "blocked_reason": artifact["blocked_reason"],
        "material_templates": [item["name"] for item in artifact["material_templates"]],
        "blockers": artifact["blockers"],
        "next_required_evidence": artifact["next_required_evidence"],
        "owner_handoff": artifact["owner_handoff"],
        "rerun_commands": artifact["rerun_commands"][:4],
        "hardware_material_status": "hardware_material_pending",
        "hardware_material_pending": True,
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "boundary_note": "software_proof only; delivery_success=false; primary_actions_enabled=false; not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_hardware_sensor_procurement_execution_pack(
    review_json: str | Path | None = None,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取上一轮 review decision artifact/summary，生成 fail-closed execution pack。"""

    review_path = Path(review_json) if review_json else None
    payload, load_issue = _read_json(review_path)
    review = (
        _normalize_review(payload)
        if payload
        else {
            "schema": "",
            "full_schema": "",
            "evidence_boundary": "",
            "status": "missing",
            "review_decision": "missing_review_decision",
            "source_intake_schema": "missing",
            "source_intake_status": "missing",
            "evidence_ref": "missing_review_decision",
            "blockers": [],
            "next_required_evidence": [],
            "owner_handoff": [],
            "rerun_commands": [],
            "not_proven": [],
            "hardware_material_status": "hardware_material_pending",
            "hardware_material_pending": True,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    )
    schema_status = _schema_status(load_issue, review)
    weak_contract = "" if load_issue or schema_status != "supported" else _weak_contract_status(review)
    unsafe_copy = bool(payload and _has_forbidden_copy(payload))
    success_claim = bool(payload and (_has_success_claim(payload) or _any_true_key(payload, "delivery_success") or _any_true_key(payload, "primary_actions_enabled")))
    status = _execution_pack_status(load_issue, schema_status, weak_contract, unsafe_copy, success_claim, review)
    safe_ref = _safe_ref(evidence_ref or review["evidence_ref"], "missing_review_decision")
    source_ref = _repo_ref(review_path) if review_path and review_path.exists() else _safe_ref(review_path, "missing")

    artifact: dict[str, Any] = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "generated_at": _utc_now(),
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "evidence_ref": safe_ref,
        "source_review_ref": source_ref,
        "source_review_schema": review["schema"] or "missing",
        "source_review_boundary": review["evidence_boundary"] or "missing",
        "source_review_status": review["status"],
        "source_review_decision": review["review_decision"],
        "source_intake_schema": review["source_intake_schema"],
        "source_intake_status": review["source_intake_status"],
        "schema_status": schema_status,
        "weak_contract": weak_contract,
        "execution_pack_status": status,
        "hardware_sensor_procurement_execution_pack": status,
        "blocked_reason": _blocked_reason(status, load_issue, schema_status, weak_contract, review),
        "blockers": review["blockers"],
        "material_templates": _material_templates(safe_ref),
        "next_required_evidence": _next_required_evidence(status, review),
        "owner_handoff": _owner_handoff_for_status(status, review),
        "rerun_commands": _rerun_commands(source_ref, review["rerun_commands"]),
        "vendor_source_boundary": {
            "source": _repo_ref(DEFAULT_VENDOR_INDEX),
            "checked_readable_local_sources": [
                "docs/vendor/waveshare_wave_rover/README.md",
                "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
                "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
                "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
            ],
            "index_listed_hardware_sources": [
                "docs/vendor/orangepizero3/OrangePi_Zero3_H618_用户手册_v1.6.pdf",
                "docs/vendor/orangepizero3/OrangePi-ZERO3_电路图.pdf",
            ],
            "project_2d_lidar_tof_procurement_proof": "not_proven",
        },
        "hardware_material_status": "hardware_material_pending",
        "hardware_material_pending": True,
        "evidence_status": "not_proven",
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "procurement_system",
            "warehouse_or_shipping",
            "physical_installation",
            "sensor_driver_runtime",
            "ros_graph",
            "serial_uart",
            "hardware_bus",
            "nav2_runtime",
            "hil",
            "route_or_elevator_field_run",
            "delivery_execution",
        ],
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    summary = _summary(artifact)
    artifact["execution_pack_summary"] = summary
    return artifact, summary, 0 if status == READY_EXECUTION_PACK else 2


def _write_json(path: str, payload: dict[str, Any]) -> None:
    # 输出路径自动创建，便于 Product sprint evidence bundle 引用。
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只做 metadata-only PC gate，不访问真实采购系统、传感器、ROS 或 HIL。
    parser = argparse.ArgumentParser(
        description="Generate hardware_sensor_procurement_execution_pack fail-closed software-proof artifact."
    )
    parser.add_argument("--review-json", default="", help="Previous hardware_sensor_procurement_review_decision artifact or summary JSON.")
    parser.add_argument("--evidence-ref", default="", help="Optional safe evidence_ref override for downstream summaries.")
    parser.add_argument("--output", default="", help="Write full hardware sensor procurement execution pack artifact JSON.")
    parser.add_argument("--summary-output", default="", help="Write compact hardware sensor procurement execution pack summary JSON.")
    parser.add_argument("--once-json", action="store_true", help="Print full artifact JSON to stdout.")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_hardware_sensor_procurement_execution_pack(
        args.review_json or None,
        evidence_ref=args.evidence_ref,
    )
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"hardware_sensor_procurement_execution_pack: artifact_file:{Path(args.output).name if args.output else ''}")
        print(f"execution_pack_status: {artifact['execution_pack_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
