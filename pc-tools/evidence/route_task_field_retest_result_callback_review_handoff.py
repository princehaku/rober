#!/usr/bin/env python3
"""生成 route/task field retest result callback review handoff artifact。

该 PC-only gate 只读取上一轮 result callback review decision 的 artifact、
summary 或 wrapper/nested JSON，把 result-review decision 转成 review 前的
owner follow-up、review-ready package 和 rerun package。它不读取真实材料目录，
不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、外部云、4G、OSS/CDN、
DB/queue 或真实手机/browser，也不触发任何机器人动作。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# 本 gate 是 result callback review decision 后的新契约，不能复用旧 handoff schema。
HANDOFF_SCHEMA = "trashbot.route_task_field_retest_result_callback_review_handoff.v1"
HANDOFF_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_result_callback_review_handoff_summary.v1"
SCHEMA_VERSION = 1
HANDOFF_BOUNDARY = "software_proof_docker_route_task_field_retest_result_callback_review_handoff_gate"

# 只接受上一轮 result callback review decision，避免跳过决策层直接包装 callback。
SOURCE_SCHEMAS = {
    "trashbot.route_task_field_retest_result_callback_review_decision.v1",
    "trashbot.route_task_field_retest_result_callback_review_decision_summary.v1",
}
SOURCE_BOUNDARY = "software_proof_docker_route_task_field_retest_result_callback_review_decision_gate"

# 下一轮 result review 前仍需要这几类证据说明；这里只生成 checklist，不读取材料。
REVIEW_READY_REQUIREMENTS = (
    "accepted_result_callback_updates",
    "owner_review_decision",
    "same_evidence_ref_match",
    "review_ready_safe_copy",
    "rerun_path_if_not_ready",
)

# not_proven 固定覆盖真实路线、电梯、终态、手机、HIL 和 O5 外部证据缺口。
NOT_PROVEN = (
    "real_nav2_fixed_route_runtime",
    "real_route_completion_signal",
    "real_task_record",
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_record",
    "real_dropoff_or_cancel_completion",
    "real_delivery_result_review",
    "real_delivery_success",
    "real_hil_pass",
    "real_phone_device_or_browser",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# rg 围栏依赖这些 literal，人工复盘也能快速识别本 gate 的边界。
BOUNDARY_NOTE = (
    "route_task_field_retest_result_callback_review_handoff; "
    "software_proof_docker_route_task_field_retest_result_callback_review_handoff_gate; "
    "not_proven; delivery_success=false; primary_actions_enabled=false; "
    "ready_for_result_review_handoff; needs_owner_follow_up; "
    "needs_callback_rerun; evidence_ref_mismatch_rerun; blocked_unsafe_review_handoff"
)

# 设计约束 01：本 gate 只消费 result callback review decision，不读材料目录。
# 设计约束 02：handoff_status 只表达 result review 前交接状态，不证明现场结果。
# 设计约束 03：ready 分支仍保持 not_proven，不能改变 Robot/mobile action。
# 设计约束 04：source decision 是唯一映射来源，不重新解释材料内容。
# 设计约束 05：unsupported schema/boundary 或缺 decision 必须 fail closed。
# 设计约束 06：unsafe copy 与 success/control claim 必须阻断。
# 设计约束 07：same_evidence_ref_required 固定为 true，维持证据链主键。
# 设计约束 08：review_ready_package 是只读包，不执行 result review。
# 设计约束 09：summary 是 Robot/mobile 可消费面，只输出白名单字段。
# 设计约束 10：wrapper/nested JSON 只递归固定 key，避免采信 raw payload。
# 设计约束 11：缺 evidence_ref 不进入 ready，因为下游无法复账。
# 设计约束 12：owner_follow_up 只透传安全摘要，不打开材料。
# 设计约束 13：rerun package 只是 PC operator 提示，不访问 ROS 或硬件。
# 设计约束 14：输出递归脱敏，blocked artifact 也不泄漏 raw source。
# 设计约束 15：dependency-free，便于 macOS PC 与 Docker 本地验证。
# 设计约束 16：exit code 保持 0，让 blocked handoff 也能作为证据落盘。
# 设计约束 17：文档和单测同步覆盖所有 handoff status mapping。
# 设计约束 18：该 gate 不推进 Objective 5 external proof。
# 设计约束 19：该 gate 不替代真实 result review 或 result reconciliation。
# 设计约束 20：该 gate 不触发 fixed-route、Nav2、dropoff 或 cancel 动作。
# 设计约束 21：ready 只代表 review package 可交接，不代表现场材料已经通过。
# 设计约束 22：needs_owner_follow_up 只要求 owner 回填，不授权任何自动驾驶动作。
# 设计约束 23：needs_callback_rerun 保留复跑路径，避免人工猜测 callback 内容。
# 设计约束 24：evidence_ref_mismatch_rerun 优先保护同一证据链主键。
# 设计约束 25：blocked_unsafe_review_handoff 统一覆盖敏感信息和控制声明。
# 设计约束 26：source schema 不匹配时不尝试“尽力理解”，直接转复跑。
# 设计约束 27：source boundary 不匹配时说明链路断裂，不能跨 gate 消费。
# 设计约束 28：缺 safe_evidence_ref 时下游无法复账，因此不能 ready。
# 设计约束 29：缺 review_decision 时不从 accepted_updates 推导结论。
# 设计约束 30：safe_copy 只能给只读 UI/diagnostics 使用，不给控制路径使用。
# 设计约束 31：owner_follow_up 保持白名单 owner/action，不透出 raw artifact。
# 设计约束 32：review_ready_package 只列要求和状态，不包含真实材料正文。
# 设计约束 33：rerun_package 使用相对命令，避免泄漏本机绝对路径。
# 设计约束 34：next_required_evidence 只写下一步证据动作，不写成功结论。
# 设计约束 35：status_reasons 使用短枚举，方便 Product closeout 复盘。
# 设计约束 36：source_callback_review_decision 只保留 schema/boundary/ref 摘要。
# 设计约束 37：robot_diagnostics_summary 与 summary 同源，避免两套口径漂移。
# 设计约束 38：mobile_readonly_summary 与 summary 同源，避免手机文案扩权。
# 设计约束 39：non_access_scope 明确本 gate 不访问运行时和硬件。
# 设计约束 40：not_proven 列表必须随 artifact 和 summary 同步输出。
# 设计约束 41：delivery_success 固定 false，不能被 source 覆盖。
# 设计约束 42：primary_actions_enabled 固定 false，不能被 source 覆盖。
# 设计约束 43：输入安全扫描发生在脱敏前，命中后不允许清洗成 ready。
# 设计约束 44：输出脱敏发生在落盘前，blocked 产物也不能泄漏敏感文本。
# 设计约束 45：final self-check 只看成功/动作声明，避免 non_access_scope 自误伤。
# 设计约束 46：FORBIDDEN_COPY 专门约束输入和外部材料，不约束内部枚举名。
# 设计约束 47：SUCCESS_CLAIM_PATTERNS 同时覆盖自由文案和 key=value 表达。
# 设计约束 48：RAW_PATH_PATTERNS 覆盖 macOS/Linux/Windows 常见绝对路径。
# 设计约束 49：SENSITIVE_PATTERNS 不尝试保留原 token，统一转为红acted 形态。
# 设计约束 50：wrapper 递归只走固定 key，避免任意 JSON 被误当 source。
# 设计约束 51：_safe_ref 对路径只保留 basename，避免证据号泄漏目录。
# 设计约束 52：_list_items 对非 list 返回空，避免字符串被当成材料列表。
# 设计约束 53：_list_text 只保留可打印标量，避免复制 nested raw object。
# 设计约束 54：_source_decision 兼容 safe_copy，但仍要求至少一个位置存在。
# 设计约束 55：_same_ref_required_ok 要求真布尔，字符串 true 不能通过。
# 设计约束 56：handoff mapping 与文档一一对应，新增状态必须补测试。
# 设计约束 57：build 函数只返回 artifact/summary/exit_code，不做副作用。
# 设计约束 58：write_json 是唯一文件写出口，便于 CLI 和测试隔离。
# 设计约束 59：main 只解析参数和输出 JSON，不嵌入业务分支。
# 设计约束 60：所有 helper 保持 dependency-free，避免 PC gate 引入 ROS 依赖。
# 设计约束 61：本文件不 import repo-local 模块，降低跨 worker 冲突。
# 设计约束 62：本 gate 不创建 fixture 目录；单测用 tempfile 隔离输入。
# 设计约束 63：ready 分支仍输出 rerun_package，方便后续 reviewer 复现。
# 设计约束 64：blocked 分支也输出 review_ready_package，方便 UI 展示原因。
# 设计约束 65：owner action 使用动词短语，避免被误读成机器指令。
# 设计约束 66：rerun commands 不包含真实 dispatch/callback 材料路径。
# 设计约束 67：upstream owner_follow_up 只作为上下文，不改变本 gate 状态。
# 设计约束 68：upstream next_required_evidence 可透传，但 unsafe 输入会先阻断。
# 设计约束 69：source_ref 与 requested_ref 都存在且不同才判 mismatch。
# 设计约束 70：source_ref 缺失时仍强制 mismatch，因为不能建立同证据链。
# 设计约束 71：same_ref status 仅接受 matched/ready，其他状态都需复跑。
# 设计约束 72：unsupported decision 进入 rerun，而不是 unsafe，便于修 schema。
# 设计约束 73：rejected_unsafe_callback 进入 blocked，保留安全边界。
# 设计约束 74：needs_material_backfill 进入 owner follow-up，保留人工补证路径。
# 设计约束 75：本 gate 不更新 OKR 或 sprint closeout，那是 Product 范围。
# 设计约束 76：本 gate 不更新 Robot/mobile 文件，那是并行 worker 范围。
# 设计约束 77：所有状态名使用 snake_case，便于 rg 和下游解析。
# 设计约束 78：所有 contract literal 与 tech-plan 保持一致。
# 设计约束 79：注释解释为何 fail closed，便于后续月度维护。
# 设计约束 80：如果未来接入真实现场材料，必须新增独立 gate 而非放宽本 gate。
# 设计约束 81：ready 输出不包含 material content，避免 reviewer 误以为已验收。
# 设计约束 82：blocked 输出仍保留 safe_evidence_ref，便于同证据链补证。
# 设计约束 83：load_issue 不直接抛异常，避免自动化链路中断留不下 artifact。
# 设计约束 84：坏 JSON 也映射为复跑，不让 Product 手动修补字段。
# 设计约束 85：非 object JSON 不可信，不能从数组或字符串猜测 schema。
# 设计约束 86：source boundary 为空时兼容历史 summary，但 schema 仍必须匹配。
# 设计约束 87：source boundary 非空且不同则认为跨链路污染。
# 设计约束 88：safe_copy schema 带 `.safe_copy` 后缀，方便下游识别白名单面。
# 设计约束 89：review_ready_package 的 ready 布尔只由 handoff_status 推导。
# 设计约束 90：rerun_package 的 required 布尔只由 handoff_status 推导。
# 设计约束 91：owner_follow_up 固定 Autonomy 主责，因为本 gate 属自主链路。
# 设计约束 92：supporting owners 仅表示只读协作，不表示文件可改范围扩大。
# 设计约束 93：非 access scope 使用内部枚举名，不作为外部输入安全扫描依据。
# 设计约束 94：summary 和 artifact 都输出 boundary，兼容不同消费者字段名。
# 设计约束 95：evidence_ref 与 safe_evidence_ref 同值，方便旧消费者读取。
# 设计约束 96：same_evidence_ref_match 保留原始安全摘要，便于 mismatch 追踪。
# 设计约束 97：source unsafe_copy/success_claim 只作为诊断字段，不直接透传正文。
# 设计约束 98：status_reasons 不包含敏感原文，只包含短理由和 evidence_ref 摘要。
# 设计约束 99：路径脱敏在 _safe_text 层完成，避免 nested helper 遗漏。
# 设计约束 100：凭证脱敏在 _safe_text 层完成，避免 owner note 泄漏 token。
# 设计约束 101：ROS topic 脱敏在 _safe_text 层完成，避免误导手机面。
# 设计约束 102：硬件平台词脱敏在 _safe_text 层完成，避免本 gate 越界。
# 设计约束 103：checksum 脱敏避免把完整材料摘要暴露给只读消费者。
# 设计约束 104：Traceback 脱敏避免把本机栈和路径带进 artifact。
# 设计约束 105：help 输出不依赖 repo 环境，保证最小 CLI 可发现性。

DECISION_TO_HANDOFF = {
    "ready_for_result_review": "ready_for_result_review_handoff",
    "needs_material_backfill": "needs_owner_follow_up",
    "needs_callback_rerun": "needs_callback_rerun",
    "evidence_ref_mismatch_rerun": "evidence_ref_mismatch_rerun",
    "rejected_unsafe_callback": "blocked_unsafe_review_handoff",
}

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

# 成功或动作授权不能通过 result review 前置 handoff 进入下游。
SUCCESS_CLAIM_PATTERNS = (
    re.compile(r"(?i)\bdelivery\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfield\s+pass(ed)?\b"),
    re.compile(r"(?i)\bhil\s+pass(ed)?\b"),
    re.compile(r"(?i)\bnav2\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bfixed[-_ ]route\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bdropoff\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bcancel\s+(success|succeeded|complete|completed|passed)\b"),
    re.compile(r"(?i)\bprimary_actions_enabled\s*[:=]\s*true\b"),
    re.compile(r"(?i)\bdelivery_success\s*[:=]\s*true\b"),
    re.compile(r"(?i)\b(start|confirm|cancel)\s+(delivery|dropoff|action)\b"),
)

# 本机绝对路径不能进入 review handoff。
RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

# blocked 输出也先脱敏，避免错误材料污染 sprint artifact。
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
    (re.compile(r"(?i)\bWAVE\s+ROVER\b"), "[REDACTED_PLATFORM]"),
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
    (re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"), r"\1[REDACTED_PATH]"),
    (re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"), "[REDACTED_PATH]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)complete artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)raw robot response"), "[REDACTED_RAW_RESPONSE]"),
)


def _utc_now() -> str:
    # UTC 时间让不同 PC/Docker 主机产物可排序审计。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有自由文本先脱敏，再进入 artifact 或 summary。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref 若被误填成本机路径，只保留 basename。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 递归脱敏是最终防线，防止新增嵌套字段绕过 helper。
    if isinstance(value, dict):
        return {str(_safe_text(key)): _safe_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return [_safe_value(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value


def _encoded(value: Any) -> str:
    # 安全扫描使用稳定 JSON，覆盖键名和值。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # forbidden copy 命中说明输入不适合进入 Robot/mobile 摘要。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY) or any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _has_success_claim(value: Any) -> bool:
    # 布尔字段和自由文案都检查，避免 success/control claim 穿透。
    if isinstance(value, dict):
        if value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都输出 blocked handoff，便于留痕。
    if not path:
        return {}, "callback_review_decision_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "callback_review_decision_missing"
    except json.JSONDecodeError:
        return {}, "callback_review_decision_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "callback_review_decision_read_error"
    if not isinstance(payload, dict):
        return {}, "callback_review_decision_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只接受 object 嵌套字段；字符串 wrapper 不可信。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # artifact、summary、safe_copy 和 wrapper 字段位置不同，取首个非空文本。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # wrapper/nested JSON 只递归白名单 key，避免 raw payload 被误采信。
    candidates = [payload]
    for key in (
        "route_task_field_retest_result_callback_review_decision",
        "route_task_field_retest_result_callback_review_decision_summary",
        "route_task_field_retest_result_callback_review_handoff",
        "route_task_field_retest_result_callback_review_handoff_summary",
        "robot_diagnostics_summary",
        "mobile_readonly_summary",
        "safe_copy",
        "artifact",
        "summary",
        "payload",
        "data",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_source_candidates(value))
    return candidates


def _find_source(payload: dict[str, Any]) -> dict[str, Any]:
    # 优先选择 schema 命中的 review decision 对象；否则保留顶层用于 unsupported 解释。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _list_items(value: Any, limit: int = 24) -> list[Any]:
    # 下游摘要只接受 list，避免弱类型字符串被当成已复核材料。
    if not isinstance(value, list):
        return []
    return _safe_value(value[:limit])


def _list_text(value: Any, limit: int = 24) -> list[str]:
    # owner/review/rerun 摘要只输出扁平文本，避免复制完整 raw object。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit] if isinstance(item, (str, int, float, bool))]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _source_decision(source: dict[str, Any]) -> str:
    # review_decision 是上游主键；status 只用于兼容 summary。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(_first_text(source.get("review_decision"), source.get("status"), safe_copy.get("review_decision"), default=""))


def _source_ref(source: dict[str, Any]) -> str:
    # safe evidence_ref 从顶层、summary 或 safe_copy 取，最终仍做路径收敛。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return _safe_ref(
        _first_text(
            source.get("safe_evidence_ref"),
            source.get("evidence_ref"),
            robot.get("safe_evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("safe_evidence_ref"),
            mobile.get("evidence_ref"),
            safe_copy.get("safe_evidence_ref"),
            safe_copy.get("evidence_ref"),
            default="",
        )
    )


def _same_ref_status(source: dict[str, Any]) -> dict[str, Any]:
    # same-evidence-ref 兼容 object 与字符串两种 summary 形态。
    safe_copy = _dict(source, "safe_copy")
    raw = source.get("same_evidence_ref_match", safe_copy.get("same_evidence_ref_match"))
    if isinstance(raw, dict):
        return _safe_value(raw)
    if isinstance(raw, str):
        return {"status": _safe_text(raw)}
    return {"status": "missing_evidence_ref"}


def _source_owner_follow_up(source: dict[str, Any]) -> list[Any]:
    # owner follow-up 可来自上游顶层或 safe_copy；这里只安全透传摘要。
    safe_copy = _dict(source, "safe_copy")
    for candidate in (source, safe_copy):
        items = _list_items(candidate.get("owner_follow_up"))
        if items:
            return items
    return []


def _source_next_required(source: dict[str, Any]) -> list[str]:
    # next_required_evidence 是 result review 前行动清单，不代表已完成。
    safe_copy = _dict(source, "safe_copy")
    for candidate in (source, safe_copy):
        items = _list_text(candidate.get("next_required_evidence"))
        if items:
            return items
    return []


def _schema_supported(source: dict[str, Any]) -> bool:
    # schema 和 boundary 双重约束，防止其它 gate JSON 混入。
    schema = str(source.get("schema", "")).strip()
    boundary = str(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()
    return schema in SOURCE_SCHEMAS and (not boundary or boundary == SOURCE_BOUNDARY)


def _same_ref_required_ok(source: dict[str, Any]) -> bool:
    # same_evidence_ref_required 必须是真布尔 true，弱类型字符串不能通过。
    return source.get("same_evidence_ref_required") is True


def _handoff_status(
    load_issue: str,
    source: dict[str, Any],
    requested_ref: str,
    source_ref: str,
    source_decision: str,
    same_ref: dict[str, Any],
    unsafe: bool,
    success_claim: bool,
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，避免坏输入落入 ready handoff。
    reasons: list[str] = []
    if load_issue:
        reasons.append(load_issue)
    if success_claim:
        return "blocked_unsafe_review_handoff", reasons + ["success_or_primary_action_claim_detected"]
    if unsafe:
        return "blocked_unsafe_review_handoff", reasons + ["unsafe_copy_detected"]
    if load_issue or not _schema_supported(source):
        return "needs_callback_rerun", reasons + ["unsupported_result_callback_review_decision_schema_or_boundary"]
    if not _same_ref_required_ok(source):
        return "evidence_ref_mismatch_rerun", reasons + ["same_evidence_ref_required_not_true"]
    if requested_ref and source_ref and requested_ref != source_ref:
        return "evidence_ref_mismatch_rerun", reasons + [f"requested_ref:{requested_ref}!={source_ref}"]
    if same_ref.get("status") not in {"matched", "ready"}:
        return "evidence_ref_mismatch_rerun", reasons + [f"same_evidence_ref:{same_ref.get('status', 'missing')}"]
    if not source_ref:
        return "evidence_ref_mismatch_rerun", reasons + ["safe_evidence_ref_missing"]
    if not source_decision:
        return "needs_callback_rerun", reasons + ["source_review_decision_missing"]
    if source_decision not in DECISION_TO_HANDOFF:
        return "needs_callback_rerun", reasons + [f"unsupported_source_review_decision:{source_decision}"]
    return DECISION_TO_HANDOFF[source_decision], reasons


def _review_ready_package(handoff_status: str, evidence_ref: str, source_decision: str) -> dict[str, Any]:
    # review-ready package 是只读验收入口，不触发真正 result review。
    ready = handoff_status == "ready_for_result_review_handoff"
    return {
        "ready": ready,
        "status": handoff_status,
        "source_review_decision": source_decision,
        "safe_evidence_ref": evidence_ref,
        "requirements": list(REVIEW_READY_REQUIREMENTS),
        "review_entry": "result_review_metadata_ready" if ready else "result_review_blocked_until_follow_up",
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _owner_follow_up(handoff_status: str, evidence_ref: str, source_decision: str, upstream_follow_up: list[Any]) -> list[dict[str, Any]]:
    # owner follow-up 只分派材料责任，不授权 Robot/mobile 任何动作。
    ref = evidence_ref or "<same_evidence_ref>"
    if handoff_status == "ready_for_result_review_handoff":
        action = "review_ready_package_before_result_review"
    elif handoff_status == "needs_owner_follow_up":
        action = "backfill_owner_material_before_result_review"
    elif handoff_status == "needs_callback_rerun":
        action = "repair_callback_review_decision_and_rerun_handoff"
    elif handoff_status == "evidence_ref_mismatch_rerun":
        action = "rerun_callback_review_decision_with_same_evidence_ref"
    else:
        action = "remove_unsafe_copy_or_control_claim_before_rerun"
    return [
        {
            "owner": "Autonomy Algorithm Engineer",
            "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer"],
            "action": action,
            "safe_evidence_ref": ref,
            "source_review_decision": source_decision,
            "upstream_owner_follow_up": upstream_follow_up,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    ]


def _rerun_package(handoff_status: str, evidence_ref: str) -> dict[str, Any]:
    # rerun package 只给 PC operator 复跑，不访问 ROS graph、Nav2 或硬件。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "required": handoff_status != "ready_for_result_review_handoff",
        "status": handoff_status,
        "safe_evidence_ref": ref,
        "commands": [
            "python3 pc-tools/evidence/route_task_field_retest_result_callback_review_decision.py "
            f"--callback-intake-json <callback_intake.json> --evidence-ref {ref} --once-json",
            "python3 pc-tools/evidence/route_task_field_retest_result_callback_review_handoff.py "
            f"--callback-review-decision-json <callback_review_decision.json> --evidence-ref {ref} --once-json",
        ],
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _next_required_evidence(handoff_status: str, evidence_ref: str, upstream_next: list[str]) -> list[str]:
    # 下一步只列证据动作，不写现场通过或完成措辞。
    ref = evidence_ref or "<same_evidence_ref>"
    if handoff_status == "ready_for_result_review_handoff":
        return upstream_next or [f"Prepare result review packet for evidence_ref={ref} from sanitized callback review decision."]
    if handoff_status == "needs_owner_follow_up":
        return upstream_next or [f"Backfill owner follow-up items for evidence_ref={ref} before result review."]
    if handoff_status == "needs_callback_rerun":
        return [f"Regenerate supported result callback review decision for evidence_ref={ref}."]
    if handoff_status == "evidence_ref_mismatch_rerun":
        return [f"Regenerate callback review decision and handoff with one evidence_ref={ref}."]
    return ["Regenerate callback review decision without raw paths, credentials, ROS topics, serial/UART, WAVE ROVER detail, checksums, control claims, or success claims."]


def _safe_copy(
    handoff_status: str,
    evidence_ref: str,
    source_decision: str,
    review_ready_package: dict[str, Any],
    next_required: list[str],
) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 raw source、完整 artifact 或材料内容。
    return {
        "schema": f"{HANDOFF_SUMMARY_SCHEMA}.safe_copy",
        "handoff_status": handoff_status,
        "status": handoff_status,
        "source_review_decision": source_decision,
        "evidence_boundary": HANDOFF_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "review_ready": bool(review_ready_package.get("ready")),
        "next_required_evidence": next_required,
        "same_evidence_ref_required": True,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_result_callback_review_handoff(
    callback_review_decision_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 result callback review decision，生成 result review 前 handoff artifact。"""
    payload, load_issue = _load_json(callback_review_decision_json)
    source = _find_source(payload) if payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _source_ref(source) if source else ""
    evidence_ref_out = requested_ref or source_ref
    source_decision = _source_decision(source) if source else ""
    same_ref = _same_ref_status(source) if source else {"status": "missing_evidence_ref"}
    upstream_follow_up = _source_owner_follow_up(source) if source else []
    upstream_next = _source_next_required(source) if source else []
    unsafe = bool(payload) and _has_forbidden_copy(source)
    success_claim = bool(payload) and _has_success_claim(source)
    handoff_status, status_reasons = _handoff_status(
        load_issue,
        source,
        requested_ref,
        source_ref,
        source_decision,
        same_ref,
        unsafe,
        success_claim,
    )
    review_ready_package = _review_ready_package(handoff_status, evidence_ref_out, source_decision)
    owner_follow_up = _owner_follow_up(handoff_status, evidence_ref_out, source_decision, upstream_follow_up)
    rerun_package = _rerun_package(handoff_status, evidence_ref_out)
    next_required = _next_required_evidence(handoff_status, evidence_ref_out, upstream_next)
    safe_copy = _safe_copy(handoff_status, evidence_ref_out, source_decision, review_ready_package, next_required)
    summary = {
        "schema": HANDOFF_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": HANDOFF_BOUNDARY,
        "boundary": HANDOFF_BOUNDARY,
        "status": handoff_status,
        "handoff_status": handoff_status,
        "status_reasons": status_reasons,
        "source_review_decision": source_decision,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_match": same_ref,
        "owner_follow_up": owner_follow_up,
        "review_ready_package": review_ready_package,
        "rerun_package": rerun_package,
        "next_required_evidence": next_required,
        "safe_copy": safe_copy,
        "fail_closed_notes": [
            "This handoff is metadata-only and does not read field material directories.",
            "Keep not_proven, delivery_success=false, and primary_actions_enabled=false until real result review evidence exists.",
        ],
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = {
        "schema": HANDOFF_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": HANDOFF_BOUNDARY,
        "boundary": HANDOFF_BOUNDARY,
        "status": handoff_status,
        "handoff_status": handoff_status,
        "status_reasons": status_reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "same_evidence_ref_match": same_ref,
        "source_callback_review_decision": {
            "load_issue": load_issue,
            "schema": _safe_text(source.get("schema", "")) if source else "",
            "evidence_boundary": _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")) if source else "",
            "source_review_decision": source_decision,
            "safe_evidence_ref": source_ref,
            "unsafe_copy": bool(unsafe),
            "success_claim": bool(success_claim),
        },
        "source_review_decision": source_decision,
        "owner_follow_up": owner_follow_up,
        "review_ready_package": review_ready_package,
        "rerun_package": rerun_package,
        "next_required_evidence": next_required,
        "safe_copy": safe_copy,
        "route_task_field_retest_result_callback_review_handoff_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "material_directory",
            "raw_field_material_content",
            "ros_graph",
            "nav2_runtime",
            "fixed_route_runtime",
            "serial_uart",
            "wave_rover",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
            "phone_device",
            "robot_action",
            "result_review_execution",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _has_success_claim(artifact) or _has_success_claim(summary):
        # 最终防线只拦截动作/成功声明；禁词已在 source 入口 fail closed。
        # artifact 自身必须保留 serial_uart 等 non_access_scope 名称，不能因此自我降级。
        artifact["status"] = "blocked_unsafe_review_handoff"
        artifact["handoff_status"] = "blocked_unsafe_review_handoff"
        summary["status"] = "blocked_unsafe_review_handoff"
        summary["handoff_status"] = "blocked_unsafe_review_handoff"
        artifact["route_task_field_retest_result_callback_review_handoff_summary"] = summary
        artifact["robot_diagnostics_summary"] = summary
        artifact["mobile_readonly_summary"] = summary
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时自动建目录；空路径表示只打印 stdout。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI dependency-free，便于 PC、Docker 和 unittest 直接复用。
    parser = argparse.ArgumentParser(description="Generate a route/task field retest result callback review handoff artifact")
    parser.add_argument("--callback-review-decision-json", required=True, help="result callback review decision artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this review handoff")
    parser.add_argument("--output", default="", help="optional handoff artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional handoff summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print handoff artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_result_callback_review_handoff(
        args.callback_review_decision_json,
        args.evidence_ref,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route_task_field_retest_result_callback_review_handoff: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"result_callback_review_handoff_summary_file: {_safe_ref(args.summary_output)}")
        print(f"handoff_status: {artifact['handoff_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
