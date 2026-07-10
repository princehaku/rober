"""WAVE ROVER same-session wheel feedback material intake。

Vendor 来源：
- docs/vendor/VENDOR_INDEX.md
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h
- docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h
- docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py
- docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml

本模块只做历史材料 intake：
- 消费上位机 same-session manual artifact；
- 只输出脱敏摘要，不回显串口、baudrate、endpoint 或 raw payload；
- 固定 HIL、安全、交付和主动作字段为 false。
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

from ros2_trashbot_hardware.wave_rover_feedback import parse_feedback_line


SCHEMA = "trashbot.wave_rover_same_session_wheel_feedback_material.v1"
EXPECTED_INPUT_SCHEMA = "trashbot.upper_robot_api.v1.base_manual_result"
PROOF_SCOPE = "software_proof_o1_same_session_wheel_feedback_material_intake_only"
READY_STATUS = "same_session_wheel_feedback_material_ready_not_delivery_proof"
BLOCKED_INVALID_STATUS = "blocked_invalid_same_session_wheel_feedback_material"
# next evidence 明确指向“新同 run 材料”，避免历史 artifact 被误当作 current HIL。
NEXT_REQUIRED_EVIDENCE = [
    "current_live_same_run_feedback_T1001_log",
    "current_live_same_run_motion_command_record",
    "current_live_operator_or_external_motion_observation",
    "current_live_hil_acceptance_record",
]
# vendor sources 只列相对路径，既满足可追溯，又不会泄露本机绝对路径。
VENDOR_SOURCES = [
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml",
]
# source ref 保留仓库相对路径，方便复验历史材料，同时不输出 CLI 输入的绝对路径。
HISTORICAL_SOURCE_REF = (
    "sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/artifacts/"
    "01_upper_manual_samesession_012.json"
)
# 四个字段永远由 intake 覆盖为 false，输入 artifact 不能提升安全状态。
FALSE_SAFETY_FIELDS = {
    "hil_pass": False,
    "safe_to_control": False,
    "delivery_success": False,
    "primary_actions_enabled": False,
}
# 只把真正会越界的 safety 字段视为 dangerous true；manual_command_executed 可是历史事实。
DANGEROUS_TRUE_FIELDS = frozenset(FALSE_SAFETY_FIELDS)
SECRET_KEY_PATTERN = re.compile(r"(token|secret|password|authorization|credential)", re.IGNORECASE)
# 输入可包含串口上下文但摘要不能回显；URL、用户绝对路径和 traceback 直接 fail-closed。
UNSAFE_VALUE_PATTERN = re.compile(
    r"(https?://|/Users/|Traceback \(most recent call last\)|bearer\s+|[A-Za-z0-9+/]{80,}={0,2})",
    re.IGNORECASE,
)


def _safe_base_summary(status: str, blocked_reasons: list[str], artifact_path: str | Path | None) -> dict[str, Any]:
    """构造固定 false 的安全摘要骨架。"""
    # 路径只保留 basename，避免 CLI 传入临时绝对路径时把本机路径写进合同。
    artifact_name = Path(artifact_path).name if artifact_path is not None else Path(HISTORICAL_SOURCE_REF).name
    return {
        "schema": SCHEMA,
        "status": status,
        "proof_scope": PROOF_SCOPE,
        "source_refs": {
            # artifact_name 只保留 basename，用于区分临时 smoke 输入而不泄露目录。
            "historical_artifact": HISTORICAL_SOURCE_REF,
            "artifact_name": artifact_name,
            "artifact_kind": "upper_robot_api_same_session_manual_result",
        },
        "vendor_sources": list(VENDOR_SOURCES),
        # 下列 material flags 默认 false，只有完整阶段链路通过后才逐项置真。
        "same_session_material_present": False,
        "motion_command_present": False,
        "feedback_request_present": False,
        "wheel_feedback_material_present": False,
        "stop_zero_readback_present": False,
        "latest_nonzero_pair": None,
        "counts": {
            "motion_window_t1001_count": 0,
            "motion_window_nonzero_pair_count": 0,
            "after_stop_t1001_count": 0,
            "after_stop_zero_pair_count": 0,
        },
        "blocked_reasons": blocked_reasons,
        "next_required_evidence": list(NEXT_REQUIRED_EVIDENCE),
        **FALSE_SAFETY_FIELDS,
    }


def _blocked(
    blocked_reasons: list[str],
    artifact_path: str | Path | None = None,
    status: str = BLOCKED_INVALID_STATUS,
) -> dict[str, Any]:
    """返回 fail-closed 摘要，不把输入细节拼进 reason。"""
    # reason 使用枚举式短字符串，避免把 raw JSON、URL、token 或 traceback 带出。
    summary = _safe_base_summary(status, _dedupe(blocked_reasons), artifact_path)
    _ensure_summary_is_safe(summary)
    return summary


def _dedupe(items: list[str]) -> list[str]:
    """保持 reason 顺序，同时去掉重复项。"""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _walk_json(value: Any):
    """深度遍历 JSON 结构，统一做危险 true 和敏感文本检查。"""
    # artifact 里有串口字段，但本 intake 会忽略它；这里只拦截 token、URL、traceback 等不可进入材料合同的内容。
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key), child
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield "", child


def _find_unsafe_input_reasons(artifact: dict[str, Any]) -> list[str]:
    """查找会让材料合同 fail-closed 的危险输入。"""
    reasons: list[str] = []
    for key, value in _walk_json(artifact):
        # 如果输入声称安全或交付已完成，本轮必须阻断，避免历史材料被升级成控制许可。
        if key in DANGEROUS_TRUE_FIELDS and value is True:
            reasons.append(f"dangerous_true_{key}")
        # key 名本身也可能泄露敏感上下文；输出只保留通用 reason，不保留原 key。
        if SECRET_KEY_PATTERN.search(key):
            reasons.append("unsafe_sensitive_key_present")
        # value 命中 URL/绝对路径/traceback 时同样 blocked，但不把原字符串写入摘要。
        if isinstance(value, str) and UNSAFE_VALUE_PATTERN.search(value):
            reasons.append("unsafe_text_present")
    return reasons


def _ensure_summary_is_safe(summary: dict[str, Any]) -> None:
    """防止输出层意外带出绝对路径、URL、token 或串口上下文。"""
    rendered = json.dumps(summary, sort_keys=True, ensure_ascii=False)
    # vendor/source 相对路径允许出现斜杠；真正禁止的是绝对路径、URL、token、traceback、串口设备和 baudrate。
    forbidden_patterns = [
        r"https?://",
        r"/Users/",
        r"/dev/tty",
        r"\b115200\b",
        r"Traceback \(most recent call last\)",
        r"bearer\s+",
        r"token",
        r"password",
        r"secret",
    ]
    for pattern in forbidden_patterns:
        if re.search(pattern, rendered, re.IGNORECASE):
            raise ValueError("unsafe summary leakage detected")


def _is_finite_number(value: Any) -> bool:
    """判断 JSON 数值能否安全参与 L/R 判定。"""
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(parsed)


def _command_matches(command_result: Any, expected_t: int, *, expect_zero: bool | None = None) -> bool:
    """校验上位机记录的 vendor command 摘要。"""
    # command_result.ok 必须为 true，否则不能说明同一串口事务真的写过该阶段命令。
    if not isinstance(command_result, dict) or command_result.get("ok") is not True:
        return False
    command = command_result.get("command")
    # T 值来自 vendor json_cmd.h；任何错 T 都按缺阶段处理。
    if not isinstance(command, dict) or command.get("T") != expected_t:
        return False
    if expected_t != 1 or expect_zero is None:
        return True
    left = command.get("L")
    right = command.get("R")
    # L/R 必须是有限数值，避免字符串、NaN 或 inf 混进运动窗口判断。
    if not _is_finite_number(left) or not _is_finite_number(right):
        return False
    if expect_zero:
        # stop 阶段必须明确是双轮 0/0，不能用单轮 0 或缺字段代替。
        return float(left) == 0.0 and float(right) == 0.0
    # motion 阶段只要求至少一个轮命令非零，因为实际反馈 pair 另由 T=1001 校验。
    return float(left) != 0.0 or float(right) != 0.0


def _feedback_frames(section: Any) -> list[dict[str, Any]]:
    """从上位机 feedback section 中只取 vendor T=1001 帧。"""
    if not isinstance(section, dict):
        return []
    frames = section.get("t1001_feedback_frames")
    if not isinstance(frames, list):
        return []
    valid_frames: list[dict[str, Any]] = []
    for frame in frames:
        if not isinstance(frame, dict):
            continue
        # 复用项目已有 T=1001 parser，避免本 intake 重复猜 r/p/y/v 字段容错规则。
        parsed = parse_feedback_line(json.dumps(frame, separators=(",", ":"), ensure_ascii=True))
        if parsed is None:
            continue
        valid_frames.append(parsed)
    return valid_frames


def _sign_pattern(left: float, right: float) -> str:
    """只描述符号组合，不把它提升为真实方向或里程计结论。"""
    if left > 0 and right > 0:
        return "both_positive"
    if left < 0 and right < 0:
        return "both_negative"
    if left > 0 and right < 0:
        return "left_positive_right_negative"
    if left < 0 and right > 0:
        return "left_negative_right_positive"
    if left == 0 and right == 0:
        return "both_zero"
    if left == 0:
        return "left_zero_right_nonzero"
    return "left_nonzero_right_zero"


def _latest_nonzero_pair(frames: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, int]:
    """提取运动窗口内最后一个同帧 L/R 非零 pair。"""
    latest: dict[str, Any] | None = None
    count = 0
    for index, frame in enumerate(frames):
        left = float(frame["left_speed"])
        right = float(frame["right_speed"])
        # 必须同一 T=1001 帧左右轮都非零，单侧非零不能证明同帧 wheel pair material。
        if left == 0.0 or right == 0.0:
            continue
        count += 1
        latest = {
            # phase 固定为 motion_window，防止后续把 stop 后或其他窗口的非零样本错算进来。
            "phase": "motion_window",
            "frame_index": index,
            "left_speed": left,
            "right_speed": right,
            "sign_pattern": _sign_pattern(left, right),
        }
    return latest, count


def _stop_zero_count(frames: list[dict[str, Any]]) -> int:
    """统计停车后同帧 L/R=0/0 反馈。"""
    count = 0
    for frame in frames:
        if float(frame["left_speed"]) == 0.0 and float(frame["right_speed"]) == 0.0:
            count += 1
    return count


def build_same_session_wheel_feedback_material_summary(
    artifact: dict[str, Any],
    artifact_path: str | Path | None = None,
) -> dict[str, Any]:
    """把历史上位机 same-session artifact 转成安全材料摘要。"""
    # root shape 错误时不能继续访问字段，直接生成最小 blocked 摘要。
    if not isinstance(artifact, dict):
        return _blocked(["artifact_root_not_object"], artifact_path)

    blocked_reasons: list[str] = []
    # schema 是本 intake 的第一道来源门，避免消费无关 JSON wrapper。
    if artifact.get("schema") != EXPECTED_INPUT_SCHEMA:
        blocked_reasons.append("schema_mismatch")

    # 正向历史 artifact 没有 top-level source；如果新输入声明了 source，就必须是预期上位机来源。
    source = artifact.get("source")
    if source not in (None, "", "upper_robot_api", "historical_upper_robot_api_manual_same_session"):
        blocked_reasons.append("source_mismatch")

    blocked_reasons.extend(_find_unsafe_input_reasons(artifact))
    transaction = artifact.get("serial_motion_transaction")
    # serial_motion_transaction 是 same-session 的唯一结构证据，没有它就不能用 top-level summary 兜底。
    if not isinstance(transaction, dict):
        blocked_reasons.append("serial_motion_transaction_missing")
        return _blocked(blocked_reasons, artifact_path)

    # 先分别校验命令阶段，再校验反馈阶段，blocked reason 会告诉现场缺哪段材料。
    motion_command_present = _command_matches(transaction.get("command_result"), 1, expect_zero=False)
    feedback_request_present = _command_matches(transaction.get("motion_feedback_request_result"), 130)
    stop_command_present = _command_matches(transaction.get("stop_result"), 1, expect_zero=True)
    after_stop_request_present = _command_matches(transaction.get("after_stop_feedback_request_result"), 130)

    if not motion_command_present:
        blocked_reasons.append("motion_command_missing_or_zero")
    if not feedback_request_present:
        blocked_reasons.append("motion_feedback_request_missing")
    if not stop_command_present:
        blocked_reasons.append("stop_command_missing_or_nonzero")
    if not after_stop_request_present:
        blocked_reasons.append("after_stop_feedback_request_missing")

    motion_frames = _feedback_frames(transaction.get("feedback_during_motion"))
    after_stop_frames = _feedback_frames(transaction.get("feedback_after_stop"))
    # 非零 pair 只从 motion window 取；after-stop 非零反而会导致 stop-zero 缺失。
    latest_pair, nonzero_count = _latest_nonzero_pair(motion_frames)
    stop_zero_count = _stop_zero_count(after_stop_frames)

    if not motion_frames:
        blocked_reasons.append("motion_window_t1001_missing")
    if nonzero_count == 0:
        blocked_reasons.append("motion_window_nonzero_pair_missing")
    if not after_stop_frames:
        blocked_reasons.append("after_stop_t1001_missing")
    if stop_zero_count == 0:
        blocked_reasons.append("after_stop_zero_pair_missing")

    status = READY_STATUS if not blocked_reasons else BLOCKED_INVALID_STATUS
    summary = _safe_base_summary(status, _dedupe(blocked_reasons), artifact_path)
    summary.update(
        {
            # same_session_material_present 只有在所有 blocked reason 清空时才为 true。
            "same_session_material_present": status == READY_STATUS,
            "motion_command_present": motion_command_present,
            "feedback_request_present": feedback_request_present and after_stop_request_present,
            "wheel_feedback_material_present": nonzero_count > 0,
            "stop_zero_readback_present": stop_zero_count > 0,
            "latest_nonzero_pair": latest_pair,
            "counts": {
                "motion_window_t1001_count": len(motion_frames),
                "motion_window_nonzero_pair_count": nonzero_count,
                "after_stop_t1001_count": len(after_stop_frames),
                "after_stop_zero_pair_count": stop_zero_count,
            },
        }
    )
    _ensure_summary_is_safe(summary)
    return summary


def load_artifact(path: str | Path) -> dict[str, Any]:
    """读取 artifact JSON；坏 JSON 在 CLI 层转成 fail-closed 摘要。"""
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("artifact_root_not_object")
    return payload


def build_summary_from_file(path: str | Path) -> dict[str, Any]:
    """从文件构建摘要，读取失败或 JSON 异常都不抛 raw traceback。"""
    try:
        artifact = load_artifact(path)
    except (OSError, json.JSONDecodeError, ValueError):
        # CLI smoke 需要可机器判断的 blocked JSON，而不是 Python traceback。
        return _blocked(["artifact_json_unreadable_or_invalid"], path)
    return build_same_session_wheel_feedback_material_summary(artifact, path)


def main(argv: list[str] | None = None) -> int:
    """CLI 入口：打印安全 JSON 摘要，不接触串口或硬件。"""
    parser = argparse.ArgumentParser(
        description="Build a sanitized WAVE ROVER same-session wheel feedback material summary."
    )
    parser.add_argument("artifact_json", help="Historical upper_robot_api manual result JSON artifact.")
    parser.add_argument("--output", help="Optional output file for the sanitized summary.")
    args = parser.parse_args(argv)

    summary = build_summary_from_file(args.artifact_json)
    payload = json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        # 输出文件只写脱敏摘要；stdout 只打印 basename，避免暴露绝对输出路径。
        Path(args.output).write_text(payload, encoding="utf-8")
        print(Path(args.output).name)
    else:
        print(payload, end="")
    # blocked 使用非零退出码，方便 smoke/HIL gate 在 shell 层 fail-closed。
    return 0 if summary["status"] == READY_STATUS else 4


if __name__ == "__main__":
    raise SystemExit(main())
