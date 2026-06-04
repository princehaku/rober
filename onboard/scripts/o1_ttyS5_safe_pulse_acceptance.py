#!/usr/bin/env python3
"""O1 /dev/ttyS5 短时点动验收 runner，默认只读 dry-run。"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# schema 固定后，现场 artifact 可以被 PC、OKR 和 sprint 留档稳定消费。
SCHEMA = "trashbot.o1.ttyS5_safe_pulse_acceptance.v1"
# 默认 base URL 指向 8787 上位 API；真实地址可由现场环境变量覆盖。
DEFAULT_BASE_URL = "http://127.0.0.1:8787"
# 本 runner 比 8787 API 自身更保守，现场点动只做短 pulse 采集材料。
DEFAULT_SPEED = 0.05
MAX_SPEED = 0.08
DEFAULT_DURATION_MS = 250
MAX_DURATION_MS = 350
DEFAULT_TIMEOUT_S = 3.0
DEFAULT_DIRECTION = "forward"
ALLOWED_DIRECTIONS = frozenset({"forward", "back", "left", "right", "stop"})

# vendor_sources 只代表本轮协议事实来源，不代表真实 HIL 已完成。
VENDOR_SOURCES = (
    "AGENTS.md",
    "OKR.md",
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h",
    "docs/interfaces/o7_upper_robot_api.md",
)

# 安全边界说明：本脚本默认只读 8787 status，不主动控制底盘。
# 安全边界说明：执行模式必须双确认，避免误把 dry-run 命令变成运动命令。
# 安全边界说明：本脚本不 import pyserial，避免绕过 8787 API guardrail。
# 安全边界说明：本脚本不打开 `/dev/ttyS5`，串口写入只允许由 8787 API 执行。
# 安全边界说明：本脚本不发送 ROS `/cmd_vel`，避免绕开当前 HTTP 安全边界。
# 安全边界说明：本脚本不发送 `T=130`，因为本轮目标不是反馈请求 probe。
# 安全边界说明：本脚本不发送 `T=131`，避免改变下位机 feedback flow 状态。
# 安全边界说明：执行模式只调用 `/api/base/manual`，让现有 API 负责自动停车。
# 安全边界说明：执行模式追加 `/api/base/stop`，是为了形成独立停车证据。
# 安全边界说明：即使 stop evidence 成功，也不能声明急停或 HIL 已通过。
# 安全边界说明：`safe_to_control` 固定 false，直到真实 ACK/HIL 材料补齐。
# 安全边界说明：`delivery_success` 固定 false，本脚本不参与真实送达任务。
# 安全边界说明：本地限幅比 8787 API 更保守，现场点动只服务短 pulse 取证。
# 安全边界说明：速度和时长先在 runner 限幅，再由 8787 API 二次限幅。
# 安全边界说明：HTTP 超时也是有效 blocker，不能为了成功率无限等待。
# 安全边界说明：非 JSON HTTP 响应必须结构化，避免现场日志只能人工猜。
# 安全边界说明：`--status-json` 用于消费既有材料，避免重复访问远端。
# 安全边界说明：`--output` 必须原子替换，避免半写 artifact 被 PC 误读。
# 安全边界说明：vendor_sources 是资料入口，不代表本轮完成真实硬件验证。
# 安全边界说明：status_summary 只摘要关键字段，不复制完整远端响应。
# 安全边界说明：T=1001 状态只从 8787 status 读取，不从串口现场猜测。
# 安全边界说明：执行参数出错时保持 fail-closed，不触发 fallback 控制。
# 安全边界说明：manual POST 失败后仍尝试 stop，优先降低现场残余风险。
# 安全边界说明：stop POST 失败也要写入 artifact，供现场继续排查。
# 安全边界说明：脚本输出单行 JSON，方便 SSH/stdin/pipe 收集。
# 安全边界说明：pretty 输出交给 `python3 -m json.tool`，脚本自身保持简单。
# 安全边界说明：本脚本是验收 runner，不是常驻服务或 UI 手控入口。
# 安全边界说明：现场执行前必须有人看护、车辆周边清空、电源切断路径可用。
# 安全边界说明：没有 CEO/现场授权时，只能运行默认 dry-run。
# 安全边界说明：任何网络或 API 异常都不应导致运动命令被补发。
# 安全边界说明：blocked_commands_not_sent 是审计字段，不是待发送队列。
# 安全边界说明：本脚本不推断轮向、速度标定、里程计或 IMU 单位。
# 安全边界说明：真实 O1 HIL 仍需要同源 T=1001、ROS topic 和 operator report。
# 安全边界说明：读取 camera/radar/base 只是材料汇总，不改变任何硬件状态。
# 安全边界说明：base.write_control_available 只代表 API 侧可写条件，不代表 ACK。
# 安全边界说明：HTTP 200 只代表 API 响应成功，不代表底盘已经安全动作。
# 安全边界说明：manual_command_executed 只来自 API JSON，不能替代 operator 观察。
# 安全边界说明：额外 stop 成功也不能替代物理急停按钮或断电路径。
# 安全边界说明：现场 artifact 必须和 operator 记录一起审查，不能单看脚本。
# 安全边界说明：任何 `T=1001` 结论都必须保持来源字段，避免混用历史材料。
# 安全边界说明：执行后必须再读一次 status，避免只看 manual 响应误判 ACK。
# 安全边界说明：acceptance_verdict 是机器合同，不让下游从 prose 猜结论。
# 安全边界说明：status/manual/stop 任一步失败都必须 fail-closed。
# 安全边界说明：operator report 只是人工观察材料，不能提升控制授权。
# 安全边界说明：operator report 缺失或不完整时，执行模式必须 fail-closed。
# 安全边界说明：dry-run 可携带 operator report，但仍然不能发送任何命令。
# 安全边界说明：operator report 不改变 safe_to_control，HIL 仍需 ACK/T=1001。
# 安全边界说明：evidence_ref 串起 status/manual/stop/post-status/report，防止现场材料散落。
# 安全边界说明：operator report 若声明了不同 evidence_ref，执行前必须阻断运动。
# 安全边界说明：执行模式必须显式绑定 operator report evidence_ref，缺失也要阻断。

# 默认模式必须显式列出禁止动作，避免 dry-run artifact 被误读成可控。
BLOCKED_COMMANDS_NOT_SENT = (
    {"command": {"T": 1}, "reason": "dry-run/status mode does not send wheel speed commands"},
    {"command": {"T": 13}, "reason": "ROS velocity command requires separate HIL validation"},
    {"command": {"T": 130}, "reason": "this runner observes API status and does not request serial feedback"},
    {"command": {"T": 131}, "reason": "feedback flow state changes are outside acceptance runner scope"},
    {"command": "cmd_vel", "reason": "runner uses 8787 API guardrail, never ROS cmd_vel directly"},
)

OPERATOR_REPORT_FIELDS = (
    "operator_present",
    "evidence_ref",
    "physical_clearance_confirmed",
    "emergency_stop_ready",
    "observed_motion",
    "observed_stop",
    "operator_notes",
    "reported_at",
)
OPERATOR_REPORT_PREFLIGHT_BOOL_FIELDS = (
    "operator_present",
    "physical_clearance_confirmed",
    "emergency_stop_ready",
)
OPERATOR_REPORT_REVIEW_BOOL_FIELDS = (
    "observed_motion",
    "observed_stop",
)
OPERATOR_REPORT_REQUIRED_REVIEW_TEXT_FIELDS = ("operator_notes", "reported_at")
OPERATOR_REPORT_GATE_STATUSES = frozenset({"ready_for_execution", "ready_for_review"})


def utc_now() -> str:
    """统一 UTC 时间，避免 PC 和 Orange Pi 时区不同导致材料难对齐。"""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def generated_evidence_ref(direction: str) -> str:
    """默认 ref 可直接进文件名和 operator report，不依赖现场人工临时命名。"""
    return f"o1-ttyS5-safe-pulse-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{direction}"


def normalize_evidence_ref(value: Any, direction: str) -> tuple[str, str]:
    """保守清洗 evidence_ref，避免空白或奇怪字符破坏 artifact 路径。"""
    raw = "" if value is None else str(value).strip()
    source = "provided" if raw else "generated"
    if not raw:
        raw = generated_evidence_ref(direction)
    safe = "".join(ch if (ch.isascii() and (ch.isalnum() or ch in {"-", "_", ".", ":", "@"})) else "-" for ch in raw)
    safe = safe.strip("-")[:160]
    return safe or generated_evidence_ref(direction), source


def clamp_float(value: float, minimum: float, maximum: float) -> float:
    """执行参数必须先本地限幅，再交给 8787 API 二次限幅。"""
    return min(max(value, minimum), maximum)


def clamp_int(value: int, minimum: int, maximum: int) -> int:
    """点动时长限幅保持整数毫秒，便于和 API 响应直接比对。"""
    return min(max(value, minimum), maximum)


def compact_error(error: BaseException) -> dict[str, str]:
    """错误只输出类型和短文本，避免把现场环境噪声写进 artifact。"""
    return {"type": type(error).__name__, "message": str(error)[:300]}


def coerce_bool(value: Any) -> bool | None:
    """人工报告可能来自表单或手写 JSON，这里只做保守布尔归一化。"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "on"}:
            return True
        if normalized in {"false", "0", "no", "n", "off"}:
            return False
    return None


