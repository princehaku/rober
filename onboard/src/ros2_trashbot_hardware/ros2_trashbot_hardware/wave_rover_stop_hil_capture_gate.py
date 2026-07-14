"""WAVE ROVER operator-gated stop HIL capture gate helper.

Vendor 来源：
- docs/vendor/VENDOR_INDEX.md
- docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py
- docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_config.h

本模块只生成 mock-only capture gate artifact；当前自动化没有现场 operator
approval，因此不会访问真实 HTTP endpoint、不会打开 UART、不会发布 ROS topic，
也不会把 fixture 反馈写成 HIL pass。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ros2_trashbot_hardware.wave_rover_feedback import parse_feedback_line


# 安全设计说明：
# 1. 本 helper 的首要目标是阻止误触真实机器人，而不是追求 live 控制便利性。
# 2. 当前自动化没有现场 operator approval，所以 live mode 必须被视为不可用。
# 3. `--mock` 只启用内存对象，不创建 socket，不导入 HTTP 客户端，不访问网络。
# 4. token gate 放在 mock stop 之前，是为了证明授权缺失时连 stop 形状都不会执行。
# 5. token 原文不写入 payload，是为了避免以后把 approval token 当作网络凭据传播。
# 6. mock stop 成功只说明调用路径可被程序记录，不说明实车接收了停车命令。
# 7. T=1001 fixture 成功只说明解析路径可用，不说明 ESP32 在当前窗口回传了反馈。
# 8. 固定 false 字段放在 artifact 顶层，方便 Product 和脚本直接断言。
# 9. `real_stop_endpoint_called=false` 与 `mock_http_stop_called=true` 必须同时出现。
# 10. `uses_real_uart=false` 明确本 helper 不会打开 `/dev/tty*` 或 Orange Pi 串口。
# 11. `nonzero_motion_command_sent=false` 明确本 helper 不携带任何 L/R/X/Z 运动轴。
# 12. `/api/base/manual` 被列为 forbidden，因为 manual endpoint 可能代表运动控制入口。
# 13. `/cmd_vel` 和 NavigateToPose 被列为 forbidden，避免硬件 gate 越界到算法执行。
# 14. fixture 解析必须复用现有 feedback parser，避免同一 T=1001 在项目内出现两套语义。
# 15. fixture 中坏 JSON 与坏 T=1001 必须 fail-closed，不能被后续好帧抵消。
# 16. `after_stop` phase 是 stop 后归零判定的语义锚点，避免启动前零速被误用。
# 17. artifact 的 blocked_reasons 保留顺序，便于后续 owner 按最早根因返工。
# 18. 输出 JSON 使用 sort_keys，确保 review 时能看到字段级别的稳定 diff。
# 19. 下一步 live 证据列表写入 artifact，防止下一轮重复包装 mock readiness。
# 20. 本模块不写 launch 参数，避免未 HIL 的默认值进入上车路径。
# 21. 本模块不修改 `wave_rover_protocol.py`，因为本轮不需要新增 UART 编码语义。
# 22. 本模块不新增 console_script；`python -m` 已满足当前自动化的 module entry。
# 23. 所有成功路径仍然保持 HIL、安全、路线和交付字段为 false。
# 24. 只有真实同窗口 stop call、UART frame、T=1001 和 HIL acceptance 才能改变这些字段。
# 25. 这些注释属于安全护栏，不是替代 vendor source 或现场证据。
# 26. mock HTTP 的成功响应不参与路线状态机，只用于证明请求 body 没有危险字段。
# 27. fixture 的 voltage/roll/pitch/yaw 只证明 parser 入口完整，不证明传感器标定。
# 28. blocked artifact 也会写出，方便 Product closeout 看到具体 fail-closed 原因。
# 29. CLI 返回码 4 代表 gate 未满足，不代表系统故障或硬件损坏。
# 30. 后续 live sprint 必须另建证据文件，不能直接复用本轮 mock artifact 当实测。

# schema 是 Product closeout 和后续验收脚本的主合同，不能随意改名。
# READY_STATUS 仍然包含 not_hil，防止 CLI exit 0 被误读成 live HIL pass。
# BLOCKED_STATUS 用于 token、mock mode、fixture 或 mock HTTP shape 任一不满足时 fail-closed。
SCHEMA = "trashbot.o1.current_stop_hil_capture_gate.v1"
PROOF_BOUNDARY = "software_proof_o1_live_stop_hil_capture_gate_mock_only"
READY_STATUS = "ready_for_mock_stop_hil_capture_gate_not_hil"
BLOCKED_STATUS = "blocked_stop_hil_capture_gate_fail_closed"
STOP_ENDPOINT = "/api/base/stop"
FORBIDDEN_MANUAL_ENDPOINT = "/api/base/manual"
MOCK_APPROVAL_TOKEN = "MOCK_APPROVED_STOP_ONLY"
DEFAULT_OUTPUT = (
    "sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/"
    "artifacts/hardware/stop_hil_capture_gate.json"
)
DEFAULT_FEEDBACK_FIXTURE = (
    "sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/"
    "artifacts/hardware/mock_t1001_feedback.json"
)

# vendor source list 必须写入 artifact，方便 reviewer 回查每个硬件事实来源。
# VENDOR_INDEX 是入口，base_ctrl.py 证明上位机 JSON 串口写法。
# config.yaml 证明 vendor app 命令 ID 与底盘配置来源。
# json_cmd.h/uart_ctrl.h 证明命令 ID 与 newline-delimited JSON 接收边界。
# movtion_module.h/ugv_config.h 证明底盘反馈、heartbeat 和底盘尺寸来自固件源码。
VENDOR_SOURCES = [
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_config.h",
]

# 顶层 false 字段是防误读护栏；mock stop 调用成功也不能翻成 safe-to-control。
# route/delivery/HIL 都依赖真实同窗口证据，本轮 fixture 只能证明解析路径可用。
# uses_real_uart=false 和 robot_control_executed=false 明确本 helper 没有触碰实车控制。
FIXED_FALSE_FIELDS = {
    "hil_pass": False,
    "safe_to_control": False,
    "route_execution_success": False,
    "delivery_success": False,
    "robot_control_executed": False,
    "nonzero_motion_command_sent": False,
    "uses_real_uart": False,
    "real_uart_opened": False,
    "manual_endpoint_called": False,
    "cmd_vel_published": False,
    "navigate_to_pose_sent": False,
    "nav2_controller_called": False,
    "real_stop_endpoint_called": False,
}

# 后续真正进入 live HIL 前必须补这些证据；列表写入 artifact 是为了避免下一轮重复包装。
# explicit_operator_approval 是安全门，current_live_stop_call 才能证明真实 endpoint 被调用。
# same_window_uart_zero_stop_frame_capture 与 post_stop_t1001_lr_zero 才能改变 HIL 相关结论。
NEXT_LIVE_REQUIRED_EVIDENCE = [
    "explicit_operator_approval",
    "current_live_stop_call",
    "same_window_uart_zero_stop_frame_capture",
    "post_stop_t1001_lr_zero",
    "hil_acceptance",
    "same_window_lidar_localization_tf_readiness",
    "current_live_nav2_controller_result",
    "delivery_operator_acceptance",
]


class MockStopHttpClient:
    """只记录 mock HTTP stop 调用形状，不发起网络请求。"""

    def __init__(self) -> None:
        # calls 是唯一副作用；没有 socket、requests 或 urllib，保证不会误触真实机器人 API。
        self.calls: list[dict[str, Any]] = []

    def post(self, path: str, json_body: dict[str, Any]) -> dict[str, Any]:
        """模拟 POST /api/base/stop，并返回本地 fake response。"""
        # mock client 仍然严格检查 path；一旦入口漂移，artifact 会 fail-closed。
        call = {
            "method": "POST",
            "path": path,
            "json_body": dict(json_body),
            "network_transport": "mock_in_memory_no_socket",
        }
        self.calls.append(call)
        return {"status_code": 200, "body": {"ok": True, "mock": True}}


def _utc_now() -> str:
    """生成稳定的 UTC ISO 时间戳，供 artifact 记录生成时刻。"""
    # 统一 Z 后缀，避免 macOS/Python 本地时区影响 JSON diff。
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _dedupe(items: list[str]) -> list[str]:
    """按首次出现顺序去重，保留最早 blocker 线索。"""
    # blocker 顺序对返工很重要，因此不用 set 直接打乱顺序。
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _load_feedback_records(fixture_path: Path) -> tuple[list[dict[str, str]], list[str]]:
    """读取 mock T=1001 fixture，兼容 frames 或 feedback_lines 两种简单形态。"""
    # fixture 是本轮唯一 feedback 来源；缺文件或坏 JSON 都必须 fail-closed。
    # 返回 records 而不是直接返回字符串，便于保留 after_stop phase。
    reasons: list[str] = []
    try:
        raw = json.loads(fixture_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [], ["mock_t1001_feedback_fixture_missing"]
    except json.JSONDecodeError as exc:
        return [], [f"mock_t1001_feedback_fixture_invalid_json:{exc.msg}"]

    records: list[dict[str, str]] = []
    if isinstance(raw, list):
        for line in raw:
            if isinstance(line, str):
                records.append({"phase": "after_stop", "line": line})
            else:
                reasons.append("mock_t1001_feedback_list_item_not_string")
    elif isinstance(raw, dict):
        frames = raw.get("feedback_frames", raw.get("frames", raw.get("feedback_lines", [])))
        if not isinstance(frames, list):
            reasons.append("mock_t1001_feedback_frames_not_list")
        else:
            for item in frames:
                if isinstance(item, str):
                    records.append({"phase": "after_stop", "line": item})
                elif isinstance(item, dict) and isinstance(item.get("line"), str):
                    records.append(
                        {
                            "phase": str(item.get("phase", "after_stop")),
                            "line": str(item["line"]),
                        }
                    )
                else:
                    reasons.append("mock_t1001_feedback_frame_missing_line")
    else:
        reasons.append("mock_t1001_feedback_fixture_root_not_object_or_list")

    if not records and not reasons:
        reasons.append("mock_t1001_feedback_fixture_empty")
    return records, _dedupe(reasons)


def _parse_t1001_feedback_fixture(fixture_path: Path) -> dict[str, Any]:
    """解析 fixture 中的 T=1001，并验证 after_stop L/R 归零。"""
    # parse_feedback_line 是项目已有的 T=1001 解析入口，避免本 helper 再造字段语义。
    # 这里先 JSON decode，是为了区分坏 JSON、非 T=1001 和 T=1001 字段缺失三类问题。
    # 非 T=1001 帧只计数不作为成功证据，因为 vendor 反馈帧类型必须精确命中。
    # 坏 JSON 或坏 T=1001 会进入 blocked_reasons，因为 fixture 本身已经不可审计。
    # after_stop L/R 必须严格等于 0；本轮没有容差概念，避免把接近零写成已停稳。
    # yaw 允许为 None，这沿用 `wave_rover_feedback.py` 对现场 `"null"` 的兼容处理。
    # voltage 只作为解析样本透传，不作为电池标定或供电健康证明。
    records, load_reasons = _load_feedback_records(fixture_path)
    parsed_samples: list[dict[str, Any]] = []
    reasons: list[str] = list(load_reasons)
    non_t1001_count = 0
    invalid_json_count = 0
    invalid_t1001_count = 0

    for index, record in enumerate(records):
        line = record["line"]
        try:
            raw_frame = json.loads(line.strip())
        except json.JSONDecodeError:
            invalid_json_count += 1
            reasons.append(f"mock_t1001_feedback_invalid_json_line_{index}")
            continue

        if not isinstance(raw_frame, dict) or raw_frame.get("T") != 1001:
            non_t1001_count += 1
            continue

        feedback = parse_feedback_line(line)
        if feedback is None:
            invalid_t1001_count += 1
            reasons.append(f"mock_t1001_feedback_invalid_t1001_line_{index}")
            continue

        # 只保留验收需要的安全字段，避免把 fixture 扩展成伪实时遥测。
        parsed_samples.append(
            {
                "phase": record["phase"],
                "left_speed": feedback["left_speed"],
                "right_speed": feedback["right_speed"],
                "roll": feedback["roll"],
                "pitch": feedback["pitch"],
                "yaw": feedback["yaw"],
                "voltage": feedback["voltage"],
                "vendor_frame": feedback["vendor_frame"],
            }
        )

    zero_after_stop = any(
        sample["phase"] == "after_stop"
        and sample["left_speed"] == 0
        and sample["right_speed"] == 0
        for sample in parsed_samples
    )
    if records and not parsed_samples:
        reasons.append("mock_t1001_feedback_no_valid_t1001_frame")
    if parsed_samples and not zero_after_stop:
        reasons.append("t1001_after_stop_lr_not_zero")

    return {
        "fixture_path": str(fixture_path),
        "fixture_used": bool(records) and not load_reasons,
        "observed_t1001_count": len(parsed_samples),
        "non_t1001_count": non_t1001_count,
        "invalid_json_count": invalid_json_count,
        "invalid_t1001_count": invalid_t1001_count,
        "after_stop_lr_zero": zero_after_stop,
        "samples": parsed_samples,
        "blocked_reasons": _dedupe(reasons),
    }


def _build_mock_stop_payload() -> dict[str, Any]:
    """生成 mock /api/base/stop body，只表达 stop 意图，不携带运动轴。"""
    # body 不记录 token 原文；token 只作为本地 gate，不应出现在 artifact 或网络 payload 中。
    # nonzero_motion_command_sent=false 是 payload 级别的防误读字段。
    return {
        "mode": "mock",
        "reason": "operator_gated_stop_hil_capture_gate",
        "nonzero_motion_command_sent": False,
        "manual_endpoint_called": False,
    }


def _validate_mock_stop_call(call: dict[str, Any] | None) -> tuple[dict[str, Any], list[str]]:
    """验证 mock HTTP stop 调用形状是否只命中 POST /api/base/stop。"""
    # shape validation 明确不等于真实 HTTP，network_transport 会固定为 mock_in_memory_no_socket。
    reasons: list[str] = []
    if call is None:
        return {"called": False, "shape_valid": False}, ["mock_http_stop_not_called"]

    body = call.get("json_body", {})
    if call.get("method") != "POST":
        reasons.append("mock_http_stop_method_not_post")
    if call.get("path") != STOP_ENDPOINT:
        reasons.append("mock_http_stop_path_not_api_base_stop")
    if call.get("network_transport") != "mock_in_memory_no_socket":
        reasons.append("mock_http_stop_transport_not_mock")
    if body.get("mode") != "mock":
        reasons.append("mock_http_stop_body_mode_not_mock")
    if body.get("nonzero_motion_command_sent") is not False:
        reasons.append("mock_http_stop_body_nonzero_guard_missing")
    if body.get("manual_endpoint_called") is not False:
        reasons.append("mock_http_stop_body_manual_guard_missing")

    return {
        "called": True,
        "shape_valid": not reasons,
        "method": call.get("method"),
        "path": call.get("path"),
        "network_transport": call.get("network_transport"),
        "json_body": body,
    }, _dedupe(reasons)


def build_stop_hil_capture_gate_artifact(
    *,
    mock: bool,
    operator_approval_token: str | None,
    feedback_fixture: Path,
    generated_at: str | None = None,
    http_client: MockStopHttpClient | None = None,
) -> dict[str, Any]:
    """生成 stop HIL capture gate artifact；只有 mock+token 正确才执行 mock stop。"""
    # token gate 是最前置安全门；缺 token 或错误 token 时连 mock stop 都不调用。
    # 真实 live 模式在本自动化中不可用，因此 mock=false 永远 fail-closed。
    # http_client 可注入，是为了单元测试能证明 token 失败时调用列表为空。
    # feedback_fixture 作为参数传入，是为了后续 live sprint 能替换输入而不改源码常量。
    # generated_at 可注入，是为了测试避免依赖当前时间。
    # mock_http_summary 默认 false，确保任何早退路径都不会留下成功假象。
    # t1001_summary 默认 false，确保 token 失败时不会误显示 fixture 已消费。
    reasons: list[str] = []
    generated_at = generated_at or _utc_now()
    token_valid = operator_approval_token == MOCK_APPROVAL_TOKEN
    mock_http_summary: dict[str, Any] = {"called": False, "shape_valid": False}
    t1001_summary: dict[str, Any] = {
        "fixture_path": str(feedback_fixture),
        "fixture_used": False,
        "observed_t1001_count": 0,
        "after_stop_lr_zero": False,
        "samples": [],
        "blocked_reasons": [],
    }

    if not mock:
        reasons.append("mock_mode_required_current_automation_has_no_live_operator")
    if not token_valid:
        reasons.append("operator_approval_token_missing_or_invalid")

    if mock and token_valid:
        # 只有通过 token gate 后才允许 mock stop；这里仍然只是内存调用，不访问真实网络。
        # response 也来自内存对象；status_code=200 仅用于验证调用形状，不代表远端响应。
        # call 从 client.calls 读取，避免 helper 私下构造一个未真实经过 mock client 的记录。
        client = http_client or MockStopHttpClient()
        response = client.post(STOP_ENDPOINT, _build_mock_stop_payload())
        call = client.calls[-1] if client.calls else None
        mock_http_summary, http_reasons = _validate_mock_stop_call(call)
        mock_http_summary["response"] = response
        reasons.extend(http_reasons)

        # stop 调用形状通过后才消费 fixture，保持“先 stop 后反馈”的语义顺序。
        t1001_summary = _parse_t1001_feedback_fixture(feedback_fixture)
        reasons.extend(t1001_summary["blocked_reasons"])

    status = READY_STATUS if not reasons else BLOCKED_STATUS
    artifact: dict[str, Any] = {
        "schema": SCHEMA,
        "generated_at": generated_at,
        "capture_gate_status": status,
        "proof_boundary": PROOF_BOUNDARY,
        "evidence_boundary": PROOF_BOUNDARY,
        "operator_approval_mode": "mock_token_only",
        "operator_approval_token_required": MOCK_APPROVAL_TOKEN,
        "operator_approval_token_valid": token_valid,
        "operator_approval_token_recorded": "not_recorded",
        "mock_mode": bool(mock),
        "stop_endpoint": STOP_ENDPOINT,
        "manual_endpoint_forbidden": FORBIDDEN_MANUAL_ENDPOINT,
        "mock_http_stop_called": mock_http_summary["called"],
        "mock_http_stop_call_shape_valid": mock_http_summary["shape_valid"],
        "mock_http_stop_call": mock_http_summary,
        "mock_t1001_feedback_fixture_used": t1001_summary["fixture_used"],
        "t1001_feedback_zero_after_stop_fixture": t1001_summary["after_stop_lr_zero"],
        "mock_t1001_feedback": t1001_summary,
        "no_motion_control_guard": [
            "no real /api/base/stop",
            "no /api/base/manual",
            "no /cmd_vel",
            "no NavigateToPose",
            "no Nav2 controller/BT",
            "no WAVE ROVER UART",
            "no nonzero motion",
        ],
        "vendor_sources": list(VENDOR_SOURCES),
        "vendor_source_summary": {
            "uart_json_framing": (
                "ugv_rpi/base_ctrl.py writes json.dumps(data) + newline as UTF-8; "
                "WAVE_ROVER_V0.9/uart_ctrl.h parses a complete JSON command on newline."
            ),
            "vendor_rpi_uart_reference": (
                "ugv_rpi/base_ctrl.py example uses /dev/ttyAMA0 at 115200 and comments "
                "/dev/serial0 at 115200; this helper does not hardcode an Orange Pi UART."
            ),
            "base_feedback_frame": "WAVE_ROVER_V0.9/json_cmd.h defines FEEDBACK_BASE_INFO as T=1001.",
            "stop_boundary": (
                "Current artifact validates mock POST /api/base/stop shape and fixture T=1001 L/R zero only; "
                "it is not a live ESP32 ACK or HIL acceptance."
            ),
        },
        "blocked_reasons": _dedupe(reasons),
        "next_live_required_evidence": list(NEXT_LIVE_REQUIRED_EVIDENCE),
        "fixed_false_field_summary": [
            "hil_pass=false",
            "safe_to_control=false",
            "route_execution_success=false",
            "delivery_success=false",
            "robot_control_executed=false",
            "nonzero_motion_command_sent=false",
            "uses_real_uart=false",
        ],
    }
    # 顶层布尔字段放最后更新，避免任何中间路径误把 success/safety 字段置 true。
    artifact.update(FIXED_FALSE_FIELDS)
    return artifact


def write_artifact(artifact: dict[str, Any], output: Path) -> None:
    """写出 JSON artifact；这是 CLI 的唯一文件副作用。"""
    # sort_keys 让验收 diff 稳定，ensure_ascii=False 保留中文文档可读性。
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """CLI entry：生成 operator-gated mock stop HIL capture gate artifact。"""
    # 不提供 live URL、串口或 ROS 参数，避免当前 automation 误触真实控制入口。
    parser = argparse.ArgumentParser(description="Build WAVE ROVER mock stop HIL capture gate artifact.")
    parser.add_argument("--mock", action="store_true", help="Use in-memory mock HTTP stop client only.")
    parser.add_argument(
        "--operator-approval-token",
        default=None,
        help="Required mock token; only MOCK_APPROVED_STOP_ONLY is accepted.",
    )
    parser.add_argument("--feedback-fixture", default=DEFAULT_FEEDBACK_FIXTURE, help="Mock T=1001 feedback fixture.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Path to write stop_hil_capture_gate.json.")
    args = parser.parse_args(argv)

    artifact = build_stop_hil_capture_gate_artifact(
        mock=args.mock,
        operator_approval_token=args.operator_approval_token,
        feedback_fixture=Path(args.feedback_fixture),
    )
    write_artifact(artifact, Path(args.output))
    print(
        json.dumps(
            {
                "artifact": args.output,
                "schema": artifact["schema"],
                "status": artifact["capture_gate_status"],
            },
            sort_keys=True,
        )
    )
    return 0 if artifact["capture_gate_status"] == READY_STATUS else 4


if __name__ == "__main__":
    raise SystemExit(main())
