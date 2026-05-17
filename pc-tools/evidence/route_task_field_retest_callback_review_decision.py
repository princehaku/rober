#!/usr/bin/env python3
"""生成 route/task field retest callback review decision artifact。

该 gate 只读取上一轮 callback intake artifact/summary/wrapper/nested JSON，
把 received/missing/same-evidence-ref/next-backfill 状态整理成 PC / Robot /
mobile 可消费的 metadata-only review decision。它不读取真实材料目录，不访问
ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、外部云、OSS/CDN、DB/queue
或 4G。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# review decision 是 callback intake 后的新契约，不能复用上游 schema。
DECISION_SCHEMA = "trashbot.route_task_field_retest_callback_review_decision.v1"
DECISION_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_callback_review_decision_summary.v1"
SCHEMA_VERSION = 1
DECISION_BOUNDARY = "software_proof_docker_route_task_field_retest_callback_review_decision_gate"

# 只接受上一轮 callback intake 的 artifact 或 summary，避免跳过 intake 直接看材料。
SOURCE_SCHEMAS = {
    "trashbot.route_task_field_retest_callback_intake.v1",
    "trashbot.route_task_field_retest_callback_intake_summary.v1",
}
SOURCE_BOUNDARY = "software_proof_docker_route_task_field_retest_callback_intake_gate"

# 八类材料只作为 metadata checklist，不会被本 gate 打开或读取。
REQUIRED_EVIDENCE_PACKET = (
    "nav2_or_fixed_route_runtime_log",
    "route_completion_signal",
    "task_record",
    "door_state",
    "target_floor_confirmation",
    "human_assistance_note",
    "dropoff_or_cancel_completion",
    "delivery_result",
)

# not_proven 固定覆盖真实路线、电梯、投放、HIL、手机和 O5 外部证据缺口。
NOT_PROVEN = (
    "real_nav2_fixed_route_runtime_log_content",
    "real_route_completion_pass",
    "real_task_record_runtime",
    "real_elevator_door_state",
    "real_target_floor_confirmation",
    "real_human_assistance_field_note",
    "real_dropoff_or_cancel_completion",
    "real_delivery_result_reviewed_success",
    "real_delivery_success",
    "real_hil_pass",
    "real_phone_device_or_browser",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

BOUNDARY_NOTE = (
    "software_proof_docker_route_task_field_retest_callback_review_decision_gate; "
    "not_proven; delivery_success=false; primary_actions_enabled=false"
)

# 设计约束 01：本 gate 只读 callback intake summary，不读取真实材料目录。
# 设计约束 02：review decision 只决定下一步材料动作，不证明现场结果。
# 设计约束 03：所有 ready 分支仍保持 not_proven，不能写 delivery success。
# 设计约束 04：缺项优先进入 backfill，不允许直接推 result intake。
# 设计约束 05：same evidence_ref 是链路主键，不一致必须复跑上游。
# 设计约束 06：unsupported schema/boundary 阻断，防止跨 gate JSON 混入。
# 设计约束 07：unsafe copy 阻断，避免 raw path、topic、凭证进入下游。
# 设计约束 08：success wording 单独阻断，便于区分“文案危险”和“字段危险”。
# 设计约束 09：summary 是 Robot/mobile 首选消费面，只输出白名单字段。
# 设计约束 10：wrapper/nested JSON 只递归固定 key，避免任意 raw payload 被采信。
# 设计约束 11：source intake blocked 时不升级为 ready，只给 repair/backfill 分支。
# 设计约束 12：required evidence packet 固定八类，新增材料必须另开契约评审。
# 设计约束 13：rerun command 只给 PC gate 命令，不触发 ROS 或 Robot action。
# 设计约束 14：owner handoff 只传递责任摘要，不授权 Start/Dropoff/Cancel。
# 设计约束 15：最终 payload 递归脱敏，blocked artifact 也不能泄漏输入。
# 设计约束 16：exit code 保持 0，让 blocked decision 也能作为证据落盘。
# 设计约束 17：dependency-free，便于 macOS PC 和 Docker 本地验证。
# 设计约束 18：文档与测试同步更新，防止工具可用但流程不可验收。
# 设计约束 19：source status 只从 intake_status/status 读取，避免解释材料内容。
# 设计约束 20：received_filenames_summary 只说明文件名收到，不说明文件有效。
# 设计约束 21：missing_materials 为空才允许 result intake readiness 为 ready。
# 设计约束 22：next_backfill_action 只能影响提示，不能覆盖缺项判断。
# 设计约束 23：source safe_copy 只是兼容入口，不是权威 raw source。
# 设计约束 24：Robot diagnostics 和 mobile_readonly 复用 summary，保持字段一致。
# 设计约束 25：safe_copy 只放下游最小字段，避免 UI 导出完整 artifact。
# 设计约束 26：not_proven 列表总是完整输出，防止 ready 分支弱化边界。
# 设计约束 27：non_access_scope 明确列出未访问系统面，便于评审复核。
# 设计约束 28：bad JSON 与 unsupported schema 合并到 unsupported_callback_schema。
# 设计约束 29：这是为了把“输入不可用”统一给现场同学复跑 intake。
# 设计约束 30：success claim 优先于 unsafe copy，便于定位错误成功措辞。
# 设计约束 31：unsafe copy 覆盖凭证、路径、ROS topic、串口和硬件词。
# 设计约束 32：raw path 在本 gate 阻断，因为它会诱导读取真实材料目录。
# 设计约束 33：credential 在本 gate 阻断，因为 PC evidence 不能携带密钥。
# 设计约束 34：ROS topic 在本 gate 阻断，因为 callback review 不触发控制面。
# 设计约束 35：serial/UART 在本 gate 阻断，因为硬件事实另走 vendor-backed gate。
# 设计约束 36：WAVE ROVER 文案阻断，避免硬件假设绕过 vendor 资料。
# 设计约束 37：checksum 阻断，避免把材料完整性误当内容真实性。
# 设计约束 38：raw robot response 阻断，Robot 侧只允许白名单 diagnostics。
# 设计约束 39：complete artifact 阻断，避免 mobile copy/export 泄漏全量 JSON。
# 设计约束 40：Traceback 阻断，避免内部错误栈进入现场交接材料。
# 设计约束 41：delivery_success=true 永远不允许，summary 固定 false。
# 设计约束 42：primary_actions_enabled=true 永远不允许，summary 固定 false。
# 设计约束 43：field pass 词只能来自真实现场验收，本 gate 看到就 blocked。
# 设计约束 44：HIL pass 词只能来自真实 HIL 证据，本 gate 看到就 blocked。
# 设计约束 45：Nav2 success 词只能来自 runtime review，本 gate 看到就 blocked。
# 设计约束 46：dropoff/cancel completion 词只能来自终态材料复核。
# 设计约束 47：source_ref 与 requested_ref 同时存在时必须严格一致。
# 设计约束 48：same_ref status 只接受 matched/ready，其它状态都复跑。
# 设计约束 49：缺 evidence_ref 不能进入 ready，因为后续材料无法复账。
# 设计约束 50：missing source status 不能进入 ready，因为 intake 未证明可读。
# 设计约束 51：source intake blocked 不直接报 unsupported，是为了保留补材料路径。
# 设计约束 52：但 schema/boundary 不支持必须报 unsupported，避免跨契约消费。
# 设计约束 53：ready_for_result_intake 只表示元数据可交给下一层复账。
# 设计约束 54：needs_material_backfill 只要求回填材料摘要，不要求实机运行。
# 设计约束 55：evidence_ref_mismatch_rerun 只要求统一主键并复跑 intake/review。
# 设计约束 56：blocked_unsafe_callback 要求清理危险 copy 后复跑。
# 设计约束 57：blocked_success_claim 要求移除成功/动作授权措辞后复跑。
# 设计约束 58：unsupported_callback_schema 要求生成受支持 intake artifact/summary。
# 设计约束 59：result_intake_readiness 是布尔摘要，不是执行命令。
# 设计约束 60：rerun_commands 是 operator 提示，不由本 gate 自动执行。
# 设计约束 61：result_intake_next 命令只是标签，避免自动化误触发。
# 设计约束 62：owner_handoff 默认 Autonomy owner，因为这是路线材料链路。
# 设计约束 63：Robot/Full-stack 只作为 supporting owner，不改动作语义。
# 设计约束 64：handoff_note 明确 Robot/mobile read-only，防止 UI 放行动作。
# 设计约束 65：required_evidence_packet 总是输出八类，便于现场对表补采。
# 设计约束 66：door_state 与 target_floor_confirmation 保留电梯证据链。
# 设计约束 67：human_assistance_note 保留跨楼层人工协助记录。
# 设计约束 68：dropoff_or_cancel_completion 与 delivery_result 保留终态材料入口。
# 设计约束 69：本 gate 不判断 delivery_result 内容，只判断 callback 摘要状态。
# 设计约束 70：本 gate 不读取 material pack，不与 material_dir gate 重叠。
# 设计约束 71：本 gate 不访问 route status，不替代 fixed-route runtime review。
# 设计约束 72：本 gate 不访问 task record，不替代 task_record replay。
# 设计约束 73：本 gate 不访问 cloud relay，不推进 Objective 5 external proof。
# 设计约束 74：本 gate 不访问 phone browser，不证明真实设备或 PWA。
# 设计约束 75：本 gate 不访问 DB/queue，不证明生产 worker/cutover。
# 设计约束 76：本 gate 不访问 OSS/CDN，不证明 live traffic。
# 设计约束 77：本 gate 不访问 4G，不证明移动网络现场链路。
# 设计约束 78：本 gate 不访问 serial/UART，不证明底盘反馈。
# 设计约束 79：本 gate 不访问 ROS graph，不改变 Nav2 或 behavior state。
# 设计约束 80：本 gate 不访问 WAVE ROVER，不需要 vendor hardware source。
# 设计约束 81：如果未来需要真实材料内容，应由 result intake/material pack 处理。
# 设计约束 82：如果未来需要真实上车结论，应由 HIL/field review 处理。
# 设计约束 83：如果未来需要手机实测，应由 phone/browser acceptance 处理。
# 设计约束 84：如果未来需要公网云证据，应由 O5 external gates 处理。
# 设计约束 85：summary 字段保持扁平，降低 Robot/mobile 解析复杂度。
# 设计约束 86：safe_evidence_ref 与 evidence_ref 同值，兼容不同下游命名。
# 设计约束 87：boundary 与 evidence_boundary 同值，兼容旧 summary 消费者。
# 设计约束 88：status 与 review_decision 同值，便于 rg 和 diagnostics 检索。
# 设计约束 89：status_reasons 只放短原因，避免复制 raw source。
# 设计约束 90：source_callback_intake 只放 schema/boundary/status/ref 摘要。
# 设计约束 91：source unsafe/success 布尔保留定位，不回显命中文案。
# 设计约束 92：received missing filenames 保留在 summary，便于现场补文件。
# 设计约束 93：unexpected filenames 由上游 intake 提供，本 gate 不重新解释。
# 设计约束 94：all_recommended_received 只是辅助字段，不单独决定 ready。
# 设计约束 95：missing_materials 比 all_recommended_received 更优先。
# 设计约束 96：source_status 必须 ready_for_field_retest_callback_intake_not_proven。
# 设计约束 97：not_proven 后缀保留，避免 ready 被误写成真实 pass。
# 设计约束 98：最终自检只因输出自身危险而降级，避免误伤 success 修复提示。
# 设计约束 99：blocked_success_claim 的 next_required_evidence 可以提到移除 success。
# 设计约束 100：该提示是修复说明，不是成功声明。
# 设计约束 101：单测必须覆盖 ready、backfill、wrapper、mismatch、schema、unsafe、success。
# 设计约束 102：文档必须说明 decision mapping 和 required evidence packet。
# 设计约束 103：README 面向 PC operator，fixed_route_workflow 面向导航流程。
# 设计约束 104：CLI 参数沿用本 ladder 的 output/summary-output/once-json 形态。
# 设计约束 105：--callback-intake-json 名称强调只读上一层，不读材料目录。
# 设计约束 106：--evidence-ref 用于期望主键，不会读取该路径内容。
# 设计约束 107：write_json 只写用户指定 output，不创建其它证据目录。
# 设计约束 108：help 输出必须足够让自动化和人工复跑。
# 设计约束 109：py_compile 验证标准库 dependency-free 入口可解析。
# 设计约束 110：unittest 验证核心分支，不扩大到 ROS/HIL/云环境。
# 设计约束 111：rg 验证 literal 契约，防止边界字符串漂移。
# 设计约束 112：git diff --check 验证本轮触碰文件的 whitespace。
# 设计约束 113：新增文件若未被 Git 跟踪，需要额外 no-index 检查。
# 设计约束 114：本 gate 不做 commit/push，交给 sprint 主流程收口。
# 设计约束 115：本 gate 的价值是把 callback intake 结果变成明确下一步。
# 设计约束 116：本 gate 的边界是 metadata-only、software-proof、fail-closed。
# 设计约束 117：本 gate 的消费者是 PC、Robot diagnostics 和 mobile read-only panel。
# 设计约束 118：本 gate 的禁止事项是读取材料、控制动作、成功结论和外部 proof。
# 设计约束 119：source wrapper 支持只是兼容存储形态，不扩大可信字段集合。
# 设计约束 120：blocked artifact 仍可被 sprint closeout 引用为失败证据。
# 设计约束 121：decision 字符串保持英文枚举，便于 Robot/mobile 稳定解析。
# 设计约束 122：中文注释解释边界，避免后续维护者误升级 proof 语义。
# 设计约束 123：自由文本脱敏不等于放行；危险输入仍必须 blocked。
# 设计约束 124：本 gate 只前进复账链路，不改变自主控制闭环状态机。
# 设计约束 125：若后续接入 result intake，应继续保持同一 evidence_ref。
# 设计约束 126：若后续接入 mobile panel，只能消费 summary/safe_copy。
# 设计约束 127：若后续接入 Robot diagnostics，只能显示只读原因和下一步。
# 设计约束 128：本文件作为 Task A 交付，不修改 Robot 或 Full-stack 范围。

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

# 成功或动作授权只能来自真实验收；本 gate 看到即 blocked_success_claim。
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
)

# 本机绝对路径或 Windows 路径不允许进入 phone-safe review summary。
RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

# blocked artifact 也要脱敏，避免把危险输入原样留在证据文件。
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
    # UTC 让不同 PC/Docker 产物可按字符串排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 自由文本统一脱敏，blocked 分支也不回显敏感原文。
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
    # 最终输出递归脱敏，防止新增嵌套字段绕过局部 helper。
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
    # 安全扫描用稳定 JSON，无法编码时退回脱敏文本。
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
    # 缺输入、坏 JSON、非 object 都输出 blocked decision，便于自动化留痕。
    if not path:
        return {}, "callback_intake_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "callback_intake_missing"
    except json.JSONDecodeError:
        return {}, "callback_intake_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "callback_intake_read_error"
    if not isinstance(payload, dict):
        return {}, "callback_intake_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只接受 object 嵌套字段，字符串 wrapper 不可信。
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
        "route_task_field_retest_callback_intake",
        "route_task_field_retest_callback_intake_summary",
        "route_task_field_retest_callback_review_decision",
        "route_task_field_retest_callback_review_decision_summary",
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
    # 优先选择 schema 命中的 intake 对象；否则保留顶层用于 unsupported 解释。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _list_text(value: Any, limit: int = 24) -> list[str]:
    # 下游摘要只接受扁平字符串列表，避免复制完整 raw object。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit] if isinstance(item, (str, int, float, bool))]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _missing_from_source(source: dict[str, Any]) -> list[str]:
    # missing_materials 可能在顶层、summary 或 safe_copy，统一提取为字符串数组。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    for value in (source.get("missing_materials"), robot.get("missing_materials"), mobile.get("missing_materials"), safe_copy.get("missing_materials")):
        materials = _list_text(value)
        if materials:
            return materials
    return []


def _received_summary(source: dict[str, Any]) -> dict[str, Any]:
    # received summary 只描述文件名回执状态，不解释文件内容是否有效。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    for candidate in (
        _dict(source, "received_filenames_summary"),
        _dict(robot, "received_filenames_summary"),
        _dict(mobile, "received_filenames_summary"),
        _dict(safe_copy, "received_filenames_summary"),
    ):
        if candidate:
            return _safe_value(candidate)
    return {
        "recommended_count": 0,
        "received_count": 0,
        "missing_count": 0,
        "received_filenames": [],
        "missing_filenames": [],
        "unexpected_filenames": [],
        "all_recommended_received": False,
    }


def _same_ref_status(source: dict[str, Any]) -> dict[str, Any]:
    # same-evidence-ref 兼容 object 与字符串两种 summary 形态。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    raw = source.get("same_evidence_ref_match", robot.get("same_evidence_ref_match", mobile.get("same_evidence_ref_match", safe_copy.get("same_evidence_ref_match"))))
    if isinstance(raw, dict):
        return _safe_value(raw)
    if isinstance(raw, str):
        return {"status": _safe_text(raw)}
    return {"status": "missing_evidence_ref"}


def _source_status(source: dict[str, Any]) -> str:
    # intake status 是上游状态主键；缺失时不能默认 ready。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(
        _first_text(
            source.get("intake_status"),
            source.get("status"),
            robot.get("intake_status"),
            robot.get("status"),
            mobile.get("intake_status"),
            mobile.get("status"),
            safe_copy.get("intake_status"),
            default="",
        )
    )


def _source_ref(source: dict[str, Any]) -> str:
    # safe evidence_ref 从顶层、summary 或 safe_copy 取，最终仍做路径收敛。
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    safe_copy = _dict(source, "safe_copy")
    return _safe_ref(
        _first_text(
            source.get("safe_evidence_ref"),
            source.get("evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("evidence_ref"),
            safe_copy.get("evidence_ref"),
            default="",
        )
    )


def _schema_supported(source: dict[str, Any]) -> bool:
    # schema 和 boundary 双重约束，防止旧 JSON 或其它 gate 混用。
    schema = str(source.get("schema", "")).strip()
    boundary = str(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()
    return schema in SOURCE_SCHEMAS and (not boundary or boundary == SOURCE_BOUNDARY)


def _review_decision(
    load_issue: str,
    source: dict[str, Any],
    requested_ref: str,
    source_ref: str,
    source_status: str,
    same_ref: dict[str, Any],
    missing_materials: list[str],
    unsafe: bool,
    success_claim: bool,
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，避免坏输入落入 ready 或 backfill。
    if load_issue or not _schema_supported(source):
        return "unsupported_callback_schema", [load_issue or "unsupported_callback_schema_or_boundary"]
    if success_claim:
        return "blocked_success_claim", ["success_or_primary_action_claim_detected"]
    if unsafe:
        return "blocked_unsafe_callback", ["unsafe_copy_detected"]
    if requested_ref and source_ref and requested_ref != source_ref:
        return "evidence_ref_mismatch_rerun", [f"requested_ref:{requested_ref}!={source_ref}"]
    if same_ref.get("status") not in {"matched", "ready"}:
        return "evidence_ref_mismatch_rerun", [f"same_evidence_ref:{same_ref.get('status', 'missing')}"]
    if source_status != "ready_for_field_retest_callback_intake_not_proven":
        return "needs_material_backfill", [f"source_intake_status:{source_status or 'missing'}"]
    if missing_materials:
        return "needs_material_backfill", ["missing_materials:" + ",".join(missing_materials)]
    return "ready_for_result_intake", []


def _result_intake_readiness(decision: str) -> dict[str, Any]:
    # readiness 是只读判断，不会触发 result intake 或 Robot action。
    return {
        "ready": decision == "ready_for_result_intake",
        "state": "ready_for_result_intake" if decision == "ready_for_result_intake" else "not_ready",
        "blocked_by": "" if decision == "ready_for_result_intake" else decision,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _next_required_evidence(decision: str, evidence_ref: str, missing: list[str]) -> list[str]:
    # 下一步证据只列材料动作，不写现场通过或完成措辞。
    ref = evidence_ref or "<same_evidence_ref>"
    if decision == "ready_for_result_intake":
        return [
            f"Run result intake with sanitized callback materials under evidence_ref={ref}.",
            "Keep the result intake output as software_proof until real field materials are reviewed.",
        ]
    if decision == "needs_material_backfill":
        materials = missing or list(REQUIRED_EVIDENCE_PACKET)
        return [f"Backfill missing callback material metadata for evidence_ref={ref}: " + ", ".join(materials[:8])]
    if decision == "evidence_ref_mismatch_rerun":
        return [f"Regenerate callback intake with one evidence_ref={ref}.", "Rerun this review decision after refs match."]
    if decision == "blocked_unsafe_callback":
        return ["Regenerate callback intake without raw paths, credentials, ROS topics, serial/UART, WAVE ROVER detail, checksums, or raw responses."]
    if decision == "blocked_success_claim":
        return ["Remove delivery success, field pass, HIL pass, Nav2 success, dropoff/cancel completion, or primary action claims from callback intake."]
    return ["Provide a supported route_task_field_retest_callback_intake artifact or summary, then rerun this review decision."]


def _owner_handoff(decision: str, evidence_ref: str, missing: list[str]) -> dict[str, Any]:
    # owner handoff 保持元数据责任分配，不把动作交给 Robot/mobile。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "owner": "Autonomy Algorithm Engineer",
        "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer"],
        "handoff_status": "result_intake_ready_not_proven" if decision == "ready_for_result_intake" else "callback_backfill_or_repair_required_not_proven",
        "handoff_note": f"Review callback intake for evidence_ref={ref}; keep Robot/mobile read-only and primary actions disabled.",
        "missing_materials": missing,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _rerun_commands(evidence_ref: str) -> dict[str, str]:
    # command labels 只给 PC operator 复跑，不访问 ROS graph 或硬件。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "review_decision": (
            "python3 pc-tools/evidence/route_task_field_retest_callback_review_decision.py "
            f"--callback-intake-json /tmp/route_task_field_retest_callback_intake_summary.json --evidence-ref {ref} --once-json"
        ),
        "result_intake_next": (
            "python3 pc-tools/evidence/route_task_field_retest_result_intake.py "
            f"--callback-review-json /tmp/route_task_field_retest_callback_review_decision_summary.json --evidence-ref {ref}"
        ),
    }


def _safe_copy(decision: str, evidence_ref: str, source_status: str, received: dict[str, Any], missing: list[str], same_ref: dict[str, Any]) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 raw source、完整 artifact 或材料内容。
    return {
        "schema": f"{DECISION_SUMMARY_SCHEMA}.safe_copy",
        "review_decision": decision,
        "evidence_boundary": DECISION_BOUNDARY,
        "evidence_ref": evidence_ref,
        "source_intake_status": source_status,
        "received_filenames_summary": received,
        "missing_materials": missing,
        "same_evidence_ref_status": same_ref.get("status", ""),
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    decision: str,
    status_reasons: list[str],
    evidence_ref: str,
    source_status: str,
    received: dict[str, Any],
    missing: list[str],
    same_ref: dict[str, Any],
    next_required: list[str],
    owner_handoff: dict[str, Any],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是 Robot/mobile 兼容消费面，字段稳定且 fail closed。
    return {
        "schema": DECISION_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": DECISION_BOUNDARY,
        "boundary": DECISION_BOUNDARY,
        "status": decision,
        "review_decision": decision,
        "status_reasons": status_reasons,
        "evidence_ref": evidence_ref,
        "safe_evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_intake_status": source_status,
        "received_filenames_summary": received,
        "missing_materials": missing,
        "same_evidence_ref_match": same_ref,
        "next_required_evidence": next_required,
        "result_intake_readiness": _result_intake_readiness(decision),
        "owner_handoff": owner_handoff,
        "rerun_commands": _rerun_commands(evidence_ref),
        "fail_closed_notes": [
            "This review decision is metadata-only and does not read field material directories.",
            "Keep not_proven, delivery_success=false, and primary_actions_enabled=false until real evidence review.",
        ],
        "required_evidence_packet": list(REQUIRED_EVIDENCE_PACKET),
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_callback_review_decision(
    callback_intake_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 callback intake，生成 metadata-only review decision artifact。"""
    payload, load_issue = _load_json(callback_intake_json)
    source = _find_source(payload) if payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _source_ref(source) if source else ""
    evidence_ref_out = requested_ref or source_ref
    source_status = _source_status(source) if source else ""
    received = _received_summary(source) if source else _received_summary({})
    missing = _missing_from_source(source) if source else []
    same_ref = _same_ref_status(source) if source else {"status": "missing_evidence_ref"}
    unsafe = bool(payload) and _has_forbidden_copy(source)
    success_claim = bool(payload) and _has_success_claim(source)
    decision, status_reasons = _review_decision(
        load_issue,
        source,
        requested_ref,
        source_ref,
        source_status,
        same_ref,
        missing,
        unsafe,
        success_claim,
    )
    next_required = _next_required_evidence(decision, evidence_ref_out, missing)
    owner_handoff = _owner_handoff(decision, evidence_ref_out, missing)
    safe_copy = _safe_copy(decision, evidence_ref_out, source_status, received, missing, same_ref)
    summary = _summary_payload(
        decision,
        status_reasons,
        evidence_ref_out,
        source_status,
        received,
        missing,
        same_ref,
        next_required,
        owner_handoff,
        safe_copy,
    )
    artifact = {
        "schema": DECISION_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": DECISION_BOUNDARY,
        "boundary": DECISION_BOUNDARY,
        "status": decision,
        "review_decision": decision,
        "status_reasons": status_reasons,
        "evidence_ref": evidence_ref_out,
        "safe_evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "source_callback_intake": {
            "load_issue": load_issue,
            "schema": _safe_text(source.get("schema", "")) if source else "",
            "evidence_boundary": _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")) if source else "",
            "source_intake_status": source_status,
            "evidence_ref": source_ref,
            "unsafe_copy": bool(unsafe),
            "success_claim": bool(success_claim),
        },
        "received_filenames_summary": received,
        "missing_materials": missing,
        "same_evidence_ref_match": same_ref,
        "next_required_evidence": next_required,
        "result_intake_readiness": _result_intake_readiness(decision),
        "owner_handoff": owner_handoff,
        "rerun_commands": _rerun_commands(evidence_ref_out),
        "safe_copy": safe_copy,
        "route_task_field_retest_callback_review_decision_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "material_directory",
            "ros_graph",
            "nav2_runtime",
            "serial_uart",
            "wave_rover",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
            "real_field_file_content",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _has_forbidden_copy(summary) or (decision != "blocked_success_claim" and _has_success_claim(summary)):
        # 最终防线：输出自身不安全时降级；success 修复提示不再误伤原始 decision。
        summary["status"] = "blocked_unsafe_callback"
        summary["review_decision"] = "blocked_unsafe_callback"
        artifact["status"] = "blocked_unsafe_callback"
        artifact["review_decision"] = "blocked_unsafe_callback"
        artifact["route_task_field_retest_callback_review_decision_summary"] = summary
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
    parser = argparse.ArgumentParser(description="Generate a route/task field retest callback review decision artifact")
    parser.add_argument("--callback-intake-json", required=True, help="callback intake artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this review decision")
    parser.add_argument("--output", default="", help="optional review decision artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional review decision summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print review decision artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_callback_review_decision(args.callback_intake_json, args.evidence_ref)
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route_task_field_retest_callback_review_decision: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"callback_review_decision_summary_file: {_safe_ref(args.summary_output)}")
        print(f"review_decision: {artifact['review_decision']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
