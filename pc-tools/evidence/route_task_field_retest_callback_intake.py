#!/usr/bin/env python3
"""生成 route/task field retest callback intake artifact。

该 gate 只消费 evidence dispatch 产物和现场同学回传的 sanitized callback
JSON，复账推荐文件是否收到、缺哪些材料、同一 evidence_ref 是否一致，以及
下一步该由谁回填。它不读取真实材料目录、不访问 ROS graph、Nav2 runtime、
serial/UART、WAVE ROVER、真实电梯、外部云或真实手机/browser。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CALLBACK_INTAKE_SCHEMA = "trashbot.route_task_field_retest_callback_intake.v1"
CALLBACK_INTAKE_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_callback_intake_summary.v1"
SCHEMA_VERSION = 1
CALLBACK_INTAKE_BOUNDARY = "software_proof_docker_route_task_field_retest_callback_intake_gate"

# callback intake 只能承接 evidence dispatch，不能跳过派发层直接消费现场材料。
DISPATCH_SCHEMA = "trashbot.route_task_field_retest_evidence_dispatch.v1"
DISPATCH_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_evidence_dispatch_summary.v1"
DISPATCH_BOUNDARY = "software_proof_docker_route_task_field_retest_evidence_dispatch_gate"
SOURCE_SCHEMAS = {DISPATCH_SCHEMA, DISPATCH_SUMMARY_SCHEMA}
SOURCE_BOUNDARIES = {DISPATCH_BOUNDARY, ""}

# 现场回执 JSON 是 field staff 手动填写或工具生成的脱敏元数据，不要求固定 schema。
CALLBACK_INPUT_SCHEMAS = {"", "trashbot.route_task_field_retest_callback.v1", "trashbot.route_task_field_retest_callback_summary.v1"}
CALLBACK_INPUT_BOUNDARIES = {"", CALLBACK_INTAKE_BOUNDARY, DISPATCH_BOUNDARY}
CALLBACK_ALLOWED_FIELDS = {
    "schema",
    "schema_version",
    "evidence_boundary",
    "boundary",
    "evidence_ref",
    "safe_evidence_ref",
    "same_evidence_ref_required",
    "recommended_filename_received_status",
    "received_filenames",
    "missing_material_ids",
    "missing_materials",
    "next_backfill_action",
    "owner_callback_note",
    "callback_checklist_result",
    "checklist_result",
    "owner_handoff",
    "delivery_success",
    "primary_actions_enabled",
}

# 八类证据包沿用 dispatch gate，callback 只能对这些材料做 metadata-only 回执。
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

# not_proven 明确本 gate 不证明真实路线、电梯、投放、HIL、手机或云能力。
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
    "software_proof_docker_route_task_field_retest_callback_intake_gate; "
    "not_proven; delivery_success=false; primary_actions_enabled=false"
)

# 设计约束 01：本模块位于 evidence dispatch 之后，只确认“回执元数据”。
# 设计约束 02：它不是现场材料读取器，因此不能打开推荐文件名。
# 设计约束 03：它不是 result intake，因此不能解释材料内容是否真实。
# 设计约束 04：它不是 terminal review，因此不能给出通过/失败验收结论。
# 设计约束 05：它不是 Robot action，因此不能放行 Start/Dropoff/Cancel。
# 设计约束 06：它不是 HIL gate，因此不能把软件回执写成实机验证。
# 设计约束 07：它不是手机实测，因此不能证明真实 iPhone/Android 可用。
# 设计约束 08：它不是 O5 外部证据，因此不能证明公网、4G、OSS/CDN 或 DB/queue。
# 设计约束 09：dispatch 输入必须受 schema 和 boundary 双重约束。
# 设计约束 10：callback 输入允许无 schema，是为了兼容现场表单导出的简单 JSON。
# 设计约束 11：callback 字段仍必须白名单化，避免 raw artifact 被塞进表单。
# 设计约束 12：recommended filename 只当相对标识，不当真实路径读取。
# 设计约束 13：received status 使用 bool，是为了避免 yes/done 这类弱类型误判。
# 设计约束 14：missing material ids 只能引用固定八类材料。
# 设计约束 15：next backfill action 只能作为下一步建议，不改变 gate 结果。
# 设计约束 16：owner callback note 只保留脱敏文本，不承载原始日志。
# 设计约束 17：callback checklist result 使用 bool，是为了保留可机器判断的围栏。
# 设计约束 18：same_evidence_ref_required 必须是 JSON true，字符串 true 不可信。
# 设计约束 19：evidence_ref 同时来自 CLI、dispatch 和 callback，三者必须一致。
# 设计约束 20：单个 received entry 也可带 evidence_ref，便于逐文件复账。
# 设计约束 21：任一显式 evidence_ref 不一致都阻断，而不是选择其中一个继续。
# 设计约束 22：缺材料不等于 JSON 坏，允许 ready_not_proven 输出缺项清单。
# 设计约束 23：缺材料时 next action 强制回填，不能采信 callback 的“送入 result intake”。
# 设计约束 24：dispatch 未 ready 时阻断，避免把上游 blocked 推进下游。
# 设计约束 25：dispatch 缺推荐文件名时阻断，因为无法判断哪些文件已收到。
# 设计约束 26：callback 缺 received filenames 时阻断，因为缺少核心回执事实。
# 设计约束 27：callback 缺 checklist result 时阻断，因为缺少现场自检事实。
# 设计约束 28：unsupported callback field 阻断，避免未来字段默认裸露到 UI。
# 设计约束 29：unsupported callback schema 阻断，避免跨 gate JSON 混入。
# 设计约束 30：unsupported callback boundary 阻断，避免把其他 proof 边界伪装成本 gate。
# 设计约束 31：unsafe copy 在脱敏前检查，命中后不允许“清洗后 ready”。
# 设计约束 32：raw path 阻断是因为本 gate 不应泄漏 host 目录，也不应诱导读目录。
# 设计约束 33：credential 阻断是为了保护 OSS、DB、queue、bearer 等密钥。
# 设计约束 34：ROS topic 阻断是为了手机侧不暴露 `/cmd_vel` 等控制细节。
# 设计约束 35：serial/UART 阻断是为了保持硬件传输细节不进现场回执摘要。
# 设计约束 36：WAVE ROVER 文案阻断是为了避免硬件假设绕过 vendor 文档。
# 设计约束 37：Traceback 阻断是为了避免把内部异常直接展示给现场人员。
# 设计约束 38：checksum 阻断是为了避免把完整材料或内部校验细节作为证明。
# 设计约束 39：complete artifact 阻断是为了防止复制整份上游 JSON。
# 设计约束 40：raw robot response 阻断是为了避免 Robot 内部响应泄漏。
# 设计约束 41：success wording 阻断是因为真实通过只能来自后续人工复核/实测。
# 设计约束 42：delivery_success=true 阻断，因为本 gate 永远固定 false。
# 设计约束 43：primary_actions_enabled=true 阻断，因为本 gate 永远不放行动作。
# 设计约束 44：safe_copy 是下游白名单，不包含 raw source 或完整 callback。
# 设计约束 45：robot_diagnostics_summary 与 mobile_readonly_summary 复用 summary。
# 设计约束 46：summary 字段保持扁平，是为了 Robot/mobile 更容易只读消费。
# 设计约束 47：required evidence packet 总是输出八类材料，方便现场对表补采。
# 设计约束 48：received filenames summary 只说明“收到文件名”，不说明文件内容。
# 设计约束 49：missing materials 来自未收到文件和 callback 明示缺项的并集。
# 设计约束 50：unexpected filenames 留在 summary，便于发现现场误传文件。
# 设计约束 51：owner handoff 只把缺项分配给 owner，不改变任务状态机。
# 设计约束 52：fail-closed rerun notes 总是要求复跑本 gate 或补材料。
# 设计约束 53：non_access_scope 明确列出本 gate 不访问的系统面。
# 设计约束 54：generated_at 使用 UTC，便于多 PC/Docker 产物按时间排序。
# 设计约束 55：write_json 自动建目录，但只写用户指定 output。
# 设计约束 56：--once-json 方便自动化捕获 artifact，不要求输出文件。
# 设计约束 57：exit_code 维持 0，是为了 blocked artifact 能作为证据被保存。
# 设计约束 58：blocked_bad_json 单独区分，便于现场先修 JSON 格式。
# 设计约束 59：blocked_missing_dispatch_json 表示上游派发产物缺失。
# 设计约束 60：blocked_missing_callback_json 表示现场回执尚未提供。
# 设计约束 61：blocked_unsupported_dispatch_schema 表示上游不是 dispatch gate。
# 设计约束 62：blocked_unsupported_callback_schema_or_fields 表示回执越过白名单。
# 设计约束 63：blocked_missing_evidence_ref 表示同证据号主键缺失。
# 设计约束 64：blocked_same_evidence_ref_not_required 表示主键约束被弱化。
# 设计约束 65：blocked_same_evidence_ref_mismatch 表示材料链不能复账。
# 设计约束 66：blocked_weak_callback_fields 表示 callback 字段类型不可机器判断。
# 设计约束 67：blocked_unsupported_missing_material_ids 表示缺项不在八类材料内。
# 设计约束 68：blocked_dispatch_not_ready 表示上游派发还不能进入回执入口。
# 设计约束 69：blocked_missing_dispatch_recommended_filenames 表示缺少回执比对对象。
# 设计约束 70：ready_for_field_retest_callback_intake_not_proven 仍然不是 field pass。
# 设计约束 71：ready_not_proven 可以带 missing_materials，表示已整理缺项。
# 设计约束 72：缺项存在时 owner_handoff 进入 owner_backfill_required_not_proven。
# 设计约束 73：缺项不存在时 owner_handoff 仍只是 owner_review_required_not_proven。
# 设计约束 74：所有输出都保留 delivery_success=false。
# 设计约束 75：所有输出都保留 primary_actions_enabled=false。
# 设计约束 76：所有输出都保留 not_proven 列表。
# 设计约束 77：NOT_PROVEN 覆盖路线、电梯、人助、投放、HIL、手机和 O5 外证。
# 设计约束 78：BOUNDARY_NOTE 用 literal 方便 rg 验收和人工复盘。
# 设计约束 79：_source_candidates 只递归白名单 key，避免任意对象被当来源。
# 设计约束 80：_callback_candidates 只递归现场回执相关 key。
# 设计约束 81：_find_callback_source 要求候选对象至少有 callback 白名单字段。
# 设计约束 82：_normalise_dispatch 不复制 source_payload 到最终 summary。
# 设计约束 83：_callback_metadata 不复制未知字段，不解析材料内容。
# 设计约束 84：_received_filename_summary 不读取文件系统，只比对推荐文件名。
# 设计约束 85：_missing_materials 不触碰材料目录，只从 metadata 推导。
# 设计约束 86：_same_ref_match 使用 expected ref 合并 CLI、dispatch、callback。
# 设计约束 87：_intake_status 先处理坏输入，再处理 schema，再处理安全问题。
# 设计约束 88：_summary_payload 是下游接口契约，新增字段必须谨慎。
# 设计约束 89：_safe_value 是最终防线，不替代前置 unsafe 阻断。
# 设计约束 90：最终 summary 自身若不安全，状态降级且不回显 raw source。
# 设计约束 91：测试覆盖 ready、wrapper、缺输入、坏 JSON、schema mismatch。
# 设计约束 92：测试覆盖 evidence_ref mismatch 和弱类型 callback 字段。
# 设计约束 93：测试覆盖 unsafe copy、success claim 和未知 callback 字段。
# 设计约束 94：测试覆盖未知 material id，防止未来材料无审查扩散。
# 设计约束 95：README 和 fixed route workflow 必须同步说明边界。
# 设计约束 96：文档必须明确 callback intake 不是 result intake。
# 设计约束 97：文档必须明确 callback intake 不读取真实材料目录。
# 设计约束 98：文档必须明确 callback intake 不能证明 field pass。
# 设计约束 99：本文件不引入第三方依赖，方便 macOS/Docker 本地直接跑。
# 设计约束 100：后续 Robot/mobile 只能消费 summary 或 safe_copy。
# 设计约束 101：后续若新增字段，必须先加入白名单、测试和文档。
# 设计约束 102：后续若需要真实材料内容，应放到独立 result/material gate。
# 设计约束 103：后续若需要真实上车结论，应放到 HIL/field review 证据链。
# 设计约束 104：后续若需要手机真实验收，应使用真实设备/browser 证据。
# 设计约束 105：后续若需要 O5 外证，应使用公网/4G/OSS/CDN/DB/queue 材料。
# 设计约束 106：本 gate 的价值是把现场回执变成可复跑、可观测、可验收的元数据。
# 设计约束 107：本 gate 的边界是 metadata-only 和 fail-closed。
# 设计约束 108：本 gate 的使用者是 PC、Robot diagnostics 和 mobile read-only panel。
# 设计约束 109：本 gate 的禁止事项是控制动作、成功结论和硬件假设。
# 设计约束 110：本 gate 的下一跳通常是 result intake 或补材料回填。
# 设计约束 111：本 gate 即使 ready，也只能说明回执入口本身可用。
# 设计约束 112：本 gate 即使所有文件名收到，也不能说明文件内容有效。
# 设计约束 113：本 gate 即使 checklist 全部 checked，也不能说明现场通过。
# 设计约束 114：本 gate 即使 owner note 存在，也不能替代真实人工复核。
# 设计约束 115：本 gate 即使 same evidence_ref matched，也不能替代实机 run。
# 设计约束 116：本 gate 保留 missing_filenames，便于现场直接补对应文件。
# 设计约束 117：本 gate 保留 unexpected_filenames，便于发现命名偏差。
# 设计约束 118：本 gate 保留 unsupported_fields，便于现场修表单模板。
# 设计约束 119：本 gate 保留 parse_issues，便于定位弱类型字段。
# 设计约束 120：本 gate 保留 fail_closed_rerun_notes，便于自动化线程继续执行。
# 设计约束 121：本 gate 不导入 dispatch 模块，避免旧模块副作用影响独立 CLI。
# 设计约束 122：本 gate 只使用标准库，降低 PC 支持环境依赖。
# 设计约束 123：本 gate 输出 JSON 排序，方便 diff 和审计。
# 设计约束 124：本 gate 对 callback note 脱敏，但不会把危险 note 改写成通过。
# 设计约束 125：本 gate 对路径型 evidence_ref 只保留 basename。
# 设计约束 126：本 gate 对推荐文件名保留相对形式，便于现场按目录组织。
# 设计约束 127：本 gate 不把 checksum 当证明，避免内容真实性错觉。
# 设计约束 128：本 gate 不把 traceback 当诊断材料，避免泄漏内部实现。
# 设计约束 129：本 gate 不把 WAVE ROVER 参数当回执字段，硬件事实另走 vendor 资料。
# 设计约束 130：本 gate 不把 serial/UART 当回执字段，硬件通信另走硬件 gate。
# 设计约束 131：本 gate 不把 ROS topic 当回执字段，行为接口另走 ROS contract。
# 设计约束 132：本 gate 不把 DB/queue URL 当回执字段，云生产证据另走 O5 gate。
# 设计约束 133：本 gate 不把 OSS AK/SK 当回执字段，凭证永不进入仓库产物。
# 设计约束 134：本 gate 不把 raw robot response 当回执字段，Robot summary 必须白名单化。
# 设计约束 135：本 gate 不把 complete artifact 当回执字段，避免 UI 展示全量 JSON。
# 设计约束 136：本 gate 不把 field pass 作为合法文案，必须由 review gate 判定。
# 设计约束 137：本 gate 不把 HIL pass 作为合法文案，必须由真实 HIL 证据判定。
# 设计约束 138：本 gate 不把 dropoff complete 作为合法文案，必须由终态材料判定。
# 设计约束 139：本 gate 不把 cancel complete 作为合法文案，必须由终态材料判定。
# 设计约束 140：本 gate 不把 Nav2 success 作为合法文案，必须由 runtime 材料判定。
# 设计约束 141：本 gate 不合并真实材料内容，避免把“收到”误写成“有效”。
# 设计约束 142：本 gate 不新增 route/task 接口，只新增 PC 侧 JSON 契约。
# 设计约束 143：本 gate 不改变既有 result intake，只给它准备更干净的输入。
# 设计约束 144：本 gate 不依赖 ROS2 环境，保证 Docker/local PC 都能验收。
# 设计约束 145：本 gate 不吞掉 blocked 原因，所有阻断都留在 intake_status。
# 设计约束 146：本 gate 不把 callback action 作为权威命令，只作为建议字段。
# 设计约束 147：本 gate 不允许缺材料时继续送 result intake，先强制补材料。
# 设计约束 148：本 gate 不允许未知 owner 字段扩散，owner 只来自 dispatch 摘要。
# 设计约束 149：本 gate 不允许 callback 扩展字段静默通过，避免契约漂移。
# 设计约束 150：本 gate 不允许文档落后于代码，README 与导航流程同步更新。

# 输入中出现底层工程细节时必须 fail closed，避免进入 Robot/mobile 展示面。
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

# 成功文案和动作放行只能来自真实验收；本地 callback intake 看到即阻断。
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

# 本机绝对路径会诱导下游读取真实目录，也可能泄漏 host 结构。
RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

# 输出前再脱敏一次；blocked 产物也不能回显敏感输入。
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
    # UTC 让 PC/Docker 产物可以跨机器按时间线审计。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 自由文本统一脱敏，防止 callback note 带入敏感材料。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # evidence_ref 若被误填成路径，只保留 basename，避免泄漏本机目录。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_value(value: Any) -> Any:
    # 最终 payload 递归脱敏，避免新增嵌套字段绕过 helper。
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
    # 安全扫描覆盖键和值；不可编码时退回脱敏文本。
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return _safe_text(value)


def _has_forbidden_copy(value: Any) -> bool:
    # 禁词在脱敏前检查，命中后直接 blocked，不做“清洗后 ready”。
    encoded = _encoded(value)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _has_raw_path_copy(value: Any) -> bool:
    # callback intake 不读取真实材料目录；绝对路径 copy 一律视为不安全。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _has_success_or_control_claim(value: Any) -> bool:
    # 顶层布尔和自由文案都检查，防止成功语义穿透到下游。
    if isinstance(value, dict):
        if value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _unsafe_copy(value: Any) -> bool:
    # 本 gate 是 metadata-only 入口，危险 copy 不允许降级成普通 note。
    return _has_forbidden_copy(value) or _has_raw_path_copy(value) or _has_success_or_control_claim(value)


def _load_json(path: str, label: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都输出 blocked shape，方便自动化复盘。
    if not path:
        return {}, f"{label}_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, f"{label}_missing"
    except json.JSONDecodeError:
        return {}, f"{label}_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, f"{label}_read_error"
    if not isinstance(payload, dict):
        return {}, f"{label}_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只接受 object 嵌套字段，字符串 wrapper 不能伪装可信 JSON。
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
    # 只递归白名单 key，避免把任意 raw payload 当成 dispatch artifact。
    candidates = [payload]
    for key in (
        "route_task_field_retest_evidence_dispatch",
        "route_task_field_retest_evidence_dispatch_summary",
        "route_task_field_retest_callback_intake",
        "route_task_field_retest_callback_intake_summary",
        "robot_diagnostics_summary",
        "mobile_readonly_summary",
        "dispatch_artifact",
        "dispatch_summary",
        "artifact",
        "summary",
        "payload",
        "data",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_source_candidates(value))
    return candidates


def _find_dispatch_source(payload: dict[str, Any]) -> dict[str, Any]:
    # 优先使用 schema 命中的对象；没有命中时保留顶层用于 unsupported 解释。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _callback_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # callback wrapper 常见于现场表单导出，仍只取白名单嵌套对象。
    candidates = [payload]
    for key in (
        "route_task_field_retest_callback",
        "route_task_field_retest_callback_summary",
        "callback",
        "field_callback",
        "field_staff_callback",
        "sanitized_callback",
        "payload",
        "data",
    ):
        value = payload.get(key)
        if isinstance(value, dict):
            candidates.extend(_callback_candidates(value))
    return candidates


def _find_callback_source(payload: dict[str, Any]) -> dict[str, Any]:
    # 有 schema 的 callback 优先；无 schema 的顶层 sanitized object 也允许。
    for candidate in _callback_candidates(payload):
        callback_fields = set(candidate.keys()) & CALLBACK_ALLOWED_FIELDS
        if str(candidate.get("schema", "")).strip() in CALLBACK_INPUT_SCHEMAS and callback_fields:
            return candidate
    return payload


def _filename_to_material(filename: str) -> str:
    # 推荐文件名固定以 material 名结尾；只从 basename 推导材料 id。
    stem = Path(filename).name
    if stem.endswith(".json"):
        stem = stem[:-5]
    return stem


def _packet_names_from(value: Any) -> list[str]:
    # required_evidence_packet 支持 list[dict] 或 list[str]，但只取安全 name。
    names = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                name = _safe_text(_first_text(item.get("name"), item.get("material"), item.get("label"), default="")).strip()
            else:
                name = _safe_text(item).strip()
            if name and name not in names:
                names.append(name)
    return names


def _recommended_filenames_from(value: Any) -> list[str]:
    # 推荐文件名必须是相对 metadata 名称，不能带本机绝对路径。
    filenames: list[str] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                filename = _safe_text(_first_text(item.get("recommended_filename"), item.get("filename"), default="")).strip()
            else:
                filename = _safe_text(item).strip()
            if filename and filename not in filenames:
                filenames.append(filename)
    return filenames


def _normalise_dispatch(payload: dict[str, Any]) -> dict[str, Any]:
    # dispatch 只作为推荐证据包来源，不把 raw source 复制到输出。
    source = _find_dispatch_source(payload)
    safe_copy = _dict(source, "safe_copy")
    dispatch_plan = _dict(source, "dispatch_plan")
    robot = _dict(source, "robot_diagnostics_summary")
    mobile = _dict(source, "mobile_readonly_summary")
    source_ref = _safe_ref(
        _first_text(
            source.get("evidence_ref"),
            robot.get("evidence_ref"),
            mobile.get("evidence_ref"),
            safe_copy.get("evidence_ref"),
            default="",
        )
    )
    packet = source.get("required_evidence_packet") or robot.get("required_evidence_packet") or safe_copy.get("required_evidence_packet")
    packet_names = _packet_names_from(packet)
    recommended = _recommended_filenames_from(
        source.get("recommended_filenames")
        or robot.get("recommended_filenames")
        or dispatch_plan.get("recommended_filenames")
        or safe_copy.get("recommended_filenames")
    )
    if not recommended and isinstance(packet, list):
        recommended = _recommended_filenames_from(packet)
    return {
        "schema": _safe_text(source.get("schema", "")),
        "evidence_boundary": _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")),
        "status": _safe_text(_first_text(source.get("dispatch_status"), source.get("status"), robot.get("dispatch_status"), robot.get("status"), default="missing")),
        "evidence_ref": source_ref,
        "same_evidence_ref_required": source.get(
            "same_evidence_ref_required",
            robot.get("same_evidence_ref_required", mobile.get("same_evidence_ref_required", safe_copy.get("same_evidence_ref_required", True))),
        ),
        "recommended_filenames": recommended,
        "required_evidence_packet": packet_names,
        "material_owners": _safe_value(source.get("material_owners") or robot.get("material_owners") or dispatch_plan.get("material_owners") or {}),
        "source_payload": source,
    }


def _callback_source_status(load_issue: str, callback: dict[str, Any]) -> dict[str, Any]:
    # callback schema 可为空，但出现未知 schema/boundary 或未知字段必须阻断。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded", "field_status": "not_loaded"}
    schema = _safe_text(callback.get("schema", "")).strip()
    boundary = _safe_text(_first_text(callback.get("evidence_boundary"), callback.get("boundary"), default="")).strip()
    fields = set(callback.keys())
    if schema not in CALLBACK_INPUT_SCHEMAS or boundary not in CALLBACK_INPUT_BOUNDARIES:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported", "field_status": "not_checked"}
    unknown = sorted(fields - CALLBACK_ALLOWED_FIELDS)
    if unknown:
        return {
            "load_status": "loaded",
            "load_issue": "",
            "schema_status": "supported",
            "field_status": "unsupported_fields",
            "unsupported_fields": unknown,
        }
    return {"load_status": "loaded", "load_issue": "", "schema_status": "supported", "field_status": "supported"}


def _dispatch_source_status(load_issue: str, normalized: dict[str, Any]) -> dict[str, Any]:
    # dispatch schema 与 boundary 必须同时支持，防止跨 gate 材料跳级。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    if normalized["schema"] in SOURCE_SCHEMAS and normalized["evidence_boundary"] in SOURCE_BOUNDARIES:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _parse_received_status(callback: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    # received status 要求显式 bool，避免 "yes"/"done" 被误判为真实材料已收到。
    raw = callback.get("recommended_filename_received_status", callback.get("received_filenames"))
    if raw in (None, ""):
        return [], "missing_callback_received_filenames"
    entries: list[dict[str, Any]] = []
    if isinstance(raw, dict):
        iterator = raw.items()
        for filename, received in iterator:
            if not isinstance(filename, str) or not isinstance(received, bool):
                return [], "weak_callback_received_filenames"
            entries.append({"filename": _safe_text(filename), "received": received})
        return entries, ""
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                return [], "weak_callback_received_filenames"
            filename = item.get("filename", item.get("recommended_filename"))
            received = item.get("received")
            if not isinstance(filename, str) or not isinstance(received, bool):
                return [], "weak_callback_received_filenames"
            entry = {"filename": _safe_text(filename), "received": received}
            if item.get("evidence_ref") is not None:
                if not isinstance(item.get("evidence_ref"), str):
                    return [], "weak_callback_received_filenames"
                entry["evidence_ref"] = _safe_ref(item.get("evidence_ref"))
            entries.append(entry)
        return entries, ""
    return [], "weak_callback_received_filenames"


def _parse_string_list(value: Any, field_name: str) -> tuple[list[str], str]:
    # 缺项列表只能是字符串数组，防止 nested raw object 混进摘要。
    if value in (None, ""):
        return [], ""
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        return [], f"weak_{field_name}"
    return [_safe_text(item) for item in value], ""


def _parse_checklist_result(callback: dict[str, Any]) -> tuple[dict[str, Any], str]:
    # checklist 结果只接受 bool 映射或 list[{item, checked}]，不接受自由嵌套。
    raw = callback.get("callback_checklist_result", callback.get("checklist_result"))
    if raw in (None, ""):
        return {"checked_count": 0, "unchecked_items": [], "items": []}, "missing_callback_checklist_result"
    items: list[dict[str, Any]] = []
    if isinstance(raw, dict):
        for item, checked in raw.items():
            if not isinstance(item, str) or not isinstance(checked, bool):
                return {}, "weak_callback_checklist_result"
            items.append({"item": _safe_text(item), "checked": checked})
    elif isinstance(raw, list):
        for entry in raw:
            if not isinstance(entry, dict) or not isinstance(entry.get("item"), str) or not isinstance(entry.get("checked"), bool):
                return {}, "weak_callback_checklist_result"
            items.append({"item": _safe_text(entry["item"]), "checked": bool(entry["checked"])})
    else:
        return {}, "weak_callback_checklist_result"
    return {
        "checked_count": sum(1 for item in items if item["checked"]),
        "unchecked_items": [item["item"] for item in items if not item["checked"]],
        "items": items,
    }, ""


def _callback_metadata(callback: dict[str, Any]) -> dict[str, Any]:
    # callback 只提取白名单元数据，不读取文件、不复制 raw artifact。
    missing_ids, missing_issue = _parse_string_list(
        callback.get("missing_material_ids", callback.get("missing_materials")),
        "missing_material_ids",
    )
    checklist, checklist_issue = _parse_checklist_result(callback)
    received, received_issue = _parse_received_status(callback)
    next_action = callback.get("next_backfill_action", "")
    owner_note = callback.get("owner_callback_note", "")
    if next_action is not None and not isinstance(next_action, str):
        next_action_issue = "weak_next_backfill_action"
    else:
        next_action_issue = ""
    if owner_note is not None and not isinstance(owner_note, str):
        owner_note_issue = "weak_owner_callback_note"
    else:
        owner_note_issue = ""
    issues = [issue for issue in (received_issue, missing_issue, checklist_issue, next_action_issue, owner_note_issue) if issue]
    callback_ref = _safe_ref(_first_text(callback.get("safe_evidence_ref"), callback.get("evidence_ref"), default=""))
    return {
        "evidence_ref": callback_ref,
        "same_evidence_ref_required": callback.get("same_evidence_ref_required", True),
        "received_entries": received,
        "missing_material_ids": missing_ids,
        "next_backfill_action": _safe_text(next_action),
        "owner_callback_note": _safe_text(owner_note),
        "callback_checklist_result": checklist,
        "parse_issues": issues,
    }


def _received_filename_summary(recommended: list[str], received_entries: list[dict[str, Any]]) -> dict[str, Any]:
    # summary 只记录推荐文件名级别收到/未收到，不解释材料内容是否真实。
    status_by_name = {entry["filename"]: bool(entry["received"]) for entry in received_entries}
    received = [name for name in recommended if status_by_name.get(name) is True]
    missing = [name for name in recommended if status_by_name.get(name) is not True]
    unexpected = [name for name in status_by_name if name not in recommended]
    return {
        "recommended_count": len(recommended),
        "received_count": len(received),
        "missing_count": len(missing),
        "received_filenames": received,
        "missing_filenames": missing,
        "unexpected_filenames": unexpected,
        "all_recommended_received": bool(recommended) and not missing and not unexpected,
    }


def _missing_materials(required_packet: list[str], recommended: list[str], received_summary: dict[str, Any], callback_missing: list[str]) -> list[str]:
    # 缺材料从未收到文件和 callback 明示缺项合并得出，不读取材料目录验证。
    missing = []
    for filename in received_summary["missing_filenames"]:
        material = _filename_to_material(filename)
        if material in required_packet and material not in missing:
            missing.append(material)
    for material in callback_missing:
        if material not in REQUIRED_EVIDENCE_PACKET:
            if material not in missing:
                missing.append(material)
            continue
        if material not in missing:
            missing.append(material)
    if not recommended:
        return list(required_packet or REQUIRED_EVIDENCE_PACKET)
    return missing


def _unsupported_material_ids(materials: list[str]) -> list[str]:
    # callback 只能引用固定八类材料，拼错或新增类型都需要人工修正。
    return [material for material in materials if material not in REQUIRED_EVIDENCE_PACKET]


def _same_ref_match(dispatch_ref: str, callback_ref: str, requested_ref: str, received_entries: list[dict[str, Any]]) -> dict[str, Any]:
    # same evidence_ref 是现场回填链路主键，所有显式 ref 必须一致。
    expected = requested_ref or dispatch_ref or callback_ref
    compared = [ref for ref in (dispatch_ref, callback_ref, requested_ref) if ref]
    compared.extend(entry["evidence_ref"] for entry in received_entries if entry.get("evidence_ref"))
    mismatches = sorted({ref for ref in compared if expected and ref != expected})
    if not expected or not compared:
        status = "missing_evidence_ref"
    elif mismatches:
        status = "mismatch"
    else:
        status = "matched"
    return {
        "status": status,
        "expected_evidence_ref": expected,
        "dispatch_evidence_ref": dispatch_ref,
        "callback_evidence_ref": callback_ref,
        "requested_evidence_ref": requested_ref,
        "mismatched_evidence_refs": mismatches,
    }


def _owner_handoff(material_owners: Any, missing: list[str], callback_note: str) -> dict[str, Any]:
    # owner handoff 只聚合责任和缺项，不承诺现场结果通过。
    owners = material_owners if isinstance(material_owners, dict) else {}
    missing_by_owner: dict[str, list[str]] = {}
    for owner, materials in owners.items():
        if isinstance(materials, list):
            owned_missing = [material for material in materials if material in missing]
            if owned_missing:
                missing_by_owner[_safe_text(owner)] = owned_missing
    return {
        "material_owners": _safe_value(owners),
        "missing_materials_by_owner": missing_by_owner,
        "owner_callback_note": callback_note,
        "handoff_status": "owner_backfill_required_not_proven" if missing else "owner_review_required_not_proven",
    }


def _next_backfill_action(status: str, callback_action: str, missing: list[str], same_ref: dict[str, Any]) -> str:
    # 下一步只给回填/复跑动作，不能给 field pass 或 delivery success 结论。
    if status.startswith("blocked_same_evidence_ref") or same_ref["status"] == "mismatch":
        return "repair_same_evidence_ref_then_rerun_callback_intake"
    if status.startswith("blocked"):
        return "repair_dispatch_or_sanitized_callback_then_rerun"
    if missing:
        return "collect_missing_materials_then_rerun_result_intake"
    return callback_action or "send_sanitized_material_summary_to_result_intake"


def _fail_closed_rerun_notes(status: str, evidence_ref: str, missing: list[str]) -> list[str]:
    # rerun notes 把 blocked 或缺项转成操作，不写真实通过措辞。
    ref = evidence_ref or "<same_evidence_ref>"
    notes = [f"Rerun route_task_field_retest_callback_intake.py with evidence_ref={ref} after callback metadata repair."]
    if missing:
        notes.append("Backfill missing material metadata before result intake: " + ", ".join(missing))
    if status != "ready_for_field_retest_callback_intake_not_proven":
        notes.append("Fix source schema, boundary, same evidence_ref, safe copy, and strict callback field types before reuse.")
    notes.append("Keep delivery_success=false and primary_actions_enabled=false until real field evidence is reviewed.")
    return [_safe_text(note) for note in notes[:6]]


def _required_packet_summary(required_packet: list[str], recommended: list[str], received_summary: dict[str, Any]) -> list[dict[str, Any]]:
    # required evidence packet 是固定 checklist，received 也只是文件名回执状态。
    packet = []
    for material in REQUIRED_EVIDENCE_PACKET:
        filename = next((name for name in recommended if _filename_to_material(name) == material), f"field_retest_packet/<same_evidence_ref>/{material}.json")
        packet.append(
            {
                "name": material,
                "recommended_filename": filename,
                "required": True,
                "received": filename in received_summary["received_filenames"],
                "source_dispatch_status": "listed_by_dispatch" if material in required_packet else "missing_from_dispatch",
            }
        )
    return packet


def _intake_status(
    dispatch_load_issue: str,
    callback_load_issue: str,
    dispatch_status: dict[str, Any],
    callback_status: dict[str, Any],
    normalized_dispatch: dict[str, Any],
    callback_meta: dict[str, Any],
    same_ref: dict[str, Any],
    unsupported_missing_ids: list[str],
    unsafe_dispatch: bool,
    unsafe_callback: bool,
) -> str:
    # fail-closed 优先级固定，坏 JSON、unsafe、证据号不一致不会落入 ready。
    bad_json = {"dispatch_json_bad_json", "dispatch_json_read_error", "dispatch_json_not_object"}
    bad_callback = {"callback_json_bad_json", "callback_json_read_error", "callback_json_not_object"}
    if dispatch_load_issue in bad_json or callback_load_issue in bad_callback:
        return "blocked_bad_json"
    if dispatch_load_issue:
        return "blocked_missing_dispatch_json"
    if callback_load_issue:
        return "blocked_missing_callback_json"
    if dispatch_status["schema_status"] != "supported":
        return "blocked_unsupported_dispatch_schema"
    if callback_status["schema_status"] != "supported" or callback_status["field_status"] != "supported":
        return "blocked_unsupported_callback_schema_or_fields"
    if not normalized_dispatch["evidence_ref"] and not callback_meta["evidence_ref"]:
        return "blocked_missing_evidence_ref"
    if normalized_dispatch["same_evidence_ref_required"] is not True or callback_meta["same_evidence_ref_required"] is not True:
        return "blocked_same_evidence_ref_not_required"
    if unsafe_dispatch or unsafe_callback:
        return "blocked_unsafe_copy"
    if callback_meta["parse_issues"]:
        return "blocked_weak_callback_fields"
    if same_ref["status"] == "mismatch":
        return "blocked_same_evidence_ref_mismatch"
    if same_ref["status"] == "missing_evidence_ref":
        return "blocked_missing_evidence_ref"
    if unsupported_missing_ids:
        return "blocked_unsupported_missing_material_ids"
    if normalized_dispatch["status"] != "ready_for_field_retest_evidence_dispatch_not_proven":
        return "blocked_dispatch_not_ready"
    if not normalized_dispatch["recommended_filenames"]:
        return "blocked_missing_dispatch_recommended_filenames"
    return "ready_for_field_retest_callback_intake_not_proven"


def _safe_copy(status: str, evidence_ref: str, received_summary: dict[str, Any], missing: list[str], same_ref: dict[str, Any]) -> dict[str, Any]:
    # safe_copy 是 Robot/mobile 白名单消费面，不包含 raw callback 或材料内容。
    return {
        "schema": f"{CALLBACK_INTAKE_SUMMARY_SCHEMA}.safe_copy",
        "intake_status": status,
        "evidence_boundary": CALLBACK_INTAKE_BOUNDARY,
        "evidence_ref": evidence_ref,
        "received_filenames_summary": received_summary,
        "missing_materials": missing,
        "same_evidence_ref_match": same_ref["status"],
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _summary_payload(
    status: str,
    evidence_ref: str,
    received_summary: dict[str, Any],
    missing: list[str],
    same_ref: dict[str, Any],
    next_action: str,
    checklist: dict[str, Any],
    owner_handoff: dict[str, Any],
    rerun_notes: list[str],
    required_packet: list[dict[str, Any]],
    safe_copy: dict[str, Any],
) -> dict[str, Any]:
    # summary 是 diagnostics/mobile 首选消费面，字段稳定且保持 fail-closed。
    return {
        "schema": CALLBACK_INTAKE_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": CALLBACK_INTAKE_BOUNDARY,
        "boundary": CALLBACK_INTAKE_BOUNDARY,
        "status": status,
        "intake_status": status,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "received_filenames_summary": received_summary,
        "missing_materials": missing,
        "same_evidence_ref_match": same_ref,
        "next_backfill_action": next_action,
        "callback_checklist_result": checklist,
        "owner_handoff": owner_handoff,
        "fail_closed_rerun_notes": rerun_notes,
        "required_evidence_packet": required_packet,
        "safe_copy": safe_copy,
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_callback_intake(
    dispatch_json: str,
    callback_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 dispatch 和 sanitized callback，生成 fail-closed intake artifact。"""
    dispatch_payload, dispatch_load_issue = _load_json(dispatch_json, "dispatch_json")
    callback_payload, callback_load_issue = _load_json(callback_json, "callback_json")
    normalized_dispatch = _normalise_dispatch(dispatch_payload) if dispatch_payload else {
        "schema": "",
        "evidence_boundary": "",
        "status": "missing",
        "evidence_ref": "",
        "same_evidence_ref_required": True,
        "recommended_filenames": [],
        "required_evidence_packet": [],
        "material_owners": {},
        "source_payload": {},
    }
    callback_source = _find_callback_source(callback_payload) if callback_payload else {}
    callback_meta = _callback_metadata(callback_source) if callback_source else {
        "evidence_ref": "",
        "same_evidence_ref_required": True,
        "received_entries": [],
        "missing_material_ids": [],
        "next_backfill_action": "",
        "owner_callback_note": "",
        "callback_checklist_result": {"checked_count": 0, "unchecked_items": [], "items": []},
        "parse_issues": [],
    }

    requested_ref = _safe_ref(evidence_ref)
    dispatch_status = _dispatch_source_status(dispatch_load_issue, normalized_dispatch)
    callback_status = _callback_source_status(callback_load_issue, callback_source)
    received_summary = _received_filename_summary(normalized_dispatch["recommended_filenames"], callback_meta["received_entries"])
    missing = _missing_materials(normalized_dispatch["required_evidence_packet"], normalized_dispatch["recommended_filenames"], received_summary, callback_meta["missing_material_ids"])
    unsupported_missing_ids = _unsupported_material_ids(callback_meta["missing_material_ids"])
    same_ref = _same_ref_match(
        normalized_dispatch["evidence_ref"],
        callback_meta["evidence_ref"],
        requested_ref,
        callback_meta["received_entries"],
    )
    unsafe_dispatch = bool(dispatch_payload) and _unsafe_copy(normalized_dispatch["source_payload"])
    unsafe_callback = bool(callback_payload) and _unsafe_copy(callback_source)
    status = _intake_status(
        dispatch_load_issue,
        callback_load_issue,
        dispatch_status,
        callback_status,
        normalized_dispatch,
        callback_meta,
        same_ref,
        unsupported_missing_ids,
        unsafe_dispatch,
        unsafe_callback,
    )

    evidence_ref_out = same_ref["expected_evidence_ref"] or requested_ref or normalized_dispatch["evidence_ref"] or callback_meta["evidence_ref"]
    owner_handoff = _owner_handoff(normalized_dispatch["material_owners"], missing, callback_meta["owner_callback_note"])
    next_action = _next_backfill_action(status, callback_meta["next_backfill_action"], missing, same_ref)
    rerun_notes = _fail_closed_rerun_notes(status, evidence_ref_out, missing)
    required_packet = _required_packet_summary(normalized_dispatch["required_evidence_packet"], normalized_dispatch["recommended_filenames"], received_summary)
    safe_copy = _safe_copy(status, evidence_ref_out, received_summary, missing, same_ref)
    summary = _summary_payload(
        status,
        evidence_ref_out,
        received_summary,
        missing,
        same_ref,
        next_action,
        callback_meta["callback_checklist_result"],
        owner_handoff,
        rerun_notes,
        required_packet,
        safe_copy,
    )

    artifact = {
        "schema": CALLBACK_INTAKE_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": CALLBACK_INTAKE_BOUNDARY,
        "boundary": CALLBACK_INTAKE_BOUNDARY,
        "status": status,
        "intake_status": status,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "source_dispatch": {
            **dispatch_status,
            "schema": normalized_dispatch["schema"],
            "evidence_boundary": normalized_dispatch["evidence_boundary"],
            "dispatch_status": normalized_dispatch["status"],
            "evidence_ref": normalized_dispatch["evidence_ref"],
            "same_evidence_ref_required": normalized_dispatch["same_evidence_ref_required"],
            "recommended_filename_count": len(normalized_dispatch["recommended_filenames"]),
            "required_evidence_packet_count": len(normalized_dispatch["required_evidence_packet"]),
            "unsafe_copy": bool(unsafe_dispatch),
        },
        "callback_source": {
            **callback_status,
            "evidence_ref": callback_meta["evidence_ref"],
            "same_evidence_ref_required": callback_meta["same_evidence_ref_required"],
            "parse_issues": callback_meta["parse_issues"],
            "unsupported_missing_material_ids": unsupported_missing_ids,
            "unsafe_copy": bool(unsafe_callback),
        },
        "received_filenames_summary": received_summary,
        "missing_materials": missing,
        "same_evidence_ref_match": same_ref,
        "next_backfill_action": next_action,
        "callback_checklist_result": callback_meta["callback_checklist_result"],
        "owner_handoff": owner_handoff,
        "fail_closed_rerun_notes": rerun_notes,
        "required_evidence_packet": required_packet,
        "safe_copy": safe_copy,
        "route_task_field_retest_callback_intake_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "material_directory",
            "ros_graph",
            "nav2_runtime",
            "serial_uart",
            "wave_rover",
            "real_elevator",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
            "phone_device_or_browser",
            "real_field_file_content",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _unsafe_copy(summary):
        # 最终防线：输出自身不安全时只降级状态，不回显 source。
        summary["status"] = "blocked_unsafe_callback_intake_summary"
        summary["intake_status"] = "blocked_unsafe_callback_intake_summary"
        artifact["status"] = "blocked_unsafe_callback_intake_summary"
        artifact["intake_status"] = "blocked_unsafe_callback_intake_summary"
        artifact["route_task_field_retest_callback_intake_summary"] = summary
        artifact["robot_diagnostics_summary"] = summary
        artifact["mobile_readonly_summary"] = summary
    return artifact, summary, 0


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时自动建目录；空路径表示只走 stdout。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI dependency-free，便于 PC、Docker 和后续 diagnostics fixture 复用。
    parser = argparse.ArgumentParser(description="Generate a route/task field retest callback intake artifact")
    parser.add_argument("--dispatch-json", required=True, help="evidence dispatch artifact, summary, or wrapper/nested JSON")
    parser.add_argument("--callback-json", required=True, help="sanitized field staff callback JSON")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this callback intake")
    parser.add_argument("--output", default="", help="optional callback intake artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional callback intake summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print callback intake artifact JSON to stdout and exit")
    args = parser.parse_args()

    artifact, summary, exit_code = build_route_task_field_retest_callback_intake(args.dispatch_json, args.callback_json, args.evidence_ref)
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route_task_field_retest_callback_intake: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"callback_intake_summary_file: {_safe_ref(args.summary_output)}")
        print(f"intake_status: {artifact['intake_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
