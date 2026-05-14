#!/usr/bin/env python3
"""生成 route/task field-run execution pack。

该工具只读取上一轮 review console JSON，把 operator 下一步转成现场联跑执行包。
它不访问 ROS graph、Nav2 runtime、硬件传输、外部云或任何真实机器人运行面。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# execution pack 是 review console 之后的现场执行契约，不能复用 review schema。
PACK_SCHEMA = "trashbot.route_task_field_run_execution_pack.v1"
PACK_SCHEMA_VERSION = 1
PACK_BOUNDARY = "software_proof_docker_route_task_field_run_execution_pack_gate"
REVIEW_SCHEMA = "trashbot.route_task_field_run_review_console.v1"
REVIEW_BOUNDARY = "software_proof_docker_route_task_field_run_review_console_gate"

# 这些材料是现场联跑要围绕同一 evidence_ref 采集的最小闭环。
FIELD_RUN_MATERIALS = (
    "route_status_json",
    "task_record_json",
    "nav2_or_fixed_route_runtime_log",
    "robot_side_task_evidence",
    "support_safe_mobile_summary",
    "pc_review_console_json",
)

# not_proven 明确把本地执行包和真实导航、硬件、投放、外部云证据隔开。
NOT_PROVEN = (
    "real_nav2_fixed_route_run",
    "real_route_capture",
    "real_robot_base_motion",
    "real_hardware_feedback",
    "real_hil_pass",
    "dropoff_completion",
    "cancel_completion",
    "delivery_success",
    "objective_5_external_cloud_or_4g_or_oss_cdn_or_db_queue_proof",
)

# phone-safe 输出不能带凭证、本机设备、控制 topic、完整 artifact 或底层平台细节。
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

# 脱敏覆盖常见凭证、DB/queue URL、控制 topic、设备路径、平台名和现场 raw 文本。
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
    (re.compile(r"(?i)WAVE\s+ROVER"), "[REDACTED_PLATFORM]"),
    (re.compile(r"(?i)Traceback \(most recent call last\):.*", re.DOTALL), "[REDACTED_TRACEBACK]"),
    (re.compile(r"(?i)\bchecksum\b\s*[:=]\s*[A-Fa-f0-9]{8,}"), "checksum=[REDACTED]"),
    (re.compile(r"(?i)complete artifact"), "[REDACTED_ARTIFACT]"),
    (re.compile(r"(?i)raw robot response"), "[REDACTED_RAW_RESPONSE]"),
)


def _utc_now() -> str:
    # UTC 时间戳便于不同 Docker/PC 主机上的执行包按字符串排序。
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any) -> str:
    # 所有自由文本统一脱敏，避免 review console 中的现场说明扩散敏感材料。
    text = str(value if value is not None else "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _safe_ref(value: Any) -> str:
    # 本机完整路径对现场交接没有价值，只保留 basename 降低泄露风险。
    text = _safe_text(value).strip()
    if not text:
        return ""
    path = Path(text)
    if path.name and (path.is_absolute() or "/" in text or "\\" in text):
        return f"file:{path.name}"
    return text


def _safe_list(value: Any, limit: int = 20) -> list[str]:
    # 兼容 review 里单字符串或数组两种形态，并限制数量避免复制完整 artifact。
    if isinstance(value, list):
        return [_safe_text(item) for item in value[:limit]]
    if value in (None, ""):
        return []
    return [_safe_text(value)]


def _safe_value(value: Any) -> Any:
    # 最终 manifest 再递归脱敏一次，防止新增字段绕过局部 helper。
    if isinstance(value, dict):
        return {str(_safe_text(k)): _safe_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_safe_value(item) for item in value]
    if isinstance(value, tuple):
        return [_safe_value(item) for item in value]
    if isinstance(value, str):
        return _safe_text(value)
    return value


def _has_forbidden_copy(value: Any) -> bool:
    # phone-safe 和 manifest 都用同一套关键词检查，新增字段也会被挡住。
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return any(token in encoded for token in FORBIDDEN_COPY)


def _load_json(path: str) -> tuple[dict[str, Any], str]:
    # 缺失、坏 JSON、非 object 都生成 blocked execution pack，而不是让现场只看到异常。
    if not path:
        return {}, "review_not_provided"
    try:
        with Path(path).expanduser().open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        return {}, "review_missing"
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}, "review_read_error"
    if not isinstance(payload, dict):
        return {}, "review_not_object"
    return payload, ""


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    # 只接受 object summary；其它形态不参与白名单消费。
    value = payload.get(key)
    return value if isinstance(value, dict) else {}


def _first_text(*values: Any, default: str = "") -> str:
    # review 可能来自 diagnostics nested summary，字段缺失时不猜测成功。
    for value in values:
        text = str(value if value is not None else "").strip()
        if text:
            return text
    return default


def _normalize_review(payload: dict[str, Any]) -> dict[str, Any]:
    # execution pack 只消费 review console 的白名单字段，不复制 raw intake 或路径。
    nested = _dict(payload, "route_task_field_run_review") or _dict(payload, "route_task_field_run_review_summary")
    source = payload if payload.get("schema") == REVIEW_SCHEMA else nested or payload
    phone = _dict(source, "phone_safe_summary")
    decision = _dict(source, "review_decision")
    return {
        "schema": _safe_text(source.get("schema", "")),
        "evidence_boundary": _safe_text(source.get("evidence_boundary", "")),
        "overall_status": _first_text(source.get("overall_status"), phone.get("status"), default="missing"),
        "review_decision": _first_text(decision.get("decision"), source.get("review_decision"), default="missing_review_decision"),
        "evidence_ref": _safe_ref(_first_text(source.get("evidence_ref"), phone.get("evidence_ref"), default="")),
        "same_evidence_ref_required": bool(source.get("same_evidence_ref_required", True)),
        "operator_next_steps": _safe_list(source.get("operator_next_steps") or phone.get("operator_next_steps")),
        "commands_to_rerun": _safe_list(source.get("commands_to_rerun") or phone.get("commands_to_rerun")),
        "not_proven": _safe_list(source.get("not_proven") or phone.get("not_proven")),
        "delivery_success": bool(source.get("delivery_success", False)),
        "primary_actions_enabled": bool(source.get("primary_actions_enabled", False)),
    }


def _source_status(load_issue: str, review: dict[str, Any]) -> dict[str, str]:
    # source_review 说明输入是否可信，不把 unsupported review 当成可执行现场包。
    if load_issue:
        return {"load_status": "blocked", "load_issue": load_issue, "schema_status": "not_loaded"}
    if review["schema"] == REVIEW_SCHEMA and review["evidence_boundary"] == REVIEW_BOUNDARY:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "supported"}
    if review["schema"] and review["schema"] != REVIEW_SCHEMA:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}
    if review["evidence_boundary"] and review["evidence_boundary"] != REVIEW_BOUNDARY:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}
    if review["overall_status"] != "missing" and review["evidence_ref"]:
        return {"load_status": "loaded", "load_issue": "", "schema_status": "compatible_summary"}
    return {"load_status": "loaded", "load_issue": "", "schema_status": "unsupported"}


def _overall_status(load_issue: str, schema_status: str, review_status: str, unsafe: bool) -> str:
    # 执行包状态必须先看输入可读性，再看 schema，再看安全，再看 review 是否 ready。
    if load_issue == "review_missing":
        return "blocked_missing_review"
    if load_issue:
        return "blocked_read_error"
    if schema_status == "unsupported":
        return "blocked_unsupported_schema"
    if unsafe:
        return "blocked_unsafe_review"
    if str(review_status).startswith("blocked"):
        return "blocked_review_not_ready"
    return "ready_for_field_run_execution_pack"


def _material_templates(evidence_ref: str) -> list[dict[str, Any]]:
    # 模板列出要采什么，不生成或访问真实运行材料。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        {
            "name": "route_status_json",
            "required_fields": ["schema_or_status", "evidence_ref", "route_progress_or_fixed_route_status"],
            "capture_note": f"Export the route status JSON for evidence_ref={ref}; keep delivery_success=false in review artifacts.",
        },
        {
            "name": "task_record_json",
            "required_fields": ["schema_or_task_id", "evidence_ref", "state_transition_history", "failure_code_or_result"],
            "capture_note": f"Export task record under evidence_ref={ref}; include failure reason when the run blocks.",
        },
        {
            "name": "nav2_or_fixed_route_runtime_log",
            "required_fields": ["evidence_ref", "start_time", "end_time", "runtime_events", "failure_reason"],
            "capture_note": f"Collect runtime log under evidence_ref={ref}; this pack does not read Nav2 runtime.",
        },
        {
            "name": "robot_side_task_evidence",
            "required_fields": ["evidence_ref", "task_id", "operator_action", "result_or_failure_reason"],
            "capture_note": f"Collect robot-side task evidence under evidence_ref={ref}; this pack remains software proof only.",
        },
        {
            "name": "support_safe_mobile_summary",
            "required_fields": ["status", "evidence_ref", "not_proven", "delivery_success"],
            "capture_note": "Share only phone-safe summary fields; do not include raw controls, credentials, local devices, or full artifacts.",
        },
        {
            "name": "pc_review_console_json",
            "required_fields": ["schema", "evidence_boundary", "operator_next_steps", "phone_safe_summary"],
            "capture_note": f"Use the review console JSON that produced this pack for evidence_ref={ref}.",
        },
    ]


def _field_run_manifest(status: str, evidence_ref: str, source_status: dict[str, str], review_status: str) -> dict[str, Any]:
    # manifest 是现场人员的总目录，明确本包只准备材料链，不证明实跑。
    return {
        "name": "route_task_field_run_execution_pack",
        "execution_state": "prepared_for_field_run" if status == "ready_for_field_run_execution_pack" else "blocked_until_review_repaired",
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "source_review": {
            **source_status,
            "overall_status": review_status,
        },
        "required_material_names": list(FIELD_RUN_MATERIALS),
        "boundary_note": "Docker/local software proof only; real navigation, hardware feedback, and delivery remain not_proven.",
    }


def _first_run_commands(evidence_ref: str) -> list[str]:
    # 命令清单保持可照抄的顺序，但不包含任何硬件、云或本机敏感参数。
    ref = evidence_ref or "<same_evidence_ref>"
    return [
        f"collect route_status_json with evidence_ref={ref}",
        f"collect task_record_json with evidence_ref={ref}",
        f"collect nav2_or_fixed_route_runtime_log with evidence_ref={ref}",
        f"collect robot_side_task_evidence with evidence_ref={ref}",
        f"collect support_safe_mobile_summary with evidence_ref={ref}",
        "run route_task_field_run_intake.py with the five field-run materials",
        "run route_task_field_run_review.py --intake-json <intake_report.json>",
        "run route_task_field_run_execution_pack.py --review-json <review_console.json>",
    ]


def _rerun_commands(evidence_ref: str, review_commands: list[str]) -> list[str]:
    # rerun 先保留 review 层修复提示，再追加本 gate 的重生成命令。
    ref = evidence_ref or "<same_evidence_ref>"
    commands = list(review_commands[:6])
    commands.extend(
        [
            f"rerun all field-run materials under the same evidence_ref={ref} when any source changes",
            "rerun route_task_field_run_intake.py after material repair",
            "rerun route_task_field_run_review.py --intake-json <intake_report.json>",
            "rerun route_task_field_run_execution_pack.py --review-json <review_console.json> --once-json",
            "keep delivery_success=false until real field evidence exists",
        ]
    )
    return commands


def _phone_summary(status: str, evidence_ref: str, review_decision: str, next_steps: list[str]) -> dict[str, Any]:
    # phone-safe summary 只暴露状态、ref、下一步计数和安全边界，不能复制完整 manifest。
    return {
        "schema": PACK_SCHEMA,
        "evidence_boundary": PACK_BOUNDARY,
        "status": status,
        "review_decision": review_decision,
        "evidence_ref": evidence_ref,
        "same_evidence_ref_required": True,
        "operator_next_steps": next_steps[:3],
        "not_proven": list(NOT_PROVEN),
        "ack_semantics": "execution_pack_only_not_delivery_success",
        "delivery_success": False,
        "primary_actions_enabled": False,
    }


def build_execution_pack(review_json: str) -> tuple[dict[str, Any], int]:
    review_payload, load_issue = _load_json(review_json)
    normalized = _normalize_review(review_payload) if review_payload else {
        "schema": "",
        "evidence_boundary": "",
        "overall_status": "missing",
        "review_decision": "missing_review",
        "evidence_ref": "",
        "operator_next_steps": [],
        "commands_to_rerun": [],
        "not_proven": [],
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    source = _source_status(load_issue, normalized)
    unsafe_source = bool(review_payload and _has_forbidden_copy(_safe_value(review_payload)))
    status = _overall_status(load_issue, source["schema_status"], normalized["overall_status"], unsafe_source)
    if normalized["delivery_success"] or normalized["primary_actions_enabled"]:
        status = "blocked_review_not_ready"

    first_run = _first_run_commands(normalized["evidence_ref"])
    rerun = _rerun_commands(normalized["evidence_ref"], normalized["commands_to_rerun"])
    phone_summary = _phone_summary(status, normalized["evidence_ref"], normalized["review_decision"], normalized["operator_next_steps"])
    if _has_forbidden_copy(phone_summary):
        status = "blocked_unsafe_review"
        phone_summary = _phone_summary(status, normalized["evidence_ref"], normalized["review_decision"], [])

    pack = {
        "schema": PACK_SCHEMA,
        "schema_version": PACK_SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "evidence_boundary": PACK_BOUNDARY,
        "overall_status": status,
        "evidence_ref": normalized["evidence_ref"],
        "same_evidence_ref_required": True,
        "field_run_manifest": _field_run_manifest(status, normalized["evidence_ref"], source, normalized["overall_status"]),
        "required_material_templates": _material_templates(normalized["evidence_ref"]),
        "first_run_commands": first_run,
        "rerun_commands": rerun,
        "operator_next_steps": normalized["operator_next_steps"],
        "source_review_decision": normalized["review_decision"],
        "phone_safe_summary": phone_summary,
        "not_proven": list(NOT_PROVEN),
        "non_access_scope": [
            "ros_graph",
            "nav2_runtime",
            "hardware_runtime",
            "external_cloud",
            "oss_cdn",
            "db_queue",
            "4g_network",
        ],
        "delivery_success": False,
        "primary_actions_enabled": False,
    }
    pack = _safe_value(pack)
    if _has_forbidden_copy(pack):
        # 最终防线只改变状态和风险列表；具体敏感词由测试暴露，避免静默误称 ready。
        pack["overall_status"] = "blocked_unsafe_review"
        pack["phone_safe_summary"]["status"] = "blocked_unsafe_review"
        pack["field_run_manifest"]["execution_state"] = "blocked_until_review_repaired"
    return pack, 0


def write_execution_pack(pack: dict[str, Any], output: str) -> None:
    # output 为空时只走 stdout；指定路径时创建父目录，方便 /tmp 验收。
    if not output:
        return
    target = Path(output).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(pack, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    # CLI 只读 review JSON；--once-json 用于 sprint 验收或 diagnostics fixture 直接消费。
    parser = argparse.ArgumentParser(description="Generate a route/task field-run execution pack manifest")
    parser.add_argument("--review-json", required=True, help="route_task_field_run_review console JSON path")
    parser.add_argument("--output", default="", help="optional execution pack JSON path")
    parser.add_argument("--once-json", action="store_true", help="print execution pack JSON to stdout and exit")
    args = parser.parse_args()

    pack, exit_code = build_execution_pack(args.review_json)
    write_execution_pack(pack, args.output)
    if args.once_json or not args.output:
        print(json.dumps(pack, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"route/task field-run execution pack: pack_file:{_safe_ref(args.output)}")
        print(f"overall_status: {pack['overall_status']}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
