#!/usr/bin/env python3
"""安全读取 WAVE ROVER 串口反馈，默认不发送，显式参数才请求一次 T=130。"""

from __future__ import annotations

import argparse
import json
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


def _decode_line(raw: bytes) -> str:
    """串口反馈可能夹杂坏字节，replace 能保留证据而不中断读取窗口。"""
    return raw.decode("utf-8", errors="replace").strip()


def _feedback_type(parsed: Any) -> str:
    """优先按 vendor `T` 字段归类；无 `T` 的 JSON 也不丢弃。"""
    if isinstance(parsed, dict) and "T" in parsed:
        return f"T={parsed['T']}"
    return "json_without_T"


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
