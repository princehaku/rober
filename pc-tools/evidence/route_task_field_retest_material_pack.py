#!/usr/bin/env python3
"""生成 route/task field retest material pack artifact。

该 dependency-free PC gate 只读取上一轮
route_task_field_retest_result_review_handoff 的 artifact、summary 或
wrapper/nested JSON，把 owner handoff、same evidence_ref、材料回填要求和
rerun commands 转成现场 owner 可执行的材料包。它不读取材料目录，不访问 ROS
graph、Nav2 runtime、serial/UART、WAVE ROVER、外部云、4G、OSS/CDN、DB/queue
或真实手机/browser，也不触发任何机器人动作。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# material pack 是 result review handoff 后的新契约，不能复用旧材料目录入口。
PACK_SCHEMA = "trashbot.route_task_field_retest_material_pack.v1"
PACK_SUMMARY_SCHEMA = "trashbot.route_task_field_retest_material_pack_summary.v1"
SCHEMA_VERSION = 1
PACK_BOUNDARY = "software_proof_docker_route_task_field_retest_material_pack_gate"

# 只接受上一轮 result review handoff，避免跳过 handoff 直接包装 raw material。
SOURCE_SCHEMAS = {
    "trashbot.route_task_field_retest_result_review_handoff.v1",
    "trashbot.route_task_field_retest_result_review_handoff_summary.v1",
}
SOURCE_BOUNDARY = "software_proof_docker_route_task_field_retest_result_review_handoff_gate"

# 八类材料是旧 material-dir gate 和下游 result_intake / acceptance_backfill 的固定清单。
REQUIRED_MATERIALS = (
    "nav2_or_fixed_route_runtime_log",
    "route_completion_signal",
    "task_record",
    "door_state",
    "target_floor_confirmation",
    "human_assistance_note",
    "dropoff_or_cancel_completion",
    "delivery_result",
)

# handoff 模式给现场 owner 展示更细的采集语义，但不替换旧目录清单。
FIELD_CAPTURE_MATERIALS = (
    "elevator_door_state",
    "target_floor_confirmation",
    "human_assistance_record",
    "nav2_fixed_route_runtime_log",
    "route_completion_signal",
    "task_record",
    "dropoff_completion",
    "cancel_completion",
    "delivery_result",
)

# 每类材料允许 JSON 或文本文件；别名只影响发现，不进入 summary 的 raw path。
MATERIAL_ALIASES: dict[str, tuple[str, ...]] = {
    "nav2_or_fixed_route_runtime_log": (
        "nav2_or_fixed_route_runtime_log.json",
        "nav2_or_fixed_route_runtime_log.log",
        "nav2_or_fixed_route_runtime_log.txt",
        "runtime_log.json",
        "runtime_log.log",
    ),
    "route_completion_signal": ("route_completion_signal.json", "completion_signal.json"),
    "task_record": ("task_record.json",),
    "door_state": ("door_state.json",),
    "target_floor_confirmation": ("target_floor_confirmation.json", "floor_confirmation.json"),
    "human_assistance_note": ("human_assistance_note.json", "human_assistance_note.md", "operator_note.md"),
    "dropoff_or_cancel_completion": (
        "dropoff_or_cancel_completion.json",
        "dropoff_completion.json",
        "cancel_completion.json",
    ),
    "delivery_result": ("delivery_result.json", "delivery_result.md"),
}

# material pack 仍是 software proof，真实现场闭环必须由后续材料回填证明。
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

# rg 围栏和人工复盘都依赖这些 literal 识别边界。
BOUNDARY_NOTE = (
    "route_task_field_retest_material_pack; "
    "software_proof_docker_route_task_field_retest_material_pack_gate; "
    "not_proven; delivery_success=false; primary_actions_enabled=false; "
    "ready_for_field_retest_material_collection_not_proven; "
    "needs_result_review_handoff_not_proven; "
    "evidence_ref_mismatch_rerun_not_proven; "
    "blocked_missing_result_review_handoff_not_proven; "
    "unsupported_result_review_handoff_schema_not_proven"
)

# 设计约束 01：本 gate 只消费 result review handoff，不读取材料目录。
# 设计约束 02：material_pack_status 只表达现场材料采集准备，不证明现场通过。
# 设计约束 03：ready 分支仍保持 not_proven，不能改变 Robot/mobile action。
# 设计约束 04：source handoff 是唯一映射来源，不重新解释 raw material。
# 设计约束 05：unsupported schema/boundary 或缺 handoff 必须 fail closed。
# 设计约束 06：unsafe copy 与 success/control claim 必须阻断。
# 设计约束 07：same_evidence_ref_required 固定为 true，维持证据链主键。
# 设计约束 08：field_capture_checklist 是人工清单，不是机器执行计划。
# 设计约束 09：summary 是 Robot/mobile 可消费面，只输出白名单字段。
# 设计约束 10：wrapper/nested JSON 只递归固定 key，避免采信 raw payload。
# 设计约束 11：缺 evidence_ref 不进入 ready，因为下游无法复账。
# 设计约束 12：owner_work_orders 只做安全摘要，不打开上游完整 artifact。
# 设计约束 13：rerun_commands 只是 PC operator 提示，不访问 ROS 或硬件。
# 设计约束 14：输出递归脱敏，blocked artifact 也不泄漏 raw source。
# 设计约束 15：dependency-free，便于 macOS PC 与 Docker 本地验证。
# 设计约束 16：exit code 保持 0，让 blocked material pack 也能作为证据落盘。
# 设计约束 17：文档和单测同步覆盖所有 material_pack_status mapping。
# 设计约束 18：该 gate 不推进 Objective 5 external proof。
# 设计约束 19：该 gate 不替代真实 route/elevator field retest。
# 设计约束 20：该 gate 不触发 fixed-route、Nav2、dropoff 或 cancel 动作。
# 设计约束 21：ready 只代表 owner 可开始采集材料，不代表材料已经通过。
# 设计约束 22：needs handoff 只要求重生 handoff，不授权自动驾驶动作。
# 设计约束 23：mismatch 优先保护同一证据链主键。
# 设计约束 24：missing handoff 与 unsupported handoff 分开，方便定位。
# 设计约束 25：source schema 不匹配时不尝试“尽力理解”，直接 unsupported。
# 设计约束 26：source boundary 不匹配时说明链路断裂，不能跨 gate 消费。
# 设计约束 27：缺 safe_evidence_ref 时下游无法复账，因此必须复跑。
# 设计约束 28：缺 handoff_status 时不从 owner_work_orders 推导结论。
# 设计约束 29：safe_copy 只能给只读 UI/diagnostics 使用，不给控制路径使用。
# 设计约束 30：callback_payload_skeleton 只列字段，不包含真实材料正文。
# 设计约束 31：field_capture_checklist 使用固定材料类，避免自由文本扩权。
# 设计约束 32：source_result_review_handoff 只保留 schema/boundary/ref 摘要。
# 设计约束 33：robot_diagnostics_summary 与 summary 同源，避免口径漂移。
# 设计约束 34：mobile_readonly_summary 与 summary 同源，避免手机文案扩权。
# 设计约束 35：non_access_scope 明确本 gate 不访问运行时和硬件。
# 设计约束 36：not_proven 列表必须随 artifact 和 summary 同步输出。
# 设计约束 37：delivery_success 固定 false，不能被 source 覆盖。
# 设计约束 38：primary_actions_enabled 固定 false，不能被 source 覆盖。
# 设计约束 39：输入安全扫描发生在脱敏前，命中后不允许清洗成 ready。
# 设计约束 40：输出脱敏发生在落盘前，blocked 产物也不能泄漏敏感文本。
# 设计约束 41：FORBIDDEN_COPY 专门约束输入，不约束内部 non_access_scope。
# 设计约束 42：SUCCESS_CLAIM_PATTERNS 同时覆盖自由文案和 key=value 表达。
# 设计约束 43：RAW_PATH_PATTERNS 覆盖 macOS/Linux/Windows 常见绝对路径。
# 设计约束 44：SENSITIVE_PATTERNS 不保留原 token，统一转为 redacted 形态。
# 设计约束 45：wrapper 递归只走固定 key，避免任意 JSON 被误当 source。
# 设计约束 46：_safe_ref 对路径只保留 basename，避免证据号泄漏目录。
# 设计约束 47：_list_text 只保留可打印标量，避免复制 nested raw object。
# 设计约束 48：source boundary 为空不兼容；本 sprint 要求边界固定。
# 设计约束 49：safe_copy schema 带 `.safe_copy` 后缀，方便下游识别白名单面。
# 设计约束 50：rerun commands 不包含真实 dispatch/callback 材料路径。
# 设计约束 51：material pack checklist 只是采集任务，不代表采集已完成。
# 设计约束 52：missing handoff 默认要求重跑上游，防止空输入误 ready。
# 设计约束 53：same_ref status 仅接受 matched/ready，其他状态都需复跑。
# 设计约束 54：source handoff ready 必须来自受支持 status，字符串推断不通过。
# 设计约束 55：本 gate 不更新 OKR 或 sprint closeout，那是 Product 范围。
# 设计约束 56：本 gate 不更新 Robot/mobile 文件，那是并行 worker 范围。
# 设计约束 57：所有状态名使用 snake_case，便于 rg 和下游解析。
# 设计约束 58：所有 contract literal 与 tech-plan 保持一致。

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
    "baudrate",
    "baud_rate",
    "Traceback",
    "checksum",
    "complete artifact",
    "raw robot response",
)

HARDWARE_DETAIL_PATTERNS = (
    re.compile(r"(?i)\bserial\s*(port|device|log|transport)?\b"),
    re.compile(r"(?i)\bUART\b"),
    re.compile(r"(?i)\bWAVE\s+ROVER\b"),
)

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

RAW_PATH_PATTERNS = (
    re.compile(r"(?i)(^|[\s=:])/(Users|tmp|var|home|ws|private)/[^\s,;]+"),
    re.compile(r"(?i)[A-Za-z]:\\[^\s,;]+"),
)

# placeholder 只能算 rejected，不允许被当成现场回填材料。
PLACEHOLDER_PATTERNS = (
    re.compile(r"(?i)\b(tbd|todo|placeholder|example|sample|dummy|not_collected|fill me)\b"),
    re.compile(r"^<[^>]+>$"),
)

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
    # UTC 时间便于 Docker-only 主机和后续 sprint artifact 按时间线复盘。
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
    return (
        any(token in encoded for token in FORBIDDEN_COPY)
        or any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)
        or any(pattern.search(encoded) for pattern in HARDWARE_DETAIL_PATTERNS)
    )


def _has_success_claim(value: Any) -> bool:
    # 布尔字段和自由文案都检查，避免 success/control claim 穿透。
    if isinstance(value, dict):
        if value.get("delivery_success") is True or value.get("primary_actions_enabled") is True:
            return True
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in SUCCESS_CLAIM_PATTERNS)


def _has_raw_path_copy(value: Any) -> bool:
    # 旧下游直接 import 这个 helper；保留行为，禁止本机绝对路径进入 summary。
    encoded = _encoded(value)
    return any(pattern.search(encoded) for pattern in RAW_PATH_PATTERNS)


def _has_success_or_control_claim(value: Any) -> bool:
    # 旧 helper 名称继续映射到当前 success/control claim 检查。
    return _has_success_claim(value)


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺输入、坏 JSON、非 object 都输出 blocked material pack，便于留痕。
    if not path:
        return {}, "result_review_handoff_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "result_review_handoff_missing"
    except json.JSONDecodeError:
        return {}, "result_review_handoff_bad_json"
    except (OSError, UnicodeDecodeError):
        return {}, "result_review_handoff_read_error"
    if not isinstance(payload, dict):
        return {}, "result_review_handoff_not_object"
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


def _read_material(path: Path) -> tuple[str, Any, str]:
    # 坏 JSON 不抛异常；转成 rejected reason，便于现场修复单个材料。
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return "", {}, "read_error"
    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return text, {}, "bad_json"
        if not isinstance(payload, dict):
            return text, payload, "json_not_object"
        return text, payload, ""
    return text, {"note": text}, ""


def _material_ref(payload: Any, text: str, fallback_ref: str) -> str:
    # JSON 优先读 evidence_ref；Markdown/log 只解析固定 evidence_ref 行。
    if isinstance(payload, dict):
        return _safe_ref(_first_text(payload.get("evidence_ref"), payload.get("ref"), default=fallback_ref))
    match = re.search(r"(?im)^\s*-?\s*evidence_ref\s*:\s*(.+?)\s*$", text)
    return _safe_ref(match.group(1).strip()) if match else fallback_ref


def _material_status(payload: Any) -> str:
    # status 只用于判断是否 placeholder，不当作现场成功结论。
    if isinstance(payload, dict):
        return _safe_text(
            _first_text(
                payload.get("status"),
                payload.get("material_status"),
                payload.get("collection_status"),
                payload.get("state"),
                default="provided",
            )
        )
    return "provided"


def _placeholder_material(text: str, payload: Any, read_issue: str) -> bool:
    # 空文件、模板词和 placeholder 状态都不能算有效现场材料。
    if read_issue:
        return False
    encoded = _encoded(payload) + "\n" + text
    if not text.strip():
        return True
    if any(pattern.search(encoded.strip()) for pattern in PLACEHOLDER_PATTERNS):
        return True
    status = _material_status(payload).lower().replace("-", "_")
    return status in {"placeholder", "not_collected", "missing", "required_not_collected"}


def _find_material_file(material_dir: Path, material_name: str) -> Path | None:
    # 只按白名单文件名查找，避免任意目录文件被包装进 artifact。
    for alias in MATERIAL_ALIASES[material_name]:
        candidate = material_dir / alias
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _metadata_summary(payload: Any, text: str) -> dict[str, Any]:
    # 输出只保留短状态字段，不复制 raw log / note / ROS topic / 文件路径。
    if not isinstance(payload, dict):
        return {"summary_status": "text_material_detected", "text_length": len(text)}
    metadata: dict[str, Any] = {}
    for key in (
        "schema",
        "status",
        "material_status",
        "collection_status",
        "state",
        "review_note",
        "failure_reason",
        "observer_note",
        "source",
    ):
        if key in payload:
            metadata[key] = _safe_text(payload[key])
    return metadata


def _scan_material(material_dir: Path, material_name: str, expected_ref: str) -> tuple[dict[str, Any], list[str]]:
    # 单类材料扫描只返回状态和拒绝原因，绝不把正文写入输出。
    path = _find_material_file(material_dir, material_name)
    if path is None:
        return {
            "name": material_name,
            "status": "missing",
            "accepted": False,
            "same_evidence_ref_required": True,
            "rejected_reasons": ["missing_material"],
        }, ["missing_material"]
    text, payload, read_issue = _read_material(path)
    evidence_ref = _material_ref(payload, text, expected_ref)
    reasons: list[str] = []
    if read_issue:
        reasons.append(read_issue)
    if _placeholder_material(text, payload, read_issue):
        reasons.append("placeholder_only")
    if expected_ref and evidence_ref and evidence_ref != expected_ref:
        reasons.append("evidence_ref_mismatch")
    if not evidence_ref:
        reasons.append("missing_evidence_ref")
    if _has_forbidden_copy(text) or _has_forbidden_copy(payload):
        reasons.append("unsafe_copy")
    if _has_raw_path_copy(text) or _has_raw_path_copy(payload):
        reasons.append("raw_path_copy")
    if _has_success_or_control_claim(text) or _has_success_or_control_claim(payload):
        reasons.append("success_or_control_claim")
    entry = {
        "name": material_name,
        "status": "accepted" if not reasons else "rejected",
        "accepted": not reasons,
        "file_ref": f"file:{path.name}",
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "metadata": _metadata_summary(payload, text),
        "rejected_reasons": reasons,
    }
    return entry, reasons


def _source_dir_status(material_dir: str) -> tuple[Path | None, dict[str, Any]]:
    # CLI 必须显式收到 material-dir；缺目录不能猜测现场材料存在。
    if not material_dir:
        return None, {"directory_status": "missing_argument", "material_dir_ref": "", "load_issue": "material_dir_not_provided"}
    path = Path(material_dir).expanduser()
    if not path.exists() or not path.is_dir():
        return None, {
            "directory_status": "missing",
            "material_dir_ref": _safe_ref(str(path)),
            "load_issue": "material_dir_missing",
        }
    return path, {"directory_status": "scanned", "material_dir_ref": _safe_ref(str(path)), "load_issue": ""}


def _pack_status(dir_status: dict[str, Any], missing: list[str], rejected: dict[str, list[str]], mismatched: list[str]) -> str:
    # fail closed 优先级固定，便于 Robot/mobile 只读消费同一状态语义。
    if dir_status["load_issue"]:
        return "blocked_missing_material_dir"
    if any("unsafe_copy" in reasons or "raw_path_copy" in reasons for reasons in rejected.values()):
        return "blocked_unsafe_material_copy"
    if any("success_or_control_claim" in reasons for reasons in rejected.values()):
        return "blocked_success_or_control_claim"
    if mismatched:
        return "blocked_same_evidence_ref_mismatch"
    if missing:
        return "blocked_missing_materials"
    if any("placeholder_only" in reasons for reasons in rejected.values()):
        return "blocked_placeholder_only_materials"
    if rejected:
        return "blocked_rejected_materials"
    return "ready_for_field_retest_material_pack_not_proven"


def _operator_next_steps(status: str, evidence_ref: str, missing: list[str], rejected: dict[str, list[str]]) -> list[str]:
    # next steps 只要求补齐和重跑 PC gate，不允许引导现场成功或启用动作。
    ref = evidence_ref or "<same_evidence_ref>"
    if status == "ready_for_field_retest_material_pack_not_proven":
        return [
            f"Run route_task_field_retest_result_intake.py with this material pack summary for evidence_ref={ref}.",
            "Then run route_task_field_retest_result_reconciliation.py before any terminal review decision.",
            "Keep delivery_success=false and primary_actions_enabled=false until real review closes.",
        ]
    steps = [f"Keep every material on evidence_ref={ref} before rerun."]
    if missing:
        steps.append("Collect missing retest materials: " + ", ".join(missing))
    if rejected:
        rejected_names = ", ".join(f"{name}({'+'.join(reasons[:2])})" for name, reasons in rejected.items())
        steps.append("Repair rejected retest materials: " + rejected_names)
    steps.append("Rerun route_task_field_retest_material_pack.py --material-dir <material_dir> --once-json.")
    return [_safe_text(step) for step in steps[:5]]


def _material_completeness(materials: list[dict[str, Any]], missing: list[str]) -> dict[str, Any]:
    # completeness 是目录材料状态，不是 field pass 或 delivery success。
    accepted = [entry["name"] for entry in materials if entry["accepted"]]
    rejected = [entry["name"] for entry in materials if entry["status"] == "rejected"]
    return {
        "required_count": len(REQUIRED_MATERIALS),
        "accepted_count": len(accepted),
        "accepted_materials": accepted,
        "missing_materials": missing,
        "rejected_materials": rejected,
        "is_complete": len(accepted) == len(REQUIRED_MATERIALS),
    }


def _summary_payload(
    status: str,
    evidence_ref: str,
    materials: list[dict[str, Any]],
    completeness: dict[str, Any],
    rejected: dict[str, list[str]],
    operator_next_steps: list[str],
) -> dict[str, Any]:
    # summary 是下游首选消费面，字段保持白名单且不包含完整 artifact。
    safe_materials = [
        {
            "name": entry["name"],
            "status": entry["status"],
            "accepted": entry["accepted"],
            "evidence_ref": entry.get("evidence_ref", ""),
            "rejected_reasons": entry.get("rejected_reasons", []),
        }
        for entry in materials
    ]
    return {
        "schema": PACK_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": PACK_BOUNDARY,
        "boundary": PACK_BOUNDARY,
        "status": status,
        "material_pack_verdict": status,
        "material_pack_status": status,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "required_materials": list(REQUIRED_MATERIALS),
        "materials": safe_materials,
        "material_completeness": completeness,
        "missing_materials": completeness["missing_materials"],
        "rejected_materials": rejected,
        "operator_next_steps": operator_next_steps,
        "safe_copy": {
            "schema": f"{PACK_SUMMARY_SCHEMA}.safe_copy",
            "status": status,
            "material_pack_verdict": status,
            "material_pack_status": status,
            "evidence_boundary": PACK_BOUNDARY,
            "evidence_ref": evidence_ref,
            "not_proven": "not_proven",
            "delivery_success": False,
            "primary_actions_enabled": False,
        },
        "not_proven": list(NOT_PROVEN),
        "primary_actions_enabled": False,
        "delivery_success": False,
    }


def _build_material_dir_pack(material_dir: str, evidence_ref: str = "") -> tuple[dict[str, Any], dict[str, Any], int]:
    # 旧 material-dir 模式保持原有 artifact/summary 字段，避免下游 gate 断裂。
    requested_ref = _safe_ref(evidence_ref)
    material_path, dir_status = _source_dir_status(material_dir)
    materials: list[dict[str, Any]] = []
    rejected: dict[str, list[str]] = {}
    missing: list[str] = []
    mismatched: list[str] = []
    if material_path is None:
        for name in REQUIRED_MATERIALS:
            materials.append({"name": name, "status": "missing", "accepted": False, "rejected_reasons": ["missing_material"]})
            missing.append(name)
    else:
        for name in REQUIRED_MATERIALS:
            entry, reasons = _scan_material(material_path, name, requested_ref)
            materials.append(entry)
            if "missing_material" in reasons:
                missing.append(name)
            elif reasons:
                rejected[name] = reasons
            if "evidence_ref_mismatch" in reasons:
                mismatched.append(name)
            if not requested_ref and entry.get("evidence_ref"):
                requested_ref = entry["evidence_ref"]
    completeness = _material_completeness(materials, missing)
    status = _pack_status(dir_status, missing, rejected, mismatched)
    next_steps = _operator_next_steps(status, requested_ref, missing, rejected)
    summary = _summary_payload(status, requested_ref, materials, completeness, rejected, next_steps)
    artifact = {
        "schema": PACK_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": PACK_BOUNDARY,
        "boundary": PACK_BOUNDARY,
        "same_evidence_ref_required": True,
        "evidence_ref": requested_ref,
        "material_pack_verdict": status,
        "material_pack_status": status,
        "source_mode": "material_dir",
        "source_material_dir": dir_status,
        "material_manifest": materials,
        "material_pack_summary": summary,
        "operator_next_steps": next_steps,
        "result_intake_hint": {
            "schema": "trashbot.route_task_field_retest_result_intake.v1",
            "command": "run route_task_field_retest_result_intake.py with this material pack summary",
        },
        "result_reconciliation_hint": {
            "schema": "trashbot.route_task_field_retest_result_reconciliation.v1",
            "command": "run route_task_field_retest_result_reconciliation.py after intake",
        },
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "ros_graph",
            "nav2_runtime",
            "hardware_transport",
            "hardware",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
            "phone_device_or_browser",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "primary_actions_enabled": False,
        "delivery_success": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _has_forbidden_copy(summary) or _has_raw_path_copy(summary) or _has_success_or_control_claim(summary):
        # 最终防线：summary 仍不安全时只保留 blocked 状态，不输出原始内容。
        summary["status"] = "blocked_unsafe_summary"
        summary["material_pack_verdict"] = "blocked_unsafe_summary"
        summary["material_pack_status"] = "blocked_unsafe_summary"
        artifact["material_pack_verdict"] = "blocked_unsafe_summary"
        artifact["material_pack_status"] = "blocked_unsafe_summary"
        artifact["material_pack_summary"] = summary
    return artifact, summary, 0


def _source_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    # wrapper/nested JSON 只递归白名单 key，避免 raw payload 被误采信。
    candidates = [payload]
    for key in (
        "route_task_field_retest_result_review_handoff",
        "route_task_field_retest_result_review_handoff_summary",
        "route_task_field_retest_material_pack",
        "route_task_field_retest_material_pack_summary",
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
    # 优先选择 schema 命中的 handoff 对象；否则保留顶层用于 unsupported 解释。
    for candidate in _source_candidates(payload):
        if str(candidate.get("schema", "")).strip() in SOURCE_SCHEMAS:
            return candidate
    return payload


def _list_text(value: Any, limit: int = 32) -> list[str]:
    # 摘要只输出扁平文本，避免复制完整 raw object。
    if isinstance(value, list):
        items: list[str] = []
        for item in value[:limit]:
            if isinstance(item, dict):
                label = _first_text(item.get("material"), item.get("name"), item.get("id"), item.get("action"), default="")
                if label:
                    items.append(_safe_text(label))
            elif isinstance(item, (str, int, float, bool)):
                items.append(_safe_text(item))
        return items
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _list_items(value: Any, limit: int = 24) -> list[Any]:
    # owner work order 只接受 list，避免字符串被当成结构化任务。
    if not isinstance(value, list):
        return []
    return _safe_value(value[:limit])


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


def _source_handoff_status(source: dict[str, Any]) -> str:
    # handoff_status 是上游主键；status 只用于兼容 summary。
    safe_copy = _dict(source, "safe_copy")
    return _safe_text(
        _first_text(
            source.get("handoff_status"),
            source.get("status"),
            safe_copy.get("handoff_status"),
            safe_copy.get("status"),
            default="",
        )
    )


def _same_ref_status(source: dict[str, Any]) -> dict[str, Any]:
    # same-ref package 兼容 object 与字符串两种 summary 形态。
    safe_copy = _dict(source, "safe_copy")
    raw = source.get("same_evidence_ref_package", safe_copy.get("same_evidence_ref_package"))
    if isinstance(raw, dict):
        return _safe_value(raw)
    if isinstance(raw, str):
        return {"status": _safe_text(raw)}
    return {"status": "missing_evidence_ref"}


def _schema_supported(source: dict[str, Any]) -> bool:
    # schema 和 boundary 双重约束，防止其它 gate JSON 混入。
    schema = str(source.get("schema", "")).strip()
    boundary = str(_first_text(source.get("evidence_boundary"), source.get("boundary"), default="")).strip()
    return schema in SOURCE_SCHEMAS and boundary == SOURCE_BOUNDARY


def _same_ref_required_ok(source: dict[str, Any]) -> bool:
    # same_evidence_ref_required 必须是真布尔 true，弱类型字符串不能通过。
    return source.get("same_evidence_ref_required") is True


def _source_owner_work_orders(source: dict[str, Any]) -> list[Any]:
    # 上游 owner work orders 只安全透传摘要，不能作为机器动作。
    safe_copy = _dict(source, "safe_copy")
    for candidate in (source, safe_copy):
        items = _list_items(candidate.get("owner_work_orders") or candidate.get("owner_handoff"))
        if items:
            return items
    return []


def _source_callback_requirements(source: dict[str, Any]) -> list[str]:
    # callback/material requirements 是下一步行动清单，不代表已完成。
    safe_copy = _dict(source, "safe_copy")
    for candidate in (source, safe_copy):
        items = _list_text(candidate.get("next_material_callback_requirements") or candidate.get("next_required_evidence"))
        if items:
            return items
    return []


def _source_rerun_commands(source: dict[str, Any]) -> list[str]:
    # 上游 rerun commands 只保留文本摘要；unsafe 输入会先 fail closed。
    for candidate in (source, _dict(source, "safe_copy")):
        items = _list_text(candidate.get("rerun_commands") or candidate.get("commands"))
        if items:
            return items
    return []


def _source_material_lists(source: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    # 材料字段只接受白名单结构；默认全部 required，防止空输入误 ready。
    accepted = _list_text(source.get("accepted_materials"))
    missing = _list_text(source.get("missing_materials"))
    rejected = _list_text(source.get("rejected_materials"))
    accepted_set = {item for item in accepted if item in FIELD_CAPTURE_MATERIALS}
    if not missing:
        missing = [item for item in FIELD_CAPTURE_MATERIALS if item not in accepted_set]
    return accepted, missing, rejected


def _source_boundary(source: dict[str, Any]) -> str:
    # source_boundary 单独保留给 artifact，方便下游核对 lineage。
    return _safe_text(_first_text(source.get("evidence_boundary"), source.get("boundary"), default=""))


def _material_pack_status(
    load_issue: str,
    source: dict[str, Any],
    requested_ref: str,
    source_ref: str,
    handoff_status: str,
    same_ref: dict[str, Any],
    unsafe: bool,
    success_claim: bool,
) -> tuple[str, list[str]]:
    # fail-closed 优先级固定，避免坏输入落入现场材料采集 ready。
    if load_issue:
        return "blocked_missing_result_review_handoff_not_proven", [load_issue]
    if success_claim:
        return "unsupported_result_review_handoff_schema_not_proven", ["success_or_primary_action_claim_detected"]
    if unsafe:
        return "unsupported_result_review_handoff_schema_not_proven", ["unsafe_copy_detected"]
    if not _schema_supported(source):
        return "unsupported_result_review_handoff_schema_not_proven", ["unsupported_result_review_handoff_schema_or_boundary"]
    if not _same_ref_required_ok(source):
        return "evidence_ref_mismatch_rerun_not_proven", ["same_evidence_ref_required_not_true"]
    if requested_ref and source_ref and requested_ref != source_ref:
        return "evidence_ref_mismatch_rerun_not_proven", [f"requested_ref:{requested_ref}!={source_ref}"]
    if same_ref.get("status") not in {"matched", "ready"}:
        return "evidence_ref_mismatch_rerun_not_proven", [f"same_evidence_ref:{same_ref.get('status', 'missing')}"]
    if not source_ref:
        return "evidence_ref_mismatch_rerun_not_proven", ["safe_evidence_ref_missing"]
    if handoff_status == "ready_for_owner_result_callback_not_proven":
        return "ready_for_field_retest_material_collection_not_proven", []
    if handoff_status in {
        "needs_result_material_callback_not_proven",
        "blocked_missing_result_review_decision_not_proven",
    }:
        return "needs_result_review_handoff_not_proven", [f"source_handoff_status:{handoff_status}"]
    if handoff_status == "evidence_ref_mismatch_rerun_not_proven":
        return "evidence_ref_mismatch_rerun_not_proven", [f"source_handoff_status:{handoff_status}"]
    return "unsupported_result_review_handoff_schema_not_proven", [f"unsupported_source_handoff_status:{handoff_status or 'missing'}"]


def _field_capture_checklist(
    material_pack_status: str,
    evidence_ref: str,
    source_requirements: list[str],
) -> list[dict[str, Any]]:
    # checklist 固定为现场材料采集动作，不携带 raw handoff 或真实材料正文。
    ref = evidence_ref or "<same_evidence_ref>"
    requirement_text = " ".join(source_requirements)
    checklist: list[dict[str, Any]] = []
    for material in FIELD_CAPTURE_MATERIALS:
        checklist.append(
            {
                "material": material,
                "owner": "field_owner",
                "safe_evidence_ref": ref,
                "required": True,
                "collection_status": "required_not_collected",
                "source_requirement_seen": material in requirement_text,
                "not_proven": "not_proven",
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
        )
    if material_pack_status != "ready_for_field_retest_material_collection_not_proven":
        for item in checklist:
            item["collection_status"] = "blocked_until_supported_result_review_handoff"
    return checklist


def _callback_payload_skeleton(evidence_ref: str, checklist: list[dict[str, Any]]) -> dict[str, Any]:
    # skeleton 是给 owner 填写的字段模板，不包含任何真实采集结果。
    ref = evidence_ref or "<same_evidence_ref>"
    return {
        "schema": "trashbot.route_task_field_retest_material_pack_callback.v1",
        "safe_evidence_ref": ref,
        "same_evidence_ref_required": True,
        "materials": [
            {
                "material": item["material"],
                "evidence_ref": ref,
                "artifact_ref": "<relative_or_redacted_artifact_ref>",
                "observer_note": "<sanitized_note>",
                "collection_status": "required_not_collected",
                "not_proven": "not_proven",
                "delivery_success": False,
                "primary_actions_enabled": False,
            }
            for item in checklist
        ],
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def _owner_work_orders(
    material_pack_status: str,
    evidence_ref: str,
    upstream_orders: list[Any],
    checklist: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    # owner work order 只描述人工补证/复跑责任，不给 Robot/mobile 控制指令。
    ref = evidence_ref or "<same_evidence_ref>"
    if material_pack_status == "ready_for_field_retest_material_collection_not_proven":
        action = "collect_route_elevator_field_retest_materials_from_material_pack"
    elif material_pack_status == "needs_result_review_handoff_not_proven":
        action = "regenerate_result_review_handoff_before_material_collection"
    elif material_pack_status == "evidence_ref_mismatch_rerun_not_proven":
        action = "rerun_result_review_handoff_with_same_evidence_ref"
    elif material_pack_status == "blocked_missing_result_review_handoff_not_proven":
        action = "provide_result_review_handoff_artifact_or_summary"
    else:
        action = "regenerate_supported_result_review_handoff_without_unsafe_copy"
    return [
        {
            "owner": "Autonomy Algorithm Engineer",
            "supporting_owners": ["Robot Platform Engineer", "User Touchpoint Full-Stack Engineer"],
            "action": action,
            "safe_evidence_ref": ref,
            "required_materials": [item["material"] for item in checklist],
            "upstream_owner_work_orders": upstream_orders,
            "delivery_success": False,
            "primary_actions_enabled": False,
        }
    ]


def _rerun_commands(material_pack_status: str, evidence_ref: str, upstream_commands: list[str]) -> list[str]:
    # rerun commands 使用占位路径，避免泄漏本机或真实材料路径。
    ref = evidence_ref or "<same_evidence_ref>"
    commands = upstream_commands[:6] if upstream_commands else []
    commands.append(
        "python3 pc-tools/evidence/route_task_field_retest_result_review_handoff.py "
        f"--result-review-decision-json <result_review_decision.json> --evidence-ref {ref} --once-json"
    )
    commands.append(
        "python3 pc-tools/evidence/route_task_field_retest_material_pack.py "
        f"--result-review-handoff-json <result_review_handoff.json> --evidence-ref {ref} --once-json"
    )
    if material_pack_status == "ready_for_field_retest_material_collection_not_proven":
        commands.append("Collect the listed field_capture_checklist items before any result callback intake.")
    return [_safe_text(command) for command in commands]


def _safe_copy(
    material_pack_status: str,
    evidence_ref: str,
    checklist: list[dict[str, Any]],
    owner_work_orders: list[dict[str, Any]],
) -> dict[str, Any]:
    # safe_copy 是下游白名单，不包含 raw source、完整 artifact 或材料内容。
    return {
        "schema": f"{PACK_SUMMARY_SCHEMA}.safe_copy",
        "material_pack_status": material_pack_status,
        "status": material_pack_status,
        "evidence_boundary": PACK_BOUNDARY,
        "safe_evidence_ref": evidence_ref,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "required_materials": [item["material"] for item in checklist],
        "owner_work_orders": owner_work_orders,
        "not_proven": "not_proven",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_route_task_field_retest_material_pack_from_handoff(
    result_review_handoff_json: str,
    evidence_ref: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    """读取 result review handoff，生成现场材料包 artifact。"""
    payload, load_issue = _load_json(result_review_handoff_json)
    source = _find_source(payload) if payload else {}
    requested_ref = _safe_ref(evidence_ref)
    source_ref = _source_ref(source) if source else ""
    evidence_ref_out = requested_ref or source_ref
    handoff_status = _source_handoff_status(source) if source else ""
    same_ref = _same_ref_status(source) if source else {"status": "missing_evidence_ref"}
    upstream_orders = _source_owner_work_orders(source) if source else []
    upstream_requirements = _source_callback_requirements(source) if source else []
    upstream_commands = _source_rerun_commands(source) if source else []
    accepted_materials, missing_materials, rejected_materials = _source_material_lists(source) if source else ([], list(FIELD_CAPTURE_MATERIALS), [])
    unsafe = bool(payload) and _has_forbidden_copy(source)
    success_claim = bool(payload) and _has_success_claim(source)
    material_pack_status, status_reasons = _material_pack_status(
        load_issue,
        source,
        requested_ref,
        source_ref,
        handoff_status,
        same_ref,
        unsafe,
        success_claim,
    )
    checklist = _field_capture_checklist(material_pack_status, evidence_ref_out, upstream_requirements)
    callback_skeleton = _callback_payload_skeleton(evidence_ref_out, checklist)
    owner_work_orders = _owner_work_orders(material_pack_status, evidence_ref_out, upstream_orders, checklist)
    rerun_commands = _rerun_commands(material_pack_status, evidence_ref_out, upstream_commands)
    safe_copy = _safe_copy(material_pack_status, evidence_ref_out, checklist, owner_work_orders)
    handoff_completeness = {
        "required_count": len(FIELD_CAPTURE_MATERIALS),
        "accepted_count": 0,
        "accepted_materials": [],
        "missing_materials": [item["material"] for item in checklist],
        "rejected_materials": [],
        "is_complete": False,
    }
    summary = {
        "schema": PACK_SUMMARY_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "evidence_boundary": PACK_BOUNDARY,
        "boundary": PACK_BOUNDARY,
        "status": material_pack_status,
        "material_pack_status": material_pack_status,
        "material_pack_verdict": material_pack_status,
        "status_reasons": status_reasons,
        "source_schema": _safe_text(source.get("schema", "")) if source else "",
        "source_boundary": _source_boundary(source) if source else "",
        "source_handoff_status": handoff_status,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "field_capture_checklist": checklist,
        "callback_payload_skeleton": callback_skeleton,
        "owner_work_orders": owner_work_orders,
        "rerun_commands": rerun_commands,
        "operator_next_steps": rerun_commands,
        "materials": checklist,
        "material_completeness": handoff_completeness,
        "accepted_materials": accepted_materials,
        "missing_materials": missing_materials,
        "rejected_materials": rejected_materials,
        "safe_copy": safe_copy,
        "fail_closed_notes": [
            "This material pack is metadata-only and does not read field material directories.",
            "Keep not_proven, delivery_success=false, and primary_actions_enabled=false until real field evidence exists.",
        ],
        "not_proven": list(NOT_PROVEN),
        "evidence_boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = {
        "schema": PACK_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": PACK_BOUNDARY,
        "boundary": PACK_BOUNDARY,
        "status": material_pack_status,
        "material_pack_status": material_pack_status,
        "material_pack_verdict": material_pack_status,
        "status_reasons": status_reasons,
        "safe_evidence_ref": evidence_ref_out,
        "evidence_ref": evidence_ref_out,
        "same_evidence_ref_required": True,
        "source_result_review_handoff": {
            "load_issue": load_issue,
            "schema": _safe_text(source.get("schema", "")) if source else "",
            "evidence_boundary": _source_boundary(source) if source else "",
            "handoff_status": handoff_status,
            "safe_evidence_ref": source_ref,
            "unsafe_copy": bool(unsafe),
            "success_claim": bool(success_claim),
        },
        "field_capture_checklist": checklist,
        "callback_payload_skeleton": callback_skeleton,
        "owner_work_orders": owner_work_orders,
        "rerun_commands": rerun_commands,
        "operator_next_steps": rerun_commands,
        "accepted_materials": accepted_materials,
        "missing_materials": missing_materials,
        "rejected_materials": rejected_materials,
        "material_manifest": checklist,
        "material_pack_summary": summary,
        "safe_copy": safe_copy,
        "route_task_field_retest_material_pack_summary": summary,
        "robot_diagnostics_summary": summary,
        "mobile_readonly_summary": summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "field_material_directory",
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
            "browser",
            "robot_action",
            "field_retest_execution",
        ],
        "boundary_note": BOUNDARY_NOTE,
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    artifact = _safe_value(artifact)
    summary = _safe_value(summary)
    if _has_success_claim(artifact) or _has_success_claim(summary):
        # 最终防线只拦截动作/成功声明；not_proven 字段不参与提升。
        artifact["status"] = "unsupported_result_review_handoff_schema_not_proven"
        artifact["material_pack_status"] = "unsupported_result_review_handoff_schema_not_proven"
        artifact["material_pack_verdict"] = "unsupported_result_review_handoff_schema_not_proven"
        summary["status"] = "unsupported_result_review_handoff_schema_not_proven"
        summary["material_pack_status"] = "unsupported_result_review_handoff_schema_not_proven"
        summary["material_pack_verdict"] = "unsupported_result_review_handoff_schema_not_proven"
        artifact["route_task_field_retest_material_pack_summary"] = summary
        artifact["robot_diagnostics_summary"] = summary
        artifact["mobile_readonly_summary"] = summary
    return artifact, summary, 0


def build_route_task_field_retest_material_pack(
    material_dir: str = "",
    evidence_ref: str = "",
    result_review_handoff_json: str = "",
) -> tuple[dict[str, Any], dict[str, Any], int]:
    # 公共函数保持旧 material-dir 调用语义；handoff 只能显式 opt-in。
    if result_review_handoff_json:
        return build_route_task_field_retest_material_pack_from_handoff(result_review_handoff_json, evidence_ref)
    return _build_material_dir_pack(material_dir, evidence_ref)


def write_json(payload: dict[str, Any], output: str) -> None:
    # 指定输出时自动建目录；空路径表示只打印 stdout。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI dependency-free，便于 PC、Docker 和 unittest 直接复用。
    parser = argparse.ArgumentParser(description="Generate a route/task field retest material pack artifact")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--material-dir", help="directory containing eight route/task field retest materials")
    source.add_argument("--result-review-handoff-json", help="result review handoff artifact, summary, or wrapper/nested JSON")
    source.add_argument("--review-handoff-summary", help="alias of --result-review-handoff-json for summary inputs")
    parser.add_argument("--evidence-ref", default="", help="expected same evidence_ref for this material pack")
    parser.add_argument("--output", default="", help="optional material pack artifact JSON output path")
    parser.add_argument("--summary-output", default="", help="optional material pack summary JSON output path")
    parser.add_argument("--once-json", action="store_true", help="print material pack artifact JSON to stdout and exit")
    args = parser.parse_args()

    handoff_json = args.result_review_handoff_json or args.review_handoff_summary or ""
    artifact, summary, exit_code = build_route_task_field_retest_material_pack(
        args.material_dir or "",
        args.evidence_ref,
        result_review_handoff_json=handoff_json,
    )
    write_json(artifact, args.output)
    write_json(summary, args.summary_output)
    if args.once_json or not (args.output or args.summary_output):
        print(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route_task_field_retest_material_pack: artifact_file:{_safe_ref(args.output)}")
        if args.summary_output:
            print(f"material_pack_summary_file: {_safe_ref(args.summary_output)}")
        print(f"material_pack_verdict: {artifact['material_pack_verdict']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
