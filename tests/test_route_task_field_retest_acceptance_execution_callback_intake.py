#!/usr/bin/env python3
"""route_task_field_retest_acceptance_execution_callback_intake 的顶层验收测试入口。

这里复用 pc-tools/evidence 下的离线围栏测试，让 sprint tech-plan 指定的
`python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_callback_intake`
能直接运行，同时避免复制一份会和 evidence 目录测试漂移的断言。
"""

from __future__ import annotations

import sys
from pathlib import Path


# pc-tools 不是 Python package；验收入口显式加入该目录，保持 CLI 与 unittest 同源。
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "pc-tools" / "evidence"
sys.path.insert(0, str(EVIDENCE_DIR))

from test_route_task_field_retest_acceptance_execution_callback_intake import (  # noqa: E402,F401
    RouteTaskFieldRetestAcceptanceExecutionCallbackIntakeTest,
)


__all__ = ["RouteTaskFieldRetestAcceptanceExecutionCallbackIntakeTest"]