def read_operator_report(path: str) -> dict[str, Any]:
    """读取 operator report；'-' 支持 SSH/stdin 管线现场补材料。"""
    text = Path(path).read_text(encoding="utf-8") if path != "-" else os.sys.stdin.read()
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("operator_report_json_must_be_object")
    return parsed


def normalize_operator_report(report: dict[str, Any] | None) -> tuple[dict[str, Any] | None, str]:
    """把人工报告分成执行前安全字段和执行后观察字段，避免流程倒置。"""
    if report is None:
        return None, "missing"
    normalized: dict[str, Any] = {}
    evidence_ref = report.get("evidence_ref")
    normalized["evidence_ref"] = str(evidence_ref).strip() if evidence_ref else None
    preflight_missing_or_invalid: list[str] = []
    review_missing_or_invalid: list[str] = []
    unsafe_fields: list[str] = []
    for field in OPERATOR_REPORT_PREFLIGHT_BOOL_FIELDS:
        value = coerce_bool(report.get(field))
        normalized[field] = value
        if value is None:
            preflight_missing_or_invalid.append(field)
        elif value is False:
            unsafe_fields.append(field)
    for field in OPERATOR_REPORT_REVIEW_BOOL_FIELDS:
        value = coerce_bool(report.get(field))
        normalized[field] = value
        if value is None:
            review_missing_or_invalid.append(field)
    notes = report.get("operator_notes")
    normalized["operator_notes"] = "" if notes is None else str(notes)
    reported_at = report.get("reported_at")
    normalized["reported_at"] = str(reported_at).strip() if reported_at else None
    for field in OPERATOR_REPORT_REQUIRED_REVIEW_TEXT_FIELDS:
        value = normalized.get(field)
        if not isinstance(value, str) or not value.strip():
            review_missing_or_invalid.append(field)
    status = "ready_for_execution"
    if preflight_missing_or_invalid or unsafe_fields:
        status = "unsafe_or_incomplete"
    elif not review_missing_or_invalid and all(normalized.get(field) is True for field in OPERATOR_REPORT_REVIEW_BOOL_FIELDS):
        status = "ready_for_review"
    normalized["normalization"] = {
        "source_fields": list(OPERATOR_REPORT_FIELDS),
        "preflight_required_fields": list(OPERATOR_REPORT_PREFLIGHT_BOOL_FIELDS),
        "review_required_fields": list(OPERATOR_REPORT_REVIEW_BOOL_FIELDS) + list(OPERATOR_REPORT_REQUIRED_REVIEW_TEXT_FIELDS),
        "missing_or_invalid_fields": preflight_missing_or_invalid + review_missing_or_invalid,
        "preflight_missing_or_invalid_fields": preflight_missing_or_invalid,
        "review_missing_or_invalid_fields": review_missing_or_invalid,
        "unsafe_fields": unsafe_fields,
    }
    return normalized, status


