#!/usr/bin/env python3
"""把 O5 mock terminal-result bridge 摘要接入 DeliveryStateMachine 离线对账。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


# 脚本只读 source summary 并写本 sprint artifact，不连接云、ROS2、Nav2 或底盘控制路径。
# 将路径压缩为 basename 是为了让 artifact 可共享，同时避免泄露开发机绝对路径。
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
BEHAVIOR_SRC = WORKSPACE_ROOT / "onboard" / "src" / "ros2_trashbot_behavior"
if str(BEHAVIOR_SRC) not in sys.path:
    sys.path.insert(0, str(BEHAVIOR_SRC))

from ros2_trashbot_behavior.delivery_state_machine import (  # noqa: E402
    DeliveryStateMachine,
    TerminalResultReconciliationError,
)


def load_json_object(path: Path) -> dict[str, Any]:
    """source summary 必须是单个 JSON object，JSONL、数组或空文件都 fail closed。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TerminalResultReconciliationError("source summary must be a JSON object")
    return data


def build_summary(
    source: dict[str, Any],
    *,
    source_summary_ref: str,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """通过 DeliveryStateMachine 生成 fail-closed summary，而不是绕过状态机格式化。"""
    machine = DeliveryStateMachine()
    summary = machine.reconcile_terminal_result_summary(
        source,
        source_summary_ref=source_summary_ref,
        generated_at_utc=generated_at_utc,
    )
    return summary


def write_summary(
    source_summary: Path,
    output: Path,
    *,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """读取 source、执行状态机离线对账并写出 artifact。"""
    source = load_json_object(source_summary)
    summary = build_summary(
        source,
        source_summary_ref=source_summary.name,
        generated_at_utc=generated_at_utc,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def _safe_error_text(exc: Exception) -> str:
    """失败日志只保留短原因，避免 traceback 或绝对路径进入验收输出。"""
    text = str(exc).replace(str(WORKSPACE_ROOT), "[workspace]")
    return f"{exc.__class__.__name__}: {text}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run O5 delivery state terminal reconciliation")
    parser.add_argument("--source-summary", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        summary = write_summary(args.source_summary, args.output)
    except (TerminalResultReconciliationError, OSError, json.JSONDecodeError) as exc:
        print(_safe_error_text(exc), file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
