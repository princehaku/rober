#!/usr/bin/env python3
"""生成 verified_terminal_result_material_owner_response_review_handoff 的 PC-only gate。"""

from __future__ import annotations

# 设计约束 01：本 gate 只消费上一轮 owner-response review-decision 的 safe metadata。
# 设计约束 02：handoff 只表达 owner/support/reviewer 人工交接，不证明真实 terminal result。
# 设计约束 03：所有输出固定 source=software_proof、software_proof、not_proven。
# 设计约束 04：所有输出固定 delivery_success=false、primary_actions_enabled=false、safe_to_control=false。
# 设计约束 05：safe evidence_ref 与 command_id 只能是短标识，不能是路径、URL 或凭证。
# 设计约束 06：accepted decision 也只进入 handoff accepted_not_proven，不打开机器人控制。
# 设计约束 07：missing/rejected/unsafe/blocked 仍写脱敏 summary，方便后续人工补证。
# 设计约束 08：PR #5 thread PRRT_kwDOSWB9286CJ3tX 必须保持 unresolved / hardware_material_pending。
# 设计约束 09：拒绝 raw artifact、完整 JSON dump、raw owner body、凭证、URL、DB/queue、OSS。
# 设计约束 10：拒绝 local path、traceback、ROS topic、/cmd_vel、serial/UART、WAVE ROVER。
# 设计约束 11：拒绝 ACK/cursor/replay/resubmit、reviewer-resolution claim、success/control claim。
# 设计约束 12：代码不新增硬件参数或协议假设，所以本文件不引用 vendor 细节。
# 设计约束 13：CLI 不访问网络、GitHub、ROS graph、真实手机、真实硬件或云服务。
# 字段说明 01：artifact_schema 面向 PC evidence bundle，summary_schema 面向 Robot/mobile 只读消费。
# 字段说明 02：robot_alias_schema 只声明安全别名，不表示 Robot diagnostics worker 已接入。
# 字段说明 03：CAPABILITY 用作跨 README、docs、tests 和 CLI 输出的稳定检索词。
# 字段说明 04：SOURCE_CAPABILITY 锁定上一轮 review decision，避免跳过人工 review 阶段。
# 字段说明 05：SOURCE 固定 software_proof，避免把 Docker/local proof 误升格为真实现场 proof。
# 字段说明 06：STATUS 固定 not_proven，所有 accepted 语义都不能覆盖它。
# 字段说明 07：EVIDENCE_BOUNDARY 是本 gate 唯一新增边界，供 rg 围栏和下游面板识别。
# 字段说明 08：SOURCE_BOUNDARY 必须来自上一轮 decision gate，缺失时视为 source 不可消费。
# 字段说明 09：ROBOT_ALIAS 只服务后续 Robot worker 安全导出，不在本文件注册 ROS 接口。
# 字段说明 10：NO_OKR_LIFT 明确阻止本地 metadata rung 被计入 OKR 百分比提升。
# 字段说明 11：PR5_THREAD_ID 固定记录 unresolved thread，不能由本地 gate 改为 resolved。
# 状态说明 01：ACCEPTED_STATUS 表示 handoff packet ready，不表示 delivery success。
# 状态说明 02：MISSING_STATUS 表示需要补交 safe handoff/material 类别。
# 状态说明 03：REJECTED_STATUS 表示上一轮 decision 已拒绝材料，后续必须替换材料。
# 状态说明 04：UNSAFE_STATUS 表示输入含 raw、凭证、控制、硬件或成功 claim。
# 状态说明 05：BLOCKED_SOURCE_STATUS 表示 source 缺失、坏 JSON、unsupported 或边界错误。
# 状态说明 06：BLOCKED_REF_STATUS 优先级高，因为 evidence_ref 混用会污染后续材料链。
# 状态说明 07：HANDOFF_STATUSES 显式列出允许枚举，便于 docs 和 tests 防漂移。
# 状态说明 08：SOURCE_ACCEPTED_STATUS 来自上一轮 decision，不是本轮新证明。
# 状态说明 09：SOURCE_MISSING_STATUS 继承为 missing handoff，保留补证路径。
# 状态说明 10：SOURCE_REJECTED_STATUS 继承为 rejected handoff，保留拒绝原因。
# 状态说明 11：SOURCE_UNSAFE_STATUS 继承为 unsafe handoff，避免清洗后误放行。
# 状态说明 12：SOURCE_BLOCKED_REF_STATUS 继续阻断，不允许 handoff 重新选择 ref。
# 输入说明 01：SUPPORTED_SOURCE_SCHEMAS 只列 safe artifact、summary 和 Robot alias。
# 输入说明 02：TERMINAL_RESULT_TYPES 限定 delivery/dropoff/cancel 三种产品结果类型。
# 输入说明 03：WRAPPER_KEYS 只展开已知 safe wrapper，避免任意 raw payload 被递归信任。
# 输入说明 04：safe_copy 可以被消费，但它仍要经过相同 source/boundary/flag 校验。
# 输入说明 05：robot_diagnostics_summary 和 mobile_readonly_summary 是兼容读取面，不是新 proof。
# 安全说明 01：SAFE_REF_RE 只允许短标识，防止路径、URL 或 blob 被伪装为 evidence_ref。
# 安全说明 02：PATH_LIKE_RE 同时拦截 Unix、Windows、file URL 和常见本地工作目录。
# 安全说明 03：URL_OR_QUEUE_RE 拦截外部 URL、DB、queue、OSS/S3 proof claim。
# 安全说明 04：FORBIDDEN_KEY_TERMS 以字段名拦截 raw/control/credential 等高风险类别。
# 安全说明 05：UNSAFE_TEXT_PATTERNS 以文本拦截字符串里的 true flags 和成功 claim。
# 安全说明 06：凭证类 pattern 不回显命中内容，只输出类别原因，避免二次泄漏。
# 安全说明 07：ROS/control pattern 拦截 /cmd_vel、topic、ROS graph 和 rclpy 语义。
# 安全说明 08：硬件 pattern 拦截 WAVE ROVER、UART、baudrate 等硬件 proof 漂移。
# 安全说明 09：ACK/cursor/replay pattern 防止 handoff 包被误用成云命令重放入口。
# 安全说明 10：PR resolved pattern 防止本地材料包伪造 GitHub reviewer closure。
# 输出说明 01：REQUIRED_HANDOFF_MATERIALS 是缺省补证类别，不是现场 proof 清单。
# 输出说明 02：NOT_PROVEN_ITEMS 明确列出仍未证明的真实能力，供 Product closeout 引用。
# 输出说明 03：BLOCKED_CLAIMS 明确列出本 gate 拒绝的高风险 claim 类别。
# 输出说明 04：BOUNDARY_NOTE 把 rg 需要的关键短语写入 artifact，便于证据围栏。
# 输出说明 05：_safe_flags 在 artifact、summary、safe_copy 和 handoff packet 中重复出现。
# 输出说明 06：重复 false flags 是有意设计，避免下游只读取局部 JSON 时误启用动作。
# 输出说明 07：owner_handoff、support_handoff、reviewer_handoff 内容相同但 route 字段显式。
# 输出说明 08：相同 packet 结构让 Robot/mobile worker 可按角色字段选择展示。
# 输出说明 09：safe_copy_text 是复制给人工/手机 UI 的短文，不包含 raw source。
# 输出说明 10：source_owner_response_review_decision_detail 只含诊断类别，不嵌入 source 原文。
# 流程说明 01：_load_json 失败不抛 traceback，改写为 blocked artifact 方便 sprint 留档。
# 流程说明 02：_find_source 优先 schema/capability，避免 wrapper 顶层噪声影响 source。
# 流程说明 03：_ref_state 要求所有显式 evidence_ref 一致，防止跨材料拼接。
# 流程说明 04：_source_contract_reasons 先做结构合同，再进入业务状态映射。
# 流程说明 05：_classify_handoff 的 priority 固定，ref mismatch 早于 unsafe 和 missing。
# 流程说明 06：_next_required 只写人工补证步骤，不写 ACK、fetch、resolve 或 robot command。
# 流程说明 07：_blocked_reason 只输出原因 token，不回显用户原始输入。
# 流程说明 08：_pr5_thread 是保守事实快照，不做 GitHub API mutation。
# 流程说明 09：_handoff_packet 是三方交接对象，不是 transport envelope。
# 流程说明 10：build 函数返回 exit_code，0 只代表 gate accepted，不代表交付成功。
# CLI 说明 01：--input 和 --source 互斥，避免同一轮混入两个不同 source。
# CLI 说明 02：--evidence-ref 是可选围栏，提供后必须与 source 完全一致。
# CLI 说明 03：--output-dir 只写本地 JSON，不创建 sprint 文档或外部证据。
# CLI 说明 04：--once-json 便于测试和一次性管道消费，不改变 safety flags。
# CLI 说明 05：CLI help 明确列出 source=software_proof 和三类 false flag，供验收命令检索。
# 兼容说明 01：本 gate 允许 artifact 与 summary 两种 schema，便于 PC 工具链连续运行。
# 兼容说明 02：本 gate 允许 Robot alias，是为了并行 Robot worker 后续接入同一安全面。
# 兼容说明 03：本 gate 不要求 source 带完整 material_status_summary，避免复制 raw 材料。
# 兼容说明 04：本 gate 保留 accepted/missing/rejected/unsafe list，只保留类别短名。
# 兼容说明 05：本 gate 不解析字符串化 JSON，因为那通常意味着 raw payload 泄漏风险。
# 兼容说明 06：本 gate 对 nested wrapper 深度有限制在白名单 key，避免无界递归风险。
# 兼容说明 07：本 gate 对坏 JSON 仍生成 blocked 分类，便于上层自动化写 sprint evidence。
# 兼容说明 08：本 gate 对缺 source 和 unsupported schema 使用同一 blocked family。
# 兼容说明 09：本 gate 对 wrong boundary 单独保留 reason，方便定位上一轮 artifact 错误。
# 兼容说明 10：本 gate 对 unsafe source 输出 unsafe family，方便 owner 重新脱敏提交。
# 审计说明 01：artifact 和 summary 都包含 generated_at，方便多轮 PC 输出排序。
# 审计说明 02：artifact 和 summary 都包含 source_schema，方便确认上游输入版本。
# 审计说明 03：artifact 和 summary 都包含 source_evidence_boundary，方便 proof boundary 审计。
# 审计说明 04：artifact 和 summary 都包含 blocked_claims，方便 reviewer 快速看拒绝范围。
# 审计说明 05：artifact 和 summary 都包含 not_proven_items，方便 Product closeout 保守记录。
# 审计说明 06：artifact 包含 source detail，但只包含类别，不包含 source 原文。
# 审计说明 07：summary_only=true 明确下游 UI 可以渲染，但不能反向当 raw source。
# 审计说明 08：safe_to_render_on_phone=true 只表示脱敏可展示，不表示真实 phone proof。
# 审计说明 09：summary_alias 与 robot_alias_schema 同时输出，避免跨 worker 命名歧义。
# 审计说明 10：safety_markers 是 rg 围栏的稳定目标，不参与业务决策。
# 风险说明 01：本 gate 不更新 OKR.md，所以 OKR lift 必须由 Product closeout 单独判断。
# 风险说明 02：本 gate 不提交 GitHub comment，所以 PR #5 unresolved 状态只能保守记录。
# 风险说明 03：本 gate 不读取硬件 vendor 文件，因为它不新增任何硬件参数或假设。
# 风险说明 04：本 gate 不运行 ROS2，因此不能证明 action/topic/service 联通。
# 风险说明 05：本 gate 不运行 browser，因此不能证明真实 mobile/web UI 已消费 summary。
# 风险说明 06：本 gate 不访问 public cloud，因此不能证明 HTTPS/TLS、4G、OSS/CDN 或 DB/queue。
# 风险说明 07：本 gate 不执行 route/elevator，因此不能证明 field pass 或 delivery success。
# 风险说明 08：本 gate 不读取 serial/UART，因此不能证明 WAVE ROVER 或 HIL。
# 风险说明 09：本 gate accepted 输出仍需要 Robot/mobile workers 分别接入只读展示。
# 风险说明 10：本 gate blocked 输出用于定位材料链问题，不应触发自动控制恢复。
# 维护说明 01：新增状态时必须同步 HANDOFF_STATUSES、docs、README 和 focused tests。
# 维护说明 02：新增 source schema 时必须确认仍是上一轮 safe metadata，而不是 raw artifact。
# 维护说明 03：新增 wrapper key 时必须确认它不会携带完整 raw payload。
# 维护说明 04：新增 forbidden key 时应保持原因类别稳定，避免破坏下游文案。
# 维护说明 05：新增 unsafe pattern 时不要把命中文本写入输出，避免敏感信息回显。
# 维护说明 06：调整 exit code 时必须同步 CLI tests，避免自动化误判 accepted。
# 维护说明 07：调整 safe_copy_text 时必须保留 boundary、false flags 和 PR #5 pending 文案。
# 维护说明 08：调整 route 字段时必须同时保留 field_owner、support_owner、reviewer_route。
# 维护说明 09：调整 evidence_ref 校验时必须保持 mismatch 优先级最高。
# 维护说明 10：调整 output filenames 时必须同步 README、interface doc 和验收命令。
# 验收说明 01：py_compile 只证明 Python 语法可加载，不证明真实联调。
# 验收说明 02：focused unittest 只证明 PC gate 分类和净化，不证明 Robot/mobile 消费。
# 验收说明 03：rg 围栏只证明关键短语存在，不证明外部 proof 已获得。
# 验收说明 04：git diff --check 只证明 touched files 没有 whitespace 错误。
# 验收说明 05：以上验收都必须继续保持 software_proof_docker_only 边界。

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ARTIFACT_SCHEMA = "trashbot.verified_terminal_result_material_owner_response_review_handoff.v1"
SUMMARY_SCHEMA = "trashbot.verified_terminal_result_material_owner_response_review_handoff_summary.v1"
ROBOT_ALIAS_SCHEMA = "trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary.v1"
SCHEMA_VERSION = 1
CAPABILITY = "verified_terminal_result_material_owner_response_review_handoff"
SOURCE_CAPABILITY = "verified_terminal_result_material_owner_response_review_decision"
SOURCE = "software_proof"
STATUS = "not_proven"
EVIDENCE_BOUNDARY = "software_proof_docker_verified_terminal_result_material_owner_response_review_handoff_gate"
SOURCE_BOUNDARY = "software_proof_docker_verified_terminal_result_material_owner_response_review_decision_gate"
ROBOT_ALIAS = "robot_diagnostics_verified_terminal_result_material_owner_response_review_handoff_summary"
NO_OKR_LIFT = "no OKR percentage lift"
PR5_THREAD_ID = "PRRT_kwDOSWB9286CJ3tX"

