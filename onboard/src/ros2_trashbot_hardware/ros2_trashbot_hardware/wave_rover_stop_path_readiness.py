"""WAVE ROVER current stop path readiness 离线证明。

Vendor 来源：
- docs/vendor/VENDOR_INDEX.md
- docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py
- docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_config.h

本模块只生成 mock/虚拟串口 readiness artifact；它不打开真实 UART、不发布
ROS topic、不调用 Nav2，也不把 stop path readiness 宣称为 HIL 或 safe-to-control。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ros2_trashbot_hardware.wave_rover_protocol import encode_json_command


# 这个 helper 是 HIL 前置证明，不参与任何线上控制链路。
# 所有字段优先服务 Product/OKR 验收脚本的机器读取。
# artifact 里即使出现 ready，也只表示 mock stop-only 合同成立。
# 真实串口、真实 ESP32 ACK、真实停车距离都必须留给后续 HIL。
# 本轮不写 launch 默认值，避免把未验证参数带进上车路径。
# 这里保留 /api/base/stop 字段，是为了证明 stop path 的入口选择。
# 这里禁止 /api/base/manual，是为了避免 readiness 被误读成手动运动授权。
SCHEMA = "trashbot.o1.current_stop_path_readiness.v1"
PROOF_BOUNDARY = "software_proof_o1_o3_current_stop_path_readiness_probe_only"
READY_STATUS = "ready_for_mock_stop_only_probe_not_hil"
BLOCKED_STATUS = "blocked_invalid_stop_path_readiness_probe"
STOP_ENDPOINT = "/api/base/stop"
FORBIDDEN_MANUAL_ENDPOINT = "/api/base/manual"
DEFAULT_OUTPUT = (
    "sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/"
    "artifacts/hardware/stop_path_readiness.json"
)

# vendor source 列表必须进入 artifact，后续审查才能追溯每个硬件事实。
# VENDOR_INDEX 是入口，base_ctrl.py 证明上位机 JSON 串口写法。
# config.yaml 证明 vendor app 的命令 ID 和基础配置来源。
# json_cmd.h 证明 T=1/T=11/T=13 的 vendor command ID。
# uart_ctrl.h 证明一行一 JSON 的固件接收边界。
# movtion_module.h 与 ugv_config.h 共同证明 heartbeat stop 的源码边界。
# 本 helper 不根据记忆补任何引脚、电压、设备名或速度单位。
VENDOR_SOURCES = [
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_config.h",
]

# 三条 zero-stop command plan 覆盖项目可能遇到的 vendor 控制入口。
# T=1 是左右速度控制，T=11 是 PWM 输入，T=13 是 ROS X/Z 控制。
# 所有运动轴固定为 0，方便后续脚本直接断言没有非零运动。
ZERO_STOP_COMMAND_PLAN = [
    {"T": 1, "L": 0, "R": 0},
    {"T": 11, "L": 0, "R": 0},
    {"T": 13, "X": 0, "Z": 0},
]

# guard 字符串保持人和机器都能读，避免 Product closeout 再做语义猜测。
# no /api/base/manual 防止把 stop readiness 和手动运动接口混在一起。
# no /cmd_vel 防止 ROS topic 被误认为本轮已经触发。
# no NavigateToPose 防止 Nav2 action 被误认为本轮已经执行。
# no real UART 防止 mock frame 被升级成实机串口证据。
# no nonzero motion 是本轮 fail-closed 的核心安全边界。
NO_MOTION_CONTROL_GUARD = [
    "no /api/base/manual",
    "no /cmd_vel",
    "no NavigateToPose",
    "no Nav2 controller/BT",
    "no real UART",
    "no nonzero motion",
]

# 这些 false 字段是 artifact 的防误读护栏。
# readiness 不能写成 safe_to_control，因为没有真实 HIL。
# hil_pass 不能为 true，因为没有当前 live 上车验收。
# route_execution_success 不能为 true，因为没有 Nav2/controller result。
# delivery_success 不能为 true，因为没有 delivery/operator acceptance。
# uses_real_uart 不能为 true，因为本轮只使用 mock virtual serial。
# nonzero_motion_command_sent 不能为 true，因为 command plan 全部为 zero-stop。
# 后续如果任何字段需要变更，必须由真实证据驱动，而不是代码默认值驱动。
FIXED_FALSE_FIELDS = {
    "manual_endpoint_called": False,
    "cmd_vel_published": False,
    "navigate_to_pose_called": False,
    "nav2_controller_called": False,
    "uses_real_uart": False,
    "real_uart_opened": False,
    "safe_to_control": False,
    "hil_pass": False,
    "route_execution_success": False,
    "delivery_success": False,
    "robot_control_executed": False,
    "nonzero_motion_command_sent": False,
}

# 下一步证据不是本轮验收条件，而是防止后续 sprint 重复包装 readiness。
# explicit operator approval 是 live HIL 前的人工安全门。
# current_live_stop_endpoint_invocation_record 证明真实 stop API 被调用。
# current_live_uart_frame_capture_for_zero_stop 证明真实串口帧发送。
# current_live_t1001_feedback_after_stop 证明 stop 后底盘反馈归零。
# same_window_lidar_localization_tf_readiness 证明路线执行前定位窗口有效。
# current_live_hil_acceptance_record 才能改变 HIL 相关字段。
# delivery_operator_acceptance_record 才能改变 delivery 相关字段。
NEXT_REQUIRED_EVIDENCE = [
    "explicit_operator_approval_for_current_live_stop_hil",
    "current_live_stop_endpoint_invocation_record",
    "current_live_uart_frame_capture_for_zero_stop",
    "current_live_t1001_feedback_after_stop",
    "same_window_lidar_localization_tf_readiness",
    "current_live_hil_acceptance_record",
    "current_live_nav2_controller_result",
    "delivery_operator_acceptance_record",
]


class MockVirtualSerial:
    """记录 UART bytes，避免 readiness probe 意外触碰真实串口设备。"""

    def __init__(self) -> None:
        # 保存 bytes 而不是字符串，便于验证一帧一换行的真实串口边界。
        # mock 串口没有设备路径，确保不会把 /dev/tty* 写进 artifact。
        self.frames: list[bytes] = []

    def write(self, frame: bytes) -> int:
        """模拟 pyserial.write，只接受 bytes 并返回写入长度。"""
        # 这里故意不支持 str，防止调用方绕过协议编码函数。
        # 返回写入长度是为了贴近 pyserial 行为，但不代表硬件 ACK。
        if not isinstance(frame, bytes):
            raise TypeError("mock virtual serial only accepts bytes")
        self.frames.append(frame)
        return len(frame)


def _command_axis_values(command: dict[str, Any]) -> list[float]:
    """提取运动轴字段；只检查 vendor stop plan 允许出现的运动字段。"""
    # 只检查 L/R/X/Z，是因为本轮 stop plan 不允许其他运动轴出现。
    # 非运动字段如 T 继续由 command type allowlist 检查。
    values: list[float] = []
    for key in ("L", "R", "X", "Z"):
        if key in command:
            values.append(float(command[key]))
    return values


def _json_frame_to_command(frame: bytes) -> dict[str, Any]:
    """把 mock UART frame 解析回 JSON object，用于证明输出可机读。"""
    # 固件 uart_ctrl.h 以 '\n' 作为完整 JSON 指令结束符，因此缺换行必须 fail-closed。
    # decode 后必须是 JSON object，数组或字符串都不能成为 UART command。
    if not frame.endswith(b"\n"):
        raise ValueError("uart frame must end with newline")
    parsed = json.loads(frame.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError("uart frame must decode to a JSON object")
    return parsed


def _validate_stop_contract(
    commands: list[dict[str, Any]],
    stop_endpoint: str,
    guard: list[str],
) -> tuple[bool, list[str]]:
    """集中校验 no-motion 合同，任何漂移都返回 blocked reason。"""
    # contract 层先检查 endpoint/guard，再检查 UART command plan。
    # 这样可以区分 API 边界漂移和底盘命令漂移，方便后续返工定位。
    blocked_reasons: list[str] = []
    if stop_endpoint != STOP_ENDPOINT:
        blocked_reasons.append("stop_endpoint_not_api_base_stop")

    # 本轮只允许 stop endpoint 出现在合同里，manual endpoint 只能作为禁止项出现。
    # guard 用字符串而不是 bool，是为了让 sprint rg 验收可以直接命中。
    joined_guard = " ".join(guard)
    if f"no {FORBIDDEN_MANUAL_ENDPOINT}" not in joined_guard:
        blocked_reasons.append("missing_no_api_base_manual_guard")
    if "no /cmd_vel" not in joined_guard:
        blocked_reasons.append("missing_no_cmd_vel_guard")
    if "no NavigateToPose" not in joined_guard:
        blocked_reasons.append("missing_no_navigate_to_pose_guard")

    # 命令必须恰好覆盖 T=1/T=11/T=13 的 zero-stop 形态，不能偷偷带非零运动轴。
    # required list 使用字面 JSON 形态，避免 0.0/0 或字段名漂移造成审查歧义。
    required = [
        {"T": 1, "L": 0, "R": 0},
        {"T": 11, "L": 0, "R": 0},
        {"T": 13, "X": 0, "Z": 0},
    ]
    for required_command in required:
        if required_command not in commands:
            blocked_reasons.append(f"missing_zero_stop_T_{required_command['T']}")

    for command in commands:
        # 任一 L/R/X/Z 非零都直接 blocked；本轮没有速度阈值或容差概念。
        if any(value != 0 for value in _command_axis_values(command)):
            blocked_reasons.append("nonzero_motion_axis_in_stop_plan")
        if command.get("T") not in (1, 11, 13):
            blocked_reasons.append("unexpected_command_type_in_stop_plan")

    return not blocked_reasons, _dedupe(blocked_reasons)


def _dedupe(items: list[str]) -> list[str]:
    """保持 blocker 顺序，避免 artifact 里出现重复噪声。"""
    # 按首次出现顺序保留原因，有利于定位最早触发的合同漂移。
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _build_frame_validation(commands: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """通过 mock/虚拟串口回放每条 zero-stop frame。"""
    # 这里刻意走 encode_json_command，而不是手写 JSON 字符串。
    # 这样 stop readiness 和现有 WAVE ROVER 协议编码保持同一实现来源。
    # mock virtual serial 只记录 bytes，不接触 serial.Serial 或设备节点。
    serial = MockVirtualSerial()
    blocked_reasons: list[str] = []
    validations: list[dict[str, Any]] = []

    for command in commands:
        # 每条 command 都必须通过协议层编码，证明 newline-delimited UTF-8 JSON 合同。
        frame = encode_json_command(command)
        serial.write(frame)

    for index, frame in enumerate(serial.frames):
        try:
            parsed = _json_frame_to_command(frame)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            # frame 解析失败时继续收集其它帧，artifact 可以显示全部问题。
            blocked_reasons.append(f"invalid_uart_frame_{index}:{exc}")
            continue

        axis_values = _command_axis_values(parsed)
        # 每帧都必须是纯 stop；虚拟串口只能证明编码和 guard，不能证明真实底盘停车。
        # bool(axis_values) 防止某帧完全缺少运动轴却被误判为 all([])=true。
        all_axes_zero = bool(axis_values) and all(value == 0 for value in axis_values)
        if not all_axes_zero:
            blocked_reasons.append(f"nonzero_or_missing_axis_in_frame_{index}")

        validations.append(
            {
                # frame_text 保留换行，便于人工核对固件一行一帧边界。
                "index": index,
                "command": parsed,
                "frame_text": frame.decode("utf-8"),
                "newline_terminated": frame.endswith(b"\n"),
                "json_object": isinstance(parsed, dict),
                "all_motion_axes_zero": all_axes_zero,
            }
        )

    return validations, _dedupe(blocked_reasons)


def build_current_stop_path_readiness_artifact(
    generated_at: str | None = None,
    commands: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """生成 current_stop_path_readiness artifact，不访问网络、ROS 或 UART。"""
    # 使用拷贝防止测试修改全局 plan 后污染后续用例或 CLI 输出。
    # generated_at 可注入，确保单元测试不依赖当前时间。
    command_plan = [dict(command) for command in (commands or ZERO_STOP_COMMAND_PLAN)]
    guard = list(NO_MOTION_CONTROL_GUARD)
    generated_at = generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    contract_ok, contract_reasons = _validate_stop_contract(command_plan, STOP_ENDPOINT, guard)
    frame_validation, frame_reasons = _build_frame_validation(command_plan)
    blocked_reasons = _dedupe(contract_reasons + frame_reasons)
    # 只要合同或 frame 有任何问题，状态就不能保持 ready。
    status = READY_STATUS if contract_ok and not frame_reasons else BLOCKED_STATUS

    artifact: dict[str, Any] = {
        "schema": SCHEMA,
        "generated_at": generated_at,
        "current_stop_path_readiness_status": status,
        "proof_boundary": PROOF_BOUNDARY,
        "stop_endpoint": STOP_ENDPOINT,
        "manual_endpoint_forbidden": FORBIDDEN_MANUAL_ENDPOINT,
        "zero_stop_command_plan": command_plan,
        "zero_stop_command_plan_summary": [
            # 这些 summary 字符串是给 rg 和人工 closeout 使用，不参与底盘控制。
            "T=1 speed control zero-stop {L=0,R=0}",
            "T=11 PWM input zero-stop {L=0,R=0}",
            "T=13 ROS control zero-stop {X=0,Z=0}",
        ],
        "mock_virtual_serial_validation": {
            # 聚合字段用于快速判断，frames 列表用于定位具体哪一帧坏了。
            "frame_count": len(frame_validation),
            "all_frames_newline_terminated": all(item["newline_terminated"] for item in frame_validation),
            "all_frames_json_objects": all(item["json_object"] for item in frame_validation),
            "all_motion_axes_zero": all(item["all_motion_axes_zero"] for item in frame_validation),
            "frames": frame_validation,
        },
        "no_motion_control_guard": guard,
        "vendor_sources": list(VENDOR_SOURCES),
        "vendor_source_summary": {
            # 这些是资料摘要，不是实测数据；heartbeat_boundary 会明确这一点。
            "uart_json_framing": (
                "base_ctrl.py writes json.dumps(data) + newline as UTF-8; "
                "uart_ctrl.h parses complete JSON when receivedChar == '\\n'."
            ),
            "vendor_rpi_uart_reference": (
                "base_ctrl.py example uses /dev/ttyAMA0 at 115200 and comments /dev/serial0 at 115200; "
                "Orange Pi device is not hardcoded by this helper."
            ),
            "zero_stop_vendor_commands": [
                "json_cmd.h CMD_SPEED_CTRL T=1 accepts L/R speed control.",
                "json_cmd.h CMD_PWM_INPUT T=11 accepts L/R PWM input.",
                "json_cmd.h CMD_ROS_CTRL T=13 accepts X/Z m/s and rad/s ROS control.",
            ],
            "heartbeat_summary": (
                "uart_ctrl.h/json_cmd.h refresh lastCmdRecvTime for T=1/T=11/T=13; "
                "ugv_config.h sets HEART_BEAT_DELAY=3000; "
                "movtion_module.h heartBeatCtrl calls setGoalSpeed(0,0) after timeout."
            ),
            "heartbeat_boundary": "source_readback_only_not_current_live_esp32_observation",
        },
        "blocked_reasons": blocked_reasons,
        # next_required_evidence 明确后续真正改变安全字段需要什么现场材料。
        "next_required_evidence": list(NEXT_REQUIRED_EVIDENCE),
        "fixed_false_field_summary": [
            # 字符串摘要辅助 rg；真正布尔字段会在 artifact.update 后写入顶层。
            # 这些文本不参与控制，只服务于自动验收和人工复盘。
            "safe_to_control=false",
            "hil_pass=false",
            "route_execution_success=false",
            "delivery_success=false",
            "robot_control_executed=false",
            "nonzero_motion_command_sent=false",
        ],
    }
    # 顶层 false 字段便于下游脚本直接 assert，不需要解析 summary 文本。
    artifact.update(FIXED_FALSE_FIELDS)
    return artifact


def write_artifact(artifact: dict[str, Any], output: Path) -> None:
    """写出可机读 JSON，并创建 sprint artifact 目录。"""
    # ensure_ascii=False 保留中文路径/说明的可读性；sort_keys 让 diff 和验收更稳定。
    # 写文件是本模块唯一副作用，且只写调用方显式传入的 artifact 路径。
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """CLI 入口：离线生成 stop path readiness artifact。"""
    # CLI 不提供串口参数，避免用户误以为本 helper 会连接真实 WAVE ROVER。
    parser = argparse.ArgumentParser(description="Build WAVE ROVER current stop path readiness artifact.")
    # --output 是唯一参数，限制 CLI 无法被误用成硬件 smoke runner。
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Path to write stop_path_readiness.json")
    args = parser.parse_args(argv)

    artifact = build_current_stop_path_readiness_artifact()
    write_artifact(artifact, Path(args.output))
    # stdout 只输出短 JSON，便于自动化从日志里拿到 status 和 artifact 路径。
    print(
        json.dumps(
            {
                "status": artifact["current_stop_path_readiness_status"],
                "artifact": args.output,
                "schema": artifact["schema"],
            },
            sort_keys=True,
        )
    )
    return 0 if artifact["current_stop_path_readiness_status"] == READY_STATUS else 4


if __name__ == "__main__":
    raise SystemExit(main())