def load_operator_report(path: str | None) -> tuple[dict[str, Any] | None, str, dict[str, str] | None]:
    """报告解析失败也要落 artifact，不能让现场材料静默丢失。"""
    if not path:
        report, status = normalize_operator_report(None)
        return report, status, None
    try:
        report, status = normalize_operator_report(read_operator_report(path))
        return report, status, None
    except Exception as exc:  # noqa: BLE001 - JSON 材料坏了也要结构化反馈。
        return None, "unsafe_or_incomplete", compact_error(exc)


def parse_json_bytes(data: bytes) -> Any:
    """HTTP 响应必须是 JSON；非 JSON 响应转成结构化 blocker。"""
    return json.loads(data.decode("utf-8"))


def http_json(
    method: str,
    base_url: str,
    path: str,
    timeout_s: float,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """只通过 8787 API 访问硬件入口，不直连串口绕过 guardrail。"""
    url = base_url.rstrip("/") + path
    body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(url, data=body, method=method)
    request.add_header("Accept", "application/json")
    if body is not None:
        request.add_header("Content-Type", "application/json")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            raw = response.read()
            parsed = parse_json_bytes(raw) if raw else {}
            return {
                "ok": 200 <= int(response.status) < 300,
                "http_status": int(response.status),
                "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
                "json": parsed if isinstance(parsed, dict) else {"non_object_json": parsed},
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        # HTTP 4xx/5xx 仍可能携带有价值 JSON，保留给验收判断。
        raw = exc.read()
        parsed: Any
        try:
            parsed = parse_json_bytes(raw) if raw else {}
        except Exception as parse_exc:  # noqa: BLE001 - 这里要保留原始 HTTP 失败。
            parsed = {"parse_error": compact_error(parse_exc), "body_preview": raw[:200].decode("utf-8", "replace")}
        return {
            "ok": False,
            "http_status": int(exc.code),
            "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
            "json": parsed if isinstance(parsed, dict) else {"non_object_json": parsed},
            "error": compact_error(exc),
        }
    except Exception as exc:  # noqa: BLE001 - 网络不可达也要形成 fail-closed artifact。
        return {
            "ok": False,
            "http_status": None,
            "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
            "json": None,
            "error": compact_error(exc),
        }


def read_status_from_file(path: str) -> dict[str, Any]:
    """支持现场把已采集 status JSON 喂给 runner，避免重复访问远端。"""
    text = Path(path).read_text(encoding="utf-8") if path != "-" else os.sys.stdin.read()
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("status_json_must_be_object")
    return parsed


def summarize_status(status_payload: dict[str, Any] | None) -> dict[str, Any]:
    """把 8787 status 折成 O1 关心的 camera/radar/base 边界。"""
    camera = status_payload.get("camera", {}) if isinstance(status_payload, dict) else {}
    radar = status_payload.get("radar", {}) if isinstance(status_payload, dict) else {}
    base = status_payload.get("base", {}) if isinstance(status_payload, dict) else {}
    feedback_ack = base.get("feedback_ack", {}) if isinstance(base, dict) else {}
    return {
        "camera": {
            "status": camera.get("status"),
            "http_status": camera.get("http_status"),
            "video_source": camera.get("video_source"),
        },
        "radar": {
            "scan_status": radar.get("scan_status"),
            "observed_lidar_port": radar.get("observed_lidar_port"),
            "baudrate": radar.get("baudrate"),
        },
        "base": {
            "port": base.get("port"),
            "baudrate": base.get("baudrate"),
            "write_control_available": base.get("write_control_available"),
            "safe_to_control": base.get("safe_to_control"),
            "t1001_observed": feedback_ack.get("t1001_observed"),
            "robot_ack_connected": feedback_ack.get("robot_ack_connected"),
            "ack_reason": feedback_ack.get("reason"),
        },
    }


def t1001_status(summary: dict[str, Any]) -> str:
    """T=1001 状态必须机器可读，不能只靠文档 prose 判断。"""
    base = summary.get("base", {})
    if base.get("t1001_observed") is True:
        return "observed"
    if base.get("t1001_observed") is False:
        return "not_observed"
    return "unknown"


def http_result_ok(result: Any) -> bool:
    """HTTP 结果只接受显式 ok=true，避免错误 JSON 被当成功。"""
    return isinstance(result, dict) and result.get("ok") is True


def ack_observed_in_response(result: Any) -> bool:
    """manual 响应里的 ACK 只能作为辅助线索，最终仍要看 post status。"""
    if not isinstance(result, dict):
        return False
    body = result.get("json")
    if not isinstance(body, dict):
        return False
    ack = body.get("feedback_ack")
    if not isinstance(ack, dict):
        return False
    return bool(ack.get("t1001_observed") is True or ack.get("robot_ack_connected") is True)


def make_verdict(
    status: str,
    *,
    reason: str,
    failed_step: str | None = None,
    t1001_or_ack_observed: bool = False,
) -> dict[str, Any]:
    """统一生成 fail-closed verdict，避免各分支拼出不一致安全字段。"""
    fail_closed = status == "blocked_before_motion" or failed_step is not None
    return {
        "status": status,
        "safe_to_control": False,
        "hil_pass": False,
        "fail_closed": fail_closed,
        "failed_step": failed_step,
        "t1001_or_ack_observed": bool(t1001_or_ack_observed),
        "reason": reason,
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    """生成基础 payload；执行路径会在此基础上补 manual/stop evidence。"""
    speed = clamp_float(float(args.speed), 0.0, MAX_SPEED)
    duration_ms = clamp_int(int(args.duration_ms), 0, MAX_DURATION_MS)
    direction = str(args.direction).strip().lower()
    evidence_ref, evidence_ref_source = normalize_evidence_ref(args.evidence_ref, direction)
    # `--dry-run` 是最高优先级安全闸，即使用户误传 execute/confirm 也不能 POST。
    execution_authorized = bool(args.execute_motion and args.confirm_physical_clearance and not args.dry_run)
    if args.dry_run:
        gate_reason = "dry-run blocks execution even when execute/confirm flags are present"
    else:
        gate_reason = "requires --execute-motion and --confirm-physical-clearance together"
    operator_report, operator_report_status, operator_report_error = load_operator_report(args.operator_report_json)
    report_ref = operator_report.get("evidence_ref") if isinstance(operator_report, dict) else None
    if not report_ref:
        report_ref_status = "missing"
    elif report_ref == evidence_ref:
        report_ref_status = "matches"
    else:
        report_ref_status = "mismatch"
    return {
        "schema": SCHEMA,
        "version": 1,
        "generated_at": utc_now(),
        "vendor_sources": list(VENDOR_SOURCES),
        "evidence_ref": evidence_ref,
        "evidence_ref_source": evidence_ref_source,
        "same_evidence_ref_required": True,
        "operator_report_evidence_ref_status": report_ref_status,
        "evidence_chain": {
            "initial_status": evidence_ref,
            "manual_request": evidence_ref,
            "extra_stop": evidence_ref,
            "post_status": evidence_ref,
            "operator_report": evidence_ref,
        },
        "evidence_boundary": "api_status_dry_run_not_hil",
        "upper_api": {"base_url": args.base_url.rstrip("/"), "status_path": "/api/status"},
        "requested_motion": {
            "direction": direction,
            "speed": speed,
            "duration_ms": duration_ms,
            "max_speed": MAX_SPEED,
            "max_duration_ms": MAX_DURATION_MS,
        },
        "execution_gate": {
            "execute_motion": bool(args.execute_motion),
            "confirm_physical_clearance": bool(args.confirm_physical_clearance),
            "dry_run": bool(args.dry_run),
            "authorized": execution_authorized,
            "reason": gate_reason,
        },
        "safe_to_control": False,
        "sends_commands": False,
        "sends_motion_commands": False,
        "robot_control_executed": False,
        "delivery_success": False,
        "status_request": None,
        "status_summary": None,
        "t1001_feedback_status": "unknown",
        "manual_request": None,
        "manual_response": None,
        "stop_request": None,
        "stop_evidence": None,
        "post_status_request": None,
        "post_status_summary": None,
        "post_t1001_feedback_status": "unknown",
        "operator_report": operator_report,
        "operator_report_status": operator_report_status,
        "operator_report_error": operator_report_error,
        "acceptance_verdict": None,
        "blocked_commands_not_sent": list(BLOCKED_COMMANDS_NOT_SENT),
        "hardware_boundary": {
            # 这些字段给 PC/runner 消费，防止把底盘反馈缺口误当成雷达 POST 前置门。
            "t1001_feedback_material_only": True,
            "t1001_not_observed_is_not_ui_refreshable": True,
            "radar_start_stop_must_not_be_gated_by_base_t1001": True,
            "manual_base_control_requires_operator_env_ack_t1001_hil": True,
            "manual_base_control_remains_fail_closed_until_hil": True,
        },
        "next_required_checks": [
            "run_on_orange_pi_same_lan_status_dry_run",
            "confirm_operator_physical_clearance_before_execute_motion",
            "collect_t1001_or_ack_evidence_before_safe_to_control_true",
        ],
        "error": None,
    }


def run_acceptance(args: argparse.Namespace) -> dict[str, Any]:
    """执行一次验收采集；默认路径只读，执行路径必须双确认。"""
    payload = build_payload(args)
    status_payload: dict[str, Any] | None = None
    status_failed = False
    try:
        if args.status_json:
            status_payload = read_status_from_file(args.status_json)
            payload["status_request"] = {"source": "local_status_json", "ok": True, "path": args.status_json}
        else:
            status_result = http_json("GET", args.base_url, "/api/status", args.http_timeout_s)
            payload["status_request"] = status_result
            status_payload = status_result.get("json") if status_result.get("ok") else None
            status_failed = not http_result_ok(status_result)
        payload["status_summary"] = summarize_status(status_payload)
        payload["t1001_feedback_status"] = t1001_status(payload["status_summary"])
    except Exception as exc:  # noqa: BLE001 - status 解析失败也要继续输出 JSON。
        status_failed = True
        payload["error"] = compact_error(exc)
        payload["status_summary"] = summarize_status(None)

    if args.execute_motion and str(args.direction).strip().lower() not in ALLOWED_DIRECTIONS:
        payload["error"] = {"type": "invalid_direction", "message": f"direction must be one of {sorted(ALLOWED_DIRECTIONS)}"}
        payload["acceptance_verdict"] = make_verdict(
            "blocked_before_motion",
            failed_step="argument_validation",
            reason="invalid direction blocked before any motion POST",
        )
        return payload
    if status_failed and payload["execution_gate"]["authorized"]:
        payload["acceptance_verdict"] = make_verdict(
            "blocked_before_motion",
            failed_step="status_request",
            reason="initial status read failed; motion POST blocked fail-closed",
        )
        return payload
    if payload["execution_gate"]["authorized"] and payload["operator_report_status"] not in OPERATOR_REPORT_GATE_STATUSES:
        payload["acceptance_verdict"] = make_verdict(
            "blocked_before_motion",
            failed_step="operator_report_missing_or_incomplete",
            reason="execute mode requires safe preflight operator report; motion POST blocked fail-closed",
            t1001_or_ack_observed=payload["t1001_feedback_status"] == "observed",
        )
        return payload
    if payload["execution_gate"]["authorized"] and payload["operator_report_evidence_ref_status"] == "missing":
        payload["acceptance_verdict"] = make_verdict(
            "blocked_before_motion",
            failed_step="operator_report_evidence_ref_missing",
            reason="execute mode requires operator report evidence_ref to bind manual/stop/post-status evidence",
            t1001_or_ack_observed=payload["t1001_feedback_status"] == "observed",
        )
        return payload
    if payload["execution_gate"]["authorized"] and payload["operator_report_evidence_ref_status"] == "mismatch":
        payload["acceptance_verdict"] = make_verdict(
            "blocked_before_motion",
            failed_step="operator_report_evidence_ref_mismatch",
            reason="operator report evidence_ref must match the runner evidence_ref before motion POST",
            t1001_or_ack_observed=payload["t1001_feedback_status"] == "observed",
        )
        return payload
    if not payload["execution_gate"]["authorized"]:
        if status_failed:
            payload["acceptance_verdict"] = make_verdict(
                "dry_run_only" if args.dry_run else "blocked_before_motion",
                failed_step="status_request",
                reason="dry-run/status read failed; no motion POST was authorized",
            )
        else:
            payload["acceptance_verdict"] = make_verdict(
                "dry_run_only",
                reason="execution was not authorized; only status evidence was collected",
                t1001_or_ack_observed=payload["t1001_feedback_status"] == "observed",
            )
        if payload["operator_report_status"] != "missing":
            payload["acceptance_verdict"]["operator_report_status"] = payload["operator_report_status"]
        return payload

    manual_body = {
        "direction": payload["requested_motion"]["direction"],
        "speed": payload["requested_motion"]["speed"],
        "duration_ms": payload["requested_motion"]["duration_ms"],
        "evidence_ref": payload["evidence_ref"],
    }
    payload["evidence_boundary"] = "api_manual_short_pulse_with_extra_stop_not_hil"
    payload["manual_request"] = {"method": "POST", "path": "/api/base/manual", "json": manual_body}
    payload["sends_commands"] = True
    payload["sends_motion_commands"] = manual_body["direction"] != "stop"
    manual_result = http_json("POST", args.base_url, "/api/base/manual", args.http_timeout_s, manual_body)
    payload["manual_response"] = manual_result
    payload["robot_control_executed"] = bool(
        manual_result.get("json", {}).get("manual_command_executed") if isinstance(manual_result.get("json"), dict) else False
    )

    # manual endpoint 自带 auto-stop；这里再调用 stop 形成独立停车证据，失败也不能吞。
    stop_result = http_json("POST", args.base_url, "/api/base/stop", args.http_timeout_s, {})
    payload["stop_request"] = {
        "method": "POST",
        "path": "/api/base/stop",
        "evidence_ref": payload["evidence_ref"],
        "reason": "extra fail-closed stop evidence after manual pulse",
    }
    payload["stop_evidence"] = stop_result
    post_status_result = http_json("GET", args.base_url, "/api/status", args.http_timeout_s)
    post_status_payload = post_status_result.get("json") if post_status_result.get("ok") else None
    payload["post_status_request"] = post_status_result
    payload["post_status_summary"] = summarize_status(post_status_payload)
    payload["post_t1001_feedback_status"] = t1001_status(payload["post_status_summary"])

    t1001_or_ack = payload["post_t1001_feedback_status"] == "observed" or ack_observed_in_response(manual_result)
    if not http_result_ok(manual_result):
        payload["acceptance_verdict"] = make_verdict(
            "motion_posted_without_ack",
            failed_step="manual_request",
            reason="manual POST failed or was rejected; extra stop and post-status evidence were still attempted",
            t1001_or_ack_observed=t1001_or_ack,
        )
    elif not http_result_ok(stop_result):
        payload["acceptance_verdict"] = make_verdict(
            "motion_posted_without_ack",
            failed_step="stop_request",
            reason="manual POST returned ok but extra stop failed; keep fail-closed",
            t1001_or_ack_observed=t1001_or_ack,
        )
    elif not http_result_ok(post_status_result):
        payload["acceptance_verdict"] = make_verdict(
            "motion_posted_without_ack",
            failed_step="post_status_request",
            reason="manual and stop were attempted but post status read failed; ACK cannot be proven",
            t1001_or_ack_observed=t1001_or_ack,
        )
    elif t1001_or_ack:
        payload["acceptance_verdict"] = make_verdict(
            "motion_posted_with_t1001",
            reason="manual/stop completed and post-status or manual response reported T=1001/ACK; HIL packet still not complete",
            t1001_or_ack_observed=True,
        )
    else:
        payload["acceptance_verdict"] = make_verdict(
            "motion_posted_without_ack",
            reason="manual/stop completed but post-status did not report T=1001 or ACK",
            t1001_or_ack_observed=False,
        )
    payload["acceptance_verdict"]["operator_report_status"] = payload["operator_report_status"]
    return payload


def write_output_atomic(path: str, payload: dict[str, Any]) -> None:
    """artifact 原子替换，避免现场采集中断留下半写 JSON。"""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(target.parent), delete=False) as handle:
        handle.write(text)
        temp_name = handle.name
    os.replace(temp_name, target)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI 默认 dry-run；危险动作必须由两个显式参数共同打开。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("ROBER_UPPER_API_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--status-json", help="读取本地 /api/status JSON，避免访问网络；'-' 表示 stdin")
    parser.add_argument("--http-timeout-s", type=float, default=DEFAULT_TIMEOUT_S)
    parser.add_argument("--direction", default=DEFAULT_DIRECTION)
    parser.add_argument("--speed", type=float, default=DEFAULT_SPEED)
    parser.add_argument("--duration-ms", type=int, default=DEFAULT_DURATION_MS)
    parser.add_argument("--evidence-ref", help="同一现场证据包 ref；默认按 UTC 和 direction 生成")
    parser.add_argument("--execute-motion", action="store_true")
    parser.add_argument("--confirm-physical-clearance", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="兼容显式 dry-run 调用；默认已经是 dry-run")
    parser.add_argument("--operator-report-json", help="读取现场 operator report JSON；'-' 表示 stdin")
    parser.add_argument("--once-json", action="store_true", help="输出单次 JSON；保留该参数便于 runbook 稳定调用")
    parser.add_argument("--output", help="原子写入同一份 JSON artifact")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = run_acceptance(args)
    if args.output:
        write_output_atomic(args.output, payload)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