ACCEPTED_STATUS = "accepted_terminal_result_material_owner_response_review_handoff_not_proven"
MISSING_STATUS = "missing_terminal_result_material_owner_response_review_handoff_not_proven"
REJECTED_STATUS = "rejected_terminal_result_material_owner_response_review_handoff_not_proven"
UNSAFE_STATUS = "unsafe_terminal_result_material_owner_response_review_handoff_not_proven"
BLOCKED_SOURCE_STATUS = "blocked_missing_terminal_result_owner_response_review_decision_not_proven"
BLOCKED_REF_STATUS = "blocked_evidence_ref_mismatch_not_proven"
HANDOFF_STATUSES = (
    ACCEPTED_STATUS,
    MISSING_STATUS,
    REJECTED_STATUS,
    UNSAFE_STATUS,
    BLOCKED_SOURCE_STATUS,
    BLOCKED_REF_STATUS,
)

SOURCE_ACCEPTED_STATUS = "accepted_terminal_result_material_owner_response_review_decision_not_proven"
SOURCE_MISSING_STATUS = "missing_terminal_result_material_owner_response_review_decision_not_proven"
SOURCE_REJECTED_STATUS = "rejected_terminal_result_material_owner_response_review_decision_not_proven"
SOURCE_UNSAFE_STATUS = "unsafe_terminal_result_material_owner_response_review_decision_not_proven"
SOURCE_BLOCKED_REF_STATUS = "blocked_evidence_ref_mismatch_not_proven"

