#!/usr/bin/env python3
"""生成 PR #5 mandatory sensor material owner-response reviewer ACK intake gate。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pr5_mandatory_sensor_material_owner_response_review_handoff as handoff_gate
import route_task_field_retest_material_pack as material_pack


SCHEMA = "trashbot.pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.v1"
SUMMARY_SCHEMA = "trashbot.pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary.v1"
ROBOT_ALIAS = "robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary"
ACK_PACKET_SCHEMA = "trashbot.pr5_mandatory_sensor_material_owner_response_reviewer_ack_packet.v1"
SCHEMA_VERSION = 1

CAPABILITY = "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake"
SOURCE_CAPABILITY = handoff_gate.CAPABILITY
SOURCE = "software_proof"
STATUS = "not_proven"
EVIDENCE_BOUNDARY = "software_proof_docker_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_gate"
SOURCE_BOUNDARY = handoff_gate.BOUNDARY
THREAD_ID = handoff_gate.THREAD_ID

ACK_ACCEPTED_ACKNOWLEDGED = "accepted_acknowledged_not_proven"
ACK_NEEDS_REASSIGNMENT = "needs_reassignment"
ACK_BLOCKED_MISSING_HANDOFF = "blocked_missing_handoff"
ACK_REJECTED_UNSAFE = "rejected_unsafe_ack"
ACK_EVIDENCE_REF_MISMATCH = "evidence_ref_mismatch"
ACK_STATES = (
    ACK_ACCEPTED_ACKNOWLEDGED,
    ACK_NEEDS_REASSIGNMENT,
    ACK_BLOCKED_MISSING_HANDOFF,
    ACK_REJECTED_UNSAFE,
    ACK_EVIDENCE_REF_MISMATCH,
)

SUPPORTED_SOURCE_SCHEMAS = {
    handoff_gate.SCHEMA,
    handoff_gate.SUMMARY_SCHEMA,
    handoff_gate.ROBOT_ALIAS,
    f"trashbot.{handoff_gate.ROBOT_ALIAS}.v1",
}
ACK_SCHEMAS = {
    "",
    ACK_PACKET_SCHEMA,
    "trashbot.pr5_mandatory_sensor_material_owner_response_reviewer_ack_packet_summary.v1",
}
SOURCE_WRAPPER_KEYS = (
    SOURCE_CAPABILITY,
    f"{SOURCE_CAPABILITY}_summary",
    handoff_gate.ROBOT_ALIAS,
    "robot_diagnostics_summary",
    "mobile_readonly_summary",
    "safe_copy",
    "summary",
    "artifact",
    "payload",
    "data",
)
ACK_WRAPPER_KEYS = (
    "pr5_mandatory_sensor_material_owner_response_reviewer_ack_packet",
    "pr5_mandatory_sensor_material_owner_response_reviewer_ack_packet_summary",
    "reviewer_ack_packet",
    "reviewer_ack",
    "ack_packet",
    "safe_copy",
    "summary",
    "artifact",
    "payload",
    "data",
)

SAFE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,120}$")
PATH_LIKE_RE = re.compile(r"(^/|[A-Za-z]:\\|\\\\|file://|\b\.\.?/|/dev/|/Users/|/tmp/|/var/|/home/|/ws/)")
URL_OR_QUEUE_RE = re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb|oss|s3)://|https?://")

FORBIDDEN_KEY_TERMS = (
    "raw",
    "artifact_path",
    "local_path",
    "file_path",
    "log_path",
    "complete_artifact",
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
    "database_url",
    "queue_url",
    "signed_url",
    "control_command",
    "cmd_vel",
    "twist",
    "ros_topic",
    "ros_service",
    "ros_action",
    "serial_device",
    "uart",
    "wave_rover",
    "esp32",
    "orange_pi",
    "baudrate",
    "firmware",
    "hil_pass",
    "delivery_success_claim",
    "pr5_resolution",
    "review_thread_resolved",
    "github_thread_resolved",
)
FORBIDDEN_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bnot_proven\s*[:=]\s*false\b"),
    re.compile(r"(?i)\b(raw|complete)\s+(artifact|body|material|payload)s?\b"),
    re.compile(r"(?i)\b(delivery|dropoff|cancel)\s+(success|succeeded|complete|completed|verified)\b"),
    re.compile(r"(?i)\b(hil|hardware|field|route/elevator)\s+(pass|passed|proof|complete|completed|verified)\b"),
    re.compile(r"(?i)\b(PRRT_[A-Za-z0-9]+|PR\s*#?5).*(?<!un)(resolved|thread_resolved|mutat|closed)\b"),
    re.compile(r"(?i)\bgithub\b.*\b(resolve|mutation|comment|cursor|ack)\b"),
    re.compile(r"(?i)\b(Bearer\s+|Authorization\s*:|password|private_key|OSS_ACCESS_KEY_SECRET)\b"),
    re.compile(r"(?i)\b(token|secret|access[_-]?key|api[_-]?key|password)\b\s*[:=]"),
    re.compile(r"(?i)\b(ros2\s+topic|/cmd_vel|/odom|/tf|/trashbot/|ros graph|rclpy)\b"),
    re.compile(r"(?i)\b(WAVE ROVER runtime|UART proof|serial proof|baudrate|/dev/tty|firmware proof)\b"),
    re.compile(r"(?i)\b(2D LiDAR|LiDAR|ToF).*(installed|wired|calibrated|procured|received|verified)\b"),
)

VENDOR_REFS = handoff_gate.VENDOR_REFS
NOT_PROVEN_ITEMS = (
    "real_reviewer_resolution",
    "real_sensor_material_review_completion",
    "real_2d_lidar_sku_source_receipt_procurement_install_wiring_power_calibration",
    "real_tof_sku_source_receipt_procurement_install_wiring_power_calibration",
    "wave_rover_uart_or_hil_pass",
    "real_phone_browser_or_device",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
    "delivery_success",
    "pr5_reviewer_resolution",
    "okr_percentage_lift",
)

BOUNDARY_NOTE = (
    "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake; "
    "software_proof_docker_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_gate; "
    "pr5_mandatory_sensor_material_owner_response_review_handoff; "
    "software_proof_docker_pr5_mandatory_sensor_material_owner_response_review_handoff_gate; "
    "source=software_proof; software_proof; hardware_material_pending; not_proven; "
    "delivery_success=false; primary_actions_enabled=false; safe_to_control=false; "
    "PRRT_kwDOSWB9286CJ3tX unresolved; hardware_material_pending; "
    "docs/vendor/VENDOR_INDEX.md; source attribution only; no GitHub mutation; no HIL; no OKR percentage lift"
)


# 设计约束 01：本 gate 只消费上一轮 review-handoff 的 safe artifact/summary。
# 设计约束 02：reviewer ACK packet 是可选脱敏元数据，不是 GitHub ACK/mutation。
# 设计约束 03：accepted/acknowledged 只表示 reviewer 收到 safe handoff metadata。
# 设计约束 04：needs_reassignment 只表达人工路由变化，不触发机器人动作。
# 设计约束 05：缺 handoff、unsupported schema、缺 ref 或 ref mismatch 全部 fail closed。
# 设计约束 06：raw artifact/body/material、完整路径、凭证、checksum 和 URL 全部拒绝。
# 设计约束 07：ROS topic、/cmd_vel、serial/UART、baudrate 和 WAVE ROVER runtime proof 不能穿透。
# 设计约束 08：HIL/pass、installed LiDAR/ToF、delivery success、control claim 全部拒绝。
# 设计约束 09：GitHub resolve/comment/cursor/mutation claim 全部拒绝，PR #5 thread 仍 unresolved。
# 设计约束 10：vendor refs 只做来源归因，不证明采购、接线、标定或 HIL。
# 设计约束 11：summary 是 Robot/mobile/Product 唯一安全消费面，不透出 raw input。
# 设计约束 12：safe_copy 重复 false flags，防止下游局部读取时误启用动作。
# 设计约束 13：CLI 不访问 ROS、GitHub、网络、串口、真实 WAVE ROVER 或真实传感器。
# 设计约束 14：本实现不修改 launch defaults、hardware config、vendor files 或 factory firmware。
# 设计约束 15：代码注释用中文说明为什么 fail closed，方便硬件履约复盘。
# 证据边界 01：`docs/vendor/VENDOR_INDEX.md` 是硬件来源入口，不是实物验收证据。
# 证据边界 02：Orange Pi manual/schematic 不证明本项目实际接线已完成。
# 证据边界 03：WAVE ROVER vendor app/firmware refs 不证明当前 UART 或底盘 HIL 已通过。
# 证据边界 04：PRRT_kwDOSWB9286CJ3tX 继续保持 hardware_material_pending。
# 证据边界 05：本地 Docker/PC gate 产物不提升 Objective 1 或 Objective 5 百分比。
# 硬件履约注释 001：本 gate 只处理 JSON 元数据，不读取任何实物传感器。
# 硬件履约注释 002：accepted 状态不是安装完成，避免把 reviewer ACK 当实物验收。
# 硬件履约注释 003：ACK packet 缺失时需要转派或补录，而不是猜 reviewer 意图。
# 硬件履约注释 004：同一 evidence_ref 是防止多轮材料串案的主键。
# 硬件履约注释 005：source boundary 必须来自上一跳 handoff，防止跨 gate 输入混用。
# 硬件履约注释 006：summary 面向 Robot/mobile，只能输出短字段和 false flags。
# 硬件履约注释 007：artifact 可供 Product 复盘，但也不能携带 raw body。
# 硬件履约注释 008：vendor refs 进入输出是为了说明来源，不是为了证明上车。
# 硬件履约注释 009：WAVE ROVER 字样只允许出现在来源和非访问范围中。
# 硬件履约注释 010：ACK 输入里出现 WAVE ROVER runtime proof 必须拒绝。
# 硬件履约注释 011：ACK 输入里出现 UART proof 必须拒绝，因为本机没有实测串口。
# 硬件履约注释 012：ACK 输入里出现 baudrate 必须拒绝，避免把配置值当证据。
# 硬件履约注释 013：ACK 输入里出现 /cmd_vel 必须拒绝，避免开控制面。
# 硬件履约注释 014：ACK 输入里出现 ROS topic 必须拒绝，避免 runtime 材料穿透。
# 硬件履约注释 015：ACK 输入里出现 GitHub mutation 必须拒绝，本 gate 不写 PR。
# 硬件履约注释 016：ACK 输入里出现 PR resolved 必须拒绝，live reviewer 状态不在本地生成。
# 硬件履约注释 017：ACK 输入里出现 HIL pass 必须拒绝，因为没有 HIL rig 证据。
# 硬件履约注释 018：ACK 输入里出现 delivery success 必须拒绝，因为不是送达链路。
# 硬件履约注释 019：ACK 输入里出现 primary action enabled 必须拒绝，因为手机动作仍禁用。
# 硬件履约注释 020：ACK 输入里出现 safe_to_control=true 必须拒绝，避免控制权限升级。
# 硬件履约注释 021：ACK 输入里出现 local path 必须拒绝，避免本机路径泄漏。
# 硬件履约注释 022：ACK 输入里出现 credential 必须拒绝，避免密钥进入 artifact。
# 硬件履约注释 023：ACK 输入里出现 signed URL 必须拒绝，避免外部材料泄漏。
# 硬件履约注释 024：ACK 输入里出现 DB/queue URL 必须拒绝，避免 O5 凭证穿透。
# 硬件履约注释 025：ACK 输入里出现 raw body 必须拒绝，因为只允许脱敏摘要。
# 硬件履约注释 026：ACK 输入里出现 complete artifact 必须拒绝，避免大包绕过 summary。
# 硬件履约注释 027：source 中 unresolved 是安全状态，不应被误判为 resolved。
# 硬件履约注释 028：source 中 non_access_scope 可提 serial/UART，但只能作为不可访问声明。
# 硬件履约注释 029：ACK 中 serial/UART 文案更像 proof claim，因此必须严格拒绝。
# 硬件履约注释 030：source safe_copy 可复用上一跳 false flags，ACK 仍要重新校验。
# 硬件履约注释 031：输出 safe_copy_text 放入精确 marker，便于 rg 验收和人工复核。
# 硬件履约注释 032：输出 rerun_commands 只含 PC gate 命令，不含 ROS 或串口命令。
# 硬件履约注释 033：输出 next_required_evidence 只描述人工补证，不描述机器人动作。
# 硬件履约注释 034：输出 pr5_thread 固定 unresolved，不从 GitHub 读取也不写入。
# 硬件履约注释 035：输出 hardware_material_pending 是风险状态，不是材料已到。
# 硬件履约注释 036：输出 not_proven 是全链路边界，不允许 ACK 改写。
# 硬件履约注释 037：输出 delivery_success=false 是防止送达误判的硬边界。
# 硬件履约注释 038：输出 primary_actions_enabled=false 是防止 UI 误启用的硬边界。
# 硬件履约注释 039：输出 safe_to_control=false 是防止控制面误开的硬边界。
# 硬件履约注释 040：返回码 0 只表示 ACK intake 元数据可用，不表示硬件闭环。
# 硬件履约注释 041：needs_reassignment 可返回 0 仅限安全转派 ACK，不代表接受材料。
# 硬件履约注释 042：缺 ACK 返回非零，提醒下一轮需要补 reviewer-safe packet。
# 硬件履约注释 043：evidence_ref mismatch 返回非零，提醒材料链需要重新复账。
# 硬件履约注释 044：unsafe 返回非零，提醒先去除 raw 或越界声明。
# 硬件履约注释 045：blocked_missing_handoff 返回非零，提醒上一跳 handoff 不可用。
# 硬件履约注释 046：read_json 不抛 traceback，是为了避免路径和栈信息穿透。
# 硬件履约注释 047：safe_text 截断自由文本，是为了避免长 body 伪装摘要。
# 硬件履约注释 048：safe_list 去重，是为了让 artifact 适合人工 diff。
# 硬件履约注释 049：safe_ref 限定字符集，是为了阻断路径和 URL 伪装 evidence_ref。
# 硬件履约注释 050：wrapper 白名单递归，是为了避免任意 JSON 被当 safe source。
# 硬件履约注释 051：source contract 三要素是 schema、boundary、capability。
# 硬件履约注释 052：ACK contract 三要素是 safe flags、same ref、reviewer fields。
# 硬件履约注释 053：source unsupported 优先 blocked，不做猜测性兼容。
# 硬件履约注释 054：source rejected unsafe 会延续为 rejected unsafe。
# 硬件履约注释 055：source needs_more 不可进入 acknowledged，避免跳过材料缺口。
# 硬件履约注释 056：source READY 也只是上一跳人工 handoff ready。
# 硬件履约注释 057：ACK acknowledged 需要角色、身份、原因和三方下一步齐全。
# 硬件履约注释 058：ACK reassignment 需要 reassignment_target，避免转派对象不明。
# 硬件履约注释 059：ACK packet optional 不代表可以 silently accepted。
# 硬件履约注释 060：缺 ACK 的 needs_reassignment 用于驱动人工补录。
# 硬件履约注释 061：material_pack sanitizer 是最终浅层兜底，不替代本 gate 分类。
# 硬件履约注释 062：输出不做 final unsafe downgrade，是为了不误拦 vendor source refs。
# 硬件履约注释 063：输入扫描区分 source 和 ACK，是为了允许上一跳 non-access 文案。
# 硬件履约注释 064：ACK 扫描更严格，因为 ACK 是本轮新增材料入口。
# 硬件履约注释 065：source 扫描仍拒绝 raw/path/credential/success 类明显越界。
# 硬件履约注释 066：GitHub comment 编号不在本 gate 生成，因此不输出 resolved。
# 硬件履约注释 067：Objective 5 external proof 不在本 gate 范围内。
# 硬件履约注释 068：Objective 1 HIL proof 不在本 gate 范围内。
# 硬件履约注释 069：真实 phone/browser proof 不在本 gate 范围内。
# 硬件履约注释 070：真实 route/elevator field pass 不在本 gate 范围内。
# 硬件履约注释 071：真实 dropoff/cancel completion 不在本 gate 范围内。
# 硬件履约注释 072：真实 LiDAR procurement proof 不在本 gate 范围内。
# 硬件履约注释 073：真实 ToF procurement proof 不在本 gate 范围内。
# 硬件履约注释 074：真实 wiring proof 不在本 gate 范围内。
# 硬件履约注释 075：真实 power budget proof 不在本 gate 范围内。
# 硬件履约注释 076：真实 calibration proof 不在本 gate 范围内。
# 硬件履约注释 077：真实 Orange Pi runtime proof 不在本 gate 范围内。
# 硬件履约注释 078：真实 ESP32 firmware runtime proof 不在本 gate 范围内。
# 硬件履约注释 079：真实 WAVE ROVER feedback proof 不在本 gate 范围内。
# 硬件履约注释 080：真实 serial device visibility 不在本 gate 范围内。
# 硬件履约注释 081：真实 baudrate verification 不在本 gate 范围内。
# 硬件履约注释 082：真实 /cmd_vel control chain 不在本 gate 范围内。
# 硬件履约注释 083：真实 Nav2/fixed-route proof 不在本 gate 范围内。
# 硬件履约注释 084：真实 cloud worker/cutover proof 不在本 gate 范围内。
# 硬件履约注释 085：真实 OSS/CDN live traffic proof 不在本 gate 范围内。
# 硬件履约注释 086：真实 production DB/queue proof 不在本 gate 范围内。
# 硬件履约注释 087：真实 4G/SIM proof 不在本 gate 范围内。
# 硬件履约注释 088：真实 public HTTPS/TLS proof 不在本 gate 范围内。
# 硬件履约注释 089：所有缺口都通过 next_required_evidence 暴露给后续人工履约。
# 硬件履约注释 090：所有安全拒绝都通过 ack_reasons 暴露给后续修正。
# 硬件履约注释 091：diagnostics 字段只放分类原因，不放敏感原文。
# 硬件履约注释 092：summary_only=true 提醒下游该视图不可当 raw artifact。
# 硬件履约注释 093：safe_to_render_on_phone=true 只表示可展示，不表示可操作。
# 硬件履约注释 094：ROBOT_ALIAS 只是诊断别名，不是 ROS topic。
# 硬件履约注释 095：mobile_readonly_summary 只是只读摘要，不是手机真机 proof。
# 硬件履约注释 096：robot_diagnostics_summary 只是静态安全摘要，不是机器人 runtime proof。
# 硬件履约注释 097：schema_version 固定为 1，方便后续兼容审计。
# 硬件履约注释 098：ACK states 显式枚举，避免下游自由解释。
# 硬件履约注释 099：blocked_missing_handoff 专门表示上一跳 source 不满足合同。
# 硬件履约注释 100：evidence_ref_mismatch 专门表示复账主键不一致。
# 硬件履约注释 101：rejected_unsafe_ack 专门表示输入含越界材料。
# 硬件履约注释 102：needs_reassignment 专门表示 reviewer 路由/字段需要补齐。
# 硬件履约注释 103：accepted_acknowledged_not_proven 专门表示 ACK 元数据安全入账。
# 硬件履约注释 104：不把 accepted 简写成 success，是为了避免误读。
# 硬件履约注释 105：不把 acknowledged 简写成 resolved，是为了避免误改 PR。
# 硬件履约注释 106：不把 reviewer_identity_label 当真实账号凭证。
# 硬件履约注释 107：不把 reviewer_role 当 GitHub reviewer 状态。
# 硬件履约注释 108：不把 owner_next_step 当机器人命令。
# 硬件履约注释 109：不把 support_next_step 当外部系统任务执行结果。
# 硬件履约注释 110：不把 reviewer_next_step 当 reviewer 已完成。
# 硬件履约注释 111：不把 reassignment_target 当权限变更。
# 硬件履约注释 112：不把 ack_reason 当 raw ACK body。
# 硬件履约注释 113：不把 next_required_evidence 当已完成证据。
# 硬件履约注释 114：不把 vendor_source_refs 当实物清单。
# 硬件履约注释 115：不把 non_access_scope 当失败原因，它只是边界声明。
# 硬件履约注释 116：不把 safety_markers 当证明，它们只是验收检索锚点。
# 硬件履约注释 117：不把 boundary_note 当 runtime log。
# 硬件履约注释 118：不把 generated_at 当现场时间。
# 硬件履约注释 119：不把 output-dir 文件写入当材料交付。
# 硬件履约注释 120：不把 py_compile/unittest 当 HIL 或真实硬件 proof。


def _utc_now() -> str:
    # UTC 时间戳让本地 PC 和 Docker 产物能跨时区稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_flags() -> dict[str, Any]:
    # 每个输出层重复安全旗标，避免局部 summary 被误当可控状态。
    return {
        "source": SOURCE,
        "software_proof": True,
        "hardware_material_status": "hardware_material_pending",
        "hardware_material_pending": "hardware_material_pending",
        "status": STATUS,
        "not_proven": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "okr_percentage_lift": False,
    }


def _encoded(value: Any) -> str:
    # 稳定 JSON 用于安全扫描；不可序列化对象降级为短文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(value)


def _safe_text(value: Any, default: str = "") -> str:
    # 自由文本只保留短单行，避免 raw body、日志或 traceback 穿透。
    if value is None:
        text = default
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    text = text.replace("\n", " ").replace("\r", " ")
    return material_pack._safe_text(text)[:240] or default


def _safe_list(value: Any, limit: int = 32) -> list[str]:
    # 列表只保留短标签；路径、URL、空值和重复项会被剔除。
    if value in (None, ""):
        return []
    items = value if isinstance(value, list) else [value]
    result: list[str] = []
    for item in list(items)[:limit]:
        if isinstance(item, dict):
            text = _safe_text(item.get("name") or item.get("step") or item.get("reason") or item.get("summary") or item.get("label"))
        else:
            text = _safe_text(item)
        if text and not PATH_LIKE_RE.search(text) and not URL_OR_QUEUE_RE.search(text):
            result.append(text)
    return list(dict.fromkeys(result))


def _read_json(path: str, label: str, required: bool = True) -> tuple[dict[str, Any], str]:
    # 读取错误统一变成可审计 blocked reason，不把 traceback 暴露给下游。
    if not path:
        return {}, f"{label}_json_not_provided" if required else ""
    try:
        payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, f"{label}_json_missing"
    except json.JSONDecodeError:
        return {}, f"{label}_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, f"{label}_json_read_error"
    if not isinstance(payload, dict):
        return {}, f"{label}_json_not_object"
    return payload, ""


def _dict(value: Any) -> dict[str, Any]:
    # wrapper 只接受 object，不解析字符串化 JSON，避免 raw payload 被绕过。
    return value if isinstance(value, dict) else {}


def _candidates(payload: dict[str, Any], wrapper_keys: tuple[str, ...]) -> list[dict[str, Any]]:
    # 只递归白名单 wrapper key，控制输入可信面。
    candidates = [payload]
    for key in wrapper_keys:
        child = _dict(payload.get(key))
        if child:
            candidates.extend(_candidates(child, wrapper_keys))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # source 必须命中上一跳 handoff schema、capability 或 Robot safe alias。
    for candidate in _candidates(payload, SOURCE_WRAPPER_KEYS):
        schema = _safe_text(candidate.get("schema"))
        capability = _safe_text(candidate.get("capability"))
        if schema in SUPPORTED_SOURCE_SCHEMAS or capability == SOURCE_CAPABILITY:
            return candidate
    return payload


def _find_ack(payload: dict[str, Any]) -> dict[str, Any]:
    # ACK packet 可 schema 化，也可作为最小 reviewer-safe 表单输入。
    for candidate in _candidates(payload, ACK_WRAPPER_KEYS):
        schema = _safe_text(candidate.get("schema"))
        if schema in ACK_SCHEMAS and (_ack_ref(candidate) or _ack_state(candidate)):
            return candidate
    return payload


def _safe_ref(value: Any) -> str:
    # evidence_ref 只能是短安全标识，不能是路径、URL 或凭证。
    text = material_pack._safe_ref(_safe_text(value))
    if text and SAFE_REF_RE.fullmatch(text) and not PATH_LIKE_RE.search(text) and not URL_OR_QUEUE_RE.search(text):
        return text
    return ""


def _source_ref(source: dict[str, Any]) -> str:
    # 上一跳 summary 可能在 top-level 或 safe_copy/review_handoff 中重复 ref。
    refs: list[str] = []
    for candidate in _candidates(source, SOURCE_WRAPPER_KEYS):
        for key in ("safe_evidence_ref", "evidence_ref"):
            ref = _safe_ref(candidate.get(key))
            if ref:
                refs.append(ref)
    unique_refs = list(dict.fromkeys(refs))
    return unique_refs[0] if len(unique_refs) == 1 else ""


def _ack_ref(ack: dict[str, Any]) -> str:
    # ACK packet 必须显式带同一个 safe evidence_ref；缺失时不能 acknowledged。
    return _safe_ref(ack.get("safe_evidence_ref") or ack.get("evidence_ref"))


def _ack_state(ack: dict[str, Any]) -> str:
    # 输入可用短状态，输出统一使用本 gate canonical 状态。
    for key in ("reviewer_ack_state", "ack_state", "acknowledgement_state", "acknowledgment_state", "status"):
        value = _safe_text(ack.get(key)).lower()
        if value in {ACK_ACCEPTED_ACKNOWLEDGED, "accepted", "acknowledged", "accepted_acknowledged", "reviewer_acknowledged"}:
            return ACK_ACCEPTED_ACKNOWLEDGED
        if value in {ACK_NEEDS_REASSIGNMENT, "reassignment_requested", "needs_owner_reassignment"}:
            return ACK_NEEDS_REASSIGNMENT
    if ack.get("acknowledged") is True or ack.get("reviewer_acknowledged") is True:
        return ACK_ACCEPTED_ACKNOWLEDGED
    return ""


def _source_status(source: dict[str, Any]) -> str:
    # handoff_status 在 artifact/summary/safe_copy 中位置可能不同。
    for candidate in _candidates(source, SOURCE_WRAPPER_KEYS):
        status = _safe_text(candidate.get("handoff_status") or candidate.get("status"))
        if status:
            return status
    return ""


def _source_boundary(source: dict[str, Any]) -> str:
    # boundary 可以用 evidence_boundary 或 boundary 表达，但必须等于上一跳边界。
    return _safe_text(source.get("evidence_boundary") or source.get("boundary"))


def _source_schema(source: dict[str, Any]) -> str:
    # schema 是防止串错 gate 的第一层合同。
    return _safe_text(source.get("schema"))


def _source_has_required_capability(source: dict[str, Any]) -> bool:
    # capability 允许嵌套在 safe_copy 中，因为 Robot/mobile 常消费 summary wrapper。
    return _safe_text(source.get("capability")) == SOURCE_CAPABILITY or SOURCE_CAPABILITY in _encoded(source)


def _has_supported_source_contract(source: dict[str, Any]) -> bool:
    # schema、boundary、capability 三者同时满足才允许进入 reviewer ACK intake。
    return (
        bool(source)
        and _source_schema(source) in SUPPORTED_SOURCE_SCHEMAS
        and _source_boundary(source) == SOURCE_BOUNDARY
        and _source_has_required_capability(source)
    )


def _is_software_not_proven(payload: dict[str, Any]) -> bool:
    # source 和 ACK 都必须保留 software_proof/not_proven/三类 false flag。
    encoded = _encoded(payload)
    return (
        _safe_text(payload.get("source")) == SOURCE
        and "not_proven" in encoded
        and "hardware_material_pending" in encoded
        and payload.get("delivery_success") is False
        and payload.get("primary_actions_enabled") is False
        and payload.get("safe_to_control") is False
    )


def _unsafe_key_paths(value: Any, prefix: str = "") -> list[str]:
    # 只记录命中的字段路径类别，不回显敏感字段值。
    paths: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            key_path = f"{prefix}.{key_text}" if prefix else key_text
            if any(term in key_text.lower() for term in FORBIDDEN_KEY_TERMS):
                paths.append(key_path)
            paths.extend(_unsafe_key_paths(child, key_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(_unsafe_key_paths(child, f"{prefix}[{index}]"))
    return paths


def _has_true_control_flag(value: Any) -> bool:
    # JSON boolean true 比自然语言更危险，必须递归阻断。
    if isinstance(value, dict):
        if value.get("delivery_success") is True or value.get("primary_actions_enabled") is True or value.get("safe_to_control") is True:
            return True
        return any(_has_true_control_flag(child) for child in value.values())
    if isinstance(value, list):
        return any(_has_true_control_flag(child) for child in value)
    return False


def _unsafe_reasons(value: dict[str, Any], *, scan_runtime_terms: bool) -> list[str]:
    # source 允许上一跳 non_access_scope 提到 serial_uart；ACK/raw wrapper 不允许。
    if not value:
        return []
    reasons: list[str] = []
    encoded = _encoded(value)
    # safe source/ACK copy may say unresolved/not_resolved; those are required false-state markers.
    scan_text = encoded.replace("unresolved", "not-open").replace("not_resolved_by_this_gate", "not-open")
    if _unsafe_key_paths(value):
        reasons.append("forbidden_raw_control_credential_hardware_hil_or_resolution_fields")
    runtime_patterns = FORBIDDEN_CLAIM_PATTERNS if scan_runtime_terms else FORBIDDEN_CLAIM_PATTERNS[:11]
    if PATH_LIKE_RE.search(encoded) or URL_OR_QUEUE_RE.search(encoded) or any(pattern.search(scan_text) for pattern in runtime_patterns):
        reasons.append("unsafe_raw_path_credential_ros_control_hardware_success_hil_or_pr5_claim")
    if _has_true_control_flag(value):
        reasons.append("true_control_or_success_flag_overclaim")
    if material_pack._has_forbidden_copy(value) or material_pack._has_raw_path_copy(value):
        reasons.append("material_pack_forbidden_copy_or_raw_path")
    return list(dict.fromkeys(reasons))


def _ack_fields(ack: dict[str, Any]) -> dict[str, Any]:
    # ACK 只允许 reviewer 身份标签、原因和三方下一步，不复制 raw reviewer body。
    return {
        "reviewer_role": _safe_text(ack.get("reviewer_role") or ack.get("role")),
        "reviewer_identity_label": _safe_text(ack.get("reviewer_identity_label") or ack.get("reviewer_label") or ack.get("reviewer")),
        "ack_reason": _safe_text(ack.get("ack_reason") or ack.get("reason")),
        "owner_next_step": _safe_text(ack.get("owner_next_step")),
        "support_next_step": _safe_text(ack.get("support_next_step")),
        "reviewer_next_step": _safe_text(ack.get("reviewer_next_step")),
        "next_required_evidence": _safe_list(ack.get("next_required_evidence")),
        "reassignment_target": _safe_text(ack.get("reassignment_target") or ack.get("new_owner") or ack.get("target_owner")),
    }


def _missing_ack_fields(fields: dict[str, Any], ack_state: str) -> list[str]:
    # acknowledged 必须能让 owner/support/reviewer 都知道下一步。
    required = [
        "reviewer_role",
        "reviewer_identity_label",
        "ack_reason",
        "owner_next_step",
        "support_next_step",
        "reviewer_next_step",
    ]
    missing = [key for key in required if not fields.get(key)]
    if not fields["next_required_evidence"]:
        missing.append("next_required_evidence")
    if ack_state == ACK_NEEDS_REASSIGNMENT and not fields["reassignment_target"]:
        missing.append("reassignment_target")
    return missing


def _normalize(
    source_payload: dict[str, Any],
    source_issue: str,
    ack_payload: dict[str, Any],
    ack_issue: str,
    requested_ref: str,
) -> dict[str, Any]:
    # normalized 是唯一决策面，artifact 不直接复制输入对象。
    source = _find_source(source_payload) if source_payload else {}
    ack = _find_ack(ack_payload) if ack_payload else {}
    source_ref = _source_ref(source) if source else ""
    ack_ref = _ack_ref(ack) if ack else ""
    requested = _safe_ref(requested_ref)
    effective_ref = requested or source_ref or ack_ref or "missing_safe_evidence_ref"
    ack_state = _ack_state(ack) if ack else ""
    ack_fields = _ack_fields(ack) if ack else {
        "reviewer_role": "",
        "reviewer_identity_label": "",
        "ack_reason": "",
        "owner_next_step": "",
        "support_next_step": "",
        "reviewer_next_step": "",
        "next_required_evidence": [],
        "reassignment_target": "",
    }
    return {
        "source_issue": source_issue,
        "ack_issue": ack_issue,
        "source": source,
        "ack": ack,
        "source_schema": _source_schema(source),
        "source_boundary": _source_boundary(source),
        "source_capability_present": _source_has_required_capability(source),
        "source_handoff_status": _source_status(source),
        "source_ref": source_ref,
        "ack_ref": ack_ref,
        "requested_ref": requested,
        "safe_evidence_ref": effective_ref,
        "ack_schema": _safe_text(ack.get("schema")) if ack else "",
        "ack_state": ack_state,
        "ack_fields": ack_fields,
        "missing_ack_fields": _missing_ack_fields(ack_fields, ack_state),
        "source_is_safe": _is_software_not_proven(source) if source else False,
        "ack_is_safe": _is_software_not_proven(ack) if ack else False,
        "source_supported": _has_supported_source_contract(source),
        "source_unsafe_reasons": _unsafe_reasons(source_payload, scan_runtime_terms=False) if source_payload else [],
        "ack_unsafe_reasons": _unsafe_reasons(ack_payload, scan_runtime_terms=True) if ack_payload else [],
    }


def _ack_decision(normalized: dict[str, Any]) -> tuple[str, list[str], int]:
    # fail-closed 顺序固定：缺 source -> unsafe -> ref mismatch -> ACK 字段。
    if normalized["source_issue"]:
        return ACK_BLOCKED_MISSING_HANDOFF, [normalized["source_issue"]], 2
    if not normalized["source_supported"]:
        return ACK_BLOCKED_MISSING_HANDOFF, ["unsupported_or_missing_pr5_owner_response_review_handoff_schema_boundary_or_capability"], 2
    if normalized["source_handoff_status"] != handoff_gate.READY:
        if normalized["source_handoff_status"] == handoff_gate.REJECTED_UNSAFE:
            return ACK_REJECTED_UNSAFE, ["source_owner_response_review_handoff_rejected_unsafe"], 5
        return ACK_BLOCKED_MISSING_HANDOFF, ["source_owner_response_review_handoff_not_ready"], 2
    if normalized["source_unsafe_reasons"]:
        return ACK_REJECTED_UNSAFE, normalized["source_unsafe_reasons"], 5
    if not normalized["source_is_safe"]:
        return ACK_REJECTED_UNSAFE, ["source_not_software_proof_hardware_material_pending_not_proven_or_false_flags_changed"], 5
    if not normalized["safe_evidence_ref"] or not normalized["source_ref"]:
        return ACK_EVIDENCE_REF_MISMATCH, ["missing_safe_evidence_ref"], 3
    if normalized["requested_ref"] and normalized["requested_ref"] != normalized["safe_evidence_ref"]:
        return ACK_EVIDENCE_REF_MISMATCH, ["requested_evidence_ref_mismatch"], 3
    if normalized["source_ref"] != normalized["safe_evidence_ref"]:
        return ACK_EVIDENCE_REF_MISMATCH, ["source_or_requested_evidence_ref_mismatch"], 3
    if not normalized["ack"]:
        return ACK_NEEDS_REASSIGNMENT, ["reviewer_ack_missing_or_unsupported_state"], 4
    if normalized["ack_issue"]:
        return ACK_NEEDS_REASSIGNMENT, [normalized["ack_issue"]], 4
    if normalized["ack_unsafe_reasons"]:
        return ACK_REJECTED_UNSAFE, normalized["ack_unsafe_reasons"], 5
    if normalized["ack_schema"] not in ACK_SCHEMAS:
        return ACK_REJECTED_UNSAFE, ["unsupported_reviewer_ack_schema"], 5
    if not normalized["ack_is_safe"]:
        return ACK_REJECTED_UNSAFE, ["ack_not_software_proof_hardware_material_pending_not_proven_or_false_flags_changed"], 5
    if not normalized["ack_ref"]:
        return ACK_EVIDENCE_REF_MISMATCH, ["missing_ack_safe_evidence_ref"], 3
    if normalized["ack_ref"] != normalized["safe_evidence_ref"]:
        return ACK_EVIDENCE_REF_MISMATCH, ["source_ack_or_requested_evidence_ref_mismatch"], 3
    if normalized["ack_state"] not in {ACK_ACCEPTED_ACKNOWLEDGED, ACK_NEEDS_REASSIGNMENT}:
        return ACK_NEEDS_REASSIGNMENT, ["reviewer_ack_missing_or_unsupported_state"], 4
    if normalized["missing_ack_fields"]:
        return ACK_NEEDS_REASSIGNMENT, [f"missing_ack_field:{field}" for field in normalized["missing_ack_fields"]], 4
    if normalized["ack_state"] == ACK_NEEDS_REASSIGNMENT:
        return ACK_NEEDS_REASSIGNMENT, ["reviewer_requested_safe_reassignment_without_success_claim"], 0
    return ACK_ACCEPTED_ACKNOWLEDGED, ["reviewer_acknowledged_not_proven_under_same_safe_evidence_ref"], 0


def _pr5_thread() -> dict[str, str]:
    # 本地 gate 只记录保守状态，不做 GitHub API mutation。
    return {
        "thread_id": THREAD_ID,
        "state": "unresolved",
        "material_state": "hardware_material_pending",
        "reviewer_resolution": "not_resolved_by_this_gate",
    }


def _source_summary(normalized: dict[str, Any]) -> dict[str, Any]:
    # source summary 只保留上一跳合同字段，不复制完整 handoff artifact。
    return {
        **_safe_flags(),
        "schema": normalized["source_schema"],
        "capability": SOURCE_CAPABILITY,
        "evidence_boundary": normalized["source_boundary"],
        "handoff_status": normalized["source_handoff_status"],
        "safe_evidence_ref": normalized["source_ref"],
        "evidence_ref": normalized["source_ref"],
        "previous_capability_present": bool(normalized["source_capability_present"]),
        "previous_boundary_present": normalized["source_boundary"] == SOURCE_BOUNDARY,
    }


def _reviewer_ack_summary(state: str, normalized: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    # reviewer_ack 只输出角色/标签/下一步，不输出 ACK packet 原文。
    fields = normalized["ack_fields"]
    return {
        **_safe_flags(),
        "schema": normalized["ack_schema"] or "reviewer_safe_ack_form",
        "reviewer_ack_state": state,
        "reviewer_role": fields["reviewer_role"],
        "reviewer_identity_label": fields["reviewer_identity_label"],
        "ack_reason": fields["ack_reason"] or ";".join(reasons)[:160],
        "owner_next_step": fields["owner_next_step"],
        "support_next_step": fields["support_next_step"],
        "reviewer_next_step": fields["reviewer_next_step"],
        "reassignment_target": fields["reassignment_target"] if state == ACK_NEEDS_REASSIGNMENT else "",
        "safe_evidence_ref": normalized["safe_evidence_ref"],
        "evidence_ref": normalized["safe_evidence_ref"],
        "same_evidence_ref_required": True,
        "pr5_thread": _pr5_thread(),
    }


def _next_required_evidence(state: str, normalized: dict[str, Any], reasons: list[str]) -> list[str]:
    # next_required_evidence 只描述人工补证和复核动作，不包含机器人命令。
    fields = normalized["ack_fields"]
    if state == ACK_ACCEPTED_ACKNOWLEDGED:
        return fields["next_required_evidence"] or [
            "keep reviewer ACK attached to the same safe evidence_ref",
            "collect real 2D LiDAR and ToF material packet before PR #5 resolution or HIL claims",
        ]
    if state == ACK_NEEDS_REASSIGNMENT:
        return fields["next_required_evidence"] or [
            "assign reviewer role and identity under the same safe evidence_ref",
            "resubmit reviewer ACK reason plus owner/support/reviewer next steps",
        ]
    if state == ACK_EVIDENCE_REF_MISMATCH:
        return ["rerun previous handoff and reviewer ACK packet under the same safe evidence_ref"]
    if state == ACK_REJECTED_UNSAFE:
        return ["remove raw bodies, local paths, credentials, ROS/control, serial/UART, HIL/pass, GitHub mutation, and success/control claims"]
    return ["provide supported PR #5 owner-response review-handoff safe output and optional reviewer ACK packet under the same safe evidence_ref"]


def _rerun_commands(evidence_ref: str) -> list[str]:
    # commands 只覆盖 PC evidence gate，不包含 ROS、serial、GitHub 写接口或网络。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"python3 pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.py --owner-response-review-handoff-json <pr5_mandatory_sensor_material_owner_response_review_handoff_summary.json> --reviewer-ack-json <reviewer_ack_packet.json> --evidence-ref {ref}",
        "keep source=software_proof, hardware_material_pending, not_proven, delivery_success=false, primary_actions_enabled=false, and safe_to_control=false",
        f"keep PR thread {THREAD_ID} unresolved until live reviewer state changes outside this gate",
    ]


def _safe_copy(state: str, normalized: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，字段保持短且稳定。
    return {
        **_safe_flags(),
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "capability": CAPABILITY,
        "source_capability": SOURCE_CAPABILITY,
        "reviewer_ack_state": state,
        "ack_reasons": reasons,
        "safe_evidence_ref": normalized["safe_evidence_ref"],
        "evidence_ref": normalized["safe_evidence_ref"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "source_evidence_boundary": normalized["source_boundary"],
        "source_handoff_status": normalized["source_handoff_status"],
        "pr5_thread": _pr5_thread(),
        "boundary_note": BOUNDARY_NOTE,
        "safe_copy_text": (
            f"{CAPABILITY}: reviewer_ack_state={state}; source_handoff_status={normalized['source_handoff_status'] or 'blocked'}; "
            f"evidence_ref={normalized['safe_evidence_ref'] or 'blocked'}; source=software_proof; "
            "hardware_material_pending; not_proven; delivery_success=false; "
            "primary_actions_enabled=false; safe_to_control=false."
        ),
    }


def _common_payload(state: str, normalized: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    # common payload 让 artifact、summary、Robot alias 三个视图保持同一合同。
    source_summary = _source_summary(normalized)
    ack_summary = _reviewer_ack_summary(state, normalized, reasons)
    next_required = _next_required_evidence(state, normalized, reasons)
    safe_copy = _safe_copy(state, normalized, reasons)
    return {
        **_safe_flags(),
        "capability": CAPABILITY,
        "source_capability": SOURCE_CAPABILITY,
        "source_schema": normalized["source_schema"],
        "source_evidence_boundary": normalized["source_boundary"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "reviewer_ack_state": state,
        "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake": state,
        "allowed_reviewer_ack_states": list(ACK_STATES),
        "ack_reasons": reasons,
        "thread_id": THREAD_ID,
        "thread_resolution": "unresolved",
        "safe_evidence_ref": normalized["safe_evidence_ref"],
        "evidence_ref": normalized["safe_evidence_ref"],
        "same_evidence_ref_required": True,
        "source_owner_response_review_handoff": source_summary,
        "reviewer_acknowledgement": ack_summary,
        "next_required_evidence": next_required,
        "rerun_commands": _rerun_commands(normalized["safe_evidence_ref"]),
        "safe_copy": safe_copy,
        "summary_alias": ROBOT_ALIAS,
        "pr5_thread": _pr5_thread(),
        "vendor_source_refs": list(VENDOR_REFS),
        "vendor_source_boundary": "source_attribution_only_not_real_sensor_or_hil_proof",
        "not_proven_items": list(NOT_PROVEN_ITEMS),
        "non_access_scope": [
            "raw_owner_response_review_handoff_body",
            "raw_reviewer_ack_body",
            "raw_sensor_materials",
            "ros_graph_or_robot_control",
            "hardware_serial_uart_or_wave_rover_runtime",
            "external_cloud_or_o5_probe",
            "real_phone_browser_runtime",
            "github_pr5_resolution_mutation",
            "okr_percentage_update",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "safety_markers": [
            CAPABILITY,
            EVIDENCE_BOUNDARY,
            "source=software_proof",
            "software_proof",
            "hardware_material_pending",
            "not_proven",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
            THREAD_ID,
            ACK_ACCEPTED_ACKNOWLEDGED,
            ACK_NEEDS_REASSIGNMENT,
            ACK_BLOCKED_MISSING_HANDOFF,
            ACK_REJECTED_UNSAFE,
            ACK_EVIDENCE_REF_MISMATCH,
        ],
    }


def build_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake(
    owner_response_review_handoff_json: str,
    reviewer_ack_json: str = "",
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """构建 reviewer ACK intake；ACK 成功仍只表示 not_proven metadata。"""
    source_payload, source_issue = _read_json(owner_response_review_handoff_json, "owner_response_review_handoff")
    ack_payload, ack_issue = _read_json(reviewer_ack_json, "reviewer_ack", required=False)
    normalized = _normalize(source_payload, source_issue, ack_payload, ack_issue, evidence_ref)
    state, reasons, exit_code = _ack_decision(normalized)
    generated_at = _utc_now()
    common = _common_payload(state, normalized, reasons)
    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "summary_only": True,
        "safe_to_render_on_phone": True,
        **common,
    }
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        **common,
        f"{CAPABILITY}_summary": summary,
        ROBOT_ALIAS: summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "reviewer_ack_intake_diagnostics": {
            "source_issue": source_issue,
            "ack_issue": ack_issue,
            "source_supported": normalized["source_supported"],
            "source_is_software_proof_not_proven": normalized["source_is_safe"],
            "ack_is_software_proof_not_proven": normalized["ack_is_safe"],
            "missing_ack_fields": normalized["missing_ack_fields"],
            "source_unsafe_reasons": normalized["source_unsafe_reasons"],
            "ack_unsafe_reasons": normalized["ack_unsafe_reasons"],
        },
    }
    artifact = material_pack._safe_value(artifact)
    summary = material_pack._safe_value(summary)
    return artifact, summary, exit_code


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    # CLI 写入缩进 JSON，便于 sprint evidence bundle 和人工 review。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只做本地 JSON gate，不提供 fetch、resolve、ACK mutation 或 robot command。
    parser = argparse.ArgumentParser(
        description=(
            "Build trashbot.pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.v1 from previous "
            "pr5_mandatory_sensor_material_owner_response_review_handoff safe metadata and optional reviewer ACK packet. "
            "Keeps source=software_proof, hardware_material_pending, not_proven, delivery_success=false, "
            "primary_actions_enabled=false, safe_to_control=false, PRRT_kwDOSWB9286CJ3tX unresolved, no GitHub mutation, "
            "no WAVE ROVER/UART/HIL proof, and no OKR percentage lift."
        )
    )
    parser.add_argument("--owner-response-review-handoff-json", "--handoff-json", "--input", dest="owner_response_review_handoff_json", required=True, help="previous owner response review handoff artifact, summary, Robot alias, or wrapper JSON")
    parser.add_argument("--reviewer-ack-json", default="", help="optional reviewer-safe ACK packet JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same safe evidence_ref")
    parser.add_argument("--output-dir", type=Path, help="optional directory for reviewer ACK intake artifact and summary")
    parser.add_argument("--output", type=Path, help="optional reviewer ACK intake artifact JSON output path")
    parser.add_argument("--summary-output", type=Path, help="optional reviewer ACK intake summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print reviewer ACK intake artifact JSON to stdout")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake(
        args.owner_response_review_handoff_json,
        args.reviewer_ack_json,
        args.evidence_ref,
    )
    output = args.output
    summary_output = args.summary_output
    if args.output_dir:
        output = output or args.output_dir / "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.json"
        summary_output = summary_output or args.output_dir / "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary.json"
    if output:
        _write_json(output, artifact)
    if summary_output:
        _write_json(summary_output, summary)
    if args.once_json or not (output or summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"{CAPABILITY}: artifact_file:{_safe_text(output)}")
        if summary_output:
            print(f"{CAPABILITY}_summary_file:{_safe_text(summary_output)}")
        print(f"reviewer_ack_state:{artifact['reviewer_ack_state']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
