#!/usr/bin/env python3
"""生成 O5 operator dropoff acceptance gate 的 synthetic 合同证明。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


# CLI 只写本地 software-proof artifact，不连接真实云、手机浏览器、ROS2、Nav2 或底盘。
# 通过状态机生成 summary，避免脚本绕过 operator acceptance 的 fail-closed 规则。
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
BEHAVIOR_SRC = WORKSPACE_ROOT / "onboard" / "src" / "ros2_trashbot_behavior"
if str(BEHAVIOR_SRC) not in sys.path:
    sys.path.insert(0, str(BEHAVIOR_SRC))

from ros2_trashbot_behavior.delivery_state_machine import (  # noqa: E402
    DeliveryStateMachine,
    TerminalResultReconciliationError,
)


SYNTHETIC_FIXTURE_MODE = "synthetic"


def synthetic_fixture() -> dict[str, Any]:
    """构造当前 sprint 可验证的 synthetic 输入，所有 live 成功条件固定 false。"""
    identity = {
        "task_id": "task_o3_28_pose_fixed_route_consumer_20260713_0402",
        "robot_id": "robot-synthetic-o5-operator-dropoff",
        "packet_id": "packet_o3_28_pose_same_task_replay_7d57826142b0c79c",
        "route_intent_id": "route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path",
        "terminal_result_id": "terminal_result_synthetic_operator_dropoff_20260714_0729",
    }
    # 证据形状保持 live-compatible，但 source_mode 明确不是 live，防止误读为现场动作。
    return {
        "fixture_mode": SYNTHETIC_FIXTURE_MODE,
        "source_mode": SYNTHETIC_FIXTURE_MODE,
        "identity": identity,
        "live_route_execution_success": False,
        "safe_to_control": False,
        "hil_pass": False,
        "terminal_result_recorded": False,
        "evidence_fresh": True,
        "same_evidence_window": True,
        "delivery_success": False,
        "dropoff_success": False,
        "route_execution_success": False,
        "real_world_delivery_proven": False,
        "delivery_success_accepted_for_state_machine": False,
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
            "acceptance_id": "synthetic_operator_dropoff_acceptance_fixture",
            "action_type": "operator_dropoff_acceptance",
            "actor_source_label": "synthetic_fixture",
            "occurred_at_utc": "2026-07-14T07:29:00Z",
            "safe_evidence_ref": "operator_dropoff_acceptance_synthetic_fixture.json",
            "redaction_status": "passed",
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
    """只允许 synthetic fixture；live 证据必须由后续现场采集链路提供。"""
    if fixture_mode != SYNTHETIC_FIXTURE_MODE:
        raise ValueError(f"unsupported fixture mode: {fixture_mode}")
    return synthetic_fixture()


def build_summary(
    *,
    fixture_mode: str,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """复用 DeliveryStateMachine，保证 CLI 输出和状态机 gate 语义一致。"""
    evidence = evidence_for_fixture_mode(fixture_mode)
    machine = DeliveryStateMachine()
    return machine.operator_dropoff_acceptance_gate(
        evidence,
        source_summary_ref=f"{fixture_mode}_operator_dropoff_acceptance_fixture",
        generated_at_utc=generated_at_utc,
    )


def write_summary(
    output: Path,
    *,
    fixture_mode: str,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """写出 sprint artifact；创建父目录并保持稳定可读 JSON。"""
    summary = build_summary(fixture_mode=fixture_mode, generated_at_utc=generated_at_utc)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def _safe_error_text(exc: Exception) -> str:
    """错误只输出短文本，不泄露 traceback、绝对路径或外部目标。"""
    text = str(exc).replace(str(WORKSPACE_ROOT), "[workspace]")
    return f"{exc.__class__.__name__}: {text}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run O5 operator dropoff acceptance gate synthetic proof")
    parser.add_argument("--fixture-mode", required=True, choices=[SYNTHETIC_FIXTURE_MODE])
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