SUPPORTED_SOURCE_SCHEMAS = {
    "trashbot.verified_terminal_result_material_owner_response_review_decision.v1",
    "trashbot.verified_terminal_result_material_owner_response_review_decision_summary.v1",
    "robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary",
    "trashbot.robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary.v1",
}
TERMINAL_RESULT_TYPES = ("delivery", "dropoff", "cancel")

WRAPPER_KEYS = (
    "verified_terminal_result_material_owner_response_review_handoff",
    "verified_terminal_result_material_owner_response_review_handoff_summary",
    "verified_terminal_result_material_owner_response_review_decision",
    "verified_terminal_result_material_owner_response_review_decision_summary",
    "robot_diagnostics_verified_terminal_result_material_owner_response_review_decision_summary",
    "robot_diagnostics_summary",
    "mobile_readonly_summary",
    "safe_copy",
    "summary",
    "artifact",
    "data",
    "payload",
    "diagnostics",
    "latest_status",
)

SAFE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,120}$")
PATH_LIKE_RE = re.compile(r"(^/|[A-Za-z]:\\|\\\\|file://|\b\.\.?/|/dev/|/Users/|/tmp/|/var/|/home/|/ws/)")
URL_OR_QUEUE_RE = re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb|oss|s3)://|https?://")
FORBIDDEN_KEY_TERMS = (
    "raw",
    "raw_artifact",
    "raw_artifacts",
    "raw_body",
    "raw_payload",
    "complete_json",
    "artifact_path",
    "local_path",
    "file_path",
    "log_path",
    "traceback",
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
    "ros_topic",
    "ros_service",
    "cmd_vel",
    "control_command",
    "serial_device",
    "uart",
    "wave_rover",
    "cursor",
    "replay",
    "resubmit",
    "reviewer_resolution",
    "review_thread_resolved",
    "github_thread_resolved",
)
UNSAFE_TEXT_PATTERNS = (
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bsafe_to_control\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bnot_proven\s*[:=]\s*false\b"),
    re.compile(r"(?i)\b(raw\s+artifact|complete\s+json|raw\s+owner|raw\s+terminal|traceback)\b"),
    re.compile(r"(?i)\b(delivery|dropoff|cancel|terminal result|route|elevator|nav2)\s+(success|succeeded|completed|complete|verified|passed)\b"),
    re.compile(r"(?i)\b(success|control|dispatch|start|confirm|cancel)\s+(claim|command|action)\b"),
    re.compile(r"(?i)\b(Bearer\s+|Authorization\s*:|password|private_key|OSS_ACCESS_KEY_SECRET)\b"),
    re.compile(r"(?i)\b(token|secret|access[_-]?key|api[_-]?key|password)\b\s*[:=]"),
    re.compile(r"(?i)\b(postgres|postgresql|mysql|redis|amqp|mongodb)://"),
    re.compile(r"(?i)\b(signed_url|oss://|s3://|https://[^\s]*token=)\b"),
    re.compile(r"(?i)\b(ros2\s+topic|/cmd_vel|/odom|/tf|/trashbot/|ros graph|rclpy)\b"),
    re.compile(r"(?i)\b(WAVE ROVER|ESP32|Orange Pi|UART|serial device|baudrate|GPIO|voltage|firmware)\b"),
    re.compile(r"(?i)\b(ack|cursor|replay|resubmit)\b.*\b(command|mutation|hint|retry|lookup)\b"),
    re.compile(r"(?i)\b(PRRT_[A-Za-z0-9]+.*resolved|reviewer.*resolved|github.*resolved|PR\s*#?5.*resolved)\b"),
)

