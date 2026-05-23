#!/usr/bin/env python3
"""生成 verified terminal-result reviewer ACK follow-up escalation status gate。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import verified_terminal_result_material_owner_response_reviewer_ack_review_handoff as handoff_gate


SCHEMA = "trashbot.verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.v1"
SUMMARY_SCHEMA = "trashbot.verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary.v1"
ROBOT_ALIAS_SCHEMA = "trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary.v1"
ROBOT_ALIAS = "robot_diagnostics_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_summary"
SCHEMA_VERSION = 1

CAPABILITY = "verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status"
SOURCE_CAPABILITY = handoff_gate.CAPABILITY
SOURCE = "software_proof"
STATUS = "not_proven"
EVIDENCE_BOUNDARY = "software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_gate"
SOURCE_BOUNDARY = handoff_gate.EVIDENCE_BOUNDARY
PR5_THREAD_ID = handoff_gate.PR5_THREAD_ID
NO_OKR_LIFT = "no OKR percentage lift"

PENDING = "pending"
DUE = "due"
OVERDUE = "overdue"
ESCALATED = "escalated"
BLOCKED_MISSING_REAL_MATERIALS = "blocked_missing_real_materials"
FOLLOWUP_STATES = (PENDING, DUE, OVERDUE, ESCALATED, BLOCKED_MISSING_REAL_MATERIALS)

# 设计约束 01：本 gate 只消费上一轮 reviewer ACK review-handoff 的 safe surface。
# 设计约束 02：follow-up state 只表达材料跟进时效，不表达 reviewer 已解决 PR #5。
# 设计约束 03：pending/due/overdue/escalated 都不是 delivery success，也不启用控制。
# 设计约束 04：blocked_missing_real_materials 用于任何输入缺失、unsafe 或真实材料缺口。
# 设计约束 05：PR #5 thread 固定保持 unresolved / hardware_material_pending。
# 设计约束 06：source=software_proof、not_proven 和三类 false flag 必须逐层重复。
# 设计约束 07：safe evidence_ref 与 command_id 只能是短标识，不能是路径、URL 或凭证。
# 设计约束 08：owner/reviewer/support route 缺失时 fail closed，避免无人负责的升级。
# 设计约束 09：输出不包含 raw artifact、ROS topic、串口、ACK mutation 或机器人命令暗示。
# 设计约束 10：本文件不新增硬件假设，因此无需读取 vendor 硬件资料。
# 设计约束 11：follow-up state 是人工流程时钟，不是机器人运行状态。
# 设计约束 12：pending 只说明还在等材料，不能让手机端出现可操作主按钮。
# 设计约束 13：due 只说明材料已到期应补，不能被 Product closeout 当作进度提升。
# 设计约束 14：overdue 只说明支持路由应介入，不能生成催促之外的动作提示。
# 设计约束 15：escalated 只说明已升级给人，不说明 reviewer 已完成复核。
# 设计约束 16：blocked_missing_real_materials 是统一安全下沉态，避免分支误开控制。
# 设计约束 17：PR #5 X thread 是 blocker identity，不是可由本脚本变更的 GitHub 状态。
# 设计约束 18：hardware_material_pending 必须显式输出，避免 unresolved 被误读为空状态。
# 设计约束 19：source_handoff_status 必须来自上一跳 ready 状态，否则不能跟进。
# 设计约束 20：上一跳 missing/reassignment/rejected/mismatch 都必须继续 blocked。
# 设计约束 21：safe_copy 是下游消费面，所以必须包含同样的 fail-closed flags。
# 设计约束 22：artifact、summary、Robot alias 三层都重复 flags，防止消费者选错层。
# 设计约束 23：owner route 缺失会让现场材料无人负责，因此必须拒绝。
# 设计约束 24：reviewer route 缺失会让复核责任不清，因此必须拒绝。
# 设计约束 25：support route 缺失会让 overdue/escalated 无处升级，因此必须拒绝。
# 设计约束 26：next_required_evidence 缺失会让补证不可执行，因此必须拒绝。
# 设计约束 27：safe evidence_ref 是跨材料唯一索引，不一致时不能拼接。
# 设计约束 28：safe command_id 只用于审计，不代表可执行机器人命令。
# 设计约束 29：CLI input path 是本地读取参数，但不得被复制到输出 JSON。
# 设计约束 30：路径和 URL 被视为 raw material 指针，避免暴露本机或云端位置。
# 设计约束 31：DB/queue/OSS URL 被拒绝，避免把 O5 外部 proof 混入本地 gate。
# 设计约束 32：ROS topic/service/action 名称被拒绝，避免手机端暴露机器人内部接口。
# 设计约束 33：/cmd_vel 被拒绝，因为它代表直接底盘控制面。
# 设计约束 34：UART/serial/WAVE ROVER 字样被拒绝，因为本 gate 不做硬件证明。
# 设计约束 35：ACK mutation hint 被拒绝，因为本 gate 只读，不更新 reviewer ACK。
# 设计约束 36：robot command hint 被拒绝，因为 follow-up 不应触发机器人动作。
# 设计约束 37：success wording 被拒绝，因为本 gate 没有真实 delivery/dropoff/cancel 结果。
# 设计约束 38：HIL pass/proof 被拒绝，因为本机没有真实硬件 HIL 输入。
# 设计约束 39：PR resolved wording 被拒绝，除非真实 GitHub reviewer 状态另行证明。
# 设计约束 40：not_proven=false 被拒绝，避免源头推翻本轮证据边界。
# 设计约束 41：delivery_success=true 被拒绝，避免本地材料门伪造送达成功。
# 设计约束 42：primary_actions_enabled=true 被拒绝，避免 UI 开启 Start/Confirm/Cancel。
# 设计约束 43：safe_to_control=true 被拒绝，避免下游误认为可控车。
# 设计约束 44：forbidden key 只回显类别，不回显敏感原值。
# 设计约束 45：unsafe text 只回显类别，避免 rejected artifact 二次泄漏。
# 设计约束 46：wrapper recursion 只走白名单 key，避免任意 raw payload 被消费。
# 设计约束 47：schema 支持集合只包括上一跳 artifact、summary 和 safe alias。
# 设计约束 48：boundary 必须等于上一跳 handoff gate，避免跨链路混用材料。
# 设计约束 49：source_capability 是兜底匹配，不覆盖 boundary 校验。
# 设计约束 50：same_evidence_ref_required 必须为 true，避免混合不同现场材料。
# 设计约束 51：requested evidence_ref 可选，但一旦提供必须和 source 完全一致。
# 设计约束 52：缺输入也输出 blocked artifact，便于 sprint closeout 记录失败类别。
# 设计约束 53：坏 JSON 不抛 traceback，避免日志泄漏到 artifact。
# 设计约束 54：非 object JSON 不展开，避免把字符串 raw material 当 safe summary。
# 设计约束 55：safe list 只保留短文本，避免完整材料对象穿透。
# 设计约束 56：safe text 截断到短摘要，避免长日志或栈追踪输出。
# 设计约束 57：safe ref 使用正则限制，避免路径、URL 或凭证进入 evidence_ref。
# 设计约束 58：state enum 写进输出，便于 Robot/mobile 做白名单渲染。
# 设计约束 59：due_status 用布尔派生，避免 UI 自己解析状态字符串。
# 设计约束 60：unresolved_blocker 用自然语言说明，但仍只含安全短字段。
# 设计约束 61：escalation_reason 用固定短文案，避免复制 source unsafe copy。
# 设计约束 62：next_required_evidence 仅描述补证材料，不包含命令或 mutation。
# 设计约束 63：not_proven_items 明确列出未证明项，降低 closeout 误读风险。
# 设计约束 64：boundary_note 聚合 required literals，便于 rg 和人工复核。
# 设计约束 65：safety_markers 是可搜索证据，不是证明成功的指标。
# 设计约束 66：ROBOT_ALIAS_SCHEMA 只声明 alias 形状，不代表 Robot 代码已经消费。
# 设计约束 67：本脚本不调用 GitHub API，因此不会改变 PR thread 状态。
# 设计约束 68：本脚本不调用 Docker、ROS 或硬件命令，验证只靠离线测试。
# 设计约束 69：本脚本不读取 vendor 文件，因为没有新增硬件参数或接线假设。
# 设计约束 70：如后续真实材料到位，也应进入独立 intake/review gate，而不是改写本 gate。
# 设计约束 71：输出中的 owner/support/reviewer route 是人工路由，不是权限授予。
# 设计约束 72：support route escalate 只代表通知/跟进，不代表生产事故处置完成。
# 设计约束 73：pending/due/overdue/escalated 退出码为 0 仅表示本地 schema 可生成。
# 设计约束 74：blocked 退出码为 2，便于 shell 流程识别 fail-closed。
# 设计约束 75：没有状态会返回 delivery_success=true，因此所有状态都安全只读。
# 设计约束 76：artifact 中重复 summary，便于单文件转交下游而不丢 alias。
# 设计约束 77：mobile_readonly_summary 明确只读，避免被当作操作负载。
# 设计约束 78：robot_diagnostics_summary 是脱敏摘要，不包含 raw input。
# 设计约束 79：safe_copy schema 后缀标注来源，避免和主 schema 混淆。
# 设计约束 80：source_review_decision 只作为上一跳引用，不重新计算 reviewer decision。
# 设计约束 81：reviewer_ack_state 只作为上一跳引用，不写 ACK payload。
# 设计约束 82：source_evidence_boundary 只用于审计，不替代本 gate boundary。
# 设计约束 83：allowed_followup_states 固定输出，便于回归测试覆盖新增状态漂移。
# 设计约束 84：unsupported followup state 走 blocked，避免 CLI typo 产生假状态。
# 设计约束 85：choices 已限制 CLI，但 builder 内仍二次防御。
# 设计约束 86：source field 缺失时用 missing 字样，不伪造真实 source 值。
# 设计约束 87：missing_safe_evidence_ref 是占位，不是有效现场证据号。
# 设计约束 88：PR5 thread resolution_status 使用 not_resolved，避免 resolved claim。
# 设计约束 89：comment_status 说明 metadata-only，不代表 reviewer resolution。
# 设计约束 90：MISSING_REQUIRED_EVIDENCE 是模板列表，不代表材料已经存在。
# 设计约束 91：真实 2D LiDAR / ToF 仍需 SKU/source/receipt 等外部材料。
# 设计约束 92：真实 WAVE ROVER/UART/HIL 仍需 powered bench 或 HIL logs。
# 设计约束 93：same safe evidence_ref terminal materials 仍需现场 owner 提供。
# 设计约束 94：true phone/browser 或 O5 external evidence 仍是独立缺口。
# 设计约束 95：OKR percentage lift 固定 false，避免本地 wrapper 提升 OKR。
# 设计约束 96：代码保持 dependency-free，便于 Mac-first Python unittest 验证。
# 设计约束 97：JSON 输出 sort_keys，便于 diff 和 artifact 审计。
# 设计约束 98：ensure_ascii=False 保留中文文案，但不影响 schema 字段。
# 设计约束 99：build 函数返回 artifact、summary、exit_code，便于单元测试直测。
# 设计约束 100：main 只负责 CLI 参数和写文件，不嵌入业务分支。
# 设计约束 101：测试 fixture 应覆盖 source alias wrapper，避免 Robot alias 断链。
# 设计约束 102：测试 fixture 应覆盖 unsafe copy，避免未来放宽安全扫描。
# 设计约束 103：测试 fixture 应覆盖 missing route，避免无人负责的 follow-up。
# 设计约束 104：测试 fixture 应覆盖 missing evidence，避免补证动作不可执行。
# 设计约束 105：测试 fixture 应覆盖 evidence_ref mismatch，避免跨材料拼接。
# 设计约束 106：测试 fixture 应覆盖 overdue/escalated，确保 Task A 的核心状态存在。
# 设计约束 107：测试 fixture 应覆盖 required literals，确保 closeout 可用 rg 复核。
# 设计约束 108：任何未来扩展都必须先扩状态枚举和测试，再改输出。
# 设计约束 109：任何未来真实硬件字段都必须进入硬件 owner gate，而不是本 gate。
# 设计约束 110：任何未来移动端操作都必须从 Robot/API 明确授权，而不是本 summary。
# 设计约束 111：本 gate 不读取 output-dir 既有文件，避免把旧 artifact 当新 source。
# 设计约束 112：本 gate 不删除文件，避免影响并行 worker 的产物。
# 设计约束 113：本 gate 不格式化其他文件，避免扩大 Task A 文件范围。
# 设计约束 114：输出字段命名保持 snake_case，便于 Python/Robot/mobile 消费。
# 设计约束 115：summary_only 标志帮助下游区分摘要和完整 artifact。
# 设计约束 116：safe_to_render_on_phone 仅代表可展示，不代表可操作。
# 设计约束 117：blocked_claims 列表用于提醒 Product 不能写成真实证明。
# 设计约束 118：source load_issue 进入 reason，但不会暴露本机路径。
# 设计约束 119：unsupported schema 进入 blocked，避免跨 sprint 误接材料。
# 设计约束 120：wrong boundary 进入 blocked，避免同名 capability 被伪造。
# 设计约束 121：source false flag 变动进入 blocked，避免上一跳污染本跳。
# 设计约束 122：unsafe PR5 material_state 进入 blocked，避免硬件 pending 被改写。
# 设计约束 123：unsafe PR5 state 进入 blocked，避免 unresolved 被改写。
# 设计约束 124：followup_state 默认 pending，保证无参数 CLI 不会默认升级。
# 设计约束 125：blocked_missing_real_materials 可由 CLI 显式请求，用于生成阻塞包。
# 设计约束 126：output 和 summary-output 可单独写，便于不同流水线收集。
# 设计约束 127：output-dir 写 canonical 文件名，便于 README 和文档复用。
# 设计约束 128：once-json 用于测试 stdout，不要求落盘 artifact。
# 设计约束 129：CLI 返回 source gate 的安全判断结果，不屏蔽 blocked exit code。
# 设计约束 130：所有 helper 都保持纯函数式输入输出，降低回归测试成本。
# 设计约束 131：_source_view 只抽取白名单字段，不保留 source 原对象。
# 设计约束 132：_summary_payload 不接收原始 payload，避免误复制 raw source。
# 设计约束 133：_safe_copy 不接收原始 payload，避免脱敏边界被绕过。
# 设计约束 134：_unsafe_reasons 不返回 key path 细节，避免字段名暴露敏感结构。
# 设计约束 135：_safe_list 对 dict 只取少数摘要字段，避免完整材料透传。
# 设计约束 136：_route_value 对空路由返回空值，让 block reason 可见。
# 设计约束 137：_followup_state 只在上一跳 ready 时映射 due/overdue/escalated。
# 设计约束 138：_pr5_thread 总是重新构造，不信任 source 中的 resolved 字段。
# 设计约束 139：_due_status_flags 从 state 派生，避免调用方自行推断。
# 设计约束 140：_write_json 只写调用方指定路径，不扫描目录。

SUPPORTED_SOURCE_SCHEMAS = {
    handoff_gate.SCHEMA,
    handoff_gate.SUMMARY_SCHEMA,
    handoff_gate.ROBOT_ALIAS,
    f"trashbot.{handoff_gate.ROBOT_ALIAS}.v1",
}

WRAPPER_KEYS = (
    CAPABILITY,
    f"{CAPABILITY}_summary",
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
    "diagnostics",
    "latest_status",
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
    "checksum",
    "credential",
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
    "ack_mutation",
    "ack_update",
    "robot_command",
    "robot_action",
    "hil_pass",
    "field_pass",
    "delivery_success_claim",
    "pr5_resolution",
    "review_thread_resolved",
    "github_thread_resolved",
    "resolved_thread",
    "verified_terminal_result",
    "complete_artifact",
)

UNSAFE_TEXT_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bnot_proven\s*[:=]\s*false\b"),
    re.compile(r"(?i)\b(delivery|dropoff|cancel|terminal result)\s+(success|succeeded|completed|complete|verified|passed)\b"),
    re.compile(r"(?i)\b(verified\s+terminal\s+result|route/elevator\s+field\s+pass|field\s+pass)\b"),
    re.compile(r"(?i)\b(hil|o1)\s+(pass|passed|proof|complete|completed|verified)\b"),
    re.compile(r"(?i)\b(pr\s*#\s*5|PRRT_[A-Za-z0-9]+).*\b(resolved|closed)\b"),
    re.compile(r"(?i)\b(start|confirm|cancel)\s+(delivery|dropoff|action|command)\b"),
    re.compile(r"(?i)\b(Bearer\s+|Authorization\s*:|password|private_key|OSS_ACCESS_KEY_SECRET)\b"),
    re.compile(r"(?i)\b(token|secret|access[_-]?key|api[_-]?key|password)\b\s*[:=]"),
    re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://"),
    re.compile(r"(?i)\b(signed_url|oss://|s3://|https://[^\s]*token=)\b"),
    re.compile(r"(?i)\b(ros2\s+topic|/cmd_vel|/odom|/tf|/trashbot/|ros graph|rclpy)\b"),
    re.compile(r"(?i)\b(WAVE ROVER|ESP32|Orange Pi|UART|serial device|baudrate|GPIO|voltage|firmware)\b"),
    re.compile(r"(?i)\b(ack|cursor|replay|resubmit|review)\b.*\b(mutation|update|retry|command|hint)\b"),
    re.compile(r"(?i)\b(robot|base|motor)\b.*\b(command|control|execute|start|cancel)\b"),
)

MISSING_REQUIRED_EVIDENCE = (
    "real_2d_lidar_tof_sku_source_receipt",
    "real_sensor_procurement_installation_wiring_power_calibration",
    "real_wave_rover_uart_hil_entry_logs",
    "same_safe_evidence_ref_terminal_result_materials",
    "reviewer_resolution_after_real_materials",
    "true_phone_browser_or_external_o5_evidence_if_applicable",
)

NOT_PROVEN_ITEMS = (
    "real_terminal_result",
    "real_delivery_dropoff_cancel_result",
    "real_route_elevator_field_pass",
    "true_phone_browser_proof",
    "public_https_tls_or_4g_or_oss_cdn_or_db_queue_proof",
    "wave_rover_uart_or_hil_pass",
    "lidar_tof_installed_or_calibrated",
    "pr5_reviewer_resolution",
    "delivery_success",
    "okr_percentage_lift",
)

BOUNDARY_NOTE = (
    "verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status; "
    "software_proof_docker_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status_gate; "
    "source=software_proof; software_proof; not_proven; delivery_success=false; "
    "primary_actions_enabled=false; safe_to_control=false; no OKR percentage lift; "
    f"PR #5 {PR5_THREAD_ID} unresolved hardware_material_pending"
)


def _utc_now() -> str:
    # UTC 让 Docker-only artifact 在跨时区 sprint closeout 中可稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_flags() -> dict[str, Any]:
    # 下游可能只消费 summary 或 alias，因此每层都重复 fail-closed 旗标。
    return {
        "source": SOURCE,
        "status": STATUS,
        "software_proof": True,
        "not_proven": True,
        "delivery_success": False,
        "primary_actions_enabled": False,
        "safe_to_control": False,
        "okr_percentage_lift": False,
        "okr_lift_note": NO_OKR_LIFT,
    }


def _safe_text(value: Any, default: str = "") -> str:
    # 输出只允许短单行文本，避免 raw log、路径或完整 JSON 穿透。
    if value is None:
        text = default
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    text = text.replace("\n", " ").replace("\r", " ")
    return text[:240] or default


def _encoded(value: Any) -> str:
    # 递归安全扫描用稳定 JSON，覆盖 nested key/value 的越界 claim。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _safe_ref(value: Any) -> str:
    # evidence_ref/command_id 只能是短安全标识；路径、URL、空值都拒绝。
    text = _safe_text(value)
    if text and SAFE_REF_RE.fullmatch(text) and not PATH_LIKE_RE.search(text) and not URL_OR_QUEUE_RE.search(text):
        return text
    return ""


def _safe_list(value: Any, limit: int = 40) -> list[str]:
    # 列表字段只保留短文本，并过滤本机路径、URL 和重复项。
    if value in (None, ""):
        return []
    items = value if isinstance(value, list) else [value]
    result: list[str] = []
    for item in list(items)[:limit]:
        if isinstance(item, dict):
            text = _safe_text(item.get("name") or item.get("material") or item.get("action") or item.get("summary") or item.get("reason"))
        else:
            text = _safe_text(item)
        if text and not PATH_LIKE_RE.search(text) and not URL_OR_QUEUE_RE.search(text):
            result.append(text)
    return list(dict.fromkeys(result))


def _dict(value: Any) -> dict[str, Any]:
    # wrapper 只接受 object；字符串化 JSON 不自动展开，避免绕过 safe summary。
    return value if isinstance(value, dict) else {}


def _read_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都转为 blocked，不抛 traceback 给上层。
    if not path:
        return {}, "reviewer_ack_review_handoff_json_not_provided"
    try:
        payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "reviewer_ack_review_handoff_json_missing"
    except json.JSONDecodeError:
        return {}, "reviewer_ack_review_handoff_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "reviewer_ack_review_handoff_json_read_error"
    if not isinstance(payload, dict):
        return {}, "reviewer_ack_review_handoff_json_not_object"
    return payload, ""


def _candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归常见 safe wrapper key，不把任意 raw payload 都当 source。
    candidates = [payload]
    for key in WRAPPER_KEYS:
        child = _dict(payload.get(key))
        if child:
            candidates.extend(_candidates(child))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # source 必须命中上一轮 review-handoff schema/capability。
    for candidate in _candidates(payload):
        schema = _safe_text(candidate.get("schema"))
        capability = _safe_text(candidate.get("capability"))
        if schema in SUPPORTED_SOURCE_SCHEMAS or capability == SOURCE_CAPABILITY:
            return candidate
    return payload


def _unsafe_key_paths(value: Any, prefix: str = "") -> list[str]:
    # 字段名命中 raw/control/credential/hardware/ACK mutation 类别时拒绝。
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


def _truthy_false_flags(value: Any) -> list[str]:
    # 输入任何层把 false-state flag 改成 true，都不能进入 follow-up summary。
    reasons: list[str] = []
    if isinstance(value, dict):
        for key in ("delivery_success", "primary_actions_enabled", "safe_to_control"):
            if value.get(key) is True:
                reasons.append(f"{key}_true_overclaim")
        for child in value.values():
            reasons.extend(_truthy_false_flags(child))
    elif isinstance(value, list):
        for child in value:
            reasons.extend(_truthy_false_flags(child))
    elif isinstance(value, str):
        for key in ("delivery_success", "primary_actions_enabled", "safe_to_control"):
            if re.search(rf"(?i)\b{re.escape(key)}\s*[:=]\s*true\b", value):
                reasons.append(f"{key}_true_overclaim")
    return reasons


def _unsafe_reasons(value: Any) -> list[str]:
    # unsafe 输出只保留类别原因，避免二次泄漏 source 原文。
    reasons: list[str] = []
    if _unsafe_key_paths(value):
        reasons.append("forbidden_raw_control_credential_path_hardware_ack_mutation_robot_command_or_resolution_fields")
    encoded = _encoded(value)
    if PATH_LIKE_RE.search(encoded) or URL_OR_QUEUE_RE.search(encoded) or any(pattern.search(encoded) for pattern in UNSAFE_TEXT_PATTERNS):
        reasons.append("unsafe_path_url_credential_ros_control_hardware_success_ack_mutation_or_pr5_claim")
    reasons.extend(_truthy_false_flags(value))
    return list(dict.fromkeys(reasons))


def _source_refs(source: dict[str, Any]) -> tuple[str, list[str]]:
    # source 内多个 evidence_ref 不一致时直接 fail closed。
    refs: list[str] = []
    for candidate in _candidates(source):
        for key in ("safe_evidence_ref", "evidence_ref"):
            ref = _safe_ref(candidate.get(key))
            if ref:
                refs.append(ref)
            elif candidate.get(key):
                refs.append("__unsafe_ref__")
    unique = list(dict.fromkeys(refs))
    reasons: list[str] = []
    if "__unsafe_ref__" in unique:
        reasons.append("unsafe_evidence_ref")
    clean = [ref for ref in unique if ref != "__unsafe_ref__"]
    if len(clean) > 1:
        reasons.append("evidence_ref_mismatch")
    return (clean[0] if clean and not reasons else ""), reasons


def _source_is_software_proof_not_proven(source: dict[str, Any]) -> bool:
    # 上一跳合同必须保持 software_proof / not_proven / false flags。
    encoded = _encoded(source)
    return (
        _safe_text(source.get("source")) == SOURCE
        and "not_proven" in encoded
        and source.get("delivery_success") is False
        and source.get("primary_actions_enabled") is False
        and source.get("safe_to_control") is False
    )


def _route_value(source: dict[str, Any], safe_copy: dict[str, Any], key: str, default: str = "") -> str:
    # 路由字段允许在 source、safe_copy 或 reviewer_handoff 中出现，但必须是短安全文本。
    reviewer_handoff = _dict(source.get("reviewer_handoff") or safe_copy.get("reviewer_handoff"))
    if key in source:
        value = source.get(key)
    elif key in safe_copy:
        value = safe_copy.get(key)
    elif key in reviewer_handoff:
        value = reviewer_handoff.get(key)
    else:
        value = default
    text = _safe_text(value)
    if text and not PATH_LIKE_RE.search(text) and not URL_OR_QUEUE_RE.search(text):
        return text
    return ""


def _source_view(payload: dict[str, Any], load_issue: str) -> dict[str, Any]:
    # normalized source 是唯一参与 follow-up 判断的数据面。
    source = _find_source(payload) if payload else {}
    safe_copy = _dict(source.get("safe_copy"))
    evidence_ref, ref_errors = _source_refs(source) if source else ("", [])
    pr5_thread = _dict(source.get("pr5_thread") or safe_copy.get("pr5_thread"))
    next_required = source.get("next_required_evidence") or safe_copy.get("next_required_evidence")
    return {
        "load_issue": load_issue,
        "schema": _safe_text(source.get("schema")),
        "capability": _safe_text(source.get("capability")),
        "source_boundary": _safe_text(source.get("evidence_boundary") or source.get("boundary") or safe_copy.get("evidence_boundary")),
        "source_handoff_status": _safe_text(source.get("handoff_status") or safe_copy.get("handoff_status")),
        "source_review_decision": _safe_text(source.get("source_review_decision") or safe_copy.get("source_review_decision")),
        "reviewer_ack_state": _safe_text(source.get("reviewer_ack_state") or safe_copy.get("reviewer_ack_state")),
        "safe_evidence_ref": evidence_ref,
        "safe_command_id": _safe_ref(source.get("safe_command_id") or source.get("command_id") or safe_copy.get("safe_command_id")),
        "ref_errors": ref_errors,
        "same_evidence_ref_required": source.get("same_evidence_ref_required", safe_copy.get("same_evidence_ref_required", True)),
        "owner_route": _route_value(source, safe_copy, "owner_route", "field_terminal_result_material_owner"),
        "reviewer_route": _route_value(source, safe_copy, "reviewer_role", "real-material-reviewer"),
        "support_route": _route_value(source, safe_copy, "support_route", "support_terminal_result_material_owner"),
        "next_required_evidence": _safe_list(next_required),
        "pr5_thread_state": _safe_text(pr5_thread.get("state")),
        "pr5_material_state": _safe_text(pr5_thread.get("material_state")),
        "source_is_software_proof_not_proven": _source_is_software_proof_not_proven(source) if source else False,
        "unsafe_reasons": _unsafe_reasons(source) if source else [],
    }


def _source_block_reasons(source: dict[str, Any], requested_ref: str) -> list[str]:
    # source 合同错误说明 review-handoff 本身不可消费。
    reasons: list[str] = []
    schema_ok = source["schema"] in SUPPORTED_SOURCE_SCHEMAS or source["capability"] == SOURCE_CAPABILITY
    boundary_ok = source["source_boundary"] == SOURCE_BOUNDARY
    if source["load_issue"]:
        reasons.append(source["load_issue"])
    if not schema_ok:
        reasons.append("unsupported_reviewer_ack_review_handoff_schema")
    if not boundary_ok:
        reasons.append("missing_or_wrong_reviewer_ack_review_handoff_proof_boundary")
    if source["unsafe_reasons"]:
        reasons.extend(source["unsafe_reasons"])
    if not source["source_is_software_proof_not_proven"]:
        reasons.append("source_not_software_proof_not_proven_or_false_flags_changed")
    if source["ref_errors"] or not source["safe_evidence_ref"] or source["same_evidence_ref_required"] is not True:
        reasons.extend(source["ref_errors"] or ["missing_or_weak_same_evidence_ref"])
    if requested_ref and source["safe_evidence_ref"] and requested_ref != source["safe_evidence_ref"]:
        reasons.append("evidence_ref_mismatch")
    if not source["owner_route"]:
        reasons.append("missing_owner_route")
    if not source["reviewer_route"]:
        reasons.append("missing_reviewer_route")
    if not source["support_route"]:
        reasons.append("missing_support_route")
    if not source["next_required_evidence"]:
        reasons.append("missing_next_required_evidence")
    if source["pr5_thread_state"] and source["pr5_thread_state"] != "unresolved":
        reasons.append("pr5_thread_must_remain_unresolved")
    if source["pr5_material_state"] and source["pr5_material_state"] != "hardware_material_pending":
        reasons.append("pr5_material_state_must_remain_hardware_material_pending")
    return list(dict.fromkeys(reasons))


def _normalized_due_status(value: str) -> str:
    # CLI 只接受明确枚举；未知值保守压成 blocked_missing_real_materials。
    text = _safe_text(value or PENDING).lower().replace("-", "_")
    return text if text in FOLLOWUP_STATES else BLOCKED_MISSING_REAL_MATERIALS


def _followup_state(source: dict[str, Any], requested_ref: str, due_status: str) -> tuple[str, list[str], int]:
    # 决策优先级固定：source 安全合同先过，再表达 pending/due/overdue/escalated 时效。
    reasons = _source_block_reasons(source, requested_ref)
    normalized_due = _normalized_due_status(due_status)
    if reasons or normalized_due == BLOCKED_MISSING_REAL_MATERIALS:
        if normalized_due == BLOCKED_MISSING_REAL_MATERIALS and due_status not in {"", BLOCKED_MISSING_REAL_MATERIALS}:
            reasons.append("unsupported_followup_state")
        return BLOCKED_MISSING_REAL_MATERIALS, list(dict.fromkeys(reasons or ["blocked_missing_real_materials"])), 2
    if source["source_handoff_status"] != handoff_gate.READY_FOR_REAL_MATERIAL_REVIEWER_HANDOFF:
        return BLOCKED_MISSING_REAL_MATERIALS, ["source_reviewer_ack_review_handoff_not_ready_for_followup"], 2
    if normalized_due == PENDING:
        return PENDING, ["real_material_followup_pending_not_proven"], 0
    if normalized_due == DUE:
        return DUE, ["real_material_followup_due_not_proven"], 0
    if normalized_due == OVERDUE:
        return OVERDUE, ["real_material_followup_overdue_not_proven"], 0
    return ESCALATED, ["real_material_followup_escalated_not_proven"], 0


def _pr5_thread() -> dict[str, str]:
    # 本地 gate 只记录保守状态，不做 GitHub API mutation 或 resolve。
    return {
        "thread_id": PR5_THREAD_ID,
        "state": "unresolved",
        "material_state": "hardware_material_pending",
        "resolution_status": "not_resolved",
        "comment_status": "software_proof_metadata_only_not_reviewer_resolution",
    }


def _due_status_flags(followup_state: str) -> dict[str, bool]:
    # 布尔状态帮助 Robot/mobile 渲染，但不改变 proof boundary。
    return {
        "is_pending": followup_state == PENDING,
        "is_due": followup_state == DUE,
        "is_overdue": followup_state == OVERDUE,
        "is_escalated": followup_state == ESCALATED,
        "is_blocked_missing_real_materials": followup_state == BLOCKED_MISSING_REAL_MATERIALS,
    }


def _escalation_reason(followup_state: str, reasons: list[str]) -> str:
    # escalation reason 是短类别，避免把 source unsafe 原文写入输出。
    if followup_state == BLOCKED_MISSING_REAL_MATERIALS:
        return _safe_text(";".join(reasons), "blocked_missing_real_materials")
    if followup_state == OVERDUE:
        return "real material follow-up is overdue; support route should escalate without success or control claims"
    if followup_state == ESCALATED:
        return "real material follow-up has been escalated; PR #5 remains unresolved and hardware_material_pending"
    if followup_state == DUE:
        return "real material follow-up is due; owner route must provide next required evidence"
    return "real material follow-up is pending; keep software_proof and wait for real materials"


def _safe_copy(followup_state: str, source: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    # safe_copy 是后续 diagnostics/mobile 建议消费面，字段稳定且全为短字段。
    return {
        **_safe_flags(),
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "capability": CAPABILITY,
        "source_capability": SOURCE_CAPABILITY,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "source_evidence_boundary": source["source_boundary"],
        "safe_evidence_ref": source["safe_evidence_ref"],
        "evidence_ref": source["safe_evidence_ref"],
        "safe_command_id": source["safe_command_id"],
        "command_id": source["safe_command_id"],
        "same_evidence_ref_required": True,
        "unresolved_blocker": "PR #5 reviewer thread PRRT_kwDOSWB9286CJ3tX remains unresolved hardware_material_pending",
        "followup_state": followup_state,
        "allowed_followup_states": list(FOLLOWUP_STATES),
        "due_status": _due_status_flags(followup_state),
        "owner_route": source["owner_route"],
        "reviewer_route": source["reviewer_route"],
        "support_route": source["support_route"],
        "escalation_reason": _escalation_reason(followup_state, reasons),
        "followup_reasons": reasons,
        "next_required_evidence": source["next_required_evidence"] or list(MISSING_REQUIRED_EVIDENCE),
        "pr5_thread": _pr5_thread(),
    }


def _summary_payload(followup_state: str, source: dict[str, Any], reasons: list[str], safe_copy: dict[str, Any]) -> dict[str, Any]:
    # summary 与 artifact 保持同一 followup_state，便于 Robot diagnostics safe alias。
    return {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "summary_only": True,
        "safe_to_render_on_phone": True,
        **_safe_flags(),
        "capability": CAPABILITY,
        "summary_alias": ROBOT_ALIAS,
        "robot_alias_schema": ROBOT_ALIAS_SCHEMA,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "source_capability": SOURCE_CAPABILITY,
        "source_evidence_boundary": source["source_boundary"],
        "source_handoff_status": source["source_handoff_status"] or "missing",
        "source_review_decision": source["source_review_decision"] or "missing",
        "reviewer_ack_state": source["reviewer_ack_state"] or "missing",
        "safe_evidence_ref": source["safe_evidence_ref"],
        "evidence_ref": source["safe_evidence_ref"],
        "safe_command_id": source["safe_command_id"],
        "command_id": source["safe_command_id"],
        "same_evidence_ref_required": True,
        "unresolved_blocker": "PR #5 reviewer thread PRRT_kwDOSWB9286CJ3tX remains unresolved hardware_material_pending",
        "followup_state": followup_state,
        "allowed_followup_states": list(FOLLOWUP_STATES),
        "due_status": _due_status_flags(followup_state),
        "owner_route": source["owner_route"],
        "reviewer_route": source["reviewer_route"],
        "support_route": source["support_route"],
        "escalation_reason": _escalation_reason(followup_state, reasons),
        "followup_reasons": reasons,
        "next_required_evidence": source["next_required_evidence"] or list(MISSING_REQUIRED_EVIDENCE),
        "pr5_thread": _pr5_thread(),
        "safe_copy": safe_copy,
        "not_proven_items": list(NOT_PROVEN_ITEMS),
        "boundary_note": BOUNDARY_NOTE,
        "safety_markers": [
            CAPABILITY,
            EVIDENCE_BOUNDARY,
            "source=software_proof",
            "software_proof",
            "not_proven",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
            NO_OKR_LIFT,
            PR5_THREAD_ID,
            "hardware_material_pending",
            PENDING,
            DUE,
            OVERDUE,
            ESCALATED,
            BLOCKED_MISSING_REAL_MATERIALS,
        ],
    }


def build_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status(
    reviewer_ack_review_handoff_json: str,
    followup_state: str = PENDING,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 reviewer-ACK-review-handoff safe source，生成 fail-closed follow-up status。"""
    source_payload, load_issue = _read_json(reviewer_ack_review_handoff_json)
    source = _source_view(source_payload, load_issue)
    requested_ref = _safe_ref(evidence_ref) or source["safe_evidence_ref"]
    state, reasons, exit_code = _followup_state(source, requested_ref, followup_state)
    if not requested_ref:
        # 缺 safe ref 时仍输出 blocked artifact，但不伪造有效证据号。
        requested_ref = "missing_safe_evidence_ref"
        source["safe_evidence_ref"] = requested_ref
    reasons = list(dict.fromkeys(reasons or [state]))
    safe_copy = _safe_copy(state, source, reasons)
    summary = _summary_payload(state, source, reasons, safe_copy)
    artifact = {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        **_safe_flags(),
        "capability": CAPABILITY,
        "source_capability": SOURCE_CAPABILITY,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "boundary": EVIDENCE_BOUNDARY,
        "source_evidence_boundary": source["source_boundary"],
        "source_handoff_status": source["source_handoff_status"] or "missing",
        "source_review_decision": source["source_review_decision"] or "missing",
        "reviewer_ack_state": source["reviewer_ack_state"] or "missing",
        "safe_evidence_ref": requested_ref,
        "evidence_ref": requested_ref,
        "safe_command_id": source["safe_command_id"],
        "command_id": source["safe_command_id"],
        "same_evidence_ref_required": True,
        "unresolved_blocker": summary["unresolved_blocker"],
        "followup_state": state,
        "allowed_followup_states": list(FOLLOWUP_STATES),
        "due_status": summary["due_status"],
        "owner_route": source["owner_route"],
        "reviewer_route": source["reviewer_route"],
        "support_route": source["support_route"],
        "escalation_reason": summary["escalation_reason"],
        "followup_reasons": reasons,
        "next_required_evidence": summary["next_required_evidence"],
        "pr5_thread": _pr5_thread(),
        "safe_copy": safe_copy,
        f"{CAPABILITY}_summary": summary,
        ROBOT_ALIAS: summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "blocked_claims": list(NOT_PROVEN_ITEMS),
        "safety_markers": summary["safety_markers"],
    }
    return artifact, summary, exit_code


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    # CLI 写入缩进 JSON，便于 sprint artifact diff 与人工 review。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 保持 dependency-free，便于 PC、Docker 和 focused unittest 共用。
    parser = argparse.ArgumentParser(
        description=(
            "Build trashbot.verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status.v1 "
            "from sanitized reviewer ACK review-handoff metadata. Keeps source=software_proof, not_proven, "
            "delivery_success=false, primary_actions_enabled=false, safe_to_control=false, and PR #5 unresolved."
        )
    )
    parser.add_argument("--reviewer-ack-review-handoff-json", "--input", required=True, help="sanitized reviewer ACK review handoff artifact, summary, or Robot alias JSON")
    parser.add_argument("--followup-state", "--due-status", default=PENDING, choices=list(FOLLOWUP_STATES), help="pending, due, overdue, escalated, or blocked_missing_real_materials")
    parser.add_argument("--evidence-ref", default="", help="expected same safe evidence_ref")
    parser.add_argument("--output", type=Path, help="optional follow-up escalation artifact JSON output path")
    parser.add_argument("--summary-output", type=Path, help="optional follow-up escalation summary JSON output path")
    parser.add_argument("--output-dir", type=Path, help="optional directory for canonical artifact and summary filenames")
    parser.add_argument("--once-json", action="store_true", help="print artifact JSON to stdout")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_verified_terminal_result_material_owner_response_reviewer_ack_followup_escalation_status(
        args.reviewer_ack_review_handoff_json,
        args.followup_state,
        args.evidence_ref,
    )
    if args.output_dir:
        _write_json(args.output_dir / f"{CAPABILITY}.json", artifact)
        _write_json(args.output_dir / f"{CAPABILITY}_summary.json", summary)
    if args.output:
        _write_json(args.output, artifact)
    if args.summary_output:
        _write_json(args.summary_output, summary)
    if args.once_json or not (args.output or args.summary_output or args.output_dir):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"{CAPABILITY}: artifact_file:{args.output or args.output_dir / f'{CAPABILITY}.json'}")
        print(f"reviewer_ack_followup_escalation_status_summary_file:{args.summary_output or args.output_dir / f'{CAPABILITY}_summary.json'}")
        print(f"followup_state:{artifact['followup_state']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
