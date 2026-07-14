#!/usr/bin/env python3
"""生成 O5 delivery state live success gate 的本地合同证明。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


# CLI 只生成 software-proof artifact，不连接真实云、ROS2、Nav2、手机浏览器或底盘。
# 通过状态机统一生成 summary，避免脚本绕过未来成功准入逻辑。
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
BEHAVIOR_SRC = WORKSPACE_ROOT / "onboard" / "src" / "ros2_trashbot_behavior"
if str(BEHAVIOR_SRC) not in sys.path:
    sys.path.insert(0, str(BEHAVIOR_SRC))

from ros2_trashbot_behavior.delivery_state_machine import (  # noqa: E402
    DeliveryStateMachine,
    TerminalResultReconciliationError,
)


SYNTHETIC_CURRENT_LIVE_MODE = "synthetic-current-live"


def synthetic_current_live_fixture() -> dict[str, Any]:
    """构造当前轮可验证的 live-shaped 输入，但显式不携带真实 live 成功。"""
    identity = {
        "task_id": "task_o3_28_pose_fixed_route_consumer_20260713_0402",
        "robot_id": "robot-synthetic-o5-live-gate",
        "packet_id": "packet_o3_28_pose_same_task_replay_7d57826142b0c79c",
        "route_intent_id": "route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path",
        "terminal_result_id": "terminal_result_synthetic_current_live_shape_20260714_0528",
    }
    return {
        "fixture_mode": SYNTHETIC_CURRENT_LIVE_MODE,
        "source_mode": SYNTHETIC_CURRENT_LIVE_MODE,
        "identity": identity,
        "live_route_execution_success": False,
        "safe_to_control": False,
        "hil_pass": False,
        "terminal_result_recorded": False,
        "delivery_success": False,
        "dropoff_success": False,
        "route_execution_success": False,
        "real_world_delivery_proven": False,
        "delivery_success_accepted_for_state_machine": False,
        "evidence_fresh": True,
        "same_evidence_window": True,
        "route_execution": {
            "task_id": identity["task_id"],
            "robot_id": identity["robot_id"],
            "packet_id": identity["packet_id"],
            "route_intent_id": identity["route_intent_id"],
            "success": False,
        },
        "operator_dropoff_acceptance": {
            "task_id": identity["task_id"],
            "robot_id": identity["robot_id"],
            "accepted": False,
        },
        "hil": {
            "task_id": identity["task_id"],
            "robot_id": identity["robot_id"],
            "pass": False,
        },
        "terminal_result": {
            "task_id": identity["task_id"],
            "robot_id": identity["robot_id"],
            "packet_id": identity["packet_id"],
            "route_intent_id": identity["route_intent_id"],
            "terminal_result_id": identity["terminal_result_id"],
            "recorded": False,
        },
    }


def evidence_for_fixture_mode(fixture_mode: str) -> dict[str, Any]:
    """限制 fixture mode，防止 CLI 被误用成真实 live 证据采集器。"""
    if fixture_mode != SYNTHETIC_CURRENT_LIVE_MODE:
        raise ValueError(f"unsupported fixture mode: {fixture_mode}")
    return synthetic_current_live_fixture()


def build_summary(
    *,
    fixture_mode: str,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """通过 DeliveryStateMachine 评估 gate，保证 CLI 和状态机语义一致。"""
    evidence = evidence_for_fixture_mode(fixture_mode)
    machine = DeliveryStateMachine()
    return machine.delivery_state_live_success_gate(
        evidence,
        source_summary_ref=f"{fixture_mode}_fixture",
        generated_at_utc=generated_at_utc,
    )


def write_summary(
    output: Path,
    *,
    fixture_mode: str,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """写出 sprint artifact；父目录不存在时创建，内容保持可复核 JSON。"""
    summary = build_summary(fixture_mode=fixture_mode, generated_at_utc=generated_at_utc)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def _safe_error_text(exc: Exception) -> str:
    """错误输出只保留短原因，不输出 traceback、绝对路径或外部连接细节。"""
    text = str(exc).replace(str(WORKSPACE_ROOT), "[workspace]")
    return f"{exc.__class__.__name__}: {text}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run O5 delivery state live success gate contract proof")
    parser.add_argument("--fixture-mode", required=True, choices=[SYNTHETIC_CURRENT_LIVE_MODE])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        summary = write_summary(args.output, fixture_mode=args.fixture_mode)
    except (TerminalResultReconciliationError, OSError, ValueError, TypeError) as exc:
        print(_safe_error_text(exc), file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