REQUIRED_HANDOFF_MATERIALS = (
    "same_safe_evidence_ref_confirmation",
    "source_owner_response_review_decision_summary",
    "owner_handoff_route",
    "support_handoff_route",
    "reviewer_handoff_route",
    "pr5_hardware_material_pending_confirmation",
)
NOT_PROVEN_ITEMS = (
    "real_terminal_delivery_result",
    "real_terminal_dropoff_result",
    "real_terminal_cancel_result",
    "real_nav2_fixed_route_run",
    "real_elevator_field_pass",
    "true_phone_browser_or_device",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
    "pr5_reviewer_resolution",
)
BLOCKED_CLAIMS = (
    "raw_artifacts",
    "complete_json_dump",
    "raw_owner_response_body",
    "raw_terminal_material",
    "credentials",
    "urls",
    "db_queue_oss",
    "local_paths",
    "traceback",
    "ros_topics_or_cmd_vel",
    "serial_uart_wave_rover",
    "ack_cursor_replay_resubmit",
    "reviewer_resolution_claim",
    "success_or_control_claim",
)
BOUNDARY_NOTE = (
    "verified_terminal_result_material_owner_response_review_handoff; "
    "software_proof_docker_verified_terminal_result_material_owner_response_review_handoff_gate; "
    "verified_terminal_result_material_owner_response_review_decision; "
    "software_proof_docker_verified_terminal_result_material_owner_response_review_decision_gate; "
    "source=software_proof; software_proof; not_proven; delivery_success=false; "
    "primary_actions_enabled=false; safe_to_control=false; "
    "PRRT_kwDOSWB9286CJ3tX unresolved hardware_material_pending; no OKR percentage lift"
)


def _utc_now() -> str:
    # UTC 时间让 Docker-only artifact 在 PC、本地容器和未来 CI 中可稳定排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_flags() -> dict[str, Any]:
    # 下游可能只消费 summary，所以所有安全旗标在 artifact/summary/safe_copy 重复输出。
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
    # 任意自由文本都压成短单行，避免 raw body 或多行日志穿透输出。
    if value is None:
        text = default
    elif isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    text = text.replace("\n", " ").replace("\r", " ")
    return text[:240] or default


