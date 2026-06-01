#!/usr/bin/env python3
"""安全读取 WAVE ROVER 串口反馈，默认不发送，显式参数才请求一次 T=130。"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any


# 安全边界说明：本文件是材料采集脚本，不是控制脚本。
# 安全边界说明：默认串口动作只有 open、readline、close。
# 安全边界说明：只有显式 --request-base-feedback 才允许写一次 T=130。
# 安全边界说明：禁止 flush/reset buffer，因为丢弃输入也会影响证据完整性。
# 安全边界说明：禁止自动发送 T=130，避免主动查询被误读成 read-only。
# 安全边界说明：禁止 T=131，避免打开或关闭底盘反馈流。
# 安全边界说明：禁止 T=1/T=13，避免触发轮速或 ROS velocity 路径。
# 安全边界说明：串口路径必须由调用方传入，不能继承 Raspberry Pi 默认值。
# 安全边界说明：115200 只是 vendor Raspberry Pi reference 的 baudrate。
# 安全边界说明：Orange Pi 真实设备名只能由远端枚举和打开结果确认。
# 安全边界说明：serial_opened=true 只证明设备能打开，不证明它就是底盘。
# 安全边界说明：read_line_count=0 只证明窗口内无现成行，不证明无反馈能力。
# 安全边界说明：parsed_json_count>0 只证明读到了 JSON，不证明反馈语义正确。
# 安全边界说明：observed_feedback_types 只按 T 字段归类，不做单位标定判断。
# 安全边界说明：safe_to_control 必须永久为 false，T=130 也不代表可控制。
# 安全边界说明：sends_motion_commands 必须永久为 false，本脚本不碰运动。
# 安全边界说明：sends_commands 只表示是否发过显式 T=130 查询。
# 安全边界说明：delivery_success 必须永久为 false，本脚本不参与送达任务。
# 安全边界说明：pyserial 缺失必须输出 JSON blocker，不能让 SSH 采集中断。
# 安全边界说明：串口权限失败必须输出 JSON error，不能改权限绕过边界。
# 安全边界说明：远端运行采用 stdin，脚本不能依赖 repo checkout 或相对资源。
# 安全边界说明：输出不保存完整长日志，只保留截断预览供人工判读。
# 安全边界说明：vendor_sources 是资料来源，不代表本轮完成硬件验收。
# 安全边界说明：本脚本不 import ROS2，也不 source ROS 环境。
# 安全边界说明：本脚本不读取凭证、网络配置或非串口设备。
# 安全边界说明：异常路径也必须带完整 fail-closed 字段，方便自动审查。
# 安全边界说明：单测注入 fake serial 是为了证明实现没有默认写路径。
# 安全边界说明：真实 HIL 需要另行采集请求/反馈/停止/标定证据。
# 安全边界说明：本轮目标是把 upper-computer readiness 推进到串口材料。
# 安全边界说明：本轮不能把 serial-open 成功写成底盘可控或 HIL pass。
# 安全边界说明：T=130 查询必须由人工显式加参数，且只能发送一次。
# 安全边界说明：所有 blocked command 都只进入 JSON 列表，不进入发送队列。
# 安全边界说明：串口打开失败不能触发 fallback 控制命令。
# 安全边界说明：读取窗口结束后必须关闭句柄，避免影响人工 HIL。
# 安全边界说明：错误信息只记录异常文本，不追加系统敏感上下文。
# 安全边界说明：readline 空返回只表示当前超时周期无数据。
# 安全边界说明：JSON 解析失败计数保留，便于判断波特率或接线问题。
# 安全边界说明：本脚本不推断电压、引脚或线序，相关结论必须回到 vendor 文档。
# 安全边界说明：远端安装 pyserial 只属于运行依赖补齐，不属于 ROS 环境改造。
# 安全边界说明：设备清单只用 stat/glob/readlink 类只读动作，不调用 lsof/fuser。
# 安全边界说明：root_cause_hints 是定位提示，不把未验证硬件写成定论。
# 安全边界说明：t1001_feedback_status 是机器合同，不能靠读 prose 判断结果。
# 安全边界说明：next_required_checks 只列下一步检查项，不替代现场 HIL 结论。
# schema 固定后，远端只读材料可以被人工或脚本稳定比对。
SCHEMA_VERSION = "trashbot.o1.wave_rover_serial_feedback_probe.v1"
# 115200 来自 vendor Raspberry Pi reference；Orange Pi 设备名仍必须上机确认。
DEFAULT_BAUDRATE = 115200
# 默认窗口短，是为了只观察已有反馈，不把本脚本变成长时间占用串口的服务。
DEFAULT_READ_TIMEOUT_S = 2.0

# T=130 来自 vendor CMD_BASE_FEEDBACK；它是本脚本唯一允许的写入命令。
BASE_FEEDBACK_REQUEST_COMMAND = {"T": 130}

# vendor_sources 只列本轮实际依赖的硬件事实入口，不代表已经完成 HIL。
VENDOR_SOURCES = (
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
)

# 只枚举串口相关候选，避免 probe 扫描无关设备或产生隐私噪声。
DEVICE_CANDIDATE_GLOBS = (
    "/dev/ttyACM*",
    "/dev/ttyUSB*",
    "/dev/serial/by-id/*",
    "/dev/serial/by-path/*",
)

# 禁止列表显式进入输出，防止远端材料被误解为可以开始控制底盘。
BLOCKED_COMMANDS_NOT_SENT = (
    {
        "command": {"T": 1},
        "reason": "wheel speed command; not allowed in serial-open/read-only probe",
    },
    {
        "command": {"T": 13},
        "reason": "ROS velocity command; firmware behavior requires separate HIL",
    },
    {
        "command": {"T": 131},
        "reason": "feedback flow state change; not allowed in read-only probe",
    },
    {
        "command": "cmd_vel",
        "reason": "ROS motion command path is outside this probe boundary",
    },
)

# 检查项命名保持稳定，后续 automation 可以直接按字符串路由工单。
NEXT_CHECK_INSTALL_PYSERIAL = "install_pyserial_on_upper_computer"
NEXT_CHECK_SERIAL_OWNER = "check_serial_owner_process"
NEXT_CHECK_VERIFY_POWER_FIRMWARE = "verify_esp32_power_and_firmware"
NEXT_CHECK_VERIFY_UART_CROSSED = "verify_uart_tx_rx_crossed"
NEXT_CHECK_VERIFY_TARGET_PORT = "verify_target_port_is_wave_rover_esp32"
NEXT_CHECK_VENDOR_TERMINAL_T130 = "use_vendor_terminal_cross_check_t130"
NEXT_CHECK_FIRMWARE_BRANCH = "verify_wave_rover_cmd_base_feedback_firmware_branch"


def _utc_now() -> str:
    """统一使用 UTC，避免本地和远端时区差异影响证据判读。"""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_pyserial() -> tuple[bool, Any | None, str | None]:
    """只导入 pyserial 模块；导入失败必须转成结构化 JSON，而不是崩溃。"""
    try:
        import serial  # type: ignore
    except Exception as exc:  # pragma: no cover - 单测用注入路径覆盖缺失场景。
        return False, None, f"{exc.__class__.__name__}: {exc}"
    return True, serial, None


def _base_payload(
    port: str,
    baudrate: int,
    read_timeout_s: float,
    request_base_feedback: bool,
    argv: list[str],
) -> dict[str, Any]:
    """生成所有环境共享的 fail-closed 字段，避免错误路径漏掉安全口径。"""
    mode = "serial_open_t130_request_once" if request_base_feedback else "serial_open_read_only_once"
    return {
        "schema": SCHEMA_VERSION,
        "version": 1,
        "generated_at": _utc_now(),
        "vendor_sources": list(VENDOR_SOURCES),
        "evidence_boundary": "serial_open_t130_feedback_request_not_hil"
        if request_base_feedback
        else "serial_open_read_only_not_hil",
        "safe_to_control": False,
        "sends_commands": bool(request_base_feedback),
        "sends_motion_commands": False,
        "robot_control_executed": False,
        "delivery_success": False,
        "port": port,
        "baudrate": baudrate,
        "baudrate_source": "vendor Raspberry Pi reference 115200; Orange Pi port is caller-selected",
        "read_timeout_s": read_timeout_s,
        "pyserial": {"available": False, "module_name": "serial", "error": None},
        "device_inventory": _collect_device_inventory(port),
        "root_cause_hints": [],
        "t1001_feedback_status": "not_requested" if not request_base_feedback else "not_observed_after_t130",
        "next_required_checks": [],
        "serial_opened": False,
        "read_line_count": 0,
        "parsed_json_count": 0,
        "invalid_json_count": 0,
        "observed_feedback_types": [],
        "error": None,
        "feedback_request": {
            "enabled": bool(request_base_feedback),
            "sent": False,
            "command": BASE_FEEDBACK_REQUEST_COMMAND,
            "command_source": "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h CMD_BASE_FEEDBACK",
            "write_error": None,
        },
        "blocked_commands_not_sent": list(BLOCKED_COMMANDS_NOT_SENT),
        "raw_line_preview": [],
        "source": {
            "probe": "o1_wave_rover_serial_feedback_probe",
            "mode": mode,
            "argv": argv,
        },
    }


def _json_error(error_type: str, message: str) -> dict[str, str]:
    """错误结构保持短字段，方便 sprint 文档脱敏摘录。"""
    return {"type": error_type, "message": message}


def _describe_device(path: str) -> dict[str, Any]:
    """只读描述设备节点；符号链接坏掉也要能输出，而不是中断 probe。"""
    entry: dict[str, Any] = {
        "path": path,
        "lexists": False,
        "exists": False,
        "is_symlink": False,
        "realpath": None,
        "realpath_exists": False,
        "mode_octal": None,
        "uid": None,
        "gid": None,
        "error": None,
    }
    try:
        entry["lexists"] = os.path.lexists(path)
        entry["exists"] = os.path.exists(path)
        entry["is_symlink"] = os.path.islink(path)
        if entry["lexists"]:
            # realpath 让 by-id -> ttyACM/ttyUSB 的关系在远端 JSON 中直接可见。
            realpath = os.path.realpath(path)
            entry["realpath"] = realpath
            entry["realpath_exists"] = os.path.exists(realpath)
            stat_result = os.stat(path)
            entry["mode_octal"] = oct(stat_result.st_mode & 0o7777)
            entry["uid"] = stat_result.st_uid
            entry["gid"] = stat_result.st_gid
    except Exception as exc:
        entry["error"] = _json_error(exc.__class__.__name__, str(exc))
    return entry


def _collect_device_inventory(target_port: str) -> dict[str, Any]:
    """收集目标端口和常见候选串口，帮助区分端口缺失、错口和 by-id 链接问题。"""
    candidate_paths: set[str] = set()
    glob_counts: dict[str, int] = {}
    glob_errors: dict[str, dict[str, str]] = {}
    for pattern in DEVICE_CANDIDATE_GLOBS:
        try:
            matches = sorted(glob.glob(pattern))
            glob_counts[pattern] = len(matches)
            candidate_paths.update(matches)
        except Exception as exc:
            # glob 理论上很少失败，但远端环境异常时也不应影响串口安全边界。
            glob_counts[pattern] = 0
            glob_errors[pattern] = _json_error(exc.__class__.__name__, str(exc))

    candidate_paths.add(target_port)
    candidates = [_describe_device(path) for path in sorted(candidate_paths)]
    return {
        "target_port": _describe_device(target_port),
        "candidate_globs": list(DEVICE_CANDIDATE_GLOBS),
        "candidate_glob_counts": glob_counts,
        "candidate_glob_errors": glob_errors,
        "candidate_ports": candidates,
    }


def _decode_line(raw: bytes) -> str:
    """串口反馈可能夹杂坏字节，replace 能保留证据而不中断读取窗口。"""
    return raw.decode("utf-8", errors="replace").strip()


def _feedback_type(parsed: Any) -> str:
    """优先按 vendor `T` 字段归类；无 `T` 的 JSON 也不丢弃。"""
    if isinstance(parsed, dict) and "T" in parsed:
        return f"T={parsed['T']}"
    return "json_without_T"


def _apply_root_cause_hints(payload: dict[str, Any]) -> None:
    """把 probe 结果折成稳定 hints，便于 automation 不再只重复 read_line_count=0。"""
    hints: list[str] = []
    target_port = payload.get("device_inventory", {}).get("target_port", {})
    error = payload.get("error")
    observed_types = set(payload.get("observed_feedback_types", []))
    feedback_request = payload.get("feedback_request", {})

    if not target_port.get("exists"):
        hints.append("target_port_missing")
    if not payload.get("pyserial", {}).get("available"):
        hints.append("pyserial_missing")
    if error and error.get("type") != "pyserial_unavailable" and not payload.get("serial_opened"):
        hints.append("serial_open_failed")
    if feedback_request.get("write_error"):
        hints.append("t130_write_failed")
    if "T=1001" in observed_types:
        hints.append("t1001_observed")
    elif payload.get("parsed_json_count", 0) > 0:
        hints.append("json_seen_without_t1001_check_target_port_or_firmware")
    if payload.get("invalid_json_count", 0) > 0:
        hints.append("invalid_json_seen_check_baudrate_or_line_framing")
    if (
        feedback_request.get("enabled")
        and feedback_request.get("sent")
        and payload.get("serial_opened")
        and payload.get("read_line_count") == 0
        and error is None
    ):
        hints.append("no_serial_lines_after_t130_check_wiring_firmware_or_wrong_port")
    elif (
        not feedback_request.get("enabled")
        and payload.get("serial_opened")
        and payload.get("read_line_count") == 0
        and error is None
    ):
        hints.append("no_serial_lines_read_only_maybe_feedback_not_streaming")

    payload["root_cause_hints"] = hints or ["probe_completed_without_specific_hint"]


def _apply_t1001_diagnostic_contract(payload: dict[str, Any]) -> None:
    """生成稳定诊断合同，避免 automation 只能二次解析 root_cause_hints。"""
    checks: list[str] = []
    observed_types = set(payload.get("observed_feedback_types", []))
    feedback_request = payload.get("feedback_request", {})
    error = payload.get("error")

    if "T=1001" in observed_types:
        payload["t1001_feedback_status"] = "observed"
        payload["next_required_checks"] = []
        return

    if not payload.get("pyserial", {}).get("available"):
        payload["t1001_feedback_status"] = "pyserial_unavailable"
        payload["next_required_checks"] = [NEXT_CHECK_INSTALL_PYSERIAL]
        return

    if not payload.get("serial_opened"):
        payload["t1001_feedback_status"] = "serial_not_opened"
        checks.extend([NEXT_CHECK_VERIFY_TARGET_PORT, NEXT_CHECK_SERIAL_OWNER])
        payload["next_required_checks"] = checks
        return

    if not feedback_request.get("enabled"):
        payload["t1001_feedback_status"] = "not_requested"
        checks.extend([NEXT_CHECK_VENDOR_TERMINAL_T130, NEXT_CHECK_VERIFY_TARGET_PORT])
        payload["next_required_checks"] = checks
        return

    if feedback_request.get("write_error") or error:
        payload["t1001_feedback_status"] = "not_observed_after_t130"
        checks.extend([NEXT_CHECK_SERIAL_OWNER, NEXT_CHECK_VERIFY_TARGET_PORT])
        payload["next_required_checks"] = checks
        return

    payload["t1001_feedback_status"] = "not_observed_after_t130"
    checks.extend(
        [
            NEXT_CHECK_VERIFY_POWER_FIRMWARE,
            NEXT_CHECK_VERIFY_UART_CROSSED,
            NEXT_CHECK_VERIFY_TARGET_PORT,
            NEXT_CHECK_SERIAL_OWNER,
            NEXT_CHECK_VENDOR_TERMINAL_T130,
            NEXT_CHECK_FIRMWARE_BRANCH,
        ]
    )
    payload["next_required_checks"] = checks


def _write_base_feedback_request(serial_obj: Any) -> None:
    """只发送 vendor T=130 查询；集中封装可以防止未来误混入运动字段。"""
    encoded = (json.dumps(BASE_FEEDBACK_REQUEST_COMMAND, separators=(",", ":")) + "\n").encode("utf-8")
    serial_obj.write(encoded)


def run_probe(
    port: str,
    baudrate: int,
    read_timeout_s: float,
    request_base_feedback: bool = False,
    argv: list[str] | None = None,
    serial_module: Any | None = None,
    serial_import_error: str | None = None,
) -> dict[str, Any]:
    """打开串口后只读已有行；函数注入 serial_module 是为了证明单测不会写串口。"""
    payload = _base_payload(port, baudrate, read_timeout_s, request_base_feedback, argv or [])
    if serial_module is None:
        available, serial_module, import_error = _load_pyserial()
    else:
        # 单测注入模块时仍按 pyserial 可用处理，避免依赖本机环境。
        available, import_error = True, serial_import_error

    payload["pyserial"]["available"] = available
    payload["pyserial"]["error"] = import_error
    if not available:
        # pyserial 缺失是环境 blocker，不应该让远端 stdin 采集直接异常退出。
        payload["error"] = _json_error("pyserial_unavailable", import_error or "pyserial is not importable")
        _apply_root_cause_hints(payload)
        _apply_t1001_diagnostic_contract(payload)
        return payload

    serial_obj = None
    observed_types: set[str] = set()
    deadline = time.monotonic() + max(0.0, read_timeout_s)
    # 每次 readline 最多阻塞 0.2s，确保整体 read-timeout 接近用户传入值。
    serial_timeout = min(0.2, max(0.01, read_timeout_s))

    try:
        # 默认只 open/read/close；显式请求时只允许写一次 vendor T=130。
        serial_obj = serial_module.Serial(port=port, baudrate=baudrate, timeout=serial_timeout)
        payload["serial_opened"] = True
        if request_base_feedback:
            try:
                # 这是唯一允许的写入点；T=130 不带速度、转向或 feedback-flow 状态。
                _write_base_feedback_request(serial_obj)
                payload["feedback_request"]["sent"] = True
            except Exception as exc:
                # 写入失败仍继续读窗口，便于判断设备是否有被动反馈或错误回显。
                payload["feedback_request"]["write_error"] = _json_error(exc.__class__.__name__, str(exc))
        while time.monotonic() < deadline:
            raw = serial_obj.readline()
            if not raw:
                continue
            line = _decode_line(raw)
            if not line:
                continue
            payload["read_line_count"] += 1
            # raw_line_preview 截断保守保留，辅助判断是否是 JSON feedback 而不保存长日志。
            if len(payload["raw_line_preview"]) < 5:
                payload["raw_line_preview"].append(line[:160])
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                payload["invalid_json_count"] += 1
                continue
            payload["parsed_json_count"] += 1
            observed_types.add(_feedback_type(parsed))
    except Exception as exc:
        # 串口不存在、权限不足、设备忙都保留为结构化 error，安全字段仍为 false。
        payload["error"] = _json_error(exc.__class__.__name__, str(exc))
    finally:
        if serial_obj is not None:
            try:
                serial_obj.close()
            except Exception as exc:
                # close 失败不改变 open/read-only 证据，但必须暴露给下一轮排查。
                payload["close_error"] = _json_error(exc.__class__.__name__, str(exc))

    payload["observed_feedback_types"] = sorted(observed_types)
    _apply_root_cause_hints(payload)
    _apply_t1001_diagnostic_contract(payload)
    return payload


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    # --once-json 保持和上一轮 readiness probe 一致，适合 SSH stdin 采集。
    parser.add_argument("--once-json", action="store_true", help="print one JSON payload and exit")
    parser.add_argument(
        "--request-base-feedback",
        action="store_true",
        help="send exactly one vendor CMD_BASE_FEEDBACK request (T=130) before reading",
    )
    # port 必须由调用方选择，避免把 Raspberry Pi reference 当 Orange Pi 默认值。
    parser.add_argument("--port", required=True, help="serial device to open read-only")
    parser.add_argument("--baudrate", type=int, default=DEFAULT_BAUDRATE, help="serial baudrate")
    parser.add_argument("--read-timeout-s", type=float, default=DEFAULT_READ_TIMEOUT_S, help="read window seconds")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    effective_argv = sys.argv[1:] if argv is None else argv
    args = parse_args(effective_argv)
    # 默认行为与 --once-json 相同；没有任何后台循环或控制路径。
    payload = run_probe(
        port=args.port,
        baudrate=args.baudrate,
        read_timeout_s=args.read_timeout_s,
        request_base_feedback=args.request_base_feedback,
        argv=effective_argv,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