def _encoded(value: Any) -> str:
    # 递归安全扫描需要稳定 JSON；不可序列化对象降级为短文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _safe_ref(value: Any) -> str:
    # evidence_ref/command_id 只能是短安全标识，路径、URL、弱字符串都拒绝。
    text = _safe_text(value)
    if text and SAFE_REF_RE.fullmatch(text) and not PATH_LIKE_RE.search(text) and not URL_OR_QUEUE_RE.search(text):
        return text
    return ""


def _dict(value: Any) -> dict[str, Any]:
    # wrapper 只接受 object，不把字符串化 JSON 自动展开为可信输入。
    return value if isinstance(value, dict) else {}


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都转成可审计分类，而不是抛 traceback。
    if not path:
        return {}, "owner_response_review_decision_json_not_provided"
    try:
        payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, "owner_response_review_decision_json_missing"
    except json.JSONDecodeError:
        return {}, "owner_response_review_decision_json_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "owner_response_review_decision_json_read_error"
    if not isinstance(payload, dict):
        return {}, "owner_response_review_decision_json_not_object"
    return payload, ""


def _candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # 只递归白名单 safe wrapper key，防止任意 raw payload 被误采信。
    candidates = [payload]
    for key in WRAPPER_KEYS:
        child = _dict(payload.get(key))
        if child:
            candidates.extend(_candidates(child))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # source 必须命中上一轮 owner response review decision schema/capability，避免跳链消费。
    for candidate in _candidates(payload):
        schema = _safe_text(candidate.get("schema"))
        capability = _safe_text(candidate.get("capability"))
        if schema in SUPPORTED_SOURCE_SCHEMAS or capability == SOURCE_CAPABILITY:
            return candidate
    return payload


def _unsafe_key_paths(value: Any, prefix: str = "") -> list[str]:
    # 字段名命中 raw/control/credential/ACK/reviewer-resolution 类别即拒绝。
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


def _true_flag_reasons(value: Any) -> list[str]:
    # true 控制旗标可能藏在嵌套 dict 或字符串 note 中，必须全局拒绝。
    reasons: list[str] = []
    if isinstance(value, dict):
        for key in ("delivery_success", "primary_actions_enabled", "safe_to_control", "control_enabled", "hil_pass", "field_pass"):
            if value.get(key) is True:
                reasons.append(f"{key}_true_overclaim")
        for child in value.values():
            reasons.extend(_true_flag_reasons(child))
    elif isinstance(value, list):
        for child in value:
            reasons.extend(_true_flag_reasons(child))
    elif isinstance(value, str):
        for key in ("delivery_success", "primary_actions_enabled", "safe_to_control"):
            if re.search(rf"(?i)\b{re.escape(key)}\s*[:=]\s*true\b", value):
                reasons.append(f"{key}_true_overclaim")
    return list(dict.fromkeys(reasons))


def _unsafe_reasons(value: Any) -> list[str]:
    # 只输出类别原因，不回显命中的敏感片段。
    if value in ({}, None, ""):
        return []
    reasons: list[str] = []
    encoded = _encoded(value)
    if _unsafe_key_paths(value):
        reasons.append("forbidden_raw_owner_response_control_credential_path_ack_replay_or_resolution_fields")
    if PATH_LIKE_RE.search(encoded) or URL_OR_QUEUE_RE.search(encoded):
        reasons.append("unsafe_path_url_db_queue_oss_or_local_path")
    if any(pattern.search(encoded) for pattern in UNSAFE_TEXT_PATTERNS):
        reasons.append("unsafe_raw_terminal_material_credential_ros_control_hardware_ack_replay_resolution_or_success_claim")
    reasons.extend(_true_flag_reasons(value))
    return list(dict.fromkeys(reasons))


def _surface_is_safe(payload: dict[str, Any]) -> bool:
    # source 的最低消费边界：software_proof + not_proven + 三个 false flags。
    encoded = _encoded(payload)
    return (
        _safe_text(payload.get("source")) == SOURCE
        and "not_proven" in encoded
        and payload.get("delivery_success") is False
        and payload.get("primary_actions_enabled") is False
        and payload.get("safe_to_control") is False
    )


def _collect_refs(value: Any) -> list[str]:
    # 只收集明确 ref 字段，用于 same safe evidence_ref 一致性检查。
    refs: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key) in {"safe_evidence_ref", "evidence_ref"}:
                refs.append(_safe_ref(child) or "__unsafe_ref__")
            refs.extend(_collect_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.extend(_collect_refs(child))
    return refs


def _ref_state(payload: dict[str, Any]) -> tuple[str, list[str]]:
    # 多个 ref 必须一致，避免把不同现场材料拼成一个 handoff。
    refs = list(dict.fromkeys(_collect_refs(payload)))
    reasons: list[str] = []
    if "__unsafe_ref__" in refs:
        reasons.append("unsafe_evidence_ref")
    clean = [ref for ref in refs if ref != "__unsafe_ref__"]
    if len(clean) > 1:
        reasons.append("evidence_ref_mismatch")
    if not clean:
        reasons.append("missing_safe_evidence_ref")
    return (clean[0] if clean and not reasons else ""), list(dict.fromkeys(reasons))


def _safe_list(value: Any, limit: int = 80) -> list[str]:
    # 列表字段只输出类别名/短摘要，不复制 raw item。
    if value in (None, ""):
        return []
    items = value if isinstance(value, list) else [value]
    result: list[str] = []
    for item in list(items)[:limit]:
        if isinstance(item, dict):
            text = _safe_text(item.get("name") or item.get("material") or item.get("category") or item.get("summary"))
        else:
            text = _safe_text(item)
        if text and not PATH_LIKE_RE.search(text) and not URL_OR_QUEUE_RE.search(text):
            result.append(text)
    return list(dict.fromkeys(result))


def _source_view(payload: dict[str, Any], read_issue: str) -> dict[str, Any]:
    # normalized source 是唯一参与 source 合同判断的数据面。
    source = _find_source(payload) if payload else {}
    safe_copy = _dict(source.get("safe_copy"))
    ref, ref_errors = _ref_state(source) if source else ("", ["missing_safe_evidence_ref"])
    decision = _safe_text(
        source.get("review_decision")
        or source.get("verified_terminal_result_material_owner_response_review_decision")
        or safe_copy.get("review_decision")
    )
    return {
        "read_issue": read_issue,
        "schema": _safe_text(source.get("schema")),
        "capability": _safe_text(source.get("capability")),
        "source_schema": _safe_text(source.get("schema")),
        "evidence_boundary": _safe_text(source.get("evidence_boundary") or source.get("boundary") or safe_copy.get("evidence_boundary")),
        "source_review_decision": decision,
        "safe_evidence_ref": ref,
        "ref_errors": ref_errors,
        "same_evidence_ref_required": source.get("same_evidence_ref_required", safe_copy.get("same_evidence_ref_required", True)),
        "safe_command_id": _safe_ref(source.get("safe_command_id") or source.get("command_id") or safe_copy.get("safe_command_id")),
        "terminal_result_type": _safe_text(source.get("terminal_result_type") or safe_copy.get("terminal_result_type")),
        "field_owner": _safe_text(source.get("field_owner") or safe_copy.get("field_owner"), "field_terminal_result_material_owner"),
        "support_owner": _safe_text(source.get("support_owner") or safe_copy.get("support_owner"), "support_terminal_result_material_owner"),
        "reviewer_route": _safe_text(source.get("reviewer_route") or safe_copy.get("reviewer_route"), "terminal_result_material_reviewer"),
        "accepted_materials": _safe_list(source.get("accepted_materials") or safe_copy.get("accepted_materials")),
        "missing_materials": _safe_list(source.get("missing_materials") or safe_copy.get("missing_materials")),
        "rejected_materials": _safe_list(source.get("rejected_materials") or safe_copy.get("rejected_materials")),
        "unsafe_materials": _safe_list(source.get("unsafe_materials") or safe_copy.get("unsafe_materials")),
        "decision_reasons": _safe_list(source.get("decision_reasons") or source.get("handoff_reasons") or source.get("reasons")),
        "next_required_evidence": _safe_list(source.get("next_required_evidence") or safe_copy.get("next_required_evidence")),
        "source_is_safe": _surface_is_safe(source) if source else False,
        "unsafe_reasons": _unsafe_reasons(source),
    }


def _source_contract_reasons(source: dict[str, Any], requested_ref: str) -> list[str]:
    # source 合同错误说明 decision 本身不可消费，应输出 blocked 或 unsafe。
    reasons: list[str] = []
    schema_ok = source["schema"] in SUPPORTED_SOURCE_SCHEMAS or source["capability"] == SOURCE_CAPABILITY
    if source["read_issue"]:
        reasons.append(source["read_issue"])
    if not schema_ok:
        reasons.append("unsupported_terminal_result_owner_response_review_decision_schema")
    if source["evidence_boundary"] != SOURCE_BOUNDARY:
        reasons.append("missing_or_wrong_terminal_result_owner_response_review_decision_boundary")
    if not source["source_is_safe"]:
        reasons.append("source_not_software_proof_not_proven_or_false_flags_changed")
    if source["terminal_result_type"] not in TERMINAL_RESULT_TYPES:
        reasons.append("unsupported_terminal_result_type")
    if source["ref_errors"] or not source["safe_evidence_ref"] or source["same_evidence_ref_required"] is not True:
        reasons.extend(source["ref_errors"] or ["missing_or_weak_same_evidence_ref"])
    if requested_ref and source["safe_evidence_ref"] and requested_ref != source["safe_evidence_ref"]:
        reasons.append("evidence_ref_mismatch")
    return list(dict.fromkeys(reasons))


def _classify_handoff(source: dict[str, Any], requested_ref: str) -> tuple[str, list[str], int]:
    # 决策优先级：缺 source/unsupported -> blocked；ref mismatch -> blocked_ref；
    # unsafe -> unsafe；rejected/missing 继承为 handoff 状态；accepted 才生成 accepted handoff。
    contract_reasons = _source_contract_reasons(source, requested_ref)
    if "evidence_ref_mismatch" in contract_reasons or source["source_review_decision"] == SOURCE_BLOCKED_REF_STATUS:
        return BLOCKED_REF_STATUS, contract_reasons or ["owner_response_review_decision_evidence_ref_mismatch"], 4
    if source["read_issue"] or "unsupported_terminal_result_owner_response_review_decision_schema" in contract_reasons:
        return BLOCKED_SOURCE_STATUS, contract_reasons, 2
    if "missing_or_wrong_terminal_result_owner_response_review_decision_boundary" in contract_reasons:
        return BLOCKED_SOURCE_STATUS, contract_reasons, 2
    if source["unsafe_reasons"]:
        return UNSAFE_STATUS, source["unsafe_reasons"], 5
    if contract_reasons:
        return UNSAFE_STATUS, contract_reasons, 5
    if source["unsafe_materials"] or source["source_review_decision"] == SOURCE_UNSAFE_STATUS:
        return UNSAFE_STATUS, source["decision_reasons"] or ["owner_response_review_decision_unsafe_not_proven"], 5
    if source["rejected_materials"] or source["source_review_decision"] == SOURCE_REJECTED_STATUS:
        return REJECTED_STATUS, source["decision_reasons"] or ["owner_response_review_decision_rejected_not_proven"], 6
    if source["missing_materials"] or source["source_review_decision"] == SOURCE_MISSING_STATUS:
        return MISSING_STATUS, source["decision_reasons"] or ["owner_response_review_decision_missing_not_proven"], 3
    if source["source_review_decision"] == SOURCE_ACCEPTED_STATUS:
        return ACCEPTED_STATUS, ["owner_response_review_decision_accepted_for_handoff_only"], 0
    return MISSING_STATUS, ["owner_response_review_decision_not_ready_for_handoff"], 3


def _next_required(handoff_status: str, evidence_ref: str, source: dict[str, Any], reasons: list[str]) -> list[str]:
    # next_required_evidence 是人工补证说明，不是 ACK、cursor、replay 或 Robot 指令。
    ref = evidence_ref or "<same_evidence_ref>"
    if handoff_status == ACCEPTED_STATUS:
        return [
            f"route accepted owner response review handoff for evidence_ref={ref} to field owner, support owner, and reviewer without enabling controls",
            "keep PR #5 PRRT_kwDOSWB9286CJ3tX unresolved / hardware_material_pending until reviewer live-resolves it outside this gate",
            "preserve source=software_proof, not_proven, delivery_success=false, primary_actions_enabled=false, safe_to_control=false",
        ]
    if handoff_status == MISSING_STATUS:
        missing = source["missing_materials"] or source["next_required_evidence"] or list(REQUIRED_HANDOFF_MATERIALS)
        return [f"backfill owner response review handoff material category: {name} for evidence_ref={ref}" for name in missing]
    if handoff_status == REJECTED_STATUS:
        rejected = source["rejected_materials"] or ["owner_response_review_decision_rejected_not_proven"]
        return [f"replace rejected owner response review decision material category: {name} for evidence_ref={ref}" for name in rejected]
    if handoff_status == UNSAFE_STATUS:
        return [f"rerun owner response review decision with sanitized metadata only for evidence_ref={ref}", *reasons]
    return [f"provide supported verified_terminal_result_material_owner_response_review_decision safe artifact or summary for evidence_ref={ref}", *reasons]


def _blocked_reason(handoff_status: str, reasons: list[str]) -> str:
    # blocked_reason 只输出短类别，避免把原始 owner response 泄漏到 summary。
    if handoff_status == ACCEPTED_STATUS:
        return ""
    return _safe_text(";".join(list(dict.fromkeys(reasons))), "blocked")


def _pr5_thread() -> dict[str, str]:
    # PR #5 状态固定保守表达，除非真实 reviewer evidence 更新。
    return {
        "thread_id": PR5_THREAD_ID,
        "state": "unresolved",
        "material_state": "hardware_material_pending",
        "comment_status": "software_proof_metadata_only_not_reviewer_resolution",
    }


def _handoff_packet(handoff_status: str, source: dict[str, Any], evidence_ref: str, reasons: list[str]) -> dict[str, Any]:
    # handoff_packet 是人工路由包，不触发 GitHub resolve、ACK、fetch 或机器人 command。
    return {
        **_safe_flags(),
        "owner_route": source["field_owner"],
        "support_route": source["support_owner"],
        "reviewer_route": source["reviewer_route"],
        "handoff_status": handoff_status,
        "handoff_reasons": reasons,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "safe_command_id": source["safe_command_id"],
        "command_id": source["safe_command_id"],
        "terminal_result_type": source["terminal_result_type"],
        "pr5_thread": _pr5_thread(),
        "not_delivery_result": True,
        "not_delivery_success": True,
        "not_dropoff_completion": True,
        "not_cancel_completion": True,
        "not_reviewer_resolution": True,
    }


def _safe_copy(handoff_status: str, source: dict[str, Any], evidence_ref: str, reasons: list[str], next_required: list[str]) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile/review 后续只读消费面，不包含 raw source 或 raw response。
    return {
        **_safe_flags(),
        "schema": f"{SUMMARY_SCHEMA}.safe_copy",
        "capability": CAPABILITY,
        "source_schema": source["source_schema"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "safe_command_id": source["safe_command_id"],
        "command_id": source["safe_command_id"],
        "terminal_result_type": source["terminal_result_type"],
        "source_review_decision": source["source_review_decision"],
        "handoff_status": handoff_status,
        "handoff_reasons": reasons,
        "owner_route": source["field_owner"],
        "support_route": source["support_owner"],
        "reviewer_route": source["reviewer_route"],
        "next_required_evidence": next_required,
        "pr5_thread": _pr5_thread(),
        "safe_copy_text": (
            f"{CAPABILITY}: handoff_status={handoff_status}; evidence_ref={evidence_ref}; "
            f"command_id={source['safe_command_id'] or 'none'}; terminal_result_type={source['terminal_result_type']}; "
            f"source_review_decision={source['source_review_decision']}; owner_route={source['field_owner']}; "
            f"support_route={source['support_owner']}; reviewer_route={source['reviewer_route']}; "
            f"evidence_boundary={EVIDENCE_BOUNDARY}; source=software_proof; software_proof; not_proven; "
            "delivery_success=false; primary_actions_enabled=false; safe_to_control=false; "
            "PRRT_kwDOSWB9286CJ3tX unresolved hardware_material_pending; no OKR percentage lift."
        ),
    }


def build_verified_terminal_result_material_owner_response_review_handoff(
    owner_response_review_decision_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 owner-response-review-decision safe source，生成 fail-closed handoff。"""
    source_payload, source_issue = _load_json(owner_response_review_decision_json)
    source = _source_view(source_payload, source_issue)
    requested_ref = _safe_ref(evidence_ref) if evidence_ref else source["safe_evidence_ref"]
    if not requested_ref:
        requested_ref = "missing_safe_evidence_ref"
    handoff_status, reasons, exit_code = _classify_handoff(source, requested_ref)
    generated_at = _utc_now()
    reasons = list(dict.fromkeys(reasons or [handoff_status]))
    next_required = _next_required(handoff_status, requested_ref, source, reasons)
    handoff_packet = _handoff_packet(handoff_status, source, requested_ref, reasons)
    safe_copy = _safe_copy(handoff_status, source, requested_ref, reasons, next_required)
    common = {
        **_safe_flags(),
        "capability": CAPABILITY,
        "source_capability": SOURCE_CAPABILITY,
        "source_schema": source["source_schema"],
        "source_evidence_boundary": source["evidence_boundary"],
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "allowed_handoff_statuses": list(HANDOFF_STATUSES),
        "handoff_status": handoff_status,
        "source_review_decision": source["source_review_decision"],
        "safe_evidence_ref": requested_ref,
        "evidence_ref": requested_ref,
        "same_evidence_ref_required": True,
        "safe_command_id": source["safe_command_id"],
        "command_id": source["safe_command_id"],
        "terminal_result_type": source["terminal_result_type"],
        "field_owner": source["field_owner"],
        "support_owner": source["support_owner"],
        "reviewer_route": source["reviewer_route"],
        "accepted_materials": source["accepted_materials"],
        "missing_materials": source["missing_materials"],
        "rejected_materials": source["rejected_materials"],
        "unsafe_materials": source["unsafe_materials"],
        "required_handoff_materials": list(REQUIRED_HANDOFF_MATERIALS),
        "blocked_reason": _blocked_reason(handoff_status, reasons),
        "handoff_reasons": reasons,
        "next_required_evidence": next_required,
        "owner_handoff": handoff_packet,
        "support_handoff": handoff_packet,
        "reviewer_handoff": handoff_packet,
        "safe_copy": safe_copy,
        "summary_alias": ROBOT_ALIAS,
        "robot_alias_schema": ROBOT_ALIAS_SCHEMA,
        "pr5_thread": _pr5_thread(),
        "blocked_claims": list(BLOCKED_CLAIMS),
        "not_proven_items": list(NOT_PROVEN_ITEMS),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "safety_markers": [
            "verified_terminal_result_material_owner_response_review_handoff",
            "software_proof_docker_verified_terminal_result_material_owner_response_review_handoff_gate",
            "source=software_proof",
            "software_proof",
            "not_proven",
            "delivery_success=false",
            "primary_actions_enabled=false",
            "safe_to_control=false",
            "PRRT_kwDOSWB9286CJ3tX",
            "hardware_material_pending",
            NO_OKR_LIFT,
        ],
    }
    summary = {
        "schema": SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "summary_only": True,
        "safe_to_render_on_phone": True,
        "verified_terminal_result_material_owner_response_review_handoff": handoff_status,
        **common,
    }
    artifact = {
        "schema": ARTIFACT_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "verified_terminal_result_material_owner_response_review_handoff": handoff_status,
        "source_owner_response_review_decision_detail": {
            "read_issue": source_issue,
            "schema": source["schema"],
            "evidence_boundary": source["evidence_boundary"],
            "unsafe_reasons": source["unsafe_reasons"],
            "ref_errors": source["ref_errors"],
        },
        **common,
        ROBOT_ALIAS: summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
    }
    return artifact, summary, exit_code


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    # CLI 写入缩进 JSON，便于 sprint evidence bundle 和人工 review。
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # CLI 只做本地 JSON gate，不提供 fetch、resolve、ACK、replay 或 robot command。
    parser = argparse.ArgumentParser(
        description=(
            "Build trashbot.verified_terminal_result_material_owner_response_review_handoff.v1 from --input/--source "
            "verified_terminal_result_material_owner_response_review_decision safe metadata. Keeps source=software_proof, "
            "software_proof, not_proven, delivery_success=false, primary_actions_enabled=false, safe_to_control=false, "
            "PRRT_kwDOSWB9286CJ3tX unresolved / hardware_material_pending, and no OKR percentage lift."
        )
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--input", dest="owner_response_review_decision_json", help="prior owner response review decision artifact, summary, or Robot safe alias JSON")
    source_group.add_argument("--source", dest="owner_response_review_decision_json", help="alias for --input")
    parser.add_argument("--evidence-ref", default="", help="expected same safe evidence_ref")
    parser.add_argument("--output-dir", type=Path, help="optional directory for owner response review handoff artifact and summary")
    parser.add_argument("--output", type=Path, help="optional owner response review handoff artifact JSON output path")
    parser.add_argument("--summary-output", type=Path, help="optional owner response review handoff summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print artifact JSON to stdout")
    args = parser.parse_args(argv)

    artifact, summary, exit_code = build_verified_terminal_result_material_owner_response_review_handoff(
        args.owner_response_review_decision_json,
        args.evidence_ref,
    )
    output = args.output
    summary_output = args.summary_output
    if args.output_dir:
        output = output or args.output_dir / "verified_terminal_result_material_owner_response_review_handoff.json"
        summary_output = summary_output or args.output_dir / "verified_terminal_result_material_owner_response_review_handoff_summary.json"
    if output:
        _write_json(output, artifact)
    if summary_output:
        _write_json(summary_output, summary)
    if args.once_json or not (output or summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"verified_terminal_result_material_owner_response_review_handoff: artifact_file:{_safe_text(output)}")
        if summary_output:
            print(f"verified_terminal_result_material_owner_response_review_handoff_summary_file:{_safe_text(summary_output)}")
        print(f"handoff_status:{artifact['handoff_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
